# utils/message_utils.py
from database.models import User, Mission, Reward, UserAchievement
from services.level_service import LevelService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.achievement_service import ACHIEVEMENTS
from utils.messages import BOT_MESSAGES
from utils.text_utils import anonymize_username
import datetime
import re


def escape_markdown(text: str) -> str:
    """
    Escapa caracteres especiales de Markdown para Telegram.

    En Telegram Markdown (no V2), solo ciertos caracteres necesitan escape:
    - _ (cursiva)
    - * (negrita)
    - ` (código)
    - [ y ] (enlaces)

    Otros caracteres se preservan para mantener la legibilidad del texto.
    """
    if not text:
        return text

    # Primero escapar backslash para no re-escapar los que agregamos
    text = text.replace('\\', '\\\\')

    # Solo caracteres que causan problemas reales en Markdown estándar
    # No escapamos todos los caracteres especiales porque no es necesario
    special_chars = ['_', '*', '`', '[', ']']

    for char in special_chars:
        text = text.replace(char, '\\' + char)

    return text


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caracteres especiales para MarkdownV2 de Telegram.

    Preserva el formato intencional (* para negrita, _ para cursiva)
    pero escapa otros caracteres especiales.

    Args:
        text: Texto a escapar

    Returns:
        Texto con caracteres especiales escapados pero formato preservado
    """
    if not text:
        return text

    # Caracteres que SIEMPRE deben escaparse (excepto * y _ que son formato)
    escape_chars = [
        ('\\', '\\\\'),  # Backslash primero
        ('[', '\\['),    # Enlace inicio
        (']', '\\]'),    # Enlace fin
        ('(', '\\('),    # Paréntesis
        (')', '\\)'),    # Paréntesis
        ('~', '\\~'),    # Tachado
        ('`', '\\`'),    # Código
        ('>', '\\>'),    # Quote
        ('#', '\\#'),    # Heading
        ('+', '\\+'),    # Plus
        ('-', '\\-'),    # Guión/lista
        ('=', '\\='),    # Igual
        ('|', '\\|'),    # Pipe
        ('{', '\\{'),    # Llave
        ('}', '\\}'),    # Llave
        ('.', '\\.'),    # Punto
        ('!', '\\!'),    # Exclamación
    ]

    for char, escaped in escape_chars:
        text = text.replace(char, escaped)

    return text


async def get_profile_message(
    user: User, active_missions: list[Mission], session: AsyncSession
) -> str:
    points_to_next_level_text = ""
    level_service = LevelService(session)
    next_level_threshold = await level_service.get_level_threshold(user.level + 1)
    if next_level_threshold != float("inf"):
        points_needed = next_level_threshold - user.points
        # Usar el mensaje personalizado para puntos al siguiente nivel
        points_to_next_level_text = BOT_MESSAGES["profile_points_to_next_level"].format(
            points_needed=points_needed,
            next_level=user.level + 1,
            next_level_threshold=next_level_threshold,
        )
    else:
        # Usar el mensaje personalizado para nivel máximo
        points_to_next_level_text = BOT_MESSAGES["profile_max_level"]

    # Usar el mensaje personalizado para no logros
    achievements_text = BOT_MESSAGES["profile_no_achievements"]
    stmt = select(UserAchievement).where(UserAchievement.user_id == user.id)
    result = await session.execute(stmt)
    records = result.scalars().all()
    if records:
        granted_achievements_list = []
        for rec in records:
            ach_data = ACHIEVEMENTS.get(rec.achievement_id)
            if ach_data:
                granted_achievements_list.append(
                    {
                        "id": rec.achievement_id,
                        "name": ach_data.get("name", rec.achievement_id),
                        "icon": ach_data.get("icon", ""),
                        "granted_at": rec.unlocked_at.isoformat(),
                    }
                )
        granted_achievements_list.sort(key=lambda x: x["granted_at"])

        achievements_list = [
            f"{ach['icon']} {ach['name']} (Desbloqueado el: {datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')})"
            for ach in granted_achievements_list
        ]
        achievements_text = (
            BOT_MESSAGES["profile_achievements_title"]
            + "\n"
            + "\n".join(achievements_list)
        )

    # Misión recomendada: mostrar solo UNA misión para no abrumar
    missions_text = BOT_MESSAGES["profile_no_active_missions"]
    if active_missions:
        # Seleccionar la misión con mejor prioridad:
        # 1. Misiones de bienvenida (beginner)
        # 2. Misiones diarias
        # 3. Misiones con menor dificultad
        # 4. Misiones con mayor recompensa

        recommended_mission = None

        # Prioridad 1: Misiones de bienvenida no completadas
        beginner_missions = [m for m in active_missions if "beginner" in (m.tags or [])]
        if beginner_missions:
            recommended_mission = beginner_missions[0]
        # Prioridad 2: Misiones diarias
        elif any(m.type == "daily" for m in active_missions):
            recommended_mission = [m for m in active_missions if m.type == "daily"][0]
        # Prioridad 3: Por dificultad y recompensa
        else:
            # Ordenar por dificultad (menor primero) y luego por recompensa (mayor primero)
            sorted_missions = sorted(
                active_missions,
                key=lambda m: (m.difficulty_level or 1, -(m.reward_points or 0))
            )
            recommended_mission = sorted_missions[0] if sorted_missions else None

        if recommended_mission:
            difficulty_stars = "⭐" * (recommended_mission.difficulty_level or 1)
            missions_text = (
                f"🎯 **Misión Recomendada:**\n\n"
                f"• {escape_markdown(recommended_mission.name)}\n"
                f"   {difficulty_stars} | {recommended_mission.reward_points} Besitos\n\n"
                f"💡 _Tienes {len(active_missions)} misiones disponibles en total_"
            )

    return (
        # Usar mensajes personalizados para cada parte del perfil
        f"{BOT_MESSAGES['profile_title']}\n\n"
        f"{BOT_MESSAGES['profile_points'].format(user_points=user.points)}\n"
        f"{BOT_MESSAGES['profile_level'].format(user_level=user.level)}\n"
        f"{points_to_next_level_text}\n\n"
        f"{achievements_text}\n\n"  # Incluye el título de logros
        f"{missions_text}"  # Incluye el título de misiones
    )


async def get_mission_details_message(mission: Mission) -> str:
    """
    Genera el mensaje de detalles de una misión, escapando caracteres especiales.

    Los emojis se preservan, pero caracteres como _, *, (, ), etc. se escapan
    para evitar errores de parsing de Markdown en Telegram.
    """
    # Escapar caracteres especiales de Markdown en el nombre y descripción
    safe_name = escape_markdown(mission.name)
    safe_description = escape_markdown(mission.description)
    safe_type = escape_markdown(mission.type.capitalize())

    # Usar el mensaje personalizado para detalles de misión
    return BOT_MESSAGES["mission_details_text"].format(
        mission_name=safe_name,
        mission_description=safe_description,
        points_reward=mission.reward_points,
        mission_type=safe_type,
    )


async def get_reward_details_message(reward: Reward, user_points: int) -> str:
    """Return a formatted description of a reward."""
    safe_title = escape_markdown(reward.title)
    safe_description = escape_markdown(reward.description)

    return BOT_MESSAGES["reward_details_text"].format(
        reward_title=safe_title,
        reward_description=safe_description,
        required_points=reward.required_points,
    )


async def get_ranking_message(users_ranking: list[User], viewer_user_id: int) -> str:
    """
    Generates a formatted message for the user ranking with anonymized usernames.
    """
    ranking_text = BOT_MESSAGES["ranking_title"] + "\n\n"

    if not users_ranking:
        return ranking_text + BOT_MESSAGES["no_ranking_data"]

    for i, user in enumerate(users_ranking):
        display_name = anonymize_username(user, viewer_user_id)
        # Escapar caracteres especiales de Markdown
        safe_display_name = escape_markdown(display_name)

        # Formatear puntos sin decimales innecesarios
        points_display = int(user.points) if user.points == int(user.points) else f"{user.points:.1f}"

        ranking_text += (
            BOT_MESSAGES["ranking_entry"].format(
                rank=i + 1,
                username=safe_display_name,
                points=points_display,
                level=user.level
            )
            + "\n"
        )

    return ranking_text


async def get_weekly_reaction_ranking_message(ranking: list[tuple[int, int]], session: AsyncSession, viewer_user_id: int) -> str:
    text = BOT_MESSAGES["weekly_ranking_title"] + "\n\n"
    if not ranking:
        return text + BOT_MESSAGES["no_ranking_data"]
    for idx, (user_id, count) in enumerate(ranking):
        user = await session.get(User, user_id)
        display_name = anonymize_username(user, viewer_user_id)
        text += BOT_MESSAGES["weekly_ranking_entry"].format(rank=idx + 1, username=display_name, count=count) + "\n"
    return text


async def get_mission_completed_message(mission: Mission) -> str:
    """Return a formatted message for mission completion."""
    safe_name = escape_markdown(mission.name)
    return BOT_MESSAGES["mission_completed_feedback"].format(
        mission_name=safe_name,
        points_reward=mission.reward_points,
    )
