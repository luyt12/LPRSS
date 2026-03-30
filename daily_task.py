"""
每日任务入口脚本
用于 GitHub Actions 环境，避免内联 Python 带来的 YAML 语法问题
"""
import os
import sys
import re

# Step 1: 爬取最新文章
print("Step 1: 爬取最新文章...")
from simple_scraper import SimpleLatePostScraper

scraper = SimpleLatePostScraper(output_dir='latepost_articles')

# 从 feed.xml 获取最新 ID，没有则从 2830 开始
latest_id = 2830
if os.path.exists('feed.xml'):
    try:
        content = open('feed.xml', encoding='utf-8').read()
        m = re.search(r'<latestArticleId>(\d+)</latestArticleId>', content)
        if m:
            latest_id = int(m.group(1))
    except Exception as e:
        print(f"读取 feed.xml 失败: {e}")

start_id = latest_id + 1
end_id = start_id + 5

print(f"爬取文章 ID 范围: {start_id} - {end_id}")
results = scraper.scrape_articles_range(start_id, end_id)
print(f"爬取结果: {results}")

# Step 2: 更新本地 feed.xml
print("Step 2: 更新本地 feed.xml...")
try:
    from update_feed_local import update_feed
    update_feed()
    print("feed.xml 更新完成")
except Exception as e:
    print(f"更新 feed.xml 失败: {e}")

# Step 3: 发送邮件
print("Step 3: 发送邮件...")
try:
    from send_email import main as send_email_main
    send_email_main()
    print("邮件发送完成")
except Exception as e:
    print(f"发送邮件失败: {e}")

print("每日任务执行完毕")
