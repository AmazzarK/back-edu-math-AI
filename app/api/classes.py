"""
Class management API endpoints for course/class operations.
"""
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime
from sqlalchemy import func
import logging

from app.services.class_management import ClassManagementService
from app.models import User
from app.extensions import db
from app.utils.decorators import handle_exceptions, role_required
from app.utils.validators import validate_json_request

logger = logging.getLogger(__name__)


class ClassCreationSchema(Schema):
    """Schema for class creation validation."""
    name = fields.Str(required=True, validate=lambda x: 1 <= len(x.strip()) <= 200)
    description = fields.Str(required=False, validate=lambda x: len(x) <= 1000)
    subject = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    grade_level = fields.Int(required=False, validate=lambda x: 1 <= x <= 12)
    max_students = fields.Int(required=False, validate=lambda x: 1 <= x <= 1000)
    start_date = fields.DateTime(required=False)
    end_date = fields.DateTime(required=False)
    settings = fields.Dict(required=False)


class ClassUpdateSchema(Schema):
    """Schema for class update validation."""
    name = fields.Str(required=False, validate=lambda x: 1 <= len(x.strip()) <= 200)
    description = fields.Str(required=False, validate=lambda x: len(x) <= 1000)
    subject = fields.Str(required=False, validate=lambda x: len(x.strip()) > 0)
    grade_level = fields.Int(required=False, validate=lambda x: 1 <= x <= 12)
    max_students = fields.Int(required=False, validate=lambda x: 1 <= x <= 1000)
    start_date = fields.DateTime(required=False)
    end_date = fields.DateTime(required=False)
    settings = fields.Dict(required=False)
    is_active = fields.Bool(required=False)


class ExerciseAssignmentSchema(Schema):
    """Schema for exercise assignment validation."""
    exercise_id = fields.Int(required=True)
    due_date = fields.DateTime(required=False, allow_none=True)
    is_mandatory = fields.Bool(required=False)
    points_worth = fields.Int(required=False, validate=lambda x: x >= 0)
    instructions = fields.Str(required=False, validate=lambda x: len(x) <= 1000)


class ClassResource(Resource):
    """Resource for class management."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get classes based on user role."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            if user.role == 'professor':
                # Get classes taught by professor
                classes = ClassManagementService.get_classes_by_professor(user_id)
            elif user.role == 'student':
                # Get classes enrolled by student
                classes = ClassManagementService.get_classes_by_student(user_id)
            else:
                # Admin can see all classes
                classes = ClassManagementService.get_all({'is_active': True})
            
            class_data = [class_obj.to_dict(include_stats=True) for class_obj in classes]
            
            return jsonify({
                'success': True,
                'data': {
                    'classes': class_data,
                    'total': len(class_data)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting classes: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve classes'
            }), 500
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    @validate_json_request
    def post(self):
        """Create a new class (professors only)."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            schema = ClassCreationSchema()
            validated_data = schema.load(data)
            
            # Create class
            new_class = ClassManagementService.create_class(
                data=validated_data,
                professor_id=user_id
            )
            
            return jsonify({
                'success': True,
                'data': new_class.to_dict(include_stats=True),
                'message': 'Class created successfully'
            }), 201
            
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': 'Invalid input data',
                'errors': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Error creating class: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to create class'
            }), 500


class ClassDetailResource(Resource):
    """Resource for individual class operations."""
    
    @jwt_required()
    @handle_exceptions
    def get(self, class_id):
        """Get class details."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            class_obj = ClassManagementService.get_by_id(class_id)
            if not class_obj:
                return jsonify({
                    'success': False,
                    'message': 'Class not found'
                }), 404
            
            # Check permissions
            if user.role == 'student':
                # Student can only see classes they're enrolled in
                from app.models import ClassEnrollment
                enrollment = ClassEnrollment.query.filter_by(
                    class_id=class_id,
                    student_id=user_id,
                    enrollment_status='active'
                ).first()
                
                if not enrollment:
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            elif user.role == 'professor':
                # Professor can only see their own classes
                if str(class_obj.professor_id) != user_id:
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            
            # Get detailed class information
            class_data = class_obj.to_dict(include_stats=True)
            
            # Add additional details for professors
            if user.role == 'professor':
                stats = ClassManagementService.get_class_statistics(class_id, user_id)
                class_data['detailed_stats'] = stats
            
            return jsonify({
                'success': True,
                'data': class_data
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error getting class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve class'
            }), 500
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    @validate_json_request
    def put(self, class_id):
        """Update class details (professors only)."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            schema = ClassUpdateSchema()
            validated_data = schema.load(data)
            
            # Update class
            updated_class = ClassManagementService.update_class(
                class_id=class_id,
                data=validated_data,
                professor_id=user_id
            )
            
            return jsonify({
                'success': True,
                'data': updated_class.to_dict(include_stats=True),
                'message': 'Class updated successfully'
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except PermissionError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 403
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': 'Invalid input data',
                'errors': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Error updating class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update class'
            }), 500
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    def delete(self, class_id):
        """Delete class (professors only)."""
        try:
            user_id = get_jwt_identity()
            
            success = ClassManagementService.delete_class(
                class_id=class_id,
                professor_id=user_id
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Class deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete class'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except PermissionError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 403
        except Exception as e:
            logger.error(f"Error deleting class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to delete class'
            }), 500


class ClassEnrollmentResource(Resource):
    """Resource for class enrollment management."""
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def post(self, class_id):
        """Enroll in a class."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if user.role != 'student':
                return jsonify({
                    'success': False,
                    'message': 'Only students can enroll in classes'
                }), 403
            
            # Enroll student
            enrollment = ClassManagementService.enroll_student(
                class_id=class_id,
                student_id=user_id
            )
            
            return jsonify({
                'success': True,
                'data': enrollment.to_dict(),
                'message': 'Successfully enrolled in class'
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error enrolling in class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to enroll in class'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    def delete(self, class_id):
        """Unenroll from a class."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if user.role != 'student':
                return jsonify({
                    'success': False,
                    'message': 'Only students can unenroll from classes'
                }), 403
            
            # Unenroll student
            success = ClassManagementService.unenroll_student(
                class_id=class_id,
                student_id=user_id
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Successfully unenrolled from class'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to unenroll from class'
                }), 500
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error unenrolling from class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to unenroll from class'
            }), 500


class ClassEnrollmentByCodeResource(Resource):
    """Resource for enrolling via class code."""
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def post(self):
        """Enroll in a class using class code."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if user.role != 'student':
                return jsonify({
                    'success': False,
                    'message': 'Only students can enroll in classes'
                }), 403
            
            data = request.get_json()
            class_code = data.get('class_code', '').strip().upper()
            
            if not class_code:
                return jsonify({
                    'success': False,
                    'message': 'Class code is required'
                }), 400
            
            # Enroll by class code
            enrollment = ClassManagementService.enroll_by_class_code(
                class_code=class_code,
                student_id=user_id
            )
            
            return jsonify({
                'success': True,
                'data': enrollment.to_dict(),
                'message': 'Successfully enrolled in class'
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error enrolling by class code: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to enroll in class'
            }), 500


class ClassAssignmentResource(Resource):
    """Resource for managing class assignments."""
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    @validate_json_request
    def post(self, class_id):
        """Assign an exercise to a class."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            schema = ExerciseAssignmentSchema()
            validated_data = schema.load(data)
            
            # Create assignment
            assignment = ClassManagementService.assign_exercise(
                class_id=class_id,
                exercise_id=validated_data['exercise_id'],
                assigned_by=user_id,
                due_date=validated_data.get('due_date'),
                is_mandatory=validated_data.get('is_mandatory', True),
                points_worth=validated_data.get('points_worth'),
                instructions=validated_data.get('instructions')
            )
            
            return jsonify({
                'success': True,
                'data': assignment.to_dict(),
                'message': 'Exercise assigned successfully'
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except PermissionError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 403
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': 'Invalid input data',
                'errors': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Error assigning exercise to class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to assign exercise'
            }), 500


class ClassStudentsResource(Resource):
    """Resource for managing class student list."""
    
    @jwt_required()
    @handle_exceptions
    def get(self, class_id):
        """Get list of students in a class."""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            # Check permissions
            class_obj = ClassManagementService.get_by_id(class_id)
            if not class_obj:
                return jsonify({
                    'success': False,
                    'message': 'Class not found'
                }), 404
            
            if user.role == 'professor':
                if str(class_obj.professor_id) != user_id:
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            elif user.role == 'student':
                # Students can only see classmates if they're enrolled
                from app.models import ClassEnrollment
                enrollment = ClassEnrollment.query.filter_by(
                    class_id=class_id,
                    student_id=user_id,
                    enrollment_status='active'
                ).first()
                
                if not enrollment:
                    return jsonify({
                        'success': False,
                        'message': 'Access denied'
                    }), 403
            
            # Get enrolled students
            from app.models import ClassEnrollment
            enrollments = ClassEnrollment.query.filter_by(
                class_id=class_id,
                enrollment_status='active'
            ).all()
            
            students = []
            for enrollment in enrollments:
                student = User.query.get(enrollment.student_id)
                if student:
                    student_data = {
                        'id': student.id,
                        'name': student.full_name,
                        'email': student.email if user.role != 'student' else None,
                        'enrolled_at': enrollment.enrolled_at.isoformat()
                    }
                    
                    # Add progress info for professors
                    if user.role == 'professor':
                        # Get student's progress in this class
                        from app.models import Progress, ClassExerciseAssignment
                        completed_assignments = db.session.query(func.count(Progress.id)).join(
                            ClassExerciseAssignment,
                            Progress.exercise_id == ClassExerciseAssignment.exercise_id
                        ).filter(
                            ClassExerciseAssignment.class_id == class_id,
                            Progress.student_id == enrollment.student_id,
                            Progress.status == 'completed'
                        ).scalar()
                        
                        total_assignments = ClassExerciseAssignment.query.filter_by(
                            class_id=class_id
                        ).count()
                        
                        student_data.update({
                            'completed_assignments': completed_assignments or 0,
                            'total_assignments': total_assignments,
                            'completion_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
                        })
                    
                    students.append(student_data)
            
            return jsonify({
                'success': True,
                'data': {
                    'students': students,
                    'total': len(students)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting students for class {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve students'
            }), 500


class ClassStatisticsResource(Resource):
    """Resource for class statistics and analytics."""
    
    @jwt_required()
    @role_required('professor')
    @handle_exceptions
    def get(self, class_id):
        """Get detailed class statistics (professors only)."""
        try:
            user_id = get_jwt_identity()
            
            stats = ClassManagementService.get_class_statistics(
                class_id=class_id,
                professor_id=user_id
            )
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 404
        except PermissionError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 403
        except Exception as e:
            logger.error(f"Error getting class statistics for {class_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve statistics'
            }), 500


# Register routes
def register_class_routes(api):
    """Register class management API routes."""
    api.add_resource(ClassResource, '/api/classes')
    api.add_resource(ClassDetailResource, '/api/classes/<int:class_id>')
    api.add_resource(ClassEnrollmentResource, '/api/classes/<int:class_id>/enrollment')
    api.add_resource(ClassEnrollmentByCodeResource, '/api/classes/enroll')
    api.add_resource(ClassAssignmentResource, '/api/classes/<int:class_id>/assignments')
    api.add_resource(ClassStudentsResource, '/api/classes/<int:class_id>/students')
    api.add_resource(ClassStatisticsResource, '/api/classes/<int:class_id>/statistics')
