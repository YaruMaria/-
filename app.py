import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345'
app.config['REMEMBER_COOKIE_DURATION'] = 0
app.config['SESSION_PERMANENT'] = False

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')  # teacher, student
    subject = db.Column(db.String(100), nullable=True)  # для учителя: предмет
    full_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с учениками (для учителя)
    students = db.relationship('Student', backref='teacher', lazy=True)


# Модель ученика (для учителя)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    level = db.Column(db.String(100), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание базы данных
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
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.permanent = False
            login_user(user, remember=False)
            flash(f'Добро пожаловать, {user.full_name or user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ошибка! Проверьте данные.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        full_name = request.form.get('full_name')

        # Валидация
        errors = []
        if len(username) < 3:
            errors.append('Логин должен содержать минимум 3 символа')
        if len(password) < 4:
            errors.append('Пароль должен содержать минимум 4 символа')
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        if not role:
            errors.append('Выберите роль')

        # Дополнительные поля в зависимости от роли
        subject = None
        if role == 'teacher':
            subject = request.form.get('subject')
            if not subject:
                errors.append('Укажите предмет, который вы преподаете')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html',
                                   username=username,
                                   full_name=full_name,
                                   role=role,
                                   subject=subject)

        # Проверка существующего пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Такой пользователь уже есть!', 'error')
            return render_template('register.html', username=username, full_name=full_name)

        # Создание нового пользователя
        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role,
            full_name=full_name,
            subject=subject
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'Регистрация успешна! Теперь войдите в свой аккаунт.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет пользователя"""
    if current_user.role == 'teacher':
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher_dashboard.html',
                               user=current_user,
                               students=students,
                               durations=durations_data)
    else:
        # Ученик
        return render_template('student_dashboard.html',
                               user=current_user,
                               durations=durations_data)


@app.route('/add_student', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'teacher':
        flash('Только учителя могут добавлять учеников', 'error')
        return redirect(url_for('dashboard'))

    student_name = request.form.get('student_name')
    student_level = request.form.get('student_level')

    if student_name:
        new_student = Student(
            name=student_name,
            level=student_level,
            teacher_id=current_user.id
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Ученик {student_name} добавлен!', 'success')
    else:
        flash('Введите имя ученика', 'error')

    return redirect(url_for('dashboard'))


@app.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.get_or_404(student_id)
    if student.teacher_id == current_user.id:
        db.session.delete(student)
        db.session.commit()
        flash(f'Ученик {student.name} удален', 'success')
    else:
        flash('Доступ запрещен', 'error')

    return redirect(url_for('dashboard'))


@app.route('/music_school')
@login_required
def music_school():
    """Музыкальная школа - доступна всем авторизованным"""
    return render_template('music_school.html',
                           durations=durations_data,
                           user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)