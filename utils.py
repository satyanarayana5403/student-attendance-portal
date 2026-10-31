import os
import time
from datetime import datetime
from functools import wraps
from collections import defaultdict
from flask import redirect, url_for, flash, request, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from models import AppSetting

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403
            flash("Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'teacher']:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Faculty or Admin access required.'}), 403
            flash("Teacher or Admin access required.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_settings():
    """Return settings as a dict with safe defaults"""
    settings = {s.key: s.value for s in AppSetting.query.all()}
    settings.setdefault('realtime', 'true')
    settings.setdefault('email', 'true')
    settings.setdefault('qr', 'true')
    settings.setdefault('geofence_enabled', 'false')
    settings.setdefault('campus_lat', '16.5062')
    settings.setdefault('campus_lng', '80.6480')
    settings.setdefault('campus_radius', '250')
    settings.setdefault('auto_absent_alerts_enabled', 'true')
    settings.setdefault('auto_absent_alert_time', '17:00')
    settings.setdefault('last_auto_alert_run', 'Never')
    settings.setdefault('last_auto_alert_stats', 'No alerts sent yet')
    return settings

def is_safe_redirect_url(target):
    """Prevent open redirect vulnerabilities to external malicious domains"""
    if not target or not isinstance(target, str):
        return False
    target = target.strip()
    return target.startswith('/') and not target.startswith('//') and '\\' not in target and '://' not in target

class SimpleRateLimiter:
    """In-memory sliding window rate limiter by client IP"""
    def __init__(self, max_requests=5, window_seconds=300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history = defaultdict(list)

    def is_limited(self, key):
        now = time.time()
        self.history[key] = [t for t in self.history[key] if now - t < self.window_seconds]
        return len(self.history[key]) >= self.max_requests

    def record(self, key):
        self.history[key].append(time.time())

    def reset(self, key):
        if key in self.history:
            del self.history[key]

# Global rate limiters
login_rate_limiter = SimpleRateLimiter(max_requests=5, window_seconds=300) # 5 failed logins per 5m
hint_rate_limiter = SimpleRateLimiter(max_requests=25, window_seconds=60)   # 25 hints per 1m

def save_secure_image(file, user_id, upload_folder, max_dimension=1024):
    """
    Validates, sanitizes, and securely saves an uploaded image.
    Strips EXIF data and re-encodes through PIL to prevent polyglot / webshell attacks.
    Returns: filename on success, None on invalid or dangerous file.
    """
    if not file or not file.filename:
        return None

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    raw_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if raw_ext not in ALLOWED_EXTENSIONS:
        return None

    safe_ext = 'jpg' if raw_ext in ('jpg', 'jpeg') else raw_ext
    filename = secure_filename(f"{user_id}_{int(datetime.now().timestamp())}.{safe_ext}")
    dest_path = os.path.join(upload_folder, filename)

    try:
        from PIL import Image, ImageOps
        # Step 1: Verify header format
        img = Image.open(file)
        img.verify()

        # Step 2: Re-open for actual processing (verify closes descriptor)
        file.seek(0)
        img = Image.open(file)
        img = ImageOps.exif_transpose(img)

        # Step 3: Resize if oversized to prevent decompression bombs
        if max(img.width, img.height) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        if safe_ext == 'jpg' and img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        img.save(dest_path, quality=90, optimize=True)
        return filename
    except Exception:
        # Strictly reject and DO NOT fallback to raw file saving
        return None
