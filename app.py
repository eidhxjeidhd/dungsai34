import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Kho lưu trữ các trang web do bác tự code (lưu theo slug)
CUSTOM_SITES = {}
USERS = {}

# Giao diện Trang chủ & Trình quản lý code
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trình Quản Lý & Xuất Bản Code Tự Viết</title>
    <style>
        body { background: #090d16; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 750px; width: 100%; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, textarea, button { width: 100%; padding: 14px; margin-top: 8px; margin-bottom: 15px; border-radius: 10px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 15px; }
        textarea { resize: vertical; height: 250px; font-family: monospace; font-size: 14px; color: #38bdf8; }
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
                <h2>🔐 Đăng Nhập Hệ Thống</h2>
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
                <h2>💻 Đăng Tải Mã Nguồn Của Bạn</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán trọn bộ code HTML/CSS/JS tự viết của bạn vào đây, hệ thống sẽ phát hành nguyên bản thành một trang web công khai!</p>
                
                <form method="POST" action="/publish_code">
                    <label>Tên đường dẫn (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shop-robux, game-tool..." required>
                    
                    <label>Dán mã nguồn HTML (Raw Code):</label>
                    <textarea name="raw_code" placeholder="&lt;!DOCTYPE html&gt;&#10;&lt;html&gt;&#10;&lt;head&gt;...&lt;/head&gt;&#10;&lt;body&gt;&#10;  Code của bạn ở đây...&#10;&lt;/body&gt;&#10;&lt;/html&gt;" required></textarea>

                    <button type="submit" class="btn-success">🚀 Phát Hành Code Lên Web Ngay</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Các Web Đã Xuất Bản</h3>
                {% if my_sites %}
                    <table>
                        <tr>
                            <th>Đường dẫn (Slug)</th>
                            <th>Hành động</th>
                            <th>Xóa</th>
                        </tr>
                        {% for slug, data in my_sites.items() %}
                        <tr>
                            <td><b>{{ slug }}</b></td>
                            <td><a href="/p/{{ slug }}" target="_blank" style="color: #38bdf8;">Truy cập link web</a></td>
                            <td><a href="/delete/{{ slug }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có trang web nào được xuất bản.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Tài khoản mặc định để test nhanh
USERS["admin@gmail.com"] = {"password": "adminpassword123"}

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_sites = {slug: data for slug, data in CUSTOM_SITES.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_sites=my_sites)
    return render_template_string(HOME_TEMPLATE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email đã tồn tại!")
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

@app.route('/publish_code', methods=['POST'])
def publish_code():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    slug = request.form.get('slug').strip().lower()
    raw_code = request.form.get('raw_code')
    
    if slug in CUSTOM_SITES:
        return "Đường dẫn (Slug) này đã bị trùng! Vui lòng chọn tên khác.", 400
        
    # Lưu lại chính xác nguyên bản đoạn code mà bác tự viết
    CUSTOM_SITES[slug] = {
        "owner": user,
        "code": raw_code
    }
    
    return redirect(url_for('view_custom_site', slug=slug))

@app.route('/p/<slug>')
def view_custom_site(slug):
    if slug not in CUSTOM_SITES:
        return "Trang web không tồn tại hoặc đã bị xóa!", 404
    # Trả về thẳng nguyên văn mã nguồn HTML do bác tự code mà không qua bộ lọc nào cả
    return render_template_string(CUSTOM_SITES[slug]['code'])

@app.route('/delete/<slug>')
def delete_site(slug):
    user = session.get('user')
    if slug in CUSTOM_SITES and CUSTOM_SITES[slug]['owner'] == user:
        del CUSTOM_SITES[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
