import logging
import csv
import io
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from datetime import datetime, timedelta
from database.models import User, ShopCategory, ShopItem, UserPurchase

logger = logging.getLogger(__name__)

class ShopAdminService:
    """Service for shop administration features"""

    def __init__(self, session: AsyncSession):
        """Initialize the ShopAdminService with database session"""
        self.session = session
        logger.debug("ShopAdminService initialized")

    async def validate_admin_access(self, user_id: int) -> bool:
        """
        Validate if a user has admin access privileges

        Args:
            user_id: Telegram user ID to validate

        Returns:
            bool: True if user is admin, False otherwise
        """
        try:
            # Use the existing is_admin function that checks both ADMIN_IDS and database
            from utils.user_roles import is_admin
            is_user_admin = await is_admin(user_id, self.session)
            logger.info(f"Admin access validation for user {user_id}: {is_user_admin}")
            return is_user_admin

        except Exception as e:
            logger.error(f"Error validating admin access for user {user_id}: {str(e)}")
            return False

    async def _handle_admin_error(self, operation: str, error: Exception, user_id: Optional[int] = None) -> None:
        """
        Centralized error handling for admin operations

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            user_id: Optional user ID for context
        """
        user_context = f" for user {user_id}" if user_id else ""
        logger.error(f"Admin operation '{operation}' failed{user_context}: {str(error)}")

        # Rollback session on error
        try:
            await self.session.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback session after error in '{operation}': {str(rollback_error)}")

    # CATEGORY MANAGEMENT METHODS

    async def create_category(self, admin_user_id: int, name: str, description: Optional[str] = None,
                            display_order: int = 0, is_vip_only: bool = False) -> Dict[str, Any]:
        """
        Create a new shop category

        Args:
            admin_user_id: ID of the admin user performing the action
            name: Name of the category (must be unique)
            description: Optional description of the category
            display_order: Display order for sorting (default: 0)
            is_vip_only: Whether category is VIP-only (default: False)

        Returns:
            Dict containing success status, message, and category data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Check if category with same name already exists
            stmt = select(ShopCategory).where(ShopCategory.name == name)
            result = await self.session.execute(stmt)
            existing_category = result.scalar_one_or_none()

            if existing_category:
                return {"success": False, "message": f"Category '{name}' already exists"}

            # Create new category
            new_category = ShopCategory(
                name=name,
                description=description,
                display_order=display_order,
                is_vip_only=is_vip_only,
                is_active=True
            )

            self.session.add(new_category)
            await self.session.commit()
            await self.session.refresh(new_category)

            logger.info(f"Category '{name}' created by admin {admin_user_id}")

            return {
                "success": True,
                "message": f"Category '{name}' created successfully",
                "category": {
                    "id": new_category.id,
                    "name": new_category.name,
                    "description": new_category.description,
                    "display_order": new_category.display_order,
                    "is_vip_only": new_category.is_vip_only,
                    "is_active": new_category.is_active,
                    "created_at": new_category.created_at.isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("create_category", e, admin_user_id)
            return {"success": False, "message": "Failed to create category"}

    async def get_categories(self, admin_user_id: int, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Get all shop categories

        Args:
            admin_user_id: ID of the admin user performing the action
            include_inactive: Whether to include inactive categories (default: False)

        Returns:
            Dict containing success status, message, and categories list if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Build query
            conditions = []
            if not include_inactive:
                conditions.append(ShopCategory.is_active == True)

            if conditions:
                stmt = select(ShopCategory).where(and_(*conditions)).order_by(ShopCategory.display_order, ShopCategory.name)
            else:
                stmt = select(ShopCategory).order_by(ShopCategory.display_order, ShopCategory.name)

            result = await self.session.execute(stmt)
            categories = result.scalars().all()

            categories_data = []
            for category in categories:
                categories_data.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "display_order": category.display_order,
                    "is_vip_only": category.is_vip_only,
                    "is_active": category.is_active,
                    "created_at": category.created_at.isoformat()
                })

            logger.info(f"Retrieved {len(categories)} categories for admin {admin_user_id}")

            return {
                "success": True,
                "message": f"Retrieved {len(categories)} categories",
                "categories": categories_data
            }

        except Exception as e:
            await self._handle_admin_error("get_categories", e, admin_user_id)
            return {"success": False, "message": "Failed to retrieve categories"}

    async def update_category(self, admin_user_id: int, category_id: int, name: Optional[str] = None,
                            description: Optional[str] = None, display_order: Optional[int] = None,
                            is_vip_only: Optional[bool] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update an existing shop category

        Args:
            admin_user_id: ID of the admin user performing the action
            category_id: ID of the category to update
            name: New name for the category (optional)
            description: New description for the category (optional)
            display_order: New display order (optional)
            is_vip_only: New VIP-only status (optional)
            is_active: New active status (optional)

        Returns:
            Dict containing success status, message, and updated category data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Get existing category
            stmt = select(ShopCategory).where(ShopCategory.id == category_id)
            result = await self.session.execute(stmt)
            category = result.scalar_one_or_none()

            if not category:
                return {"success": False, "message": f"Category with ID {category_id} not found"}

            # Check if new name conflicts with existing categories (if name is being changed)
            if name and name != category.name:
                stmt = select(ShopCategory).where(and_(ShopCategory.name == name, ShopCategory.id != category_id))
                result = await self.session.execute(stmt)
                existing_category = result.scalar_one_or_none()

                if existing_category:
                    return {"success": False, "message": f"Category name '{name}' already exists"}

            # Update fields if provided
            updated_fields = []
            if name is not None and name != category.name:
                category.name = name
                updated_fields.append("name")

            if description is not None and description != category.description:
                category.description = description
                updated_fields.append("description")

            if display_order is not None and display_order != category.display_order:
                category.display_order = display_order
                updated_fields.append("display_order")

            if is_vip_only is not None and is_vip_only != category.is_vip_only:
                category.is_vip_only = is_vip_only
                updated_fields.append("is_vip_only")

            if is_active is not None and is_active != category.is_active:
                category.is_active = is_active
                updated_fields.append("is_active")

            if not updated_fields:
                return {"success": False, "message": "No changes provided"}

            await self.session.commit()
            await self.session.refresh(category)

            logger.info(f"Category {category_id} updated by admin {admin_user_id}. Fields: {', '.join(updated_fields)}")

            return {
                "success": True,
                "message": f"Category updated successfully. Updated fields: {', '.join(updated_fields)}",
                "category": {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "display_order": category.display_order,
                    "is_vip_only": category.is_vip_only,
                    "is_active": category.is_active,
                    "created_at": category.created_at.isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("update_category", e, admin_user_id)
            return {"success": False, "message": "Failed to update category"}

    async def delete_category(self, admin_user_id: int, category_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Delete a shop category

        Args:
            admin_user_id: ID of the admin user performing the action
            category_id: ID of the category to delete
            force: If True, deletes category even if it has associated items (default: False)

        Returns:
            Dict containing success status and message
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Get existing category
            stmt = select(ShopCategory).where(ShopCategory.id == category_id)
            result = await self.session.execute(stmt)
            category = result.scalar_one_or_none()

            if not category:
                return {"success": False, "message": f"Category with ID {category_id} not found"}

            category_name = category.name

            # Check if category has associated shop items (unless force is True)
            if not force:
                from database.models import ShopItem
                stmt = select(func.count(ShopItem.c.id)).where(ShopItem.category_id == category_id)
                result = await self.session.execute(stmt)
                item_count = result.scalar()

                if item_count > 0:
                    return {
                        "success": False,
                        "message": f"Cannot delete category '{category_name}' as it has {item_count} associated items. Use force=True to override."
                    }

            # Delete the category
            await self.session.delete(category)
            await self.session.commit()

            logger.info(f"Category '{category_name}' (ID: {category_id}) deleted by admin {admin_user_id}")

            return {
                "success": True,
                "message": f"Category '{category_name}' deleted successfully"
            }

        except Exception as e:
            await self._handle_admin_error("delete_category", e, admin_user_id)
            return {"success": False, "message": "Failed to delete category"}

    # SHOP ITEM MANAGEMENT METHODS

    async def create_shop_item(self, admin_user_id: int, name: str, description: str, price: int,
                              category_id: Optional[int] = None, is_vip_only: bool = False,
                              unlocks_lore_piece_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new shop item

        Args:
            admin_user_id: ID of the admin user performing the action
            name: Name of the item (must be unique)
            description: Description of the item
            price: Price in besitos (must be positive)
            category_id: Optional category ID for the item
            is_vip_only: Whether item is VIP-only (default: False)
            unlocks_lore_piece_id: Optional lore piece ID that this item unlocks

        Returns:
            Dict containing success status, message, and item data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Basic validation
            if not name or not name.strip():
                return {"success": False, "message": "Item name is required"}

            if not description or not description.strip():
                return {"success": False, "message": "Item description is required"}

            if price <= 0:
                return {"success": False, "message": "Item price must be positive"}

            # Check if item with same name already exists
            stmt = select(ShopItem).where(ShopItem.name == name.strip())
            result = await self.session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if existing_item:
                return {"success": False, "message": f"Item '{name}' already exists"}

            # Validate category exists if provided
            if category_id:
                stmt = select(ShopCategory).where(ShopCategory.id == category_id)
                result = await self.session.execute(stmt)
                category = result.scalar_one_or_none()

                if not category:
                    return {"success": False, "message": f"Category with ID {category_id} not found"}

                if not category.is_active:
                    return {"success": False, "message": f"Category '{category.name}' is inactive"}

            # Validate lore piece exists if provided
            if unlocks_lore_piece_id:
                from database.models import LorePiece
                stmt = select(LorePiece).where(LorePiece.id == unlocks_lore_piece_id)
                result = await self.session.execute(stmt)
                lore_piece = result.scalar_one_or_none()

                if not lore_piece:
                    return {"success": False, "message": f"Lore piece with ID {unlocks_lore_piece_id} not found"}

            # Create new shop item
            new_item = ShopItem(
                name=name.strip(),
                description=description.strip(),
                price=price,
                category_id=category_id,
                is_vip_only=is_vip_only,
                unlocks_lore_piece_id=unlocks_lore_piece_id,
                is_active=True
            )

            self.session.add(new_item)
            await self.session.commit()
            await self.session.refresh(new_item)

            logger.info(f"Shop item '{name}' created by admin {admin_user_id}")

            return {
                "success": True,
                "message": f"Shop item '{name}' created successfully",
                "item": {
                    "id": new_item.id,
                    "name": new_item.name,
                    "description": new_item.description,
                    "price": new_item.price,
                    "category_id": new_item.category_id,
                    "is_vip_only": new_item.is_vip_only,
                    "unlocks_lore_piece_id": new_item.unlocks_lore_piece_id,
                    "is_active": new_item.is_active,
                    "created_at": new_item.created_at.isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("create_shop_item", e, admin_user_id)
            return {"success": False, "message": "Failed to create shop item"}

    async def update_shop_item(self, admin_user_id: int, item_id: int, name: Optional[str] = None,
                              description: Optional[str] = None, price: Optional[int] = None,
                              category_id: Optional[int] = None, is_vip_only: Optional[bool] = None,
                              unlocks_lore_piece_id: Optional[int] = None,
                              is_active: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update an existing shop item

        Args:
            admin_user_id: ID of the admin user performing the action
            item_id: ID of the item to update
            name: New name for the item (optional)
            description: New description for the item (optional)
            price: New price for the item (optional)
            category_id: New category ID for the item (optional, use -1 to remove category)
            is_vip_only: New VIP-only status (optional)
            unlocks_lore_piece_id: New lore piece ID (optional, use -1 to remove)
            is_active: New active status (optional)

        Returns:
            Dict containing success status, message, and updated item data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Get existing item
            stmt = select(ShopItem).where(ShopItem.c.id == item_id)
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                return {"success": False, "message": f"Shop item with ID {item_id} not found"}

            # Validate inputs
            if price is not None and price <= 0:
                return {"success": False, "message": "Item price must be positive"}

            # Check if new name conflicts with existing items (if name is being changed)
            if name and name.strip() != item.name:
                stmt = select(ShopItem).where(and_(ShopItem.name == name.strip(), ShopItem.c.id != item_id))
                result = await self.session.execute(stmt)
                existing_item = result.scalar_one_or_none()

                if existing_item:
                    return {"success": False, "message": f"Item name '{name}' already exists"}

            # Validate category exists if provided
            if category_id is not None and category_id != -1:
                stmt = select(ShopCategory).where(ShopCategory.id == category_id)
                result = await self.session.execute(stmt)
                category = result.scalar_one_or_none()

                if not category:
                    return {"success": False, "message": f"Category with ID {category_id} not found"}

                if not category.is_active:
                    return {"success": False, "message": f"Category '{category.name}' is inactive"}

            # Validate lore piece exists if provided
            if unlocks_lore_piece_id is not None and unlocks_lore_piece_id != -1:
                from database.models import LorePiece
                stmt = select(LorePiece).where(LorePiece.id == unlocks_lore_piece_id)
                result = await self.session.execute(stmt)
                lore_piece = result.scalar_one_or_none()

                if not lore_piece:
                    return {"success": False, "message": f"Lore piece with ID {unlocks_lore_piece_id} not found"}

            # Update fields if provided
            updated_fields = []

            if name is not None and name.strip() != item.name:
                item.name = name.strip()
                updated_fields.append("name")

            if description is not None and description.strip() != item.description:
                item.description = description.strip()
                updated_fields.append("description")

            if price is not None and price != item.price:
                item.price = price
                updated_fields.append("price")

            if category_id is not None:
                new_category_id = None if category_id == -1 else category_id
                if new_category_id != item.category_id:
                    item.category_id = new_category_id
                    updated_fields.append("category_id")

            if is_vip_only is not None and is_vip_only != item.is_vip_only:
                item.is_vip_only = is_vip_only
                updated_fields.append("is_vip_only")

            if unlocks_lore_piece_id is not None:
                new_lore_piece_id = None if unlocks_lore_piece_id == -1 else unlocks_lore_piece_id
                if new_lore_piece_id != item.unlocks_lore_piece_id:
                    item.unlocks_lore_piece_id = new_lore_piece_id
                    updated_fields.append("unlocks_lore_piece_id")

            if is_active is not None and is_active != item.is_active:
                item.is_active = is_active
                updated_fields.append("is_active")

            if not updated_fields:
                return {"success": False, "message": "No changes provided"}

            await self.session.commit()
            await self.session.refresh(item)

            logger.info(f"Shop item {item_id} updated by admin {admin_user_id}. Fields: {', '.join(updated_fields)}")

            return {
                "success": True,
                "message": f"Shop item updated successfully. Updated fields: {', '.join(updated_fields)}",
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "category_id": item.category_id,
                    "is_vip_only": item.is_vip_only,
                    "unlocks_lore_piece_id": item.unlocks_lore_piece_id,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("update_shop_item", e, admin_user_id)
            return {"success": False, "message": "Failed to update shop item"}

    async def get_shop_items(self, admin_user_id: int, category_id: Optional[int] = None,
                            include_inactive: bool = False, is_vip_only: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get shop items with filtering options

        Args:
            admin_user_id: ID of the admin user performing the action
            category_id: Optional category ID to filter by
            include_inactive: Whether to include inactive items (default: False)
            is_vip_only: Filter by VIP-only status (None for all, True for VIP-only, False for non-VIP)

        Returns:
            Dict containing success status, message, and items list if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Build query conditions
            conditions = []

            if not include_inactive:
                conditions.append(ShopItem.is_active == True)

            if category_id is not None:
                conditions.append(ShopItem.category_id == category_id)

            if is_vip_only is not None:
                conditions.append(ShopItem.is_vip_only == is_vip_only)

            # Build and execute query
            if conditions:
                stmt = select(ShopItem).where(and_(*conditions)).order_by(ShopItem.name)
            else:
                stmt = select(ShopItem).order_by(ShopItem.name)

            result = await self.session.execute(stmt)
            items = result.scalars().all()

            # Prepare items data
            items_data = []
            for item in items:
                items_data.append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "category_id": item.category_id,
                    "is_vip_only": item.is_vip_only,
                    "unlocks_lore_piece_id": item.unlocks_lore_piece_id,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat()
                })

            logger.info(f"Retrieved {len(items)} shop items for admin {admin_user_id} with filters: category_id={category_id}, include_inactive={include_inactive}, is_vip_only={is_vip_only}")

            return {
                "success": True,
                "message": f"Retrieved {len(items)} shop items",
                "items": items_data
            }

        except Exception as e:
            await self._handle_admin_error("get_shop_items", e, admin_user_id)
            return {"success": False, "message": "Failed to retrieve shop items"}

    async def create_lore_linked_item(self, admin_user_id: int, item_name: str, item_description: str,
                                    item_price: int, lore_title: str, lore_code_name: str,
                                    lore_content: str, lore_content_type: str = "text",
                                    category_id: Optional[int] = None, is_vip_only: bool = False,
                                    lore_description: Optional[str] = None, lore_category: Optional[str] = None,
                                    is_main_story: bool = False, unlock_condition_type: Optional[str] = None,
                                    unlock_condition_value: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new shop item with an associated lore piece in a single atomic transaction

        Args:
            admin_user_id: ID of the admin user performing the action
            item_name: Name of the shop item (must be unique)
            item_description: Description of the shop item
            item_price: Price in besitos (must be positive)
            lore_title: Title of the lore piece
            lore_code_name: Unique code name for the lore piece
            lore_content: Content of the lore piece
            lore_content_type: Type of content (default: "text")
            category_id: Optional category ID for the item
            is_vip_only: Whether item is VIP-only (default: False)
            lore_description: Optional description for the lore piece
            lore_category: Optional category for the lore piece
            is_main_story: Whether lore piece is part of main story (default: False)
            unlock_condition_type: Optional unlock condition type
            unlock_condition_value: Optional unlock condition value

        Returns:
            Dict containing success status, message, and both item and lore piece data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Basic validation
            if not item_name or not item_name.strip():
                return {"success": False, "message": "Item name is required"}

            if not item_description or not item_description.strip():
                return {"success": False, "message": "Item description is required"}

            if item_price <= 0:
                return {"success": False, "message": "Item price must be positive"}

            if not lore_title or not lore_title.strip():
                return {"success": False, "message": "Lore title is required"}

            if not lore_code_name or not lore_code_name.strip():
                return {"success": False, "message": "Lore code name is required"}

            if not lore_content or not lore_content.strip():
                return {"success": False, "message": "Lore content is required"}

            # Check if shop item with same name already exists
            stmt = select(ShopItem).where(ShopItem.name == item_name.strip())
            result = await self.session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if existing_item:
                return {"success": False, "message": f"Shop item '{item_name}' already exists"}

            # Check if lore piece with same code name already exists
            from database.models import LorePiece
            stmt = select(LorePiece).where(LorePiece.code_name == lore_code_name.strip())
            result = await self.session.execute(stmt)
            existing_lore = result.scalar_one_or_none()

            if existing_lore:
                return {"success": False, "message": f"Lore piece with code name '{lore_code_name}' already exists"}

            # Validate category exists if provided
            if category_id:
                stmt = select(ShopCategory).where(ShopCategory.id == category_id)
                result = await self.session.execute(stmt)
                category = result.scalar_one_or_none()

                if not category:
                    return {"success": False, "message": f"Category with ID {category_id} not found"}

                if not category.is_active:
                    return {"success": False, "message": f"Category '{category.name}' is inactive"}

            # Create the lore piece first (following existing pattern)
            new_lore_piece = LorePiece(
                code_name=lore_code_name.strip(),
                title=lore_title.strip(),
                description=lore_description.strip() if lore_description else None,
                content_type=lore_content_type,
                content=lore_content.strip(),
                category=lore_category,
                is_main_story=is_main_story,
                unlock_condition_type=unlock_condition_type,
                unlock_condition_value=unlock_condition_value,
                is_active=True
            )

            self.session.add(new_lore_piece)
            await self.session.flush()  # Flush to get the lore piece ID

            # Create the shop item linked to the lore piece
            new_shop_item = ShopItem(
                name=item_name.strip(),
                description=item_description.strip(),
                price=item_price,
                category_id=category_id,
                is_vip_only=is_vip_only,
                unlocks_lore_piece_id=new_lore_piece.id,
                is_active=True
            )

            self.session.add(new_shop_item)

            # Commit both entities atomically
            await self.session.commit()
            await self.session.refresh(new_lore_piece)
            await self.session.refresh(new_shop_item)

            logger.info(f"Lore-linked shop item '{item_name}' and lore piece '{lore_code_name}' created by admin {admin_user_id}")

            return {
                "success": True,
                "message": f"Lore-linked shop item '{item_name}' created successfully",
                "item": {
                    "id": new_shop_item.id,
                    "name": new_shop_item.name,
                    "description": new_shop_item.description,
                    "price": new_shop_item.price,
                    "category_id": new_shop_item.category_id,
                    "is_vip_only": new_shop_item.is_vip_only,
                    "unlocks_lore_piece_id": new_shop_item.unlocks_lore_piece_id,
                    "is_active": new_shop_item.is_active,
                    "created_at": new_shop_item.created_at.isoformat()
                },
                "lore_piece": {
                    "id": new_lore_piece.id,
                    "code_name": new_lore_piece.code_name,
                    "title": new_lore_piece.title,
                    "description": new_lore_piece.description,
                    "content_type": new_lore_piece.content_type,
                    "content": new_lore_piece.content,
                    "category": new_lore_piece.category,
                    "is_main_story": new_lore_piece.is_main_story,
                    "unlock_condition_type": new_lore_piece.unlock_condition_type,
                    "unlock_condition_value": new_lore_piece.unlock_condition_value,
                    "is_active": new_lore_piece.is_active,
                    "created_at": new_lore_piece.created_at.isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("create_lore_linked_item", e, admin_user_id)
            return {"success": False, "message": "Failed to create lore-linked shop item"}

    # ANALYTICS METHODS

    async def get_purchase_analytics(self, admin_user_id: int, days_back: Optional[int] = 30,
                                   user_id: Optional[int] = None, category_id: Optional[int] = None,
                                   item_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive purchase analytics and user purchase history

        Args:
            admin_user_id: ID of the admin user performing the action
            days_back: Number of days to look back for analytics (default: 30, None for all time)
            user_id: Optional filter by specific user ID
            category_id: Optional filter by specific category ID
            item_id: Optional filter by specific item ID

        Returns:
            Dict containing success status, message, and analytics data if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Build base query conditions
            conditions = []

            # Date filtering
            if days_back is not None:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                conditions.append(UserPurchase.c.purchased_at >= cutoff_date)

            # User filtering
            if user_id is not None:
                conditions.append(UserPurchase.c.user_id == user_id)

            # Item filtering
            if item_id is not None:
                conditions.append(UserPurchase.c.shop_item_id == item_id)

            # Category filtering (requires join with ShopItem)
            if category_id is not None:
                conditions.append(ShopItem.category_id == category_id)

            # Get purchase history with user and item details
            purchase_query = (
                select(
                    UserPurchase.c.id,
                    UserPurchase.c.user_id,
                    UserPurchase.c.shop_item_id,
                    UserPurchase.c.purchased_at,
                    UserPurchase.c.price_paid,
                    User.username,
                    User.first_name,
                    User.role,
                    ShopItem.name.label('item_name'),
                    ShopItem.description.label('item_description'),
                    ShopItem.is_vip_only,
                    ShopCategory.name.label('category_name')
                )
                .select_from(
                    UserPurchase
                    .join(User, UserPurchase.c.user_id == User.c.id)
                    .join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id)
                    .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                )
            )

            if conditions:
                purchase_query = purchase_query.where(and_(*conditions))

            purchase_query = purchase_query.order_by(desc(UserPurchase.c.purchased_at))

            result = await self.session.execute(purchase_query)
            purchases = result.fetchall()

            # Format purchase history
            purchase_history = []
            for purchase in purchases:
                purchase_history.append({
                    "purchase_id": purchase.id,
                    "user_id": purchase.user_id,
                    "username": purchase.username,
                    "first_name": purchase.first_name,
                    "user_role": purchase.role,
                    "item_id": purchase.shop_item_id,
                    "item_name": purchase.item_name,
                    "item_description": purchase.item_description,
                    "is_vip_only": purchase.is_vip_only,
                    "category_name": purchase.category_name,
                    "price_paid": purchase.price_paid,
                    "purchased_at": purchase.purchased_at.isoformat()
                })

            # Calculate analytics metrics
            analytics = await self._calculate_purchase_metrics(conditions, days_back)

            logger.info(f"Retrieved purchase analytics for admin {admin_user_id} - {len(purchases)} purchases, {days_back} days back")

            return {
                "success": True,
                "message": f"Retrieved purchase analytics for {len(purchases)} purchases",
                "analytics": analytics,
                "purchase_history": purchase_history,
                "filters": {
                    "days_back": days_back,
                    "user_id": user_id,
                    "category_id": category_id,
                    "item_id": item_id
                }
            }

        except Exception as e:
            await self._handle_admin_error("get_purchase_analytics", e, admin_user_id)
            return {"success": False, "message": "Failed to retrieve purchase analytics"}

    async def _calculate_purchase_metrics(self, base_conditions: List, days_back: Optional[int]) -> Dict[str, Any]:
        """
        Calculate comprehensive purchase metrics for analytics

        Args:
            base_conditions: Base query conditions to apply
            days_back: Number of days to look back

        Returns:
            Dict containing various analytics metrics
        """
        try:
            # Total sales and revenue
            revenue_query = (
                select(
                    func.count(UserPurchase.c.id).label('total_purchases'),
                    func.sum(UserPurchase.c.price_paid).label('total_revenue'),
                    func.avg(UserPurchase.c.price_paid).label('average_order_value'),
                    func.count(func.distinct(UserPurchase.c.user_id)).label('unique_buyers')
                )
                .select_from(UserPurchase.join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id))
            )

            if base_conditions:
                revenue_query = revenue_query.where(and_(*base_conditions))

            result = await self.session.execute(revenue_query)
            revenue_data = result.fetchone()

            # Category performance
            category_query = (
                select(
                    ShopCategory.name.label('category_name'),
                    func.coalesce(ShopCategory.name, 'Uncategorized').label('category_display'),
                    func.count(UserPurchase.c.id).label('purchases'),
                    func.sum(UserPurchase.c.price_paid).label('revenue'),
                    func.avg(UserPurchase.c.price_paid).label('avg_price')
                )
                .select_from(
                    UserPurchase
                    .join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id)
                    .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                )
            )

            if base_conditions:
                category_query = category_query.where(and_(*base_conditions))

            category_query = category_query.group_by(ShopCategory.name).order_by(desc('revenue'))

            result = await self.session.execute(category_query)
            category_data = result.fetchall()

            # Top selling items
            top_items_query = (
                select(
                    ShopItem.name.label('item_name'),
                    ShopItem.price.label('item_price'),
                    func.count(UserPurchase.c.id).label('purchases'),
                    func.sum(UserPurchase.c.price_paid).label('revenue'),
                    ShopCategory.name.label('category_name')
                )
                .select_from(
                    UserPurchase
                    .join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id)
                    .outerjoin(ShopCategory, ShopItem.category_id == ShopCategory.id)
                )
            )

            if base_conditions:
                top_items_query = top_items_query.where(and_(*base_conditions))

            top_items_query = (
                top_items_query
                .group_by(ShopItem.c.id, ShopItem.name, ShopItem.price, ShopCategory.name)
                .order_by(desc('purchases'))
                .limit(10)
            )

            result = await self.session.execute(top_items_query)
            top_items_data = result.fetchall()

            # VIP vs Free user purchases
            vip_analysis_query = (
                select(
                    User.role,
                    func.count(UserPurchase.c.id).label('purchases'),
                    func.sum(UserPurchase.c.price_paid).label('revenue'),
                    func.avg(UserPurchase.c.price_paid).label('avg_order_value'),
                    func.count(func.distinct(UserPurchase.c.user_id)).label('unique_buyers')
                )
                .select_from(
                    UserPurchase
                    .join(User, UserPurchase.c.user_id == User.c.id)
                    .join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id)
                )
            )

            if base_conditions:
                vip_analysis_query = vip_analysis_query.where(and_(*base_conditions))

            vip_analysis_query = vip_analysis_query.group_by(User.role)

            result = await self.session.execute(vip_analysis_query)
            vip_data = result.fetchall()

            # Daily purchase trends (if days_back is specified)
            daily_trends = []
            if days_back is not None and days_back <= 90:  # Only for reasonable timeframes
                daily_query = (
                    select(
                        func.date(UserPurchase.c.purchased_at).label('purchase_date'),
                        func.count(UserPurchase.c.id).label('purchases'),
                        func.sum(UserPurchase.c.price_paid).label('revenue')
                    )
                    .select_from(UserPurchase.join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id))
                )

                if base_conditions:
                    daily_query = daily_query.where(and_(*base_conditions))

                daily_query = (
                    daily_query
                    .group_by(func.date(UserPurchase.c.purchased_at))
                    .order_by(func.date(UserPurchase.c.purchased_at))
                )

                result = await self.session.execute(daily_query)
                daily_data = result.fetchall()

                for day in daily_data:
                    daily_trends.append({
                        "date": day.purchase_date.isoformat() if day.purchase_date else None,
                        "purchases": day.purchases or 0,
                        "revenue": day.revenue or 0
                    })

            # Calculate conversion rate (users who purchased vs total active users)
            total_users_query = select(func.count(User.c.id)).where(User.role.in_(['free', 'vip']))
            result = await self.session.execute(total_users_query)
            total_users = result.scalar() or 0

            conversion_rate = 0.0
            if total_users > 0 and revenue_data.unique_buyers:
                conversion_rate = (revenue_data.unique_buyers / total_users) * 100

            # Format analytics data
            analytics = {
                "summary": {
                    "total_purchases": revenue_data.total_purchases or 0,
                    "total_revenue": revenue_data.total_revenue or 0,
                    "average_order_value": float(revenue_data.average_order_value or 0),
                    "unique_buyers": revenue_data.unique_buyers or 0,
                    "conversion_rate": round(conversion_rate, 2)
                },
                "category_performance": [
                    {
                        "category": cat.category_display,
                        "purchases": cat.purchases or 0,
                        "revenue": cat.revenue or 0,
                        "average_price": float(cat.avg_price or 0)
                    }
                    for cat in category_data
                ],
                "top_items": [
                    {
                        "item_name": item.item_name,
                        "item_price": item.item_price,
                        "purchases": item.purchases or 0,
                        "revenue": item.revenue or 0,
                        "category": item.category_name
                    }
                    for item in top_items_data
                ],
                "user_type_analysis": [
                    {
                        "user_type": vip.role,
                        "purchases": vip.purchases or 0,
                        "revenue": vip.revenue or 0,
                        "average_order_value": float(vip.avg_order_value or 0),
                        "unique_buyers": vip.unique_buyers or 0
                    }
                    for vip in vip_data
                ],
                "daily_trends": daily_trends
            }

            return analytics

        except Exception as e:
            logger.error(f"Error calculating purchase metrics: {str(e)}")
            return {
                "summary": {"total_purchases": 0, "total_revenue": 0, "average_order_value": 0, "unique_buyers": 0, "conversion_rate": 0},
                "category_performance": [],
                "top_items": [],
                "user_type_analysis": [],
                "daily_trends": []
            }

    async def get_admin_statistics(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive admin statistics for shop management dashboard

        Args:
            admin_user_id: ID of the admin user performing the action

        Returns:
            Dict containing success status, message, and comprehensive statistics if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Shop inventory statistics
            inventory_stats = await self._get_inventory_statistics()

            # Sales performance metrics
            sales_stats = await self._get_sales_statistics()

            # User engagement metrics
            user_stats = await self._get_user_engagement_statistics()

            # Recent activity summary
            recent_activity = await self._get_recent_activity_summary()

            logger.info(f"Retrieved admin statistics for admin {admin_user_id}")

            return {
                "success": True,
                "message": "Admin statistics retrieved successfully",
                "statistics": {
                    "inventory": inventory_stats,
                    "sales": sales_stats,
                    "users": user_stats,
                    "recent_activity": recent_activity,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            await self._handle_admin_error("get_admin_statistics", e, admin_user_id)
            return {"success": False, "message": "Failed to retrieve admin statistics"}

    async def _get_inventory_statistics(self) -> Dict[str, Any]:
        """Get shop inventory statistics"""
        try:
            # Total items and categories
            items_query = select(
                func.count(ShopItem.c.id).label('total_items'),
                func.count(case((ShopItem.is_active == True, 1))).label('active_items'),
                func.count(case((ShopItem.is_vip_only == True, 1))).label('vip_items'),
                func.count(case((ShopItem.unlocks_lore_piece_id.isnot(None), 1))).label('lore_items')
            )
            result = await self.session.execute(items_query)
            items_data = result.fetchone()

            categories_query = select(
                func.count(ShopCategory.id).label('total_categories'),
                func.count(case((ShopCategory.is_active == True, 1))).label('active_categories'),
                func.count(case((ShopCategory.is_vip_only == True, 1))).label('vip_categories')
            )
            result = await self.session.execute(categories_query)
            categories_data = result.fetchone()

            # Price distribution
            price_stats_query = select(
                func.min(ShopItem.price).label('min_price'),
                func.max(ShopItem.price).label('max_price'),
                func.avg(ShopItem.price).label('avg_price')
            ).where(ShopItem.is_active == True)
            result = await self.session.execute(price_stats_query)
            price_data = result.fetchone()

            return {
                "items": {
                    "total": items_data.total_items or 0,
                    "active": items_data.active_items or 0,
                    "inactive": (items_data.total_items or 0) - (items_data.active_items or 0),
                    "vip_only": items_data.vip_items or 0,
                    "with_lore": items_data.lore_items or 0
                },
                "categories": {
                    "total": categories_data.total_categories or 0,
                    "active": categories_data.active_categories or 0,
                    "inactive": (categories_data.total_categories or 0) - (categories_data.active_categories or 0),
                    "vip_only": categories_data.vip_categories or 0
                },
                "pricing": {
                    "min_price": price_data.min_price or 0,
                    "max_price": price_data.max_price or 0,
                    "average_price": float(price_data.avg_price or 0)
                }
            }

        except Exception as e:
            logger.error(f"Error getting inventory statistics: {str(e)}")
            return {"items": {}, "categories": {}, "pricing": {}}

    async def _get_sales_statistics(self) -> Dict[str, Any]:
        """Get sales performance statistics"""
        try:
            # Overall sales metrics
            overall_query = select(
                func.count(UserPurchase.c.id).label('total_sales'),
                func.sum(UserPurchase.c.price_paid).label('total_revenue'),
                func.avg(UserPurchase.c.price_paid).label('avg_order_value'),
                func.count(func.distinct(UserPurchase.c.user_id)).label('unique_customers')
            )
            result = await self.session.execute(overall_query)
            overall_data = result.fetchone()

            # Time-based metrics
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=7)
            month_start = today_start - timedelta(days=30)

            # Today's sales
            today_query = select(
                func.count(UserPurchase.c.id).label('sales'),
                func.sum(UserPurchase.c.price_paid).label('revenue')
            ).where(UserPurchase.c.purchased_at >= today_start)
            result = await self.session.execute(today_query)
            today_data = result.fetchone()

            # Week's sales
            week_query = select(
                func.count(UserPurchase.c.id).label('sales'),
                func.sum(UserPurchase.c.price_paid).label('revenue')
            ).where(UserPurchase.c.purchased_at >= week_start)
            result = await self.session.execute(week_query)
            week_data = result.fetchone()

            # Month's sales
            month_query = select(
                func.count(UserPurchase.c.id).label('sales'),
                func.sum(UserPurchase.c.price_paid).label('revenue')
            ).where(UserPurchase.c.purchased_at >= month_start)
            result = await self.session.execute(month_query)
            month_data = result.fetchone()

            return {
                "overall": {
                    "total_sales": overall_data.total_sales or 0,
                    "total_revenue": overall_data.total_revenue or 0,
                    "average_order_value": float(overall_data.avg_order_value or 0),
                    "unique_customers": overall_data.unique_customers or 0
                },
                "today": {
                    "sales": today_data.sales or 0,
                    "revenue": today_data.revenue or 0
                },
                "last_7_days": {
                    "sales": week_data.sales or 0,
                    "revenue": week_data.revenue or 0
                },
                "last_30_days": {
                    "sales": month_data.sales or 0,
                    "revenue": month_data.revenue or 0
                }
            }

        except Exception as e:
            logger.error(f"Error getting sales statistics: {str(e)}")
            return {"overall": {}, "today": {}, "last_7_days": {}, "last_30_days": {}}

    async def _get_user_engagement_statistics(self) -> Dict[str, Any]:
        """Get user engagement statistics"""
        try:
            # User base metrics
            users_query = select(
                func.count(User.c.id).label('total_users'),
                func.count(case((User.role == 'vip', 1))).label('vip_users'),
                func.count(case((User.role == 'free', 1))).label('free_users')
            )
            result = await self.session.execute(users_query)
            users_data = result.fetchone()

            # Users with purchases
            buyers_query = select(
                func.count(func.distinct(UserPurchase.c.user_id)).label('total_buyers')
            )
            result = await self.session.execute(buyers_query)
            buyers_data = result.fetchone()

            # Calculate conversion rate
            total_users = users_data.total_users or 0
            total_buyers = buyers_data.total_buyers or 0
            conversion_rate = (total_buyers / total_users * 100) if total_users > 0 else 0

            # VIP conversion metrics
            vip_buyers_query = select(
                func.count(func.distinct(UserPurchase.c.user_id)).label('vip_buyers')
            ).select_from(
                UserPurchase.join(User, UserPurchase.c.user_id == User.c.id)
            ).where(User.role == 'vip')
            result = await self.session.execute(vip_buyers_query)
            vip_buyers_data = result.fetchone()

            vip_users = users_data.vip_users or 0
            vip_buyers = vip_buyers_data.vip_buyers or 0
            vip_conversion_rate = (vip_buyers / vip_users * 100) if vip_users > 0 else 0

            return {
                "user_base": {
                    "total_users": total_users,
                    "vip_users": vip_users,
                    "free_users": users_data.free_users or 0
                },
                "purchasing_behavior": {
                    "total_buyers": total_buyers,
                    "overall_conversion_rate": round(conversion_rate, 2),
                    "vip_buyers": vip_buyers,
                    "vip_conversion_rate": round(vip_conversion_rate, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error getting user engagement statistics: {str(e)}")
            return {"user_base": {}, "purchasing_behavior": {}}

    async def _get_recent_activity_summary(self) -> Dict[str, Any]:
        """Get recent activity summary"""
        try:
            # Recent purchases (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)

            recent_purchases_query = select(
                UserPurchase.c.purchased_at,
                User.username,
                User.first_name,
                ShopItem.name.label('item_name'),
                UserPurchase.c.price_paid
            ).select_from(
                UserPurchase
                .join(User, UserPurchase.c.user_id == User.c.id)
                .join(ShopItem, UserPurchase.c.shop_item_id == ShopItem.c.id)
            ).where(
                UserPurchase.c.purchased_at >= yesterday
            ).order_by(desc(UserPurchase.c.purchased_at)).limit(10)

            result = await self.session.execute(recent_purchases_query)
            recent_purchases = result.fetchall()

            # Format recent purchases
            recent_activity = []
            for purchase in recent_purchases:
                recent_activity.append({
                    "type": "purchase",
                    "timestamp": purchase.purchased_at.isoformat(),
                    "user": purchase.username or purchase.first_name or "Unknown User",
                    "item_name": purchase.item_name,
                    "price": purchase.price_paid
                })

            return {
                "recent_purchases": recent_activity,
                "summary": f"{len(recent_activity)} purchases in the last 24 hours"
            }

        except Exception as e:
            logger.error(f"Error getting recent activity summary: {str(e)}")
            return {"recent_purchases": [], "summary": "Unable to load recent activity"}

    # CSV IMPORT/EXPORT METHODS

    async def export_catalog_csv(self, admin_user_id: int, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Export shop catalog (categories and items) to CSV format

        Args:
            admin_user_id: ID of the admin user performing the action
            include_inactive: Whether to include inactive categories and items (default: False)

        Returns:
            Dict containing success status, message, and CSV content if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Get categories
            categories_conditions = []
            if not include_inactive:
                categories_conditions.append(ShopCategory.is_active == True)

            if categories_conditions:
                categories_stmt = select(ShopCategory).where(and_(*categories_conditions)).order_by(ShopCategory.display_order, ShopCategory.name)
            else:
                categories_stmt = select(ShopCategory).order_by(ShopCategory.display_order, ShopCategory.name)

            categories_result = await self.session.execute(categories_stmt)
            categories = categories_result.scalars().all()

            # Get items
            items_conditions = []
            if not include_inactive:
                items_conditions.append(ShopItem.is_active == True)

            if items_conditions:
                items_stmt = select(ShopItem).where(and_(*items_conditions)).order_by(ShopItem.name)
            else:
                items_stmt = select(ShopItem).order_by(ShopItem.name)

            items_result = await self.session.execute(items_stmt)
            items = items_result.scalars().all()

            # Create CSV content
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)

            # Write categories section
            writer.writerow(['# CATEGORIES'])
            writer.writerow(['type', 'id', 'name', 'description', 'display_order', 'is_vip_only', 'is_active', 'created_at'])

            for category in categories:
                writer.writerow([
                    'category',
                    category.id,
                    category.name,
                    category.description or '',
                    category.display_order,
                    category.is_vip_only,
                    category.is_active,
                    category.created_at.isoformat()
                ])

            # Add separator
            writer.writerow([])

            # Write items section
            writer.writerow(['# ITEMS'])
            writer.writerow(['type', 'id', 'name', 'description', 'price', 'category_id', 'category_name', 'is_vip_only', 'unlocks_lore_piece_id', 'is_active', 'created_at'])

            for item in items:
                # Get category name if exists
                category_name = ''
                if item.category_id:
                    category = next((c for c in categories if c.id == item.category_id), None)
                    if category:
                        category_name = category.name

                writer.writerow([
                    'item',
                    item.id,
                    item.name,
                    item.description or '',
                    item.price,
                    item.category_id or '',
                    category_name,
                    item.is_vip_only,
                    item.unlocks_lore_piece_id or '',
                    item.is_active,
                    item.created_at.isoformat()
                ])

            csv_content = csv_output.getvalue()
            csv_output.close()

            logger.info(f"Catalog CSV exported by admin {admin_user_id} - {len(categories)} categories, {len(items)} items")

            return {
                "success": True,
                "message": f"Catalog CSV exported successfully - {len(categories)} categories, {len(items)} items",
                "csv_content": csv_content,
                "stats": {
                    "categories_count": len(categories),
                    "items_count": len(items),
                    "include_inactive": include_inactive
                }
            }

        except Exception as e:
            await self._handle_admin_error("export_catalog_csv", e, admin_user_id)
            return {"success": False, "message": "Failed to export catalog CSV"}

    async def import_catalog_csv(self, admin_user_id: int, csv_content: str, update_existing: bool = False,
                                skip_validation_errors: bool = False) -> Dict[str, Any]:
        """
        Import shop catalog (categories and items) from CSV format

        Args:
            admin_user_id: ID of the admin user performing the action
            csv_content: CSV content string to import
            update_existing: Whether to update existing items/categories with same names (default: False)
            skip_validation_errors: Whether to skip rows with validation errors and continue (default: False)

        Returns:
            Dict containing success status, message, and import results if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Basic CSV validation
            if not csv_content or not csv_content.strip():
                return {"success": False, "message": "CSV content is required"}

            # Parse CSV content
            csv_input = io.StringIO(csv_content)
            reader = csv.reader(csv_input)

            import_results = {
                "categories_processed": 0,
                "categories_created": 0,
                "categories_updated": 0,
                "categories_errors": [],
                "items_processed": 0,
                "items_created": 0,
                "items_updated": 0,
                "items_errors": [],
                "validation_errors": []
            }

            current_section = None
            category_header_found = False
            item_header_found = False
            categories_by_name = {}  # Track categories for item validation

            try:
                for row_num, row in enumerate(reader, 1):
                    # Skip empty rows
                    if not row or all(cell.strip() == '' for cell in row):
                        continue

                    # Check for section headers
                    if row and row[0].startswith('#'):
                        if 'CATEGORIES' in row[0].upper():
                            current_section = 'categories'
                            continue
                        elif 'ITEMS' in row[0].upper():
                            current_section = 'items'
                            continue

                    # Check for field headers
                    if row and len(row) > 0 and row[0] == 'type':
                        if current_section == 'categories':
                            category_header_found = True
                            continue
                        elif current_section == 'items':
                            item_header_found = True
                            continue

                    # Process data rows
                    if current_section == 'categories' and category_header_found:
                        result = await self._import_category_from_csv_row(
                            row, row_num, update_existing, skip_validation_errors
                        )
                        if result:
                            import_results["categories_processed"] += 1
                            if result.get("action") == "created":
                                import_results["categories_created"] += 1
                                categories_by_name[result["category"]["name"]] = result["category"]
                            elif result.get("action") == "updated":
                                import_results["categories_updated"] += 1
                                categories_by_name[result["category"]["name"]] = result["category"]
                            elif result.get("error"):
                                import_results["categories_errors"].append(f"Row {row_num}: {result['error']}")
                                if not skip_validation_errors:
                                    await self.session.rollback()
                                    return {"success": False, "message": f"Category import error at row {row_num}: {result['error']}"}

                    elif current_section == 'items' and item_header_found:
                        result = await self._import_item_from_csv_row(
                            row, row_num, update_existing, skip_validation_errors, categories_by_name
                        )
                        if result:
                            import_results["items_processed"] += 1
                            if result.get("action") == "created":
                                import_results["items_created"] += 1
                            elif result.get("action") == "updated":
                                import_results["items_updated"] += 1
                            elif result.get("error"):
                                import_results["items_errors"].append(f"Row {row_num}: {result['error']}")
                                if not skip_validation_errors:
                                    await self.session.rollback()
                                    return {"success": False, "message": f"Item import error at row {row_num}: {result['error']}"}

            except Exception as parse_error:
                await self.session.rollback()
                return {"success": False, "message": f"CSV parsing error: {str(parse_error)}"}

            # Commit all changes if we've gotten this far
            await self.session.commit()

            logger.info(f"Catalog CSV imported by admin {admin_user_id} - Results: {import_results}")

            return {
                "success": True,
                "message": f"Catalog CSV imported successfully - {import_results['categories_created']} categories created, {import_results['categories_updated']} categories updated, {import_results['items_created']} items created, {import_results['items_updated']} items updated",
                "import_results": import_results
            }

        except Exception as e:
            await self._handle_admin_error("import_catalog_csv", e, admin_user_id)
            return {"success": False, "message": "Failed to import catalog CSV"}

    async def _import_category_from_csv_row(self, row: List[str], row_num: int, update_existing: bool,
                                          skip_validation_errors: bool) -> Optional[Dict[str, Any]]:
        """
        Import a single category from CSV row

        Args:
            row: CSV row data
            row_num: Row number for error reporting
            update_existing: Whether to update existing categories
            skip_validation_errors: Whether to skip validation errors

        Returns:
            Dict with import result or None if skipped
        """
        try:
            # Validate row structure
            if len(row) < 7:  # Minimum required fields
                error_msg = "Insufficient columns for category row"
                if skip_validation_errors:
                    return {"error": error_msg}
                return {"error": error_msg}

            row_type, cat_id, name, description, display_order, is_vip_only, is_active = row[:7]

            # Skip if not a category row
            if row_type.lower() != 'category':
                return None

            # Validate required fields
            if not name or not name.strip():
                error_msg = "Category name is required"
                if skip_validation_errors:
                    return {"error": error_msg}
                return {"error": error_msg}

            name = name.strip()
            description = description.strip() if description else None

            # Validate and convert numeric fields
            try:
                display_order = int(display_order) if display_order else 0
            except ValueError:
                display_order = 0

            # Validate boolean fields
            is_vip_only = str(is_vip_only).lower() in ('true', '1', 'yes', 'on')
            is_active = str(is_active).lower() in ('true', '1', 'yes', 'on')

            # Check if category already exists
            stmt = select(ShopCategory).where(ShopCategory.name == name)
            result = await self.session.execute(stmt)
            existing_category = result.scalar_one_or_none()

            if existing_category:
                if not update_existing:
                    return {"error": f"Category '{name}' already exists"}

                # Update existing category
                existing_category.description = description
                existing_category.display_order = display_order
                existing_category.is_vip_only = is_vip_only
                existing_category.is_active = is_active

                await self.session.flush()
                await self.session.refresh(existing_category)

                return {
                    "action": "updated",
                    "category": {
                        "id": existing_category.id,
                        "name": existing_category.name,
                        "description": existing_category.description,
                        "display_order": existing_category.display_order,
                        "is_vip_only": existing_category.is_vip_only,
                        "is_active": existing_category.is_active
                    }
                }
            else:
                # Create new category
                new_category = ShopCategory(
                    name=name,
                    description=description,
                    display_order=display_order,
                    is_vip_only=is_vip_only,
                    is_active=is_active
                )

                self.session.add(new_category)
                await self.session.flush()
                await self.session.refresh(new_category)

                return {
                    "action": "created",
                    "category": {
                        "id": new_category.id,
                        "name": new_category.name,
                        "description": new_category.description,
                        "display_order": new_category.display_order,
                        "is_vip_only": new_category.is_vip_only,
                        "is_active": new_category.is_active
                    }
                }

        except Exception as e:
            error_msg = f"Error processing category row: {str(e)}"
            return {"error": error_msg}

    async def _import_item_from_csv_row(self, row: List[str], row_num: int, update_existing: bool,
                                      skip_validation_errors: bool, categories_by_name: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Import a single item from CSV row

        Args:
            row: CSV row data
            row_num: Row number for error reporting
            update_existing: Whether to update existing items
            skip_validation_errors: Whether to skip validation errors
            categories_by_name: Dictionary of category names to category data

        Returns:
            Dict with import result or None if skipped
        """
        try:
            # Validate row structure
            if len(row) < 10:  # Minimum required fields
                error_msg = "Insufficient columns for item row"
                if skip_validation_errors:
                    return {"error": error_msg}
                return {"error": error_msg}

            row_type, item_id, name, description, price, category_id, category_name, is_vip_only, unlocks_lore_piece_id, is_active = row[:10]

            # Skip if not an item row
            if row_type.lower() != 'item':
                return None

            # Validate required fields
            if not name or not name.strip():
                error_msg = "Item name is required"
                if skip_validation_errors:
                    return {"error": error_msg}
                return {"error": error_msg}

            name = name.strip()
            description = description.strip() if description else ""

            # Validate and convert price
            try:
                price = int(price)
                if price <= 0:
                    error_msg = "Item price must be positive"
                    if skip_validation_errors:
                        return {"error": error_msg}
                    return {"error": error_msg}
            except (ValueError, TypeError):
                error_msg = "Invalid price format"
                if skip_validation_errors:
                    return {"error": error_msg}
                return {"error": error_msg}

            # Handle category_id
            final_category_id = None
            if category_id and category_id.strip():
                try:
                    final_category_id = int(category_id)
                except ValueError:
                    # If category_id is not numeric, try to find by category_name
                    if category_name and category_name.strip():
                        category_name = category_name.strip()
                        if category_name in categories_by_name:
                            final_category_id = categories_by_name[category_name]["id"]
                        else:
                            # Try to find in database
                            stmt = select(ShopCategory).where(ShopCategory.name == category_name)
                            result = await self.session.execute(stmt)
                            category = result.scalar_one_or_none()
                            if category:
                                final_category_id = category.id

            # Validate boolean fields
            is_vip_only = str(is_vip_only).lower() in ('true', '1', 'yes', 'on')
            is_active = str(is_active).lower() in ('true', '1', 'yes', 'on')

            # Handle lore_piece_id
            final_lore_piece_id = None
            if unlocks_lore_piece_id and unlocks_lore_piece_id.strip():
                try:
                    final_lore_piece_id = int(unlocks_lore_piece_id)
                except ValueError:
                    # Invalid lore piece ID format - set to None
                    final_lore_piece_id = None

            # Check if item already exists
            stmt = select(ShopItem).where(ShopItem.name == name)
            result = await self.session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if existing_item:
                if not update_existing:
                    return {"error": f"Item '{name}' already exists"}

                # Update existing item
                existing_item.description = description
                existing_item.price = price
                existing_item.category_id = final_category_id
                existing_item.is_vip_only = is_vip_only
                existing_item.unlocks_lore_piece_id = final_lore_piece_id
                existing_item.is_active = is_active

                await self.session.flush()
                await self.session.refresh(existing_item)

                return {
                    "action": "updated",
                    "item": {
                        "id": existing_item.id,
                        "name": existing_item.name,
                        "description": existing_item.description,
                        "price": existing_item.price,
                        "category_id": existing_item.category_id,
                        "is_vip_only": existing_item.is_vip_only,
                        "unlocks_lore_piece_id": existing_item.unlocks_lore_piece_id,
                        "is_active": existing_item.is_active
                    }
                }
            else:
                # Create new item
                new_item = ShopItem(
                    name=name,
                    description=description,
                    price=price,
                    category_id=final_category_id,
                    is_vip_only=is_vip_only,
                    unlocks_lore_piece_id=final_lore_piece_id,
                    is_active=is_active
                )

                self.session.add(new_item)
                await self.session.flush()
                await self.session.refresh(new_item)

                return {
                    "action": "created",
                    "item": {
                        "id": new_item.id,
                        "name": new_item.name,
                        "description": new_item.description,
                        "price": new_item.price,
                        "category_id": new_item.category_id,
                        "is_vip_only": new_item.is_vip_only,
                        "unlocks_lore_piece_id": new_item.unlocks_lore_piece_id,
                        "is_active": new_item.is_active
                    }
                }

        except Exception as e:
            error_msg = f"Error processing item row: {str(e)}"
            return {"error": error_msg}

    # NARRATIVE INTEGRATION METHODS

    async def register_narrative_item(self, admin_user_id: int, item_id: int,
                                    narrative_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a shop item for automatic narrative integration with decision requirements mapping
        and teaser/exclusive fragment generation following CoordinadorCentral patterns.

        Args:
            admin_user_id: ID of the admin user performing the action
            item_id: ID of the shop item to register for narrative integration
            narrative_config: Optional configuration for narrative integration including:
                - decision_id: Decision ID that should require this item
                - teaser_content: Custom teaser content (auto-generated if not provided)
                - exclusive_content: Custom exclusive content (auto-generated if not provided)
                - fragment_character: Character for fragments (default: "diana")
                - category: Narrative category (default: "item_unlock")

        Returns:
            Dict containing success status, message, and integration details if successful
        """
        try:
            # Validate admin access
            if not await self.validate_admin_access(admin_user_id):
                return {"success": False, "message": "Admin access required"}

            # Get the shop item
            stmt = select(ShopItem).where(ShopItem.c.id == item_id)
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                return {"success": False, "message": f"Shop item with ID {item_id} not found"}

            if not item.is_active:
                return {"success": False, "message": f"Cannot register inactive item '{item.name}' for narrative integration"}

            # Set default narrative configuration
            config = narrative_config or {}
            decision_id = config.get("decision_id")
            fragment_character = config.get("fragment_character", "diana")
            category = config.get("category", "item_unlock")

            # Auto-generate decision_id if not provided, based on item characteristics
            if decision_id is None:
                decision_id = await self._generate_decision_id_for_item(item)

            # Import required models for fragment creation
            from database.narrative_models import StoryFragment, NarrativeChoice
            from database.models import LorePiece

            # Create or update lore piece for this item if it doesn't have one
            lore_piece = None
            if item.unlocks_lore_piece_id:
                stmt = select(LorePiece).where(LorePiece.id == item.unlocks_lore_piece_id)
                result = await self.session.execute(stmt)
                lore_piece = result.scalar_one_or_none()

            if not lore_piece:
                # Create a new lore piece for this item
                lore_piece = await self._create_item_lore_piece(item, config)
                item.unlocks_lore_piece_id = lore_piece.id

            # Generate teaser and exclusive fragments
            teaser_fragment = await self._create_teaser_fragment(item, lore_piece, config)
            exclusive_fragment = await self._create_exclusive_fragment(item, lore_piece, config)

            # Update the CoordinadorCentral decision requirements mapping
            await self._register_decision_requirement(decision_id, item.name)

            # Create narrative choices connecting teaser to exclusive content
            await self._create_narrative_choices(teaser_fragment, exclusive_fragment, item)

            await self.session.commit()

            logger.info(f"Narrative item '{item.name}' registered by admin {admin_user_id} with decision_id {decision_id}")

            return {
                "success": True,
                "message": f"Item '{item.name}' successfully registered for narrative integration",
                "integration_details": {
                    "item_id": item.id,
                    "item_name": item.name,
                    "decision_id": decision_id,
                    "lore_piece_id": lore_piece.id,
                    "teaser_fragment_key": teaser_fragment.key,
                    "exclusive_fragment_key": exclusive_fragment.key,
                    "narrative_category": category,
                    "character": fragment_character
                }
            }

        except Exception as e:
            await self._handle_admin_error("register_narrative_item", e, admin_user_id)
            return {"success": False, "message": "Failed to register item for narrative integration"}

    async def _generate_decision_id_for_item(self, item: ShopItem) -> int:
        """
        Generate an appropriate decision ID for an item based on its characteristics
        following the existing pattern in CoordinadorCentral.
        """
        # Base decision ID on item characteristics and existing patterns
        if "diario" in item.name.lower() and "secreto" in item.name.lower():
            return 1  # First decision requires diary (existing pattern)
        elif "diario" in item.name.lower() and "íntimo" in item.name.lower():
            return 15  # Diary intimate choice (existing pattern)
        elif "collar" in item.name.lower():
            return 20  # Jewelry decisions
        elif "cofre" in item.name.lower() or "recuerdo" in item.name.lower():
            return 25  # Memory-related decisions
        elif "máscara" in item.name.lower():
            return 30  # Mask/disguise decisions
        else:
            # Generate based on item ID for uniqueness, offset to avoid conflicts
            return 100 + item.id

    async def _create_item_lore_piece(self, item: ShopItem, config: Dict[str, Any]) -> "LorePiece":
        """Create a lore piece for the item following existing patterns."""
        from database.models import LorePiece

        # Generate content based on item characteristics
        if "diario" in item.name.lower():
            content_type = "diary_entry"
            content = self._generate_diary_content(item, config)
        elif "collar" in item.name.lower():
            content_type = "jewelry_story"
            content = self._generate_jewelry_content(item, config)
        elif "cofre" in item.name.lower():
            content_type = "memory_box"
            content = self._generate_memory_content(item, config)
        else:
            content_type = "item_story"
            content = self._generate_generic_item_content(item, config)

        lore_piece = LorePiece(
            code_name=f"{item.name.lower().replace(' ', '_').replace('📖', '').replace('📓', '').replace('🔑', '').replace('💎', '').replace('🎭', '').strip()}_lore",
            title=f"Historia de {item.name}",
            description=f"La historia íntima detrás de {item.name}",
            content_type=content_type,
            content=content,
            category=config.get("category", "item_unlock"),
            is_main_story=False,
            unlock_condition_type="shop_item",
            unlock_condition_value=str(item.id),
            is_active=True
        )

        self.session.add(lore_piece)
        await self.session.flush()
        return lore_piece

    async def _create_teaser_fragment(self, item: ShopItem, lore_piece: "LorePiece",
                                    config: Dict[str, Any]) -> "StoryFragment":
        """Create a teaser fragment that shows when user doesn't have the item."""
        from database.narrative_models import StoryFragment

        teaser_content = config.get("teaser_content") or self._generate_teaser_content(item)

        teaser_fragment = StoryFragment(
            key=f"{item.name.lower().replace(' ', '_').replace('📖', '').replace('📓', '').replace('🔑', '').replace('💎', '').replace('🎭', '').strip()}_tease",
            text=teaser_content,
            character=config.get("fragment_character", "diana"),
            level=1,
            min_besitos=0,
            required_role=None,
            reward_besitos=5  # Small reward for viewing teaser
        )

        self.session.add(teaser_fragment)
        await self.session.flush()
        return teaser_fragment

    async def _create_exclusive_fragment(self, item: ShopItem, lore_piece: "LorePiece",
                                       config: Dict[str, Any]) -> "StoryFragment":
        """Create the exclusive fragment that shows when user has the item."""
        from database.narrative_models import StoryFragment

        exclusive_content = config.get("exclusive_content") or self._generate_exclusive_content(item, lore_piece)

        exclusive_fragment = StoryFragment(
            key=f"{item.name.lower().replace(' ', '_').replace('📖', '').replace('📓', '').replace('🔑', '').replace('💎', '').replace('🎭', '').strip()}_exclusive",
            text=exclusive_content,
            character=config.get("fragment_character", "diana"),
            level=2,
            min_besitos=0,
            required_role=None,
            reward_besitos=15  # Higher reward for exclusive content
        )

        self.session.add(exclusive_fragment)
        await self.session.flush()
        return exclusive_fragment

    async def _register_decision_requirement(self, decision_id: int, item_name: str) -> None:
        """
        Register the decision requirement mapping following CoordinadorCentral patterns.
        Since DecisionRequirement model doesn't exist, we log the mapping for manual integration.
        """
        # Log the decision requirement mapping for manual addition to CoordinadorCentral
        logger.info(f"NARRATIVE INTEGRATION: decision_id {decision_id} requires item '{item_name}'")
        logger.info(f"Add to CoordinadorCentral._flujo_tomar_decision decision_requirements dict: {decision_id}: \"{item_name}\"")

        # Store in a simple metadata approach using lore piece if available
        # This allows the system to work without requiring database schema changes
        # The CoordinadorCentral can be updated manually with the logged mappings

    async def _create_narrative_choices(self, teaser_fragment: "StoryFragment",
                                      exclusive_fragment: "StoryFragment", item: ShopItem) -> None:
        """Create narrative choices linking teaser to exclusive content."""
        from database.narrative_models import NarrativeChoice

        # Choice to view the full content (requires item)
        exclusive_choice = NarrativeChoice(
            source_fragment_id=teaser_fragment.id,
            destination_fragment_key=exclusive_fragment.key,
            text=f"📖 Leer el contenido completo (requiere {item.name})",
            required_besitos=0,
            required_role=None
        )

        # Choice to visit shop if user doesn't have the item
        shop_choice = NarrativeChoice(
            source_fragment_id=teaser_fragment.id,
            destination_fragment_key="shop_redirect",
            text="🛍️ Visitar la tienda",
            required_besitos=0,
            required_role=None
        )

        self.session.add_all([exclusive_choice, shop_choice])

    def _generate_teaser_content(self, item: ShopItem) -> str:
        """Generate teaser content based on item characteristics."""
        base_templates = {
            "diario": "💋 *Diana susurra mientras acaricia las páginas de su {item_name}...*\n\n\"Aquí están escritos mis secretos más profundos, mis confesiones más íntimas... pero solo quienes poseen mi {item_name} pueden leer estas palabras.\"\n\n*Sus ojos brillan con un misterio que te invita a descubrir más...*",
            "collar": "✨ *Diana toca delicadamente su {item_name}, sus dedos trazando cada detalle...*\n\n\"Este collar guarda la memoria de una noche muy especial... Si lo tuvieras, podrías conocer toda la historia.\"\n\n*Una sonrisa enigmática se dibuja en sus labios...*",
            "cofre": "🔑 *Diana abre ligeramente su {item_name}, revelando solo un destello de su contenido...*\n\n\"Recuerdos, fotografías, cartas de amor... Todo está aquí, esperando a quien sepa valorar estos tesoros.\"\n\n*Cierra el cofre suavemente, guardando sus secretos...*",
            "máscara": "🎭 *Diana sostiene su {item_name} entre sus manos, contemplándola con nostalgia...*\n\n\"Esa noche en el baile de máscaras cambió todo... Si tuvieras esta máscara, podrías revivir cada momento mágico.\"\n\n*La luz juega con las curvas de la máscara, creando sombras misteriosas...*"
        }

        # Determine template based on item name
        item_type = "diario" if "diario" in item.name.lower() else \
                   "collar" if "collar" in item.name.lower() else \
                   "cofre" if "cofre" in item.name.lower() else \
                   "máscara" if "máscara" in item.name.lower() else \
                   "diario"  # Default template

        template = base_templates[item_type]
        return template.format(item_name=item.name)

    def _generate_exclusive_content(self, item: ShopItem, lore_piece: "LorePiece") -> str:
        """Generate exclusive content that shows when user has the item."""
        return f"🔓 **Contenido Exclusivo Desbloqueado**\n\n{lore_piece.content}\n\n*Gracias a tu {item.name}, ahora conoces este secreto íntimo de Diana...*"

    def _generate_diary_content(self, item: ShopItem, config: Dict[str, Any]) -> str:
        """Generate diary-specific content."""
        if "íntimo" in item.name.lower():
            return "💭 *Querido diario íntimo,*\n\nHoy he sentido una conexión especial con alguien... Sus mensajes despiertan en mí sensaciones que creía olvidadas. Hay algo en la forma en que me escribe que me hace vibrar por dentro.\n\n*¿Será esta la persona que estaba esperando? Solo el tiempo lo dirá...*\n\n💋 Diana"
        else:
            return "📝 *Mi querido diario,*\n\nHe estado pensando mucho últimamente en las conexiones genuinas, en esas personas especiales que aparecen en nuestras vidas cuando menos lo esperamos.\n\nCada conversación es un regalo, cada mensaje una caricia al alma.\n\n✨ Diana"

    def _generate_jewelry_content(self, item: ShopItem, config: Dict[str, Any]) -> str:
        """Generate jewelry-specific content."""
        return f"✨ **La Historia del {item.name}**\n\nEste collar fue un regalo muy especial, recibido en una noche de luna llena. Cada vez que lo uso, recuerdo las palabras susurradas al oído: 'Eres la luz que ilumina mi oscuridad'.\n\n*Ahora que conoces su historia, cada vez que lo veas brillar, recordarás este momento íntimo entre nosotros...*\n\n💎 Diana"

    def _generate_memory_content(self, item: ShopItem, config: Dict[str, Any]) -> str:
        """Generate memory box content."""
        return f"📦 **Contenido del {item.name}**\n\n*Diana abre el cofre completamente, revelando sus tesoros más preciados...*\n\n• Una fotografía de una puesta de sol\n• Una carta perfumada con su esencia\n• Un pétalos de rosa seco\n• Una llave pequeña de plata\n\n\"Cada objeto cuenta una historia de amor, pasión y misterio. Ahora que tienes mi cofre, eres custodio de estos recuerdos.\"\n\n🗝️ Diana"

    def _generate_generic_item_content(self, item: ShopItem, config: Dict[str, Any]) -> str:
        """Generate generic content for any item."""
        return f"🌟 **El Secreto de {item.name}**\n\n*Diana sonríe mientras te cuenta la historia detrás de este objeto especial...*\n\n\"No es solo un objeto, es un pedazo de mi alma, una parte de mi historia que ahora comparto contigo. Cada vez que lo veas, recordarás este momento especial entre nosotros.\"\n\n*Sus ojos brillan con ternura y complicidad...*\n\n💋 Diana"