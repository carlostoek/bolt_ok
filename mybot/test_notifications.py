"""
Script de prueba para verificar la unificación de notificaciones.
Este script simula el flujo de notificaciones de misiones y reacciones
para validar que las notificaciones estén correctamente unificadas.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.notification_service import NotificationService
from database.base import Base

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock para simular el bot
class MockBot:
    async def send_message(self, user_id, text, **kwargs):
        logger.info(f"Mensaje enviado a {user_id}: {text}")
        return True

async def test_unified_notifications():
    """Prueba el sistema de notificaciones unificadas."""
    logger.info("Iniciando prueba de notificaciones unificadas...")
    
    # Configurar conexión a la base de datos
    engine = create_async_engine('sqlite+aiosqlite:///./test_db.sqlite')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # Base is already imported
    
    async with engine.begin() as conn:
        # Crear tablas para prueba (si no existen)
        await conn.run_sync(Base.metadata.create_all)
    
    # Crear sesión y bot mock
    async with async_session() as session:
        bot = MockBot()
        notification_service = NotificationService(session, bot)
        
        # Probar diferentes combinaciones de notificaciones
        test_user_id = 12345
        
        # Caso 1: Solo notificación de misión
        logger.info("Caso 1: Solo notificación de misión")
        await notification_service.add_notification(
            test_user_id,
            "mission",
            {
                "name": "Misión de prueba",
                "points": 50,
                "description": "Esta es una misión de prueba"
            }
        )
        await asyncio.sleep(1.5)  # Esperar a que se envíe la notificación
        
        # Caso 2: Solo notificación de puntos
        logger.info("Caso 2: Solo notificación de puntos")
        await notification_service.add_notification(
            test_user_id,
            "points",
            {
                "points": 25,
                "total": 125,
                "source": "test"
            }
        )
        await asyncio.sleep(1.5)
        
        # Caso 3: Combinación de notificaciones misión + puntos (deberían agruparse)
        logger.info("Caso 3: Combinación misión + puntos (deberían agruparse)")
        await notification_service.add_notification(
            test_user_id,
            "mission",
            {
                "name": "Misión combinada",
                "points": 30,
                "description": "Esta misión se debería combinar con puntos"
            }
        )
        await notification_service.add_notification(
            test_user_id,
            "points",
            {
                "points": 15,
                "total": 140,
                "source": "test"
            }
        )
        await asyncio.sleep(1.5)
        
        # Caso 4: Notificación de reacción nativa
        logger.info("Caso 4: Notificación de reacción nativa")
        await notification_service.add_notification(
            test_user_id,
            "reaction",
            {
                "type": "publication",
                "reaction_type": "👍",
                "is_native": True
            }
        )
        await asyncio.sleep(1.5)
        
        # Caso 5: Notificación de reacción que completa misión (deberían agruparse)
        logger.info("Caso 5: Reacción que completa misión (deberían agruparse)")
        await notification_service.add_notification(
            test_user_id,
            "reaction",
            {
                "type": "publication",
                "reaction_type": "❤️",
                "is_native": False
            }
        )
        await notification_service.add_notification(
            test_user_id,
            "mission",
            {
                "name": "Reaccionar con corazón",
                "points": 40,
                "description": "Esta misión se completó por reaccionar con corazón"
            }
        )
        await asyncio.sleep(1.5)
        
        logger.info("Pruebas de notificación completadas")

if __name__ == "__main__":
    asyncio.run(test_unified_notifications())