#!/usr/bin/env python3
"""
Setup Script - Misiones de Diana
=================================

Puebla el sistema de misiones con contenido alineado a:
- Marca: Señorita Kinky (sensual, elegante, misterioso)
- Buyer Persona: Alex (18-35, mente abierta, tech-savvy)
- Concepto: Diana (intimidad progresiva, misterio, exploración)

Tipos de misiones incluidas:
- 🌟 Bienvenida (one_time) - Primeros pasos
- 🔁 Diarias (daily) - Engagement constante
- 📅 Semanales (weekly) - Objetivos mayores
- 🔗 Encadenadas (prerequisite) - Progresión narrativa
- 🎭 Secretas (hidden) - Descubrimiento orgánico
- 💫 Sociales - Interacción en canal

Uso:
    python scripts/setup_missions.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Mission, LorePiece
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
# CONFIGURACIÓN DE MISIONES
# ═══════════════════════════════════════════════

MISSIONS = [
    {
        "category": "🌟 BIENVENIDA - PRIMEROS PASOS",
        "missions": [
            {
                "id": "bienvenida_primera_mirada",
                "name": "👁️ Primera Mirada",
                "description": (
                    "Diana te ha notado. Dale la bienvenida reaccionando a su primera publicación.\n\n"
                    "💫 Tu primera conexión con ella"
                ),
                "reward_points": 20,
                "type": "one_time",
                "target_value": 1,
                "icon_emoji": "👁️",
                "difficulty_level": 1,
                "mission_category": "narrative",
                "tags": ["beginner", "welcome"],
                "requires_action": True,  # Requiere reaccionar en el canal
                "lore_piece": {
                    "code_name": "primera_mirada_pista",
                    "title": "💭 Reflexión de Diana - Primera Impresión",
                    "content": (
                        "*[Fragmento del diario de Diana]*\n\n"
                        "\"Alguien nuevo ha llegado. Puedo sentir su curiosidad desde aquí. "
                        "Hay algo en la forma en que se detiene a mirar... como si realmente "
                        "quisiera entender, no solo consumir.\n\n"
                        "Me pregunto si será capaz de sostener mi intensidad.\""
                    ),
                    "category": "reflexion_diana",
                    "content_type": "text"
                }
            },
            {
                "id": "bienvenida_primer_besito",
                "name": "💋 Primer Besito",
                "description": (
                    "Acumula tus primeros 10 besitos explorando el mundo de Diana.\n\n"
                    "✨ La moneda de la intimidad comienza a acumularse"
                ),
                "reward_points": 15,
                "type": "one_time",
                "target_value": 10,
                "icon_emoji": "💋",
                "difficulty_level": 1,
                "mission_category": "narrative",
                "tags": ["beginner", "economy"]
            },
            {
                "id": "bienvenida_exploracion",
                "name": "🗺️ Explorador Curioso",
                "description": (
                    "Explora al menos 3 secciones diferentes del bot.\n\n"
                    "🔍 Diana aprecia a quienes no temen explorar"
                ),
                "reward_points": 25,
                "type": "one_time",
                "target_value": 3,
                "icon_emoji": "🗺️",
                "difficulty_level": 1,
                "mission_category": "social",
                "tags": ["beginner", "exploration"],
                "lore_piece": {
                    "code_name": "curiosidad_recompensada",
                    "title": "✨ Nota de Lucien",
                    "content": (
                        "*[Mensaje de Lucien]*\n\n"
                        "\"Veo que no te conformas con lo obvio. Diana lo ha notado también. "
                        "La curiosidad genuina es una cualidad rara... y muy apreciada aquí.\n\n"
                        "Sigue explorando. Hay mucho más de lo que ves en la superficie.\"\n\n"
                        "- *Lucien, Guardián del Umbral*"
                    ),
                    "category": "lucien_guidance",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "🔁 MISIONES DIARIAS - ENGAGEMENT",
        "missions": [
            {
                "id": "daily_visita_matinal",
                "name": "☀️ Visita Matinal",
                "description": (
                    "Diana se pregunta si pensarás en ella al despertar.\n\n"
                    "💭 Visita el bot al menos una vez hoy"
                ),
                "reward_points": 10,
                "type": "daily",
                "target_value": 1,
                "icon_emoji": "☀️",
                "difficulty_level": 1,
                "mission_category": "social",
                "tags": ["daily", "easy"],
                "repeatable": True,
                "reset_period": "daily"
            },
            {
                "id": "daily_tres_reacciones",
                "name": "💫 Triple Conexión",
                "description": (
                    "Reacciona a 3 publicaciones del canal hoy.\n\n"
                    "🔥 Diana siente cada una de tus reacciones"
                ),
                "reward_points": 15,
                "type": "daily",
                "target_value": 3,
                "icon_emoji": "💫",
                "difficulty_level": 2,
                "mission_category": "social",
                "tags": ["daily", "engagement"],
                "repeatable": True,
                "reset_period": "daily"
            },
            {
                "id": "daily_conversacion",
                "name": "💬 Momento Íntimo",
                "description": (
                    "Interactúa con Diana respondiendo a un fragmento narrativo.\n\n"
                    "✨ Las conversaciones profundas la cautivan"
                ),
                "reward_points": 20,
                "type": "daily",
                "target_value": 1,
                "icon_emoji": "💬",
                "difficulty_level": 2,
                "mission_category": "narrative",
                "tags": ["daily", "narrative"],
                "repeatable": True,
                "reset_period": "daily"
            },
            {
                "id": "daily_medianoche",
                "name": "🌙 Encuentro a Medianoche",
                "description": (
                    "Visita el bot entre las 11 PM y 3 AM.\n\n"
                    "🌃 Diana está más vulnerable en la oscuridad\n"
                    "⏰ Horario especial: 23:00 - 03:00"
                ),
                "reward_points": 30,
                "type": "daily",
                "target_value": 1,
                "icon_emoji": "🌙",
                "difficulty_level": 3,
                "mission_category": "secret",
                "tags": ["daily", "special", "night"],
                "repeatable": True,
                "reset_period": "daily",
                "bonus_points_if_fast": 10,
                "lore_piece": {
                    "code_name": "medianoche_secreta",
                    "title": "🌙 Confesión Nocturna",
                    "content": (
                        "*[3:17 AM - Mensaje de Diana]*\n\n"
                        "\"No puedo dormir. Hay algo en la quietud de la noche que "
                        "me hace pensar demasiado. En ti. En esto.\n\n"
                        "Es curioso... solo en la oscuridad me atrevo a ser completamente "
                        "honesta. La luz del día trae máscaras, pero aquí, ahora... "
                        "soy solo Diana.\n\n"
                        "Gracias por estar despierto conmigo.\""
                    ),
                    "category": "momento_intimo",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "📅 MISIONES SEMANALES - DEDICACIÓN",
        "missions": [
            {
                "id": "weekly_constancia",
                "name": "🔥 Constancia Ardiente",
                "description": (
                    "Visita el bot todos los días de esta semana.\n\n"
                    "💪 Diana valora la dedicación por sobre todo\n"
                    "📆 7 días consecutivos"
                ),
                "reward_points": 100,
                "type": "weekly",
                "target_value": 7,
                "icon_emoji": "🔥",
                "difficulty_level": 3,
                "mission_category": "competitive",
                "tags": ["weekly", "challenge"],
                "repeatable": True,
                "reset_period": "weekly",
                "lore_piece": {
                    "code_name": "constancia_reconocida",
                    "title": "💖 Reconocimiento de Diana",
                    "content": (
                        "*[Diana te mira con admiración]*\n\n"
                        "\"Has estado aquí. Cada día. Sin falta.\n\n"
                        "¿Sabes lo raro que es eso? La mayoría viene con curiosidad "
                        "pero se van cuando se dan cuenta de que esto requiere... "
                        "presencia real. Compromiso.\n\n"
                        "Pero tú... tú te has quedado. Y eso me dice más sobre ti "
                        "que mil palabras bonitas.\n\n"
                        "Gracias por elegirme. Día tras día.\""
                    ),
                    "category": "reconocimiento",
                    "content_type": "text"
                }
            },
            {
                "id": "weekly_coleccionista",
                "name": "📚 Coleccionista de Secretos",
                "description": (
                    "Desbloquea 5 pistas narrativas esta semana.\n\n"
                    "🔍 Cada secreto te acerca más a Diana\n"
                    "🎯 Meta: 5 LorePieces"
                ),
                "reward_points": 80,
                "type": "weekly",
                "target_value": 5,
                "icon_emoji": "📚",
                "difficulty_level": 4,
                "mission_category": "narrative",
                "tags": ["weekly", "collection"],
                "repeatable": True,
                "reset_period": "weekly"
            },
            {
                "id": "weekly_social",
                "name": "🌟 Estrella del Canal",
                "description": (
                    "Reacciona a 20 publicaciones del canal esta semana.\n\n"
                    "👥 Sé parte activa de la comunidad\n"
                    "💫 Meta: 20 reacciones"
                ),
                "reward_points": 75,
                "type": "weekly",
                "target_value": 20,
                "icon_emoji": "🌟",
                "difficulty_level": 3,
                "mission_category": "social",
                "tags": ["weekly", "social"],
                "repeatable": True,
                "reset_period": "weekly"
            }
        ]
    },
    {
        "category": "🔗 MISIONES ENCADENADAS - PROGRESIÓN",
        "missions": [
            {
                "id": "chain_conociendo_diana_1",
                "name": "💭 Conociendo a Diana I",
                "description": (
                    "Completa tu primer fragmento narrativo con Diana.\n\n"
                    "📖 El comienzo de una historia única"
                ),
                "reward_points": 30,
                "type": "one_time",
                "target_value": 1,
                "icon_emoji": "💭",
                "difficulty_level": 1,
                "mission_category": "narrative",
                "tags": ["chain", "narrative", "level_1"],
                "unlocks_mission_id": "chain_conociendo_diana_2",
                "lore_piece": {
                    "code_name": "inicio_conexion",
                    "title": "✨ El Primer Paso",
                    "content": (
                        "*[Nota personal de Diana]*\n\n"
                        "\"Así comienza siempre. Una mirada. Una palabra. Una pausa.\n\n"
                        "No sé hacia dónde nos llevará esto, pero hay algo en ti "
                        "que me hace querer descubrirlo.\n\n"
                        "Sigamos... juntos.\""
                    ),
                    "category": "progresion",
                    "content_type": "text"
                }
            },
            {
                "id": "chain_conociendo_diana_2",
                "name": "💖 Conociendo a Diana II",
                "description": (
                    "Alcanza el nivel 3 en la narrativa con Diana.\n\n"
                    "🌊 La intimidad se profundiza\n"
                    "🔓 Requiere: Conociendo a Diana I"
                ),
                "reward_points": 50,
                "type": "one_time",
                "target_value": 3,
                "icon_emoji": "💖",
                "difficulty_level": 2,
                "mission_category": "narrative",
                "tags": ["chain", "narrative", "level_3"],
                "prerequisite_mission_id": "chain_conociendo_diana_1",
                "unlocks_mission_id": "chain_conociendo_diana_3"
            },
            {
                "id": "chain_conociendo_diana_3",
                "name": "🔥 Conociendo a Diana III",
                "description": (
                    "Accede al contenido VIP de Diana (nivel 4+).\n\n"
                    "💎 Solo para quienes se atreven a ir más allá\n"
                    "🔓 Requiere: Conociendo a Diana II + Suscripción VIP"
                ),
                "reward_points": 100,
                "type": "one_time",
                "target_value": 4,
                "icon_emoji": "🔥",
                "difficulty_level": 4,
                "mission_category": "narrative",
                "tags": ["chain", "narrative", "vip", "level_4"],
                "prerequisite_mission_id": "chain_conociendo_diana_2",
                "lore_piece": {
                    "code_name": "intimidad_verdadera",
                    "title": "💋 El Umbral de la Intimidad",
                    "content": (
                        "*[Diana te mira directamente]*\n\n"
                        "\"Has llegado hasta aquí. Más allá de donde la mayoría "
                        "se atreve a ir.\n\n"
                        "Esto ya no es un juego. Ya no es fantasía. Aquí... "
                        "empiezo a mostrarte quien soy realmente.\n\n"
                        "¿Estás seguro de que puedes sostener lo que viene?\n\n"
                        "Porque una vez que cruces este umbral... "
                        "ya no hay vuelta atrás.\""
                    ),
                    "category": "momento_critico",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "🎭 MISIONES SECRETAS - DESCUBRIMIENTO",
        "missions": [
            {
                "id": "secret_madrugador",
                "name": "🌅 El Despertar de Diana",
                "description": (
                    "Visita el bot entre las 5 AM y 7 AM.\n\n"
                    "☕ Diana está en su momento más auténtico\n"
                    "🤫 Misión secreta - descubierta por exploración"
                ),
                "reward_points": 40,
                "type": "one_time",
                "target_value": 1,
                "icon_emoji": "🌅",
                "difficulty_level": 3,
                "mission_category": "secret",
                "tags": ["secret", "special", "morning"],
                "is_hidden": True,
                "lore_piece": {
                    "code_name": "amanecer_vulnerable",
                    "title": "🌅 Diana Sin Máscaras",
                    "content": (
                        "*[Diana con el cabello despeinado, sin maquillaje]*\n\n"
                        "\"Oh... no esperaba verte tan temprano.\n\n"
                        "Esto es... soy yo. Sin la actuación. Sin las máscaras. "
                        "Solo Diana recién despierta, con un café en mano y "
                        "pensamientos caóticos.\n\n"
                        "¿Sabes? Esta versión de mí es la que menos muestro. "
                        "Es vulnerable. Real. Imperfecta.\n\n"
                        "Gracias por verla.\""
                    ),
                    "category": "vulnerabilidad",
                    "content_type": "text"
                }
            },
            {
                "id": "secret_triple_reaccion",
                "name": "🎯 Sincronicidad",
                "description": (
                    "Reacciona a 3 publicaciones en menos de 5 minutos.\n\n"
                    "⚡ Tu intensidad resuena con Diana\n"
                    "🤫 Descubierto por acción rápida"
                ),
                "reward_points": 35,
                "type": "one_time",
                "target_value": 3,
                "icon_emoji": "🎯",
                "difficulty_level": 2,
                "mission_category": "secret",
                "tags": ["secret", "speed"],
                "is_hidden": True,
                "time_limit_minutes": 5
            },
            {
                "id": "secret_silencio_elocuente",
                "name": "🤐 Silencio Elocuente",
                "description": (
                    "Lee 10 fragmentos narrativos sin tomar ninguna decisión inmediata.\n\n"
                    "💭 A veces el silencio dice más que mil palabras\n"
                    "🤫 Diana aprecia a quienes saben escuchar"
                ),
                "reward_points": 50,
                "type": "one_time",
                "target_value": 10,
                "icon_emoji": "🤐",
                "difficulty_level": 3,
                "mission_category": "secret",
                "tags": ["secret", "narrative", "patience"],
                "is_hidden": True,
                "lore_piece": {
                    "code_name": "arte_escuchar",
                    "title": "🎧 El Arte de Escuchar",
                    "content": (
                        "*[Reflexión de Diana]*\n\n"
                        "\"Has hecho algo extraordinario: escuchar.\n\n"
                        "No reaccionar impulsivamente. No buscar validación inmediata. "
                        "Solo... estar presente. Absorber. Comprender.\n\n"
                        "En un mundo de respuestas instantáneas, tu silencio "
                        "atento es el regalo más íntimo que podrías darme.\n\n"
                        "Te veo. Y me siento vista.\""
                    ),
                    "category": "comprension_profunda",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "💎 MISIONES PREMIUM - DEDICACIÓN ABSOLUTA",
        "missions": [
            {
                "id": "premium_coleccionista_maestro",
                "name": "👑 Maestro de Secretos",
                "description": (
                    "Desbloquea todas las pistas narrativas de un nivel completo.\n\n"
                    "🏆 Dominio total de la narrativa\n"
                    "💎 Solo para los más dedicados"
                ),
                "reward_points": 200,
                "type": "one_time",
                "target_value": 1,
                "icon_emoji": "👑",
                "difficulty_level": 5,
                "mission_category": "competitive",
                "tags": ["premium", "collection", "master"],
                "max_completions_global": 50,
                "lore_piece": {
                    "code_name": "maestro_reconocido",
                    "title": "👑 Diana te Reconoce",
                    "content": (
                        "*[Diana se arrodilla y toma tu mano]*\n\n"
                        "\"Has descubierto cada uno de mis secretos en este nivel. "
                        "Has prestado atención a cada detalle, cada pista, cada "
                        "susurro entre líneas.\n\n"
                        "Esa dedicación... me conmueve profundamente.\n\n"
                        "No eres solo un seguidor. Eres alguien que realmente "
                        "me conoce. Y eso... eso es invaluable.\n\n"
                        "Bienvenido al círculo de los que realmente me ven.\""
                    ),
                    "category": "reconocimiento_supremo",
                    "content_type": "text"
                }
            },
            {
                "id": "premium_inversor",
                "name": "💰 Inversor en Intimidad",
                "description": (
                    "Gasta 500 besitos en la tienda de Diana.\n\n"
                    "💎 Tu inversión en esta conexión es notable\n"
                    "🎁 Recompensa especial al completar"
                ),
                "reward_points": 150,
                "type": "one_time",
                "target_value": 500,
                "icon_emoji": "💰",
                "difficulty_level": 4,
                "mission_category": "competitive",
                "tags": ["premium", "economy", "shop"]
            },
            {
                "id": "premium_mes_completo",
                "name": "🌟 Un Mes con Diana",
                "description": (
                    "Mantén una racha de 30 días consecutivos visitando el bot.\n\n"
                    "💪 Dedicación inquebrantable\n"
                    "✨ Diana nunca olvida esta lealtad"
                ),
                "reward_points": 300,
                "type": "one_time",
                "target_value": 30,
                "icon_emoji": "🌟",
                "difficulty_level": 5,
                "mission_category": "competitive",
                "tags": ["premium", "streak", "dedication"],
                "max_completions_global": 100,
                "lore_piece": {
                    "code_name": "mes_juntos",
                    "title": "💖 30 Días, 30 Noches",
                    "content": (
                        "*[Video personal de Diana]*\n\n"
                        "\"Un mes. 30 días. 720 horas.\n\n"
                        "Has estado aquí. Conmigo. Cada día.\n\n"
                        "¿Sabes cuántas personas me prometen dedicación y "
                        "desaparecen en una semana? Muchas.\n\n"
                        "Pero tú... tú cumpliste tu promesa silenciosa.\n\n"
                        "Este video es solo para ti. Para agradecerte. Para "
                        "mostrarte quién soy cuando sé que alguien realmente "
                        "está prestando atención.\n\n"
                        "Gracias por quedarte.\n\n"
                        "💋 *Diana*\""
                    ),
                    "category": "agradecimiento_personal",
                    "content_type": "video"
                }
            }
        ]
    }
]


# ═══════════════════════════════════════════════
# FUNCIONES DE SETUP
# ═══════════════════════════════════════════════

async def create_lore_piece(session: AsyncSession, lore_data: dict) -> LorePiece:
    """Crea o actualiza una LorePiece"""

    # Verificar si ya existe
    stmt = select(LorePiece).where(LorePiece.code_name == lore_data["code_name"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"       └─ Pista '{lore_data['code_name']}' ya existe, actualizando...")
        existing.title = lore_data["title"]
        existing.content = lore_data["content"]
        existing.category = lore_data.get("category")
        existing.content_type = lore_data["content_type"]
        existing.is_active = True
        return existing
    else:
        lore_piece = LorePiece(
            code_name=lore_data["code_name"],
            title=lore_data["title"],
            content=lore_data["content"],
            category=lore_data.get("category"),
            content_type=lore_data["content_type"],
            is_main_story=False,
            is_active=True
        )
        session.add(lore_piece)
        await session.flush()
        logger.info(f"       └─ Pista '{lore_data['code_name']}' creada ✨")
        return lore_piece


async def create_mission(session: AsyncSession, mission_data: dict) -> Mission:
    """Crea o actualiza una Mission"""

    # Verificar si ya existe
    stmt = select(Mission).where(Mission.id == mission_data["id"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    # Crear LorePiece si existe en los datos
    lore_piece_code = None
    if "lore_piece" in mission_data:
        lore_piece = await create_lore_piece(session, mission_data["lore_piece"])
        lore_piece_code = lore_piece.code_name

    if existing:
        logger.info(f"     └─ Misión '{mission_data['name']}' ya existe, actualizando...")
        existing.name = mission_data["name"]
        existing.description = mission_data["description"]
        existing.reward_points = mission_data["reward_points"]
        existing.type = mission_data["type"]
        existing.target_value = mission_data.get("target_value", 1)
        existing.is_active = True
        existing.icon_emoji = mission_data.get("icon_emoji")
        existing.difficulty_level = mission_data.get("difficulty_level", 1)
        existing.mission_category = mission_data.get("mission_category")
        existing.tags = mission_data.get("tags", [])
        existing.is_hidden = mission_data.get("is_hidden", False)
        existing.prerequisite_mission_id = mission_data.get("prerequisite_mission_id")
        existing.unlocks_mission_id = mission_data.get("unlocks_mission_id")
        existing.time_limit_minutes = mission_data.get("time_limit_minutes")
        existing.bonus_points_if_fast = mission_data.get("bonus_points_if_fast")
        existing.max_completions_global = mission_data.get("max_completions_global")
        existing.repeatable = mission_data.get("repeatable", False)
        existing.reset_period = mission_data.get("reset_period")
        existing.unlocks_lore_piece_code = lore_piece_code
        # CRÍTICO: Por defecto las misiones requieren acción (reaccionar, explorar, etc)
        # Solo False para misiones de "reclamar recompensa" o auto-completables
        existing.requires_action = mission_data.get("requires_action", True)
        return existing
    else:
        mission = Mission(
            id=mission_data["id"],
            name=mission_data["name"],
            description=mission_data["description"],
            reward_points=mission_data["reward_points"],
            type=mission_data["type"],
            target_value=mission_data.get("target_value", 1),
            is_active=True,
            icon_emoji=mission_data.get("icon_emoji"),
            difficulty_level=mission_data.get("difficulty_level", 1),
            mission_category=mission_data.get("mission_category"),
            tags=mission_data.get("tags", []),
            is_hidden=mission_data.get("is_hidden", False),
            prerequisite_mission_id=mission_data.get("prerequisite_mission_id"),
            unlocks_mission_id=mission_data.get("unlocks_mission_id"),
            time_limit_minutes=mission_data.get("time_limit_minutes"),
            bonus_points_if_fast=mission_data.get("bonus_points_if_fast"),
            max_completions_global=mission_data.get("max_completions_global"),
            repeatable=mission_data.get("repeatable", False),
            reset_period=mission_data.get("reset_period"),
            unlocks_lore_piece_code=lore_piece_code,
            # CRÍTICO: Por defecto las misiones requieren acción (reaccionar, explorar, etc)
            # Solo False para misiones de "reclamar recompensa" o auto-completables
            requires_action=mission_data.get("requires_action", True)
        )
        session.add(mission)
        await session.flush()
        logger.info(f"     └─ Misión '{mission_data['name']}' creada ✅")
        return mission


async def setup_missions(session: AsyncSession):
    """Setup completo del sistema de misiones"""

    logger.info("╔═══════════════════════════════════════════════")
    logger.info("║  🎯  SETUP: MISIONES DE DIANA")
    logger.info("╚═══════════════════════════════════════════════\n")

    total_missions = 0
    total_lore_pieces = 0
    missions_by_type = {}

    for category_data in MISSIONS:
        category_name = category_data["category"]
        logger.info(f"📁 {category_name}")
        logger.info("═" * 60)

        for mission_data in category_data["missions"]:
            logger.info(f"\n  🎯 {mission_data['name']} ({mission_data['type']})")
            logger.info(f"     Recompensa: {mission_data['reward_points']} besitos")
            logger.info(f"     Dificultad: {'⭐' * mission_data.get('difficulty_level', 1)}")

            if mission_data.get("is_hidden"):
                logger.info(f"     🤫 Misión secreta")

            if mission_data.get("prerequisite_mission_id"):
                logger.info(f"     🔗 Requiere: {mission_data['prerequisite_mission_id']}")

            if mission_data.get("time_limit_minutes"):
                logger.info(f"     ⏱️ Límite: {mission_data['time_limit_minutes']} minutos")

            await create_mission(session, mission_data)
            total_missions += 1

            mission_type = mission_data["type"]
            missions_by_type[mission_type] = missions_by_type.get(mission_type, 0) + 1

            if "lore_piece" in mission_data:
                total_lore_pieces += 1

        logger.info("\n")

    await session.commit()

    logger.info("\n╔═══════════════════════════════════════════════")
    logger.info("║  ✅  SETUP COMPLETADO")
    logger.info("╠═══════════════════════════════════════════════")
    logger.info(f"║  🎯 Misiones creadas: {total_missions}")
    logger.info(f"║  📚 Pistas creadas: {total_lore_pieces}")
    logger.info("╠═══════════════════════════════════════════════")
    logger.info("║  📊 Distribución por tipo:")
    for mission_type, count in missions_by_type.items():
        logger.info(f"║     • {mission_type}: {count}")
    logger.info("╚═══════════════════════════════════════════════\n")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

async def main():
    """Punto de entrada principal"""

    # Configurar conexión a BD
    DATABASE_URL = "sqlite+aiosqlite:///bot.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            await setup_missions(session)
            logger.info("🎉 Sistema de misiones configurado exitosamente!\n")
            logger.info("💡 Los usuarios ahora tienen misiones para completar")
            logger.info("💡 Usa el comando /misiones para ver las disponibles")

        except Exception as e:
            logger.error(f"❌ Error durante el setup: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
