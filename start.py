#!/usr/bin/env python3
"""
Simple startup script for the Educational Math AI Platform backend.
"""
import os
from app import create_app

if __name__ == '__main__':
    # Create the Flask app
    app = create_app()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Educational Math AI Platform Backend...")
    print(f"📍 Server running on: http://localhost:{port}")
    print("📚 API Documentation available at: http://localhost:{port}/api/docs")
    print("🔧 Environment: Development")
    print("\n" + "="*60)
    print("Available API Endpoints:")
    print("  POST /api/auth/register    - User Registration")
    print("  POST /api/auth/login       - User Login")
    print("  GET  /api/auth/profile     - Get User Profile")
    print("  PUT  /api/auth/profile     - Update User Profile")
    print("  POST /api/auth/refresh     - Refresh JWT Token")
    print("  POST /api/auth/logout      - Logout User")
    print("  POST /api/auth/forgot-password - Request Password Reset")
    print("  POST /api/auth/reset-password  - Reset Password")
    print("="*60)
    print("\n🧪 Test Accounts Available:")
    print("  Admin:     email=admin@eduplatform.com,     password=admin123")
    print("  Professor: email=professor@eduplatform.com, password=professor123")
    print("  Student:   email=student@eduplatform.com,   password=student123")
    print("="*60 + "\n")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True
    )
