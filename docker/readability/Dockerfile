# Readability Scraper - 基于基础镜像
FROM scraper-base:latest

# 安装Readability特定依赖
RUN pip install \
    readability-lxml==0.8.1 \
    html2text==2020.1.16

# 复制爬虫脚本
COPY readability_scraper.py /app/
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
    CMD python3 -c "import readability; print('OK')" || exit 1

# 入口脚本
COPY docker/readability/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# 启动脚本
COPY docker/readability/start.sh /app/
RUN chmod +x /app/start.sh

# ENTRYPOINT ["/app/entrypoint.sh"]
# CMD ["python3", "readability_scraper.py"]
ENTRYPOINT ["/app/start.sh"]