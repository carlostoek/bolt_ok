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

router = Router()

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
        else:  // issues_found
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