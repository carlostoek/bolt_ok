"""
Handler del Wizard de Creación de Misiones V2

Panel de administración mejorado que permite crear misiones complejas sin tocar código.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.admin_mission_states import AdminMissionWizardStates
from services.mission_template_service import MissionTemplateService
from services.mission_service import MissionService
from services.mission_stats_service import MissionStatsService
from database.models import Mission, LorePiece
from keyboards.common import get_back_kb

logger = logging.getLogger(__name__)
router = Router()


# ========== PASO 1: SELECCIÓN DE TIPO DE MISIÓN ==========

@router.callback_query(F.data == "admin_create_mission_v2")
async def start_mission_wizard(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el wizard de creación de misión mejorado"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    template_service = MissionTemplateService(session)
    templates = template_service.list_templates()

    keyboard = []
    for template in templates:
        emoji = template.get("icon", "📌")
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {template['name']} (⭐ x{template['difficulty']})",
                callback_data=f"wizard_template_{template['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="⚙️ Personalizada (desde cero)", callback_data="wizard_custom")])
    keyboard.append([InlineKeyboardButton(text="🔙 Cancelar", callback_data="admin_content_missions")])

    text = (
        "🎯 **Crear Nueva Misión**\n\n"
        "Selecciona un template para empezar más rápido, "
        "o crea una misión personalizada desde cero.\n\n"
        "**Templates disponibles:**"
    )

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(AdminMissionWizardStates.selecting_mission_type)
    await callback.answer()


@router.callback_query(AdminMissionWizardStates.selecting_mission_type, F.data.startswith("wizard_template_"))
async def select_template(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario selecciona un template"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    template_id = callback.data.split("wizard_template_")[-1]
    template_service = MissionTemplateService(session)

    try:
        template = template_service.get_template(template_id)
        await state.update_data(template_id=template_id, template_config=template["config"])

        text = (
            f"✅ **Template seleccionado:** {template['name']}\n\n"
            f"📝 {template['description']}\n\n"
            "Ahora vamos a personalizar esta misión.\n\n"
            "**Paso 1/6:** Ingresa el nombre de la misión:"
        )

        await callback.message.edit_text(text, reply_markup=get_back_kb("admin_content_missions"))
        await state.set_state(AdminMissionWizardStates.entering_name)
        await callback.answer()

    except ValueError as e:
        await callback.answer(str(e), show_alert=True)


@router.callback_query(AdminMissionWizardStates.selecting_mission_type, F.data == "wizard_custom")
async def start_custom_mission(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario crea misión personalizada desde cero"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(template_id=None, template_config={})

    text = (
        "⚙️ **Misión Personalizada**\n\n"
        "Crearás una misión completamente desde cero.\n\n"
        "**Paso 1/6:** Ingresa el nombre de la misión:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("admin_content_missions"))
    await state.set_state(AdminMissionWizardStates.entering_name)
    await callback.answer()


# ========== PASO 2: INFORMACIÓN BÁSICA ==========

@router.message(AdminMissionWizardStates.entering_name)
async def process_mission_name(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa el nombre de la misión"""
    if not await is_admin(message.from_user.id, session):
        return

    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres. Intenta de nuevo:")
        return

    await state.update_data(name=name)

    text = (
        f"✅ Nombre: **{name}**\n\n"
        "**Paso 2/6:** Ingresa una descripción breve de la misión:"
    )

    await message.answer(text, reply_markup=get_back_kb("admin_content_missions"))
    await state.set_state(AdminMissionWizardStates.entering_description)


@router.message(AdminMissionWizardStates.entering_description)
async def process_mission_description(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa la descripción de la misión"""
    if not await is_admin(message.from_user.id, session):
        return

    description = message.text.strip()
    await state.update_data(description=description)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Narrativa", callback_data="wizard_cat_narrative")],
            [InlineKeyboardButton(text="💬 Social", callback_data="wizard_cat_social")],
            [InlineKeyboardButton(text="🏆 Competitiva", callback_data="wizard_cat_competitive")],
            [InlineKeyboardButton(text="🤫 Secreta", callback_data="wizard_cat_secret")],
            [InlineKeyboardButton(text="⚙️ General", callback_data="wizard_cat_general")],
            [InlineKeyboardButton(text="🔙 Atrás", callback_data="wizard_back_to_name")],
        ]
    )

    text = (
        "✅ Descripción guardada\n\n"
        "**Paso 3/6:** Selecciona la categoría de la misión:"
    )

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminMissionWizardStates.selecting_category)


@router.callback_query(AdminMissionWizardStates.selecting_category, F.data.startswith("wizard_cat_"))
async def process_category(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa la categoría seleccionada"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    category = callback.data.split("wizard_cat_")[-1]
    await state.update_data(mission_category=category)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐", callback_data="wizard_diff_1")],
            [InlineKeyboardButton(text="⭐⭐", callback_data="wizard_diff_2")],
            [InlineKeyboardButton(text="⭐⭐⭐", callback_data="wizard_diff_3")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="wizard_diff_4")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="wizard_diff_5")],
            [InlineKeyboardButton(text="🔙 Atrás", callback_data="wizard_back_to_desc")],
        ]
    )

    text = (
        f"✅ Categoría: **{category}**\n\n"
        "**Paso 4/6:** Selecciona la dificultad:"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(AdminMissionWizardStates.selecting_difficulty)
    await callback.answer()


@router.callback_query(AdminMissionWizardStates.selecting_difficulty, F.data.startswith("wizard_diff_"))
async def process_difficulty(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Procesa la dificultad seleccionada"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    difficulty = int(callback.data.split("wizard_diff_")[-1])
    await state.update_data(difficulty_level=difficulty)

    text = (
        f"✅ Dificultad: {'⭐' * difficulty}\n\n"
        "**Paso 5/6:** Ingresa la recompensa en puntos (ej. 150):"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("admin_content_missions"))
    await state.set_state(AdminMissionWizardStates.entering_reward_points)
    await callback.answer()


# ========== PASO 3: RECOMPENSAS ==========

@router.message(AdminMissionWizardStates.entering_reward_points)
async def process_reward_points(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa los puntos de recompensa"""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        points = int(message.text.strip())
        if points < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Ingresa un número válido (mayor o igual a 0):")
        return

    await state.update_data(reward_points=points)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Sí, agregar pista", callback_data="wizard_add_lore_yes")],
            [InlineKeyboardButton(text="❌ No, continuar", callback_data="wizard_add_lore_no")],
        ]
    )

    text = (
        f"✅ Recompensa: **{points} puntos**\n\n"
        "**Paso 6/6:** ¿Desbloquea alguna pista de lore al completarse?"
    )

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminMissionWizardStates.selecting_lore_unlock)


@router.callback_query(AdminMissionWizardStates.selecting_lore_unlock, F.data == "wizard_add_lore_yes")
async def select_lore_piece(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Muestra lista de pistas de lore disponibles"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    stmt = select(LorePiece).where(LorePiece.is_active == True).limit(10)
    result = await session.execute(stmt)
    lore_pieces = result.scalars().all()

    if not lore_pieces:
        await callback.answer("No hay pistas de lore disponibles", show_alert=True)
        await state.update_data(unlocks_lore_piece_code=None)
        await show_preview(callback.message, state, session)
        return

    keyboard = []
    for piece in lore_pieces:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🎯 {piece.title}",
                callback_data=f"wizard_lore_{piece.code_name}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="❌ No agregar pista", callback_data="wizard_add_lore_no")])

    await callback.message.edit_text(
        "Selecciona la pista de lore que se desbloqueará:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(AdminMissionWizardStates.selecting_lore_unlock, F.data.startswith("wizard_lore_"))
async def confirm_lore_piece(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Confirma la pista de lore seleccionada"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    lore_code = callback.data.split("wizard_lore_")[-1]
    await state.update_data(unlocks_lore_piece_code=lore_code)

    await callback.answer(f"✅ Pista '{lore_code}' agregada", show_alert=True)
    await show_preview(callback.message, state, session)


@router.callback_query(AdminMissionWizardStates.selecting_lore_unlock, F.data == "wizard_add_lore_no")
async def skip_lore_piece(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario decide no agregar pista de lore"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(unlocks_lore_piece_code=None)
    await show_preview(callback.message, state, session)


# ========== PREVIEW Y CONFIRMACIÓN ==========

async def show_preview(message: Message, state: FSMContext, session: AsyncSession):
    """Muestra un preview de la misión antes de crearla"""
    data = await state.get_data()

    template_id = data.get("template_id")
    template_config = data.get("template_config", {})

    # Merge de configuración
    name = data.get("name", "Sin nombre")
    description = data.get("description", "Sin descripción")
    category = data.get("mission_category", template_config.get("mission_category", "general"))
    difficulty = data.get("difficulty_level", template_config.get("difficulty_level", 1))
    reward_points = data.get("reward_points", 100)
    lore_code = data.get("unlocks_lore_piece_code")

    preview_text = (
        "📋 **PREVIEW DE LA MISIÓN**\n\n"
        f"**Nombre:** {name}\n"
        f"**Descripción:** {description}\n"
        f"**Categoría:** {category}\n"
        f"**Dificultad:** {'⭐' * difficulty}\n"
        f"**Recompensa:** {reward_points} puntos\n"
    )

    if lore_code:
        preview_text += f"**Desbloquea pista:** {lore_code}\n"

    if template_id:
        preview_text += f"\n**Basada en template:** {template_id}\n"

    preview_text += "\n¿Crear esta misión?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar y Crear", callback_data="wizard_confirm_create")],
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_content_missions")],
        ]
    )

    await message.edit_text(preview_text, reply_markup=keyboard)
    await state.set_state(AdminMissionWizardStates.confirming_creation)


@router.callback_query(AdminMissionWizardStates.confirming_creation, F.data == "wizard_confirm_create")
async def confirm_and_create_mission(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Crea la misión finalmente"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()
    template_id = data.get("template_id")
    template_config = data.get("template_config", {})

    try:
        # Preparar valores
        mission_values = {
            "name": data.get("name", "Nueva Misión"),
            "description": data.get("description", ""),
            "reward_points": data.get("reward_points", 100),
            "mission_category": data.get("mission_category", template_config.get("mission_category")),
            "difficulty_level": data.get("difficulty_level", template_config.get("difficulty_level", 1)),
            "unlocks_lore_piece_code": data.get("unlocks_lore_piece_code"),
            "target_value": data.get("target_value", template_config.get("target_value", 1)),
            "type": template_config.get("type", "one_time"),
            "requires_action": template_config.get("requires_action", False),
            "action_data": template_config.get("action_data"),
        }

        if template_id:
            # Crear desde template
            template_service = MissionTemplateService(session)
            mission = await template_service.create_from_template(template_id, mission_values)
        else:
            # Crear manualmente
            mission_service = MissionService(session)
            mission = await mission_service.create_mission(**mission_values)

        await callback.message.edit_text(
            f"✅ **¡Misión creada exitosamente!**\n\n"
            f"ID: `{mission.id}`\n"
            f"Nombre: {mission.name}\n\n"
            f"La misión ya está disponible para los usuarios.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Volver a Misiones", callback_data="admin_content_missions")]]
            )
        )
        await state.clear()
        await callback.answer("¡Misión creada!", show_alert=True)

    except Exception as e:
        logger.error(f"Error creando misión: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


# ========== VER ESTADÍSTICAS DE MISIÓN ==========

@router.callback_query(F.data.startswith("admin_mission_stats_"))
async def show_mission_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas de una misión"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    mission_id = callback.data.split("admin_mission_stats_")[-1]
    stats_service = MissionStatsService(session)

    stats = await stats_service.get_mission_stats(mission_id)

    if not stats:
        await callback.answer("Misión no encontrada", show_alert=True)
        return

    text = (
        f"📊 **Estadísticas: {stats['mission_name']}**\n\n"
        f"**Total completaciones:** {stats['total_completions']}\n"
        f"**Usuarios únicos:** {stats['unique_users']}\n"
        f"**Tasa de completación:** {stats['completion_rate']}%\n"
        f"**Usuarios activos:** {stats['current_active_users']}\n"
    )

    if stats.get('average_time_days'):
        text += f"**Tiempo promedio:** {stats['average_time_days']} días\n"

    if stats.get('max_completions_global'):
        text += f"\n**Límite global:** {stats['current_completions_global']}/{stats['max_completions_global']}\n"

    if stats.get('top_completers'):
        text += "\n**🏆 Top Completadores:**\n"
        for idx, completer in enumerate(stats['top_completers'][:5], 1):
            text += f"{idx}. @{completer['username']} - {completer['completions']}x\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
