# 使用官方的Python基础镜像并指定版本
FROM python:3.11.11-slim
LABEL maintainer="Anonymous"

ARG BOT_TOKEN
ARG TELEGRAM_DB_HOST
ARG TELEGRAM_DB_PORT
ARG TELEGRAM_DB_TYPE
ARG TELEGRAM_DB_USERNAME
ARG TELEGRAM_DB_PASSWORD
ARG TELEGRAM_DB_DATABASE
ARG TELEGRAM_DB_CORE_POOL_SIZE
ARG TELEGRAM_DB_MAX_POOL_SIZE

ENV BOT_TOKEN=$BOT_TOKEN TELEGRAM_DB_HOST=$TELEGRAM_DB_HOST TELEGRAM_DB_PORT=$TELEGRAM_DB_PORT TELEGRAM_DB_TYPE=$TELEGRAM_DB_TYPE TELEGRAM_DB_USERNAME=$TELEGRAM_DB_USERNAME TELEGRAM_DB_PASSWORD=$TELEGRAM_DB_PASSWORD TELEGRAM_DB_DATABASE=$TELEGRAM_DB_DATABASE TELEGRAM_DB_CORE_POOL_SIZE=$TELEGRAM_DB_CORE_POOL_SIZE TELEGRAM_DB_MAX_POOL_SIZE=$TELEGRAM_DB_MAX_POOL_SIZE

# 设置工作目录
WORKDIR /app

# 将当前目录的所有内容复制到容器中的/app目录
COPY . /app

# 如果有requirements.txt文件，安装依赖库
# 确保你的应用程序有这个文件
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 显示一个容器启动时要运行的命令
# 假设你的应用程序的入口文件是app.py
CMD ["python", "main.py"]