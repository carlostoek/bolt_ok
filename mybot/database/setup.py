# database/setup.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal, engine as app_engine, Base
from utils.config import Config

logger = logging.getLogger(__name__)

TABLES_ORDER = [
    'users',
    'achievements',
    'story_fragments',
    'narrative_choices',
    'user_narrative_states',
    'rewards',
    'lore_pieces',
    'missions',
    'events',
    'raffles',
    'badges',
    'levels',
    'invite_tokens',
    'subscription_plans',
    'subscription_tokens',
    'tariffs',
    'config_entries',
    'bot_config',
    'channels',
    'pending_channel_requests',
    'challenges',
    'auctions',
    'trivias',
    'user_rewards',
    'user_achievements',
    'user_mission_entries',
    'raffle_entries',
    'user_badges',
    'vip_subscriptions',
    'vip_grants',  # Nueva tabla para auditoría de VIP grants
    'user_stats',
    'tokens',
    'user_challenge_progress',
    'button_reactions',
    'bids',
    'auction_participants',
    'minigame_play',
    'user_lore_pieces',
    'trivia_questions',
    'trivia_attempts',
    'trivia_user_answers',
    'shop_items',
    'user_purchases',
]

async def init_db():
    try:
        logger.info("Inicializando motor de base de datos desde database/setup.py...")

        async with app_engine.begin() as conn:
            # This is now handled by the app's init_db, but we keep it for legacy scripts
            # that might call this function directly.
            logger.info("Verificando/creando tablas desde legacy init_db...")
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Tablas verificadas/creadas exitosamente desde legacy init_db.")
        
        await populate_initial_shop_items()
        
        return app_engine

    except Exception as e:
        logger.critical(f"Error crítico al inicializar la base de datos: {e}")
        raise

def get_session_factory():
    return AsyncSessionLocal

async def get_session() -> AsyncSession:
    return AsyncSessionLocal()

async def populate_initial_shop_items():
    """Add some initial items to the shop if it's empty"""
    from .models import ShopItem
    from sqlalchemy import select
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Check if there are any shop items
        result = await session.execute(select(ShopItem))
        items = result.scalars().all()
        
        if not items:
            logger.info("Populating shop with initial items...")
            # Add some sample items
            initial_items = [
                ShopItem(
                    name="📖 Diario Secreto",
                    description="Un diario personal con historias íntimas de Diana",
                    price=50,
                    is_vip_only=False,
                    unlocks_lore_piece_id=None
                ),
                ShopItem(
                    name="🔑 Cofre del Recuerdo",
                    description="Contiene fotos y cartas del pasado de Lucien",
                    price=100,
                    is_vip_only=False,
                    unlocks_lore_piece_id=None
                ),
                ShopItem(
                    name="💎 Collar VIP Exclusivo",
                    description="Un collar que Diana usó en una cita importante",
                    price=200,
                    is_vip_only=True,
                    unlocks_lore_piece_id=None
                ),
                ShopItem(
                    name="🎭 Máscara del Baile",
                    description="La máscara que Lucien usó en el baile de máscaras",
                    price=150,
                    is_vip_only=False,
                    unlocks_lore_piece_id=None
                )
            ]
            
            session.add_all(initial_items)
            await session.commit()
            logger.info(f"Added {len(initial_items)} initial shop items")
