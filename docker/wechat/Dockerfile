# WeChat Scraper - 基于Selenium镜像
FROM scraper-selenium:latest

# 复制爬虫脚本（覆盖selenium_scraper.py）
COPY wechat_scraper.py /app/
COPY webs.txt /app/

# 创建工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV RESULTS_DIR=/app/results
ENV DISPLAY=:99

# 创建结果目录
RUN mkdir -p /app/results

# 设置卷挂载点
VOLUME ["/app/results"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "from selenium import webdriver; from selenium.webdriver.chrome.options import Options; options = Options(); options.add_argument('--headless'); print('OK')" || exit 1

# 入口脚本
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "wechat_scraper.py"]