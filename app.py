import os
import importlib.util
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

PROJECTS_DIR = "cloud_projects_isolated"
os.makedirs(PROJECTS_DIR, exist_ok=True)

CLOUD_APPS = {}
USERS = {}

# Đoạn code mẫu chuẩn Cloud, có sẵn database SQLite độc lập cho từng shop
DEFAULT_ISOLATED_CODE = """import os
import sqlite3

# File database SQLite riêng biệt nằm gọn trong thư mục của shop này
DB_FILE = os.path.join(os.path.dirname(__file__), 'shop_database.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Hàm xử lý chính khi có người truy cập vào shop
def handle_request(req):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Xử lý thêm sản phẩm nếu có yêu cầu POST
    if req.method == 'POST':
        item_name = req.form.get('item_name')
        if item_name:
            c.execute("INSERT INTO items (name) VALUES (?)", (item_name,))
            conn.commit()
            
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()
    
    # Giao diện HTML của shop
    html = '''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Shop Cloud Độc Lập</title>
        <style>
            body { background: #090d16; color: #fff; font-family: sans-serif; text-align: center; padding: 40px; }
            .box { background: #1e293b; padding: 30px; border-radius: 16px; display: inline-block; border: 1px solid #334155; width: 100%; max-width: 400px; box-sizing: border-box; text-align: left; }
            input, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
            button { background: #16a34a; font-weight: bold; border: none; cursor: pointer; }
            ul { list-style: none; padding: 0; margin-top: 20px; }
            li { background: #0f172a; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #334155; }
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: center;">
            <div class="box">
                <h2 style="color: #38bdf8; text-align: center; margin-top: 0;">🛍️ Shop Của Tôi</h2>
                <form method="POST">
                    <label>Tên sản phẩm / tài khoản:</label>
                    <input type="text" name="item_name" placeholder="Nhập vào đây..." required>
                    <button type="submit">Lưu Vào Database Riêng</button>
                </form>
                <h3 style="margin-bottom: 5px;">Kho Dữ Liệu:</h3>
                <ul>
                    {% for item in items %}
                        <li>📦 {{ item[1] }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, items=items)
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Cloud Python Độc Lập</title>
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
                <h2>🔐 Đăng Nhập Hệ Thống Cloud</h2>
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
                <h2>⚡ Triển Khai Shop/App Lên Cloud</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán code Python có tích hợp SQLite mẫu bên dưới, đặt tên đường dẫn và bấm xuất bản!</p>
                
                <form method="POST" action="/deploy">
                    <label>Tên Đường Dẫn (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shopgamecua-toi..." required>
                    
                    <label>Mã nguồn Python (.py) - Có sẵn mẫu:</label>
                    <textarea name="py_code" required>{{ default_code }}</textarea>

                    <button type="submit" class="btn-success">🚀 Xuất Bản Lên Cloud Ngay</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Các App Đã Lên Cloud</h3>
                {% if my_apps %}
                    <table>
                        <tr>
                            <th>Đường dẫn (Slug)</th>
                            <th>Trạng thái</th>
                            <th>Hành động</th>
                        </tr>
                        {% for slug, info in my_apps.items() %}
                        <tr>
                            <td><b>{{ slug }}</b></td>
                            <td><span style="color: #4ade80;">● Hoạt động 24/7 (Độc lập DB)</span></td>
                            <td>
                                <a href="/site/{{ slug }}/" target="_blank" style="color: #38bdf8; margin-right: 10px;">Mở Web</a>
                                <a href="/delete/{{ slug }}" style="color: #f87171; text-decoration: none;">Xóa</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có ứng dụng nào được xuất bản.</p>
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
        my_apps = {slug: data for slug, data in CLOUD_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_apps=my_apps, default_code=DEFAULT_ISOLATED_CODE)
    return render_template_string(HOME_TEMPLATE, default_code=DEFAULT_ISOLATED_CODE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email đã tồn tại!", default_code=DEFAULT_ISOLATED_CODE)
        USERS[email] = {"password": password}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!", default_code=DEFAULT_ISOLATED_CODE)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/deploy', methods=['POST'])
def deploy():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    slug = request.form.get('slug').strip().lower()
    py_code = request.form.get('py_code')
    
    if slug in CLOUD_APPS:
        return "Tên đường dẫn này đã tồn tại! Vui lòng chọn tên khác.", 400
        
    # Tạo thư mục riêng cho từng shop (cách ly hoàn toàn mã nguồn và database)
    proj_folder = os.path.join(PROJECTS_DIR, slug)
    os.makedirs(proj_folder, exist_ok=True)
    
    file_path = os.path.join(proj_folder, "main.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    CLOUD_APPS[slug] = {"owner": user, "path": file_path, "folder": proj_folder}
    return redirect(url_for('index'))

# Điều phối request tới app con độc lập mà không cần mở port rườm rà
@app.route('/site/<slug>/', defaults={'subpath': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/site/<slug>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def site_handler(slug, subpath):
    if slug not in CLOUD_APPS:
        return "Trang web cloud không tồn tại!", 404
        
    file_path = CLOUD_APPS[slug]['path']
    try:
        # Nạp động module Python của riêng project đó vào lúc có người truy cập
        spec = importlib.util.spec_from_file_location(f"project_{slug}", file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Gọi hàm handle_request đã được định nghĩa trong code của user
        if hasattr(mod, 'handle_request'):
            return mod.handle_request(request)
        else:
            return "Lỗi: Code Python phải có hàm handle_request(req) để xử lý dữ liệu!", 500
    except Exception as e:
        return f"Lỗi thực thi mã nguồn: {str(e)}", 500

@app.route('/delete/<slug>')
def delete_app(slug):
    user = session.get('user')
    if slug in CLOUD_APPS and CLOUD_APPS[slug]['owner'] == user:
        try:
            # Xóa sạch thư mục chứa code và database riêng của shop đó
            import shutil
            shutil.rmtree(CLOUD_APPS[slug]['folder'], ignore_errors=True)
        except:
            pass
        del CLOUD_APPS[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
