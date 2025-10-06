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
    
    # Rate Limiting Configuration
    app.config['RATELIMIT_STORAGE_URL'] = os.getenv('REDIS_URL', 'memory://')
    app.config['RATELIMIT_DEFAULT'] = '1000 per hour'
    
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
    """Register Flask blueprints."""
    # Authentication API
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'message': 'Educational Mathematics AI Platform API is running',
            'version': '2.0.0'
        }), 200
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': 'Educational Mathematics AI Platform API',
            'version': '2.0.0',
            'description': 'Production-grade backend API for educational platform',
            'documentation': '/api/docs',
            'endpoints': {
                'auth': '/auth',
                'health': '/health',
                'docs': '/api/docs'
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
