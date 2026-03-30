"""
RSS Feed 更新脚本（本地版本，不推送 GitHub）
用于 GitHub Actions 环境
"""
import os
import re
import glob
import xml.etree.ElementTree as ET
from datetime import datetime

FEED_PATH = 'feed.xml'
ARTICLES_DIR = 'latepost_articles'
MAX_ITEMS = 50


def get_latest_id_from_feed():
    """从 feed.xml 获取最新文章 ID"""
    if not os.path.exists(FEED_PATH):
        return 0
    try:
        with open(FEED_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'<latestArticleId>(\d+)</latestArticleId>', content)
        if match:
            return int(match.group(1))
        matches = re.findall(r'id=(\d+)', content)
        if matches:
            return max(int(m) for m in matches)
    except Exception as e:
        print(f"获取最新ID失败: {e}")
    return 0


def update_feed():
    """更新本地 feed.xml"""
    # 获取所有文章文件
    files = glob.glob(os.path.join(ARTICLES_DIR, 'latepost_article_*.md'))
    if not files:
        print("没有文章文件")
        return

    # 解析所有文章 ID
    article_ids = []
    for f in files:
        m = re.search(r'latepost_article_(\d+)', f)
        if m:
            article_ids.append(int(m.group(1)))

    if not article_ids:
        print("无法解析文章 ID")
        return

    article_ids.sort(reverse=True)
    print(f"找到 {len(article_ids)} 篇文章，最新 ID: {article_ids[0]}")

    # 构建 RSS 内容
    now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

    # 读取现有 feed.xml 或创建新的
    if os.path.exists(FEED_PATH):
        try:
            tree = ET.parse(FEED_PATH)
            root = tree.getroot()
            channel = root.find('channel')
            # 清空现有 items
            for item in channel.findall('item'):
                channel.remove(item)
            # 更新 lastBuildDate
            lbd = channel.find('lastBuildDate')
            if lbd is not None:
                lbd.text = now
        except Exception:
            # 文件损坏，重新创建
            os.remove(FEED_PATH)
            root = None
    else:
        root = None

    if root is None:
        # 创建新 RSS
        root = ET.Element('rss', version='2.0')
        channel = ET.SubElement(root, 'channel')
        ET.SubElement(channel, 'title').text = '晚点 LatePost'
        ET.SubElement(channel, 'link').text = 'https://www.latepost.com'
        ET.SubElement(channel, 'description').text = '晚点 LatePost 文章订阅'
        ET.SubElement(channel, 'language').text = 'zh-cn'
        ET.SubElement(channel, 'lastBuildDate').text = now
        ET.SubElement(channel, 'latestArticleId').text = str(article_ids[0])
        tree = ET.ElementTree(root)

    # 添加文章 items
    for article_id in article_ids[:MAX_ITEMS]:
        filepath = os.path.join(ARTICLES_DIR, f'latepost_article_{article_id}.md')
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析文章
        title_match = re.search(r'^# (.+)', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f'文章 {article_id}'

        date_match = re.search(r'\*\*发布日期\*\*: (.+)', content)
        date_str = date_match.group(1).strip() if date_match else now

        # 创建 item
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = title
        link_text = f'https://www.latepost.com/news/dj_detail?id={article_id}'
        ET.SubElement(item, 'link').text = link_text
        ET.SubElement(item, 'guid').text = link_text

        pubdate = ET.SubElement(item, 'pubDate')
        pubdate.text = now

    # 更新 latestArticleId
    channel = root.find('channel')
    lid = channel.find('latestArticleId')
    if lid is None:
        lid = ET.SubElement(channel, 'latestArticleId')
    lid.text = str(article_ids[0])

    # 保存
    tree.write(FEED_PATH, encoding='utf-8', xml_declaration=True)
    print(f"feed.xml 已更新，共 {len(article_ids[:MAX_ITEMS])} 篇文章")


if __name__ == '__main__':
    update_feed()
