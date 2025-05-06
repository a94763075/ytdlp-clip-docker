#!/bin/bash

cd "$(dirname "$0")"

# 建立（可選）image
docker build -t yt-clipper .