"""
Request validation utilities.
"""
import functools
import logging
from flask import request, jsonify
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


def validate_json_request(f):
    """Decorator to validate that request contains valid JSON."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must contain JSON data',
                'error_code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        try:
            data = request.get_json()
            if data is None:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format',
                    'error_code': 'INVALID_JSON'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Failed to parse JSON data',
                'error_code': 'JSON_PARSE_ERROR'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_schema(schema_class, location='json'):
    """
    Decorator to validate request data against a Marshmallow schema.
    
    Args:
        schema_class: Marshmallow schema class
        location: Where to get data from ('json', 'args', 'form')
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                
                if location == 'json':
                    if not request.is_json:
                        return jsonify({
                            'success': False,
                            'message': 'Request must contain JSON data'
                        }), 400
                    data = request.get_json()
                elif location == 'args':
                    data = request.args.to_dict()
                elif location == 'form':
                    data = request.form.to_dict()
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid data location specified'
                    }), 500
                
                validated_data = schema.load(data)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': e.messages,
                    'error_code': 'VALIDATION_ERROR'
                }), 400
            except Exception as e:
                logger.error(f"Validation error in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Validation error occurred'
                }), 500
        
        return decorated_function
    return decorator


def validate_query_params(**param_validators):
    """
    Decorator to validate query parameters.
    
    Args:
        **param_validators: Dictionary of parameter names and their validators
    
    Example:
        @validate_query_params(
            page=lambda x: int(x) > 0,
            per_page=lambda x: 1 <= int(x) <= 100
        )
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            errors = {}
            
            for param_name, validator in param_validators.items():
                value = request.args.get(param_name)
                
                if value is not None:
                    try:
                        if not validator(value):
                            errors[param_name] = f'Invalid value for {param_name}'
                    except (ValueError, TypeError) as e:
                        errors[param_name] = f'Invalid format for {param_name}: {str(e)}'
            
            if errors:
                return jsonify({
                    'success': False,
                    'message': 'Invalid query parameters',
                    'errors': errors,
                    'error_code': 'INVALID_QUERY_PARAMS'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions=None, max_size=None):
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_extensions: List of allowed file extensions
        max_size: Maximum file size in bytes
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': 'No file provided',
                    'error_code': 'NO_FILE'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': 'No file selected',
                    'error_code': 'NO_FILE_SELECTED'
                }), 400
            
            # Check file extension
            if allowed_extensions:
                if not file.filename or '.' not in file.filename:
                    return jsonify({
                        'success': False,
                        'message': 'File must have an extension',
                        'error_code': 'NO_FILE_EXTENSION'
                    }), 400
                
                extension = file.filename.rsplit('.', 1)[1].lower()
                if extension not in allowed_extensions:
                    return jsonify({
                        'success': False,
                        'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}',
                        'error_code': 'INVALID_FILE_TYPE'
                    }), 400
            
            # Check file size
            if max_size:
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > max_size:
                    return jsonify({
                        'success': False,
                        'message': f'File too large. Maximum size: {max_size} bytes',
                        'error_code': 'FILE_TOO_LARGE'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_ids(**id_validators):
    """
    Decorator to validate ID parameters from URL.
    
    Args:
        **id_validators: Dictionary of ID parameter names and their validators
    
    Example:
        @validate_ids(
            user_id=lambda x: len(str(x)) <= 50,
            class_id=lambda x: isinstance(x, int) and x > 0
        )
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            errors = {}
            
            for id_name, validator in id_validators.items():
                if id_name in kwargs:
                    try:
                        if not validator(kwargs[id_name]):
                            errors[id_name] = f'Invalid {id_name}'
                    except (ValueError, TypeError) as e:
                        errors[id_name] = f'Invalid format for {id_name}: {str(e)}'
            
            if errors:
                return jsonify({
                    'success': False,
                    'message': 'Invalid ID parameters',
                    'errors': errors,
                    'error_code': 'INVALID_ID_PARAMS'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_required_fields(*required_fields):
    """
    Decorator to validate that required fields are present in request data.
    
    Args:
        *required_fields: Field names that must be present
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Request must contain JSON data'
                }), 400
            
            data = request.get_json()
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'error_code': 'MISSING_REQUIRED_FIELDS',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def sanitize_input(f):
    """Decorator to sanitize input data."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_json:
            data = request.get_json()
            if data:
                # Basic sanitization
                sanitized_data = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        # Remove potentially dangerous characters
                        sanitized_value = value.strip()
                        # You can add more sophisticated sanitization here
                        sanitized_data[key] = sanitized_value
                    else:
                        sanitized_data[key] = value
                
                # Replace the original data with sanitized data
                request._cached_json = (sanitized_data, sanitized_data)
        
        return f(*args, **kwargs)
    
    return decorated_function


class ValidationUtils:
    """Utility class for common validation functions."""
    
    @staticmethod
    def is_valid_email(email):
        """Check if email format is valid."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_password(password):
        """Check if password meets requirements."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is valid"
    
    @staticmethod
    def is_valid_phone(phone):
        """Check if phone number format is valid."""
        import re
        # Basic phone validation (can be improved)
        pattern = r'^\+?[\d\s\-\(\)]{10,}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def sanitize_string(text, max_length=None):
        """Sanitize a string input."""
        if not isinstance(text, str):
            return text
        
        # Remove leading/trailing whitespace
        sanitized = text.strip()
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_pagination_params(page, per_page, max_per_page=100):
        """Validate and normalize pagination parameters."""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except (ValueError, TypeError):
            raise ValueError("Page and per_page must be integers")
        
        if page < 1:
            page = 1
        
        if per_page < 1:
            per_page = 20
        elif per_page > max_per_page:
            per_page = max_per_page
        
        return page, per_page
