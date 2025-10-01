"""
Panel de Administración de Narrativa
Gestión completa de fragmentos, decisiones y vinculación con productos.
Similar al panel de administración de tienda.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
from database.models import Achievement, LorePiece, ShopItem
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit

logger = logging.getLogger(__name__)
router = Router()

# ==================== ESTADOS FSM ====================

class NarrativeAdminStates(StatesGroup):
    """Estados para la gestión administrativa de narrativa"""

    # Creación de fragmentos
    create_fragment_waiting_key = State()
    create_fragment_waiting_text = State()
    create_fragment_waiting_image_url = State()
    create_fragment_waiting_character = State()
    create_fragment_waiting_level = State()
    create_fragment_waiting_min_besitos = State()
    create_fragment_waiting_reward_besitos = State()
    create_fragment_waiting_required_role = State()

    # Edición de fragmentos
    edit_fragment_waiting_value = State()

    # Creación de decisiones
    create_choice_waiting_text = State()
    create_choice_waiting_destination = State()
    create_choice_waiting_required_besitos = State()
    create_choice_waiting_required_role = State()

    # Edición de decisiones
    edit_choice_waiting_value = State()

    # Vinculación con productos
    link_waiting_fragment = State()
    link_waiting_product = State()


# ==================== MENÚ PRINCIPAL ====================

@router.callback_query(F.data == "admin_narrative_panel")
async def show_narrative_admin_panel(callback: CallbackQuery, session: AsyncSession):
    """Muestra el panel principal de administración de narrativa"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    # Obtener estadísticas
    fragments_stmt = select(func.count()).select_from(StoryFragment)
    fragments_result = await session.execute(fragments_stmt)
    total_fragments = fragments_result.scalar() or 0

    choices_stmt = select(func.count()).select_from(NarrativeChoice)
    choices_result = await session.execute(choices_stmt)
    total_choices = choices_result.scalar() or 0

    users_stmt = select(func.count()).select_from(UserNarrativeState)
    users_result = await session.execute(users_stmt)
    active_users = users_result.scalar() or 0

    text = f"""📖 **Panel de Administración - Narrativa**

📊 **Estadísticas:**
• Fragmentos: {total_fragments}
• Decisiones: {total_choices}
• Usuarios activos: {active_users}

Selecciona una opción:"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Gestionar Fragmentos", callback_data="narrative_admin_fragments")
    builder.button(text="🔀 Gestionar Decisiones", callback_data="narrative_admin_choices")
    builder.button(text="🔗 Vincular Productos", callback_data="narrative_admin_link_products")
    builder.button(text="✅ Validar Narrativa", callback_data="narrative_admin_validate")
    builder.button(text="📊 Estadísticas Detalladas", callback_data="narrative_admin_stats")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    builder.adjust(1)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


# ==================== GESTIÓN DE FRAGMENTOS ====================

@router.callback_query(F.data == "narrative_admin_fragments")
async def show_fragments_management(callback: CallbackQuery, session: AsyncSession):
    """Muestra la lista de fragmentos para gestionar"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    stmt = select(StoryFragment).order_by(StoryFragment.level, StoryFragment.key)
    result = await session.execute(stmt)
    fragments = result.scalars().all()

    text = f"""📚 **Gestión de Fragmentos**

Total: {len(fragments)} fragmentos

Selecciona un fragmento para ver detalles o crear uno nuevo:"""

    builder = InlineKeyboardBuilder()

    # Botón para crear nuevo fragmento
    builder.button(text="➕ Crear Nuevo Fragmento", callback_data="narrative_create_fragment")
    builder.adjust(1)

    # Listar fragmentos existentes
    if fragments:
        for fragment in fragments:
            emoji = "🎩" if fragment.character == "Lucien" else "🌸" if fragment.character == "Diana" else "📖"
            label = f"{emoji} {fragment.key} (Nivel {fragment.level})"
            builder.button(text=label, callback_data=f"narrative_view_fragment:{fragment.id}")
        builder.adjust(1)

    builder.button(text="🔙 Volver", callback_data="admin_narrative_panel")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_view_fragment:"))
async def view_fragment_detail(callback: CallbackQuery, session: AsyncSession):
    """Muestra los detalles de un fragmento específico"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    fragment_id = int(callback.data.split(":")[1])
    fragment = await session.get(StoryFragment, fragment_id)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    # Contar decisiones
    choices_stmt = select(func.count()).select_from(NarrativeChoice).where(
        NarrativeChoice.source_fragment_id == fragment_id
    )
    choices_result = await session.execute(choices_stmt)
    choices_count = choices_result.scalar() or 0

    # Preparar detalles
    emoji = "🎩" if fragment.character == "Lucien" else "🌸" if fragment.character == "Diana" else "📖"

    # Información de imagen
    image_info = "🖼️ Sin imagen"
    if fragment.image_url:
        if fragment.image_url.startswith("http"):
            image_info = "🖼️ Imagen (URL)"
        else:
            image_info = "🖼️ Imagen (Telegram)"

    text = f"""{emoji} **Fragmento: {fragment.key}**

📝 **Texto:**
{fragment.text[:200]}{"..." if len(fragment.text) > 200 else ""}

{image_info}

⚙️ **Configuración:**
• Personaje: {fragment.character}
• Nivel: {fragment.level}
• Besitos mínimos: {fragment.min_besitos}
• Recompensa: {fragment.reward_besitos} besitos
• Rol requerido: {fragment.required_role or "Ninguno"}
• Auto-siguiente: {fragment.auto_next_fragment_key or "No configurado"}

🔀 **Decisiones:** {choices_count}

🕐 **Creado:** {fragment.created_at.strftime("%Y-%m-%d %H:%M") if fragment.created_at else "N/A"}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Fragmento", callback_data=f"narrative_edit_fragment:{fragment_id}")
    builder.button(text="🔀 Gestionar Decisiones", callback_data=f"narrative_manage_choices:{fragment_id}")
    builder.button(text="🎬 Preview", callback_data=f"narrative_preview:{fragment_id}")
    builder.button(text="🗑️ Eliminar", callback_data=f"narrative_delete_fragment_confirm:{fragment_id}")
    builder.button(text="🔙 Volver", callback_data="narrative_admin_fragments")
    builder.adjust(1)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


# ==================== CREACIÓN DE FRAGMENTOS ====================

@router.callback_query(F.data == "narrative_create_fragment")
async def start_create_fragment(callback: CallbackQuery, state: FSMContext):
    """Inicia el flujo de creación de un nuevo fragmento"""
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_key)

    text = """➕ **Crear Nuevo Fragmento**

**Paso 1/8: Key del Fragmento**

Ingresa un identificador único para este fragmento (ej: `start`, `mansion_entrance`, `diana_intro`).

Este key se usará para referenciar el fragmento en las decisiones.

💡 Usa snake_case y hazlo descriptivo.

Escribe `/cancel` para cancelar."""

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.message(NarrativeAdminStates.create_fragment_waiting_key)
async def create_fragment_receive_key(message: Message, session: AsyncSession, state: FSMContext):
    """Recibe el key del fragmento y pide el texto"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada")
        return

    key = message.text.strip()

    # Validar que el key no exista
    stmt = select(StoryFragment).where(StoryFragment.key == key)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        await message.answer(f"❌ Ya existe un fragmento con el key `{key}`. Ingresa otro key:")
        return

    # Guardar el key
    await state.update_data(key=key)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_text)

    await message.answer(
        f"""✅ Key guardado: `{key}`

**Paso 2/8: Texto del Fragmento**

Ahora escribe el contenido narrativo completo del fragmento.

Puedes usar formato Markdown:
• **Negrita** con `**texto**`
• *Cursiva* con `*texto*`
• Emojis para personajes

Ejemplo:
🌸 **Diana:** Bienvenido a mi mundo...

Escribe `/cancel` para cancelar."""
    )


@router.message(NarrativeAdminStates.create_fragment_waiting_text)
async def create_fragment_receive_text(message: Message, state: FSMContext):
    """Recibe el texto y pide la imagen"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada")
        return

    text = message.text.strip()
    await state.update_data(text=text)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_image_url)

    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Sin imagen", callback_data="narrative_create_image:skip")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(1)

    await message.answer(
        """✅ Texto guardado

**Paso 3/8: Imagen del Fragmento (Opcional)**

¿Deseas agregar una imagen a este fragmento?

Opciones:
• Envía una **URL de imagen** (https://...)
• Envía una **imagen directamente** (Telegram guardará el file_id)
• Presiona "⏭️ Sin imagen" para continuar sin imagen

La imagen se mostrará junto al texto del fragmento.

Escribe `/cancel` para cancelar.""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "narrative_create_image:skip")
async def create_fragment_skip_image(callback: CallbackQuery, state: FSMContext):
    """Salta el paso de imagen y continúa al personaje"""
    await state.update_data(image_url=None)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_character)

    builder = InlineKeyboardBuilder()
    builder.button(text="🎩 Lucien", callback_data="narrative_create_char:Lucien")
    builder.button(text="🌸 Diana", callback_data="narrative_create_char:Diana")
    builder.button(text="📖 Narrador", callback_data="narrative_create_char:Narrador")
    builder.button(text="✍️ Otro (escribir)", callback_data="narrative_create_char:custom")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(2)

    await callback.message.edit_text(
        """⏭️ Sin imagen

**Paso 4/8: Personaje**

Selecciona el personaje que habla en este fragmento:""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.message(NarrativeAdminStates.create_fragment_waiting_image_url)
async def create_fragment_receive_image(message: Message, state: FSMContext):
    """Recibe la imagen (URL o foto) y pide el personaje"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada")
        return

    image_url = None

    # Verificar si es una URL
    if message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
        image_url = message.text.strip()
    # Verificar si es una foto
    elif message.photo:
        # Obtener la foto de mayor calidad
        photo = message.photo[-1]
        image_url = photo.file_id
    else:
        await message.answer(
            "❌ Formato no válido. Por favor:\n"
            "• Envía una URL que empiece con http:// o https://\n"
            "• Envía una imagen directamente\n"
            "• Usa el botón '⏭️ Sin imagen' para continuar"
        )
        return

    await state.update_data(image_url=image_url)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_character)

    builder = InlineKeyboardBuilder()
    builder.button(text="🎩 Lucien", callback_data="narrative_create_char:Lucien")
    builder.button(text="🌸 Diana", callback_data="narrative_create_char:Diana")
    builder.button(text="📖 Narrador", callback_data="narrative_create_char:Narrador")
    builder.button(text="✍️ Otro (escribir)", callback_data="narrative_create_char:custom")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(2)

    await message.answer(
        """✅ Imagen guardada

**Paso 4/8: Personaje**

Selecciona el personaje que habla en este fragmento:""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("narrative_create_char:"))
async def create_fragment_receive_character(callback: CallbackQuery, state: FSMContext):
    """Recibe el personaje y pide el nivel"""
    character_choice = callback.data.split(":")[1]

    if character_choice == "custom":
        await state.set_state(NarrativeAdminStates.create_fragment_waiting_character)
        await callback.message.edit_text("Escribe el nombre del personaje:")
        await callback.answer()
        return

    await state.update_data(character=character_choice)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_level)

    builder = InlineKeyboardBuilder()
    for level in range(1, 7):
        tier = "Gratuito" if level <= 3 else "VIP"
        builder.button(text=f"Nivel {level} ({tier})", callback_data=f"narrative_create_level:{level}")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(2)

    await callback.message.edit_text(
        f"""✅ Personaje: {character_choice}

**Paso 5/8: Nivel de Acceso**

Selecciona el nivel del fragmento:
• Niveles 1-3: Contenido gratuito
• Niveles 4-6: Contenido VIP

El nivel determina en qué etapa de la historia aparece.""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_create_level:"))
async def create_fragment_receive_level(callback: CallbackQuery, state: FSMContext):
    """Recibe el nivel y pide besitos mínimos"""
    level = int(callback.data.split(":")[1])
    await state.update_data(level=level)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_min_besitos)

    builder = InlineKeyboardBuilder()
    builder.button(text="0 (Sin requisito)", callback_data="narrative_create_minbesitos:0")
    builder.button(text="10 besitos", callback_data="narrative_create_minbesitos:10")
    builder.button(text="25 besitos", callback_data="narrative_create_minbesitos:25")
    builder.button(text="50 besitos", callback_data="narrative_create_minbesitos:50")
    builder.button(text="100 besitos", callback_data="narrative_create_minbesitos:100")
    builder.button(text="✍️ Otro (escribir)", callback_data="narrative_create_minbesitos:custom")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(2)

    await callback.message.edit_text(
        f"""✅ Nivel: {level}

**Paso 6/8: Besitos Mínimos**

¿Cuántos besitos necesita el usuario para acceder a este fragmento?""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_create_minbesitos:"))
async def create_fragment_receive_min_besitos(callback: CallbackQuery, state: FSMContext):
    """Recibe besitos mínimos y pide recompensa"""
    value = callback.data.split(":")[1]

    if value == "custom":
        await state.set_state(NarrativeAdminStates.create_fragment_waiting_min_besitos)
        await callback.message.edit_text("Escribe la cantidad de besitos mínimos necesarios (número):")
        await callback.answer()
        return

    min_besitos = int(value)
    await state.update_data(min_besitos=min_besitos)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_reward_besitos)

    builder = InlineKeyboardBuilder()
    builder.button(text="0 (Sin recompensa)", callback_data="narrative_create_reward:0")
    builder.button(text="5 besitos", callback_data="narrative_create_reward:5")
    builder.button(text="10 besitos", callback_data="narrative_create_reward:10")
    builder.button(text="15 besitos", callback_data="narrative_create_reward:15")
    builder.button(text="25 besitos", callback_data="narrative_create_reward:25")
    builder.button(text="✍️ Otro (escribir)", callback_data="narrative_create_reward:custom")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(2)

    await callback.message.edit_text(
        f"""✅ Besitos mínimos: {min_besitos}

**Paso 7/8: Recompensa en Besitos**

¿Cuántos besitos gana el usuario al leer este fragmento?""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_create_reward:"))
async def create_fragment_receive_reward(callback: CallbackQuery, state: FSMContext):
    """Recibe recompensa y pide rol requerido"""
    value = callback.data.split(":")[1]

    if value == "custom":
        await state.set_state(NarrativeAdminStates.create_fragment_waiting_reward_besitos)
        await callback.message.edit_text("Escribe la cantidad de besitos de recompensa (número):")
        await callback.answer()
        return

    reward_besitos = int(value)
    await state.update_data(reward_besitos=reward_besitos)
    await state.set_state(NarrativeAdminStates.create_fragment_waiting_required_role)

    builder = InlineKeyboardBuilder()
    builder.button(text="Sin requisito de rol", callback_data="narrative_create_role:none")
    builder.button(text="Requiere VIP", callback_data="narrative_create_role:vip")
    builder.button(text="❌ Cancelar", callback_data="narrative_create_cancel")
    builder.adjust(1)

    await callback.message.edit_text(
        f"""✅ Recompensa: {reward_besitos} besitos

**Paso 8/8: Rol Requerido**

¿Este fragmento requiere que el usuario tenga un rol específico?""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_create_role:"))
async def create_fragment_finalize(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Finaliza la creación del fragmento"""
    role_choice = callback.data.split(":")[1]
    required_role = None if role_choice == "none" else role_choice

    # Obtener todos los datos
    data = await state.get_data()

    # Crear el fragmento
    new_fragment = StoryFragment(
        key=data["key"],
        text=data["text"],
        image_url=data.get("image_url"),
        character=data["character"],
        level=data["level"],
        min_besitos=data["min_besitos"],
        reward_besitos=data["reward_besitos"],
        required_role=required_role
    )

    session.add(new_fragment)
    await session.commit()
    await session.refresh(new_fragment)

    await state.clear()

    emoji = "🎩" if new_fragment.character == "Lucien" else "🌸" if new_fragment.character == "Diana" else "📖"

    text = f"""✅ **Fragmento Creado Exitosamente**

{emoji} **{new_fragment.key}**

📝 Texto: {new_fragment.text[:100]}...
🎭 Personaje: {new_fragment.character}
📊 Nivel: {new_fragment.level}
💰 Besitos mínimos: {new_fragment.min_besitos}
🎁 Recompensa: {new_fragment.reward_besitos}
🔐 Rol: {required_role or "Ninguno"}

**Próximos pasos:**
Ahora puedes añadir decisiones a este fragmento para crear el flujo narrativo."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔀 Añadir Decisiones", callback_data=f"narrative_manage_choices:{new_fragment.id}")
    builder.button(text="📚 Ver Todos los Fragmentos", callback_data="narrative_admin_fragments")
    builder.button(text="➕ Crear Otro Fragmento", callback_data="narrative_create_fragment")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "narrative_create_cancel")
async def cancel_create_fragment(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Cancela la creación de fragmento"""
    await state.clear()
    await callback.answer("❌ Creación cancelada")

    # Volver al listado de fragmentos
    await show_fragments_management(callback, session)


# ==================== EDICIÓN DE FRAGMENTOS ====================

@router.callback_query(F.data.startswith("narrative_edit_fragment:"))
async def show_edit_fragment_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú de edición de un fragmento"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    fragment_id = int(callback.data.split(":")[1])
    fragment = await session.get(StoryFragment, fragment_id)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    text = f"""✏️ **Editar Fragmento: {fragment.key}**

Selecciona qué campo deseas editar:"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Texto", callback_data=f"narrative_edit_field:{fragment_id}:text")
    builder.button(text="🖼️ Imagen", callback_data=f"narrative_edit_field:{fragment_id}:image_url")
    builder.button(text="🎭 Personaje", callback_data=f"narrative_edit_field:{fragment_id}:character")
    builder.button(text="📊 Nivel", callback_data=f"narrative_edit_field:{fragment_id}:level")
    builder.button(text="💰 Besitos Mínimos", callback_data=f"narrative_edit_field:{fragment_id}:min_besitos")
    builder.button(text="🎁 Recompensa", callback_data=f"narrative_edit_field:{fragment_id}:reward_besitos")
    builder.button(text="🔐 Rol Requerido", callback_data=f"narrative_edit_field:{fragment_id}:required_role")
    builder.button(text="🔄 Auto-Siguiente", callback_data=f"narrative_edit_field:{fragment_id}:auto_next")
    builder.button(text="🔙 Volver", callback_data=f"narrative_view_fragment:{fragment_id}")
    builder.adjust(2)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_edit_field:"))
async def start_edit_fragment_field(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia la edición de un campo específico del fragmento"""
    parts = callback.data.split(":")
    fragment_id = int(parts[1])
    field = parts[2]

    fragment = await session.get(StoryFragment, fragment_id)
    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    # Guardar contexto
    await state.update_data(fragment_id=fragment_id, field=field)

    if field == "text":
        await state.set_state(NarrativeAdminStates.edit_fragment_waiting_value)
        await callback.message.edit_text(
            f"📝 **Editar Texto**\n\n"
            f"Texto actual:\n{fragment.text[:500]}...\n\n"
            f"Escribe el nuevo texto del fragmento:"
        )
    elif field == "image_url":
        await state.set_state(NarrativeAdminStates.edit_fragment_waiting_value)

        current_image = fragment.image_url or "Sin imagen"
        image_type = ""
        if fragment.image_url:
            if fragment.image_url.startswith("http"):
                image_type = " (URL)"
            else:
                image_type = " (Telegram file_id)"

        builder = InlineKeyboardBuilder()
        builder.button(text="🗑️ Quitar imagen", callback_data=f"narrative_edit_value:{fragment_id}:image_url:remove")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_fragment:{fragment_id}")
        builder.adjust(1)

        await callback.message.edit_text(
            f"🖼️ **Editar Imagen**\n\n"
            f"Imagen actual: {current_image}{image_type}\n\n"
            f"Opciones:\n"
            f"• Envía una **URL de imagen** (https://...)\n"
            f"• Envía una **imagen directamente**\n"
            f"• Presiona '🗑️ Quitar imagen' para eliminarla",
            reply_markup=builder.as_markup()
        )
    elif field == "character":
        builder = InlineKeyboardBuilder()
        builder.button(text="🎩 Lucien", callback_data=f"narrative_edit_value:{fragment_id}:character:Lucien")
        builder.button(text="🌸 Diana", callback_data=f"narrative_edit_value:{fragment_id}:character:Diana")
        builder.button(text="📖 Narrador", callback_data=f"narrative_edit_value:{fragment_id}:character:Narrador")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_fragment:{fragment_id}")
        builder.adjust(2)

        await callback.message.edit_text(
            f"🎭 **Editar Personaje**\n\n"
            f"Personaje actual: {fragment.character}\n\n"
            f"Selecciona el nuevo personaje:",
            reply_markup=builder.as_markup()
        )
    elif field == "level":
        builder = InlineKeyboardBuilder()
        for level in range(1, 7):
            tier = "Gratuito" if level <= 3 else "VIP"
            builder.button(text=f"Nivel {level} ({tier})", callback_data=f"narrative_edit_value:{fragment_id}:level:{level}")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_fragment:{fragment_id}")
        builder.adjust(2)

        await callback.message.edit_text(
            f"📊 **Editar Nivel**\n\n"
            f"Nivel actual: {fragment.level}\n\n"
            f"Selecciona el nuevo nivel:",
            reply_markup=builder.as_markup()
        )
    elif field == "required_role":
        builder = InlineKeyboardBuilder()
        builder.button(text="Sin requisito", callback_data=f"narrative_edit_value:{fragment_id}:required_role:none")
        builder.button(text="VIP", callback_data=f"narrative_edit_value:{fragment_id}:required_role:vip")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_fragment:{fragment_id}")
        builder.adjust(2)

        await callback.message.edit_text(
            f"🔐 **Editar Rol Requerido**\n\n"
            f"Rol actual: {fragment.required_role or 'Ninguno'}\n\n"
            f"Selecciona el nuevo rol:",
            reply_markup=builder.as_markup()
        )
    else:
        await state.set_state(NarrativeAdminStates.edit_fragment_waiting_value)
        current_value = getattr(fragment, field, "No configurado")
        await callback.message.edit_text(
            f"✏️ **Editar {field}**\n\n"
            f"Valor actual: {current_value}\n\n"
            f"Escribe el nuevo valor:"
        )

    await callback.answer()


@router.message(NarrativeAdminStates.edit_fragment_waiting_value)
async def receive_edit_fragment_value(message: Message, session: AsyncSession, state: FSMContext):
    """Recibe el nuevo valor y actualiza el fragmento"""
    data = await state.get_data()
    fragment_id = data.get("fragment_id")
    field = data.get("field")

    fragment = await session.get(StoryFragment, fragment_id)
    if not fragment:
        await message.answer("❌ Fragmento no encontrado")
        await state.clear()
        return

    # Procesar según el tipo de campo
    if field == "image_url":
        # Verificar si es una URL o una foto
        if message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
            new_value = message.text.strip()
        elif message.photo:
            photo = message.photo[-1]
            new_value = photo.file_id
        else:
            await message.answer(
                "❌ Formato no válido. Por favor:\n"
                "• Envía una URL que empiece con http:// o https://\n"
                "• Envía una imagen directamente\n"
                "• Usa el botón '🗑️ Quitar imagen' para eliminarla"
            )
            return
    else:
        new_value = message.text.strip()

        # Actualizar el campo
        if field in ["min_besitos", "reward_besitos", "level"]:
            try:
                new_value = int(new_value)
            except ValueError:
                await message.answer("❌ El valor debe ser un número")
                return

    setattr(fragment, field, new_value)
    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Campo **{field}** actualizado correctamente"
    )

    # Mostrar menú de edición nuevamente
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Ver Fragmento", callback_data=f"narrative_view_fragment:{fragment_id}")
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"narrative_edit_fragment:{fragment_id}")
    builder.button(text="📚 Ver Todos", callback_data="narrative_admin_fragments")
    builder.adjust(1)

    await message.answer("¿Qué deseas hacer ahora?", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("narrative_edit_value:"))
async def receive_edit_fragment_value_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Recibe el nuevo valor desde callback y actualiza el fragmento"""
    parts = callback.data.split(":")
    fragment_id = int(parts[1])
    field = parts[2]
    new_value = parts[3]

    fragment = await session.get(StoryFragment, fragment_id)
    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    # Procesar valor
    if new_value == "none":
        new_value = None
    elif new_value == "remove":
        new_value = None
    elif field in ["level", "min_besitos", "reward_besitos"]:
        new_value = int(new_value)

    setattr(fragment, field, new_value)
    await session.commit()
    await state.clear()

    await callback.answer(f"✅ {field} actualizado", show_alert=True)

    # Mostrar fragmento actualizado
    await view_fragment_detail(callback, session)


# ==================== ELIMINACIÓN DE FRAGMENTOS ====================

@router.callback_query(F.data.startswith("narrative_delete_fragment_confirm:"))
async def confirm_delete_fragment(callback: CallbackQuery, session: AsyncSession):
    """Solicita confirmación para eliminar un fragmento"""
    fragment_id = int(callback.data.split(":")[1])
    fragment = await session.get(StoryFragment, fragment_id)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    text = f"""⚠️ **Confirmar Eliminación**

¿Estás seguro de que deseas eliminar el fragmento **{fragment.key}**?

Esta acción:
• Eliminará el fragmento permanentemente
• Eliminará todas sus decisiones
• NO se puede deshacer

Los usuarios que estén en este fragmento perderán su progreso."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Sí, Eliminar", callback_data=f"narrative_delete_fragment:{fragment_id}")
    builder.button(text="❌ Cancelar", callback_data=f"narrative_view_fragment:{fragment_id}")
    builder.adjust(1)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_delete_fragment:"))
async def delete_fragment(callback: CallbackQuery, session: AsyncSession):
    """Elimina el fragmento y sus decisiones"""
    fragment_id = int(callback.data.split(":")[1])
    fragment = await session.get(StoryFragment, fragment_id)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    fragment_key = fragment.key

    # Eliminar el fragmento (las decisiones se eliminan por cascade)
    await session.delete(fragment)
    await session.commit()

    await callback.answer(f"✅ Fragmento {fragment_key} eliminado", show_alert=True)

    # Volver al listado
    await show_fragments_management(callback, session)


# ==================== GESTIÓN DE DECISIONES ====================

@router.callback_query(F.data.startswith("narrative_manage_choices:"))
async def manage_fragment_choices(callback: CallbackQuery, session: AsyncSession):
    """Muestra y gestiona las decisiones de un fragmento"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    fragment_id = int(callback.data.split(":")[1])
    fragment = await session.get(StoryFragment, fragment_id)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    # Obtener decisiones
    stmt = select(NarrativeChoice).where(
        NarrativeChoice.source_fragment_id == fragment_id
    ).order_by(NarrativeChoice.id)
    result = await session.execute(stmt)
    choices = result.scalars().all()

    emoji = "🎩" if fragment.character == "Lucien" else "🌸" if fragment.character == "Diana" else "📖"

    text = f"""{emoji} **Decisiones de: {fragment.key}**

Total: {len(choices)} decisiones

Selecciona una decisión para editar o crea una nueva:"""

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Añadir Nueva Decisión", callback_data=f"narrative_create_choice:{fragment_id}")
    builder.adjust(1)

    # Listar decisiones existentes
    for idx, choice in enumerate(choices, 1):
        label = f"{idx}. {choice.text[:40]}... → {choice.destination_fragment_key}"
        builder.button(text=label, callback_data=f"narrative_view_choice:{choice.id}")
    builder.adjust(1)

    builder.button(text="🔙 Volver al Fragmento", callback_data=f"narrative_view_fragment:{fragment_id}")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_view_choice:"))
async def view_choice_detail(callback: CallbackQuery, session: AsyncSession):
    """Muestra los detalles de una decisión"""
    choice_id = int(callback.data.split(":")[1])
    choice = await session.get(NarrativeChoice, choice_id)

    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    fragment = await session.get(StoryFragment, choice.source_fragment_id)

    text = f"""🔀 **Detalle de Decisión**

📝 **Texto:** {choice.text}

🎯 **Destino:** {choice.destination_fragment_key}

⚙️ **Requisitos:**
• Besitos: {choice.required_besitos or 0}
• Rol: {choice.required_role or "Ninguno"}

📍 **Fragmento origen:** {fragment.key if fragment else "Desconocido"}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Decisión", callback_data=f"narrative_edit_choice:{choice_id}")
    builder.button(text="🗑️ Eliminar", callback_data=f"narrative_delete_choice_confirm:{choice_id}")
    builder.button(text="🔙 Volver", callback_data=f"narrative_manage_choices:{choice.source_fragment_id}")
    builder.adjust(1)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_create_choice:"))
async def start_create_choice(callback: CallbackQuery, state: FSMContext):
    """Inicia el flujo de creación de una nueva decisión"""
    fragment_id = int(callback.data.split(":")[1])

    await state.update_data(choice_fragment_id=fragment_id)
    await state.set_state(NarrativeAdminStates.create_choice_waiting_text)

    text = """➕ **Crear Nueva Decisión**

**Paso 1/4: Texto de la Decisión**

Escribe el texto que verá el usuario como opción.

Ejemplo:
• "Estoy listo para comenzar"
• "Necesito saber más primero"
• "¿Dónde está Diana?"

Escribe `/cancel` para cancelar."""

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"narrative_manage_choices:{fragment_id}")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.message(NarrativeAdminStates.create_choice_waiting_text)
async def create_choice_receive_text(message: Message, state: FSMContext):
    """Recibe el texto y pide el destino"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada")
        return

    text = message.text.strip()
    await state.update_data(choice_text=text)
    await state.set_state(NarrativeAdminStates.create_choice_waiting_destination)

    await message.answer(
        f"""✅ Texto guardado: "{text}"

**Paso 2/4: Fragmento de Destino**

Escribe el **key** del fragmento al que llevará esta decisión.

💡 Por ejemplo: `mansion_entrance`, `diana_intro`, `vip_chamber`

Asegúrate de que el fragmento ya existe o créalo después.

Escribe `/cancel` para cancelar."""
    )


@router.message(NarrativeAdminStates.create_choice_waiting_destination)
async def create_choice_receive_destination(message: Message, state: FSMContext):
    """Recibe el destino y pide requisitos de besitos"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Creación cancelada")
        return

    destination = message.text.strip()
    await state.update_data(choice_destination=destination)
    await state.set_state(NarrativeAdminStates.create_choice_waiting_required_besitos)

    builder = InlineKeyboardBuilder()
    builder.button(text="0 (Sin requisito)", callback_data="narrative_choice_besitos:0")
    builder.button(text="10 besitos", callback_data="narrative_choice_besitos:10")
    builder.button(text="25 besitos", callback_data="narrative_choice_besitos:25")
    builder.button(text="50 besitos", callback_data="narrative_choice_besitos:50")
    builder.button(text="✍️ Otro", callback_data="narrative_choice_besitos:custom")
    builder.adjust(2)

    await message.answer(
        f"""✅ Destino: {destination}

**Paso 3/4: Besitos Requeridos**

¿Cuántos besitos necesita el usuario para elegir esta opción?""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("narrative_choice_besitos:"))
async def create_choice_receive_besitos(callback: CallbackQuery, state: FSMContext):
    """Recibe requisito de besitos y pide rol"""
    value = callback.data.split(":")[1]

    if value == "custom":
        await state.set_state(NarrativeAdminStates.create_choice_waiting_required_besitos)
        await callback.message.edit_text("Escribe la cantidad de besitos requeridos (número):")
        await callback.answer()
        return

    required_besitos = int(value)
    await state.update_data(choice_required_besitos=required_besitos)
    await state.set_state(NarrativeAdminStates.create_choice_waiting_required_role)

    builder = InlineKeyboardBuilder()
    builder.button(text="Sin requisito", callback_data="narrative_choice_role:none")
    builder.button(text="Requiere VIP", callback_data="narrative_choice_role:vip")
    builder.adjust(1)

    await callback.message.edit_text(
        f"""✅ Besitos requeridos: {required_besitos}

**Paso 4/4: Rol Requerido**

¿Esta opción requiere que el usuario tenga un rol específico?""",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_choice_role:"))
async def create_choice_finalize(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Finaliza la creación de la decisión"""
    role_choice = callback.data.split(":")[1]
    required_role = None if role_choice == "none" else role_choice

    # Obtener datos
    data = await state.get_data()
    fragment_id = data["choice_fragment_id"]

    # Crear la decisión
    new_choice = NarrativeChoice(
        source_fragment_id=fragment_id,
        text=data["choice_text"],
        destination_fragment_key=data["choice_destination"],
        required_besitos=data["choice_required_besitos"],
        required_role=required_role
    )

    session.add(new_choice)
    await session.commit()
    await state.clear()

    await callback.answer("✅ Decisión creada", show_alert=True)

    # Mostrar la decisión recién creada
    await session.refresh(new_choice)

    text = f"""✅ **Decisión Creada Exitosamente**

📝 Texto: {new_choice.text}
🎯 Destino: {new_choice.destination_fragment_key}
💰 Besitos: {new_choice.required_besitos or 0}
🔐 Rol: {required_role or "Ninguno"}"""

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Añadir Otra Decisión", callback_data=f"narrative_create_choice:{fragment_id}")
    builder.button(text="🔀 Ver Todas las Decisiones", callback_data=f"narrative_manage_choices:{fragment_id}")
    builder.button(text="📖 Ver Fragmento", callback_data=f"narrative_view_fragment:{fragment_id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("narrative_edit_choice:"))
async def show_edit_choice_menu(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú de edición de una decisión"""
    choice_id = int(callback.data.split(":")[1])
    choice = await session.get(NarrativeChoice, choice_id)

    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    text = f"""✏️ **Editar Decisión**

Texto actual: {choice.text}

Selecciona qué campo deseas editar:"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Texto", callback_data=f"narrative_edit_choice_field:{choice_id}:text")
    builder.button(text="🎯 Destino", callback_data=f"narrative_edit_choice_field:{choice_id}:destination")
    builder.button(text="💰 Besitos", callback_data=f"narrative_edit_choice_field:{choice_id}:besitos")
    builder.button(text="🔐 Rol", callback_data=f"narrative_edit_choice_field:{choice_id}:role")
    builder.button(text="🔙 Volver", callback_data=f"narrative_view_choice:{choice_id}")
    builder.adjust(2)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_edit_choice_field:"))
async def start_edit_choice_field(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia la edición de un campo de la decisión"""
    parts = callback.data.split(":")
    choice_id = int(parts[1])
    field = parts[2]

    choice = await session.get(NarrativeChoice, choice_id)
    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    await state.update_data(edit_choice_id=choice_id, edit_choice_field=field)

    if field == "text":
        await state.set_state(NarrativeAdminStates.edit_choice_waiting_value)
        await callback.message.edit_text(
            f"📝 **Editar Texto**\n\n"
            f"Texto actual: {choice.text}\n\n"
            f"Escribe el nuevo texto:"
        )
    elif field == "destination":
        await state.set_state(NarrativeAdminStates.edit_choice_waiting_value)
        await callback.message.edit_text(
            f"🎯 **Editar Destino**\n\n"
            f"Destino actual: {choice.destination_fragment_key}\n\n"
            f"Escribe el nuevo key de destino:"
        )
    elif field == "besitos":
        builder = InlineKeyboardBuilder()
        builder.button(text="0", callback_data=f"narrative_choice_edit_value:{choice_id}:required_besitos:0")
        builder.button(text="10", callback_data=f"narrative_choice_edit_value:{choice_id}:required_besitos:10")
        builder.button(text="25", callback_data=f"narrative_choice_edit_value:{choice_id}:required_besitos:25")
        builder.button(text="50", callback_data=f"narrative_choice_edit_value:{choice_id}:required_besitos:50")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_choice:{choice_id}")
        builder.adjust(2)

        await callback.message.edit_text(
            f"💰 **Editar Besitos Requeridos**\n\n"
            f"Besitos actuales: {choice.required_besitos or 0}\n\n"
            f"Selecciona la nueva cantidad:",
            reply_markup=builder.as_markup()
        )
    elif field == "role":
        builder = InlineKeyboardBuilder()
        builder.button(text="Sin requisito", callback_data=f"narrative_choice_edit_value:{choice_id}:required_role:none")
        builder.button(text="VIP", callback_data=f"narrative_choice_edit_value:{choice_id}:required_role:vip")
        builder.button(text="❌ Cancelar", callback_data=f"narrative_edit_choice:{choice_id}")
        builder.adjust(2)

        await callback.message.edit_text(
            f"🔐 **Editar Rol Requerido**\n\n"
            f"Rol actual: {choice.required_role or 'Ninguno'}\n\n"
            f"Selecciona el nuevo rol:",
            reply_markup=builder.as_markup()
        )

    await callback.answer()


@router.message(NarrativeAdminStates.edit_choice_waiting_value)
async def receive_edit_choice_value(message: Message, session: AsyncSession, state: FSMContext):
    """Recibe el nuevo valor y actualiza la decisión"""
    data = await state.get_data()
    choice_id = data.get("edit_choice_id")
    field = data.get("edit_choice_field")
    new_value = message.text.strip()

    choice = await session.get(NarrativeChoice, choice_id)
    if not choice:
        await message.answer("❌ Decisión no encontrada")
        await state.clear()
        return

    # Mapear campos
    field_map = {
        "text": "text",
        "destination": "destination_fragment_key"
    }
    db_field = field_map.get(field, field)

    setattr(choice, db_field, new_value)
    await session.commit()
    await state.clear()

    await message.answer(f"✅ Campo actualizado correctamente")

    builder = InlineKeyboardBuilder()
    builder.button(text="🔀 Ver Decisión", callback_data=f"narrative_view_choice:{choice_id}")
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"narrative_edit_choice:{choice_id}")
    builder.adjust(1)

    await message.answer("¿Qué deseas hacer ahora?", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("narrative_choice_edit_value:"))
async def receive_edit_choice_value_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Recibe el nuevo valor desde callback"""
    parts = callback.data.split(":")
    choice_id = int(parts[1])
    field = parts[2]
    new_value = parts[3]

    choice = await session.get(NarrativeChoice, choice_id)
    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    # Procesar valor
    if new_value == "none":
        new_value = None
    elif field == "required_besitos":
        new_value = int(new_value)

    setattr(choice, field, new_value)
    await session.commit()
    await state.clear()

    await callback.answer(f"✅ {field} actualizado", show_alert=True)
    await view_choice_detail(callback, session)


@router.callback_query(F.data.startswith("narrative_delete_choice_confirm:"))
async def confirm_delete_choice(callback: CallbackQuery, session: AsyncSession):
    """Solicita confirmación para eliminar una decisión"""
    choice_id = int(callback.data.split(":")[1])
    choice = await session.get(NarrativeChoice, choice_id)

    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    text = f"""⚠️ **Confirmar Eliminación**

¿Eliminar la decisión "{choice.text}"?

Esta acción no se puede deshacer."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Sí, Eliminar", callback_data=f"narrative_delete_choice:{choice_id}")
    builder.button(text="❌ Cancelar", callback_data=f"narrative_view_choice:{choice_id}")
    builder.adjust(1)

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("narrative_delete_choice:"))
async def delete_choice(callback: CallbackQuery, session: AsyncSession):
    """Elimina la decisión"""
    choice_id = int(callback.data.split(":")[1])
    choice = await session.get(NarrativeChoice, choice_id)

    if not choice:
        await callback.answer("❌ Decisión no encontrada", show_alert=True)
        return

    fragment_id = choice.source_fragment_id
    await session.delete(choice)
    await session.commit()

    await callback.answer("✅ Decisión eliminada", show_alert=True)

    # Volver a la gestión de decisiones
    await manage_fragment_choices(callback, session)


# ==================== VALIDACIÓN DE NARRATIVA ====================

@router.callback_query(F.data == "narrative_admin_validate")
async def validate_narrative(callback: CallbackQuery, session: AsyncSession):
    """Valida la integridad de la narrativa"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    # Obtener todos los fragmentos y decisiones
    fragments_stmt = select(StoryFragment)
    fragments_result = await session.execute(fragments_stmt)
    fragments = {f.key: f for f in fragments_result.scalars().all()}

    choices_stmt = select(NarrativeChoice)
    choices_result = await session.execute(choices_stmt)
    choices = choices_result.scalars().all()

    # Validaciones
    errors = []
    warnings = []

    # 1. Verificar que exista fragmento "start"
    if "start" not in fragments:
        errors.append("❌ No existe fragmento 'start' (punto de inicio)")

    # 2. Verificar destinos de decisiones
    for choice in choices:
        if choice.destination_fragment_key not in fragments:
            errors.append(f"❌ Decisión '{choice.text[:30]}...' apunta a fragmento inexistente: {choice.destination_fragment_key}")

    # 3. Detectar fragmentos huérfanos (sin decisiones que lleguen a ellos)
    referenced_fragments = set()
    for choice in choices:
        referenced_fragments.add(choice.destination_fragment_key)

    orphan_fragments = []
    for key in fragments.keys():
        if key != "start" and key not in referenced_fragments:
            orphan_fragments.append(key)

    if orphan_fragments:
        warnings.append(f"⚠️ Fragmentos huérfanos (ninguna decisión lleva a ellos): {', '.join(orphan_fragments[:5])}")

    # 4. Detectar fragmentos sin salida
    fragments_with_choices = set()
    for choice in choices:
        fragments_with_choices.add(choice.source_fragment_id)

    dead_ends = []
    for key, fragment in fragments.items():
        if fragment.id not in fragments_with_choices and not fragment.auto_next_fragment_key:
            dead_ends.append(key)

    if dead_ends:
        warnings.append(f"⚠️ Fragmentos sin salida (no tienen decisiones ni auto-siguiente): {', '.join(dead_ends[:5])}")

    # Generar reporte
    text = f"""✅ **Validación de Narrativa**

📊 **Resumen:**
• Fragmentos totales: {len(fragments)}
• Decisiones totales: {len(choices)}

"""

    if errors:
        text += "🔴 **Errores Críticos:**\n"
        for error in errors[:10]:
            text += f"{error}\n"
        text += "\n"

    if warnings:
        text += "🟡 **Advertencias:**\n"
        for warning in warnings[:10]:
            text += f"{warning}\n"
        text += "\n"

    if not errors and not warnings:
        text += "✅ **Todo correcto!** No se encontraron problemas.\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_narrative_panel")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


# ==================== ESTADÍSTICAS DETALLADAS ====================

@router.callback_query(F.data == "narrative_admin_stats")
async def show_detailed_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas detalladas del sistema narrativo"""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return

    # Fragmentos por nivel
    level_stmt = select(
        StoryFragment.level,
        func.count(StoryFragment.id)
    ).group_by(StoryFragment.level)
    level_result = await session.execute(level_stmt)
    level_dist = dict(level_result.all())

    # Fragmentos por personaje
    char_stmt = select(
        StoryFragment.character,
        func.count(StoryFragment.id)
    ).group_by(StoryFragment.character)
    char_result = await session.execute(char_stmt)
    char_dist = dict(char_result.all())

    # Usuarios activos
    users_stmt = select(func.count()).select_from(UserNarrativeState)
    users_result = await session.execute(users_stmt)
    active_users = users_result.scalar() or 0

    # Fragmento más visitado
    most_visited_stmt = select(
        UserNarrativeState.current_fragment_key,
        func.count(UserNarrativeState.user_id)
    ).group_by(UserNarrativeState.current_fragment_key).order_by(
        func.count(UserNarrativeState.user_id).desc()
    ).limit(1)
    most_visited_result = await session.execute(most_visited_stmt)
    most_visited = most_visited_result.first()

    text = f"""📊 **Estadísticas Detalladas**

👥 **Usuarios:**
• Usuarios activos en narrativa: {active_users}

📚 **Distribución por Nivel:**
"""

    for level in sorted(level_dist.keys()):
        count = level_dist[level]
        tier = "Gratuito" if level <= 3 else "VIP"
        text += f"• Nivel {level} ({tier}): {count} fragmentos\n"

    text += "\n🎭 **Distribución por Personaje:**\n"
    for character, count in char_dist.items():
        emoji = "🎩" if character == "Lucien" else "🌸" if character == "Diana" else "📖"
        text += f"• {emoji} {character}: {count} fragmentos\n"

    if most_visited:
        text += f"\n🔥 **Fragmento más visitado:** {most_visited[0]} ({most_visited[1]} usuarios)"

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_narrative_panel")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()


# ==================== VINCULACIÓN CON PRODUCTOS (Placeholder) ====================

@router.callback_query(F.data == "narrative_admin_link_products")
async def show_product_linking(callback: CallbackQuery, session: AsyncSession):
    """Muestra el sistema de vinculación con productos (en desarrollo)"""
    text = """🔗 **Vinculación con Productos**

Esta funcionalidad permite configurar qué productos de la tienda desbloquean fragmentos narrativos.

🚧 **En desarrollo:**
• Vincular productos con fragmentos
• Configurar fragmentos que requieren compras
• Ver productos que desbloquean contenido

Por ahora, los productos pueden desbloquear **LorePiece** a través del campo `unlocks_lore_piece_id` en la tienda."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_narrative_panel")

    await safe_edit(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()
