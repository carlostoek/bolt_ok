import asyncio
import logging
import sys
from datetime import datetime
from sqlalchemy import select

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.setup import init_db, get_session_factory
from database.models import PendingChannelRequest
from utils.config import BOT_TOKEN, VIP_CHANNEL_ID

# Configuración de logging simplificada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Reducir ruido de librerías externas
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Router principal para comandos
router = Router()

# Middleware para inyectar la sesión de base de datos
class DBSessionMiddleware:
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        async with self.session_pool() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            finally:
                await session.close()

# Comando para mostrar solicitudes pendientes
@router.message(Command("mostrar"))
async def mostrar_solicitudes(message: Message, session: AsyncSession):
    """Mostrar solicitudes pendientes."""
    try:
        # Obtener solicitudes pendientes
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.approved == False
        )
        result = await session.execute(stmt)
        pending_requests = result.scalars().all()
        
        if not pending_requests:
            await message.answer("No hay solicitudes pendientes.")
            return
        
        # Contar solicitudes
        count = len(pending_requests)
        
        # Formatear detalles de las solicitudes
        texto = f"📋 **{count} Solicitudes pendientes**:\n\n"
        
        for i, req in enumerate(pending_requests[:10], 1):  # Limitar a 10 para el mensaje
            tiempo_espera = datetime.utcnow() - req.request_timestamp
            horas = int(tiempo_espera.total_seconds() // 3600)
            minutos = int((tiempo_espera.total_seconds() % 3600) // 60)
            
            texto += (
                f"{i}. ID Usuario: `{req.user_id}`\n"
                f"   Solicitado hace: {horas}h {minutos}m\n"
                f"   Chat ID: `{req.chat_id}`\n\n"
            )
        
        if count > 10:
            texto += f"... y {count - 10} solicitudes más."
        
        await message.answer(texto, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logging.error(f"Error mostrando solicitudes: {e}")
        await message.answer(f"❌ Error: {str(e)}")

# Comando para aceptar solicitudes pendientes
@router.message(Command("aceptar"))
async def aceptar_solicitudes(message: Message, session: AsyncSession, bot: Bot):
    """Aceptar solicitudes pendientes."""
    try:
        # Obtener solicitudes pendientes
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.approved == False
        )
        result = await session.execute(stmt)
        pending_requests = result.scalars().all()
        
        if not pending_requests:
            await message.answer("No hay solicitudes pendientes para aceptar.")
            return
        
        count = len(pending_requests)
        processed = 0
        
        # Procesar cada solicitud
        for req in pending_requests:
            try:
                # Aprobar la solicitud en Telegram
                await bot.approve_chat_join_request(
                    chat_id=req.chat_id,
                    user_id=req.user_id
                )
                
                # Marcar como aprobada en la base de datos
                req.approved = True
                req.approval_timestamp = datetime.utcnow()
                processed += 1
                
                # Notificar al usuario (opcional)
                try:
                    await bot.send_message(
                        req.user_id, 
                        "✅ Tu solicitud para unirte al canal ha sido aprobada."
                    )
                except Exception as e:
                    logging.warning(f"No se pudo notificar al usuario {req.user_id}: {e}")
                
                logging.info(f"Aprobada solicitud de usuario {req.user_id} para canal {req.chat_id}")
                
            except Exception as e:
                logging.error(f"Error aprobando solicitud {req.id}: {e}")
        
        # Guardar cambios en la base de datos
        if processed > 0:
            await session.commit()
            await message.answer(f"✅ Se aprobaron {processed} de {count} solicitudes pendientes.")
        else:
            await message.answer("❌ No se pudo aprobar ninguna solicitud.")
    
    except Exception as e:
        logging.error(f"Error procesando solicitudes: {e}")
        await message.answer(f"❌ Error: {str(e)}")

# Manejador para detectar nuevas solicitudes de ingreso
@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest, session: AsyncSession):
    """Detectar y registrar solicitudes de unión al canal."""
    try:
        user_id = event.from_user.id
        chat_id = event.chat.id
        
        # Verificar si ya existe una solicitud pendiente
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == chat_id,
            PendingChannelRequest.approved == False
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            logging.info(f"Solicitud ya existente para usuario {user_id} en canal {chat_id}")
            return
        
        # Crear nueva solicitud
        pending = PendingChannelRequest(
            user_id=user_id,
            chat_id=chat_id,
            request_timestamp=datetime.utcnow(),
            approved=False
        )
        
        session.add(pending)
        await session.commit()
        
        logging.info(f"Nueva solicitud registrada: Usuario {user_id} para canal {chat_id}")
        
        # Enviar mensaje al usuario (opcional)
        try:
            await event.bot.send_message(
                user_id,
                f"📋 Tu solicitud para unirte al canal ha sido registrada. Te notificaremos cuando sea aprobada."
            )
        except Exception as e:
            logging.warning(f"No se pudo enviar mensaje al usuario {user_id}: {e}")
    
    except Exception as e:
        logging.error(f"Error procesando solicitud de unión: {e}")

async def main():
    """Función principal."""
    try:
        # Inicializar base de datos
        logging.info("Inicializando base de datos...")
        await init_db()
        
        # Configurar bot
        session_factory = get_session_factory()
        bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher(storage=MemoryStorage())
        
        # Configurar middleware
        session_middleware = DBSessionMiddleware(session_factory)
        dp.update.middleware(session_middleware)
        
        # Registrar router
        dp.include_router(router)
        
        # Iniciar el bot
        logging.info("Bot iniciado. Presiona Ctrl+C para detener.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
    except Exception as e:
        logging.critical(f"Error crítico: {e}", exc_info=True)
    finally:
        logging.info("Bot detenido.")
        if 'bot' in locals():
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot detenido manualmente.")
    except Exception as e:
        logging.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)