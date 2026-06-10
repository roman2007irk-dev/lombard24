FROM python:3.11-slim
WORKDIR /app
RUN pip install flask flask-sqlalchemy flask-login flask-wtf pymysql python-dotenv bcrypt
COPY . .
CMD ["python", "app.py"]
