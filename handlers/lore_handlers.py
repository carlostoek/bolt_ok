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
from utils.localization import get_text
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
        await message.answer(get_text("backpack.empty_message_lore"))
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
                'description': get_text("backpack.lore_prefix", title=piece.title)
            })

    # Prepare purchased items
    purchased_items = []
    for purchase_record, shop_item in purchase_records:
        purchased_items.append({
            'type': 'item',
            'title': shop_item.name,
            'item_id': shop_item.id,
            'description': get_text("backpack.item_prefix", name=shop_item.name, price=shop_item.price)
        })

    # Combine all items
    all_items = lore_pieces + purchased_items

    # Create keyboard
    keyboard_buttons = []
    for item in all_items:
        if item['type'] == 'lore':
            keyboard_buttons.append(
                [InlineKeyboardButton(text=get_text("backpack.lore_button_prefix", title=item['title']),
                                  callback_data=f"show_lore_piece:{item['code_name']}")]
            )
        else:
            keyboard_buttons.append(
                [InlineKeyboardButton(text=get_text("backpack.item_button_prefix", title=item['title']),
                                  callback_data=f"show_purchased_item:{item['item_id']}")]
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(
        f"{get_text('backpack.title')}\n\n{get_text('backpack.header')}",
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
        await callback.answer(get_text("backpack.lore_not_found"), show_alert=True)
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
        await callback.answer(get_text("backpack.lore_display_error"), show_alert=True)
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
        await callback.answer(get_text("backpack.item_not_found"), show_alert=True)
        return

    # Get purchase details
    stmt = select(UserPurchase).where(
        UserPurchase.user_id == callback.from_user.id,
        UserPurchase.shop_item_id == int(item_id)
    )
    result = await session.execute(stmt)
    purchase = result.scalar_one_or_none()

    if not purchase:
        await callback.answer(get_text("backpack.item_not_owned"), show_alert=True)
        return

    # Create a nice message about the purchased item
    message_parts = [
        get_text("backpack.purchased_item_title", name=item.name),
        get_text("backpack.price_paid", price=purchase.price_paid),
        get_text("backpack.purchase_date", date=purchase.purchased_at.strftime('%Y-%m-%d %H:%M'))
    ]
    
    if item.description:
        message_parts.append(get_text("backpack.description", description=item.description))
    
    if item.unlocks_lore_piece_id:
        from database.models import LorePiece
        lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
        if lore_piece:
            message_parts.append(get_text("backpack.unlocks", title=lore_piece.title))
    
    message_parts.append(get_text("backpack.purchase_thanks"))

    await callback.message.answer("\n".join(message_parts))
    await callback.answer()
