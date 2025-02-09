#!/bin/zsh

app_name=telegram-bot-v2
token=$(cat .env.dev | head -n 1 | sed 's/.*=//')

docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 --build-arg BOT_TOKEN=$token -t $app_name .
docker run -it --rm $app_name