import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

# Add the project root to sys.path to import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import Base, configure_engine, engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata

# Detect database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")


def get_database_url():
    """
    Obtiene la URL de la base de datos desde las variables de entorno.
    """
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include custom names for constraint naming
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Custom function to include objects in autogenerate.
    This helps filter out unwanted objects or include special ones.
    """
    # Exclude tables that are not part of our application
    if type_ == "table":
        # Add custom logic here if needed
        pass
    return True


def do_run_migrations(connection):
    """
    Execute migrations with a database connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        # Add custom naming conventions
        render_as_batch=True,  # Enable batch mode for SQLite compatibility
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an
    Engine and associate a connection with the context.
    """
    database_url = get_database_url()
    
    # Configure engine if not already done
    if engine is None:
        configure_engine(database_url)
    
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


def run_migrations():
    """
    Main function to run migrations, detects if online or offline mode is needed.
    """
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


# Import all models here so that they are registered with the metadata
def import_models():
    """
    Import all application models to ensure they are registered with SQLAlchemy metadata.
    This is essential for Alembic to detect and include all tables in migrations.
    """
    try:
        # Import narrative models
        from app.models.narrative import StoryFragment, NarrativeChoice, UserNarrativeState  # type: ignore
        # Import shop models
        from app.models.shop import ShopItem, ProductFile, InventoryItem, UserPurchase  # type: ignore
        # Import gamification models
        from app.models.gamification import Mission, Reward, Achievement, Badge  # type: ignore
        # Import automation models
        from app.models.automation import AutomationTrigger, TriggerAction, TriggerExecutionLog  # type: ignore
        # Import user models
        from app.models.user import User, UserMissionEntry, UserFragmentView  # type: ignore
        # Import lore models
        from app.models.lore import LorePiece, UserLorePiece  # type: ignore
    except ImportError:
        # Models may not exist yet, that's ok for initial setup
        pass


# Import all models before running migrations
import_models()

# Run the migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())