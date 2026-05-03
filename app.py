from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
# Файл базы данных будет создан в папке проекта под именем database.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- МОДЕЛИ БАЗЫ ДАННЫХ ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Связь с записями: один пользователь может иметь много записей
    records = db.relationship('Record', backref='owner', lazy=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- МАРШРУТЫ (ROUTES) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Хешируем пароль для безопасности
        hashed_pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(username=request.form['username'], password=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Аккаунт создан! Теперь вы можете войти.')
            return redirect(url_for('login'))
        except:
            flash('Такой пользователь уже существует.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Ошибка входа. Проверьте логин и пароль.')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Показываем только те записи, которые принадлежат вошедшему пользователю
    user_records = Record.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', records=user_records)

# ЭТОТ БЛОК МЫ ДОБАВИЛИ: Сохранение данных в базу
@app.route('/add_record', methods=['POST'])
@login_required
def add_record():
    content = request.form.get('content')
    if content:
        # Создаем запись и привязываем её к ID текущего пользователя
        new_record = Record(content=content, user_id=current_user.id)
        db.session.add(new_record)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Создает таблицы, если их еще нет
    app.run(debug=True)
