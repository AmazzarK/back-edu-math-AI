from app import create_app, db
from app.models import User, Course, Badge
from app.utils.auth import hash_password
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
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            full_name="System Administrator",
            email="admin@eduplatform.com",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        
        # Create professor user
        professor = User(
            id=uuid.uuid4(),
            full_name="Dr. Jane Smith",
            email="professor@eduplatform.com",
            password_hash=hash_password("prof123"),
            role="professor"
        )
        
        # Create student user
        student = User(
            id=uuid.uuid4(),
            full_name="John Doe",
            email="student@eduplatform.com",
            password_hash=hash_password("student123"),
            role="student"
        )
        
        # Add users to session
        db.session.add(admin)
        db.session.add(professor)
        db.session.add(student)
        
        # Commit users first to get their IDs
        db.session.commit()
        
        # Create a sample course
        course = Course(
            title="Introduction to Mathematics",
            description="Basic mathematical concepts and problem-solving techniques",
            professor_id=professor.id
        )
        
        db.session.add(course)
        
        # Create sample badges
        badges = [
            Badge(
                name="First Steps",
                description="Completed your first exercise",
                icon_url="https://example.com/icons/first-steps.png"
            ),
            Badge(
                name="Quiz Master",
                description="Scored 100% on a test",
                icon_url="https://example.com/icons/quiz-master.png"
            ),
            Badge(
                name="Consistent Learner",
                description="Completed exercises for 7 days straight",
                icon_url="https://example.com/icons/consistent-learner.png"
            )
        ]
        
        for badge in badges:
            db.session.add(badge)
        
        # Commit all changes
        db.session.commit()
        
        print("Database seeded successfully!")
        print(f"Admin: admin@eduplatform.com / admin123")
        print(f"Professor: professor@eduplatform.com / prof123")
        print(f"Student: student@eduplatform.com / student123")

if __name__ == '__main__':
    seed_database()
