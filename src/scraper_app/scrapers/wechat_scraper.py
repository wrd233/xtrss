#!/usr/bin/env python3
"""
WeChat Article Scraper
微信公众号文章专用爬虫实现
"""

import os
import json
import time
import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List

from scraper_app.scrapers.base_scraper import BaseScraper
from scraper_app.utils.logger import get_logger

class WeChatScraper(BaseScraper):
    """微信爬虫"""
    
    def __init__(self):
        super().__init__("wechat")
        self.logger = get_logger(__name__)
        self.ua = UserAgent()
        self.max_workers = 2  # 微信爬虫使用较少的工作线程，避免被封
        self.lock = threading.Lock()
        self.scraped_count = 0
        
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
        return self.scrape_with_wechat_method(url)
    
    def scrape_with_wechat_method(self, url: str) -> Dict:
        """微信文章专用爬取方法"""
        driver = None
        try:
            self.logger.debug(f"开始爬取微信文章: {url}")
            
            # 验证是否为微信URL
            if 'weixin.qq.com' not in url and 'mp.weixin.qq.com' not in url:
                return {
                    'url': url,
                    'website_type': 'wechat',
                    'error': 'Not a WeChat URL',
                    'method': 'wechat_selenium',
                    'success': False
                }
            
            driver = self.get_selenium_driver()
            if not driver:
                return {
                    'url': url,
                    'website_type': 'wechat',
                    'error': 'Failed to create Selenium driver',
                    'method': 'wechat_selenium',
                    'success': False
                }
            
            # 导航到页面
            driver.get(url)
            
            # 等待页面加载 - 微信文章页面特殊处理
            try:
                # 等待文章内容加载
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "rich_media_content"))
                )
            except TimeoutException:
                self.logger.warning(f"微信文章内容加载超时: {url}")
                # 尝试其他选择器
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except TimeoutException:
                    self.logger.error(f"微信页面完全加载超时: {url}")
            
            # 等待额外时间让动态内容加载
            time.sleep(3)
            
            # 获取页面源代码
            page_source = driver.page_source
            
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 微信文章特定的内容提取
            title = ""
            content = ""
            author = ""
            publish_time = ""
            
            # 提取标题
            title_selectors = [
                'h1.rich_media_title',
                'h2.rich_media_title', 
                '.rich_media_title',
                'title',
                'h1',
                'h2'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    if title:
                        break
            
            # 提取作者
            author_selectors = [
                '.rich_media_meta_text',
                '.rich_media_meta_nickname',
                '.profile_nickname',
                '.account_nickname_inner'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text().strip()
                    if author:
                        break
            
            # 提取发布时间
            time_selectors = [
                '.rich_media_meta_list em',
                '.rich_media_meta_text em',
                '.publish_time',
                'time'
            ]
            
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    publish_time = time_elem.get_text().strip()
                    if publish_time:
                        break
            
            # 提取主要内容
            content_selectors = [
                '.rich_media_content',
                '#js_content',
                '.rich_media_area_primary_inner',
                'article',
                '.article_content',
                '.content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除不需要的元素
                    for unwanted in content_elem.find_all(['script', 'style', 'iframe', 'noscript']):
                        unwanted.decompose()
                    
                    # 获取文本内容
                    content = content_elem.get_text(separator=' ', strip=True)
                    if len(content) > 100:  # 确保内容长度足够
                        break
            
            # 如果主要内容提取失败，尝试使用Selenium直接获取文本
            if not content or len(content) < 100:
                try:
                    # 尝试微信特定的内容区域
                    content_elements = driver.find_elements(By.CSS_SELECTOR, '.rich_media_content')
                    if content_elements:
                        content = content_elements[0].text
                    else:
                        # 回退到body文本
                        body_element = driver.find_element(By.TAG_NAME, 'body')
                        content = body_element.text
                        
                        # 清理微信特定的无关内容
                        if '分享到朋友圈' in content:
                            content = content.split('分享到朋友圈')[0]
                        if '阅读原文' in content:
                            content = content.split('阅读原文')[0]
                except:
                    pass
            
            # 最终内容清理
            if content:
                content = ' '.join(content.split())  # 标准化空白字符
            
            result = {
                'url': url,
                'title': title,
                'description': '',  # 微信文章通常没有meta description
                'content': content,
                'website_type': 'wechat',
                'method': 'wechat_selenium',
                'author': author,
                'publish_time': publish_time,
                'status_code': 200,
                'success': bool(content and len(content) > 100)
            }
            
            self.logger.debug(f"微信爬取完成: {url} - {'成功' if result['success'] else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"微信爬取失败 {url}: {e}")
            return {
                'url': url,
                'website_type': 'wechat',
                'error': str(e),
                'method': 'wechat_selenium',
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
            result = self.scrape_with_wechat_method(url)
            
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
                'method': 'wechat_selenium',
                'success': False
            }
    
    def scrape_all_urls(self, urls: List[str], workers: int = 2) -> Dict[str, Dict]:  # 微信爬虫使用较少的工作线程
        """批量爬取多个URL"""
        self.logger.info(f"开始微信多线程爬取，共{len(urls)}个URL，使用{workers}个工作线程")
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
                        'method': 'wechat_selenium',
                        'success': False
                    }
        
        self.logger.info(f"微信爬取完成，共处理{len(all_results)}个URL")
        return all_results