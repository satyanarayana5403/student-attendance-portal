import os
import csv
from datetime import datetime
from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager, csrf, migrate
from models import User, Student, Teacher, AppSetting

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.teacher import teacher_bp
    from routes.student import student_bp
    from routes.api import api_bp
    from routes.support import support_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(support_bp, url_prefix='/support')

    # Catch-all alias for legacy endpoints
    from core import mark_attendance
    from flask import request, jsonify
    
    @app.route('/get_stats')
    def get_stats():
        from routes.api import api_stats
        return api_stats()

    @app.route('/mark_attendance_api', methods=['POST'])
    @csrf.exempt
    def mark_attendance_api():
        data = request.get_json() or {}
        uid = data.get('uid', '').strip()
        if not uid:
            return jsonify({'success': False, 'message': 'UID required'}), 400
        success, msg = mark_attendance(uid)
        return jsonify({'success': success, 'message': msg})

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Database Initialization (Deferred to first request)
    _db_initialized = False

    def init_db():
        try:
            db.create_all()
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("[OK] Default admin created (admin/admin123)")

            defaults = {'realtime': 'true', 'email': 'true', 'qr': 'true'}
            for key, val in defaults.items():
                if not AppSetting.query.filter_by(key=key).first():
                    db.session.add(AppSetting(key=key, value=val))
            db.session.commit()
            print("[OK] Database initialized successfully")
        except Exception as e:
            print(f"[WARN] Database initialization failed: {e}")
            raise e

    def migrate_baseline_data():
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
                        username=username,
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

    @app.before_request
    def ensure_db_initialized():
        nonlocal _db_initialized
        if not _db_initialized:
            try:
                init_db()
                migrate_baseline_data()
                _db_initialized = True
            except Exception as e:
                print(f"[ERROR] Failed to initialize database: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 5000)))
