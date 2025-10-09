import logging
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.repositories.base_repository import BaseRepository
from database.models import ShopItem, UserPurchase, User

logger = logging.getLogger(__name__)

class ShopRepository(BaseRepository[ShopItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(ShopItem, session)

    async def get_item_by_id(self, item_id: int) -> ShopItem | None:
        try:
            stmt = select(ShopItem).where(ShopItem.id == item_id).options(selectinload(ShopItem.product_files))
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting shop item by id {item_id}: {e}")
            return None

    async def get_all_active_items(self) -> list[ShopItem]:
        try:
            stmt = select(ShopItem).where(ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all active shop items: {e}")
            return []

    async def get_available_items_for_user(self, user_id: int, is_vip: bool) -> list[ShopItem]:
        try:
            subquery = (
                select(UserPurchase.shop_item_id)
                .where(UserPurchase.user_id == user_id)
                .group_by(UserPurchase.shop_item_id)
                .having(func.count(UserPurchase.id) >= ShopItem.max_purchases_per_user)
                .subquery()
            )

            stmt = select(ShopItem).where(
                ShopItem.is_active == True,
                ShopItem.id.notin_(select(subquery.c.shop_item_id))
            )

            if not is_vip:
                stmt = stmt.where(ShopItem.is_vip_only == False)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting available items for user {user_id}: {e}")
            return []

    async def create_item(self, item_data: dict) -> ShopItem:
        return await self.create(item_data)

    async def update_item(self, item_id: int, data: dict) -> ShopItem | None:
        return await self.update(item_id, data)

    async def delete_item(self, item_id: int) -> bool:
        return await self.delete(item_id)

    async def get_user_purchases(self, user_id: int) -> list[UserPurchase]:
        try:
            stmt = select(UserPurchase).where(UserPurchase.user_id == user_id).options(selectinload(UserPurchase.shop_item))
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting purchases for user {user_id}: {e}")
            return []
