from werkzeug.utils import safe_join
import subprocess
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, abort


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPLETED_DIR = os.path.join(SCRIPT_DIR, "completed_clips")
os.makedirs(COMPLETED_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "replace_with_random_secret"

active_jobs: dict[str, dict] = {}


# ──────────────────────────────
# 前端頁面
# ──────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ──────────────────────────────
# 提交切片
# ──────────────────────────────
@app.route("/submit_job", methods=["POST"])
def submit_job():
    data = request.get_json(silent=True) or {}
    url = data.get("video_url", "").strip()
    start = data.get("start_time", "").strip()
    end = data.get("end_time", "").strip()
    if not (url and start and end):
        return jsonify(status="error", message="請填入所有欄位！"), 400

    job_id = str(uuid.uuid4())
    filename_base = f"clip_{start.replace(':', '-')}_to_{end.replace(':', '-')}"
    # 這裡假設 Makefile 最終會輸出 mp4 名稱為 <filename_base>.mp4
    cmd = [
        "make",
        "nocookie_clip",
        f"VIDEO_URL={url}",
        f"START_TIME={start}",
        f"END_TIME={end}",
        f"OUTPUT_FILENAME_BASE={filename_base}",
        f"OUTPUT_DIR={COMPLETED_DIR}",
    ]

    try:
        proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR)
        active_jobs[job_id] = dict(
            process=proc, expected=filename_base, status="processing"
        )
        return (
            jsonify(status="success", job_id=job_id, message="已開始處理，請稍候…"),
            202,
        )
    except FileNotFoundError:
        return jsonify(status="error", message="找不到 make，請確認環境"), 500
    except Exception as e:
        return jsonify(status="error", message=f"無法啟動切片：{e}"), 500


# ──────────────────────────────
# 輪詢任務狀態
# ──────────────────────────────
@app.route("/check_status/<job_id>")
def check_status(job_id):
    job = active_jobs.get(job_id)
    if not job:
        return jsonify(status="error", message="無效的任務 ID"), 404

    proc: subprocess.Popen = job["process"]
    rc = proc.poll()
    if rc is None:
        return jsonify(status="processing", message="仍在處理中…")

    # 已結束
    expected = job["expected"]
    mp4_name = next(
        (f for f in os.listdir(COMPLETED_DIR) if expected in f and f.endswith(".mp4")),
        None,
    )

    if rc == 0 and mp4_name:
        job["status"] = "completed"
        job["filename"] = mp4_name
        return jsonify(
            status="completed", message="切片完成！點擊下載", filename=mp4_name
        )
    else:
        job["status"] = "failed"
        return jsonify(
            status="failed", message=f"切片失敗 (code={rc})，請查看伺服器日誌"
        )


# ──────────────────────────────
# 下載檔案
# ──────────────────────────────
@app.route("/download/<path:filename>")
def download(filename):
    """
    只允許下載 completed_clips 目錄內、且存在的 mp4。
    """
    # 1. 防止目錄跳脫
    safe_path = safe_join(COMPLETED_DIR, filename)
    if not safe_path or not os.path.isfile(safe_path):
        abort(404)

    # 2. 讓瀏覽器直接下載
    return send_from_directory(COMPLETED_DIR, filename, as_attachment=True)


# ──────────────────────────────
# 入口
# ──────────────────────────────
if __name__ == "__main__":
    print("⇢ 伺服器啟動 http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
