# database/setup.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from .base import Base
from utils.config import Config

logger = logging.getLogger(__name__)

_engine = None
_sessionmaker = None

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
    global _engine
    try:
        logger.info("Inicializando motor de base de datos SQLite...")

        db_url = Config.DATABASE_URL.strip()

        if not db_url.startswith("sqlite+aiosqlite://"):
            raise ValueError("DATABASE_URL debe comenzar con 'sqlite+aiosqlite://' para usar SQLite async.")

        if _engine is None:
            _engine = create_async_engine(
                db_url,
                echo=False,
                poolclass=NullPool
            )

        async with _engine.begin() as conn:
            logger.info("Creando tablas en orden definido...")
            tables = [Base.metadata.tables[name] for name in TABLES_ORDER if name in Base.metadata.tables]
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
            
            # Create any remaining tables that might not be in TABLES_ORDER
            logger.info("Creando tablas restantes...")
            remaining_tables = [table for name, table in Base.metadata.tables.items() if name not in TABLES_ORDER]
            if remaining_tables:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=remaining_tables))
            
            logger.info("Todas las tablas creadas exitosamente.")
        
        # Populate initial shop items if the shop is empty
        await populate_initial_shop_items()
        
        return _engine

    except Exception as e:
        logger.critical(f"Error crítico al inicializar la base de datos: {e}")
        raise

def get_session_factory():
    global _sessionmaker
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db first.")
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _sessionmaker

async def get_session() -> AsyncSession:
    session_factory = get_session_factory()
    return session_factory()

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
