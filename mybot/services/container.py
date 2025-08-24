from typing import Optional, Callable, AsyncGenerator
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from aiogram import Bot

from database.base import Base
from services.interfaces import IUserNarrativeService, IRewardSystem, INotificationService, IPointService
from services.user_narrative_service import UserNarrativeService
from services.reward_service import RewardSystem
from services.notification_service import NotificationService
from services.point_service import PointService
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.event_service import EventService


class Container(containers.DeclarativeContainer):
    """
    Contenedor de dependencias para los servicios de la aplicación.
    Centraliza la creación y gestión de dependencias.
    """
    
    # Configuración general
    config = providers.Configuration()
    
    # Recursos compartidos
    db_engine = providers.Resource(
        create_async_engine,
        config.db.url,
        echo=config.db.echo,
    )
    
    # Factoría de sesiones de BD
    session_factory = providers.Factory(
        sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Proveedor de sesión de BD (scope request)
    session = providers.Resource(
        session_factory_provider=session_factory,
    )
    
    # Bot de Telegram
    bot = providers.Dependency(instance_of=Bot)
    
    # Servicios core - nivel 1 (sin dependencias de otros servicios)
    level_service = providers.Factory(
        LevelService,
        session=session,
    )
    
    achievement_service = providers.Factory(
        AchievementService,
        session=session,
    )
    
    event_service = providers.Factory(
        EventService,
        session=session,
    )
    
    # Servicios core - nivel 2 (con dependencias simples)
    notification_service = providers.Factory(
        NotificationService,
        session=session,
        bot=bot,
    )
    
    # Servicios core - nivel 3 (con dependencias complejas)
    point_service = providers.Factory(
        PointService,
        session=session,
        # Inyecta las dependencias necesarias
        level_service=level_service,
        achievement_service=achievement_service,
        notification_service=notification_service,
    )
    
    # Servicios específicos
    reward_system = providers.Factory(
        RewardSystem,
        session=session,
        point_service=point_service,
    )
    
    user_narrative_service = providers.Factory(
        UserNarrativeService,
        session=session,
        reward_system=reward_system,
    )
    
    # Gateways - Providers para interfaces
    user_narrative_service_provider = providers.Factory(
        lambda container: container.user_narrative_service(),
        container=providers.Self(),
    )
    
    reward_system_provider = providers.Factory(
        lambda container: container.reward_system(),
        container=providers.Self(),
    )
    
    notification_service_provider = providers.Factory(
        lambda container: container.notification_service(),
        container=providers.Self(),
    )
    
    point_service_provider = providers.Factory(
        lambda container: container.point_service(),
        container=providers.Self(),
    )


# Función para inicializar el contenedor
async def init_container(database_url: str, bot: Bot, echo: bool = False) -> Container:
    """
    Inicializa el contenedor de dependencias con la configuración especificada.
    
    Args:
        database_url (str): URL de conexión a la base de datos
        bot (Bot): Instancia del bot de Telegram
        echo (bool): Activar log de consultas SQL
        
    Returns:
        Container: Contenedor de dependencias configurado
    """
    container = Container()
    container.config.from_dict({
        "db": {
            "url": database_url,
            "echo": echo,
        }
    })
    container.bot.override(bot)
    
    return container


# Helper para obtener una sesión desde el contenedor
async def get_session(container: Container) -> AsyncGenerator[AsyncSession, None]:
    """
    Obtiene una sesión de base de datos del contenedor.
    
    Args:
        container (Container): Contenedor de dependencias
        
    Yields:
        AsyncSession: Sesión de base de datos
    """
    async with container.session() as session:
        yield session