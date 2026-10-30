import time
import io
import base64
import qrcode
from flask import jsonify, request
from core import generate_totp_token, haversine_distance
from models import AppSetting
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


@student_bp.route('/api/dynamic_pass', methods=['GET'])
@login_required
def api_dynamic_pass():
    if current_user.role != 'student' or not current_user.student_profile:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    prof = current_user.student_profile
    now_ts = int(time.time())
    window = 15
    current_step = now_ts // window
    seconds_remaining = window - (now_ts % window)

    # Generate TOTP token
    token = generate_totp_token(prof.uid, step=current_step, window=window)

    # Generate QR Code image as data URI
    try:
        qr = qrcode.QRCode(box_size=7, border=2)
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        qr_data_uri = f"data:image/png;base64,{qr_b64}"
    except Exception as e:
        qr_data_uri = ""

    # Geo-fence check if coordinates provided
    geofence_info = {'enabled': False}
    try:
        geo_setting = AppSetting.query.filter_by(key='geofence_enabled').first()
        if geo_setting and geo_setting.value == 'true':
            lat_set = AppSetting.query.filter_by(key='campus_lat').first()
            lng_set = AppSetting.query.filter_by(key='campus_lng').first()
            rad_set = AppSetting.query.filter_by(key='campus_radius').first()
            c_lat = float(lat_set.value if lat_set and lat_set.value else '16.5062')
            c_lng = float(lng_set.value if lng_set and lng_set.value else '80.6480')
            c_rad = float(rad_set.value if rad_set and rad_set.value else '250')

            geofence_info = {
                'enabled': True,
                'campus_lat': c_lat,
                'campus_lng': c_lng,
                'allowed_radius_m': c_rad
            }

            lat = request.args.get('lat')
            lng = request.args.get('lng')
            if lat and lng:
                dist = haversine_distance(float(lat), float(lng), c_lat, c_lng)
                geofence_info['distance_m'] = round(dist, 1)
                geofence_info['within_campus'] = (dist <= c_rad)
    except Exception:
        pass

    return jsonify({
        'success': True,
        'token': token,
        'qr_image': qr_data_uri,
        'seconds_remaining': seconds_remaining,
        'interval': window,
        'timestamp': now_ts,
        'student': {
            'name': prof.name,
            'uid': prof.uid,
            'email': prof.email or ''
        },
        'geofence': geofence_info
    })
