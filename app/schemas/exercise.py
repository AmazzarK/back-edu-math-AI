from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Exercise, Progress
from app.extensions import db


class ExerciseSchema(SQLAlchemyAutoSchema):
    """Schema for Exercise model."""
    
    class Meta:
        model = Exercise
        load_instance = True
        sqla_session = db.session
        exclude = ('solutions',)  # Don't expose solutions by default
    
    # Custom fields with validation
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=1000))
    difficulty = fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    subject = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    type = fields.Str(validate=validate.OneOf(['multiple_choice', 'short_answer', 'calculation', 'essay']))
    questions = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))
    solutions = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))
    max_score = fields.Float(validate=validate.Range(min=0, max=1000))
    time_limit = fields.Int(validate=validate.Range(min=1, max=480))  # 1-480 minutes
    tags = fields.List(fields.Str(), missing=[])
    
    @validates_schema
    def validate_questions_solutions(self, data, **kwargs):
        """Validate that questions and solutions match."""
        questions = data.get('questions', [])
        solutions = data.get('solutions', [])
        
        if len(questions) != len(solutions):
            raise ValidationError("Number of questions must match number of solutions.")
        
        # Validate question structure based on type
        exercise_type = data.get('type', 'multiple_choice')
        
        for i, (question, solution) in enumerate(zip(questions, solutions)):
            if not isinstance(question, dict) or not isinstance(solution, dict):
                raise ValidationError(f"Question and solution {i+1} must be objects.")
            
            if 'text' not in question:
                raise ValidationError(f"Question {i+1} must have a 'text' field.")
            
            if exercise_type == 'multiple_choice':
                if 'options' not in question or len(question['options']) < 2:
                    raise ValidationError(f"Multiple choice question {i+1} must have at least 2 options.")
                if 'correct_option' not in solution:
                    raise ValidationError(f"Solution {i+1} must specify 'correct_option'.")
            
            elif exercise_type in ['calculation', 'short_answer']:
                if 'answer' not in solution:
                    raise ValidationError(f"Solution {i+1} must have an 'answer' field.")


class ExerciseCreateSchema(ExerciseSchema):
    """Schema for creating exercises (includes solutions)."""
    
    class Meta(ExerciseSchema.Meta):
        exclude = ()  # Include solutions for creation


class ExerciseUpdateSchema(Schema):
    """Schema for updating exercises."""
    
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str(validate=validate.Length(max=1000))
    difficulty = fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    subject = fields.Str(validate=validate.Length(min=2, max=100))
    type = fields.Str(validate=validate.OneOf(['multiple_choice', 'short_answer', 'calculation', 'essay']))
    questions = fields.List(fields.Dict(), validate=validate.Length(min=1))
    solutions = fields.List(fields.Dict(), validate=validate.Length(min=1))
    max_score = fields.Float(validate=validate.Range(min=0, max=1000))
    time_limit = fields.Int(validate=validate.Range(min=1, max=480))
    is_published = fields.Bool()
    tags = fields.List(fields.Str())


class ExerciseListSchema(Schema):
    """Schema for listing exercises with filters."""
    
    page = fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = fields.Int(missing=10, validate=validate.Range(min=1, max=100))
    difficulty = fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    subject = fields.Str()
    type = fields.Str(validate=validate.OneOf(['multiple_choice', 'short_answer', 'calculation', 'essay']))
    professor_id = fields.Str()
    search = fields.Str(validate=validate.Length(max=100))
    tags = fields.List(fields.Str())


class ProgressSchema(SQLAlchemyAutoSchema):
    """Schema for Progress model."""
    
    class Meta:
        model = Progress
        load_instance = True
        sqla_session = db.session
    
    # Custom fields
    time_spent = fields.Int(validate=validate.Range(min=0))
    answers = fields.List(fields.Dict(), missing=[])
    feedback = fields.Dict(missing={})


class ProgressSubmissionSchema(Schema):
    """Schema for submitting exercise answers."""
    
    exercise_id = fields.Int(required=True)
    answers = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))
    time_spent = fields.Int(validate=validate.Range(min=0))
    
    @validates_schema
    def validate_answers(self, data, **kwargs):
        """Validate answer format."""
        answers = data.get('answers', [])
        
        for i, answer in enumerate(answers):
            if not isinstance(answer, dict):
                raise ValidationError(f"Answer {i+1} must be an object.")
            
            # Basic validation - specific validation depends on exercise type
            if 'question_index' not in answer:
                answer['question_index'] = i
            
            if 'answer' not in answer and 'selected_option' not in answer:
                raise ValidationError(f"Answer {i+1} must contain either 'answer' or 'selected_option'.")


class ProgressStartSchema(Schema):
    """Schema for starting an exercise."""
    
    exercise_id = fields.Int(required=True)


class AnalyticsStudentSchema(Schema):
    """Schema for student analytics request."""
    
    student_id = fields.Str(required=True)
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    subject = fields.Str()


class AnalyticsClassSchema(Schema):
    """Schema for class analytics request."""
    
    course_id = fields.Int()
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    difficulty = fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    subject = fields.Str()


class AnalyticsOverviewSchema(Schema):
    """Schema for overview analytics request."""
    
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    group_by = fields.Str(validate=validate.OneOf(['day', 'week', 'month']))
