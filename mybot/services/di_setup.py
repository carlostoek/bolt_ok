import logging
from typing import Dict, Any, Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.container import Container, init_container
from services.di_middleware import DIContainerMiddleware
from services.interfaces import IUserNarrativeService, IRewardSystem, INotificationService, IPointService

logger = logging.getLogger(__name__)


class DISetup:
    """
    Clase para configurar y acceder al contenedor de dependencias.
    Proporciona una interfaz unificada para la integración del DI.
    """
    
    _instance: Optional['DISetup'] = None
    _container: Optional[Container] = None
    
    @classmethod
    async def initialize(cls, database_url: str, bot: Bot, echo: bool = False) -> 'DISetup':
        """
        Inicializa el contenedor de dependencias.
        
        Args:
            database_url (str): URL de conexión a la base de datos
            bot (Bot): Instancia del bot de Telegram
            echo (bool): Activar log de consultas SQL
            
        Returns:
            DISetup: Instancia de DISetup con el contenedor inicializado
        """
        if cls._instance is None:
            logger.info("Inicializando contenedor de dependencias...")
            
            instance = cls()
            instance._container = await init_container(database_url, bot, echo)
            
            cls._instance = instance
            
            logger.info("Contenedor de dependencias inicializado correctamente")
            
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'DISetup':
        """
        Obtiene la instancia del DISetup.
        
        Returns:
            DISetup: Instancia de DISetup
            
        Raises:
            RuntimeError: Si no se ha inicializado DISetup
        """
        if cls._instance is None:
            raise RuntimeError("DISetup no ha sido inicializado. Llama a initialize() primero.")
        return cls._instance
    
    @property
    def container(self) -> Container:
        """
        Obtiene el contenedor de dependencias.
        
        Returns:
            Container: Contenedor de dependencias
            
        Raises:
            RuntimeError: Si no se ha inicializado el contenedor
        """
        if self._container is None:
            raise RuntimeError("El contenedor no ha sido inicializado")
        return self._container
    
    def get_middleware(self) -> DIContainerMiddleware:
        """
        Obtiene el middleware de inyección de dependencias.
        
        Returns:
            DIContainerMiddleware: Middleware de inyección de dependencias
        """
        return DIContainerMiddleware(self.container)
    
    def get_session_factory(self):
        """
        Obtiene la factoría de sesiones de base de datos.
        
        Returns:
            Callable: Factoría de sesiones
        """
        return self.container.session_factory
    
    async def get_session(self) -> AsyncSession:
        """
        Obtiene una sesión de base de datos.
        
        Returns:
            AsyncSession: Sesión de base de datos
        """
        return await self.container.session()
    
    def get_user_narrative_service(self) -> IUserNarrativeService:
        """
        Obtiene el servicio de narrativa de usuario.
        
        Returns:
            IUserNarrativeService: Servicio de narrativa de usuario
        """
        return self.container.user_narrative_service_provider()
    
    def get_reward_system(self) -> IRewardSystem:
        """
        Obtiene el sistema de recompensas.
        
        Returns:
            IRewardSystem: Sistema de recompensas
        """
        return self.container.reward_system_provider()
    
    def get_notification_service(self) -> INotificationService:
        """
        Obtiene el servicio de notificaciones.
        
        Returns:
            INotificationService: Servicio de notificaciones
        """
        return self.container.notification_service_provider()
    
    def get_point_service(self) -> IPointService:
        """
        Obtiene el servicio de puntos.
        
        Returns:
            IPointService: Servicio de puntos
        """
        return self.container.point_service_provider()