import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config

# 导入简单爬虫
from simple_scraper import scrape_urls
from simple_scrapers import scrape_urls_async, scrape_with_scraper

logger = logging.getLogger(__name__)

class ScraperAdapter:
    """爬虫适配器，统一不同爬虫的接口"""
    
    def __init__(self):
        self.scrapers = {
            'requests': 'requests',
        }
    
    def scrape_urls(self, urls: List[str], scraper_type: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """使用指定爬虫爬取URL列表 - 支持并发处理"""
        if scraper_type not in self.scrapers:
            raise ValueError(f"不支持的爬虫类型: {scraper_type}")
        
        logger.info(f"开始爬取任务: {len(urls)}个URL, 类型: {scraper_type}")
        
        try:
            # 阶段2只支持requests爬虫
            if scraper_type == 'requests':
                # 使用并发处理URL列表
                results = self._scrape_urls_concurrent(urls, scraper_type)
                
                successful_count = sum(1 for r in results if r.get('success', False))
                failed_count = len(results) - successful_count
                
                logger.info(f"爬取任务完成: 成功{successful_count}个, 失败{failed_count}个")
                return results
            else:
                raise ValueError(f"阶段2暂不支持爬虫类型: {scraper_type}")
                
        except Exception as e:
            logger.error(f"爬虫适配器错误: {str(e)}")
            raise
    
    def _scrape_urls_concurrent(self, urls: List[str], scraper_type: str) -> List[Dict[str, Any]]:
        """使用线程池并发爬取URL列表"""
        logger.info(f"使用并发模式爬取 {len(urls)} 个URL")
        
        # 根据URL数量动态调整线程池大小
        max_workers = min(len(urls), 10)  # 最多10个并发线程
        results = [None] * len(urls)  # 预分配结果列表，保持顺序
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(scrape_with_scraper, url, scraper_type): i 
                for i, url in enumerate(urls)
            }
            
            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result(timeout=35)  # 单个URL超时35秒
                    results[index] = result
                    completed_count += 1
                    
                    # 记录进度
                    if completed_count % 5 == 0 or completed_count == len(urls):
                        logger.info(f"并发爬取进度: {completed_count}/{len(urls)}")
                        
                except Exception as e:
                    logger.error(f"URL爬取失败 [{index}]: {urls[index]} - {str(e)}")
                    results[index] = {
                        'url': urls[index],
                        'success': False,
                        'title': None,
                        'content': None,
                        'publish_date': None,
                        'error': str(e),
                        'scraper_type': scraper_type
                    }
                    completed_count += 1
        
        # 检查是否有None结果（理论上不应该有）
        none_results = [i for i, r in enumerate(results) if r is None]
        if none_results:
            logger.error(f"发现 {len(none_results)} 个未处理的结果，索引: {none_results}")
        
        logger.info(f"并发爬取完成: 处理了 {completed_count} 个URL")
        return results
    
    def get_supported_scrapers(self) -> List[str]:
        """获取支持的爬虫类型列表"""
        return list(self.scrapers.keys())

# 创建全局适配器实例
scraper_adapter = ScraperAdapter()