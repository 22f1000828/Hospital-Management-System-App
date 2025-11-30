from app import create_app, db
from app.models import User, Department
from config import Config

def init_db():
    app = create_app(Config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin already exists or not
        admin = User.query.filter_by(role='Admin').first()
        if admin:
            print(f"Admin user already exists: {admin.username}")
            return
        
        # Create default admin user
        admin = User(
            username='admin',
            email='admin@hospital.com',
            role='Admin',
            is_active=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        
        # Create default departments
        departments = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular system'},
            {'name': 'Neurology', 'description': 'Brain and nervous system'},
            {'name': 'Orthopedics', 'description': 'Bones, joints, and muscles'},
            {'name': 'Pediatrics', 'description': 'Children\'s health'},
            {'name': 'Dermatology', 'description': 'Skin, hair, and nails'},
            {'name': 'General Medicine', 'description': 'General health and wellness'}
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(name=dept_data['name']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
        
        db.session.commit()
        print("Database initialized successfully!")
        print("Admin user created:")
        print("  Username: admin")
        print("  Email: admin@hospital.com")
        print("  Password: admin123")

if __name__ == '__main__':
    init_db()

