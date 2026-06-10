# -*- coding: utf-8 -*-
import os
from flask import Flask, request, render_template_string, redirect, url_for, session, flash
from functools import wraps
import hashlib
import pymysql
from pymysql.cursors import DictCursor
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'lombard24_secret_key_2026'
app.config['JSON_AS_ASCII'] = False

# === ПРЯМЫЕ ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ ===
MYSQL_HOST = 'mysql.railway.internal'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'nznMsbPIayOTzVTXGHHgIIQptbHqOreF'
MYSQL_DATABASE = 'railway'
MYSQL_PORT = 3306

def get_db():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT,
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

# Инициализация БД
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, full_name VARCHAR(100), role VARCHAR(20) DEFAULT 'user')")
        cur.execute("INSERT IGNORE INTO users (username, password, full_name, role) VALUES ('admin', MD5('admin123'), 'Администратор', 'admin')")
        cur.execute("CREATE TABLE IF NOT EXISTS clients (id INT AUTO_INCREMENT PRIMARY KEY, full_name VARCHAR(150) NOT NULL, passport VARCHAR(20) UNIQUE NOT NULL, phone VARCHAR(20) NOT NULL, address TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS contracts (id INT AUTO_INCREMENT PRIMARY KEY, client_id INT NOT NULL, item_name VARCHAR(200) NOT NULL, pawn_amount DECIMAL(10,2) DEFAULT 0, loan_amount DECIMAL(10,2) NOT NULL, amount DECIMAL(10,2) NOT NULL, interest_rate DECIMAL(5,2) DEFAULT 5.0, start_date DATE NOT NULL, due_date DATE NOT NULL, status VARCHAR(20) DEFAULT 'active', paid_amount DECIMAL(10,2) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE)")
        cur.execute("CREATE TABLE IF NOT EXISTS payments (id INT AUTO_INCREMENT PRIMARY KEY, contract_id INT NOT NULL, amount DECIMAL(10,2) NOT NULL, payment_date DATE NOT NULL, payment_type VARCHAR(20) DEFAULT 'percent', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE)")
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")

init_db()

# ========== HTML ШАБЛОНЫ ==========
LOGIN_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Lombard24 | Вход</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;min-height:100vh;display:flex;justify-content:center;align-items:center}
.login{background:white;padding:40px;border-radius:24px;width:420px;box-shadow:0 10px 30px rgba(0,0,0,0.1)}
h1{color:#e6a017;font-size:36px;text-align:center}
.sub{color:#666;text-align:center;margin-bottom:30px}
input{width:100%;padding:14px;margin:12px 0;border:1px solid #ddd;border-radius:12px}
button{width:100%;padding:14px;background:#e6a017;color:#fff;border:none;border-radius:12px;font-weight:700;cursor:pointer}
.error{color:#e74c3c;text-align:center;margin-top:15px}
</style></head>
<body><div class="login"><h1>🏦 Lombard24</h1><div class="sub">Премиум ломбард</div>
<form method="post"><input type="text" name="username" placeholder="Логин"><input type="password" name="password" placeholder="Пароль"><button type="submit">Войти</button></form>
<a href="/register" style="display:block;text-align:center;margin-top:15px;color:#e6a017">Нет аккаунта? Зарегистрироваться</a>
{% with msg = get_flashed_messages() %}{% if msg %}<div class="error">{{ msg[0] }}</div>{% endif %}{% endwith %}</div></body></html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Регистрация | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;min-height:100vh;display:flex;justify-content:center;align-items:center}
.register{background:white;padding:40px;border-radius:24px;width:420px;box-shadow:0 10px 30px rgba(0,0,0,0.1)}
h1{color:#e6a017;font-size:36px;text-align:center}
input{width:100%;padding:14px;margin:12px 0;border:1px solid #ddd;border-radius:12px}
button{width:100%;padding:14px;background:#e6a017;color:#fff;border:none;border-radius:12px;font-weight:700;cursor:pointer}
</style></head>
<body><div class="register"><h1>🏦 Lombard24</h1><h3 style="text-align:center">Регистрация</h3>
<form method="post"><input type="text" name="full_name" placeholder="ФИО"><input type="text" name="username" placeholder="Логин"><input type="password" name="password" placeholder="Пароль"><button type="submit">Зарегистрироваться</button></form>
<a href="/login" style="display:block;text-align:center;margin-top:15px;color:#e6a017">Уже есть аккаунт? Войти</a>
{% with msg = get_flashed_messages() %}{% if msg %}<div class="error">{{ msg[0] }}</div>{% endif %}{% endwith %}</div></body></html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Lombard24 | Дашборд</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#fff;padding:15px 30px;display:flex;justify-content:space-between;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.logo{font-size:24px;font-weight:800;color:#e6a017}
.nav-links a{color:#555;text-decoration:none;margin-left:25px}
.nav-links a:hover{color:#e6a017}
.container{padding:30px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:30px}
.stat-card{background:#fff;padding:20px;border-radius:16px;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #e6a017}
.stat-value{font-size:28px;font-weight:800;color:#e6a017}
.stat-label{color:#888;margin-top:5px}
.section-title{font-size:20px;margin-bottom:15px;color:#333}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}
.card{background:#fff;border-radius:16px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
.card h3{margin-bottom:15px;color:#e6a017}
.contract-item{background:#f9f9f9;padding:12px;border-radius:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.overdue{background:#fff3f3;border-left:3px solid #e74c3c}
.btn{background:#e6a017;color:#fff;padding:5px 12px;border-radius:20px;text-decoration:none;font-size:12px}
</style></head>
<body>
<div class="navbar"><div class="logo">🏦 Lombard24</div><div class="nav-links">
<a href="/dashboard">Дашборд</a>
<a href="/clients">Клиенты</a>
<a href="/contracts">Договоры</a>
<a href="/payments">Платежи</a>
<a href="/reports">Отчёты</a>
{% if session.role == 'admin' %}<a href="/client/add" style="background:#e6a017;color:#fff;padding:5px 15px;border-radius:20px">+ Добавить клиента</a>{% endif %}
<span style="margin-left:20px">👤 {{ session.username }} ({{ session.role }})</span>
<a href="/logout">Выйти</a>
</div></div>
<div class="container">
<div class="stats"><div class="stat-card"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">Активных договоров</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.overdue }}</div><div class="stat-label">Просроченных</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.loans }} ₽</div><div class="stat-label">Выдано займов</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.paid }} ₽</div><div class="stat-label">Получено платежей</div></div></div>
<h2 class="section-title">⚠️ Просроченные договоры</h2>
<div class="grid"><div class="card">{% for c in overdue %}<div class="contract-item overdue"><div><b>{{ c.client_name }}</b><br><small>{{ c.item_name }}</small></div><div>просрочка {{ c.days }} дн.<br>{% if session.role == 'admin' %}<a href="/contract/{{ c.id }}/pay" class="btn">💰 Платёж</a>{% endif %}</div></div>{% else %}<p>Нет просрочек</p>{% endfor %}</div>
<div class="card"><h3>📅 Ближайшие выплаты</h3>{% for c in soon %}<div class="contract-item"><div><b>{{ c.client_name }}</b><br><small>{{ c.item_name }}</small></div><div>до {{ c.due_date }}<br>{{ c.remaining }} ₽</div></div>{% endfor %}</div></div></div></body></html>
'''

CLIENTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Клиенты | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#fff;padding:15px 30px;display:flex;justify-content:space-between;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.logo{color:#e6a017;font-size:24px;font-weight:800}
.nav-links a{color:#555;text-decoration:none;margin-left:25px}
.container{padding:30px}
table{width:100%;background:#fff;border-radius:16px;border-collapse:collapse;overflow:hidden}
th,td{padding:12px 15px;text-align:left;border-bottom:1px solid #eee}
th{background:#faf6f0;color:#333}
.btn{background:#e6a017;color:#fff;padding:10px 20px;border-radius:25px;text-decoration:none;display:inline-block;margin-bottom:20px}
</style></head>
<body><div class="navbar"><div class="logo">🏦 Lombard24</div><div class="nav-links"><a href="/dashboard">Дашборд</a><a href="/clients">Клиенты</a><a href="/contracts">Договоры</a><a href="/payments">Платежи</a><a href="/reports">Отчёты</a><span>👤 {{ session.username }} ({{ session.role }})</span><a href="/logout">Выйти</a></div></div>
<div class="container"><h1>👥 Клиенты</h1>
{% if session.role == 'admin' %}<a href="/client/add" class="btn">+ Добавить клиента</a>{% endif %}
<table><thead><tr><th>ID</th><th>ФИО</th><th>Паспорт</th><th>Телефон</th><th>Адрес</th></tr></thead>
<tbody>{% for c in clients %}<tr><td>{{ c.id }}</td><td>{{ c.full_name }}</td><td>{{ c.passport }}</td><td>{{ c.phone }}</td><td>{{ c.address or '' }}</td></tr>{% endfor %}</tbody></table></div></body></html>
'''

CONTRACTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Договоры | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#fff;padding:15px 30px;display:flex;justify-content:space-between;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.logo{color:#e6a017;font-size:24px;font-weight:800}
.nav-links a{color:#555;text-decoration:none;margin-left:25px}
.container{padding:30px}
table{width:100%;background:#fff;border-radius:16px;border-collapse:collapse;overflow:hidden}
th,td{padding:12px 15px;text-align:left;border-bottom:1px solid #eee}
th{background:#faf6f0;color:#333}
.badge-active{background:#d4edda;color:#155724;padding:4px 12px;border-radius:20px;font-size:12px}
.badge-overdue{background:#f8d7da;color:#721c24;padding:4px 12px;border-radius:20px;font-size:12px}
.badge-redeemed{background:#d1ecf1;color:#0c5460;padding:4px 12px;border-radius:20px;font-size:12px}
.btn{background:#e6a017;color:#fff;padding:5px 12px;border-radius:20px;text-decoration:none;font-size:12px}
</style></head>
<body><div class="navbar"><div class="logo">🏦 Lombard24</div><div class="nav-links"><a href="/dashboard">Дашборд</a><a href="/clients">Клиенты</a><a href="/contracts">Договоры</a><a href="/payments">Платежи</a><a href="/reports">Отчёты</a><span>👤 {{ session.username }} ({{ session.role }})</span><a href="/logout">Выйти</a></div></div>
<div class="container"><h1>📄 Договоры залога</h1>
{% if session.role == 'admin' %}<a href="/contract/add" class="btn">+ Оформить договор</a>{% endif %}
<table><thead><tr><th>№</th><th>Клиент</th><th>Залог</th><th>Сумма</th><th>Остаток</th><th>Срок до</th><th>Статус</th>{% if session.role == 'admin' %}<th>Действия</th>{% endif %}</tr></thead>
<tbody>{% for c in contracts %}<tr><td>{{ c.id }}</td><td>{{ c.client_name }}</td><td>{{ c.item_name }}</td><td>{{ c.loan_amount }} ₽</td><td>{{ c.remaining }} ₽</td><td>{{ c.due_date }}</td><td><span class="badge badge-{{ c.status }}">{{ c.status }}</span></td>{% if session.role == 'admin' %}<td><a href="/contract/{{ c.id }}/pay" class="btn">💰 Платёж</a></td>{% endif %}</tr>{% endfor %}</tbody></table></div></body></html>
'''

PAYMENTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Платежи | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#fff;padding:15px 30px;display:flex;justify-content:space-between;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.logo{color:#e6a017;font-size:24px;font-weight:800}
.nav-links a{color:#555;text-decoration:none;margin-left:25px}
.container{padding:30px}
table{width:100%;background:#fff;border-radius:16px;border-collapse:collapse;overflow:hidden}
th,td{padding:12px 15px;text-align:left;border-bottom:1px solid #eee}
th{background:#faf6f0;color:#333}
</style></head>
<body><div class="navbar"><div class="logo">🏦 Lombard24</div><div class="nav-links"><a href="/dashboard">Дашборд</a><a href="/clients">Клиенты</a><a href="/contracts">Договоры</a><a href="/payments">Платежи</a><a href="/reports">Отчёты</a><span>👤 {{ session.username }} ({{ session.role }})</span><a href="/logout">Выйти</a></div></div>
<div class="container"><h1>💳 История платежей</h1>
<table><thead><tr><th>Дата</th><th>Клиент</th><th>Залог</th><th>Сумма</th><th>Тип</th></tr></thead>
<tbody>{% for p in payments %}<tr><td>{{ p.payment_date }}</td><td>{{ p.client_name }}</td><td>{{ p.item_name }}</td><td>{{ p.amount }} ₽</td><td>{{ p.payment_type }}<tr>{% endfor %}</tbody></table></div></body></html>
'''

REPORTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Отчёты | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#fff;padding:15px 30px;display:flex;justify-content:space-between;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.logo{color:#e6a017;font-size:24px;font-weight:800}
.nav-links a{color:#555;text-decoration:none;margin-left:25px}
.container{padding:30px}
.card{background:#fff;border-radius:16px;padding:20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
.btn{background:#e6a017;color:#fff;padding:8px 16px;border-radius:25px;border:none;cursor:pointer}
input{padding:10px;border:1px solid #ddd;border-radius:8px}
</style></head>
<body><div class="navbar"><div class="logo">🏦 Lombard24</div><div class="nav-links"><a href="/dashboard">Дашборд</a><a href="/clients">Клиенты</a><a href="/contracts">Договоры</a><a href="/payments">Платежи</a><a href="/reports">Отчёты</a><span>👤 {{ session.username }} ({{ session.role }})</span><a href="/logout">Выйти</a></div></div>
<div class="container"><h1>📊 Финансовые отчёты</h1>
<div class="card"><h3>Доходы за период</h3><form method="get"><input type="date" name="start" value="{{ start }}"> — <input type="date" name="end" value="{{ end }}"><button type="submit" class="btn">Показать</button></form><p style="margin-top:15px"><strong>Доход:</strong> {{ total_income }} ₽</p></div>
<div class="card"><h3>Просроченные договоры</h3>{% for c in overdue %}<p>• {{ c.client_name }} — {{ c.item_name }} ({{ c.days }} дн., долг {{ c.debt }} ₽)</p>{% else %}<p>Нет просрочек</p>{% endfor %}</div>
<div class="card"><h3>Активные договоры</h3><p>Всего: {{ active_count }} на сумму {{ active_sum }} ₽</p></div></div></body></html>
'''

CLIENT_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Новый клиент</title><style>
body{background:#f5f5f5;font-family:'Inter',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:#fff;padding:30px;border-radius:16px;width:400px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
h2{color:#e6a017}input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px}
button{width:100%;padding:12px;background:#e6a017;color:#fff;border:none;border-radius:8px;cursor:pointer}
</style></head>
<body><div class="form"><h2>➕ Новый клиент</h2><form method="post"><input type="text" name="full_name" placeholder="ФИО"><input type="text" name="passport" placeholder="Паспорт"><input type="text" name="phone" placeholder="Телефон"><input type="text" name="address" placeholder="Адрес"><button type="submit">Сохранить</button></form><a href="/clients">← Назад</a></div></body></html>
'''

CONTRACT_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Новый договор</title><style>
body{background:#f5f5f5;font-family:'Inter',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:#fff;padding:30px;border-radius:16px;width:500px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
h2{color:#e6a017}input,select{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px}
button{width:100%;padding:12px;background:#e6a017;color:#fff;border:none;border-radius:8px;cursor:pointer}
</style></head>
<body><div class="form"><h2>📝 Оформить договор</h2><form method="post"><select name="client_id"><option value="">Выберите клиента</option>{% for c in clients %}<option value="{{ c.id }}">{{ c.full_name }}</option>{% endfor %}</select><input type="text" name="item_name" placeholder="Предмет залога"><input type="number" name="pawn_amount" placeholder="Оценочная стоимость"><input type="number" name="loan_amount" placeholder="Сумма займа"><input type="number" name="interest_rate" value="5"><input type="date" name="due_date"><button type="submit">Оформить</button></form><a href="/contracts">← Назад</a></div></body></html>
'''

PAY_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Приём платежа</title><style>
body{background:#f5f5f5;font-family:'Inter',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:#fff;padding:30px;border-radius:16px;width:450px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.info{background:#f9f9f9;padding:15px;border-radius:12px;margin-bottom:20px}
h2{color:#e6a017}input,select{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px}
button{width:100%;padding:12px;background:#e6a017;color:#fff;border:none;border-radius:8px;cursor:pointer}
</style></head>
<body><div class="form"><h2>💰 Приём платежа</h2><div class="info"><p><strong>Клиент:</strong> {{ contract.client_name }}</p><p><strong>Залог:</strong> {{ contract.item_name }}</p><p><strong>Остаток:</strong> {{ contract.remaining }} ₽</p></div>
<form method="post"><input type="number" name="amount" placeholder="Сумма" step="0.01"><select name="payment_type"><option value="percent">Проценты</option><option value="partial">Частичное погашение</option><option value="full">Полное погашение</option></select><button type="submit">Записать платёж</button></form><a href="/contracts">← Назад</a></div></body></html>
'''

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            flash('Пользователь с таким логином уже существует')
            return redirect(url_for('register'))
        hashed_pw = hashlib.md5(password.encode()).hexdigest()
        cur.execute("INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, 'user')", (username, hashed_pw, full_name))
        conn.commit()
        conn.close()
        flash('Регистрация успешна! Теперь войдите.')
        return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            pwd_hash = hashlib.md5(request.form['password'].encode()).hexdigest()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (request.form['username'], pwd_hash))
            user = cur.fetchone()
            conn.close()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            flash('Неверный логин или пароль')
        except Exception as e:
            flash(f'Ошибка БД: {e}')
    return render_template_string(LOGIN_HTML)

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
        return render_template_string(DASHBOARD_HTML, username=session.get('username'), role=session.get('role'),
            stats={'active': active, 'overdue': overdue_cnt, 'loans': loans, 'paid': paid},
            overdue=overdue, soon=soon)
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/clients')
def clients():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients ORDER BY id DESC")
        data = cur.fetchall()
        conn.close()
        return render_template_string(CLIENTS_HTML, clients=data, username=session.get('username'), role=session.get('role'))
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/client/add', methods=['GET', 'POST'])
@admin_required
def add_client():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO clients (full_name, passport, phone, address) VALUES (%s,%s,%s,%s)",
                        (request.form['full_name'], request.form['passport'], request.form['phone'], request.form.get('address','')))
            conn.commit()
            conn.close()
            return redirect(url_for('clients'))
        except Exception as e:
            flash(f'Ошибка: {e}')
    return render_template_string(CLIENT_FORM)

@app.route('/contracts')
def contracts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.*, cl.full_name as client_name,
            (c.loan_amount - c.paid_amount) as remaining
            FROM contracts c JOIN clients cl ON c.client_id = cl.id
            ORDER BY c.id DESC
        """)
        data = cur.fetchall()
        conn.close()
        return render_template_string(CONTRACTS_HTML, contracts=data, username=session.get('username'), role=session.get('role'))
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/contract/add', methods=['GET', 'POST'])
@admin_required
def add_contract():
    if request.method == 'POST':
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO contracts (client_id, item_name, pawn_amount, loan_amount, amount, interest_rate, start_date, due_date, status, paid_amount)
                VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'active', 0)
            """, (request.form['client_id'], request.form['item_name'], request.form['pawn_amount'],
                  request.form['loan_amount'], request.form['loan_amount'], request.form['interest_rate'], request.form['due_date']))
            conn.commit()
            conn.close()
            return redirect(url_for('contracts'))
        except Exception as e:
            flash(f'Ошибка: {e}')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name FROM clients")
    clients = cur.fetchall()
    conn.close()
    return render_template_string(CONTRACT_FORM, clients=clients)

@app.route('/contract/<int:id>/pay', methods=['GET', 'POST'])
@admin_required
def add_payment(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT c.*, cl.full_name as client_name FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.id=%s", (id,))
    contract = cur.fetchone()
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            ptype = request.form['payment_type']
            cur.execute("INSERT INTO payments (contract_id, amount, payment_date, payment_type) VALUES (%s, %s, CURDATE(), %s)", (id, amount, ptype))
            cur.execute("UPDATE contracts SET paid_amount = paid_amount + %s WHERE id=%s", (amount, id))
            cur.execute("UPDATE contracts SET status = 'redeemed' WHERE id=%s AND loan_amount - paid_amount <= 0", (id,))
            conn.commit()
            conn.close()
            return redirect(url_for('contracts'))
        except Exception as e:
            flash(f'Ошибка: {e}')
    conn.close()
    contract['remaining'] = contract['loan_amount'] - contract['paid_amount']
    return render_template_string(PAY_FORM, contract=contract)

@app.route('/payments')
def payments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.*, cl.full_name as client_name, c.item_name
            FROM payments p
            JOIN contracts c ON p.contract_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            ORDER BY p.payment_date DESC
        """)
        data = cur.fetchall()
        conn.close()
        return render_template_string(PAYMENTS_HTML, payments=data, username=session.get('username'), role=session.get('role'))
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    start = request.args.get('start', date.today().replace(day=1).isoformat())
    end = request.args.get('end', date.today().isoformat())
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE payment_date BETWEEN %s AND %s", (start, end))
        income = cur.fetchone()
        cur.execute("SELECT c.*, cl.full_name as client_name, (c.loan_amount - c.paid_amount) as debt, DATEDIFF(CURDATE(), c.due_date) as days FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.status='active' AND c.due_date < CURDATE()")
        overdue = cur.fetchall()
        cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(loan_amount - paid_amount),0) as total FROM contracts WHERE status='active'")
        active = cur.fetchone()
        conn.close()
        return render_template_string(REPORTS_HTML, total_income=income['total'], overdue=overdue, 
                                      active_count=active['cnt'], active_sum=active['total'], 
                                      username=session.get('username'), role=session.get('role'), start=start, end=end)
    except Exception as e:
        return f"Ошибка: {e}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
