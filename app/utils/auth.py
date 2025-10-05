import jwt
import bcrypt
from functools import wraps
from flask import request, jsonify, current_app
from app.models import User
from app import db

def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, password):
    """Check hashed password against a password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id, role):
    """Generate JWT token for user."""
    payload = {
        'user_id': str(user_id),
        'role': role
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

def decode_token(token):
    """Decode JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            payload = decode_token(token)
            if payload is None:
                return jsonify({'error': 'Token is invalid'}), 401
            
            current_user = User.query.filter_by(id=payload['user_id']).first()
            if current_user is None:
                return jsonify({'error': 'User not found'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    """Decorator to require specific role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def get_current_user():
    """Get current user from JWT token."""
    token = None
    
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return None
    
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        if payload is None:
            return None
        
        current_user = User.query.filter_by(id=payload['user_id']).first()
        return current_user
    except Exception:
        return None
