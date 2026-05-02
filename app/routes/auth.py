from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.get('/login')
def login():
    return render_template('login.html')


@auth_bp.post('/login')
def login_post():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return 'Неверное имя пользователя или пароль.', 401

    session['user_id'] = user.id
    return redirect(url_for('web.index'))


@auth_bp.get('/register')
def register():
    return render_template('register.html')


@auth_bp.post('/register')
def register_post():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    full_name = request.form.get('full_name', '').strip()

    if not username or not password or not full_name:
        return 'Все поля обязательны для заполнения.', 400

    if len(username) < 3:
        return 'Логин должен быть не менее 3 символов.', 400

    if len(password) < 6:
        return 'Пароль должен быть не менее 6 символов.', 400

    if User.query.filter_by(username=username).first():
        return 'Пользователь с таким логином уже существует.', 400

    user = User(username=username, full_name=full_name, role='user')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    return redirect(url_for('web.index'))


@auth_bp.get('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
