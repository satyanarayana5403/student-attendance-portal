from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Attendance
from extensions import db

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('main.index'))

    prof = current_user.student_profile
    if not prof:
        flash("Student profile not found.", "danger")
        return redirect(url_for('auth.login'))

    records = Attendance.query.filter_by(student_id=prof.id).order_by(Attendance.date.desc()).all()

    # Analytics: calculate attendance percentage
    total_sessions = db.session.query(db.func.count(db.distinct(Attendance.date))).scalar() or 0
    total_sessions = max(total_sessions, 1)  # Avoid division by zero
    presence = len(records)
    percentage = round((presence / total_sessions) * 100, 1)

    # Calculate absent days
    all_dates = set(r[0] for r in db.session.query(db.distinct(Attendance.date)).all())
    present_dates = set(r.date for r in records)
    absent_dates = sorted(all_dates - present_dates, reverse=True)

    # Calendar data: current month present/absent days for calendar widget
    now = datetime.now()
    month_start = now.replace(day=1).strftime('%Y-%m-%d')
    next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')

    month_present = set()
    for r in records:
        if month_start <= r.date <= month_end:
            month_present.add(r.date)

    month_absent = set()
    for d in all_dates:
        if month_start <= d <= month_end and d not in month_present:
            month_absent.add(d)

    return render_template('student_dashboard.html',
        prof=prof,
        records=records,
        percentage=percentage,
        total_sessions=total_sessions,
        present_count=presence,
        absent_dates=absent_dates,
        month_present=list(month_present),
        month_absent=list(month_absent),
        current_month=now.strftime('%Y-%m'),
    )
