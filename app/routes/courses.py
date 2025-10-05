from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import Course, Enrollment, User
from app.utils.auth import token_required, role_required
from app.utils.validation import CourseSchema
from app import db

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('', methods=['GET'])
@token_required
def get_courses(current_user):
    """
    Get All Courses
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    responses:
      200:
        description: List of courses
    """
    if current_user.role == 'student':
        # Students see only enrolled courses
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        courses = [enrollment.course for enrollment in enrollments]
    elif current_user.role == 'professor':
        # Professors see their own courses
        courses = Course.query.filter_by(professor_id=current_user.id).all()
    else:
        # Admins see all courses
        courses = Course.query.all()
    
    return jsonify([course.to_dict() for course in courses]), 200

@courses_bp.route('/<int:course_id>', methods=['GET'])
@token_required
def get_course(current_user, course_id):
    """
    Get Single Course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    parameters:
      - in: path
        name: course_id
        type: integer
        required: true
    responses:
      200:
        description: Course details
      404:
        description: Course not found
    """
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course_id
        ).first()
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 403
    elif current_user.role == 'professor' and course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to view this course'}), 403
    
    return jsonify(course.to_dict()), 200

@courses_bp.route('', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def create_course(current_user):
    """
    Create New Course
    ---
    tags:
      - Courses
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
    responses:
      201:
        description: Course created successfully
      400:
        description: Validation error
    """
    try:
        schema = CourseSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    new_course = Course(
        title=data['title'],
        description=data.get('description', ''),
        professor_id=current_user.id
    )
    
    db.session.add(new_course)
    db.session.commit()
    
    return jsonify({
        'message': 'Course created successfully',
        'course': new_course.to_dict()
    }), 201

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@token_required
@role_required('professor', 'admin')
def update_course(current_user, course_id):
    """
    Update Course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    parameters:
      - in: path
        name: course_id
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
    responses:
      200:
        description: Course updated successfully
      404:
        description: Course not found
      403:
        description: Not authorized
    """
    course = Course.query.get_or_404(course_id)
    
    # Check if professor owns this course (admins can edit any)
    if current_user.role == 'professor' and course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to edit this course'}), 403
    
    try:
        schema = CourseSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    course.title = data['title']
    course.description = data.get('description', course.description)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Course updated successfully',
        'course': course.to_dict()
    }), 200

@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@token_required
@role_required('professor', 'admin')
def delete_course(current_user, course_id):
    """
    Delete Course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    parameters:
      - in: path
        name: course_id
        type: integer
        required: true
    responses:
      200:
        description: Course deleted successfully
      404:
        description: Course not found
      403:
        description: Not authorized
    """
    course = Course.query.get_or_404(course_id)
    
    # Check if professor owns this course (admins can delete any)
    if current_user.role == 'professor' and course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this course'}), 403
    
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'message': 'Course deleted successfully'}), 200

@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@token_required
@role_required('student')
def enroll_in_course(current_user, course_id):
    """
    Enroll in Course
    ---
    tags:
      - Courses
    security:
      - Bearer: []
    parameters:
      - in: path
        name: course_id
        type: integer
        required: true
    responses:
      201:
        description: Enrolled successfully
      400:
        description: Already enrolled
      404:
        description: Course not found
    """
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    # Create enrollment
    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Enrolled successfully',
        'enrollment': enrollment.to_dict()
    }), 201
