"""
Flask extensions initialization module.
Centralized location for all Flask extensions.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_caching import Cache
from flasgger import Swagger
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
cache = Cache()
swagger = Swagger()

# JWT blocklist for revoked tokens (in production, use Redis)
jwt_blocklist = set()

def init_extensions(app):
    """Initialize Flask extensions with app instance."""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    
    # Configure and initialize caching
    cache_config = {
        'CACHE_TYPE': 'SimpleCache',  # Default to simple in-memory cache
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    
    # Use Redis if available
    redis_url = os.getenv('REDIS_URL')
    if redis_url and redis_url != 'memory://':
        try:
            cache_config.update({
                'CACHE_TYPE': 'RedisCache',
                'CACHE_REDIS_URL': redis_url,
                'CACHE_KEY_PREFIX': 'eduplatform:'
            })
        except Exception:
            # Fallback to simple cache if Redis fails
            pass
    
    app.config.update(cache_config)
    app.config['CACHE_ENABLED'] = True
    cache.init_app(app)
    
    # Swagger configuration
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
        "title": "Educational Mathematics AI Platform API",
        "version": "1.0.0",
        "description": "Production-grade backend API for educational platform"
    }
    swagger.init_app(app, config=swagger_config)
    
    # JWT configuration
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if token is in blocklist."""
        return jwt_payload['jti'] in jwt_blocklist
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token."""
        return {
            'error': 'token_expired',
            'message': 'The token has expired'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token."""
        return {
            'error': 'invalid_token',
            'message': 'Signature verification failed'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token."""
        return {
            'error': 'authorization_required',
            'message': 'Request does not contain an access token'
        }, 401
    
    return app
