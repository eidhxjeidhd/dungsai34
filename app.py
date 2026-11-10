import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Kho lưu trữ các trang web được tạo ra tự động
CREATED_SITES = {}
USERS = {}

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trình Tạo Web Siêu Tốc Pro</title>
    <style>
        body { background: #090d16; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 650px; width: 100%; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, textarea, select, button { width: 100%; padding: 14px; margin-top: 8px; margin-bottom: 15px; border-radius: 10px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        textarea { resize: vertical; height: 120px; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; transform: translateY(-2px); }
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
                <h2>🔐 Đăng Nhập / Đăng Ký Hệ Thống</h2>
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
                <h2>⚡ Tạo Web Công Khai Siêu Mạnh</h2>
                <p style="color: #94a3b8; font-size: 14px;">Nhập thông tin bên dưới, hệ thống sẽ xuất bản và chuyển hướng bạn thẳng đến trang web mới ngay lập tức!</p>
                
                <form method="POST" action="/create_site">
                    <label>Đường dẫn trang web (Slug - Viết liền không dấu):</label>
                    <input type="text" name="slug" placeholder="Ví dụ: shop-acc-vip, su-kien..." required>
                    
                    <label>Tiêu đề trang (Title trên trình duyệt):</label>
                    <input type="text" name="title" placeholder="Ví dụ: Shop Blox Fruit Giá Rẻ" required>

                    <label>Tiêu đề chính (Heading H1):</label>
                    <input type="text" name="heading" placeholder="Ví dụ: Chào Mừng Đến Với Shop Của Tôi" required>

                    <label>Nội dung chi tiết trang web:</label>
                    <textarea name="content" placeholder="Nhập nội dung thông điệp, mô tả dịch vụ hoặc giới thiệu..." required></textarea>

                    <label>Phong cách giao diện:</label>
                    <select name="theme">
                        <option value="modern">🌌 Tối Hiện Đại & Neon (Đẹp nhất)</option>
                        <option value="gaming">🎮 Phong Cách Gaming (Đỏ/Đen)</option>
                        <option value="clean">💎 Sáng Sủa & Tối Giản</option>
                    </select>

                    <button type="submit" class="btn-success">🚀 Tạo Web Và Chuyển Hướng Ngay</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Web Bạn Đã Tạo</h3>
                {% if my_sites %}
                    <table>
                        <tr>
                            <th>Tiêu đề</th>
                            <th>Đường dẫn</th>
                            <th>Xóa</th>
                        </tr>
                        {% for s in my_sites %}
                        <tr>
                            <td><b>{{ s.title }}</b></td>
                            <td><a href="/site/{{ s.slug }}" target="_blank" style="color: #38bdf8;">Xem web</a></td>
                            <td><a href="/delete_site/{{ s.slug }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có trang web nào được tạo.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Template siêu mạnh với hiệu ứng cực chất cho các trang web được sinh ra
STRONG_SITE_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { 
            background: {% if theme == 'gaming' %}#1a0505{% elif theme == 'clean' %}#f1f5f9{% else %}#090d16{% endif %}; 
            color: {% if theme == 'clean' %}#1e293b{% else %}#f8fafc{% endif %}; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; 
        }
        .main-box { 
            background: {% if theme == 'clean' %}#ffffff{% else %}rgba(30, 41, 59, 0.95)%}{% endif %}; 
            padding: 40px; border-radius: 20px; max-width: 650px; width: 100%; 
            border: 2px solid {% if theme == 'gaming' %}#ef4444{% elif theme == 'clean' %}#cbd5e1{% else %}#38bdf8{% endif %}; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.4); text-align: center; 
        }
        h1 { 
            color: {% if theme == 'gaming' %}#f87171{% elif theme == 'clean' %}#0284c7{% else %}#38bdf8{% endif %}; 
            margin-top: 0; font-size: 32px; text-transform: uppercase; letter-spacing: 1px;
        }
        .content-box { 
            background: {% if theme == 'clean' %}#f8fafc{% else %}#0f172a{% endif %}; 
            padding: 20px; border-radius: 12px; margin-top: 20px; text-align: left; 
            border: 1px solid {% if theme == 'clean' %}#e2e8f0{% else %}#334155{% endif %};
            color: {% if theme == 'clean' %}#334155{% else %}#cbd5e1{% endif %}; 
            font-size: 17px; line-height: 1.7; white-space: pre-wrap; word-break: break-word;
        }
        .badge { 
            display: inline-block; background: {% if theme == 'gaming' %}#991b1b{% else %}#0284c7{% endif %}; 
            color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-bottom: 20px; 
        }
        .footer { margin-top: 30px; font-size: 13px; color: #64748b; border-top: 1px solid #334155; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="main-box">
        <div class="badge">🔥 Trang Web Công Khai Chính Thức</div>
        <h1>{{ heading }}</h1>
        <div class="content-box">{{ content }}</div>
        <div class="footer">
            Được xuất bản tự động bởi hệ thống Python Flask Web Builder.
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
    theme = request.form.get('theme')
    
    if slug in CREATED_SITES:
        return "Đường dẫn (Slug) này đã có người dùng! Vui lòng chọn tên khác.", 400
        
    # Lưu thông tin trang web mới
    CREATED_SITES[slug] = {
        "owner": user,
        "title": title,
        "heading": heading,
        "content": content,
        "theme": theme
    }
    
    # Tự động chuyển hướng thẳng đến trang web công khai vừa tạo xong!
    return redirect(url_for('view_site', slug=slug))

@app.route('/site/<slug>')
def view_site(slug):
    if slug not in CREATED_SITES:
        return "Trang web này không tồn tại hoặc đã bị xóa!", 404
    site_data = CREATED_SITES[slug]
    return render_template_string(STRONG_SITE_TEMPLATE, **site_data)

@app.route('/delete_site/<slug>')
def delete_site(slug):
    user = session.get('user')
    if slug in CREATED_SITES and CREATED_SITES[slug]['owner'] == user:
        del CREATED_SITES[slug]
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
