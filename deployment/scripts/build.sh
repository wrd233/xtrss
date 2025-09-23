#!/bin/bash
set -e

echo "🐳 Building Docker images for new project structure..."

# 构建基础镜像
echo "📦 Building base image..."
docker build --target scraper-base -t scraper-base:latest -f deployment/Dockerfile .

# 构建各个爬虫镜像
echo "🔨 Building scraper images..."

# Requests scraper
echo "  📄 Building requests scraper..."
docker build -t requests-scraper:latest -f deployment/docker/requests/Dockerfile .

echo "✅ All Docker images built successfully!"
echo ""
echo "🚀 To run the requests scraper:"
echo "   docker-compose -f deployment/docker-compose.yml run requests-scraper"