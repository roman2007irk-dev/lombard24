# -*- coding: utf-8 -*-
import os
import re
import hashlib
import threading
import time
from datetime import date
from functools import wraps
from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.secret_key = 'lombard24_secret_key_2026'
app.config['JSON_AS_ASCII'] = False

# ==================== ПОДКЛЮЧЕНИЕ К БД (РАБОТАЕТ ВЕЗДЕ) ====================
def get_db():
    # Пытаемся получить переменные окружения Railway
    mysql_host = os.environ.get('MYSQLHOST')
    if mysql_host:
        return pymysql.connect(
            host=mysql_host,
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQLPASSWORD', ''),
            database=os.environ.get('MYSQLDATABASE', 'railway'),
            port=int(os.environ.get('MYSQLPORT', 3306)),
            cursorclass=DictCursor,
            autocommit=True,
            charset='utf8mb4'
        )
    # Локальная разработка (Docker)
    return pymysql.connect(
        host='db',
        user='root',
        password='root123',
        database='lombard24',
        cursorclass=DictCursor,
        autocommit=True,
        charset='utf8mb4'
    )

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Доступ запрещён. Требуются права администратора.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def check_overdue():
    with app.app_context():
        while True:
            time.sleep(86400)
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("UPDATE contracts SET status = 'overdue' WHERE status='active' AND due_date < CURDATE()")
                conn.commit()
                conn.close()
            except:
                pass

threading.Thread(target=check_overdue, daemon=True).start()

# ==================== HTML ШАБЛОНЫ ====================
# (все твои шаблоны должны быть здесь)
# Я укажу их кратко, но ты можешь вставить свои

LOGIN_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Lombard24 | Вход</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#eef2f5 100%);min-height:100vh;display:flex;justify-content:center;align-items:center}
.login{background:white;padding:50px;border-radius:32px;width:450px;box-shadow:0 20px 40px rgba(0,0,0,0.05);text-align:center}
h1{color:#2d6a4f;font-size:42px;margin-bottom:10px}
.sub{color:#6c757d;margin-bottom:30px}
input{width:100%;padding:15px;margin:12px 0;border:2px solid #e9ecef;border-radius:16px;font-size:16px}
input:focus{outline:none;border-color:#2d6a4f;box-shadow:0 0 0 3px rgba(45,106,79,0.1)}
button{width:100%;padding:15px;background:#2d6a4f;color:white;border:none;border-radius:16px;font-size:16px;font-weight:600;cursor:pointer}
button:hover{background:#1b4d3e}
.error{color:#dc3545;margin-top:15px}
</style></head>
<body><div class="login"><h1><i class="fas fa-gem"></i> Lombard24</h1><div class="sub">Современный ломбард</div>
<form method="post"><input type="text" name="username" placeholder="Логин"><input type="password" name="password" placeholder="Пароль"><button type="submit"><i class="fas fa-sign-in-alt"></i> Войти</button></form>
{% with msg = get_flashed_messages() %}{% if msg %}<div class="error">{{ msg[0] }}</div>{% endif %}{% endwith %}
<a href="/register" style="display:block;margin-top:20px;color:#2d6a4f;text-decoration:none">Нет аккаунта? Зарегистрироваться</a>
</div></body></html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Регистрация | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#eef2f5 100%);min-height:100vh;display:flex;justify-content:center;align-items:center}
.register{background:white;padding:40px;border-radius:32px;width:450px;box-shadow:0 20px 40px rgba(0,0,0,0.05);text-align:center}
h1{color:#2d6a4f;font-size:36px;margin-bottom:20px}
input{width:100%;padding:15px;margin:12px 0;border:2px solid #e9ecef;border-radius:16px;font-size:16px}
input:focus{outline:none;border-color:#2d6a4f;box-shadow:0 0 0 3px rgba(45,106,79,0.1)}
button{width:100%;padding:15px;background:#2d6a4f;color:white;border:none;border-radius:16px;font-size:16px;font-weight:600;cursor:pointer}
button:hover{background:#1b4d3e}
</style></head>
<body><div class="register"><h1><i class="fas fa-gem"></i> Lombard24</h1>
<form method="post"><input type="text" name="username" placeholder="Логин" required><input type="password" name="password" placeholder="Пароль" required><input type="text" name="full_name" placeholder="ФИО" required><button type="submit"><i class="fas fa-user-plus"></i> Зарегистрироваться</button></form>
<a href="/login" style="display:block;margin-top:20px;color:#2d6a4f;text-decoration:none">← Уже есть аккаунт? Войти</a>
</div></body></html>
'''

# ДЛЯ ЭКОНОМИИ МЕСТА — добавь остальные шаблоны из твоего app.py:
# DASHBOARD_HTML, CLIENTS_HTML, CLIENT_FORM, CONTRACTS_HTML, 
# CONTRACT_FORM, PAYMENTS_HTML, PAY_FORM, REPORTS_HTML, USERS_HTML

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            pwd = hashlib.md5(request.form['password'].encode()).hexdigest()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (request.form['username'], pwd))
            user = cur.fetchone()
            conn.close()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                return redirect(url_for('dashboard'))
            flash('Неверный логин или пароль')
        except Exception as e:
            flash(f'Ошибка подключения к БД: {str(e)}')
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            username = request.form['username'].strip()
            pwd = hashlib.md5(request.form['password'].encode()).hexdigest()
            full_name = request.form['full_name'].strip()
            
            if not username or len(username) < 3:
                flash('Логин должен содержать минимум 3 символа')
                return redirect(url_for('register'))
            if not full_name:
                flash('ФИО не может быть пустым')
                return redirect(url_for('register'))
            
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                flash('Логин уже существует')
                return redirect(url_for('register'))
            
            cur.execute("INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, 'user')", (username, pwd, full_name))
            conn.commit()
            conn.close()
            flash('Регистрация успешна!')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}')
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM contracts WHERE status='active'")
        active = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM contracts WHERE status='overdue' OR (status='active' AND due_date < CURDATE())")
        overdue_cnt = cur.fetchone()['cnt']
        cur.execute("SELECT COALESCE(SUM(loan_amount),0) as total FROM contracts")
        loans = cur.fetchone()['total']
        cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM payments")
        paid = cur.fetchone()['total']
        cur.execute("SELECT c.*, cl.full_name as client_name, DATEDIFF(CURDATE(), c.due_date) as days FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.status='active' AND c.due_date < CURDATE()")
        overdue = cur.fetchall()
        cur.execute("SELECT c.*, cl.full_name as client_name, (c.loan_amount - c.paid_amount) as remaining FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.status='active' AND c.due_date > CURDATE() ORDER BY c.due_date LIMIT 5")
        soon = cur.fetchall()
        conn.close()
        return render_template_string(DASHBOARD_HTML, username=session.get('username'), role=session.get('role', 'user'),
            stats={'active': active, 'overdue': overdue_cnt, 'loans': loans, 'paid': paid},
            overdue=overdue, soon=soon)
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Добавь остальные маршруты: /clients, /client/add, /contracts, /contract/add, /payments, /reports, /users
# Они такие же, как в твоём рабочем app.py

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
