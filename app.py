import os
import sqlite3
import subprocess
import threading
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_cloud_panel'

DB_FILE = 'panel_database.db'

# Lưu trữ tiến trình bot đang chạy theo bot_id: {'process': proc, 'logs': []}
running_processes = {}
process_locks = {}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    code TEXT)''')
    conn.commit()
    conn.close()

init_db()

def monitor_bot(bot_id, process):
    for line in process.stdout:
        if bot_id not in running_processes:
            break
        with process_locks[bot_id]:
            running_processes[bot_id]['logs'].append(line)
            if len(running_processes[bot_id]['logs']) > 150:
                running_processes[bot_id]['logs'].pop(0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and user[1] == password:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Tài khoản hoặc mật khẩu không chính xác!"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Đăng Nhập - Cloud Bot Panel</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: #1e293b; padding: 30px; border-radius: 12px; width: 320px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            input { width: 100%; padding: 10px; margin: 10px 0; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #16a34a; border: none; color: #fff; font-weight: bold; border-radius: 6px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #15803d; }
            .link { text-align: center; margin-top: 15px; font-size: 13px; }
            .link a { color: #38bdf8; text-decoration: none; }
            .error { color: #ef4444; font-size: 13px; text-align: center; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🔑 Đăng Nhập</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Tên đăng nhập" required>
                <input type="password" name="password" placeholder="Mật khẩu" required>
                <button type="submit">Đăng Nhập</button>
            </form>
            <div class="link">Chưa có tài khoản? <a href="/register">Đăng ký ngay</a></div>
        </div>
    </body>
    </html>
    ''', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            success = "Đăng ký thành công! Hãy đăng nhập."
        except sqlite3.IntegrityError:
            error = "Tên đăng nhập đã tồn tại!"
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Đăng Ký - Cloud Bot Panel</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: #1e293b; padding: 30px; border-radius: 12px; width: 320px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            input { width: 100%; padding: 10px; margin: 10px 0; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #2563eb; border: none; color: #fff; font-weight: bold; border-radius: 6px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #1d4ed8; }
            .link { text-align: center; margin-top: 15px; font-size: 13px; }
            .link a { color: #38bdf8; text-decoration: none; }
            .error { color: #ef4444; font-size: 13px; text-align: center; margin-bottom: 10px; }
            .success { color: #22c55e; font-size: 13px; text-align: center; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>📝 Đăng Ký</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success">{{ success }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Tên đăng nhập" required>
                <input type="password" name="password" placeholder="Mật khẩu" required>
                <button type="submit">Đăng Ký</button>
            </form>
            <div class="link">Đã có tài khoản? <a href="/login">Đăng nhập</a></div>
        </div>
    </body>
    </html>
    ''', error=error, success=success)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM bots WHERE user_id = ?", (user_id,))
    bots = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Quản Lý Bot - Cloud Panel</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; padding: 20px; margin: 0; }
            .container { max-width: 900px; margin: auto; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 20px; }
            h1 { color: #38bdf8; margin: 0; font-size: 22px; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
            input, button { padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; }
            button { background: #16a34a; font-weight: bold; cursor: pointer; border: none; }
            button:hover { background: #15803d; }
            .bot-item { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 12px 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; }
            .bot-actions a { color: #38bdf8; text-decoration: none; margin-right: 15px; font-weight: bold; }
            .bot-actions a.delete { color: #ef4444; }
            .logout { background: #dc2626; color: #fff; padding: 8px 15px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Danh Sách Bot Của Bạn ({{ session['username'] }})</h1>
                <a href="/logout" class="logout">Đăng Xuất</a>
            </div>

            <!-- Tạo bot mới -->
            <div class="card">
                <h3>➕ Tạo Bot Mới</h3>
                <form action="/create_bot" method="POST" style="display: flex; gap: 10px;">
                    <input type="text" name="bot_name" placeholder="Nhập tên bot của bạn..." required style="flex: 1;">
                    <button type="submit">Tạo Bot</button>
                </form>
            </div>

            <!-- Danh sách các bot -->
            <div class="card">
                <h3>📋 Tất Cả Các Bot Đã Tạo</h3>
                {% if bots %}
                    {% for bot in bots %}
                    <div class="bot-item">
                        <span>🤖 <b>{{ bot[1] }}</b></span>
                        <div class="bot-actions">
                            <a href="/bot/{{ bot[0] }}">⚙️ Quản lý & Code</a>
                            <a href="/delete_bot/{{ bot[0] }}" class="delete" onclick="return confirm('Bạn có chắc muốn xóa bot này?')">🗑️ Xóa</a>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Bạn chưa tạo con bot nào cả. Hãy tạo ngay một bot ở trên!</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    ''', bots=bots)

@app.route('/create_bot', methods=['POST'])
def create_bot():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
