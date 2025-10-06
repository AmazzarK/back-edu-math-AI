"""
Enhanced database seeding script for Educational Mathematics AI Platform.
Creates sample users with the new User model structure.
"""
from app import create_app
from app.extensions import db
from app.models import User
import uuid

def seed_database():
    """Seed the database with initial data."""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if users already exist
        if User.query.first():
            print("Database already seeded!")
            return
        
        print("Seeding database with sample data...")
        
        # Create admin user
        admin = User(
            email="admin@eduplatform.com",
            role="admin",
            profile_data={
                'first_name': 'System',
                'last_name': 'Administrator',
                'phone': '+1234567890',
                'bio': 'System administrator for the Educational Mathematics AI Platform',
                'avatar_url': 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin',
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC',
                    'email_notifications': True
                }
            },
            is_active=True,
            email_confirmed=True
        )
        admin.set_password("Admin123!")
        
        # Create professor user
        professor = User(
            email="professor@eduplatform.com",
            role="professor",
            profile_data={
                'first_name': 'Dr. Jane',
                'last_name': 'Smith',
                'phone': '+1234567891',
                'bio': 'Mathematics professor with 10+ years of experience in educational technology',
                'avatar_url': 'https://api.dicebear.com/7.x/avataaars/svg?seed=professor',
                'preferences': {
                    'language': 'en',
                    'timezone': 'EST',
                    'email_notifications': True
                }
            },
            is_active=True,
            email_confirmed=True
        )
        professor.set_password("Prof123!")
        
        # Create student user
        student = User(
            email="student@eduplatform.com",
            role="student",
            profile_data={
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+1234567892',
                'bio': 'Enthusiastic mathematics student passionate about AI and technology',
                'avatar_url': 'https://api.dicebear.com/7.x/avataaars/svg?seed=student',
                'preferences': {
                    'language': 'en',
                    'timezone': 'PST',
                    'email_notifications': False
                }
            },
            is_active=True,
            email_confirmed=True
        )
        student.set_password("Student123!")
        
        # Create additional test users
        test_student = User(
            email="teststudent@eduplatform.com",
            role="student",
            profile_data={
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'phone': '',
                'bio': 'Test student account for development and testing',
                'avatar_url': 'https://api.dicebear.com/7.x/avataaars/svg?seed=teststudent',
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC',
                    'email_notifications': True
                }
            },
            is_active=True,
            email_confirmed=False  # For testing email confirmation flow
        )
        test_student.set_password("Test123!")
        
        test_professor = User(
            email="testprof@eduplatform.com",
            role="professor",
            profile_data={
                'first_name': 'Dr. Bob',
                'last_name': 'Wilson',
                'phone': '+1987654321',
                'bio': 'Test professor account for development and testing',
                'avatar_url': 'https://api.dicebear.com/7.x/avataaars/svg?seed=testprof',
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC',
                    'email_notifications': True
                }
            },
            is_active=True,
            email_confirmed=True
        )
        test_professor.set_password("TestProf123!")
        
        # Add users to session
        users = [admin, professor, student, test_student, test_professor]
        for user in users:
            db.session.add(user)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Database seeded successfully!")
        print("\n🔑 Default User Accounts:")
        print("=" * 50)
        print(f"Admin:          admin@eduplatform.com / Admin123!")
        print(f"Professor:      professor@eduplatform.com / Prof123!")
        print(f"Student:        student@eduplatform.com / Student123!")
        print(f"Test Student:   teststudent@eduplatform.com / Test123!")
        print(f"Test Professor: testprof@eduplatform.com / TestProf123!")
        print("=" * 50)
        print("\n🚀 You can now:")
        print("1. Start the server: python run.py")
        print("2. Test the API at: http://localhost:5000")
        print("3. View API docs at: http://localhost:5000/api/docs")
        print("4. Test endpoints with the accounts above")

if __name__ == '__main__':
    seed_database()
