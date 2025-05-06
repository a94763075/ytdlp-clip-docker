#!/bin/bash

echo "正在檢查更新..."

# 儲存 git pull --rebase 的輸出
output=$(git pull origin master --rebase)

# 顯示原始輸出
echo "$output"

# 判斷是否已經是最新
if echo "$output" | grep -q "Already up to date."; then
  echo "✅ 已經是最新版本"
else
  echo "✅ 更新完成"
fi
