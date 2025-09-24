#!/usr/bin/env python3
"""
竞速Worker - 多爬虫竞速处理失败的任务
"""

import time
import logging
import signal
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config, TaskStatus
from redis_client import RedisClient
from simple_scrapers import scrape_with_scraper, SCRAPERS

# 设置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RaceWorker:
    """竞速Worker - 处理requests失败的任务"""
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.running = True
        self.current_task_id: Optional[str] = None
        logger.info(f"RaceWorker初始化完成，支持的爬虫: {list(SCRAPERS.keys())}")
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"接收到信号 {signum}，正在优雅关闭...")
        self.running = False
    
    def process_race_task(self, task_id: str) -> bool:
        """处理竞速任务 - 多个爬虫同时尝试"""
        try:
            logger.info(f"开始竞速处理任务: {task_id}")
            
            # 获取任务详情
            task_data = self.redis_client.get_task(task_id)
            if not task_data:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            # 检查是否是竞速任务
            if task_data['scraper_type'] != 'race':
                logger.info(f"跳过非竞速任务: {task_id}")
                return True
            
            # 更新状态为处理中
            self.redis_client.update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                progress=20
            )
            
            urls = task_data['urls']
            options = task_data.get('options', {})
            
            logger.info(f"竞速任务详情: {len(urls)}个URL")
            
            # 使用线程池让所有爬虫同时竞争
            first_success = None
            winner_scraper = None
            
            # 可用的爬虫类型（排除requests，因为它已经试过了）
            race_scrapers = ['newspaper', 'readability', 'trafilatura']
            
            with ThreadPoolExecutor(max_workers=len(race_scrapers)) as executor:
                # 提交所有爬虫任务
                future_to_scraper = {
                    executor.submit(self.scrape_with_scraper, urls, scraper_type): scraper_type
                    for scraper_type in race_scrapers
                }
                
                # 等待第一个成功的结果
                for future in as_completed(future_to_scraper, timeout=45):  # 45秒超时
                    scraper_type = future_to_scraper[future]
                    try:
                        results = future.result(timeout=5)
                        
                        # 检查是否有成功的爬取
                        success_count = sum(1 for r in results if r.get('success', False))
                        
                        logger.info(f"[{scraper_type}] 完成爬取，成功: {success_count}/{len(results)}")
                        
                        if success_count > 0:
                            logger.info(f"🎯 [{scraper_type}] 率先完成，使用其结果!")
                            first_success = results
                            winner_scraper = scraper_type
                            
                            # 取消其他还在运行的任务
                            for f in future_to_scraper:
                                if f != future and not f.done():
                                    f.cancel()
                            break
                        
                    except Exception as e:
                        logger.error(f"[{scraper_type}] 爬取异常: {e}")
            
            # 检查竞速结果
            if first_success:
                # 有爬虫成功，存储结果
                self.redis_client.store_results(task_id, first_success)
                self.redis_client.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    progress=100
                )
                logger.info(f"✅ 竞速任务完成: {task_id}, 获胜爬虫: {winner_scraper}")
                return True
            else:
                # 所有爬虫都失败
                logger.warning(f"❌ 所有爬虫都失败: {task_id}")
                self.redis_client.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error_message="所有爬虫尝试均失败"
                )
                return False
                
        except Exception as e:
            logger.error(f"竞速处理任务失败 {task_id}: {str(e)}")
            self.redis_client.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=f"竞速处理异常: {str(e)}"
            )
            return False
    
    def scrape_with_scraper(self, urls: List[str], scraper_type: str) -> List[Dict[str, Any]]:
        """使用指定爬虫爬取URL列表"""
        logger.info(f"[{scraper_type}] 开始批量爬取: {len(urls)}个URL")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"[{scraper_type}] 爬取进度: {i+1}/{len(urls)} - {url}")
                
                result = scrape_with_scraper(url, scraper_type)
                results.append(result)
                
                if result.get('success', False):
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"[{scraper_type}] 爬取异常: {url} - {str(e)}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'scraper_type': scraper_type
                })
        
        logger.info(f"[{scraper_type}] 批量爬取完成: 成功{successful_count}个, 失败{failed_count}个")
        return results
    
    def get_next_race_task(self) -> Optional[str]:
        """从竞速队列获取任务"""
        # 使用不同的队列名称
        task_id = self.redis_client.redis_client.brpop('race_queue', timeout=Config.POLL_INTERVAL)
        if task_id:
            return task_id[1]
        return None
    
    def run(self):
        """运行RaceWorker主循环"""
        logger.info("RaceWorker开始运行...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            while self.running:
                try:
                    # 从竞速队列获取任务
                    task_id = self.get_next_race_task()
                    
                    if task_id:
                        self.current_task_id = task_id
                        logger.info(f"竞速Worker获取到新任务: {task_id}")
                        
                        # 处理竞速任务
                        success = self.process_race_task(task_id)
                        
                        if success:
                            logger.info(f"竞速任务处理成功: {task_id}")
                        else:
                            logger.error(f"竞速任务处理失败: {task_id}")
                        
                        self.current_task_id = None
                    else:
                        # 没有任务，等待一段时间
                        logger.debug("竞速队列没有新任务，等待中...")
                        time.sleep(Config.POLL_INTERVAL)
                
                except KeyboardInterrupt:
                    logger.info("用户中断，正在退出...")
                    break
                except Exception as e:
                    logger.error(f"RaceWorker循环错误: {str(e)}")
                    time.sleep(Config.POLL_INTERVAL)
        
        finally:
            logger.info("RaceWorker已停止")
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理RaceWorker资源...")
        if self.current_task_id:
            try:
                self.redis_client.update_task_status(
                    self.current_task_id,
                    TaskStatus.FAILED,
                    error_message="RaceWorker异常停止"
                )
            except Exception as e:
                logger.error(f"清理任务状态时出错: {e}")

def main():
    """主函数"""
    try:
        worker = RaceWorker()
        worker.run()
    except Exception as e:
        logger.error(f"RaceWorker启动失败: {e}")
        sys.exit(1)
    finally:
        if 'worker' in locals():
            worker.cleanup()

if __name__ == "__main__":
    main()