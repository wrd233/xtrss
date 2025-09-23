#!/usr/bin/env python3
"""
Requests + BeautifulSoup Web Scraper
基于requests和BeautifulSoup的爬虫实现
"""

import os
import re
import json
import time
import datetime
import requests
import threading
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class RequestsScraper(BaseScraper):
    """Requests + BeautifulSoup爬虫"""
    
    def __init__(self):
        super().__init__("requests")
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
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        return self.scrape_with_requests(url)
    
    def scrape_with_requests(self, url: str) -> Dict:
        """使用requests和BeautifulSoup爬取网页"""
        try:
            self.logger.debug(f"开始爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # 提取meta描述
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            # 提取主要内容
            content = ""
            
            # 尝试常见的内容选择器
            content_selectors = [
                'article', 'main', '.content', '.article-content', 
                '.post-content', '.entry-content', '#content',
                '.news-content', '.text-content', '.entry-body',
                '.post-body', '.article-body', '.main-content',
                '#main-content', '.story-content', '.post-text'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # 移除不需要的元素
                    for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    content = element.get_text(separator=' ', strip=True)
                    if len(content) > 200:  # 只接受内容充足的
                        break
            
            # 如果没有找到具体内容，尝试body但进行清理
            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    # 复制body避免修改原始内容
                    body_copy = BeautifulSoup(str(body), 'html.parser')
                    # 移除不需要的元素
                    for unwanted in body_copy.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
                        unwanted.decompose()
                    body_content = body_copy.get_text(separator=' ', strip=True)
                    if len(body_content) > len(content):
                        content = body_content
            
            result = {
                'url': url,
                'title': title_text,
                'description': description,
                'content': content,
                'website_type': self.detect_website_type(url),
                'method': 'requests_beautifulsoup',
                'status_code': response.status_code,
                'success': bool(content and len(content) > 100)
            }
            
            self.logger.debug(f"爬取完成: {url} - {'成功' if result['success'] else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': self.detect_website_type(url),
                'error': str(e),
                'method': 'requests_beautifulsoup',
                'success': False
            }
    
    def scrape_url_with_thread(self, url_data):
        """在线程中爬取单个URL"""
        url, index, total = url_data
        
        try:
            self.logger.info(f"线程 {threading.current_thread().name}: 处理URL {index}/{total} - {url}")
            result = self.scrape_with_requests(url)
            
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
                'method': 'requests_beautifulsoup',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 5) -> Dict[str, Dict]:
        """批量爬取多个URL"""
        self.logger.info(f"开始多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
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
                        'method': 'requests_beautifulsoup',
                        'success': False
                    }
        
        self.logger.info(f"爬取完成，共处理{len(all_results)}个URL")
        return all_results