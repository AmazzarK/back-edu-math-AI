"""
Authentication API endpoints.
Enhanced RESTful authentication with JWT, role-based access, and profile management.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError

from app.extensions import limiter
from app.schemas.auth import (
    UserRegistrationSchema, UserLoginSchema, UserProfileSchema,
    ForgotPasswordSchema, ResetPasswordSchema, ChangePasswordSchema,
    UserResponseSchema, TokenResponseSchema, RefreshTokenSchema,
    MessageSchema, ErrorSchema
)
from app.services.auth import AuthService
from app.utils.auth import jwt_required_with_user, role_required, any_role_required

# Create blueprint
auth_bp = Blueprint('auth', __name__)
api = Api(auth_bp)

class RegisterResource(Resource):
    """User registration endpoint."""
    
    decorators = [limiter.limit("5 per minute")]
    
    def post(self):
        """
        Register a new user
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
                - confirm_password
                - role
              properties:
                email:
                  type: string
                  format: email
                  example: student@example.com
                password:
                  type: string
                  minLength: 8
                  example: SecurePass123!
                confirm_password:
                  type: string
                  example: SecurePass123!
                role:
                  type: string
                  enum: [student, professor, admin]
                  example: student
                first_name:
                  type: string
                  example: John
                last_name:
                  type: string
                  example: Doe
        responses:
          201:
            description: User registered successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                user:
                  $ref: '#/definitions/User'
          400:
            description: Validation error or user already exists
        """
        try:
            schema = UserRegistrationSchema()
            data = schema.load(request.get_json() or {})
            
            user, error = AuthService.register_user(
                email=data['email'],
                password=data['password'],
                role=data['role'],
                first_name=data.get('first_name'),
                last_name=data.get('last_name')
            )
            
            if error:
                return {'error': 'registration_failed', 'message': error}, 400
            
            response_schema = UserResponseSchema()
            return {
                'message': 'User registered successfully',
                'user': response_schema.dump(user.to_dict())
            }, 201
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Registration failed due to server error'
            }, 500

class LoginResource(Resource):
    """User login endpoint."""
    
    decorators = [limiter.limit("10 per minute")]
    
    def post(self):
        """
        User login
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                  example: student@example.com
                password:
                  type: string
                  example: SecurePass123!
        responses:
          200:
            description: Login successful
            schema:
              type: object
              properties:
                message:
                  type: string
                access_token:
                  type: string
                refresh_token:
                  type: string
                expires_in:
                  type: integer
                token_type:
                  type: string
                user:
                  $ref: '#/definitions/User'
          401:
            description: Invalid credentials
        """
        try:
            schema = UserLoginSchema()
            data = schema.load(request.get_json() or {})
            
            user, error = AuthService.authenticate_user(
                email=data['email'],
                password=data['password']
            )
            
            if error:
                return {'error': 'authentication_failed', 'message': error}, 401
            
            token_data = AuthService.create_tokens(user)
            
            return {
                'message': 'Login successful',
                **token_data
            }, 200
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Login failed due to server error'
            }, 500

class LogoutResource(Resource):
    """User logout endpoint."""
    
    @jwt_required()
    def post(self):
        """
        User logout
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        responses:
          200:
            description: Logout successful
          401:
            description: Invalid or missing token
        """
        try:
            success, error = AuthService.logout_user()
            
            if not success:
                return {'error': 'logout_failed', 'message': error}, 400
            
            return {'message': 'Logout successful'}, 200
            
        except Exception as e:
            current_app.logger.error(f"Logout error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Logout failed due to server error'
            }, 500

class RefreshResource(Resource):
    """Token refresh endpoint."""
    
    @jwt_required(refresh=True)
    def post(self):
        """
        Refresh access token
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        responses:
          200:
            description: Token refreshed successfully
            schema:
              type: object
              properties:
                access_token:
                  type: string
                expires_in:
                  type: integer
                token_type:
                  type: string
          401:
            description: Invalid refresh token
        """
        try:
            token_data, error = AuthService.refresh_token()
            
            if error:
                return {'error': 'token_refresh_failed', 'message': error}, 401
            
            return {
                'message': 'Token refreshed successfully',
                **token_data
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Token refresh failed due to server error'
            }, 500

class ProfileResource(Resource):
    """User profile management endpoint."""
    
    @any_role_required
    def get(self, current_user):
        """
        Get user profile
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        responses:
          200:
            description: User profile retrieved successfully
            schema:
              $ref: '#/definitions/User'
          404:
            description: User not found
        """
        try:
            response_schema = UserResponseSchema()
            return response_schema.dump(current_user.to_dict()), 200
            
        except Exception as e:
            current_app.logger.error(f"Get profile error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Failed to retrieve profile'
            }, 500
    
    @any_role_required
    def put(self, current_user):
        """
        Update user profile
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                first_name:
                  type: string
                  example: John
                last_name:
                  type: string
                  example: Doe
                phone:
                  type: string
                  example: "+1234567890"
                bio:
                  type: string
                  example: "Mathematics enthusiast"
                avatar_url:
                  type: string
                  format: uri
                  example: "https://example.com/avatar.jpg"
                preferences:
                  type: object
                  properties:
                    language:
                      type: string
                      example: en
                    timezone:
                      type: string
                      example: UTC
                    email_notifications:
                      type: boolean
                      example: true
        responses:
          200:
            description: Profile updated successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                user:
                  $ref: '#/definitions/User'
          400:
            description: Validation error
        """
        try:
            schema = UserProfileSchema()
            data = schema.load(request.get_json() or {})
            
            user, error = AuthService.update_user_profile(
                user_id=current_user.id,
                profile_data=data
            )
            
            if error:
                return {'error': 'profile_update_failed', 'message': error}, 400
            
            response_schema = UserResponseSchema()
            return {
                'message': 'Profile updated successfully',
                'user': response_schema.dump(user.to_dict())
            }, 200
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Update profile error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Failed to update profile'
            }, 500

class ForgotPasswordResource(Resource):
    """Forgot password endpoint."""
    
    decorators = [limiter.limit("3 per minute")]
    
    def post(self):
        """
        Initiate password reset
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
              properties:
                email:
                  type: string
                  format: email
                  example: student@example.com
        responses:
          200:
            description: Password reset email sent (if email exists)
          400:
            description: Validation error
        """
        try:
            schema = ForgotPasswordSchema()
            data = schema.load(request.get_json() or {})
            
            success, error = AuthService.initiate_password_reset(data['email'])
            
            # Always return success to prevent email enumeration
            return {
                'message': 'If the email exists, a password reset link has been sent'
            }, 200
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Forgot password error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Password reset failed due to server error'
            }, 500

class ResetPasswordResource(Resource):
    """Reset password endpoint."""
    
    decorators = [limiter.limit("5 per minute")]
    
    def post(self):
        """
        Reset password with token
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - token
                - password
                - confirm_password
              properties:
                token:
                  type: string
                  example: "reset_token_here"
                password:
                  type: string
                  minLength: 8
                  example: NewSecurePass123!
                confirm_password:
                  type: string
                  example: NewSecurePass123!
        responses:
          200:
            description: Password reset successful
          400:
            description: Invalid token or validation error
        """
        try:
            schema = ResetPasswordSchema()
            data = schema.load(request.get_json() or {})
            
            success, error = AuthService.reset_password(
                token=data['token'],
                new_password=data['password']
            )
            
            if not success:
                return {'error': 'password_reset_failed', 'message': error}, 400
            
            return {'message': 'Password reset successful'}, 200
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Reset password error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Password reset failed due to server error'
            }, 500

class ChangePasswordResource(Resource):
    """Change password endpoint."""
    
    @any_role_required
    def post(self, current_user):
        """
        Change user password
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - current_password
                - new_password
                - confirm_password
              properties:
                current_password:
                  type: string
                  example: CurrentPass123!
                new_password:
                  type: string
                  minLength: 8
                  example: NewSecurePass123!
                confirm_password:
                  type: string
                  example: NewSecurePass123!
        responses:
          200:
            description: Password changed successfully
          400:
            description: Invalid current password or validation error
        """
        try:
            schema = ChangePasswordSchema()
            data = schema.load(request.get_json() or {})
            
            success, error = AuthService.change_password(
                user_id=current_user.id,
                current_password=data['current_password'],
                new_password=data['new_password']
            )
            
            if not success:
                return {'error': 'password_change_failed', 'message': error}, 400
            
            return {'message': 'Password changed successfully'}, 200
            
        except ValidationError as err:
            return {
                'error': 'validation_failed',
                'message': 'Invalid input data',
                'details': err.messages
            }, 400
        except Exception as e:
            current_app.logger.error(f"Change password error: {str(e)}")
            return {
                'error': 'internal_error',
                'message': 'Password change failed due to server error'
            }, 500

# Register API resources
api.add_resource(RegisterResource, '/register')
api.add_resource(LoginResource, '/login')
api.add_resource(LogoutResource, '/logout')
api.add_resource(RefreshResource, '/refresh')
api.add_resource(ProfileResource, '/profile')
api.add_resource(ForgotPasswordResource, '/forgot-password')
api.add_resource(ResetPasswordResource, '/reset-password')
api.add_resource(ChangePasswordResource, '/change-password')
