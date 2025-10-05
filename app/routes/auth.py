from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import User
from app.utils.auth import hash_password, check_password, generate_token, token_required
from app.utils.validation import UserRegistrationSchema, UserLoginSchema
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
      - Authentication
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

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    try:
        schema = UserLoginSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password(user.password_hash, data['password']):
        token = generate_token(user.id, user.role)
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user_info(current_user):
    """
    Get Current User Info
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user information
      401:
        description: Unauthorized
    """
    return jsonify(current_user.to_dict()), 200
