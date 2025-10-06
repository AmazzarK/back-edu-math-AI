"""
Notification service for handling various types of notifications.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
from app.extensions import db
from app.models import Notification, User
from app.services.base import BaseService
from app.utils.cache import cache_key, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)


class NotificationService(BaseService):
    """Service for managing notifications."""
    
    model = Notification
    
    # Notification types and their default settings
    NOTIFICATION_TYPES = {
        'exercise_assigned': {
            'title_template': 'New Exercise Assigned: {exercise_title}',
            'message_template': 'A new exercise "{exercise_title}" has been assigned in {class_name}.',
            'priority': 'medium',
            'email_enabled': True
        },
        'exercise_completed': {
            'title_template': 'Exercise Completed: {exercise_title}',
            'message_template': 'You have completed the exercise "{exercise_title}" with a score of {score}.',
            'priority': 'low',
            'email_enabled': False
        },
        'class_enrollment': {
            'title_template': 'Class Enrollment Update',
            'message_template': 'Your enrollment status in "{class_name}" has been updated.',
            'priority': 'medium',
            'email_enabled': True
        },
        'assignment_due': {
            'title_template': 'Assignment Due Soon: {exercise_title}',
            'message_template': 'The assignment "{exercise_title}" is due in {time_remaining}.',
            'priority': 'high',
            'email_enabled': True
        },
        'grade_posted': {
            'title_template': 'Grade Posted: {exercise_title}',
            'message_template': 'Your grade for "{exercise_title}" has been posted: {grade}.',
            'priority': 'medium',
            'email_enabled': True
        },
        'system_announcement': {
            'title_template': 'System Announcement',
            'message_template': '{message}',
            'priority': 'high',
            'email_enabled': True
        },
        'chat_message': {
            'title_template': 'New Chat Message',
            'message_template': 'You have a new message in your AI tutor chat.',
            'priority': 'low',
            'email_enabled': False
        },
        'file_upload': {
            'title_template': 'File Upload Complete',
            'message_template': 'Your file "{filename}" has been uploaded successfully.',
            'priority': 'low',
            'email_enabled': False
        }
    }
    
    @classmethod
    def create_notification(
        cls,
        user_id: str,
        notification_type: str,
        data: Dict[str, Any],
        title: Optional[str] = None,
        message: Optional[str] = None,
        priority: Optional[str] = None,
        send_email: Optional[bool] = None
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            data: Additional data for the notification
            title: Custom title (overrides template)
            message: Custom message (overrides template)
            priority: Notification priority (low, medium, high)
            send_email: Whether to send email notification
        
        Returns:
            Created notification object
        """
        try:
            # Get notification type configuration
            type_config = cls.NOTIFICATION_TYPES.get(notification_type, {})
            
            # Generate title and message from templates if not provided
            if not title and 'title_template' in type_config:
                try:
                    title = type_config['title_template'].format(**data)
                except KeyError as e:
                    logger.warning(f"Missing template variable for title: {e}")
                    title = type_config.get('title_template', 'Notification')
            
            if not message and 'message_template' in type_config:
                try:
                    message = type_config['message_template'].format(**data)
                except KeyError as e:
                    logger.warning(f"Missing template variable for message: {e}")
                    message = type_config.get('message_template', 'You have a new notification.')
            
            # Set defaults
            if not title:
                title = 'Notification'
            if not message:
                message = 'You have a new notification.'
            if not priority:
                priority = type_config.get('priority', 'medium')
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                priority=priority,
                data=data
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Schedule email if enabled
            if send_email or (send_email is None and type_config.get('email_enabled', False)):
                cls._schedule_email_notification(notification)
            
            logger.info(f"Notification created: {notification.id} for user {user_id}")
            return notification
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise
    
    @classmethod
    def get_user_notifications(
        cls,
        user_id: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Get paginated notifications for a user."""
        try:
            query = Notification.query.filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            if notification_type:
                query = query.filter(Notification.type == notification_type)
            
            query = query.order_by(desc(Notification.created_at))
            
            # Paginate
            paginated = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            notifications = [notif.to_dict() for notif in paginated.items]
            
            return {
                'notifications': notifications,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
                'unread_count': cls.get_unread_count(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def mark_as_read(cls, notification_id: int, user_id: str) -> bool:
        """Mark a notification as read."""
        try:
            notification = Notification.query.filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                raise ValueError("Notification not found")
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Notification marked as read: {notification_id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            raise
    
    @classmethod
    def mark_all_as_read(cls, user_id: str, notification_type: Optional[str] = None) -> int:
        """Mark all notifications as read for a user."""
        try:
            query = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            
            if notification_type:
                query = query.filter(Notification.type == notification_type)
            
            updated_count = query.update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            db.session.commit()
            
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def delete_notification(cls, notification_id: int, user_id: str) -> bool:
        """Delete a notification."""
        try:
            notification = Notification.query.filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                raise ValueError("Notification not found")
            
            db.session.delete(notification)
            db.session.commit()
            
            logger.info(f"Notification deleted: {notification_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            raise
    
    @classmethod
    def get_unread_count(cls, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        try:
            cache_key_name = cache_key('unread_notifications', user_id)
            cached_count = get_cached_result(cache_key_name)
            
            if cached_count is not None:
                return cached_count
            
            count = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
            
            # Cache for 5 minutes
            set_cached_result(cache_key_name, count, timeout=300)
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0
    
    @classmethod
    def get_notification_stats(cls, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        try:
            total_notifications = Notification.query.filter(
                Notification.user_id == user_id
            ).count()
            
            unread_notifications = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
            
            # Get counts by type
            type_counts = db.session.query(
                Notification.type,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id
            ).group_by(Notification.type).all()
            
            # Get counts by priority
            priority_counts = db.session.query(
                Notification.priority,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id
            ).group_by(Notification.priority).all()
            
            # Recent notifications (last 7 days)
            recent_count = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            return {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'read_notifications': total_notifications - unread_notifications,
                'recent_notifications': recent_count,
                'by_type': {type_name: count for type_name, count in type_counts},
                'by_priority': {priority: count for priority, count in priority_counts}
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def create_bulk_notifications(
        cls,
        user_ids: List[str],
        notification_type: str,
        data: Dict[str, Any],
        **kwargs
    ) -> List[Notification]:
        """Create notifications for multiple users."""
        try:
            notifications = []
            
            for user_id in user_ids:
                try:
                    notification = cls.create_notification(
                        user_id=user_id,
                        notification_type=notification_type,
                        data=data,
                        **kwargs
                    )
                    notifications.append(notification)
                except Exception as e:
                    logger.error(f"Error creating notification for user {user_id}: {str(e)}")
                    continue
            
            logger.info(f"Created {len(notifications)} bulk notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error creating bulk notifications: {str(e)}")
            raise
    
    @classmethod
    def cleanup_old_notifications(cls, days_old: int = 90) -> int:
        """Delete old notifications to keep database clean."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            deleted_count = Notification.query.filter(
                and_(
                    Notification.created_at < cutoff_date,
                    Notification.is_read == True
                )
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up old notifications: {str(e)}")
            raise
    
    @classmethod
    def get_due_assignment_notifications(cls) -> List[Dict[str, Any]]:
        """Get assignments that need due date notifications."""
        try:
            from app.models import ClassExerciseAssignment, ClassEnrollment
            
            # Find assignments due in 24 hours or 1 hour
            tomorrow = datetime.utcnow() + timedelta(hours=24)
            one_hour = datetime.utcnow() + timedelta(hours=1)
            
            # Get assignments due soon
            assignments = ClassExerciseAssignment.query.filter(
                and_(
                    ClassExerciseAssignment.due_date.isnot(None),
                    or_(
                        and_(
                            ClassExerciseAssignment.due_date <= tomorrow,
                            ClassExerciseAssignment.due_date > datetime.utcnow() + timedelta(hours=23)
                        ),
                        and_(
                            ClassExerciseAssignment.due_date <= one_hour,
                            ClassExerciseAssignment.due_date > datetime.utcnow()
                        )
                    )
                )
            ).all()
            
            notifications_to_create = []
            
            for assignment in assignments:
                # Get enrolled students
                enrollments = ClassEnrollment.query.filter(
                    and_(
                        ClassEnrollment.class_id == assignment.class_id,
                        ClassEnrollment.enrollment_status == 'active'
                    )
                ).all()
                
                time_remaining = assignment.due_date - datetime.utcnow()
                
                if time_remaining <= timedelta(hours=1):
                    time_str = "1 hour"
                else:
                    time_str = "24 hours"
                
                for enrollment in enrollments:
                    # Check if we've already sent this notification
                    existing_notification = Notification.query.filter(
                        and_(
                            Notification.user_id == enrollment.student_id,
                            Notification.type == 'assignment_due',
                            Notification.data['assignment_id'].astext == str(assignment.id),
                            Notification.created_at >= datetime.utcnow() - timedelta(hours=2)
                        )
                    ).first()
                    
                    if not existing_notification:
                        notifications_to_create.append({
                            'user_id': enrollment.student_id,
                            'assignment': assignment,
                            'time_remaining': time_str
                        })
            
            return notifications_to_create
            
        except Exception as e:
            logger.error(f"Error getting due assignment notifications: {str(e)}")
            return []
    
    @classmethod
    def send_due_assignment_notifications(cls):
        """Send notifications for assignments due soon."""
        try:
            notifications_to_create = cls.get_due_assignment_notifications()
            
            for notif_data in notifications_to_create:
                cls.create_notification(
                    user_id=notif_data['user_id'],
                    notification_type='assignment_due',
                    data={
                        'assignment_id': notif_data['assignment'].id,
                        'exercise_id': notif_data['assignment'].exercise_id,
                        'exercise_title': notif_data['assignment'].exercise.title if notif_data['assignment'].exercise else 'Unknown',
                        'class_id': notif_data['assignment'].class_id,
                        'time_remaining': notif_data['time_remaining'],
                        'due_date': notif_data['assignment'].due_date.isoformat()
                    },
                    send_email=True
                )
            
            logger.info(f"Sent {len(notifications_to_create)} due assignment notifications")
            
        except Exception as e:
            logger.error(f"Error sending due assignment notifications: {str(e)}")
    
    @classmethod
    def _schedule_email_notification(cls, notification: Notification):
        """Schedule email notification to be sent asynchronously."""
        try:
            # Import here to avoid circular imports
            from app.tasks.email_tasks import send_notification_email
            
            # Get user email
            user = User.query.get(notification.user_id)
            if not user or not user.email:
                logger.warning(f"Cannot send email notification - user not found or no email: {notification.user_id}")
                return
            
            # Schedule email task (this would use Celery in production)
            # For now, we'll just log that the email would be sent
            logger.info(f"Email notification scheduled for {user.email}: {notification.title}")
            
            # In a real implementation, you would call:
            # send_notification_email.delay(notification.id)
            
        except Exception as e:
            logger.error(f"Error scheduling email notification: {str(e)}")
    
    @classmethod
    def update_notification_preferences(cls, user_id: str, preferences: Dict[str, bool]) -> bool:
        """Update user's notification preferences."""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Update user's notification preferences
            current_settings = user.settings or {}
            current_settings['notifications'] = preferences
            user.settings = current_settings
            
            db.session.commit()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating notification preferences for user {user_id}: {str(e)}")
            raise
