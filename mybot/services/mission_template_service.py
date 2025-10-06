"""
Servicio de templates de misiones

Proporciona templates predefinidos para crear misiones comunes sin configuración manual.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from services.mission_service import MissionService

logger = logging.getLogger(__name__)


class MissionTemplateService:
    """Servicio para crear misiones desde templates predefinidos"""

    TEMPLATES = {
        "narrative_simple": {
            "name": "Misión Narrativa Simple",
            "description": "Una misión que avanza la historia",
            "config": {
                "type": "one_time",
                "mission_category": "narrative",
                "requires_action": False,
                "difficulty_level": 1,
                "icon_emoji": "📖",
            },
        },
        "reaction_collector": {
            "name": "Colector de Reacciones",
            "description": "Reaccionar X veces con emoji específico",
            "config": {
                "type": "weekly",
                "mission_category": "social",
                "requires_action": True,
                "difficulty_level": 2,
                "icon_emoji": "💕",
                "action_data": {"action_type": "reaction_count", "required_emoji": "❤️"},
            },
        },
        "ranking_challenge": {
            "name": "Desafío de Ranking",
            "description": "Estar en el top X de una métrica",
            "config": {
                "type": "weekly",
                "mission_category": "competitive",
                "requires_action": True,
                "difficulty_level": 4,
                "icon_emoji": "🏆",
                "action_data": {
                    "action_type": "ranking",
                    "ranking_metric": "weekly_reactions",
                },
            },
        },
        "speed_mission": {
            "name": "Misión Contra Reloj",
            "description": "Completar en tiempo límite",
            "config": {
                "type": "one_time",
                "mission_category": "timed",
                "requires_action": True,
                "difficulty_level": 3,
                "icon_emoji": "⏰",
                "time_limit_minutes": 5,
                "action_data": {"action_type": "timed"},
            },
        },
        "daily_login": {
            "name": "Inicio de Sesión Diario",
            "description": "Conectarse X días consecutivos",
            "config": {
                "type": "daily",
                "mission_category": "social",
                "requires_action": True,
                "difficulty_level": 1,
                "icon_emoji": "📅",
                "repeatable": True,
                "reset_period": "daily",
                "action_data": {"action_type": "login_streak"},
            },
        },
        "secret_mission": {
            "name": "Misión Secreta",
            "description": "Misión oculta que se descubre con una acción específica",
            "config": {
                "type": "one_time",
                "mission_category": "secret",
                "requires_action": True,
                "is_hidden": True,
                "difficulty_level": 5,
                "icon_emoji": "🔮",
                "action_data": {
                    "discovery_trigger": "reaction_with_specific_emoji",
                    "required_emoji": "🔮",
                },
            },
        },
        "chain_mission": {
            "name": "Misión en Cadena",
            "description": "Misión que desbloquea otra al completarse",
            "config": {
                "type": "one_time",
                "mission_category": "narrative",
                "requires_action": False,
                "difficulty_level": 2,
                "icon_emoji": "🔗",
            },
        },
        "limited_mission": {
            "name": "Misión Limitada",
            "description": "Solo X usuarios pueden completarla (escasez)",
            "config": {
                "type": "one_time",
                "mission_category": "competitive",
                "requires_action": False,
                "difficulty_level": 3,
                "icon_emoji": "⚡",
                "max_completions_global": 100,
            },
        },
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mission_service = MissionService(session)

    async def create_from_template(
        self, template_name: str, custom_values: dict
    ) -> "Mission":
        """
        Crea una misión desde un template predefinido.

        Args:
            template_name: Nombre del template
            custom_values: Valores personalizados que sobrescriben el template
                {
                    "name": "Mi Misión",
                    "description": "Descripción personalizada",
                    "reward_points": 200,
                    "target_value": 5,
                    ...
                }

        Returns:
            Mission creada
        """
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Template '{template_name}' no existe")

        template = self.TEMPLATES[template_name]
        config = template["config"].copy()

        # Merge con valores personalizados
        merged_config = {**config, **custom_values}

        # Crear la misión usando el servicio
        mission = await self.mission_service.create_mission(
            name=merged_config.get("name", template["name"]),
            description=merged_config.get("description", template["description"]),
            mission_type=merged_config.get("type", "one_time"),
            target_value=merged_config.get("target_value", 1),
            reward_points=merged_config.get("reward_points", 100),
            duration_days=merged_config.get("duration_days", 0),
            requires_action=merged_config.get("requires_action", False),
            action_data=merged_config.get("action_data"),
        )

        # Actualizar campos avanzados
        mission.mission_category = merged_config.get("mission_category")
        mission.is_hidden = merged_config.get("is_hidden", False)
        mission.icon_emoji = merged_config.get("icon_emoji")
        mission.difficulty_level = merged_config.get("difficulty_level", 1)
        mission.tags = merged_config.get("tags", [])
        mission.prerequisite_mission_id = merged_config.get("prerequisite_mission_id")
        mission.unlocks_mission_id = merged_config.get("unlocks_mission_id")
        mission.time_limit_minutes = merged_config.get("time_limit_minutes")
        mission.bonus_points_if_fast = merged_config.get("bonus_points_if_fast")
        mission.min_ranking_position = merged_config.get("min_ranking_position")
        mission.max_completions_global = merged_config.get("max_completions_global")
        mission.repeatable = merged_config.get("repeatable", False)
        mission.reset_period = merged_config.get("reset_period")
        mission.xp_reward = merged_config.get("xp_reward", 0)
        mission.unlocks_lore_piece_code = merged_config.get("unlocks_lore_piece_code")

        await self.session.commit()
        await self.session.refresh(mission)

        logger.info(
            f"Misión creada desde template '{template_name}': {mission.id}"
        )
        return mission

    def list_templates(self) -> list[dict]:
        """Lista todos los templates disponibles"""
        return [
            {
                "id": template_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "category": template_data["config"].get("mission_category", "general"),
                "difficulty": template_data["config"].get("difficulty_level", 1),
                "icon": template_data["config"].get("icon_emoji", "📌"),
            }
            for template_id, template_data in self.TEMPLATES.items()
        ]

    def get_template(self, template_name: str) -> dict:
        """Obtiene un template específico"""
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Template '{template_name}' no existe")
        return self.TEMPLATES[template_name]
