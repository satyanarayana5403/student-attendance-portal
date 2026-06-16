from datetime import datetime
from models import Student, Attendance, TeacherAttendance
from extensions import db
import logging

try:
    from gsheet_helper import append_to_gsheet
except Exception:
    def append_to_gsheet(*a, **k): pass

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
