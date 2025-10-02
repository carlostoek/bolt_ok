"""
Admin Handler para Content Management System (CMS)

Permite a los admins:
- Subir sets de contenido (fotos, videos, audios)
- Listar y buscar sets existentes
- Enviar sets a usuarios
- Ver estadísticas de distribución
"""
import logging
import json
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.admin_state import AdminContentSetStates
from services.content_service import ContentService
from keyboards.admin_content_cms_kb import (
    get_cms_main_keyboard,
    get_content_type_keyboard,
    get_tier_keyboard,
    get_category_keyboard,
    get_archetype_keyboard,
    get_file_upload_keyboard,
    get_sets_list_keyboard,
    get_set_actions_keyboard,
    get_confirm_keyboard
)
from keyboards.common import get_back_kb

logger = logging.getLogger(__name__)
router = Router()


# ========== MENÚ PRINCIPAL CMS ==========

@router.callback_query(F.data == "cms_main")
async def show_cms_main_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Muestra el menú principal del CMS"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear()

    text = (
        "📦 **Content Management System**\n\n"
        "Sistema de gestión de contenido multimedia para el journey del usuario.\n\n"
        "Aquí puedes subir, organizar y distribuir sets de fotos, videos y audios."
    )

    await callback.message.edit_text(text, reply_markup=get_cms_main_keyboard())
    await callback.answer()


# ========== WIZARD DE CREACIÓN DE SET ==========

@router.callback_query(F.data == "cms_create_set")
async def start_create_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el wizard de creación de set"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "📤 **Crear Nuevo Content Set**\n\n"
        "**Paso 1/7:** Ingresa el ID único del set\n\n"
        "El ID debe ser en snake_case (ej: `primera_mirada`, `day_7_gift`)\n"
        "Este ID se usará para identificar el set en el sistema."
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("cms_main"))
    await state.set_state(AdminContentSetStates.entering_set_id)
    await callback.answer()


@router.message(AdminContentSetStates.entering_set_id)
async def process_set_id(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el ID del set"""
    if not await is_admin(message.from_user.id, session):
        return

    set_id = message.text.strip().lower().replace(" ", "_")

    # Validar formato
    if not set_id.replace("_", "").isalnum():
        await message.answer(
            "❌ El ID solo puede contener letras, números y guiones bajos.\n"
            "Intenta de nuevo:"
        )
        return

    # Verificar si ya existe
    content_service = ContentService(session)
    existing = await content_service.get_content_set(set_id)
    if existing:
        await message.answer(
            f"❌ Ya existe un set con el ID `{set_id}`.\n"
            "Elige otro ID:"
        )
        return

    await state.update_data(set_id=set_id)

    text = (
        f"✅ ID: `{set_id}`\n\n"
        "**Paso 2/7:** Ingresa el nombre display del set\n\n"
        "Este es el nombre que verán los usuarios (ej: `Primera Mirada`, `Regalo Día 7`)"
    )

    await message.answer(text, reply_markup=get_back_kb("cms_main"))
    await state.set_state(AdminContentSetStates.entering_name)


@router.message(AdminContentSetStates.entering_name)
async def process_set_name(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el nombre del set"""
    if not await is_admin(message.from_user.id, session):
        return

    name = message.text.strip()

    if len(name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres. Intenta de nuevo:")
        return

    await state.update_data(name=name)

    text = (
        f"✅ Nombre: **{name}**\n\n"
        "**Paso 3/7:** Ingresa una descripción interna (opcional)\n\n"
        "Esta descripción es solo para ti como admin.\n"
        "Envía `-` si no quieres agregar descripción."
    )

    await message.answer(text, reply_markup=get_back_kb("cms_main"))
    await state.set_state(AdminContentSetStates.entering_description)


@router.message(AdminContentSetStates.entering_description)
async def process_set_description(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa la descripción del set"""
    if not await is_admin(message.from_user.id, session):
        return

    description = message.text.strip()
    if description == "-":
        description = None

    await state.update_data(description=description)

    text = (
        "✅ Descripción guardada\n\n"
        "**Paso 4/7:** Selecciona el tipo de contenido"
    )

    await message.answer(text, reply_markup=get_content_type_keyboard())
    await state.set_state(AdminContentSetStates.selecting_type)


@router.callback_query(AdminContentSetStates.selecting_type, F.data.startswith("cms_type_"))
async def process_content_type(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa el tipo de contenido seleccionado"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    content_type = callback.data.split("cms_type_")[-1]
    await state.update_data(content_type=content_type)

    type_names = {
        "photo_set": "Set de Fotos 📸",
        "video": "Video 🎬",
        "audio": "Audio 🎵",
        "mixed": "Mixto 🎭"
    }

    text = (
        f"✅ Tipo: **{type_names.get(content_type)}**\n\n"
        "**Paso 5/7:** Selecciona el tier (nivel de acceso)"
    )

    await callback.message.edit_text(text, reply_markup=get_tier_keyboard())
    await state.set_state(AdminContentSetStates.selecting_tier)
    await callback.answer()


@router.callback_query(AdminContentSetStates.selecting_tier, F.data.startswith("cms_tier_"))
async def process_tier(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa el tier seleccionado"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    tier = callback.data.split("cms_tier_")[-1]
    await state.update_data(tier=tier)

    tier_names = {
        "free": "Free 🆓",
        "vip": "VIP ⭐",
        "gift": "Gift/Milestone 🎁",
        "premium": "Premium 💎"
    }

    text = (
        f"✅ Tier: **{tier_names.get(tier)}**\n\n"
        "**Paso 6/7:** Selecciona la categoría (opcional)"
    )

    await callback.message.edit_text(text, reply_markup=get_category_keyboard())
    await state.set_state(AdminContentSetStates.selecting_category)
    await callback.answer()


@router.callback_query(AdminContentSetStates.selecting_category, F.data.startswith("cms_cat_"))
async def process_category(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa la categoría seleccionada"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    category = callback.data.split("cms_cat_")[-1]
    if category == "skip":
        category = None

    await state.update_data(category=category)

    text = (
        f"✅ Categoría: **{category or 'Sin categoría'}**\n\n"
        "**Paso 7/8:** Selecciona el arquetipo objetivo"
    )

    await callback.message.edit_text(text, reply_markup=get_archetype_keyboard())
    await state.set_state(AdminContentSetStates.selecting_archetype)
    await callback.answer()


@router.callback_query(AdminContentSetStates.selecting_archetype, F.data.startswith("cms_arch_"))
async def process_archetype(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa el arquetipo seleccionado"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    archetype = callback.data.split("cms_arch_")[-1]
    await state.update_data(for_archetype=archetype)

    data = await state.get_data()

    arch_names = {
        "luz": "Luz (Diurno) ☀️",
        "sombra": "Sombra (Nocturno) 🌙",
        "all": "Todos 🌐"
    }

    text = (
        f"✅ Arquetipo: **{arch_names.get(archetype)}**\n\n"
        "**Paso 8/8:** Sube los archivos\n\n"
    )

    # Instrucciones según tipo
    content_type = data.get("content_type")
    if content_type == "photo_set":
        text += "📸 Sube todas las fotos del set (una por una o en grupo)\n"
    elif content_type == "video":
        text += "🎬 Sube el video\n"
    elif content_type == "audio":
        text += "🎵 Sube el archivo de audio\n"
    elif content_type == "mixed":
        text += "🎭 Sube las fotos y videos en el orden que quieras\n"

    text += "\nCuando termines, presiona **✅ Listo**"

    await callback.message.edit_text(text, reply_markup=get_file_upload_keyboard())
    await state.update_data(file_ids=[])  # Inicializar lista vacía
    await state.set_state(AdminContentSetStates.uploading_files)
    await callback.answer()


@router.message(AdminContentSetStates.uploading_files, F.photo)
async def process_photo_upload(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa foto subida"""
    if not await is_admin(message.from_user.id, session):
        return

    # Obtener el file_id de la foto de mayor resolución
    file_id = message.photo[-1].file_id

    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    file_ids.append(file_id)
    await state.update_data(file_ids=file_ids)

    await message.answer(f"✅ Foto {len(file_ids)} guardada")


@router.message(AdminContentSetStates.uploading_files, F.video)
async def process_video_upload(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa video subido"""
    if not await is_admin(message.from_user.id, session):
        return

    file_id = message.video.file_id

    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    file_ids.append(file_id)
    await state.update_data(file_ids=file_ids)

    await message.answer(f"✅ Video {len(file_ids)} guardado")


@router.message(AdminContentSetStates.uploading_files, F.audio)
async def process_audio_upload(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa audio subido"""
    if not await is_admin(message.from_user.id, session):
        return

    file_id = message.audio.file_id

    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    file_ids.append(file_id)
    await state.update_data(file_ids=file_ids)

    await message.answer(f"✅ Audio {len(file_ids)} guardado")


@router.callback_query(AdminContentSetStates.uploading_files, F.data == "cms_files_done")
async def finish_file_upload(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Termina la subida de archivos y muestra preview"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()
    file_ids = data.get("file_ids", [])

    if not file_ids:
        await callback.answer("❌ Debes subir al menos un archivo", show_alert=True)
        return

    # Preparar preview
    type_names = {
        "photo_set": "Set de Fotos 📸",
        "video": "Video 🎬",
        "audio": "Audio 🎵",
        "mixed": "Mixto 🎭"
    }

    tier_names = {
        "free": "Free 🆓",
        "vip": "VIP ⭐",
        "gift": "Gift/Milestone 🎁",
        "premium": "Premium 💎"
    }

    arch_names = {
        "luz": "Luz ☀️",
        "sombra": "Sombra 🌙",
        "all": "Todos 🌐"
    }

    text = (
        "📋 **PREVIEW DEL CONTENT SET**\n\n"
        f"**ID:** `{data.get('set_id')}`\n"
        f"**Nombre:** {data.get('name')}\n"
        f"**Descripción:** {data.get('description') or 'Sin descripción'}\n"
        f"**Tipo:** {type_names.get(data.get('content_type'))}\n"
        f"**Tier:** {tier_names.get(data.get('tier'))}\n"
        f"**Categoría:** {data.get('category') or 'Sin categoría'}\n"
        f"**Arquetipo:** {arch_names.get(data.get('for_archetype'))}\n"
        f"**Archivos:** {len(file_ids)} archivo(s)\n\n"
        "¿Crear este content set?"
    )

    await callback.message.edit_text(text, reply_markup=get_confirm_keyboard("create"))
    await state.set_state(AdminContentSetStates.confirming_creation)
    await callback.answer()


@router.callback_query(AdminContentSetStates.confirming_creation, F.data == "cms_confirm_create")
async def confirm_create_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    """Confirma y crea el content set en BD"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()

    try:
        content_service = ContentService(session)

        content_set = await content_service.create_content_set(
            id=data.get("set_id"),
            name=data.get("name"),
            type=data.get("content_type"),
            tier=data.get("tier"),
            file_ids=data.get("file_ids"),
            description=data.get("description"),
            category=data.get("category"),
            for_archetype=data.get("for_archetype", "all")
        )

        text = (
            f"✅ **Content Set creado exitosamente!**\n\n"
            f"ID: `{content_set.id}`\n"
            f"Nombre: {content_set.name}\n"
            f"Archivos: {len(content_set.file_ids)}\n\n"
            "El set ya está disponible para enviarse a usuarios."
        )

        await callback.message.edit_text(text, reply_markup=get_cms_main_keyboard())
        await state.clear()
        await callback.answer("¡Set creado!", show_alert=True)

    except Exception as e:
        logger.error(f"Error creando content set: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


# ========== LISTAR SETS ==========

@router.callback_query(F.data == "cms_list_sets")
async def list_content_sets(callback: CallbackQuery, session: AsyncSession):
    """Lista todos los content sets"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    content_service = ContentService(session)
    sets = await content_service.list_content_sets(active_only=True)

    if not sets:
        text = "📋 **Content Sets**\n\nNo hay content sets creados aún."
        await callback.message.edit_text(text, reply_markup=get_cms_main_keyboard())
        await callback.answer()
        return

    text = f"📋 **Content Sets** ({len(sets)} sets)\n\nSelecciona un set para ver detalles:"

    await callback.message.edit_text(text, reply_markup=get_sets_list_keyboard(sets))
    await callback.answer()


@router.callback_query(F.data.startswith("cms_list_page_"))
async def navigate_sets_list(callback: CallbackQuery, session: AsyncSession):
    """Navega entre páginas de la lista"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    page = int(callback.data.split("cms_list_page_")[-1])

    content_service = ContentService(session)
    sets = await content_service.list_content_sets(active_only=True)

    text = f"📋 **Content Sets** ({len(sets)} sets)\n\nSelecciona un set para ver detalles:"

    await callback.message.edit_text(text, reply_markup=get_sets_list_keyboard(sets, page=page))
    await callback.answer()


@router.callback_query(F.data.startswith("cms_view_set_"))
async def view_content_set(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles de un content set"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_view_set_")[-1]

    content_service = ContentService(session)
    content_set = await content_service.get_content_set(set_id)

    if not content_set:
        await callback.answer("Set no encontrado", show_alert=True)
        return

    type_names = {
        "photo_set": "Set de Fotos 📸",
        "video": "Video 🎬",
        "audio": "Audio 🎵",
        "mixed": "Mixto 🎭"
    }

    tier_names = {
        "free": "Free 🆓",
        "vip": "VIP ⭐",
        "gift": "Gift 🎁",
        "premium": "Premium 💎"
    }

    text = (
        f"📦 **{content_set.name}**\n\n"
        f"**ID:** `{content_set.id}`\n"
        f"**Tipo:** {type_names.get(content_set.type)}\n"
        f"**Tier:** {tier_names.get(content_set.tier)}\n"
        f"**Categoría:** {content_set.category or 'Sin categoría'}\n"
        f"**Arquetipo:** {content_set.for_archetype}\n"
        f"**Archivos:** {len(content_set.file_ids)}\n"
        f"**Descripción:** {content_set.description or 'Sin descripción'}\n"
        f"**Creado:** {content_set.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"**Activo:** {'✅ Sí' if content_set.is_active else '❌ No'}\n\n"
        "¿Qué acción deseas realizar?"
    )

    await callback.message.edit_text(text, reply_markup=get_set_actions_keyboard(set_id))
    await callback.answer()


# ========== ENVIAR SET A USUARIO ==========

@router.callback_query(F.data.startswith("cms_send_"))
async def start_send_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el proceso de enviar un set a un usuario"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_send_")[-1]
    await state.update_data(set_to_send=set_id)

    text = (
        "📨 **Enviar Content Set a Usuario**\n\n"
        f"Set: `{set_id}`\n\n"
        "Envía el **user_id** del usuario destino:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("cms_main"))
    await state.set_state(AdminContentSetStates.selecting_user_to_send)
    await callback.answer()


@router.message(AdminContentSetStates.selecting_user_to_send)
async def process_user_to_send(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el user_id ingresado"""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ingresa un user_id numérico válido:")
        return

    await state.update_data(target_user_id=user_id)

    text = (
        f"✅ Usuario: `{user_id}`\n\n"
        "Ingresa el **mensaje de contexto** que acompañará el contenido.\n\n"
        "Este mensaje es narrativo (de Lucien o Diana) y se enviará ANTES del contenido.\n"
        "Envía `-` si no quieres mensaje de contexto."
    )

    await message.answer(text, reply_markup=get_back_kb("cms_main"))
    await state.set_state(AdminContentSetStates.entering_context_message)


@router.message(AdminContentSetStates.entering_context_message)
async def process_context_message(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el mensaje de contexto"""
    if not await is_admin(message.from_user.id, session):
        return

    context_message = message.text.strip()
    if context_message == "-":
        context_message = ""

    await state.update_data(context_message=context_message)

    data = await state.get_data()

    text = (
        "📨 **Confirmar Envío**\n\n"
        f"**Set:** `{data.get('set_to_send')}`\n"
        f"**Usuario:** `{data.get('target_user_id')}`\n"
        f"**Mensaje:** {context_message or 'Sin mensaje'}\n\n"
        "¿Enviar ahora?"
    )

    await message.answer(text, reply_markup=get_confirm_keyboard("send"))
    await state.set_state(AdminContentSetStates.confirming_send)


@router.callback_query(AdminContentSetStates.confirming_send, F.data == "cms_confirm_send")
async def confirm_send_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    """Confirma y envía el set al usuario"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()

    try:
        content_service = ContentService(session)

        success = await content_service.send_content_set(
            user_id=data.get("target_user_id"),
            set_id=data.get("set_to_send"),
            context_message=data.get("context_message", ""),
            bot=bot,
            trigger_type="manual",
            sent_by_admin=True
        )

        if success:
            text = (
                "✅ **Content set enviado exitosamente!**\n\n"
                f"Set: `{data.get('set_to_send')}`\n"
                f"Usuario: `{data.get('target_user_id')}`"
            )
            await callback.message.edit_text(text, reply_markup=get_cms_main_keyboard())
            await state.clear()
            await callback.answer("¡Enviado!", show_alert=True)
        else:
            await callback.answer("❌ Error enviando el set. Revisa los logs.", show_alert=True)

    except Exception as e:
        logger.error(f"Error enviando content set: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


# ========== ESTADÍSTICAS ==========

@router.callback_query(F.data.startswith("cms_stats_"))
async def show_set_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas de un set específico"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_stats_")[-1]

    content_service = ContentService(session)

    # Obtener registros de envío para este set
    from sqlalchemy import select, func
    from database.models import GiftRecord

    stmt = select(
        func.count(GiftRecord.id).label("total_sends"),
        func.count(func.distinct(GiftRecord.user_id)).label("unique_users")
    ).where(GiftRecord.content_set_id == set_id)

    result = await session.execute(stmt)
    stats = result.one()

    text = (
        f"📊 **Estadísticas: {set_id}**\n\n"
        f"**Total enviado:** {stats.total_sends} veces\n"
        f"**Usuarios únicos:** {stats.unique_users}\n"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb(f"cms_view_set_{set_id}"))
    await callback.answer()


# ========== DESACTIVAR/ELIMINAR ==========

@router.callback_query(F.data.startswith("cms_deactivate_"))
async def deactivate_set(callback: CallbackQuery, session: AsyncSession):
    """Desactiva un content set"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_deactivate_")[-1]

    content_service = ContentService(session)
    await content_service.delete_content_set(set_id, soft_delete=True)

    await callback.answer("✅ Set desactivado", show_alert=True)
    await callback.message.edit_text(
        f"✅ Set `{set_id}` desactivado exitosamente.",
        reply_markup=get_cms_main_keyboard()
    )


@router.callback_query(F.data.startswith("cms_delete_"))
async def delete_set(callback: CallbackQuery, session: AsyncSession):
    """Elimina permanentemente un content set"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_delete_")[-1]

    text = (
        f"⚠️ **ELIMINAR PERMANENTEMENTE**\n\n"
        f"Vas a eliminar el set `{set_id}` de la base de datos.\n"
        f"Esta acción NO se puede deshacer.\n\n"
        "¿Estás seguro?"
    )

    await callback.message.edit_text(text, reply_markup=get_confirm_keyboard("delete", set_id))
    await callback.answer()


@router.callback_query(F.data.startswith("cms_confirm_delete_"))
async def confirm_delete_set(callback: CallbackQuery, session: AsyncSession):
    """Confirma eliminación permanente"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    set_id = callback.data.split("cms_confirm_delete_")[-1]

    content_service = ContentService(session)
    await content_service.delete_content_set(set_id, soft_delete=False)

    await callback.answer("✅ Set eliminado permanentemente", show_alert=True)
    await callback.message.edit_text(
        f"✅ Set `{set_id}` eliminado de la base de datos.",
        reply_markup=get_cms_main_keyboard()
    )
