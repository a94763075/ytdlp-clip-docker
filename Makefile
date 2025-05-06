# 可自訂變數 (這些可以被來自 app.py 的指令行參數覆蓋)
VIDEO_URL ?= https://www.youtube.com/watch?v=-wiI0DwP5bY
START_TIME ?= 00:00
END_TIME ?= 00:10

# --- 新增：輸出目錄和檔名基礎的預設值 ---
# 使用 ?=，這樣只有在沒有從指令行傳入這些變數時，才會使用這些預設值
# app.py 在呼叫 make 時會傳入這些變數
OUTPUT_DIR ?= completed_clips
OUTPUT_FILENAME_BASE ?= 回放片段_$(subst :, -, $(START_TIME))_to_$(subst :, -, $(END_TIME))

# --- 舊的寫死輸出名稱 (註解掉或刪除) ---
# OUTPUT_NAME = downloads/回放片段_$(subst :, -, $(START_TIME))_to_$(subst :, -, $(END_TIME)).mp4

# yt-dlp 執行路徑 (在 poetry 虛擬環境中)
# 注意：如果在 Docker 容器中執行，要確保 poetry 或 yt-dlp 是可用的
# 如果 Docker 映像中是全域安裝的 yt-dlp，可以改成 YTDLP = yt-dlp
YTDLP = poetry run yt-dlp
# YTDLP = yt-dlp # 如果是全域安裝或不在 poetry 環境

# 升級 yt-dlp
update:
	poetry add yt-dlp@latest

# 下載影片片段 (使用 cookie)
clip:
	@echo "--- Running Target: clip ---"
	@echo "Output Directory: $(OUTPUT_DIR)"
	@echo "Output Filename Base: $(OUTPUT_FILENAME_BASE)"
	# 確保輸出目錄存在
	@mkdir -p "$(OUTPUT_DIR)"
	# 使用組合的路徑和檔名基礎
	$(YTDLP) --extractor-args "youtube:player_client=chrome" \
		--format "bestvideo[height<=1080][fps<=60]+bestaudio/best[height<=1080][fps<=60]" \
		--cookies-from-browser chrome \
		"$(VIDEO_URL)" \
		--merge-output-format mp4 \
		--download-sections "*$(START_TIME)-$(END_TIME)" \
		--force-keyframes-at-cuts \
		-o "$(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4" # <--- 修改這裡
	@echo "Output saved to: $(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4"
	@echo "--- Target Finished: clip ---"


# 列出影片格式
formats:
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		--cookies-from-browser chrome \
		"$(VIDEO_URL)" --list-formats


# 不使用 cookie 下載影片片段 (舊版，可選修改或刪除)
nocookie_clip_old:
	@echo "--- Running Target: nocookie_clip_old ---"
	@echo "Output Directory: $(OUTPUT_DIR)"
	@echo "Output Filename Base: $(OUTPUT_FILENAME_BASE)"
	@mkdir -p "$(OUTPUT_DIR)"
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		"$(VIDEO_URL)" \
		--merge-output-format mp4 \
		--progress-template "download:進度 %(progress._percent_str)s | 速度 %(progress._speed_str)s | 剩餘時間 %(progress._eta_str)s" \
		--download-sections "*$(START_TIME)-$(END_TIME)" \
		--force-keyframes-at-cuts \
		-o "$(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4" # <--- 修改這裡
	@echo "Output saved to: $(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4"
	@echo "--- Target Finished: nocookie_clip_old ---"

# 不使用 cookie 下載影片片段 (這是 app.py 主要呼叫的目標)
nocookie_clip:
	@echo "--- Running Target: nocookie_clip ---"
	@echo "Input URL: $(VIDEO_URL)"
	@echo "Start Time: $(START_TIME)"
	@echo "End Time: $(END_TIME)"
	@echo "Output Directory: $(OUTPUT_DIR)"
	@echo "Output Filename Base: $(OUTPUT_FILENAME_BASE)"
	# 確保輸出目錄存在
	@mkdir -p "$(OUTPUT_DIR)"
	# 使用組合的路徑和檔名基礎
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		"$(VIDEO_URL)" \
		--downloader ffmpeg \
		--external-downloader-args "-stats -loglevel warning" \
		--merge-output-format mp4 \
		--progress-template "download:進度 %(progress._percent_str)s | 速度 %(progress._speed_str)s | 剩餘時間 %(progress._eta_str)s" \
		--download-sections "*$(START_TIME)-$(END_TIME)" \
		--force-keyframes-at-cuts \
		-o "$(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4" # <--- 修改這裡
	@echo "Output saved to: $(OUTPUT_DIR)/$(OUTPUT_FILENAME_BASE).mp4"
	@echo "--- Target Finished: nocookie_clip ---"

# .PHONY: update clip formats nocookie_clip_old nocookie_clip # 可選：宣告哪些不是檔案名稱