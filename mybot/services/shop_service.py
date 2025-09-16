import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from database.models import ShopItem, UserPurchase, User, UserLorePiece, ShopCategory
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
            # Ensure the "Diario Íntimo" item exists
            await self._ensure_diario_intimo_item_exists()
            
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

    async def get_categorized_items(self, user_id: int) -> Dict[str, List[ShopItem]]:
        """Get available shop items organized by category, considering VIP status"""
        try:
            # Ensure required items exist
            await self._ensure_diario_diana_item_exists()
            await self._ensure_diario_intimo_item_exists()

            # Check if user is VIP by getting their subscription
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())

            # Query shop items with their categories, ordered by category display_order and item name
            stmt = (
                select(ShopItem, ShopCategory)
                .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                .where(ShopItem.is_active == True)
                .order_by(ShopCategory.display_order.asc().nulls_last(), ShopItem.name)
            )
            result = await self.session.execute(stmt)
            items_with_categories = result.all()

            # Organize items by category
            categorized_items = {}

            for shop_item, category in items_with_categories:
                # Apply VIP filtering logic
                if not is_vip and shop_item.is_vip_only:
                    continue

                # Determine category name
                if category:
                    category_name = category.name
                    # Skip VIP-only categories if user is not VIP
                    if not is_vip and category.is_vip_only:
                        continue
                else:
                    category_name = "Sin Categoría"  # Default category for uncategorized items

                # Add item to the appropriate category
                if category_name not in categorized_items:
                    categorized_items[category_name] = []
                categorized_items[category_name].append(shop_item)

            logger.info(f"Found {sum(len(items) for items in categorized_items.values())} available items across {len(categorized_items)} categories for user {user_id} (VIP: {is_vip})")
            return categorized_items

        except Exception as e:
            logger.error(f"Error getting categorized items for user {user_id}: {str(e)}")
            return {}

    async def search_items(
        self,
        user_id: int,
        search_query: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        limit: Optional[int] = 50
    ) -> List[ShopItem]:
        """
        Search shop items with name/description search and price range filtering

        Args:
            user_id: ID of the user performing the search
            search_query: Search term for name/description (case-insensitive)
            min_price: Minimum price filter (inclusive)
            max_price: Maximum price filter (inclusive)
            limit: Maximum number of results to return (default: 50)

        Returns:
            List of ShopItem objects matching the search criteria
        """
        try:
            # Check if user is VIP to determine available items
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())

            # Start with base query for active items
            stmt = select(ShopItem).where(ShopItem.is_active == True)

            # Apply VIP filtering
            if not is_vip:
                stmt = stmt.where(ShopItem.is_vip_only == False)

            # Apply search query filter (case-insensitive search in name and description)
            if search_query:
                search_term = f"%{search_query.lower()}%"
                stmt = stmt.where(
                    or_(
                        func.lower(ShopItem.name).like(search_term),
                        func.lower(ShopItem.description).like(search_term)
                    )
                )

            # Apply price range filters
            price_conditions = []
            if min_price is not None:
                price_conditions.append(ShopItem.price >= min_price)
            if max_price is not None:
                price_conditions.append(ShopItem.price <= max_price)

            if price_conditions:
                stmt = stmt.where(and_(*price_conditions))

            # Order by name for consistent results and apply limit
            stmt = stmt.order_by(ShopItem.name)
            if limit:
                stmt = stmt.limit(limit)

            # Execute query
            result = await self.session.execute(stmt)
            items = result.scalars().all()

            logger.info(f"Search completed for user {user_id}: query='{search_query}', "
                       f"price_range=[{min_price}, {max_price}], found {len(items)} items")

            return items

        except Exception as e:
            logger.error(f"Error searching items for user {user_id}: {str(e)}")
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
        """Purchase an item for the user with promotional pricing applied"""
        try:
            # Get the item
            stmt = select(ShopItem).where(ShopItem.id == item_id, ShopItem.is_active == True)
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                return {"success": False, "message": "Item not found"}

            # Check if user is VIP for VIP-only items
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())

            if item.is_vip_only and not is_vip:
                return {"success": False, "message": "VIP subscription required"}

            # Calculate promotional pricing
            pricing = await self._calculate_promotional_pricing(item, user_id, is_vip)
            final_price = pricing["current_price"]

            # Check user points against promotional price
            user = await self.session.get(User, user_id)
            if user is None:
                return {"success": False, "message": "User not found"}

            if user.points < final_price:
                return {"success": False, "message": "Insufficient points"}

            # Check if user already purchased this item
            existing_purchase_stmt = select(UserPurchase).where(
                UserPurchase.user_id == user_id,
                UserPurchase.shop_item_id == item_id
            )
            existing_purchase_result = await self.session.execute(existing_purchase_stmt)
            if existing_purchase_result.scalar_one_or_none():
                return {"success": False, "message": "Item already purchased"}

            # Deduct promotional price (not base price)
            user.points -= final_price

            # Record purchase with the actual price paid (promotional price)
            purchase = UserPurchase(
                user_id=user_id,
                shop_item_id=item_id,
                price_paid=final_price  # Record the actual price paid with promotions
            )
            self.session.add(purchase)

            # Unlock lore piece if applicable
            unlocked_lore = False
            if item.unlocks_lore_piece_id:
                # Add to user's lore pieces (backpack) directly
                unlocked_lore = await self._add_to_backpack(user_id, item_id, item)

            await self.session.commit()

            # Enhanced return information including promotional details
            result_data = {
                "success": True,
                "message": "Purchase successful",
                "unlocked_lore": unlocked_lore,
                "pricing": pricing,
                "item_name": item.name
            }

            # Add savings information if there was a promotion
            if pricing["is_on_sale"]:
                result_data["savings"] = pricing["savings"]
                result_data["promotion_applied"] = pricing["promotion_name"]

            return result_data

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error purchasing item {item_id} for user {user_id}: {str(e)}")
            return {"success": False, "message": "Error processing purchase"}

    async def get_item_details(self, user_id: int, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific shop item for a user

        Args:
            user_id: ID of the user requesting item details
            item_id: ID of the shop item to get details for

        Returns:
            Dictionary containing detailed item information including:
            - Basic item information (name, description, price, etc.)
            - Promotion pricing (if applicable)
            - Unlock previews (lore piece information)
            - Purchase eligibility information
            - User-specific information (already purchased, VIP status, etc.)
        """
        try:
            # Get the shop item with its related data
            stmt = (
                select(ShopItem, ShopCategory)
                .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                .where(ShopItem.id == item_id, ShopItem.is_active == True)
            )
            result = await self.session.execute(stmt)
            item_data = result.first()

            if not item_data:
                logger.warning(f"Shop item {item_id} not found or inactive")
                return None

            shop_item, category = item_data

            # Get user information
            user = await self.session.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None

            # Check VIP status
            subscription = await self.subscription_service.get_subscription(user_id)
            is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > func.now())

            # Check if user has already purchased this item
            purchase_stmt = select(UserPurchase).where(
                UserPurchase.user_id == user_id,
                UserPurchase.shop_item_id == item_id
            )
            purchase_result = await self.session.execute(purchase_stmt)
            already_purchased = purchase_result.scalar_one_or_none() is not None

            # Get lore piece information if item unlocks content
            lore_preview = None
            if shop_item.unlocks_lore_piece_id:
                from database.models import LorePiece
                lore_stmt = select(LorePiece).where(LorePiece.id == shop_item.unlocks_lore_piece_id)
                lore_result = await self.session.execute(lore_stmt)
                lore_piece = lore_result.scalar_one_or_none()

                if lore_piece:
                    # Create a preview without revealing full content
                    content_preview = lore_piece.content[:200] + "..." if len(lore_piece.content) > 200 else lore_piece.content
                    lore_preview = {
                        "title": lore_piece.title,
                        "description": lore_piece.description,
                        "content_type": lore_piece.content_type,
                        "content_preview": content_preview,
                        "category": lore_piece.category,
                        "is_main_story": lore_piece.is_main_story
                    }

            # Check purchase eligibility
            eligibility = {
                "can_purchase": True,
                "reasons": []
            }

            # Check if already purchased
            if already_purchased:
                eligibility["can_purchase"] = False
                eligibility["reasons"].append("already_purchased")

            # Check VIP requirement
            if shop_item.is_vip_only and not is_vip:
                eligibility["can_purchase"] = False
                eligibility["reasons"].append("vip_required")

            # Calculate promotional pricing with actual promotion logic first
            pricing = await self._calculate_promotional_pricing(shop_item, user_id, is_vip)

            # Check sufficient points against promotional price
            if user.points < pricing["current_price"]:
                eligibility["can_purchase"] = False
                eligibility["reasons"].append("insufficient_points")
                eligibility["points_needed"] = pricing["current_price"] - user.points

            # Build detailed item information
            item_details = {
                "id": shop_item.id,
                "name": shop_item.name,
                "description": shop_item.description,
                "pricing": pricing,
                "is_vip_only": shop_item.is_vip_only,
                "category": {
                    "id": category.id if category else None,
                    "name": category.name if category else "Sin Categoría",
                    "description": category.description if category else None,
                    "is_vip_only": category.is_vip_only if category else False
                },
                "unlocks_content": shop_item.unlocks_lore_piece_id is not None,
                "lore_preview": lore_preview,
                "created_at": shop_item.created_at,
                "user_info": {
                    "already_purchased": already_purchased,
                    "is_vip": is_vip,
                    "current_points": user.points,
                    "purchase_eligibility": eligibility
                }
            }

            logger.info(f"Retrieved detailed information for item {item_id} for user {user_id}")
            return item_details

        except Exception as e:
            logger.error(f"Error getting item details for item {item_id} and user {user_id}: {str(e)}")
            return None

    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's purchased items (inventory) with usage tracking"""
        try:
            # Query user purchases with shop item details
            stmt = (
                select(UserPurchase, ShopItem, ShopCategory)
                .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
                .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                .where(UserPurchase.user_id == user_id)
                .order_by(UserPurchase.purchased_at.desc())
            )
            result = await self.session.execute(stmt)
            purchases = result.all()

            inventory_items = []
            for purchase, shop_item, category in purchases:
                # Check if item unlocks lore content
                has_lore_content = shop_item.unlocks_lore_piece_id is not None
                lore_accessed = False

                if has_lore_content:
                    # Check if user has accessed the lore content
                    from database.models import UserLorePiece
                    lore_stmt = select(UserLorePiece).where(
                        UserLorePiece.user_id == user_id,
                        UserLorePiece.lore_piece_id == shop_item.unlocks_lore_piece_id
                    )
                    lore_result = await self.session.execute(lore_stmt)
                    lore_accessed = lore_result.scalar_one_or_none() is not None

                inventory_item = {
                    "purchase_id": purchase.id,
                    "item_id": shop_item.id,
                    "name": shop_item.name,
                    "description": shop_item.description,
                    "price_paid": purchase.price_paid,
                    "purchased_at": purchase.purchased_at,
                    "category_name": category.name if category else "Sin Categoría",
                    "is_vip_only": shop_item.is_vip_only,
                    "has_lore_content": has_lore_content,
                    "lore_accessed": lore_accessed,
                    "unlocks_lore_piece_id": shop_item.unlocks_lore_piece_id
                }
                inventory_items.append(inventory_item)

            logger.info(f"Retrieved {len(inventory_items)} inventory items for user {user_id}")
            return inventory_items

        except Exception as e:
            logger.error(f"Error getting user inventory for user {user_id}: {str(e)}")
            return []

    async def get_inventory_item_details(self, user_id: int, item_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific inventory item"""
        try:
            # Get the purchase and item details
            stmt = (
                select(UserPurchase, ShopItem, ShopCategory)
                .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
                .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                .where(
                    UserPurchase.user_id == user_id,
                    UserPurchase.shop_item_id == item_id
                )
            )
            result = await self.session.execute(stmt)
            purchase_data = result.first()

            if not purchase_data:
                return None

            purchase, shop_item, category = purchase_data

            # Get lore piece details if applicable
            lore_details = None
            if shop_item.unlocks_lore_piece_id:
                from database.models import LorePiece, UserLorePiece

                # Get lore piece information
                lore_stmt = select(LorePiece).where(LorePiece.id == shop_item.unlocks_lore_piece_id)
                lore_result = await self.session.execute(lore_stmt)
                lore_piece = lore_result.scalar_one_or_none()

                # Check if user has accessed it
                user_lore_stmt = select(UserLorePiece).where(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == shop_item.unlocks_lore_piece_id
                )
                user_lore_result = await self.session.execute(user_lore_stmt)
                user_lore = user_lore_result.scalar_one_or_none()

                if lore_piece:
                    lore_details = {
                        "id": lore_piece.id,
                        "title": lore_piece.title,
                        "description": lore_piece.description,
                        "content_type": lore_piece.content_type,
                        "category": lore_piece.category,
                        "is_main_story": lore_piece.is_main_story,
                        "accessed": user_lore is not None,
                        "accessed_at": user_lore.unlocked_at if user_lore else None,
                        "access_context": user_lore.context if user_lore else None
                    }

            item_details = {
                "purchase_id": purchase.id,
                "item_id": shop_item.id,
                "name": shop_item.name,
                "description": shop_item.description,
                "price_paid": purchase.price_paid,
                "purchased_at": purchase.purchased_at,
                "category": {
                    "name": category.name if category else "Sin Categoría",
                    "description": category.description if category else None
                },
                "is_vip_only": shop_item.is_vip_only,
                "lore_details": lore_details
            }

            return item_details

        except Exception as e:
            logger.error(f"Error getting inventory item details for user {user_id}, item {item_id}: {str(e)}")
            return None

    async def _calculate_promotional_pricing(self, shop_item: ShopItem, user_id: int, is_vip: bool) -> Dict[str, Any]:
        """
        Calculate promotional pricing for a shop item based on various factors.

        Args:
            shop_item: The shop item to calculate pricing for
            user_id: The user requesting the pricing
            is_vip: Whether the user has VIP status

        Returns:
            Dictionary containing pricing information with promotional adjustments
        """
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import select, func
            from database.models import UserPurchase, User

            base_price = shop_item.price
            current_price = base_price
            discount_percentage = 0
            is_on_sale = False
            promotion_name = None

            # Get user information for personalized promotions
            user = await self.session.get(User, user_id)
            user_total_purchases = 0
            user_total_spent = 0

            if user:
                # Calculate user's purchase history
                purchase_stmt = (
                    select(func.count(UserPurchase.id), func.coalesce(func.sum(UserPurchase.price_paid), 0))
                    .where(UserPurchase.user_id == user_id)
                )
                result = await self.session.execute(purchase_stmt)
                user_total_purchases, user_total_spent = result.first() or (0, 0)

            # Apply promotional logic based on various criteria

            # 1. VIP Member Discount - 10% off for VIP members
            if is_vip and not shop_item.is_vip_only:
                discount_percentage = max(discount_percentage, 10)
                promotion_name = "Descuento VIP"

            # 2. First Purchase Discount - 15% off first item
            if user_total_purchases == 0:
                discount_percentage = max(discount_percentage, 15)
                promotion_name = "Descuento Primera Compra"

            # 3. Bulk Purchase Discount - Higher discounts for loyal customers
            elif user_total_purchases >= 5:
                discount_percentage = max(discount_percentage, 20)
                promotion_name = "Descuento Cliente Frecuente"
            elif user_total_purchases >= 3:
                discount_percentage = max(discount_percentage, 12)
                promotion_name = "Descuento Cliente Leal"

            # 4. High Spender Discount - Additional discount for users who spent a lot
            if user_total_spent >= 200:
                discount_percentage = max(discount_percentage, 25)
                promotion_name = "Descuento Gran Comprador"
            elif user_total_spent >= 100:
                discount_percentage = max(discount_percentage, 15)
                promotion_name = "Descuento Buen Cliente"

            # 5. Item Category Specific Promotions
            if shop_item.name and "Diario" in shop_item.name:
                # Special promotion for diary items
                discount_percentage = max(discount_percentage, 20)
                promotion_name = "Promoción Especial Diarios"

            # 6. Time-based promotions (weekend discounts, etc.)
            current_time = datetime.utcnow()
            is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6

            if is_weekend:
                discount_percentage = max(discount_percentage, 10)
                if promotion_name is None:
                    promotion_name = "Descuento de Fin de Semana"

            # 7. Low points encouragement - Discount for users with few points
            if user and user.points < 50 and base_price > user.points * 0.8:
                discount_percentage = max(discount_percentage, 30)
                promotion_name = "Descuento de Apoyo"

            # Apply the discount if any promotion is active
            if discount_percentage > 0:
                is_on_sale = True
                discount_amount = int(base_price * discount_percentage / 100)
                current_price = max(1, base_price - discount_amount)  # Minimum price of 1 besito

                # Recalculate exact discount percentage based on final prices
                discount_percentage = int(((base_price - current_price) / base_price) * 100)

            return {
                "base_price": base_price,
                "current_price": current_price,
                "discount_percentage": discount_percentage,
                "is_on_sale": is_on_sale,
                "promotion_name": promotion_name,
                "savings": base_price - current_price if is_on_sale else 0
            }

        except Exception as e:
            logger.error(f"Error calculating promotional pricing for item {shop_item.id}: {str(e)}")
            # Fallback to base pricing on error
            return {
                "base_price": shop_item.price,
                "current_price": shop_item.price,
                "discount_percentage": 0,
                "is_on_sale": False,
                "promotion_name": None,
                "savings": 0
            }

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
