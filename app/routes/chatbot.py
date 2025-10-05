from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import ChatbotMessage
from app.utils.auth import token_required, role_required
from app.utils.validation import ChatbotMessageSchema
from app import db

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/messages', methods=['POST'])
@token_required
@role_required('student')
def save_chatbot_message(current_user):
    """
    Save Chatbot Message
    ---
    tags:
      - Chatbot
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
            sender_role:
              type: string
              enum: [student, ai]
    responses:
      201:
        description: Message saved successfully
      400:
        description: Validation error
    """
    try:
        schema = ChatbotMessageSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    new_message = ChatbotMessage(
        user_id=current_user.id,
        sender_role=data['sender_role'],
        message=data['message']
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({
        'message': 'Message saved successfully',
        'chatbot_message': new_message.to_dict()
    }), 201

@chatbot_bp.route('/messages/<user_id>', methods=['GET'])
@token_required
def get_chatbot_history(current_user, user_id):
    """
    Get Chatbot Message History
    ---
    tags:
      - Chatbot
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
    responses:
      200:
        description: Chat history
      403:
        description: Not authorized
    """
    # Students can only view their own chat history
    # Professors and admins can view any student's chat history
    if current_user.role == 'student' and str(current_user.id) != user_id:
        return jsonify({'error': 'Not authorized to view this chat history'}), 403
    
    messages = ChatbotMessage.query.filter_by(user_id=user_id).order_by(ChatbotMessage.created_at).all()
    
    return jsonify([message.to_dict() for message in messages]), 200

@chatbot_bp.route('/messages', methods=['GET'])
@token_required
@role_required('student')
def get_my_chatbot_history(current_user):
    """
    Get My Chatbot Message History
    ---
    tags:
      - Chatbot
    security:
      - Bearer: []
    responses:
      200:
        description: My chat history
    """
    messages = ChatbotMessage.query.filter_by(user_id=current_user.id).order_by(ChatbotMessage.created_at).all()
    
    return jsonify([message.to_dict() for message in messages]), 200
