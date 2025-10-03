"""
Admin Handler para Gift Service

Permite a los admins:
- Enviar regalos manuales por eventos
- Ver estadísticas de regalos
- Ver historial de regalos enviados
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.admin_state import AdminGiftStates
from services.gift_service import GiftService, GIFT_MESSAGES
from services.user_service import UserService
from keyboards.admin_gift_kb import (
    get_gift_main_keyboard,
    get_event_type_keyboard,
    get_gift_sets_keyboard,
    get_custom_message_keyboard,
    get_confirm_gift_keyboard
)
from keyboards.common import get_back_kb

logger = logging.getLogger(__name__)
router = Router()


# ========== MENÚ PRINCIPAL ==========

@router.callback_query(F.data == "gift_main")
async def show_gift_main_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Muestra el menú principal del Gift Service"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear()

    text = (
        "🎁 **Gift Service**\n\n"
        "Sistema de regalos estratégicos para usuarios.\n\n"
        "Envía contenido especial por:\n"
        "• Ganar subastas 🏆\n"
        "• Compras en tienda 🛍️\n"
        "• Alcanzar niveles 🎯\n"
        "• Sorpresas espontáneas 💝\n"
        "• Y más..."
    )

    await callback.message.edit_text(text, reply_markup=get_gift_main_keyboard())
    await callback.answer()


# ========== ENVIAR REGALO ==========

@router.callback_query(F.data == "gift_send")
async def start_send_gift(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el proceso de enviar un regalo"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "🎁 **Enviar Regalo**\n\n"
        "**Paso 1/4:** Selecciona el tipo de evento:"
    )

    await callback.message.edit_text(text, reply_markup=get_event_type_keyboard())
    await state.set_state(AdminGiftStates.selecting_event_type)
    await callback.answer()


@router.callback_query(AdminGiftStates.selecting_event_type, F.data.startswith("gift_event_"))
async def select_event_type(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario selecciona el tipo de evento"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    event_type = callback.data.split("gift_event_")[-1]
    await state.update_data(event_type=event_type)

    # Nombres bonitos para mostrar
    event_names = {
        "auction_won": "🏆 Ganó Subasta",
        "shop_purchase": "🛍️ Compró en Tienda",
        "level_reached": "🎯 Alcanzó Nivel",
        "surprise": "💝 Sorpresa Espontánea",
        "loyalty": "💎 Recompensa Lealtad",
        "birthday": "🎂 Cumpleaños",
        "custom": "✨ Personalizado"
    }

    text = (
        f"✅ Evento: **{event_names.get(event_type, event_type)}**\n\n"
        "**Paso 2/4:** Ingresa el **user_id** del destinatario:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("gift_main"))
    await state.set_state(AdminGiftStates.entering_user_id)
    await callback.answer()


@router.message(AdminGiftStates.entering_user_id)
async def process_user_id(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el user_id ingresado"""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ingresa un user_id numérico válido:")
        return

    # Verificar que el usuario existe
    user_service = UserService(session)
    user = await user_service.get_user(user_id)

    if not user:
        await message.answer(
            f"❌ Usuario {user_id} no encontrado.\n"
            "Intenta con otro user_id:"
        )
        return

    await state.update_data(target_user_id=user_id, target_username=user.username)

    # Obtener content sets disponibles para regalos
    gift_service = GiftService(session)
    sets = await gift_service.list_available_gift_sets()

    if not sets:
        await message.answer(
            "❌ No hay content sets disponibles para regalar.\n\n"
            "Crea un content set con tier='gift' primero desde el CMS.",
            reply_markup=get_back_kb("gift_main")
        )
        await state.clear()
        return

    text = (
        f"✅ Usuario: `{user_id}` (@{user.username or 'sin username'})\n\n"
        "**Paso 3/4:** Selecciona el content set a enviar:"
    )

    await message.answer(text, reply_markup=get_gift_sets_keyboard(sets))
    await state.set_state(AdminGiftStates.selecting_content_set)


@router.callback_query(AdminGiftStates.selecting_content_set, F.data.startswith("gift_select_"))
async def select_content_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario selecciona el content set"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("gift_select_")[-1]
    await state.update_data(content_set_id=set_id)

    # Verificar si el evento requiere datos adicionales
    data = await state.get_data()
    event_type = data.get("event_type")

    # Eventos que requieren contexto adicional
    needs_context = {
        "auction_won": "Ingresa el **nombre de la subasta** ganada:",
        "shop_purchase": "Ingresa el **nombre del item** comprado:",
        "level_reached": "Ingresa el **nivel** alcanzado (número):",
        "loyalty": "Ingresa los **días activos** (número):"
    }

    if event_type in needs_context:
        text = (
            f"✅ Content set: `{set_id}`\n\n"
            f"**Paso 4a/4:** {needs_context[event_type]}"
        )
        await callback.message.edit_text(text, reply_markup=get_back_kb("gift_main"))
        await state.set_state(AdminGiftStates.entering_context_data)
    else:
        # Preguntar si quiere mensaje personalizado
        text = (
            f"✅ Content set: `{set_id}`\n\n"
            "**Paso 4/4:** ¿Deseas agregar un mensaje personalizado o usar el template?"
        )
        await callback.message.edit_text(text, reply_markup=get_custom_message_keyboard())
        await state.set_state(AdminGiftStates.entering_custom_message)

    await callback.answer()


@router.message(AdminGiftStates.entering_context_data)
async def process_context_data(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa datos de contexto adicionales"""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    event_type = data.get("event_type")
    context_value = message.text.strip()

    # Mapear el valor según el tipo de evento
    context_data = {}
    if event_type == "auction_won":
        context_data = {"item_name": context_value}
    elif event_type == "shop_purchase":
        context_data = {"item_name": context_value}
    elif event_type == "level_reached":
        try:
            level = int(context_value)
            context_data = {"level": level}
        except ValueError:
            await message.answer("❌ Ingresa un número válido para el nivel:")
            return
    elif event_type == "loyalty":
        try:
            days = int(context_value)
            context_data = {"days": days}
        except ValueError:
            await message.answer("❌ Ingresa un número válido para los días:")
            return

    await state.update_data(context_data=context_data)

    # Preguntar por mensaje personalizado
    text = (
        "✅ Datos guardados\n\n"
        "**Paso 4b/4:** ¿Deseas agregar un mensaje personalizado o usar el template?"
    )

    await message.answer(text, reply_markup=get_custom_message_keyboard())
    await state.set_state(AdminGiftStates.entering_custom_message)


@router.callback_query(AdminGiftStates.entering_custom_message, F.data == "gift_custom_yes")
async def request_custom_message(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario quiere escribir un mensaje personalizado"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "✍️ **Mensaje Personalizado**\n\n"
        "Escribe el mensaje que acompañará el regalo.\n\n"
        "Este mensaje reemplazará el template por defecto."
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("gift_main"))
    await state.update_data(wants_custom_message=True)
    await callback.answer()


@router.message(AdminGiftStates.entering_custom_message)
async def process_custom_message(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el mensaje personalizado"""
    if not await is_admin(message.from_user.id, session):
        return

    custom_message = message.text.strip()
    await state.update_data(custom_message=custom_message)

    # Mostrar preview
    await show_gift_preview(message, state, session)


@router.callback_query(AdminGiftStates.entering_custom_message, F.data == "gift_custom_no")
async def skip_custom_message(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario usa el template por defecto"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(custom_message=None)

    # Mostrar preview
    await show_gift_preview(callback.message, state, session)
    await callback.answer()


async def show_gift_preview(message: Message, state: FSMContext, session: AsyncSession):
    """Muestra un preview del regalo antes de enviarlo"""
    data = await state.get_data()

    event_names = {
        "auction_won": "🏆 Ganó Subasta",
        "shop_purchase": "🛍️ Compró en Tienda",
        "level_reached": "🎯 Alcanzó Nivel",
        "surprise": "💝 Sorpresa",
        "loyalty": "💎 Lealtad",
        "birthday": "🎂 Cumpleaños",
        "custom": "✨ Personalizado"
    }

    event_type = data.get("event_type")
    user_id = data.get("target_user_id")
    username = data.get("target_username")
    set_id = data.get("content_set_id")
    custom_message = data.get("custom_message")
    context_data = data.get("context_data", {})

    text = (
        "📋 **PREVIEW DEL REGALO**\n\n"
        f"**Destinatario:** {user_id} (@{username or 'sin username'})\n"
        f"**Evento:** {event_names.get(event_type)}\n"
        f"**Content Set:** `{set_id}`\n"
    )

    if context_data:
        text += f"**Contexto:** {context_data}\n"

    if custom_message:
        text += f"\n**Mensaje personalizado:**\n{custom_message[:100]}...\n"
    else:
        text += f"\n**Mensaje:** Template por defecto\n"

    text += "\n¿Enviar este regalo?"

    await message.answer(text, reply_markup=get_confirm_gift_keyboard())
    await state.set_state(AdminGiftStates.confirming_gift)


@router.callback_query(AdminGiftStates.confirming_gift, F.data == "gift_confirm_send")
async def confirm_send_gift(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    """Confirma y envía el regalo"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()

    await callback.answer("⏳ Enviando regalo...", show_alert=True)

    try:
        gift_service = GiftService(session)

        success = await gift_service.send_gift(
            user_id=data.get("target_user_id"),
            content_set_id=data.get("content_set_id"),
            event_type=data.get("event_type"),
            bot=bot,
            context_data=data.get("context_data"),
            custom_message=data.get("custom_message"),
            sent_by_admin=True
        )

        if success:
            text = (
                "✅ **Regalo enviado exitosamente!**\n\n"
                f"Usuario: {data.get('target_user_id')}\n"
                f"Set: `{data.get('content_set_id')}`\n"
                f"Evento: {data.get('event_type')}"
            )
            await callback.message.edit_text(text, reply_markup=get_gift_main_keyboard())
            await state.clear()
        else:
            await callback.message.edit_text(
                "❌ Error enviando el regalo. Revisa los logs.",
                reply_markup=get_gift_main_keyboard()
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Error enviando regalo: {e}")
        await callback.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_gift_main_keyboard()
        )
        await state.clear()


# ========== ESTADÍSTICAS ==========

@router.callback_query(F.data == "gift_stats")
async def show_gift_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas de regalos"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        gift_service = GiftService(session)
        stats = await gift_service.get_gift_stats()

        text = (
            "📊 **Estadísticas de Regalos**\n\n"
            f"**Total enviado:** {stats['total_gifts']} regalos\n"
            f"**Usuarios únicos:** {stats['unique_users']}\n"
            f"**Enviados por admin:** {stats['admin_gifts']}\n"
            f"**Automáticos:** {stats['automatic_gifts']}\n\n"
            "**Por tipo de evento:**\n"
        )

        event_names = {
            "auction_won": "🏆 Subastas",
            "shop_purchase": "🛍️ Tienda",
            "level_reached": "🎯 Niveles",
            "surprise": "💝 Sorpresas",
            "loyalty": "💎 Lealtad",
            "birthday": "🎂 Cumpleaños",
            "custom": "✨ Personalizados",
            "automatic": "🤖 Journey"
        }

        for event_type, count in stats['gifts_by_type'].items():
            name = event_names.get(event_type, event_type)
            text += f"  {name}: {count}\n"

        await callback.message.edit_text(text, reply_markup=get_back_kb("gift_main"))
        await callback.answer()

    except Exception as e:
        logger.error(f"Error mostrando estadísticas: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


# ========== HISTORIAL ==========

@router.callback_query(F.data == "gift_history")
async def show_gift_history(callback: CallbackQuery, session: AsyncSession):
    """Muestra historial reciente de regalos"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        from sqlalchemy import select
        from database.models import GiftRecord

        # Obtener últimos 10 regalos
        stmt = (
            select(GiftRecord)
            .order_by(GiftRecord.sent_at.desc())
            .limit(10)
        )

        result = await session.execute(stmt)
        records = result.scalars().all()

        if not records:
            text = "📋 **Historial de Regalos**\n\nNo hay regalos registrados aún."
        else:
            text = "📋 **Historial Reciente**\n\n"

            for record in records:
                date = record.sent_at.strftime("%Y-%m-%d %H:%M")
                by = "👤 Admin" if record.sent_by_admin else "🤖 Auto"
                text += (
                    f"• {date}\n"
                    f"  Usuario: {record.user_id}\n"
                    f"  Set: `{record.content_set_id}`\n"
                    f"  Tipo: {record.trigger_type}\n"
                    f"  {by}\n\n"
                )

        await callback.message.edit_text(text, reply_markup=get_back_kb("gift_main"))
        await callback.answer()

    except Exception as e:
        logger.error(f"Error mostrando historial: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)
