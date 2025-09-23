#!/usr/bin/env python3
"""
Trafilatura Web Scraper
基于Trafilatura库的内容提取爬虫实现
"""

import os
import json
import time
import datetime
import trafilatura
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List
from urllib.parse import urlparse

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class TrafilaturaScraper(BaseScraper):
    """Trafilatura爬虫"""
    
    def __init__(self):
        super().__init__("trafilatura")
        self.logger = get_logger(__name__)
        self.lock = threading.Lock()
        self.scraped_count = 0
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        return self.scrape_with_trafilatura(url)
    
    def scrape_with_trafilatura(self, url: str) -> Dict:
        """使用Trafilatura进行内容提取"""
        try:
            self.logger.debug(f"开始使用Trafilatura爬取: {url}")
            
            # 下载页面内容
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {
                    'url': url,
                    'website_type': self.detect_website_type(url),
                    'error': 'Failed to download URL',
                    'method': 'trafilatura',
                    'success': False
                }
            
            # 使用Trafilatura提取内容
            if 'zh' in url or 'cn' in url:
                # 中文内容
                result = trafilatura.extract(downloaded, url=url, target_language='zh', include_comments=False, include_tables=False, include_images=False)
            else:
                # 英文内容
                result = trafilatura.extract(downloaded, url=url, target_language='en', include_comments=False, include_tables=False, include_images=False)
            
            if not result:
                return {
                    'url': url,
                    'website_type': self.detect_website_type(url),
                    'error': 'No meaningful content extracted',
                    'method': 'trafilatura',
                    'success': False
                }
            
            # 使用Trafilatura提取元数据
            metadata = trafilatura.extract_metadata(downloaded)
            
            # 解析提取的内容
            title = ""
            description = ""
            content = ""
            
            if result:
                lines = result.split('\n')
                if lines:
                    title = lines[0].strip() if lines[0].strip() else ""
                    if len(lines) > 1:
                        # 假设第二行可能是简短描述
                        potential_desc = lines[1].strip()
                        if len(potential_desc) < 200 and len(potential_desc) > 10:
                            description = potential_desc
                    # 剩余内容作为正文
                    content = '\n'.join(lines[1:]).strip()
            
            # 如果内容太短，尝试其他提取方法
            if len(content) < 100:
                # 使用更宽松的提取参数
                loose_result = trafilatura.extract(downloaded, url=url, include_comments=True, include_tables=True)
                if loose_result and len(loose_result) > len(content):
                    content = loose_result
            
            final_result = {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'website_type': self.detect_website_type(url),
                'method': 'trafilatura',
                'metadata': {
                    'author': metadata.author if metadata else None,
                    'date': metadata.date if metadata else None,
                    'sitename': metadata.sitename if metadata else None,
                    'title_meta': metadata.title if metadata else None,
                },
                'success': bool(content and len(content) > 100)
            }
            
            self.logger.debug(f"Trafilatura爬取完成: {url} - {'成功' if final_result['success'] else '失败'}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Trafilatura爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': self.detect_website_type(url),
                'error': str(e),
                'method': 'trafilatura',
                'success': False
            }
    
    def scrape_url_with_thread(self, url_data):
        """在线程中爬取单个URL"""
        url, index, total = url_data
        
        try:
            self.logger.info(f"线程 {threading.current_thread().name}: 处理URL {index}/{total} - {url}")
            result = self.scrape_with_trafilatura(url)
            
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
                'method': 'trafilatura',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 5) -> Dict[str, Dict]:
        """批量爬取多个URL"""
        self.logger.info(f"开始Trafilatura多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
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
                        'method': 'trafilatura',
                        'success': False
                    }
        
        self.logger.info(f"Trafilatura爬取完成，共处理{len(all_results)}个URL")
        return all_results