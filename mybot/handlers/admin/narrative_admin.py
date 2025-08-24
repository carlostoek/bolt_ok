"""
Manejadores para la administración de contenido narrativo.
Permite a los administradores gestionar, visualizar y analizar el contenido narrativo.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from services.narrative_admin_service import NarrativeAdminService
from services.event_bus import get_event_bus, EventType
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from utils.callback_utils import parse_callback_data
from utils.handler_decorators import safe_handler
from .narrative_admin_kb import (
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

# Configurar logger
logger = logging.getLogger(__name__)

# Crear router
router = Router()

# Estados FSM para creación/edición de fragmentos
class NarrativeFragmentStates(StatesGroup):
    selecting_type = State()
    entering_title = State()
    entering_content = State()
    configuring_choices = State()
    configuring_requirements = State()
    configuring_triggers = State()
    confirming_creation = State()
    
    # Estados para edición
    editing_title = State()
    editing_content = State()
    editing_type = State()
    
    # Estados para búsqueda
    entering_search_query = State()
    
    # Estados para conexiones
    adding_connection_target = State()
    adding_connection_text = State()

# ==================== NAVEGACIÓN PRINCIPAL ====================

@router.callback_query(F.data == "admin_fragments_manage")
@safe_handler("❌ Error accediendo a la administración de fragmentos narrativos.")
async def handle_admin_fragments_manage(callback: CallbackQuery, session: AsyncSession):
    """
    Punto de entrada principal para la administración narrativa.
    Integrado con el sistema de menús Diana.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Preparar teclado principal de administración narrativa
        keyboard = get_narrative_admin_keyboard()
        
        # Preparar texto de bienvenida
        admin_service = NarrativeAdminService(session)
        stats = await admin_service.get_narrative_stats()
        
        text = f"""
📖 **SISTEMA DE ADMINISTRACIÓN NARRATIVA**
*Gestión avanzada de contenido narrativo*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Resumen del Sistema**
• Fragmentos totales: {stats.get('total_fragments', 0)}
• Fragmentos activos: {stats.get('active_fragments', 0)}
• Usuarios en narrativa: {stats.get('users_in_narrative', 0)}

🔍 **Fragmentos por Tipo**
• Historia: {stats.get('fragments_by_type', {}).get('STORY', 0)}
• Decisión: {stats.get('fragments_by_type', {}).get('DECISION', 0)}
• Información: {stats.get('fragments_by_type', {}).get('INFO', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ **Panel de Administración**
Seleccione una opción para gestionar el contenido narrativo:
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("📖 Administración narrativa cargada")
        
    except Exception as e:
        logger.error(f"Error mostrando menú de administración narrativa: {e}")
        await callback.answer("❌ Error cargando sistema de administración narrativa", show_alert=True)

@router.callback_query(F.data == "admin_narrative_menu")
@safe_handler("❌ Error accediendo al menú de administración narrativa.")
async def handle_narrative_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra el menú principal de administración narrativa.
    """
    await handle_admin_fragments_manage(callback, session)

@router.callback_query(F.data == "admin_narrative_refresh")
@safe_handler("❌ Error actualizando el menú de administración narrativa.")
async def handle_narrative_refresh(callback: CallbackQuery, session: AsyncSession):
    """
    Actualiza el menú principal de administración narrativa.
    """
    await handle_admin_fragments_manage(callback, session)

# ==================== GESTIÓN DE FRAGMENTOS ====================

@router.callback_query(F.data.startswith("admin_fragments_list"))
@safe_handler("❌ Error listando fragmentos narrativos.")
async def list_fragments(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra la lista paginada de fragmentos narrativos.
    Soporta filtrado por tipo y paginación.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Analizar parámetros de la callback query
        params = parse_callback_data(callback.data)
        page = int(params.get("page", 1))
        filter_type = params.get("filter")
        
        # Ajustar filtro si es 'all'
        if filter_type == "all":
            filter_type = None
        
        # Obtener fragmentos paginados
        admin_service = NarrativeAdminService(session)
        fragments_data = await admin_service.get_all_fragments(
            page=page,
            limit=10,
            filter_type=filter_type
        )
        
        # Preparar teclado con paginación
        keyboard = get_fragments_list_keyboard(
            page=page,
            total_pages=fragments_data["total_pages"],
            filter_type=filter_type
        )
        
        # Preparar texto con listado
        fragments = fragments_data["items"]
        
        header = f"""
📝 **FRAGMENTOS NARRATIVOS**
*Página {page}/{fragments_data["total_pages"]} - Total: {fragments_data["total"]}*
"""
        
        if filter_type:
            header += f"*Filtro:* {filter_type}\n"
            
        header += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not fragments:
            text = header + "😔 No se encontraron fragmentos con estos criterios."
        else:
            text = header
            for i, fragment in enumerate(fragments):
                # Iconos según tipo
                icon = "📖" if fragment["type"] == "STORY" else "🔀" if fragment["type"] == "DECISION" else "ℹ️"
                
                # Indicador de estado
                status = "✅" if fragment["is_active"] else "❌"
                
                # Agregar a la lista
                text += f"{i+1}. {status} {icon} **{fragment['title']}**\n"
                text += f"   ID: `{fragment['id']}`\n"
                text += f"   Tipo: {fragment['type']} | Actualizado: {fragment['updated_at'][:10]}\n\n"
        
        text += """
Para ver detalles, haga clic en el fragmento correspondiente.
Para crear un nuevo fragmento, use el botón "➕ Nuevo".
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("📝 Listado de fragmentos cargado")
        
    except Exception as e:
        logger.error(f"Error listando fragmentos narrativos: {e}")
        await callback.answer("❌ Error cargando fragmentos", show_alert=True)

@router.callback_query(F.data.startswith("admin_view_fragment"))
@safe_handler("❌ Error mostrando detalles del fragmento.")
async def view_fragment(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra los detalles de un fragmento específico.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Obtener detalles del fragmento
        admin_service = NarrativeAdminService(session)
        fragment_details = await admin_service.get_fragment_details(fragment_id)
        
        # Preparar teclado
        keyboard = get_fragment_detail_keyboard(fragment_id)
        
        # Iconos según tipo
        type_icon = "📖" if fragment_details["type"] == "STORY" else "🔀" if fragment_details["type"] == "DECISION" else "ℹ️"
        
        # Formatear contenido
        content = fragment_details["content"]
        if len(content) > 500:
            content = content[:497] + "..."
        
        # Preparar texto con detalles
        text = f"""
{type_icon} **FRAGMENTO NARRATIVO: {fragment_details['title']}**
*ID:* `{fragment_details['id']}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 **Detalles Básicos**
• Tipo: {fragment_details['type']}
• Estado: {"✅ Activo" if fragment_details['is_active'] else "❌ Inactivo"}
• Creado: {fragment_details['created_at'][:10] if fragment_details['created_at'] else "N/A"}
• Actualizado: {fragment_details['updated_at'][:10] if fragment_details['updated_at'] else "N/A"}

📊 **Estadísticas**
• Usuarios actuales: {fragment_details['statistics']['active_users']}
• Visitado por: {fragment_details['statistics']['visited_users']} usuarios
• Completado por: {fragment_details['statistics']['completed_users']} usuarios
• Tasa de finalización: {fragment_details['statistics']['completion_rate']:.1f}%

💬 **Contenido**
{content}

🔄 **Conexiones**
• Opciones: {len(fragment_details['choices'])}
"""
        
        # Agregar sección de opciones si las hay
        if fragment_details['choices']:
            text += "\n**Opciones disponibles:**\n"
            for i, choice in enumerate(fragment_details['choices']):
                text += f"{i+1}. {choice.get('text', 'Sin texto')}"
                if 'next_fragment' in choice:
                    text += f" → `{choice['next_fragment']}`"
                text += "\n"
        
        # Agregar sección de requisitos si los hay
        if fragment_details['required_clues']:
            text += "\n**Requisitos:**\n"
            for clue in fragment_details['required_clues']:
                text += f"• {clue}\n"
        
        # Agregar sección de triggers si los hay
        if fragment_details['triggers'] and any(fragment_details['triggers'].values()):
            text += "\n**Triggers:**\n"
            for trigger_type, trigger_data in fragment_details['triggers'].items():
                if trigger_data:
                    text += f"• {trigger_type}: {json.dumps(trigger_data, ensure_ascii=False)}\n"
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer(f"📝 Fragmento {fragment_details['title']} cargado")
        
    except ValueError as e:
        logger.error(f"Error de validación al ver fragmento: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error mostrando detalles del fragmento: {e}")
        await callback.answer("❌ Error cargando detalles del fragmento", show_alert=True)

@router.callback_query(F.data == "admin_create_fragment")
@safe_handler("❌ Error iniciando creación de fragmento.")
async def start_fragment_creation(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Inicia el flujo de creación de fragmento narrativo.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Preparar teclado para selección de tipo
        keyboard = get_fragment_type_keyboard()
        
        text = """
📝 **CREAR NUEVO FRAGMENTO**
*Paso 1 de 5: Selección de tipo*

Por favor, seleccione el tipo de fragmento que desea crear:

• 📖 **Historia (STORY)**: Fragmento narrativo principal con texto de la historia.

• 🔀 **Decisión (DECISION)**: Punto de decisión donde el usuario debe elegir.

• ℹ️ **Información (INFO)**: Fragmento informativo con detalles adicionales.

Cada tipo de fragmento tiene características y usos específicos. Seleccione el más adecuado para su propósito.
"""
        
        # Establecer estado FSM
        await state.set_state(NarrativeFragmentStates.selecting_type)
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("📝 Inicio de creación de fragmento")
        
    except Exception as e:
        logger.error(f"Error iniciando creación de fragmento: {e}")
        await callback.answer("❌ Error iniciando creación", show_alert=True)
        await state.clear()

@router.callback_query(NarrativeFragmentStates.selecting_type, F.data.startswith("admin_fragment_type_select"))
@safe_handler("❌ Error seleccionando tipo de fragmento.")
async def process_fragment_type_selection(callback: CallbackQuery, state: FSMContext):
    """
    Procesa la selección de tipo de fragmento y pide el título.
    """
    try:
        # Obtener tipo seleccionado
        params = parse_callback_data(callback.data)
        fragment_type = params.get("type")
        
        if not fragment_type:
            await callback.answer("❌ Tipo de fragmento no válido", show_alert=True)
            return
        
        # Guardar tipo en datos del estado
        await state.update_data(fragment_type=fragment_type)
        
        # Preparar mensaje para solicitar título
        type_names = {
            "STORY": "Historia",
            "DECISION": "Decisión",
            "INFO": "Información"
        }
        
        text = f"""
📝 **CREAR NUEVO FRAGMENTO**
*Paso 2 de 5: Título del fragmento*

Tipo seleccionado: **{type_names.get(fragment_type, fragment_type)}**

Por favor, envíe el título para este fragmento narrativo.
El título debe ser descriptivo y conciso (máximo 200 caracteres).

*Ejemplos:*
• "El encuentro en el jardín"
• "Decisión: ¿Seguir a Diana o explorar solo?"
• "Información sobre la mansión"

Para cancelar el proceso, escriba "cancelar".
"""
        
        # Cambiar al siguiente estado
        await state.set_state(NarrativeFragmentStates.entering_title)
        
        await safe_edit(callback.message, text)
        await callback.answer(f"Tipo {type_names.get(fragment_type, fragment_type)} seleccionado")
        
    except Exception as e:
        logger.error(f"Error procesando selección de tipo: {e}")
        await callback.answer("❌ Error seleccionando tipo", show_alert=True)

@router.message(NarrativeFragmentStates.entering_title)
@safe_handler("❌ Error procesando título de fragmento.")
async def process_fragment_title(message: Message, state: FSMContext):
    """
    Procesa el título del fragmento y solicita el contenido.
    """
    try:
        # Verificar si el usuario quiere cancelar
        if message.text.lower() == "cancelar":
            await state.clear()
            await safe_answer(message, "❌ Creación de fragmento cancelada.")
            return
        
        # Validar título
        title = message.text.strip()
        if not title:
            await safe_answer(message, "❌ El título no puede estar vacío. Por favor, envíe un título válido.")
            return
            
        if len(title) > 200:
            await safe_answer(message, "❌ El título es demasiado largo (máximo 200 caracteres). Por favor, acórtelo.")
            return
        
        # Guardar título en datos del estado
        await state.update_data(title=title)
        
        # Obtener tipo para personalizar mensaje
        state_data = await state.get_data()
        fragment_type = state_data.get("fragment_type")
        
        # Preparar mensaje para solicitar contenido
        type_guidance = {
            "STORY": "Describa la escena, diálogos y eventos que ocurren en este fragmento.",
            "DECISION": "Describa la situación que requiere una decisión del usuario.",
            "INFO": "Proporcione la información detallada que debe mostrar este fragmento."
        }
        
        text = f"""
📝 **CREAR NUEVO FRAGMENTO**
*Paso 3 de 5: Contenido del fragmento*

Título: **{title}**

Por favor, envíe el contenido para este fragmento narrativo.
{type_guidance.get(fragment_type, "Proporcione el contenido completo del fragmento.")}

Puede usar formato Markdown:
• *texto* para cursiva
• **texto** para negrita
• `texto` para código
• [texto](URL) para enlaces

Para cancelar el proceso, escriba "cancelar".
"""
        
        # Cambiar al siguiente estado
        await state.set_state(NarrativeFragmentStates.entering_content)
        
        await safe_answer(message, text)
        
    except Exception as e:
        logger.error(f"Error procesando título de fragmento: {e}")
        await safe_answer(message, "❌ Error procesando título. Por favor, inténtelo de nuevo.")

@router.message(NarrativeFragmentStates.entering_content)
@safe_handler("❌ Error procesando contenido de fragmento.")
async def process_fragment_content(message: Message, state: FSMContext, session: AsyncSession):
    """
    Procesa el contenido del fragmento y confirma la creación.
    """
    try:
        # Verificar si el usuario quiere cancelar
        if message.text.lower() == "cancelar":
            await state.clear()
            await safe_answer(message, "❌ Creación de fragmento cancelada.")
            return
        
        # Validar contenido
        content = message.text.strip()
        if not content:
            await safe_answer(message, "❌ El contenido no puede estar vacío. Por favor, envíe contenido válido.")
            return
        
        # Guardar contenido en datos del estado
        await state.update_data(content=content)
        
        # Obtener datos del fragmento
        fragment_data = await state.get_data()
        
        # Crear fragmento en la base de datos
        admin_service = NarrativeAdminService(session)
        fragment = await admin_service.create_fragment({
            "title": fragment_data.get("title"),
            "content": content,
            "fragment_type": fragment_data.get("fragment_type"),
            "is_active": True,
            "choices": [],
            "triggers": {},
            "required_clues": []
        })
        
        # Limpiar estado FSM
        await state.clear()
        
        # Mostrar confirmación con detalles del fragmento creado
        text = f"""
✅ **FRAGMENTO CREADO EXITOSAMENTE**

📝 **Detalles del fragmento:**
• Título: **{fragment['title']}**
• Tipo: {fragment['type']}
• ID: `{fragment['id']}`

Para configurar opciones y conexiones, use el botón "🔄 Conexiones".
Para editar los detalles, use el botón "✏️ Editar".

El fragmento está activo y listo para ser utilizado en la narrativa.
"""
        
        # Preparar teclado para opciones post-creación
        keyboard = get_fragment_detail_keyboard(fragment['id'])
        
        await safe_answer(message, text, reply_markup=keyboard)
        
    except ValueError as e:
        logger.error(f"Error de validación al crear fragmento: {e}")
        await safe_answer(message, f"❌ Error de validación: {str(e)}")
    except Exception as e:
        logger.error(f"Error procesando contenido de fragmento: {e}")
        await safe_answer(message, "❌ Error creando fragmento. Por favor, inténtelo de nuevo.")

@router.callback_query(F.data.startswith("admin_edit_fragment?"))
@safe_handler("❌ Error iniciando edición de fragmento.")
async def start_fragment_edit(callback: CallbackQuery, session: AsyncSession):
    """
    Inicia el flujo de edición de fragmento.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Obtener detalles del fragmento
        admin_service = NarrativeAdminService(session)
        fragment_details = await admin_service.get_fragment_details(fragment_id)
        
        # Preparar teclado
        keyboard = get_fragment_edit_keyboard(fragment_id)
        
        text = f"""
✏️ **EDITAR FRAGMENTO**
*{fragment_details['title']}*

Seleccione qué aspecto del fragmento desea editar:

• 📝 **Título** - Cambiar el título del fragmento
• 📄 **Contenido** - Modificar el texto principal
• 🔀 **Tipo** - Cambiar entre STORY, DECISION o INFO
• 🔄 **Conexiones** - Editar las opciones y conexiones
• 🎯 **Requisitos** - Configurar pistas necesarias
• 🔔 **Triggers** - Configurar efectos del fragmento

ID: `{fragment_details['id']}`
Tipo actual: {fragment_details['type']}
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("✏️ Modo de edición activado")
        
    except ValueError as e:
        logger.error(f"Error de validación al iniciar edición: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error iniciando edición de fragmento: {e}")
        await callback.answer("❌ Error iniciando edición", show_alert=True)

@router.callback_query(F.data.startswith("admin_delete_fragment?"))
@safe_handler("❌ Error preparando eliminación de fragmento.")
async def confirm_delete_fragment(callback: CallbackQuery, session: AsyncSession):
    """
    Solicita confirmación para eliminar un fragmento.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Obtener detalles del fragmento
        admin_service = NarrativeAdminService(session)
        fragment_details = await admin_service.get_fragment_details(fragment_id)
        
        # Preparar teclado de confirmación
        keyboard = get_confirm_delete_keyboard(fragment_id)
        
        text = f"""
🗑️ **CONFIRMAR ELIMINACIÓN**

¿Está seguro que desea eliminar el siguiente fragmento?

• Título: **{fragment_details['title']}**
• Tipo: {fragment_details['type']}
• ID: `{fragment_details['id']}`

⚠️ **ADVERTENCIA**: Esta acción marcará el fragmento como inactivo.
Los fragmentos se desactivan en lugar de eliminarse para mantener la integridad de los datos.

Los usuarios que estén actualmente en este fragmento podrían experimentar problemas.
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("⚠️ Confirme la eliminación")
        
    except ValueError as e:
        logger.error(f"Error de validación al confirmar eliminación: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error preparando eliminación de fragmento: {e}")
        await callback.answer("❌ Error preparando eliminación", show_alert=True)

@router.callback_query(F.data.startswith("admin_confirm_delete_fragment?"))
@safe_handler("❌ Error eliminando fragmento.")
async def delete_fragment(callback: CallbackQuery, session: AsyncSession):
    """
    Elimina un fragmento tras confirmación.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Eliminar fragmento (desactivar)
        admin_service = NarrativeAdminService(session)
        await admin_service.delete_fragment(fragment_id)
        
        # Preparar teclado para volver al listado
        keyboard = get_fragments_list_keyboard()
        
        text = """
✅ **FRAGMENTO DESACTIVADO EXITOSAMENTE**

El fragmento ha sido marcado como inactivo y ya no estará disponible para los usuarios.

Para ver la lista de fragmentos, haga clic en el botón correspondiente.
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("✅ Fragmento desactivado")
        
    except ValueError as e:
        logger.error(f"Error de validación al eliminar fragmento: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error eliminando fragmento: {e}")
        await callback.answer("❌ Error eliminando fragmento", show_alert=True)

# ==================== VISUALIZACIÓN DE STORYBOARD ====================

@router.callback_query(F.data.startswith("admin_narrative_storyboard"))
@safe_handler("❌ Error cargando storyboard.")
async def view_storyboard(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra la visualización del storyboard narrativo.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Analizar parámetros de la callback query
        params = parse_callback_data(callback.data)
        view_type = params.get("view", "tree")
        root_id = params.get("root")
        
        # Preparar teclado
        keyboard = get_storyboard_keyboard(root_id, view_type)
        
        # Preparar mensaje
        text = f"""
🔖 **STORYBOARD NARRATIVO**
*Visualización de la estructura narrativa*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Para implementar una visualización completa se requiere el StoryboardService.

Seleccione un tipo de visualización y el fragmento raíz para comenzar.

Vista actual: **{view_type}**
"""
        
        if root_id:
            # Obtener detalles del fragmento raíz
            admin_service = NarrativeAdminService(session)
            fragment_details = await admin_service.get_fragment_details(root_id)
            
            text += f"""
**Fragmento raíz:** {fragment_details['title']}
**ID:** `{fragment_details['id']}`
**Tipo:** {fragment_details['type']}

Para ver la estructura completa, implemente el StoryboardService.
"""
        else:
            text += """
No hay fragmento raíz seleccionado. 
Utilice la opción "🔍 Buscar Fragmento" para seleccionar un punto de inicio.
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("🔖 Storyboard cargado")
        
    except Exception as e:
        logger.error(f"Error mostrando storyboard: {e}")
        await callback.answer("❌ Error cargando storyboard", show_alert=True)

# ==================== ANALÍTICAS NARRATIVAS ====================

@router.callback_query(F.data == "admin_narrative_analytics")
@safe_handler("❌ Error cargando analíticas narrativas.")
async def view_narrative_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra las analíticas del sistema narrativo.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener estadísticas
        admin_service = NarrativeAdminService(session)
        stats = await admin_service.get_narrative_stats()
        
        # Preparar teclado
        keyboard = get_narrative_analytics_keyboard()
        
        # Calcular distribución de tipos
        total = stats.get("total_fragments", 0)
        types = stats.get("fragments_by_type", {})
        
        story_percent = (types.get("STORY", 0) / total * 100) if total > 0 else 0
        decision_percent = (types.get("DECISION", 0) / total * 100) if total > 0 else 0
        info_percent = (types.get("INFO", 0) / total * 100) if total > 0 else 0
        
        # Preparar texto
        text = f"""
📊 **ANALÍTICAS NARRATIVAS**
*Estadísticas y métricas del sistema narrativo*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **Fragmentos**
• Total: {stats.get("total_fragments", 0)}
• Activos: {stats.get("active_fragments", 0)} ({stats.get("active_fragments", 0)/total*100:.1f}% del total)
• Inactivos: {stats.get("inactive_fragments", 0)} ({stats.get("inactive_fragments", 0)/total*100:.1f}% del total)

📝 **Distribución por Tipo**
• Historia: {types.get("STORY", 0)} ({story_percent:.1f}%)
• Decisión: {types.get("DECISION", 0)} ({decision_percent:.1f}%)
• Información: {types.get("INFO", 0)} ({info_percent:.1f}%)

🔀 **Conexiones**
• Fragmentos con conexiones: {stats.get("fragments_with_connections", 0)}
• Porcentaje conectado: {stats.get("fragments_with_connections", 0)/total*100:.1f}%

👥 **Participación**
• Usuarios en narrativa: {stats.get("users_in_narrative", 0)}
• Promedio fragmentos completados: {stats.get("avg_fragments_completed", 0):.1f}

Para ver análisis más detallados, seleccione una opción:
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("📊 Analíticas cargadas")
        
    except Exception as e:
        logger.error(f"Error mostrando analíticas narrativas: {e}")
        await callback.answer("❌ Error cargando analíticas", show_alert=True)

# ==================== BÚSQUEDA DE FRAGMENTOS ====================

@router.callback_query(F.data == "admin_narrative_search")
@safe_handler("❌ Error iniciando búsqueda.")
async def start_narrative_search(callback: CallbackQuery, state: FSMContext):
    """
    Inicia la búsqueda de fragmentos narrativos.
    """
    try:
        # Establecer estado FSM
        await state.set_state(NarrativeFragmentStates.entering_search_query)
        
        text = """
🔍 **BÚSQUEDA DE FRAGMENTOS**
*Introduzca términos para buscar*

Por favor, envíe el texto a buscar en los fragmentos narrativos.
La búsqueda se realizará en títulos y contenido.

*Ejemplos:*
• "Diana"
• "jardín"
• "decisión importante"

Para cancelar la búsqueda, escriba "cancelar".
"""
        
        await safe_edit(callback.message, text)
        await callback.answer("🔍 Introduzca términos de búsqueda")
        
    except Exception as e:
        logger.error(f"Error iniciando búsqueda narrativa: {e}")
        await callback.answer("❌ Error iniciando búsqueda", show_alert=True)

@router.message(NarrativeFragmentStates.entering_search_query)
@safe_handler("❌ Error procesando búsqueda.")
async def process_search_query(message: Message, state: FSMContext, session: AsyncSession):
    """
    Procesa la consulta de búsqueda y muestra resultados.
    """
    try:
        # Verificar si el usuario quiere cancelar
        if message.text.lower() == "cancelar":
            await state.clear()
            await safe_answer(message, "❌ Búsqueda cancelada.")
            return
        
        # Obtener consulta
        query = message.text.strip()
        if not query or len(query) < 2:
            await safe_answer(message, "❌ Por favor, introduzca al menos 2 caracteres para buscar.")
            return
        
        # Realizar búsqueda
        admin_service = NarrativeAdminService(session)
        search_results = await admin_service.get_all_fragments(
            page=1,
            limit=10,
            search_query=query
        )
        
        # Limpiar estado FSM
        await state.clear()
        
        # Preparar teclado con resultados
        keyboard = get_search_results_keyboard(
            results=search_results["items"],
            page=1,
            total_pages=search_results["total_pages"],
            query=query
        )
        
        # Preparar texto con resultados
        if not search_results["items"]:
            text = f"""
🔍 **RESULTADOS DE BÚSQUEDA**
*Consulta: "{query}"*

No se encontraron fragmentos que coincidan con la búsqueda.

Intente con otros términos o use el botón para una nueva búsqueda.
"""
        else:
            text = f"""
🔍 **RESULTADOS DE BÚSQUEDA**
*Consulta: "{query}"*
*Encontrados: {search_results["total"]} fragmentos*

Página {search_results["page"]}/{search_results["total_pages"]}

**Fragmentos encontrados:**
"""
            
            for i, fragment in enumerate(search_results["items"]):
                # Iconos según tipo
                icon = "📖" if fragment["type"] == "STORY" else "🔀" if fragment["type"] == "DECISION" else "ℹ️"
                
                # Indicador de estado
                status = "✅" if fragment["is_active"] else "❌"
                
                # Agregar a la lista
                text += f"{i+1}. {status} {icon} **{fragment['title']}**\n"
        
        await safe_answer(message, text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error procesando búsqueda: {e}")
        await safe_answer(message, "❌ Error realizando búsqueda. Por favor, inténtelo de nuevo.")
        await state.clear()

# ==================== CONEXIONES DE FRAGMENTOS ====================

@router.callback_query(F.data.startswith("admin_fragment_connections?"))
@safe_handler("❌ Error cargando conexiones de fragmento.")
async def view_fragment_connections(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra y permite gestionar las conexiones de un fragmento.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
    
    try:
        # Obtener ID del fragmento
        params = parse_callback_data(callback.data)
        fragment_id = params.get("id")
        
        if not fragment_id:
            await callback.answer("❌ ID de fragmento no especificado", show_alert=True)
            return
        
        # Obtener conexiones del fragmento
        admin_service = NarrativeAdminService(session)
        connections_data = await admin_service.get_fragment_connections(fragment_id)
        
        # Preparar teclado
        keyboard = get_fragment_connections_keyboard(
            fragment_id=fragment_id,
            connections=connections_data.get("outgoing_connections", [])
        )
        
        # Preparar texto
        outgoing = connections_data.get("outgoing_connections", [])
        incoming = connections_data.get("incoming_connections", [])
        
        text = f"""
🔄 **CONEXIONES DE FRAGMENTO**
*{connections_data.get('fragment_title', 'Fragmento')}*

ID: `{fragment_id}`
Tipo: {connections_data.get('fragment_type', 'Desconocido')}

**Conexiones Salientes ({len(outgoing)}):**
"""
        
        if not outgoing:
            text += "• No hay conexiones salientes configuradas.\n"
        else:
            for i, conn in enumerate(outgoing):
                text += f"{i+1}. \"{conn.get('choice_text', 'Sin texto')}\" → "
                text += f"**{conn.get('title', 'Fragmento')}**"
                if not conn.get('is_active', True):
                    text += " ❌"
                text += "\n"
        
        text += f"\n**Conexiones Entrantes ({len(incoming)}):**\n"
        
        if not incoming:
            text += "• No hay conexiones entrantes.\n"
        else:
            for i, conn in enumerate(incoming):
                text += f"{i+1}. **{conn.get('title', 'Fragmento')}** → "
                text += f"\"{conn.get('choice_text', 'Sin texto')}\""
                if not conn.get('is_active', True):
                    text += " ❌"
                text += "\n"
        
        text += """
Use los botones para gestionar las conexiones salientes.
Para añadir una nueva conexión, pulse "➕ Añadir Conexión".
"""
        
        await safe_edit(callback.message, text, reply_markup=keyboard)
        await callback.answer("🔄 Conexiones cargadas")
        
    except ValueError as e:
        logger.error(f"Error de validación al ver conexiones: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"Error mostrando conexiones de fragmento: {e}")
        await callback.answer("❌ Error cargando conexiones", show_alert=True)

# ==================== INTEGRAR ROUTER CON APLICACIÓN ====================

def setup_narrative_admin_handlers(dp):
    """
    Configura los handlers de administración narrativa en el despachador.
    
    Args:
        dp: Despachador de mensajes de Aiogram
    """
    dp.include_router(router)
    logger.info("Handlers de administración narrativa configurados")
    
    return router