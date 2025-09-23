#!/usr/bin/env python3
"""
Selenium Web Scraper
基于Selenium浏览器的爬虫实现，适用于JavaScript渲染的页面
"""

import os
import json
import time
import datetime
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class SeleniumScraper(BaseScraper):
    """Selenium爬虫"""
    
    def __init__(self):
        super().__init__("selenium")
        self.logger = get_logger(__name__)
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.lock = threading.Lock()
        self.scraped_count = 0
        
        # Selenium配置
        self.html2text = None  # 将在需要时导入
    
    def get_selenium_driver(self):
        """创建并返回Selenium Chrome/Chromium驱动"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-images')  # 禁用图片以加快加载速度
            chrome_options.add_argument('--disable-javascript')  # 先尝试禁用JS
            chrome_options.add_argument(f'user-agent={self.ua.random}')
            
            # 尝试不同的Chrome/Chromium二进制文件位置
            chromium_paths = [
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable'
            ]
            
            for path in chromium_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    break
            
            # 创建驱动
            driver = webdriver.Chrome(options=chrome_options)
            return driver
            
        except Exception as e:
            self.logger.error(f"创建Selenium驱动失败: {e}")
            return None
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        return self.scrape_with_selenium(url)
    
    def scrape_with_selenium(self, url: str) -> Dict:
        """使用Selenium进行页面爬取"""
        driver = None
        try:
            self.logger.debug(f"开始使用Selenium爬取: {url}")
            
            driver = self.get_selenium_driver()
            if not driver:
                return {
                    'url': url,
                    'website_type': self.detect_website_type(url),
                    'error': 'Failed to create Selenium driver',
                    'method': 'selenium',
                    'success': False
                }
            
            # 导航到页面
            driver.get(url)
            
            # 等待页面加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                self.logger.warning(f"页面加载超时: {url}")
            
            # 等待额外时间让动态内容加载
            time.sleep(2)
            
            # 获取页面源代码
            page_source = driver.page_source
            
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(page_source, 'html.parser')
            
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
            
            # 提取主要内容 - 使用多种选择器策略
            content = ""
            
            # Selenium友好的内容选择器
            content_selectors = [
                'article', 'main', '.content', '.article-content', 
                '.post-content', '.entry-content', '#content',
                '.news-content', '.text-content', '.entry-body',
                '.post-body', '.article-body', '.main-content',
                '#main-content', '.story-content', '.post-text',
                '.dynamic-content', '.rendered-content'  # 针对动态内容
            ]
            
            for selector in content_selectors:
                try:
                    # 尝试使用Selenium的find_element
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]  # 取第一个匹配的元素
                        content = element.text
                        if len(content) > 200:
                            break
                except:
                    # 如果Selenium方法失败，回退到BeautifulSoup
                    element = soup.select_one(selector)
                    if element:
                        # 移除不需要的元素
                        for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            unwanted.decompose()
                        content = element.get_text(separator=' ', strip=True)
                        if len(content) > 200:
                            break
            
            # 如果还是没有找到内容，尝试body
            if not content or len(content) < 200:
                try:
                    # 先尝试Selenium获取body文本
                    body_element = driver.find_element(By.TAG_NAME, 'body')
                    body_content = body_element.text
                    if len(body_content) > len(content):
                        content = body_content
                except:
                    # 回退到BeautifulSoup
                    body = soup.find('body')
                    if body:
                        body_copy = BeautifulSoup(str(body), 'html.parser')
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
                'method': 'selenium_webdriver',
                'status_code': 200,  # Selenium不返回HTTP状态码
                'success': bool(content and len(content) > 100)
            }
            
            self.logger.debug(f"Selenium爬取完成: {url} - {'成功' if result['success'] else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Selenium爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': self.detect_website_type(url),
                'error': str(e),
                'method': 'selenium_webdriver',
                'success': False
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def scrape_url_with_thread(self, url_data):
        """在线程中爬取单个URL"""
        url, index, total = url_data
        
        try:
            self.logger.info(f"线程 {threading.current_thread().name}: 处理URL {index}/{total} - {url}")
            result = self.scrape_with_selenium(url)
            
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
                'method': 'selenium_webdriver',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 3) -> Dict[str, Dict]:  # Selenium使用较少的工作线程
        """批量爬取多个URL"""
        self.logger.info(f"开始Selenium多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
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
                        'method': 'selenium_webdriver',
                        'success': False
                    }
        
        self.logger.info(f"Selenium爬取完成，共处理{len(all_results)}个URL")
        return all_results