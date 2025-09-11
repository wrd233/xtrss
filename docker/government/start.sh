#!/bin/bash
set -e

# Government Scraper 启动脚本
# 统一的结果处理：/results/government/articles/ 和 /results/government/crawling_report.json

echo "🏛️ Starting Government Scraper..."
echo "Working directory: $(pwd)"

# 设置结果目录
RESULTS_DIR="/results/government"
ARTICLES_DIR="$RESULTS_DIR/articles"

echo "Results directory: $RESULTS_DIR"
echo "Articles directory: $ARTICLES_DIR"

# 确保结果目录存在
mkdir -p "$RESULTS_DIR"
mkdir -p "$ARTICLES_DIR"

# 检查webs.txt文件是否存在
if [ ! -f "webs.txt" ]; then
    echo "❌ webs.txt not found!"
    echo "Creating sample webs.txt..."
    cat > webs.txt <<EOF
https://www.gov.cn/zhengce/content/202508/content_7037861.htm
https://cjhy.mot.gov.cn/xw/slxw/202509/t20250901_459007.shtml
https://www.cac.gov.cn/2025-08/27/c_1758018277755538.htm
https://www.beijing.gov.cn
https://www.shanghai.gov.cn
EOF
fi

echo "📋 URLs to scrape:"
cat webs.txt
echo ""

# 运行爬虫并捕获输出
echo "🚀 Starting scraping process..."
if python3 government_scraper.py; then
    echo "✅ Scraping completed successfully!"
    
    # 检查结果是否生成在government_results目录
    if [ -d "government_results" ]; then
        echo "📁 Moving results to unified directory structure..."
        
        # 移动文章文件到统一的articles目录
        if [ -d "government_results/articles" ]; then
            cp -r government_results/articles/* "$ARTICLES_DIR/" 2>/dev/null || true
        fi
        
        # 复制爬取报告
        if [ -f "government_results/crawling_report.json" ]; then
            cp "government_results/crawling_report.json" "$RESULTS_DIR/"
            echo "📊 Report saved to: $RESULTS_DIR/crawling_report.json"
        fi
        
        # 复制其他结果文件
        if ls government_results/*.json 1> /dev/null 2>&1; then
            cp government_results/*.json "$ARTICLES_DIR/" 2>/dev/null || true
        fi
        
        echo "✅ Results organized in unified structure:"
        echo "  📁 Articles: $ARTICLES_DIR"
        echo "  📊 Report: $RESULTS_DIR/crawling_report.json"
        
        # 显示统计信息
        if [ -f "$RESULTS_DIR/crawling_report.json" ]; then
            echo ""
            echo "📈 Scraping Statistics:"
            if command -v python3 > /dev/null 2>&1; then
                python3 -c "
import json
import os
report_path = '$RESULTS_DIR/crawling_report.json'
if os.path.exists(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    metadata = report.get('metadata', {})
    print(f\"Total URLs: {metadata.get('total_urls', 'N/A')}\")
    print(f\"Successful: {metadata.get('successful_scrapes', 'N/A')}\")
    print(f\"Failed: {metadata.get('failed_scrapes', 'N/A')}\")
    if metadata.get('total_urls', 0) > 0:
        success_rate = (metadata.get('successful_scrapes', 0) / metadata.get('total_urls', 1)) * 100
        print(f\"Success Rate: {success_rate:.1f}%\")
"
            fi
        fi
        
    else
        echo "⚠️  No results directory found, but scraping completed."
    fi
    
else
    echo "❌ Scraping failed!"
    exit 1
fi

echo ""
echo "🎉 Government scraper finished! Check results in:"
echo "   📁 $RESULTS_DIR"
echo "   📄 $RESULTS_DIR/crawling_report.json"
echo "   📂 $ARTICLES_DIR"