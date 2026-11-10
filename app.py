import os
import importlib.util
import shutil
import re
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

PROJECTS_DIR = "cloud_projects_isolated"
os.makedirs(PROJECTS_DIR, exist_ok=True)

CLOUD_APPS = {}

# Tài khoản admin quản lý hệ thống
USERS = {
    "admin": {"password": "123", "is_admin": True}
}

# Code mẫu chuẩn chỉnh, an toàn cho app con
DEFAULT_ISOLATED_CODE = """import os
import sqlite3
from flask import render_template_string

DB_FILE = os.path.join(os.path.dirname(__file__), 'shop_database.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    conn.commit()
    conn.close()

init_db()

def handle_request(req):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if req.method == 'POST':
        item_name = req.form.get('item_name')
        if item_name:
            c.execute("INSERT INTO items (name) VALUES (?)", (item_name,))
            conn.commit()
            
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>App Độc Lập Trên Cloud</title>
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
                <h2 style="color: #38bdf8; text-align: center; margin-top: 0;">🛍️ App Của Tôi</h2>
                <form method="POST">
                    <label>Nhập nội dung:</label>
                    <input type="text" name="item_name" placeholder="Ghi chú gì đó..." required>
                    <button type="submit">Lưu Vào Database</button>
                </form>
                <h3 style="margin-bottom: 5px;">Dữ Liệu Đã Lưu:</h3>
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
    <title>Hệ Thống Cloud Tạo App Tự Động</title>
    <style>
        body { background: #090d16; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 850px; width: 100%; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, textarea, button { width: 100%; padding: 14px; margin-top: 8px; margin-bottom: 15px; border-radius: 10px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 15px; }
        textarea { resize: vertical; height: 320px; font-family: monospace; font-size: 13px; color: #38bdf8; }
        button, .btn-link { display: inline-block; text-align: center; background: #0284c7; font-weight: bold; border: none; cursor: pointer; transition: 0.2s; text-decoration: none; color: #fff; padding: 8px 12px; border-radius: 8px; font-size: 13px; margin-right: 4px; }
        button:hover, .btn-link:hover { opacity: 0.8; }
        .btn-success { background: #16a34a; width: 100%; padding: 14px; border-radius: 10px; font-size: 15px; }
        .btn-success:hover { background: #15803d; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
        .badge-admin { background: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 11px; margin-left: 5px; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.get('user') %}
            <div class="card">
                <h2>🔐 Đăng Nhập Cloud Platform</h2>
                <form method="POST" action="/auth">
                    <label>Tài khoản:</label>
                    <input type="text" name="email" placeholder="Nhập tài khoản..." required>
                    <label>Mật khẩu:</label>
                    <input type="password" name="password" placeholder="Nhập mật khẩu..." required>
                    <div style="display: flex; gap: 10px;">
                        <button type="submit" name="action" value="login" class="btn-success" style="flex: 1; margin:0;">Đăng Nhập</button>
                        <button type="submit" name="action" value="register" style="flex: 1; margin:0; background:#0284c7;">Đăng Ký</button>
                    </div>
                </form>
                {% if error %}
                    <p style="color: #f87171; text-align: center;">{{ error }}</p>
                {% endif %}
            </div>
        {% else %}
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>👤 Tài khoản: <b>{{ session.get('user') }}</b> {% if is_admin %}<span class="badge-admin">ADMIN</span>{% endif %}</span>
                    <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
                </div>
            </div>

            <div class="card">
                <h2>⚡ Tạo & Triển Khai App Mới Lên Cloud</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán mã nguồn Python tích hợp SQLite vào đây, đặt tên đường dẫn và bấm xuất bản!</p>
                
                <form method="POST" action="/deploy">
                    <label>Tên Đường Dẫn (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shopcua-toi..." required>
                    
                    <label>Mã nguồn Python (.py):</label>
                    <textarea name="py_code" required>{{ default_code }}</textarea>

                    <button type="submit" class="btn-success">🚀 Xuất Bản App Lên Cloud</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Các App Đang Hoạt Động</h3>
                {% if my_apps %}
                    <table>
                        <tr>
                            <th>Đường dẫn (Slug)</th>
                            {% if is_admin %}<th>Chủ sở hữu</th>{% endif %}
                            <th>Thao tác</th>
                        </tr>
                        {% for slug, info in my_apps.items() %}
                        <tr>
                            <td><b>{{ slug }}</b></td>
                            {% if is_admin %}<td><span style="color: #38bdf8;">{{ info.owner }}</span></td>{% endif %}
                            <td>
                                <a href="/site/{{ slug }}/" target="_blank" class="btn-link" style="background: #0284c7;">Mở App</a>
                                {% if is_admin %}
                                    <a href="/admin/code/{{ slug }}" class="btn-link" style="background: #eab308;">Xem Code</a>
                                {% endif %}
                                <a href="/delete/{{ slug }}" class="btn-link" style="background: #ef4444;" onclick="return confirm('Bạn có chắc chắn muốn xóa app này không?');">Xóa</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có ứng dụng nào trên hệ thống.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    user = session.get('user')
    if user:
        is_admin = USERS.get(user, {}).get("is_admin", False)
        if is_admin:
            my_apps = CLOUD_APPS
        else:
            my_apps = {slug: data for slug, data in CLOUD_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_apps=my_apps, default_code=DEFAULT_ISOLATED_CODE, is_admin=is_admin)
    return render_template_string(HOME_TEMPLATE, default_code=DEFAULT_ISOLATED_CODE, is_admin=False)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email').strip()
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Tài khoản này đã tồn tại!", default_code=DEFAULT_ISOLATED_CODE, is_admin=False)
        USERS[email] = {"password": password, "is_admin": False}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!", default_code=DEFAULT_ISOLATED_CODE, is_admin=False)
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
    
    if not slug:
        return "Tên đường dẫn không được để trống!", 400
        
    proj_folder = os.path.join(PROJECTS_DIR, slug)
    os.makedirs(proj_folder, exist_ok=True)
    
    file_path = os.path.join(proj_folder, "main.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    CLOUD_APPS[slug] = {"owner": user, "path": file_path, "folder": proj_folder}
    return redirect(url_for('index'))

@app.route('/site/')
@app.route('/site')
def site_index_redirect():
    return redirect(url_for('index'))

# --- NÂNG CẤP HỆ THỐNG ĐIỀU HƯỚNG & VÁ LỖI ĐƯỜNG DẪN TỰ ĐỘNG ---
def auto_fix_html_links(html_content, slug):
    if not isinstance(html_content, str):
        return html_content
    prefix = f"/site/{slug}/"
    # Tự động thay thế các đường dẫn tuyệt đối bắt đầu bằng dấu / thành đường dẫn có chứa /site/<slug>/
    # Giúp app con dùng href="/login" hay action="/topup" tự động chạy mượt mà không bao giờ 404
    html_content = re.sub(r'href=["\']/(?!/)', f'href="{prefix}', html_content)
    html_content = re.sub(r'action=["\']/(?!/)', f'action="{prefix}', html_content)
    return html_content

@app.route('/site/<slug>/', defaults={'subpath': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/site/<slug>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def site_handler(slug, subpath):
    if slug not in CLOUD_APPS:
        return "Trang web cloud không tồn tại hoặc đã bị xóa!", 404
        
    file_path = CLOUD_APPS[slug]['path']
    try:
        spec = importlib.util.spec_from_file_location(f"project_{slug}", file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        if hasattr(mod, 'handle_request'):
            original_path_info = request.environ.get('PATH_INFO', '')
            
            # Chuẩn hóa path truyền vào app con
            clean_subpath = '/' + subpath if subpath else '/'
            request.environ['PATH_INFO'] = clean_subpath
            
            # Gọi hàm xử lý của app con
            response = mod.handle_request(request)
            
            # Trả lại path gốc cho hệ thống
            request.environ['PATH_INFO'] = original_path_info
            
            # Nếu response trả về là chuỗi HTML, tự động fix các đường dẫn liên kết
            if isinstance(response, str):
                response = auto_fix_html_links(response, slug)
            
            return response
        else:
            return "Lỗi: Code Python của app con phải có hàm handle_request(req)!", 500
    except Exception as e:
        import traceback
        return f"<pre style='color: #f87171; background: #1e293b; padding: 20px; border-radius: 8px;'>Lỗi thực thi mã nguồn ứng dụng:\n{traceback.format_exc()}</pre>", 500

@app.route('/admin/code/<slug>')
def admin_view_code(slug):
    user = session.get('user')
    is_admin = USERS.get(user, {}).get("is_admin", False)
    if not is_admin:
        return "Bạn không có quyền truy cập tính năng này!", 403
    if slug not in CLOUD_APPS:
        return "App không tồn tại!", 404
        
    with open(CLOUD_APPS[slug]['path'], "r", encoding="utf-8") as f:
        code_content = f.read()
        
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Xem Code: {{ slug }}</title>
            <style>
                body { background: #090d16; color: #fff; font-family: sans-serif; padding: 25px; margin: 0; display: flex; justify-content: center; }
                .container { max-width: 900px; width: 100%; }
                pre { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; overflow-x: auto; color: #38bdf8; font-family: monospace; font-size: 13px; line-height: 1.5; }
                a { display: inline-block; background: #0284c7; color: #fff; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-bottom: 20px; }
                a:hover { background: #0369a1; }
                h2 { color: #38bdf8; margin-top: 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/">⬅️ Quay lại trang quản lý</a>
                <h2>📄 Mã Nguồn Project: <span style="color: #f8fafc;">{{ slug }}</span></h2>
                <p style="color: #94a3b8;">Chủ sở hữu: <b>{{ owner }}</b></p>
                <pre>{{ code }}</pre>
            </div>
        </body>
        </html>
    """, slug=slug, owner=CLOUD_APPS[slug]['owner'], code=code_content)

@app.route('/delete/<slug>')
def delete_app(slug):
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
        
    is_admin = USERS.get(user, {}).get("is_admin", False)
    
    if slug in CLOUD_APPS and (is_admin or CLOUD_APPS[slug]['owner'] == user):
        try:
            shutil.rmtree(CLOUD_APPS[slug]['folder'], ignore_errors=True)
        except:
            pass
        del CLOUD_APPS[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
