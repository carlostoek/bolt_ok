from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from services.mission_service import MissionService
from database.models import User
from utils.localization import get_text
from aiogram import Bot

router = Router()

@router.callback_query(F.data == "misiones_disponibles")
async def show_available_missions(callback: CallbackQuery, session: AsyncSession):
    """Muestra la lista de misiones disponibles con información enriquecida."""
    await callback.answer("📋 Cargando misiones...", show_alert=False)

    user_id = callback.from_user.id
    mission_service = MissionService(session)
    
    # Obtener misiones activas filtradas por usuario
    missions = await mission_service.get_active_missions(user_id=user_id)

    if not missions:
        missions_text = "🎯 *Misiones Disponibles*\n\n"
        missions_text += "📭 No hay misiones disponibles en este momento.\n\n"
        missions_text += "¡Vuelve más tarde para nuevas misiones! ✨"
    else:
        user = await session.get(User, user_id)
        missions_text = "🎯 *Misiones Disponibles*\n\n"
        missions_text += "Completa misiones para ganar besitos y desbloquear contenido exclusivo:\n\n"
        
        for i, mission in enumerate(missions, 1):
            # Verificar estado de completado
            completed, reason = await mission_service.check_mission_completion_status(user, mission)
            status = "✅ COMPLETADA" if completed else "🔄 EN PROGRESO"
            
            missions_text += f"{i}. *{mission.name}*\n"
            missions_text += f"   📝 {mission.description}\n"
            missions_text += f"   💰 Recompensa: {mission.reward_points} besitos\n"
            missions_text += f"   📊 Estado: {status}\n"
            
            # Agregar información específica según el tipo de misión
            if mission.type == "daily":
                missions_text += "   ⏰ *Tipo:* Diaria (se renueva cada 24h)\n"
            elif mission.type == "weekly":
                missions_text += "   📅 *Tipo:* Semanal\n"
            elif mission.type == "reaction":
                missions_text += "   ❤️ *Tipo:* Reaccionar a publicaciones\n"
                missions_text += "   💡 *Cómo completar:* Ve al canal y reacciona a las publicaciones\n"
            
            missions_text += "\n"

        missions_text += "\n💡 *Consejo:* Revisa cada misión para ver instrucciones detalladas."

    # Agregar botones de acción
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Botón para recargar misiones
    builder.button(text="🔄 Actualizar", callback_data="misiones_disponibles")
    
    # Botón para volver al menú principal
    builder.button(text="🏠 Menú Principal", callback_data="main_menu")
    
    builder.adjust(1)
    
    await callback.message.edit_text(
        missions_text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
