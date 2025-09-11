#!/bin/bash
set -e

echo "🕷️ Starting Selenium Scraper..."
echo "Working directory: $(pwd)"
echo "Results directory: $RESULTS_DIR"

# 启动虚拟显示
echo "🖥️ Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
echo "✅ Virtual display started"

# 确保结果目录存在
mkdir -p "$RESULTS_DIR"

# 检查webs.txt文件是否存在
if [ ! -f "webs.txt" ]; then
    echo "❌ webs.txt not found!"
    echo "Creating sample webs.txt..."
    cat > webs.txt <<EOF
https://www.example.com
https://httpbin.org/html
https://www.python.org
EOF
fi

echo "📋 URLs to scrape:"
cat webs.txt
echo ""

# 等待虚拟显示完全启动
sleep 2

# 运行爬虫
echo "🚀 Starting scraping process..."
exec "$@"