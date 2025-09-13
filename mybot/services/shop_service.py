import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import ShopItem, UserPurchase, User
from services.point_service import PointService
from services.narrative_service import NarrativeService
from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class ShopService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)
        self.subscription_service = SubscriptionService(session)

    async def get_available_items(self, user_id: int) -> List[ShopItem]:
        """Get available shop items for the user, considering VIP status"""
        # Check if user is VIP
        is_vip = await self.subscription_service.is_user_vip(user_id)
        
        stmt = select(ShopItem).where(ShopItem.is_active == True)
        result = await self.session.execute(stmt)
        all_items = result.scalars().all()
        
        # Filter VIP-only items if user is not VIP
        if not is_vip:
            return [item for item in all_items if not item.is_vip_only]
        return all_items

    async def purchase_item(self, user_id: int, item_id: int) -> Dict[str, Any]:
        """Purchase an item for the user"""
        # Start a transaction
        async with self.session.begin():
            # Get the item
            stmt = select(ShopItem).where(ShopItem.id == item_id, ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()
            
            if not item:
                return {"success": False, "message": "Item not found"}
            
            # Check if user is VIP for VIP-only items
            if item.is_vip_only:
                is_vip = await self.subscription_service.is_user_vip(user_id)
                if not is_vip:
                    return {"success": False, "message": "VIP subscription required"}
            
            # Check user points
            user = await self.session.get(User, user_id)
            if user.points < item.price:
                return {"success": False, "message": "Insufficient points"}
            
            # Deduct points
            user.points -= item.price
            
            # Record purchase
            purchase = UserPurchase(
                user_id=user_id,
                shop_item_id=item_id,
                price_paid=item.price
            )
            self.session.add(purchase)
            
            # Unlock lore piece if applicable
            if item.unlocks_lore_piece_id:
                await self.narrative_service.unlock_lore_piece(
                    user_id, item.unlocks_lore_piece_id
                )
            
            return {
                "success": True, 
                "message": "Purchase successful",
                "unlocked_lore": item.unlocks_lore_piece_id is not None
            }
