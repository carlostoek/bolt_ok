"""
Handlers administrativos para gestión de narrativa.
Permite a los admins cargar, editar y gestionar contenido narrativo.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Document
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
import tempfile

from services.narrative_loader import NarrativeLoader
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from utils.localization import get_text

router = Router()

class NarrativeAdminStates(StatesGroup):
    waiting_for_narrative_file = State()
    waiting_for_fragment_json = State()

@router.message(Command("load_narrative"))
async def load_narrative_command(message: Message, session: AsyncSession):
    """Carga fragmentos narrativos desde la carpeta narrative_fragments."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, get_text("admin_narrative_handlers.admins_only"))
        return
    
    try:
        loader = NarrativeLoader(session)
        
        # Intentar cargar desde directorio
        await loader.load_fragments_from_directory("mybot/narrative_fragments")
        
        # Si no hay archivos, cargar narrativa por defecto
        await loader.load_default_narrative()
        
        await safe_answer(message, get_text("admin_narrative_handlers.narrative_loaded"))
        
    except Exception as e:
        await safe_answer(message, get_text("admin_narrative_handlers.error", error=str(e)))

@router.message(Command("upload_narrative"))
async def upload_narrative_command(message: Message, session: AsyncSession, state: FSMContext):
    """Inicia el proceso para subir un archivo narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, get_text("admin_narrative_handlers.admins_only"))
        return
    
    await safe_answer(
        message,
        get_text("admin_narrative_handlers.upload_narrative_prompt")
    )
    await state.set_state(NarrativeAdminStates.waiting_for_narrative_file)

@router.message(NarrativeAdminStates.waiting_for_narrative_file, F.document)
async def handle_narrative_file(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa un archivo JSON de fragmento narrativo."""
    if not message.document:
        await safe_answer(message, get_text("admin_narrative_handlers.no_document_detected"))
        return
    
    if not message.document.file_name.endswith('.json'):
        await safe_answer(message, get_text("admin_narrative_handlers.file_must_be_json"))
        return
    
    try:
        # Descargar el archivo
        file = await message.bot.get_file(message.document.file_id)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as temp_file:
            await message.bot.download_file(file.file_path, temp_file.name)
            temp_path = temp_file.name
        
        # Cargar el fragmento
        loader = NarrativeLoader(session)
        await loader.load_fragment_from_file(temp_path)
        
        await safe_answer(message, get_text("admin_narrative_handlers.fragment_loaded"))
        
    except json.JSONDecodeError as e:
        await safe_answer(message, get_text("admin_narrative_handlers.json_error", error=str(e)))
    except Exception as e:
        await safe_answer(message, get_text("admin_narrative_handlers.error", error=str(e)))
    finally:
        # Limpiar archivo temporal
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        await state.clear()

@router.message(Command("narrative_stats"))
async def narrative_admin_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas del sistema narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, get_text("admin_narrative_handlers.admins_only"))
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
        
        stats_text = f'{get_text("admin_narrative_handlers.narrative_stats_title")}\n\n'
        stats_text += f'{get_text("admin_narrative_handlers.narrative_stats_content", total_fragments=total_fragments, total_choices=total_choices, active_users=active_users)}\n\n'
        stats_text += f'{get_text("admin_narrative_handlers.narrative_stats_distribution")}'
        
        for level in sorted(level_distribution.keys()):
            count = level_distribution[level]
            level_type = get_text("admin_narrative_handlers.level_type_free") if level <= 3 else get_text("admin_narrative_handlers.level_type_vip")
            stats_text += get_text("admin_narrative_handlers.level_distribution_item", level=level, level_type=level_type, count=count)
        
        await safe_answer(message, stats_text)
        
    except Exception as e:
        await safe_answer(message, get_text("admin_narrative_handlers.error", error=str(e)))

@router.message(Command("reset_narrative"))
async def reset_user_narrative(message: Message, session: AsyncSession):
    """Reinicia la narrativa de un usuario (solo admins)."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, get_text("admin_narrative_handlers.admins_only"))
        return
    
    # Extraer user_id del comando
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await safe_answer(
            message, 
            get_text("admin_narrative_handlers.reset_narrative_usage")
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
            await safe_answer(message, get_text("admin_narrative_handlers.narrative_reset_success", target_user_id=target_user_id))
        else:
            await safe_answer(message, get_text("admin_narrative_handlers.user_has_no_narrative_progress", target_user_id=target_user_id))
            
    except ValueError:
        await safe_answer(message, get_text("admin_narrative_handlers.invalid_user_id"))
    except Exception as e:
        await safe_answer(message, get_text("admin_narrative_handlers.error", error=str(e)))