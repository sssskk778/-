from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.get('/login')
def login():
    return render_template('login.html')

@auth_bp.post('/login')
def login_post():
    user = User.query.filter_by(username=request.form.get('username','')).first()
    if not user or not user.check_password(request.form.get('password','')):
        flash('Неверное имя пользователя или пароль.')
        return redirect(url_for('auth.login'))
    session['user_id'] = user.id
    return redirect(url_for('web.index'))

@auth_bp.get('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
