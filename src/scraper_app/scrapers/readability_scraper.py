#!/usr/bin/env python3
"""
Readability Web Scraper
基于Readability库的内容提取爬虫实现
"""

import os
import json
import time
import datetime
import requests
from readability import Document
import html2text
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List
from urllib.parse import urlparse

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class ReadabilityScraper(BaseScraper):
    """Readability爬虫"""
    
    def __init__(self):
        super().__init__("readability")
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.lock = threading.Lock()
        self.scraped_count = 0
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = True
        self.html2text.ignore_images = True
        self.html2text.ignore_tables = True
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        return self.scrape_with_readability(url)
    
    def scrape_with_readability(self, url: str) -> Dict:
        """使用Readability进行内容提取"""
        try:
            self.logger.debug(f"开始使用Readability爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 使用Readability解析文档
            doc = Document(response.text)
            
            # 提取标题
            title = doc.title()
            
            # 提取主要内容（HTML格式）
            content_html = doc.summary()
            
            # 转换为纯文本
            content_text = self.html2text.handle(content_html)
            
            # 清理文本
            content_text = ' '.join(content_text.split())
            
            result = {
                'url': url,
                'title': title or '',
                'description': '',  # Readability不直接提供meta描述
                'content': content_text,
                'website_type': self.detect_website_type(url),
                'method': 'readability',
                'content_html': content_html,  # 保留HTML版本
                'status_code': response.status_code,
                'success': bool(content_text and len(content_text) > 100)
            }
            
            self.logger.debug(f"Readability爬取完成: {url} - {'成功' if result['success'] else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Readability爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': self.detect_website_type(url),
                'error': str(e),
                'method': 'readability',
                'success': False
            }
    
    def scrape_url_with_thread(self, url_data):
        """在线程中爬取单个URL"""
        url, index, total = url_data
        
        try:
            self.logger.info(f"线程 {threading.current_thread().name}: 处理URL {index}/{total} - {url}")
            result = self.scrape_with_readability(url)
            
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
                'method': 'readability',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 5) -> Dict[str, Dict]:
        """批量爬取多个URL"""
        self.logger.info(f"开始Readability多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
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
                        'method': 'readability',
                        'success': False
                    }
        
        self.logger.info(f"Readability爬取完成，共处理{len(all_results)}个URL")
        return all_results