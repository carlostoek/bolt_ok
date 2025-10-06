import asyncio
import logging
from sqlalchemy.future import select
from database.setup import init_db, get_session_factory
from database.models import ShopItem, LorePiece

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate_shop():
    """
    Populates the shop with a predefined list of items, including items linked to lore pieces.
    """
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        # --- 1. Create Lore Pieces ---
        # Ensure lore pieces exist before creating shop items that link to them.
        lore_piece_1 = LorePiece(
            code_name="DIANA_DIARY_1",
            title="Entrada del Diario de Diana",
            description="Una página arrancada del diario de Diana.",
            content_type="text",
            content="He descubierto un secreto sobre la mansión...",
            category="Diarios",
            is_main_story=False,
        )
        lore_piece_2 = LorePiece(
            code_name="LUCIEN_LETTER_1",
            title="Carta de Lucien",
            description="Una carta de Lucien a un destinatario desconocido.",
            content_type="text",
            content="No puedo revelar la verdad, no todavía.",
            category="Cartas",
            is_main_story=False,
        )
        
        # Check if lore pieces already exist
        existing_lp1 = await session.execute(select(LorePiece).where(LorePiece.code_name == "DIANA_DIARY_1"))
        if not existing_lp1.scalar_one_or_none():
            session.add(lore_piece_1)
            logger.info("Creating lore piece: DIANA_DIARY_1")
        
        existing_lp2 = await session.execute(select(LorePiece).where(LorePiece.code_name == "LUCIEN_LETTER_1"))
        if not existing_lp2.scalar_one_or_none():
            session.add(lore_piece_2)
            logger.info("Creating lore piece: LUCIEN_LETTER_1")
            
        await session.commit()

        # --- 2. Define Shop Items ---
        # Get the created lore pieces to link them to shop items
        lp1_result = await session.execute(select(LorePiece).where(LorePiece.code_name == "DIANA_DIARY_1"))
        lp1 = lp1_result.scalar_one()
        
        lp2_result = await session.execute(select(LorePiece).where(LorePiece.code_name == "LUCIEN_LETTER_1"))
        lp2 = lp2_result.scalar_one()

        shop_items_to_add = [
            {
                "name": "Pista del Pasado",
                "description": "Desbloquea una entrada del diario de Diana.",
                "price": 75,
                "is_vip_only": False,
                "unlocks_lore_piece_id": lp1.id,
            },
            {
                "name": "Secreto Familiar",
                "description": "Una carta misteriosa escrita por Lucien.",
                "price": 120,
                "is_vip_only": False,
                "unlocks_lore_piece_id": lp2.id,
            },
            {
                "name": "Acceso VIP a la Biblioteca",
                "description": "Acceso exclusivo a una sección oculta de la biblioteca.",
                "price": 250,
                "is_vip_only": True,
                "unlocks_lore_piece_id": None,
            },
            {
                "name": "Llave Antigua",
                "description": "Una llave ornamentada que parece abrir algo importante.",
                "price": 180,
                "is_vip_only": False,
                "unlocks_lore_piece_id": None,
            },
        ]

        # --- 3. Add Shop Items to Database ---
        for item_data in shop_items_to_add:
            # Check if an item with the same name already exists
            result = await session.execute(select(ShopItem).where(ShopItem.name == item_data["name"]))
            existing_item = result.scalar_one_or_none()

            if existing_item:
                logger.info(f"El artículo '{item_data['name']}' ya existe. Omitiendo.")
            else:
                new_item = ShopItem(**item_data)
                session.add(new_item)
                logger.info(f"Añadiendo artículo a la tienda: {item_data['name']}")
        
        await session.commit()
        logger.info("Población de la tienda completada.")

if __name__ == "__main__":
    asyncio.run(populate_shop())