"""
Notification API endpoints for managing user notifications.
"""
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
import logging

from app.services.notification import NotificationService
from app.models import User
from app.utils.decorators import handle_exceptions, role_required

logger = logging.getLogger(__name__)


class NotificationPreferencesSchema(Schema):
    """Schema for notification preferences validation."""
    email_notifications = fields.Bool(required=False)
    exercise_assigned = fields.Bool(required=False)
    exercise_completed = fields.Bool(required=False)
    class_enrollment = fields.Bool(required=False)
    assignment_due = fields.Bool(required=False)
    grade_posted = fields.Bool(required=False)
    system_announcement = fields.Bool(required=False)
    chat_message = fields.Bool(required=False)
    file_upload = fields.Bool(required=False)


class NotificationResource(Resource):
    """Resource for managing user notifications."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get user's notifications."""
        try:
            user_id = get_jwt_identity()
            
            # Get query parameters
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            notification_type = request.args.get('type')
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 50)
            
            # Get notifications
            notifications_data = NotificationService.get_user_notifications(
                user_id=user_id,
                unread_only=unread_only,
                notification_type=notification_type,
                page=page,
                per_page=per_page
            )
            
            return jsonify({
                'success': True,
                'data': notifications_data
            })
            
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve notifications'
            }), 500


class NotificationDetailResource(Resource):
    """Resource for individual notification operations."""
    
    @jwt_required()
    @handle_exceptions
    def put(self, notification_id):
        """Mark notification as read."""
        try:
            user_id = get_jwt_identity()
            
            success = NotificationService.mark_as_read(notification_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Notification marked as read'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to mark notification as read'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update notification'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    def delete(self, notification_id):
        """Delete a notification."""
        try:
            user_id = get_jwt_identity()
            
            success = NotificationService.delete_notification(notification_id, user_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Notification deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete notification'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to delete notification'
            }), 500


class NotificationBulkResource(Resource):
    """Resource for bulk notification operations."""
    
    @jwt_required()
    @handle_exceptions
    def put(self):
        """Mark all notifications as read."""
        try:
            user_id = get_jwt_identity()
            
            # Get optional notification type filter
            notification_type = request.args.get('type')
            
            updated_count = NotificationService.mark_all_as_read(
                user_id=user_id,
                notification_type=notification_type
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'updated_count': updated_count
                },
                'message': f'Marked {updated_count} notifications as read'
            })
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to mark notifications as read'
            }), 500


class NotificationStatsResource(Resource):
    """Resource for notification statistics."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get notification statistics for user."""
        try:
            user_id = get_jwt_identity()
            
            stats = NotificationService.get_notification_stats(user_id)
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get notification statistics'
            }), 500


class NotificationUnreadCountResource(Resource):
    """Resource for getting unread notification count."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get count of unread notifications."""
        try:
            user_id = get_jwt_identity()
            
            unread_count = NotificationService.get_unread_count(user_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'unread_count': unread_count
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get unread count'
            }), 500


class NotificationPreferencesResource(Resource):
    """Resource for managing notification preferences."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get user's notification preferences."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # Get current preferences from user settings
            preferences = user.settings.get('notifications', {}) if user.settings else {}
            
            # Set defaults for missing preferences
            default_preferences = {
                'email_notifications': True,
                'exercise_assigned': True,
                'exercise_completed': False,
                'class_enrollment': True,
                'assignment_due': True,
                'grade_posted': True,
                'system_announcement': True,
                'chat_message': False,
                'file_upload': False
            }
            
            # Merge with defaults
            for key, default_value in default_preferences.items():
                if key not in preferences:
                    preferences[key] = default_value
            
            return jsonify({
                'success': True,
                'data': {
                    'preferences': preferences
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting notification preferences: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get notification preferences'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    def put(self):
        """Update user's notification preferences."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            # Validate preferences
            schema = NotificationPreferencesSchema()
            try:
                validated_data = schema.load(data)
            except ValidationError as e:
                return jsonify({
                    'success': False,
                    'message': 'Invalid preference data',
                    'errors': e.messages
                }), 400
            
            # Update preferences
            success = NotificationService.update_notification_preferences(
                user_id=user_id,
                preferences=validated_data
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Notification preferences updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to update notification preferences'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except Exception as e:
            logger.error(f"Error updating notification preferences: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update notification preferences'
            }), 500


class NotificationAdminResource(Resource):
    """Resource for admin notification operations."""
    
    @jwt_required()
    @role_required('admin')
    @handle_exceptions
    def post(self):
        """Create system-wide notification (admin only)."""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Message is required'
                }), 400
            
            title = data.get('title', 'System Announcement')
            message = data['message']
            target_roles = data.get('target_roles', ['student', 'professor'])
            send_email = data.get('send_email', True)
            
            # Get target users
            from app.models import User
            target_users = User.query.filter(User.role.in_(target_roles)).all()
            user_ids = [str(user.id) for user in target_users]
            
            # Create bulk notifications
            notifications = NotificationService.create_bulk_notifications(
                user_ids=user_ids,
                notification_type='system_announcement',
                data={'message': message},
                title=title,
                message=message,
                send_email=send_email
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'notifications_created': len(notifications),
                    'target_users': len(user_ids)
                },
                'message': f'System notification sent to {len(notifications)} users'
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating system notification: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to create system notification'
            }), 500
    
    @jwt_required()
    @role_required('admin')
    @handle_exceptions
    def delete(self):
        """Clean up old notifications (admin only)."""
        try:
            days_old = request.args.get('days_old', 90, type=int)
            
            # Limit to reasonable values
            days_old = max(7, min(days_old, 365))
            
            deleted_count = NotificationService.cleanup_old_notifications(days_old)
            
            return jsonify({
                'success': True,
                'data': {
                    'deleted_count': deleted_count,
                    'days_old': days_old
                },
                'message': f'Cleaned up {deleted_count} old notifications'
            })
            
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to clean up notifications'
            }), 500


class NotificationTypesResource(Resource):
    """Resource for getting available notification types."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get available notification types and their settings."""
        try:
            notification_types = {}
            
            for type_name, config in NotificationService.NOTIFICATION_TYPES.items():
                notification_types[type_name] = {
                    'title_template': config.get('title_template', ''),
                    'message_template': config.get('message_template', ''),
                    'priority': config.get('priority', 'medium'),
                    'email_enabled': config.get('email_enabled', False)
                }
            
            return jsonify({
                'success': True,
                'data': {
                    'notification_types': notification_types
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting notification types: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get notification types'
            }), 500


# Register routes
def register_notification_routes(api):
    """Register notification API routes."""
    api.add_resource(NotificationResource, '/api/notifications')
    api.add_resource(NotificationDetailResource, '/api/notifications/<int:notification_id>')
    api.add_resource(NotificationBulkResource, '/api/notifications/bulk')
    api.add_resource(NotificationStatsResource, '/api/notifications/stats')
    api.add_resource(NotificationUnreadCountResource, '/api/notifications/unread-count')
    api.add_resource(NotificationPreferencesResource, '/api/notifications/preferences')
    api.add_resource(NotificationAdminResource, '/api/notifications/admin')
    api.add_resource(NotificationTypesResource, '/api/notifications/types')
