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
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from utils.menu_manager import menu_manager
from keyboards.admin_narrative_kb import get_fragment_management_kb
from states.admin_states import NarrativeFragmentStates
from database.narrative_models import StoryFragment, NarrativeChoice

router = Router()
logger = logging.getLogger(__name__)

class NarrativeAdminStates(StatesGroup):
    waiting_for_narrative_file = State()
    waiting_for_fragment_json = State()

@router.message(Command("load_narrative"))
async def load_narrative_command(message: Message, session: AsyncSession):
    """Carga fragmentos narrativos desde la carpeta narrative_fragments con validación."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        # Usar el servicio administrativo para cargar con validación
        from services.narrative_admin_service import NarrativeAdminService
        admin_service = NarrativeAdminService(session)
        
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
    """Procesa un archivo JSON de fragmento narrativo con validación y seguridad."""
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
        
        # Leer el contenido del archivo para validación
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # Usar el servicio administrativo para cargar con validación
        from services.narrative_admin_service import NarrativeAdminService
        admin_service = NarrativeAdminService(session)
        result = await admin_service.bulk_import_narrative_content(file_content)
        
        if result["status"] == "success":
            await safe_answer(
                message, 
                "✅ **Fragmentos Cargados**\n\n"
                f"Los fragmentos narrativos se han cargado exitosamente.\n"
                f"Importados: {result['imported_count']}"
            )
        elif result["status"] == "partial_success":
            error_details = "\n".join([
                f"• Fragmento {frag['key']}: {', '.join(frag['errors'])}"
                for frag in result.get("failed_fragments", [])
            ])
            await safe_answer(
                message,
                "⚠️ **Carga Parcialmente Exitosa**\n\n"
                f"Importados: {result['imported_count']}\n"
                f"Fallidos: {result['failed_count']}\n\n"
                f"**Errores:**\n{error_details}"
            )
        else:
            error_msg = result.get("message", "Error desconocido")
            error_details = "\n".join(result.get("errors", []))
            full_error = f"{error_msg}\n{error_details}" if error_details else error_msg
            await safe_answer(message, f"❌ **Error**: {full_error}")
        
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

@router.message(Command("validate_narrative"))
async def validate_narrative_command(message: Message, session: AsyncSession):
    """Valida la consistencia del sistema narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        from services.narrative_admin_service import NarrativeAdminService
        admin_service = NarrativeAdminService(session)
        
        # Validar consistencia narrativa
        report = await admin_service.validate_narrative_consistency()
        
        if report["status"] == "ok":
            await safe_answer(
                message,
                "✅ **Validación Exitosa**\n\n"
                "La narrativa es consistente. No se encontraron problemas.\n\n"
                f"📊 **Estadísticas:**\n"
                f"• Fragmentos totales: {report['summary']['total_fragments']}\n"
                f"• Fragmentos accesibles: {report['summary']['reachable_fragments']}"
            )
        elif report["status"] == "empty":
            await safe_answer(message, "⚠️ **Sin Fragmentos**\n\nNo hay fragmentos narrativos en la base de datos.")
        elif report["status"] == "error":
            error_msg = "\n".join(report["issues"])
            await safe_answer(message, f"❌ **Error de Validación**\n\n{error_msg}")
        else:  # issues_found
            orphaned = ", ".join(report["orphaned_fragments"]) if report["orphaned_fragments"] else "Ninguno"
            dead_ends = ", ".join(report["dead_end_fragments"]) if report["dead_end_fragments"] else "Ninguno"
            
            broken_links_text = "\n".join([
                f"• {link['source']} → {link['destination']} (\"{link['choice_text']}\")"
                for link in report["broken_links"]
            ]) if report["broken_links"] else "Ninguno"
            
            await safe_answer(
                message,
                "⚠️ **Problemas Encontrados**\n\n"
                f"📊 **Resumen:**\n"
                f"• Fragmentos totales: {report['summary']['total_fragments']}\n"
                f"• Fragmentos accesibles: {report['summary']['reachable_fragments']}\n"
                f"• Fragmentos huérfanos: {report['summary']['orphaned_count']}\n"
                f"• Fragmentos sin salida: {report['summary']['dead_end_count']}\n"
                f"• Enlaces rotos: {report['summary']['broken_link_count']}\n\n"
                f"🔗 **Fragmentos Huérfanos:**\n{orphaned}\n\n"
                f"🔚 **Fragmentos Sin Salida:**\n{dead_ends}\n\n"
                f"❌ **Enlaces Rotos:**\n{broken_links_text}"
            )

    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")

# =============================
# CALLBACK QUERY HANDLERS FOR ADMIN NARRATIVE MANAGEMENT
# =============================

@router.callback_query(F.data == "admin_narrative_fragments")
async def show_narrative_fragments_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display the story fragments management menu.

    Implements requirement 1.1 - Story fragment management organized by level and progression path.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get fragment count statistics for the menu
        from sqlalchemy import select, func
        fragments_stmt = select(func.count()).select_from(StoryFragment)
        fragments_result = await session.execute(fragments_stmt)
        total_fragments = fragments_result.scalar() or 0

        # Build menu text with comprehensive information
        menu_text = "📖 **Gestión de Fragmentos Narrativos**\n\n"
        menu_text += "Administra todos los fragmentos de la historia organizados por nivel y ruta de progresión.\n\n"

        menu_text += f"📊 **Estado actual:**\n"
        menu_text += f"• Fragmentos totales: {total_fragments}\n\n"

        menu_text += "**🔧 Herramientas disponibles:**\n"
        menu_text += "• Crear nuevos fragmentos con editor enriquecido\n"
        menu_text += "• Editar fragmentos existentes preservando la integridad\n"
        menu_text += "• Organizar por nivel y ruta de progresión\n"
        menu_text += "• Configurar condiciones de acceso complejas\n"
        menu_text += "• Validar consistencia narrativa automáticamente\n\n"

        menu_text += "**Selecciona una acción:**"

        keyboard = get_fragment_management_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_fragments"
        )

    except Exception as e:
        logger.error(f"Error showing fragments menu: {e}")
        await callback.answer("❌ Error al cargar gestión de fragmentos", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_narrative_lore")
async def show_narrative_lore_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Redirect to the lore admin handlers menu.

    This handler provides seamless navigation between narrative and lore management.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Import and redirect to lore admin handlers
        from handlers.admin.lore_admin_handlers import show_lore_admin_menu
        await show_lore_admin_menu(callback, session)

    except Exception as e:
        logger.error(f"Error redirecting to lore admin: {e}")
        await callback.answer("❌ Error al cargar gestión de lore", show_alert=True)

@router.callback_query(F.data == "admin_fragment_create")
async def start_fragment_creation(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Start the fragment creation process with guided form.

    Implements requirement 1.1 - Enhanced fragment creation with validation.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Send form instructions
        form_text = "➕ **Crear Nuevo Fragmento Narrativo**\n\n"
        form_text += "Te guiaré paso a paso para crear un nuevo fragmento.\n\n"
        form_text += "**Paso 1/6: Clave del fragmento**\n\n"
        form_text += "Ingresa una clave única para identificar este fragmento.\n"
        form_text += "Debe ser alfanumérica, sin espacios (ej: `intro_lucien`, `decision_01`).\n\n"
        form_text += "**Formato:**\n"
        form_text += "• Solo letras, números y guiones bajos\n"
        form_text += "• Máximo 50 caracteres\n"
        form_text += "• Debe ser única en el sistema\n\n"
        form_text += "**Escribe la clave del fragmento:**"

        from keyboards.common import get_back_kb

        await menu_manager.update_menu(
            callback,
            form_text,
            get_back_kb("admin_narrative_fragments"),
            session,
            "admin_fragment_create_form"
        )

        # Set state to wait for fragment key
        await state.set_state(NarrativeFragmentStates.waiting_for_fragment_key)

        logger.info(f"Fragment creation started by admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error starting fragment creation: {e}")
        await callback.answer("❌ Error al iniciar creación de fragmento", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_fragment_list")
async def show_fragments_list(callback: CallbackQuery, session: AsyncSession):
    """
    Display paginated list of all story fragments.

    Implements requirement 1.1 - Comprehensive fragment listing with pagination.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get all fragments with pagination support
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload

        # Get first page of fragments (10 per page)
        stmt = select(StoryFragment).options(
            selectinload(StoryFragment.choices)
        ).order_by(StoryFragment.level, StoryFragment.key).limit(10)

        result = await session.execute(stmt)
        fragments = result.scalars().all()

        # Count total fragments for pagination
        count_stmt = select(func.count()).select_from(StoryFragment)
        count_result = await session.execute(count_stmt)
        total_fragments = count_result.scalar() or 0

        if not fragments:
            list_text = "📋 **Lista de Fragmentos**\n\n"
            list_text += "No hay fragmentos narrativos en el sistema.\n\n"
            list_text += "Usa el botón **➕ Crear Fragmento** para empezar."
        else:
            list_text = f"📋 **Lista de Fragmentos** (Página 1)\n\n"
            list_text += f"Mostrando {len(fragments)} de {total_fragments} fragmentos.\n\n"

            for i, fragment in enumerate(fragments, 1):
                choice_count = len(fragment.choices) if fragment.choices else 0
                auto_next = " → Auto" if fragment.auto_next_fragment_key else ""

                list_text += f"**{i}. {fragment.key}**\n"
                list_text += f"• Nivel: {fragment.level} | Personaje: {fragment.character}\n"
                list_text += f"• Decisiones: {choice_count}{auto_next}\n"
                list_text += f"• Besitos: {fragment.min_besitos} req / {fragment.reward_besitos} reward\n\n"

        # Build pagination keyboard
        from keyboards.common import get_back_kb
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()

        # Add pagination controls if needed
        if total_fragments > 10:
            builder.button(text="📄 Página Siguiente", callback_data="admin_fragment_list:1")
            builder.adjust(1)

        # Add navigation buttons
        builder.button(text="🔙 Volver", callback_data="admin_narrative_fragments")
        builder.adjust(1)

        keyboard = builder.as_markup()

        await menu_manager.update_menu(
            callback,
            list_text,
            keyboard,
            session,
            "admin_fragment_list"
        )

    except Exception as e:
        logger.error(f"Error showing fragments list: {e}")
        await callback.answer("❌ Error al cargar lista de fragmentos", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_fragment_edit")
async def start_fragment_edit_selection(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Start the fragment editing process with fragment selection.

    Implements requirement 1.1 - Fragment editing with preservation of narrative integrity.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get available fragments for editing
        from sqlalchemy import select

        stmt = select(StoryFragment).order_by(StoryFragment.level, StoryFragment.key).limit(20)
        result = await session.execute(stmt)
        fragments = result.scalars().all()

        if not fragments:
            edit_text = "✏️ **Editar Fragmento**\n\n"
            edit_text += "No hay fragmentos disponibles para editar.\n\n"
            edit_text += "Crea algunos fragmentos primero usando **➕ Crear Fragmento**."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_narrative_fragments")
        else:
            edit_text = "✏️ **Editar Fragmento**\n\n"
            edit_text += "Selecciona el fragmento que deseas editar.\n"
            edit_text += "Puedes modificar texto, configuración y decisiones.\n\n"
            edit_text += "**Fragmentos disponibles:**\n\n"

            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()

            for fragment in fragments[:10]:  # Show first 10
                edit_text += f"• **{fragment.key}** (Nivel {fragment.level})\n"
                builder.button(
                    text=f"{fragment.key[:20]}{'...' if len(fragment.key) > 20 else ''}",
                    callback_data=f"edit_fragment:{fragment.key}"
                )

            # Add navigation
            builder.button(text="🔙 Volver", callback_data="admin_narrative_fragments")
            builder.adjust(2, 2, 2, 1)  # 2 columns for fragments, 1 for back
            keyboard = builder.as_markup()

        await menu_manager.update_menu(
            callback,
            edit_text,
            keyboard,
            session,
            "admin_fragment_edit_selection"
        )

        # Set state for edit selection
        await state.set_state(NarrativeFragmentStates.waiting_for_edit_selection)

    except Exception as e:
        logger.error(f"Error starting fragment edit: {e}")
        await callback.answer("❌ Error al cargar edición de fragmentos", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_fragment_by_level")
async def show_fragments_by_level(callback: CallbackQuery, session: AsyncSession):
    """
    Display fragments organized by level for better narrative structure visualization.

    Implements requirement 1.1 - Level organization and progression path management.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get fragments grouped by level
        from sqlalchemy import select, func

        # Get level distribution
        level_stmt = select(
            StoryFragment.level,
            func.count().label('count')
        ).group_by(StoryFragment.level).order_by(StoryFragment.level)

        level_result = await session.execute(level_stmt)
        level_distribution = level_result.all()

        if not level_distribution:
            level_text = "🗂️ **Fragmentos por Nivel**\n\n"
            level_text += "No hay fragmentos en el sistema para organizar por niveles."
        else:
            level_text = "🗂️ **Fragmentos por Nivel**\n\n"
            level_text += "Organización de la narrativa por niveles de progresión.\n\n"

            total_fragments = sum(row.count for row in level_distribution)
            level_text += f"📊 **Resumen:** {total_fragments} fragmentos en {len(level_distribution)} niveles\n\n"

            for level, count in level_distribution:
                level_type = "🆓 Gratuito" if level <= 3 else "💎 VIP"
                level_text += f"**Nivel {level}** {level_type}\n"
                level_text += f"• {count} fragmentos\n"

                # Show sample fragments for this level
                sample_stmt = select(StoryFragment.key).where(
                    StoryFragment.level == level
                ).limit(3)
                sample_result = await session.execute(sample_stmt)
                sample_keys = [row[0] for row in sample_result.all()]

                if sample_keys:
                    level_text += f"• Ejemplos: {', '.join(sample_keys[:2])}"
                    if len(sample_keys) > 2:
                        level_text += f" y {count - 2} más"
                    level_text += "\n"

                level_text += "\n"

            # Add level management instructions
            level_text += "💡 **Gestión de niveles:**\n"
            level_text += "• Niveles 1-3: Contenido gratuito accesible para todos\n"
            level_text += "• Niveles 4+: Contenido VIP que requiere suscripción\n"
            level_text += "• Asegúrate de que cada nivel tenga progresión coherente"

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_narrative_fragments")

        await menu_manager.update_menu(
            callback,
            level_text,
            keyboard,
            session,
            "admin_fragment_by_level"
        )

    except Exception as e:
        logger.error(f"Error showing fragments by level: {e}")
        await callback.answer("❌ Error al cargar fragmentos por nivel", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_fragment_connections")
async def show_fragment_connections(callback: CallbackQuery, session: AsyncSession):
    """
    Visualize the narrative graph connections between fragments.

    Implements requirement 1.1 - Connection visualization and narrative flow analysis.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        await callback.answer("🔍 Analizando conexiones narrativas...", show_alert=False)

        # Use the narrative admin service to get narrative graph data
        from services.narrative_admin_service import NarrativeAdminService
        admin_service = NarrativeAdminService(session)

        # Get validation report which includes connection analysis
        report = await admin_service.validate_narrative_consistency()

        connections_text = "🔗 **Conexiones Narrativas**\n\n"
        connections_text += "Visualización del grafo narrativo y análisis de flujo.\n\n"

        if report["status"] == "empty":
            connections_text += "❌ **No hay fragmentos** para analizar conexiones.\n"
            connections_text += "Crea algunos fragmentos primero."
        elif report["status"] == "error":
            connections_text += "❌ **Error en el análisis:**\n"
            connections_text += "\n".join(report.get("issues", []))
        else:
            # Show connection statistics
            summary = report["summary"]
            connections_text += f"📊 **Estadísticas de conexión:**\n"
            connections_text += f"• Fragmentos totales: {summary['total_fragments']}\n"
            connections_text += f"• Fragmentos conectados: {summary['reachable_fragments']}\n"
            connections_text += f"• Fragmentos huérfanos: {summary['orphaned_count']}\n"
            connections_text += f"• Enlaces rotos: {summary['broken_link_count']}\n\n"

            # Health indicator
            if summary['broken_link_count'] == 0 and summary['orphaned_count'] == 0:
                connections_text += "✅ **Estado de conexiones:** Saludable\n\n"
            elif summary['broken_link_count'] > 0 or summary['orphaned_count'] > 0:
                connections_text += "⚠️ **Estado de conexiones:** Requiere atención\n\n"

            # Show specific connection issues
            if report.get("orphaned_fragments"):
                connections_text += "🔗 **Fragmentos huérfanos:**\n"
                orphaned_list = ", ".join(report["orphaned_fragments"][:5])
                if len(report["orphaned_fragments"]) > 5:
                    orphaned_list += f" y {len(report['orphaned_fragments']) - 5} más"
                connections_text += f"{orphaned_list}\n\n"

            if report.get("broken_links"):
                connections_text += "❌ **Enlaces rotos detectados:**\n"
                for link in report["broken_links"][:3]:
                    connections_text += f"• {link['source']} → {link['destination']}\n"
                if len(report["broken_links"]) > 3:
                    connections_text += f"• Y {len(report['broken_links']) - 3} enlaces rotos más\n"
                connections_text += "\n"

            # Navigation flow analysis
            if summary['reachable_fragments'] > 0:
                reachability_percent = (summary['reachable_fragments'] / summary['total_fragments']) * 100
                connections_text += f"📈 **Análisis de flujo:**\n"
                connections_text += f"• Alcanzabilidad: {reachability_percent:.1f}%\n"
                if reachability_percent >= 95:
                    connections_text += "• Estado: Excelente flujo narrativo\n"
                elif reachability_percent >= 80:
                    connections_text += "• Estado: Buen flujo narrativo\n"
                else:
                    connections_text += "• Estado: Flujo narrativo necesita mejoras\n"

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_narrative_fragments")

        await menu_manager.update_menu(
            callback,
            connections_text,
            keyboard,
            session,
            "admin_fragment_connections"
        )

        logger.info(f"Fragment connections analysis performed by admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing fragment connections: {e}")
        await callback.answer("❌ Error al analizar conexiones", show_alert=True)

@router.callback_query(F.data == "admin_fragment_delete")
async def start_fragment_deletion(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Start the fragment deletion process with safety confirmation.

    Implements requirement 1.1 - Safe fragment deletion with validation and confirmation.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get available fragments for deletion (excluding 'start' fragment)
        from sqlalchemy import select

        stmt = select(StoryFragment).where(
            StoryFragment.key != 'start'
        ).order_by(StoryFragment.level, StoryFragment.key).limit(15)

        result = await session.execute(stmt)
        fragments = result.scalars().all()

        if not fragments:
            delete_text = "🗑️ **Eliminar Fragmento**\n\n"
            delete_text += "No hay fragmentos disponibles para eliminar.\n\n"
            delete_text += "**Nota:** El fragmento 'start' no puede ser eliminado por seguridad."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_narrative_fragments")
        else:
            delete_text = "🗑️ **Eliminar Fragmento**\n\n"
            delete_text += "⚠️ **ADVERTENCIA:** Esta acción es irreversible.\n"
            delete_text += "Eliminar un fragmento puede romper las conexiones narrativas.\n\n"
            delete_text += "**Fragmentos disponibles para eliminación:**\n\n"

            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()

            for fragment in fragments[:10]:  # Show first 10
                # Check if fragment has incoming references
                choices_stmt = select(NarrativeChoice).where(
                    NarrativeChoice.destination_fragment_key == fragment.key
                )
                choices_result = await session.execute(choices_stmt)
                has_references = choices_result.first() is not None

                reference_indicator = " ⚠️" if has_references else ""
                delete_text += f"• **{fragment.key}** (Nivel {fragment.level}){reference_indicator}\n"

                builder.button(
                    text=f"🗑️ {fragment.key[:15]}{'...' if len(fragment.key) > 15 else ''}",
                    callback_data=f"confirm_delete:{fragment.key}"
                )

            delete_text += "\n⚠️ = Fragmento referenciado por otros (eliminar causará enlaces rotos)\n\n"
            delete_text += "**Selecciona un fragmento para eliminar:**"

            # Add navigation
            builder.button(text="🔙 Volver", callback_data="admin_narrative_fragments")
            builder.adjust(2, 2, 2, 1)  # 2 columns for fragments, 1 for back
            keyboard = builder.as_markup()

        await menu_manager.update_menu(
            callback,
            delete_text,
            keyboard,
            session,
            "admin_fragment_delete_selection"
        )

        # Set state for deletion confirmation
        await state.set_state(NarrativeFragmentStates.waiting_for_delete_confirmation)

    except Exception as e:
        logger.error(f"Error starting fragment deletion: {e}")
        await callback.answer("❌ Error al cargar eliminación de fragmentos", show_alert=True)

    await callback.answer()