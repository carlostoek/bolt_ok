"""
Handler administrativo para configurar la imagen de Lucien en el onboarding.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BotConfig
from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb

router = Router()


class LucienConfigStates(StatesGroup):
    waiting_for_image = State()


@router.callback_query(F.data == "admin_lucien_config")
async def lucien_config_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Menú de configuración de Lucien para onboarding.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    # Obtener configuración actual
    config = await session.get(BotConfig, 1)
    current_image = config.lucien_image_file_id if config else None
    
    status = "✅ Configurada" if current_image else "❌ No configurada"
    
    text = (
        "🎭 <b>Configuración de Lucien</b>\n\n"
        f"📸 <b>Imagen actual:</b> {status}\n\n"
        "La imagen de Lucien se envía cuando los usuarios solicitan acceso al canal gratuito.\n\n"
        "👇 <b>Opciones disponibles:</b>"
    )
    
    keyboard = [
        [{"text": "📸 Configurar/Cambiar imagen", "callback_data": "set_lucien_image"}],
        [{"text": "🗑️ Eliminar imagen", "callback_data": "remove_lucien_image"}] if current_image else [],
        [{"text": "🧪 Probar mensaje con imagen", "callback_data": "test_lucien_message"}] if current_image else [],
        [{"text": "🔙 Volver", "callback_data": "admin_config"}]
    ]
    
    # Filtrar filas vacías
    keyboard = [row for row in keyboard if row]
    
    await update_menu(
        callback,
        text,
        {"inline_keyboard": keyboard},
        session,
        "admin_lucien_config"
    )
    await callback.answer()


@router.callback_query(F.data == "set_lucien_image")
async def set_lucien_image(callback: CallbackQuery, state: FSMContext):
    """
    Solicitar imagen de Lucien al administrador.
    """
    if not await is_admin(callback.from_user.id):
        return await callback.answer()
    
    await callback.message.edit_text(
        "🎭 <b>Configurar imagen de Lucien</b>\n\n"
        "📸 Por favor, envía la imagen de Lucien que quieres usar en los mensajes de onboarding.\n\n"
        "💡 <i>La imagen debe ser clara y representativa del personaje de Lucien como asistente de Diana.</i>\n\n"
        "❌ <b>/cancel</b> para cancelar",
        parse_mode="HTML",
        reply_markup=get_back_kb("admin_lucien_config")
    )
    
    await state.set_state(LucienConfigStates.waiting_for_image)
    await callback.answer()


@router.message(LucienConfigStates.waiting_for_image, F.photo)
async def receive_lucien_image(message: Message, state: FSMContext, session: AsyncSession):
    """
    Recibir y guardar la imagen de Lucien.
    """
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        # Obtener el file_id de la imagen con mejor calidad
        photo = message.photo[-1]  # La última es la de mejor calidad
        file_id = photo.file_id
        
        # Guardar en la base de datos
        config = await session.get(BotConfig, 1)
        if not config:
            config = BotConfig(id=1)
            session.add(config)
        
        config.lucien_image_file_id = file_id
        await session.commit()
        
        # Confirmar configuración
        await message.reply(
            "✅ <b>Imagen de Lucien configurada correctamente!</b>\n\n"
            f"📸 <b>File ID:</b> <code>{file_id}</code>\n\n"
            "🎭 La imagen se enviará automáticamente en los mensajes de onboarding.\n\n"
            "👇 Usa el menú para probar el mensaje:",
            parse_mode="HTML",
            reply_markup={"inline_keyboard": [[
                {"text": "🧪 Probar mensaje", "callback_data": "test_lucien_message"},
                {"text": "🔙 Volver al menú", "callback_data": "admin_lucien_config"}
            ]]}
        )
        
    except Exception as e:
        await message.reply(
            f"❌ Error configurando la imagen: {e}",
            reply_markup=get_back_kb("admin_lucien_config")
        )
    
    await state.clear()


@router.callback_query(F.data == "remove_lucien_image")
async def remove_lucien_image(callback: CallbackQuery, session: AsyncSession):
    """
    Eliminar la imagen de Lucien configurada.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    try:
        config = await session.get(BotConfig, 1)
        if config:
            config.lucien_image_file_id = None
            await session.commit()
        
        await callback.message.edit_text(
            "🗑️ <b>Imagen de Lucien eliminada</b>\n\n"
            "📸 Los mensajes de onboarding se enviarán solo con texto.\n\n"
            "👇 Puedes configurar una nueva imagen:",
            parse_mode="HTML",
            reply_markup={"inline_keyboard": [[
                {"text": "📸 Configurar nueva imagen", "callback_data": "set_lucien_image"},
                {"text": "🔙 Volver al menú", "callback_data": "admin_lucien_config"}
            ]]}
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Error eliminando la imagen: {e}",
            reply_markup=get_back_kb("admin_lucien_config")
        )
    
    await callback.answer("✅ Imagen eliminada")


@router.callback_query(F.data == "test_lucien_message")
async def test_lucien_message(callback: CallbackQuery, session: AsyncSession):
    """
    Enviar mensaje de prueba con la imagen de Lucien.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    try:
        config = await session.get(BotConfig, 1)
        if not config or not config.lucien_image_file_id:
            await callback.answer("❌ No hay imagen configurada", show_alert=True)
            return
        
        # Enviar mensaje de prueba
        test_message = (
            "🧪 <b>MENSAJE DE PRUEBA</b>\n\n"
            "🎭 <b>¡Hola Administrador!</b>\n\n"
            "Soy <b>Lucien</b>, asistente personal de Diana.\n\n"
            "🔍 <i>He recibido tu solicitud para unirte a nuestro canal gratuito...</i>\n\n"
            "⏰ <b>El proceso de evaluación toma aproximadamente 15 minutos.</b>\n\n"
            "🌟 <i>Tip: Los usuarios que siguen a Diana en sus redes sociales suelen ser aprobados más rápido...</i>\n\n"
            "📱 <b>Síguenos mientras esperas:</b>\n"
            "• Instagram: @diana_oficial\n"
            "• TikTok: @diana_content\n"
            "• Twitter: @diana_updates\n\n"
            "<i>Te mantendré informado del progreso...</i> 💫"
        )
        
        await callback.bot.send_photo(
            callback.from_user.id,
            photo=config.lucien_image_file_id,
            caption=test_message,
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Mensaje de prueba enviado")
        
    except Exception as e:
        await callback.answer(f"❌ Error enviando prueba: {e}", show_alert=True)


@router.message(LucienConfigStates.waiting_for_image, F.text)
async def handle_text_instead_of_image(message: Message, state: FSMContext):
    """
    Manejar cuando se envía texto en lugar de imagen.
    """
    if message.text and message.text.lower() in ['/cancel', 'cancel']:
        await message.reply(
            "❌ Configuración cancelada.",
            reply_markup=get_back_kb("admin_lucien_config")
        )
        await state.clear()
        return
    
    await message.reply(
        "❌ <b>Por favor, envía una imagen (no texto)</b>\n\n"
        "📸 Necesito la imagen de Lucien para el onboarding.\n\n"
        "❌ <b>/cancel</b> para cancelar",
        parse_mode="HTML"
    )