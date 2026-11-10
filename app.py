import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Kho lưu trữ các trang web được tạo ra (Slug -> Thông tin trang web)
CREATED_SITES = {}
USERS = {}

# Giao diện Trang chủ & Quản lý / Tạo web
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Web Tạo Web</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 650px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, textarea, select, button { width: 100%; padding: 12px; margin-top: 8px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        textarea { resize: vertical; height: 100px; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #0369a1; }
        .btn-success { background: #16a34a; }
        .btn-success:hover { background: #15803d; }
        .link-box { background: #090d16; padding: 10px; border-radius: 8px; word-break: break-all; color: #34d399; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.get('user') %}
            <div class="card">
                <h2>🔐 Đăng Nhập / Đăng Ký Trình Tạo Web</h2>
                <form method="POST" action="/auth">
                    <label>Tài khoản Gmail:</label>
                    <input type="email" name="email" placeholder="Nhập Gmail..." required>
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
                    <span>👤 Chủ sở hữu: <b>{{ session.get('user') }}</b></span>
                    <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
                </div>
            </div>

            <div class="card">
                <h2>🚀 Trình Tạo Web Tự Động</h2>
                <p style="color: #94a3b8; font-size: 14px;">Điền thông tin bên dưới để hệ thống tự động xuất bản một trang web công khai mới:</p>
                
                <form method="POST" action="/create_site">
                    <label>Đường dẫn trang web (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: chao-ngay-moi, shop-game..." required>
                    
                    <label>Tiêu đề trang (Title):</label>
                    <input type="text" name="title" placeholder="Ví dụ: Shop Acc Blox Fruit Uy Tín" required>

                    <label>Tiêu đề chính trên web (Heading):</label>
                    <input type="text" name="heading" placeholder="Ví dụ: Chào mừng bạn đến với cửa hàng!" required>

                    <label>Nội dung hiển thị trên web:</label>
                    <textarea name="content" placeholder="Nhập nội dung giới thiệu, mô tả hoặc thông điệp của bạn ở đây..." required></textarea>

                    <label>Chọn phong cách màu nền:</label>
                    <select name="bg_color">
                        <option value="#0f172a">Tối hiện đại (Dark Slate)</option>
                        <option value="#18181b">Đen tuyền (Zinc Dark)</option>
                        <option value="#0f172a">Xanh biển sâu (Deep Ocean)</option>
                        <option value="#3b0764">Tím huyền bí (Purple Night)</option>
                    </select>

                    <button type="submit" class="btn-success">✨ Tạo Và Xuất Bản Web Ngay</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Các Web Bạn Đã Tạo</h3>
                {% if my_sites %}
                    <table>
                        <tr>
                            <th>Tên Web / Tiêu đề</th>
                            <th>Đường dẫn công khai</th>
                            <th>Thao tác</th>
                        </tr>
                        {% for s in my_sites %}
                        <tr>
                            <td><b>{{ s.title }}</b></td>
                            <td><a href="/site/{{ s.slug }}" target="_blank" style="color: #38bdf8;">/site/{{ s.slug }}</a></td>
                            <td><a href="/delete_site/{{ s.slug }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Bạn chưa tạo trang web nào cả.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Giao diện mẫu cho các trang web con được tạo ra tự động
DYNAMIC_SITE_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { background: {{ bg_color }}; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; }
        .site-card { background: rgba(30, 41, 59, 0.85); padding: 30px; border-radius: 16px; max-width: 600px; width: 100%; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; }
        h1 { color: #38bdf8; margin-top: 0; font-size: 28px; }
        p { color: #cbd5e1; font-size: 18px; line-height: 1.6; white-space: pre-wrap; margin-top: 20px; }
        .footer { margin-top: 30px; font-size: 12px; color: #64748b; border-top: 1px solid #334155; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="site-card">
        <h1>{{ heading }}</h1>
        <p>{{ content }}</p>
        <div class="footer">
            Trang web này được tạo tự động bởi hệ thống Python Flask Web Builder.
        </div>
    </div>
</body>
</html>
"""

USERS["admin@gmail.com"] = {"password": "adminpassword123"}

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_sites = [s for s in CREATED_SITES.values() if s['owner'] == user]
        return render_template_string(HOME_TEMPLATE, my_sites=my_sites)
    return render_template_string(HOME_TEMPLATE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email này đã tồn tại!")
        USERS[email] = {"password": password}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/create_site', methods=['POST'])
def create_site():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    slug = request.form.get('slug').strip().lower()
    title = request.form.get('title')
    heading = request.form.get('heading')
    content = request.form.get('content')
    bg_color = request.form.get('bg_color')
    
    if slug in CREATED_SITES:
        return "Đường dẫn (Slug) này đã tồn tại! Vui lòng chọn tên khác.", 400
        
    CREATED_SITES[slug] = {
        "owner": user,
        "title": title,
        "heading": heading,
        "content": content,
        "bg_color": bg_color
    }
    
    return redirect(url_for('index'))

@app.route('/site/<slug>')
def view_site(slug):
    if slug not in CREATED_SITES:
        return "Trang web này không tồn tại hoặc đã bị xóa!", 404
    site_data = CREATED_SITES[slug]
    return render_template_string(DYNAMIC_SITE_TEMPLATE, **site_data)

@app.route('/delete_site/<slug>')
def delete_site(slug):
    user = session.get('user')
    if slug in CREATED_SITES and CREATED_SITES[slug]['owner'] == user:
        del CREATED_SITES[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
