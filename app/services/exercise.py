from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Exercise, Progress, User
from app.services.base import BaseService
import logging

logger = logging.getLogger(__name__)


class ExerciseService(BaseService):
    """Service class for exercise operations."""
    
    model = Exercise
    
    @classmethod
    def create_exercise(cls, data: Dict, creator_id: str) -> Exercise:
        """Create a new exercise."""
        try:
            exercise = Exercise(
                title=data['title'],
                description=data.get('description', ''),
                difficulty=data.get('difficulty', 'medium'),
                subject=data['subject'],
                type=data.get('type', 'multiple_choice'),
                questions=data['questions'],
                solutions=data['solutions'],
                created_by=creator_id,
                course_id=data.get('course_id'),
                max_score=data.get('max_score', 100.0),
                time_limit=data.get('time_limit'),
                is_published=data.get('is_published', False),
                tags=data.get('tags', [])
            )
            
            db.session.add(exercise)
            db.session.commit()
            
            logger.info(f"Exercise created: {exercise.id} by user {creator_id}")
            return exercise
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating exercise: {str(e)}")
            raise
    
    @classmethod
    def update_exercise(cls, exercise_id: int, data: Dict, user_id: str) -> Exercise:
        """Update an exercise."""
        try:
            exercise = cls.get_by_id(exercise_id)
            if not exercise:
                raise ValueError("Exercise not found")
            
            # Check ownership for professors
            if str(exercise.created_by) != user_id:
                raise PermissionError("Not authorized to update this exercise")
            
            # Update fields
            for field, value in data.items():
                if hasattr(exercise, field) and field not in ['id', 'created_by', 'created_at']:
                    setattr(exercise, field, value)
            
            exercise.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Exercise updated: {exercise.id}")
            return exercise
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating exercise {exercise_id}: {str(e)}")
            raise
    
    @classmethod
    def delete_exercise(cls, exercise_id: int, user_id: str) -> bool:
        """Delete an exercise."""
        try:
            exercise = cls.get_by_id(exercise_id)
            if not exercise:
                raise ValueError("Exercise not found")
            
            # Check ownership for professors
            if str(exercise.created_by) != user_id:
                raise PermissionError("Not authorized to delete this exercise")
            
            db.session.delete(exercise)
            db.session.commit()
            
            logger.info(f"Exercise deleted: {exercise_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting exercise {exercise_id}: {str(e)}")
            raise
    
    @classmethod
    def get_exercises_with_filters(cls, filters: Dict) -> Tuple[List[Exercise], int]:
        """Get exercises with pagination and filters."""
        try:
            query = Exercise.query.options(joinedload(Exercise.creator))
            
            # Apply filters
            if filters.get('difficulty'):
                query = query.filter(Exercise.difficulty == filters['difficulty'])
            
            if filters.get('subject'):
                query = query.filter(Exercise.subject.ilike(f"%{filters['subject']}%"))
            
            if filters.get('type'):
                query = query.filter(Exercise.type == filters['type'])
            
            if filters.get('professor_id'):
                query = query.filter(Exercise.created_by == filters['professor_id'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Exercise.title.ilike(search_term),
                        Exercise.description.ilike(search_term),
                        Exercise.subject.ilike(search_term)
                    )
                )
            
            if filters.get('tags'):
                # Filter by tags (JSONB contains)
                for tag in filters['tags']:
                    query = query.filter(Exercise.tags.contains([tag]))
            
            # Only show published exercises for students
            query = query.filter(Exercise.is_published == True)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Exercise.created_at))
            
            # Pagination
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 10)
            
            total = query.count()
            exercises = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return exercises, total
            
        except Exception as e:
            logger.error(f"Error getting exercises with filters: {str(e)}")
            raise
    
    @classmethod
    def get_exercises_by_professor(cls, professor_id: str) -> List[Exercise]:
        """Get all exercises created by a professor."""
        try:
            return Exercise.query.filter(Exercise.created_by == professor_id)\
                .order_by(desc(Exercise.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting exercises by professor {professor_id}: {str(e)}")
            raise
    
    @classmethod
    def get_exercises_by_subject(cls, subject: str) -> List[Exercise]:
        """Get exercises by subject."""
        try:
            return Exercise.query.filter(
                and_(
                    Exercise.subject.ilike(f"%{subject}%"),
                    Exercise.is_published == True
                )
            ).order_by(desc(Exercise.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting exercises by subject {subject}: {str(e)}")
            raise


class ProgressService(BaseService):
    """Service class for progress operations."""
    
    model = Progress
    
    @classmethod
    def start_exercise(cls, student_id: str, exercise_id: int) -> Progress:
        """Start an exercise for a student."""
        try:
            # Check if exercise exists and is published
            exercise = Exercise.query.filter(
                and_(Exercise.id == exercise_id, Exercise.is_published == True)
            ).first()
            
            if not exercise:
                raise ValueError("Exercise not found or not published")
            
            # Get or create progress record
            progress = Progress.query.filter(
                and_(Progress.student_id == student_id, Progress.exercise_id == exercise_id)
            ).first()
            
            if not progress:
                progress = Progress(
                    student_id=student_id,
                    exercise_id=exercise_id
                )
                db.session.add(progress)
            
            # Start the attempt
            progress.start_attempt()
            db.session.commit()
            
            logger.info(f"Exercise {exercise_id} started by student {student_id}")
            return progress
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting exercise {exercise_id} for student {student_id}: {str(e)}")
            raise
    
    @classmethod
    def submit_answers(cls, student_id: str, exercise_id: int, answers: List[Dict], 
                      time_spent: Optional[int] = None) -> Progress:
        """Submit answers for an exercise."""
        try:
            # Get progress record
            progress = Progress.query.filter(
                and_(Progress.student_id == student_id, Progress.exercise_id == exercise_id)
            ).first()
            
            if not progress:
                raise ValueError("Progress record not found. Start the exercise first.")
            
            if progress.status not in ['in_progress', 'completed']:
                raise ValueError("Cannot submit answers for this exercise state")
            
            # Update time spent
            if time_spent is not None:
                progress.time_spent = time_spent
            
            # Submit answers and calculate score
            score = progress.submit_answers(answers, auto_score=True)
            
            db.session.commit()
            
            logger.info(f"Answers submitted for exercise {exercise_id} by student {student_id}, score: {score}")
            return progress
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting answers for exercise {exercise_id}: {str(e)}")
            raise
    
    @classmethod
    def get_student_progress(cls, student_id: str, filters: Optional[Dict] = None) -> List[Progress]:
        """Get progress records for a student."""
        try:
            query = Progress.query.filter(Progress.student_id == student_id)\
                .options(joinedload(Progress.exercise))
            
            if filters:
                if filters.get('subject'):
                    query = query.join(Exercise).filter(
                        Exercise.subject.ilike(f"%{filters['subject']}%")
                    )
                
                if filters.get('status'):
                    query = query.filter(Progress.status == filters['status'])
                
                if filters.get('start_date'):
                    query = query.filter(Progress.created_at >= filters['start_date'])
                
                if filters.get('end_date'):
                    query = query.filter(Progress.created_at <= filters['end_date'])
            
            return query.order_by(desc(Progress.updated_at)).all()
            
        except Exception as e:
            logger.error(f"Error getting student progress for {student_id}: {str(e)}")
            raise
    
    @classmethod
    def get_exercise_progress(cls, exercise_id: int) -> List[Progress]:
        """Get progress records for an exercise."""
        try:
            return Progress.query.filter(Progress.exercise_id == exercise_id)\
                .options(joinedload(Progress.student))\
                .order_by(desc(Progress.updated_at)).all()
        except Exception as e:
            logger.error(f"Error getting exercise progress for {exercise_id}: {str(e)}")
            raise


class AnalyticsService:
    """Service class for analytics operations."""
    
    @classmethod
    def get_student_analytics(cls, student_id: str, filters: Optional[Dict] = None) -> Dict:
        """Get comprehensive analytics for a student."""
        try:
            query = Progress.query.filter(Progress.student_id == student_id)
            
            # Apply date filters
            if filters and filters.get('start_date'):
                query = query.filter(Progress.created_at >= filters['start_date'])
            if filters and filters.get('end_date'):
                query = query.filter(Progress.created_at <= filters['end_date'])
            
            progress_records = query.all()
            
            # Calculate metrics
            total_exercises = len(progress_records)
            completed_exercises = len([p for p in progress_records if p.status == 'completed'])
            in_progress_exercises = len([p for p in progress_records if p.status == 'in_progress'])
            
            # Calculate average score
            completed_with_scores = [p for p in progress_records if p.status == 'completed' and p.score is not None]
            avg_score = sum(p.score for p in completed_with_scores) / len(completed_with_scores) if completed_with_scores else 0
            
            # Calculate total time spent
            total_time = sum(p.time_spent or 0 for p in progress_records)
            
            # Subject breakdown
            subject_stats = {}
            for progress in progress_records:
                if progress.exercise and progress.exercise.subject:
                    subject = progress.exercise.subject
                    if subject not in subject_stats:
                        subject_stats[subject] = {
                            'total': 0,
                            'completed': 0,
                            'avg_score': 0,
                            'scores': []
                        }
                    
                    subject_stats[subject]['total'] += 1
                    if progress.status == 'completed':
                        subject_stats[subject]['completed'] += 1
                        if progress.score is not None:
                            subject_stats[subject]['scores'].append(progress.score)
            
            # Calculate averages for subjects
            for subject, stats in subject_stats.items():
                if stats['scores']:
                    stats['avg_score'] = sum(stats['scores']) / len(stats['scores'])
                stats.pop('scores')  # Remove raw scores from output
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_activity = Progress.query.filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.updated_at >= week_ago
                )
            ).count()
            
            return {
                'student_id': student_id,
                'summary': {
                    'total_exercises': total_exercises,
                    'completed_exercises': completed_exercises,
                    'in_progress_exercises': in_progress_exercises,
                    'completion_rate': (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0,
                    'average_score': round(avg_score, 2),
                    'total_time_spent': total_time,
                    'recent_activity': recent_activity
                },
                'subject_breakdown': subject_stats,
                'performance_trend': cls._get_performance_trend(student_id, filters)
            }
            
        except Exception as e:
            logger.error(f"Error getting student analytics for {student_id}: {str(e)}")
            raise
    
    @classmethod
    def get_class_analytics(cls, filters: Optional[Dict] = None) -> Dict:
        """Get class-level analytics."""
        try:
            query = db.session.query(Progress).join(Exercise)
            
            # Apply filters
            if filters:
                if filters.get('course_id'):
                    query = query.filter(Exercise.course_id == filters['course_id'])
                if filters.get('difficulty'):
                    query = query.filter(Exercise.difficulty == filters['difficulty'])
                if filters.get('subject'):
                    query = query.filter(Exercise.subject.ilike(f"%{filters['subject']}%"))
                if filters.get('start_date'):
                    query = query.filter(Progress.created_at >= filters['start_date'])
                if filters.get('end_date'):
                    query = query.filter(Progress.created_at <= filters['end_date'])
            
            progress_records = query.all()
            
            # Calculate class metrics
            total_attempts = len(progress_records)
            completed_attempts = len([p for p in progress_records if p.status == 'completed'])
            
            # Score distribution
            scores = [p.score for p in progress_records if p.score is not None]
            score_ranges = {
                '90-100': len([s for s in scores if s >= 90]),
                '80-89': len([s for s in scores if 80 <= s < 90]),
                '70-79': len([s for s in scores if 70 <= s < 80]),
                '60-69': len([s for s in scores if 60 <= s < 70]),
                'below-60': len([s for s in scores if s < 60])
            }
            
            # Difficulty success rates
            difficulty_stats = {}
            for progress in progress_records:
                if progress.exercise:
                    difficulty = progress.exercise.difficulty
                    if difficulty not in difficulty_stats:
                        difficulty_stats[difficulty] = {
                            'total': 0,
                            'completed': 0,
                            'scores': []
                        }
                    
                    difficulty_stats[difficulty]['total'] += 1
                    if progress.status == 'completed':
                        difficulty_stats[difficulty]['completed'] += 1
                        if progress.score is not None:
                            difficulty_stats[difficulty]['scores'].append(progress.score)
            
            # Calculate success rates
            for difficulty, stats in difficulty_stats.items():
                success_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                difficulty_stats[difficulty] = {
                    'total_attempts': stats['total'],
                    'completed': stats['completed'],
                    'success_rate': round(success_rate, 2),
                    'average_score': round(avg_score, 2)
                }
            
            return {
                'summary': {
                    'total_attempts': total_attempts,
                    'completed_attempts': completed_attempts,
                    'completion_rate': (completed_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                    'average_score': round(sum(scores) / len(scores), 2) if scores else 0
                },
                'score_distribution': score_ranges,
                'difficulty_breakdown': difficulty_stats,
                'active_students': cls._get_active_students_count(filters)
            }
            
        except Exception as e:
            logger.error(f"Error getting class analytics: {str(e)}")
            raise
    
    @classmethod
    def get_overview_analytics(cls, filters: Optional[Dict] = None) -> Dict:
        """Get system overview analytics."""
        try:
            # Basic counts
            total_users = User.query.count()
            total_students = User.query.filter(User.role == 'student').count()
            total_professors = User.query.filter(User.role == 'professor').count()
            total_exercises = Exercise.query.count()
            total_progress = Progress.query.count()
            
            # Recent activity (last 30 days)
            month_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = User.query.filter(User.created_at >= month_ago).count()
            recent_exercises = Exercise.query.filter(Exercise.created_at >= month_ago).count()
            recent_submissions = Progress.query.filter(Progress.updated_at >= month_ago).count()
            
            # Popular subjects
            subject_query = db.session.query(
                Exercise.subject,
                func.count(Progress.id).label('attempts')
            ).join(Progress).group_by(Exercise.subject).order_by(desc('attempts')).limit(10)
            
            popular_subjects = [
                {'subject': row[0], 'attempts': row[1]}
                for row in subject_query.all()
            ]
            
            return {
                'system_overview': {
                    'total_users': total_users,
                    'total_students': total_students,
                    'total_professors': total_professors,
                    'total_exercises': total_exercises,
                    'total_submissions': total_progress
                },
                'recent_activity': {
                    'new_registrations': recent_registrations,
                    'new_exercises': recent_exercises,
                    'new_submissions': recent_submissions
                },
                'popular_subjects': popular_subjects,
                'growth_metrics': cls._get_growth_metrics(filters)
            }
            
        except Exception as e:
            logger.error(f"Error getting overview analytics: {str(e)}")
            raise
    
    @classmethod
    def _get_performance_trend(cls, student_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Get performance trend for a student."""
        try:
            # Get last 10 completed exercises
            query = Progress.query.filter(
                and_(
                    Progress.student_id == student_id,
                    Progress.status == 'completed',
                    Progress.score.isnot(None)
                )
            ).order_by(desc(Progress.completed_at)).limit(10)
            
            progress_records = query.all()
            
            return [
                {
                    'date': p.completed_at.isoformat() if p.completed_at else None,
                    'score': p.score,
                    'exercise_title': p.exercise.title if p.exercise else None
                }
                for p in reversed(progress_records)  # Chronological order
            ]
            
        except Exception as e:
            logger.error(f"Error getting performance trend for student {student_id}: {str(e)}")
            return []
    
    @classmethod
    def _get_active_students_count(cls, filters: Optional[Dict] = None) -> int:
        """Get count of active students (submitted in last 7 days)."""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            return db.session.query(Progress.student_id).filter(
                Progress.updated_at >= week_ago
            ).distinct().count()
        except Exception as e:
            logger.error(f"Error getting active students count: {str(e)}")
            return 0
    
    @classmethod
    def _get_growth_metrics(cls, filters: Optional[Dict] = None) -> Dict:
        """Get growth metrics over time."""
        try:
            # Simple month-over-month growth
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_users = User.query.filter(User.created_at >= current_month).count()
            last_month_users = User.query.filter(
                and_(User.created_at >= last_month, User.created_at < current_month)
            ).count()
            
            current_exercises = Exercise.query.filter(Exercise.created_at >= current_month).count()
            last_month_exercises = Exercise.query.filter(
                and_(Exercise.created_at >= last_month, Exercise.created_at < current_month)
            ).count()
            
            return {
                'user_growth': {
                    'current_month': current_users,
                    'last_month': last_month_users,
                    'growth_rate': ((current_users - last_month_users) / last_month_users * 100) if last_month_users > 0 else 0
                },
                'exercise_growth': {
                    'current_month': current_exercises,
                    'last_month': last_month_exercises,
                    'growth_rate': ((current_exercises - last_month_exercises) / last_month_exercises * 100) if last_month_exercises > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting growth metrics: {str(e)}")
            return {'user_growth': {}, 'exercise_growth': {}}
