"""
Flask application factory with enhanced architecture.
Production-grade backend for Educational Mathematics AI Platform.
"""
import os
import logging
from datetime import timedelta
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """
    Create Flask application with factory pattern.
    
    Args:
        config_name (str): Configuration name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Configuration
    configure_app(app, config_name)
    
    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app import models
    
    # Register blueprints
    register_blueprints(app)
    
    # Configure logging
    configure_logging(app)
    
    # Error handlers
    register_error_handlers(app)
    
    return app

def configure_app(app, config_name=None):
    """Configure Flask application."""
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    
    # Base configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///eduplatform.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
    
    # CORS Configuration
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    app.config['CORS_ALLOW_HEADERS'] = ['Content-Type', 'Authorization']
    app.config['CORS_METHODS'] = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # Redis Configuration for caching and Celery
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config['RATELIMIT_STORAGE_URL'] = app.config['REDIS_URL']
    app.config['RATELIMIT_DEFAULT'] = '1000 per hour'
    
    # Celery Configuration
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', app.config['REDIS_URL'])
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', app.config['REDIS_URL'])
    
    # OpenAI Configuration
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    app.config['OPENAI_MODEL'] = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    app.config['OPENAI_MAX_TOKENS'] = int(os.getenv('OPENAI_MAX_TOKENS', 1000))
    app.config['OPENAI_TEMPERATURE'] = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    
    # File Upload Configuration
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB
    
    # AWS S3 Configuration (optional)
    app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    app.config['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
    app.config['S3_BUCKET_NAME'] = os.getenv('S3_BUCKET_NAME')
    
    # Application URLs
    app.config['APP_URL'] = os.getenv('APP_URL', 'http://localhost:3000')
    app.config['API_URL'] = os.getenv('API_URL', 'http://localhost:5000')
    
    # Email Configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@eduplatform.com')
    
    # Environment-specific configuration
    if config_name == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['SQLALCHEMY_ECHO'] = False
    elif config_name == 'testing':
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=30)
        app.config['WTF_CSRF_ENABLED'] = False
    else:  # development
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
        app.config['SQLALCHEMY_ECHO'] = False

def register_blueprints(app):
    """Register Flask blueprints and API routes."""
    from flask_restful import Api
    
    # Initialize Flask-RESTful
    api = Api(app)
    
    # Authentication API
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Exercises and Analytics API
    from app.api.exercises import exercises_bp
    app.register_blueprint(exercises_bp, url_prefix='/api')
    
    # Register new API endpoints with Flask-RESTful
    
    # Chat API endpoints
    from app.api.chat import register_chat_routes
    register_chat_routes(api)
    
    # Class management API endpoints
    from app.api.classes import register_class_routes
    register_class_routes(api)
    
    # Dashboard API endpoints
    from app.api.dashboard import register_dashboard_routes
    register_dashboard_routes(api)
    
    # File management API endpoints
    from app.api.files import register_file_routes
    register_file_routes(api)
    
    # Notification API endpoints
    from app.api.notifications import register_notification_routes
    register_notification_routes(api)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'message': 'Educational Mathematics AI Platform API is running',
            'version': '3.0.0'
        }), 200
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': 'Educational Mathematics AI Platform API',
            'version': '3.0.0',
            'description': 'Production-grade backend API for educational platform with AI tutoring',
            'documentation': '/api/docs',
            'features': [
                'AI-powered tutoring and chat',
                'Class and course management',
                'File upload and storage',
                'Real-time notifications',
                'Comprehensive analytics dashboard',
                'Progress tracking and gamification'
            ],
            'endpoints': {
                'auth': '/api/auth',
                'exercises': '/api/exercises',
                'progress': '/api/progress',
                'analytics': '/api/analytics',
                'chat': '/api/chat',
                'classes': '/api/classes',
                'dashboard': '/api/dashboard',
                'files': '/api/files',
                'notifications': '/api/notifications',
                'health': '/health'
            }
        }), 200

def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Production logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        app.logger.setLevel(logging.INFO)
        app.logger.info('Educational Platform API startup')

def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors."""
        return jsonify({
            'error': 'bad_request',
            'message': 'Bad request - invalid input data',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors."""
        return jsonify({
            'error': 'unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors."""
        return jsonify({
            'error': 'forbidden',
            'message': 'Insufficient permissions',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors."""
        return jsonify({
            'error': 'not_found',
            'message': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle method not allowed errors."""
        return jsonify({
            'error': 'method_not_allowed',
            'message': 'Method not allowed for this endpoint',
            'status_code': 405
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit exceeded errors."""
        return jsonify({
            'error': 'rate_limit_exceeded',
            'message': 'Rate limit exceeded. Please try again later.',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors."""
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        app.logger.error(f'Unexpected error: {str(error)}')
        
        # Don't reveal internal errors in production
        if app.config.get('DEBUG'):
            return jsonify({
                'error': 'unexpected_error',
                'message': str(error),
                'status_code': 500
            }), 500
        else:
            return jsonify({
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
