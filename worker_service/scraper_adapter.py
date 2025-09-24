import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from config import Config

# 导入简单爬虫
from simple_scraper import scrape_urls

logger = logging.getLogger(__name__)

class ScraperAdapter:
    """爬虫适配器，统一不同爬虫的接口"""
    
    def __init__(self):
        self.scrapers = {
            'requests': 'requests',
        }
    
    def scrape_urls(self, urls: List[str], scraper_type: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """使用指定爬虫爬取URL列表"""
        if scraper_type not in self.scrapers:
            raise ValueError(f"不支持的爬虫类型: {scraper_type}")
        
        logger.info(f"开始爬取任务: {len(urls)}个URL, 类型: {scraper_type}")
        
        try:
            # 阶段2只支持requests爬虫
            if scraper_type == 'requests':
                results = scrape_urls(urls)
                
                successful_count = sum(1 for r in results if r.get('success', False))
                failed_count = len(results) - successful_count
                
                logger.info(f"爬取任务完成: 成功{successful_count}个, 失败{failed_count}个")
                return results
            else:
                raise ValueError(f"阶段2暂不支持爬虫类型: {scraper_type}")
                
        except Exception as e:
            logger.error(f"爬虫适配器错误: {str(e)}")
            raise
    
    def get_supported_scrapers(self) -> List[str]:
        """获取支持的爬虫类型列表"""
        return list(self.scrapers.keys())

# 创建全局适配器实例
scraper_adapter = ScraperAdapter()