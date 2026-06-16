from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username', '').strip()).first()
        if u and u.check_password(request.form.get('password', '')):
            remember = request.form.get('remember', False)
            login_user(u, remember=bool(remember))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    current_user.set_password(new_pw)
    db.session.commit()
    flash("✓ Password changed successfully!", "success")
    return redirect(request.referrer or url_for('main.index'))
