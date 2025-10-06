"""
Authentication utilities and decorators.
Role-based access control (RBAC) decorators for route-level permissions.
"""
import jwt
import bcrypt
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User
from app.extensions import db

def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, password):
    """Check hashed password against a password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def jwt_required_with_user(f):
    """
    JWT required decorator that also injects current_user.
    
    Usage:
        @jwt_required_with_user
        def protected_route(current_user):
            return {'user_id': current_user.id}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user:
                return jsonify({
                    'error': 'user_not_found',
                    'message': 'User not found'
                }), 404
            
            if not current_user.is_active:
                return jsonify({
                    'error': 'account_deactivated',
                    'message': 'Account is deactivated'
                }), 403
            
            return f(current_user, *args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"JWT verification error: {str(e)}")
            return jsonify({
                'error': 'authentication_failed',
                'message': 'Authentication failed'
            }), 401
    
    return decorated

def role_required(*allowed_roles):
    """
    Role-based access control decorator.
    
    Args:
        *allowed_roles: Variable number of allowed roles
        
    Usage:
        @role_required('admin')
        @role_required('professor', 'admin')
        def admin_only_route(current_user):
            return {'message': 'Admin access granted'}
    """
    def decorator(f):
        @wraps(f)
        @jwt_required_with_user
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({
                    'error': 'insufficient_permissions',
                    'message': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    return decorator

def admin_required(f):
    """Admin-only access decorator."""
    return role_required('admin')(f)

def professor_or_admin_required(f):
    """Professor or admin access decorator."""
    return role_required('professor', 'admin')(f)

def student_required(f):
    """Student-only access decorator."""
    return role_required('student')(f)

def any_role_required(f):
    """Any authenticated user access decorator."""
    return role_required('student', 'professor', 'admin')(f)

def check_user_ownership_or_admin(user_id_field='user_id'):
    """
    Check if current user owns the resource or is admin.
    
    Args:
        user_id_field (str): Field name containing user ID in request data
        
    Usage:
        @check_user_ownership_or_admin('student_id')
        def update_student_profile(current_user):
            # Only student themselves or admin can update
            pass
    """
    def decorator(f):
        @wraps(f)
        @jwt_required_with_user
        def decorated(current_user, *args, **kwargs):
            # Admin can access everything
            if current_user.role == 'admin':
                return f(current_user, *args, **kwargs)
            
            # Get user ID from request data or URL parameters
            target_user_id = None
            
            # Check URL parameters
            if user_id_field in kwargs:
                target_user_id = kwargs[user_id_field]
            
            # Check request JSON
            elif request.is_json and request.get_json().get(user_id_field):
                target_user_id = request.get_json()[user_id_field]
            
            # Check request args
            elif request.args.get(user_id_field):
                target_user_id = request.args.get(user_id_field)
            
            if not target_user_id:
                return jsonify({
                    'error': 'missing_user_id',
                    'message': f'Missing {user_id_field} in request'
                }), 400
            
            # Check ownership
            if str(current_user.id) != str(target_user_id):
                return jsonify({
                    'error': 'access_denied',
                    'message': 'You can only access your own resources'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    return decorator

def get_current_user():
    """
    Get current user from JWT token (utility function).
    
    Returns:
        User: Current user object or None
    """
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        
        if current_user_id:
            return User.query.get(current_user_id)
        
        return None
        
    except Exception:
        return None

def validate_token_claims(required_claims=None):
    """
    Validate additional JWT claims.
    
    Args:
        required_claims (dict): Required claims to validate
        
    Usage:
        @validate_token_claims({'role': 'admin'})
        def admin_route(current_user):
            pass
    """
    def decorator(f):
        @wraps(f)
        @jwt_required_with_user
        def decorated(current_user, *args, **kwargs):
            if required_claims:
                claims = get_jwt()
                
                for claim, expected_value in required_claims.items():
                    if claims.get(claim) != expected_value:
                        return jsonify({
                            'error': 'invalid_token_claims',
                            'message': f'Invalid token claim: {claim}'
                        }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    return decorator

# Legacy decorators for backward compatibility
def token_required(f):
    """Legacy token required decorator."""
    return jwt_required_with_user(f)
