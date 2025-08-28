import csv
from datetime import datetime
from email_helper import send_email

STUDENT_DATA_CSV = 'students.csv'
ATTENDANCE_LOG = 'attendance_log.csv'

def load_student_data():
    students = {}
    try:
        with open(STUDENT_DATA_CSV, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                uid = row['UID']
                students[uid] = {
                    'Name': row['Name'],
                    'Email': row.get('ParentEmail') or row.get('Email', '').strip()
                }
    except FileNotFoundError:
        print(f"Error: {STUDENT_DATA_CSV} not found.")
    return students

def get_present_uids(today_date):
    present_uids = set()
    try:
        with open(ATTENDANCE_LOG, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Date'] == today_date:
                    present_uids.add(row['UID'])
    except FileNotFoundError:
        print(f"Warning: {ATTENDANCE_LOG} not found.")
    return present_uids

def notify_absentees():
    today = datetime.now().strftime('%Y-%m-%d')
    all_students = load_student_data()
    present_uids = get_present_uids(today)

    absentees = [uid for uid in all_students if uid not in present_uids]

    print(f"\n📅 Date: {today}")
    print(f"🧍‍♂️ Total Students: {len(all_students)}")
    print(f"✅ Present: {len(present_uids)}")
    print(f"❌ Absent: {len(absentees)}\n")

    for uid in absentees:
        name = all_students[uid]['Name']
        email = all_students[uid]['Email']
        subject = f"Absence Notification: {name}"
        message = f"""Dear Parent,

This is to inform you that {name} (UID: {uid}) was absent today ({today}).

Please ensure they provide a valid reason or medical certificate if needed.

Regards,  
Smart Attendance System
"""
        if email:
            send_email(email, subject, message)
            print(f"✅ Email sent to: {email} for {name}")
        else:
            print(f"⚠️  No email provided for: {name} (UID: {uid})")

if __name__ == '__main__':
    notify_absentees()
