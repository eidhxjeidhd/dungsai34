import os
import random
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

USERS = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thật Lòng Hay Giả Dối</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 600px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        input, button { width: 100%; padding: 12px; margin-top: 10px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #0369a1; }
        .btn-success { background: #16a34a; }
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
                <h2>🔐 Đăng Nhập / Đăng Ký</h2>
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
        {% elif session.get('user') == 'admin@gmail.com' %}
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #facc15; font-weight: bold;">👑 Khu Vực Admin</span>
                    <a href="/logout" style="color: #f87171; text-decoration: none;">Đăng xuất</a>
                </div>
                <h2>Quản Lý Toàn Bộ Người Dùng</h2>
                {% if users_list %}
                    <table>
                        <tr>
                            <th>Email</th>
                            <th>Số câu hỏi</th>
                            <th>Xem thói quen</th>
                        </tr>
                        {% for u in users_list %}
                        <tr>
                            <td>{{ u.email }}</td>
                            <td>{{ u.questions|length }} câu</td>
                            <td><a href="/admin/view/{{ u.email }}" style="color: #38bdf8; text-decoration: none;">Xem chi tiết</a></td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có người dùng nào.</p>
                {% endif %}
            </div>
        {% else %}
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>👤 Chào, <b>{{ session.get('user') }}</b></span>
                    <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
                </div>
            </div>

            <div class="card">
                <h2>🔗 Link Thử Thách Của Bạn</h2>
                <p style="color: #94a3b8; font-size: 14px;">Sao chép link này gửi cho bạn bè:</p>
                <div class="link-box">{{ base_url }}/play/{{ session.get('user') }}</div>

                <h3>✍️ Thêm Câu Hỏi Tùy Chỉnh (Đã tạo: {{ questions|length }}/10 câu)</h3>
                <p style="color: #94a3b8; font-size: 13px;">Bạn có thể tạo tối đa 10 câu.</p>
                
                {% if questions|length < 10 %}
                <form method="POST" action="/add_question">
                    <label>Câu hỏi thói quen:</label>
                    <input type="text" name="question" placeholder="Ví dụ: Tôi hay dùng ốp điện thoại màu gì?" required>
                    <label style="color: #34d399;">Đáp án đúng (Thật lòng):</label>
                    <input type="text" name="correct" placeholder="Ví dụ: Ốp màu trắng" required>
                    <label style="color: #f87171;">Đáp án sai 1 (Na ná):</label>
                    <input type="text" name="wrong1" placeholder="Ví dụ: Ốp màu đen" required>
                    <label style="color: #f87171;">Đáp án sai 2 (Na ná):</label>
                    <input type="text" name="wrong2" placeholder="Ví dụ: Ốp màu trong suốt" required>
                    <label style="color: #f87171;">Đáp án sai 3 (Na ná):</label>
                    <input type="text" name="wrong3" placeholder="Ví dụ: Không dùng ốp" required>
                    <button type="submit" class="btn-success">Thêm Câu Này Vào Link</button>
                </form>
                {% else %}
                <p style="color: #facc15; text-align: center;">Bạn đã đạt giới hạn tối đa 10 câu hỏi!</p>
                {% endif %}
            </div>

            <div class="card">
                <h3>📋 Danh Sách Câu Hỏi Đã Tạo ({{ questions|length }})</h3>
                {% if questions %}
                    <table>
                        <tr>
                            <th>STT</th>
                            <th>Câu hỏi & Đáp án đúng</th>
                            <th>Xóa</th>
                        </tr>
                        {% for q in questions %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>
                                <b>Q: {{ q.q }}</b><br>
                                <span style="color: #34d399;">✔ Đúng: {{ q.correct }}</span>
                            </td>
                            <td><a href="/delete_q/{{ loop.index0 }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                        </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p style="color: #94a3b8; text-align: center;">Chưa có câu hỏi nào.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

PLAY_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thử Thách Thật Lòng Hay Giả Dối</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 600px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; text-align: center; }
        .radio-label { display: block; background: #0f172a; padding: 10px; margin-top: 8px; border-radius: 6px; border: 1px solid #475569; cursor: pointer; }
        .radio-label:hover { background: #1e293b; border-color: #38bdf8; }
        button { width: 100%; padding: 12px; margin-top: 15px; border-radius: 8px; border: none; background: #16a34a; color: #fff; font-weight: bold; cursor: pointer; font-size: 16px; }
        button:hover { background: #15803d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>🎯 Thử Thách Thói Quen Của: <span style="color: #facc15;">{{ owner }}</span></h2>
            <p style="text-align: center; color: #94a3b8; font-size: 14px;">Bài kiểm tra gồm có <b>{{ quiz_data|length }} câu hỏi</b>.</p>
            
            {% if not result_checked %}
                <form method="POST">
                    {% for item in quiz_data %}
                        <div style="margin-bottom: 20px;">
                            <label><b>Câu {{ loop.index }}:</b> {{ item.q }}</label>
                            {% for opt in item.options %}
                                <label class="radio-label">
                                    <input type="radio" name="question_{{ item.index }}" value="{{ opt }}" required> {{ opt }}
                                </label>
                            {% endfor %}
                        </div>
                    {% endfor %}
                    <button type="submit">Kiểm Tra Độ Thật Lòng</button>
                </form>
            {% else %}
                <div style="text-align: center;">
                    <h3>Kết Quả Đánh Giá</h3>
                    <p style="font-size: 20px; color: {% if score == 100 %}#34d399{% else %}#f87171{% endif %};">
                        Độ thật lòng / Hiểu nhau: <b>{{ score }}%</b> (Đúng {{ correct_count }}/{{ total_questions }} câu)
                    </p>
                    <p style="color: #94a3b8;">{{ message }}</p>
                    <a href="/play/{{ owner }}"><button style="background: #0284c7; margin-top: 15px;">Làm Lại Thử Thách</button></a>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADMIN_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Xem Thói Quen</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 600px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2 { color: #38bdf8; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>Thói Quen Của: {{ target_email }}</h2>
            <table>
                <tr>
                    <th>STT</th>
                    <th>Câu hỏi</th>
                    <th>Đáp án đúng & Các đáp án nhiễu</th>
                </tr>
                {% for q in questions %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td><b>{{ q.q }}</b></td>
                    <td>
                        <span style="color: #34d399;">✔ Đúng: {{ q.correct }}</span><br>
                        <span style="color: #f87171;">❌ Sai: {{ q.wrongs|join(', ') }}</span>
                    </td>
                </tr>
                {% endfor %}
            </table>
            <br>
            <a href="/" style="color: #38bdf8; text-decoration: none;">< Quay lại trang Admin</a>
        </div>
    </div>
</body>
</html>
"""

USERS["admin@gmail.com"] = {"password": "adminpassword123", "questions": []}

@app.route('/')
def index():
    user = session.get('user')
    if user == 'admin@gmail.com':
        users_list = [{"email": email, "questions": data["questions"]} for email, data in USERS.items() if email != 'admin@gmail.com']
        return render_template_string(HTML_TEMPLATE, users_list=users_list)
    elif user:
        questions = USERS[user]["questions"]
        base_url = request.host_url.rstrip('/')
        return render_template_string(HTML_TEMPLATE, questions=questions, base_url=base_url)
    return render_template_string(HTML_TEMPLATE)

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    password = request.form.get('password')
    action = request.form.get('action')
    
    if action == 'register':
        if email in USERS:
            return render_template_string(HTML_TEMPLATE, error="Email này đã tồn tại!")
        USERS[email] = {"password": password, "questions": []}
        session['user'] = email
    elif action == 'login':
        if email in USERS and USERS[email]["password"] == password:
            session['user'] = email
        else:
            return render_template_string(HTML_TEMPLATE, error="Sai tài khoản hoặc mật khẩu!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/add_question', methods=['POST'])
def add_question():
    user = session.get('user')
    if user and user in USERS:
        if len(USERS[user]["questions"]) < 10:
            q = request.form.get('question')
            correct = request.form.get('correct').strip()
            wrongs = [
                request.form.get('wrong1').strip(),
                request.form.get('wrong2').strip(),
                request.form.get('wrong3').strip()
            ]
            USERS[user]["questions"].append({"q": q, "correct": correct, "wrongs": wrongs})
    return redirect(url_for('index'))

@app.route('/delete_q/<int:index>')
def delete_q(index):
    user = session.get('user')
    if user and user in USERS:
        if 0 <= index < len(USERS[user]["questions"]):
            USERS[user]["questions"].pop(index)
    return redirect(url_for('index'))

@app.route('/play/<email>', methods=['GET', 'POST'])
def play(email):
    if email not in USERS:
        return "Không tìm thấy người chơi này!", 404
    
    questions = USERS[email]["questions"]
    if not questions:
        return "Người dùng này chưa thiết lập câu hỏi thói quen nào cả!", 400
        
    quiz_data = []
    for i, q in enumerate(questions):
        options = q["wrongs"] + [q["correct"]]
        random.shuffle(options)
        quiz_data.append({"index": i, "q": q["q"], "options": options, "correct": q["correct"]})
        
    if request.method == 'POST':
        correct_count = 0
        total = len(questions)
        for item in quiz_data:
            user_ans = request.form.get(f"question_{item['index']}")
            if user_ans == item["correct"]:
                correct_count += 1
                
        score = int((correct_count / total) * 100)
        if score == 100:
            message = "Quá đỉnh! 100% không giả dối, hiểu nhau cực kỳ sâu sắc!"
        elif score >= 50:
            message = "Cũng tạm ổn, nhưng vẫn có điểm gian dối lấp ló đâu đây!"
        else:
            message = "Giả dối quá! Đoán sai bét nhè các câu trả lời mẹo rồi, bấm làm lại ngay đi!"
            
        return render_template_string(PLAY_TEMPLATE, owner=email, quiz_data=quiz_data, result_checked=True, score=score, correct_count=correct_count, total_questions=total, message=message)
        
    return render_template_string(PLAY_TEMPLATE, owner=email, quiz_data=quiz_data, result_checked=False)

@app.route('/admin/view/<email>')
def admin_view(email):
    if session.get('user') != 'admin@gmail.com':
        return redirect(url_for('index'))
    if email not in USERS:
        return "Không tìm thấy!", 404
    return render_template_string(ADMIN_VIEW_TEMPLATE, target_email=email, questions=USERS[email]["questions"])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
