import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'nexus-attendance-secure-key-2026-xyz!')
    UPLOAD_FOLDER = 'static/uploads/profiles'
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB limit
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours CSRF token life
    
    # Cookie security against XSS & CSRF
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    DB_URL = os.getenv('DATABASE_URL')
    if DB_URL:
        if DB_URL.startswith('postgresql://'):
            DB_URL = DB_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
        elif DB_URL.startswith('mysql://') and 'pymysql' not in DB_URL:
            DB_URL = DB_URL.replace('mysql://', 'mysql+pymysql://', 1)
        
        # Strip query parameters (like ?ssl-mode=...) from MySQL URLs 
        # as they cause "unexpected keyword argument" errors in pymysql
        if 'mysql' in DB_URL and '?' in DB_URL:
            DB_URL = DB_URL.split('?')[0]
    else:
        DB_URL = 'mysql+pymysql://root:Venky%40321@localhost:3306/attendance_db'

    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configure engine options with SSL support for cloud providers like Aiven
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    if DB_URL and ('aivencloud.com' in DB_URL or 'ssl-mode=REQUIRED' in DB_URL):
        engine_options["connect_args"] = {"ssl": {}}

    SQLALCHEMY_ENGINE_OPTIONS = engine_options
