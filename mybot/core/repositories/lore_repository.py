import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.repositories.base_repository import BaseRepository
from database.models import LorePiece, UserLorePiece
from database.hint_combination import HintCombination

logger = logging.getLogger(__name__)

class LoreRepository(BaseRepository[LorePiece]):
    def __init__(self, session: AsyncSession):
        super().__init__(LorePiece, session)

    async def get_lore_piece_by_id(self, lore_id: int) -> LorePiece | None:
        return await self.get_by_id(lore_id)

    async def get_lore_piece_by_code(self, code_name: str) -> LorePiece | None:
        try:
            stmt = select(LorePiece).where(LorePiece.code_name == code_name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting lore piece by code {code_name}: {e}")
            return None

    async def get_user_lore_pieces(self, user_id: int) -> list[LorePiece]:
        try:
            stmt = (
                select(LorePiece)
                .join(UserLorePiece, UserLorePiece.lore_piece_id == LorePiece.id)
                .where(UserLorePiece.user_id == user_id)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting lore pieces for user {user_id}: {e}")
            return []

    async def create_lore_piece(self, data: dict) -> LorePiece:
        return await self.create(data)

    async def unlock_for_user(self, user_id: int, lore_id: int) -> UserLorePiece:
        try:
            stmt = select(UserLorePiece).where(UserLorePiece.user_id == user_id, UserLorePiece.lore_piece_id == lore_id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            user_lore_piece = UserLorePiece(user_id=user_id, lore_piece_id=lore_id)
            self.session.add(user_lore_piece)
            await self.session.flush()
            await self.session.refresh(user_lore_piece)
            return user_lore_piece
        except Exception as e:
            logger.error(f"Error unlocking lore piece {lore_id} for user {user_id}: {e}")
            await self.session.rollback()
            raise

    async def get_hint_combinations(self) -> list[HintCombination]:
        try:
            stmt = select(HintCombination)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting hint combinations: {e}")
            return []
