"""
Email service for sending various types of emails.
For now, this is a stub that prints to console.
In production, integrate with SendGrid, AWS SES, or similar.
"""
from flask import current_app

class EmailService:
    """Email service class for sending emails."""
    
    @staticmethod
    def send_welcome_email(user):
        """
        Send welcome email to new user.
        
        Args:
            user (User): User object
        """
        try:
            # In production, send actual email
            message = f"""
            ========================================
            WELCOME EMAIL SENT TO: {user.email}
            ========================================
            
            Welcome to Educational Mathematics AI Platform!
            
            Dear {user.full_name or user.email},
            
            Thank you for registering as a {user.role.title()}.
            
            Your account has been created successfully.
            Please confirm your email address by clicking the link below:
            
            http://localhost:3000/confirm-email?token=dummy_token
            
            Best regards,
            Educational Mathematics AI Platform Team
            ========================================
            """
            
            print(message)
            current_app.logger.info(f"Welcome email sent to {user.email}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email: {str(e)}")
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """
        Send password reset email.
        
        Args:
            user (User): User object
            reset_token (str): Password reset token
        """
        try:
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
            
            message = f"""
            ========================================
            PASSWORD RESET EMAIL SENT TO: {user.email}
            ========================================
            
            Password Reset Request
            
            Dear {user.full_name or user.email},
            
            You have requested to reset your password for your Educational Mathematics AI Platform account.
            
            Please click the link below to reset your password:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you did not request this password reset, please ignore this email.
            
            Best regards,
            Educational Mathematics AI Platform Team
            ========================================
            """
            
            print(message)
            current_app.logger.info(f"Password reset email sent to {user.email}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {str(e)}")
    
    @staticmethod
    def send_password_changed_notification(user):
        """
        Send password changed notification.
        
        Args:
            user (User): User object
        """
        try:
            message = f"""
            ========================================
            PASSWORD CHANGED NOTIFICATION SENT TO: {user.email}
            ========================================
            
            Password Changed Successfully
            
            Dear {user.full_name or user.email},
            
            Your password has been successfully changed.
            
            If you did not make this change, please contact our support team immediately.
            
            Best regards,
            Educational Mathematics AI Platform Team
            ========================================
            """
            
            print(message)
            current_app.logger.info(f"Password changed notification sent to {user.email}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to send password changed notification: {str(e)}")
    
    @staticmethod
    def send_email_confirmation(user, confirmation_token):
        """
        Send email confirmation.
        
        Args:
            user (User): User object
            confirmation_token (str): Email confirmation token
        """
        try:
            confirmation_url = f"http://localhost:3000/confirm-email?token={confirmation_token}"
            
            message = f"""
            ========================================
            EMAIL CONFIRMATION SENT TO: {user.email}
            ========================================
            
            Please Confirm Your Email Address
            
            Dear {user.full_name or user.email},
            
            Please confirm your email address by clicking the link below:
            {confirmation_url}
            
            This link will expire in 24 hours.
            
            Best regards,
            Educational Mathematics AI Platform Team
            ========================================
            """
            
            print(message)
            current_app.logger.info(f"Email confirmation sent to {user.email}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email confirmation: {str(e)}")
