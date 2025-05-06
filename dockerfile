# ---- 基礎映像 ----
FROM python:3.9

# 安裝系統套件：ffmpeg、curl、make
RUN apt-get update && \
    apt-get install -y ffmpeg curl make && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Poetry（global）
RUN pip install --no-cache-dir poetry

# 工作目錄
WORKDIR /app

# 複製專案依賴定義
COPY pyproject.toml poetry.lock* README.md Makefile ./

# 告訴 Poetry：在專案目錄建立 .venv，並安裝依賴（包括 yt-dlp、flask）
RUN poetry config virtualenvs.create true \
 && poetry config virtualenvs.in-project true \
 && poetry install --no-root --no-interaction --no-ansi


# 複製 Web app 原始碼
COPY app.py ./
COPY templates/ ./templates/


# 暴露 Flask 預設 port
EXPOSE 5000

# 預設啟動：使用 poetry run 來啟動 Flask
ENTRYPOINT ["poetry", "run", "python", "app.py"]
