import os
import importlib.util
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Thư mục lưu trữ code trên Cloud
CLOUD_STORAGE = "cloud_projects"
os.makedirs(CLOUD_STORAGE, exist_ok=True)

# Lưu bộ nhớ tạm các module đang chạy trên mây
LOADED_MODULES = {}
USERS = {}

# Đoạn code Python mẫu chuẩn Cloud (dùng hàm render hoặc trả về giao diện trực tiếp)
DEFAULT_CLOUD_CODE = """# Code Python chạy trực tiếp trên Cloud
from flask import Blueprint, render_template_string

# Tạo blueprint riêng cho shop của bạn
bp = Blueprint('my_cloud_shop', __name__)

HTML_CODE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Shop Cloud Của Tiến</title>
    <style>
        body { background: #090d16; color: #fff; font-family: sans-serif; text-align: center; padding: 50px; }
        .box { background: #1e293b; padding: 30px; border-radius: 16px; display: inline-block; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; }
        p { color: #94a3b8; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🚀 Shop Đang Chạy Trên Cloud!</h1>
        <p>Ứng dụng này hoạt động 24/7 trên mây và đồng bộ toàn cầu.</p>
    </div>
</body>
</html>
'''

@bp.route('/')
def index():
    return render_template_string(HTML_CODE)
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Cloud Python Tự Động</title>
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
                <h2>☁️ Trình Triển Khai Code Python Lên Cloud</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán code Python (Blueprint) vào đây để xuất bản thẳng ra một đường link cloud công khai toàn cầu, hoạt động đồng bộ 24/7!</p>
                
                <form method="POST" action="/deploy_cloud">
                    <label>Tên Đường Dẫn (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shop-cua-toi..." required>
                    
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
                            <th>Trạng thái Cloud</th>
                            <th>Hành động</th>
                        </tr>
                        {% for slug, info in my_apps.items() %}
                        <tr>
                            <td><b>{{ slug }}</b></td>
                            <td><span style="color: #4ade80;">● Hoạt động 24/7</span></td>
                            <td>
                                <a href="/site/{{ slug }}/" target="_blank" style="color: #38bdf8; margin-right: 10px;">Mở Link Cloud</a>
                                <a href="/delete/{{ slug }}" style="color: #f87171; text-decoration: none;">Xóa</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có ứng dụng nào được xuất bản lên cloud.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

USERS["admin@gmail.com"] = {"password": "adminpassword123"}
CLOUD_APPS = {}

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_apps = {slug: data for slug, data in CLOUD_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_apps=my_apps, default_code=DEFAULT_CLOUD_CODE)
    return render_template_string(HOME_TEMPLATE, default_code=DEFAULT_CLOUD_CODE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email đã tồn tại!", default_code=DEFAULT_CLOUD_CODE)
        USERS[email] = {"password": password}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!", default_code=DEFAULT_CLOUD_CODE)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/deploy_cloud', methods=['POST'])
def deploy_cloud():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    slug = request.form.get('slug').strip().lower()
    py_code = request.form.get('py_code')
    
    if slug in CLOUD_APPS:
        return "Tên đường dẫn này đã tồn tại trên cloud! Hãy chọn tên khác.", 400
        
    # Ghi file .py vào thư mục cloud
    file_path = os.path.join(CLOUD_STORAGE, f"{slug}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    try:
        # Nạp động module Python trực tiếp vào Flask app trên cloud
        spec = importlib.util.spec_from_file_location(slug, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Đăng ký blueprint của user vào app chính với đường dẫn /site/<slug>/
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp, url_prefix=f'/site/{slug}')
            CLOUD_APPS[slug] = {"owner": user, "path": file_path}
        else:
            return "Lỗi: Code Python phải chứa biến 'bp' (Blueprint) để tích hợp lên Cloud!", 400
    except Exception as e:
        return f"Lỗi cú pháp Python trên Cloud: {str(e)}", 500
        
    return redirect(url_for('index'))

@app.route('/delete/<slug>')
def delete_app(slug):
    user = session.get('user')
    if slug in CLOUD_APPS and CLOUD_APPS[slug]['owner'] == user:
        try:
            os.remove(CLOUD_APPS[slug]['path'])
        except:
            pass
        del CLOUD_APPS[slug]
        # Lưu ý: Flask không hỗ trợ unregister blueprint trực tiếp dễ dàng, nên khi xóa sẽ cần khởi động lại app nhẹ hoặc xóa khỏi danh sách quản lý.
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
