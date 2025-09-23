#!/bin/bash
set -e

# WeChat Scraper 启动脚本 - 适配新结构
# 统一的结果处理：/app/data/output/YYYY-MM-DD_HH-MM-SS/ 目录结构

echo "💬 Starting WeChat Scraper (New Structure)..."
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# 设置结果目录（使用时间戳创建子目录）
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
RESULTS_DIR="/app/data/output/$TIMESTAMP"
ARTICLES_DIR="$RESULTS_DIR/articles"

echo "Results directory: $RESULTS_DIR"
echo "Articles directory: $ARTICLES_DIR"
echo "Timestamp: $TIMESTAMP"

# 确保结果目录存在
mkdir -p "$RESULTS_DIR"
mkdir -p "$ARTICLES_DIR"

# 启动虚拟显示（Xvfb）
echo "🖥️  Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99

# 等待虚拟显示启动
sleep 2

# 检查webs.txt文件是否存在
if [ ! -f "data/input/webs.txt" ]; then
    echo "❌ data/input/webs.txt not found!"
    echo "Creating sample webs.txt..."
    mkdir -p data/input
    cat > data/input/webs.txt <<EOF
https://mp.weixin.qq.com/s?__biz=MzA3MzI4MjgzMw==&mid=2650986961&idx=2&sn=00d3c32b9b44fc02da6ca3602ad1a90a&chksm=84e71dafb39094b9253035787f59e0ffb440b3fa139f6a35b0ede8751c160ced1d5822d305ad#rd
https://mp.weixin.qq.com/s/9Mnl0uHj5xCzM5rTdItN6Q
https://mp.weixin.qq.com/s/X8GWbx5na254QXPReL3-bg
https://mp.weixin.qq.com/s/bwBZjSsctPRCe6b1xB5nxA
https://mp.weixin.qq.com/s?__biz=MzA3MzI4MjgzMw==&mid=2650987701&idx=2&sn=7f6ce326a6444c894c176b2e2d2d8b03&chksm=84e718cbb39091dd37bd30da502465ed4a4c6b20ce7edbd7bca3af2506a11763c62a6bb01981#rd
EOF
fi

echo "📋 URLs to scrape:"
cat data/input/webs.txt
echo ""

# 运行爬虫并捕获输出
echo "🚀 Starting scraping process..."
if python3 -m src.scraper_app.main --scraper wechat --input data/input/webs.txt --output "$RESULTS_DIR"; then
    echo "✅ Scraping completed successfully!"
    
    # 检查结果结构
    if [ -d "$RESULTS_DIR" ]; then
        echo "📁 Results structure:"
        ls -la "$RESULTS_DIR"
        
        # 显示统计信息
        if [ -f "$RESULTS_DIR/crawling_report.json" ]; then
            echo ""
            echo "📈 Scraping Statistics:"
            python3 -c "
import json
import os
report_path = '$RESULTS_DIR/crawling_report.json'
if os.path.exists(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    metadata = report.get('metadata', {})
    print(f'Total URLs: {metadata.get(\"total_urls\", \"N/A\")}')
    print(f'Successful: {metadata.get(\"successful_scrapes\", \"N/A\")}')
    print(f'Failed: {metadata.get(\"failed_scrapes\", \"N/A\")}')
    if metadata.get('total_urls', 0) > 0:
        success_rate = (metadata.get('successful_scrapes', 0) / metadata.get('total_urls', 1)) * 100
        print(f'Success Rate: {success_rate:.1f}%')
    if metadata.get('duration_seconds'):
        print(f'Duration: {metadata.get(\"duration_seconds\")} seconds')
"
        fi
        
        # 统计文章数量
        if [ -d "$ARTICLES_DIR" ]; then
            article_count=$(find "$ARTICLES_DIR" -name "*.json" | wc -l)
            echo "Articles saved: $article_count"
        fi
        
        echo ""
        echo "✅ Results organized in unified structure:"
        echo "  📁 Results: $RESULTS_DIR"
        echo "  📊 Report: $RESULTS_DIR/crawling_report.json"
        echo "  📂 Articles: $ARTICLES_DIR"
        
    else
        echo "⚠️  No results directory found, but scraping completed."
    fi
    
else
    echo "❌ Scraping failed!"
    exit 1
fi

echo ""
echo "🎉 WeChat scraper finished! Check results in:"
echo "   📁 $RESULTS_DIR"
echo "   📄 $RESULTS_DIR/crawling_report.json"
echo "   📂 $ARTICLES_DIR"
echo ""
echo "📁 Also check in host: data/output/$TIMESTAMP/"

# 清理虚拟显示
pkill Xvfb || true