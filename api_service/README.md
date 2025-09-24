# 爬虫API服务

基于Flask的爬虫API服务，提供异步任务调度和结果查询功能。

## 功能特性

- ✅ RESTful API设计
- ✅ 异步任务处理
- ✅ Redis消息队列
- ✅ 多种爬虫类型支持
- ✅ API Key认证
- ✅ 速率限制
- ✅ 任务进度跟踪
- ✅ 结果自动过期

## API接口

### 1. 健康检查
```http
GET /health
```

### 2. 创建爬取任务
```http
POST /api/v1/scrape
Content-Type: application/json
X-API-Key: your-api-key

{
    "urls": ["https://example.com", "https://example.org"],
    "scraper_type": "requests",
    "options": {}
}
```

### 3. 查询任务状态
```http
GET /api/v1/tasks/{task_id}
X-API-Key: your-api-key
```

### 4. 获取任务结果
```http
GET /api/v1/tasks/{task_id}/results
X-API-Key: your-api-key
```

### 5. 系统统计
```http
GET /api/v1/stats
X-API-Key: your-api-key
```

## 快速开始

### 1. 环境配置
```bash
cd api_service
cp .env.example .env
# 编辑 .env 文件
```

### 2. 启动Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. 启动API服务
```bash
pip install -r requirements.txt
python app.py
```

### 4. 运行测试
```bash
python test_api.py
```

## Docker部署

```bash
docker-compose -f docker-compose.api.yml up -d
```

## 支持的爬虫类型

- `requests` - Requests + BeautifulSoup
- `government` - 政府网站专用
- `newspaper` - Newspaper3k
- `readability` - Readability算法
- `selenium` - Selenium浏览器
- `trafilatura` - Trafilatura库
- `wechat` - 微信文章专用

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| REDIS_HOST | Redis主机 | localhost |
| REDIS_PORT | Redis端口 | 6379 |
| API_KEY | API密钥 | your-secret-api-key-here |
| RATE_LIMIT_PER_MINUTE | 每分钟请求限制 | 60 |
| TASK_EXPIRE_HOURS | 任务过期时间(小时) | 24 |
| RESULT_EXPIRE_HOURS | 结果过期时间(小时) | 24 |

## 状态码说明

- `200` - 请求成功
- `202` - 任务已接受
- `400` - 请求参数错误
- `401` - 认证失败
- `404` - 资源不存在
- `425` - 任务未完成
- `429` - 请求过于频繁
- `500` - 服务器内部错误
- `503` - 服务不可用

## 错误处理

所有错误响应都遵循统一的错误格式：

```json
{
    "error": "错误类型",
    "message": "错误消息",
    "details": {
        "additional_info": "详细信息"
    }
}
```