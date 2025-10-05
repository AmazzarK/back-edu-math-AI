from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import User, Course
from app.utils.auth import token_required, role_required, hash_password
from app.utils.validation import UserRegistrationSchema
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_all_users(current_user):
    """
    Get All Users
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: List of all users
    """
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@admin_bp.route('/users', methods=['POST'])
@token_required
@role_required('admin')
def create_user(current_user):
    """
    Create New User (Admin Only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            full_name:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: string
              enum: [student, professor, admin]
    responses:
      201:
        description: User created successfully
      400:
        description: Validation error or user already exists
    """
    try:
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User with this email already exists'}), 400
    
    # Create new user
    hashed_password = hash_password(data['password'])
    new_user = User(
        full_name=data['full_name'],
        email=data['email'],
        password_hash=hashed_password,
        role=data['role']
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': new_user.to_dict()
    }), 201

@admin_bp.route('/users/<user_id>', methods=['GET'])
@token_required
@role_required('admin')
def get_user(current_user, user_id):
    """
    Get Single User
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
@role_required('admin')
def update_user(current_user, user_id):
    """
    Update User
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            full_name:
              type: string
            email:
              type: string
            role:
              type: string
              enum: [student, professor, admin]
    responses:
      200:
        description: User updated successfully
      404:
        description: User not found
      400:
        description: Validation error
    """
    user = User.query.get_or_404(user_id)
    
    try:
        schema = UserRegistrationSchema(partial=True, exclude=['password'])
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if email is being changed and if it's already taken
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already taken'}), 400
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(current_user, user_id):
    """
    Delete User
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
      400:
        description: Cannot delete yourself
    """
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if str(user.id) == str(current_user.id):
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@admin_bp.route('/courses', methods=['GET'])
@token_required
@role_required('admin')
def get_all_courses(current_user):
    """
    Get All Courses (Admin View)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: List of all courses with enrollment counts
    """
    courses = Course.query.all()
    
    courses_data = []
    for course in courses:
        course_dict = course.to_dict()
        course_dict['enrollment_count'] = len(course.enrollments)
        course_dict['test_count'] = len(course.tests)
        course_dict['exercise_count'] = len(course.exercises)
        courses_data.append(course_dict)
    
    return jsonify(courses_data), 200

@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required('admin')
def get_system_stats(current_user):
    """
    Get System Statistics
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: System statistics
    """
    stats = {
        'total_users': User.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'professors': User.query.filter_by(role='professor').count(),
        'admins': User.query.filter_by(role='admin').count(),
        'total_courses': Course.query.count(),
        'total_enrollments': db.session.query(db.func.count(db.distinct(db.text('enrollments.id')))).scalar() or 0
    }
    
    return jsonify(stats), 200
