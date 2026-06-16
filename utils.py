from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from models import AppSetting

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'teacher']:
            flash("Teacher or Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_settings():
    """Return settings as a dict with safe defaults"""
    settings = {s.key: s.value for s in AppSetting.query.all()}
    settings.setdefault('realtime', 'true')
    settings.setdefault('email', 'true')
    settings.setdefault('qr', 'true')
    return settings
