import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345'
app.config['REMEMBER_COOKIE_DURATION'] = 0
app.config['SESSION_PERMANENT'] = False

# Настройка загрузки файлов
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Список предметов
SUBJECTS = [
    {'id': 'math', 'name': '📐 Математика'},
    {'id': 'russian', 'name': '📖 Русский язык'},
    {'id': 'english', 'name': '🇬🇧 Английский язык'},
    {'id': 'solfeggio', 'name': '🎵 Сольфеджио'},
    {'id': 'music', 'name': '🎹 Музыка'},
    {'id': 'physics', 'name': '⚡ Физика'},
    {'id': 'history', 'name': '📜 История'},
    {'id': 'biology', 'name': '🔬 Биология'},
]

# Список уровней
LEVELS = [
    {'id': 'beginner', 'name': '🌱 Начальный'},
    {'id': 'elementary', 'name': '📘 Элементарный'},
    {'id': 'intermediate', 'name': '📙 Средний'},
    {'id': 'advanced', 'name': '🏆 Продвинутый'},
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
    games = db.relationship('Game', backref='creator', lazy=True)


# Модель ученика
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
    stars = db.Column(db.Integer, default=0)

    star_history = db.relationship('StarHistory', backref='student', lazy=True)


# Модель игры
class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    questions = db.relationship('GameQuestion', backref='game', lazy=True, cascade='all, delete-orphan')


# Модель вопроса для игры
class GameQuestion(db.Model):
    __tablename__ = 'game_questions'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    correct_text = db.Column(db.String(200), nullable=False)
    order_index = db.Column(db.Integer, default=0)


# Модель истории начисления звезд
class StarHistory(db.Model):
    __tablename__ = 'star_history'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    stars_earned = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    game = db.relationship('Game')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание базы данных
with app.app_context():
    db.create_all()
    print("База данных готова")

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

        errors = []
        if len(username) < 3:
            errors.append('Логин должен содержать минимум 3 символа')
        if len(password) < 4:
            errors.append('Пароль должен содержать минимум 4 символа')
        if password != confirm_password:
            errors.append('Пароли не совпадают')

        subject = None
        if role == 'teacher':
            subject = request.form.get('subject')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', subjects=SUBJECTS)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Такой пользователь уже есть!', 'error')
            return render_template('register.html', subjects=SUBJECTS)

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

        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', subjects=SUBJECTS)


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        students = Student.query.filter_by(teacher_id=current_user.id).all()
        games = Game.query.filter_by(creator_id=current_user.id).all()
        return render_template('teacher_dashboard.html',
                               user=current_user,
                               students=students,
                               games=games,
                               subjects=SUBJECTS,
                               levels=LEVELS)
    else:
        games = Game.query.filter_by(is_active=True).all()
        return render_template('student_dashboard.html',
                               user=current_user,
                               games=games,
                               durations=durations_data)


# ЗАГРУЗКА СВОЕЙ КАРТИНКИ
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    # Сохраняем файл
    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    image_url = f'/static/uploads/{filename}'
    return jsonify({'url': image_url})


# СОЗДАНИЕ ИГРЫ
@app.route('/create_game', methods=['POST'])
@login_required
def create_game():
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    game_name = request.form.get('game_name')
    questions_data = json.loads(request.form.get('questions', '[]'))

    if not game_name or not questions_data:
        flash('Заполните название игры и добавьте вопросы', 'error')
        return redirect(url_for('dashboard'))

    new_game = Game(
        name=game_name,
        creator_id=current_user.id
    )
    db.session.add(new_game)
    db.session.commit()

    for idx, q in enumerate(questions_data):
        question = GameQuestion(
            game_id=new_game.id,
            image_url=q['image_url'],
            correct_text=q['text'],
            order_index=idx
        )
        db.session.add(question)

    db.session.commit()
    flash(f'Игра "{game_name}" успешно создана!', 'success')
    return redirect(url_for('dashboard'))


# УДАЛЕНИЕ ИГРЫ
@app.route('/delete_game/<int:game_id>')
@login_required
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    if game.creator_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(game)
    db.session.commit()
    flash('Игра удалена', 'success')
    return redirect(url_for('dashboard'))


# ЗАПУСК ИГРЫ (для ученика)
@app.route('/play_game/<int:game_id>')
@login_required
def play_game(game_id):
    game = Game.query.get_or_404(game_id)

    # Перемешиваем вопросы для игры
    questions = list(game.questions)
    import random
    random.shuffle(questions)

    # Создаем перемешанные подписи
    texts = [q.correct_text for q in questions]
    random.shuffle(texts)

    return render_template('play_game.html',
                           game=game,
                           questions=questions,
                           shuffled_texts=texts)


# ПРОВЕРКА РЕЗУЛЬТАТА ИГРЫ
@app.route('/check_game_result', methods=['POST'])
@login_required
def check_game_result():
    data = request.json
    game_id = data.get('game_id')
    matches = data.get('matches', {})

    game = Game.query.get_or_404(game_id)
    questions = {str(q.id): q.correct_text for q in game.questions}

    correct_count = 0
    for q_id, matched_text in matches.items():
        if questions.get(q_id) == matched_text:
            correct_count += 1

    total = len(questions)
    score_percent = (correct_count / total) * 100 if total > 0 else 0

    # Сохраняем результат в сессию
    session['game_result'] = {
        'game_id': game_id,
        'game_name': game.name,
        'correct': correct_count,
        'total': total,
        'score': score_percent
    }

    return jsonify({
        'correct': correct_count,
        'total': total,
        'score': score_percent,
        'passed': score_percent >= 70
    })


# ПОЛУЧИТЬ РЕЗУЛЬТАТ ИГРЫ
@app.route('/get_game_result')
@login_required
def get_game_result():
    result = session.get('game_result')
    if not result:
        return jsonify({'error': 'Нет результата'}), 404
    return jsonify(result)


# НАЧИСЛИТЬ ЗВЕЗДУ УЧЕНИКУ
# НАЧИСЛИТЬ ЗВЕЗДУ УЧЕНИКУ
@app.route('/award_star', methods=['POST'])
@login_required
def award_star():
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    student_id = request.form.get('student_id')
    game_result = session.get('game_result')

    if not game_result:
        flash('Сначала нужно пройти игру', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.get_or_404(student_id)
    if student.teacher_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    # Начисляем звезду
    student.stars = (student.stars or 0) + 1

    # Сохраняем историю
    star_history = StarHistory(
        student_id=student.id,
        game_id=game_result['game_id'],
        stars_earned=1
    )
    db.session.add(star_history)
    db.session.commit()

    # Очищаем результат
    session.pop('game_result', None)

    flash(f'⭐ Звезда начислена ученику {student.name} за игру "{game_result["game_name"]}"!', 'success')
    return redirect(url_for('dashboard'))


# СТРАНИЦА УЧЕНИКА
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

    star_history = StarHistory.query.filter_by(student_id=student.id) \
        .order_by(StarHistory.created_at.desc()).all()

    subject_name = student.subject
    for s in SUBJECTS:
        if s['id'] == student.subject:
            subject_name = s['name']
            break

    return render_template('student_detail.html',
                           student=student,
                           subjects=SUBJECTS,
                           levels=LEVELS,
                           subject_name=subject_name,
                           star_history=star_history)


# ДОБАВЛЕНИЕ УЧЕНИКА
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


# РЕДАКТИРОВАНИЕ УЧЕНИКА
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


# УДАЛЕНИЕ УЧЕНИКА
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


# МУЗЫКАЛЬНАЯ ШКОЛА
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


# СТРАНИЦА ВЫБОРА УЧЕНИКА ДЛЯ НАЧИСЛЕНИЯ ЗВЕЗДЫ
@app.route('/select_student_for_star')
@login_required
def select_student_for_star():
    if current_user.role != 'teacher':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))

    game_result = session.get('game_result')
    if not game_result:
        flash('Сначала нужно пройти игру', 'error')
        return redirect(url_for('dashboard'))

    students = Student.query.filter_by(teacher_id=current_user.id).all()

    return render_template('select_student.html',
                           students=students,
                           game_result=game_result)

if __name__ == '__main__':
    app.run(debug=True)