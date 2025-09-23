#!/usr/bin/env python3
"""
调度器 - 负责协调和管理所有爬虫任务
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

from scraper_app.scrapers.requests_scraper import RequestsScraper
from scraper_app.scrapers.government_scraper import GovernmentScraper
from scraper_app.scrapers.newspaper_scraper import NewspaperScraper
from scraper_app.scrapers.readability_scraper import ReadabilityScraper
from scraper_app.scrapers.selenium_scraper import SeleniumScraper
from scraper_app.scrapers.trafilatura_scraper import TrafilaturaScraper
from scraper_app.scrapers.wechat_scraper import WeChatScraper
from scraper_app.reporting.generator import ReportGenerator
from scraper_app.utils.logger import get_logger

class ScraperDispatcher:
    """爬虫调度器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.scrapers = {
            'requests': RequestsScraper(),
            'government': GovernmentScraper(),
            'newspaper': NewspaperScraper(),
            'readability': ReadabilityScraper(),
            'selenium': SeleniumScraper(),
            'trafilatura': TrafilaturaScraper(),
            'wechat': WeChatScraper()
        }
        self.report_generator = ReportGenerator()
    
    def load_urls(self, input_file: str) -> List[str]:
        """加载URL列表"""
        try:
            input_path = Path(input_file)
            if not input_path.is_absolute():
                # 相对路径，基于当前工作目录（Docker中的/app）
                input_path = Path.cwd() / input_file
            
            self.logger.info(f"尝试加载文件: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"成功加载 {len(urls)} 个URL")
            return urls
        except FileNotFoundError:
            self.logger.error(f"输入文件不存在: {input_file} (路径: {input_path.absolute()})")
            raise
        except Exception as e:
            self.logger.error(f"加载URL失败: {e}")
            raise
    
    def run(self, scraper_type: str, input_file: str, output_dir: str, workers: int = 5) -> Dict:
        """运行爬虫任务"""
        self.logger.info(f"开始执行爬虫任务: {scraper_type}")
        
        # 加载URL
        urls = self.load_urls(input_file)
        if not urls:
            self.logger.warning("没有可爬取的URL")
            return {}
        
        # 获取爬虫实例
        scraper = self.scrapers.get(scraper_type)
        if not scraper:
            raise ValueError(f"不支持的爬虫类型: {scraper_type}")
        
        # 执行爬取
        start_time = datetime.datetime.now()
        results = scraper.scrape_all_urls(urls, workers)
        end_time = datetime.datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # 保存结果
        self._save_results(results, output_dir)
        
        # 生成报告
        self._generate_report(results, output_dir, duration)
        
        return results
    
    def _save_results(self, results: Dict, output_dir: str):
        """保存爬取结果"""
        articles_dir = Path(output_dir) / "articles"
        articles_dir.mkdir(parents=True, exist_ok=True)
        
        for url, data in results.items():
            # 使用URL哈希值作为文件名
            import hashlib
            filename = hashlib.md5(url.encode()).hexdigest() + '.json'
            filepath = articles_dir / filename
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.logger.error(f"保存结果失败 {url}: {e}")
        
        self.logger.info(f"结果已保存到: {articles_dir}")
    
    def _generate_report(self, results: Dict, output_dir: str, duration: float):
        """生成爬取报告"""
        report_path = Path(output_dir) / "crawling_report.json"
        
        report_data = self.report_generator.generate_report(results, duration)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"报告已生成: {report_path}")
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
        
        # 同时生成执行摘要
        summary_path = Path(output_dir) / "execution_summary.md"
        self.report_generator.generate_summary(report_data, summary_path)