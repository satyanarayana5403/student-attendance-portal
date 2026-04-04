from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from collections import defaultdict
from email_helper import send_email
from gsheet_helper import append_to_gsheet
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import qrcode
import csv
import os
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'abc123-dev-only')

# Environment variables
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

# Database configuration
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
# Render uses postgresql:// but SQLAlchemy needs postgresql+psycopg2://
if DB_URL.startswith('postgresql://'):
    DB_URL = DB_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = False

# Initialize database
db = SQLAlchemy(app)

# ============ DATABASE MODELS ============

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.uid}: {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    date = db.Column(db.String(10), nullable=False, index=True)
    time = db.Column(db.String(8), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Unique constraint: one attendance per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance_per_day'),)
    
    def __repr__(self):
        return f'<Attendance {self.date} {self.time}>'


# ============ DATABASE INITIALIZATION ============

def init_db():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")


def migrate_csv_to_db():
    """Migrate existing CSV data to SQLite database"""
    with app.app_context():
        # Migrate students.csv
        if os.path.exists('students.csv'):
            print("Migrating students.csv...")
            with open('students.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not Student.query.filter_by(uid=row['UID']).first():
                        student = Student(
                            uid=row['UID'],
                            name=row['Name'],
                            email=row.get('ParentEmail', '')
                        )
                        db.session.add(student)
            db.session.commit()
            print("✓ Students migrated")

        # Migrate attendance_log.csv
        if os.path.exists('attendance_log.csv'):
            print("Migrating attendance_log.csv...")
            with open('attendance_log.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student = Student.query.filter_by(uid=row['UID']).first()
                    if student:
                        existing = Attendance.query.filter_by(
                            student_id=student.id,
                            date=row['Date']
                        ).first()
                        if not existing:
                            attendance = Attendance(
                                student_id=student.id,
                                date=row['Date'],
                                time=row['Time']
                            )
                            db.session.add(attendance)
            db.session.commit()
            print("✓ Attendance records migrated")


# ============ DATABASE HELPER FUNCTIONS ============

def get_present_uids(date):
    """Get set of student UIDs present on a given date"""
    records = Attendance.query.filter_by(date=date).all()
    return {record.student.uid for record in records}


def get_all_students():
    """Get all students as dictionary"""
    students = {}
    for student in Student.query.all():
        students[student.uid] = {
            'id': student.id,
            'name': student.name,
            'email': student.email
        }
    return students


def mark_attendance(uid):
    """Mark attendance for a student"""
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')

    # Find student by UID
    student = Student.query.filter_by(uid=uid).first()
    if not student:
        return False, "UID not found."

    # Check if already marked today
    existing = Attendance.query.filter_by(
        student_id=student.id,
        date=date
    ).first()
    
    if existing:
        return False, "Attendance already marked for today."

    # Mark attendance
    attendance = Attendance(
        student_id=student.id,
        date=date,
        time=time
    )
    db.session.add(attendance)
    db.session.commit()

    # Send to Google Sheets
    append_to_gsheet(f"{date} {time}", uid, student.name)
    
    return True, f"Attendance marked for {student.name}."


# ============ ROUTES ============

# Home page (manual UID entry)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uid = request.form.get('uid', '').strip()
        if uid:
            success, message = mark_attendance(uid)
            flash(message, 'success' if success else 'danger')
        else:
            flash("UID cannot be empty.", 'warning')
        return redirect(url_for('index'))

    # Live count logic
    today = datetime.now().strftime('%Y-%m-%d')
    total_students = Student.query.count()
    present = len(get_present_uids(today))

    return render_template('index.html', total=total_students, present=present)


# Dashboard with grouped attendance logs
@app.route('/dashboard')
def dashboard():
    grouped_logs = defaultdict(list)
    
    # Query all attendance records
    records = Attendance.query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    
    for record in records:
        grouped_logs[record.date].append({
            'Date': record.date,
            'Time': record.time,
            'UID': record.student.uid,
            'Name': record.student.name
        })
    
    grouped_logs = dict(grouped_logs)
    return render_template('dashboard.html', grouped_logs=grouped_logs)


# QR scanner AJAX POST endpoint
@app.route('/mark_attendance_api', methods=['POST'])
def mark_attendance_api():
    data = request.get_json()
    uid = data.get('uid', '').strip()
    if not uid:
        return jsonify({'message': 'UID is missing.'}), 400

    success, message = mark_attendance(uid)
    return jsonify({'message': message}), (200 if success else 400)


# Get current stats for real-time updates
@app.route('/get_stats', methods=['GET'])
def get_stats():
    today = datetime.now().strftime('%Y-%m-%d')
    total_students = Student.query.count()
    present = len(get_present_uids(today))
    
    return jsonify({
        'total': total_students,
        'present': present,
        'percentage': round((present / total_students * 100) if total_students else 0, 1)
    })


# Management page (Students, Sessions, Settings all in one)
@app.route('/management')
def management_page():
    # Get students
    students = []
    for student in Student.query.all():
        students.append((student.uid, student.name, student.email))
    total_students = len(students)

    # Get sessions (dates with attendance)
    sessions = defaultdict(int)
    records = Attendance.query.all()
    for record in records:
        sessions[record.date] += 1
    sessions = dict(sorted(sessions.items(), reverse=True))

    return render_template('management.html', 
                         students=students, 
                         total_students=total_students, 
                         sessions=sessions)


# Keep old routes for backward compatibility (redirect to new management page)
@app.route('/students')
def students_page():
    return redirect('/management')

@app.route('/sessions')
def sessions_page():
    return redirect('/management')

@app.route('/settings')
def settings_page():
    return redirect('/management')


# Absent report
@app.route('/report')
def report():
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all students
    all_students = Student.query.all()
    
    # Get present students today
    present_ids = {record.student_id for record in Attendance.query.filter_by(date=today).all()}
    
    # Calculate absentees
    absentees = [(s.uid, s.name) for s in all_students if s.id not in present_ids]

    total_students = len(all_students)
    total_present = len(present_ids)
    total_absent = len(absentees)

    return render_template(
        'report.html',
        date=today,
        absentees=absentees,
        total_students=total_students,
        total_present=total_present,
        total_absent=total_absent
    )

# Export report
@app.route('/report/export/<string:file_type>')
def export_report(file_type):
    today = datetime.now().strftime('%Y-%m-%d')
    all_students = Student.query.all()
    present_ids = {record.student_id for record in Attendance.query.filter_by(date=today).all()}
    absentees = [(s.uid, s.name) for s in all_students if s.id not in present_ids]
    df = pd.DataFrame(absentees, columns=['UID', 'Name'])

    if file_type == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Absentees')
        output.seek(0)
        return send_file(output, download_name='absentees.xlsx', as_attachment=True)

    elif file_type == 'pdf':
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 50, f"Absentees on {today}")
        y = height - 80
        for uid, name in absentees:
            c.drawString(50, y, f"{uid} - {name}")
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 14)
                y = height - 50
        c.save()
        buffer.seek(0)
        return send_file(buffer, download_name='absentees.pdf', as_attachment=True)

    return "Invalid file type", 400

# Send absent email alerts
@app.route('/send-emails')
def send_absent_emails():
    """Send absence notification emails asynchronously"""
    today = datetime.now().strftime('%Y-%m-%d')
    all_students = Student.query.all()
    present_ids = {record.student_id for record in Attendance.query.filter_by(date=today).all()}
    absentees = [(s.uid, s.name, s.email) for s in all_students if s.id not in present_ids]
    
    # Count absentees with email
    email_count = sum(1 for _, _, email in absentees if email)
    
    # Send emails in background thread (don't wait)
    def send_emails_background():
        for uid, name, email in absentees:
            if email:
                try:
                    subject = f"Absent Alert: {name}"
                    body = f"Dear Parent,\n\nThis is to inform you that {name} was absent on {today}.\n\nRegards,\nAttendance System"
                    send_email(email, subject, body)
                except Exception as e:
                    print(f"⚠️  Failed to send email to {email}: {e}")
    
    # Start background thread with daemon=True so it won't block shutdown
    thread = threading.Thread(target=send_emails_background, daemon=True)
    thread.start()
    
    # Return immediately without waiting
    flash(f"Sending email notifications to {email_count} absentee(s) in background...", "info")
    return redirect(url_for('report'))

# Absentees view page
@app.route('/absentees')
def view_absentees():
    today = datetime.now().strftime('%Y-%m-%d')
    all_students = Student.query.all()
    present_ids = {record.student_id for record in Attendance.query.filter_by(date=today).all()}
    absentees = [(s.uid, s.name) for s in all_students if s.id not in present_ids]
    return render_template('absentees.html', date=today, absentees=absentees)

@app.route('/export-absentees')
def export_absentees():
    today = datetime.now().strftime('%Y-%m-%d')
    all_students = Student.query.all()
    present_ids = {record.student_id for record in Attendance.query.filter_by(date=today).all()}

    absentees = [
        {'UID': s.uid, 'Name': s.name, 'Email': s.email}
        for s in all_students if s.id not in present_ids
    ]

    df = pd.DataFrame(absentees)
    file_path = f"absentees_{today}.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

@app.route('/download_qr_pdf')
def download_qr_pdf():
    """Download QR codes as PDF - optimized for large datasets"""
    try:
        students = Student.query.limit(100).all()  # Limit to first 100 students
        pdf_path = "qr_codes.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        x, y = 50, height - 100
        for i, student in enumerate(students):
            # Generate QR code
            qr = qrcode.make(student.uid)
            img_io = BytesIO()
            qr.save(img_io, format='PNG')
            img_io.seek(0)

            # Wrap BytesIO stream with ImageReader
            img = ImageReader(img_io)

            c.drawImage(img, x, y, width=80, height=80)
            c.drawString(x + 90, y + 30, f"{student.name} ({student.uid})")

            y -= 100
            if y < 100:
                c.showPage()
                y = height - 100

        c.save()
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash(f"Error generating QR PDF: {e}", "danger")
        return redirect(url_for('dashboard'))

# Delete attendance logs older than 30 days (cleanup on startup)
def cleanup_old_records():
    """Delete attendance records older than 30 days"""
    cutoff = datetime.now() - timedelta(days=30)
    Attendance.query.filter(Attendance.created_at < cutoff).delete()
    db.session.commit()




# ============ APPLICATION STARTUP ============

# Database initialization flag
_db_initialized = False

@app.before_request
def initialize_database():
    """Initialize database on first request (works with gunicorn)"""
    global _db_initialized
    if not _db_initialized:
        try:
            with app.app_context():
                # Create all tables
                init_db()
                
                # Migrate CSV data if it hasn't been migrated yet
                if Student.query.count() == 0 and os.path.exists('students.csv'):
                    print("\n?? Migrating CSV data to database...")
                    migrate_csv_to_db()
                    print("? Migration complete!\n")
                
                # Cleanup old records
                cleanup_old_records()
                
                _db_initialized = True
        except Exception as e:
            print(f"Database initialization error: {e}")


if __name__ == '__main__':
    # Run Flask app (debug only in development)
    app.run(debug=not IS_PRODUCTION, port=int(os.getenv('PORT', 5000)))
