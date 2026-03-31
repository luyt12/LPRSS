"""
LatePost 文章邮件发送脚本
读取 latepost_articles/ 目录下的文章，发送 HTML 邮件
"""
import os
import sys
import smtplib
import ssl
import glob
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 直接从环境变量读取，不依赖 .env 文件
EMAIL_TO = os.getenv("EMAIL_TO") or ""
EMAIL_FROM = os.getenv("EMAIL_FROM") or ""
SMTP_HOST = os.getenv("SMTP_HOST") or ""
SMTP_PORT = int(os.getenv("SMTP_PORT") or "465")
SMTP_USER = os.getenv("SMTP_USER") or ""
SMTP_PASS = os.getenv("SMTP_PASS") or ""

_missing = [k for k, v in {"EMAIL_TO": EMAIL_TO, "EMAIL_FROM": EMAIL_FROM, "SMTP_HOST": SMTP_HOST, "SMTP_USER": SMTP_USER, "SMTP_PASS": SMTP_PASS}.items() if not v]
if _missing:
    print("ERROR: Missing required env vars: " + ", ".join(_missing))
    sys.exit(1)

ARTICLES_DIR = "latepost_articles"
MAX_ARTICLES = 10  # 每次最多发送文章数


def read_articles():
    """读取 latepost_articles/ 目录下的所有文章"""
    articles = []
    pattern = os.path.join(ARTICLES_DIR, "latepost_article_*.md")
    files = glob.glob(pattern)
    
    if not files:
        print(f"未找到任何文章文件: {pattern}")
        return articles
    
    # 按文件修改时间排序，最新的在前
    files.sort(key=os.path.getmtime, reverse=True)
    
    for filepath in files[:MAX_ARTICLES]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            articles.append({
                'path': filepath,
                'content': content,
                'mtime': os.path.getmtime(filepath)
            })
        except Exception as e:
            print(f"读取文章失败 {filepath}: {e}")
    
    return articles


def parse_article(content):
    """解析文章 Markdown，提取标题、作者、日期、链接、正文"""
    lines = content.split('\n')
    
    title = "无标题"
    date = ""
    author = ""
    link = ""
    body_lines = []
    in_body = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# ') and not in_body:
            title = line[2:].strip()
            continue
        
        if line.startswith('- **') or line.startswith('**'):
            if '发布日期' in line:
                date = line.split('**')[-1].strip()
            elif '作者' in line:
                author = line.split('**')[-1].strip()
            elif '原文链接' in line:
                link = line.split('**')[-1].strip()
            continue
        
        if line == '---':
            in_body = True
            continue
        
        if in_body and line:
            body_lines.append(line)
    
    return {
        'title': title,
        'date': date,
        'author': author,
        'link': link,
        'body': '\n\n'.join(body_lines)
    }


def format_email_html(articles):
    """将文章列表格式化为 HTML 邮件"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    articles_html = []
    for i, article in enumerate(articles):
        parsed = parse_article(article['content'])
        
        # 格式化正文（简单处理换行）
        body_html = parsed['body'].replace('\n\n', '</p><p>').replace('\n', '<br>')
        if body_html:
            body_html = f'<p>{body_html}</p>'
        
        # 提取链接文本
        link_html = f'<a href="{parsed["link"]}">阅读原文</a>' if parsed['link'] else ''
        
        article_html = f"""
        <div style="margin-bottom: 40px; padding-bottom: 30px; border-bottom: 1px solid #e0e0e0;">
            <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 10px 0;">{i+1}. {parsed['title']}</h2>
            <div style="color: #888; font-size: 13px; margin-bottom: 15px;">
                {f"作者：{parsed['author']} &nbsp;&nbsp;" if parsed['author'] else ""}
                {f"发布日期：{parsed['date']}" if parsed['date'] else ""}
            </div>
            <div style="font-size: 15px; line-height: 1.8; color: #333;">
                {body_html}
            </div>
            <div style="margin-top: 15px; font-size: 13px;">
                {link_html}
            </div>
        </div>
        """
        articles_html.append(article_html)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #1a1a1a;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #1a1a1a;
            margin: 0;
            font-size: 24px;
        }}
        .date {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #888;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>晚点 LatePost 文章精选</h1>
            <div class="date">{today} · 共 {len(articles)} 篇文章</div>
        </div>
        <div class="content">
            {''.join(articles_html)}
        </div>
        <div class="footer">
            此邮件由 OpenClaw Agent 自动发送<br>
        </div>
    </div>
</body>
</html>"""
    return html


def send_email(html_content):
    """发送 HTML 邮件"""
    if not SMTP_PASS:
        print("[ERR] SMTP_PASS 未设置")
        return False
    
    subject = f"晚点 LatePost 文章精选 - {datetime.now().strftime('%Y-%m-%d')}"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print(f"[OK] 邮件已发送至 {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"[ERR] 邮件发送失败: {e}")
        return False


def main():
    print("=== 晚点 LatePost 邮件发送 ===")
    
    # 读取文章
    articles = read_articles()
    if not articles:
        print("[WARN] 没有找到文章，跳过发送")
        return False
    
    print(f"读取到 {len(articles)} 篇文章")
    
    # 格式化邮件
    html = format_email_html(articles)
    
    # 发送
    return send_email(html)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
