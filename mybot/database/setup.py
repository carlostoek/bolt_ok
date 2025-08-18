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
    'narrative_fragments',
    'narrative_decisions',
    'user_decision_log',
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
]

async def init_db():
    global _engine
    try:
        db_url = Config.DATABASE_URL.strip()
        
        if db_url.startswith("postgresql+asyncpg://"):
            logger.info("Inicializando motor de base de datos PostgreSQL...")
        elif db_url.startswith("sqlite+aiosqlite://"):
            logger.info("Inicializando motor de base de datos SQLite...")
        else:
            raise ValueError("DATABASE_URL debe comenzar con 'postgresql+asyncpg://' o 'sqlite+aiosqlite://'")

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
            logger.info("Tablas creadas exitosamente.")
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
