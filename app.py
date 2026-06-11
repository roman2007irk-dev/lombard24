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

# ==================== ПОДКЛЮЧЕНИЕ К БД (РАБОТАЕТ И ТАМ, И ТАМ) ====================
def get_db():
    if os.environ.get('MYSQLHOST'):
        return pymysql.connect(
            host=os.environ.get('MYSQLHOST'),
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQLPASSWORD', ''),
            database=os.environ.get('MYSQLDATABASE', 'railway'),
            port=int(os.environ.get('MYSQLPORT', 3306)),
            cursorclass=DictCursor,
            autocommit=True,
            charset='utf8mb4'
        )
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

# ==================== ВСЕ ТВОИ HTML ШАБЛОНЫ (ДИЗАЙН КАК БЫЛ) ====================
# ВСТАВЬ СЮДА ВСЕ СВОИ ШАБЛОНЫ ИЗ ТВОЕГО РАБОЧЕГО app.py
# (LOGIN_HTML, REGISTER_HTML, DASHBOARD_HTML, CLIENTS_HTML, CLIENT_FORM,
#  CONTRACTS_HTML, CONTRACT_FORM, PAYMENTS_HTML, PAY_FORM, REPORTS_HTML, USERS_HTML)

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

# ОСТАЛЬНЫЕ МАРШРУТЫ (clients, contracts, payments, reports, users) - вставь свои

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
