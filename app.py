import os
import subprocess
import sys
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Thư mục chứa các project Python do người dùng tự tạo
PROJECTS_DIR = "user_projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Quản lý danh sách các app đang chạy ngầm
RUNNING_APPS = {}
USERS = {}

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
        textarea { resize: vertical; height: 300px; font-family: monospace; font-size: 13px; color: #38bdf8; }
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
                <h2>⚡ Dán Mã Nguồn Python (Backend App)</h2>
                <p style="color: #94a3b8; font-size: 14px;">Dán code Flask/Python tự viết của bạn vào đây. Hệ thống sẽ tự tạo file, cấp cổng chạy độc lập để làm shop hoặc tool động!</p>
                
                <form method="POST" action="/deploy_py">
                    <label>Tên Project (Slug - Viết liền không dấu):</label>
                    <input type="text" name="project_name" placeholder="Ví dụ: myshop, toolkiemhieu..." required>
                    
                    <label>Mã nguồn Python (.py):</label>
                    <textarea name="py_code" placeholder="from flask import Flask&#10;app = Flask(__name__)&#10;&#10;@app.route('/')&#10;def home():&#10;    return 'Shop của tôi đang chạy!'&#10;&#10;if __name__ == '__main__':&#10;    app.run(host='0.0.0.0', port=5001)" required></textarea>

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
NEXT_PORT = 6000 # Cổng khởi điểm cho các app con do người dùng tạo

@app.route('/')
def index():
    user = session.get('user')
    if user:
        my_projects = {name: data for name, data in RUNNING_APPS.items() if data['owner'] == user}
        return render_template_string(HOME_TEMPLATE, my_projects=my_projects)
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
        
    # Tạo thư mục riêng cho project
    proj_folder = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(proj_folder, exist_ok=True)
    
    file_path = os.path.join(proj_folder, "main.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(py_code)
        
    # Cấp một port độc lập và chạy tiến trình Python ngầm
    port = NEXT_PORT
    NEXT_PORT += 1
    
    try:
        # Chạy file python độc lập dưới background
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
        # Tắt tiến trình đang chạy ngầm
        try:
            RUNNING_APPS[project_name]['process'].terminate()
        except:
            pass
        del RUNNING_APPS[project_name]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
