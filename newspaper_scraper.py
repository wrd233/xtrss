#!/usr/bin/env python3
"""
Newspaper3k Web Scraper
Standalone version of the newspaper scraping method from scraper.py
"""

import os
import json
import time
import datetime
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class NewspaperScraper:
    def __init__(self):
        self.lock = threading.Lock()
        self.scraped_count = 0

    def detect_website_type(self, url):
        """Detect the type of website"""
        from urllib.parse import urlparse
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
                'method': 'newspaper3k',
                'success': bool(article.text and len(article.text) > 50)
            }
        except Exception as e:
            return {
                'error': str(e),
                'method': 'newspaper3k',
                'success': False
            }

    def scrape_url_with_thread(self, url_data):
        """Scrape a single URL with thread-safe logging"""
        url, index, total = url_data
        
        try:
            print(f"Thread {threading.current_thread().name}: Processing URL {index}/{total} - {url}")
            result = self.scrape_with_newspaper(url)
            
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
                'method': 'newspaper3k',
                'success': False
            }

    def scrape_all_urls(self, urls, max_workers=5):
        """Scrape multiple URLs using multi-threading"""
        print(f"Starting multi-threaded scraping of {len(urls)} URLs with {max_workers} workers using Newspaper3k")
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
                        'method': 'newspaper3k',
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
        website_type = NewspaperScraper().detect_website_type(url)
        detailed_result = {
            'url': url,
            'website_type': website_type,
            'success': result.get('success', False),
            'method': result.get('method', 'newspaper3k'),
            'title': result.get('title', ''),
            'content_length': len(result.get('content', '')),
            'author': result.get('author', ''),
            'date': result.get('date', ''),
            'top_image': result.get('top_image', ''),
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
    print("🕷️  Newspaper3k Web Scraper")
    print("="*60)
    
    # Create results directory
    results_dir = "newspaper_results"
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
    
    print(f"Starting to crawl {len(urls)} URLs with Newspaper3k...")
    start_time = datetime.datetime.now()
    
    # Initialize scraper and scrape all URLs
    scraper = NewspaperScraper()
    results = scraper.scrape_all_urls(urls, max_workers=5)
    
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
    scraper = NewspaperScraper()
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