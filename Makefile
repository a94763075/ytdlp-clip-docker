# 可自訂變數
VIDEO_URL = https://www.youtube.com/watch?v=-wiI0DwP5bY
START_TIME = 16:15
END_TIME = 18:40
OUTPUT_NAME = 回放片段_$(subst :, -, $(START_TIME))_to_$(subst :, -, $(END_TIME)).mp4

# yt-dlp 執行路徑 (在 poetry 虛擬環境中)
YTDLP = poetry run yt-dlp

# 升級 yt-dlp
update:
	poetry add yt-dlp@latest

# 下載影片片段
clip:
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		--cookies-from-browser chrome \
		"$(VIDEO_URL)" \
		--merge-output-format mp4 \
		--download-sections "*$(START_TIME)-$(END_TIME)" \
		--force-keyframes-at-cuts \
		-o "$(OUTPUT_NAME)"

# 列出影片格式
formats:
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		--cookies-from-browser chrome \
		"$(VIDEO_URL)" --list-formats


# 不使用 cookie 下載影片片段
nocookie_clip:
	$(YTDLP) --extractor-args "youtube:player_client=web_safari" \
		"$(VIDEO_URL)" \
		--merge-output-format mp4 \
		--download-sections "*$(START_TIME)-$(END_TIME)" \
		--force-keyframes-at-cuts \
		-o "$(OUTPUT_NAME)"

