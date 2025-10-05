from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import Badge, StudentBadge, User
from app.utils.auth import token_required, role_required
from app.utils.validation import BadgeSchema, BadgeAssignmentSchema
from app import db

badges_bp = Blueprint('badges', __name__)

@badges_bp.route('', methods=['GET'])
@token_required
def get_badges(current_user):
    """
    Get All Badges
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    responses:
      200:
        description: List of all available badges
    """
    badges = Badge.query.all()
    return jsonify([badge.to_dict() for badge in badges]), 200

@badges_bp.route('', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def create_badge(current_user):
    """
    Create New Badge
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            icon_url:
              type: string
    responses:
      201:
        description: Badge created successfully
      400:
        description: Validation error
    """
    try:
        schema = BadgeSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    new_badge = Badge(
        name=data['name'],
        description=data.get('description', ''),
        icon_url=data.get('icon_url')
    )
    
    db.session.add(new_badge)
    db.session.commit()
    
    return jsonify({
        'message': 'Badge created successfully',
        'badge': new_badge.to_dict()
    }), 201

@badges_bp.route('/assign', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def assign_badge(current_user):
    """
    Assign Badge to Student
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            student_id:
              type: string
            badge_id:
              type: integer
    responses:
      201:
        description: Badge assigned successfully
      400:
        description: Validation error or badge already assigned
      404:
        description: Student or badge not found
    """
    try:
        schema = BadgeAssignmentSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Verify student exists and is a student
    student = User.query.filter_by(id=data['student_id'], role='student').first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Verify badge exists
    badge = Badge.query.get(data['badge_id'])
    if not badge:
        return jsonify({'error': 'Badge not found'}), 404
    
    # Check if badge already assigned
    existing_assignment = StudentBadge.query.filter_by(
        student_id=data['student_id'],
        badge_id=data['badge_id']
    ).first()
    
    if existing_assignment:
        return jsonify({'error': 'Badge already assigned to this student'}), 400
    
    # Create assignment
    student_badge = StudentBadge(
        student_id=data['student_id'],
        badge_id=data['badge_id']
    )
    
    db.session.add(student_badge)
    db.session.commit()
    
    return jsonify({
        'message': 'Badge assigned successfully',
        'assignment': student_badge.to_dict()
    }), 201

@badges_bp.route('/student/achievements', methods=['GET'])
@token_required
@role_required('student')
def get_student_achievements(current_user):
    """
    Get Student's Earned Badges
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    responses:
      200:
        description: List of student's earned badges
    """
    student_badges = StudentBadge.query.filter_by(student_id=current_user.id).all()
    return jsonify([sb.to_dict() for sb in student_badges]), 200

@badges_bp.route('/<int:badge_id>', methods=['PUT'])
@token_required
@role_required('admin')
def update_badge(current_user, badge_id):
    """
    Update Badge
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    parameters:
      - in: path
        name: badge_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            icon_url:
              type: string
    responses:
      200:
        description: Badge updated successfully
      404:
        description: Badge not found
    """
    badge = Badge.query.get_or_404(badge_id)
    
    try:
        schema = BadgeSchema(partial=True)
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    if 'name' in data:
        badge.name = data['name']
    if 'description' in data:
        badge.description = data['description']
    if 'icon_url' in data:
        badge.icon_url = data['icon_url']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Badge updated successfully',
        'badge': badge.to_dict()
    }), 200

@badges_bp.route('/<int:badge_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_badge(current_user, badge_id):
    """
    Delete Badge
    ---
    tags:
      - Badges
    security:
      - Bearer: []
    parameters:
      - in: path
        name: badge_id
        type: integer
        required: true
    responses:
      200:
        description: Badge deleted successfully
      404:
        description: Badge not found
    """
    badge = Badge.query.get_or_404(badge_id)
    
    db.session.delete(badge)
    db.session.commit()
    
    return jsonify({'message': 'Badge deleted successfully'}), 200
