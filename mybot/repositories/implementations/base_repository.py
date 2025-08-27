"""Base repository implementation with common functionality."""

import logging
from typing import Type, TypeVar, Generic, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations and query optimization."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
        self._query_cache = {}
    
    async def _execute_query(self, stmt, single: bool = False, use_cache: bool = False):
        """Execute query with error handling and optional caching."""
        try:
            if use_cache:
                cache_key = str(stmt)
                if cache_key in self._query_cache:
                    logger.debug(f"Using cached result for {self.model.__name__}")
                    return self._query_cache[cache_key]
            
            result = await self.session.execute(stmt)
            
            if single:
                data = result.scalar_one_or_none()
            else:
                data = result.scalars().all()
            
            if use_cache:
                self._query_cache[cache_key] = data
            
            return data
        except SQLAlchemyError as e:
            logger.error(f"Database error in {self.model.__name__} repository: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {self.model.__name__} repository: {e}")
            raise
    
    def _clear_cache(self):
        """Clear query cache."""
        self._query_cache.clear()
    
    async def get_by_id(self, id_value: Any) -> Optional[T]:
        """Get entity by primary key."""
        try:
            return await self.session.get(self.model, id_value)
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id_value}: {e}")
            return None
    
    async def get_all(self, limit: Optional[int] = None) -> List[T]:
        """Get all entities with optional limit."""
        stmt = select(self.model)
        if limit:
            stmt = stmt.limit(limit)
        return await self._execute_query(stmt)
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        try:
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            self._clear_cache()
            return entity
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            await self.session.rollback()
            raise
    
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        try:
            await self.session.commit()
            await self.session.refresh(entity)
            self._clear_cache()
            return entity
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            await self.session.rollback()
            raise
    
    async def delete_by_id(self, id_value: Any) -> bool:
        """Delete entity by primary key."""
        try:
            entity = await self.session.get(self.model, id_value)
            if entity:
                await self.session.delete(entity)
                await self.session.commit()
                self._clear_cache()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} with id {id_value}: {e}")
            await self.session.rollback()
            return False
    
    async def exists(self, id_value: Any) -> bool:
        """Check if entity exists by primary key."""
        stmt = select(func.count()).select_from(self.model).where(
            getattr(self.model, 'id') == id_value
        )
        result = await self._execute_query(stmt, single=True)
        return result > 0
    
    async def count(self) -> int:
        """Get total count of entities."""
        stmt = select(func.count()).select_from(self.model)
        return await self._execute_query(stmt, single=True)
    
    async def count_with_conditions(self, **conditions) -> int:
        """Get count with conditions."""
        stmt = select(func.count()).select_from(self.model)
        for field, value in conditions.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        return await self._execute_query(stmt, single=True)
    
    async def find_by_conditions(self, limit: Optional[int] = None, **conditions) -> List[T]:
        """Find entities by conditions."""
        stmt = select(self.model)
        for field, value in conditions.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        if limit:
            stmt = stmt.limit(limit)
        return await self._execute_query(stmt)
    
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in bulk."""
        try:
            self.session.add_all(entities)
            await self.session.commit()
            for entity in entities:
                await self.session.refresh(entity)
            self._clear_cache()
            return entities
        except Exception as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            await self.session.rollback()
            raise
    
    def _build_search_query(self, base_stmt, search_fields: List[str], query: str):
        """Build search query across multiple fields."""
        if not query.strip():
            return base_stmt
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{query}%"))
        
        if search_conditions:
            base_stmt = base_stmt.where(or_(*search_conditions))
        
        return base_stmt
    
    async def search(self, query: str, search_fields: List[str], limit: int = 50) -> List[T]:
        """Search entities across specified fields."""
        stmt = select(self.model)
        stmt = self._build_search_query(stmt, search_fields, query)
        stmt = stmt.limit(limit)
        return await self._execute_query(stmt)
    
    def _add_eager_loading(self, stmt, relationships: List[str]):
        """Add eager loading for relationships."""
        for relationship in relationships:
            if hasattr(self.model, relationship):
                stmt = stmt.options(selectinload(getattr(self.model, relationship)))
        return stmt