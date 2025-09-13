"""Handlers para mostrar y gestionar las piezas de lore desbloqueadas."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import LorePiece, UserLorePiece
from aiogram import Bot


logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("mochila"))
async def show_lore_backpack(message: Message, session: AsyncSession) -> None:
    """Muestra todas las pistas desbloqueadas y ítems comprados por el usuario."""
    # Get lore pieces
    stmt = select(UserLorePiece).where(UserLorePiece.user_id == message.from_user.id)
    result = await session.execute(stmt)
    lore_records = result.scalars().all()

    # Get purchased items
    from database.models import UserPurchase, ShopItem
    stmt = select(UserPurchase, ShopItem).join(
        ShopItem, UserPurchase.shop_item_id == ShopItem.id
    ).where(UserPurchase.user_id == message.from_user.id)
    result = await session.execute(stmt)
    purchase_records = result.all()

    if not lore_records and not purchase_records:
        await message.answer("Tu mochila está vacía. ¡Compra ítems en la tienda o desbloquea pistas!")
        return

    # Prepare lore pieces
    lore_pieces = []
    for rec in lore_records:
        piece = await session.get(LorePiece, rec.lore_piece_id)
        if piece:
            lore_pieces.append({
                'type': 'lore',
                'title': piece.title,
                'code_name': piece.code_name,
                'description': f"Pista: {piece.title}"
            })

    # Prepare purchased items
    purchased_items = []
    for purchase_record, shop_item in purchase_records:
        purchased_items.append({
            'type': 'item',
            'title': shop_item.name,
            'item_id': shop_item.id,
            'description': f"Comprado: {shop_item.name} ({shop_item.price} besitos)"
        })

    # Combine all items
    all_items = lore_pieces + purchased_items

    # Create keyboard
    keyboard_buttons = []
    for item in all_items:
        if item['type'] == 'lore':
            keyboard_buttons.append(
                [InlineKeyboardButton(text=f"📖 {item['title']}", callback_data=f"show_lore_piece:{item['code_name']}")]
            )
        else:
            keyboard_buttons.append(
                [InlineKeyboardButton(text=f"🛍️ {item['title']}", callback_data=f"show_purchased_item:{item['item_id']}")]
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(
        "🎒 **Tu Mochila**\n\nAquí están todos tus ítems comprados y pistas desbloqueadas:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("show_lore_piece:"))
async def show_lore_piece(callback: CallbackQuery, session: AsyncSession) -> None:
    """Envía el contenido de una pista al usuario."""
    code = callback.data.split(":", 1)[1]
    stmt = select(LorePiece).where(LorePiece.code_name == code)
    result = await session.execute(stmt)
    piece = result.scalar_one_or_none()

    if not piece:
        await callback.answer("Pista no encontrada", show_alert=True)
        return

    try:
        if piece.content_type == "text":
            await callback.message.answer(piece.content)
        elif piece.content_type == "image":
            await callback.message.answer_photo(piece.content)
        elif piece.content_type == "video":
            await callback.message.answer_video(piece.content)
        else:
            await callback.message.answer(piece.content)
    except Exception as exc:
        logger.error("Error sending lore piece %s: %s", code, exc)
        await callback.answer("No se pudo mostrar la pista", show_alert=True)
        return

    await callback.answer()

@router.callback_query(F.data.startswith("show_purchased_item:"))
async def show_purchased_item(callback: CallbackQuery, session: AsyncSession) -> None:
    """Muestra información sobre un ítem comprado."""
    item_id = callback.data.split(":", 1)[1]
    
    from database.models import ShopItem, UserPurchase
    stmt = select(ShopItem).where(ShopItem.id == int(item_id))
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        await callback.answer("Ítem no encontrado", show_alert=True)
        return

    # Get purchase details
    stmt = select(UserPurchase).where(
        UserPurchase.user_id == callback.from_user.id,
        UserPurchase.shop_item_id == int(item_id)
    )
    result = await session.execute(stmt)
    purchase = result.scalar_one_or_none()

    if not purchase:
        await callback.answer("No tienes este ítem", show_alert=True)
        return

    # Create a nice message about the purchased item
    message = f"🛍️ **{item.name}**\n\n"
    message += f"💎 Precio pagado: {purchase.price_paid} besitos\n"
    message += f"📅 Comprado el: {purchase.purchased_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    if item.description:
        message += f"📝 Descripción: {item.description}\n\n"
    
    if item.unlocks_lore_piece_id:
        from database.models import LorePiece
        lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
        if lore_piece:
            message += f"✨ Desbloquea: {lore_piece.title}\n"
    
    message += "\n¡Gracias por tu compra! 💋"

    await callback.message.answer(message)
    await callback.answer()
