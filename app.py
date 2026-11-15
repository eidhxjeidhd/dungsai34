import os
import sqlite3
import subprocess
import threading
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_cloud_panel'

DB_FILE = 'panel_database.db'

# Lưu trữ tiến trình bot đang chạy theo bot_id: {'process': proc, 'logs': [], 'file': filename}
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

# CSS chung cho toàn bộ giao diện (Bảy màu, animation đổi màu liên tục, neon glow)
GLOBAL_STYLE = '''
<style>
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes rainbowGlow {
        0% { border-color: #ff0055; box-shadow: 0 0 20px rgba(255, 0, 85, 0.4); }
        20% { border-color: #ffaa00; box-shadow: 0 0 20px rgba(255, 170, 0, 0.4); }
        40% { border-color: #ffff00; box-shadow: 0 0 20px rgba(255, 255, 0, 0.4); }
        60% { border-color: #00ffcc; box-shadow: 0 0 20px rgba(0, 255, 204, 0.4); }
        80% { border-color: #9900ff; box-shadow: 0 0 20px rgba(153, 0, 255, 0.4); }
        100% { border-color: #ff0055; box-shadow: 0 0 20px rgba(255, 0, 85, 0.4); }
    }
    @keyframes textRainbow {
        0% { color: #ff3366; }
        20% { color: #ff9933; }
        40% { color: #ffff33; }
        60% { color: #33cc66; }
        80% { color: #3399ff; }
        100% { color: #cc33ff; }
    }
    body {
        background: linear-gradient(-45deg, #090d16, #1e1b4b, #31103f, #0f172a, #022c22);
        background-size: 500% 500%;
        animation: gradientBG 15s ease infinite;
        color: #fff;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        min-height: 100vh;
        margin: 0;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .main-wrapper { width: 100%; max-width: 1100px; padding: 20px; box-sizing: border-box; }
    .box, .card {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(16px);
        border: 2px solid #ff0055;
        animation: rainbowGlow 8s linear infinite;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        transition: transform 0.3s ease;
    }
    .box:hover, .card:hover { transform: translateY(-3px); }
    h1, h2, h3 {
        animation: textRainbow 6s linear infinite;
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    input {
        width: 100%;
        padding: 12px 15px;
        margin: 12px 0;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid #475569;
        color: #fff;
        border-radius: 8px;
        box-sizing: border-box;
        outline: none;
        transition: border-color 0.3s, box-shadow 0.3s;
    }
    input:focus {
        border-color: #00ffcc;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
    }
    button, .btn-action {
        width: 100%;
        padding: 12px;
        background: linear-gradient(45deg, #ff0055, #ff9900, #33cc66, #0099ff, #9900ff);
        background-size: 300% 300%;
        animation: gradientBG 6s ease infinite;
        border: none;
        color: #fff;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        transition: transform 0.2s, filter 0.2s;
    }
    button:hover {
        transform: scale(1.02);
        filter: brightness(1.2);
    }
    .link { text-align: center; margin-top: 15px; font-size: 14px; }
    .link a { color: #00ffcc; text-decoration: none; font-weight: bold; }
    .link a:hover { text-decoration: underline; }
    .error { color: #ff3366; font-size: 13px; text-align: center; margin-bottom: 10px; font-weight: bold; }
    .success { color: #00ffcc; font-size: 13px; text-align: center; margin-bottom: 10px; font-weight: bold; }
</style>
'''

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
            error = "⚠️ Tài khoản hoặc mật khẩu không chính xác!"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Đăng Nhập - Rainbow Cloud Panel</title>
        ''' + GLOBAL_STYLE + '''
        <style>body { display: flex; justify-content: center; align-items: center; } .box { width: 350px; }</style>
    </head>
    <body>
        <div class="box">
            <h2>🔑 Đăng Nhập Hệ Thống</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Tên đăng nhập" required>
                <input type="password" name="password" placeholder="Mật khẩu" required>
                <button type="submit">VÀO HỆ THỐNG</button>
            </form>
            <div class="link">Chưa có tài khoản? <a href="/register">Đăng ký ngay 🌟</a></div>
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
            success = "✨ Đăng ký thành công! Hãy đăng nhập."
        except sqlite3.IntegrityError:
            error = "⚠️ Tên đăng nhập đã tồn tại!"
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Đăng Ký - Rainbow Cloud Panel</title>
        ''' + GLOBAL_STYLE + '''
        <style>body { display: flex; justify-content: center; align-items: center; } .box { width: 350px; }</style>
    </head>
    <body>
        <div class="box">
            <h2>📝 Đăng Ký Tài Khoản</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success">{{ success }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Tên đăng nhập" required>
                <input type="password" name="password" placeholder="Mật khẩu" required>
                <button type="submit">ĐĂNG KÝ NGAY</button>
            </form>
            <div class="link">Đã có tài khoản? <a href="/login">Đăng nhập 🚀</a></div>
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
        <title>Quản Lý Bot - Rainbow Cloud Panel</title>
        ''' + GLOBAL_STYLE + '''
        <style>
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 25px; }
            .bot-item { display: flex; justify-content: space-between; align-items: center; background: rgba(15, 23, 42, 0.9); padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.2); transition: 0.3s; }
            .bot-item:hover { border-color: #00ffcc; box-shadow: 0 0 15px rgba(0,255,204,0.3); }
            .bot-actions a { color: #00ffcc; text-decoration: none; margin-right: 15px; font-weight: bold; }
            .bot-actions a.delete { color: #ff3366; }
            .logout-btn { background: linear-gradient(45deg, #ff0055, #ff3366); width: auto; padding: 8px 20px; border-radius: 8px; color: #fff; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="main-wrapper">
            <div class="header">
                <h1>🤖 Chào mừng, {{ session['username'] }}!</h1>
                <a href="/logout" class="logout-btn">🚪 Đăng Xuất</a>
            </div>

            <!-- Tạo bot mới -->
            <div class="card" style="margin-bottom: 25px;">
                <h3>➕ Tạo Bot Telegram Mới</h3>
                <form action="/create_bot" method="POST" style="display: flex; gap: 15px;">
                    <input type="text" name="bot_name" placeholder="Nhập tên con bot của bạn..." required style="margin: 0; flex: 1;">
                    <button type="submit" style="width: 150px; margin: 0;">TẠO BOT</button>
                </form>
            </div>

            <!-- Danh sách các bot -->
            <div class="card">
                <h3>📋 Danh Sách Bot Đang Quản Lý</h3>
                {% if bots %}
                    {% for bot in bots %}
                    <div class="bot-item">
                        <span>🤖 <b style="font-size: 16px;">{{ bot[1] }}</b></span>
                        <div class="bot-actions">
                            <a href="/bot/{{ bot[0] }}">⚙️ Quản Lý & Code</a>
                            <a href="/delete_bot/{{ bot[0] }}" class="delete" onclick="return confirm('Bạn có chắc muốn xóa bot này?')">🗑️ Xóa</a>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #94a3b8; text-align: center; padding: 20px;">Chưa có con bot nào cả. Hãy tạo ngay một bot ở khung phía trên nhé! ✨</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    ''', bots=bots, session=session)

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
    bot.reply_to(message, "👋 Chào bạn! Bot bảy màu hoạt động độc lập qua Panel.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Đã nhận tin nhắn: {message.text}")

if __name__ == '__main__':
    bot.infinity_polling(skip_pending=True)
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
            running_processes[bot_id]['process'].wait(timeout=2)
        except:
            try:
                running_processes[bot_id]['process'].kill()
            except:
                pass
        try:
            if os.path.exists(running_processes[bot_id]['file']):
                os.remove(running_processes[bot_id]['file'])
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
            
        if action == 'save_and_run':
            if bot_id in running_processes:
                try:
                    running_processes[bot_id]['process'].terminate()
                    running_processes[bot_id]['process'].wait(timeout=2)
                except:
                    try:
                        running_processes[bot_id]['process'].kill()
                    except:
                        pass
                try:
                    if os.path.exists(running_processes[bot_id]['file']):
                        os.remove(running_processes[bot_id]['file'])
                except:
                    pass
                del running_processes[bot_id]
                
            temp_file = f"temp_bot_{bot_id}_{uuid.uuid4().hex[:8]}.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code_content)
                
            process_locks[bot_id] = threading.Lock()
            running_processes[bot_id] = {
                'file': temp_file,
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
                message = "✨ Đã lưu code và khởi động bot thành công rực rỡ!"
            except Exception as e:
                message = f"Lỗi khởi động: {str(e)}"
                
        elif action == 'stop':
            if bot_id in running_processes:
                try:
                    running_processes[bot_id]['process'].terminate()
                    running_processes[bot_id]['process'].wait(timeout=2)
                except:
                    try:
                        running_processes[bot_id]['process'].kill()
                    except:
                        pass
                try:
                    if os.path.exists(running_processes[bot_id]['file']):
                        os.remove(running_processes[bot_id]['file'])
                except:
                    pass
                del running_processes[bot_id]
                message = "🛑 Đã dừng hoạt động bot thành công!"
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
        <title>Quản Lý: {{ bot[1] }} - Rainbow Panel</title>
        ''' + GLOBAL_STYLE + '''
        <style>
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 20px; }
            .status-badge { padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 13px; }
            .running { background: #00ffcc; color: #000; box-shadow: 0 0 15px rgba(0,255,204,0.6); }
            .stopped { background: #ff3366; color: #fff; box-shadow: 0 0 15px rgba(255,51,102,0.6); }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { display: flex; flex-direction: column; }
            textarea { width: 100%; height: 380px; background: rgba(10, 15, 30, 0.95); color: #00ffcc; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; box-sizing: border-box; resize: vertical; outline: none; }
            textarea:focus { border-color: #ff0055; box-shadow: 0 0 10px rgba(255,0,85,0.4); }
            pre.logs { width: 100%; height: 380px; background: rgba(10, 15, 30, 0.95); color: #00ff66; border: 1px solid #475569; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; box-sizing: border-box; margin: 0; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; }
            .btn-group { margin-top: 15px; display: flex; gap: 10px; }
            .btn-group button { margin-top: 0; flex: 1; }
            .alert { background: rgba(0, 150, 255, 0.2); border: 1px solid #0099ff; color: #fff; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; backdrop-filter: blur(5px); }
            .back { color: #00ffcc; text-decoration: none; font-weight: bold; font-size: 14px; }
            .back:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="main-wrapper" style="max-width: 1200px;">
            <div class="header">
                <div>
                    <a href="/" class="back">← Quay lại danh sách</a>
                    <h1 style="display:inline-block; margin-left:15px; font-size: 22px;">⚙️ Quản lý: {{ bot[1] }}</h1>
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
                            <button type="submit" name="action" value="save" style="background: linear-gradient(45deg, #0066ff, #00ccff);">💾 Chỉ Lưu</button>
                            <button type="submit" name="action" value="save_and_run" style="background: linear-gradient(45deg, #00ff66, #009933);">🚀 Lưu & Chạy</button>
                            <button type="submit" name="action" value="stop" style="background: linear-gradient(45deg, #ff0055, #cc0000);">🛑 Dừng</button>
                        </div>
                    </form>
                </div>

                <!-- Cột 2: Logs -->
                <div class="card">
                    <h3>
                        📊 Nhật Ký Hoạt Động (Logs)
                        <button onclick="location.reload()" style="width: auto; padding: 4px 12px; font-size: 11px; margin-top:0;">🔄 Làm mới</button>
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
