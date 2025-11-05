import logging
from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.repositories.base_repository import BaseRepository
from database.narrative_models import StoryFragment, NarrativeChoice

logger = logging.getLogger(__name__)

class NarrativeRepository(BaseRepository[StoryFragment]):
    def __init__(self, session: AsyncSession):
        super().__init__(StoryFragment, session)

    async def get_fragment_by_key(self, key: str) -> StoryFragment | None:
        """
        Retrieves a story fragment by its unique key.

        :param key: The unique key of the fragment.
        :return: The StoryFragment instance or None if not found.
        """
        try:
            stmt = select(StoryFragment).where(StoryFragment.key == key).options(selectinload(StoryFragment.choices))
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting fragment by key {key}: {e}")
            return None

    async def get_all_fragments_with_choices(self) -> list[StoryFragment]:
        """
        Retrieves all story fragments, preloading their choices to avoid N+1 queries.

        :return: A list of StoryFragment instances with their choices loaded.
        """
        try:
            stmt = select(StoryFragment).options(selectinload(StoryFragment.choices))
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all fragments with choices: {e}")
            return []

    async def get_fragment_choices(self, fragment_id: int) -> list[NarrativeChoice]:
        """
        Retrieves all choices for a given story fragment.

        :param fragment_id: The ID of the source story fragment.
        :return: A list of NarrativeChoice instances.
        """
        try:
            stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting choices for fragment {fragment_id}: {e}")
            return []

    async def create_fragment(self, fragment_data: dict) -> StoryFragment:
        """
        Creates a new story fragment.

        :param fragment_data: A dictionary with the fragment's data.
        :return: The created StoryFragment instance.
        """
        return await self.create(fragment_data)

    async def update_fragment(self, fragment_id: int, data: dict) -> StoryFragment | None:
        """
        Updates an existing story fragment.

        :param fragment_id: The ID of the fragment to update.
        :param data: A dictionary with the new data.
        :return: The updated StoryFragment instance or None if not found.
        """
        return await self.update(fragment_id, data)

    async def delete_fragment(self, fragment_id: int) -> bool:
        """
        Deletes a story fragment by its ID.

        :param fragment_id: The ID of the fragment to delete.
        :return: True if deletion was successful, False otherwise.
        """
        return await self.delete(fragment_id)

    async def create_choice(self, choice_data: dict) -> NarrativeChoice:
        """
        Creates a new narrative choice.

        :param choice_data: A dictionary with the choice's data.
        :return: The created NarrativeChoice instance.
        """
        try:
            instance = NarrativeChoice(**choice_data)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Error creating NarrativeChoice with data {choice_data}: {e}")
            await self.session.rollback()
            raise

    async def update_choice(self, choice_id: int, data: dict) -> NarrativeChoice | None:
        """
        Updates an existing narrative choice.

        :param choice_id: The ID of the choice to update.
        :param data: A dictionary with the new data.
        :return: The updated NarrativeChoice instance or None if not found.
        """
        try:
            instance = await self.session.get(NarrativeChoice, choice_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await self.session.flush()
                await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Error updating NarrativeChoice with id {choice_id}: {e}")
            await self.session.rollback()
            raise

    async def delete_choice(self, choice_id: int) -> bool:
        """
        Deletes a narrative choice by its ID.

        :param choice_id: The ID of the choice to delete.
        :return: True if deletion was successful, False otherwise.
        """
        try:
            stmt = delete(NarrativeChoice).where(NarrativeChoice.id == choice_id)
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting NarrativeChoice with id {choice_id}: {e}")
            await self.session.rollback()
            return False
