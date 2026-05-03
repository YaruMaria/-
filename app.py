import os
import sqlite3
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

# Список доступных предметов
SUBJECTS = [
    {'id': 'math', 'name': '📐 Математика', 'icon': '📐'},
    {'id': 'russian', 'name': '📖 Русский язык', 'icon': '📖'},
    {'id': 'english', 'name': '🇬🇧 Английский язык', 'icon': '🇬🇧'},
    {'id': 'solfeggio', 'name': '🎵 Сольфеджио', 'icon': '🎵'},
    {'id': 'music', 'name': '🎹 Музыка', 'icon': '🎹'},
    {'id': 'physics', 'name': '⚡ Физика', 'icon': '⚡'},
    {'id': 'history', 'name': '📜 История', 'icon': '📜'},
    {'id': 'biology', 'name': '🔬 Биология', 'icon': '🔬'},
    {'id': 'chemistry', 'name': '🧪 Химия', 'icon': '🧪'},
    {'id': 'literature', 'name': '📚 Литература', 'icon': '📚'},
]

# Список уровней
LEVELS = [
    {'id': 'beginner', 'name': '🌱 Начальный'},
    {'id': 'elementary', 'name': '📘 Элементарный'},
    {'id': 'pre_intermediate', 'name': '📙 Средний'},
    {'id': 'intermediate', 'name': '📕 Продвинутый'},
    {'id': 'advanced', 'name': '🏆 Профессиональный'},
]


# Модель пользователя
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    subject = db.Column(db.String(100), nullable=True)
    full_name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship('Student', backref='teacher', lazy=True)


# Модель ученика (упрощенная)
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    level = db.Column(db.String(100), nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.String(50), nullable=True)
    goal = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Функция для обновления существующей базы данных
def migrate_database():
    """Добавляет недостающие колонки в существующую базу данных"""
    db_path = os.path.join(os.path.dirname(__file__), 'school.db')

    if not os.path.exists(db_path):
        print("База данных не найдена, будет создана новая")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем таблицу students
        cursor.execute("PRAGMA table_info(students)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        # Удаляем ненужные колонки если они есть
        columns_to_remove = ['parent_name', 'parent_phone', 'additional_subjects']
        for col_name in columns_to_remove:
            if col_name in existing_columns:
                print(f"Колонка {col_name} будет проигнорирована")

        # Добавляем недостающие колонки в students если их нет
        student_columns = {
            'age': 'INTEGER',
            'notes': 'TEXT'
        }

        for col_name, col_type in student_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")
                    print(f"Добавлена колонка {col_name} в таблицу students")
                except Exception as e:
                    print(f"Ошибка при добавлении {col_name}: {e}")

        # Проверяем таблицу users
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        # Добавляем недостающие колонки в users
        user_columns = {
            'phone': 'TEXT',
            'email': 'TEXT',
            'full_name': 'TEXT'
        }

        for col_name, col_type in user_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"Добавлена колонка {col_name} в таблицу users")
                except Exception as e:
                    print(f"Ошибка при добавлении {col_name}: {e}")

        conn.commit()
        conn.close()
        print("Миграция базы данных завершена")
    except Exception as e:
        print(f"Ошибка при миграции: {e}")


# Создание/обновление базы данных
with app.app_context():
    migrate_database()
    db.create_all()
    print("База данных готова к работе")

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
        phone = request.form.get('phone')
        email = request.form.get('email')

        errors = []
        if len(username) < 3:
            errors.append('Логин должен содержать минимум 3 символа')
        if len(password) < 4:
            errors.append('Пароль должен содержать минимум 4 символа')
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        if not role:
            errors.append('Выберите роль')

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
                                   subject=subject,
                                   phone=phone,
                                   email=email,
                                   subjects=SUBJECTS)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Такой пользователь уже есть!', 'error')
            return render_template('register.html', username=username, full_name=full_name, subjects=SUBJECTS)

        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role,
            full_name=full_name,
            subject=subject,
            phone=phone,
            email=email
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'Регистрация успешна! Теперь войдите в свой аккаунт.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', subjects=SUBJECTS)


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher_dashboard.html',
                               user=current_user,
                               students=students,
                               subjects=SUBJECTS,
                               levels=LEVELS)
    else:
        return render_template('student_dashboard.html',
                               user=current_user,
                               durations=durations_data)


@app.route('/student/<int:student_id>')
@login_required
def view_student(student_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.get_or_404(student_id)
    if student.teacher_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    subject_name = student.subject
    for s in SUBJECTS:
        if s['id'] == student.subject:
            subject_name = s['name']
            break

    return render_template('student_detail.html',
                           student=student,
                           subjects=SUBJECTS,
                           levels=LEVELS,
                           subject_name=subject_name)


@app.route('/add_student', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'teacher':
        flash('Только учителя могут добавлять учеников', 'error')
        return redirect(url_for('dashboard'))

    name = request.form.get('name')
    age = request.form.get('age')
    level = request.form.get('level')
    subject = request.form.get('subject')
    start_date = request.form.get('start_date')
    goal = request.form.get('goal')
    notes = request.form.get('notes')

    if name:
        new_student = Student(
            name=name,
            age=int(age) if age else None,
            level=level,
            subject=subject,
            start_date=start_date,
            goal=goal,
            notes=notes,
            teacher_id=current_user.id
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f'Ученик {name} добавлен!', 'success')
    else:
        flash('Введите имя ученика', 'error')

    return redirect(url_for('dashboard'))


@app.route('/edit_student/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.get_or_404(student_id)
    if student.teacher_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student.name = request.form.get('name')
    student.age = int(request.form.get('age')) if request.form.get('age') else None
    student.level = request.form.get('level')
    student.subject = request.form.get('subject')
    student.start_date = request.form.get('start_date')
    student.goal = request.form.get('goal')
    student.notes = request.form.get('notes')

    db.session.commit()
    flash(f'Данные ученика {student.name} обновлены!', 'success')
    return redirect(url_for('view_student', student_id=student_id))


@app.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.get_or_404(student_id)
    if student.teacher_id == current_user.id:
        name = student.name
        db.session.delete(student)
        db.session.commit()
        flash(f'Ученик {name} удален', 'success')
    else:
        flash('Доступ запрещен', 'error')

    return redirect(url_for('dashboard'))


@app.route('/music_school')
@login_required
def music_school():
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