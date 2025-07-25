"""
Handler for free channel configuration by administrators.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from services.free_channel_service import FreeChannelService
from utils.admin_check import is_admin
from utils.message_safety import safe_answer, safe_edit
from keyboards.admin_config_kb import create_free_channel_config_keyboard

router = Router()
logger = logging.getLogger(__name__)


class FreeChannelConfigStates(StatesGroup):
    """Estados para configuración del canal gratuito."""
    waiting_for_wait_time = State()
    waiting_for_social_message = State()
    waiting_for_welcome_message = State()


@router.callback_query(F.data == "admin_free_channel_config")
async def show_free_channel_config(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Mostrar menú de configuración del canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    free_service = FreeChannelService(session, bot)
    stats = await free_service.get_channel_statistics()
    
    config_text = (
        "🔧 **Configuración del Canal Gratuito**\n\n"
        f"📊 **Estado Actual:**\n"
        f"• Canal configurado: {'✅' if stats['channel_configured'] else '❌'}\n"
        f"• Tiempo de espera: {stats['wait_time_minutes']} minutos\n"
        f"• Solicitudes pendientes: {stats['pending_requests']}\n"
        f"• Total procesadas: {stats['total_processed']}\n"
        f"• Usuarios con rol FREE: {stats.get('free_users_count', 0)}\n\n"
        "⚙️ **Opciones de configuración:**"
    )
    
    if stats['channel_configured']:
        config_text += f"\n• Canal: {stats.get('channel_title', 'N/A')} (ID: {stats['channel_id']})"
    
    keyboard = create_free_channel_config_keyboard(stats)
    await safe_edit(callback, config_text, reply_markup=keyboard)


@router.callback_query(F.data == "config_wait_time")
async def config_wait_time(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Configurar tiempo de espera para aprobaciones."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    await state.set_state(FreeChannelConfigStates.waiting_for_wait_time)
    
    text = (
        "⏰ **Configurar Tiempo de Espera**\n\n"
        "Ingresa el tiempo de espera en minutos antes de aprobar automáticamente las solicitudes.\n\n"
        "📝 **Ejemplos:**\n"
        "• `0` - Aprobar inmediatamente\n"
        "• `5` - Esperar 5 minutos\n"
        "• `60` - Esperar 1 hora\n"
        "• `1440` - Esperar 24 horas\n\n"
        "Envía el número de minutos:"
    )
    
    await safe_edit(callback, text)


@router.message(FreeChannelConfigStates.waiting_for_wait_time)
async def process_wait_time(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Procesar el tiempo de espera configurado."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ No tienes permisos de administrador.")
        return
    
    try:
        wait_minutes = int(message.text.strip())
        if wait_minutes < 0:
            await safe_answer(message, "❌ El tiempo de espera no puede ser negativo.")
            return
        
        free_service = FreeChannelService(session, bot)
        success = await free_service.set_wait_time_minutes(wait_minutes)
        
        if success:
            if wait_minutes == 0:
                response = "✅ Configurado para aprobar solicitudes **inmediatamente**."
            elif wait_minutes < 60:
                response = f"✅ Tiempo de espera configurado a **{wait_minutes} minutos**."
            else:
                hours = wait_minutes // 60
                remaining_minutes = wait_minutes % 60
                if remaining_minutes > 0:
                    time_text = f"{hours} horas y {remaining_minutes} minutos"
                else:
                    time_text = f"{hours} horas"
                response = f"✅ Tiempo de espera configurado a **{time_text}**."
            
            await safe_answer(message, response)
        else:
            await safe_answer(message, "❌ Error al configurar el tiempo de espera.")
        
    except ValueError:
        await safe_answer(message, "❌ Por favor, ingresa un número válido de minutos.")
    
    await state.clear()


@router.callback_query(F.data == "config_social_message")
async def config_social_message(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Configurar mensaje de redes sociales."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    await state.set_state(FreeChannelConfigStates.waiting_for_social_message)
    
    text = (
        "📱 **Configurar Mensaje de Redes Sociales**\n\n"
        "Este mensaje se envía automáticamente cuando un usuario solicita unirse al canal gratuito.\n\n"
        "💡 **Puedes usar:**\n"
        "• `{user_name}` - Se reemplaza por el nombre del usuario\n"
        "• Markdown para formato\n"
        "• Enlaces a tus redes sociales\n\n"
        "📝 **Envía el mensaje personalizado:**"
    )
    
    await safe_edit(callback, text)


@router.message(FreeChannelConfigStates.waiting_for_social_message)
async def process_social_message(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Procesar el mensaje de redes sociales configurado."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ No tienes permisos de administrador.")
        return
    
    social_message = message.text.strip()
    if len(social_message) > 4000:
        await safe_answer(message, "❌ El mensaje es muy largo. Máximo 4000 caracteres.")
        return
    
    free_service = FreeChannelService(session, bot)
    success = await free_service.set_social_media_message(social_message)
    
    if success:
        await safe_answer(message, "✅ Mensaje de redes sociales configurado exitosamente.")
    else:
        await safe_answer(message, "❌ Error al configurar el mensaje de redes sociales.")
    
    await state.clear()


@router.callback_query(F.data == "config_welcome_message")
async def config_welcome_message(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Configurar mensaje de bienvenida."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    await state.set_state(FreeChannelConfigStates.waiting_for_welcome_message)
    
    text = (
        "🎉 **Configurar Mensaje de Bienvenida**\n\n"
        "Este mensaje se envía cuando un usuario es aprobado al canal gratuito.\n\n"
        "💡 **Puedes usar:**\n"
        "• Markdown para formato\n"
        "• Emojis para hacer el mensaje más atractivo\n"
        "• Instrucciones sobre cómo usar el canal\n\n"
        "📝 **Envía el mensaje de bienvenida:**"
    )
    
    await safe_edit(callback, text)


@router.message(FreeChannelConfigStates.waiting_for_welcome_message)
async def process_welcome_message(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Procesar el mensaje de bienvenida configurado."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ No tienes permisos de administrador.")
        return
    
    welcome_message = message.text.strip()
    if len(welcome_message) > 4000:
        await safe_answer(message, "❌ El mensaje es muy largo. Máximo 4000 caracteres.")
        return
    
    free_service = FreeChannelService(session, bot)
    success = await free_service.set_welcome_message(welcome_message)
    
    if success:
        await safe_answer(message, "✅ Mensaje de bienvenida configurado exitosamente.")
    else:
        await safe_answer(message, "❌ Error al configurar el mensaje de bienvenida.")
    
    await state.clear()


@router.callback_query(F.data == "test_approval_flow")
async def test_approval_flow(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Probar el flujo de aprobación manualmente."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    free_service = FreeChannelService(session, bot)
    processed = await free_service.process_pending_requests()
    
    if processed > 0:
        await safe_answer(callback, f"✅ Se procesaron {processed} solicitudes pendientes.")
    else:
        await safe_answer(callback, "ℹ️ No hay solicitudes pendientes para procesar.")


@router.callback_query(F.data == "view_pending_requests")
async def view_pending_requests(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Ver solicitudes pendientes detalladas."""
    if not await is_admin(callback.from_user.id, session):
        await safe_answer(callback, "❌ No tienes permisos de administrador.")
        return
    
    from database.models import PendingChannelRequest
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    # Obtener solicitudes pendientes
    stmt = select(PendingChannelRequest).where(
        PendingChannelRequest.approved == False
    ).order_by(PendingChannelRequest.request_timestamp.desc()).limit(10)
    
    result = await session.execute(stmt)
    pending_requests = result.scalars().all()
    
    if not pending_requests:
        await safe_answer(callback, "ℹ️ No hay solicitudes pendientes.")
        return
    
    free_service = FreeChannelService(session, bot)
    wait_minutes = await free_service.get_wait_time_minutes()
    
    text = "📋 **Solicitudes Pendientes** (últimas 10):\n\n"
    
    for req in pending_requests:
        time_passed = datetime.utcnow() - req.request_timestamp
        time_remaining = timedelta(minutes=wait_minutes) - time_passed
        
        if time_remaining.total_seconds() > 0:
            remaining_minutes = int(time_remaining.total_seconds() / 60)
            status = f"⏳ {remaining_minutes}min restantes"
        else:
            status = "✅ Listo para aprobar"
        
        text += (
            f"👤 Usuario ID: `{req.user_id}`\n"
            f"📅 Solicitado: {req.request_timestamp.strftime('%d/%m %H:%M')}\n"
            f"📊 Estado: {status}\n"
            f"📱 Mensaje social: {'✅' if req.social_media_message_sent else '❌'}\n\n"
        )
    
    await safe_edit(callback, text)