# 多阶段构建的统一Dockerfile
FROM python:3.11-slim as base

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 基础镜像标签
FROM base as scraper-base

# 创建必要的目录结构
RUN mkdir -p /app/{src,data/input,data/output,results}

# 设置Python路径
ENV PYTHONPATH=/app/src:$PYTHONPATH

# 最终应用镜像
FROM scraper-base as app

# 复制源代码
COPY src/ ./src/
COPY main.py ./

# 创建数据目录
RUN mkdir -p data/{input,output}

# 设置默认命令
CMD ["python3", "main.py", "--scraper", "requests"]