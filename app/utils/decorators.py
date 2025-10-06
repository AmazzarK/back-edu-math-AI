"""
Utility decorators for API endpoints.
"""
import functools
import logging
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models import User

logger = logging.getLogger(__name__)


def handle_exceptions(f):
    """Decorator to handle common exceptions in API endpoints."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"ValueError in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except PermissionError as e:
            logger.warning(f"PermissionError in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred'
            }), 500
    
    return decorated_function


def role_required(*allowed_roles):
    """Decorator to check if user has required role."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user:
                    return jsonify({
                        'success': False,
                        'message': 'User not found'
                    }), 404
                
                if user.role not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'message': f'Access denied. Required role: {" or ".join(allowed_roles)}'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in role check for {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Authorization error'
                }), 500
        
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to check if user is admin."""
    return role_required('admin')(f)


def professor_required(f):
    """Decorator to check if user is professor."""
    return role_required('professor')(f)


def student_required(f):
    """Decorator to check if user is student."""
    return role_required('student')(f)


def rate_limit(max_requests=60, window=60):
    """
    Simple rate limiting decorator.
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # In a production environment, you would implement proper rate limiting
            # using Redis or another caching solution
            # For now, this is a placeholder
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """
    Decorator to cache API responses.
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # In a production environment, you would implement proper caching
            # using Redis or another caching solution
            # For now, this is a placeholder that just calls the function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def log_api_call(f):
    """Decorator to log API calls for monitoring."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity() if hasattr(get_jwt_identity, '__call__') else None
            logger.info(f"API call: {f.__name__} by user {user_id}")
            
            result = f(*args, **kwargs)
            
            # Log successful completion
            if hasattr(result, 'status_code'):
                status = result.status_code
            else:
                status = 'success'
            
            logger.info(f"API call completed: {f.__name__} - status: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"API call failed: {f.__name__} - error: {str(e)}")
            raise
    
    return decorated_function


def validate_content_type(content_type='application/json'):
    """Decorator to validate request content type."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if request.content_type != content_type:
                return jsonify({
                    'success': False,
                    'message': f'Content-Type must be {content_type}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_json_data(f):
    """Decorator to ensure request has JSON data."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must contain JSON data'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body cannot be empty'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def paginate_response(default_per_page=20, max_per_page=100):
    """Decorator to add pagination parameters to request."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', default_per_page, type=int)
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            
            if per_page < 1:
                per_page = default_per_page
            elif per_page > max_per_page:
                per_page = max_per_page
            
            # Add to kwargs
            kwargs['page'] = page
            kwargs['per_page'] = per_page
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def track_user_activity(activity_type='api_call'):
    """Decorator to track user activity."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                if user_id:
                    # In a production environment, you would store this activity
                    # in a database or analytics service
                    logger.info(f"User activity: {user_id} - {activity_type} - {f.__name__}")
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error tracking activity for {f.__name__}: {str(e)}")
                return f(*args, **kwargs)  # Continue execution even if tracking fails
        
        return decorated_function
    return decorator


def measure_performance(f):
    """Decorator to measure API endpoint performance."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Performance: {f.__name__} took {duration:.4f} seconds")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"Performance: {f.__name__} failed after {duration:.4f} seconds")
            raise
    
    return decorated_function
