from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.config_service import ConfigService
from sqlalchemy.ext.asyncio import AsyncSession


async def get_admin_main_kb(session: AsyncSession = None):
    """Return the main admin inline keyboard with comprehensive layout."""
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
    
    # Fila 2: Sistemas de gamificación y narrativa
    builder.button(text="🎮 Gamificación", callback_data="admin_manage_content")
    builder.button(text="📖 Narrativa", callback_data="admin_fragments_manage")
    
    # Fila 3: Comercio y eventos
    builder.button(text="🏛️ Subastas", callback_data="admin_auction_main")
    builder.button(text="🎉 Eventos", callback_data="admin_manage_events_sorteos")
    
    # Fila 4: Sistema y estadísticas
    builder.button(text="📊 Estadísticas", callback_data="admin_stats")
    builder.button(text="⚙️ Configuración", callback_data="admin_config")
    
    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    builder.button(text="↩️ Volver", callback_data="admin_back")
    
    # Distribución: 2x2x2x2x2 = 10 botones total
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()
