import os
import subprocess
import threading
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Tên file chứa code người dùng
USER_CODE_FILE = 'user_script.py'

# Biến toàn cục quản lý tiến trình bot đang chạy
bot_process = None
bot_logs = []
log_lock = threading.Lock()

# Tạo file code mẫu ban đầu nếu chưa có
if not os.path.exists(USER_CODE_FILE):
    with open(USER_CODE_FILE, 'w', encoding='utf-8') as f:
        f.write('''# --- DÁN CODE BOT HOẶC SCRIPT PYTHON CỦA BẠN VÀO ĐÂY ---
import time

print("🤖 Bot mẫu đang khởi động...")
while True:
    print("Bot đang hoạt động 24/7...")
    time.sleep(5)
''')

def monitor_process(process):
    """Đọc log từ tiến trình đang chạy và lưu lại"""
    global bot_logs
    for line in process.stdout:
        with log_lock:
            bot_logs.append(line)
            if len(bot_logs) > 150:  # Giữ lại 150 dòng log gần nhất
                bot_logs.pop(0)

def start_bot():
    """Khởi động tiến trình chạy file code của người dùng"""
    global bot_process, bot_logs
    stop_bot()
    
    with log_lock:
        bot_logs.append("--- [HỆ THỐNG] Đang khởi động code mới... ---\n")
        
    try:
        # Chạy file user_script.py bằng Python dưới dạng tiến trình nền
        bot_process = subprocess.Popen(
            ['python', USER_CODE_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        # Chạy luồng đọc log song song để không làm nghẽn web
        threading.Thread(target=monitor_process, args=(bot_process,), daemon=True).start()
    except Exception as e:
        with log_lock:
            bot_logs.append(f"--- [LỖI] Không thể chạy code: {str(e)} ---\n")

def stop_bot():
    """Dừng tiến trình bot hiện tại nếu đang chạy"""
    global bot_process, bot_logs
    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=3)
        except:
            bot_process.kill()
        bot_process = None
        with log_lock:
            bot_logs.append("--- [HỆ THỐNG] Đã dừng tiến trình cũ. ---\n")

@app.route('/', methods=['GET', 'POST'])
def index():
    global bot_logs
    
    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_and_run':
            # Lấy code mới từ trình soạn thảo trên web
            new_code = request.form.get('code_content', '')
            
            # Ghi đè vào file code
            with open(USER_CODE_FILE, 'w', encoding='utf-8') as f:
                f.write(new_code)
                
            # Khởi động lại bot với code mới
            start_bot()
            message = "✨ Đã lưu code mới và khởi động lại bot thành công!"
            
        elif action == 'stop':
            stop_bot()
            message = "🛑 Đã dừng bot thành công!"

    # Đọc nội dung code hiện tại để hiển thị lên khung soạn thảo
    current_code = ""
    if os.path.exists(USER_CODE_FILE):
        with open(USER_CODE_FILE, 'r', encoding='utf-8') as f:
            current_code = f.read()

    # Kiểm tra trạng thái bot đang chạy hay không
    is_running = bot_process is not None and bot_process.poll() is None

    html = '''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Cloud Bot Panel - Thay Đổi Code Trực Tuyến</title>
        <style>
            body { background: #090d16; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; margin: 0; }
            .container { max-width: 1100px; margin: auto; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 20px; }
            h1 { color: #38bdf8; margin: 0; font-size: 22px; }
            .status-badge { padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; }
            .running { background: #16a34a; color: #fff; }
            .stopped { background: #dc2626; color: #fff; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; }
            h3 { margin-top: 0; color: #cbd5e1; font-size: 16px; display: flex; justify-content: space-between; align-items: center; }
            textarea { width: 100%; height: 380px; background: #0f172a; color: #38bdf8; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: 'Courier New', Courier, monospace; font-size: 13px; box-sizing: border-box; resize: vertical; outline: none; }
            pre.logs { width: 100%; height: 380px; background: #0f172a; color: #00ff00; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: 'Courier New', Courier, monospace; font-size: 13px; box-sizing: border-box; margin: 0; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; }
            .btn-group { margin-top: 15px; display: flex; gap: 10px; }
            button { flex: 1; padding: 12px; border-radius: 8px; border: none; font-weight: bold; cursor: pointer; font-size: 14px; }
            .btn-save { background: #16a34a; color: #fff; }
            .btn-save:hover { background: #15803d; }
            .btn-stop { background: #dc2626; color: #fff; }
            .btn-stop:hover { background: #b91c1c; }
            .alert { background: #0369a1; color: #fff; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Cloud Bot Panel (Hot-Reload Code)</h1>
                <div>
                    {% if is_running %}
                        <span class="status-badge running">● Đang Chạy 24/7</span>
                    {% else %}
                        <span class="status-badge stopped">■ Đã Dừng</span>
                    {% endif %}
                </div>
            </div>

            {% if message %}
                <div class="alert">{{ message }}</div>
            {% endif %}

            <div class="grid">
                <!-- Cột 1: Soạn thảo code -->
                <div class="card">
                    <h3>📝 Trình Soạn Thảo Code Python</h3>
                    <form method="POST">
                        <textarea name="code_content" spellcheck="false">{{ current_code }}</textarea>
                        <div class="btn-group">
                            <button type="submit" name="action" value="save_and_run" class="btn-save">💾 Lưu & Chạy Lại Code Mới</button>
                            <button type="submit" name="action" value="stop" class="btn-stop">🛑 Dừng Bot</button>
                        </div>
                    </form>
                </div>

                <!-- Cột 2: Xem Log thời gian thực -->
                <div class="card">
                    <h3>
                        📊 Nhật Ký Hoạt Động (Logs)
                        <button onclick="location.reload()" style="background: #334155; color: #fff; padding: 4px 10px; font-size: 11px; border-radius: 4px; border:none; cursor:pointer;">🔄 Làm mới log</button>
                    </h3>
                    <pre class="logs" id="logBox">{% for line in logs %}{{ line }}{% endfor %}</pre>
                </div>
            </div>
        </div>

        <script>
            // Tự động cuộn log xuống dưới cùng
            const logBox = document.getElementById('logBox');
            logBox.scrollTop = logBox.scrollHeight;
        </script>
    </body>
    </html>
    '''
    
    with log_lock:
        logs_copy = list(bot_logs)
        
    return render_template_string(html, current_code=current_code, is_running=is_running, logs=logs_copy, message=message)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
