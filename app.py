# -*- coding: utf-8 -*-
import os
import re
import hashlib
import threading
import time
from datetime import date, datetime
from functools import wraps
from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.secret_key = 'lombard24_secret_key_2026'
app.config['JSON_AS_ASCII'] = False

def get_db():
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

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Lombard24 | Дашборд</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03);position:sticky;top:0;z-index:100}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.logo i{color:#2d6a4f;margin-right:8px}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px;font-weight:500;transition:0.3s}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:25px;margin-bottom:40px}
.stat-card{background:white;padding:25px;border-radius:24px;box-shadow:0 2px 8px rgba(0,0,0,0.03);transition:0.3s;border:1px solid #e9ecef}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 8px 25px rgba(0,0,0,0.05)}
.stat-value{font-size:36px;font-weight:800;color:#2d6a4f}
.stat-label{color:#6c757d;margin-top:8px;font-size:14px}
.section-title{font-size:22px;margin-bottom:25px;color:#1a1a2e;display:flex;align-items:center;gap:10px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:25px}
.card{background:white;border-radius:24px;padding:25px;box-shadow:0 2px 8px rgba(0,0,0,0.03);border:1px solid #e9ecef}
.card h3{margin-bottom:20px;color:#2d6a4f;font-size:18px}
.contract-item{background:#f8f9fa;padding:15px;border-radius:16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;transition:0.3s}
.contract-item:hover{background:#e9ecef}
.overdue{background:#fff3f3;border-left:4px solid #dc3545}
.btn{background:#2d6a4f;color:white;padding:8px 20px;border-radius:40px;text-decoration:none;font-size:13px;font-weight:500;transition:0.3s;display:inline-block}
.btn:hover{background:#1b4d3e;transform:scale(1.02)}
</style></head>
<body>
<div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div>
<div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a>{% if role == 'admin' %}<a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a>{% endif %}<span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container">
<div class="stats"><div class="stat-card"><div class="stat-value">{{ stats.active }}</div><div class="stat-label"><i class="fas fa-check-circle"></i> Активных договоров</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.overdue }}</div><div class="stat-label"><i class="fas fa-exclamation-triangle"></i> Просроченных</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.loans }} ₽</div><div class="stat-label"><i class="fas fa-ruble-sign"></i> Выдано займов</div></div>
<div class="stat-card"><div class="stat-value">{{ stats.paid }} ₽</div><div class="stat-label"><i class="fas fa-hand-holding-usd"></i> Получено платежей</div></div></div>
<h2 class="section-title"><i class="fas fa-exclamation-triangle" style="color:#dc3545"></i> Просроченные договоры</h2>
<div class="grid"><div class="card">{% for c in overdue %}<div class="contract-item overdue"><div><b>{{ c.client_name }}</b><br><small style="color:#6c757d">{{ c.item_name }}</small></div><div style="text-align:right"><span style="color:#dc3545;font-weight:600">{{ c.days }} дн.</span><br>{% if role == 'admin' %}<a href="/contract/{{ c.id }}/pay" class="btn" style="margin-top:8px;display:inline-block">💰 Принять платёж</a>{% endif %}</div></div>{% else %}<p style="color:#6c757d">Нет просроченных договоров</p>{% endfor %}</div>
<div class="card"><h3><i class="fas fa-calendar-alt"></i> Ближайшие выплаты</h3>{% for c in soon %}<div class="contract-item"><div><b>{{ c.client_name }}</b><br><small style="color:#6c757d">{{ c.item_name }}</small></div><div style="text-align:right"><span style="color:#2d6a4f">до {{ c.due_date }}</span><br><span class="stat-value" style="font-size:16px">{{ c.remaining }} ₽</span></div></div>{% endfor %}</div></div></div></body></html>
'''

CLIENTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Клиенты | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03)}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
h1{margin-bottom:25px;color:#1a1a2e;display:flex;align-items:center;gap:10px}
table{width:100%;background:white;border-radius:20px;border-collapse:collapse;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.03)}
th,td{padding:16px;text-align:left;border-bottom:1px solid #e9ecef}
th{background:#f8f9fa;color:#2d6a4f;font-weight:600}
.btn{background:#2d6a4f;color:white;padding:10px 24px;border-radius:40px;text-decoration:none;display:inline-block;margin-bottom:25px;font-weight:500;transition:0.3s}
.btn:hover{background:#1b4d3e}
.btn-sm{background:#2d6a4f;color:white;padding:6px 14px;border-radius:30px;text-decoration:none;font-size:12px;display:inline-block;margin:0 3px}
.btn-sm:hover{background:#1b4d3e}
.btn-danger{background:#dc3545;color:white;padding:6px 14px;border-radius:30px;text-decoration:none;font-size:12px;display:inline-block}
.btn-danger:hover{background:#bb2d3b}
</style></head>
<body><div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div>
<div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a>{% if role == 'admin' %}<a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a>{% endif %}<span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container"><h1><i class="fas fa-users"></i> Клиенты</h1>
{% if role == 'admin' %}<a href="/client/add" class="btn"><i class="fas fa-plus"></i> Добавить клиента</a>{% endif %}
<br><br>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead style="background-color: #2d6a4f; color: white;">
<tr>
<th>ID</th><th>ФИО</th><th>Паспорт</th><th>Телефон</th><th>Адрес</th>{% if role == 'admin' %}<th>Действия</th>{% endif %}
</tr>
</thead>
<tbody>
{% for c in clients %}
<tr>
<td>{{ c.id }}</td>
<td>{{ c.full_name }}</td>
<td>{{ c.passport }}</td>
<td>{{ c.phone }}</td>
<td>{{ c.address or '' }}</td>
{% if role == 'admin' %}
<td><a href="/client/edit/{{ c.id }}" class="btn-sm"><i class="fas fa-edit"></i> Ред</a> <a href="/client/delete/{{ c.id }}" class="btn-danger" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i> Удалить</a></td>
{% endif %}
</tr>
{% endfor %}
</tbody>
</table>
<a href="/" style="color:#2d6a4f;display:block;margin-top:20px">← На главную</a>
</div></body></html>
'''

CLIENT_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{% if client %}Редактировать клиента{% else %}Новый клиент{% endif %}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:white;padding:40px;border-radius:28px;width:480px;box-shadow:0 20px 40px rgba(0,0,0,0.05)}
h2{color:#2d6a4f;margin-bottom:25px;display:flex;align-items:center;gap:10px}
input{width:100%;padding:14px;margin:12px 0;border:2px solid #e9ecef;border-radius:16px;font-size:15px;transition:0.3s}
input:focus{outline:none;border-color:#2d6a4f}
button{background:#2d6a4f;color:white;padding:14px;border:none;border-radius:16px;width:100%;font-weight:600;font-size:16px;cursor:pointer;transition:0.3s}
button:hover{background:#1b4d3e}
</style></head>
<body><div class="form"><h2>{% if client %}<i class="fas fa-edit"></i> Редактировать клиента{% else %}<i class="fas fa-user-plus"></i> Новый клиент{% endif %}</h2>
<form method="post" id="clientForm">
<input type="text" name="full_name" placeholder="ФИО" value="{{ client.full_name if client else '' }}" required>
<input type="text" name="passport" placeholder="Паспорт" value="{{ client.passport if client else '' }}" required>
<input type="text" name="phone" id="phone" placeholder="Телефон" value="{{ client.phone if client else '' }}" required>
<input type="text" name="address" placeholder="Адрес" value="{{ client.address if client else '' }}">
<button type="submit">{% if client %}<i class="fas fa-save"></i> Сохранить{% else %}<i class="fas fa-plus"></i> Добавить{% endif %}</button>
</form><a href="/clients" style="color:#2d6a4f;display:block;margin-top:20px;text-align:center">← Назад</a></div>
<script>
document.getElementById('clientForm').addEventListener('submit', function(e) {
    let phone = document.getElementById('phone').value;
    let phoneRegex = /^\+?[0-9]{10,15}$/;
    if (!phoneRegex.test(phone)) { alert('Ошибка: неверный формат телефона'); e.preventDefault(); }
});
</script></body></html>
'''

CLIENT_EDIT_FORM = CLIENT_FORM

CONTRACTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Договоры | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03)}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
table{width:100%;background:white;border-radius:20px;border-collapse:collapse;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.03)}
th,td{padding:14px;text-align:left;border-bottom:1px solid #e9ecef}
th{background:#f8f9fa;color:#2d6a4f}
.badge{padding:4px 12px;border-radius:30px;font-size:12px;font-weight:500}
.badge-active{background:#d4edda;color:#155724}
.badge-overdue{background:#f8d7da;color:#721c24}
.btn{background:#2d6a4f;color:white;padding:6px 14px;border-radius:30px;text-decoration:none;font-size:12px;display:inline-block;margin:2px}
.btn-sm{background:#2d6a4f;color:white;padding:5px 12px;border-radius:30px;text-decoration:none;font-size:11px}
.btn-danger{background:#dc3545;color:white;padding:5px 12px;border-radius:30px;text-decoration:none;font-size:11px}
</style></head>
<body><div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div>
<div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a>{% if role == 'admin' %}<a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a>{% endif %}<span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container"><h1><i class="fas fa-file-contract"></i> Договоры залога</h1>
{% if role == 'admin' %}<a href="/contract/add" class="btn"><i class="fas fa-plus"></i> Оформить договор</a>{% endif %}<br><br>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead style="background-color: #2d6a4f; color: white;">
<tr>
<th>№</th><th>Клиент</th><th>Залог</th><th>Сумма</th><th>Остаток</th><th>Срок до</th><th>Статус</th>{% if role == 'admin' %}<th>Действия</th>{% endif %}
</tr>
</thead>
<tbody>
{% for c in contracts %}
<tr>
<td>{{ c.id }}</td>
<td>{{ c.client_name }}</td>
<td>{{ c.item_name }}</td>
<td>{{ c.loan_amount }} ₽</td>
<td>{{ c.remaining }} ₽</td>
<td>{{ c.due_date }}</td>
<td><span class="badge badge-{{ c.status }}">{{ c.status }}</span></td>
{% if role == 'admin' %}
<td><a href="/contract/edit/{{ c.id }}" class="btn-sm"><i class="fas fa-edit"></i></a> <a href="/contract/delete/{{ c.id }}" class="btn-danger" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i></a> <a href="/contract/{{ c.id }}/pay" class="btn"><i class="fas fa-money-bill-wave"></i> Платёж</a></td>
{% endif %}
</tr>
{% endfor %}
</tbody>
</table>
<a href="/" style="color:#2d6a4f;display:block;margin-top:20px">← На главную</a>
</div></body></html>
'''

CONTRACT_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{% if contract %}Редактировать договор{% else %}Новый договор{% endif %}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:white;padding:40px;border-radius:28px;width:550px;box-shadow:0 20px 40px rgba(0,0,0,0.05)}
h2{color:#2d6a4f;margin-bottom:25px}
input,select{width:100%;padding:14px;margin:12px 0;border:2px solid #e9ecef;border-radius:16px;font-size:15px}
input:focus,select:focus{outline:none;border-color:#2d6a4f}
button{background:#2d6a4f;color:white;padding:14px;border:none;border-radius:16px;width:100%;font-weight:600;cursor:pointer;transition:0.3s}
button:hover{background:#1b4d3e}
</style></head>
<body><div class="form"><h2>{% if contract %}<i class="fas fa-edit"></i> Редактировать договор{% else %}<i class="fas fa-plus"></i> Оформить договор{% endif %}</h2>
<form method="post" id="contractForm">
<select name="client_id" required>{% for c in clients %}<option value="{{ c.id }}" {% if contract and contract.client_id == c.id %}selected{% endif %}>{{ c.full_name }}</option>{% endfor %}</select>
<input type="text" name="item_name" placeholder="Предмет залога" value="{{ contract.item_name if contract else '' }}" required>
<input type="number" name="pawn_amount" placeholder="Оценочная стоимость" step="0.01" value="{{ contract.pawn_amount if contract else '' }}" id="pawn_amount">
<input type="number" name="loan_amount" id="loan_amount" placeholder="Сумма займа" step="0.01" value="{{ contract.loan_amount if contract else '' }}" required>
<input type="number" name="interest_rate" value="{{ contract.interest_rate if contract else 5 }}" step="0.1">
<input type="date" name="due_date" id="due_date" value="{{ contract.due_date if contract else '' }}" required>
<button type="submit">{% if contract %}<i class="fas fa-save"></i> Сохранить{% else %}<i class="fas fa-check"></i> Оформить{% endif %}</button>
</form>
<a href="/contracts" style="color:#2d6a4f;display:block;margin-top:20px;text-align:center">← Назад</a></div>
<script>
document.getElementById('contractForm').addEventListener('submit', function(e) {
    let loan_amount = parseFloat(document.getElementById('loan_amount').value);
    let pawn_amount = parseFloat(document.getElementById('pawn_amount').value || 0);
    let due_date = document.getElementById('due_date').value;
    let today = new Date().toISOString().split('T')[0];
    
    if (loan_amount <= 0) {
        alert('Ошибка: Сумма займа должна быть положительной');
        e.preventDefault();
    } else if (pawn_amount > 0 && loan_amount > pawn_amount) {
        alert('Ошибка: Сумма займа не может превышать оценочную стоимость');
        e.preventDefault();
    } else if (due_date < today) {
        alert('Ошибка: Срок возврата не может быть в прошлом');
        e.preventDefault();
    }
});
</script></body></html>
'''

PAYMENTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Платежи | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03)}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
table{width:100%;background:white;border-radius:20px;border-collapse:collapse;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.03)}
th,td{padding:14px;text-align:left;border-bottom:1px solid #e9ecef}
th{background:#f8f9fa;color:#2d6a4f}
.btn-danger{background:#dc3545;color:white;padding:5px 12px;border-radius:30px;text-decoration:none;font-size:11px}
</style></head>
<body><div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div><div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a>{% if role == 'admin' %}<a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a>{% endif %}<span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container"><h1><i class="fas fa-credit-card"></i> История платежей</h1>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead style="background-color: #2d6a4f; color: white;">
<tr>
<th>Дата</th><th>Клиент</th><th>Залог</th><th>Сумма</th><th>Тип</th>{% if role == 'admin' %}<th>Действия</th>{% endif %}
</tr>
</thead>
<tbody>
{% for p in payments %}
<tr>
<td>{{ p.payment_date }}</td>
<td>{{ p.client_name }}</td>
<td>{{ p.item_name }}</td>
<td>{{ p.amount }} ₽</td>
<td>{{ p.payment_type }}</td>
{% if role == 'admin' %}
<td><a href="/payment/delete/{{ p.id }}" class="btn-danger" onclick="return confirm('Удалить платёж?')"><i class="fas fa-trash"></i> Удалить</a></td>
{% endif %}
</tr>
{% endfor %}
</tbody>
</table>
<a href="/" style="color:#2d6a4f;display:block;margin-top:20px">← На главную</a>
</div></body></html>
'''

PAY_FORM = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Приём платежа</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;display:flex;justify-content:center;align-items:center;min-height:100vh}
.form{background:white;padding:40px;border-radius:28px;width:500px;box-shadow:0 20px 40px rgba(0,0,0,0.05)}
.info{background:#f8f9fa;padding:20px;border-radius:20px;margin-bottom:25px}
h2{color:#2d6a4f;margin-bottom:25px}
input,select{width:100%;padding:14px;margin:12px 0;border:2px solid #e9ecef;border-radius:16px;font-size:15px}
input:focus,select:focus{outline:none;border-color:#2d6a4f}
button{background:#2d6a4f;color:white;padding:14px;border:none;border-radius:16px;width:100%;font-weight:600;cursor:pointer;transition:0.3s}
button:hover{background:#1b4d3e}
</style></head>
<body><div class="form"><h2><i class="fas fa-money-bill-wave"></i> Приём платежа</h2>
<div class="info"><p><strong><i class="fas fa-user"></i> Клиент:</strong> {{ contract.client_name }}</p><p><strong><i class="fas fa-gem"></i> Залог:</strong> {{ contract.item_name }}</p><p><strong><i class="fas fa-ruble-sign"></i> Остаток:</strong> <span id="remaining">{{ contract.remaining }}</span> ₽</p></div>
<form method="post" id="paymentForm">
<input type="number" name="amount" id="amount" placeholder="Сумма" step="0.01" required>
<select name="payment_type" required><option value="percent">Проценты</option><option value="partial">Частичное погашение</option><option value="full">Полное погашение</option></select>
<button type="submit"><i class="fas fa-check"></i> Записать платёж</button>
</form>
<a href="/contracts" style="color:#2d6a4f;display:block;margin-top:20px;text-align:center">← Назад</a></div>
<script>
document.getElementById('paymentForm').addEventListener('submit', function(e) {
    let amount = parseFloat(document.getElementById('amount').value);
    let remaining = parseFloat(document.getElementById('remaining').innerText);
    if (amount <= 0) {
        alert('Ошибка: Сумма платежа должна быть положительной');
        e.preventDefault();
    } else if (amount > remaining) {
        alert('Ошибка: Сумма платежа превышает остаток по договору');
        e.preventDefault();
    }
});
</script></body></html>
'''

REPORTS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Отчёты | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03)}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
.card{background:white;border-radius:24px;padding:25px;margin-bottom:25px;box-shadow:0 2px 8px rgba(0,0,0,0.03);border:1px solid #e9ecef}
.card h3{color:#2d6a4f;margin-bottom:20px}
.btn{background:#2d6a4f;color:white;padding:10px 24px;border-radius:40px;border:none;cursor:pointer;font-weight:500;transition:0.3s}
.btn:hover{background:#1b4d3e}
input{padding:12px;background:white;border:2px solid #e9ecef;border-radius:16px;margin:0 5px}
</style></head>
<body><div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div><div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a>{% if role == 'admin' %}<a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a>{% endif %}<span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container"><h1><i class="fas fa-chart-bar"></i> Финансовые отчёты</h1>
<div class="card"><h3><i class="fas fa-calendar-alt"></i> Доходы за период</h3><form method="get"><input type="date" name="start" value="{{ start }}"> — <input type="date" name="end" value="{{ end }}"><button type="submit" class="btn"><i class="fas fa-search"></i> Показать</button></form><p style="margin-top:20px;font-size:24px;color:#2d6a4f"><strong>{{ total_income }} ₽</strong></p></div>
<div class="card"><h3><i class="fas fa-exclamation-triangle"></i> Просроченные договоры</h3>{% for c in overdue %}<p>• {{ c.client_name }} — {{ c.item_name }} ({{ c.days }} дн., долг {{ c.debt }} ₽)</p>{% endfor %}</div>
<div class="card"><h3><i class="fas fa-chart-line"></i> Активные договоры</h3><p>Всего: <strong>{{ active_count }}</strong> на сумму <strong>{{ active_sum }} ₽</strong></p></div></div></body></html>
'''

USERS_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Пользователи | Lombard24</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f7fa;color:#1a1a2e}
.navbar{background:white;padding:18px 40px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.03)}
.logo{font-size:28px;font-weight:800;color:#2d6a4f}
.nav-links a{color:#4a4a5a;text-decoration:none;margin-left:30px}
.nav-links a:hover{color:#2d6a4f}
.container{padding:40px}
table{width:100%;background:white;border-radius:20px;border-collapse:collapse;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.03)}
th,td{padding:14px;text-align:left;border-bottom:1px solid #e9ecef}
th{background:#f8f9fa;color:#2d6a4f}
.btn-sm{background:#2d6a4f;color:white;padding:5px 12px;border-radius:30px;text-decoration:none;font-size:11px;display:inline-block;margin:0 3px}
.btn-sm:hover{background:#1b4d3e}
.btn-danger{background:#dc3545;color:white;padding:5px 12px;border-radius:30px;text-decoration:none;font-size:11px}
</style></head>
<body><div class="navbar"><div class="logo"><i class="fas fa-gem"></i> Lombard24</div><div class="nav-links"><a href="/dashboard"><i class="fas fa-chart-line"></i> Дашборд</a><a href="/clients"><i class="fas fa-users"></i> Клиенты</a><a href="/contracts"><i class="fas fa-file-contract"></i> Договоры</a><a href="/payments"><i class="fas fa-credit-card"></i> Платежи</a><a href="/reports"><i class="fas fa-chart-bar"></i> Отчёты</a><a href="/users"><i class="fas fa-users-cog"></i> Пользователи</a><span style="margin-left:30px;color:#6c757d"><i class="fas fa-user-circle"></i> {{ username }} ({{ role }})</span><a href="/logout"><i class="fas fa-sign-out-alt"></i> Выйти</a></div></div>
<div class="container"><h1><i class="fas fa-users-cog"></i> Пользователи</h1>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<thead style="background-color: #2d6a4f; color: white;">
<tr>
<th>ID</th><th>Логин</th><th>ФИО</th><th>Роль</th><th>Действия</th>
</tr>
</thead>
<tbody>
{% for u in users %}
<tr>
<td>{{ u.id }}</td>
<td>{{ u.username }}</td>
<td>{{ u.full_name or '' }}</td>
<td><form method="post" action="/user/role/{{ u.id }}" style="display:inline"><select name="role"><option value="user" {% if u.role == 'user' %}selected{% endif %}>user</option><option value="admin" {% if u.role == 'admin' %}selected{% endif %}>admin</option></select><button type="submit" class="btn-sm">Изменить</button></form></td>
<td>{% if u.username != 'admin' %}<a href="/user/delete/{{ u.id }}" class="btn-danger" onclick="return confirm('Удалить пользователя?')"><i class="fas fa-trash"></i> Удалить</a>{% else %}<span style="color:#6c757d">Нельзя удалить</span>{% endif %}</td>
</tr>
{% endfor %}
</tbody>
</table>
<a href="/dashboard" style="color:#2d6a4f;display:block;margin-top:20px">← На главную</a>
</div></body></html>
'''

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        username = request.form['username'].strip()
        pwd = hashlib.md5(request.form['password'].encode()).hexdigest()
        full_name = request.form['full_name'].strip()
        
        # Валидация
        if not username:
            flash('Ошибка: Логин не может быть пустым')
            return redirect(url_for('register'))
        if len(username) < 3:
            flash('Ошибка: Логин должен содержать минимум 3 символа')
            return redirect(url_for('register'))
        if not full_name:
            flash('Ошибка: ФИО не может быть пустым')
            return redirect(url_for('register'))
        
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash('Ошибка: Пользователь с таким логином уже существует')
            return redirect(url_for('register'))
        
        cur.execute("INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, 'user')", (username, pwd, full_name))
        conn.commit()
        conn.close()
        flash('Регистрация успешна!')
        return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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

@app.route('/clients')
def clients():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template_string(CLIENTS_HTML, clients=data, username=session.get('username'), role=session.get('role', 'user'))

@app.route('/client/add', methods=['GET', 'POST'])
@admin_required
def add_client():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        passport = request.form['passport'].strip()
        phone = request.form['phone'].strip()
        address = request.form.get('address', '').strip()
        
        # Валидация
        if not full_name:
            flash('Ошибка: ФИО не может быть пустым')
            return redirect(url_for('add_client'))
        if not passport:
            flash('Ошибка: Паспорт не может быть пустым')
            return redirect(url_for('add_client'))
        if not phone:
            flash('Ошибка: Телефон не может быть пустым')
            return redirect(url_for('add_client'))
        if not re.match(r'^\+?[0-9]{10,15}$', phone):
            flash('Ошибка: Телефон должен содержать 10-15 цифр, может начинаться с +')
            return redirect(url_for('add_client'))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM clients WHERE passport = %s", (passport,))
        if cur.fetchone():
            flash('Ошибка: Клиент с таким паспортом уже существует')
            conn.close()
            return redirect(url_for('add_client'))
        
        cur.execute("INSERT INTO clients (full_name, passport, phone, address) VALUES (%s,%s,%s,%s)", (full_name, passport, phone, address))
        conn.commit()
        conn.close()
        flash('Клиент успешно добавлен')
        return redirect(url_for('clients'))
    return render_template_string(CLIENT_FORM, client=None)

@app.route('/client/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_client(id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        passport = request.form['passport'].strip()
        phone = request.form['phone'].strip()
        address = request.form.get('address', '').strip()
        
        if not full_name:
            flash('Ошибка: ФИО не может быть пустым')
            return redirect(url_for('edit_client', id=id))
        if not passport:
            flash('Ошибка: Паспорт не может быть пустым')
            return redirect(url_for('edit_client', id=id))
        if not re.match(r'^\+?[0-9]{10,15}$', phone):
            flash('Ошибка: Неверный формат телефона')
            return redirect(url_for('edit_client', id=id))
        
        cur.execute("SELECT id FROM clients WHERE passport=%s AND id!=%s", (passport, id))
        if cur.fetchone():
            flash('Ошибка: Клиент с таким паспортом уже существует')
            return redirect(url_for('edit_client', id=id))
        
        cur.execute("UPDATE clients SET full_name=%s, passport=%s, phone=%s, address=%s WHERE id=%s", (full_name, passport, phone, address, id))
        conn.commit()
        conn.close()
        flash('Клиент обновлён')
        return redirect(url_for('clients'))
    cur.execute("SELECT * FROM clients WHERE id=%s", (id,))
    client = cur.fetchone()
    conn.close()
    return render_template_string(CLIENT_EDIT_FORM, client=client)

@app.route('/client/delete/<int:id>')
@admin_required
def delete_client(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Клиент удалён')
    return redirect(url_for('clients'))

@app.route('/contracts')
def contracts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT c.*, cl.full_name as client_name, (c.loan_amount - c.paid_amount) as remaining FROM contracts c JOIN clients cl ON c.client_id = cl.id ORDER BY c.id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template_string(CONTRACTS_HTML, contracts=data, username=session.get('username'), role=session.get('role', 'user'))

@app.route('/contract/add', methods=['GET', 'POST'])
@admin_required
def add_contract():
    if request.method == 'POST':
        client_id = request.form['client_id']
        item_name = request.form['item_name'].strip()
        pawn_amount = float(request.form['pawn_amount'] or 0)
        loan_amount = float(request.form['loan_amount'])
        interest_rate = float(request.form['interest_rate'])
        due_date = request.form['due_date']
        
        # Валидация
        if not client_id:
            flash('Ошибка: Выберите клиента')
            return redirect(url_for('add_contract'))
        if not item_name:
            flash('Ошибка: Предмет залога не может быть пустым')
            return redirect(url_for('add_contract'))
        if loan_amount <= 0:
            flash('Ошибка: Сумма займа должна быть положительной')
            return redirect(url_for('add_contract'))
        if pawn_amount > 0 and loan_amount > pawn_amount:
            flash('Ошибка: Сумма займа не может превышать оценочную стоимость')
            return redirect(url_for('add_contract'))
        if due_date < date.today().isoformat():
            flash('Ошибка: Срок возврата не может быть в прошлом')
            return redirect(url_for('add_contract'))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM clients WHERE id=%s", (client_id,))
        if not cur.fetchone():
            flash('Ошибка: Выбранный клиент не существует')
            conn.close()
            return redirect(url_for('add_contract'))
        
        cur.execute("""
            INSERT INTO contracts (client_id, item_name, pawn_amount, loan_amount, amount, interest_rate, start_date, due_date, status, paid_amount)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'active', 0)
        """, (client_id, item_name, pawn_amount, loan_amount, loan_amount, interest_rate, due_date))
        conn.commit()
        conn.close()
        flash('Договор успешно оформлен')
        return redirect(url_for('contracts'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name FROM clients")
    clients = cur.fetchall()
    conn.close()
    return render_template_string(CONTRACT_FORM, contract=None, clients=clients)

@app.route('/contract/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_contract(id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'POST':
        client_id = request.form['client_id']
        item_name = request.form['item_name'].strip()
        pawn_amount = float(request.form['pawn_amount'] or 0)
        loan_amount = float(request.form['loan_amount'])
        interest_rate = float(request.form['interest_rate'])
        due_date = request.form['due_date']
        
        if loan_amount <= 0:
            flash('Ошибка: Сумма займа должна быть положительной')
            return redirect(url_for('edit_contract', id=id))
        if pawn_amount > 0 and loan_amount > pawn_amount:
            flash('Ошибка: Сумма займа не может превышать оценочную стоимость')
            return redirect(url_for('edit_contract', id=id))
        if due_date < date.today().isoformat():
            flash('Ошибка: Срок возврата не может быть в прошлом')
            return redirect(url_for('edit_contract', id=id))
        
        cur.execute("""
            UPDATE contracts SET client_id=%s, item_name=%s, pawn_amount=%s, loan_amount=%s, interest_rate=%s, due_date=%s WHERE id=%s
        """, (client_id, item_name, pawn_amount, loan_amount, interest_rate, due_date, id))
        conn.commit()
        conn.close()
        flash('Договор обновлён')
        return redirect(url_for('contracts'))
    
    cur.execute("SELECT * FROM contracts WHERE id=%s", (id,))
    contract = cur.fetchone()
    cur.execute("SELECT id, full_name FROM clients")
    clients = cur.fetchall()
    conn.close()
    return render_template_string(CONTRACT_FORM, contract=contract, clients=clients)

@app.route('/contract/delete/<int:id>')
@admin_required
def delete_contract(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM contracts WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Договор удалён')
    return redirect(url_for('contracts'))

@app.route('/contract/<int:id>/pay', methods=['GET', 'POST'])
@admin_required
def add_payment(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT c.*, cl.full_name as client_name FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.id=%s", (id,))
    contract = cur.fetchone()
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        ptype = request.form['payment_type']
        remaining = contract['loan_amount'] - contract['paid_amount']
        
        if amount <= 0:
            flash('Ошибка: Сумма платежа должна быть положительной')
            return redirect(url_for('add_payment', id=id))
        if amount > remaining:
            flash('Ошибка: Сумма платежа превышает остаток по договору')
            return redirect(url_for('add_payment', id=id))
        
        cur.execute("INSERT INTO payments (contract_id, amount, payment_date, payment_type) VALUES (%s, %s, CURDATE(), %s)", (id, amount, ptype))
        cur.execute("UPDATE contracts SET paid_amount = paid_amount + %s WHERE id=%s", (amount, id))
        cur.execute("UPDATE contracts SET status = 'redeemed' WHERE id=%s AND loan_amount - paid_amount <= 0", (id,))
        conn.commit()
        conn.close()
        flash('Платёж успешно принят')
        return redirect(url_for('contracts'))
    
    conn.close()
    contract['remaining'] = contract['loan_amount'] - contract['paid_amount']
    return render_template_string(PAY_FORM, contract=contract)

@app.route('/payments')
def payments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.*, cl.full_name as client_name, c.item_name FROM payments p JOIN contracts c ON p.contract_id = c.id JOIN clients cl ON c.client_id = cl.id ORDER BY p.payment_date DESC")
    data = cur.fetchall()
    conn.close()
    return render_template_string(PAYMENTS_HTML, payments=data, username=session.get('username'), role=session.get('role', 'user'))

@app.route('/payment/delete/<int:id>')
@admin_required
def delete_payment(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Платёж удалён')
    return redirect(url_for('payments'))

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    start = request.args.get('start', date.today().replace(day=1).isoformat())
    end = request.args.get('end', date.today().isoformat())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE payment_date BETWEEN %s AND %s", (start, end))
    income = cur.fetchone()
    cur.execute("SELECT c.*, cl.full_name as client_name, (c.loan_amount - c.paid_amount) as debt, DATEDIFF(CURDATE(), c.due_date) as days FROM contracts c JOIN clients cl ON c.client_id = cl.id WHERE c.status='active' AND c.due_date < CURDATE()")
    overdue = cur.fetchall()
    cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(loan_amount - paid_amount),0) as total FROM contracts WHERE status='active'")
    active = cur.fetchone()
    conn.close()
    return render_template_string(REPORTS_HTML, total_income=income['total'], overdue=overdue, active_count=active['cnt'], active_sum=active['total'], username=session.get('username'), role=session.get('role', 'user'), start=start, end=end)

@app.route('/users')
@admin_required
def users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, role FROM users ORDER BY id")
    data = cur.fetchall()
    conn.close()
    return render_template_string(USERS_HTML, users=data, username=session.get('username'), role=session.get('role', 'user'))

@app.route('/user/role/<int:id>', methods=['POST'])
@admin_required
def change_role(id):
    new_role = request.form['role']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role=%s WHERE id=%s", (new_role, id))
    conn.commit()
    conn.close()
    flash('Роль пользователя изменена')
    return redirect(url_for('users'))

@app.route('/user/delete/<int:id>')
@admin_required
def delete_user(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Пользователь удалён')
    return redirect(url_for('users'))

@app.errorhandler(404)
def not_found(e):
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>404</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"><style>body{font-family:Inter;background:#f5f7fa;display:flex;justify-content:center;align-items:center;height:100vh}.error{text-align:center;color:#1a1a2e}h1{font-size:100px;color:#2d6a4f}a{color:#2d6a4f;text-decoration:none}</style><body><div class="error"><h1>404</h1><p>Страница не найдена</p><a href="/dashboard"><i class="fas fa-home"></i> На главную</a></div></body></html>', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
