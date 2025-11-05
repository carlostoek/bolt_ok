import logging
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository with basic CRUD operations.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initializes the repository.

        :param model: The SQLAlchemy model class.
        :param session: The SQLAlchemy async session.
        """
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: Any) -> ModelType | None:
        """
        Retrieves an entity by its primary key.

        :param entity_id: The ID of the entity.
        :return: The entity instance or None if not found.
        """
        try:
            # Assuming the primary key column is named 'id'
            return await self.session.get(self.model, entity_id)
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {entity_id}: {e}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Retrieves all entities with pagination.

        :param skip: Number of records to skip.
        :param limit: Maximum number of records to return.
        :return: A list of entity instances.
        """
        try:
            stmt = select(self.model).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []

    async def create(self, data: dict) -> ModelType:
        """
        Creates a new entity.

        :param data: A dictionary with the entity's data.
        :return: The created entity instance.
        """
        try:
            instance = self.model(**data)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__} with data {data}: {e}")
            await self.session.rollback()
            raise

    async def update(self, entity_id: Any, data: dict) -> ModelType | None:
        """
        Updates an existing entity.

        :param entity_id: The ID of the entity to update.
        :param data: A dictionary with the new data.
        :return: The updated entity instance or None if not found.
        """
        try:
            instance = await self.get_by_id(entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await self.session.flush()
                await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} with id {entity_id}: {e}")
            await self.session.rollback()
            raise

    async def delete(self, entity_id: Any) -> bool:
        """
        Deletes an entity by its ID.

        :param entity_id: The ID of the entity to delete.
        :return: True if deletion was successful, False otherwise.
        """
        try:
            instance = await self.get_by_id(entity_id)
            if instance:
                await self.session.delete(instance)
                await self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} with id {entity_id}: {e}")
            await self.session.rollback()
            return False
