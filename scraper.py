#!/usr/bin/env python3
"""
Web Scraper Module
Implements multiple scraping techniques for different types of websites
"""

import os
import re
import json
import time
import logging
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
import trafilatura
from newspaper import Article
from readability import Document
import html2text
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, max_workers=5):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.scraped_count = 0
        
    def get_selenium_driver(self):
        """Create and return a Selenium Chrome/Chromium driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-images')  # Disable images for faster loading
            chrome_options.add_argument('--disable-javascript')  # Try disabling JS first
            chrome_options.add_argument(f'user-agent={self.ua.random}')
            
            # Try different Chrome/Chromium binary locations
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
            
            # Try to use chromedriver from system or environment
            chromedriver_paths = [
                '/usr/bin/chromedriver',
                '/usr/bin/chromium-driver',
                '/usr/local/bin/chromedriver',
                os.environ.get('CHROMEDRIVER_PATH')
            ]
            
            driver = None
            for path in chromedriver_paths:
                if path and os.path.exists(path):
                    try:
                        from selenium.webdriver.chrome.service import Service
                        service = Service(path)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        break
                    except Exception as e:
                        logger.warning(f"Failed to create driver with {path}: {e}")
                        continue
            
            # If no specific chromedriver found, try default
            if not driver:
                driver = webdriver.Chrome(options=chrome_options)
            
            return driver
        except Exception as e:
            logger.error(f"Error creating Selenium driver: {e}")
            return None
    
    def detect_website_type(self, url):
        """Detect the type of website to apply appropriate scraping strategy"""
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
    
    def scrape_with_requests(self, url):
        """Basic requests + BeautifulSoup scraping"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extract meta description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            # Extract main content
            content = ""
            
            # Try common content selectors
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
                    # Remove unwanted elements
                    for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    content = element.get_text(separator=' ', strip=True)
                    if len(content) > 200:  # Only accept if content is substantial
                        break
            
            # If no specific content found, try body but clean it
            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    # Clone body to avoid modifying original
                    body_copy = BeautifulSoup(str(body), 'html.parser')
                    # Remove unwanted elements
                    for unwanted in body_copy.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
                        unwanted.decompose()
                    body_content = body_copy.get_text(separator=' ', strip=True)
                    if len(body_content) > len(content):
                        content = body_content
            
            return {
                'title': title_text,
                'description': description,
                'content': content,
                'method': 'requests_beautifulsoup',
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Requests scraping failed for {url}: {e}")
            return None
    
    def scrape_with_trafilatura(self, url):
        """Use Trafilatura for content extraction"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, with_metadata=True, include_comments=False)
                if result:
                    data = json.loads(result)
                    return {
                        'title': data.get('title', ''),
                        'description': data.get('description', ''),
                        'content': data.get('text', ''),
                        'author': data.get('author', ''),
                        'date': data.get('date', ''),
                        'method': 'trafilatura'
                    }
            return None
        except Exception as e:
            logger.error(f"Trafilatura scraping failed for {url}: {e}")
            return None
    
    def scrape_with_newspaper(self, url):
        """Use Newspaper3k for article extraction"""
        try:
            article = Article(url, language='zh' if 'cn' in url else 'en')
            article.download()
            article.parse()
            
            return {
                'title': article.title,
                'content': article.text,
                'author': ', '.join(article.authors) if article.authors else '',
                'date': str(article.publish_date) if article.publish_date else '',
                'top_image': article.top_image,
                'method': 'newspaper3k'
            }
        except Exception as e:
            logger.error(f"Newspaper scraping failed for {url}: {e}")
            return None
    
    def scrape_with_readability(self, url):
        """Use Readability for content extraction"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            doc = Document(response.content)
            
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            
            content = h.handle(doc.summary())
            
            return {
                'title': doc.title(),
                'content': content,
                'method': 'readability'
            }
        except Exception as e:
            logger.error(f"Readability scraping failed for {url}: {e}")
            return None
    
    def scrape_with_selenium(self, url):
        """Use Selenium for JavaScript-heavy sites"""
        driver = None
        try:
            driver = self.get_selenium_driver()
            if not driver:
                return None
            
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(5)
            
            # Try to wait for specific content elements
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article, main, .content, .article-content, .rich_media_content"))
                )
            except TimeoutException:
                logger.warning(f"Content elements not found for {url}, continuing anyway")
            
            # Get page source
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract content
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            content = ""
            content_selectors = [
                'article', 'main', '.content', '.article-content', 
                '.post-content', '.entry-content', '#content',
                '.news-content', '.text-content', '.rich_media_content',
                '.entry-body', '.post-body', '.article-body', 
                '.main-content', '#main-content', '.story-content'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Remove unwanted elements from each content element
                    for element in elements:
                        for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            unwanted.decompose()
                    
                    content = ' '.join([elem.get_text(separator=' ', strip=True) for elem in elements])
                    if len(content) > 200:  # Only accept substantial content
                        break
            
            # If no content found, try body
            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    # Clone body to avoid modifying original
                    body_copy = BeautifulSoup(str(body), 'html.parser')
                    # Remove unwanted elements
                    for unwanted in body_copy.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
                        unwanted.decompose()
                    body_content = body_copy.get_text(separator=' ', strip=True)
                    if len(body_content) > len(content):
                        content = body_content
            
            return {
                'title': title_text,
                'content': content,
                'method': 'selenium',
                'url': driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Selenium scraping failed for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def scrape_wechat_article(self, url):
        """Specialized scraping for WeChat articles"""
        try:
            driver = self.get_selenium_driver()
            if not driver:
                return None
            
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rich_media_content"))
            )
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract WeChat specific content
            title = soup.find('h1', class_='rich_media_title')
            title_text = title.get_text().strip() if title else ""
            
            content_div = soup.find('div', class_='rich_media_content')
            content = content_div.get_text(separator=' ', strip=True) if content_div else ""
            
            author = soup.find('span', class_='rich_media_meta rich_media_meta_text')
            author_text = author.get_text().strip() if author else ""
            
            return {
                'title': title_text,
                'content': content,
                'author': author_text,
                'method': 'wechat_selenium'
            }
            
        except Exception as e:
            logger.error(f"WeChat scraping failed for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def scrape_government_site(self, url):
        """Specialized scraping for government websites"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Government sites often have specific content areas
            content_selectors = [
                '.content', '.article-content', '#content', 
                '.TRS_Editor', '.Custom_UnionStyle',
                '.govcn_article', '.article'
            ]
            
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            return {
                'title': title_text,
                'content': content,
                'method': 'government_specialized'
            }
            
        except Exception as e:
            logger.error(f"Government site scraping failed for {url}: {e}")
            return None
    
    def scrape_url(self, url):
        """Scrape a single URL using multiple techniques"""
        logger.info(f"Scraping: {url}")
        
        website_type = self.detect_website_type(url)
        logger.info(f"Detected website type: {website_type}")
        
        results = {
            'url': url,
            'website_type': website_type,
            'attempts': [],
            'success': False,
            'final_content': None
        }
        
        # Try different scraping methods based on website type
        if website_type == 'wechat':
            # Try WeChat specialized scraping first
            wechat_result = self.scrape_wechat_article(url)
            if wechat_result:
                results['attempts'].append(wechat_result)
                results['success'] = True
                results['final_content'] = wechat_result
                return results
        
        elif website_type == 'government':
            # Try government specialized scraping
            gov_result = self.scrape_government_site(url)
            if gov_result:
                results['attempts'].append(gov_result)
                if gov_result.get('content'):
                    results['success'] = True
                    results['final_content'] = gov_result
                    return results
        
        # Try general methods
        methods = [
            ('trafilatura', self.scrape_with_trafilatura),
            ('newspaper', self.scrape_with_newspaper),
            ('readability', self.scrape_with_readability),
            ('requests', self.scrape_with_requests),
            ('selenium', self.scrape_with_selenium)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying method: {method_name}")
                result = method_func(url)
                
                if result:
                    result['attempt_method'] = method_name
                    results['attempts'].append(result)
                    
                    # Check if we got meaningful content
                    content = result.get('content', '')
                    title = result.get('title', '')
                    
                    # More lenient criteria for content quality
                    if content and len(content.strip()) > 50 and title and len(title.strip()) > 5:
                        results['success'] = True
                        results['final_content'] = result
                        logger.info(f"Success with {method_name} - Content length: {len(content)}, Title: {title[:50]}...")
                        break
                        
            except Exception as e:
                logger.error(f"Method {method_name} failed for {url}: {e}")
                continue
        
        return results
    
    def scrape_url_with_thread(self, url_data):
        """Scrape a single URL with thread-safe logging"""
        url, index, total = url_data
        
        try:
            logger.info(f"Thread {threading.current_thread().name}: Processing URL {index}/{total} - {url}")
            result = self.scrape_url(url)
            
            with self.lock:
                self.scraped_count += 1
                current_count = self.scraped_count
            
            logger.info(f"Thread {threading.current_thread().name}: Completed {current_count}/{total} - {url} - {'SUCCESS' if result['success'] else 'FAILED'}")
            
            return url, result
            
        except Exception as e:
            logger.error(f"Thread {threading.current_thread().name}: Error processing {url}: {e}")
            return url, {
                'url': url,
                'website_type': 'unknown',
                'attempts': [],
                'success': False,
                'final_content': None,
                'error': str(e)
            }
    
    def scrape_urls(self, urls):
        """Scrape multiple URLs using multi-threading"""
        logger.info(f"Starting multi-threaded scraping of {len(urls)} URLs with {self.max_workers} workers")
        all_results = {}
        
        # Prepare URL data with indices
        url_data = [(url, i+1, len(urls)) for i, url in enumerate(urls)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.scrape_url_with_thread, data): data[0] 
                for data in url_data
            }
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    url, result = future.result()
                    all_results[url] = result
                except Exception as e:
                    logger.error(f"Exception processing {url}: {e}")
                    all_results[url] = {
                        'url': url,
                        'website_type': 'unknown',
                        'attempts': [],
                        'success': False,
                        'final_content': None,
                        'error': str(e)
                    }
        
        logger.info(f"Multi-threaded scraping completed. Total results: {len(all_results)}")
        return all_results