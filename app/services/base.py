from typing import Optional, List, Dict, Any
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common CRUD operations."""
    
    model = None  # Should be overridden in subclasses
    
    @classmethod
    def get_by_id(cls, id: Any) -> Optional[Any]:
        """Get a record by ID."""
        try:
            return cls.model.query.get(id)
        except Exception as e:
            logger.error(f"Error getting {cls.model.__name__} by ID {id}: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, limit: Optional[int] = None) -> List[Any]:
        """Get all records with optional limit."""
        try:
            query = cls.model.query
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all {cls.model.__name__}: {str(e)}")
            return []
    
    @classmethod
    def create(cls, data: Dict) -> Optional[Any]:
        """Create a new record."""
        try:
            instance = cls.model(**data)
            db.session.add(instance)
            db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating {cls.model.__name__}: {str(e)}")
            raise
    
    @classmethod
    def update(cls, id: Any, data: Dict) -> Optional[Any]:
        """Update a record by ID."""
        try:
            instance = cls.get_by_id(id)
            if not instance:
                return None
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating {cls.model.__name__} {id}: {str(e)}")
            raise
    
    @classmethod
    def delete(cls, id: Any) -> bool:
        """Delete a record by ID."""
        try:
            instance = cls.get_by_id(id)
            if not instance:
                return False
            
            db.session.delete(instance)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting {cls.model.__name__} {id}: {str(e)}")
            raise
    
    @classmethod
    def exists(cls, id: Any) -> bool:
        """Check if a record exists by ID."""
        return cls.get_by_id(id) is not None
    
    @classmethod
    def count(cls) -> int:
        """Get total count of records."""
        try:
            return cls.model.query.count()
        except Exception as e:
            logger.error(f"Error counting {cls.model.__name__}: {str(e)}")
            return 0
