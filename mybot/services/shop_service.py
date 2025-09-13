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
        """Purchase an item for the user using the CoordinadorCentral"""
        try:
            # Use CoordinadorCentral to handle the purchase
            from services.coordinador_central import CoordinadorCentral, AccionUsuario
            
            coordinador = CoordinadorCentral(self.session)
            result = await coordinador.ejecutar_flujo(
                user_id,
                AccionUsuario.COMPRAR_ITEM,
                item_id=item_id
            )
            
            return result
        except Exception as e:
            logger.error(f"Error purchasing item {item_id} for user {user_id}: {str(e)}")
            return {"success": False, "message": "Error processing purchase"}
