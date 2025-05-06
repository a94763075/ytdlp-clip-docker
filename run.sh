#!/bin/bash

cd "$(dirname "$0")"

# 如果已經有同名 container，就移除
if [ "$(docker ps -a -q -f name=my-clipper)" ]; then
  echo "⚠️  發現同名 container，準備移除..."
  docker rm -f my-clipper
fi

# 建立（可選）image
# docker build -t yt-clipper .

# 啟動新的 container
docker run -p 5001:5001 --rm --name my-clipper \
  -v "$(pwd)/downloads:/app/downloads" \
  -e FLASK_SECRET_KEY='your_very_secret_random_key' \
  yt-clipper
