#!/usr/bin/env python3
"""
Newspaper3k Web Scraper
基于Newspaper3k库的文章提取爬虫实现
"""

import os
import json
import time
import datetime
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List
from urllib.parse import urlparse

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class NewspaperScraper(BaseScraper):
    """Newspaper3k爬虫"""
    
    def __init__(self):
        super().__init__("newspaper")
        self.logger = get_logger(__name__)
        self.lock = threading.Lock()
        self.scraped_count = 0
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        return self.scrape_with_newspaper(url)
    
    def scrape_with_newspaper(self, url: str) -> Dict:
        """使用Newspaper3k进行文章提取"""
        try:
            self.logger.debug(f"开始使用Newspaper3k爬取: {url}")
            
            article = Article(url, language='zh' if 'cn' in url else 'en')
            article.download()
            article.parse()
            
            # 如果文章没有标题或正文，标记为失败
            if not article.title and not article.text:
                return {
                    'url': url,
                    'website_type': self.detect_website_type(url),
                    'error': 'No meaningful content extracted',
                    'method': 'newspaper3k',
                    'success': False
                }
            
            result = {
                'url': url,
                'title': article.title or '',
                'description': article.meta_description or '',
                'content': article.text or '',
                'website_type': self.detect_website_type(url),
                'method': 'newspaper3k',
                'authors': article.authors or [],
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'top_image': article.top_image or '',
                'movies': article.movies or [],
                'success': bool(article.text and len(article.text) > 100)
            }
            
            self.logger.debug(f"Newspaper3k爬取完成: {url} - {'成功' if result['success'] else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Newspaper3k爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': self.detect_website_type(url),
                'error': str(e),
                'method': 'newspaper3k',
                'success': False
            }
    
    def scrape_url_with_thread(self, url_data):
        """在线程中爬取单个URL"""
        url, index, total = url_data
        
        try:
            self.logger.info(f"线程 {threading.current_thread().name}: 处理URL {index}/{total} - {url}")
            result = self.scrape_with_newspaper(url)
            
            with self.lock:
                self.scraped_count += 1
                current_count = self.scraped_count
            
            self.logger.info(f"线程 {threading.current_thread().name}: 完成 {current_count}/{total} - {url} - {'成功' if result['success'] else '失败'}")
            
            return url, result
            
        except Exception as e:
            self.logger.error(f"线程 {threading.current_thread().name}: 处理 {url} 出错: {e}")
            return url, {
                'url': url,
                'website_type': 'unknown',
                'error': str(e),
                'method': 'newspaper3k',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 5) -> Dict[str, Dict]:
        """批量爬取多个URL"""
        self.logger.info(f"开始Newspaper3k多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
        all_results = {}
        
        # 准备URL数据（带索引）
        url_data = [(url, i+1, len(urls)) for i, url in enumerate(urls)]
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.scrape_url_with_thread, data): data[0] 
                for data in url_data
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    url, result = future.result()
                    all_results[url] = result
                except Exception as e:
                    self.logger.error(f"处理 {url} 异常: {e}")
                    all_results[url] = {
                        'url': url,
                        'website_type': 'unknown',
                        'error': str(e),
                        'method': 'newspaper3k',
                        'success': False
                    }
        
        self.logger.info(f"Newspaper3k爬取完成，共处理{len(all_results)}个URL")
        return all_results