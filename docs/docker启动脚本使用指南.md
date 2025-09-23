# Docker爬虫启动脚本使用指南

## 🎯 概述

我为每个爬虫创建了统一的启动脚本，放置在`docker/各爬虫目录/start.sh`，实现了标准化的结果处理流程。

## 📁 启动脚本位置

```
docker/
├── requests/start.sh         # Requests + BeautifulSoup爬虫
├── trafilatura/start.sh      # Trafilatura内容提取爬虫
├── newspaper/start.sh        # Newspaper3k新闻爬虫
├── readability/start.sh      # Readability可读性爬虫
├── selenium/start.sh         # Selenium浏览器爬虫
├── wechat/start.sh           # 微信公众号专用爬虫
└── government/start.sh       # 政府网站专用爬虫
```

## 🚀 使用方法

### 1. 使用Docker Compose启动（推荐）

```bash
# 启动特定爬虫（以requests为例）
docker-compose up requests-scraper

# 启动多个爬虫
docker-compose up requests-scraper trafilatura-scraper

# 后台运行
docker-compose up -d requests-scraper

# 查看实时日志
docker-compose logs -f requests-scraper
```

### 2. 直接运行启动脚本（容器内部）

```bash
# 进入容器
docker-compose run --rm requests-scraper bash

# 在容器内运行启动脚本
/app/start.sh
```

## 📊 统一结果结构

所有爬虫都会生成统一的结果结构：

```
results/
├── requests/
│   ├── crawling_report.json    # 爬取统计报告
│   └── articles/               # 具体文章文件
│       ├── article1.json
│       ├── article2.json
│       └── ...
├── trafilatura/
│   ├── crawling_report.json
│   └── articles/
├── newspaper/
│   ├── crawling_report.json
│   └── articles/
├── readability/
│   ├── crawling_report.json
│   └── articles/
├── selenium/
│   ├── crawling_report.json
│   └── articles/
├── wechat/
│   ├── crawling_report.json
│   └── articles/
└── government/
    ├── crawling_report.json
    └── articles/
```

## 📋 crawling_report.json 结构

```json
{
  "metadata": {
    "generated_at": "2025-09-11T01:30:23.675157",
    "total_urls": 25,
    "successful_scrapes": 17,
    "failed_scrapes": 8
  },
  "detailed_results": [
    {
      "url": "https://example.com/article",
      "website_type": "news",
      "success": true,
      "method": "requests_beautifulsoup",
      "title": "文章标题",
      "content_length": 2684,
      "error": "",
      "status_code": 200
    }
  ]
}
```

## 🛠️ 启动脚本功能特点

### ✅ 自动功能
- **自动创建目录结构**：自动创建`/results/爬虫类型/articles/`目录
- **智能结果整理**：自动将爬虫结果整理到统一结构
- **统计信息展示**：运行完成后显示爬取统计信息
- **错误处理**：完善的错误检测和处理机制
- **webs.txt检查**：自动检查并创建示例URL文件

### 🎨 用户友好的输出
```
🕷️ Starting Requests Scraper...
📋 URLs to scrape: [显示URL列表]
🚀 Starting scraping process...
✅ Scraping completed successfully!
📁 Moving results to unified directory structure...
📊 Report saved to: /results/requests/crawling_report.json
📈 Scraping Statistics:
Total URLs: 25
Successful: 17
Failed: 8
Success Rate: 68.0%
🎉 Requests scraper finished!
```

## 🔧 可用爬虫服务名称

| 服务名称 | 爬虫类型 | 特点 |
|---------|---------|------|
| `requests-scraper` | Requests + BeautifulSoup | 基础HTTP爬虫，适合静态页面 |
| `trafilatura-scraper` | Trafilatura | 智能内容提取，适合文章 |
| `newspaper-scraper` | Newspaper3k | 新闻网站专用 |
| `readability-scraper` | Readability | 可读性算法提取 |
| `selenium-scraper` | Selenium + Chrome | 支持JavaScript渲染 |
| `wechat-scraper` | 微信公众号专用 | 专门处理微信文章 |
| `government-scraper` | 政府网站专用 | 专门处理政府网站 |

## 📝 使用示例

### 基本使用
```bash
# 1. 确保webs.txt文件存在
cat webs.txt

# 2. 启动requests爬虫
docker-compose up requests-scraper

# 3. 查看结果
ls -la results/requests/
cat results/requests/crawling_report.json | jq .
```

### 对比不同爬虫效果
```bash
# 同时运行多个爬虫进行对比
docker-compose up requests-scraper trafilatura-scraper

# 对比结果
echo "=== Requests 爬虫结果 ==="
cat results/requests/crawling_report.json | jq .metadata
echo "=== Trafilatura 爬虫结果 ==="
cat results/trafilatura/crawling_report.json | jq .metadata
```

### 批量测试
```bash
# 启动所有爬虫（并行运行）
docker-compose up

# 后台运行所有爬虫
docker-compose up -d

# 查看运行状态
docker-compose ps

# 停止所有爬虫
docker-compose down
```

## ⚠️ 注意事项

1. **依赖关系**：`wechat-scraper`依赖`selenium-scraper`，需要同时启动或先启动selenium
   ```bash
   docker-compose up selenium-scraper wechat-scraper
   ```

2. **资源需求**：`selenium-scraper`和`wechat-scraper`需要较多内存，建议分配至少2GB

3. **结果权限**：结果文件可能以root权限创建，需要时使用`sudo`查看或修改

4. **日志查看**：
   ```bash
   # 查看特定爬虫日志
   docker-compose logs requests-scraper
   
   # 实时查看日志
   docker-compose logs -f requests-scraper
   ```

## 🚀 高级用法

### 自定义URL列表
```bash
# 使用自定义的URL文件
echo "https://custom-site.com/article" > my_urls.txt
docker-compose run --rm -v $(pwd)/my_urls.txt:/app/webs.txt requests-scraper
```

### 结果分析
```bash
# 统计所有爬虫的成功率
for scraper in requests trafilatura newspaper readability selenium wechat government; do
    if [ -f "results/$scraper/crawling_report.json" ]; then
        echo "=== $scraper ==="
        cat "results/$scraper/crawling_report.json" | jq .metadata
    fi
done
```

## 🔍 故障排除

如果启动脚本遇到问题：

1. **检查日志**：`docker-compose logs 爬虫名称`
2. **验证构建**：`docker-compose build 爬虫名称`
3. **检查文件权限**：确保脚本有执行权限
4. **查看容器内路径**：结果在容器内的`/results/爬虫类型/`目录

## 📊 性能对比建议

可以通过统一的结果结构，轻松对比不同爬虫的性能：

```bash
# 创建对比报告
echo "爬虫类型,总URL,成功,失败,成功率,耗时" > comparison.csv
for scraper in requests trafilatura newspaper readability; do
    if [ -f "results/$scraper/crawling_report.json" ]; then
        python3 -c "
import json
with open('results/$scraper/crawling_report.json') as f:
    data = json.load(f)
meta = data['metadata']
success_rate = (meta['successful_scrapes'] / meta['total_urls']) * 100
print(f'$scraper,{meta[\"total_urls\"]},{meta[\"successful_scrapes\"]},{meta[\"failed_scrapes\"]},{success_rate:.1f}%,N/A')
" >> comparison.csv
fi
done
```

这样，你就拥有了一套完整的、标准化的爬虫启动和管理系统！🎉