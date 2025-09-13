from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from handlers.lore_handlers import show_lore_backpack
from handlers.missions_handler import show_available_missions
from handlers.narrative_handler import start_narrative_command

router = Router()

@router.message(F.text == "🎒 Mochila")
async def handle_backpack_button(message: Message, session: AsyncSession):
    # Directly call the lore handler function
    await show_lore_backpack(message, session)

@router.message(F.text == "💰 Billetera")
async def handle_wallet_button(message: Message, session: AsyncSession):
    await message.answer("💰 **Tu Billetera**\n\nFuncionalidad en desarrollo...")

@router.message(F.text == "🎯 Misiones")
async def handle_missions_button(message: Message, session: AsyncSession):
    # Create a mock callback to reuse the existing handler
    class MockCallback:
        def __init__(self, message):
            self.from_user = message.from_user
            self.data = "misiones_disponibles"
            self.message = message
            
        async def answer(self, *args, **kwargs):
            pass
    
    mock_callback = MockCallback(message)
    await show_available_missions(mock_callback, session)

@router.message(F.text == "⚙️ Configuración")
async def handle_config_button(message: Message, session: AsyncSession):
    await message.answer("⚙️ **Configuración**\n\nOpciones de usuario...")

@router.message(F.text == "❓ Ayuda")
async def handle_help_button(message: Message, session: AsyncSession):
    await message.answer("❓ **Ayuda**\n\nGuía de uso del bot...")

@router.message(F.text == "📖 Historia")
async def handle_narrative_button(message: Message, session: AsyncSession):
    await start_narrative_command(message, session)

@router.message(F.text == "🔓 Nivel de Muestra")
async def handle_sample_level_button(message: Message, session: AsyncSession):
    """Handle access to the sample level that requires 'Diario de Diana'"""
    # Use CoordinadorCentral to check access
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        message.from_user.id,
        AccionUsuario.VERIFICAR_ACCESO_NIVEL,
        level_name="nivel_muestra"
    )
    
    if result.get("access_granted"):
        await message.answer("🔓 **Acceso Concedido al Nivel de Muestra**\n\n¡Bienvenido al contenido exclusivo del Diario de Diana!")
        # Here you would start the actual narrative level
    else:
        await message.answer(f"❌ **Acceso Restringido**\n\n{result.get('message', 'No puedes acceder a este nivel.')}")
