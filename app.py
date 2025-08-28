from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from email_helper import send_email
from gsheet_helper import append_to_gsheet
from flask import send_file
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key'

STUDENT_FILE = 'students.csv'
ATTENDANCE_FILE = 'attendance_log.csv'

# Load students from CSV
def get_present_uids(date):
    present_uids = set()
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == date:
                    present_uids.add(row['UID'])
    return present_uids

def load_students():
    students = {}
    try:
        with open(STUDENT_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                students[row['UID']] = {
                    'name': row['Name'],
                    'email': row.get('ParentEmail', '')
                }
    except FileNotFoundError:
        print("students.csv not found.")
    return students

# Save attendance to CSV
def mark_attendance(uid):
    students = load_students()
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')

    if uid not in students:
        return False, "UID not found."

    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Time', 'UID', 'Name'])

    with open(ATTENDANCE_FILE, 'r') as f:
        existing_records = [row for row in csv.DictReader(f)]
        for row in existing_records:
            if row['UID'] == uid and row['Date'] == date:
                return False, "Attendance already marked for today."

    with open(ATTENDANCE_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date, time, uid, students[uid]['name']])

    append_to_gsheet(f"{date} {time}", uid, students[uid]['name'])
    return True, f"Attendance marked for {students[uid]['name']}."

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
    students = load_students()
    present = get_present_uids(today)

    return render_template('index.html', total=len(students), present=len(present))

# Dashboard with grouped attendance logs
@app.route('/dashboard')
def dashboard():
    if not os.path.exists(ATTENDANCE_FILE):
        return render_template('dashboard.html', grouped_logs={})

    grouped_logs = defaultdict(list)
    with open(ATTENDANCE_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            grouped_logs[row['Date']].append(row)
    grouped_logs = dict(sorted(grouped_logs.items(), reverse=True))
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

# Absent report
@app.route('/report')
def report():
    students = load_students()
    today = datetime.now().strftime('%Y-%m-%d')
    present_uids = set()

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    present_uids.add(row['UID'])

    absentees = [(uid, data['name']) for uid, data in students.items() if uid not in present_uids]

    total_students = len(students)
    total_present = len(present_uids)
    total_absent = len(absentees)

    return render_template(
        'report.html',
        date=today,
        absentees=absentees,
        total_students=total_students,
        total_present=total_present,
        total_absent=total_absent
    )

@app.route('/report/export/<string:file_type>')
def export_report(file_type):
    students = load_students()
    today = datetime.now().strftime('%Y-%m-%d')
    present_uids = set()

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    present_uids.add(row['UID'])

    absentees = [(uid, data['name']) for uid, data in students.items() if uid not in present_uids]
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
    students = load_students()
    today = datetime.now().strftime('%Y-%m-%d')
    present_uids = set()

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    present_uids.add(row['UID'])

    absentees = [(uid, data['name'], data['email']) for uid, data in students.items() if uid not in present_uids]

    for uid, name, email in absentees:
        if email:
            subject = f"Absent Alert: {name}"
            body = f"Dear Parent,\n\nThis is to inform you that {name} was absent on {today}.\n\nRegards,\nAttendance System"
            send_email(email, subject, body)

    flash(f"Email notifications sent to {len(absentees)} absentee(s).", "success")
    return redirect(url_for('report'))

# Absentees view page
@app.route('/absentees')
def view_absentees():
    students = load_students()
    today = datetime.now().strftime('%Y-%m-%d')
    present_uids = set()

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Date'] == today:
                    present_uids.add(row['UID'])

    absentees = [(uid, data['name']) for uid, data in students.items() if uid not in present_uids]
    return render_template('absentees.html', date=today, absentees=absentees)

@app.route('/export-absentees')
def export_absentees():
    students = load_students()
    today = datetime.now().strftime('%Y-%m-%d')
    present_uids = get_present_uids(today)

    absentees = [
        {'UID': uid, 'Name': data['name'], 'Email': data['email']}
        for uid, data in students.items() if uid not in present_uids
    ]

    df = pd.DataFrame(absentees)
    file_path = f"absentees_{today}.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

@app.route('/download_qr_pdf')
def download_qr_pdf():
    students = load_students()
    pdf_path = "qr_codes.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    x, y = 50, height - 100
    for i, (uid, data) in enumerate(students.items()):
        qr = qrcode.make(uid)
        img_io = BytesIO()
        qr.save(img_io, format='PNG')
        img_io.seek(0)

        # Wrap BytesIO stream with ImageReader
        img = ImageReader(img_io)

        c.drawImage(img, x, y, width=80, height=80)
        c.drawString(x + 90, y + 30, f"{data['name']} ({uid})")

        y -= 100
        if y < 100:
            c.showPage()
            y = height - 100

    c.save()
    return send_file(pdf_path, as_attachment=True)

# Delete attendance logs older than 30 days
@app.before_request
def delete_old_logs():
    if not os.path.exists(ATTENDANCE_FILE):
        return

    cutoff = datetime.now() - timedelta(days=30)
    rows = []

    with open(ATTENDANCE_FILE, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            if datetime.strptime(row['Date'], '%Y-%m-%d') >= cutoff:
                rows.append(row)

    with open(ATTENDANCE_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
