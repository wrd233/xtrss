# Selenium Scraper - 基于基础镜像
FROM scraper-base:latest

# 安装Chrome和ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
    && wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P ~/ \
    && unzip ~/chromedriver_linux64.zip -d ~/ \
    && rm ~/chromedriver_linux64.zip \
    && mv -f ~/chromedriver /usr/local/bin/chromedriver \
    && chmod 755 /usr/local/bin/chromedriver

# 安装Selenium
RUN pip install selenium==4.15.2

# 复制爬虫脚本
COPY selenium_scraper.py /app/
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
COPY docker/selenium/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# 启动脚本
COPY docker/selenium/start.sh /app/
RUN chmod +x /app/start.sh

# ENTRYPOINT ["/app/entrypoint.sh"]
# CMD ["python3", "selenium_scraper.py"]
ENTRYPOINT ["/app/start.sh"]