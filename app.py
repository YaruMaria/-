import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345'
app.config['REMEMBER_COOKIE_DURATION'] = 0
app.config['SESSION_PERMANENT'] = False

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя для Базы Данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание базы данных перед запуском
with app.app_context():
    db.create_all()

# Данные для музыкальной игры
durations_data = [
    {'id': 'whole', 'name': 'Целая нота', 'value': 1.0},
    {'id': 'half', 'name': 'Половинная', 'value': 0.5},
    {'id': 'quarter', 'name': 'Четвертная', 'value': 0.25},
    {'id': 'eighth', 'name': 'Восьмая', 'value': 0.125}
]


@app.route('/')
def index():
    """Главная страница - перенаправляет на логин"""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Говорим Flask, что сессия НЕ постоянная
            session.permanent = False
            # login_user БЕЗ параметра remember=True
            login_user(user, remember=False)
            return redirect(url_for('music_school'))
        else:
            flash('Ошибка! Проверьте данные.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Проверка, нет ли уже такого пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Такой пользователь уже есть!')
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('Успешно! Теперь войдите.')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/music_school')
@login_required
def music_school():
    """Музыкальная школа - доступна только после логина"""
    return render_template('music_school.html', durations=durations_data)


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)