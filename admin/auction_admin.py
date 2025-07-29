from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from mybot.database.models import Auction, AuctionStatus, Bid, User
from mybot.services.auction_service import (
    notify_auction_start,
    notify_auction_winner,
    get_auction_winner,
    refund_auction_bids
)
from mybot.services.config_service import ConfigService
from mybot.keyboards.admin_auction_kb import (
    get_auction_settings_kb,
    get_auction_management_kb
)

router = Router()

@router.callback_query(F.data == "admin_auction_main")
async def auction_main_menu(callback: CallbackQuery):
    """Muestra el menú principal de subastas"""
    await callback.answer("Menú de subastas")

@router.callback_query(F.data.startswith("auction_duration_"))
async def set_auction_duration(callback: CallbackQuery):
    """Configura la duración de la subasta"""
    duration = callback.data.split("_")[-1]
    await callback.answer(f"Duración configurada: {duration} horas")

@router.callback_query(F.data == "auction_basic_settings")
async def auction_basic_settings(callback: CallbackQuery, session: AsyncSession):
    """Show basic auction settings"""
    config = await ConfigService(session).get_auction_config()
    
    text = f"""
⚙️ Configuración básica de subastas

⏳ Duración predeterminada: {config.default_duration} horas
💰 Depósito mínimo: {config.min_deposit}
📊 Incremento mínimo: {config.min_increment}
"""
    keyboard = get_auction_settings_kb(basic=True)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "auction_advanced_settings")
async def auction_advanced_settings(callback: CallbackQuery, session: AsyncSession):
    """Show advanced auction settings"""
    config = await ConfigService(session).get_auction_config()
    
    text = f"""
🔧 Configuración avanzada de subastas

📢 Canal de anuncios: {config.notify_channel or 'No configurado'}
📅 Horario activo: {config.active_hours or '24/7'}
🔐 Requisitos VIP: {config.vip_requirements or 'Ninguno'}
"""
    keyboard = get_auction_settings_kb(advanced=True)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("view_auction_"))
async def view_auction(callback: CallbackQuery, session: AsyncSession):
    """Show detailed auction view"""
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if not auction:
        await callback.answer("❌ Subasta no encontrada")
        return

    text = f"""
📌 Subasta #{auction.id}
🛒 Item: {auction.item_name}
💰 Precio inicial: {auction.starting_price}
🏷️ Precio actual: {auction.current_price}
⏳ Estado: {auction.status.value}
📅 Creada: {auction.created_at}
🕒 Finaliza: {auction.end_time}
"""
    keyboard = get_auction_management_kb(auction_id)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("view_auction_details_"))
async def view_auction_details(callback: CallbackQuery, session: AsyncSession):
    """Show extended auction details with bids"""
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    bids = await session.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.created_at.desc())
        .limit(10)
    )
    
    text = f"""
📊 Detalles de subasta #{auction.id}
🛒 Item: {auction.item_name}
💰 Precio actual: {auction.current_price}
👥 Participantes: {auction.bid_count}
"""
    
    if bids:
        text += "\n🏆 Últimas ofertas:\n"
        for bid in bids.scalars():
            user = await session.get(User, bid.user_id)
            text += f"• {user.username}: {bid.amount}\n"
    
    await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data.startswith("start_auction_"))
async def start_auction(callback: CallbackQuery, session: AsyncSession):
    """Start an auction"""
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if auction.status != AuctionStatus.PENDING:
        await callback.answer("❌ Solo se pueden iniciar subastas pendientes")
        return

    auction.status = AuctionStatus.ACTIVE
    auction.start_time = datetime.now()
    auction.end_time = auction.start_time + timedelta(hours=auction.duration)
    
    await session.commit()
    
    # Notify subscribers
    await notify_auction_start(auction)
    
    await callback.answer(f"✅ Subasta #{auction_id} iniciada")
    await view_auction(callback, session)  # Refresh view

@router.callback_query(F.data.startswith("end_auction_"))
async def end_auction(callback: CallbackQuery, session: AsyncSession):
    """End an auction early"""
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if auction.status != AuctionStatus.ACTIVE:
        await callback.answer("❌ Solo se pueden finalizar subastas activas")
        return

    auction.status = AuctionStatus.COMPLETED
    auction.end_time = datetime.now()
    
    # Process winner and notifications
    winner = await get_auction_winner(session, auction_id)
    if winner:
        await notify_auction_winner(winner, auction)
    
    await session.commit()
    await callback.answer(f"🏁 Subasta #{auction_id} finalizada")
    await view_auction(callback, session)  # Refresh view

@router.callback_query(F.data.startswith("cancel_auction_"))
async def cancel_auction(callback: CallbackQuery, session: AsyncSession):
    """Cancel an auction"""
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if auction.status not in [AuctionStatus.PENDING, AuctionStatus.ACTIVE]:
        await callback.answer("❌ No se puede cancelar esta subasta")
        return

    auction.status = AuctionStatus.CANCELLED
    
    # Refund any bids if needed
    if auction.status == AuctionStatus.ACTIVE:
        await refund_auction_bids(session, auction_id)
    
    await session.commit()
    await callback.answer(f"❌ Subasta #{auction_id} cancelada")
    await view_auction(callback, session)  # Refresh view

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_auction_action(callback: CallbackQuery):
    """Confirmar acción de subasta"""
    action, _, auction_id = callback.data.split("_")[1:]
    await callback.answer(f"Confirmando {action} para subasta {auction_id}")

@router.callback_query(F.data.startswith("*_auction_*"))
async def handle_dynamic_auction(callback: CallbackQuery):
    """Manejador dinámico para acciones de subasta"""
    action = callback.data.split("_")[0]
    auction_id = callback.data.split("_")[-1]
    await callback.answer(f"Procesando {action} para subasta {auction_id}")

@router.callback_query(F.data == "edit_auction_data")
async def edit_auction_data(callback: CallbackQuery):
    """Editar datos de subasta"""
    await callback.answer()
    await callback.message.answer("✏️ Modo edición de subasta activado")

@router.callback_query(F.data == "auction_advanced_settings")
async def auction_advanced_settings(callback: CallbackQuery):
    """Mostrar configuración avanzada de subastas"""
    await callback.answer()
    await callback.message.answer("⚙ Mostrando configuración avanzada de subastas")
