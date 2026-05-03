import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345'  # Секретный ключ для сессий

# Настройка менеджера авторизации
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Куда перенаправлять неавторизованных
login_manager.login_message = "Пожалуйста, войдите, чтобы увидеть эту страницу."

# Временная база данных в памяти (Имя: {пароль, id})
# В реальном проекте здесь должна быть база данных (SQLite/PostgreSQL)
users_db = {
    "admin": {"password": generate_password_hash("1234"), "id": "1"}
}


# Класс пользователя для Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    for username, data in users_db.items():
        if data['id'] == user_id:
            return User(user_id, username)
    return None


# ГЛАВНАЯ СТРАНИЦА (теперь закрыта декоратором)
@app.route('/')
@login_required
def index():
    return render_template('index.html', name=current_user.username)


# СТРАНИЦА ВХОДА
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_data = users_db.get(username)
        if user_data and check_password_hash(user_data['password'], password):
            user_obj = User(user_data['id'], username)
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')

    return render_template('login.html')


# РЕГИСТРАЦИЯ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users_db:
            flash('Пользователь уже существует')
        else:
            # Добавляем в нашу "базу"
            new_id = str(len(users_db) + 1)
            users_db[username] = {
                "password": generate_password_hash(password),
                "id": new_id
            }
            flash('Регистрация успешна! Теперь войдите.')
            return redirect(url_for('login'))

    return render_template('register.html')


# ВЫХОД
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
