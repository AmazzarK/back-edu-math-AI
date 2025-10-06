"""
Dashboard service for aggregating data and analytics.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import (
    User, Exercise, Progress, Class, ClassEnrollment, 
    ClassExerciseAssignment, ChatConversation, Notification, UploadedFile
)
from app.services.base import BaseService
from app.utils.cache import cache_key, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)


class DashboardService(BaseService):
    """Service for generating dashboard data and analytics."""
    
    @classmethod
    def get_student_dashboard(cls, student_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a student."""
        try:
            cache_key_name = cache_key('student_dashboard', student_id)
            cached_data = get_cached_result(cache_key_name)
            
            if cached_data:
                return cached_data
            
            # Basic student info
            student = User.query.get(student_id)
            if not student:
                raise ValueError("Student not found")
            
            # Recent progress (last 7 days)
            recent_progress = cls._get_recent_progress(student_id, days=7)
            
            # Class enrollments
            enrolled_classes = cls._get_student_classes(student_id)
            
            # Pending assignments
            pending_assignments = cls._get_pending_assignments(student_id)
            
            # Overall statistics
            overall_stats = cls._get_student_overall_stats(student_id)
            
            # Recent chat activity
            recent_chats = cls._get_recent_chat_activity(student_id)
            
            # Achievements and streaks
            achievements = cls._get_student_achievements(student_id)
            
            # Upcoming deadlines
            upcoming_deadlines = cls._get_upcoming_deadlines(student_id)
            
            dashboard_data = {
                'student_info': {
                    'id': student.id,
                    'name': student.full_name,
                    'email': student.email,
                    'joined_date': student.created_at.isoformat(),
                    'last_active': recent_progress[0]['completed_at'] if recent_progress else None
                },
                'recent_progress': recent_progress,
                'enrolled_classes': enrolled_classes,
                'pending_assignments': pending_assignments,
                'overall_stats': overall_stats,
                'recent_chats': recent_chats,
                'achievements': achievements,
                'upcoming_deadlines': upcoming_deadlines,
                'quick_stats': {
                    'total_exercises_completed': overall_stats['total_completed'],
                    'average_score': overall_stats['average_score'],
                    'current_streak': achievements['current_streak'],
                    'total_classes': len(enrolled_classes),
                    'pending_assignments': len(pending_assignments)
                }
            }
            
            # Cache for 10 minutes
            set_cached_result(cache_key_name, dashboard_data, timeout=600)
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting student dashboard for {student_id}: {str(e)}")
            raise
    
    @classmethod
    def get_professor_dashboard(cls, professor_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a professor."""
        try:
            cache_key_name = cache_key('professor_dashboard', professor_id)
            cached_data = get_cached_result(cache_key_name)
            
            if cached_data:
                return cached_data
            
            # Basic professor info
            professor = User.query.get(professor_id)
            if not professor:
                raise ValueError("Professor not found")
            
            # Classes taught
            classes_taught = cls._get_professor_classes(professor_id)
            
            # Recent student activity across all classes
            recent_activity = cls._get_professor_recent_activity(professor_id)
            
            # Overall teaching statistics
            teaching_stats = cls._get_professor_teaching_stats(professor_id)
            
            # Class performance analytics
            class_analytics = cls._get_class_performance_analytics(professor_id)
            
            # Recent assignments
            recent_assignments = cls._get_professor_recent_assignments(professor_id)
            
            # Student performance insights
            student_insights = cls._get_student_performance_insights(professor_id)
            
            dashboard_data = {
                'professor_info': {
                    'id': professor.id,
                    'name': professor.full_name,
                    'email': professor.email,
                    'total_classes': len(classes_taught),
                    'total_students': teaching_stats['total_students']
                },
                'classes_taught': classes_taught,
                'recent_activity': recent_activity,
                'teaching_stats': teaching_stats,
                'class_analytics': class_analytics,
                'recent_assignments': recent_assignments,
                'student_insights': student_insights,
                'quick_stats': {
                    'total_classes': teaching_stats['total_classes'],
                    'total_students': teaching_stats['total_students'],
                    'average_class_score': teaching_stats['average_class_score'],
                    'total_assignments': teaching_stats['total_assignments'],
                    'recent_submissions': len(recent_activity)
                }
            }
            
            # Cache for 15 minutes
            set_cached_result(cache_key_name, dashboard_data, timeout=900)
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting professor dashboard for {professor_id}: {str(e)}")
            raise
    
    @classmethod
    def get_admin_dashboard(cls) -> Dict[str, Any]:
        """Get comprehensive dashboard data for administrators."""
        try:
            cache_key_name = cache_key('admin_dashboard')
            cached_data = get_cached_result(cache_key_name)
            
            if cached_data:
                return cached_data
            
            # Platform-wide statistics
            platform_stats = cls._get_platform_statistics()
            
            # User analytics
            user_analytics = cls._get_user_analytics()
            
            # Activity trends
            activity_trends = cls._get_activity_trends()
            
            # System health metrics
            system_health = cls._get_system_health_metrics()
            
            # Popular content
            popular_content = cls._get_popular_content()
            
            # Recent registrations
            recent_registrations = cls._get_recent_registrations()
            
            dashboard_data = {
                'platform_stats': platform_stats,
                'user_analytics': user_analytics,
                'activity_trends': activity_trends,
                'system_health': system_health,
                'popular_content': popular_content,
                'recent_registrations': recent_registrations,
                'quick_stats': {
                    'total_users': platform_stats['total_users'],
                    'total_exercises': platform_stats['total_exercises'],
                    'total_classes': platform_stats['total_classes'],
                    'daily_active_users': user_analytics['daily_active_users'],
                    'completion_rate': platform_stats['completion_rate']
                }
            }
            
            # Cache for 30 minutes
            set_cached_result(cache_key_name, dashboard_data, timeout=1800)
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting admin dashboard: {str(e)}")
            raise
    
    @classmethod
    def _get_recent_progress(cls, student_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent progress for a student."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            progress_items = Progress.query.filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.updated_at >= cutoff_date
                )
            ).options(
                joinedload(Progress.exercise)
            ).order_by(desc(Progress.updated_at)).limit(10).all()
            
            return [
                {
                    'id': progress.id,
                    'exercise_title': progress.exercise.title if progress.exercise else 'Unknown',
                    'exercise_id': progress.exercise_id,
                    'status': progress.status,
                    'score': progress.score,
                    'time_spent': progress.time_spent,
                    'completed_at': progress.updated_at.isoformat(),
                    'attempts': progress.attempts
                }
                for progress in progress_items
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent progress for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_student_classes(cls, student_id: str) -> List[Dict[str, Any]]:
        """Get classes for a student."""
        try:
            enrollments = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.student_id == student_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).options(
                joinedload(ClassEnrollment.class_obj),
                joinedload(ClassEnrollment.class_obj.professor)
            ).all()
            
            classes = []
            for enrollment in enrollments:
                class_obj = enrollment.class_obj
                if class_obj and class_obj.is_active:
                    # Get assignment stats for this class
                    total_assignments = ClassExerciseAssignment.query.filter(
                        ClassExerciseAssignment.class_id == class_obj.id
                    ).count()
                    
                    completed_assignments = db.session.query(Progress).join(
                        ClassExerciseAssignment,
                        Progress.exercise_id == ClassExerciseAssignment.exercise_id
                    ).filter(
                        and_(
                            ClassExerciseAssignment.class_id == class_obj.id,
                            Progress.student_id == student_id,
                            Progress.status == 'completed'
                        )
                    ).count()
                    
                    classes.append({
                        'id': class_obj.id,
                        'name': class_obj.name,
                        'subject': class_obj.subject,
                        'professor': class_obj.professor.full_name if class_obj.professor else 'Unknown',
                        'class_code': class_obj.class_code,
                        'total_assignments': total_assignments,
                        'completed_assignments': completed_assignments,
                        'completion_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0,
                        'enrolled_at': enrollment.enrolled_at.isoformat()
                    })
            
            return classes
            
        except Exception as e:
            logger.error(f"Error getting student classes for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_pending_assignments(cls, student_id: str) -> List[Dict[str, Any]]:
        """Get pending assignments for a student."""
        try:
            # Get all assignments for classes the student is enrolled in
            assignments = db.session.query(ClassExerciseAssignment).join(
                ClassEnrollment,
                ClassExerciseAssignment.class_id == ClassEnrollment.class_id
            ).filter(
                and_(
                    ClassEnrollment.student_id == student_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).options(
                joinedload(ClassExerciseAssignment.exercise),
                joinedload(ClassExerciseAssignment.class_obj)
            ).all()
            
            pending = []
            for assignment in assignments:
                # Check if student has completed this exercise
                progress = Progress.query.filter(
                    and_(
                        Progress.student_id == student_id,
                        Progress.exercise_id == assignment.exercise_id,
                        Progress.status == 'completed'
                    )
                ).first()
                
                if not progress:  # Not completed yet
                    pending.append({
                        'assignment_id': assignment.id,
                        'exercise_id': assignment.exercise_id,
                        'exercise_title': assignment.exercise.title if assignment.exercise else 'Unknown',
                        'class_name': assignment.class_obj.name if assignment.class_obj else 'Unknown',
                        'class_id': assignment.class_id,
                        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                        'is_overdue': assignment.due_date < datetime.utcnow() if assignment.due_date else False,
                        'assigned_date': assignment.assigned_at.isoformat(),
                        'is_mandatory': assignment.is_mandatory
                    })
            
            # Sort by due date (overdue first, then by due date)
            pending.sort(key=lambda x: (
                x['due_date'] is None,  # None dates go last
                x['due_date'] if x['due_date'] else '9999-12-31'
            ))
            
            return pending
            
        except Exception as e:
            logger.error(f"Error getting pending assignments for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_student_overall_stats(cls, student_id: str) -> Dict[str, Any]:
        """Get overall statistics for a student."""
        try:
            # Total exercises attempted and completed
            total_attempted = Progress.query.filter(
                Progress.student_id == student_id
            ).count()
            
            total_completed = Progress.query.filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed'
                )
            ).count()
            
            # Average score
            avg_score = db.session.query(func.avg(Progress.score)).filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed',
                    Progress.score.isnot(None)
                )
            ).scalar()
            
            # Total time spent
            total_time = db.session.query(func.sum(Progress.time_spent)).filter(
                Progress.student_id == student_id
            ).scalar()
            
            # Best score
            best_score = db.session.query(func.max(Progress.score)).filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed'
                )
            ).scalar()
            
            return {
                'total_attempted': total_attempted,
                'total_completed': total_completed,
                'completion_rate': (total_completed / total_attempted * 100) if total_attempted > 0 else 0,
                'average_score': round(avg_score, 2) if avg_score else 0,
                'best_score': best_score or 0,
                'total_time_spent': total_time or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting overall stats for {student_id}: {str(e)}")
            return {}
    
    @classmethod
    def _get_recent_chat_activity(cls, student_id: str) -> List[Dict[str, Any]]:
        """Get recent chat activity for a student."""
        try:
            conversations = ChatConversation.query.filter(
                ChatConversation.user_id == student_id
            ).order_by(desc(ChatConversation.updated_at)).limit(5).all()
            
            return [
                {
                    'id': conv.id,
                    'title': conv.title,
                    'message_count': len(conv.messages) if hasattr(conv, 'messages') else 0,
                    'last_activity': conv.updated_at.isoformat(),
                    'context_type': conv.context_type
                }
                for conv in conversations
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent chat activity for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_student_achievements(cls, student_id: str) -> Dict[str, Any]:
        """Get achievements and streaks for a student."""
        try:
            # Calculate current streak (consecutive days with completed exercises)
            current_streak = cls._calculate_streak(student_id)
            
            # Longest streak
            longest_streak = cls._calculate_longest_streak(student_id)
            
            # Other achievements
            achievements = {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'badges': cls._get_student_badges(student_id)
            }
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error getting achievements for {student_id}: {str(e)}")
            return {'current_streak': 0, 'longest_streak': 0, 'badges': []}
    
    @classmethod
    def _get_upcoming_deadlines(cls, student_id: str) -> List[Dict[str, Any]]:
        """Get upcoming assignment deadlines."""
        try:
            upcoming = []
            pending_assignments = cls._get_pending_assignments(student_id)
            
            for assignment in pending_assignments:
                if assignment['due_date']:
                    due_date = datetime.fromisoformat(assignment['due_date'].replace('Z', '+00:00'))
                    days_until_due = (due_date - datetime.utcnow()).days
                    
                    if days_until_due <= 7:  # Next 7 days
                        upcoming.append({
                            **assignment,
                            'days_until_due': days_until_due
                        })
            
            return sorted(upcoming, key=lambda x: x['due_date'])
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_professor_classes(cls, professor_id: str) -> List[Dict[str, Any]]:
        """Get classes taught by a professor."""
        try:
            classes = Class.query.filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).all()
            
            class_data = []
            for class_obj in classes:
                # Get enrollment count
                enrollment_count = ClassEnrollment.query.filter(
                    and_(
                        ClassEnrollment.class_id == class_obj.id,
                        ClassEnrollment.enrollment_status == 'active'
                    )
                ).count()
                
                # Get assignment count
                assignment_count = ClassExerciseAssignment.query.filter(
                    ClassExerciseAssignment.class_id == class_obj.id
                ).count()
                
                # Get average class performance
                avg_performance = cls._get_class_average_performance(class_obj.id)
                
                class_data.append({
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'subject': class_obj.subject,
                    'class_code': class_obj.class_code,
                    'enrollment_count': enrollment_count,
                    'max_students': class_obj.max_students,
                    'assignment_count': assignment_count,
                    'average_performance': avg_performance,
                    'created_at': class_obj.created_at.isoformat()
                })
            
            return class_data
            
        except Exception as e:
            logger.error(f"Error getting professor classes for {professor_id}: {str(e)}")
            return []
    
    @classmethod
    def _calculate_streak(cls, student_id: str) -> int:
        """Calculate current consecutive day streak."""
        try:
            # Get dates with completed exercises in reverse chronological order
            completed_dates = db.session.query(
                func.date(Progress.updated_at).label('date')
            ).filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed'
                )
            ).distinct().order_by(desc('date')).all()
            
            if not completed_dates:
                return 0
            
            # Count consecutive days starting from today
            streak = 0
            current_date = datetime.utcnow().date()
            
            for date_row in completed_dates:
                if date_row.date == current_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                elif date_row.date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = date_row.date - timedelta(days=1)
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating streak for {student_id}: {str(e)}")
            return 0
    
    @classmethod
    def _calculate_longest_streak(cls, student_id: str) -> int:
        """Calculate longest consecutive day streak ever achieved."""
        try:
            # This is a simplified version - in production you might want to cache this
            # Get all unique dates with completions
            completed_dates = db.session.query(
                func.date(Progress.updated_at).label('date')
            ).filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed'
                )
            ).distinct().order_by('date').all()
            
            if not completed_dates:
                return 0
            
            longest_streak = 1
            current_streak = 1
            
            for i in range(1, len(completed_dates)):
                current_date = completed_dates[i].date
                prev_date = completed_dates[i-1].date
                
                if current_date == prev_date + timedelta(days=1):
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 1
            
            return longest_streak
            
        except Exception as e:
            logger.error(f"Error calculating longest streak for {student_id}: {str(e)}")
            return 0
    
    @classmethod
    def _get_student_badges(cls, student_id: str) -> List[Dict[str, Any]]:
        """Get badges/achievements for a student."""
        badges = []
        
        try:
            # Get completion stats
            stats = cls._get_student_overall_stats(student_id)
            
            # First completion badge
            if stats['total_completed'] >= 1:
                badges.append({
                    'name': 'First Steps',
                    'description': 'Completed your first exercise',
                    'icon': '🎯',
                    'earned_at': 'Recently'
                })
            
            # High achiever badges
            if stats['average_score'] >= 90:
                badges.append({
                    'name': 'High Achiever',
                    'description': 'Maintain 90%+ average score',
                    'icon': '⭐',
                    'earned_at': 'Recently'
                })
            
            # Volume badges
            if stats['total_completed'] >= 10:
                badges.append({
                    'name': 'Dedicated Learner',
                    'description': 'Completed 10+ exercises',
                    'icon': '📚',
                    'earned_at': 'Recently'
                })
            
            if stats['total_completed'] >= 50:
                badges.append({
                    'name': 'Math Champion',
                    'description': 'Completed 50+ exercises',
                    'icon': '🏆',
                    'earned_at': 'Recently'
                })
            
            return badges
            
        except Exception as e:
            logger.error(f"Error getting badges for {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_platform_statistics(cls) -> Dict[str, Any]:
        """Get platform-wide statistics."""
        try:
            total_users = User.query.count()
            total_students = User.query.filter(User.role == 'student').count()
            total_professors = User.query.filter(User.role == 'professor').count()
            total_exercises = Exercise.query.count()
            total_classes = Class.query.filter(Class.is_active == True).count()
            total_progress = Progress.query.count()
            total_completed = Progress.query.filter(Progress.status == 'completed').count()
            
            # Completion rate
            completion_rate = (total_completed / total_progress * 100) if total_progress > 0 else 0
            
            # Average score across platform
            avg_score = db.session.query(func.avg(Progress.score)).filter(
                and_(
                    Progress.status == 'completed',
                    Progress.score.isnot(None)
                )
            ).scalar()
            
            return {
                'total_users': total_users,
                'total_students': total_students,
                'total_professors': total_professors,
                'total_exercises': total_exercises,
                'total_classes': total_classes,
                'total_progress_records': total_progress,
                'total_completed_exercises': total_completed,
                'completion_rate': round(completion_rate, 2),
                'platform_average_score': round(avg_score, 2) if avg_score else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting platform statistics: {str(e)}")
            return {}
    
    @classmethod
    def _get_user_analytics(cls) -> Dict[str, Any]:
        """Get user analytics and activity patterns."""
        try:
            # Daily active users (last 24 hours)
            daily_active = User.query.filter(
                User.last_login >= datetime.utcnow() - timedelta(days=1)
            ).count()
            
            # Weekly active users
            weekly_active = User.query.filter(
                User.last_login >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Monthly active users
            monthly_active = User.query.filter(
                User.last_login >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            # New registrations this week
            new_users_week = User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'daily_active_users': daily_active,
                'weekly_active_users': weekly_active,
                'monthly_active_users': monthly_active,
                'new_users_this_week': new_users_week
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {}
    
    @classmethod
    def _get_activity_trends(cls) -> Dict[str, Any]:
        """Get activity trends over time."""
        try:
            # Exercise completions per day (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            daily_completions = db.session.query(
                func.date(Progress.updated_at).label('date'),
                func.count(Progress.id).label('count')
            ).filter(
                and_(
                    Progress.status == 'completed',
                    Progress.updated_at >= thirty_days_ago
                )
            ).group_by(func.date(Progress.updated_at)).all()
            
            # User registrations per day (last 30 days)
            daily_registrations = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= thirty_days_ago
            ).group_by(func.date(User.created_at)).all()
            
            return {
                'daily_completions': [
                    {'date': row.date.isoformat(), 'count': row.count}
                    for row in daily_completions
                ],
                'daily_registrations': [
                    {'date': row.date.isoformat(), 'count': row.count}
                    for row in daily_registrations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting activity trends: {str(e)}")
            return {}
    
    @classmethod
    def _get_system_health_metrics(cls) -> Dict[str, Any]:
        """Get system health and performance metrics."""
        try:
            # Database health indicators
            total_notifications = Notification.query.count()
            unread_notifications = Notification.query.filter(
                Notification.is_read == False
            ).count()
            
            total_files = UploadedFile.query.count()
            total_storage_size = db.session.query(
                func.sum(UploadedFile.file_size)
            ).scalar() or 0
            
            # Chat activity
            total_conversations = ChatConversation.query.count()
            active_conversations = ChatConversation.query.filter(
                ChatConversation.updated_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'database_health': 'healthy',  # Could add actual health checks
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'total_files': total_files,
                'total_storage_mb': round(total_storage_size / (1024 * 1024), 2),
                'total_conversations': total_conversations,
                'active_conversations_week': active_conversations
            }
            
        except Exception as e:
            logger.error(f"Error getting system health metrics: {str(e)}")
            return {}
    
    @classmethod
    def _get_popular_content(cls) -> Dict[str, Any]:
        """Get popular exercises and content."""
        try:
            # Most attempted exercises
            popular_exercises = db.session.query(
                Exercise.id,
                Exercise.title,
                func.count(Progress.id).label('attempt_count')
            ).join(Progress).group_by(
                Exercise.id, Exercise.title
            ).order_by(desc('attempt_count')).limit(10).all()
            
            # Highest rated exercises (by average score)
            highest_rated = db.session.query(
                Exercise.id,
                Exercise.title,
                func.avg(Progress.score).label('avg_score'),
                func.count(Progress.id).label('completion_count')
            ).join(Progress).filter(
                Progress.status == 'completed'
            ).group_by(
                Exercise.id, Exercise.title
            ).having(
                func.count(Progress.id) >= 5  # At least 5 completions
            ).order_by(desc('avg_score')).limit(10).all()
            
            return {
                'most_attempted': [
                    {
                        'exercise_id': row.id,
                        'title': row.title,
                        'attempt_count': row.attempt_count
                    }
                    for row in popular_exercises
                ],
                'highest_rated': [
                    {
                        'exercise_id': row.id,
                        'title': row.title,
                        'average_score': round(row.avg_score, 2),
                        'completion_count': row.completion_count
                    }
                    for row in highest_rated
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting popular content: {str(e)}")
            return {}
    
    @classmethod
    def _get_recent_registrations(cls) -> List[Dict[str, Any]]:
        """Get recent user registrations."""
        try:
            recent_users = User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(desc(User.created_at)).limit(10).all()
            
            return [
                {
                    'id': user.id,
                    'name': user.full_name,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat()
                }
                for user in recent_users
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent registrations: {str(e)}")
            return []
    
    @classmethod
    def _get_professor_recent_activity(cls, professor_id: str) -> List[Dict[str, Any]]:
        """Get recent student activity across professor's classes."""
        try:
            # Get all classes taught by professor
            class_ids = db.session.query(Class.id).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).subquery()
            
            # Get recent progress from students in those classes
            recent_activity = db.session.query(Progress).join(
                ClassEnrollment,
                Progress.student_id == ClassEnrollment.student_id
            ).filter(
                and_(
                    ClassEnrollment.class_id.in_(class_ids),
                    ClassEnrollment.enrollment_status == 'active',
                    Progress.updated_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).options(
                joinedload(Progress.student),
                joinedload(Progress.exercise)
            ).order_by(desc(Progress.updated_at)).limit(20).all()
            
            return [
                {
                    'student_name': progress.student.full_name if progress.student else 'Unknown',
                    'exercise_title': progress.exercise.title if progress.exercise else 'Unknown',
                    'status': progress.status,
                    'score': progress.score,
                    'completed_at': progress.updated_at.isoformat()
                }
                for progress in recent_activity
            ]
            
        except Exception as e:
            logger.error(f"Error getting professor recent activity for {professor_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_professor_teaching_stats(cls, professor_id: str) -> Dict[str, Any]:
        """Get overall teaching statistics for a professor."""
        try:
            # Count classes
            total_classes = Class.query.filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).count()
            
            # Count total students across all classes
            total_students = db.session.query(func.count(func.distinct(ClassEnrollment.student_id))).join(
                Class
            ).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).scalar()
            
            # Count total assignments
            total_assignments = db.session.query(func.count(ClassExerciseAssignment.id)).join(
                Class
            ).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).scalar()
            
            # Calculate average class score
            avg_class_score = cls._get_professor_average_class_score(professor_id)
            
            return {
                'total_classes': total_classes,
                'total_students': total_students or 0,
                'total_assignments': total_assignments or 0,
                'average_class_score': avg_class_score
            }
            
        except Exception as e:
            logger.error(f"Error getting professor teaching stats for {professor_id}: {str(e)}")
            return {}
    
    @classmethod
    def _get_class_performance_analytics(cls, professor_id: str) -> List[Dict[str, Any]]:
        """Get performance analytics for each class."""
        try:
            classes = Class.query.filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).all()
            
            analytics = []
            for class_obj in classes:
                class_analytics = cls._get_single_class_analytics(class_obj.id)
                class_analytics['class_name'] = class_obj.name
                class_analytics['class_id'] = class_obj.id
                analytics.append(class_analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting class performance analytics for {professor_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_professor_recent_assignments(cls, professor_id: str) -> List[Dict[str, Any]]:
        """Get recent assignments created by professor."""
        try:
            assignments = ClassExerciseAssignment.query.join(Class).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).options(
                joinedload(ClassExerciseAssignment.exercise),
                joinedload(ClassExerciseAssignment.class_obj)
            ).order_by(desc(ClassExerciseAssignment.assigned_at)).limit(10).all()
            
            return [
                {
                    'assignment_id': assignment.id,
                    'exercise_title': assignment.exercise.title if assignment.exercise else 'Unknown',
                    'class_name': assignment.class_obj.name if assignment.class_obj else 'Unknown',
                    'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                    'assigned_at': assignment.assigned_at.isoformat()
                }
                for assignment in assignments
            ]
            
        except Exception as e:
            logger.error(f"Error getting professor recent assignments for {professor_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_student_performance_insights(cls, professor_id: str) -> Dict[str, Any]:
        """Get insights about student performance across professor's classes."""
        try:
            # Get all students in professor's classes
            student_ids = db.session.query(func.distinct(ClassEnrollment.student_id)).join(
                Class
            ).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).subquery()
            
            # Performance distribution
            score_ranges = [
                ('90-100', 90, 100),
                ('80-89', 80, 89),
                ('70-79', 70, 79),
                ('60-69', 60, 69),
                ('Below 60', 0, 59)
            ]
            
            performance_distribution = {}
            for range_name, min_score, max_score in score_ranges:
                count = Progress.query.filter(
                    and_(
                        Progress.student_id.in_(student_ids),
                        Progress.status == 'completed',
                        Progress.score >= min_score,
                        Progress.score <= max_score
                    )
                ).count()
                performance_distribution[range_name] = count
            
            # Students needing attention (low scores or no recent activity)
            struggling_students = cls._get_struggling_students_for_professor(professor_id)
            
            return {
                'performance_distribution': performance_distribution,
                'struggling_students': struggling_students
            }
            
        except Exception as e:
            logger.error(f"Error getting student performance insights for {professor_id}: {str(e)}")
            return {}
    
    @classmethod
    def _get_class_average_performance(cls, class_id: int) -> float:
        """Get average performance for a specific class."""
        try:
            # Get all students in the class
            student_ids = db.session.query(ClassEnrollment.student_id).filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).subquery()
            
            # Get average score for these students
            avg_score = db.session.query(func.avg(Progress.score)).filter(
                and_(
                    Progress.student_id.in_(student_ids),
                    Progress.status == 'completed',
                    Progress.score.isnot(None)
                )
            ).scalar()
            
            return round(avg_score, 2) if avg_score else 0.0
            
        except Exception as e:
            logger.error(f"Error getting class average performance for {class_id}: {str(e)}")
            return 0.0
    
    @classmethod
    def _get_professor_average_class_score(cls, professor_id: str) -> float:
        """Get average score across all professor's classes."""
        try:
            # Get all students in professor's classes
            student_ids = db.session.query(func.distinct(ClassEnrollment.student_id)).join(
                Class
            ).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).subquery()
            
            # Get average score for these students
            avg_score = db.session.query(func.avg(Progress.score)).filter(
                and_(
                    Progress.student_id.in_(student_ids),
                    Progress.status == 'completed',
                    Progress.score.isnot(None)
                )
            ).scalar()
            
            return round(avg_score, 2) if avg_score else 0.0
            
        except Exception as e:
            logger.error(f"Error getting professor average class score for {professor_id}: {str(e)}")
            return 0.0
    
    @classmethod
    def _get_single_class_analytics(cls, class_id: int) -> Dict[str, Any]:
        """Get detailed analytics for a single class."""
        try:
            # Student count
            student_count = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).count()
            
            # Assignment count
            assignment_count = ClassExerciseAssignment.query.filter(
                ClassExerciseAssignment.class_id == class_id
            ).count()
            
            # Average performance
            avg_performance = cls._get_class_average_performance(class_id)
            
            # Completion rate
            total_possible_completions = student_count * assignment_count
            actual_completions = db.session.query(func.count(Progress.id)).join(
                ClassExerciseAssignment,
                Progress.exercise_id == ClassExerciseAssignment.exercise_id
            ).join(
                ClassEnrollment,
                Progress.student_id == ClassEnrollment.student_id
            ).filter(
                and_(
                    ClassExerciseAssignment.class_id == class_id,
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active',
                    Progress.status == 'completed'
                )
            ).scalar()
            
            completion_rate = (actual_completions / total_possible_completions * 100) if total_possible_completions > 0 else 0
            
            return {
                'student_count': student_count,
                'assignment_count': assignment_count,
                'average_performance': avg_performance,
                'completion_rate': round(completion_rate, 2),
                'total_completions': actual_completions or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting single class analytics for {class_id}: {str(e)}")
            return {}
    
    @classmethod
    def _get_struggling_students_for_professor(cls, professor_id: str) -> List[Dict[str, Any]]:
        """Get students who might need attention in professor's classes."""
        try:
            # Get students with low average scores or no recent activity
            struggling = []
            
            # Get all students in professor's classes
            student_enrollments = db.session.query(
                ClassEnrollment.student_id,
                Class.name.label('class_name')
            ).join(Class).filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).all()
            
            for enrollment in student_enrollments:
                student_id = enrollment.student_id
                
                # Calculate student's average score
                avg_score = db.session.query(func.avg(Progress.score)).filter(
                    and_(
                        Progress.student_id == student_id,
                        Progress.status == 'completed',
                        Progress.score.isnot(None)
                    )
                ).scalar()
                
                # Check recent activity
                recent_activity = Progress.query.filter(
                    and_(
                        Progress.student_id == student_id,
                        Progress.updated_at >= datetime.utcnow() - timedelta(days=7)
                    )
                ).count()
                
                # Flag as struggling if low score or no recent activity
                if (avg_score and avg_score < 70) or recent_activity == 0:
                    student = User.query.get(student_id)
                    if student:
                        struggling.append({
                            'student_id': str(student_id),
                            'student_name': student.full_name,
                            'class_name': enrollment.class_name,
                            'average_score': round(avg_score, 2) if avg_score else 0,
                            'recent_activity': recent_activity,
                            'reason': 'Low average score' if avg_score and avg_score < 70 else 'No recent activity'
                        })
            
            return struggling[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Error getting struggling students for professor {professor_id}: {str(e)}")
            return []
