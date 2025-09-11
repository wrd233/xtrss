# 基础镜像，包含Python和通用依赖
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --upgrade pip

# 安装通用Python包
RUN pip install \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    fake-useragent==1.4.0 \
    html2text==2020.1.16 \
    urllib3==2.0.7

# 创建结果目录
RUN mkdir -p /app/results

# 设置默认命令
CMD ["python3", "--version"]