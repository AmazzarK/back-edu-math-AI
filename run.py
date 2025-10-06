#!/usr/bin/env python3
"""
Development startup script for EduMath AI Platform.
This script initializes the database and starts the Flask application.
"""
import os
import sys
import logging
from flask_migrate import upgrade
from app import create_app
from app.extensions import db
from app.models import User, Exercise

def setup_logging():
    """Configure logging for startup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def init_database(app):
    """Initialize database with tables and seed data."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Check if we need to create an admin user
        admin_user = User.query.filter_by(email='admin@edumath-ai.com').first()
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                email='admin@edumath-ai.com',
                full_name='System Administrator',
                role='admin'
            )
            admin_user.set_password('admin123')  # Change this in production!
            db.session.add(admin_user)
            
            # Create sample professor
            professor = User(
                email='professor@edumath-ai.com',
                full_name='Dr. Jane Smith',
                role='professor'
            )
            professor.set_password('professor123')
            db.session.add(professor)
            
            # Create sample student
            student = User(
                email='student@edumath-ai.com',
                full_name='John Doe',
                role='student'
            )
            student.set_password('student123')
            db.session.add(student)
            
            try:
                db.session.commit()
                print("✓ Default users created successfully!")
                print("  Admin: admin@edumath-ai.com / admin123")
                print("  Professor: professor@edumath-ai.com / professor123")
                print("  Student: student@edumath-ai.com / student123")
                print("  ⚠️  Please change these passwords in production!")
            except Exception as e:
                print(f"✗ Error creating default users: {e}")
                db.session.rollback()
        else:
            print("✓ Admin user already exists")
        
        # Create sample exercises if none exist
        if Exercise.query.count() == 0:
            print("Creating sample exercises...")
            sample_exercises = [
                {
                    'title': 'Basic Addition',
                    'description': 'Practice basic addition problems',
                    'content': 'Solve: 5 + 3 = ?',
                    'difficulty': 'beginner',
                    'topic': 'arithmetic',
                    'points': 10
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
                }
            ]
            
            for exercise_data in sample_exercises:
                exercise = Exercise(**exercise_data)
                db.session.add(exercise)
            
            try:
                db.session.commit()
                print("✓ Sample exercises created successfully!")
            except Exception as e:
                print(f"✗ Error creating sample exercises: {e}")
                db.session.rollback()
        else:
            print("✓ Exercises already exist in database")

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   Please check your .env file")
        return False
    
    return True

def check_optional_services():
    """Check status of optional services."""
    print("\nChecking optional services...")
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        print("✓ Redis connection successful")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Caching and background tasks will be limited")
    
    # Check OpenAI API
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✓ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not configured")
        print("   AI chat features will use mock responses")
    
    # Check Email configuration
    mail_server = os.getenv('MAIL_SERVER')
    if mail_server:
        print("✓ Email server configured")
    else:
        print("⚠️  Email server not configured")
        print("   Email notifications will be logged only")

def main():
    """Main startup function."""
    setup_logging()
    
    print("🚀 Starting EduMath AI Platform...")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        print("Please create a .env file based on .env.example")
        sys.exit(1)
    
    # Create Flask app
    app = create_app()
    
    # Initialize database
    init_database(app)
    
    # Check optional services
    check_optional_services()
    
    print("\n" + "=" * 50)
    print("✓ EduMath AI Platform started successfully!")
    print(f"✓ Environment: {app.config.get('FLASK_ENV', 'development')}")
    print(f"✓ Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("✓ Server running on http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  🏠 Health Check: http://localhost:5000/health")
    print("  📚 API Info: http://localhost:5000/api/info")
    print("  🔐 Auth: http://localhost:5000/api/auth/")
    print("  🤖 Chat: http://localhost:5000/api/chat/")
    print("  🏫 Classes: http://localhost:5000/api/classes/")
    print("  📊 Dashboard: http://localhost:5000/api/dashboard/")
    print("  📁 Files: http://localhost:5000/api/files/")
    print("  🔔 Notifications: http://localhost:5000/api/notifications/")
    print("\n🎯 Ready for development!")
    print("=" * 50)
    
    # Start the application
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5000)),
            debug=app.config.get('DEBUG', True),
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down EduMath AI Platform...")
        print("✓ Application stopped gracefully")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
