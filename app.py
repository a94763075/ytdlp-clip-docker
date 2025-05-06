from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"

# 預設 Chrome Profile 路徑
CHROME_PROFILE = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default"
)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("video_url", "").strip()
        start = request.form.get("start_time", "").strip()
        end = request.form.get("end_time", "").strip()
        if not url or not start or not end:
            flash("請填入所有欄位！", "error")
            return redirect(url_for("index"))

        # 在 container 裡執行 Makefile 裡的 clip 目標

        # "nocookie_clip", 先不使用 cookie

        cmd = [
            "make",
            "nocookie_clip",
            f"VIDEO_URL={url}",
            f"START_TIME={start}",
            f"END_TIME={end}",
        ]

        # 這裡同時傳入環境變數，讓 yt-dlp 找到 Chrome cookie
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = (
            "/root/.config"  # 讓 yt-dlp 等工具看到 ~/.config/google-chrome
        )

        # 執行切片指令
        try:
            subprocess.Popen(cmd, cwd="/app", env=env)
        except Exception as e:
            flash(f"切片失敗：{e}", "error")
            return redirect(url_for("index"))

        # 建立輸出檔名
        out_name = f"回放片段_{start.replace(':','-')}_to_{end.replace(':','-')}.mp4"
        flash(f"切片已啟動，檔名：{out_name}，完成後請到專案目錄查看。", "success")
        return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    # 綁到 0.0.0.0，外部才能連
    app.run(host="0.0.0.0", port=5001)
