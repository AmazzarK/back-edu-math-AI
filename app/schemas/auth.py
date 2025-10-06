"""
Marshmallow schemas for request/response validation and serialization.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import re

class UserRegistrationSchema(Schema):
    """Schema for user registration."""
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(['student', 'professor', 'admin']))
    first_name = fields.Str(required=False, validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(required=False, validate=validate.Length(max=50), allow_none=True)
    
    @validates('password')
    def validate_password(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')
    
    def validate(self, data, **kwargs):
        """Cross-field validation."""
        errors = {}
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        if errors:
            raise ValidationError(errors)
        return data

class UserLoginSchema(Schema):
    """Schema for user login."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UserProfileSchema(Schema):
    """Schema for user profile update."""
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    phone = fields.Str(validate=validate.Length(max=20), allow_none=True)
    bio = fields.Str(validate=validate.Length(max=500), allow_none=True)
    avatar_url = fields.Url(allow_none=True)
    preferences = fields.Dict(allow_none=True)
    
    @validates('phone')
    def validate_phone(self, value):
        """Validate phone number format."""
        if value and not re.match(r'^\+?[\d\s\-\(\)]+$', value):
            raise ValidationError('Invalid phone number format')

class ForgotPasswordSchema(Schema):
    """Schema for forgot password request."""
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    """Schema for password reset."""
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    
    @validates('password')
    def validate_password(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')
    
    def validate(self, data, **kwargs):
        """Cross-field validation."""
        errors = {}
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        if errors:
            raise ValidationError(errors)
        return data

class ChangePasswordSchema(Schema):
    """Schema for password change."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    
    @validates('new_password')
    def validate_new_password(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')
    
    def validate(self, data, **kwargs):
        """Cross-field validation."""
        errors = {}
        if data.get('new_password') != data.get('confirm_password'):
            errors['confirm_password'] = ['Passwords do not match']
        if data.get('current_password') == data.get('new_password'):
            errors['new_password'] = ['New password must be different from current password']
        if errors:
            raise ValidationError(errors)
        return data

class UserResponseSchema(Schema):
    """Schema for user response data."""
    id = fields.Str()
    email = fields.Email()
    role = fields.Str()
    profile_data = fields.Dict()
    is_active = fields.Bool()
    email_confirmed = fields.Bool()
    last_login = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    full_name = fields.Str()

class TokenResponseSchema(Schema):
    """Schema for token response."""
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)
    expires_in = fields.Int(required=True)
    token_type = fields.Str(required=True, default='Bearer')
    user = fields.Nested(UserResponseSchema)

class RefreshTokenSchema(Schema):
    """Schema for token refresh."""
    refresh_token = fields.Str(required=True)

class MessageSchema(Schema):
    """Schema for simple message responses."""
    message = fields.Str(required=True)
    status = fields.Str(required=True, default='success')

class ErrorSchema(Schema):
    """Schema for error responses."""
    error = fields.Str(required=True)
    message = fields.Str(required=True)
    details = fields.Dict(allow_none=True)
