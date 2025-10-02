"""
Admin Handler para User Journey Management

Permite a los admins:
- Ver estadísticas de milestones
- Forzar procesamiento manual
- Testear milestones específicos
- Ver estado de journey de usuarios
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from utils.user_roles import is_admin
from services.user_journey_service import UserJourneyService
from services.user_service import UserService
from database.models import UserMilestone, User
from keyboards.admin_journey_kb import get_journey_main_keyboard, get_milestone_test_keyboard
from keyboards.common import get_back_kb

logger = logging.getLogger(__name__)
router = Router()


class AdminJourneyStates(StatesGroup):
    """Estados FSM para journey admin"""
    waiting_for_user_id = State()
    waiting_for_test_user_id = State()


# ========== MENÚ PRINCIPAL ==========

@router.callback_query(F.data == "journey_main")
async def show_journey_main_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Muestra el menú principal del Journey admin"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear()

    text = (
        "🎯 **Journey Management**\n\n"
        "Panel de administración del sistema de milestones automáticos.\n\n"
        "Aquí puedes monitorear, testear y gestionar el journey de los usuarios."
    )

    await callback.message.edit_text(text, reply_markup=get_journey_main_keyboard())
    await callback.answer()


# ========== ESTADÍSTICAS ==========

@router.callback_query(F.data == "journey_stats")
async def show_journey_stats(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas del journey"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Contar usuarios totales
        stmt = select(func.count(User.id))
        result = await session.execute(stmt)
        total_users = result.scalar()

        # Contar milestones completados por tipo
        stmt_day1 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_1",
            UserMilestone.completed == True
        )
        result = await session.execute(stmt_day1)
        day1_completed = result.scalar()

        stmt_day7 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_7",
            UserMilestone.completed == True
        )
        result = await session.execute(stmt_day7)
        day7_completed = result.scalar()

        stmt_day30 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_30",
            UserMilestone.completed == True
        )
        result = await session.execute(stmt_day30)
        day30_completed = result.scalar()

        # Contar milestones pendientes
        stmt_pending_day1 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_1",
            UserMilestone.completed == False
        )
        result = await session.execute(stmt_pending_day1)
        day1_pending = result.scalar()

        stmt_pending_day7 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_7",
            UserMilestone.completed == False
        )
        result = await session.execute(stmt_pending_day7)
        day7_pending = result.scalar()

        stmt_pending_day30 = select(func.count(UserMilestone.id)).where(
            UserMilestone.milestone_type == "day_30",
            UserMilestone.completed == False
        )
        result = await session.execute(stmt_pending_day30)
        day30_pending = result.scalar()

        # Calcular tasas de conversión
        day1_rate = (day1_completed / total_users * 100) if total_users > 0 else 0
        day7_rate = (day7_completed / total_users * 100) if total_users > 0 else 0
        day30_rate = (day30_completed / total_users * 100) if total_users > 0 else 0

        text = (
            "📊 **Estadísticas del Journey**\n\n"
            f"**Usuarios totales:** {total_users}\n\n"
            "**Day 1 - Bienvenida:**\n"
            f"✅ Completados: {day1_completed} ({day1_rate:.1f}%)\n"
            f"⏳ Pendientes: {day1_pending}\n\n"
            "**Day 7 - Oferta VIP:**\n"
            f"✅ Completados: {day7_completed} ({day7_rate:.1f}%)\n"
            f"⏳ Pendientes: {day7_pending}\n\n"
            "**Day 30 - Final:**\n"
            f"✅ Completados: {day30_completed} ({day30_rate:.1f}%)\n"
            f"⏳ Pendientes: {day30_pending}\n"
        )

        await callback.message.edit_text(text, reply_markup=get_back_kb("journey_main"))
        await callback.answer()

    except Exception as e:
        logger.error(f"Error mostrando estadísticas del journey: {e}")
        await callback.answer(f"Error: {str(e)}", show_alert=True)


# ========== FORZAR PROCESAMIENTO ==========

@router.callback_query(F.data == "journey_force_process")
async def force_process_milestones(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Fuerza el procesamiento inmediato de todos los milestones pendientes"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await callback.answer("⏳ Procesando milestones...", show_alert=True)

    try:
        journey_service = UserJourneyService(session)
        stats = await journey_service.process_all_milestones(bot)

        text = (
            "✅ **Procesamiento Completado**\n\n"
            f"**Day 1 procesados:** {stats['day_1_processed']}\n"
            f"**Day 7 procesados:** {stats['day_7_processed']}\n"
            f"**Day 30 procesados:** {stats['day_30_processed']}\n"
            f"**Errores:** {stats['errors']}\n"
        )

        await callback.message.edit_text(text, reply_markup=get_back_kb("journey_main"))

    except Exception as e:
        logger.error(f"Error forzando procesamiento: {e}")
        await callback.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_kb("journey_main")
        )


# ========== TEST MILESTONE ==========

@router.callback_query(F.data == "journey_test")
async def start_milestone_test(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el test de un milestone"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "🧪 **Test de Milestone**\n\n"
        "Selecciona qué milestone quieres testear:"
    )

    await callback.message.edit_text(text, reply_markup=get_milestone_test_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("journey_test_day_"))
async def select_milestone_to_test(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Usuario selecciona el milestone a testear"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    milestone_type = callback.data.split("journey_test_day_")[-1]
    milestone_type = f"day_{milestone_type}"

    await state.update_data(test_milestone_type=milestone_type)

    milestone_names = {
        "day_1": "Day 1 - Bienvenida",
        "day_7": "Day 7 - Oferta VIP",
        "day_30": "Day 30 - Final"
    }

    text = (
        f"🧪 **Test: {milestone_names.get(milestone_type)}**\n\n"
        "Envía el **user_id** del usuario al que quieres enviar este milestone:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("journey_main"))
    await state.set_state(AdminJourneyStates.waiting_for_test_user_id)
    await callback.answer()


@router.message(AdminJourneyStates.waiting_for_test_user_id)
async def process_test_user_id(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Procesa el user_id para test"""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ingresa un user_id numérico válido:")
        return

    data = await state.get_data()
    milestone_type = data.get("test_milestone_type")

    # Verificar que el usuario existe
    user_service = UserService(session)
    user = await user_service.get_user(user_id)

    if not user:
        await message.answer(
            f"❌ Usuario {user_id} no encontrado en la base de datos.",
            reply_markup=get_back_kb("journey_main")
        )
        await state.clear()
        return

    # Enviar milestone
    try:
        journey_service = UserJourneyService(session)

        if milestone_type == "day_1":
            success = await journey_service.process_day_1_milestone(user, bot)
        elif milestone_type == "day_7":
            success = await journey_service.process_day_7_milestone(user, bot)
        elif milestone_type == "day_30":
            success = await journey_service.process_day_30_milestone(user, bot)
        else:
            success = False

        if success:
            await message.answer(
                f"✅ Milestone {milestone_type} enviado a usuario {user_id}",
                reply_markup=get_back_kb("journey_main")
            )
        else:
            await message.answer(
                f"❌ Error enviando milestone {milestone_type} a usuario {user_id}",
                reply_markup=get_back_kb("journey_main")
            )

        await state.clear()

    except Exception as e:
        logger.error(f"Error testeando milestone: {e}")
        await message.answer(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_kb("journey_main")
        )
        await state.clear()


# ========== VER USUARIO ==========

@router.callback_query(F.data == "journey_view_user")
async def start_view_user_journey(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia la vista de journey de un usuario"""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "👤 **Ver Journey de Usuario**\n\n"
        "Envía el **user_id** del usuario:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_kb("journey_main"))
    await state.set_state(AdminJourneyStates.waiting_for_user_id)
    await callback.answer()


@router.message(AdminJourneyStates.waiting_for_user_id)
async def process_view_user_id(message: Message, session: AsyncSession, state: FSMContext):
    """Muestra el journey de un usuario específico"""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ingresa un user_id numérico válido:")
        return

    # Obtener usuario
    user_service = UserService(session)
    user = await user_service.get_user(user_id)

    if not user:
        await message.answer(
            f"❌ Usuario {user_id} no encontrado.",
            reply_markup=get_back_kb("journey_main")
        )
        await state.clear()
        return

    # Obtener milestones del usuario
    stmt = select(UserMilestone).where(UserMilestone.user_id == user_id)
    result = await session.execute(stmt)
    milestones = result.scalars().all()

    text = (
        f"👤 **Journey de Usuario {user_id}**\n\n"
        f"**Username:** @{user.username or 'Sin username'}\n"
        f"**Rol:** {user.role}\n"
        f"**Registrado:** {user.joined_at.strftime('%Y-%m-%d') if user.joined_at else 'N/A'}\n\n"
        "**Milestones:**\n"
    )

    milestone_map = {m.milestone_type: m for m in milestones}

    for mtype in ["day_1", "day_7", "day_30"]:
        milestone = milestone_map.get(mtype)
        if milestone:
            status = "✅ Completado" if milestone.completed else "⏳ Pendiente"
            completed_date = milestone.completed_at.strftime('%Y-%m-%d %H:%M') if milestone.completed_at else "-"
            text += f"\n**{mtype.upper()}:** {status}\n"
            if milestone.completed:
                text += f"  Completado: {completed_date}\n"
        else:
            text += f"\n**{mtype.upper()}:** ❌ No inicializado\n"

    await message.answer(text, reply_markup=get_back_kb("journey_main"))
    await state.clear()
