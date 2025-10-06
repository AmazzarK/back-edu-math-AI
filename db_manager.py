#!/usr/bin/env python3
"""
Database management script for EduMath AI Platform.
Provides utilities for database operations during development.
"""
import os
import sys
from datetime import datetime, timedelta
from flask_migrate import init, migrate, upgrade, downgrade
from app import create_app
from app.extensions import db
from app.models import User, Exercise, StudentProgress, ChatConversation, Class, UploadedFile, Notification

def create_admin_user():
    """Create an admin user interactively."""
    app = create_app()
    with app.app_context():
        print("Creating admin user...")
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("Email is required")
            return
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists")
            return
        
        full_name = input("Enter full name: ").strip()
        password = input("Enter password: ").strip()
        
        if not password:
            print("Password is required")
            return
        
        admin_user = User(
            email=email,
            full_name=full_name,
            role='admin'
        )
        admin_user.set_password(password)
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ Admin user {email} created successfully!")
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            db.session.rollback()

def reset_database():
    """Reset the database (drop all tables and recreate)."""
    app = create_app()
    with app.app_context():
        response = input("This will delete ALL data. Are you sure? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Operation cancelled")
            return
        
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        print("✓ Database reset complete!")

def seed_sample_data():
    """Seed the database with sample data for development."""
    app = create_app()
    with app.app_context():
        print("Seeding sample data...")
        
        # Create sample users
        users_data = [
            {
                'email': 'admin@edumath-ai.com',
                'full_name': 'System Administrator',
                'role': 'admin',
                'password': 'admin123'
            },
            {
                'email': 'prof1@edumath-ai.com',
                'full_name': 'Dr. Sarah Johnson',
                'role': 'professor',
                'password': 'professor123'
            },
            {
                'email': 'prof2@edumath-ai.com',
                'full_name': 'Dr. Michael Chen',
                'role': 'professor',
                'password': 'professor123'
            },
            {
                'email': 'student1@edumath-ai.com',
                'full_name': 'Alice Cooper',
                'role': 'student',
                'password': 'student123'
            },
            {
                'email': 'student2@edumath-ai.com',
                'full_name': 'Bob Wilson',
                'role': 'student',
                'password': 'student123'
            },
            {
                'email': 'student3@edumath-ai.com',
                'full_name': 'Charlie Brown',
                'role': 'student',
                'password': 'student123'
            }
        ]
        
        created_users = {}
        for user_data in users_data:
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                user = User(
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    role=user_data['role']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                created_users[user_data['role'] + '_' + user_data['email'].split('@')[0]] = user
        
        try:
            db.session.commit()
            print("✓ Sample users created")
        except Exception as e:
            print(f"✗ Error creating users: {e}")
            db.session.rollback()
            return
        
        # Refresh users from database
        admin = User.query.filter_by(email='admin@edumath-ai.com').first()
        prof1 = User.query.filter_by(email='prof1@edumath-ai.com').first()
        prof2 = User.query.filter_by(email='prof2@edumath-ai.com').first()
        student1 = User.query.filter_by(email='student1@edumath-ai.com').first()
        student2 = User.query.filter_by(email='student2@edumath-ai.com').first()
        student3 = User.query.filter_by(email='student3@edumath-ai.com').first()
        
        # Create sample exercises
        exercises_data = [
            {
                'title': 'Basic Addition',
                'description': 'Practice basic addition problems',
                'content': 'Solve: 5 + 3 = ?',
                'difficulty': 'beginner',
                'topic': 'arithmetic',
                'points': 10
            },
            {
                'title': 'Multiplication Tables',
                'description': 'Practice multiplication tables',
                'content': 'Solve: 7 × 8 = ?',
                'difficulty': 'beginner',
                'topic': 'arithmetic',
                'points': 15
            },
            {
                'title': 'Linear Equations',
                'description': 'Solve linear equations',
                'content': 'Solve for x: 2x + 5 = 13',
                'difficulty': 'intermediate',
                'topic': 'algebra',
                'points': 20
            },
            {
                'title': 'Quadratic Equations',
                'description': 'Solve quadratic equations using the quadratic formula',
                'content': 'Solve: x² - 5x + 6 = 0',
                'difficulty': 'intermediate',
                'topic': 'algebra',
                'points': 25
            },
            {
                'title': 'Pythagorean Theorem',
                'description': 'Apply the Pythagorean theorem to find missing sides',
                'content': 'In a right triangle, if a = 3 and b = 4, find c.',
                'difficulty': 'intermediate',
                'topic': 'geometry',
                'points': 20
            },
            {
                'title': 'Calculus Derivatives',
                'description': 'Find derivatives of polynomial functions',
                'content': 'Find the derivative of f(x) = 3x² + 2x - 1',
                'difficulty': 'advanced',
                'topic': 'calculus',
                'points': 30
            }
        ]
        
        created_exercises = []
        for exercise_data in exercises_data:
            exercise = Exercise(**exercise_data)
            db.session.add(exercise)
            created_exercises.append(exercise)
        
        try:
            db.session.commit()
            print("✓ Sample exercises created")
        except Exception as e:
            print(f"✗ Error creating exercises: {e}")
            db.session.rollback()
            return
        
        # Create sample classes
        if prof1 and prof2:
            classes_data = [
                {
                    'name': 'Algebra I - Fall 2024',
                    'description': 'Introduction to algebraic concepts and problem solving',
                    'professor_id': prof1.id,
                    'subject': 'Algebra',
                    'enrollment_code': 'ALG001',
                    'max_students': 30
                },
                {
                    'name': 'Geometry - Fall 2024',
                    'description': 'Fundamental principles of geometry',
                    'professor_id': prof1.id,
                    'subject': 'Geometry',
                    'enrollment_code': 'GEO001',
                    'max_students': 25
                },
                {
                    'name': 'Calculus I - Fall 2024',
                    'description': 'Introduction to differential and integral calculus',
                    'professor_id': prof2.id,
                    'subject': 'Calculus',
                    'enrollment_code': 'CALC001',
                    'max_students': 20
                }
            ]
            
            for class_data in classes_data:
                class_obj = Class(**class_data)
                db.session.add(class_obj)
            
            try:
                db.session.commit()
                print("✓ Sample classes created")
            except Exception as e:
                print(f"✗ Error creating classes: {e}")
                db.session.rollback()
                return
        
        # Create some sample progress for students
        if student1 and created_exercises:
            for i, exercise in enumerate(created_exercises[:3]):  # First 3 exercises
                progress = StudentProgress(
                    user_id=student1.id,
                    exercise_id=exercise.id,
                    completed=True,
                    score=85 + (i * 5),  # 85, 90, 95
                    attempts=1,
                    time_spent=120 + (i * 30)  # 2-3.5 minutes
                )
                db.session.add(progress)
        
        try:
            db.session.commit()
            print("✓ Sample progress data created")
        except Exception as e:
            print(f"✗ Error creating progress: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 50)
        print("✓ Sample data seeding complete!")
        print("Sample accounts created:")
        print("  Admin: admin@edumath-ai.com / admin123")
        print("  Professor 1: prof1@edumath-ai.com / professor123")
        print("  Professor 2: prof2@edumath-ai.com / professor123")
        print("  Student 1: student1@edumath-ai.com / student123")
        print("  Student 2: student2@edumath-ai.com / student123")
        print("  Student 3: student3@edumath-ai.com / student123")
        print("=" * 50)

def show_stats():
    """Show database statistics."""
    app = create_app()
    with app.app_context():
        print("Database Statistics:")
        print("=" * 30)
        print(f"Users: {User.query.count()}")
        print(f"  - Admins: {User.query.filter_by(role='admin').count()}")
        print(f"  - Professors: {User.query.filter_by(role='professor').count()}")
        print(f"  - Students: {User.query.filter_by(role='student').count()}")
        print(f"Exercises: {Exercise.query.count()}")
        print(f"Student Progress: {StudentProgress.query.count()}")
        print(f"Chat Conversations: {ChatConversation.query.count()}")
        print(f"Classes: {Class.query.count()}")
        print(f"Uploaded Files: {UploadedFile.query.count()}")
        print(f"Notifications: {Notification.query.count()}")

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("EduMath AI Platform - Database Management")
        print("Usage: python db_manager.py <command>")
        print("\nAvailable commands:")
        print("  init        - Initialize database migrations")
        print("  migrate     - Generate a new migration")
        print("  upgrade     - Apply migrations")
        print("  downgrade   - Rollback last migration")
        print("  reset       - Reset database (WARNING: deletes all data)")
        print("  seed        - Seed database with sample data")
        print("  admin       - Create admin user")
        print("  stats       - Show database statistics")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        app = create_app()
        with app.app_context():
            init()
            print("✓ Database migrations initialized")
    
    elif command == 'migrate':
        message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
        app = create_app()
        with app.app_context():
            migrate(message=message)
            print(f"✓ Migration created: {message}")
    
    elif command == 'upgrade':
        app = create_app()
        with app.app_context():
            upgrade()
            print("✓ Database upgraded")
    
    elif command == 'downgrade':
        app = create_app()
        with app.app_context():
            downgrade()
            print("✓ Database downgraded")
    
    elif command == 'reset':
        reset_database()
    
    elif command == 'seed':
        seed_sample_data()
    
    elif command == 'admin':
        create_admin_user()
    
    elif command == 'stats':
        show_stats()
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python db_manager.py' to see available commands")

if __name__ == '__main__':
    main()
