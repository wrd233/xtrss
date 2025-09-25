# 并发性能优化功能

## 概述

我们实现了两个主要的并发性能优化：

1. **异步爬取支持** - 在 `simple_scrapers.py` 中添加了 asyncio 支持
2. **URL并发处理** - 在 `worker.py` 和 `scraper_adapter.py` 中使用 ThreadPoolExecutor

## 新功能详解

### 1. 异步爬取 (Asyncio Support)

**文件**: `worker_service/simple_scrapers.py`

**主要改进**:
- 添加了 `aiohttp` 支持，实现真正的异步HTTP请求
- 每个爬虫类都有异步版本的方法 (`scrape_url_async`)
- 支持批量异步爬取 (`scrape_urls_async`)
- 自动会话管理和连接池复用

**使用方法**:
```python
from simple_scrapers import scrape_urls_async
import asyncio

async def test_async():
    urls = ['https://example.com', 'https://httpbin.org/html']
    results = await scrape_urls_async(urls, 'requests')
    return results

# 运行异步爬取
results = asyncio.run(test_async())
```

### 2. URL并发处理 (ThreadPoolExecutor)

**文件**: `worker_service/scraper_adapter.py`

**主要改进**:
- 使用 `ThreadPoolExecutor` 实现URL级别的并发处理
- 动态线程池大小（最多10个并发线程）
- 保持结果顺序与输入URL一致
- 单个URL超时35秒，防止长时间阻塞

**配置参数**:
```bash
# 在 docker-compose.race.yml 中配置
MAX_WORKERS=5          # Worker进程的最大并发数
URL_CONCURRENT_LIMIT=10 # 单个任务的URL并发爬取限制
```

## 性能提升对比

### 测试场景
- 8个测试URL（包含延迟响应的URL）
- 串行处理 vs 并发处理

### 预期性能提升
```
串行处理（旧版本）:
- 每个URL平均30秒超时
- 8个URL ≈ 240秒（4分钟）

并发处理（新版本）:
- 最大10个并发线程
- 8个URL ≈ 30-60秒（考虑网络延迟）

性能提升: 约 75-80%
```

## 如何使用

### 1. 重新构建Docker镜像
```bash
# 停止现有服务
docker-compose -f docker-compose.race.yml down

# 重新构建（包含新的依赖）
docker-compose -f docker-compose.race.yml build

# 启动服务
docker-compose -f docker-compose.race.yml up -d
```

### 2. 运行性能测试
```bash
# 进入项目目录
cd /home/parallels/work/another_rss

# 运行性能测试脚本
docker-compose -f docker-compose.race.yml exec api python /app/test_concurrent_performance.py

# 或者在worker容器中运行
docker-compose -f docker-compose.race.yml exec worker_requests python /app/test_concurrent_performance.py
```

### 3. 监控日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.race.yml logs -f

# 查看特定Worker日志
docker-compose -f docker-compose.race.yml logs -f worker_requests

# 查看API服务日志
docker-compose -f docker-compose.race.yml logs -f api
```

## 配置调优

### 环境变量
在 `docker-compose.race.yml` 中可以调整以下参数：

```yaml
environment:
  - MAX_WORKERS=5              # Worker并发进程数
  - URL_CONCURRENT_LIMIT=10    # URL并发爬取数
  - POLL_INTERVAL=2             # 任务轮询间隔（秒）
  - LOG_LEVEL=INFO              # 日志级别
```

### 调优建议
- **小批量URL**（<10个）: `MAX_WORKERS=3-5`
- **大批量URL**（>50个）: `MAX_WORKERS=10-15`
- **网络延迟高**: 减少 `URL_CONCURRENT_LIMIT` 到 5-8
- **目标网站限制严格**: 设置 `URL_CONCURRENT_LIMIT=3-5`

## 故障排除

### 常见问题

1. **容器构建失败**
   ```bash
   # 确保requirements.txt包含新依赖
   aiohttp==3.9.1
   aiofiles==23.2.1
   ```

2. **性能没有提升**
   - 检查 `MAX_WORKERS` 和 `URL_CONCURRENT_LIMIT` 设置
   - 确认目标网站是否支持并发访问
   - 查看日志中是否有大量超时错误

3. **内存使用过高**
   - 减少 `MAX_WORKERS` 和 `URL_CONCURRENT_LIMIT`
   - 检查是否有连接泄漏（应该已修复）

### 日志监控要点
```bash
# 查看并发处理相关日志
docker-compose logs | grep -E "(并发|耗时|线程|Worker)"

# 查看性能统计
docker-compose logs | grep -E "(成功|失败|耗时)"
```

## 后续优化计划

1. **连接池优化**: 进一步优化HTTP连接复用
2. **智能限流**: 根据目标网站响应动态调整并发数
3. **缓存机制**: 添加爬取结果缓存
4. **队列优化**: 实现优先级队列

## 注意事项

- 并发处理会增加目标网站的负载，请合理设置并发数
- 某些网站可能有反爬虫机制，需要适当降低并发
- 建议在生产环境中逐步增加并发数，观察效果
- 保持对目标网站的尊重，避免过高频率访问