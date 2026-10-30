import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import sqlite3
import pymysql
from datetime import datetime
from app import create_app
from extensions import db
from models import User, Student, Teacher, Attendance, TeacherAttendance, AppSetting, SupportTicket

app = create_app()

def migrate():
    sqlite_conn = sqlite3.connect("scratch/head_attendance.db")
    sqlite_conn.row_factory = sqlite3.Row
    s_cur = sqlite_conn.cursor()

    with app.app_context():
        # Ensure all tables exist in MySQL
        print("Creating MySQL tables...")
        db.create_all()

        # Clean existing tables in MySQL if any
        # Disable foreign key checks for clean load
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
        for tbl in ['support_tickets', 'teacher_attendance', 'attendance', 'teachers', 'students', 'settings', 'users']:
            db.session.execute(db.text(f"TRUNCATE TABLE {tbl};"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.session.commit()

        # 1. Migrate Users
        print("\n--- Migrating Users ---")
        s_cur.execute("SELECT * FROM users")
        users_rows = s_cur.fetchall()
        user_map = {} # id -> username
        for r in users_rows:
            c_at = r['created_at']
            if isinstance(c_at, str):
                try:
                    c_at = datetime.fromisoformat(c_at)
                except Exception:
                    c_at = datetime.now()
            user = User(
                id=r['id'],
                username=r['username'],
                password_hash=r['password_hash'],
                role=r['role'],
                created_at=c_at
            )
            user_map[r['id']] = r['username']
            db.session.add(user)
        db.session.commit()
        print(f"Migrated {len(users_rows)} users.")

        # 2. Migrate Settings
        print("\n--- Migrating Settings ---")
        s_cur.execute("SELECT * FROM settings")
        settings_rows = s_cur.fetchall()
        for r in settings_rows:
            setting = AppSetting(
                id=r['id'],
                key=r['key'],
                value=r['value']
            )
            db.session.add(setting)
        db.session.commit()
        print(f"Migrated {len(settings_rows)} settings.")

        # 3. Migrate Students
        print("\n--- Migrating Students ---")
        s_cur.execute("SELECT * FROM students")
        students_rows = s_cur.fetchall()
        for r in students_rows:
            uname = user_map.get(r['user_id'], r['uid'].lower().replace(" ", ""))
            student = Student(
                id=r['id'],
                user_id=r['user_id'],
                username=uname,
                uid=r['uid'],
                name=r['name'],
                email=r['email'] or '',
                profile_pic=r['profile_pic'] or 'default_student.png'
            )
            db.session.add(student)
        db.session.commit()
        print(f"Migrated {len(students_rows)} students.")

        # 4. Migrate Teachers
        print("\n--- Migrating Teachers ---")
        s_cur.execute("SELECT * FROM teachers")
        teachers_rows = s_cur.fetchall()
        for r in teachers_rows:
            uname = user_map.get(r['user_id'], r['name'].lower().replace(" ", ""))
            teacher = Teacher(
                id=r['id'],
                user_id=r['user_id'],
                username=uname,
                name=r['name'],
                department=r['department'] or '',
                email=r['email'] or '',
                profile_pic=r['profile_pic'] or 'default_teacher.png'
            )
            db.session.add(teacher)
        db.session.commit()
        print(f"Migrated {len(teachers_rows)} teachers.")

        # 5. Migrate Attendance
        print("\n--- Migrating Attendance ---")
        s_cur.execute("SELECT * FROM attendance")
        attendance_rows = s_cur.fetchall()
        for r in attendance_rows:
            att = Attendance(
                id=r['id'],
                student_id=r['student_id'],
                date=r['date'],
                time=r['time']
            )
            db.session.add(att)
        db.session.commit()
        print(f"Migrated {len(attendance_rows)} attendance records.")

        # 6. Migrate Teacher Attendance
        print("\n--- Migrating Teacher Attendance ---")
        s_cur.execute("SELECT * FROM teacher_attendance")
        t_att_rows = s_cur.fetchall()
        for r in t_att_rows:
            t_att = TeacherAttendance(
                id=r['id'],
                teacher_id=r['teacher_id'],
                date=r['date'],
                time=r['time']
            )
            db.session.add(t_att)
        db.session.commit()
        print(f"Migrated {len(t_att_rows)} teacher attendance records.")

        # 7. Migrate Support Tickets
        print("\n--- Migrating Support Tickets ---")
        s_cur.execute("SELECT * FROM support_tickets")
        tickets_rows = s_cur.fetchall()
        for r in tickets_rows:
            t_at = r['created_at']
            if isinstance(t_at, str):
                try:
                    t_at = datetime.fromisoformat(t_at)
                except Exception:
                    t_at = datetime.now()
            u_at = r['updated_at']
            if isinstance(u_at, str):
                try:
                    u_at = datetime.fromisoformat(u_at)
                except Exception:
                    u_at = datetime.now()
            ticket = SupportTicket(
                id=r['id'],
                user_id=r['user_id'],
                subject=r['subject'],
                message=r['message'],
                status=r['status'] or 'open',
                admin_reply=r['admin_reply'] or '',
                created_at=t_at,
                updated_at=u_at
            )
            db.session.add(ticket)
        db.session.commit()
        print(f"Migrated {len(tickets_rows)} support tickets.")

    sqlite_conn.close()
    print("\n[SUCCESS] All data successfully migrated from SQLite to MySQL!")

if __name__ == '__main__':
    migrate()
