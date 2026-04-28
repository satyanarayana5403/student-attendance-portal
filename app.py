import os
import csv
import threading
import time as time_mod
from datetime import datetime, timedelta
from collections import defaultdict
from io import BytesIO
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helpers (lazy — these might not be configured on all systems)
try:
    from email_helper import send_email
except Exception:
    def send_email(*a, **k): pass

try:
    from gsheet_helper import append_to_gsheet
except Exception:
    def append_to_gsheet(*a, **k): pass

# ============================================================
# FLASK APP CONFIGURATION
# ============================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'nexus-fallback-key-change-me')
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire (better UX)

# Database configuration — reads from .env, defaults to SQLite
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
if DB_URL.startswith('postgresql://'):
    DB_URL = DB_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

# Test MySQL connectivity — fall back to SQLite if unreachable
if 'mysql' in DB_URL:
    try:
        import pymysql
        from urllib.parse import urlparse, unquote
        parsed = urlparse(DB_URL.replace('mysql+pymysql://', 'http://'))
        host = parsed.hostname or 'localhost'
        port = parsed.port or 3306
        user = parsed.username or 'root'
        password = unquote(parsed.password or '')
        db_name = (parsed.path or '').lstrip('/')
        pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=db_name or None, connect_timeout=5
        ).close()
        print(f"[OK] MySQL connection verified ({user}@{host}:{port}/{db_name})")
    except Exception as e:
        print(f"[WARN] MySQL unreachable ({e}), falling back to SQLite")
        DB_URL = 'sqlite:///attendance.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = None

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================
# DATABASE MODELS
# ============================================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    uid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), default='')
    profile_pic = db.Column(db.String(255), default='default_student.png')

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), default='')
    email = db.Column(db.String(255), default='')
    profile_pic = db.Column(db.String(255), default='default_teacher.png')

    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    date = db.Column(db.String(10), nullable=False, index=True)
    time = db.Column(db.String(8), nullable=False)

    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_student_attendance_per_day'),)


class TeacherAttendance(db.Model):
    __tablename__ = 'teacher_attendance'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True)
    date = db.Column(db.String(10), nullable=False, index=True)
    time = db.Column(db.String(8), nullable=False)

    __table_args__ = (db.UniqueConstraint('teacher_id', 'date', name='unique_teacher_attendance_per_day'),)


class AppSetting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')       # open, in_progress, resolved
    admin_reply = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = db.relationship('User', backref='tickets')


# ============================================================
# AUTH HELPERS
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'teacher']:
            flash("Teacher or Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_settings():
    """Return settings as a dict with safe defaults"""
    settings = {s.key: s.value for s in AppSetting.query.all()}
    settings.setdefault('realtime', 'true')
    settings.setdefault('email', 'true')
    settings.setdefault('qr', 'true')
    return settings


# ============================================================
# INITIALIZATION (runs once at startup, NOT per-request)
# ============================================================

def init_db():
    """Create tables and seed default data"""
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("[OK] Default admin created (admin/admin123)")

    # Default settings
    defaults = {'realtime': 'true', 'email': 'true', 'qr': 'true'}
    for key, val in defaults.items():
        if not AppSetting.query.filter_by(key=key).first():
            db.session.add(AppSetting(key=key, value=val))
    db.session.commit()


def migrate_baseline_data():
    """Migrate students.csv to the new User/Student model structure (one-time)"""
    if not os.path.exists('students.csv'):
        return
    try:
        with open('students.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row.get('UID', '').strip()
                if not uid or Student.query.filter_by(uid=uid).first():
                    continue
                username = uid.lower().replace(" ", "")
                user = User.query.filter_by(username=username).first()
                if not user:
                    user = User(username=username, role='student')
                    user.set_password('123456')
                    db.session.add(user)
                    db.session.flush()

                student = Student(
                    user_id=user.id,
                    uid=uid,
                    name=row.get('Name', 'Unknown'),
                    email=row.get('ParentEmail', '')
                )
                db.session.add(student)
        db.session.commit()
        print("[OK] CSV data migrated successfully")
    except Exception as e:
        db.session.rollback()
        print(f"[WARN] Migration skipped: {e}")


# Run initialization once when the app starts
with app.app_context():
    init_db()
    migrate_baseline_data()


# ============================================================
# CORE BUSINESS LOGIC
# ============================================================

def mark_attendance(uid):
    """Mark a student present by UID. Returns (success, message)."""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    student = Student.query.filter_by(uid=uid).first()
    if not student:
        return False, f"Student with UID '{uid}' not found."
    if Attendance.query.filter_by(student_id=student.id, date=date_str).first():
        return False, f"{student.name} already marked today."

    rec = Attendance(student_id=student.id, date=date_str, time=time_str)
    db.session.add(rec)
    db.session.commit()
    try:
        append_to_gsheet(f"{date_str} {time_str}", uid, student.name)
    except Exception:
        pass
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


# ============================================================
# ROUTES — AUTH
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username', '').strip()).first()
        if u and u.check_password(request.form.get('password', '')):
            remember = request.form.get('remember', False)
            login_user(u, remember=bool(remember))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(request.referrer or url_for('index'))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(request.referrer or url_for('index'))

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "danger")
        return redirect(request.referrer or url_for('index'))

    current_user.set_password(new_pw)
    db.session.commit()
    flash("✓ Password changed successfully!", "success")
    return redirect(request.referrer or url_for('index'))


@app.route('/')
@login_required
def index():
    """Route users to their role-specific dashboard"""
    if current_user.role == 'admin':
        return redirect(url_for('management_page'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


# ============================================================
# ROUTES — ADMIN
# ============================================================

@app.route('/management')
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
        config_db=DB_URL,
        chart_labels=chart_labels,
        chart_present=chart_present,
        chart_absent=chart_absent,
    )


@app.route('/register_user', methods=['POST'])
@admin_required
def register_user():
    role = request.form.get('role', 'student')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    name = request.form.get('name', '').strip()

    if not username or not password or not name:
        flash("All required fields must be filled.", "danger")
        return redirect(url_for('management_page'))

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists.", "danger")
        return redirect(url_for('management_page'))

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role == 'teacher':
        t = Teacher(
            user_id=user.id,
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
            return redirect(url_for('management_page'))
        if Student.query.filter_by(uid=uid).first():
            flash(f"UID '{uid}' already exists.", "danger")
            db.session.rollback()
            return redirect(url_for('management_page'))
        s = Student(
            user_id=user.id,
            uid=uid,
            name=name,
            email=request.form.get('email', '')
        )
        db.session.add(s)

    db.session.commit()
    flash(f"✓ {role.capitalize()} '{name}' registered successfully!", "success")
    return redirect(url_for('management_page'))


@app.route('/edit_user/<int:user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit an existing user's profile details"""
    user = User.query.get_or_404(user_id)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()

    if not name:
        flash("Name is required.", "danger")
        return redirect(url_for('management_page'))

    if user.role == 'student' and user.student_profile:
        user.student_profile.name = name
        user.student_profile.email = email
    elif user.role == 'teacher' and user.teacher_profile:
        user.teacher_profile.name = name
        user.teacher_profile.email = email
        user.teacher_profile.department = request.form.get('dept', '').strip()

    # Update password if provided
    new_password = request.form.get('password', '').strip()
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)

    db.session.commit()
    flash(f"✓ User '{name}' updated successfully!", "success")
    return redirect(url_for('management_page'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Cannot delete admin accounts.", "danger")
        return redirect(url_for('management_page'))

    if user.student_profile:
        db.session.delete(user.student_profile)
    if user.teacher_profile:
        db.session.delete(user.teacher_profile)
    db.session.delete(user)
    db.session.commit()
    flash("✓ User deleted.", "success")
    return redirect(url_for('management_page'))


@app.route('/admin/mark_attendance', methods=['POST'])
@admin_required
def admin_mark_attendance():
    uid = request.form.get('uid', '').strip()
    if not uid:
        flash("UID is required.", "danger")
        return redirect(url_for('management_page'))
    success, msg = mark_attendance(uid)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('management_page'))


# ============================================================
# ROUTES — TEACHER
# ============================================================

@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    teacher_prof = current_user.teacher_profile
    if not teacher_prof:
        flash("Teacher profile not found.", "danger")
        return redirect(url_for('login'))

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


@app.route('/teacher/mark_self', methods=['POST'])
@teacher_required
def teacher_mark_self():
    success, msg = mark_teacher_attendance(current_user.teacher_profile.id)
    flash(msg, "success" if success else "warning")
    return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/mark_student', methods=['POST'])
@teacher_required
def teacher_mark_student():
    uid = request.form.get('uid', '').strip()
    if not uid:
        flash("Student UID is required.", "danger")
        return redirect(url_for('teacher_dashboard'))
    success, msg = mark_attendance(uid)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('teacher_dashboard'))


# ============================================================
# ROUTES — STUDENT
# ============================================================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))

    prof = current_user.student_profile
    if not prof:
        flash("Student profile not found.", "danger")
        return redirect(url_for('login'))

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


# ============================================================
# ROUTES — API & UTILITIES
# ============================================================

@app.route('/api/settings', methods=['GET', 'POST'])
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


@app.route('/api/stats')
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


# Keep /get_stats as alias for backward compat
@app.route('/get_stats')
@login_required
def get_stats():
    """Alias for /api/stats — backward compatibility"""
    return api_stats()


@app.route('/api/attendance/trend')
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


@app.route('/api/students/search')
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


@app.route('/mark_attendance_api', methods=['POST'])
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


@app.route('/upload_profile', methods=['POST'])
@login_required
def upload_profile():
    if 'file' not in request.files:
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for('index'))

    # Validate file type
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        flash("Only image files (PNG, JPG, GIF, WebP) are allowed.", "danger")
        return redirect(request.referrer or url_for('index'))

    filename = secure_filename(f"{current_user.id}_{int(datetime.now().timestamp())}.{ext}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    if current_user.role == 'student' and current_user.student_profile:
        current_user.student_profile.profile_pic = filename
    elif current_user.role == 'teacher' and current_user.teacher_profile:
        current_user.teacher_profile.profile_pic = filename
    db.session.commit()
    flash("✓ Profile photo updated!", "success")
    return redirect(request.referrer or url_for('index'))


@app.route('/export/<export_type>')
@admin_required
def export_data(export_type):
    """Export attendance data as CSV or Excel"""
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

@app.route('/send_absent_notifications', methods=['POST'])
@admin_required
@csrf.exempt  # Called via AJAX
def send_absent_notifications():
    """Send email notifications to all absent students and teachers for today"""
    settings = get_settings()
    if settings.get('email') != 'true':
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
        return jsonify({
            'success': True,
            'message': 'Everyone is present today! No notifications needed.',
            'sent': 0, 'failed': 0, 'skipped': 0, 'total_absent': 0
        })

    # Send emails in background thread so the UI doesn't freeze
    results = {'sent': 0, 'failed': 0, 'skipped': 0, 'details': []}

    def send_notifications():
        with app.app_context():
            # Student absent notifications
            for student in absent_students:
                if not student['email'] or '@' not in student['email']:
                    results['skipped'] += 1
                    results['details'].append({'name': student['name'], 'status': 'skipped', 'reason': 'No email'})
                    continue
                subject = f"Absent Notification — {today}"
                body = (
                    f"Dear Parent/Guardian,\n\n"
                    f"This is to inform you that {student['name']} (UID: {student['uid']}) "
                    f"was marked absent on {today}.\n\n"
                    f"If this is an error, please contact the administration.\n\n"
                    f"Regards,\nNexus Attendance System"
                )
                try:
                    ok = send_email(student['email'], subject, body)
                    if ok:
                        results['sent'] += 1
                        results['details'].append({'name': student['name'], 'status': 'sent'})
                    else:
                        results['failed'] += 1
                        results['details'].append({'name': student['name'], 'status': 'failed'})
                except Exception as e:
                    print(f"EXCEPTION STUDENT: {e}")
                    results['failed'] += 1
                    results['details'].append({'name': student['name'], 'status': 'failed'})

            # Teacher absent notifications
            for teacher in absent_teachers:
                if not teacher['email'] or '@' not in teacher['email']:
                    results['skipped'] += 1
                    results['details'].append({'name': teacher['name'], 'status': 'skipped', 'reason': 'No email'})
                    continue
                subject = f"Absent Notification — {today}"
                body = (
                    f"Dear {teacher['name']},\n\n"
                    f"This is to inform you that your attendance was not recorded today ({today}).\n\n"
                    f"If this is an error, please contact the administration.\n\n"
                    f"Regards,\nNexus Attendance System"
                )
                try:
                    ok = send_email(teacher['email'], subject, body)
                    if ok:
                        results['sent'] += 1
                        results['details'].append({'name': teacher['name'], 'status': 'sent'})
                    else:
                        results['failed'] += 1
                        results['details'].append({'name': teacher['name'], 'status': 'failed'})
                except Exception as e:
                    print(f"EXCEPTION TEACHER: {e}")
                    results['failed'] += 1
                    results['details'].append({'name': teacher['name'], 'status': 'failed'})

    # Run synchronously for small counts, async for large
    if total_absent <= 5:
        send_notifications()
    else:
        thread = threading.Thread(target=send_notifications, daemon=True)
        thread.start()
        thread.join(timeout=30)  # Wait up to 30s

    return jsonify({
        'success': True,
        'message': f"Notifications processed: {results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped (no email)",
        'sent': results['sent'],
        'failed': results['failed'],
        'skipped': results['skipped'],
        'total_absent': total_absent,
        'details': results['details']
    })


@app.route('/api/absentees')
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


# ============================================================
# ROUTES — SUPPORT TICKETS
# ============================================================

@app.route('/support', methods=['GET'])
@login_required
def support_tickets():
    if current_user.role == 'admin':
        return redirect(url_for('management_page') + '#support')
    
    # Render support page (we will just return JSON and use JS modals in the dashboard instead)
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    return jsonify([
        {
            'id': t.id,
            'subject': t.subject,
            'message': t.message,
            'status': t.status,
            'admin_reply': t.admin_reply,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        } for t in tickets
    ])

@app.route('/support/new', methods=['POST'])
@login_required
def new_support_ticket():
    data = request.get_json()
    if not data or not data.get('subject') or not data.get('message'):
        return jsonify({'success': False, 'message': 'Subject and message are required'}), 400
        
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=data['subject'],
        message=data['message']
    )
    db.session.add(ticket)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Support ticket submitted successfully'})

@app.route('/api/admin/support', methods=['GET'])
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

@app.route('/api/admin/support/<int:ticket_id>/reply', methods=['POST'])
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


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 5000)))
