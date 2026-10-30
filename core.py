import os
import time
import math
import hmac
import hashlib
import logging
from datetime import datetime
from extensions import db
from models import Student, Attendance, TeacherAttendance, AttendanceAnomaly, AppSetting
from flask import current_app

try:
    from gsheet_helper import append_to_gsheet
except Exception:
    def append_to_gsheet(*a, **k): pass

def get_secret_key():
    try:
        from flask import current_app
        if current_app and current_app.config.get('SECRET_KEY'):
            return current_app.config.get('SECRET_KEY')
    except Exception:
        pass
    try:
        from config import Config
        return Config.SECRET_KEY
    except Exception:
        return 'nexus-portal-secret-key-production'

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def generate_totp_token(uid, step=None, window=15):
    """
    Generate an encrypted, time-bound TOTP token for student pass.
    Format: NEXUS:<UID>:<STEP>:<SIGNATURE>
    Rotates every `window` seconds (default 15s).
    """
    if step is None:
        step = int(time.time()) // window
    secret = get_secret_key()
    message = f"{uid.upper()}:{step}"
    sig = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()[:12]
    return f"NEXUS:{uid.upper()}:{step}:{sig}"

def validate_totp_token(raw_code, window=15):
    """
    Validate a raw scanned string.
    Returns: (is_valid, uid, anomaly_type, anomaly_details)
    """
    raw = (raw_code or '').strip()
    if not raw.startswith("NEXUS:"):
        # Legacy/direct UID
        return True, raw, None, None

    parts = raw.split(":")
    if len(parts) != 4:
        return False, parts[1] if len(parts) > 1 else 'UNKNOWN', 'TAMPERED_QR', 'Malformed dynamic pass payload.'

    _, uid, token_step_str, sig = parts
    try:
        token_step = int(token_step_str)
    except ValueError:
        return False, uid, 'TAMPERED_QR', 'Invalid step value in dynamic token.'

    # Verify signature
    secret = get_secret_key()
    expected_sig = hmac.new(secret.encode('utf-8'), f"{uid}:{token_step}".encode('utf-8'), hashlib.sha256).hexdigest()[:12]
    if sig != expected_sig:
        return False, uid, 'TAMPERED_QR', 'Cryptographic signature mismatch! Pass may be forged.'

    current_step = int(time.time()) // window
    diff_steps = current_step - token_step

    # Allow current step and immediate previous step (0 to 30s grace) to absorb minor scanning/network delay
    if diff_steps < -1:
        return False, uid, 'TAMPERED_QR', 'Pass generated with future timestamp.'
    elif diff_steps > 1:
        seconds_late = diff_steps * window
        return False, uid, 'EXPIRED_QR', f'Pass expired by ~{seconds_late}s. Screenshot / forwarded pass proxy blocked.'

    return True, uid, None, None

def log_anomaly(uid, name, anomaly_type, severity, details, ip_address=''):
    """Record a security anomaly into attendance_anomalies."""
    try:
        student = Student.query.filter(Student.uid.ilike(uid)).first() if uid else None
        anomaly = AttendanceAnomaly(
            student_id=student.id if student else None,
            uid=uid or 'UNKNOWN',
            name=name or (student.name if student else 'Unknown Student'),
            anomaly_type=anomaly_type,
            severity=severity,
            details=details,
            ip_address=ip_address or '',
            created_at=datetime.now()
        )
        db.session.add(anomaly)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.warning(f"Failed to log security anomaly: {e}")

def mark_attendance(raw_input, client_ip=None, user_lat=None, user_lng=None, method='Scan'):
    """
    Mark student attendance with dynamic TOTP anti-proxy and geo-fence verification.
    Returns: (success: bool, message: str)
    """
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')

    # 1. Validate Dynamic TOTP pass
    is_valid_totp, uid, anomaly_type, anomaly_details = validate_totp_token(raw_input)
    if not is_valid_totp:
        student = Student.query.filter(Student.uid.ilike(uid)).first()
        student_name = student.name if student else 'Unknown'
        log_anomaly(uid, student_name, anomaly_type, 'danger', anomaly_details, client_ip)
        return False, f"⚠️ Security Alert: {anomaly_details}"

    student = Student.query.filter(Student.uid.ilike(uid)).first()
    if not student:
        return False, f"Student with UID '{uid}' not found in registry."

    # 2. Check if already marked today + Rapid repeat check
    existing = Attendance.query.filter_by(student_id=student.id, date=date_str).first()
    if existing:
        # Check if scanned very recently (within 3 mins)
        try:
            prev_time = datetime.strptime(f"{existing.date} {existing.time}", "%Y-%m-%d %H:%M:%S")
            diff_secs = (now - prev_time).total_seconds()
            if diff_secs < 180:
                log_anomaly(
                    student.uid,
                    student.name,
                    'RAPID_REPEAT',
                    'warning',
                    f"Rapid repeat scan detected ({int(diff_secs)}s after first check-in). Possible buddy/proxy scan.",
                    client_ip
                )
        except Exception:
            pass
        return False, f"ℹ️ {student.name} is already marked present for today."

    # 3. Campus Geo-Fencing Verification
    try:
        geo_setting = AppSetting.query.filter_by(key='geofence_enabled').first()
        if geo_setting and geo_setting.value == 'true':
            lat_set = AppSetting.query.filter_by(key='campus_lat').first()
            lng_set = AppSetting.query.filter_by(key='campus_lng').first()
            rad_set = AppSetting.query.filter_by(key='campus_radius').first()

            campus_lat = float(lat_set.value if lat_set and lat_set.value else '16.5062')
            campus_lng = float(lng_set.value if lng_set and lng_set.value else '80.6480')
            campus_rad = float(rad_set.value if rad_set and rad_set.value else '250')

            if user_lat is not None and user_lng is not None and str(user_lat).strip() != '' and str(user_lng).strip() != '':
                dist = haversine_distance(float(user_lat), float(user_lng), campus_lat, campus_lng)
                if dist > campus_rad:
                    details = f"Scan rejected: {dist:.1f}m away from campus (Max radius: {campus_rad:.0f}m)."
                    log_anomaly(student.uid, student.name, 'OUTSIDE_GEOFENCE', 'danger', details, client_ip)
                    return False, f"⚠️ Geo-Fence Breach: You are {dist:.0f}m away from campus perimeter (Allowed: {campus_rad:.0f}m)."
            else:
                details = "Scan rejected: Location coordinates were not provided while Campus Geo-Fencing is strictly active."
                log_anomaly(student.uid, student.name, 'MISSING_GPS', 'warning', details, client_ip)
                return False, "⚠️ Location Required: GPS coordinates are mandatory while Campus Geo-Fencing is active. Please enable device location."
    except Exception as e:
        logging.warning(f"Geo-fencing check error: {e}")

    # 4. Mark attendance
    rec = Attendance(student_id=student.id, date=date_str, time=time_str)
    db.session.add(rec)
    db.session.commit()

    try:
        append_to_gsheet(f"{date_str} {time_str}", student.uid, student.name)
    except Exception as e:
        logging.warning(f"Failed to append to gsheet: {e}")

    return True, f"✓ Marked {student.name} as present."

def mark_teacher_attendance(teacher_id):
    """Mark teacher self-attendance. Returns (success, message)."""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    if TeacherAttendance.query.filter_by(teacher_id=teacher_id, date=date_str).first():
        return False, "Already marked today."
    rec = TeacherAttendance(teacher_id=teacher_id, date=date_str, time=time_str)
    db.session.add(rec)
    db.session.commit()
    return True, "✓ Your attendance marked successfully."
