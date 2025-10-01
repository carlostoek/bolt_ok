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
        """Get available shop items for the user, considering VIP status and stock"""
        try:
            # Ensure the "Diario de Diana" item exists
            await self._ensure_diario_diana_item_exists()
            # Ensure the "Diario Íntimo" item exists
            await self._ensure_diario_intimo_item_exists()

            # Check if user is VIP using the proper service method
            is_vip = await self.subscription_service.is_subscription_active(user_id)

            stmt = select(ShopItem).where(ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            all_items = result.scalars().all()

            # Log all found items for debugging
            logger.info(f"Found {len(all_items)} active shop items")
            for item in all_items:
                logger.info(f"Shop item: {item.name} (VIP: {item.is_vip_only})")

            # Filter items based on stock, VIP status, and availability dates
            available_items = []
            now = datetime.now()

            for item in all_items:
                # Filter VIP-only items if user is not VIP
                if item.is_vip_only and not is_vip:
                    continue

                # Check date availability
                if item.available_from is not None and now < item.available_from:
                    logger.info(f"Item {item.name} not yet available (starts {item.available_from})")
                    continue

                if item.available_until is not None and now > item.available_until:
                    logger.info(f"Item {item.name} no longer available (ended {item.available_until})")
                    continue

                # Check stock availability
                if item.stock_limit is not None:
                    # Count total purchases
                    purchases_stmt = select(func.count(UserPurchase.id)).where(
                        UserPurchase.shop_item_id == item.id
                    )
                    purchases_result = await self.session.execute(purchases_stmt)
                    total_purchases = purchases_result.scalar() or 0

                    # Skip if sold out
                    if total_purchases >= item.stock_limit:
                        logger.info(f"Item {item.name} is sold out ({total_purchases}/{item.stock_limit})")
                        continue

                # Check if user has reached their purchase limit
                if item.max_purchases_per_user > 0:
                    user_purchases_stmt = select(func.count(UserPurchase.id)).where(
                        UserPurchase.user_id == user_id,
                        UserPurchase.shop_item_id == item.id
                    )
                    user_purchases_result = await self.session.execute(user_purchases_stmt)
                    user_purchases = user_purchases_result.scalar() or 0

                    # Skip if user has reached their limit
                    if user_purchases >= item.max_purchases_per_user:
                        logger.info(f"User {user_id} has reached purchase limit for {item.name} ({user_purchases}/{item.max_purchases_per_user})")
                        continue

                # Check unlock requirements (compound conditions)
                if item.unlock_requirements is not None:
                    from services.condition_checker import ConditionChecker
                    checker = ConditionChecker(self.session)
                    meets_requirements, _ = await checker.check_requirements(user_id, item.unlock_requirements)

                    if not meets_requirements:
                        logger.info(f"User {user_id} does not meet requirements for {item.name}")
                        continue

                available_items.append(item)

            logger.info(f"Showing {len(available_items)} available items to user {user_id}")
            return available_items
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

    async def _ensure_diario_intimo_item_exists(self):
        """Ensure the 'Diario Íntimo' shop item exists"""
        try:
            from database.models import LorePiece
            # Check if the item already exists
            stmt = select(ShopItem).where(ShopItem.name == "📓 Diario Íntimo")
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                # Create the lore piece first
                lore_piece = LorePiece(
                    title="Diario Íntimo de Diana",
                    code_name="diario_intimo_diana",
                    content="Acceso exclusivo al contenido más íntimo de Diana. Sus pensamientos más profundos y secretos revelados...",
                    content_type="text",
                    unlock_condition_type="requires_item",
                    unlock_condition_value="diario_intimo"
                )
                self.session.add(lore_piece)
                await self.session.flush()

                # Create the shop item
                shop_item = ShopItem(
                    name="📓 Diario Íntimo",
                    description="El diario personal más íntimo de Diana. Desbloquea contenido narrativo especial y exclusivo.",
                    price=30,
                    is_vip_only=False,
                    is_active=True,
                    unlocks_lore_piece_id=lore_piece.id
                )
                self.session.add(shop_item)
                await self.session.commit()
                logger.info("Created 'Diario Íntimo' shop item")
            else:
                logger.info("'Diario Íntimo' shop item already exists")
        except Exception as e:
            logger.error(f"Error ensuring Diario Íntimo item exists: {str(e)}")
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

            # Check date availability
            now = datetime.now()
            if item.available_from is not None and now < item.available_from:
                return {
                    "success": False,
                    "message": f"❌ {item.name} aún no está disponible. Estará disponible desde {item.available_from.strftime('%d/%m/%Y')}."
                }

            if item.available_until is not None and now > item.available_until:
                return {
                    "success": False,
                    "message": f"❌ {item.name} ya no está disponible. Estuvo disponible hasta {item.available_until.strftime('%d/%m/%Y')}."
                }

            # Check unlock requirements
            if item.unlock_requirements is not None:
                from services.condition_checker import ConditionChecker
                checker = ConditionChecker(self.session)
                meets_requirements, failed_conditions = await checker.check_requirements(user_id, item.unlock_requirements)

                if not meets_requirements:
                    # Build error message with failed conditions
                    conditions_text = "\n• ".join(failed_conditions)
                    return {
                        "success": False,
                        "message": f"❌ No cumples los requisitos para {item.name}:\n\n• {conditions_text}"
                    }

            # Check stock availability
            if item.stock_limit is not None:
                # Count total purchases for this item
                total_purchases_stmt = select(func.count(UserPurchase.id)).where(
                    UserPurchase.shop_item_id == item_id
                )
                total_purchases_result = await self.session.execute(total_purchases_stmt)
                total_purchases = total_purchases_result.scalar() or 0

                if total_purchases >= item.stock_limit:
                    return {
                        "success": False,
                        "message": f"❌ {item.name} agotado. Solo había {item.stock_limit} unidades disponibles."
                    }

            # Check max purchases per user
            if item.max_purchases_per_user > 0:
                # Count purchases by this user
                user_purchases_stmt = select(func.count(UserPurchase.id)).where(
                    UserPurchase.user_id == user_id,
                    UserPurchase.shop_item_id == item_id
                )
                user_purchases_result = await self.session.execute(user_purchases_stmt)
                user_purchases = user_purchases_result.scalar() or 0

                if user_purchases >= item.max_purchases_per_user:
                    times_text = "vez" if item.max_purchases_per_user == 1 else "veces"
                    return {
                        "success": False,
                        "message": f"❌ Ya compraste {item.name} el máximo de {item.max_purchases_per_user} {times_text} permitido."
                    }

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
            unlocked_lore = None
            if item.unlocks_lore_piece_id:
                # Add to user's lore pieces (backpack) directly
                unlocked_lore = await self._add_to_backpack(user_id, item_id, item)

            # Don't clear pending_decision_id - it will be processed when user returns to narrative
            # The narrative handler will process the pending decision after purchase
            logger.info(f"Purchase successful for user {user_id}. Pending decision will be processed on return to narrative.")
            
            await self.session.commit()
            return {
                "success": True,
                "message": "Purchase successful",
                "unlocked_lore": unlocked_lore  # Now returns dict or None
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error purchasing item {item_id} for user {user_id}: {str(e)}")
            return {"success": False, "message": "Error processing purchase"}

    async def _add_to_backpack(self, user_id: int, item_id: int, shop_item: ShopItem):
        """Add purchased item to user's backpack directly and return lore piece info"""
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
                # Get the lore piece details
                lore_piece = await self.session.get(LorePiece, shop_item.unlocks_lore_piece_id)

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

                # Return lore piece information as dictionary
                if lore_piece:
                    return {
                        'title': lore_piece.title,
                        'description': lore_piece.description or 'Nuevo contenido desbloqueado',
                        'code_name': lore_piece.code_name
                    }

            return None
        except Exception as e:
            logger.error(f"Error adding item to backpack for user {user_id}: {str(e)}")
            return None
