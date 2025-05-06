
# 🎬 YouTube Clipper

Flask 網頁應用，可下載 YouTube 影片片段（剪輯），支援 yt-dlp、自動剪輯與 Chrome 資料夾掛載。

---

## 📦 環境需求

- Python 3.9+
- [Poetry](https://python-poetry.org/)
- Docker（可選）

---

## 🚀 本地開發（不使用 Docker）

1. 安裝 Poetry

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2. 安裝相依套件

    ```bash
    poetry install
    ```

3. 執行應用程式

    ```bash
    # 預設埠號為 5000
    poetry run python3 -m app
    ```

    若要改用其他埠號（例如 5001）：

    ```bash
    poetry run python3 -m app --port 5001
    ```

---

## 🐳 使用 Docker 執行

1. 建立 Docker 映像檔

    ```bash
    docker build -t yt-clipper .
    ```

2. 執行容器（包含 Chrome cookie，以支援私人影片或高齡限制）

    ```bash
    docker run -p 5001:5001 --rm --name my-clipper \
      -v "$HOME/Library/Application Support/Google/Chrome/Default:/root/.config/google-chrome/Default:ro" \
      -v "$(pwd)/downloads:/app/downloads" \
      -e FLASK_SECRET_KEY='your_very_secret_random_key' \
      yt-clipper
    ```

3. 不使用 cookie

    ```bash
    docker run -p 5001:5001 --rm --name my-clipper \
      -v "$(pwd)/downloads:/app/downloads" \
      -e FLASK_SECRET_KEY='your_very_secret_random_key' \
      yt-clipper
    ```

所有下載的影片會儲存在本機的 `downloads/` 資料夾中。

---

## ✅ CI 狀態與自動測試

本專案已整合以下 GitHub Actions 自動化流程：

### 🔎 一般程式碼檢查 CI

- 使用 [flake8](https://flake8.pycqa.org/) 執行 Python 程式碼風格與潛在錯誤檢查
- 自動掃描 `app.py` 是否有未使用的 import、語法錯誤、過長行等問題
- 可在 `.flake8` 調整規則

### 🔐 安全性掃描 CI

- 整合 [Bandit](https://bandit.readthedocs.io/) 進行 Python 程式安全性分析
- 可檢測如 `eval()`、硬編碼密碼、Flask debug 模式等常見風險
- CI 自動執行 `bandit -r app.py` 並回報結果

CI 會在每次 Push / Pull Request 時自動觸發，確保程式碼品質與穩定性。

---

## 📁 專案結構

```

.
├── app.py                  # 主應用程式入口
├── templates/              # Flask HTML templates
├── downloads/              # 影片下載目錄（Docker 掛載）
├── pyproject.toml          # Poetry 專案定義
├── poetry.lock             # 鎖定依賴版本
├── Makefile                # 自動化指令（可選）
└── Dockerfile              # Docker 設定

```

---

## ⚙️ 環境變數

| 變數名稱             | 說明                     | 範例                              |
| -------------------- | ------------------------ | --------------------------------- |
| `FLASK_SECRET_KEY`   | Flask Session 加密金鑰   | `your_very_secret_random_key`     |

---

## 📊 速率限制參考（預設設定）

- 訪客模式：約 300 部影片／小時（約 1,000 次請求）
- 登入帳號：約 2,000 部影片／小時（約 4,000 次請求）

---

## 📝 TODO

- [ ] 支援影片剪輯參數（`start` / `end`）
- [ ] 支援多影片批次處理
- [ ] 支援格式選擇與字幕下載

---

## 🧑‍💻 作者

Created by [Jonah Yen](https://github.com/your-username) — MIT License

---

### 參考

- [yt-dlp Extractors: Logging in with OAuth](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#logging-in-with-oauth)

