from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dependency_injector.containers import Container


class DIContainerMiddleware(BaseMiddleware):
    """
    Middleware que inyecta el contenedor de dependencias en los datos del manejador.
    Permite que los manejadores accedan a los servicios configurados en el contenedor.
    """
    
    def __init__(self, container: Container):
        """
        Constructor del middleware.
        
        Args:
            container (Container): Contenedor de dependencias a inyectar
        """
        self.container = container
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Método invocado para cada evento procesado por el dispatcher.
        
        Args:
            handler: Función manejadora del evento
            event: Evento de Telegram a procesar
            data: Datos adicionales del evento
            
        Returns:
            Any: Resultado del manejador
        """
        # Inyectar el contenedor en los datos
        data["container"] = self.container
        
        # Llamar al siguiente manejador en la cadena
        return await handler(event, data)