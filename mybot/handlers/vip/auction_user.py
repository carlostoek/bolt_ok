from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.menu_utils import update_menu, send_temporary_reply
from keyboards.auction_kb import (
    get_auction_main_kb,
    get_auction_list_kb,
    get_auction_details_kb,
    get_bid_amount_kb,
    get_bid_confirmation_kb,
    get_auction_notifications_kb,
    get_bid_history_kb
)
from services.auction_service import AuctionService
from database.models import User, AuctionParticipant
from utils.text_utils import format_points, format_time_remaining, anonymize_username
import logging

logger = logging.getLogger(__name__)
router = Router()


class UserAuctionStates(StatesGroup):
    """States for user auction interactions."""
    placing_custom_bid = State()
    confirming_bid = State()


@router.callback_query(F.data == "auction_main")
async def auction_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Main auction menu for users."""
    user_id = callback.from_user.id
    # NOTA: Removida verificación VIP - FREE pueden ver subastas
    # La verificación VIP se hace al intentar PUJAR, no al ver

    await update_menu(
        callback,
        "🏛️ **Subastas en Tiempo Real**\n\nParticipa en subastas exclusivas y gana premios únicos.",
        get_auction_main_kb(),
        session,
        "auction_main",
    )
    await callback.answer()


@router.callback_query(F.data == "view_active_auctions")
async def view_active_auctions(callback: CallbackQuery, session: AsyncSession):
    """View all active auctions."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    auction_service = AuctionService(session)
    auctions = await auction_service.get_active_auctions()
    
    if not auctions:
        await callback.message.edit_text(
            "🔥 **Subastas Activas**\n\nNo hay subastas activas en este momento.\n\n"
            "¡Mantente atento! Pronto habrá nuevas oportunidades.",
            reply_markup=get_auction_main_kb()
        )
    else:
        text_lines = ["🔥 **Subastas Activas**\n"]
        for auction in auctions:
            time_remaining = format_time_remaining(auction.end_time)
            current_bid = auction.current_highest_bid or auction.initial_price
            participant_count = await auction_service._get_participant_count(auction.id)
            
            text_lines.append(
                f"• **{auction.name}**\n"
                f"  💰 Puja actual: {current_bid} pts\n"
                f"  👥 Participantes: {participant_count}\n"
                f"  ⏰ {time_remaining}\n"
            )
        
        await callback.message.edit_text(
            "\n".join(text_lines),
            reply_markup=get_auction_list_kb(auctions)
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_auction_"))
async def view_auction_details(callback: CallbackQuery, session: AsyncSession):
    """View detailed auction information."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    auction_id = int(callback.data.split("_")[-1])
    auction_service = AuctionService(session)
    
    details = await auction_service.get_auction_details(auction_id, user_id)
    if not details:
        await callback.answer("❌ Subasta no encontrada", show_alert=True)
        return
    
    auction = details['auction']
    
    # Build detailed message
    details_text = (
        f"🏛️ **{auction.name}**\n\n"
        f"📄 **Descripción:**\n{auction.description}\n\n"
        f"🎁 **Premio:**\n{auction.prize_description}\n\n"
        f"💰 **Precio inicial:** {auction.initial_price} pts\n"
        f"🔥 **Puja actual:** {auction.current_highest_bid or 0} pts\n"
    )
    
    if details['highest_bidder_display']:
        details_text += f"🏆 **Pujador líder:** {details['highest_bidder_display']}\n"
    
    details_text += (
        f"👥 **Participantes:** {details['participant_count']}\n"
        f"⏰ **Tiempo restante:** {details['time_remaining']}\n"
    )
    
    if details['is_participating']:
        if details['viewer_highest_bid']:
            details_text += f"\n💎 **Tu puja más alta:** {details['viewer_highest_bid']} pts\n"
        else:
            details_text += f"\n📝 **Estás participando** en esta subasta\n"
    
    if auction.status.value == 'active':
        details_text += f"\n🎯 **Puja mínima:** {details['min_next_bid']} pts"
    
    # Check if user can bid
    user = await session.get(User, user_id)
    user_can_bid = (
        auction.status.value == 'active' and 
        user and 
        user.points >= details['min_next_bid'] and
        auction.highest_bidder_id != user_id
    )
    
    await callback.message.edit_text(
        details_text,
        reply_markup=get_auction_details_kb(
            auction_id, 
            details['is_participating'], 
            auction.status.value,
            user_can_bid
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("place_bid_"))
async def start_place_bid(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start the bidding process."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    auction_id = int(callback.data.split("_")[-1])
    auction_service = AuctionService(session)
    
    details = await auction_service.get_auction_details(auction_id, user_id)
    if not details:
        await callback.answer("❌ Subasta no encontrada", show_alert=True)
        return
    
    auction = details['auction']
    user = await session.get(User, user_id)
    
    # Validate bidding conditions
    if auction.status.value != 'active':
        await callback.answer("❌ Esta subasta no está activa", show_alert=True)
        return
    
    if auction.highest_bidder_id == user_id:
        await callback.answer("❌ Ya eres el pujador más alto", show_alert=True)
        return
    
    min_bid = details['min_next_bid']
    if not user or user.points < min_bid:
        await callback.answer(
            f"❌ No tienes suficientes puntos. Necesitas {min_bid}, tienes {format_points(user.points)}",
            show_alert=True
        )
        return
    
    # Store auction info in state
    await state.update_data(auction_id=auction_id, min_bid=min_bid)
    
    await callback.message.edit_text(
        f"💰 **Hacer Puja - {auction.name}**\n\n"
        f"🎯 **Puja mínima:** {min_bid} pts\n"
        f"💎 **Tus puntos:** {format_points(user.points)} pts\n\n"
        f"Selecciona la cantidad que deseas pujar:",
        reply_markup=get_bid_amount_kb(min_bid)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quick_bid_"))
async def quick_bid(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle quick bid selection."""
    user_id = callback.from_user.id
    amount = int(callback.data.split("_")[-1])
    
    data = await state.get_data()
    auction_id = data.get('auction_id')
    
    if not auction_id:
        await callback.answer("❌ Error en la sesión", show_alert=True)
        return
    
    await state.update_data(bid_amount=amount)
    
    auction_service = AuctionService(session)
    details = await auction_service.get_auction_details(auction_id, user_id)
    auction = details['auction']
    
    await callback.message.edit_text(
        f"💰 **Confirmar Puja**\n\n"
        f"🏛️ **Subasta:** {auction.name}\n"
        f"💎 **Tu puja:** {amount} pts\n"
        f"🔥 **Puja actual:** {auction.current_highest_bid or 0} pts\n\n"
        f"¿Confirmas esta puja?",
        reply_markup=get_bid_confirmation_kb(auction_id, amount)
    )
    await callback.answer()


@router.callback_query(F.data == "custom_bid_amount")
async def custom_bid_amount(callback: CallbackQuery, state: FSMContext):
    """Request custom bid amount."""
    data = await state.get_data()
    min_bid = data.get('min_bid', 0)
    
    await callback.message.edit_text(
        f"✏️ **Puja Personalizada**\n\n"
        f"Ingresa la cantidad que deseas pujar (mínimo {min_bid} pts):",
        reply_markup=get_auction_main_kb()
    )
    await state.set_state(UserAuctionStates.placing_custom_bid)
    await callback.answer()


@router.message(UserAuctionStates.placing_custom_bid)
async def process_custom_bid(message: Message, state: FSMContext, session: AsyncSession):
    """Process custom bid amount."""
    user_id = message.from_user.id
    
    try:
        amount = int(message.text.strip())
    except ValueError:
        await send_temporary_reply(message, "❌ Ingresa un número válido.")
        return
    
    data = await state.get_data()
    auction_id = data.get('auction_id')
    min_bid = data.get('min_bid', 0)
    
    if amount < min_bid:
        await send_temporary_reply(message, f"❌ La puja mínima es {min_bid} pts.")
        return
    
    user = await session.get(User, user_id)
    if not user or user.points < amount:
        await send_temporary_reply(
            message, 
            f"❌ No tienes suficientes puntos. Tienes {format_points(user.points)}, necesitas {amount}."
        )
        return
    
    await state.update_data(bid_amount=amount)
    
    auction_service = AuctionService(session)
    details = await auction_service.get_auction_details(auction_id, user_id)
    auction = details['auction']
    
    await message.answer(
        f"💰 **Confirmar Puja**\n\n"
        f"🏛️ **Subasta:** {auction.name}\n"
        f"💎 **Tu puja:** {amount} pts\n"
        f"🔥 **Puja actual:** {auction.current_highest_bid or 0} pts\n\n"
        f"¿Confirmas esta puja?",
        reply_markup=get_bid_confirmation_kb(auction_id, amount)
    )
    await state.set_state(UserAuctionStates.confirming_bid)


@router.callback_query(F.data.startswith("confirm_bid_"))
async def confirm_bid(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    """Confirm and place the bid."""
    user_id = callback.from_user.id
    
    parts = callback.data.split("_")
    auction_id = int(parts[2])
    amount = int(parts[3])
    
    auction_service = AuctionService(session)
    success, message = await auction_service.place_bid(auction_id, user_id, amount, bot)
    
    if success:
        await callback.message.edit_text(
            f"✅ **Puja Realizada**\n\n"
            f"{message}\n\n"
            f"🔔 Recibirás notificaciones si alguien supera tu puja.",
            reply_markup=get_auction_main_kb()
        )
        
        logger.info(f"User {user_id} placed bid of {amount} in auction {auction_id}")
    else:
        await callback.message.edit_text(
            f"❌ **Error al Pujar**\n\n"
            f"{message}",
            reply_markup=get_auction_main_kb()
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_bid")
async def cancel_bid(callback: CallbackQuery, state: FSMContext):
    """Cancel the bidding process."""
    await state.clear()
    await callback.message.edit_text(
        "❌ **Puja Cancelada**\n\nPuedes intentar pujar nuevamente cuando quieras.",
        reply_markup=get_auction_main_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "view_my_auctions")
async def view_my_auctions(callback: CallbackQuery, session: AsyncSession):
    """View user's participated auctions."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    auction_service = AuctionService(session)
    auctions = await auction_service.get_user_auctions(user_id, include_ended=False)
    
    if not auctions:
        await callback.message.edit_text(
            "📋 **Mis Subastas**\n\nNo estás participando en ninguna subasta actualmente.\n\n"
            "¡Explora las subastas activas para participar!",
            reply_markup=get_auction_main_kb()
        )
    else:
        text_lines = ["📋 **Mis Subastas Activas**\n"]
        for auction in auctions:
            # Get user's highest bid
            user_bid = await auction_service._get_user_highest_bid(auction.id, user_id)
            is_winning = auction.highest_bidder_id == user_id
            
            status_emoji = "🏆" if is_winning else "📝"
            status_text = "Ganando" if is_winning else "Participando"
            
            text_lines.append(
                f"{status_emoji} **{auction.name}**\n"
                f"  💎 Tu puja: {user_bid or 0} pts\n"
                f"  🔥 Puja actual: {auction.current_highest_bid or 0} pts\n"
                f"  📊 Estado: {status_text}\n"
            )
        
        await callback.message.edit_text(
            "\n".join(text_lines),
            reply_markup=get_auction_list_kb(auctions)
        )
    
    await callback.answer()


@router.callback_query(F.data == "view_auction_history")
async def view_auction_history(callback: CallbackQuery, session: AsyncSession):
    """View user's auction history."""
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    auction_service = AuctionService(session)
    auctions = await auction_service.get_user_auctions(user_id, include_ended=True)
    
    # Filter only ended auctions
    ended_auctions = [a for a in auctions if a.status.value == 'ended']
    
    if not ended_auctions:
        await callback.message.edit_text(
            "🏆 **Historial de Subastas**\n\nNo tienes historial de subastas finalizadas.",
            reply_markup=get_auction_main_kb()
        )
    else:
        text_lines = ["🏆 **Historial de Subastas**\n"]
        for auction in ended_auctions[-10:]:  # Last 10 auctions
            user_bid = await auction_service._get_user_highest_bid(auction.id, user_id)
            won = auction.winner_id == user_id
            
            result_emoji = "🏆" if won else "📝"
            result_text = "Ganaste" if won else "Participaste"
            
            text_lines.append(
                f"{result_emoji} **{auction.name}**\n"
                f"  💎 Tu puja: {user_bid or 0} pts\n"
                f"  🏁 Resultado: {result_text}\n"
                f"  📅 {auction.ended_at.strftime('%d/%m/%Y')}\n"
            )
        
        await callback.message.edit_text(
            "\n".join(text_lines),
            reply_markup=get_auction_main_kb()
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_notifications_"))
async def toggle_notifications(callback: CallbackQuery, session: AsyncSession):
    """Toggle auction notifications for user."""
    user_id = callback.from_user.id
    auction_id = int(callback.data.split("_")[-1])
    
    # Get current notification status
    from sqlalchemy import select
    stmt = select(AuctionParticipant).where(
        AuctionParticipant.auction_id == auction_id,
        AuctionParticipant.user_id == user_id
    )
    result = await session.execute(stmt)
    participant = result.scalar_one_or_none()
    
    if not participant:
        await callback.answer("❌ No estás participando en esta subasta", show_alert=True)
        return
    
    # Toggle notifications
    participant.notifications_enabled = not participant.notifications_enabled
    await session.commit()
    
    status = "activadas" if participant.notifications_enabled else "desactivadas"
    await callback.answer(f"🔔 Notificaciones {status}", show_alert=True)
    
    # Return to auction details
    await view_auction_details(callback, session)
