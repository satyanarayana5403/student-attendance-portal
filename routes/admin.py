from datetime import datetime, timedelta
from collections import defaultdict
import threading
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from models import Student, Teacher, Attendance, User, TeacherAttendance
from extensions import db
from utils import admin_required, get_settings
from core import mark_attendance
from io import BytesIO

from email_helper import send_email
import uuid

admin_bp = Blueprint('admin', __name__)

# Global dictionary for tracking email progress
email_tasks = {}

@admin_bp.route('/management')
@admin_required
def management_page():
    students = Student.query.all()
    teachers = Teacher.query.all()
    settings = get_settings()

    # Attendance stats
    today = datetime.now().strftime('%Y-%m-%d')
    present_today = Attendance.query.filter_by(date=today).count()
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    absent_today = total_students - present_today

    # Session history: dates → attendance count
    all_attendance = Attendance.query.all()
    sessions = defaultdict(int)
    for a in all_attendance:
        sessions[a.date] += 1

    # Chart data: last 14 days attendance trend
    chart_labels = []
    chart_present = []
    chart_absent = []
    for i in range(13, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = Attendance.query.filter_by(date=d).count()
        chart_labels.append(d)
        chart_present.append(count)
        chart_absent.append(max(0, total_students - count))

    return render_template('management.html',
        students=students,
        teachers=teachers,
        settings=settings,
        present_today=present_today,
        absent_today=absent_today,
        total_students=total_students,
        total_teachers=total_teachers,
        sessions=dict(sorted(sessions.items(), reverse=True)),
        today=today,
        config_db=current_app.config['SQLALCHEMY_DATABASE_URI'],
        chart_labels=chart_labels,
        chart_present=chart_present,
        chart_absent=chart_absent,
    )

@admin_bp.route('/register_user', methods=['POST'])
@admin_required
def register_user():
    role = request.form.get('role', 'student')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '').strip()

    if not username or not password or not name:
        flash("All required fields must be filled.", "danger")
        return redirect(url_for('admin.management_page'))

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists.", "danger")
        return redirect(url_for('admin.management_page'))

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role == 'teacher':
        t = Teacher(
            user_id=user.id,
            username=username,
            name=name,
            email=request.form.get('email', ''),
            department=request.form.get('dept', '')
        )
        db.session.add(t)
    elif role == 'student':
        uid = request.form.get('uid', '').strip()
        if not uid:
            flash("Student UID is required.", "danger")
            db.session.rollback()
            return redirect(url_for('admin.management_page'))
        if Student.query.filter_by(uid=uid).first():
            flash(f"UID '{uid}' already exists.", "danger")
            db.session.rollback()
            return redirect(url_for('admin.management_page'))
        s = Student(
            user_id=user.id,
            username=username,
            uid=uid,
            name=name,
            email=request.form.get('email', '')
        )
        db.session.add(s)

    db.session.commit()
    flash(f"✓ {role.capitalize()} '{name}' registered successfully!", "success")
    return redirect(url_for('admin.management_page'))


@admin_bp.route('/edit_user/<int:user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()

    if not name:
        flash("Name is required.", "danger")
        return redirect(url_for('admin.management_page'))

    if user.role == 'student' and user.student_profile:
        user.student_profile.name = name
        user.student_profile.email = email
    elif user.role == 'teacher' and user.teacher_profile:
        user.teacher_profile.name = name
        user.teacher_profile.email = email
        user.teacher_profile.department = request.form.get('dept', '').strip()

    new_password = request.form.get('password', '').strip()
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)

    db.session.commit()
    flash(f"✓ User '{name}' updated successfully!", "success")
    return redirect(url_for('admin.management_page'))


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Cannot delete admin accounts.", "danger")
        return redirect(url_for('admin.management_page'))

    if user.student_profile:
        db.session.delete(user.student_profile)
    if user.teacher_profile:
        db.session.delete(user.teacher_profile)
    db.session.delete(user)
    db.session.commit()
    flash("✓ User deleted.", "success")
    return redirect(url_for('admin.management_page'))


@admin_bp.route('/mark_attendance', methods=['POST'])
@admin_required
def admin_mark_attendance():
    uid = request.form.get('uid', '').strip()
    if not uid:
        flash("UID is required.", "danger")
        return redirect(url_for('admin.management_page'))
    success, msg = mark_attendance(uid)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('admin.management_page'))


@admin_bp.route('/export/<export_type>')
@admin_required
def export_data(export_type):
    if export_type == 'csv':
        output = BytesIO()
        records = db.session.query(Attendance, Student).join(Student).all()
        lines = "Date,Time,UID,Name\n"
        for att, stu in records:
            lines += f"{att.date},{att.time},{stu.uid},{stu.name}\n"
        output.write(lines.encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True,
                        download_name=f'attendance_{datetime.now().strftime("%Y%m%d")}.csv')

    elif export_type == 'excel':
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance"
        ws.append(["Date", "Time", "UID", "Name"])
        records = db.session.query(Attendance, Student).join(Student).all()
        for att, stu in records:
            ws.append([att.date, att.time, stu.uid, stu.name])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True,
                        download_name=f'attendance_{datetime.now().strftime("%Y%m%d")}.xlsx')

    return "Unknown export type", 400

from extensions import csrf
@admin_bp.route('/send_absent_notifications', methods=['GET', 'POST'])
@admin_required
@csrf.exempt
def send_absent_notifications():
    """Send email notifications to all absent students and teachers for today"""
    settings = get_settings()
    if settings.get('email') != 'true':
        if request.method == 'GET':
            flash("Email notifications are disabled in settings.", "danger")
            return redirect(url_for('admin.management_page'))
        return jsonify({'success': False, 'message': 'Email notifications are disabled in settings.'}), 403

    today = datetime.now().strftime('%Y-%m-%d')

    # Find absent students
    present_student_ids = {a.student_id for a in Attendance.query.filter_by(date=today).all()}
    all_students = Student.query.all()
    absent_students = [{'name': s.name, 'uid': s.uid, 'email': s.email} for s in all_students if s.id not in present_student_ids]

    # Find absent teachers
    present_teacher_ids = {a.teacher_id for a in TeacherAttendance.query.filter_by(date=today).all()}
    all_teachers = Teacher.query.all()
    absent_teachers = [{'name': t.name, 'email': t.email} for t in all_teachers if t.id not in present_teacher_ids]

    total_absent = len(absent_students) + len(absent_teachers)
    if total_absent == 0:
        if request.method == 'GET':
            flash("Everyone is present today! No notifications needed.", "info")
            return redirect(url_for('admin.management_page'))
        return jsonify({
            'success': True,
            'message': 'Everyone is present today! No notifications needed.',
            'done': True,
            'sent': 0, 'failed': 0, 'skipped': 0, 'total': 0
        })

    task_id = str(uuid.uuid4())
    email_tasks[task_id] = {
        'sent': 0, 'failed': 0, 'skipped': 0, 
        'total': total_absent, 'done': False, 'message': ''
    }

    app = current_app._get_current_object()

    def send_notifications(tid):
        with app.app_context():
            # Student absent notifications
            for student in absent_students:
                if not student['email'] or '@' not in student['email']:
                    email_tasks[tid]['skipped'] += 1
                    continue
                subject = f"Absent Notification — {today}"
                body = (f"Dear Parent/Guardian,\n\n"
                        f"This is to inform you that {student['name']} (UID: {student['uid']}) was marked absent on {today}.\n\n"
                        f"Regards,\nNexus Attendance System")
                try:
                    ok = send_email(student['email'], subject, body)
                    if ok: email_tasks[tid]['sent'] += 1
                    else: email_tasks[tid]['failed'] += 1
                except Exception:
                    email_tasks[tid]['failed'] += 1

            # Teacher absent notifications
            for teacher in absent_teachers:
                if not teacher['email'] or '@' not in teacher['email']:
                    email_tasks[tid]['skipped'] += 1
                    continue
                subject = f"Absent Notification — {today}"
                body = (f"Dear {teacher['name']},\n\n"
                        f"This is to inform you that your attendance was not recorded today ({today}).\n\n"
                        f"Regards,\nNexus Attendance System")
                try:
                    ok = send_email(teacher['email'], subject, body)
                    if ok: email_tasks[tid]['sent'] += 1
                    else: email_tasks[tid]['failed'] += 1
                except Exception:
                    email_tasks[tid]['failed'] += 1
            
            # Finished
            email_tasks[tid]['message'] = f"Notifications processed: {email_tasks[tid]['sent']} sent, {email_tasks[tid]['failed']} failed, {email_tasks[tid]['skipped']} skipped"
            email_tasks[tid]['done'] = True

    thread = threading.Thread(target=send_notifications, args=(task_id,), daemon=True)
    thread.start()

    if request.method == 'GET':
        flash("Email notifications are sending in the background.", "success")
        return redirect(url_for('admin.management_page'))

    return jsonify({
        'success': True,
        'task_id': task_id,
        'total': total_absent
    })

@admin_bp.route('/api/email_progress/<task_id>')
@admin_required
def email_progress(task_id):
    if task_id not in email_tasks:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(email_tasks[task_id])
