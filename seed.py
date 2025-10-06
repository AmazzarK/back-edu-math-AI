"""
Enhanced database seeding script for Educational Mathematics AI Platform.
Creates sample users with the new User model structure and sample exercises.
"""
from app import create_app
from app.extensions import db
from app.models import User, Exercise, Progress
from datetime import datetime, timedelta
import uuid

def create_sample_exercises(professor_id, student_id):
    """Create sample exercises and progress data."""
    
    # Sample exercises with different types and difficulties
    exercises_data = [
        {
            'title': 'Basic Arithmetic',
            'description': 'Fundamental arithmetic operations for beginners',
            'difficulty': 'easy',
            'subject': 'Mathematics',
            'type': 'multiple_choice',
            'questions': [
                {
                    'text': 'What is 15 + 27?',
                    'options': ['40', '42', '44', '46']
                },
                {
                    'text': 'What is 8 × 7?',
                    'options': ['54', '56', '58', '60']
                },
                {
                    'text': 'What is 144 ÷ 12?',
                    'options': ['11', '12', '13', '14']
                }
            ],
            'solutions': [
                {'correct_option': 1},  # 42
                {'correct_option': 1},  # 56
                {'correct_option': 1}   # 12
            ],
            'max_score': 100.0,
            'time_limit': 15,
            'is_published': True,
            'tags': ['arithmetic', 'basic', 'beginner']
        },
        {
            'title': 'Algebraic Equations',
            'description': 'Solving simple linear equations',
            'difficulty': 'medium',
            'subject': 'Algebra',
            'type': 'calculation',
            'questions': [
                {
                    'text': 'Solve for x: 2x + 5 = 13',
                    'hint': 'Subtract 5 from both sides, then divide by 2'
                },
                {
                    'text': 'Solve for y: 3y - 7 = 14',
                    'hint': 'Add 7 to both sides, then divide by 3'
                }
            ],
            'solutions': [
                {'answer': 4, 'tolerance': 0.1},
                {'answer': 7, 'tolerance': 0.1}
            ],
            'max_score': 100.0,
            'time_limit': 20,
            'is_published': True,
            'tags': ['algebra', 'equations', 'linear']
        },
        {
            'title': 'Geometry Basics',
            'description': 'Basic geometric shapes and properties',
            'difficulty': 'easy',
            'subject': 'Geometry',
            'type': 'multiple_choice',
            'questions': [
                {
                    'text': 'How many sides does a pentagon have?',
                    'options': ['4', '5', '6', '7']
                },
                {
                    'text': 'What is the sum of angles in a triangle?',
                    'options': ['90°', '180°', '270°', '360°']
                }
            ],
            'solutions': [
                {'correct_option': 1},  # 5
                {'correct_option': 1}   # 180°
            ],
            'max_score': 100.0,
            'time_limit': 10,
            'is_published': True,
            'tags': ['geometry', 'shapes', 'angles']
        }
    ]
    
    created_exercises = []
    
    for exercise_data in exercises_data:
        exercise = Exercise(
            title=exercise_data['title'],
            description=exercise_data['description'],
            difficulty=exercise_data['difficulty'],
            subject=exercise_data['subject'],
            type=exercise_data['type'],
            questions=exercise_data['questions'],
            solutions=exercise_data['solutions'],
            created_by=professor_id,
            max_score=exercise_data['max_score'],
            time_limit=exercise_data['time_limit'],
            is_published=exercise_data['is_published'],
            tags=exercise_data['tags']
        )
        
        db.session.add(exercise)
        created_exercises.append(exercise)
    
    # Commit exercises first to get IDs
    db.session.commit()
    
    # Create sample progress records for the student
    sample_progress = [
        {
            'exercise': created_exercises[0],  # Basic Arithmetic
            'answers': [
                {'question_index': 0, 'selected_option': 1},  # Correct
                {'question_index': 1, 'selected_option': 1},  # Correct
                {'question_index': 2, 'selected_option': 0}   # Incorrect
            ],
            'time_spent': 480,  # 8 minutes
            'completed_days_ago': 3
        },
        {
            'exercise': created_exercises[1],  # Algebraic Equations
            'answers': [
                {'question_index': 0, 'answer': 4},   # Correct
                {'question_index': 1, 'answer': 6.5}  # Close but not exact
            ],
            'time_spent': 720,  # 12 minutes
            'completed_days_ago': 2
        }
    ]
    
    for progress_data in sample_progress:
        exercise = progress_data['exercise']
        
        progress = Progress(
            student_id=student_id,
            exercise_id=exercise.id,
            status='completed',
            attempts=1,
            time_spent=progress_data['time_spent'],
            answers=progress_data['answers']
        )
        
        # Calculate score using the exercise's scoring logic
        progress.score = exercise.calculate_score(progress_data['answers'])
        
        # Set realistic timestamps
        completed_time = datetime.utcnow() - timedelta(days=progress_data['completed_days_ago'])
        progress.started_at = completed_time - timedelta(seconds=progress_data['time_spent'])
        progress.completed_at = completed_time
        progress.submitted_at = completed_time
        progress.created_at = progress.started_at
        progress.updated_at = completed_time
        
        db.session.add(progress)
    
    return created_exercises

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
        
        print("👥 Users created successfully!")
        
        # Create sample exercises and progress
        print("📚 Creating sample exercises and progress data...")
        exercises = create_sample_exercises(professor.id, student.id)
        
        db.session.commit()
        
        print(f"✅ Created {len(exercises)} sample exercises")
        print(f"✅ Created {Progress.query.count()} progress records")
        
        print("✅ Database seeded successfully!")
        print("\n🔑 Default User Accounts:")
        print("=" * 50)
        print(f"Admin:          admin@eduplatform.com / Admin123!")
        print(f"Professor:      professor@eduplatform.com / Prof123!")
        print(f"Student:        student@eduplatform.com / Student123!")
        print(f"Test Student:   teststudent@eduplatform.com / Test123!")
        print(f"Test Professor: testprof@eduplatform.com / TestProf123!")
        print("=" * 50)
        print("\n� Sample Data Created:")
        for i, exercise in enumerate(exercises, 1):
            print(f"   {i}. {exercise.title} ({exercise.difficulty.title()} - {exercise.subject})")
        print("=" * 50)
        print("\n�🚀 You can now:")
        print("1. Start the server: python start.py")
        print("2. Test the API at: http://localhost:5000")
        print("3. View API docs at: http://localhost:5000/api/docs")
        print("4. Test exercise endpoints with Postman")
        print("5. Login as student to see progress analytics")

if __name__ == '__main__':
    seed_database()
