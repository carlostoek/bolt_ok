from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

@router.message(F.text == "🎒 Mochila")
async def handle_backpack_button(message: Message, session: AsyncSession):
    # Import the router and use the handler directly
    from backpack import router as backpack_router
    # Trigger the backpack handler
    from aiogram import F
    from aiogram.types import Message
    # Create a fake context to trigger the handler
    # Since the handler is already registered, we can just call it directly
    for handler in backpack_router.message.handlers:
        if hasattr(handler, 'filters') and any(isinstance(f, F) and getattr(f, 'text', None) == "🎒 Mochila" for f in handler.filters):
            await handler.handler(message, session=session)
            return
    # Fallback if handler not found
    await message.answer("La mochila no está disponible en este momento.")

@router.message(F.text == "💰 Billetera")
async def handle_wallet_button(message: Message, session: AsyncSession):
    await message.answer("💰 **Tu Billetera**\n\nFuncionalidad en desarrollo...")

@router.message(F.text == "🎯 Misiones")
async def handle_missions_button(message: Message, session: AsyncSession):
    from handlers.missions_handler import show_available_missions
    fake_callback = type("cb", (), {"from_user": message.from_user, "data": "misiones_disponibles", "message": message})
    await show_available_missions(fake_callback, session)

@router.message(F.text == "⚙️ Configuración")
async def handle_config_button(message: Message, session: AsyncSession):
    await message.answer("⚙️ **Configuración**\n\nOpciones de usuario...")

@router.message(F.text == "❓ Ayuda")
async def handle_help_button(message: Message, session: AsyncSession):
    await message.answer("❓ **Ayuda**\n\nGuía de uso del bot...")

@router.message(F.text == "📖 Historia")
async def handle_narrative_button(message: Message, session: AsyncSession):
    from handlers.narrative_handler import start_narrative_command
    await start_narrative_command(message, session)
