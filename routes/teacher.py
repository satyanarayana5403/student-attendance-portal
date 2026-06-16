from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models import Student, Attendance, TeacherAttendance
from extensions import db
from utils import teacher_required, get_settings
from core import mark_attendance, mark_teacher_attendance

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
@teacher_required
def teacher_dashboard():
    teacher_prof = current_user.teacher_profile
    if not teacher_prof:
        flash("Teacher profile not found.", "danger")
        return redirect(url_for('auth.login'))

    today = datetime.now().strftime('%Y-%m-%d')
    present_today = Attendance.query.filter_by(date=today).count()
    total_students = Student.query.count()
    teacher_marked = TeacherAttendance.query.filter_by(
        teacher_id=teacher_prof.id, date=today
    ).first() is not None

    # Recent attendance log
    recent_attendance = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.date == today
    ).order_by(Attendance.time.desc()).all()

    # Weekly trend for mini chart
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = Attendance.query.filter_by(date=d).count()
        chart_labels.append(d[-5:])  # MM-DD format
        chart_data.append(count)

    return render_template('teacher_dashboard.html',
        prof=teacher_prof,
        present=present_today,
        total_students=total_students,
        marked=teacher_marked,
        recent=recent_attendance,
        today=today,
        chart_labels=chart_labels,
        chart_data=chart_data,
        settings=get_settings()
    )

@teacher_bp.route('/mark_self', methods=['POST'])
@teacher_required
def teacher_mark_self():
    success, msg = mark_teacher_attendance(current_user.teacher_profile.id)
    flash(msg, "success" if success else "warning")
    return redirect(url_for('teacher.teacher_dashboard'))


@teacher_bp.route('/mark_student', methods=['POST'])
@teacher_required
def teacher_mark_student():
    uid = request.form.get('uid', '').strip()
    if not uid:
        flash("Student UID is required.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))
    success, msg = mark_attendance(uid)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('teacher.teacher_dashboard'))
