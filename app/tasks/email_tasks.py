"""
Email notification tasks using Celery for asynchronous processing.
"""
import logging
from typing import Dict, List, Optional
from celery import Celery
from flask import current_app
from flask_mail import Message
from app.extensions import mail
from app.models import Notification, User

logger = logging.getLogger(__name__)

# Initialize Celery (this would be configured in your main app)
def create_celery_app(app=None):
    """Create and configure Celery app."""
    celery = Celery(
        app.import_name if app else 'edu-math-ai',
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0'
    )
    
    if app:
        # Update configuration
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# For now, we'll create a mock celery app for development
celery = create_celery_app()


@celery.task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: int):
    """
    Send email notification asynchronously.
    
    Args:
        notification_id: ID of the notification to send via email
    """
    try:
        # Get notification
        notification = Notification.query.get(notification_id)
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return False
        
        # Get user
        user = User.query.get(notification.user_id)
        if not user or not user.email:
            logger.warning(f"User {notification.user_id} not found or has no email")
            return False
        
        # Check if user has email notifications enabled
        user_settings = user.settings or {}
        notification_settings = user_settings.get('notifications', {})
        
        if not notification_settings.get('email_notifications', True):
            logger.info(f"Email notifications disabled for user {user.id}")
            return False
        
        # Check if this notification type should send emails
        type_enabled = notification_settings.get(notification.type, True)
        if not type_enabled:
            logger.info(f"Email disabled for notification type {notification.type} for user {user.id}")
            return False
        
        # Create email message
        subject = f"[EduMath AI] {notification.title}"
        
        # Create email body
        email_body = create_email_body(notification, user)
        
        # Send email
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=email_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@edumath-ai.com')
        )
        
        mail.send(msg)
        
        logger.info(f"Email notification sent to {user.email} for notification {notification_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email notification {notification_id}: {str(e)}")
        
        # Retry with exponential backoff
        try:
            self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email notification {notification_id}")
            return False


@celery.task(bind=True, max_retries=3)
def send_bulk_email_notifications(self, notification_ids: List[int]):
    """
    Send multiple email notifications in bulk.
    
    Args:
        notification_ids: List of notification IDs to send
    """
    try:
        success_count = 0
        failed_count = 0
        
        for notification_id in notification_ids:
            try:
                result = send_notification_email.apply(args=[notification_id])
                if result.get():
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error sending bulk email {notification_id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Bulk email completed: {success_count} success, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}
        
    except Exception as e:
        logger.error(f"Error in bulk email task: {str(e)}")
        return {'success': 0, 'failed': len(notification_ids)}


@celery.task
def send_welcome_email(user_id: str):
    """
    Send welcome email to new user.
    
    Args:
        user_id: ID of the new user
    """
    try:
        user = User.query.get(user_id)
        if not user or not user.email:
            logger.warning(f"User {user_id} not found or has no email for welcome email")
            return False
        
        subject = "Welcome to EduMath AI!"
        
        # Create welcome email body
        email_body = create_welcome_email_body(user)
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=email_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@edumath-ai.com')
        )
        
        mail.send(msg)
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {str(e)}")
        return False


@celery.task
def send_assignment_reminder_emails():
    """
    Send reminder emails for assignments due soon.
    This task should be run periodically (e.g., daily).
    """
    try:
        from app.services.notification import NotificationService
        
        # Get notifications that need to be sent for due assignments
        NotificationService.send_due_assignment_notifications()
        
        logger.info("Assignment reminder emails processed")
        return True
        
    except Exception as e:
        logger.error(f"Error sending assignment reminder emails: {str(e)}")
        return False


@celery.task
def send_weekly_progress_report(user_id: str):
    """
    Send weekly progress report to user.
    
    Args:
        user_id: ID of the user to send report to
    """
    try:
        user = User.query.get(user_id)
        if not user or not user.email:
            logger.warning(f"User {user_id} not found or has no email for progress report")
            return False
        
        # Check if user wants weekly reports
        user_settings = user.settings or {}
        notification_settings = user_settings.get('notifications', {})
        
        if not notification_settings.get('weekly_progress_report', True):
            logger.info(f"Weekly progress reports disabled for user {user.id}")
            return False
        
        # Get user's progress data
        from app.services.dashboard import DashboardService
        
        if user.role == 'student':
            dashboard_data = DashboardService.get_student_dashboard(user_id)
        elif user.role == 'professor':
            dashboard_data = DashboardService.get_professor_dashboard(user_id)
        else:
            logger.info(f"No progress report for role {user.role}")
            return False
        
        subject = "Your Weekly Progress Report - EduMath AI"
        
        # Create progress report email
        email_body = create_progress_report_email(user, dashboard_data)
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=email_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@edumath-ai.com')
        )
        
        mail.send(msg)
        
        logger.info(f"Weekly progress report sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending weekly progress report to user {user_id}: {str(e)}")
        return False


@celery.task
def cleanup_old_email_logs():
    """
    Clean up old email logs and temporary data.
    This task should be run periodically.
    """
    try:
        # This would clean up any email-related logs or temporary data
        # For now, we'll just log that the cleanup ran
        logger.info("Email logs cleanup completed")
        return True
        
    except Exception as e:
        logger.error(f"Error during email logs cleanup: {str(e)}")
        return False


def create_email_body(notification: Notification, user: User) -> str:
    """
    Create HTML email body for notification.
    
    Args:
        notification: Notification object
        user: User object
    
    Returns:
        HTML email body string
    """
    # Basic HTML template for notifications
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{notification.title}</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px; 
            }}
            .header {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 20px; 
                text-align: center; 
                border-radius: 5px 5px 0 0; 
            }}
            .content {{ 
                background-color: #f9f9f9; 
                padding: 20px; 
                border-radius: 0 0 5px 5px; 
            }}
            .footer {{ 
                text-align: center; 
                padding: 20px; 
                font-size: 12px; 
                color: #666; 
            }}
            .button {{ 
                display: inline-block; 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 10px 0; 
            }}
            .priority-high {{ border-left: 4px solid #f44336; }}
            .priority-medium {{ border-left: 4px solid #ff9800; }}
            .priority-low {{ border-left: 4px solid #2196f3; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>EduMath AI</h1>
        </div>
        <div class="content priority-{notification.priority}">
            <h2>{notification.title}</h2>
            <p>Hello {user.full_name},</p>
            <p>{notification.message}</p>
            
            <p><a href="{get_app_url()}" class="button">View in App</a></p>
            
            <hr>
            <p><small>
                This notification was sent on {notification.created_at.strftime('%B %d, %Y at %I:%M %p')}.
                <br>
                You can manage your notification preferences in your account settings.
            </small></p>
        </div>
        <div class="footer">
            <p>&copy; 2024 EduMath AI. All rights reserved.</p>
            <p>
                <a href="{get_app_url()}/settings/notifications">Notification Settings</a> | 
                <a href="{get_app_url()}/support">Support</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html_template


def create_welcome_email_body(user: User) -> str:
    """
    Create HTML email body for welcome email.
    
    Args:
        user: User object
    
    Returns:
        HTML email body string
    """
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to EduMath AI</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px; 
            }}
            .header {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 30px; 
                text-align: center; 
                border-radius: 5px 5px 0 0; 
            }}
            .content {{ 
                background-color: #f9f9f9; 
                padding: 30px; 
                border-radius: 0 0 5px 5px; 
            }}
            .footer {{ 
                text-align: center; 
                padding: 20px; 
                font-size: 12px; 
                color: #666; 
            }}
            .button {{ 
                display: inline-block; 
                background-color: #4CAF50; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 20px 0; 
                font-weight: bold; 
            }}
            .features {{ 
                list-style-type: none; 
                padding: 0; 
            }}
            .features li {{ 
                padding: 10px 0; 
                border-bottom: 1px solid #ddd; 
            }}
            .features li:before {{ 
                content: "✓ "; 
                color: #4CAF50; 
                font-weight: bold; 
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to EduMath AI!</h1>
            <p>Your AI-powered mathematics learning companion</p>
        </div>
        <div class="content">
            <h2>Hello {user.full_name}!</h2>
            
            <p>Welcome to EduMath AI, the revolutionary platform that makes learning mathematics engaging, interactive, and personalized just for you.</p>
            
            <h3>What you can do with EduMath AI:</h3>
            <ul class="features">
                <li>Practice math exercises tailored to your level</li>
                <li>Get instant AI-powered tutoring and explanations</li>
                <li>Track your progress with detailed analytics</li>
                <li>Join classes and collaborate with peers</li>
                <li>Receive personalized learning recommendations</li>
                <li>Access your studies from anywhere, anytime</li>
            </ul>
            
            <p>Ready to start your mathematical journey?</p>
            
            <div style="text-align: center;">
                <a href="{get_app_url()}/dashboard" class="button">Get Started Now</a>
            </div>
            
            <hr>
            
            <h3>Need Help?</h3>
            <p>Our support team is here to help you succeed:</p>
            <ul>
                <li><strong>Help Center:</strong> <a href="{get_app_url()}/help">View tutorials and guides</a></li>
                <li><strong>Support:</strong> <a href="{get_app_url()}/support">Contact our team</a></li>
                <li><strong>Community:</strong> Join our learning community</li>
            </ul>
            
            <p>Happy learning!</p>
            <p><strong>The EduMath AI Team</strong></p>
        </div>
        <div class="footer">
            <p>&copy; 2024 EduMath AI. All rights reserved.</p>
            <p>
                <a href="{get_app_url()}/settings/notifications">Notification Settings</a> | 
                <a href="{get_app_url()}/support">Support</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html_template


def create_progress_report_email(user: User, dashboard_data: Dict) -> str:
    """
    Create HTML email body for progress report.
    
    Args:
        user: User object
        dashboard_data: Dashboard data from service
    
    Returns:
        HTML email body string
    """
    quick_stats = dashboard_data.get('quick_stats', {})
    
    if user.role == 'student':
        stats_content = f"""
            <li><strong>Exercises Completed:</strong> {quick_stats.get('total_exercises_completed', 0)}</li>
            <li><strong>Average Score:</strong> {quick_stats.get('average_score', 0)}%</li>
            <li><strong>Current Streak:</strong> {quick_stats.get('current_streak', 0)} days</li>
            <li><strong>Classes Enrolled:</strong> {quick_stats.get('total_classes', 0)}</li>
        """
    else:  # professor
        stats_content = f"""
            <li><strong>Classes Teaching:</strong> {quick_stats.get('total_classes', 0)}</li>
            <li><strong>Total Students:</strong> {quick_stats.get('total_students', 0)}</li>
            <li><strong>Average Class Score:</strong> {quick_stats.get('average_class_score', 0)}%</li>
            <li><strong>Assignments Created:</strong> {quick_stats.get('total_assignments', 0)}</li>
        """
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Weekly Progress Report</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px; 
            }}
            .header {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 20px; 
                text-align: center; 
                border-radius: 5px 5px 0 0; 
            }}
            .content {{ 
                background-color: #f9f9f9; 
                padding: 20px; 
                border-radius: 0 0 5px 5px; 
            }}
            .stats {{ 
                background-color: white; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 15px 0; 
            }}
            .stats ul {{ 
                list-style-type: none; 
                padding: 0; 
            }}
            .stats li {{ 
                padding: 8px 0; 
                border-bottom: 1px solid #eee; 
            }}
            .button {{ 
                display: inline-block; 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 10px 0; 
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Weekly Progress Report</h1>
        </div>
        <div class="content">
            <h2>Hello {user.full_name}!</h2>
            
            <p>Here's your weekly progress summary from EduMath AI:</p>
            
            <div class="stats">
                <h3>📈 Your Week in Numbers:</h3>
                <ul>
                    {stats_content}
                </ul>
            </div>
            
            <p>Keep up the great work! Consistent practice is the key to mastering mathematics.</p>
            
            <div style="text-align: center;">
                <a href="{get_app_url()}/dashboard" class="button">View Full Dashboard</a>
            </div>
            
            <hr>
            
            <p><small>
                This weekly report is sent every Sunday. You can disable these emails in your notification settings.
            </small></p>
        </div>
    </body>
    </html>
    """
    
    return html_template


def get_app_url() -> str:
    """Get the application base URL."""
    return current_app.config.get('APP_URL', 'http://localhost:3000')


# Periodic task schedule (this would be configured in your Celery beat schedule)
@celery.periodic_task(run_every=60 * 60 * 24)  # Daily
def daily_tasks():
    """Run daily maintenance tasks."""
    try:
        # Send assignment reminders
        send_assignment_reminder_emails.delay()
        
        # Clean up old data
        cleanup_old_email_logs.delay()
        
        logger.info("Daily email tasks scheduled")
        
    except Exception as e:
        logger.error(f"Error in daily email tasks: {str(e)}")


@celery.periodic_task(run_every=60 * 60 * 24 * 7)  # Weekly on Sundays
def weekly_tasks():
    """Run weekly tasks."""
    try:
        # Send weekly progress reports to all users who have them enabled
        from app.models import User
        
        users = User.query.all()
        for user in users:
            user_settings = user.settings or {}
            notification_settings = user_settings.get('notifications', {})
            
            if notification_settings.get('weekly_progress_report', True):
                send_weekly_progress_report.delay(str(user.id))
        
        logger.info("Weekly progress reports scheduled")
        
    except Exception as e:
        logger.error(f"Error in weekly email tasks: {str(e)}")
