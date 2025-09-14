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
            # Ensure the "Diario de Diana" item exists
            await self._ensure_diario_diana_item_exists()
            
            # Check if user is VIP by getting their subscription
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())
            
            stmt = select(ShopItem).where(ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            all_items = result.scalars().all()
            
            # Log all found items for debugging
            logger.info(f"Found {len(all_items)} active shop items")
            for item in all_items:
                logger.info(f"Shop item: {item.name} (VIP: {item.is_vip_only})")
            
            # Filter VIP-only items if user is not VIP
            if not is_vip:
                non_vip_items = [item for item in all_items if not item.is_vip_only]
                logger.info(f"Showing {len(non_vip_items)} non-VIP items to user {user_id}")
                return non_vip_items
            logger.info(f"Showing all {len(all_items)} items to VIP user {user_id}")
            return all_items
        except Exception as e:
            logger.error(f"Error getting available items for user {user_id}: {str(e)}")
            return []

    async def _ensure_diario_diana_item_exists(self):
        """Ensure the 'Diario de Diana' shop item exists"""
        try:
            from database.models import LorePiece
            # Check if the item already exists
            stmt = select(ShopItem).where(ShopItem.name == "📖 Diario Secreto")
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()
            
            if not item:
                # Create the lore piece first
                lore_piece = LorePiece(
                    title="Diario Secreto de Diana",
                    code_name="diario_secreto_diana",
                    content="Contenido exclusivo del diario secreto de Diana...",
                    content_type="text",
                    unlock_conditions={"requires_item": "diario_diana"}
                )
                self.session.add(lore_piece)
                await self.session.flush()
                
                # Create the shop item
                shop_item = ShopItem(
                    name="📖 Diario Secreto",
                    description="Un diario personal de Diana que desbloquea contenido exclusivo",
                    price=50,
                    is_vip_only=False,
                    is_active=True,
                    unlocks_lore_piece_id=lore_piece.id
                )
                self.session.add(shop_item)
                await self.session.commit()
                logger.info("Created 'Diario Secreto' shop item")
            else:
                logger.info("'Diario Secreto' shop item already exists")
        except Exception as e:
            logger.error(f"Error ensuring Diario de Diana item exists: {str(e)}")
            await self.session.rollback()

    async def has_item_in_inventory(self, user_id: int, item_name: str) -> bool:
        """Check if user has a specific item in their inventory"""
        try:
            # Check if user has purchased the item
            stmt = select(UserPurchase, ShopItem).join(
                ShopItem, UserPurchase.shop_item_id == ShopItem.id
            ).where(
                UserPurchase.user_id == user_id,
                ShopItem.name == item_name
            )
            result = await self.session.execute(stmt)
            return result.first() is not None
        except Exception as e:
            logger.error(f"Error checking inventory for user {user_id}: {str(e)}")
            return False

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
                # Add to user's lore pieces (backpack) directly
                unlocked_lore = await self._add_to_backpack(user_id, item_id, item)
            
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

    async def _add_to_backpack(self, user_id: int, item_id: int, shop_item: ShopItem) -> bool:
        """Add purchased item to user's backpack directly"""
        try:
            from database.models import UserLorePiece, LorePiece
            from datetime import datetime
            from sqlalchemy import select
            
            # Check if the user already has this lore piece
            result = await self.session.execute(
                select(UserLorePiece).where(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == shop_item.unlocks_lore_piece_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Add to user's lore pieces (backpack)
                user_lore_piece = UserLorePiece(
                    user_id=user_id,
                    lore_piece_id=shop_item.unlocks_lore_piece_id,
                    context={
                        'source': 'shop_purchase',
                        'item_id': item_id,
                        'item_name': shop_item.name,
                        'purchased_at': datetime.utcnow().isoformat()
                    }
                )
                self.session.add(user_lore_piece)
                await self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding item to backpack for user {user_id}: {str(e)}")
            return False
