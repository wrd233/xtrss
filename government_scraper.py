#!/usr/bin/env python3
"""
Government Website Scraper
Standalone version of the government specialized scraping method from scraper.py
"""

import os
import json
import time
import datetime
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class GovernmentScraper:
    def __init__(self, max_workers=5):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.scraped_count = 0

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
                'method': 'government_specialized',
                'status_code': response.status_code,
                'success': bool(content and len(content) > 50)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'method': 'government_specialized',
                'success': False
            }

    def scrape_url_with_thread(self, url_data):
        """Scrape a single URL with thread-safe logging"""
        url, index, total = url_data
        
        # Check if it's a government URL
        if 'gov.cn' not in url:
            print(f"Thread {threading.current_thread().name}: Skipping {url} - Not a government URL")
            return url, {
                'url': url,
                'website_type': 'non_government',
                'error': 'Not a government website URL',
                'method': 'government_specialized',
                'success': False
            }
        
        try:
            print(f"Thread {threading.current_thread().name}: Processing government URL {index}/{total} - {url}")
            result = self.scrape_government_site(url)
            
            with self.lock:
                self.scraped_count += 1
                current_count = self.scraped_count
            
            print(f"Thread {threading.current_thread().name}: Completed {current_count}/{total} - {url} - {'SUCCESS' if result['success'] else 'FAILED'}")
            
            return url, result
            
        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Error processing {url}: {e}")
            return url, {
                'url': url,
                'website_type': 'government',
                'error': str(e),
                'method': 'government_specialized',
                'success': False
            }

    def scrape_all_urls(self, urls, max_workers=None):
        """Scrape multiple URLs using multi-threading"""
        if max_workers is None:
            max_workers = self.max_workers
            
        # Filter only government URLs
        gov_urls = [url for url in urls if 'gov.cn' in url]
        non_gov_urls = [url for url in urls if url not in gov_urls]
        
        if non_gov_urls:
            print(f"Skipping {len(non_gov_urls)} non-government URLs")
        
        if not gov_urls:
            print("No government URLs found to process")
            return {}
            
        print(f"Starting multi-threaded scraping of {len(gov_urls)} government URLs with {max_workers} workers")
        all_results = {}
        
        # Prepare URL data with indices
        url_data = [(url, i+1, len(gov_urls)) for i, url in enumerate(gov_urls)]
        
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
                        'website_type': 'government',
                        'error': str(e),
                        'method': 'government_specialized',
                        'success': False
                    }
        
        # Add results for non-government URLs
        for url in non_gov_urls:
            all_results[url] = {
                'url': url,
                'website_type': 'non_government',
                'error': 'Not a government website URL',
                'method': 'government_specialized',
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
            'method': result.get('method', 'government_specialized'),
            'title': result.get('title', ''),
            'content_length': len(result.get('content', '')),
            'error': result.get('error', ''),
            'status_code': result.get('status_code', 0)
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
    print("🕷️  Government Website Scraper")
    print("="*60)
    
    # Create results directory
    results_dir = "government_results"
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
    
    print(f"Starting to crawl government websites from {len(urls)} URLs...")
    print("⚠️  Note: Only government URLs (gov.cn) will be processed")
    start_time = datetime.datetime.now()
    
    # Initialize scraper and scrape all URLs
    scraper = GovernmentScraper(max_workers=5)
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
    gov_attempts = sum(1 for r in results.values() if r.get('website_type') == 'government')
    
    print(f"\n{'='*60}")
    print(f"CRAWLING COMPLETED")
    print(f"{'='*60}")
    print(f"Total URLs processed: {total}")
    print(f"Government URLs attempted: {gov_attempts}")
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