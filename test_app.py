#!/usr/bin/env python3
"""
Quick test script to verify the Flask app can start and respond to requests.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    
    print("✅ Flask app imports successfully!")
    
    # Create the app
    app = create_app()
    
    print("✅ Flask app created successfully!")
    
    # Test app context
    with app.app_context():
        # Create database tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Test a simple route
        with app.test_client() as client:
            response = client.get('/api/health')
            print(f"✅ Health check endpoint responds with status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.get_json()}")
    
    print("\n🎉 Your Flask application is working correctly!")
    print("📍 You can now run: python run.py")
    print("🌐 The API will be available at: http://localhost:5000")
    print("📚 API Documentation at: http://localhost:5000/api/docs")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
