#!/usr/bin/env python3
"""
Selenium Web Scraper
Standalone version of the selenium scraping method from scraper.py
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

class SeleniumScraper:
    def __init__(self, max_workers=3):  # Fewer workers for Selenium due to resource usage
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
                        print(f"Failed to create driver with {path}: {e}")
                        continue
            
            # If no specific chromedriver found, try default
            if not driver:
                driver = webdriver.Chrome(options=chrome_options)
            
            return driver
        except Exception as e:
            print(f"Error creating Selenium driver: {e}")
            return None
    
    def detect_website_type(self, url):
        """Detect the type of website"""
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

    def scrape_with_selenium(self, url):
        """Use Selenium for JavaScript-heavy sites"""
        driver = None
        try:
            driver = self.get_selenium_driver()
            if not driver:
                return {
                    'error': 'Failed to create Selenium driver',
                    'method': 'selenium',
                    'success': False
                }
            
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
                print(f"Content elements not found for {url}, continuing anyway")
            
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
                'url': driver.current_url,
                'success': bool(content and len(content) > 100)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'method': 'selenium',
                'success': False
            }
        finally:
            if driver:
                driver.quit()

    def scrape_url_with_thread(self, url_data):
        """Scrape a single URL with thread-safe logging"""
        url, index, total = url_data
        
        try:
            print(f"Thread {threading.current_thread().name}: Processing URL {index}/{total} - {url}")
            result = self.scrape_with_selenium(url)
            
            with self.lock:
                self.scraped_count += 1
                current_count = self.scraped_count
            
            print(f"Thread {threading.current_thread().name}: Completed {current_count}/{total} - {url} - {'SUCCESS' if result['success'] else 'FAILED'}")
            
            return url, result
            
        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Error processing {url}: {e}")
            return url, {
                'url': url,
                'website_type': 'unknown',
                'error': str(e),
                'method': 'selenium',
                'success': False
            }

    def scrape_all_urls(self, urls, max_workers=None):
        """Scrape multiple URLs using multi-threading"""
        if max_workers is None:
            max_workers = self.max_workers
            
        print(f"Starting multi-threaded scraping of {len(urls)} URLs with {max_workers} workers using Selenium")
        all_results = {}
        
        # Prepare URL data with indices
        url_data = [(url, i+1, len(urls)) for i, url in enumerate(urls)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                    print(f"Exception processing {url}: {e}")
                    all_results[url] = {
                        'url': url,
                        'website_type': 'unknown',
                        'error': str(e),
                        'method': 'selenium',
                        'success': False
                    }
        
        return all_results

def save_individual_results(results, output_dir):
    """Save individual results for each website"""
    os.makedirs(output_dir, exist_ok=True)
    
    for url, data in results.items():
        # Create filename from URL
        filename = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('=', '_').replace('&', '_') + '.json'
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Error saving {filename}: {e}")

def create_detailed_report(results, report_path):
    """Create detailed report with success/failure analysis"""
    report = {
        'metadata': {
            'generated_at': datetime.datetime.now().isoformat(),
            'total_urls': len(results),
            'successful_scrapes': sum(1 for r in results.values() if r.get('success', False)),
            'failed_scrapes': sum(1 for r in results.values() if not r.get('success', False))
        },
        'detailed_results': []
    }
    
    for url, result in results.items():
        website_type = SeleniumScraper().detect_website_type(url)
        detailed_result = {
            'url': url,
            'website_type': website_type,
            'success': result.get('success', False),
            'method': result.get('method', 'selenium'),
            'title': result.get('title', ''),
            'content_length': len(result.get('content', '')),
            'final_url': result.get('url', ''),
            'error': result.get('error', '')
        }
        
        report['detailed_results'].append(detailed_result)
    
    # Save report
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Detailed report saved: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return report

def main():
    """Main function"""
    print("🕷️  Selenium Web Scraper")
    print("="*60)
    
    # Create results directory
    results_dir = "selenium_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Load URLs
    try:
        with open('webs.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(urls)} URLs from webs.txt")
    except FileNotFoundError:
        print("❌ webs.txt not found")
        return
    except Exception as e:
        print(f"❌ Error reading webs.txt: {e}")
        return
    
    print(f"Starting to crawl {len(urls)} URLs with Selenium...")
    print("⚠️  Note: Selenium scraping is slower due to browser automation")
    start_time = datetime.datetime.now()
    
    # Initialize scraper and scrape all URLs
    scraper = SeleniumScraper(max_workers=3)  # Use fewer workers for Selenium
    results = scraper.scrape_all_urls(urls)
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Save individual results
    print("\nSaving individual results...")
    save_individual_results(results, os.path.join(results_dir, "articles"))
    
    # Create detailed report
    print("\nCreating detailed report...")
    report_path = os.path.join(results_dir, "crawling_report.json")
    report = create_detailed_report(results, report_path)
    
    # Print summary
    successful = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"CRAWLING COMPLETED")
    print(f"{'='*60}")
    print(f"Total URLs processed: {total}")
    print(f"Successful scrapes: {successful}")
    print(f"Failed scrapes: {total - successful}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Average time per URL: {duration/total:.2f} seconds")
    print(f"Results saved to: {results_dir}/")
    print(f"Detailed report: {report_path}")
    print(f"{'='*60}")
    
    # Print website type summary
    scraper = SeleniumScraper()
    type_stats = {}
    for url in results.keys():
        wtype = scraper.detect_website_type(url)
        if wtype not in type_stats:
            type_stats[wtype] = {'total': 0, 'success': 0}
        type_stats[wtype]['total'] += 1
        if results[url].get('success', False):
            type_stats[wtype]['success'] += 1
    
    print("\nWebsite Type Summary:")
    for wtype, stats in type_stats.items():
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {wtype}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

if __name__ == "__main__":
    main()