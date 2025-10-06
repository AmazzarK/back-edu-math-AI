"""
Class management service for handling courses, enrollments, and assignments.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import (
    Class, ClassEnrollment, ClassExerciseAssignment, 
    User, Exercise, Progress, Notification
)
from app.services.base import BaseService
from app.utils.cache import cache_key, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)


class ClassManagementService(BaseService):
    """Service for managing classes and enrollments."""
    
    model = Class
    
    @classmethod
    def create_class(cls, data: Dict, professor_id: str) -> Class:
        """Create a new class."""
        try:
            # Generate unique class code
            class_code = Class.generate_class_code()
            
            class_obj = Class(
                name=data['name'],
                description=data.get('description', ''),
                subject=data['subject'],
                grade_level=data.get('grade_level'),
                professor_id=professor_id,
                class_code=class_code,
                max_students=data.get('max_students', 30),
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                settings=data.get('settings', {})
            )
            
            db.session.add(class_obj)
            db.session.commit()
            
            logger.info(f"Class created: {class_obj.id} by professor {professor_id}")
            return class_obj
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating class: {str(e)}")
            raise
    
    @classmethod
    def update_class(cls, class_id: int, data: Dict, professor_id: str) -> Class:
        """Update a class."""
        try:
            class_obj = cls.get_by_id(class_id)
            if not class_obj:
                raise ValueError("Class not found")
            
            if str(class_obj.professor_id) != professor_id:
                raise PermissionError("Only the class professor can update this class")
            
            # Update fields
            updatable_fields = [
                'name', 'description', 'subject', 'grade_level', 
                'max_students', 'start_date', 'end_date', 'settings', 'is_active'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(class_obj, field, data[field])
            
            class_obj.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Class updated: {class_obj.id}")
            return class_obj
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating class {class_id}: {str(e)}")
            raise
    
    @classmethod
    def delete_class(cls, class_id: int, professor_id: str) -> bool:
        """Delete a class."""
        try:
            class_obj = cls.get_by_id(class_id)
            if not class_obj:
                raise ValueError("Class not found")
            
            if str(class_obj.professor_id) != professor_id:
                raise PermissionError("Only the class professor can delete this class")
            
            # Check if class has students or assignments
            if class_obj.enrollments or class_obj.assigned_exercises:
                # Soft delete - deactivate instead of hard delete
                class_obj.is_active = False
                db.session.commit()
                logger.info(f"Class deactivated: {class_id}")
            else:
                # Hard delete if no enrollments or assignments
                db.session.delete(class_obj)
                db.session.commit()
                logger.info(f"Class deleted: {class_id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting class {class_id}: {str(e)}")
            raise
    
    @classmethod
    def get_classes_by_professor(cls, professor_id: str) -> List[Class]:
        """Get all classes for a professor."""
        try:
            return Class.query.filter(
                and_(
                    Class.professor_id == professor_id,
                    Class.is_active == True
                )
            ).order_by(desc(Class.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting classes for professor {professor_id}: {str(e)}")
            raise
    
    @classmethod
    def get_classes_by_student(cls, student_id: str) -> List[Class]:
        """Get all classes for a student."""
        try:
            return db.session.query(Class).join(ClassEnrollment).filter(
                and_(
                    ClassEnrollment.student_id == student_id,
                    ClassEnrollment.enrollment_status == 'active',
                    Class.is_active == True
                )
            ).order_by(desc(Class.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting classes for student {student_id}: {str(e)}")
            raise
    
    @classmethod
    def enroll_student(cls, class_id: int, student_id: str, 
                      enrolled_by: Optional[str] = None) -> ClassEnrollment:
        """Enroll a student in a class."""
        try:
            class_obj = cls.get_by_id(class_id)
            if not class_obj:
                raise ValueError("Class not found")
            
            if not class_obj.is_active:
                raise ValueError("Cannot enroll in inactive class")
            
            # Check if already enrolled
            existing_enrollment = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.student_id == student_id
                )
            ).first()
            
            if existing_enrollment:
                if existing_enrollment.enrollment_status == 'active':
                    raise ValueError("Student is already enrolled in this class")
                else:
                    # Reactivate enrollment
                    existing_enrollment.enrollment_status = 'active'
                    existing_enrollment.enrolled_at = datetime.utcnow()
                    db.session.commit()
                    return existing_enrollment
            
            # Check class capacity
            active_enrollments = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).count()
            
            if active_enrollments >= class_obj.max_students:
                raise ValueError("Class is full")
            
            # Create new enrollment
            enrollment = ClassEnrollment(
                class_id=class_id,
                student_id=student_id,
                enrollment_status='active'
            )
            
            db.session.add(enrollment)
            db.session.commit()
            
            # Create notification
            cls._create_enrollment_notification(student_id, class_obj, 'enrolled')
            
            logger.info(f"Student {student_id} enrolled in class {class_id}")
            return enrollment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error enrolling student {student_id} in class {class_id}: {str(e)}")
            raise
    
    @classmethod
    def unenroll_student(cls, class_id: int, student_id: str, 
                        unenrolled_by: Optional[str] = None) -> bool:
        """Unenroll a student from a class."""
        try:
            enrollment = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.student_id == student_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).first()
            
            if not enrollment:
                raise ValueError("Student is not enrolled in this class")
            
            enrollment.enrollment_status = 'dropped'
            db.session.commit()
            
            # Create notification
            class_obj = cls.get_by_id(class_id)
            cls._create_enrollment_notification(student_id, class_obj, 'unenrolled')
            
            logger.info(f"Student {student_id} unenrolled from class {class_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error unenrolling student {student_id} from class {class_id}: {str(e)}")
            raise
    
    @classmethod
    def enroll_by_class_code(cls, class_code: str, student_id: str) -> ClassEnrollment:
        """Enroll student using class code."""
        try:
            class_obj = Class.query.filter(
                and_(
                    Class.class_code == class_code.upper(),
                    Class.is_active == True
                )
            ).first()
            
            if not class_obj:
                raise ValueError("Invalid class code")
            
            return cls.enroll_student(class_obj.id, student_id)
            
        except Exception as e:
            logger.error(f"Error enrolling student {student_id} with code {class_code}: {str(e)}")
            raise
    
    @classmethod
    def assign_exercise(cls, class_id: int, exercise_id: int, assigned_by: str,
                       due_date: Optional[datetime] = None, **kwargs) -> ClassExerciseAssignment:
        """Assign an exercise to a class."""
        try:
            # Verify class and exercise exist
            class_obj = cls.get_by_id(class_id)
            if not class_obj:
                raise ValueError("Class not found")
            
            if str(class_obj.professor_id) != assigned_by:
                raise PermissionError("Only the class professor can assign exercises")
            
            exercise = Exercise.query.get(exercise_id)
            if not exercise:
                raise ValueError("Exercise not found")
            
            # Check if already assigned
            existing_assignment = ClassExerciseAssignment.query.filter(
                and_(
                    ClassExerciseAssignment.class_id == class_id,
                    ClassExerciseAssignment.exercise_id == exercise_id
                )
            ).first()
            
            if existing_assignment:
                raise ValueError("Exercise is already assigned to this class")
            
            # Create assignment
            assignment = ClassExerciseAssignment(
                class_id=class_id,
                exercise_id=exercise_id,
                assigned_by=assigned_by,
                due_date=due_date,
                is_mandatory=kwargs.get('is_mandatory', True),
                points_worth=kwargs.get('points_worth'),
                instructions=kwargs.get('instructions')
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            # Notify all enrolled students
            cls._notify_students_of_assignment(class_id, exercise, assignment)
            
            logger.info(f"Exercise {exercise_id} assigned to class {class_id}")
            return assignment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning exercise {exercise_id} to class {class_id}: {str(e)}")
            raise
    
    @classmethod
    def get_class_statistics(cls, class_id: int, professor_id: str) -> Dict[str, Any]:
        """Get comprehensive class statistics."""
        try:
            class_obj = cls.get_by_id(class_id)
            if not class_obj:
                raise ValueError("Class not found")
            
            if str(class_obj.professor_id) != professor_id:
                raise PermissionError("Access denied")
            
            # Basic stats
            total_students = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).count()
            
            total_assignments = ClassExerciseAssignment.query.filter(
                ClassExerciseAssignment.class_id == class_id
            ).count()
            
            # Student performance stats
            student_enrollments = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).all()
            
            student_ids = [enrollment.student_id for enrollment in student_enrollments]
            
            # Get assignment progress
            assignments = ClassExerciseAssignment.query.filter(
                ClassExerciseAssignment.class_id == class_id
            ).all()
            
            assignment_stats = []
            for assignment in assignments:
                completed_count = Progress.query.filter(
                    and_(
                        Progress.exercise_id == assignment.exercise_id,
                        Progress.student_id.in_(student_ids),
                        Progress.status == 'completed'
                    )
                ).count()
                
                avg_score = db.session.query(func.avg(Progress.score)).filter(
                    and_(
                        Progress.exercise_id == assignment.exercise_id,
                        Progress.student_id.in_(student_ids),
                        Progress.status == 'completed'
                    )
                ).scalar()
                
                assignment_stats.append({
                    'assignment_id': assignment.id,
                    'exercise_title': assignment.exercise.title if assignment.exercise else None,
                    'total_students': total_students,
                    'completed_count': completed_count,
                    'completion_rate': (completed_count / total_students * 100) if total_students > 0 else 0,
                    'average_score': round(avg_score, 2) if avg_score else 0
                })
            
            # Recent activity
            recent_progress = Progress.query.filter(
                and_(
                    Progress.student_id.in_(student_ids),
                    Progress.updated_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            return {
                'class_info': class_obj.to_dict(include_stats=True),
                'total_students': total_students,
                'total_assignments': total_assignments,
                'assignment_stats': assignment_stats,
                'recent_activity': recent_progress,
                'average_class_score': cls._calculate_class_average_score(student_ids),
                'top_performers': cls._get_top_performers(student_ids, limit=5),
                'struggling_students': cls._get_struggling_students(student_ids, limit=5)
            }
            
        except Exception as e:
            logger.error(f"Error getting class statistics for {class_id}: {str(e)}")
            raise
    
    @classmethod
    def _calculate_class_average_score(cls, student_ids: List[str]) -> float:
        """Calculate average score for the class."""
        if not student_ids:
            return 0.0
        
        avg_score = db.session.query(func.avg(Progress.score)).filter(
            and_(
                Progress.student_id.in_(student_ids),
                Progress.status == 'completed',
                Progress.score.isnot(None)
            )
        ).scalar()
        
        return round(avg_score, 2) if avg_score else 0.0
    
    @classmethod
    def _get_top_performers(cls, student_ids: List[str], limit: int = 5) -> List[Dict]:
        """Get top performing students in the class."""
        if not student_ids:
            return []
        
        # Calculate average score per student
        student_averages = db.session.query(
            Progress.student_id,
            func.avg(Progress.score).label('avg_score'),
            func.count(Progress.id).label('completed_count')
        ).filter(
            and_(
                Progress.student_id.in_(student_ids),
                Progress.status == 'completed',
                Progress.score.isnot(None)
            )
        ).group_by(Progress.student_id).order_by(desc('avg_score')).limit(limit).all()
        
        top_performers = []
        for student_id, avg_score, completed_count in student_averages:
            user = User.query.get(student_id)
            if user:
                top_performers.append({
                    'student_id': str(student_id),
                    'student_name': user.full_name,
                    'average_score': round(avg_score, 2),
                    'completed_exercises': completed_count
                })
        
        return top_performers
    
    @classmethod
    def _get_struggling_students(cls, student_ids: List[str], limit: int = 5) -> List[Dict]:
        """Get students who might need additional help."""
        if not student_ids:
            return []
        
        # Find students with low scores or incomplete assignments
        student_stats = db.session.query(
            Progress.student_id,
            func.avg(Progress.score).label('avg_score'),
            func.count(Progress.id).label('total_attempts')
        ).filter(
            Progress.student_id.in_(student_ids)
        ).group_by(Progress.student_id).all()
        
        struggling_students = []
        for student_id, avg_score, total_attempts in student_stats:
            # Consider struggling if low average score or few attempts
            if (avg_score and avg_score < 60) or total_attempts < 3:
                user = User.query.get(student_id)
                if user:
                    struggling_students.append({
                        'student_id': str(student_id),
                        'student_name': user.full_name,
                        'average_score': round(avg_score, 2) if avg_score else 0,
                        'total_attempts': total_attempts,
                        'reason': 'Low average score' if avg_score and avg_score < 60 else 'Few attempts'
                    })
        
        return struggling_students[:limit]
    
    @classmethod
    def _create_enrollment_notification(cls, student_id: str, class_obj: Class, action: str):
        """Create notification for enrollment/unenrollment."""
        try:
            if action == 'enrolled':
                title = f"Enrolled in {class_obj.name}"
                message = f"You have been enrolled in the class '{class_obj.name}' taught by {class_obj.professor.full_name}."
            else:
                title = f"Unenrolled from {class_obj.name}"
                message = f"You have been unenrolled from the class '{class_obj.name}'."
            
            notification = Notification(
                user_id=student_id,
                type='class_enrollment',
                title=title,
                message=message,
                data={
                    'class_id': class_obj.id,
                    'class_name': class_obj.name,
                    'action': action
                }
            )
            
            db.session.add(notification)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error creating enrollment notification: {str(e)}")
    
    @classmethod
    def _notify_students_of_assignment(cls, class_id: int, exercise: Exercise, 
                                     assignment: ClassExerciseAssignment):
        """Notify all students in class of new assignment."""
        try:
            # Get all enrolled students
            enrollments = ClassEnrollment.query.filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.enrollment_status == 'active'
                )
            ).all()
            
            for enrollment in enrollments:
                notification = Notification(
                    user_id=enrollment.student_id,
                    type='exercise_assigned',
                    title=f"New Assignment: {exercise.title}",
                    message=f"A new exercise '{exercise.title}' has been assigned to your class.",
                    data={
                        'exercise_id': exercise.id,
                        'assignment_id': assignment.id,
                        'class_id': class_id,
                        'due_date': assignment.due_date.isoformat() if assignment.due_date else None
                    }
                )
                
                db.session.add(notification)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error notifying students of assignment: {str(e)}")
