#!/usr/bin/env python3
"""
爬虫基类 - 定义所有爬虫的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List

class BaseScraper(ABC):
    """爬虫基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL
        
        Args:
            url: 要爬取的URL
            
        Returns:
            Dict: 爬取结果，必须包含success字段
        """
        pass
    
    @abstractmethod
    def scrape_all_urls(self, urls: List[str], workers: int = 5) -> Dict[str, Dict]:
        """批量爬取多个URL
        
        Args:
            urls: URL列表
            workers: 并发线程数
            
        Returns:
            Dict: URL到结果的映射
        """
        pass
    
    def detect_website_type(self, url: str) -> str:
        """检测网站类型
        
        Args:
            url: 网站URL
            
        Returns:
            str: 网站类型
        """
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        
        if 'weixin.qq.com' in domain or 'mp.weixin.qq.com' in domain:
            return 'wechat'
        elif 'gov.cn' in domain:
            return 'government'
        elif 'ieee.org' in domain:
            return 'academic'
        elif 'jos.org.cn' in domain:
            return 'journal'
        elif 'baijiahao.baidu.com' in domain:
            return 'baidu_baijiahao'
        elif 'thepaper.cn' in domain:
            return 'thepaper'
        elif 'sohu.com' in domain:
            return 'sohu'
        elif 'news.cctv.com' in domain:
            return 'cctv'
        elif 'bjnews.com.cn' in domain:
            return 'bjnews'
        else:
            return 'general'