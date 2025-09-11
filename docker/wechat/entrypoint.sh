#!/bin/bash
set -e

echo "🕷️ Starting WeChat Scraper..."
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
    echo "Creating sample webs.txt with WeChat URLs..."
    cat > webs.txt <<EOF
https://mp.weixin.qq.com/s?__biz=MzA4ODk4MjAzOA==&mid=2649659402&idx=1&sn=1234567890abcdef
https://mp.weixin.qq.com/s?__biz=MzA4ODk4MjAzOA==&mid=2649659402&idx=2&sn=abcdef1234567890
https://www.example.com
EOF
fi

echo "📋 URLs to scrape:"
cat webs.txt
echo ""

# 等待虚拟显示完全启动
sleep 2

# 运行爬虫
echo "🚀 Starting scraping process..."
echo "⚠️  Note: Only WeChat URLs (weixin.qq.com or mp.weixin.qq.com) will be processed"
exec "$@"