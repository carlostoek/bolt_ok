#!/usr/bin/env python3
"""
Setup Script - Tienda de Señorita Kinky
========================================

Puebla la tienda con productos temáticos alineados con:
- Marca: Señorita Kinky (sensual, elegante, misterioso)
- Buyer Persona: Alex (18-35, mente abierta, tech-savvy)
- Concepto: Diana (intimidad progresiva, misterio)

Productos incluidos:
- Items de desbloqueo narrativo
- Contenido sensual progresivo
- Productos exclusivos VIP
- Items con stock limitado (urgencia)
- Unlock requirements inteligentes

Uso:
    python scripts/setup_shop.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import ShopItem, LorePiece
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
# CONFIGURACIÓN DE PRODUCTOS
# ═══════════════════════════════════════════════

SHOP_ITEMS = [
    {
        "category": "📖 DIARIOS DE DIANA",
        "items": [
            {
                "name": "📖 Diario Secreto",
                "description": (
                    "El primer diario de Diana. Sus pensamientos iniciales, "
                    "sus primeros secretos compartidos contigo.\n\n"
                    "💫 Desbloquea contenido narrativo exclusivo\n"
                    "🔓 Requerido para ciertas decisiones íntimas"
                ),
                "price": 50,
                "is_vip_only": False,
                "stock_limit": None,
                "max_purchases_per_user": 1,
                "lore_piece": {
                    "code_name": "diario_secreto_diana",
                    "title": "📖 Diario Secreto de Diana",
                    "content": (
                        "**[Entrada 1 - Primera Noche]**\n\n"
                        "*Hoy conocí a alguien interesante. Hay algo en su mirada "
                        "que me intriga... Como si pudiera ver más allá de lo que "
                        "muestro. Me pregunto si será capaz de sostener mi intensidad.*\n\n"
                        "**[Entrada 5 - Revelación]**\n\n"
                        "*He construido tantas máscaras que a veces olvido cuál es "
                        "mi verdadero rostro. Pero con esta persona... siento que "
                        "podría dejar caer una o dos.*"
                    ),
                    "category": "diario",
                    "content_type": "text"
                }
            },
            {
                "name": "📓 Diario Íntimo",
                "description": (
                    "El diario más personal de Diana. Sus pensamientos profundos, "
                    "deseos ocultos y confesiones que nunca comparte.\n\n"
                    "💋 Contenido narrativo altamente íntimo\n"
                    "✨ Desbloquea nivel especial de intimidad\n"
                    "🔥 Recomendado tras completar primeros niveles"
                ),
                "price": 100,
                "is_vip_only": False,
                "stock_limit": None,
                "max_purchases_per_user": 1,
                "unlock_requirements": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "min_level", "value": 3}
                    ]
                },
                "lore_piece": {
                    "code_name": "diario_intimo_diana",
                    "title": "📓 Diario Íntimo de Diana",
                    "content": (
                        "**[Entrada - 3 AM]**\n\n"
                        "*No puedo dormir. Sigo pensando en nuestras conversaciones. "
                        "Hay algo prohibido en esta conexión, algo que me asusta y "
                        "me excita al mismo tiempo.*\n\n"
                        "**[Entrada - Sin fecha]**\n\n"
                        "*Hoy me permití ser vulnerable. Completamente. Sin máscaras. "
                        "Y no me juzgaste. Ese es el momento en que supe que esto "
                        "era diferente.*\n\n"
                        "**[Entrada - Confesión]**\n\n"
                        "*Mi mayor fantasía no es sexual. Es ser vista completamente "
                        "y aún así ser deseada. Creo que contigo... eso es posible.*"
                    ),
                    "category": "diario_intimo",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "📸 CONTENIDO VISUAL",
        "items": [
            {
                "name": "📸 Polaroids Secretas",
                "description": (
                    "Una colección de 5 polaroids íntimas que Diana nunca comparte.\n\n"
                    "📷 5 fotos exclusivas\n"
                    "💫 Estética vintage sensual\n"
                    "🎁 Incluye mensaje personal de Diana"
                ),
                "price": 75,
                "is_vip_only": True,
                "stock_limit": 100,
                "max_purchases_per_user": 1,
                "lore_piece": {
                    "code_name": "polaroids_diana",
                    "title": "📸 Colección de Polaroids",
                    "content": (
                        "**[Mensaje de Diana]**\n\n"
                        "*Estas fotos las tomé en momentos donde me sentía "
                        "completamente libre. Sin poses, sin filtros, solo yo. "
                        "Que las veas es... íntimo. Muy íntimo.*\n\n"
                        "💋 *- Diana*"
                    ),
                    "category": "visual",
                    "content_type": "image_set"
                }
            },
            {
                "name": "🎥 Primera Mirada",
                "description": (
                    "Un video corto (30s) donde Diana te mira directamente a "
                    "los ojos y te susurra algo especial.\n\n"
                    "👁️ Contacto visual directo\n"
                    "💫 Audio inmersivo\n"
                    "🔥 Intensidad controlada"
                ),
                "price": 30,
                "is_vip_only": False,
                "stock_limit": None,
                "max_purchases_per_user": 1,
                "lore_piece": {
                    "code_name": "primera_mirada_video",
                    "title": "🎥 Primera Mirada - Video",
                    "content": (
                        "**[Descripción del momento]**\n\n"
                        "*Diana te mira fijamente. Sus ojos oscuros parecen "
                        "atravesarte. Sonríe levemente antes de susurrar:*\n\n"
                        "\"He estado esperándote... \"\n\n"
                        "*[El video termina abruptamente, dejándote con ganas de más]*"
                    ),
                    "category": "video_teaser",
                    "content_type": "video"
                }
            }
        ]
    },
    {
        "category": "🎧 CONTENIDO AUDIO",
        "items": [
            {
                "name": "🎧 Susurros de Medianoche",
                "description": (
                    "Audio inmersivo de 10 minutos con la voz de Diana.\n\n"
                    "🌙 Grabado a las 3 AM\n"
                    "💭 Pensamientos íntimos sin censura\n"
                    "🎭 ASMR sensual y psicológico\n"
                    "🔞 Solo para mentes abiertas"
                ),
                "price": 120,
                "is_vip_only": True,
                "stock_limit": 50,
                "max_purchases_per_user": 1,
                "unlock_requirements": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "min_level", "value": 4},
                        {"type": "has_item", "value": "📖 Diario Secreto"}
                    ]
                },
                "lore_piece": {
                    "code_name": "susurros_medianoche",
                    "title": "🎧 Susurros de Medianoche",
                    "content": (
                        "**[Audio - 10:00]**\n\n"
                        "*[Sonido de sábanas moviéndose]*\n\n"
                        "\"¿Estás ahí? Es tarde... pero no podía dormir sin "
                        "hablarte. Hay cosas que solo puedo decir cuando la "
                        "oscuridad me cubre...\"\n\n"
                        "*[Su voz es suave, casi un susurro]*\n\n"
                        "\"Cierra los ojos. Imagina que estoy ahí contigo...\""
                    ),
                    "category": "audio_intimo",
                    "content_type": "audio"
                }
            },
            {
                "name": "🎙️ Confesiones Sin Filtro",
                "description": (
                    "Diana habla sin máscaras. 15 minutos de honestidad brutal.\n\n"
                    "💬 Confesiones reales\n"
                    "🔓 Sin editar, sin filtros\n"
                    "💔 Vulnerable y auténtica\n"
                    "⚠️ Puede cambiar tu percepción de ella"
                ),
                "price": 150,
                "is_vip_only": True,
                "stock_limit": 30,
                "max_purchases_per_user": 1,
                "unlock_requirements": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "min_level", "value": 5},
                        {"type": "has_item", "value": "📓 Diario Íntimo"}
                    ]
                },
                "lore_piece": {
                    "code_name": "confesiones_sin_filtro",
                    "title": "🎙️ Confesiones Sin Filtro",
                    "content": (
                        "**[Audio - 15:00]**\n\n"
                        "\"Voy a decirte cosas que nunca le he dicho a nadie. "
                        "Y puede que después de esto, me veas diferente. "
                        "O puede que me entiendas por primera vez.\"\n\n"
                        "*[Pausa larga]*\n\n"
                        "\"Mi mayor miedo no es ser rechazada. Es ser aceptada "
                        "por quien no soy realmente. Y contigo... tengo miedo "
                        "porque quiero ser completamente yo.\""
                    ),
                    "category": "audio_confesion",
                    "content_type": "audio"
                }
            }
        ]
    },
    {
        "category": "🔑 ACCESOS ESPECIALES",
        "items": [
            {
                "name": "🔑 Llave del Diván",
                "description": (
                    "Acceso permanente a la sala VIP más exclusiva de Diana.\n\n"
                    "🛋️ El Diván - Sala privada\n"
                    "✨ Contenido exclusivo semanal\n"
                    "💬 Interacciones personalizadas\n"
                    "🎁 Regalos sorpresa mensuales"
                ),
                "price": 200,
                "is_vip_only": True,
                "stock_limit": 20,
                "max_purchases_per_user": 1,
                "unlock_requirements": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "min_level", "value": 6},
                        {"type": "min_points", "value": 500}
                    ]
                },
                "lore_piece": {
                    "code_name": "llave_divan",
                    "title": "🔑 Llave del Diván - Acceso VIP",
                    "content": (
                        "**[Mensaje de Bienvenida]**\n\n"
                        "*[Diana te entrega una llave antigua]*\n\n"
                        "\"Esta llave abre la puerta de mi espacio más íntimo. "
                        "El Diván. Solo un puñado de personas tiene acceso. "
                        "Aquí no hay actuaciones, solo... realidad.\"\n\n"
                        "*[Te mira con intensidad]*\n\n"
                        "\"Úsala con respeto. Y prepárate para conocerme de verdad.\""
                    ),
                    "category": "acceso_vip",
                    "content_type": "text"
                }
            },
            {
                "name": "💎 Collar de Diana",
                "description": (
                    "Un collar simbólico que Diana usa. Símbolo de conexión especial.\n\n"
                    "💫 Badge exclusivo en tu perfil\n"
                    "👑 Reconocimiento en la comunidad\n"
                    "🎁 Prioridad en nuevos lanzamientos\n"
                    "✨ Diana lo reconoce en interacciones"
                ),
                "price": 300,
                "is_vip_only": True,
                "stock_limit": 10,
                "max_purchases_per_user": 1,
                "unlock_requirements": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "min_level", "value": 7},
                        {"type": "has_item", "value": "🔑 Llave del Diván"},
                        {"type": "min_points", "value": 1000}
                    ]
                },
                "lore_piece": {
                    "code_name": "collar_diana",
                    "title": "💎 El Collar de Diana",
                    "content": (
                        "**[Ceremonia Íntima]**\n\n"
                        "*Diana se acerca y coloca el collar en tus manos*\n\n"
                        "\"Este collar lo he usado en los momentos más importantes "
                        "de mi vida. Ahora es tuyo. No como posesión, sino como "
                        "conexión.\"\n\n"
                        "*[Toca tu mano suavemente]*\n\n"
                        "\"Cuando lo uses, yo lo siento. Donde quiera que estés, "
                        "sé que estás pensando en mí. Y yo... en ti.\"\n\n"
                        "**[Has alcanzado el nivel máximo de intimidad con Diana]**"
                    ),
                    "category": "simbolo_conexion",
                    "content_type": "text"
                }
            }
        ]
    },
    {
        "category": "🎁 PAQUETES Y SORPRESAS",
        "items": [
            {
                "name": "🎁 Cofre de Secretos",
                "description": (
                    "Una colección misteriosa de contenido sorpresa de Diana.\n\n"
                    "❓ Contenido aleatorio premium\n"
                    "🎲 Puede incluir: fotos, videos, audios, textos\n"
                    "✨ Valor mínimo: 150 besitos\n"
                    "🎰 Factor sorpresa garantizado"
                ),
                "price": 80,
                "is_vip_only": False,
                "stock_limit": None,
                "max_purchases_per_user": 3,
                "lore_piece": {
                    "code_name": "cofre_secretos",
                    "title": "🎁 Cofre de Secretos",
                    "content": (
                        "**[Al abrir el cofre]**\n\n"
                        "*[Una nota escrita a mano]*\n\n"
                        "\"Me gusta la idea de sorprenderte. Dentro de este cofre "
                        "hay algo que elegí específicamente pensando en el tipo "
                        "de persona que eres.\"\n\n"
                        "*[Diana]*\n\n"
                        "P.D: Si te gusta la sorpresa, puedes abrir otro cofre. "
                        "Nunca sabes qué encontrarás..."
                    ),
                    "category": "sorpresa",
                    "content_type": "mixed"
                }
            },
            {
                "name": "💝 Regalo de Cumpleaños",
                "description": (
                    "Un regalo especial de Diana para tu cumpleaños.\n\n"
                    "🎂 Contenido personalizado\n"
                    "💌 Mensaje de cumpleaños de Diana\n"
                    "🎁 Sorpresa adicional\n"
                    "⏰ Disponible solo en tu mes de cumpleaños"
                ),
                "price": 50,
                "is_vip_only": False,
                "stock_limit": None,
                "max_purchases_per_user": 1,
                "available_from": None,
                "available_until": None,
                "lore_piece": {
                    "code_name": "regalo_cumpleanos",
                    "title": "💝 Feliz Cumpleaños",
                    "content": (
                        "**[Video mensaje personal]**\n\n"
                        "*[Diana aparece con una sonrisa genuina]*\n\n"
                        "\"Feliz cumpleaños... Sé que es un día especial para ti. "
                        "Y quería que supieras que eres especial para mí también.\"\n\n"
                        "*[Se acerca a la cámara]*\n\n"
                        "\"Hoy, celebra todo lo que eres. Y gracias... por estar aquí.\"\n\n"
                        "*[Te manda un beso]*"
                    ),
                    "category": "celebracion",
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
        logger.info(f"  └─ LorePiece '{lore_data['code_name']}' ya existe, actualizando...")
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
        logger.info(f"  └─ LorePiece '{lore_data['code_name']}' creada")
        return lore_piece


async def create_shop_item(session: AsyncSession, item_data: dict) -> ShopItem:
    """Crea o actualiza un ShopItem"""

    # Verificar si ya existe
    stmt = select(ShopItem).where(ShopItem.name == item_data["name"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    # Crear LorePiece si existe en los datos
    lore_piece_id = None
    if "lore_piece" in item_data:
        lore_piece = await create_lore_piece(session, item_data["lore_piece"])
        lore_piece_id = lore_piece.id

    if existing:
        logger.info(f"  └─ ShopItem '{item_data['name']}' ya existe, actualizando...")
        existing.description = item_data["description"]
        existing.price = item_data["price"]
        existing.is_vip_only = item_data["is_vip_only"]
        existing.stock_limit = item_data.get("stock_limit")
        existing.max_purchases_per_user = item_data.get("max_purchases_per_user", 1)
        existing.unlock_requirements = item_data.get("unlock_requirements")
        existing.available_from = item_data.get("available_from")
        existing.available_until = item_data.get("available_until")
        existing.unlocks_lore_piece_id = lore_piece_id
        existing.is_active = True
        return existing
    else:
        shop_item = ShopItem(
            name=item_data["name"],
            description=item_data["description"],
            price=item_data["price"],
            is_vip_only=item_data["is_vip_only"],
            stock_limit=item_data.get("stock_limit"),
            max_purchases_per_user=item_data.get("max_purchases_per_user", 1),
            unlock_requirements=item_data.get("unlock_requirements"),
            available_from=item_data.get("available_from"),
            available_until=item_data.get("available_until"),
            unlocks_lore_piece_id=lore_piece_id,
            is_active=True
        )
        session.add(shop_item)
        await session.flush()
        logger.info(f"  └─ ShopItem '{item_data['name']}' creado")
        return shop_item


async def setup_shop(session: AsyncSession):
    """Setup completo de la tienda"""

    logger.info("╔═══════════════════════════════════════════════")
    logger.info("║  🛍️  SETUP: TIENDA DE SEÑORITA KINKY")
    logger.info("╚═══════════════════════════════════════════════\n")

    total_items = 0
    total_lore_pieces = 0

    for category_data in SHOP_ITEMS:
        category_name = category_data["category"]
        logger.info(f"📦 Categoría: {category_name}")
        logger.info("─" * 50)

        for item_data in category_data["items"]:
            logger.info(f"\n  🔹 Procesando: {item_data['name']}")
            logger.info(f"     Precio: {item_data['price']} besitos")
            logger.info(f"     VIP Only: {'Sí' if item_data['is_vip_only'] else 'No'}")

            if item_data.get("stock_limit"):
                logger.info(f"     Stock: {item_data['stock_limit']} unidades")

            if item_data.get("unlock_requirements"):
                logger.info(f"     Requirements: {item_data['unlock_requirements']}")

            await create_shop_item(session, item_data)
            total_items += 1

            if "lore_piece" in item_data:
                total_lore_pieces += 1

        logger.info("\n")

    await session.commit()

    logger.info("\n╔═══════════════════════════════════════════════")
    logger.info("║  ✅  SETUP COMPLETADO")
    logger.info("╠═══════════════════════════════════════════════")
    logger.info(f"║  📦 Shop Items creados: {total_items}")
    logger.info(f"║  📚 Lore Pieces creadas: {total_lore_pieces}")
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
            await setup_shop(session)
            logger.info("🎉 Tienda configurada exitosamente!\n")
            logger.info("💡 Ahora los usuarios pueden comprar items en /tienda")

        except Exception as e:
            logger.error(f"❌ Error durante el setup: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
