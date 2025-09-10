#!/usr/bin/env python3
"""
Web Scraping Project - Main Script
Attempts to scrape article content from various websites using multiple techniques
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from scraper import WebScraper
from report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_urls(filename='webs.txt'):
    """Load URLs from webs.txt file"""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
        logger.info(f"Loaded {len(urls)} URLs from {filename}")
    except FileNotFoundError:
        logger.error(f"File {filename} not found")
        return []
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return []
    return urls

def create_output_directories():
    """Create necessary output directories"""
    directories = ['output/articles', 'output/reports']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def main():
    """Main function to orchestrate the scraping process"""
    logger.info("Starting web scraping project")
    
    # Create output directories
    create_output_directories()
    
    # Load URLs
    urls = load_urls()
    if not urls:
        logger.error("No URLs to scrape. Exiting.")
        return
    
    # Initialize scraper with multi-threading
    max_workers = min(8, len(urls))  # Use up to 8 threads, but no more than URLs
    scraper = WebScraper(max_workers=max_workers)
    
    # Initialize report generator
    report_generator = ReportGenerator()
    
    # Scrape all URLs
    logger.info(f"Starting to scrape {len(urls)} URLs using {max_workers} threads")
    start_time = datetime.now()
    
    try:
        results = scraper.scrape_urls(urls)
        
        end_time = datetime.now()
        scraping_duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Scraping completed in {scraping_duration:.2f} seconds")
        
        # Calculate success rate
        successful_scrapes = sum(1 for result in results.values() if result.get('success', False))
        success_rate = (successful_scrapes / len(urls) * 100) if urls else 0
        
        logger.info(f"Success rate: {success_rate:.1f}% ({successful_scrapes}/{len(urls)})")
        
        # Save individual articles
        saved_articles = 0
        for url, data in results.items():
            if data.get('success'):
                # Create filename from URL
                filename = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('=', '_').replace('&', '_') + '.json'
                filepath = os.path.join('output/articles', filename)
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved article: {filename}")
                    saved_articles += 1
                except Exception as e:
                    logger.error(f"Error saving article {filename}: {e}")
        
        logger.info(f"Total articles saved: {saved_articles}")
        
        # Generate comprehensive report
        logger.info("Generating detailed scraping report")
        report = report_generator.generate_report(results)
        
        # Add performance metrics to report
        report['performance'] = {
            'scraping_duration_seconds': scraping_duration,
            'urls_per_second': len(urls) / scraping_duration if scraping_duration > 0 else 0,
            'articles_saved': saved_articles,
            'max_workers_used': max_workers
        }
        
        # Save JSON report
        report_filename = f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_filepath = os.path.join('output/reports', report_filename)
        
        try:
            with open(report_filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved JSON report: {report_filename}")
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
        
        # Generate HTML report
        html_report = report_generator.generate_html_report(report)
        html_filename = f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_filepath = os.path.join('output/reports', html_filename)
        
        try:
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_report)
            logger.info(f"Saved HTML report: {html_filename}")
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
        
        # Print summary to console
        print(f"\n{'='*60}")
        print(f"SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total URLs processed: {len(urls)}")
        print(f"Successful scrapes: {successful_scrapes}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Articles saved: {saved_articles}")
        print(f"Time taken: {scraping_duration:.2f} seconds")
        print(f"Speed: {len(urls) / scraping_duration:.2f} URLs/second")
        print(f"Reports generated:")
        print(f"  - JSON: {report_filename}")
        print(f"  - HTML: {html_filename}")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Critical error during scraping: {e}")
        print(f"Error: Scraping failed - {e}")
        return
    
    logger.info("Web scraping project completed successfully")

if __name__ == "__main__":
    main()