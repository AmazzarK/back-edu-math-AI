"""
Chat API endpoints for AI tutoring functionality.
"""
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
import logging

from app.services.chat import ChatService
from app.services.ai_provider import AIProviderService
from app.utils.decorators import handle_exceptions
from app.utils.validators import validate_json_request

logger = logging.getLogger(__name__)


class ChatMessageSchema(Schema):
    """Schema for chat message validation."""
    message = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    conversation_id = fields.Int(required=False, allow_none=True)
    context_type = fields.Str(required=False, validate=lambda x: x in ['general', 'exercise', 'homework'])
    context_data = fields.Dict(required=False)


class ChatConversationResource(Resource):
    """Resource for managing chat conversations."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get user's chat conversations."""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 50)
            
            conversations = ChatService.get_user_conversations(
                user_id=user_id,
                page=page,
                per_page=per_page
            )
            
            return jsonify({
                'success': True,
                'data': conversations
            })
            
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve conversations'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def post(self):
        """Create a new chat conversation."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            schema = ChatMessageSchema()
            validated_data = schema.load(data)
            
            # Create conversation and send first message
            response = ChatService.send_message(
                user_id=user_id,
                message=validated_data['message'],
                conversation_id=validated_data.get('conversation_id'),
                context_type=validated_data.get('context_type', 'general'),
                context_data=validated_data.get('context_data', {})
            )
            
            return jsonify({
                'success': True,
                'data': response
            }), 201
            
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': 'Invalid input data',
                'errors': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to create conversation'
            }), 500


class ChatMessageResource(Resource):
    """Resource for sending chat messages."""
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def post(self):
        """Send a message in a chat conversation."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Validate input
            schema = ChatMessageSchema()
            validated_data = schema.load(data)
            
            # Send message
            response = ChatService.send_message(
                user_id=user_id,
                message=validated_data['message'],
                conversation_id=validated_data.get('conversation_id'),
                context_type=validated_data.get('context_type', 'general'),
                context_data=validated_data.get('context_data', {})
            )
            
            return jsonify({
                'success': True,
                'data': response
            })
            
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': 'Invalid input data',
                'errors': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to send message'
            }), 500


class ChatConversationDetailResource(Resource):
    """Resource for individual conversation management."""
    
    @jwt_required()
    @handle_exceptions
    def get(self, conversation_id):
        """Get conversation details with messages."""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            
            conversation = ChatService.get_conversation_with_messages(
                conversation_id=conversation_id,
                user_id=user_id,
                page=page,
                per_page=per_page
            )
            
            if not conversation:
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found'
                }), 404
            
            return jsonify({
                'success': True,
                'data': conversation
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve conversation'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def put(self, conversation_id):
        """Update conversation (e.g., title)."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            # Simple validation for title update
            if 'title' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Title is required'
                }), 400
            
            title = data['title'].strip()
            if not title or len(title) > 200:
                return jsonify({
                    'success': False,
                    'message': 'Title must be between 1 and 200 characters'
                }), 400
            
            updated_conversation = ChatService.update_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                updates={'title': title}
            )
            
            if not updated_conversation:
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found'
                }), 404
            
            return jsonify({
                'success': True,
                'data': updated_conversation.to_dict()
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update conversation'
            }), 500
    
    @jwt_required()
    @handle_exceptions
    def delete(self, conversation_id):
        """Delete a conversation."""
        try:
            user_id = get_jwt_identity()
            
            success = ChatService.delete_conversation(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            if not success:
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'Conversation deleted successfully'
            })
            
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to delete conversation'
            }), 500


class ChatSuggestionsResource(Resource):
    """Resource for getting AI suggestions and help."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get suggested conversation starters or help topics."""
        try:
            user_id = get_jwt_identity()
            
            # Get context-aware suggestions
            suggestions = ChatService.get_conversation_suggestions(user_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'suggestions': suggestions
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting chat suggestions: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get suggestions'
            }), 500


class ChatAnalyticsResource(Resource):
    """Resource for chat analytics and insights."""
    
    @jwt_required()
    @handle_exceptions
    def get(self):
        """Get chat analytics for the user."""
        try:
            user_id = get_jwt_identity()
            
            analytics = ChatService.get_user_chat_analytics(user_id)
            
            return jsonify({
                'success': True,
                'data': analytics
            })
            
        except Exception as e:
            logger.error(f"Error getting chat analytics: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get analytics'
            }), 500


class ChatExerciseHelpResource(Resource):
    """Resource for getting AI help with specific exercises."""
    
    @jwt_required()
    @handle_exceptions
    @validate_json_request
    def post(self, exercise_id):
        """Get AI help for a specific exercise."""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            question = data.get('question', '').strip()
            if not question:
                return jsonify({
                    'success': False,
                    'message': 'Question is required'
                }), 400
            
            # Get exercise help
            response = ChatService.get_exercise_help(
                user_id=user_id,
                exercise_id=exercise_id,
                question=question,
                student_answer=data.get('student_answer'),
                hint_level=data.get('hint_level', 'medium')
            )
            
            return jsonify({
                'success': True,
                'data': response
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error getting exercise help for {exercise_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get exercise help'
            }), 500


# Register routes
def register_chat_routes(api):
    """Register chat API routes."""
    api.add_resource(ChatConversationResource, '/api/chat/conversations')
    api.add_resource(ChatMessageResource, '/api/chat/message')
    api.add_resource(ChatConversationDetailResource, '/api/chat/conversations/<int:conversation_id>')
    api.add_resource(ChatSuggestionsResource, '/api/chat/suggestions')
    api.add_resource(ChatAnalyticsResource, '/api/chat/analytics')
    api.add_resource(ChatExerciseHelpResource, '/api/chat/exercise/<int:exercise_id>/help')
