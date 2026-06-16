import os
from datetime import datetime
from flask import Blueprint, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask import current_app
from extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Route users to their role-specific dashboard"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.management_page'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher.teacher_dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student.student_dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/upload_profile', methods=['POST'])
@login_required
def upload_profile():
    if 'file' not in request.files:
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    # Validate file type
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        flash("Only image files (PNG, JPG, GIF, WebP) are allowed.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    filename = secure_filename(f"{current_user.id}_{int(datetime.now().timestamp())}.{ext}")
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    if current_user.role == 'student' and current_user.student_profile:
        current_user.student_profile.profile_pic = filename
    elif current_user.role == 'teacher' and current_user.teacher_profile:
        current_user.teacher_profile.profile_pic = filename
    db.session.commit()
    flash("✓ Profile photo updated!", "success")
    return redirect(request.referrer or url_for('main.index'))
