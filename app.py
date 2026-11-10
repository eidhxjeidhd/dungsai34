import os
import subprocess
import sys
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, Response

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Thư mục chứa các project độc lập
PROJECTS_DIR = "mini_render_projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Quản lý tiến trình và cổng của các app con
RUNNING_APPS = {} # {slug: {"port": 8001, "process": process, "owner": user}}
USERS = {}
NEXT_PORT = 8001  # Cổng bắt đầu cho các app con

# Đoạn code mẫu chuẩn có sẵn database SQLite độc lập cho từng shop
DEFAULT_RENDER_CODE = """import os
from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Tạo database SQLite riêng biệt cho từng shop
DB_NAME = 'shop_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Mini-Render Shop</title>
    <style>
        body { background: #090d16; color: #fff; font-family: sans-serif; text-align: center; padding: 40px; }
        .box { background: #1e293b; padding: 30px; border-radius: 16px; display: inline-block; border: 1px solid #334155; width: 100%; max-width: 400px; box-sizing: border-box; }
        input, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { background: #16a34a; font-weight: bold; border: none; cursor: pointer; }
        ul { list-style: none; padding: 0; text-align: left; margin-top: 20px; }
        li { background: #0f172a; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #334155; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color: #38bdf8;">🛍️ Shop Độc Lập Trên Cloud</h2>
        <form method="POST" action="/add">
            <input type="text" name="item_name" placeholder="Nhập tên sản phẩm..." required>
            <button type="submit">Thêm Vào Database</button>
        </form>
        <h3>Danh Sách Đã Lưu:</h3>
        <ul>
            {% for item in items %}
                <li>📦 {{ item[1] }}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, items=items)

@app.route('/add', methods=['POST'])
def add():
    item_name = request.form.get('item_name')
    if item_name:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO items (name) VALUES (?)", (item_name,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # App con sẽ chạy trên cổng được hệ thống cấp tự động
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port)
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Mini-Render Cloud</title>
    <style>
        body { background: #090d16; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 800px; width: 100%; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, textarea, button { width: 100%; padding: 14px; margin-top: 8px; margin-bottom: 15px; border-radius: 10px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 15px; }
        textarea { resize: vertical; height: 320px; font-family: monospace; font-size: 13px; color: #38bdf8; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; }
        .btn-success { background: #16a34a; }
        .btn-success:hover { background: #15803d; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.get('user') %}
            <div class="card">
                <h2>🔐 Đăng Nhập Mini-Render</h2>
                <form method="POST" action="/auth">
                    <label>Tài khoản:</label>
                    <input type="email" name="email" placeholder="Nhập email..." required>
                    <label>Mật khẩu:</label>
                    <input type="password" name="password" placeholder="Nhập mật khẩu..." required>
                    <div style="display: flex; gap: 10px;">
                        <button type="submit" name="action" value="login" class="btn-success" style="flex: 1;">Đăng Nhập</button>
                        <button type="submit" name="action" value="register" style="flex: 1;">Đăng Ký</button>
                    </div>
                </form>
                {% if error %}
                    <p style="color: #f87171; text-align: center;">{{ error }}</p>
                {% endif %}
            </div>
        {% else %}
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>👤 Tài khoản: <b>{{ session.get('user') }}</b></span>
                    <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
                </div>
            </div>

            <div class="card">
                <h2>🚀 Triển Khai App/Shop Độc Lập (Mini-Render)</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán code Python có kèm database SQLite vào đây. Hệ thống sẽ tự dựng tiến trình ngầm riêng biệt!</p>
                
                <form method="POST" action="/deploy">
                    <label>Tên Slug (Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shopgame..." required>
                    
                    <label>Mã nguồn Python (.py):</label>
                    <textarea name="py_code" required>{{ default_code }}</textarea>

                    <button type="submit" class="btn-success">⚡ Build & Deploy App</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách App Đang Chạy Ngầm</h3>
                {% if my_apps %}
                    <table>
                        <tr>
                            <th>Slug</th>
                            <th>Cổng Nội Bộ</th>
                            <th>Trạng thái</th>
                            <th>Hành động</th>
                        </tr>
                        {% for slug, info in my_apps.items() %}
                        <tr>
                            <td><b>{{ slug }}</b></td>
                            <td>{{ info.port }}</td>
                            <td><span style="color: #4ade80;">● Đang chạy 24/7</span></td>
                            <td>
                                <a href="/site/{{ slug }}/" target="_blank" style="color: #38bdf8; margin-right: 10px;">Mở Link Cloud</a>
                                <a href="/delete/{{ slug }}" style="color: #f87171; text-decoration: none;">Tắt/Xóa</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có app nào được deploy.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

USERS["admin@gmail.com"] = {"password": "adminpassword123"}

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_apps = {slug: data for slug, data in RUNNING_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_apps=my_apps, default_code=DEFAULT_RENDER_CODE)
    return render_template_string(HOME_TEMPLATE, default_code=DEFAULT_RENDER_CODE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email đã tồn tại!", default_code=DEFAULT_RENDER_CODE)
        USERS[email] = {"password": password}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!", default_code=DEFAULT_RENDER_CODE)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/deploy', methods=['POST'])
def deploy():
    global NEXT_PORT
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    slug = request.form.get('slug').strip().lower()
    py_code = request.form.get('py_code')
    
    if slug in RUNNING_APPS:
        return "Slug này đã tồn tại! Vui lòng chọn tên khác.", 400
        
    # Tạo thư mục riêng cho từng project (giống như clone repo trên Render)
    proj_folder = os.path.join(PROJECTS_DIR, slug)
    os.makedirs(proj_folder, exist_ok=True)
    
    file_path = os.path.join(proj_folder, "main.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    port = NEXT_PORT
    NEXT_PORT += 1
    
    try:
        # Khởi chạy tiến trình Python ngầm độc lập, truyền port vào tham số
        process = subprocess.Popen([sys.executable, file_path, str(port)], cwd=proj_folder)
        RUNNING_APPS[slug] = {
            "owner": user,
            "port": port,
            "process": process
        }
    except Exception as e:
        return f"Lỗi khởi chạy tiến trình: {str(e)}", 500
        
    return redirect(url_for('index'))

# Cổng Proxy Trung Tâm: Nhận request và chuyển tiếp ngầm tới app con tương ứng
@app.route('/site/<slug>/', defaults={'subpath': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/site/<slug>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_handler(slug, subpath):
    if slug not in RUNNING_APPS:
        return "Ứng dụng không tồn tại hoặc đã bị tắt!", 404
        
    port = RUNNING_APPS[slug]['port']
    target_url = f"http://127.0.0.1:{port}/{subpath}"
    
    try:
        # Thực hiện chuyển tiếp request thông qua thư viện requests ngầm
        if request.method == 'GET':
            resp = requests.get(target_url, params=request.args, cookies=request.cookies, allow_redirects=False)
        elif request.method == 'POST':
            resp = requests.post(target_url, data=request.form, files=request.files, cookies=request.cookies, allow_redirects=False)
        else:
            resp = requests.request(request.method, target_url, data=request.form, cookies=request.cookies, allow_redirects=False)
            
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]
        
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"Đang khởi động hoặc app con gặp sự cố: {str(e)}", 502

@app.route('/delete/<slug>')
def delete_app(slug):
    user = session.get('user')
    if slug in RUNNING_APPS and RUNNING_APPS[slug]['owner'] == user:
        try:
            RUNNING_APPS[slug]['process.terminate']() # Tắt tiến trình ngầm
            RUNNING_APPS[slug]['process'].kill()
        except:
            pass
        del RUNNING_APPS[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
