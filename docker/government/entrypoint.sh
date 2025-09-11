#!/bin/bash
set -e

echo "🕷️ Starting Government Website Scraper..."
echo "Working directory: $(pwd)"
echo "Results directory: $RESULTS_DIR"

# 确保结果目录存在
mkdir -p "$RESULTS_DIR"

# 检查webs.txt文件是否存在
if [ ! -f "webs.txt" ]; then
    echo "❌ webs.txt not found!"
    echo "Creating sample webs.txt with government URLs..."
    cat > webs.txt <<EOF
https://www.gov.cn
https://www.beijing.gov.cn
https://www.shanghai.gov.cn
https://www.example.com
EOF
fi

echo "📋 URLs to scrape:"
cat webs.txt
echo ""

# 运行爬虫
echo "🚀 Starting scraping process..."
echo "⚠️  Note: Only government URLs (gov.cn) will be processed"
exec "$@"