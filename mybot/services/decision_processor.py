"""
Decision Processor Service - Handles special decision logic (item requirements, teasers, etc.)

This service is extracted from CoordinadorCentral to follow the Single Responsibility Principle.
It manages all decision-specific logic including:
- Item requirement checking
- Special decision flows (teasers, redirects)
- Decision requirement configuration loading

Author: Extracted from CoordinadorCentral
Date: 2025-10-10
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from config.decision_constants import DecisionID, get_decision_name
from database.narrative_models import StoryFragment

logger = logging.getLogger(__name__)

# Path to decision requirements configuration
_DECISION_REQUIREMENTS_PATH = Path(__file__).parent.parent / "config" / "decision_requirements.json"


def _load_decision_requirements() -> Dict[int, str]:
    """
    Load decision requirements from JSON configuration file.
    Returns a dictionary mapping decision_id (int) to item_name (str).
    Falls back to hardcoded defaults if file doesn't exist.

    Returns:
        Dict mapping decision IDs to required item names
    """
    if not _DECISION_REQUIREMENTS_PATH.exists():
        logger.warning(
            f"[DECISION_PROCESSOR] Decision requirements file not found at "
            f"{_DECISION_REQUIREMENTS_PATH}, using defaults"
        )
        # Return hardcoded defaults
        return {
            1: "📖 Diario Secreto",
            15: "📓 Diario Íntimo",
        }

    try:
        with open(_DECISION_REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Convert string keys to integers
            requirements = {int(k): v for k, v in config.items()}
            logger.info(
                f"[DECISION_PROCESSOR] Loaded {len(requirements)} decision requirements "
                f"from configuration"
            )
            return requirements
    except Exception as e:
        logger.error(
            f"[DECISION_PROCESSOR] Error loading decision requirements from "
            f"{_DECISION_REQUIREMENTS_PATH}: {e}"
        )
        # Return hardcoded defaults on error
        return {
            1: "📖 Diario Secreto",
            15: "📓 Diario Íntimo",
        }


class DecisionProcessor:
    """
    Handles special decision logic (item requirements, teasers, etc.)

    This service is extracted from CoordinadorCentral for better SRP compliance.
    It manages all decision-specific processing including:
    - Checking if decisions require items
    - Processing special decision flows (like teaser redirects)
    - Managing decision-specific state transitions

    Attributes:
        session: Database session for async operations
        shop_service: Service for checking user inventory
        narrative_service: Service for fragment operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the DecisionProcessor with required services.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        # Import here to avoid circular dependencies
        try:
            from services.shop_service import ShopService
            from services.narrative_service import NarrativeService
            self.shop_service = ShopService(session)
            self.narrative_service = NarrativeService(session)
            logger.info("[DECISION_PROCESSOR] Service initialized successfully")
        except ImportError as e:
            logger.error(f"[DECISION_PROCESSOR] Failed to import required services: {e}")
            raise

    async def check_item_requirement(
        self,
        user_id: int,
        decision_id: int
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a decision requires an item and if the user has it.

        This method loads decision requirements from JSON configuration and checks
        the user's inventory to determine if they can proceed with the decision.

        Args:
            user_id: Telegram user ID
            decision_id: ID of the decision being made

        Returns:
            Tuple containing:
                - has_item (bool): Whether user has the required item
                - required_item_name (Optional[str]): Name of required item, or None
                - teaser_fragment_key (Optional[str]): Key for teaser fragment if applicable

        Example:
            >>> has_item, item_name, teaser_key = await processor.check_item_requirement(12345, 15)
            >>> if not has_item and item_name:
            >>>     print(f"User needs {item_name}")
        """
        # Load decision requirements from JSON configuration
        # This is managed through the admin panel (Admin → Tienda → Gestionar Desbloqueos)
        decision_requirements = _load_decision_requirements()

        logger.debug(
            f"[DECISION_PROCESSOR] Checking item requirement for user {user_id}, "
            f"decision {get_decision_name(decision_id)} (ID: {decision_id})"
        )

        # Check if this decision requires an item
        required_item = decision_requirements.get(decision_id)

        if not required_item:
            # No item required - user can proceed
            logger.debug(
                f"[DECISION_PROCESSOR] Decision {decision_id} has no item requirement"
            )
            return True, None, None

        # Check user inventory for the required item
        has_item = await self.shop_service.has_item_in_inventory(user_id, required_item)

        if has_item:
            logger.info(
                f"[DECISION_PROCESSOR] User {user_id} has required item '{required_item}' "
                f"for decision {decision_id}"
            )
            return True, required_item, None
        else:
            logger.info(
                f"[DECISION_PROCESSOR] User {user_id} missing item '{required_item}' "
                f"for decision {decision_id}"
            )

            # Determine if there's a teaser fragment for this decision
            teaser_fragment_key = None
            if decision_id == DecisionID.DIARY_INTIMATE:
                teaser_fragment_key = "diana_diary_tease"
                logger.info(
                    f"[DECISION_PROCESSOR] Special decision {get_decision_name(decision_id)} "
                    f"has teaser fragment: {teaser_fragment_key}"
                )

            return False, required_item, teaser_fragment_key

    async def process_special_decision(
        self,
        user_id: int,
        decision_id: int,
        has_required_item: bool,
        teaser_fragment_key: Optional[str]
    ) -> Optional[StoryFragment]:
        """
        Handle special decision flows (teasers, redirects, etc.)

        This method processes decisions that have special behavior, such as showing
        a teaser fragment when the user doesn't have the required item, instead of
        simply blocking access.

        Args:
            user_id: Telegram user ID
            decision_id: ID of the decision being made
            has_required_item: Whether user has the required item
            teaser_fragment_key: Key for teaser fragment, if applicable

        Returns:
            StoryFragment if redirected to teaser, None if normal flow should continue

        Example:
            >>> fragment = await processor.process_special_decision(
            ...     user_id=12345,
            ...     decision_id=DecisionID.DIARY_INTIMATE,
            ...     has_required_item=False,
            ...     teaser_fragment_key="diana_diary_tease"
            ... )
            >>> if fragment:
            ...     # User was redirected to teaser
            ...     return show_fragment(fragment)
        """
        # If user has the required item, no special processing needed
        if has_required_item:
            logger.debug(
                f"[DECISION_PROCESSOR] No special processing needed for decision {decision_id} "
                f"- user has required item"
            )
            return None

        # If no teaser fragment defined, no special processing
        if not teaser_fragment_key:
            logger.debug(
                f"[DECISION_PROCESSOR] No teaser fragment for decision {decision_id}"
            )
            return None

        # Special handling for diary intimate decision - redirect to teaser
        if decision_id == DecisionID.DIARY_INTIMATE:
            logger.info(
                f"[DECISION_PROCESSOR] Special decision {get_decision_name(decision_id)} "
                f"- redirecting to teaser fragment: {teaser_fragment_key}"
            )

            try:
                # Get the teaser fragment
                teaser_fragment = await self.narrative_service._get_fragment_by_key(
                    teaser_fragment_key
                )

                if not teaser_fragment:
                    logger.error(
                        f"[DECISION_PROCESSOR] Teaser fragment '{teaser_fragment_key}' "
                        f"not found for decision {decision_id}"
                    )
                    return None

                # Update user state to the teaser fragment
                user_state = await self.narrative_service._get_or_create_user_state(user_id)
                user_state.current_fragment_key = teaser_fragment.key
                user_state.fragments_visited = (user_state.fragments_visited or 0) + 1

                # Process fragment rewards (besitos, etc.)
                await self.narrative_service._process_fragment_rewards(user_id, teaser_fragment)
                await self.session.commit()

                logger.info(
                    f"[DECISION_PROCESSOR] Successfully redirected user {user_id} to "
                    f"teaser fragment: {teaser_fragment.key}"
                )

                return teaser_fragment

            except Exception as e:
                logger.exception(
                    f"[DECISION_PROCESSOR] Error processing teaser redirect for "
                    f"user {user_id}, decision {decision_id}: {e}"
                )
                return None

        # No special processing for other decision types yet
        logger.debug(
            f"[DECISION_PROCESSOR] No special processing implemented for "
            f"decision {decision_id}"
        )
        return None

    async def get_required_item_message(
        self,
        decision_id: int,
        required_item_name: str,
        character_voice_service=None
    ) -> str:
        """
        Generate a message for when user lacks a required item.

        Args:
            decision_id: ID of the decision
            required_item_name: Name of the required item
            character_voice_service: Optional CharacterVoiceService for authentic messages

        Returns:
            Formatted message string explaining the requirement
        """
        # Try to get authentic character voice message
        if character_voice_service:
            try:
                from services.character_voice_service import CharacterType, EmotionalContext
                restriction_message = character_voice_service.get_character_response(
                    CharacterType.DIANA,
                    EmotionalContext.VULNERABILIDAD_BAJA,
                    "item_required"
                )
            except Exception as e:
                logger.debug(
                    f"[DECISION_PROCESSOR] Could not get character voice message: {e}"
                )
                restriction_message = "💋 Diana susurra: 'Este camino requiere algo más íntimo...'"
        else:
            restriction_message = "💋 Diana susurra: 'Este camino requiere algo más íntimo...'"

        message = (
            f"{restriction_message}\n\n"
            f"🔒 **Acceso Restringido**\n\n"
            f"Necesitas el {required_item_name} para tomar esta decisión.\n\n"
            f"Visita la tienda para adquirirlo."
        )

        logger.info(
            f"[DECISION_PROCESSOR] Generated item requirement message for "
            f"decision {decision_id}, item: {required_item_name}"
        )

        return message
