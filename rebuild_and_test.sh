#!/bin/bash

echo "🚀 重新构建Docker镜像并测试并发功能"
echo "=================================="

# 1. 停止现有服务
echo "1. 停止现有服务..."
docker-compose -f docker-compose.race.yml down

# 2. 重新构建镜像（包含新的依赖和代码）
echo "2. 重新构建Docker镜像..."
docker-compose -f docker-compose.race.yml build --no-cache

# 3. 启动服务
echo "3. 启动所有服务..."
docker-compose -f docker-compose.race.yml up -d

# 4. 等待服务启动
echo "4. 等待服务启动..."
sleep 10

# 5. 检查服务状态
echo "5. 检查服务状态..."
docker-compose -f docker-compose.race.yml ps

# 6. 测试API健康状态
echo "6. 测试API健康状态..."
curl -s http://localhost:5000/health | jq '.' || echo "API健康检查失败"

# 7. 运行并发性能测试
echo "7. 运行并发性能测试..."
echo "测试将在5秒后开始..."
sleep 5

# 复制测试脚本到API容器
docker cp test_concurrent_performance.py $(docker-compose -f docker-compose.race.yml ps -q api):/app/

# 在API容器中运行测试
echo "开始并发性能测试..."
docker-compose -f docker-compose.race.yml exec -T api python /app/test_concurrent_performance.py

echo ""
echo "=================================="
echo "测试完成！查看日志以获取详细信息："
echo "docker-compose -f docker-compose.race.yml logs -f"
echo ""
echo "或者查看特定Worker的并发处理日志："
echo "docker-compose -f docker-compose.race.yml logs worker_requests | grep -E '(并发|耗时|线程)'"