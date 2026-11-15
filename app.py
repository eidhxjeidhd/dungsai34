import os
import subprocess
import threading
from flask import Flask, render_template_string, request

app = Flask(__name__)

RUNNING_PROCESS = None
BOT_LOGS = []
LOG_LOCK = threading.Lock()
BOT_FILE = "running_bot.py"

def monitor_process(proc):
    global RUNNING_PROCESS
    for line in proc.stdout:
        with LOG_LOCK:
            BOT_LOGS.append(line)
            if len(BOT_LOGS) > 150:
                BOT_LOGS.pop(0)

@app.route('/', methods=['GET', 'POST'])
def index():
    global RUNNING_PROCESS, BOT_LOGS
    message = ""
    
    # Lấy code cũ nếu có, nếu chưa thì hiển thị code mẫu
    if os.path.exists(BOT_FILE):
        with open(BOT_FILE, 'r', encoding='utf-8') as f:
            code_content = f.read()
    else:
        code_content = '''import time
import telebot

TOKEN = "ĐIỀN_TOKEN_CỦA_BẠN_VÀO_ĐÂY"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name or "bạn"
    bot.reply_to(message, f"👋 Chào {user_name}! Bot chạy trên Cloud Panel của ông đã lên sóng thành công 24/7! 🚀")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    text = message.text
    bot.reply_to(message, f"🤖 Bot đã nhận: '{text}'. Hệ thống đang chạy rất mượt! 💯")

if __name__ == '__main__':
    bot.infinity_polling()
'''

    if request.method == 'POST':
        action = request.form.get('action')
        code_content = request.form.get('code_content', '')
        
        # Lưu code vào file
        with open(BOT_FILE, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        if action == 'save_and_run':
            # Dừng tiến trình cũ nếu đang chạy
            if RUNNING_PROCESS and RUNNING_PROCESS.poll() is None:
                try:
                    RUNNING_PROCESS.terminate()
                except:
                    pass
            
            with LOG_LOCK:
                BOT_LOGS = ["--- [HỆ THỐNG] Đang khởi động code mới... ---\n"]
            
            try:
                proc = subprocess.Popen(
                    ['python', BOT_FILE],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                RUNNING_PROCESS = proc
                threading.Thread(target=monitor_process, args=(proc,), daemon=True).start()
                message = "✨ Đã lưu code và khởi động lại bot thành công!"
            except Exception as e:
                message = f"Lỗi khởi động: {str(e)}"
                
        elif action == 'stop':
            if RUNNING_PROCESS and RUNNING_PROCESS.poll() is None:
                try:
                    RUNNING_PROCESS.terminate()
                except:
                    pass
                message = "🛑 Đã dừng bot thành công!"
            else:
                message = "Bot hiện không chạy."
        elif action == 'save':
            message = "💾 Đã lưu code thành công!"

    is_running = RUNNING_PROCESS is not None and RUNNING_PROCESS.poll() is None
    with LOG_LOCK:
        current_logs = list(BOT_LOGS) if BOT_LOGS else ["--- [HỆ THỐNG] Chưa có log nào ---"]

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Cloud Bot Panel</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; padding: 15px; margin: 0; }
            .container { max-width: 1200px; margin: auto; }
            .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 12px 20px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; }
            h1 { color: #38bdf8; margin: 0; font-size: 18px; }
            .status-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 12px; }
            .running { background: #16a34a; color: #fff; }
            .stopped { background: #dc2626; color: #fff; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            @media(max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; }
            h3 { margin-top: 0; color: #cbd5e1; font-size: 14px; display: flex; justify-content: space-between; align-items: center; }
            textarea { width: 100%; height: 350px; background: #0f172a; color: #38bdf8; border: 1px solid #475569; border-radius: 6px; padding: 10px; font-family: monospace; font-size: 12px; box-sizing: border-box; resize: vertical; outline: none; }
            pre.logs { width: 100%; height: 350px; background: #0f172a; color: #00ff00; border: 1px solid #475569; border-radius: 6px; padding: 10px; font-family: monospace; font-size: 12px; box-sizing: border-box; margin: 0; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; }
            .btn-group { margin-top: 12px; display: flex; gap: 8px; }
            button { flex: 1; padding: 10px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; font-size: 12px; }
            .btn-save { background: #2563eb; color: #fff; }
            .btn-run { background: #16a34a; color: #fff; }
            .btn-stop { background: #dc2626; color: #fff; }
            .alert { background: #0369a1; color: #fff; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; }
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
                <div class="card">
                    <h3>📝 Trình Soạn Thảo Code Python</h3>
                    <form method="POST">
                        <textarea name="code_content" spellcheck="false">{{ code_content }}</textarea>
                        <div class="btn-group">
                            <button type="submit" name="action" value="save" class="btn-save">💾 Lưu</button>
                            <button type="submit" name="action" value="save_and_run" class="btn-run">🚀 Lưu & Chạy Lại</button>
                            <button type="submit" name="action" value="stop" class="btn-stop">🛑 Dừng</button>
                        </div>
                    </form>
                </div>

                <div class="card">
                    <h3>
                        📊 Nhật Ký Hoạt Động (Logs)
                        <button onclick="location.reload()" style="background: #334155; color: #fff; padding: 3px 8px; font-size: 11px; border-radius: 4px; border:none; cursor:pointer;">🔄 Làm mới</button>
                    </h3>
                    <pre class="logs" id="logBox">{% for line in current_logs %}{{ line }}{% endfor %}</pre>
                </div>
            </div>
        </div>
        <script>
            const logBox = document.getElementById('logBox');
            logBox.scrollTop = logBox.scrollHeight;
        </script>
    </body>
    </html>
    ''', code_content=code_content, is_running=is_running, current_logs=current_logs, message=message)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
