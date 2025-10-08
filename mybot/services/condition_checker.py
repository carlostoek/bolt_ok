"""
Service for checking compound unlock requirements for shop items.

Supports complex conditions like:
- User level >= 5
- VIP status = true
- Owns specific item
- Points >= 100
- Owns lore piece
- Completed mission
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import (
    User, ShopItem, UserPurchase, UserLorePiece,
    UserMissionEntry, Mission
)
from utils.constants import ConditionOperator, ConditionType, ComparisonOperator

logger = logging.getLogger(__name__)


class ConditionChecker:
    """Evaluates compound unlock requirements for shop items."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_requirements(
        self,
        user_id: int,
        requirements: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user meets compound requirements.

        Args:
            user_id: User ID to check
            requirements: JSON requirements structure or None

        Returns:
            Tuple of (meets_requirements: bool, failed_conditions: List[str])
        """
        if requirements is None:
            return True, []

        operator = requirements.get("operator", ConditionOperator.AND)
        conditions = requirements.get("conditions", [])

        if not conditions:
            return True, []

        # Evaluate each condition
        results = []
        failed_messages = []

        for condition in conditions:
            meets_condition, fail_message = await self._check_single_condition(
                user_id, condition
            )
            results.append(meets_condition)
            if not meets_condition:
                failed_messages.append(fail_message)

        # Apply operator logic
        if operator == ConditionOperator.AND:
            meets_all = all(results)
            return meets_all, failed_messages if not meets_all else []
        elif operator == ConditionOperator.OR:
            meets_any = any(results)
            return meets_any, failed_messages if not meets_any else []
        else:
            logger.error(f"Unknown operator: {operator}")
            return False, ["Error: operador desconocido"]

    async def _check_single_condition(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Check a single condition.

        Returns:
            Tuple of (passes: bool, fail_message: str)
        """
        cond_type = condition.get("type")
        value = condition.get("value")
        comparison = condition.get("comparison", ComparisonOperator.GREATER_EQUAL)

        try:
            if cond_type == ConditionType.LEVEL:
                return await self._check_level(user_id, value, comparison)
            elif cond_type == ConditionType.VIP_STATUS:
                return await self._check_vip_status(user_id, value)
            elif cond_type == ConditionType.OWNS_ITEM:
                return await self._check_owns_item(user_id, value)
            elif cond_type == ConditionType.POINTS:
                return await self._check_points(user_id, value, comparison)
            elif cond_type == ConditionType.OWNS_LORE_PIECE:
                return await self._check_owns_lore_piece(user_id, value)
            elif cond_type == ConditionType.COMPLETED_MISSION:
                return await self._check_completed_mission(user_id, value)
            else:
                logger.error(f"Unknown condition type: {cond_type}")
                return False, f"Tipo de condición desconocido: {cond_type}"
        except Exception as e:
            logger.error(f"Error checking condition {cond_type}: {e}")
            return False, f"Error verificando condición: {str(e)}"

    async def _check_level(
        self,
        user_id: int,
        required_level: int,
        comparison: str
    ) -> Tuple[bool, str]:
        """Check if user meets level requirement."""
        user = await self.session.get(User, user_id)
        if not user:
            return False, "Usuario no encontrado"

        user_level = user.level or 1

        passes = self._compare_values(user_level, required_level, comparison)

        if passes:
            return True, ""
        else:
            return False, f"Requiere nivel {comparison} {required_level} (tienes nivel {user_level})"

    async def _check_vip_status(self, user_id: int, required_vip: bool) -> Tuple[bool, str]:
        """Check if user's VIP status matches requirement."""
        from services.subscription_service import SubscriptionService
        sub_service = SubscriptionService(self.session)
        is_vip = await sub_service.is_user_vip(user_id)

        if is_vip == required_vip:
            return True, ""
        elif required_vip:
            return False, "Requiere suscripción VIP"
        else:
            return False, "Solo para usuarios Free"

    async def _check_owns_item(self, user_id: int, item_identifier: Any) -> Tuple[bool, str]:
        """Check if user owns a specific shop item."""
        # item_identifier can be item_id (int) or item_name (str)

        if isinstance(item_identifier, int):
            # Check by ID
            stmt = select(UserPurchase).where(
                UserPurchase.user_id == user_id,
                UserPurchase.shop_item_id == item_identifier
            )
        else:
            # Check by name
            stmt = select(UserPurchase).join(ShopItem).where(
                UserPurchase.user_id == user_id,
                ShopItem.name == str(item_identifier)
            )

        result = await self.session.execute(stmt)
        purchase = result.scalar_one_or_none()

        if purchase:
            return True, ""
        else:
            # Get item name for better message
            if isinstance(item_identifier, int):
                item = await self.session.get(ShopItem, item_identifier)
                item_name = item.name if item else f"Item #{item_identifier}"
            else:
                item_name = str(item_identifier)

            return False, f"Requiere tener: {item_name}"

    async def _check_points(
        self,
        user_id: int,
        required_points: float,
        comparison: str
    ) -> Tuple[bool, str]:
        """Check if user meets points requirement."""
        user = await self.session.get(User, user_id)
        if not user:
            return False, "Usuario no encontrado"

        user_points = user.points or 0

        passes = self._compare_values(user_points, required_points, comparison)

        if passes:
            return True, ""
        else:
            return False, f"Requiere {required_points} besitos {comparison} (tienes {user_points:.0f})"

    async def _check_owns_lore_piece(
        self,
        user_id: int,
        lore_code: str
    ) -> Tuple[bool, str]:
        """Check if user has unlocked a specific lore piece."""
        from database.models import LorePiece

        # Get lore piece by code
        lore_stmt = select(LorePiece).where(LorePiece.code_name == lore_code)
        lore_result = await self.session.execute(lore_stmt)
        lore_piece = lore_result.scalar_one_or_none()

        if not lore_piece:
            return False, f"Pista narrativa '{lore_code}' no encontrada"

        # Check if user has it
        unlock_stmt = select(UserLorePiece).where(
            UserLorePiece.user_id == user_id,
            UserLorePiece.lore_piece_id == lore_piece.id
        )
        unlock_result = await self.session.execute(unlock_stmt)
        has_lore = unlock_result.scalar_one_or_none() is not None

        if has_lore:
            return True, ""
        else:
            return False, f"Requiere desbloquear: {lore_piece.title}"

    async def _check_completed_mission(
        self,
        user_id: int,
        mission_id: str
    ) -> Tuple[bool, str]:
        """Check if user has completed a specific mission."""
        stmt = select(UserMissionEntry).where(
            UserMissionEntry.user_id == user_id,
            UserMissionEntry.mission_id == mission_id,
            UserMissionEntry.completed == True
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry:
            return True, ""
        else:
            # Get mission name for better message
            mission = await self.session.get(Mission, mission_id)
            mission_name = mission.name if mission else mission_id
            return False, f"Requiere completar misión: {mission_name}"

    def _compare_values(self, actual: float, required: float, comparison: str) -> bool:
        """Compare two values using the specified operator."""
        if comparison == ComparisonOperator.GREATER_EQUAL:
            return actual >= required
        elif comparison == ComparisonOperator.GREATER:
            return actual > required
        elif comparison == ComparisonOperator.EQUAL:
            return actual == required
        elif comparison == ComparisonOperator.LESS_EQUAL:
            return actual <= required
        elif comparison == ComparisonOperator.LESS:
            return actual < required
        else:
            logger.error(f"Unknown comparison operator: {comparison}")
            return False

    async def get_requirements_summary(
        self,
        requirements: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate a human-readable summary of requirements.

        Returns:
            String describing all requirements
        """
        if not requirements:
            return "Sin requisitos especiales"

        operator = requirements.get("operator", "AND")
        conditions = requirements.get("conditions", [])

        if not conditions:
            return "Sin requisitos especiales"

        summaries = []
        for condition in conditions:
            summary = await self._get_condition_summary(condition)
            summaries.append(summary)

        operator_text = " Y " if operator == "AND" else " O "
        return operator_text.join(summaries)

    async def _get_condition_summary(self, condition: Dict[str, Any]) -> str:
        """Get human-readable summary of a single condition."""
        cond_type = condition.get("type")
        value = condition.get("value")
        comparison = condition.get("comparison", ">=")

        if cond_type == "level":
            return f"Nivel {comparison} {value}"
        elif cond_type == "vip_status":
            return "Ser VIP" if value else "Ser usuario Free"
        elif cond_type == "owns_item":
            if isinstance(value, int):
                item = await self.session.get(ShopItem, value)
                item_name = item.name if item else f"Item #{value}"
            else:
                item_name = str(value)
            return f"Tener: {item_name}"
        elif cond_type == "points":
            return f"{value} besitos {comparison}"
        elif cond_type == "owns_lore_piece":
            from database.models import LorePiece
            lore_stmt = select(LorePiece).where(LorePiece.code_name == value)
            lore_result = await self.session.execute(lore_stmt)
            lore = lore_result.scalar_one_or_none()
            lore_name = lore.title if lore else value
            return f"Desbloquear: {lore_name}"
        elif cond_type == "completed_mission":
            mission = await self.session.get(Mission, value)
            mission_name = mission.name if mission else value
            return f"Completar: {mission_name}"
        else:
            return f"Condición: {cond_type}"
