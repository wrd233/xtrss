#!/usr/bin/env python3
"""
Complete Web Scraper Runner - Pure Python Version
Runs the complete scraping process using only standard library
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import os
import re
import time
import datetime
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.content_parts = []
        self.in_content = False
        self.content_tags = ['article', 'main', 'div', 'section', 'p']
        self.content_classes = ['content', 'article', 'post', 'entry', 'main', 'body', 'text']
        self.current_tag = []
        self.tag_attrs = []
        
    def handle_starttag(self, tag, attrs):
        self.current_tag.append(tag)
        self.tag_attrs.append(dict(attrs))
        
        # Check if this might be content
        if tag in self.content_tags:
            attrs_dict = dict(attrs)
            class_val = attrs_dict.get('class', '')
            id_val = attrs_dict.get('id', '')
            
            # Check if class or id suggests content
            for content_class in self.content_classes:
                if content_class in class_val.lower() or content_class in id_val.lower():
                    self.in_content = True
                    break
        
        if tag == 'title':
            self.in_title = True
    
    def handle_endtag(self, tag):
        if self.current_tag:
            self.current_tag.pop()
            self.tag_attrs.pop()
        
        if tag == 'title':
            self.in_title = False
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
            
        if self.in_title:
            self.title += data
        
        # Avoid script and style content
        if self.current_tag and self.current_tag[-1] not in ['script', 'style']:
            if self.in_content or len(self.content_parts) < 50:  # Collect more content
                self.content_parts.append(data)
    
    def get_content(self):
        title = self.title.strip()
        content = ' '.join(self.content_parts).strip()
        return title, content

def detect_website_type(url):
    """Detect the type of website"""
    domain = urllib.parse.urlparse(url).netloc.lower()
    
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
    elif 'news.66wz.com' in domain:
        return 'local_news'
    elif 'abcnews.go.com' in domain:
        return 'abc_news'
    elif 'cbsnews.com' in domain:
        return 'cbs_news'
    elif 'openai.com' in domain:
        return 'openai'
    elif 'usnews.com' in domain:
        return 'us_news'
    else:
        return 'general'

def scrape_with_basic_requests(url):
    """Basic HTTP request scraping"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        parser = SimpleHTMLParser()
        parser.feed(html)
        title, content = parser.get_content()
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content).strip()
        
        return {
            'title': title,
            'content': content,
            'method': 'basic_requests',
            'success': bool(content and len(content) > 100)  # 只要有正文内容就算成功，标题可选
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'method': 'basic_requests',
            'success': False
        }

def scrape_url(url):
    """Scrape a single URL"""
    print(f"Processing: {url}")
    website_type = detect_website_type(url)
    
    result = {
        'url': url,
        'website_type': website_type,
        'attempts': [],
        'success': False,
        'final_method': None,
        'final_content': None
    }
    
    # Try basic requests first
    basic_result = scrape_with_basic_requests(url)
    result['attempts'].append(basic_result)
    
    if basic_result['success']:
        result['success'] = True
        result['final_method'] = 'basic_requests'
        result['final_content'] = basic_result
        print(f"  ✓ Success with basic_requests - {len(basic_result['content'])} chars")
    else:
        print(f"  ✗ Failed with basic_requests: {basic_result.get('error', 'No meaningful content')}")
    
    return result

def scrape_all_urls(urls, max_workers=5):
    """Scrape all URLs using multi-threading"""
    print(f"Starting multi-threaded scraping of {len(urls)} URLs with {max_workers} workers")
    
    results = {}
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(scrape_url, url): url for url in urls}
        
        # Process completed tasks
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results[url] = result
                completed += 1
                print(f"Progress: {completed}/{len(urls)} completed")
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results[url] = {
                    'url': url,
                    'website_type': 'unknown',
                    'attempts': [],
                    'success': False,
                    'final_method': None,
                    'final_content': None,
                    'error': str(e)
                }
    
    return results

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
            'final_method': result.get('final_method', 'none'),
            'title': result.get('final_content', {}).get('title', '') if result.get('final_content') else '',
            'content_length': len(result.get('final_content', {}).get('content', '')) if result.get('final_content') else 0,
            'error': result.get('error', ''),
            'attempts_count': len(result.get('attempts', [])),
            'attempts_summary': []
        }
        
        # Add attempts summary
        for attempt in result.get('attempts', []):
            attempt_summary = {
                'method': attempt.get('method', 'unknown'),
                'success': attempt.get('success', False),
                'error': attempt.get('error', ''),
                'content_length': len(attempt.get('content', '')) if attempt.get('content') else 0
            }
            detailed_result['attempts_summary'].append(attempt_summary)
        
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
    print("🕷️  Complete Web Scraper - Pure Python Version")
    print("="*60)
    
    # Create results directory
    results_dir = "crawling_results"
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
    
    print(f"Starting to crawl {len(urls)} URLs...")
    start_time = datetime.datetime.now()
    
    # Scrape all URLs
    results = scrape_all_urls(urls, max_workers=3)  # Use fewer workers to be respectful
    
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