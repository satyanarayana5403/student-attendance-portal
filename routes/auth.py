from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db
from utils import is_safe_redirect_url, login_rate_limiter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # Brute force protection: rate limit repeated failed attempts
        if login_rate_limiter.is_limited(client_ip):
            flash("⚠️ Too many failed attempts. Account temporarily locked for 5 minutes.", "danger")
            return render_template('login.html'), 429

        raw_username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        u = User.query.filter_by(username=raw_username).first()
        if not u and raw_username:
            u = User.query.filter(User.username.ilike(raw_username)).first()

        if u and u.check_password(password):
            # Reset rate limiter on successful authentication
            login_rate_limiter.reset(client_ip)

            # Session Fixation defense
            session.clear()

            remember = request.form.get('remember', False)
            login_user(u, remember=bool(remember))

            # Validate open redirect
            next_page = request.args.get('next')
            if not is_safe_redirect_url(next_page):
                next_page = url_for('main.index')

            return redirect(next_page)

        # Record failed attempt
        login_rate_limiter.record(client_ip)
        flash("Invalid username or password.", "danger")

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
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
