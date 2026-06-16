from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import AppSetting, Student, Teacher, Attendance, SupportTicket
from extensions import db, csrf
from utils import admin_required, get_settings
from core import mark_attendance

api_bp = Blueprint('api', __name__)

@api_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
@csrf.exempt
def api_settings():
    if request.method == 'POST':
        data = request.get_json()
        for key, val in data.items():
            s = AppSetting.query.filter_by(key=key).first()
            if s:
                s.value = str(val)
            else:
                db.session.add(AppSetting(key=key, value=str(val)))
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify(get_settings())

@api_bp.route('/stats')
@login_required
def api_stats():
    """Real-time stats API for dashboard auto-refresh"""
    today = datetime.now().strftime('%Y-%m-%d')
    total = Student.query.count()
    present = Attendance.query.filter_by(date=today).count()
    pct = round((present / max(total, 1)) * 100, 1)
    return jsonify({
        'present_today': present,
        'total_students': total,
        'total_teachers': Teacher.query.count(),
        'total': total,
        'present': present,
        'percentage': pct,
        'absent': total - present,
    })

# Keep /get_stats as alias for backward compat (in main app if needed)

@api_bp.route('/attendance/trend')
@login_required
def api_attendance_trend():
    """Attendance trend data for Chart.js — last N days"""
    days = min(int(request.args.get('days', 14)), 90)
    total_students = Student.query.count()
    labels = []
    present = []
    absent = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = Attendance.query.filter_by(date=d).count()
        labels.append(d)
        present.append(count)
        absent.append(max(0, total_students - count))
    return jsonify({'labels': labels, 'present': present, 'absent': absent, 'total': total_students})

@api_bp.route('/students/search')
@login_required
def api_students_search():
    """AJAX student search for admin panel"""
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])
    students = Student.query.filter(
        db.or_(
            Student.name.ilike(f'%{q}%'),
            Student.uid.ilike(f'%{q}%'),
            Student.email.ilike(f'%{q}%')
        )
    ).limit(20).all()
    return jsonify([{
        'id': s.id,
        'uid': s.uid,
        'name': s.name,
        'email': s.email
    } for s in students])

@api_bp.route('/mark_attendance', methods=['POST'])
@login_required
@csrf.exempt  # Exempt for QR scanner AJAX calls
def mark_attendance_api():
    """JSON API for QR scanner and AJAX manual entry"""
    data = request.get_json() or {}
    uid = data.get('uid', '').strip()
    if not uid:
        return jsonify({'success': False, 'message': 'UID required'}), 400
    success, msg = mark_attendance(uid)
    return jsonify({'success': success, 'message': msg})
@api_bp.route('/absentees')
@admin_required
def api_absentees():
    """Get today's absentee list for the notification panel"""
    today = datetime.now().strftime('%Y-%m-%d')

    # Absent students
    present_ids = {a.student_id for a in Attendance.query.filter_by(date=today).all()}
    absent_students = [
        {'name': s.name, 'uid': s.uid, 'email': s.email or '', 'type': 'Student'}
        for s in Student.query.all() if s.id not in present_ids
    ]

    # Absent teachers
    from models import TeacherAttendance
    present_teacher_ids = {a.teacher_id for a in TeacherAttendance.query.filter_by(date=today).all()}
    absent_teachers = [
        {'name': t.name, 'uid': '', 'email': t.email or '', 'type': 'Teacher'}
        for t in Teacher.query.all() if t.id not in present_teacher_ids
    ]

    return jsonify({
        'absent_students': absent_students,
        'absent_teachers': absent_teachers,
        'total': len(absent_students) + len(absent_teachers)
    })

@api_bp.route('/admin/support', methods=['GET'])
@admin_required
def all_support_tickets():
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return jsonify([
        {
            'id': t.id,
            'user': t.user.username,
            'role': t.user.role,
            'subject': t.subject,
            'message': t.message,
            'status': t.status,
            'admin_reply': t.admin_reply,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        } for t in tickets
    ])

@api_bp.route('/admin/support/<int:ticket_id>/reply', methods=['POST'])
@admin_required
def reply_support_ticket(ticket_id):
    ticket = db.session.get(SupportTicket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket not found'}), 404
        
    data = request.get_json()
    if 'status' in data:
        ticket.status = data['status']
    if 'admin_reply' in data:
        ticket.admin_reply = data['admin_reply']
        
    db.session.commit()
    return jsonify({'success': True, 'message': 'Ticket updated successfully'})
