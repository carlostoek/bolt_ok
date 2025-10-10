"""
Narrative State Machine - Centralizes state management for narrative flow.

This module provides a robust state machine to eliminate race conditions
in the narrative system by centralizing all state transitions related to
the shop→narrative flow.

The state machine uses atomic database operations and comprehensive logging
to ensure state consistency across concurrent operations.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.narrative_models import UserNarrativeState

logger = logging.getLogger(__name__)


class NarrativeFlowState(Enum):
    """Represents the current state of a user's narrative flow."""

    READING_FRAGMENT = "reading"
    MAKING_DECISION = "deciding"
    SHOPPING = "shopping"
    PROCESSING_PURCHASE = "processing_purchase"
    RETURNING_FROM_SHOP = "returning"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class NarrativeStateMachine:
    """
    Manages state transitions for the narrative flow system.

    This state machine centralizes all state management for the shop→narrative
    flow, preventing race conditions by using atomic database operations and
    proper state validation.

    Attributes:
        session: AsyncSession for database operations
    """

    # Define valid state transitions
    VALID_TRANSITIONS = {
        NarrativeFlowState.READING_FRAGMENT: {
            NarrativeFlowState.MAKING_DECISION,
            NarrativeFlowState.SHOPPING,
        },
        NarrativeFlowState.MAKING_DECISION: {
            NarrativeFlowState.SHOPPING,
            NarrativeFlowState.READING_FRAGMENT,
        },
        NarrativeFlowState.SHOPPING: {
            NarrativeFlowState.PROCESSING_PURCHASE,
            NarrativeFlowState.RETURNING_FROM_SHOP,
        },
        NarrativeFlowState.PROCESSING_PURCHASE: {
            NarrativeFlowState.RETURNING_FROM_SHOP,
        },
        NarrativeFlowState.RETURNING_FROM_SHOP: {
            NarrativeFlowState.READING_FRAGMENT,
            NarrativeFlowState.MAKING_DECISION,
        },
    }

    def __init__(self, session: AsyncSession):
        """
        Initialize the state machine.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    async def _get_or_create_user_state(
        self,
        user_id: int
    ) -> UserNarrativeState:
        """
        Get or create the UserNarrativeState record for a user.

        Args:
            user_id: The user's ID

        Returns:
            UserNarrativeState record
        """
        result = await self.session.execute(
            select(UserNarrativeState).where(
                UserNarrativeState.user_id == user_id
            )
        )
        user_state = result.scalar_one_or_none()

        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                shop_context={}
            )
            self.session.add(user_state)
            await self.session.flush()
            logger.info(f"[STATE_MACHINE] Created new state record for user {user_id}")

        return user_state

    async def _validate_transition(
        self,
        user_id: int,
        from_state: NarrativeFlowState,
        to_state: NarrativeFlowState
    ) -> None:
        """
        Validate that a state transition is allowed.

        Args:
            user_id: The user's ID
            from_state: Current state
            to_state: Desired state

        Raises:
            StateTransitionError: If the transition is invalid
        """
        valid_next_states = self.VALID_TRANSITIONS.get(from_state, set())

        if to_state not in valid_next_states:
            error_msg = (
                f"Invalid state transition for user {user_id}: "
                f"{from_state.value} -> {to_state.value}"
            )
            logger.error(f"[STATE_MACHINE] {error_msg}")
            raise StateTransitionError(error_msg)

    async def get_current_state(self, user_id: int) -> NarrativeFlowState:
        """
        Get the current state for a user.

        Args:
            user_id: The user's ID

        Returns:
            Current NarrativeFlowState
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)

            # If no shop_context, user is in default state
            if not user_state.shop_context:
                return NarrativeFlowState.READING_FRAGMENT

            state_value = user_state.shop_context.get('state')
            if not state_value:
                return NarrativeFlowState.READING_FRAGMENT

            try:
                return NarrativeFlowState(state_value)
            except ValueError:
                logger.warning(
                    f"[STATE_MACHINE] Invalid state value '{state_value}' "
                    f"for user {user_id}, defaulting to READING_FRAGMENT"
                )
                return NarrativeFlowState.READING_FRAGMENT

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error getting current state for user {user_id}: {e}",
                exc_info=True
            )
            # Default to safe state
            return NarrativeFlowState.READING_FRAGMENT

    async def transition_to_shop(
        self,
        user_id: int,
        current_fragment_key: str,
        pending_decision_id: Optional[int] = None
    ) -> bool:
        """
        Transition user to shopping state.

        This method atomically transitions the user to SHOPPING state and
        stores all necessary context for returning to the narrative.

        Args:
            user_id: The user's ID
            current_fragment_key: Fragment key to return to
            pending_decision_id: Optional decision awaiting completion

        Returns:
            True if transition succeeded, False otherwise
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)
            current_state = await self.get_current_state(user_id)

            # Validate transition
            await self._validate_transition(
                user_id,
                current_state,
                NarrativeFlowState.SHOPPING
            )

            # Build shop context
            shop_context = {
                'state': NarrativeFlowState.SHOPPING.value,
                'return_fragment_key': current_fragment_key,
                'transition_timestamp': datetime.utcnow().isoformat(),
                'previous_state': current_state.value,
            }

            if pending_decision_id is not None:
                shop_context['pending_decision_id'] = pending_decision_id

            # Atomic update
            user_state.shop_context = shop_context
            await self.session.commit()

            logger.info(
                f"[STATE_MACHINE] User {user_id} transitioned to SHOPPING "
                f"(from {current_state.value}). "
                f"Return fragment: {current_fragment_key}, "
                f"Pending decision: {pending_decision_id}"
            )

            return True

        except StateTransitionError as e:
            logger.error(f"[STATE_MACHINE] State transition error: {e}")
            await self.session.rollback()
            return False

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error transitioning user {user_id} to shop: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return False

    async def transition_to_processing_purchase(
        self,
        user_id: int,
        item_id: Optional[int] = None
    ) -> bool:
        """
        Transition user to processing purchase state.

        Args:
            user_id: The user's ID
            item_id: Optional item being purchased

        Returns:
            True if transition succeeded, False otherwise
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)
            current_state = await self.get_current_state(user_id)

            # Validate transition
            await self._validate_transition(
                user_id,
                current_state,
                NarrativeFlowState.PROCESSING_PURCHASE
            )

            # Update state, preserve existing context
            if not user_state.shop_context:
                user_state.shop_context = {}

            user_state.shop_context['state'] = NarrativeFlowState.PROCESSING_PURCHASE.value
            user_state.shop_context['purchase_timestamp'] = datetime.utcnow().isoformat()

            if item_id is not None:
                user_state.shop_context['processing_item_id'] = item_id

            await self.session.commit()

            logger.info(
                f"[STATE_MACHINE] User {user_id} transitioned to PROCESSING_PURCHASE "
                f"(item_id: {item_id})"
            )

            return True

        except StateTransitionError as e:
            logger.error(f"[STATE_MACHINE] State transition error: {e}")
            await self.session.rollback()
            return False

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error transitioning user {user_id} to processing: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return False

    async def return_from_shop(self, user_id: int) -> Dict[str, Any]:
        """
        Get shop return context WITHOUT modifying state (READ-ONLY).

        CRITICAL: This method is READ-ONLY. It returns the shop context
        but does NOT clear it. The caller must explicitly call
        clear_shop_context() ONLY after successful decision processing.

        This prevents the race condition where context is lost if decision
        processing fails after returning from shop.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing:
                - success: bool
                - return_fragment_key: str or None
                - pending_decision_id: int or None
                - previous_state: str or None
                - error: str (only if success=False)
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)
            current_state = await self.get_current_state(user_id)

            # Must be in shop-related state
            if current_state not in {
                NarrativeFlowState.SHOPPING,
                NarrativeFlowState.PROCESSING_PURCHASE,
                NarrativeFlowState.RETURNING_FROM_SHOP,
            }:
                error_msg = f"Cannot return from shop in state: {current_state.value}"
                logger.warning(f"[STATE_MACHINE] {error_msg} for user {user_id}")
                return {
                    'success': False,
                    'error': error_msg,
                    'return_fragment_key': None,
                    'pending_decision_id': None,
                }

            # Extract return context (READ-ONLY - no modifications)
            shop_context = user_state.shop_context or {}
            return_fragment_key = shop_context.get('return_fragment_key')
            pending_decision_id = shop_context.get('pending_decision_id')
            previous_state = shop_context.get('previous_state')

            logger.info(
                f"[STATE_MACHINE] User {user_id} shop context retrieved (READ-ONLY): "
                f"Return fragment: {return_fragment_key}, "
                f"Pending decision: {pending_decision_id} "
                f"- Context will be cleared by caller on success"
            )

            return {
                'success': True,
                'return_fragment_key': return_fragment_key,
                'pending_decision_id': pending_decision_id,
                'previous_state': previous_state,
            }

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error reading shop context for user {user_id}: {e}",
                exc_info=True
            )
            return {
                'success': False,
                'error': str(e),
                'return_fragment_key': None,
                'pending_decision_id': None,
            }

    async def clear_shop_context(self, user_id: int) -> None:
        """
        Clear all shop-related context for a user.

        This resets the user to a clean READING_FRAGMENT state.
        Use this when you need to reset a user's state (e.g., on errors
        or when starting a new narrative).

        Args:
            user_id: The user's ID
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)

            # Clear to default reading state
            user_state.shop_context = {
                'state': NarrativeFlowState.READING_FRAGMENT.value,
                'cleared_timestamp': datetime.utcnow().isoformat(),
            }

            await self.session.commit()

            logger.info(
                f"[STATE_MACHINE] Cleared shop context for user {user_id}, "
                f"reset to READING_FRAGMENT"
            )

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error clearing shop context for user {user_id}: {e}",
                exc_info=True
            )
            await self.session.rollback()

    async def get_shop_context(self, user_id: int) -> Dict[str, Any]:
        """
        Get the complete shop context for a user.

        Useful for debugging and understanding the user's state.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing the shop context
        """
        try:
            user_state = await self._get_or_create_user_state(user_id)
            return user_state.shop_context or {}

        except Exception as e:
            logger.error(
                f"[STATE_MACHINE] Error getting shop context for user {user_id}: {e}",
                exc_info=True
            )
            return {}

    async def is_in_shop_flow(self, user_id: int) -> bool:
        """
        Check if user is currently in any shop-related state.

        Args:
            user_id: The user's ID

        Returns:
            True if user is in shop flow, False otherwise
        """
        current_state = await self.get_current_state(user_id)
        return current_state in {
            NarrativeFlowState.SHOPPING,
            NarrativeFlowState.PROCESSING_PURCHASE,
            NarrativeFlowState.RETURNING_FROM_SHOP,
        }
