#!/usr/bin/env python3
"""
爬虫Worker - 从Redis队列获取任务并执行
"""

import time
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from config import Config, TaskStatus
from redis_client import RedisClient
from scraper_adapter import scraper_adapter

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/worker_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class Worker:
    def __init__(self):
        self.redis_client = RedisClient()
        self.running = True
        self.current_task_id: Optional[str] = None
        logger.info(f"Worker初始化完成，类型: {Config.WORKER_TYPE}")
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"接收到信号 {signum}，正在优雅关闭...")
        self.running = False
    
    def process_task(self, task_id: str) -> bool:
        """处理单个任务"""
        try:
            logger.info(f"开始处理任务: {task_id}")
            
            # 获取任务详情
            task_data = self.redis_client.get_task(task_id)
            if not task_data:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            # 检查Worker类型是否匹配
            scraper_type = task_data['scraper_type']
            if Config.WORKER_TYPE != 'all' and scraper_type != Config.WORKER_TYPE:
                logger.info(f"跳过任务 {task_id}: 类型不匹配 ({scraper_type} vs {Config.WORKER_TYPE})")
                # 将任务重新放回队列
                self.redis_client.redis_client.lpush('scrape_queue', task_id)
                return True
            
            # 更新任务状态为处理中
            self.redis_client.update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                progress=10
            )
            
            # 执行爬取任务
            urls = task_data['urls']
            options = task_data.get('options', {})
            
            logger.info(f"任务详情: {len(urls)}个URL, 类型: {scraper_type}")
            
            # 更新进度到50%
            self.redis_client.update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                progress=50
            )
            
            # 调用爬虫适配器
            results = scraper_adapter.scrape_urls(urls, scraper_type, options)
            
            # 检查成功率
            success_count = sum(1 for r in results if r.get('success', False))
            total_count = len(results)
            success_rate = success_count / total_count if total_count > 0 else 0
            
            logger.info(f"爬取完成: 成功{success_count}/{total_count} (成功率: {success_rate:.1%})")
            
            # 如果requests成功率太低，转入竞速模式
            if scraper_type == 'requests' and success_rate < 0.7:
                logger.warning(f"requests成功率过低({success_rate:.1%})，转入竞速模式")
                
                # 将任务转入竞速队列
                self.redis_client.redis_client.lpush('race_queue', task_id)
                
                # 更新任务状态为竞速模式
                self.redis_client.update_task_status(
                    task_id, 
                    TaskStatus.PROCESSING, 
                    progress=95,
                    error_message="requests成功率低，启动竞速模式"
                )
                
                # 更新任务类型为竞速
                self.redis_client.redis_client.hset(f'task:{task_id}', 'scraper_type', 'race')
                
                logger.info(f"任务 {task_id} 已转入竞速队列")
                return True
            
            # 更新进度到90%
            self.redis_client.update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                progress=90
            )
            
            # 存储结果
            self.redis_client.store_results(task_id, results)
            
            # 更新任务状态为完成
            self.redis_client.update_task_status(
                task_id, 
                TaskStatus.COMPLETED, 
                progress=100
            )
            
            logger.info(f"任务完成: {task_id}, 结果数: {len(results)}")
            return True
            
        except Exception as e:
            logger.error(f"处理任务失败 {task_id}: {str(e)}")
            
            # requests失败，转入竞速模式
            if scraper_type == 'requests':
                logger.info(f"requests处理失败，转入竞速模式: {task_id}")
                
                # 将任务转入竞速队列
                self.redis_client.redis_client.lpush('race_queue', task_id)
                
                # 更新任务状态和类型
                self.redis_client.update_task_status(
                    task_id, 
                    TaskStatus.PROCESSING, 
                    error_message=f"requests失败，转入竞速模式: {str(e)}"
                )
                self.redis_client.redis_client.hset(f'task:{task_id}', 'scraper_type', 'race')
                
                logger.info(f"任务 {task_id} 已转入竞速队列")
                return True
            else:
                # 其他爬虫类型直接失败
                self.redis_client.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error_message=str(e)
                )
                return False
    
    def run(self):
        """运行Worker主循环"""
        logger.info("Worker开始运行...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            while self.running:
                try:
                    # 从队列获取任务
                    task_id = self.redis_client.get_next_task()
                    
                    if task_id:
                        self.current_task_id = task_id
                        logger.info(f"获取到新任务: {task_id}")
                        
                        # 处理任务
                        success = self.process_task(task_id)
                        
                        if success:
                            logger.info(f"任务处理成功: {task_id}")
                        else:
                            logger.error(f"任务处理失败: {task_id}")
                        
                        self.current_task_id = None
                    else:
                        # 没有任务，等待一段时间
                        logger.debug("没有新任务，等待中...")
                        time.sleep(Config.POLL_INTERVAL)
                
                except KeyboardInterrupt:
                    logger.info("用户中断，正在退出...")
                    break
                except Exception as e:
                    logger.error(f"Worker循环错误: {str(e)}")
                    time.sleep(Config.POLL_INTERVAL)
        
        finally:
            logger.info("Worker已停止")
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理Worker资源...")
        # 如果有正在处理的任务，将其状态更新为失败
        if self.current_task_id:
            try:
                self.redis_client.update_task_status(
                    self.current_task_id,
                    TaskStatus.FAILED,
                    error_message="Worker异常停止"
                )
            except Exception as e:
                logger.error(f"清理任务状态时出错: {e}")

def main():
    """主函数"""
    try:
        worker_type = Config.WORKER_TYPE
        
        if worker_type == 'race':
            # 运行竞速Worker
            from race_worker import RaceWorker
            logger.info("启动竞速Worker模式")
            worker = RaceWorker()
        else:
            # 运行普通Worker
            logger.info(f"启动普通Worker模式: {worker_type}")
            worker = Worker()
        
        worker.run()
    except Exception as e:
        logger.error(f"Worker启动失败: {e}")
        sys.exit(1)
    finally:
        if 'worker' in locals():
            worker.cleanup()

if __name__ == "__main__":
    main()