import json
import hashlib
from typing import Any, Optional, Dict
from flask import current_app
from app.extensions import cache
import logging

logger = logging.getLogger(__name__)


def cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and kwargs."""
    try:
        # Sort kwargs for consistent keys
        sorted_kwargs = sorted(kwargs.items())
        key_string = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Use hash for long keys
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_string
    except Exception as e:
        logger.error(f"Error generating cache key: {str(e)}")
        return f"{prefix}:default"


def get_cached_result(key: str) -> Optional[Dict[str, Any]]:
    """Get cached result by key."""
    try:
        if not current_app.config.get('CACHE_ENABLED', True):
            return None
        
        cached_data = cache.get(key)
        if cached_data:
            logger.debug(f"Cache hit for key: {key}")
            return cached_data
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Error getting cached result for key {key}: {str(e)}")
        return None


def set_cached_result(key: str, data: Dict[str, Any], timeout: int = 300) -> bool:
    """Set cached result with timeout."""
    try:
        if not current_app.config.get('CACHE_ENABLED', True):
            return False
        
        cache.set(key, data, timeout=timeout)
        logger.debug(f"Cached result for key: {key} with timeout: {timeout}")
        return True
    except Exception as e:
        logger.error(f"Error setting cached result for key {key}: {str(e)}")
        return False


def invalidate_cache_pattern(pattern: str) -> bool:
    """Invalidate cache entries matching a pattern."""
    try:
        # Note: This is a simple implementation
        # In production, consider using Redis SCAN or similar
        cache.clear()
        logger.info(f"Cache cleared for pattern: {pattern}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {str(e)}")
        return False


def warm_cache(key: str, data_func, timeout: int = 300) -> Any:
    """Warm cache with data from function if not exists."""
    try:
        cached_data = get_cached_result(key)
        if cached_data:
            return cached_data
        
        # Generate fresh data
        fresh_data = data_func()
        set_cached_result(key, fresh_data, timeout)
        return fresh_data
    except Exception as e:
        logger.error(f"Error warming cache for key {key}: {str(e)}")
        # Return fresh data even if caching fails
        return data_func()


class CacheManager:
    """Cache manager for exercise and analytics data."""
    
    @staticmethod
    def invalidate_exercise_caches(exercise_id: Optional[int] = None):
        """Invalidate exercise-related caches."""
        try:
            patterns = [
                'exercises_list',
                'exercises_by_professor',
                'exercises_by_subject'
            ]
            
            if exercise_id:
                patterns.extend([
                    f'exercise_{exercise_id}',
                    f'exercise_progress_{exercise_id}'
                ])
            
            for pattern in patterns:
                invalidate_cache_pattern(pattern)
                
        except Exception as e:
            logger.error(f"Error invalidating exercise caches: {str(e)}")
    
    @staticmethod
    def invalidate_analytics_caches(student_id: Optional[str] = None):
        """Invalidate analytics-related caches."""
        try:
            patterns = [
                'class_analytics',
                'overview_analytics'
            ]
            
            if student_id:
                patterns.append(f'student_analytics_{student_id}')
            
            for pattern in patterns:
                invalidate_cache_pattern(pattern)
                
        except Exception as e:
            logger.error(f"Error invalidating analytics caches: {str(e)}")
    
    @staticmethod
    def invalidate_progress_caches(student_id: str, exercise_id: int):
        """Invalidate progress-related caches."""
        try:
            patterns = [
                f'student_progress_{student_id}',
                f'exercise_progress_{exercise_id}',
                f'student_analytics_{student_id}',
                'class_analytics',
                'overview_analytics'
            ]
            
            for pattern in patterns:
                invalidate_cache_pattern(pattern)
                
        except Exception as e:
            logger.error(f"Error invalidating progress caches: {str(e)}")
