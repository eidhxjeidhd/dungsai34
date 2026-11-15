import os
import sqlite3
import uuid
from flask import Flask, redirect, render_template_string, request, url_for
from pyngrok import ngrok, conf

app = Flask(__name__)

# Tự động nhận diện Authtoken từ biến môi trường khi chạy lệnh
auth_token = os.environ.get("NGROK_AUTHTOKEN")
if auth_token:
    conf.get_default().auth_token = auth_token

# Khởi tạo Database SQLite cục bộ trên Termux
def init_db():
    conn = sqlite3.connect('cloud.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

PUBLIC_URL = ""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Termux Auto Cloud</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 500px; width: 90%; border: 1px solid #334155; }
        h2 { color: #38bdf8; margin-top: 0; text-align: center; }
        textarea { width: 100%; height: 100px; background: #0f172a; border: 1px solid #334155; color: #e2e8f0; padding: 10px; border-radius: 8px; box-sizing: border-box; resize: vertical; font-size: 14px; }
        button { background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 15px; font-size: 16px; }
        button:hover { background: #0ea5e9; }
        .result { margin-top: 20px; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; word-break: break-all; }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .public-badge { background: #065f46; color: #34d399; padding: 6px 10px; border-radius: 8px; font-size: 12px; margin-bottom: 15px; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>☁️ Termux Auto Cloud</h2>
        <div class="public-badge">🌐 Đang mở online qua Ngrok</div>
        <form action="/add" method="POST">
            <textarea name="content" placeholder="Nhập nội dung cần lưu trữ vào đây..." required></textarea>
            <button type="submit">Tạo Link Lưu Trữ</button>
        </form>
        {% if link %}
        <div class="result">
            <p style="margin:0 0 5px 0; color:#94a3b8; font-size:13px;">Đã tạo link thành công:</p>
            <a href="{{ link }}" target="_blank">{{ link }}</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xem Nội Dung - Cloud</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 600px; width: 90%; border: 1px solid #334155; word-break: break-word; }
        h2 { color: #38bdf8; margin-top: 0; }
        pre { white-space: pre-wrap; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; color: #e2e8f0; font-family: monospace; font-size: 14px; }
        .back { display: inline-block; margin-top: 15px; color: #38bdf8; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📄 Nội Dung Lưu Trữ</h2>
        <pre>{{ content }}</pre>
        <a class="back" href="/">← Quay lại trang chủ</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE, link=None)

@app.route('/add', methods=['POST'])
def add_content():
    content = request.form.get('content')
    if not content:
        return redirect(url_for('home'))
        
    code = str(uuid.uuid4())[:6]
    
    conn = sqlite3.connect('cloud.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO links (code, content) VALUES (?, ?)', (code, content))
    conn.commit()
    conn.close()
    
    link = f"{PUBLIC_URL}/s/{code}"
    return render_template_string(HOME_TEMPLATE, link=link)

@app.route('/s/<code>')
def view_content(code):
    conn = sqlite3.connect('cloud.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM links WHERE code = ?', (code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return render_template_string(VIEW_TEMPLATE, content=row[0])
    else:
        return "<h2 style='text-align:center; color:#ef4444; margin-top:50px; font-family:sans-serif;'>❌ Link không tồn tại hoặc đã bị xóa!</h2>", 404

if __name__ == '__main__':
    public_url = ngrok.connect(5000)
    PUBLIC_URL = str(public_url).split('"')[1]
    
    print(f"\n==============================================")
    print(f"🌐 LINK TRANG CHỦ CÔNG KHAI: {PUBLIC_URL}")
    print(f"==============================================\n")
    
    app.run(host='0.0.0.0', port=5000)
irect(url_for('login'))
    bot_name = request.form.get('bot_name')
    user_id = session['user_id']
    
    default_code = '''import time
import telebot

TOKEN = "ĐIỀN_TOKEN_CỦA_BẠN_VÀO_ĐÂY"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Chào bạn! Bot hoạt động độc lập qua Panel.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Đã nhận: {message.text}")

if __name__ == '__main__':
    bot.infinity_polling()
'''
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO bots (user_id, name, code) VALUES (?, ?, ?)", (user_id, bot_name, default_code))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_bot/<int:bot_id>')
def delete_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if bot_id in running_processes:
        try:
            running_processes[bot_id]['process'].terminate()
        except:
            pass
        del running_processes[bot_id]
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bots WHERE id = ? AND user_id = ?", (bot_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/bot/<int:bot_id>', methods=['GET', 'POST'])
def manage_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, code FROM bots WHERE id = ? AND user_id = ?", (bot_id, session['user_id']))
    bot = c.fetchone()
    conn.close()
    
    if not bot:
        return "Không tìm thấy bot hoặc bạn không có quyền truy cập!", 404
        
    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        code_content = request.form.get('code_content', '')
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE bots SET code = ? WHERE id = ?", (code_content, bot_id))
        conn.commit()
        conn.close()
        
        bot = (bot[0], bot[1], code_content)
        
        temp_file = f"temp_bot_{bot_id}.py"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        if action == 'save_and_run':
            if bot_id in running_processes:
                try:
                    running_processes[bot_id]['process'].terminate()
                except:
                    pass
                del running_processes[bot_id]
                
            process_locks[bot_id] = threading.Lock()
            running_processes[bot_id] = {
                'logs': [f"--- [HỆ THỐNG] Đang khởi động bot {bot[1]}... ---\n"]
            }
            
            try:
                proc = subprocess.Popen(
                    ['python', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                running_processes[bot_id]['process'] = proc
                threading.Thread(target=monitor_bot, args=(bot_id, proc), daemon=True).start()
                message = "✨ Đã lưu code và khởi động bot thành công!"
            except Exception as e:
                message = f"Lỗi khởi động: {str(e)}"
                
        elif action == 'stop':
            if bot_id in running_processes:
                try:
                    running_processes[bot_id]['process'].terminate()
                except:
                    pass
                del running_processes[bot_id]
                message = "🛑 Đã dừng bot thành công!"
            else:
                message = "Bot hiện không chạy."
                
        elif action == 'save':
            message = "💾 Đã lưu thay đổi code thành công!"

    is_running = bot_id in running_processes and running_processes[bot_id]['process'].poll() is None
    logs = running_processes[bot_id]['logs'] if bot_id in running_processes else ["--- Bot chưa được khởi động hoặc đã dừng ---"]

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Quản Lý: {{ bot[1] }}</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; padding: 20px; margin: 0; }
            .container { max-width: 1100px; margin: auto; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 20px; }
            h1 { color: #38bdf8; margin: 0; font-size: 20px; }
            .status-badge { padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; }
            .running { background: #16a34a; color: #fff; }
            .stopped { background: #dc2626; color: #fff; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; }
            h3 { margin-top: 0; color: #cbd5e1; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
            textarea { width: 100%; height: 350px; background: #0f172a; color: #38bdf8; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; box-sizing: border-box; resize: vertical; outline: none; }
            pre.logs { width: 100%; height: 350px; background: #0f172a; color: #00ff00; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; box-sizing: border-box; margin: 0; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; }
            .btn-group { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
            button { flex: 1; padding: 10px; border-radius: 8px; border: none; font-weight: bold; cursor: pointer; font-size: 13px; }
            .btn-save { background: #2563eb; color: #fff; }
            .btn-run { background: #16a34a; color: #fff; }
            .btn-stop { background: #dc2626; color: #fff; }
            .alert { background: #0369a1; color: #fff; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; }
            .back { color: #38bdf8; text-decoration: none; font-weight: bold; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <a href="/" class="back">← Quay lại danh sách</a>
                    <h1 style="display:inline-block; margin-left:15px;">⚙️ Quản lý Bot: {{ bot[1] }}</h1>
                </div>
                <div>
                    {% if is_running %}
                        <span class="status-badge running">● Đang Chạy</span>
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
                        <textarea name="code_content" spellcheck="false">{{ bot[2] }}</textarea>
                        <div class="btn-group">
                            <button type="submit" name="action" value="save" class="btn-save">💾 Chỉ Lưu</button>
                            <button type="submit" name="action" value="save_and_run" class="btn-run">🚀 Lưu & Chạy</button>
                            <button type="submit" name="action" value="stop" class="btn-stop">🛑 Dừng</button>
                        </div>
                    </form>
                </div>

                <!-- Cột 2: Logs -->
                <div class="card">
                    <h3>
                        📊 Nhật Ký Hoạt Động (Logs)
                        <button onclick="location.reload()" style="background: #334155; color: #fff; padding: 4px 10px; font-size: 11px; border-radius: 4px; border:none; cursor:pointer;">🔄 Làm mới</button>
                    </h3>
                    <pre class="logs" id="logBox">{% for line in logs %}{{ line }}{% endfor %}</pre>
                </div>
            </div>
        </div>
        <script>
            const logBox = document.getElementById('logBox');
            logBox.scrollTop = logBox.scrollHeight;
        </script>
    </body>
    </html>
    ''', bot=bot, is_running=is_running, logs=logs, message=message)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
