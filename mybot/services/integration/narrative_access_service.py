"""
Integration service to connect narrative system with subscription verification.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from services.subscription_service import SubscriptionService
from services.narrative_service import NarrativeService

logger = logging.getLogger(__name__)

class NarrativeAccessService:
    """
    Service to handle access control for narrative content based on subscription status.
    Integrates the narrative system with the subscription system.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_service = SubscriptionService(session)
        self.narrative_service = NarrativeService(session)
    
    async def can_access_fragment(self, user_id: int, fragment_key: str) -> bool:
        """
        Checks if a user can access a specific narrative fragment based on their subscription.
        VIP fragments (levels 4-6) require an active subscription.
        
        Args:
            user_id: The Telegram user ID
            fragment_key: The key of the narrative fragment
            
        Returns:
            bool: True if the user can access the fragment, False otherwise
        """
        # Check if fragment is VIP content (levels 4-6)
        if fragment_key.startswith(('level4_', 'level5_', 'level6_', 'vip_')):
            is_subscribed = await self.subscription_service.is_subscription_active(user_id)
            if not is_subscribed:
                logger.info(f"User {user_id} attempted to access VIP fragment {fragment_key} without subscription")
                return False
            logger.info(f"User {user_id} granted access to VIP fragment {fragment_key}")
            return True
        
        # Non-VIP content is accessible to all
        return True
    
    async def get_accessible_fragment(self, user_id: int, requested_fragment_key: str = None):
        """
        Gets a fragment that the user can access. If the requested fragment is not accessible,
        returns a fallback fragment or a message about subscription requirements.
        
        Args:
            user_id: The Telegram user ID
            requested_fragment_key: Optional specific fragment key to access
            
        Returns:
            dict: The fragment data or a message about subscription requirements
        """
        fragment_key = requested_fragment_key
        if not fragment_key:
            # Get user's current fragment from narrative service
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            fragment_key = current_fragment.key if current_fragment else 'start'
        
        # Check access
        can_access = await self.can_access_fragment(user_id, fragment_key)
        if not can_access:
            # Return subscription required message instead of actual fragment
            return {
                "type": "subscription_required",
                "message": "Este contenido requiere una suscripción VIP activa.",
                "requested_fragment": fragment_key
            }
        
        # User can access, get the actual fragment
        if requested_fragment_key:
            # TODO: Implement fragment fetching by key
            # This would need to be added to NarrativeService
            pass
        
        # Return current fragment from narrative service
        return await self.narrative_service.get_user_current_fragment(user_id)
