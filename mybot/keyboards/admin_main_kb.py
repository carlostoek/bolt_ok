from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.config_service import ConfigService
from sqlalchemy.ext.asyncio import AsyncSession


async def get_admin_main_kb(session: AsyncSession = None):
    """Return the main admin inline keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Gestión de canales principales con nombres personalizados
    vip_text = "💎 Canal VIP"
    free_text = "💬 Canal Free"
    
    # Si tenemos una sesión, intentamos obtener los nombres personalizados
    if session:
        config = ConfigService(session)
        vip_name = await config.get_vip_channel_name()
        free_name = await config.get_free_channel_name()
        
        if vip_name:
            vip_text = f"💎 {vip_name}"
        if free_name:
            free_text = f"💬 {free_name}"
    
    builder.button(text=vip_text, callback_data="admin_vip")
    builder.button(text=free_text, callback_data="admin_free")
    
    # Fila 2: Entretenimiento y juegos
    builder.button(text="🎮 Juego Kinky", callback_data="admin_kinky_game")
    builder.button(text="📊 Estadísticas", callback_data="admin_stats")
    
    # Fila 3: Configuración y navegación
    builder.button(text="⚙️ Configuración", callback_data="admin_config")
    builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    
    # Fila 4: Navegación
    builder.button(text="↩️ Volver", callback_data="admin_back")
    
    # Distribución: 2x2, luego 2x1, luego 1
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()
