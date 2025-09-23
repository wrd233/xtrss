#!/usr/bin/env python3
"""
报告生成器 - 生成爬取结果的详细报告
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List

from scraper_app.utils.logger import get_logger

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def generate_report(self, results: Dict, duration: float) -> Dict:
        """生成详细报告"""
        self.logger.info("开始生成爬取报告")
        
        report = {
            'metadata': {
                'generated_at': datetime.datetime.now().isoformat(),
                'total_urls': len(results),
                'successful_scrapes': sum(1 for r in results.values() if r.get('success', False)),
                'failed_scrapes': sum(1 for r in results.values() if not r.get('success', False)),
                'duration_seconds': duration,
                'average_time_per_url': duration / len(results) if results else 0
            },
            'summary': {},
            'detailed_results': []
        }
        
        # 按网站类型统计
        type_stats = {}
        for url, result in results.items():
            wtype = result.get('website_type', 'unknown')
            if wtype not in type_stats:
                type_stats[wtype] = {'total': 0, 'success': 0}
            type_stats[wtype]['total'] += 1
            if result.get('success', False):
                type_stats[wtype]['success'] += 1
        
        report['summary']['website_types'] = type_stats
        
        # 详细结果
        for url, result in results.items():
            detailed_result = {
                'url': url,
                'website_type': result.get('website_type', 'unknown'),
                'success': result.get('success', False),
                'method': result.get('method', 'requests_beautifulsoup'),
                'title': result.get('title', ''),
                'description': result.get('description', ''),
                'content_length': len(result.get('content', '')),
                'error': result.get('error', ''),
                'status_code': result.get('status_code', 0)
            }
            
            report['detailed_results'].append(detailed_result)
        
        self.logger.info("爬取报告生成完成")
        return report
    
    def generate_summary(self, report_data: Dict, output_path: Path):
        """生成执行摘要（Markdown格式）"""
        self.logger.info("开始生成执行摘要")
        
        metadata = report_data['metadata']
        summary = report_data['summary']
        
        content = f"""# 爬取执行摘要

## 基本信息
- **生成时间**: {metadata['generated_at']}
- **总URL数**: {metadata['total_urls']}
- **成功爬取**: {metadata['successful_scrapes']}
- **失败爬取**: {metadata['failed_scrapes']}
- **成功率**: {(metadata['successful_scrapes']/metadata['total_urls']*100):.1f}%
- **总耗时**: {metadata['duration_seconds']:.2f}秒
- **平均每个URL耗时**: {metadata['average_time_per_url']:.2f}秒

## 网站类型统计

"""
        
        for wtype, stats in summary['website_types'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            content += f"- **{wtype}**: {stats['success']}/{stats['total']} ({success_rate:.1f}%)\n"
        
        content += f"""
## 详细结果

详细结果请查看 `crawling_report.json` 文件。

## 输出文件

- 爬取报告: `crawling_report.json`
- 执行摘要: `execution_summary.md`
- 文章详情: `articles/` 目录下的JSON文件
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"执行摘要已生成: {output_path}")
        except Exception as e:
            self.logger.error(f"生成执行摘要失败: {e}")
            raise