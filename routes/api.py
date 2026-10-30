from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from flask_login import login_required

from models import User, AppSetting, Student, Teacher, Attendance, TeacherAttendance, SupportTicket, AttendanceAnomaly

from extensions import db, csrf

from utils import admin_required, get_settings, hint_rate_limiter

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

    if current_user.role not in ['admin', 'teacher']:
        return jsonify([]), 403

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

    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Forbidden: Only faculty and administrators can mark attendance.'}), 403

    data = request.get_json() or {}

    uid = data.get('uid', '').strip()

    if not uid:

        return jsonify({'success': False, 'message': 'UID required'}), 400

    lat = data.get('lat')

    lng = data.get('lng')

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    success, msg = mark_attendance(uid, client_ip=client_ip, user_lat=lat, user_lng=lng)

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

@api_bp.route('/check_user_hint', methods=['GET'])

def check_user_hint():

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    # Rate limit automated enumeration attempts
    if hint_rate_limiter.is_limited(client_ip):
        return jsonify({'found': False, 'message': 'Rate limit exceeded'}), 429
    hint_rate_limiter.record(client_ip)

    username = request.args.get('username', '').strip().lower()

    if not username:

        return jsonify({'found': False})

    u = User.query.filter(db.func.lower(User.username) == username).first()

    if not u:

        return jsonify({'found': False})

    # Check baseline credentials

    suggested = None

    if u.check_password('admin123'):

        suggested = 'admin123'

    elif u.check_password('123456'):

        suggested = '123456'

    elif u.check_password('teacher123'):

        suggested = 'teacher123'

    elif u.check_password('password'):

        suggested = 'password'

    return jsonify({

        'found': True,

        'role': u.role,

        'suggested_password': suggested

    })

@api_bp.route('/session_attendees', methods=['GET'])

@admin_required

def api_session_attendees():

    """Retrieve full list of attendees (students and teachers) present on a given session date."""

    date_str = request.args.get('date', '').strip()

    if not date_str:

        return jsonify({'success': False, 'message': 'Date parameter is required'}), 400

    student_records = Attendance.query.filter_by(date=date_str).order_by(Attendance.time.asc()).all()

    teacher_records = TeacherAttendance.query.filter_by(date=date_str).order_by(TeacherAttendance.time.asc()).all()

    attendees = []

    for a in student_records:

        s = a.student

        if s:

            attendees.append({

                'type': 'Student',

                'name': s.name,

                'uid': s.uid,

                'email': s.email or '—',

                'department': '—',

                'time': a.time,

                'profile_pic': s.profile_pic or 'default_student.png'

            })

    for ta in teacher_records:

        t = ta.teacher

        if t:

            attendees.append({

                'type': 'Teacher',

                'name': t.name,

                'uid': t.username or '—',

                'email': t.email or '—',

                'department': t.department or '—',

                'time': ta.time,

                'profile_pic': t.profile_pic or 'default_teacher.png'

            })

    attendees.sort(key=lambda x: x.get('time', ''))

    return jsonify({

        'success': True,

        'date': date_str,

        'total_present': len(attendees),

        'attendees': attendees

    })

@api_bp.route('/anomalies', methods=['GET'])

@admin_required

def api_anomalies():

    """Retrieve recent anti-proxy security anomalies."""

    anomalies = AttendanceAnomaly.query.order_by(AttendanceAnomaly.created_at.desc()).limit(50).all()

    unresolved_count = AttendanceAnomaly.query.filter_by(resolved=False).count()

    return jsonify({

        'success': True,

        'unresolved_count': unresolved_count,

        'anomalies': [

            {

                'id': a.id,

                'uid': a.uid,

                'name': a.name or 'Unknown',

                'type': a.anomaly_type,

                'severity': a.severity,

                'details': a.details,

                'ip': a.ip_address,

                'time': a.created_at.strftime('%Y-%m-%d %H:%M:%S'),

                'resolved': a.resolved

            }

            for a in anomalies

        ]

    })

@api_bp.route('/anomalies/dismiss/<int:anomaly_id>', methods=['POST'])

@admin_required

@csrf.exempt
def api_dismiss_anomaly(anomaly_id):

    anomaly = db.session.get(AttendanceAnomaly, anomaly_id)

    if anomaly:

        anomaly.resolved = True

        db.session.commit()

        return jsonify({'success': True, 'message': 'Anomaly resolved'})

    return jsonify({'success': False, 'message': 'Not found'}), 404

@api_bp.route('/anomalies/clear_all', methods=['POST'])

@admin_required

@csrf.exempt
def api_clear_all_anomalies():

    AttendanceAnomaly.query.update({'resolved': True})

    db.session.commit()

    return jsonify({'success': True, 'message': 'All anomalies cleared'})

@api_bp.route('/geofence_status', methods=['GET'])

@admin_required

def api_geofence_status():

    geo_setting = AppSetting.query.filter_by(key='geofence_enabled').first()

    lat_set = AppSetting.query.filter_by(key='campus_lat').first()

    lng_set = AppSetting.query.filter_by(key='campus_lng').first()

    rad_set = AppSetting.query.filter_by(key='campus_radius').first()

    return jsonify({

        'enabled': (geo_setting.value == 'true') if geo_setting else False,

        'campus_lat': float(lat_set.value) if lat_set and lat_set.value else 16.5062,

        'campus_lng': float(lng_set.value) if lng_set and lng_set.value else 80.6480,

        'campus_radius': float(rad_set.value) if rad_set and rad_set.value else 250

    })

@api_bp.route('/save_geofence', methods=['POST'])

@admin_required

@csrf.exempt
def api_save_geofence():

    data = request.get_json() or {}

    enabled = str(data.get('enabled', 'false')).lower()

    lat = str(data.get('campus_lat', '16.5062')).strip()

    lng = str(data.get('campus_lng', '80.6480')).strip()

    rad = str(data.get('campus_radius', '250')).strip()

    for k, v in [('geofence_enabled', enabled), ('campus_lat', lat), ('campus_lng', lng), ('campus_radius', rad)]:

        s = AppSetting.query.filter_by(key=k).first()

        if not s:

            s = AppSetting(key=k, value=v)

            db.session.add(s)

        else:

            s.value = v

    db.session.commit()

    return jsonify({'success': True, 'message': 'Geo-fencing settings saved successfully!'})

