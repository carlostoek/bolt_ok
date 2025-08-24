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
import logging

from services.narrative_loader import NarrativeLoader

# Configurar logger
logger = logging.getLogger(__name__)
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from utils.callback_utils import parse_callback_data
from services.narrative_admin_service import NarrativeAdminService
from handlers.admin.narrative_admin_kb import (
    get_narrative_admin_keyboard,
    get_fragments_list_keyboard,
    get_fragment_detail_keyboard,
    get_fragment_edit_keyboard,
    get_storyboard_keyboard,
    get_fragment_connections_keyboard,
    get_narrative_analytics_keyboard,
    get_fragment_type_keyboard,
    get_confirm_delete_keyboard,
    get_search_results_keyboard
)

router = Router()

class NarrativeAdminStates(StatesGroup):
    waiting_for_narrative_file = State()
    waiting_for_fragment_json = State()

@router.message(Command("load_narrative"))
async def load_narrative_command(message: Message, session: AsyncSession):
    """Carga fragmentos narrativos desde la carpeta narrative_fragments."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        loader = NarrativeLoader(session)
        
        # Intentar cargar desde directorio
        await loader.load_fragments_from_directory("mybot/narrative_fragments")
        
        # Si no hay archivos, cargar narrativa por defecto
        await loader.load_default_narrative()
        
        await safe_answer(message, "✅ **Narrativa Cargada**\n\nLos fragmentos narrativos han sido cargados exitosamente.")
        
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")

@router.message(Command("upload_narrative"))
async def upload_narrative_command(message: Message, session: AsyncSession, state: FSMContext):
    """Inicia el proceso para subir un archivo narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    await safe_answer(
        message,
        "📤 **Subir Narrativa**\n\n"
        "Envía un archivo JSON con el fragmento narrativo.\n\n"
        "**Formato esperado:**\n"
        "```json\n"
        "{\n"
        '  "fragment_id": "UNIQUE_ID",\n'
        '  "content": "Texto del fragmento",\n'
        '  "character": "Lucien",\n'
        '  "level": 1,\n'
        '  "required_besitos": 0,\n'
        '  "reward_besitos": 5,\n'
        '  "decisions": [\n'
        '    {\n'
        '      "text": "Opción 1",\n'
        '      "next_fragment": "NEXT_ID"\n'
        '    }\n'
        '  ]\n'
        "}\n"
        "```"
    )
    await state.set_state(NarrativeAdminStates.waiting_for_narrative_file)

@router.message(NarrativeAdminStates.waiting_for_narrative_file, F.document)
async def handle_narrative_file(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa un archivo JSON de fragmento narrativo."""
    if not message.document:
        await safe_answer(message, "❌ No se detectó ningún documento.")
        return
    
    if not message.document.file_name.endswith('.json'):
        await safe_answer(message, "❌ El archivo debe ser un JSON (.json).")
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
        
        await safe_answer(message, "✅ **Fragmento Cargado**\n\nEl fragmento narrativo se ha cargado exitosamente.")
        
    except json.JSONDecodeError as e:
        await safe_answer(message, f"❌ **Error de JSON**: {str(e)}")
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        await state.clear()

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


# Handler para el menú principal de administración narrativa
@router.callback_query(F.data.in_({"admin_fragments_manage", "admin_narrative_refresh"}))
async def handle_admin_fragments_manage(callback: CallbackQuery, session: AsyncSession):
    """Muestra el menú principal de administración narrativa."""
    # Depuración explícita
    logger.info(f"Recibido callback para administración narrativa: {callback.data}")
    
    # Intentar extraer directamente el from_user.id para verificar que llega correctamente
    try:
        user_id = callback.from_user.id
        logger.info(f"Usuario que activó el callback: {user_id}")
    except Exception as e:
        logger.error(f"Error al obtener el usuario del callback: {e}")
        
    # Continuar con el handler normal
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener servicio de administración narrativa
        narrative_admin_service = NarrativeAdminService(session)
        
        # Obtener estadísticas del sistema narrativo
        stats = await narrative_admin_service.get_narrative_stats()
        
        # Construir el mensaje
        text = f"""
📖 **SISTEMA DE ADMINISTRACIÓN NARRATIVA**

┌─────────────────────────────────┐
│     ESTADO DEL CONTENIDO      │
├─────────────────────────────────┤
│ 📚 Fragmentos totales: {stats.get('total_fragments', 0)}      │
│ 📋 Fragmentos activos: {stats.get('active_fragments', 0)}     │
│ 👥 Usuarios en narrativa: {stats.get('users_in_narrative', 0)}  │
└─────────────────────────────────┘

📊 **Distribución por tipo**
• Historia: {stats.get('fragments_by_type', {}).get('STORY', 0)}
• Decisión: {stats.get('fragments_by_type', {}).get('DECISION', 0)}
• Información: {stats.get('fragments_by_type', {}).get('INFO', 0)}

✨ **Herramientas de Administración**
Gestiona el contenido narrativo y analiza el engagement.
"""
        
        # Obtener teclado
        keyboard = get_narrative_admin_keyboard()
        
        # Enviar mensaje
        await safe_edit(callback.message, text, reply_markup=keyboard)
        
        # Confirmar acción
        await callback.answer("📖 Administración narrativa cargada")
        
    except Exception as e:
        logger.error(f"Error al mostrar administración narrativa: {e}")
        await callback.answer("❌ Error al cargar administración narrativa", show_alert=True)


@router.callback_query(F.data == "admin_narrative_menu")
async def handle_admin_narrative_menu(callback: CallbackQuery, session: AsyncSession):
    """Regresa al menú principal de administración narrativa."""
    await handle_admin_fragments_manage(callback, session)


@router.callback_query(F.data.startswith("admin_fragments_list"))
async def list_fragments(callback: CallbackQuery, session: AsyncSession):
    """Muestra la lista paginada de fragmentos narrativos."""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener parámetros de la callback
        params = parse_callback_data(callback.data)
        page = int(params.get("page", 1))
        filter_type = params.get("filter")
        if filter_type == "all":
            filter_type = None
        
        # Obtener servicio de administración narrativa
        narrative_admin_service = NarrativeAdminService(session)
        
        # Obtener fragmentos paginados
        result = await narrative_admin_service.get_all_fragments(
            page=page,
            limit=10,
            filter_type=filter_type,
            include_inactive=False
        )
        
        # Crear mensaje con la lista de fragmentos
        text = f"""
📄 **FRAGMENTOS NARRATIVOS**
┌─────────────────────────────────┐
│      LISTA DE FRAGMENTOS       │
├─────────────────────────────────┤
"""
        
        # Si no hay fragmentos
        if not result["items"]:
            text += "│ No hay fragmentos disponibles.  │\n"
        else:
            # Mostrar fragmentos
            for item in result["items"]:
                # Emojis para estado y tipo
                state_emoji = "✅" if item["is_active"] else "❌"
                type_emoji = {
                    "STORY": "📖",  # Historia
                    "DECISION": "🔸",  # Decisión
                    "INFO": "ℹ️"  # Información
                }.get(item["type"], "📄")
                
                # Truncar título si es muy largo
                title = item["title"]
                if len(title) > 20:
                    title = title[:17] + "..."
                
                # Agregar línea para este fragmento
                text += f"│ {state_emoji} {type_emoji} [{item['id']}] {title} │\n"
        
        text += "└─────────────────────────────────┘\n"
        text += f"Total: {result['total']} | Página: {page}/{result.get('total_pages', 1)}"
        
        # Obtener teclado con paginación
        keyboard = get_fragments_list_keyboard(
            page=page,
            total_pages=result.get("total_pages", 1),
            filter_type=filter_type
        )
        
        # Enviar mensaje
        await safe_edit(callback.message, text, reply_markup=keyboard)
        
        # Confirmar acción
        await callback.answer("📄 Lista de fragmentos cargada")
        
    except Exception as e:
        logger.error(f"Error al listar fragmentos: {e}")
        await callback.answer("❌ Error al cargar fragmentos", show_alert=True)


@router.callback_query(F.data.startswith("admin_view_fragment"))
async def view_fragment(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles de un fragmento narrativo."""
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento de la callback
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Obtener servicio de administración narrativa
        narrative_admin_service = NarrativeAdminService(session)
        
        # Obtener detalles del fragmento
        fragment = await narrative_admin_service.get_fragment_details(fragment_id)
        
        # Emojis para estado y tipo
        state_emoji = "✅" if fragment["is_active"] else "❌"
        type_emoji = {
            "STORY": "📖",  # Historia
            "DECISION": "🔸",  # Decisión
            "INFO": "ℹ️"  # Información
        }.get(fragment["type"], "📄")
        
        # Formatear fechas
        created_at = fragment.get("created_at", "").split("T")[0] if fragment.get("created_at") else "N/A"
        updated_at = fragment.get("updated_at", "").split("T")[0] if fragment.get("updated_at") else "N/A"
        
        # Crear mensaje con detalles del fragmento
        text = f"""
📄 **FRAGMENTO NARRATIVO: {fragment["title"]}**
┌─────────────────────────────────┐
│      DETALLES DEL FRAGMENTO     │
├─────────────────────────────────┤
│ ID: {fragment["id"]}\n│ Tipo: {type_emoji} {fragment["type"]}\n│ Estado: {state_emoji} {'Activo' if fragment["is_active"] else 'Inactivo'}\n│ Creado: {created_at}\n│ Actualizado: {updated_at}
├─────────────────────────────────┤
│ CONTENIDO                       │
├─────────────────────────────────┤
"""
        
        # Agregar contenido (truncado si es muy largo)
        content = fragment["content"]
        if len(content) > 500:
            content = content[:497] + "..."
        text += f"{content}\n"
        
        # Estadísticas de uso si están disponibles
        if "statistics" in fragment:
            stats = fragment["statistics"]
            text += f"""
├─────────────────────────────────┤
│ ESTADÍSTICAS                    │
├─────────────────────────────────┤
│ Usuarios actuales: {stats.get('active_users', 0)}\n│ Usuarios que han visitado: {stats.get('visited_users', 0)}\n│ Usuarios completados: {stats.get('completed_users', 0)}\n│ Tasa de finalización: {stats.get('completion_rate', 0)}%
"""
        
        text += "└─────────────────────────────────┘"
        
        # Obtener teclado para detalles de fragmento
        keyboard = get_fragment_detail_keyboard(fragment_id)
        
        # Enviar mensaje
        await safe_edit(callback.message, text, reply_markup=keyboard)
        
        # Confirmar acción
        await callback.answer(f"📄 Fragmento '{fragment['id']}' cargado")
        
    except Exception as e:
        logger.error(f"Error al ver fragmento: {e}")
        await callback.answer("❌ Error al cargar fragmento", show_alert=True)
