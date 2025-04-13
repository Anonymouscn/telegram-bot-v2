#!/bin/zsh

app_name=telegram-bot-v2

# .env 文件路径
env_file=".env.dev"

# 读取 .env 文件并设置环境变量
while IFS='=' read -r key value; do
    # 忽略空行和注释行
    if [[ -z "$key" || "$key" =~ ^# ]]; then
        continue
    fi
    # 设置环境变量
    export "$key"="$value"
done < "$env_file"

# 输出确认已设置的环境变量
echo "环境变量已设置"

docker buildx build --platform linux/amd64,linux/arm64 \
--build-arg BOT_TOKEN="$BOT_TOKEN" \
--build-arg TELEGRAM_DB_HOST="$TELEGRAM_DB_HOST" \
--build-arg TELEGRAM_DB_PORT="$TELEGRAM_DB_PORT" \
--build-arg TELEGRAM_DB_TYPE="$TELEGRAM_DB_TYPE" \
--build-arg TELEGRAM_DB_USERNAME="$TELEGRAM_DB_USERNAME" \
--build-arg TELEGRAM_DB_PASSWORD="$TELEGRAM_DB_PASSWORD" \
--build-arg TELEGRAM_DB_DATABASE="$TELEGRAM_DB_DATABASE" \
--build-arg TELEGRAM_DB_CORE_POOL_SIZE="$TELEGRAM_DB_CORE_POOL_SIZE" \
--build-arg TELEGRAM_DB_MAX_POOL_SIZE="$TELEGRAM_DB_MAX_POOL_SIZE" \
--no-cache \
-t pgl888999/telegram-bot-v2 --push .

# docker run -it --rm pgl888999/telegram-bot-v2