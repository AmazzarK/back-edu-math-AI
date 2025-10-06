#!/usr/bin/env python3
"""
Quick test script to verify all imports are working correctly.
"""

try:
    # Test Flask imports
    import flask
    from flask_restful import Api, Resource
    from flask_jwt_extended import JWTManager
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_mail import Mail
    from flask_caching import Cache
    
    print("✓ Flask packages imported successfully")
    
    # Test database imports
    import psycopg2
    import marshmallow
    from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
    
    print("✓ Database packages imported successfully")
    
    # Test security imports
    import bcrypt
    from email_validator import validate_email
    
    print("✓ Security packages imported successfully")
    
    # Test task queue imports
    import celery
    import redis
    
    print("✓ Task queue packages imported successfully")
    
    # Test AI imports
    import openai
    
    print("✓ AI packages imported successfully")
    
    # Test file processing imports
    from PIL import Image
    import boto3
    
    print("✓ File processing packages imported successfully")
    
    # Test other utilities
    from werkzeug.utils import secure_filename
    import requests
    from dotenv import load_dotenv
    
    print("✓ Utility packages imported successfully")
    
    print("\n🎉 All package imports successful!")
    print("The EduMath AI Platform backend is ready to run!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    exit(1)
