from app import app
from extensions import db
from models import User, Teacher

with app.app_context():
    print("Triggering initialization via test client...")
    client = app.test_client()
    client.get('/') # This fires before_request which runs init_db and migrate_baseline_data
    
    print("Adding sample teachers...")
    teacher_data = [
        ('teacher1', 'Jane Doe', 'Computer Science'),
        ('teacher2', 'John Smith', 'Mathematics')
    ]
    
    for username, name, dept in teacher_data:
        teacher_user = User.query.filter_by(username=username).first()
        if not teacher_user:
            u = User(username=username, role='teacher')
            u.set_password('teacher123')
            db.session.add(u)
            db.session.flush()
            t = Teacher(user_id=u.id, username=username, name=name, department=dept)
            db.session.add(t)
            print(f"Added teacher: {name}")
    
    db.session.commit()
    print("Database population complete!")
