#!/bin/bash

# Docker构建脚本
set -e

echo "🐳 Starting Docker build process for all scrapers..."
echo "="*60

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：构建镜像
build_image() {
    local service_name=$1
    local dockerfile_path=$2
    local image_name=$3
    
    echo -e "${YELLOW}Building $service_name...${NC}"
    
    if docker build -f "$dockerfile_path" -t "$image_name" . ; then
        echo -e "${GREEN}✅ $service_name built successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to build $service_name${NC}"
        return 1
    fi
}

# 创建结果目录
echo "📁 Creating results directories..."
mkdir -p results/{requests,trafilatura,newspaper,readability,selenium,wechat,government}
echo "✅ Results directories created"

# 检查webs.txt文件
if [ ! -f "webs.txt" ]; then
    echo "❌ webs.txt not found! Creating sample file..."
    cat > webs.txt <<EOF
https://www.example.com
https://httpbin.org/html
https://www.python.org
https://www.gov.cn
https://www.beijing.gov.cn
EOF
fi

echo "🔨 Building base image first..."
if build_image "Base Image" "docker/base/Dockerfile" "scraper-base:latest"; then
    echo "✅ Base image built successfully"
else
    echo "❌ Failed to build base image"
    exit 1
fi

# 构建各个爬虫镜像
echo "🔨 Building scraper images..."

SCRAPERS=(
    "requests:docker/requests/Dockerfile:scraper-requests:latest"
    "trafilatura:docker/trafilatura/Dockerfile:scraper-trafilatura:latest"
    "newspaper:docker/newspaper/Dockerfile:scraper-newspaper:latest"
    "readability:docker/readability/Dockerfile:scraper-readability:latest"
    "selenium:docker/selenium/Dockerfile:scraper-selenium:latest"
    "wechat:docker/wechat/Dockerfile:scraper-wechat:latest"
    "government:docker/government/Dockerfile:scraper-government:latest"
)

FAILED_BUILDS=()
SUCCESSFUL_BUILDS=()

for scraper in "${SCRAPERS[@]}"; do
    IFS=':' read -r name dockerfile image <<< "$scraper"
    
    if build_image "$name" "$dockerfile" "$image"; then
        SUCCESSFUL_BUILDS+=("$name")
    else
        FAILED_BUILDS+=("$name")
    fi
    
    echo "" # 空行分隔
    sleep 2 # 短暂暂停，避免构建过快

done

# 构建总结
echo "="*60
echo "🏗️  Build Summary:"
echo "="*60

if [ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]; then
    echo -e "${GREEN}✅ Successfully built:${NC}"
    for build in "${SUCCESSFUL_BUILDS[@]}"; do
        echo "  - $build"
    done
fi

if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Failed to build:${NC}"
    for build in "${FAILED_BUILDS[@]}"; do
        echo "  - $build"
    done
fi

echo ""
echo "="*60
echo "📝 Usage Instructions:"
echo "="*60
echo "1. Run all scrapers:"
echo "   docker-compose up"
echo ""
echo "2. Run specific scraper:"
echo "   docker-compose up requests-scraper"
echo ""
echo "3. Run in background:"
echo "   docker-compose up -d"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f [service-name]"
echo ""
echo "5. Stop all services:"
echo "   docker-compose down"
echo ""
echo "Results will be saved in: ./results/[scraper-type]/"
echo "="*60

if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
    exit 1
fi

echo -e "${GREEN}🎉 All builds completed successfully!${NC}"