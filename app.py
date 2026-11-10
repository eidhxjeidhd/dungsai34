import os
import subprocess
import sys
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

PROJECTS_DIR = "user_projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

RUNNING_APPS = {}
USERS = {}

# Đoạn code mẫu mặc định để sẵn trong ô cho người dùng copy hoặc sửa
DEFAULT_TEMPLATE_CODE = """from flask import Flask, render_template_string

app = Flask(__name__)

# Giao diện mẫu của shop / trang web
HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Shop Của Tôi</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: sans-serif; text-align: center; padding: 50px; }
        .box { background: #1e293b; padding: 30px; border-radius: 12px; display: inline-block; border: 1px solid #334155; }
        h1 { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🚀 Chào mừng đến với Shop của tôi!</h1>
        <p>Đây là trang web chạy bằng code Python tự chỉnh sửa.</p>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

if __name__ == '__main__':
    # Chạy ở port bất kỳ do hệ thống chỉ định
    app.run(host='0.0.0.0', port=5000)
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xưởng Sản Xuất Web Python Tự Động</title>
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
                <h2>⚡ Kho Code Mẫu & Triển Khai Python</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dưới đây là đoạn code Python mẫu có sẵn. Bạn có thể sao chép ra ngoài, hoặc chỉnh sửa trực tiếp trong ô bên dưới rồi bấm khởi chạy!</p>
                
                <form method="POST" action="/deploy_py">
                    <label>Tên Project (Slug - Viết liền không dấu):</label>
                    <input type="text" name="project_name" placeholder="Ví dụ: shopcua-toi..." required>
                    
                    <label>Mã nguồn Python (.py) - Có sẵn mẫu để sửa:</label>
                    <!-- Đưa thẳng code mẫu vào bên trong thẻ textarea để hiện sẵn cho người dùng -->
                    <textarea name="py_code" required>{{ default_code }}</textarea>

                    <button type="submit" class="btn-success">🚀 Khởi Chạy App Python Ngay</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 Danh Sách Các App Đang Hoạt Động</h3>
                {% if my_projects %}
                    <table>
                        <tr>
                            <th>Tên Project</th>
                            <th>Cổng (Port)</th>
                            <th>Trạng thái</th>
                            <th>Hành động</th>
                        </tr>
                        {% for name, info in my_projects.items() %}
                        <tr>
                            <td><b>{{ name }}</b></td>
                            <td>{{ info.port }}</td>
                            <td><span style="color: #4ade80;">● Đang chạy</span></td>
                            <td>
                                <a href="http://localhost:{{ info.port }}" target="_blank" style="color: #38bdf8; margin-right: 10px;">Mở Web</a>
                                <a href="/stop/{{ name }}" style="color: #f87171; text-decoration: none;">Tắt</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có ứng dụng Python nào được triển khai.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

USERS["admin@gmail.com"] = {"password": "adminpassword123"}
NEXT_PORT = 6000

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_projects = {name: data for name, data in RUNNING_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_projects=my_projects, default_code=DEFAULT_TEMPLATE_CODE)
    return render_template_string(HOME_TEMPLATE, default_code=DEFAULT_TEMPLATE_CODE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HOME_TEMPLATE, error="Email đã tồn tại!", default_code=DEFAULT_TEMPLATE_CODE)
        USERS[email] = {"password": password}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HOME_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!", default_code=DEFAULT_TEMPLATE_CODE)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/deploy_py', methods=['POST'])
def deploy_py():
    global NEXT_PORT
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    project_name = request.form.get('project_name').strip().lower()
    py_code = request.form.get('py_code')
    
    if project_name in RUNNING_APPS:
        return "Tên project này đã tồn tại! Vui lòng chọn tên khác.", 400
        
    proj_folder = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(proj_folder, exist_ok=True)
    
    file_path = os.path.join(proj_folder, "main.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    port = NEXT_PORT
    NEXT_PORT += 1
    
    try:
        process = subprocess.Popen([sys.executable, file_path], cwd=proj_folder)
        RUNNING_APPS[project_name] = {
            "owner": user,
            "port": port,
            "process": process
        }
    except Exception as e:
        return f"Lỗi khi khởi chạy ứng dụng: {str(e)}", 500
        
    return redirect(url_for('index'))

@app.route('/stop/<project_name>')
def stop_project(project_name):
    user = session.get('user')
    if project_name in RUNNING_APPS and RUNNING_APPS[project_name]['owner'] == user:
        try:
            RUNNING_APPS[project_name]['process'].terminate()
        except:
            pass
        del RUNNING_APPS[project_name]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
