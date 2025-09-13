import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import ShopItem, UserPurchase, User, UserLorePiece
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
        try:
            # Check if user is VIP by getting their subscription
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())
            
            stmt = select(ShopItem).where(ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            all_items = result.scalars().all()
            
            # Filter VIP-only items if user is not VIP
            if not is_vip:
                return [item for item in all_items if not item.is_vip_only]
            return all_items
        except Exception as e:
            logger.error(f"Error getting available items for user {user_id}: {str(e)}")
            return []

    async def purchase_item(self, user_id: int, item_id: int) -> Dict[str, Any]:
        """Purchase an item for the user directly"""
        try:
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
            if user is None:
                return {"success": False, "message": "User not found"}
                
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
            unlocked_lore = False
            if item.unlocks_lore_piece_id:
                # Make sure to flush before calling other services
                await self.session.flush()
                # Add to user's lore pieces (backpack)
                # Check if the user already has this lore piece
                result = await self.session.execute(
                    select(UserLorePiece).where(
                        UserLorePiece.user_id == user_id,
                        UserLorePiece.lore_piece_id == item.unlocks_lore_piece_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # Use CoordinadorCentral to add to backpack
                    from services.coordinador_central import CoordinadorCentral, AccionUsuario
                    coordinador = CoordinadorCentral(self.session)
                    result = await coordinador.ejecutar_flujo(
                        user_id,
                        AccionUsuario.AGREGAR_A_MOCHILA,
                        item_id=item_id
                    )
                    unlocked_lore = result.get("success", False)
                else:
                    unlocked_lore = False
            
            await self.session.commit()
            return {
                "success": True, 
                "message": "Purchase successful",
                "unlocked_lore": unlocked_lore
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error purchasing item {item_id} for user {user_id}: {str(e)}")
            return {"success": False, "message": "Error processing purchase"}
