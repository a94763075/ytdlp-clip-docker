from flask import Flask, render_template, request, jsonify
import subprocess
import os
import uuid  # 用於產生獨特的任務 ID

# --- 設定 ---
# 取得此腳本所在的目錄
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# 設定輸出目錄為腳本所在目錄下的 'completed_clips' 子目錄 (推薦用於本機執行)
COMPLETED_DIR = os.path.join(SCRIPT_DIR, "completed_clips")
# 如果您在 Docker 中執行，請改回:
# COMPLETED_DIR = "/app/completed_clips"

# 建立輸出目錄 (如果它不存在的話)
if not os.path.exists(COMPLETED_DIR):
    try:
        os.makedirs(COMPLETED_DIR)
        print(f"--- Info: Created directory: {COMPLETED_DIR}")
    except OSError as e:
        print(f"--- Error: Could not create directory {COMPLETED_DIR}: {e}")
        # 如果目錄無法建立，可能後續會出錯，這裡先印出錯誤

app = Flask(__name__)
# 請在生產環境中替換為一個真正隨機且保密的金鑰
app.secret_key = "replace_with_a_random_secret_for_production"

# 用來儲存進行中的任務: {job_id: {'process': Popen物件, 'expected_filename_part': 檔名部分, ...}}
active_jobs = {}


@app.route("/")
def index():
    # 渲染主頁面
    return render_template("index.html")


@app.route("/submit_job", methods=["POST"])
def submit_job():
    data = request.get_json()
    url = data.get("video_url", "").strip()
    start = data.get("start_time", "").strip()
    end = data.get("end_time", "").strip()

    if not url or not start or not end:
        return jsonify({"status": "error", "message": "請填入所有欄位！"}), 400

    job_id = str(uuid.uuid4())
    # 清理時間字串，用於檔名 (將 ':' 替換為 '-')
    safe_start = start.replace(":", "-")
    safe_end = end.replace(":", "-")
    # 預期的檔名基礎部分 (Makefile 應該基於此建立最終檔名)
    expected_filename_part = f"回放片段_{safe_start}_to_{safe_end}"

    # 準備執行 make 命令
    # 假設您的 Makefile 在專案根目錄 (與 app.py 同層)
    # 如果 Makefile 在不同位置，請調整 cwd
    project_root = SCRIPT_DIR  # 使用腳本所在目錄作為專案根目錄 (推薦用於本機)
    # 如果在 Docker 中，且您的工作目錄是 /app，則改回:
    # project_root = "/app"

    cmd = [
        "make",
        "nocookie_clip",  # 假設這是 Makefile 中的目標(target)
        f"VIDEO_URL={url}",
        f"START_TIME={start}",
        f"END_TIME={end}",
        f"JOB_ID={job_id}",  # 可以傳遞 job_id 給 make，如果需要用它命名
        f"OUTPUT_FILENAME_BASE={expected_filename_part}",  # 傳遞檔名基礎部分
        # 傳遞輸出目錄給 Makefile (可選，但建議)
        f"OUTPUT_DIR={os.path.abspath(COMPLETED_DIR)}",
    ]
    # 確保 Makefile 中的 'nocookie_clip' 目標能夠接收並使用這些變數，
    # 特別是將輸出檔案放到 OUTPUT_DIR 指定的目錄下，
    # 並可能使用 OUTPUT_FILENAME_BASE 來命名 (例如 "{OUTPUT_FILENAME_BASE}.mp4")。

    env = os.environ.copy()
    # 這行是針對特定 Linux/Docker 環境下 yt-dlp 尋找 Chrome cookie 的設定，
    # 如果您在本機 macOS 且 yt-dlp 能直接找到 cookie，可能不需要設定。
    # env["XDG_CONFIG_HOME"] = "/root/.config" # 在本機 macOS 可能不需要

    try:
        print(f"--- Info: Running command: {' '.join(cmd)} in {project_root}")
        # 在背景執行 make 命令
        process = subprocess.Popen(cmd, cwd=project_root, env=env)
        active_jobs[job_id] = {
            "process": process,
            "expected_filename_part": expected_filename_part,
            "start_time_req": start,
            "end_time_req": end,
            "status": "processing",
        }
        # 給使用者的初始檔名提示 (最終檔名由 Makefile 決定)
        user_friendly_output_name = f"{expected_filename_part}.mp4"
        print(
            f"--- Info: Job {job_id} started. Expecting file like '{expected_filename_part}.mp4' in {COMPLETED_DIR}"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"切片已啟動，預計檔名：{user_friendly_output_name}。正在處理中...",
                    "job_id": job_id,
                }
            ),
            202,
        )  # HTTP 狀態碼 202 Accepted

    except FileNotFoundError:
        # 如果 'make' 命令本身找不到
        print(f"--- Error: 'make' command not found. Is make installed and in PATH?")
        return (
            jsonify(
                {"status": "error", "message": f"啟動切片失敗：找不到 'make' 命令。"}
            ),
            500,
        )
    except Exception as e:
        print(f"--- Error: Failed to start job {job_id}: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"啟動切片失敗：{str(e)}",
                },
            ),
            500,
        )


@app.route("/check_status/<job_id>", methods=["GET"])
def check_status(job_id):
    job = active_jobs.get(job_id)
    if not job:
        print(f"--- Warning: Status check for invalid job ID: {job_id}")
        return jsonify({"status": "error", "message": "無效的任務 ID"}), 404

    process = job["process"]
    return_code = process.poll()  # 檢查行程是否已終止

    if return_code is None:
        # 行程仍在執行中
        # print(f"--- Debug: Job {job_id} is still processing.") # 可選：印出仍在處理的訊息
        return jsonify({"status": "processing", "message": "仍在處理中..."})
    else:
        # 行程已結束
        print(f"--- Info: Job {job_id} finished with return code: {return_code}")
        found_file = None
        absolute_completed_dir = ""  # 初始化變數

        # --- 加入除錯資訊 START ---
        try:
            # 1. 取得並印出 COMPLETED_DIR 的絕對路徑
            absolute_completed_dir = os.path.abspath(COMPLETED_DIR)
            print(f"--- 除錯：正在此絕對路徑中搜尋檔案: {absolute_completed_dir}")

            # 2. 取得並印出該目錄下的所有檔案和子目錄名稱
            dir_contents = os.listdir(COMPLETED_DIR)
            print(f"--- 除錯：目錄 {absolute_completed_dir} 中的內容: {dir_contents}")

        except FileNotFoundError:
            # 如果 COMPLETED_DIR 本身就不存在
            print(
                f"--- 除錯：錯誤 - 找不到目錄: {COMPLETED_DIR} (絕對路徑: {os.path.abspath(COMPLETED_DIR)})"
            )
            dir_contents = []  # 設為空列表，避免下面的迴圈出錯
        except Exception as e:
            # 其他讀取目錄時可能發生的錯誤
            print(f"--- 除錯：讀取目錄 {COMPLETED_DIR} 時發生錯誤: {e}")
            dir_contents = []  # 設為空列表
        # --- 加入除錯資訊 END ---

        # 現在用上面取得的 dir_contents 列表來尋找檔案
        for f_name in dir_contents:
            # print(f"--- 除錯：正在比對 '{job['expected_filename_part']}' 與 '{f_name}'") # 可選的詳細比對
            # 修正：確保 expected_filename_part 沒有額外空格，並檢查 f_name 是否包含它
            # 注意：如果檔名有空格問題，最根本的解決方法是修正 Makefile 的檔名產生邏輯
            if job["expected_filename_part"].strip() in f_name and f_name.endswith(
                ".mp4"
            ):
                found_file = f_name
                print(f"--- 除錯：找到匹配檔案: {found_file}")  # 印出找到的檔案
                break  # 找到就跳出迴圈

        # --- 後續的判斷邏輯 ---
        final_message = ""
        if return_code == 0 and found_file:
            full_found_path = os.path.join(absolute_completed_dir, found_file)
            print(f"--- 除錯：找到檔案的完整路徑: {full_found_path}")
            # 修改成功訊息，讓使用者知道檔案在哪裡
            final_message = (
                f"切片完成！檔案 '{found_file}' 已儲存於 '{COMPLETED_DIR}' 目錄。"
            )
            job["status"] = "completed"
            job["final_filename"] = found_file
            print(f"--- Info: Job {job_id} completed successfully. File: {found_file}")

        elif return_code == 0 and not found_file:
            final_message = f"處理完成但無法在 '{COMPLETED_DIR}' 中找到預期的輸出檔案 ({job['expected_filename_part']}.mp4)。請檢查 Makefile 的輸出路徑和檔名設定。"
            job["status"] = "error_finding_file"
            print(
                f"--- Warning: Job {job_id} finished (code 0) but output file not found in {COMPLETED_DIR}. Expected pattern: {job['expected_filename_part']}"
            )

        else:  # return_code != 0
            final_message = f"切片失敗。錯誤碼：{return_code}。請檢查終端機中的 'make' 命令輸出或伺服器日誌獲取詳細資訊。 可以換個“網路 IP” 試試看 或等一個小時後再試試看 或先測試其他影片可否下載"
            job["status"] = "failed"
            print(f"--- Error: Job {job_id} failed with return code {return_code}.")

        # 注意：這裡沒有立即從 active_jobs 中刪除任務，以便前端可以重複查詢最終狀態。
        # 在實際應用中，您可能需要一個清理機制來移除舊的已完成或失敗的任務。

        return jsonify(
            {
                "status": job["status"],
                "message": final_message,
                "filename": job.get("final_filename"),  # 如果成功找到檔案，這裡會有檔名
            }
        )


if __name__ == "__main__":
    print(f"--- Starting Flask server ---")
    print(f"--- Output directory set to: {os.path.abspath(COMPLETED_DIR)}")
    # 綁定到 0.0.0.0 使其可以從外部網路訪問 (例如在 Docker 中或需要區域網路訪問時)
    # debug=True 會在程式碼變更時自動重載伺服器，並提供更詳細的錯誤頁面，生產環境中應設為 False
    app.run(host="0.0.0.0", port=5001, debug=True)
