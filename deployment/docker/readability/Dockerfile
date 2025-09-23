# Readability Scraper - 基于新结构
FROM scraper-base:latest

# 复制新结构的代码
COPY src/ /app/src/
COPY main.py /app/
COPY data/input/webs.txt /app/data/input/webs.txt

# 创建工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:$PYTHONPATH

# 设置结果目录环境变量（已更新为新架构）
ENV RESULTS_DIR=/app/data/output

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import readability; print('OK')" || exit 1

# 复制启动脚本
COPY deployment/scripts/readability/start.sh /app/
RUN chmod +x /app/start.sh

# 入口脚本
ENTRYPOINT ["/app/start.sh"]