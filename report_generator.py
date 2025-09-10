#!/usr/bin/env python3
"""
Report Generator Module
Generates comprehensive reports about scraping results
"""

import json
import logging
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.report_data = {}
    
    def generate_report(self, results):
        """Generate a comprehensive report from scraping results"""
        logger.info("Generating scraping report")
        
        total_urls = len(results)
        successful_scrapes = sum(1 for result in results.values() if result.get('success', False))
        failed_scrapes = total_urls - successful_scrapes
        success_rate = (successful_scrapes / total_urls * 100) if total_urls > 0 else 0
        
        # Analyze by website type
        website_types = Counter()
        success_by_type = Counter()
        
        # Analyze by scraping method
        method_success = Counter()
        method_attempts = Counter()
        
        # Detailed website results
        website_results = []
        
        for url, result in results.items():
            website_type = result.get('website_type', 'unknown')
            website_types[website_type] += 1
            
            if result.get('success', False):
                success_by_type[website_type] += 1
            
            # Analyze attempts
            final_content = result.get('final_content', {})
            if final_content:
                method = final_content.get('method', 'unknown')
                method_success[method] += 1
            
            for attempt in result.get('attempts', []):
                method = attempt.get('method', 'unknown')
                method_attempts[method] += 1
            
            # Create website result entry
            website_result = {
                'url': url,
                'website_type': website_type,
                'success': result.get('success', False),
                'final_method': final_content.get('method', 'none') if final_content else 'none',
                'title': final_content.get('title', '') if final_content else '',
                'content_length': len(final_content.get('content', '')) if final_content else 0,
                'attempts_count': len(result.get('attempts', [])),
                'error_reason': self._get_error_reason(result)
            }
            
            website_results.append(website_result)
        
        # Calculate method success rates
        method_stats = {}
        for method in method_attempts.keys():
            attempts = method_attempts[method]
            successes = method_success[method]
            success_rate_method = (successes / attempts * 100) if attempts > 0 else 0
            method_stats[method] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': success_rate_method
            }
        
        # Calculate success rates by website type
        type_stats = {}
        for wtype in website_types.keys():
            total = website_types[wtype]
            successes = success_by_type[wtype]
            success_rate_type = (successes / total * 100) if total > 0 else 0
            type_stats[wtype] = {
                'total': total,
                'successes': successes,
                'success_rate': success_rate_type
            }
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_urls': total_urls,
                'successful_scrapes': successful_scrapes,
                'failed_scrapes': failed_scrapes,
                'overall_success_rate': round(success_rate, 2)
            },
            'summary': {
                'by_website_type': type_stats,
                'by_method': method_stats
            },
            'detailed_results': website_results,
            'recommendations': self._generate_recommendations(type_stats, method_stats),
            'raw_data': results
        }
        
        return report
    
    def _get_error_reason(self, result):
        """Analyze why scraping failed for a URL"""
        if result.get('success', False):
            return None
        
        attempts = result.get('attempts', [])
        if not attempts:
            return "No successful scraping attempts"
        
        # Check if any attempt got content but it was too short
        for attempt in attempts:
            content = attempt.get('content', '')
            if content and len(content.strip()) < 100:
                return "Content too short or incomplete"
        
        # Check if title was missing
        for attempt in attempts:
            title = attempt.get('title', '')
            if not title:
                return "No title found"
        
        return "Multiple methods attempted but no meaningful content extracted"
    
    def _generate_recommendations(self, type_stats, method_stats):
        """Generate recommendations based on the scraping results"""
        recommendations = []
        
        # Analyze website types with low success rates
        for wtype, stats in type_stats.items():
            if stats['success_rate'] < 50:
                if wtype == 'wechat':
                    recommendations.append({
                        'type': 'website_specific',
                        'target': 'WeChat articles',
                        'issue': f'Low success rate ({stats["success_rate"]:.1f}%)',
                        'recommendation': 'Consider using specialized WeChat scraping tools or APIs'
                    })
                elif wtype == 'government':
                    recommendations.append({
                        'type': 'website_specific', 
                        'target': 'Government websites',
                        'issue': f'Low success rate ({stats["success_rate"]:.1f}%)',
                        'recommendation': 'Government sites may have strict anti-scraping measures. Consider slower rates and more sophisticated methods.'
                    })
                elif wtype == 'academic':
                    recommendations.append({
                        'type': 'website_specific',
                        'target': 'Academic/IEEE papers',
                        'issue': f'Low success rate ({stats["success_rate"]:.1f}%)',
                        'recommendation': 'Academic papers may require institutional access or specialized parsers'
                    })
        
        # Analyze method performance
        best_method = max(method_stats.items(), key=lambda x: x[1]['success_rate'])
        worst_method = min(method_stats.items(), key=lambda x: x[1]['success_rate'])
        
        recommendations.append({
            'type': 'method_optimization',
            'target': 'Scraping methods',
            'issue': 'Inconsistent method performance',
            'recommendation': f'Prioritize {best_method[0]} (success rate: {best_method[1]["success_rate"]:.1f}%) over {worst_method[0]} (success rate: {worst_method[1]["success_rate"]:.1f}%)'
        })
        
        # General recommendations
        recommendations.extend([
            {
                'type': 'general',
                'target': 'All scraping',
                'issue': 'Anti-scraping measures',
                'recommendation': 'Implement rotating proxies, user agents, and request delays'
            },
            {
                'type': 'general',
                'target': 'Content quality',
                'issue': 'Content validation',
                'recommendation': 'Implement better content validation (minimum length, keyword checks)'
            }
        ])
        
        return recommendations
    
    def generate_html_report(self, report_data):
        """Generate an HTML report for better visualization"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scraping Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .summary-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .success-rate {{
            font-size: 2em;
            font-weight: bold;
            color: #28a745;
        }}
        .failed-rate {{
            color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .success {{
            background-color: #d4edda;
            color: #155724;
        }}
        .failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .recommendations {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }}
        .recommendations h3 {{
            margin-top: 0;
            color: #856404;
        }}
        .recommendation {{
            margin-bottom: 15px;
            padding: 10px;
            background-color: #fff;
            border-radius: 5px;
            border-left: 3px solid #ffc107;
        }}
        .url-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web Scraping Report</h1>
            <p>Generated on: {generated_at}</p>
            <p>Total URLs processed: {total_urls}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Overall Success Rate</h3>
                <div class="success-rate">{overall_success_rate}%</div>
            </div>
            <div class="summary-card">
                <h3>Successful Scrapes</h3>
                <div class="success-rate">{successful_scrapes}</div>
            </div>
            <div class="summary-card">
                <h3>Failed Scrapes</h3>
                <div class="success-rate failed-rate">{failed_scrapes}</div>
            </div>
        </div>
        
        <h2>Success Rate by Website Type</h2>
        <table>
            <thead>
                <tr>
                    <th>Website Type</th>
                    <th>Total</th>
                    <th>Successful</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {website_type_rows}
            </tbody>
        </table>
        
        <h2>Method Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Method</th>
                    <th>Attempts</th>
                    <th>Successes</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {method_rows}
            </tbody>
        </table>
        
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Method</th>
                    <th>Title</th>
                    <th>Content Length</th>
                </tr>
            </thead>
            <tbody>
                {detailed_rows}
            </tbody>
        </table>
        
        <div class="recommendations">
            <h3>Recommendations</h3>
            {recommendation_items}
        </div>
    </div>
</body>
</html>
"""
        
        # Generate website type rows
        website_type_rows = ""
        for wtype, stats in report_data['summary']['by_website_type'].items():
            website_type_rows += f"""
                <tr>
                    <td>{wtype}</td>
                    <td>{stats['total']}</td>
                    <td>{stats['successes']}</td>
                    <td>{stats['success_rate']:.1f}%</td>
                </tr>"""
        
        # Generate method rows
        method_rows = ""
        for method, stats in report_data['summary']['by_method'].items():
            method_rows += f"""
                <tr>
                    <td>{method}</td>
                    <td>{stats['attempts']}</td>
                    <td>{stats['successes']}</td>
                    <td>{stats['success_rate']:.1f}%</td>
                </tr>"""
        
        # Generate detailed rows
        detailed_rows = ""
        for result in report_data['detailed_results']:
            status_class = "success" if result['success'] else "failed"
            status_text = "Success" if result['success'] else "Failed"
            
            detailed_rows += f"""
                <tr class="{status_class}">
                    <td class="url-cell" title="{result['url']}">{result['url'][:50]}...</td>
                    <td>{result['website_type']}</td>
                    <td>{status_text}</td>
                    <td>{result['final_method']}</td>
                    <td>{result['title'][:50] if result['title'] else 'N/A'}</td>
                    <td>{result['content_length']}</td>
                </tr>"""
        
        # Generate recommendation items
        recommendation_items = ""
        for rec in report_data['recommendations']:
            recommendation_items += f"""
                <div class="recommendation">
                    <strong>{rec['target']}:</strong> {rec['issue']}<br>
                    <em>Recommendation:</em> {rec['recommendation']}
                </div>"""
        
        # Fill in the template
        html_content = html_template.format(
            generated_at=report_data['metadata']['generated_at'],
            total_urls=report_data['metadata']['total_urls'],
            overall_success_rate=report_data['metadata']['overall_success_rate'],
            successful_scrapes=report_data['metadata']['successful_scrapes'],
            failed_scrapes=report_data['metadata']['failed_scrapes'],
            website_type_rows=website_type_rows,
            method_rows=method_rows,
            detailed_rows=detailed_rows,
            recommendation_items=recommendation_items
        )
        
        return html_content