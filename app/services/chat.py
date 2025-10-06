"""
Chat service for managing AI chatbot conversations.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, desc
from app.extensions import db, cache
from app.models import ChatConversation, User
from app.services.base import BaseService
from app.services.ai_provider import ChatbotService, AIProviderFactory
from app.utils.cache import cache_key, get_cached_result, set_cached_result

logger = logging.getLogger(__name__)


class ChatService(BaseService):
    """Service for managing chat conversations."""
    
    model = ChatConversation
    
    def __init__(self):
        self.chatbot_service = ChatbotService()
    
    @classmethod
    def start_conversation(cls, user_id: str, initial_message: Optional[str] = None) -> ChatConversation:
        """Start a new conversation."""
        try:
            conversation = ChatConversation(
                user_id=user_id,
                messages=[],
                context={},
                is_active=True
            )
            
            if initial_message:
                conversation.add_message('user', initial_message)
            
            db.session.add(conversation)
            db.session.commit()
            
            logger.info(f"New conversation started: {conversation.id} for user {user_id}")
            return conversation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting conversation for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def send_message(cls, conversation_id: int, user_id: str, message: str) -> Dict[str, Any]:
        """Send a message and get AI response."""
        try:
            conversation = cls.get_by_id(conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")
            
            if str(conversation.user_id) != user_id:
                raise PermissionError("Access denied to this conversation")
            
            if not conversation.is_active:
                raise ValueError("Conversation is not active")
            
            # Add user message
            conversation.add_message('user', message)
            
            # Get user context for better AI responses
            user_context = cls._get_user_context(user_id)
            
            # Prepare conversation history for AI
            ai_messages = cls._prepare_ai_messages(conversation.messages)
            
            # Generate AI response
            chatbot_service = ChatbotService()
            ai_response = chatbot_service.generate_response(ai_messages, user_context)
            
            # Add AI response to conversation
            conversation.add_message('assistant', ai_response, {
                'model_used': 'gpt-3.5-turbo',  # This should come from the AI service
                'response_time': datetime.utcnow().isoformat()
            })
            
            db.session.commit()
            
            # Invalidate cache
            cls._invalidate_conversation_cache(user_id)
            
            logger.info(f"Message sent in conversation {conversation_id}")
            
            return {
                'success': True,
                'conversation': conversation.to_dict(),
                'ai_response': ai_response
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sending message in conversation {conversation_id}: {str(e)}")
            raise
    
    @classmethod
    def get_user_conversations(cls, user_id: str, limit: int = 20) -> List[ChatConversation]:
        """Get conversations for a user."""
        try:
            # Check cache first
            cache_key_str = cache_key('user_conversations', user_id=user_id, limit=limit)
            cached_result = get_cached_result(cache_key_str)
            if cached_result:
                # Convert cached data back to objects
                conversation_ids = [conv['id'] for conv in cached_result]
                return ChatConversation.query.filter(ChatConversation.id.in_(conversation_ids)).all()
            
            conversations = ChatConversation.query.filter(
                ChatConversation.user_id == user_id
            ).order_by(desc(ChatConversation.updated_at)).limit(limit).all()
            
            # Cache the result
            conversation_data = [conv.to_dict(include_messages=False) for conv in conversations]
            set_cached_result(cache_key_str, conversation_data, timeout=300)  # 5 minutes
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def get_conversation_with_messages(cls, conversation_id: int, user_id: str) -> ChatConversation:
        """Get a specific conversation with messages."""
        try:
            conversation = cls.get_by_id(conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")
            
            if str(conversation.user_id) != user_id:
                raise PermissionError("Access denied to this conversation")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            raise
    
    @classmethod
    def delete_conversation(cls, conversation_id: int, user_id: str) -> bool:
        """Delete a conversation."""
        try:
            conversation = cls.get_by_id(conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")
            
            if str(conversation.user_id) != user_id:
                raise PermissionError("Access denied to this conversation")
            
            db.session.delete(conversation)
            db.session.commit()
            
            # Invalidate cache
            cls._invalidate_conversation_cache(user_id)
            
            logger.info(f"Conversation {conversation_id} deleted")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            raise
    
    @classmethod
    def update_conversation_context(cls, conversation_id: int, user_id: str, 
                                   context_updates: Dict) -> ChatConversation:
        """Update conversation context."""
        try:
            conversation = cls.get_by_id(conversation_id)
            if not conversation:
                raise ValueError("Conversation not found")
            
            if str(conversation.user_id) != user_id:
                raise PermissionError("Access denied to this conversation")
            
            if not conversation.context:
                conversation.context = {}
            
            conversation.context.update(context_updates)
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return conversation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating conversation context {conversation_id}: {str(e)}")
            raise
    
    @classmethod
    def get_conversation_analytics(cls, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for user's chat usage."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            conversations = ChatConversation.query.filter(
                and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.created_at >= cutoff_date
                )
            ).all()
            
            total_conversations = len(conversations)
            total_messages = sum(len(conv.messages or []) for conv in conversations)
            user_messages = sum(
                len([msg for msg in (conv.messages or []) if msg.get('role') == 'user'])
                for conv in conversations
            )
            ai_messages = total_messages - user_messages
            
            # Calculate average conversation length
            avg_conversation_length = total_messages / total_conversations if total_conversations > 0 else 0
            
            # Most active days
            daily_activity = {}
            for conv in conversations:
                date_str = conv.created_at.date().isoformat()
                daily_activity[date_str] = daily_activity.get(date_str, 0) + 1
            
            return {
                'period_days': days,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'user_messages': user_messages,
                'ai_messages': ai_messages,
                'avg_conversation_length': round(avg_conversation_length, 1),
                'daily_activity': daily_activity,
                'most_active_day': max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else None
            }
            
        except Exception as e:
            logger.error(f"Error getting chat analytics for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def _get_user_context(cls, user_id: str) -> Dict[str, Any]:
        """Get user context for AI responses."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {}
            
            context = {
                'user_role': user.role,
                'user_name': user.full_name
            }
            
            # Add recent exercise subjects if available
            from app.models import Progress, Exercise
            recent_progress = Progress.query.filter(
                and_(
                    Progress.student_id == user_id,
                    Progress.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).join(Exercise).limit(5).all()
            
            if recent_progress:
                recent_subjects = list(set([p.exercise.subject for p in recent_progress if p.exercise]))
                context['recent_subjects'] = recent_subjects
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context for {user_id}: {str(e)}")
            return {}
    
    @classmethod
    def _prepare_ai_messages(cls, messages: List[Dict]) -> List[Dict]:
        """Prepare conversation messages for AI API."""
        if not messages:
            return []
        
        # Limit to recent messages to avoid token limits
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        # Format for AI API
        ai_messages = []
        for msg in recent_messages:
            if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                ai_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        return ai_messages
    
    @classmethod
    def _invalidate_conversation_cache(cls, user_id: str):
        """Invalidate cached conversation data for user."""
        try:
            # This is a simple implementation - in production, use more sophisticated cache invalidation
            from app.utils.cache import invalidate_cache_pattern
            invalidate_cache_pattern(f'user_conversations*{user_id}*')
        except Exception as e:
            logger.error(f"Error invalidating conversation cache: {str(e)}")


class ChatModerationService:
    """Service for chat content moderation."""
    
    @staticmethod
    def is_appropriate_content(message: str) -> bool:
        """Check if message content is appropriate."""
        # Simple keyword-based filtering
        inappropriate_keywords = [
            'hate', 'violence', 'abuse', 'inappropriate'
        ]
        
        message_lower = message.lower()
        return not any(keyword in message_lower for keyword in inappropriate_keywords)
    
    @staticmethod
    def is_educational_context(message: str) -> bool:
        """Check if message is in educational context."""
        educational_keywords = [
            'math', 'algebra', 'geometry', 'calculus', 'equation',
            'solve', 'problem', 'homework', 'study', 'learn'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in educational_keywords)
    
    @classmethod
    def moderate_message(cls, message: str) -> Dict[str, Any]:
        """Moderate a message before processing."""
        return {
            'is_appropriate': cls.is_appropriate_content(message),
            'is_educational': cls.is_educational_context(message),
            'should_process': cls.is_appropriate_content(message)
        }
