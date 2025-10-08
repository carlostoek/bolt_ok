"""
Handlers administrativos para gestión de narrativa.
Permite a los admins cargar, editar y gestionar contenido narrativo.
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.message_safety import safe_answer

router = Router()

@router.message(Command("narrative_stats"))
async def narrative_admin_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas del sistema narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        from sqlalchemy import select, func
        from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
        
        # Contar fragmentos
        fragments_stmt = select(func.count()).select_from(StoryFragment)
        fragments_result = await session.execute(fragments_stmt)
        total_fragments = fragments_result.scalar() or 0
        
        # Contar decisiones
        choices_stmt = select(func.count()).select_from(NarrativeChoice)
        choices_result = await session.execute(choices_stmt)
        total_choices = choices_result.scalar() or 0
        
        # Contar usuarios con progreso narrativo
        users_stmt = select(func.count()).select_from(UserNarrativeState)
        users_result = await session.execute(users_stmt)
        active_users = users_result.scalar() or 0
        
        # Fragmentos por nivel
        level_stmt = select(StoryFragment.level, func.count()).select_from(StoryFragment).group_by(StoryFragment.level)
        level_result = await session.execute(level_stmt)
        level_distribution = dict(level_result.all())
        
        stats_text = f"""📊 **Estadísticas del Sistema Narrativo**

📚 **Contenido**:
• Fragmentos totales: {total_fragments}
• Decisiones totales: {total_choices}
• Usuarios activos: {active_users}

📈 **Distribución por Nivel**:"""
        
        for level in sorted(level_distribution.keys()):
            count = level_distribution[level]
            level_type = "Gratuito" if level <= 3 else "VIP"
            stats_text += f"\n• Nivel {level} ({level_type}): {count} fragmentos"
        
        await safe_answer(message, stats_text)
        
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")

@router.message(Command("reset_narrative"))
async def reset_user_narrative(message: Message, session: AsyncSession):
    """Reinicia la narrativa de un usuario (solo admins)."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    # Extraer user_id del comando
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await safe_answer(
            message, 
            "❌ **Uso**: `/reset_narrative <user_id>`\n\n"
            "Ejemplo: `/reset_narrative 123456789`"
        )
        return
    
    try:
        target_user_id = int(command_parts[1])
        
        # Buscar y eliminar estado narrativo del usuario
        from database.narrative_models import UserNarrativeState
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == target_user_id)
        result = await session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if user_state:
            await session.delete(user_state)
            await session.commit()
            await safe_answer(message, f"✅ **Narrativa Reiniciada**\n\nLa historia del usuario {target_user_id} ha sido reiniciada.")
        else:
            await safe_answer(message, f"❌ El usuario {target_user_id} no tiene progreso narrativo.")
            
    except ValueError:
        await safe_answer(message, "❌ ID de usuario inválido.")
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")
