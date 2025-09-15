"""
Shop Caching Service for DianaBot

Provides memory-based caching for shop items and categories to improve performance
and reduce database queries. Implements TTL management and cache invalidation methods.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import ShopItem, ShopCategory

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item with TTL information"""
    data: Any
    expires_at: datetime
    created_at: datetime


class ShopCacheService:
    """
    Memory-based caching service for shop items and categories.

    Features:
    - TTL (Time To Live) management for cache entries
    - Separate caching for items and categories
    - Cache invalidation methods
    - User-specific caching for VIP filtering
    - Automatic cache cleanup
    """

    def __init__(self, session: AsyncSession, default_ttl_minutes: int = 15):
        """
        Initialize the shop cache service.

        Args:
            session: Database session for fallback queries
            default_ttl_minutes: Default cache TTL in minutes (default: 15)
        """
        self.session = session
        self.default_ttl = timedelta(minutes=default_ttl_minutes)

        # Cache storage
        self._items_cache: Dict[str, CacheEntry] = {}
        self._categories_cache: Dict[str, CacheEntry] = {}
        self._user_items_cache: Dict[int, CacheEntry] = {}  # user_id -> categorized items

        # Cache keys
        self._ALL_ITEMS_KEY = "all_items"
        self._ALL_CATEGORIES_KEY = "all_categories"
        self._ACTIVE_ITEMS_KEY = "active_items"
        self._ACTIVE_CATEGORIES_KEY = "active_categories"

        logger.info(f"ShopCacheService initialized with {default_ttl_minutes}min TTL")

    async def get_all_items(self, force_refresh: bool = False) -> List[ShopItem]:
        """
        Get all shop items (including inactive ones).

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of all shop items
        """
        if not force_refresh:
            cached_items = self._get_cached_data(self._items_cache, self._ALL_ITEMS_KEY)
            if cached_items is not None:
                logger.debug("Retrieved all items from cache")
                return cached_items

        # Fetch from database
        try:
            stmt = select(ShopItem).order_by(ShopItem.name)
            result = await self.session.execute(stmt)
            items = list(result.scalars().all())

            # Cache the result
            self._set_cached_data(self._items_cache, self._ALL_ITEMS_KEY, items)
            logger.info(f"Cached {len(items)} total items")
            return items

        except Exception as e:
            logger.error(f"Error fetching all items from database: {str(e)}")
            return []

    async def get_active_items(self, force_refresh: bool = False) -> List[ShopItem]:
        """
        Get only active shop items.

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of active shop items
        """
        if not force_refresh:
            cached_items = self._get_cached_data(self._items_cache, self._ACTIVE_ITEMS_KEY)
            if cached_items is not None:
                logger.debug("Retrieved active items from cache")
                return cached_items

        # Fetch from database
        try:
            stmt = select(ShopItem).where(ShopItem.is_active == True).order_by(ShopItem.name)
            result = await self.session.execute(stmt)
            items = list(result.scalars().all())

            # Cache the result
            self._set_cached_data(self._items_cache, self._ACTIVE_ITEMS_KEY, items)
            logger.info(f"Cached {len(items)} active items")
            return items

        except Exception as e:
            logger.error(f"Error fetching active items from database: {str(e)}")
            return []

    async def get_all_categories(self, force_refresh: bool = False) -> List[ShopCategory]:
        """
        Get all shop categories (including inactive ones).

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of all shop categories
        """
        if not force_refresh:
            cached_categories = self._get_cached_data(self._categories_cache, self._ALL_CATEGORIES_KEY)
            if cached_categories is not None:
                logger.debug("Retrieved all categories from cache")
                return cached_categories

        # Fetch from database
        try:
            stmt = select(ShopCategory).order_by(ShopCategory.display_order, ShopCategory.name)
            result = await self.session.execute(stmt)
            categories = list(result.scalars().all())

            # Cache the result
            self._set_cached_data(self._categories_cache, self._ALL_CATEGORIES_KEY, categories)
            logger.info(f"Cached {len(categories)} total categories")
            return categories

        except Exception as e:
            logger.error(f"Error fetching all categories from database: {str(e)}")
            return []

    async def get_active_categories(self, force_refresh: bool = False) -> List[ShopCategory]:
        """
        Get only active shop categories.

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of active shop categories
        """
        if not force_refresh:
            cached_categories = self._get_cached_data(self._categories_cache, self._ACTIVE_CATEGORIES_KEY)
            if cached_categories is not None:
                logger.debug("Retrieved active categories from cache")
                return cached_categories

        # Fetch from database
        try:
            stmt = select(ShopCategory).where(ShopCategory.is_active == True).order_by(
                ShopCategory.display_order, ShopCategory.name
            )
            result = await self.session.execute(stmt)
            categories = list(result.scalars().all())

            # Cache the result
            self._set_cached_data(self._categories_cache, self._ACTIVE_CATEGORIES_KEY, categories)
            logger.info(f"Cached {len(categories)} active categories")
            return categories

        except Exception as e:
            logger.error(f"Error fetching active categories from database: {str(e)}")
            return []

    async def get_user_available_items(self, user_id: int, is_vip: bool, force_refresh: bool = False) -> List[ShopItem]:
        """
        Get items available to a specific user based on VIP status.

        Args:
            user_id: User ID for caching
            is_vip: Whether the user has VIP status
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of items available to the user
        """
        if not force_refresh:
            cached_items = self._get_cached_data(self._user_items_cache, f"available_{user_id}")
            if cached_items is not None:
                logger.debug(f"Retrieved available items for user {user_id} from cache")
                return cached_items

        # Get all active items and filter by VIP status
        active_items = await self.get_active_items(force_refresh=force_refresh)

        if is_vip:
            # VIP users can see all active items
            available_items = active_items
        else:
            # Non-VIP users can only see non-VIP items
            available_items = [item for item in active_items if not item.is_vip_only]

        # Cache the result with shorter TTL for user-specific data
        user_ttl = timedelta(minutes=5)  # Shorter TTL for user-specific caches
        self._set_cached_data(self._user_items_cache, f"available_{user_id}", available_items, ttl=user_ttl)
        logger.info(f"Cached {len(available_items)} available items for user {user_id} (VIP: {is_vip})")
        return available_items

    async def get_items_by_category(self, category_id: Optional[int], is_vip: bool = True, force_refresh: bool = False) -> List[ShopItem]:
        """
        Get items filtered by category.

        Args:
            category_id: Category ID to filter by (None for uncategorized items)
            is_vip: Whether to include VIP-only items
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of items in the specified category
        """
        cache_key = f"category_{category_id}_vip_{is_vip}"

        if not force_refresh:
            cached_items = self._get_cached_data(self._items_cache, cache_key)
            if cached_items is not None:
                logger.debug(f"Retrieved category {category_id} items from cache")
                return cached_items

        # Get active items and filter by category and VIP status
        active_items = await self.get_active_items(force_refresh=force_refresh)

        # Filter by category
        if category_id is None:
            # Get uncategorized items
            category_items = [item for item in active_items if item.category_id is None]
        else:
            category_items = [item for item in active_items if item.category_id == category_id]

        # Filter by VIP status
        if not is_vip:
            category_items = [item for item in category_items if not item.is_vip_only]

        # Cache the result
        self._set_cached_data(self._items_cache, cache_key, category_items)
        logger.info(f"Cached {len(category_items)} items for category {category_id}")
        return category_items

    def invalidate_items_cache(self):
        """Invalidate all items cache entries."""
        keys_to_remove = [
            self._ALL_ITEMS_KEY,
            self._ACTIVE_ITEMS_KEY
        ]

        # Also remove category-specific and user-specific caches
        keys_to_remove.extend([key for key in self._items_cache.keys() if key.startswith("category_")])

        for key in keys_to_remove:
            self._items_cache.pop(key, None)

        # Clear user-specific caches
        self._user_items_cache.clear()

        logger.info("Invalidated items cache")

    def invalidate_categories_cache(self):
        """Invalidate all categories cache entries."""
        keys_to_remove = [
            self._ALL_CATEGORIES_KEY,
            self._ACTIVE_CATEGORIES_KEY
        ]

        for key in keys_to_remove:
            self._categories_cache.pop(key, None)

        logger.info("Invalidated categories cache")

    def invalidate_user_cache(self, user_id: int):
        """
        Invalidate cache entries for a specific user.

        Args:
            user_id: User ID to invalidate cache for
        """
        keys_to_remove = [key for key in self._user_items_cache.keys() if str(user_id) in str(key)]

        for key in keys_to_remove:
            self._user_items_cache.pop(key, None)

        logger.info(f"Invalidated cache for user {user_id}")

    def invalidate_all_cache(self):
        """Invalidate all cache entries."""
        self._items_cache.clear()
        self._categories_cache.clear()
        self._user_items_cache.clear()
        logger.info("Invalidated all cache entries")

    def cleanup_expired_entries(self):
        """Remove expired cache entries from all caches."""
        now = datetime.utcnow()

        # Clean items cache
        expired_items = [key for key, entry in self._items_cache.items() if entry.expires_at <= now]
        for key in expired_items:
            del self._items_cache[key]

        # Clean categories cache
        expired_categories = [key for key, entry in self._categories_cache.items() if entry.expires_at <= now]
        for key in expired_categories:
            del self._categories_cache[key]

        # Clean user items cache
        expired_user_items = [key for key, entry in self._user_items_cache.items() if entry.expires_at <= now]
        for key in expired_user_items:
            del self._user_items_cache[key]

        total_expired = len(expired_items) + len(expired_categories) + len(expired_user_items)
        if total_expired > 0:
            logger.info(f"Cleaned up {total_expired} expired cache entries")

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring and debugging.

        Returns:
            Dictionary with cache statistics
        """
        now = datetime.utcnow()

        # Count active entries
        active_items = sum(1 for entry in self._items_cache.values() if entry.expires_at > now)
        active_categories = sum(1 for entry in self._categories_cache.values() if entry.expires_at > now)
        active_user_items = sum(1 for entry in self._user_items_cache.values() if entry.expires_at > now)

        # Count expired entries
        expired_items = sum(1 for entry in self._items_cache.values() if entry.expires_at <= now)
        expired_categories = sum(1 for entry in self._categories_cache.values() if entry.expires_at <= now)
        expired_user_items = sum(1 for entry in self._user_items_cache.values() if entry.expires_at <= now)

        return {
            "active_entries": {
                "items": active_items,
                "categories": active_categories,
                "user_items": active_user_items,
                "total": active_items + active_categories + active_user_items
            },
            "expired_entries": {
                "items": expired_items,
                "categories": expired_categories,
                "user_items": expired_user_items,
                "total": expired_items + expired_categories + expired_user_items
            },
            "total_entries": {
                "items": len(self._items_cache),
                "categories": len(self._categories_cache),
                "user_items": len(self._user_items_cache),
                "total": len(self._items_cache) + len(self._categories_cache) + len(self._user_items_cache)
            },
            "default_ttl_minutes": self.default_ttl.total_seconds() / 60
        }

    def _get_cached_data(self, cache: Dict[str, CacheEntry], key: str) -> Optional[Any]:
        """
        Get data from cache if not expired.

        Args:
            cache: Cache dictionary to search in
            key: Cache key

        Returns:
            Cached data if valid, None if expired or not found
        """
        if key not in cache:
            return None

        entry = cache[key]
        if entry.expires_at <= datetime.utcnow():
            # Entry has expired, remove it
            del cache[key]
            return None

        return entry.data

    def _set_cached_data(self, cache: Dict[str, CacheEntry], key: str, data: Any, ttl: Optional[timedelta] = None):
        """
        Set data in cache with TTL.

        Args:
            cache: Cache dictionary to store in
            key: Cache key
            data: Data to cache
            ttl: Time to live (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        now = datetime.utcnow()
        entry = CacheEntry(
            data=data,
            expires_at=now + ttl,
            created_at=now
        )
        cache[key] = entry