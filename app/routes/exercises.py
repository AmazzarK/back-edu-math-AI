from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import Exercise, Course, Enrollment
from app.utils.auth import token_required, role_required
from app.utils.validation import ExerciseSchema
from app import db

exercises_bp = Blueprint('exercises', __name__)

@exercises_bp.route('', methods=['GET'])
@token_required
def get_exercises(current_user):
    """
    Get Exercises
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    responses:
      200:
        description: List of exercises
    """
    if current_user.role == 'student':
        # Students see exercises from enrolled courses
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        course_ids = [enrollment.course_id for enrollment in enrollments]
        exercises = Exercise.query.filter(Exercise.course_id.in_(course_ids)).all()
    elif current_user.role == 'professor':
        # Professors see exercises from their courses
        courses = Course.query.filter_by(professor_id=current_user.id).all()
        course_ids = [course.id for course in courses]
        exercises = Exercise.query.filter(Exercise.course_id.in_(course_ids)).all()
    else:
        # Admins see all exercises
        exercises = Exercise.query.all()
    
    return jsonify([exercise.to_dict() for exercise in exercises]), 200

@exercises_bp.route('/<int:exercise_id>', methods=['GET'])
@token_required
def get_exercise(current_user, exercise_id):
    """
    Get Single Exercise
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: exercise_id
        type: integer
        required: true
    responses:
      200:
        description: Exercise details
      404:
        description: Exercise not found
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check permissions
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=exercise.course_id
        ).first()
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 403
    elif current_user.role == 'professor':
        if exercise.course.professor_id != current_user.id:
            return jsonify({'error': 'Not authorized to view this exercise'}), 403
    
    return jsonify(exercise.to_dict()), 200

@exercises_bp.route('', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def create_exercise(current_user):
    """
    Create New Exercise
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            content:
              type: object
            course_id:
              type: integer
    responses:
      201:
        description: Exercise created successfully
      400:
        description: Validation error
      403:
        description: Not authorized
    """
    try:
        schema = ExerciseSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if professor owns the course
    course = Course.query.get_or_404(data['course_id'])
    if current_user.role == 'professor' and course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to create exercise for this course'}), 403
    
    new_exercise = Exercise(
        title=data['title'],
        description=data.get('description', ''),
        content=data.get('content', {}),
        course_id=data['course_id']
    )
    
    db.session.add(new_exercise)
    db.session.commit()
    
    return jsonify({
        'message': 'Exercise created successfully',
        'exercise': new_exercise.to_dict()
    }), 201

@exercises_bp.route('/<int:exercise_id>', methods=['PUT'])
@token_required
@role_required('professor', 'admin')
def update_exercise(current_user, exercise_id):
    """
    Update Exercise
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: exercise_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            content:
              type: object
    responses:
      200:
        description: Exercise updated successfully
      404:
        description: Exercise not found
      403:
        description: Not authorized
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if professor owns the course
    if current_user.role == 'professor' and exercise.course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to edit this exercise'}), 403
    
    try:
        # Use partial loading for updates
        schema = ExerciseSchema(partial=True)
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    if 'title' in data:
        exercise.title = data['title']
    if 'description' in data:
        exercise.description = data['description']
    if 'content' in data:
        exercise.content = data['content']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Exercise updated successfully',
        'exercise': exercise.to_dict()
    }), 200

@exercises_bp.route('/<int:exercise_id>', methods=['DELETE'])
@token_required
@role_required('professor', 'admin')
def delete_exercise(current_user, exercise_id):
    """
    Delete Exercise
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: exercise_id
        type: integer
        required: true
    responses:
      200:
        description: Exercise deleted successfully
      404:
        description: Exercise not found
      403:
        description: Not authorized
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if professor owns the course
    if current_user.role == 'professor' and exercise.course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this exercise'}), 403
    
    db.session.delete(exercise)
    db.session.commit()
    
    return jsonify({'message': 'Exercise deleted successfully'}), 200

@exercises_bp.route('/<int:exercise_id>/submit', methods=['POST'])
@token_required
@role_required('student')
def submit_exercise(current_user, exercise_id):
    """
    Submit Exercise Work
    ---
    tags:
      - Exercises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: exercise_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            submission:
              type: object
    responses:
      200:
        description: Exercise submitted successfully
      403:
        description: Not enrolled in course
      404:
        description: Exercise not found
    """
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=exercise.course_id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    submission_data = request.json.get('submission', {})
    
    # Here you would typically save the submission to a separate table
    # For now, we'll just return success
    # In a real implementation, you'd have an ExerciseSubmission model
    
    return jsonify({
        'message': 'Exercise submitted successfully',
        'exercise_id': exercise_id,
        'student_id': str(current_user.id)
    }), 200
