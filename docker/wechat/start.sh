#!/bin/bash
set -e

# WeChat Scraper 启动脚本
# 统一的结果处理：/results/wechat/articles/ 和 /results/wechat/crawling_report.json

echo "💬 Starting WeChat Scraper..."
echo "Working directory: $(pwd)"

# 设置结果目录
RESULTS_DIR="/results/wechat"
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
https://mp.weixin.qq.com/s/lqnPnTC1Ij-m8kqU_dOTKA
https://mp.weixin.qq.com/s/qx3D4yYWLFRANs53yQmQeQ
https://mp.weixin.qq.com/s/9Mnl0uHj5xCzM5rTdItN6Q
https://mp.weixin.qq.com/s/X8GWbx5na254QXPReL3-bg
https://mp.weixin.qq.com/s/bwBZjSsctPRCe6b1xB5nxA
EOF
fi

echo "📋 URLs to scrape:"
cat webs.txt
echo ""

# 启动Chrome浏览器服务
echo "🔄 Starting Chrome browser service..."
# 启动Xvfb虚拟显示（如果需要）
if command -v Xvfb > /dev/null 2>&1; then
    echo "Starting Xvfb virtual display..."
    Xvfb :99 -ac -screen 0 1280x1024x24 &
    export DISPLAY=:99
    sleep 2
fi

# 等待selenium服务准备就绪
echo "⏳ Waiting for Selenium service to be ready..."
sleep 5

# 运行爬虫并捕获输出
echo "🚀 Starting scraping process..."
if python3 wechat_scraper.py; then
    echo "✅ Scraping completed successfully!"
    
    # 检查结果是否生成在wechat_results目录
    if [ -d "wechat_results" ]; then
        echo "📁 Moving results to unified directory structure..."
        
        # 移动文章文件到统一的articles目录
        if [ -d "wechat_results/articles" ]; then
            cp -r wechat_results/articles/* "$ARTICLES_DIR/" 2>/dev/null || true
        fi
        
        # 复制爬取报告
        if [ -f "wechat_results/crawling_report.json" ]; then
            cp "wechat_results/crawling_report.json" "$RESULTS_DIR/"
            echo "📊 Report saved to: $RESULTS_DIR/crawling_report.json"
        fi
        
        # 复制其他结果文件
        if ls wechat_results/*.json 1> /dev/null 2>&1; then
            cp wechat_results/*.json "$ARTICLES_DIR/" 2>/dev/null || true
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

# 清理Chrome进程
echo "🧹 Cleaning up Chrome processes..."
pkill -f chrome || true
pkill -f chromedriver || true
pkill -f Xvfb || true

echo ""
echo "🎉 WeChat scraper finished! Check results in:"
echo "   📁 $RESULTS_DIR"
echo "   📄 $RESULTS_DIR/crawling_report.json"
echo "   📂 $ARTICLES_DIR"