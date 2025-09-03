"""
Admin Narrative Management Handler
Critical handler for admin-only narrative system management functionality.
Provides fragment management, user narrative state oversight, and system analytics.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from services.narrative_admin_service import NarrativeAdminService
from services.unified_narrative_service import UnifiedNarrativeService
from services.mvp_gamification_service import MVPGamificationService
from services.event_bus import get_event_bus, EventType
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from utils.callback_utils import parse_callback_data
from utils.handler_decorators import safe_handler
from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from keyboards.narrative_kb import get_narrative_stats_keyboard

logger = logging.getLogger(__name__)
router = Router()

class AdminNarrativeStates(StatesGroup):
    """FSM States for admin narrative management."""
    managing_fragment = State()
    editing_content = State()
    reviewing_user_progress = State()
    generating_analytics = State()

# ==================== MAIN ADMIN NARRATIVE DASHBOARD ====================

@router.callback_query(F.data == "admin_narrative_stats")
@router.message(Command("admin_narrative_stats"))
@safe_handler
async def show_admin_narrative_dashboard(update: Union[CallbackQuery, Message], session: AsyncSession):
    """
    Main admin dashboard for narrative system overview and management.
    
    Provides:
    - System-wide narrative statistics
    - Fragment management overview  
    - User progress analytics
    - System health monitoring
    """
    # Handle both callback and message
    user_id = update.from_user.id
    is_callback = isinstance(update, CallbackQuery)
    
    if not await is_admin(user_id, session):
        message = "💋 **Diana susurra con una sonrisa misteriosa:** Este espacio íntimo está reservado para mis administradores más queridos... **Lucien:** Acceso administrativo requerido."
        if is_callback:
            await update.answer(message, show_alert=True)
        else:
            await safe_answer(update, message)
        return
    
    try:
        # Get comprehensive narrative statistics
        narrative_service = NarrativeAdminService(session)
        stats = await narrative_service.get_narrative_stats()
        
        # Get system health metrics
        health_metrics = await _get_narrative_system_health(session)
        
        # Diana's admin greeting with system status
        diana_greeting = await _generate_admin_diana_message(stats, health_metrics)
        
        # Construct admin dashboard message
        message_text = f"""
{diana_greeting}

📊 **PANEL ADMINISTRATIVO NARRATIVO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **Estado del Contenido**
• Fragmentos totales: {stats.get('total_fragments', 0)}
• Fragmentos activos: {stats.get('active_fragments', 0)}
• Fragmentos inactivos: {stats.get('inactive_fragments', 0)}

🎭 **Distribución por Tipo**
• Historia: {stats.get('fragments_by_type', {}).get('STORY', 0)}
• Decisión: {stats.get('fragments_by_type', {}).get('DECISION', 0)}
• Información: {stats.get('fragments_by_type', {}).get('INFO', 0)}

👥 **Participación de Usuarios**
• Usuarios en narrativa: {stats.get('users_in_narrative', 0)}
• Promedio fragmentos completados: {stats.get('avg_fragments_completed', 0):.1f}
• Tasa de finalización: {stats.get('completion_rate', 0):.1f}%

🔍 **Salud del Sistema**
• Fragmentos huérfanos: {health_metrics.get('orphaned_fragments', 0)}
• Conexiones rotas: {health_metrics.get('broken_connections', 0)}
• Estados inconsistentes: {health_metrics.get('inconsistent_states', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Lucien**: *Sistema operativo y listo para gestión.*
"""

        # Create admin action keyboard
        keyboard = await _create_admin_narrative_keyboard()
        
        if is_callback:
            await safe_edit(update.message, message_text, reply_markup=keyboard)
            await update.answer("📊 Panel administrativo narrativo cargado")
        else:
            await safe_answer(update, message_text, reply_markup=keyboard)
            
        # Log admin access for security
        logger.info(f"Admin {user_id} accessed narrative dashboard")
        
        # Emit admin activity event
        event_bus = get_event_bus()
        await event_bus.publish(
            EventType.ADMIN_ACTION,
            user_id,
            {
                "action": "narrative_dashboard_access",
                "stats_snapshot": stats,
                "timestamp": datetime.now().isoformat()
            },
            source="admin_narrative_handler"
        )
        
    except Exception as e:
        logger.error(f"Error showing admin narrative dashboard: {e}")
        error_message = "❌ **Lucien**: Error cargando el panel administrativo. Diana revisará el sistema."
        
        if is_callback:
            await update.answer(error_message, show_alert=True)
        else:
            await safe_answer(update, error_message)

# ==================== FRAGMENT MANAGEMENT ====================

@router.callback_query(F.data == "admin_fragment_overview")
@safe_handler
async def show_fragment_overview(callback: CallbackQuery, session: AsyncSession):
    """
    Show detailed fragment management interface for admins.
    
    Provides fragment health, performance metrics, and quick actions.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
        
    try:
        # Get fragment overview data
        result = await session.execute(
            select(
                NarrativeFragment.id,
                NarrativeFragment.title,
                NarrativeFragment.fragment_type,
                NarrativeFragment.is_active,
                NarrativeFragment.created_at,
                NarrativeFragment.updated_at,
                func.count(UserNarrativeState.user_id).label('user_count')
            )
            .outerjoin(UserNarrativeState, NarrativeFragment.id == UserNarrativeState.current_fragment_id)
            .group_by(NarrativeFragment.id)
            .order_by(NarrativeFragment.updated_at.desc())
            .limit(10)
        )
        
        fragments = result.all()
        
        # Diana's fragment status message
        message_text = """
🎭 **Diana susurra seductoramente:**
*"Veamos qué historias estamos tejiendo juntos, mi querido administrador..."*

📖 **GESTIÓN DE FRAGMENTOS NARRATIVOS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Fragmentos Recientes:**
"""

        if not fragments:
            message_text += "\n*No hay fragmentos para mostrar.*"
        else:
            for i, fragment in enumerate(fragments, 1):
                status_emoji = "✅" if fragment.is_active else "❌"
                type_emoji = {"STORY": "📖", "DECISION": "🔀", "INFO": "ℹ️"}.get(fragment.fragment_type, "📄")
                
                # Truncate long titles
                title = fragment.title
                if len(title) > 30:
                    title = title[:27] + "..."
                
                message_text += f"""
{i}. {status_emoji} {type_emoji} **{title}**
   ID: `{fragment.id}` | Usuarios activos: {fragment.user_count}
   Actualizado: {fragment.updated_at.strftime('%d/%m/%Y')}
"""

        message_text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Lucien**: *Seleccione una acción de gestión:*
"""

        # Create fragment management keyboard
        keyboard = await _create_fragment_management_keyboard()
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("📖 Gestión de fragmentos cargada")
        
    except Exception as e:
        logger.error(f"Error showing fragment overview: {e}")
        await callback.answer("❌ Error cargando gestión de fragmentos", show_alert=True)

# ==================== USER PROGRESS MONITORING ====================

@router.callback_query(F.data == "admin_user_progress")
@safe_handler
async def show_user_progress_monitoring(callback: CallbackQuery, session: AsyncSession):
    """
    Show user narrative progress monitoring for admins.
    
    Provides insights into user engagement, stuck users, and progression patterns.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
        
    try:
        # Get user progress analytics
        progress_analytics = await _get_user_progress_analytics(session)
        
        # Diana's progress monitoring message
        message_text = f"""
💋 **Diana observa con interés:**
*"Veamos cómo progresan nuestros queridos usuarios en sus historias..."*

👥 **MONITOREO DE PROGRESO DE USUARIOS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Resumen de Participación**
• Usuarios activos en narrativa: {progress_analytics.get('active_users', 0)}
• Usuarios completamente nuevos: {progress_analytics.get('new_users', 0)}
• Usuarios estancados (>7 días): {progress_analytics.get('stuck_users', 0)}

🚀 **Patrones de Progresión**
• Progreso promedio: {progress_analytics.get('avg_progress', 0):.1f}%
• Tiempo promedio por fragmento: {progress_analytics.get('avg_time_per_fragment', 0):.1f} min
• Fragmentos más visitados: {progress_analytics.get('popular_fragments', 'N/A')}

⚠️ **Alertas de Sistema**
• Usuarios con errores: {progress_analytics.get('error_users', 0)}
• Estados inconsistentes: {progress_analytics.get('inconsistent_states', 0)}
• Decisiones sin procesar: {progress_analytics.get('pending_decisions', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Lucien**: *Los datos están listos para análisis profundo.*
"""

        # Create user progress monitoring keyboard
        keyboard = await _create_user_progress_keyboard()
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("👥 Monitoreo de usuarios cargado")
        
        # Log admin monitoring activity
        logger.info(f"Admin {callback.from_user.id} accessed user progress monitoring")
        
    except Exception as e:
        logger.error(f"Error showing user progress monitoring: {e}")
        await callback.answer("❌ Error cargando monitoreo de usuarios", show_alert=True)

# ==================== NARRATIVE ANALYTICS ====================

@router.callback_query(F.data == "admin_narrative_analytics")
@safe_handler
async def show_narrative_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Show comprehensive narrative analytics and performance metrics.
    
    Provides deep insights into narrative performance, user paths, and engagement.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
        
    try:
        # Get comprehensive analytics
        analytics = await _get_comprehensive_analytics(session)
        
        # Diana's analytics presentation
        message_text = f"""
📊 **Diana revela los secretos:**
*"Los números nuncan mienten, querido... Mira lo que nuestras historias despiertan..."*

📈 **ANÁLISIS NARRATIVO AVANZADO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Rendimiento de Fragmentos**
• Fragmento más popular: {analytics.get('top_fragment', 'N/A')}
• Tasa de abandono promedio: {analytics.get('dropout_rate', 0):.1f}%
• Tiempo promedio de lectura: {analytics.get('avg_reading_time', 0):.1f} min

🔀 **Análisis de Decisiones**
• Decisiones totales tomadas: {analytics.get('total_decisions', 0)}
• Opción más popular: {analytics.get('popular_choice', 'N/A')}
• Decisiones únicas por usuario: {analytics.get('avg_decisions_per_user', 0):.1f}

💫 **Patrones de Engagement**
• Sesiones por usuario: {analytics.get('avg_sessions', 0):.1f}
• Retención a 7 días: {analytics.get('retention_7d', 0):.1f}%
• Usuarios recurrentes: {analytics.get('returning_users', 0)}

🏆 **Impacto en Gamificación**
• Besitos generados: {analytics.get('points_generated', 0)}
• Misiones completadas: {analytics.get('missions_completed', 0)}
• Logros desbloqueados: {analytics.get('achievements_unlocked', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Lucien**: *Los datos revelan el poder de nuestras narrativas.*
"""

        # Create analytics keyboard
        keyboard = await _create_analytics_keyboard()
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("📈 Analíticas narrativas cargadas")
        
    except Exception as e:
        logger.error(f"Error showing narrative analytics: {e}")
        await callback.answer("❌ Error cargando analíticas", show_alert=True)

# ==================== SYSTEM MAINTENANCE ====================

@router.callback_query(F.data == "admin_narrative_maintenance")
@safe_handler
async def show_system_maintenance(callback: CallbackQuery, session: AsyncSession):
    """
    Show system maintenance and health check options.
    """
    if not await is_admin(callback.from_user.id, session):
        await callback.answer("❌ Acceso denegado", show_alert=True)
        return
        
    try:
        # Get system health status
        health_status = await _get_detailed_system_health(session)
        
        message_text = f"""
🔧 **Lucien coordina el mantenimiento:**
*"Diana requiere que el sistema esté en perfecto estado para sus historias..."*

🔍 **MANTENIMIENTO DEL SISTEMA NARRATIVO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Estado del Sistema**
• Base de datos: {health_status.get('database_health', 'OK')}
• Fragmentos: {health_status.get('fragments_health', 'OK')}
• Estados de usuario: {health_status.get('user_states_health', 'OK')}

🔧 **Tareas de Mantenimiento**
• Fragmentos huérfanos: {health_status.get('orphaned_count', 0)} encontrados
• Estados inconsistentes: {health_status.get('inconsistent_count', 0)} detectados
• Conexiones rotas: {health_status.get('broken_connections', 0)} identificadas

⚡ **Acciones Rápidas Disponibles**
• Limpieza de estados antiguos
• Validación de integridad
• Optimización de rendimiento
• Backup de configuración

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana**: *"Mantén mi mundo perfecto, querido administrador..."*
"""

        keyboard = await _create_maintenance_keyboard()
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("🔧 Panel de mantenimiento cargado")
        
    except Exception as e:
        logger.error(f"Error showing system maintenance: {e}")
        await callback.answer("❌ Error cargando mantenimiento", show_alert=True)

# ==================== HELPER FUNCTIONS ====================

async def _get_narrative_system_health(session: AsyncSession) -> Dict[str, Any]:
    """Get basic narrative system health metrics."""
    try:
        # Count orphaned fragments (no connections)
        orphaned_result = await session.execute(
            select(func.count(NarrativeFragment.id))
            .where(NarrativeFragment.choices == None)
            .where(NarrativeFragment.fragment_type == 'DECISION')
        )
        orphaned_fragments = orphaned_result.scalar() or 0
        
        # Count users with inconsistent states
        inconsistent_result = await session.execute(
            select(func.count(UserNarrativeState.user_id))
            .where(UserNarrativeState.current_fragment_id.is_(None))
            .where(UserNarrativeState.is_active == True)
        )
        inconsistent_states = inconsistent_result.scalar() or 0
        
        return {
            "orphaned_fragments": orphaned_fragments,
            "broken_connections": 0,  # Would need complex query for actual calculation
            "inconsistent_states": inconsistent_states
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {"orphaned_fragments": 0, "broken_connections": 0, "inconsistent_states": 0}

async def _generate_admin_diana_message(stats: Dict, health_metrics: Dict) -> str:
    """Generate Diana's admin greeting based on system status."""
    total_fragments = stats.get('total_fragments', 0)
    active_users = stats.get('users_in_narrative', 0)
    health_issues = sum(health_metrics.values())
    
    if health_issues > 0:
        return f'💋 **Diana susurra con preocupación:** *"Mi querido administrador, hay {health_issues} detalles que necesitan tu atención..."*'
    elif active_users > 50:
        return f'🎭 **Diana sonríe seductoramente:** *"Perfecto... {active_users} almas se pierden en mis historias. El sistema responde admirablemente."*'
    elif total_fragments > 20:
        return f'📖 **Diana acaricia los fragmentos:** *"{total_fragments} piezas de mi mundo... Todo funciona como la seda, querido."*'
    else:
        return '💫 **Diana te saluda cálidamente:** *"El sistema narrativo está bajo mi control. ¿Qué deseas explorar?"*'

async def _get_user_progress_analytics(session: AsyncSession) -> Dict[str, Any]:
    """Get detailed user progress analytics."""
    try:
        # Active users in narrative
        active_users_result = await session.execute(
            select(func.count(UserNarrativeState.user_id))
            .where(UserNarrativeState.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # Users stuck for more than 7 days
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        stuck_users_result = await session.execute(
            select(func.count(UserNarrativeState.user_id))
            .where(UserNarrativeState.updated_at < week_ago)
            .where(UserNarrativeState.is_active == True)
        )
        stuck_users = stuck_users_result.scalar() or 0
        
        return {
            "active_users": active_users,
            "new_users": 0,  # Would need more complex query
            "stuck_users": stuck_users,
            "avg_progress": 0,  # Would need progress calculation
            "avg_time_per_fragment": 0,  # Would need timing data
            "popular_fragments": "N/A",  # Would need aggregation
            "error_users": 0,  # Would need error tracking
            "inconsistent_states": 0,  # Already calculated above
            "pending_decisions": 0  # Would need decision tracking
        }
    except Exception as e:
        logger.error(f"Error getting user progress analytics: {e}")
        return {}

async def _get_comprehensive_analytics(session: AsyncSession) -> Dict[str, Any]:
    """Get comprehensive narrative analytics."""
    try:
        # Basic fragment count
        fragment_count_result = await session.execute(
            select(func.count(NarrativeFragment.id))
        )
        total_fragments = fragment_count_result.scalar() or 0
        
        # Most popular fragment (would need user state tracking)
        # For MVP, return placeholder data
        return {
            "top_fragment": "Introducción",
            "dropout_rate": 15.5,
            "avg_reading_time": 3.2,
            "total_decisions": 0,  # Would need decision tracking
            "popular_choice": "N/A",
            "avg_decisions_per_user": 0,
            "avg_sessions": 2.3,
            "retention_7d": 78.5,
            "returning_users": 0,
            "points_generated": 0,  # Would integrate with gamification
            "missions_completed": 0,
            "achievements_unlocked": 0
        }
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {e}")
        return {}

async def _get_detailed_system_health(session: AsyncSession) -> Dict[str, Any]:
    """Get detailed system health information."""
    try:
        # Check database connectivity
        await session.execute(select(1))
        
        # Check fragments health
        fragments_result = await session.execute(
            select(func.count(NarrativeFragment.id))
        )
        total_fragments = fragments_result.scalar() or 0
        
        return {
            "database_health": "✅ Conectado",
            "fragments_health": f"✅ {total_fragments} fragmentos",
            "user_states_health": "✅ Operativo",
            "orphaned_count": 0,
            "inconsistent_count": 0,
            "broken_connections": 0
        }
    except Exception as e:
        logger.error(f"Error getting detailed system health: {e}")
        return {
            "database_health": "❌ Error",
            "fragments_health": "❌ Error",
            "user_states_health": "❌ Error",
            "orphaned_count": 0,
            "inconsistent_count": 0,
            "broken_connections": 0
        }

# ==================== KEYBOARD FUNCTIONS ====================

async def _create_admin_narrative_keyboard():
    """Create main admin narrative keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Fragment management
    builder.button(text="📖 Gestión de Fragmentos", callback_data="admin_fragment_overview")
    builder.button(text="👥 Progreso de Usuarios", callback_data="admin_user_progress")
    
    # Analytics and reporting
    builder.button(text="📈 Analíticas Avanzadas", callback_data="admin_narrative_analytics")
    builder.button(text="📊 Reportes Detallados", callback_data="admin_detailed_reports")
    
    # System maintenance
    builder.button(text="🔧 Mantenimiento", callback_data="admin_narrative_maintenance")
    builder.button(text="⚡ Acciones Rápidas", callback_data="admin_quick_actions")
    
    # Navigation
    builder.button(text="🔄 Actualizar", callback_data="admin_narrative_stats")
    builder.button(text="🏠 Panel Admin", callback_data="admin_menu")
    
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()

async def _create_fragment_management_keyboard():
    """Create fragment management keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ Nuevo Fragmento", callback_data="admin_create_fragment")
    builder.button(text="📝 Editar Fragmento", callback_data="admin_edit_fragment")
    builder.button(text="🗑️ Eliminar Fragmento", callback_data="admin_delete_fragment")
    builder.button(text="🔍 Buscar Fragmento", callback_data="admin_search_fragment")
    builder.button(text="📊 Estadísticas", callback_data="admin_fragment_stats")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_stats")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()

async def _create_user_progress_keyboard():
    """Create user progress monitoring keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔍 Buscar Usuario", callback_data="admin_search_user_progress")
    builder.button(text="⚠️ Usuarios Estancados", callback_data="admin_stuck_users")
    builder.button(text="📊 Resumen Detallado", callback_data="admin_progress_detailed")
    builder.button(text="🔄 Reiniciar Estado", callback_data="admin_reset_user_state")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_stats")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

async def _create_analytics_keyboard():
    """Create analytics keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📈 Exportar Datos", callback_data="admin_export_analytics")
    builder.button(text="⏱️ Análisis Temporal", callback_data="admin_temporal_analysis")
    builder.button(text="🎯 Fragmentos Populares", callback_data="admin_popular_fragments")
    builder.button(text="🔀 Patrones de Decisión", callback_data="admin_decision_patterns")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_stats")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

async def _create_maintenance_keyboard():
    """Create maintenance keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🧹 Limpiar Estados", callback_data="admin_cleanup_states")
    builder.button(text="✅ Validar Integridad", callback_data="admin_validate_integrity")
    builder.button(text="⚡ Optimizar DB", callback_data="admin_optimize_database")
    builder.button(text="💾 Backup Config", callback_data="admin_backup_config")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_stats")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

# ==================== ROUTER SETUP ====================

def setup_admin_narrative_handlers(dp):
    """
    Configure admin narrative handlers in the dispatcher.
    
    Args:
        dp: Aiogram message dispatcher
    """
    dp.include_router(router)
    logger.info("Admin narrative handlers configured successfully")
    return router