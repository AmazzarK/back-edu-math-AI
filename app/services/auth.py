"""
Authentication service layer.
Business logic for user authentication, registration, and profile management.
"""
import uuid
import secrets
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from app.extensions import db, jwt_blocklist
from app.models import User
from app.services.email import EmailService

class AuthService:
    """Service class for authentication operations."""
    
    @staticmethod
    def register_user(email, password, role, first_name=None, last_name=None):
        """
        Register a new user.
        
        Args:
            email (str): User email
            password (str): User password
            role (str): User role (student, professor, admin)
            first_name (str, optional): User first name
            last_name (str, optional): User last name
            
        Returns:
            tuple: (User object, error message)
        """
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email.lower()).first()
            if existing_user:
                return None, "User with this email already exists"
            
            # Create new user
            user = User(
                email=email.lower(),
                role=role,
                profile_data={
                    'first_name': first_name or '',
                    'last_name': last_name or '',
                    'phone': '',
                    'bio': '',
                    'avatar_url': '',
                    'preferences': {
                        'language': 'en',
                        'timezone': 'UTC',
                        'email_notifications': True
                    }
                }
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # TODO: Send email confirmation
            EmailService.send_welcome_email(user)
            
            return user, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            return None, "Registration failed"
    
    @staticmethod
    def authenticate_user(email, password):
        """
        Authenticate user credentials.
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            tuple: (User object, error message)
        """
        try:
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                return None, "Invalid email or password"
            
            if not user.is_active:
                return None, "Account is deactivated"
            
            if not user.check_password(password):
                return None, "Invalid email or password"
            
            # Update last login
            user.update_last_login()
            
            return user, None
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return None, "Authentication failed"
    
    @staticmethod
    def create_tokens(user):
        """
        Create access and refresh tokens for user.
        
        Args:
            user (User): User object
            
        Returns:
            dict: Token data
        """
        additional_claims = {
            "role": user.role,
            "email": user.email
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600),
            "token_type": "Bearer",
            "user": user.to_dict()
        }
    
    @staticmethod
    def refresh_token():
        """
        Refresh access token using refresh token.
        
        Returns:
            tuple: (token data, error message)
        """
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return None, "User not found or inactive"
            
            additional_claims = {
                "role": user.role,
                "email": user.email
            }
            
            new_access_token = create_access_token(
                identity=str(user.id),
                additional_claims=additional_claims
            )
            
            return {
                "access_token": new_access_token,
                "expires_in": current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600),
                "token_type": "Bearer"
            }, None
            
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return None, "Token refresh failed"
    
    @staticmethod
    def logout_user():
        """
        Logout user by adding token to blocklist.
        
        Returns:
            tuple: (success, error message)
        """
        try:
            jti = get_jwt()['jti']
            jwt_blocklist.add(jti)
            return True, None
        except Exception as e:
            current_app.logger.error(f"Logout error: {str(e)}")
            return False, "Logout failed"
    
    @staticmethod
    def get_user_profile(user_id):
        """
        Get user profile by ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            tuple: (User object, error message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            return user, None
        except Exception as e:
            current_app.logger.error(f"Get profile error: {str(e)}")
            return None, "Failed to get user profile"
    
    @staticmethod
    def update_user_profile(user_id, profile_data):
        """
        Update user profile.
        
        Args:
            user_id (str): User ID
            profile_data (dict): Profile data to update
            
        Returns:
            tuple: (User object, error message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            user.update_profile(profile_data)
            db.session.commit()
            
            return user, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Update profile error: {str(e)}")
            return None, "Failed to update profile"
    
    @staticmethod
    def initiate_password_reset(email):
        """
        Initiate password reset process.
        
        Args:
            email (str): User email
            
        Returns:
            tuple: (success, error message)
        """
        try:
            user = User.query.filter_by(email=email.lower()).first()
            if not user:
                # Don't reveal if email exists
                return True, None
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store token in cache/database (simplified for demo)
            # In production, store in Redis with expiration
            user.profile_data = user.profile_data or {}
            user.profile_data['reset_token'] = reset_token
            user.profile_data['reset_token_expires'] = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            
            db.session.commit()
            
            # Send reset email
            EmailService.send_password_reset_email(user, reset_token)
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset initiation error: {str(e)}")
            return False, "Failed to initiate password reset"
    
    @staticmethod
    def reset_password(token, new_password):
        """
        Reset password using token.
        
        Args:
            token (str): Reset token
            new_password (str): New password
            
        Returns:
            tuple: (success, error message)
        """
        try:
            # Find user with this token
            users = User.query.all()
            user = None
            
            for u in users:
                if (u.profile_data and 
                    u.profile_data.get('reset_token') == token and
                    u.profile_data.get('reset_token_expires')):
                    
                    expires_at = datetime.fromisoformat(u.profile_data['reset_token_expires'])
                    if expires_at > datetime.utcnow():
                        user = u
                        break
            
            if not user:
                return False, "Invalid or expired reset token"
            
            # Update password
            user.set_password(new_password)
            
            # Clear reset token
            user.profile_data['reset_token'] = None
            user.profile_data['reset_token_expires'] = None
            
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset error: {str(e)}")
            return False, "Failed to reset password"
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Change user password.
        
        Args:
            user_id (str): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            tuple: (success, error message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if not user.check_password(current_password):
                return False, "Current password is incorrect"
            
            user.set_password(new_password)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {str(e)}")
            return False, "Failed to change password"
