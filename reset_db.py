from app import db, app, User, AppSetting
from dotenv import load_dotenv

def reset_db():
    load_dotenv()
    with app.app_context():
        print(f"Connecting to: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        
        print("Creating default admin...")
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        print("Creating default settings...")
        defaults = {'realtime': 'true', 'email': 'true', 'qr': 'true'}
        for key, val in defaults.items():
            db.session.add(AppSetting(key=key, value=val))
        
        db.session.commit()
        print("Done!")

if __name__ == '__main__':
    reset_db()
