"""
晚点 LatePost 文章邮件服务
定时爬取最新文章并发送邮件
"""
import os
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# 导入项目模块
import simple_scraper
import update_rss
import send_email

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

# 常量
ARTICLES_DIR = 'latepost_articles'
FEED_PATH = 'feed.xml'
TIMEZONE_EST = pytz.timezone('America/New_York')


def daily_task():
    """
    每日任务流程：
    1. 爬取最新文章
    2. 更新 feed.xml（仅用于记录，不推送 GitHub）
    3. 发送邮件
    """
    logger.info("=" * 40)
    logger.info("开始执行每日任务")
    
    # Step 1: 爬取最新文章
    logger.info("Step 1: 爬取最新文章")
    try:
        scraper = simple_scraper.SimpleLatePostScraper(output_dir=ARTICLES_DIR)
        rss_updater = update_rss.RSSUpdater(feed_path=FEED_PATH, articles_dir=ARTICLES_DIR)
        
        latest_id = rss_updater.get_latest_article_id()
        if not latest_id:
            logger.warning("无法获取最新文章ID，尝试从 ID 2800 开始")
            latest_id = 2800
        
        start_id = int(latest_id) + 1
        end_id = start_id + 5  # 每次抓取最新 5 篇
        
        logger.info(f"爬取文章 ID 范围: {start_id} - {end_id}")
        results = scraper.scrape_articles_range(start_id, end_id)
        
        if results['success']:
            logger.info(f"成功爬取 {len(results['success'])} 篇新文章")
        else:
            logger.info("没有发现新文章")
            
    except Exception as e:
        logger.error(f"Step 1 失败: {e}")
    
    # Step 2: 更新 feed.xml（本地记录）
    logger.info("Step 2: 更新 feed.xml")
    try:
        rss_updater = update_rss.RSSUpdater(feed_path=FEED_PATH, articles_dir=ARTICLES_DIR)
        new_ids = list(range(start_id, end_id + 1))
        rss_updater.update_feed(new_ids)
        logger.info("feed.xml 更新完成")
    except Exception as e:
        logger.error(f"Step 2 失败: {e}")
    
    # Step 3: 发送邮件
    logger.info("Step 3: 发送邮件")
    try:
        success = send_email.main()
        if success:
            logger.info("邮件发送成功")
        else:
            logger.error("邮件发送失败")
    except Exception as e:
        logger.error(f"Step 3 失败: {e}")
    
    logger.info("每日任务执行完毕")
    logger.info("=" * 40)


def main():
    logger.info("晚点 LatePost 邮件服务启动")
    
    # 立即执行一次
    daily_task()
    
    # 设置定时任务
    scheduler = BlockingScheduler(timezone=TIMEZONE_EST)
    
    # 每天 22:00 EST 自动执行
    scheduler.add_job(
        daily_task,
        trigger=CronTrigger(hour=22, minute=0, timezone=TIMEZONE_EST),
        id='daily_latepost_email',
        name='Daily LatePost Email at 22:00 EST',
        replace_existing=True
    )
    
    logger.info("定时任务已设置: 每天 22:00 EST 执行")
    logger.info("按 Ctrl+C 退出")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("服务已停止")


if __name__ == "__main__":
    main()
