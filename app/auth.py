from functools import wraps
from flask import session, redirect, url_for, abort
from app.models import User

class Roles:
    ADMIN = 'admin'
    USER = 'user'

def current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for('auth.login'))
        if user.role != Roles.ADMIN:
            abort(403)
        return view(*args, **kwargs)
    return wrapped
