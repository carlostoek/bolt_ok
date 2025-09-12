# services/shop_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import ShopItem, User, UserInventory
from services.point_service import PointService
from services.narrative_service import NarrativeService
import logging

logger = logging.getLogger(__name__)

class ShopService:
    """Service for handling shop-related logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)

    async def get_shop_items(self, user_id: int) -> list[ShopItem]:
        """
        Retrieves a list of shop items available to the user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of ShopItem objects.
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return []

            stmt = select(ShopItem).where(ShopItem.is_active == True)
            
            # If the user is not a VIP, filter out VIP-only items
            if user.role != "vip":
                stmt = stmt.where(ShopItem.required_vip == False)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error getting shop items for user {user_id}: {e}")
            return []

    async def purchase_item(self, user_id: int, item_id: int) -> dict:
        """
        Handles the purchase of a shop item by a user.

        Args:
            user_id: The ID of the user making the purchase.
            item_id: The ID of the item to purchase.

        Returns:
            A dictionary with the result of the purchase.
        """
        try:
            user = await self.session.get(User, user_id)
            item = await self.session.get(ShopItem, item_id)

            if not user or not item:
                return {"success": False, "message": "Usuario o artículo no encontrado."}

            # Check if the user already owns the item
            existing_inventory = await self.session.execute(
                select(UserInventory).where(
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id
                )
            )
            if existing_inventory.scalar_one_or_none():
                return {"success": False, "message": "Ya posees este artículo."}

            # Check if the user has enough points
            if user.points < item.price:
                return {"success": False, "message": "No tienes suficientes besitos para comprar este artículo."}

            # Start a transaction
            async with self.session.begin():
                # Deduct points
                await self.point_service.deduct_points(user_id, item.price)

                # Add item to inventory
                new_inventory_item = UserInventory(user_id=user_id, item_id=item_id)
                self.session.add(new_inventory_item)

                # Unlock lore piece if applicable
                if item.unlocks_lore_piece_code:
                    await self.narrative_service.unlock_lore_piece_for_user(user_id, item.unlocks_lore_piece_code)

            await self.session.commit()
            return {"success": True, "message": f"¡Has comprado {item.name} por {item.price} besitos!"}

        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Error purchasing item {item_id} for user {user_id}: {e}")
            return {"success": False, "message": "Ocurrió un error al procesar tu compra."}