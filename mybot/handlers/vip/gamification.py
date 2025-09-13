"""
Enhanced gamification handlers with improved menu management.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from utils.user_roles import get_user_role
from services.point_service import PointService
from services.achievement_service import AchievementService
from services.mission_service import MissionService
from services.reward_service import RewardService
from utils.messages import BOT_MESSAGES
from services.message_service import MessageService
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("rewards"))
async def rewards_command(message: Message, session: AsyncSession):
    """Enhanced rewards command with clean menu management."""
    user_id = message.from_user.id
    
    # Check if user has access to rewards (VIP or admin)
    role = await get_user_role(message.bot, user_id, session=session)
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\n"
            "Esta función está disponible solo para miembros VIP.\n"
            "¡Suscríbete para acceder a todas las recompensas!",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("rewards", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "rewards")
    except Exception as e:
        logger.error(f"Error showing rewards for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron cargar las recompensas. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data == "menu_principal")
async def go_to_main_menu_from_inline(callback: CallbackQuery, session: AsyncSession):
    """Enhanced main menu navigation."""
    user_id = callback.from_user.id
    
    try:
        text, keyboard = await menu_factory.create_menu("main", user_id, session, callback.bot)
        await menu_manager.update_menu(callback, text, keyboard, session, "main")
    except Exception as e:
        logger.error(f"Error navigating to main menu for user {user_id}: {e}")
        await callback.answer("Error al cargar el menú principal", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    """Enhanced menu navigation with improved error handling."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    try:
        menu_type = callback.data.split(":")[1]
        
        # Check access for VIP-only features
        vip_only_menus = ["rewards", "ranking", "auctions", "shop_inventory"]
        if menu_type in vip_only_menus and role not in ["vip", "admin"]:
            await callback.answer(
                "Esta función está disponible solo para miembros VIP.", 
                show_alert=True
            )
            return
        
        # Handle shop menus specially
        if menu_type == "shop":
            from handlers.shop_handler import shop_menu_callback
            return await shop_menu_callback(callback, session)
        elif menu_type == "shop_inventory":
            from handlers.shop_handler import shop_inventory_callback
            return await shop_inventory_callback(callback, session)
        
        # Handle other menus through menu factory
        text, keyboard = await menu_factory.create_menu(menu_type, user_id, session, callback.bot)
        await menu_manager.update_menu(callback, text, keyboard, session, menu_type)
    except Exception as e:
        logger.error(f"Error in menu navigation for user {user_id}: {e}")
        await callback.answer("Error al cargar el menú", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "view_level")
async def show_user_level(callback: CallbackQuery, session: AsyncSession):
    """Show user level with enhanced formatting."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Debes iniciar con /start", show_alert=True)
        return

    from services.level_service import get_next_level_info
    from utils.messages import NIVEL_TEMPLATE
    
    info = get_next_level_info(int(user.points))
    text = NIVEL_TEMPLATE.format(
        current_level=info["current_level"],
        points=int(user.points),
        percentage=info["percentage_to_next"],
        points_needed=info["points_needed"],
        next_level=info["next_level"],
    )

    from keyboards.common import get_back_kb
    await menu_manager.update_menu(
        callback, 
        text, 
        get_back_kb("menu:profile"), 
        session, 
        "level_view"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("claim_reward_"))
async def handle_claim_reward_callback(callback: CallbackQuery, session: AsyncSession):
    """Enhanced reward claiming with better feedback."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    try:
        reward_id = int(callback.data.split("_")[-1])
        reward_service = RewardService(session)
        success, message = await reward_service.claim_reward(user_id, reward_id)

        if success:
            # Refresh rewards menu
            text, keyboard = await menu_factory.create_menu("rewards", user_id, session, callback.bot)
            success_text = f"✅ **¡Recompensa Reclamada!**\n\n{message}\n\n" + text.split('\n\n', 1)[-1]
            await menu_manager.update_menu(callback, success_text, keyboard, session, "rewards")
            await callback.answer("¡Recompensa reclamada exitosamente!", show_alert=True)
        else:
            await callback.answer(message, show_alert=True)
    except Exception as e:
        logger.error(f"Error claiming reward for user {user_id}: {e}")
        await callback.answer("Error al reclamar la recompensa", show_alert=True)

@router.callback_query(F.data.startswith("mission_"))
async def handle_mission_details_callback(callback: CallbackQuery, session: AsyncSession):
    """Enhanced mission details with better navigation."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    try:
        mission_id = callback.data[len("mission_"):]
        mission_service = MissionService(session)
        mission = await mission_service.get_mission_by_id(mission_id)

        if not mission:
            await callback.answer("Misión no encontrada.", show_alert=True)
            return

        from utils.message_utils import get_mission_details_message
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        mission_details_message = await get_mission_details_message(mission)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Completar Misión", callback_data=f"complete_mission_{mission_id}")],
                [InlineKeyboardButton(text="⬅️ Volver a Misiones", callback_data="menu:missions")],
                [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")],
            ]
        )

        await menu_manager.update_menu(callback, mission_details_message, keyboard, session, "mission_details")
    except Exception as e:
        logger.error(f"Error showing mission details for user {user_id}: {e}")
        await callback.answer("Error al cargar los detalles de la misión", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("complete_mission_"))
async def handle_complete_mission_callback(callback: CallbackQuery, session: AsyncSession):
    """Enhanced mission completion with better feedback."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    try:
        mission_id = callback.data[len("complete_mission_"):]
        mission_service = MissionService(session)
        user = await session.get(User, user_id)
        mission = await mission_service.get_mission_by_id(mission_id)

        if not user or not mission:
            await callback.answer("Error: Usuario o misión no encontrada.", show_alert=True)
            return

        # Check if already completed
        is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
        if is_completed_for_period:
            await callback.answer("Ya completaste esta misión. ¡Pronto habrá más!", show_alert=True)
            return

        # Complete mission
        completed, completed_mission_obj = await mission_service.complete_mission(
            user_id, mission_id, bot=callback.bot
        )

        if completed:
            # Show success and return to missions menu
            text, keyboard = await menu_factory.create_menu("missions", user_id, session, callback.bot)
            success_text = f"🎉 **¡Misión Completada!**\n\n" \
                          f"Has completado '{mission.name}' y ganado {mission.reward_points} puntos.\n\n" + \
                          text.split('\n\n', 1)[-1]
            
            await menu_manager.update_menu(callback, success_text, keyboard, session, "missions")
            await callback.answer("¡Misión completada exitosamente!", show_alert=True)
        else:
            await callback.answer(
                "No puedes completar esta misión ahora mismo o requiere una acción externa.",
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Error completing mission for user {user_id}: {e}")
        await callback.answer("Error al completar la misión", show_alert=True)

@router.message(F.text.regexp("/checkin"))
async def handle_daily_checkin(message: Message, session: AsyncSession, bot: Bot):
    """Enhanced daily checkin with better feedback."""
    user_id = message.from_user.id
    role = await get_user_role(bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return
    
    try:
        service = PointService(session)
        success, progress = await service.daily_checkin(user_id, bot)
        
        if success:
            mission_service = MissionService(session)
            completed_challenges = await mission_service.increment_challenge_progress(
                user_id, "checkins", bot=bot
            )
            await mission_service.update_progress(
                user_id, "login_streak", current_value=progress.checkin_streak, bot=bot
            )
            
            success_text = f"✅ **Check-in Exitoso**\n\n" \
                          f"Has ganado 10 puntos.\n" \
                          f"Racha actual: {progress.checkin_streak} días"
            
            if completed_challenges:
                success_text += f"\n\n🎯 ¡Desafío completado! +100 puntos adicionales"
            
            await menu_manager.send_temporary_message(message, success_text, auto_delete_seconds=8)
        else:
            await menu_manager.send_temporary_message(
                message,
                "ℹ️ **Check-in Ya Realizado**\n\nYa realizaste tu check-in hoy. Vuelve mañana.",
                auto_delete_seconds=5
            )
    except Exception as e:
        logger.error(f"Error in daily checkin for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar el check-in. Intenta nuevamente.",
            auto_delete_seconds=5
        )

# Reply keyboard handlers with enhanced experience
@router.message(F.text == "👤 Perfil")
async def show_profile_from_reply_keyboard(message: Message, session: AsyncSession):
    """Enhanced profile display from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("profile", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "profile")
    except Exception as e:
        logger.error(f"Error showing profile for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar tu perfil. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.message(F.text == "🗺 Misiones")
async def show_missions_from_reply_keyboard(message: Message, session: AsyncSession):
    """Enhanced missions display from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("missions", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "missions")
    except Exception as e:
        logger.error(f"Error showing missions for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron cargar las misiones. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.message(F.text == "🎁 Recompensas")
async def show_rewards_from_reply_keyboard(message: Message, session: AsyncSession):
    """Enhanced rewards display from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("rewards", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "rewards")
    except Exception as e:
        logger.error(f"Error showing rewards for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron cargar las recompensas. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.message(F.text == "🏛️ Subastas")
async def show_auctions_from_reply_keyboard(message: Message, session: AsyncSession):
    """Enhanced auctions display from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("auctions", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "auctions")
    except Exception as e:
        logger.error(f"Error showing auctions for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron cargar las subastas. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.message(F.text == "🏆 Ranking")
async def show_ranking_from_reply_keyboard(message: Message, session: AsyncSession):
    """Enhanced ranking display from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Restringido**\n\nEsta función está disponible solo para miembros VIP.",
            auto_delete_seconds=5
        )
        return


@router.message(Command("weeklyranking"))
async def show_weekly_ranking(message: Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    role = await get_user_role(bot, user_id, session=session)
    if role not in ["vip", "admin"]:
        await message.answer("Comando disponible solo para VIP")
        return
    msg_service = MessageService(session, bot)
    ranking = await msg_service.get_weekly_reaction_ranking()
    from utils.message_utils import get_weekly_reaction_ranking_message
    text = await get_weekly_reaction_ranking_message(ranking, session, user_id)
    await message.answer(text)
    
    try:
        text, keyboard = await menu_factory.create_menu("ranking", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "ranking")
    except Exception as e:
        logger.error(f"Error showing ranking for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el ranking. Intenta nuevamente.",
            auto_delete_seconds=5
        )

@router.message(F.text & ~F.text.startswith("/"))
async def handle_unrecognized_text(message: Message, session: AsyncSession, bot: Bot):
    """Enhanced handler for unrecognized text with better user guidance."""
    user_id = message.from_user.id
    role = await get_user_role(bot, user_id, session=session)

    try:
        text, keyboard = await menu_factory.create_menu("main", user_id, session, bot)
        
        # Add helpful message about unrecognized command
        help_text = "ℹ️ **Comando No Reconocido**\n\n" \
                   "No entendí ese comando. Aquí tienes el menú principal:\n\n" + \
                   text.split('\n\n', 1)[-1]
        
        await menu_manager.show_menu(message, help_text, keyboard, session, "main")
    except Exception as e:
        logger.error(f"Error handling unrecognized text for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nHubo un problema. Usa /start para volver al menú principal.",
            auto_delete_seconds=5
        )

    logger.warning(f"Unrecognized message from user {user_id}: {message.text}")
