#!/usr/bin/env python3
"""
WeChat Article Scraper
Standalone version of the WeChat specialized scraping method from scraper.py
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
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class WeChatScraper:
    def __init__(self, max_workers=2):  # Fewer workers for Selenium due to resource usage
        self.ua = UserAgent()
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

    def scrape_wechat_article(self, url):
        """Specialized scraping for WeChat articles"""
        driver = None
        try:
            driver = self.get_selenium_driver()
            if not driver:
                return {
                    'error': 'Failed to create Selenium driver',
                    'method': 'wechat_selenium',
                    'success': False
                }
            
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
                'method': 'wechat_selenium',
                'success': bool(content and len(content) > 50)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'method': 'wechat_selenium',
                'success': False
            }
        finally:
            if driver:
                driver.quit()

    def scrape_url_with_thread(self, url_data):
        """Scrape a single URL with thread-safe logging"""
        url, index, total = url_data
        
        # Check if it's a WeChat URL
        if 'weixin.qq.com' not in url and 'mp.weixin.qq.com' not in url:
            print(f"Thread {threading.current_thread().name}: Skipping {url} - Not a WeChat URL")
            return url, {
                'url': url,
                'website_type': 'non_wechat',
                'error': 'Not a WeChat article URL',
                'method': 'wechat_selenium',
                'success': False
            }
        
        try:
            print(f"Thread {threading.current_thread().name}: Processing WeChat URL {index}/{total} - {url}")
            result = self.scrape_wechat_article(url)
            
            with self.lock:
                self.scraped_count += 1
                current_count = self.scraped_count
            
            print(f"Thread {threading.current_thread().name}: Completed {current_count}/{total} - {url} - {'SUCCESS' if result['success'] else 'FAILED'}")
            
            return url, result
            
        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Error processing {url}: {e}")
            return url, {
                'url': url,
                'website_type': 'wechat',
                'error': str(e),
                'method': 'wechat_selenium',
                'success': False
            }

    def scrape_all_urls(self, urls, max_workers=None):
        """Scrape multiple URLs using multi-threading"""
        if max_workers is None:
            max_workers = self.max_workers
            
        # Filter only WeChat URLs
        wechat_urls = [url for url in urls if 'weixin.qq.com' in url or 'mp.weixin.qq.com' in url]
        non_wechat_urls = [url for url in urls if url not in wechat_urls]
        
        if non_wechat_urls:
            print(f"Skipping {len(non_wechat_urls)} non-WeChat URLs")
        
        if not wechat_urls:
            print("No WeChat URLs found to process")
            return {}
            
        print(f"Starting multi-threaded scraping of {len(wechat_urls)} WeChat URLs with {max_workers} workers")
        all_results = {}
        
        # Prepare URL data with indices
        url_data = [(url, i+1, len(wechat_urls)) for i, url in enumerate(wechat_urls)]
        
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
                        'website_type': 'wechat',
                        'error': str(e),
                        'method': 'wechat_selenium',
                        'success': False
                    }
        
        # Add results for non-WeChat URLs
        for url in non_wechat_urls:
            all_results[url] = {
                'url': url,
                'website_type': 'non_wechat',
                'error': 'Not a WeChat article URL',
                'method': 'wechat_selenium',
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
        detailed_result = {
            'url': url,
            'website_type': result.get('website_type', 'unknown'),
            'success': result.get('success', False),
            'method': result.get('method', 'wechat_selenium'),
            'title': result.get('title', ''),
            'content_length': len(result.get('content', '')),
            'author': result.get('author', ''),
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
    print("🕷️  WeChat Article Scraper")
    print("="*60)
    
    # Create results directory
    results_dir = "wechat_results"
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
    
    print(f"Starting to crawl WeChat articles from {len(urls)} URLs...")
    print("⚠️  Note: Only WeChat URLs (weixin.qq.com or mp.weixin.qq.com) will be processed")
    start_time = datetime.datetime.now()
    
    # Initialize scraper and scrape all URLs
    scraper = WeChatScraper(max_workers=2)  # Use fewer workers for Selenium
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
    wechat_attempts = sum(1 for r in results.values() if r.get('website_type') == 'wechat')
    
    print(f"\n{'='*60}")
    print(f"CRAWLING COMPLETED")
    print(f"{'='*60}")
    print(f"Total URLs processed: {total}")
    print(f"WeChat URLs attempted: {wechat_attempts}")
    print(f"Successful scrapes: {successful}")
    print(f"Failed scrapes: {total - successful}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Average time per URL: {duration/total:.2f} seconds")
    print(f"Results saved to: {results_dir}/")
    print(f"Detailed report: {report_path}")
    print(f"{'='*60}")
    
    # Print website type summary
    type_stats = {}
    for result in results.values():
        wtype = result.get('website_type', 'unknown')
        if wtype not in type_stats:
            type_stats[wtype] = {'total': 0, 'success': 0}
        type_stats[wtype]['total'] += 1
        if result.get('success', False):
            type_stats[wtype]['success'] += 1
    
    print("\nWebsite Type Summary:")
    for wtype, stats in type_stats.items():
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {wtype}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

if __name__ == "__main__":
    main()