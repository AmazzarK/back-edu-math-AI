"""
Dashboard API endpoints for data aggregation and analytics.
"""
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.services.dashboard import DashboardService
from app.models import User
from app.utils.decorators import handle_exceptions, role_required

logger = logging.getLogger(__name__)


class StudentDashboardResource(Resource):
    """Resource for student dashboard data."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get comprehensive dashboard data for a student."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            if user.role != 'student':
                return jsonify({
                    'success': False,
                    'message': 'Access denied - students only'
                }), 403
            
            dashboard_data = DashboardService.get_student_dashboard(user_id)
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting student dashboard: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve dashboard data'
            }), 500


class ProfessorDashboardResource(Resource):
    """Resource for professor dashboard data."""
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    def get(self):
        """Get comprehensive dashboard data for a professor."""
        try:
            user_id = get_jwt_identity()
            
            dashboard_data = DashboardService.get_professor_dashboard(user_id)
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting professor dashboard: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve dashboard data'
            }), 500


class AdminDashboardResource(Resource):
    """Resource for admin dashboard data."""
    
    @jwt_required()
    @role_required('admin')
    @handle_exceptions
    def get(self):
        """Get comprehensive dashboard data for administrators."""
        try:
            dashboard_data = DashboardService.get_admin_dashboard()
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting admin dashboard: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve dashboard data'
            }), 500


class DashboardOverviewResource(Resource):
    """Resource for general dashboard overview based on user role."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get dashboard data appropriate for the user's role."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # Route to appropriate dashboard based on role
            if user.role == 'student':
                dashboard_data = DashboardService.get_student_dashboard(user_id)
            elif user.role == 'professor':
                dashboard_data = DashboardService.get_professor_dashboard(user_id)
            elif user.role == 'admin':
                dashboard_data = DashboardService.get_admin_dashboard()
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user role'
                }), 400
            
            # Add user role to response
            dashboard_data['user_role'] = user.role
            
            return jsonify({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve dashboard data'
            }), 500


class DashboardQuickStatsResource(Resource):
    """Resource for quick statistics summary."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get quick stats summary for the user."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # Get appropriate quick stats based on role
            if user.role == 'student':
                dashboard_data = DashboardService.get_student_dashboard(user_id)
                quick_stats = dashboard_data.get('quick_stats', {})
            elif user.role == 'professor':
                dashboard_data = DashboardService.get_professor_dashboard(user_id)
                quick_stats = dashboard_data.get('quick_stats', {})
            elif user.role == 'admin':
                dashboard_data = DashboardService.get_admin_dashboard()
                quick_stats = dashboard_data.get('quick_stats', {})
            else:
                quick_stats = {}
            
            return jsonify({
                'success': True,
                'data': {
                    'user_role': user.role,
                    'quick_stats': quick_stats
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting quick stats: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve quick stats'
            }), 500


class DashboardAnalyticsResource(Resource):
    """Resource for detailed analytics data."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get analytics data based on user role and permissions."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # Get analytics data based on role
            if user.role == 'student':
                # Student analytics: personal progress and achievements
                dashboard_data = DashboardService.get_student_dashboard(user_id)
                analytics = {
                    'personal_progress': dashboard_data.get('recent_progress', []),
                    'achievements': dashboard_data.get('achievements', {}),
                    'class_performance': dashboard_data.get('enrolled_classes', []),
                    'overall_stats': dashboard_data.get('overall_stats', {})
                }
                
            elif user.role == 'professor':
                # Professor analytics: class performance and student insights
                dashboard_data = DashboardService.get_professor_dashboard(user_id)
                analytics = {
                    'class_analytics': dashboard_data.get('class_analytics', []),
                    'student_insights': dashboard_data.get('student_insights', {}),
                    'teaching_stats': dashboard_data.get('teaching_stats', {}),
                    'recent_activity': dashboard_data.get('recent_activity', [])
                }
                
            elif user.role == 'admin':
                # Admin analytics: platform-wide statistics
                dashboard_data = DashboardService.get_admin_dashboard()
                analytics = {
                    'platform_stats': dashboard_data.get('platform_stats', {}),
                    'user_analytics': dashboard_data.get('user_analytics', {}),
                    'activity_trends': dashboard_data.get('activity_trends', {}),
                    'system_health': dashboard_data.get('system_health', {}),
                    'popular_content': dashboard_data.get('popular_content', {})
                }
                
            else:
                analytics = {}
            
            return jsonify({
                'success': True,
                'data': {
                    'user_role': user.role,
                    'analytics': analytics
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve analytics data'
            }), 500


class DashboardChartsResource(Resource):
    """Resource for chart data for dashboard visualizations."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get chart data for dashboard visualizations."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            chart_type = request.args.get('type', 'overview')
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            charts_data = {}
            
            if user.role == 'student':
                dashboard_data = DashboardService.get_student_dashboard(user_id)
                
                if chart_type in ['overview', 'progress']:
                    # Progress over time chart
                    recent_progress = dashboard_data.get('recent_progress', [])
                    progress_chart = {
                        'type': 'line',
                        'title': 'Progress Over Time',
                        'data': [
                            {
                                'date': item['completed_at'][:10],  # Extract date part
                                'score': item['score'] or 0
                            }
                            for item in recent_progress
                            if item['status'] == 'completed'
                        ]
                    }
                    charts_data['progress_chart'] = progress_chart
                
                if chart_type in ['overview', 'performance']:
                    # Performance by class chart
                    enrolled_classes = dashboard_data.get('enrolled_classes', [])
                    performance_chart = {
                        'type': 'bar',
                        'title': 'Performance by Class',
                        'data': [
                            {
                                'class_name': class_data['name'],
                                'completion_rate': class_data['completion_rate']
                            }
                            for class_data in enrolled_classes
                        ]
                    }
                    charts_data['performance_chart'] = performance_chart
            
            elif user.role == 'professor':
                dashboard_data = DashboardService.get_professor_dashboard(user_id)
                
                if chart_type in ['overview', 'classes']:
                    # Class performance chart
                    class_analytics = dashboard_data.get('class_analytics', [])
                    class_chart = {
                        'type': 'bar',
                        'title': 'Class Performance Overview',
                        'data': [
                            {
                                'class_name': analytics['class_name'],
                                'average_performance': analytics['average_performance'],
                                'completion_rate': analytics['completion_rate']
                            }
                            for analytics in class_analytics
                        ]
                    }
                    charts_data['class_performance_chart'] = class_chart
                
                if chart_type in ['overview', 'activity']:
                    # Recent activity chart
                    recent_activity = dashboard_data.get('recent_activity', [])
                    activity_chart = {
                        'type': 'timeline',
                        'title': 'Recent Student Activity',
                        'data': recent_activity[:10]  # Limit to recent 10
                    }
                    charts_data['activity_chart'] = activity_chart
            
            elif user.role == 'admin':
                dashboard_data = DashboardService.get_admin_dashboard()
                
                if chart_type in ['overview', 'platform']:
                    # Platform statistics chart
                    platform_stats = dashboard_data.get('platform_stats', {})
                    platform_chart = {
                        'type': 'pie',
                        'title': 'Platform Overview',
                        'data': [
                            {'label': 'Students', 'value': platform_stats.get('total_students', 0)},
                            {'label': 'Professors', 'value': platform_stats.get('total_professors', 0)},
                            {'label': 'Classes', 'value': platform_stats.get('total_classes', 0)},
                            {'label': 'Exercises', 'value': platform_stats.get('total_exercises', 0)}
                        ]
                    }
                    charts_data['platform_chart'] = platform_chart
                
                if chart_type in ['overview', 'trends']:
                    # Activity trends chart
                    activity_trends = dashboard_data.get('activity_trends', {})
                    trends_chart = {
                        'type': 'line',
                        'title': 'Activity Trends (30 Days)',
                        'data': {
                            'completions': activity_trends.get('daily_completions', []),
                            'registrations': activity_trends.get('daily_registrations', [])
                        }
                    }
                    charts_data['trends_chart'] = trends_chart
            
            return jsonify({
                'success': True,
                'data': {
                    'user_role': user.role,
                    'chart_type': chart_type,
                    'charts': charts_data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting chart data: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve chart data'
            }), 500


# Register routes
def register_dashboard_routes(api):
    """Register dashboard API routes."""
    api.add_resource(DashboardOverviewResource, '/api/dashboard')
    api.add_resource(StudentDashboardResource, '/api/dashboard/student')
    api.add_resource(ProfessorDashboardResource, '/api/dashboard/professor')
    api.add_resource(AdminDashboardResource, '/api/dashboard/admin')
    api.add_resource(DashboardQuickStatsResource, '/api/dashboard/quick-stats')
    api.add_resource(DashboardAnalyticsResource, '/api/dashboard/analytics')
    api.add_resource(DashboardChartsResource, '/api/dashboard/charts')
