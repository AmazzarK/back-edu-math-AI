from flask import Blueprint
from flask_restful import Api
from flask import request, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.exercise import (
    ExerciseSchema, ExerciseCreateSchema, ExerciseUpdateSchema, 
    ExerciseListSchema, ProgressSchema, ProgressSubmissionSchema,
    ProgressStartSchema, AnalyticsStudentSchema, AnalyticsClassSchema,
    AnalyticsOverviewSchema
)
from app.services.exercise import ExerciseService, ProgressService, AnalyticsService
from app.utils.auth import role_required, jwt_required_with_user
from app.utils.cache import cache_key, get_cached_result, set_cached_result
from app.extensions import limiter
import logging

logger = logging.getLogger(__name__)

# Create blueprint
exercises_bp = Blueprint('exercises', __name__)
api = Api(exercises_bp)


class ExerciseListResource(Resource):
    """Resource for listing and creating exercises."""
    
    @limiter.limit("100 per minute")
    def get(self):
        """Get exercises with pagination and filters."""
        try:
            # Validate query parameters
            schema = ExerciseListSchema()
            filters = schema.load(request.args)
            
            # Check cache first
            cache_key_str = cache_key('exercises_list', **filters)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get exercises
            exercises, total = ExerciseService.get_exercises_with_filters(filters)
            
            # Serialize exercises
            exercise_schema = ExerciseSchema(many=True)
            exercises_data = exercise_schema.dump(exercises)
            
            # Prepare response
            response_data = {
                'success': True,
                'data': {
                    'exercises': exercises_data,
                    'pagination': {
                        'page': filters.get('page', 1),
                        'per_page': filters.get('per_page', 10),
                        'total': total,
                        'pages': (total + filters.get('per_page', 10) - 1) // filters.get('per_page', 10)
                    }
                },
                'message': 'Exercises retrieved successfully'
            }
            
            # Cache the result for 5 minutes
            set_cached_result(cache_key_str, response_data, timeout=300)
            
            return response_data
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except Exception as e:
            logger.error(f"Error getting exercises: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500
    
    @jwt_required()
    @role_required(['professor', 'admin'])
    def post(self):
        """Create a new exercise."""
        try:
            current_user = get_jwt_identity()
            user_info = jwt_required_with_user()
            
            # Validate input
            schema = ExerciseCreateSchema()
            data = schema.load(request.get_json())
            
            # Create exercise
            exercise = ExerciseService.create_exercise(data, current_user)
            
            # Serialize response
            exercise_schema = ExerciseSchema()
            exercise_data = exercise_schema.dump(exercise)
            
            return {
                'success': True,
                'data': exercise_data,
                'message': 'Exercise created successfully'
            }, 201
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except Exception as e:
            logger.error(f"Error creating exercise: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }, 500


class ExerciseResource(Resource):
    """Resource for individual exercise operations."""
    
    @limiter.limit("200 per minute")
    def get(self, exercise_id):
        """Get a specific exercise."""
        try:
            exercise = ExerciseService.get_by_id(exercise_id)
            if not exercise:
                return {
                    'success': False,
                    'error': 'Exercise not found'
                }, 404
            
            # Check if user can see solutions
            include_solutions = False
            try:
                current_user = get_jwt_identity()
                user_info = jwt_required_with_user()
                if user_info and user_info.get('role') in ['professor', 'admin']:
                    include_solutions = True
            except:
                pass  # Not authenticated, don't include solutions
            
            # Serialize exercise
            exercise_data = exercise.to_dict(include_solutions=include_solutions)
            
            return {
                'success': True,
                'data': exercise_data,
                'message': 'Exercise retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Error getting exercise {exercise_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500
    
    @jwt_required()
    @role_required(['professor', 'admin'])
    def put(self, exercise_id):
        """Update an exercise."""
        try:
            current_user = get_jwt_identity()
            
            # Validate input
            schema = ExerciseUpdateSchema()
            data = schema.load(request.get_json())
            
            # Update exercise
            exercise = ExerciseService.update_exercise(exercise_id, data, current_user)
            
            # Serialize response
            exercise_schema = ExerciseSchema()
            exercise_data = exercise_schema.dump(exercise)
            
            return {
                'success': True,
                'data': exercise_data,
                'message': 'Exercise updated successfully'
            }
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }, 404
        except PermissionError as e:
            return {
                'success': False,
                'error': str(e)
            }, 403
        except Exception as e:
            logger.error(f"Error updating exercise {exercise_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500
    
    @jwt_required()
    @role_required(['professor', 'admin'])
    def delete(self, exercise_id):
        """Delete an exercise."""
        try:
            current_user = get_jwt_identity()
            
            # Delete exercise
            success = ExerciseService.delete_exercise(exercise_id, current_user)
            
            return {
                'success': True,
                'message': 'Exercise deleted successfully'
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }, 404
        except PermissionError as e:
            return {
                'success': False,
                'error': str(e)
            }, 403
        except Exception as e:
            logger.error(f"Error deleting exercise {exercise_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ExercisesByProfessorResource(Resource):
    """Resource for getting exercises by professor."""
    
    @jwt_required()
    @limiter.limit("50 per minute")
    def get(self, professor_id):
        """Get exercises created by a specific professor."""
        try:
            # Check cache first
            cache_key_str = cache_key('exercises_by_professor', professor_id=professor_id)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get exercises
            exercises = ExerciseService.get_exercises_by_professor(professor_id)
            
            # Serialize exercises
            exercise_schema = ExerciseSchema(many=True)
            exercises_data = exercise_schema.dump(exercises)
            
            response_data = {
                'success': True,
                'data': exercises_data,
                'message': f'Exercises by professor retrieved successfully'
            }
            
            # Cache for 10 minutes
            set_cached_result(cache_key_str, response_data, timeout=600)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting exercises by professor {professor_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ExercisesBySubjectResource(Resource):
    """Resource for getting exercises by subject."""
    
    @limiter.limit("100 per minute")
    def get(self, subject):
        """Get exercises by subject."""
        try:
            # Check cache first
            cache_key_str = cache_key('exercises_by_subject', subject=subject)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get exercises
            exercises = ExerciseService.get_exercises_by_subject(subject)
            
            # Serialize exercises
            exercise_schema = ExerciseSchema(many=True)
            exercises_data = exercise_schema.dump(exercises)
            
            response_data = {
                'success': True,
                'data': exercises_data,
                'message': f'Exercises for subject "{subject}" retrieved successfully'
            }
            
            # Cache for 10 minutes
            set_cached_result(cache_key_str, response_data, timeout=600)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting exercises by subject {subject}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ProgressSubmissionResource(Resource):
    """Resource for submitting exercise progress."""
    
    @jwt_required()
    @role_required(['student'])
    @limiter.limit("20 per minute")
    def post(self):
        """Submit answers for an exercise."""
        try:
            current_user = get_jwt_identity()
            
            # Validate input
            schema = ProgressSubmissionSchema()
            data = schema.load(request.get_json())
            
            # Submit answers
            progress = ProgressService.submit_answers(
                student_id=current_user,
                exercise_id=data['exercise_id'],
                answers=data['answers'],
                time_spent=data.get('time_spent')
            )
            
            # Serialize response
            progress_schema = ProgressSchema()
            progress_data = progress_schema.dump(progress)
            
            return {
                'success': True,
                'data': progress_data,
                'message': 'Answers submitted successfully'
            }, 201
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error submitting progress: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ProgressStartResource(Resource):
    """Resource for starting an exercise."""
    
    @jwt_required()
    @role_required(['student'])
    @limiter.limit("30 per minute")
    def post(self):
        """Start an exercise."""
        try:
            current_user = get_jwt_identity()
            
            # Validate input
            schema = ProgressStartSchema()
            data = schema.load(request.get_json())
            
            # Start exercise
            progress = ProgressService.start_exercise(
                student_id=current_user,
                exercise_id=data['exercise_id']
            )
            
            # Serialize response
            progress_schema = ProgressSchema()
            progress_data = progress_schema.dump(progress)
            
            return {
                'success': True,
                'data': progress_data,
                'message': 'Exercise started successfully'
            }, 201
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }, 400
        except Exception as e:
            logger.error(f"Error starting exercise: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class StudentProgressResource(Resource):
    """Resource for getting student progress."""
    
    @jwt_required()
    @limiter.limit("50 per minute")
    def get(self, student_id):
        """Get progress for a specific student."""
        try:
            current_user = get_jwt_identity()
            user_info = jwt_required_with_user()
            
            # Check permissions: students can only see their own progress
            if user_info.get('role') == 'student' and current_user != student_id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }, 403
            
            # Get progress
            progress_records = ProgressService.get_student_progress(student_id)
            
            # Serialize response
            progress_schema = ProgressSchema(many=True)
            progress_data = progress_schema.dump(progress_records)
            
            return {
                'success': True,
                'data': progress_data,
                'message': 'Student progress retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Error getting student progress for {student_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ExerciseProgressResource(Resource):
    """Resource for getting exercise progress."""
    
    @jwt_required()
    @role_required(['professor', 'admin'])
    @limiter.limit("50 per minute")
    def get(self, exercise_id):
        """Get progress for a specific exercise."""
        try:
            # Get progress
            progress_records = ProgressService.get_exercise_progress(exercise_id)
            
            # Serialize response
            progress_schema = ProgressSchema(many=True)
            progress_data = progress_schema.dump(progress_records)
            
            return {
                'success': True,
                'data': progress_data,
                'message': 'Exercise progress retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Error getting exercise progress for {exercise_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class StudentAnalyticsResource(Resource):
    """Resource for student analytics."""
    
    @jwt_required()
    @limiter.limit("20 per minute")
    def get(self, student_id):
        """Get analytics for a specific student."""
        try:
            current_user = get_jwt_identity()
            user_info = jwt_required_with_user()
            
            # Check permissions: students can only see their own analytics
            if user_info.get('role') == 'student' and current_user != student_id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }, 403
            
            # Check cache first
            cache_key_str = cache_key('student_analytics', student_id=student_id)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get analytics
            analytics_data = AnalyticsService.get_student_analytics(student_id)
            
            response_data = {
                'success': True,
                'data': analytics_data,
                'message': 'Student analytics retrieved successfully'
            }
            
            # Cache for 15 minutes
            set_cached_result(cache_key_str, response_data, timeout=900)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting student analytics for {student_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class ClassAnalyticsResource(Resource):
    """Resource for class analytics."""
    
    @jwt_required()
    @role_required(['professor', 'admin'])
    @limiter.limit("10 per minute")
    def get(self):
        """Get class-level analytics."""
        try:
            # Validate query parameters
            schema = AnalyticsClassSchema()
            filters = schema.load(request.args)
            
            # Check cache first
            cache_key_str = cache_key('class_analytics', **filters)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get analytics
            analytics_data = AnalyticsService.get_class_analytics(filters)
            
            response_data = {
                'success': True,
                'data': analytics_data,
                'message': 'Class analytics retrieved successfully'
            }
            
            # Cache for 30 minutes
            set_cached_result(cache_key_str, response_data, timeout=1800)
            
            return response_data
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except Exception as e:
            logger.error(f"Error getting class analytics: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500


class OverviewAnalyticsResource(Resource):
    """Resource for overview analytics."""
    
    @jwt_required()
    @role_required(['admin'])
    @limiter.limit("5 per minute")
    def get(self):
        """Get system overview analytics."""
        try:
            # Validate query parameters
            schema = AnalyticsOverviewSchema()
            filters = schema.load(request.args)
            
            # Check cache first
            cache_key_str = cache_key('overview_analytics', **filters)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                return cached_result
            
            # Get analytics
            analytics_data = AnalyticsService.get_overview_analytics(filters)
            
            response_data = {
                'success': True,
                'data': analytics_data,
                'message': 'Overview analytics retrieved successfully'
            }
            
            # Cache for 1 hour
            set_cached_result(cache_key_str, response_data, timeout=3600)
            
            return response_data
            
        except ValidationError as e:
            return {
                'success': False,
                'error': 'Validation error',
                'details': e.messages
            }, 400
        except Exception as e:
            logger.error(f"Error getting overview analytics: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }, 500

# Register API resources
api.add_resource(ExerciseListResource, '/exercises')
api.add_resource(ExerciseResource, '/exercises/<int:exercise_id>')
api.add_resource(ExercisesByProfessorResource, '/exercises/by-professor/<string:professor_id>')
api.add_resource(ExercisesBySubjectResource, '/exercises/by-subject/<string:subject>')

api.add_resource(ProgressStartResource, '/progress/start')
api.add_resource(ProgressSubmissionResource, '/progress/submit')
api.add_resource(StudentProgressResource, '/progress/student/<string:student_id>')
api.add_resource(ExerciseProgressResource, '/progress/exercise/<int:exercise_id>')

api.add_resource(StudentAnalyticsResource, '/analytics/student/<string:student_id>')
api.add_resource(ClassAnalyticsResource, '/analytics/class')
api.add_resource(OverviewAnalyticsResource, '/analytics/overview')
