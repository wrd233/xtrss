# Requests Scraper - 基于基础镜像
FROM scraper-base:latest

# 复制爬虫脚本
COPY requests_scraper.py /app/
COPY webs.txt /app/

# 创建工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV RESULTS_DIR=/app/results

# 创建结果目录
RUN mkdir -p /app/results

# 设置卷挂载点
VOLUME ["/app/results"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; print('OK')" || exit 1

# 复制启动脚本
COPY docker/requests/start.sh /app/
RUN chmod +x /app/start.sh

# 入口脚本（使用新的start.sh）
ENTRYPOINT ["/app/start.sh"]