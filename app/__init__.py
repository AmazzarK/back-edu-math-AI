from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'super_secret_key')
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
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
        "specs_route": "/api/docs"
    }
    swagger = Swagger(app, config=swagger_config)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app import models
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.courses import courses_bp
    from app.routes.tests import tests_bp
    from app.routes.exercises import exercises_bp
    from app.routes.badges import badges_bp
    from app.routes.admin import admin_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.professor import professor_bp
    from app.routes.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(tests_bp, url_prefix='/tests')
    app.register_blueprint(exercises_bp, url_prefix='/exercises')
    app.register_blueprint(badges_bp, url_prefix='/badges')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(professor_bp, url_prefix='/professor')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Invalid credentials'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500
    
    return app
