"""
Servicio de validación de misiones

Valida si un usuario puede completar una misión basándose en:
- Requisitos (nivel, VIP, badges)
- Cooldowns
- Límites globales
- Misiones prerequisito
- Reglas en action_data
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Mission, User, UserMissionEntry

logger = logging.getLogger(__name__)


class MissionValidatorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_complete(self, user_id: int, mission_id: str) -> tuple[bool, str]:
        """
        Verifica si un usuario puede completar una misión.

        Returns:
            (can_complete: bool, reason: str)
        """
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission:
            return False, "Usuario o misión no encontrada"

        if not mission.is_active:
            return False, "La misión no está activa"

        # Validar prerequisitos de misión
        if mission.prerequisite_mission_id:
            can_proceed, reason = await self._check_prerequisite(user, mission)
            if not can_proceed:
                return False, reason

        # Validar límite global de completaciones
        if mission.max_completions_global:
            if mission.current_completions_global >= mission.max_completions_global:
                return False, "Esta misión ha alcanzado su límite de completaciones"

        # Validar si ya fue completada (para misiones no repetibles)
        if not mission.repeatable:
            is_completed, _ = await self._check_already_completed(user, mission)
            if is_completed:
                return False, "Ya completaste esta misión"

        # Validar cooldown
        if mission.repeatable and mission.reset_period:
            can_repeat, reason = await self._check_cooldown(user, mission)
            if not can_repeat:
                return False, reason

        # Validar reglas en action_data
        if mission.action_data:
            validation_rules = mission.action_data.get("validation_rules", {})
            can_proceed, reason = await self._check_validation_rules(user, validation_rules)
            if not can_proceed:
                return False, reason

        return True, "OK"

    async def _check_prerequisite(self, user: User, mission: Mission) -> tuple[bool, str]:
        """Verifica si el usuario completó la misión prerequisito"""
        prereq_id = mission.prerequisite_mission_id
        if prereq_id in user.missions_completed:
            return True, "OK"
        return False, f"Debes completar la misión prerequisito primero"

    async def _check_already_completed(self, user: User, mission: Mission) -> tuple[bool, str]:
        """Verifica si el usuario ya completó la misión"""
        if mission.id in user.missions_completed:
            return True, "already_completed"
        return False, "not_completed"

    async def _check_cooldown(self, user: User, mission: Mission) -> tuple[bool, str]:
        """Verifica el cooldown de misiones repetibles"""
        if mission.id not in user.missions_completed:
            return True, "OK"

        last_completed_str = user.missions_completed.get(mission.id)
        last_completed = datetime.fromisoformat(last_completed_str)
        now = datetime.now()

        if mission.reset_period == "daily":
            cooldown = timedelta(days=1)
        elif mission.reset_period == "weekly":
            cooldown = timedelta(weeks=1)
        elif mission.reset_period == "monthly":
            cooldown = timedelta(days=30)
        else:
            # Cooldown personalizado en action_data
            validation_rules = mission.action_data.get("validation_rules", {})
            cooldown_hours = validation_rules.get("cooldown_hours", 0)
            cooldown = timedelta(hours=cooldown_hours)

        if (now - last_completed) < cooldown:
            remaining = cooldown - (now - last_completed)
            hours = int(remaining.total_seconds() // 3600)
            return False, f"Debes esperar {hours} horas para repetir esta misión"

        return True, "OK"

    async def _check_validation_rules(self, user: User, rules: dict) -> tuple[bool, str]:
        """Valida reglas personalizadas en action_data"""
        # Validar nivel mínimo
        min_level = rules.get("min_level")
        if min_level and user.level < min_level:
            return False, f"Requiere nivel {min_level}"

        # Validar VIP
        requires_vip = rules.get("requires_vip", False)
        if requires_vip and user.role not in ["vip", "admin"]:
            return False, "Requiere suscripción VIP"

        # Validar badge específico
        requires_badge = rules.get("requires_badge")
        if requires_badge:
            user_badges = user.achievements.get("badges", [])
            if requires_badge not in user_badges:
                return False, f"Requiere el badge '{requires_badge}'"

        return True, "OK"

    async def validate_action(
        self, user_id: int, mission_id: str, action_performed: dict
    ) -> tuple[bool, str]:
        """
        Valida que una acción cumple con los requisitos de la misión.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión
            action_performed: Dict con datos de la acción realizada
                Ejemplos:
                - {"emoji": "💋", "message_id": 123}
                - {"ranking_position": 5, "metric": "weekly_reactions"}
                - {"time_taken_seconds": 120}

        Returns:
            (is_valid: bool, message: str)
        """
        mission = await self.session.get(Mission, mission_id)
        if not mission or not mission.action_data:
            return True, "OK"

        action_data = mission.action_data
        action_type = action_data.get("action_type")

        # Validar reacción con emoji específico
        if action_type == "reaction_count":
            required_emoji = action_data.get("required_emoji")
            if required_emoji and action_performed.get("emoji") != required_emoji:
                return False, f"Debes reaccionar con {required_emoji}"

        # Validar ranking
        elif action_type == "ranking":
            ranking_position = action_performed.get("ranking_position", 999)
            min_position = mission.min_ranking_position or action_data.get("ranking_position", 10)
            if ranking_position > min_position:
                return False, f"Debes estar en el top {min_position}"

        # Validar tiempo
        elif action_type == "timed":
            time_taken = action_performed.get("time_taken_seconds", 999999)
            time_limit = (mission.time_limit_minutes or 0) * 60
            if time_limit and time_taken > time_limit:
                return False, f"Se acabó el tiempo ({mission.time_limit_minutes} min)"

        return True, "OK"
