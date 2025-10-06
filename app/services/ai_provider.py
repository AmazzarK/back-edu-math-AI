"""
AI Provider abstraction layer for chatbot functionality.
Supports OpenAI and can be extended for other providers.
"""
import os
import openai
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Custom exception for AI provider errors."""
    pass


class BaseAIProvider:
    """Base class for AI providers."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    def generate_response(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate AI response from messages."""
        raise NotImplementedError
    
    def generate_math_help(self, question: str, context: Optional[Dict] = None) -> str:
        """Generate math help response."""
        raise NotImplementedError


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        openai.api_key = api_key
        self.model = kwargs.get('model', 'gpt-3.5-turbo')
        self.max_tokens = kwargs.get('max_tokens', 1000)
        self.temperature = kwargs.get('temperature', 0.7)
    
    def generate_response(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            # Prepare messages for OpenAI format
            openai_messages = self._prepare_messages(messages)
            
            response = openai.ChatCompletion.create(
                model=kwargs.get('model', self.model),
                messages=openai_messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                presence_penalty=kwargs.get('presence_penalty', 0.0)
            )
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'usage': response.usage._asdict() if response.usage else {},
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
        except openai.error.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise AIProviderError("Rate limit exceeded. Please try again later.")
        
        except openai.error.InvalidRequestError as e:
            logger.error(f"OpenAI invalid request: {str(e)}")
            raise AIProviderError("Invalid request. Please check your input.")
        
        except openai.error.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise AIProviderError("Authentication failed. Please check API configuration.")
        
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise AIProviderError(f"AI service unavailable: {str(e)}")
    
    def generate_math_help(self, question: str, context: Optional[Dict] = None) -> str:
        """Generate math help response with educational context."""
        try:
            # Create educational context
            system_prompt = self._create_math_tutor_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            response = self.generate_response(messages, temperature=0.5)
            
            if response['success']:
                return response['content']
            else:
                raise AIProviderError("Failed to generate math help response")
                
        except Exception as e:
            logger.error(f"Error generating math help: {str(e)}")
            raise
    
    def _prepare_messages(self, messages: List[Dict]) -> List[Dict]:
        """Prepare messages for OpenAI format."""
        openai_messages = []
        
        for msg in messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                openai_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        return openai_messages
    
    def _create_math_tutor_prompt(self, context: Optional[Dict] = None) -> str:
        """Create system prompt for math tutoring."""
        base_prompt = """You are a helpful and patient mathematics tutor for students. Your role is to:

1. Provide clear, step-by-step explanations for math problems
2. Use encouraging and supportive language
3. Break down complex problems into simpler steps
4. Provide examples when helpful
5. Ask follow-up questions to ensure understanding
6. Avoid giving direct answers without explanation

Guidelines:
- Always explain the reasoning behind each step
- Use simple language appropriate for the student's level
- Encourage the student to think through the problem
- Provide hints rather than complete solutions when possible
- Be patient and supportive, especially when students are struggling

"""
        
        if context:
            # Add contextual information
            if context.get('student_level'):
                base_prompt += f"\nStudent Level: {context['student_level']}"
            
            if context.get('subject_focus'):
                base_prompt += f"\nSubject Focus: {context['subject_focus']}"
            
            if context.get('recent_topics'):
                base_prompt += f"\nRecent Topics Covered: {', '.join(context['recent_topics'])}"
            
            if context.get('difficulty_areas'):
                base_prompt += f"\nAreas of Difficulty: {', '.join(context['difficulty_areas'])}"
        
        return base_prompt


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing and development."""
    
    def __init__(self, api_key: str = "mock", **kwargs):
        super().__init__(api_key, **kwargs)
    
    def generate_response(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate mock response."""
        last_message = messages[-1] if messages else {}
        user_content = last_message.get('content', '')
        
        # Simple rule-based responses for testing
        mock_responses = [
            "I understand you're asking about math. Let me help you with that step by step.",
            "That's a great question! Let's break this problem down together.",
            "I can see this involves mathematical concepts. Here's how we can approach it:",
            "Mathematics can be challenging, but let's work through this systematically."
        ]
        
        import random
        response_content = random.choice(mock_responses)
        
        if 'equation' in user_content.lower() or 'solve' in user_content.lower():
            response_content += " To solve this equation, we'll need to isolate the variable."
        
        return {
            'success': True,
            'content': response_content,
            'usage': {'total_tokens': 50, 'prompt_tokens': 20, 'completion_tokens': 30},
            'model': 'mock-model',
            'finish_reason': 'stop'
        }
    
    def generate_math_help(self, question: str, context: Optional[Dict] = None) -> str:
        """Generate mock math help response."""
        response = self.generate_response([{"role": "user", "content": question}])
        return response['content']


class AIProviderFactory:
    """Factory for creating AI provider instances."""
    
    providers = {
        'openai': OpenAIProvider,
        'mock': MockAIProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, api_key: str, **kwargs) -> BaseAIProvider:
        """Create AI provider instance."""
        if provider_type not in cls.providers:
            raise ValueError(f"Unsupported AI provider: {provider_type}")
        
        provider_class = cls.providers[provider_type]
        return provider_class(api_key, **kwargs)
    
    @classmethod
    def get_default_provider(cls) -> BaseAIProvider:
        """Get default configured provider."""
        provider_type = os.getenv('AI_PROVIDER', 'mock')
        api_key = os.getenv('OPENAI_API_KEY', 'mock-key')
        
        config = {
            'model': os.getenv('AI_MODEL', 'gpt-3.5-turbo'),
            'max_tokens': int(os.getenv('AI_MAX_TOKENS', '1000')),
            'temperature': float(os.getenv('AI_TEMPERATURE', '0.7'))
        }
        
        return cls.create_provider(provider_type, api_key, **config)


class ChatbotService:
    """High-level service for chatbot functionality."""
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        self.ai_provider = ai_provider or AIProviderFactory.get_default_provider()
    
    def generate_response(self, conversation_messages: List[Dict], 
                         user_context: Optional[Dict] = None) -> str:
        """Generate chatbot response with context."""
        try:
            # Add system context if needed
            if user_context:
                system_msg = self._create_contextual_system_message(user_context)
                messages = [system_msg] + conversation_messages
            else:
                messages = conversation_messages
            
            response = self.ai_provider.generate_response(messages)
            
            if response['success']:
                return response['content']
            else:
                return "I'm sorry, I couldn't generate a response right now. Please try again."
                
        except AIProviderError as e:
            logger.error(f"AI Provider error: {str(e)}")
            return f"Sorry, I'm having trouble right now: {str(e)}"
        
        except Exception as e:
            logger.error(f"Chatbot service error: {str(e)}")
            return "I'm experiencing technical difficulties. Please try again later."
    
    def generate_math_help(self, question: str, student_context: Optional[Dict] = None) -> str:
        """Generate math-specific help response."""
        try:
            return self.ai_provider.generate_math_help(question, student_context)
        except Exception as e:
            logger.error(f"Math help generation error: {str(e)}")
            return "I'm having trouble helping with math right now. Please try asking your question differently."
    
    def _create_contextual_system_message(self, context: Dict) -> Dict[str, str]:
        """Create system message with user context."""
        context_info = []
        
        if context.get('user_role'):
            context_info.append(f"User role: {context['user_role']}")
        
        if context.get('recent_subjects'):
            context_info.append(f"Recent subjects: {', '.join(context['recent_subjects'])}")
        
        if context.get('difficulty_level'):
            context_info.append(f"Preferred difficulty: {context['difficulty_level']}")
        
        system_content = "You are a helpful math tutor. "
        if context_info:
            system_content += f"Context: {'; '.join(context_info)}. "
        
        system_content += "Provide educational, encouraging responses."
        
        return {"role": "system", "content": system_content}
