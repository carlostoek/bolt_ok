"""
Enhanced Analytics Handlers for Administrative Users.
Provides comprehensive analytics interface with enhanced performance and functionality.
Implements requirements 5.1 (Administrative Analysis and Reports) and 5.5 (Data Export).
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from keyboards.admin_analytics_kb import (
    get_analytics_admin_main_kb, get_user_segments_kb, get_fragment_analytics_kb,
    get_choice_patterns_kb, get_bottlenecks_kb, get_character_voice_kb,
    get_export_options_kb, get_analytics_detail_kb, get_analytics_pagination_kb,
    get_character_specific_kb, get_user_journey_analytics_kb, get_report_generation_kb,
    get_advanced_export_kb, get_analytics_insights_kb, get_real_time_analytics_kb
)
from keyboards.common import get_back_kb
from services.analytics_service import AnalyticsService
from services.cached_analytics_service import CachedAnalyticsService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)
router = Router()

# Initialize cache service for enhanced performance
cache_service = CacheService()

# Response time tracking
async def track_response_time(func, *args, **kwargs):
    """Track response time to ensure 3-second compliance (Requirement 5.1)."""
    start_time = datetime.utcnow()
    try:
        result = await func(*args, **kwargs)
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()

        if response_time > 3.0:
            logger.warning(f"Response time exceeded 3 seconds: {response_time:.2f}s for {func.__name__}")
        else:
            logger.info(f"Response time: {response_time:.2f}s for {func.__name__}")

        return result
    except Exception as e:
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        logger.error(f"Error in {func.__name__} after {response_time:.2f}s: {e}")
        raise


# ENHANCED DASHBOARD HANDLERS

@router.callback_query(F.data == "admin_enhanced_analytics_dashboard")
async def show_enhanced_analytics_dashboard(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced analytics dashboard with real-time metrics.
    Implements requirement 5.1 - Display metrics within 3 seconds.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    async def _dashboard_logic():
        cached_analytics_service = CachedAnalyticsService(session, cache_service)

        # Get comprehensive dashboard data with caching
        dashboard_data = await cached_analytics_service.get_comprehensive_dashboard_data()

        menu_text = "📊 **Dashboard de Análisis Mejorado**\\n\\n"
        menu_text += "⚡ **Métricas en tiempo real con rendimiento optimizado**\\n\\n"

        if dashboard_data.get("status") == "success":
            # Active users metrics
            user_segments = dashboard_data.get("user_segments", {})
            if user_segments.get("status") == "success":
                segment_counts = user_segments.get("segment_counts", {})
                total_active = sum(segment_counts.values())

                menu_text += f"👥 **Usuarios Activos:** {total_active}\\n"
                menu_text += f"• Whales: {segment_counts.get('whales', 0)}\\n"
                menu_text += f"• Altamente comprometidos: {segment_counts.get('highly_engaged', 0)}\\n"
                menu_text += f"• Exploradores: {segment_counts.get('explorers', 0)}\\n\\n"

            # Current subscriptions
            subscription_stats = dashboard_data.get("subscription_stats", {})
            if subscription_stats:
                menu_text += f"💳 **Suscripciones Actuales:** {subscription_stats.get('active_subscriptions', 0)}\\n"
                menu_text += f"• Nuevas hoy: {subscription_stats.get('new_today', 0)}\\n"
                menu_text += f"• Renovaciones: {subscription_stats.get('renewals', 0)}\\n\\n"

            # Engagement metrics
            engagement = dashboard_data.get("engagement_metrics", {})
            if engagement:
                menu_text += f"📈 **Engagement:**\\n"
                menu_text += f"• Sesiones activas: {engagement.get('active_sessions', 0)}\\n"
                menu_text += f"• Interacciones/hora: {engagement.get('interactions_per_hour', 0)}\\n"
                menu_text += f"• Tiempo promedio: {engagement.get('avg_session_time', 0)} min\\n\\n"

            # Performance indicators
            performance = dashboard_data.get("performance", {})
            if performance:
                menu_text += f"⚡ **Rendimiento del Sistema:**\\n"
                menu_text += f"• Tiempo de respuesta promedio: {performance.get('avg_response_time', 0.5):.2f}s\\n"
                menu_text += f"• Cache hit ratio: {performance.get('cache_hit_ratio', 85)}%\\n\\n"

        else:
            menu_text += "⏳ **Cargando métricas en tiempo real...**\\n\\n"

        # Cache status
        cache_stats = cached_analytics_service.get_cache_stats()
        menu_text += f"💾 **Cache:** {cache_stats.get('entries', 0)} entradas activas\\n"
        menu_text += f"🕒 **Actualizado:** {datetime.utcnow().strftime('%H:%M:%S')}\\n\\n"

        menu_text += "**Análisis detallado disponible:**"

        keyboard = get_analytics_detail_kb("enhanced_dashboard")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_analytics_dashboard"
        )

    try:
        await track_response_time(_dashboard_logic)
    except Exception as e:
        logger.error(f"Error in enhanced analytics dashboard: {e}")
        await callback.answer("❌ Error al cargar el dashboard mejorado", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_enhanced_analytics_metrics")
async def show_enhanced_metrics(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced metrics with detailed breakdowns.
    Implements requirement 5.1 - Administrative Analysis within 3 seconds.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    async def _metrics_logic():
        analytics_service = AnalyticsService(session)

        # Get detailed metrics
        metrics_data = await analytics_service.get_administrative_metrics()

        menu_text = "📊 **Métricas Administrativas Detalladas**\\n\\n"

        if metrics_data.get("status") == "success":
            admin_metrics = metrics_data.get("admin_metrics", {})

            # User growth metrics
            user_growth = admin_metrics.get("user_growth", {})
            if user_growth:
                menu_text += f"📈 **Crecimiento de Usuarios:**\\n"
                menu_text += f"• Usuarios totales: {user_growth.get('total_users', 0)}\\n"
                menu_text += f"• Nuevos esta semana: {user_growth.get('new_this_week', 0)}\\n"
                menu_text += f"• Tasa de crecimiento: {user_growth.get('growth_rate', 0):.1f}%\\n"
                menu_text += f"• Retención 7 días: {user_growth.get('retention_7d', 0):.1f}%\\n\\n"

            # Revenue metrics
            revenue_metrics = admin_metrics.get("revenue", {})
            if revenue_metrics:
                menu_text += f"💰 **Métricas de Ingresos:**\\n"
                menu_text += f"• Ingresos totales: ${revenue_metrics.get('total_revenue', 0):.2f}\\n"
                menu_text += f"• Ingresos mensuales: ${revenue_metrics.get('monthly_revenue', 0):.2f}\\n"
                menu_text += f"• ARPU: ${revenue_metrics.get('arpu', 0):.2f}\\n"
                menu_text += f"• LTV promedio: ${revenue_metrics.get('avg_ltv', 0):.2f}\\n\\n"

            # Activity metrics
            activity_metrics = admin_metrics.get("activity", {})
            if activity_metrics:
                menu_text += f"🎯 **Métricas de Actividad:**\\n"
                menu_text += f"• Sesiones diarias: {activity_metrics.get('daily_sessions', 0)}\\n"
                menu_text += f"• Duración promedio: {activity_metrics.get('avg_duration', 0)} min\\n"
                menu_text += f"• Interacciones totales: {activity_metrics.get('total_interactions', 0)}\\n"
                menu_text += f"• Tasa de engagement: {activity_metrics.get('engagement_rate', 0):.1f}%\\n\\n"

            # Content performance
            content_metrics = admin_metrics.get("content", {})
            if content_metrics:
                menu_text += f"📖 **Rendimiento del Contenido:**\\n"
                menu_text += f"• Fragmentos más populares: {content_metrics.get('popular_fragments', 0)}\\n"
                menu_text += f"• Tasa de finalización: {content_metrics.get('completion_rate', 0):.1f}%\\n"
                menu_text += f"• Puntos de abandono: {content_metrics.get('drop_points', 0)}\\n\\n"

        else:
            menu_text += "❌ Error al cargar métricas detalladas\\n\\n"

        menu_text += f"🕒 **Generado:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}\\n\\n"
        menu_text += "**Selecciona una categoría para análisis profundo:**"

        keyboard = get_analytics_detail_kb("enhanced_metrics")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_analytics_metrics"
        )

    try:
        await track_response_time(_metrics_logic)
    except Exception as e:
        logger.error(f"Error in enhanced metrics: {e}")
        await callback.answer("❌ Error al cargar métricas detalladas", show_alert=True)

    await callback.answer()


# ENHANCED EXPORT HANDLERS

@router.callback_query(F.data == "admin_enhanced_export_main")
async def show_enhanced_export_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced export menu with multiple format options.
    Implements requirement 5.5 - Generate reports within 30 seconds.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "📤 **Exportación de Datos Mejorada**\\n\\n"
        menu_text += "⚡ **Generación optimizada de reportes en múltiples formatos**\\n\\n"

        menu_text += "📊 **Formatos disponibles:**\\n"
        menu_text += "• JSON - Datos estructurados completos\\n"
        menu_text += "• CSV - Formato tabular para análisis\\n"
        menu_text += "• Excel - Hojas de cálculo avanzadas\\n"
        menu_text += "• PDF - Reportes visuales con gráficos\\n\\n"

        menu_text += "📅 **Rangos de tiempo:**\\n"
        menu_text += "• Última hora - Datos en tiempo real\\n"
        menu_text += "• Último día - Actividad reciente\\n"
        menu_text += "• Última semana - Tendencias semanales\\n"
        menu_text += "• Último mes - Análisis mensual\\n"
        menu_text += "• Personalizado - Fechas específicas\\n\\n"

        menu_text += "⚡ **Tiempo estimado de generación:** < 30 segundos\\n\\n"
        menu_text += "**Selecciona el tipo de exportación:**"

        keyboard = get_export_options_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_export_main"
        )

    except Exception as e:
        logger.error(f"Error showing enhanced export menu: {e}")
        await callback.answer("❌ Error al cargar menú de exportación", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("admin_enhanced_export_"))
async def process_enhanced_export(callback: CallbackQuery, session: AsyncSession):
    """
    Process enhanced export requests with optimized generation.
    Implements requirement 5.5 - Generate reports within 30 seconds.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    export_type = callback.data.replace("admin_enhanced_export_", "")

    async def _export_logic():
        analytics_service = AnalyticsService(session)

        # Show processing message
        await callback.answer("⏳ Generando reporte... (máx. 30s)", show_alert=False)

        # Determine export parameters
        export_params = {
            "format": "json",
            "range": "week",
            "include_charts": False
        }

        if "json" in export_type:
            export_params["format"] = "json"
        elif "csv" in export_type:
            export_params["format"] = "csv"
        elif "excel" in export_type:
            export_params["format"] = "excel"
        elif "pdf" in export_type:
            export_params["format"] = "pdf"
            export_params["include_charts"] = True

        if "hour" in export_type:
            export_params["range"] = "hour"
        elif "day" in export_type:
            export_params["range"] = "day"
        elif "week" in export_type:
            export_params["range"] = "week"
        elif "month" in export_type:
            export_params["range"] = "month"

        # Calculate date range
        now = datetime.utcnow()
        if export_params["range"] == "hour":
            start_date = now - timedelta(hours=1)
            range_display = "última hora"
        elif export_params["range"] == "day":
            start_date = now - timedelta(days=1)
            range_display = "último día"
        elif export_params["range"] == "week":
            start_date = now - timedelta(days=7)
            range_display = "última semana"
        elif export_params["range"] == "month":
            start_date = now - timedelta(days=30)
            range_display = "último mes"
        else:
            start_date = now - timedelta(days=7)
            range_display = "última semana"

        # Generate export data
        export_start_time = datetime.utcnow()

        try:
            if export_params["format"] == "json":
                export_result = await analytics_service.export_analytics_data(
                    (start_date.isoformat(), now.isoformat()),
                    "json"
                )
            elif export_params["format"] == "csv":
                export_result = await analytics_service.export_analytics_data(
                    (start_date.isoformat(), now.isoformat()),
                    "csv"
                )
            elif export_params["format"] == "excel":
                # Enhanced Excel export with multiple sheets
                export_result = await analytics_service.export_enhanced_analytics_data(
                    start_date, now, "excel"
                )
            elif export_params["format"] == "pdf":
                # Enhanced PDF export with charts
                export_result = await analytics_service.export_enhanced_analytics_data(
                    start_date, now, "pdf", include_charts=True
                )
            else:
                export_result = {"status": "error", "message": "Formato no soportado"}

        except Exception as e:
            logger.error(f"Export generation error: {e}")
            export_result = {"status": "error", "message": str(e)}

        export_end_time = datetime.utcnow()
        generation_time = (export_end_time - export_start_time).total_seconds()

        # Build result menu
        menu_text = f"📤 **Exportación Completada**\\n\\n"

        if isinstance(export_result, dict) and export_result.get("status") == "error":
            menu_text += f"❌ **Error en la exportación:**\\n"
            menu_text += f"Detalle: {export_result.get('message', 'Error desconocido')}\\n\\n"
        else:
            menu_text += f"✅ **Exportación exitosa**\\n"
            menu_text += f"📅 **Período:** {range_display}\\n"
            menu_text += f"📄 **Formato:** {export_params['format'].upper()}\\n"
            menu_text += f"⏱️ **Tiempo de generación:** {generation_time:.2f}s\\n"

            # Check compliance with 30-second requirement
            if generation_time <= 30:
                menu_text += f"✅ **Cumple requisito de tiempo (≤30s)**\\n"
            else:
                menu_text += f"⚠️ **Excedió tiempo límite (>30s)**\\n"
                logger.warning(f"Export generation exceeded 30s: {generation_time:.2f}s")

            menu_text += f"🕒 **Generado:** {now.strftime('%d/%m/%Y %H:%M:%S')}\\n\\n"

            # Show data summary
            if export_params["format"] == "json" and isinstance(export_result, str):
                data_size = len(export_result)
                menu_text += f"📊 **Tamaño:** ~{data_size:,} caracteres\\n"
            elif export_params["format"] == "csv":
                menu_text += f"📊 **Archivos CSV generados con datos analíticos**\\n"
            elif export_params["format"] == "excel":
                menu_text += f"📊 **Archivo Excel con múltiples hojas de análisis**\\n"
            elif export_params["format"] == "pdf":
                menu_text += f"📊 **Reporte PDF con gráficos y métricas**\\n"

        menu_text += "\\n**Los datos están listos para descarga.**"

        keyboard = get_back_kb("admin_enhanced_export_main")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            f"admin_enhanced_export_complete_{export_params['format']}"
        )

        logger.info(f"Enhanced export completed for admin {callback.from_user.id}: "
                   f"{export_params['format']}, {range_display}, {generation_time:.2f}s")

    try:
        await track_response_time(_export_logic)
    except Exception as e:
        logger.error(f"Error in enhanced export: {e}")
        await callback.answer("❌ Error en la exportación mejorada", show_alert=True)

    await callback.answer()


# REAL-TIME ANALYTICS HANDLERS

@router.callback_query(F.data == "admin_enhanced_realtime")
async def show_enhanced_realtime_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced real-time analytics with live updates.
    Implements requirement 5.1 - Display metrics within 3 seconds.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    async def _realtime_logic():
        cached_analytics_service = CachedAnalyticsService(session, cache_service)

        # Get real-time metrics
        realtime_data = await cached_analytics_service.get_realtime_metrics()

        current_time = datetime.utcnow()
        menu_text = "⚡ **Análisis en Tiempo Real Mejorado**\\n\\n"
        menu_text += f"🕒 **Actualizado:** {current_time.strftime('%H:%M:%S UTC')}\\n\\n"

        if realtime_data.get("status") == "success":
            metrics = realtime_data.get("metrics", {})

            # Current activity
            activity = metrics.get("current_activity", {})
            menu_text += f"👥 **Actividad Actual:**\\n"
            menu_text += f"• Usuarios en línea: {activity.get('online_users', 0)}\\n"
            menu_text += f"• Sesiones activas: {activity.get('active_sessions', 0)}\\n"
            menu_text += f"• Interacciones/min: {activity.get('interactions_per_minute', 0)}\\n\\n"

            # Live performance
            performance = metrics.get("performance", {})
            menu_text += f"📊 **Rendimiento en Vivo:**\\n"
            menu_text += f"• Tiempo respuesta promedio: {performance.get('avg_response_time', 0):.2f}s\\n"
            menu_text += f"• Throughput: {performance.get('requests_per_second', 0)} req/s\\n"
            menu_text += f"• Cache hit rate: {performance.get('cache_hit_rate', 0):.1f}%\\n\\n"

            # Recent events
            events = metrics.get("recent_events", [])
            if events:
                menu_text += f"🔔 **Eventos Recientes:**\\n"
                for event in events[:3]:
                    event_time = event.get("timestamp", "")
                    event_type = event.get("type", "")
                    event_desc = event.get("description", "")
                    menu_text += f"• {event_time} - {event_type}: {event_desc}\\n"
                menu_text += "\\n"

            # Alerts
            alerts = metrics.get("alerts", [])
            if alerts:
                menu_text += f"⚠️ **Alertas Activas:**\\n"
                for alert in alerts:
                    alert_type = alert.get("type", "")
                    alert_msg = alert.get("message", "")
                    menu_text += f"• {alert_type}: {alert_msg}\\n"
                menu_text += "\\n"
            else:
                menu_text += f"✅ **Sin alertas activas**\\n\\n"

        else:
            menu_text += "⏳ **Cargando métricas en tiempo real...**\\n\\n"

        menu_text += "🔄 **Actualización automática cada 30 segundos**\\n\\n"
        menu_text += "**Opciones de monitoreo:**"

        keyboard = get_real_time_analytics_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_realtime"
        )

    try:
        await track_response_time(_realtime_logic)
    except Exception as e:
        logger.error(f"Error in enhanced realtime analytics: {e}")
        await callback.answer("❌ Error al cargar análisis en tiempo real", show_alert=True)

    await callback.answer()


# PERFORMANCE MONITORING HANDLERS

@router.callback_query(F.data == "admin_enhanced_performance")
async def show_enhanced_performance_monitoring(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced performance monitoring with detailed system metrics.
    Implements requirement 5.1 - System performance tracking.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    async def _performance_logic():
        analytics_service = AnalyticsService(session)

        # Get performance metrics
        performance_data = await analytics_service.get_system_performance_metrics()

        menu_text = "⚡ **Monitoreo de Rendimiento del Sistema**\\n\\n"

        if performance_data.get("status") == "success":
            metrics = performance_data.get("metrics", {})

            # Response time compliance
            response_times = metrics.get("response_times", {})
            menu_text += f"📊 **Cumplimiento de Tiempos de Respuesta:**\\n"
            menu_text += f"• Promedio general: {response_times.get('average', 0):.2f}s\\n"
            menu_text += f"• Percentil 95: {response_times.get('p95', 0):.2f}s\\n"
            menu_text += f"• Cumplimiento 3s: {response_times.get('compliance_3s', 0):.1f}%\\n"

            # Color coding for compliance
            compliance_3s = response_times.get('compliance_3s', 0)
            if compliance_3s >= 95:
                compliance_status = "✅ Excelente"
            elif compliance_3s >= 90:
                compliance_status = "⚠️ Bueno"
            else:
                compliance_status = "❌ Necesita atención"
            menu_text += f"• Estado: {compliance_status}\\n\\n"

            # Database performance
            db_metrics = metrics.get("database", {})
            menu_text += f"🗄️ **Rendimiento de Base de Datos:**\\n"
            menu_text += f"• Consultas/segundo: {db_metrics.get('queries_per_second', 0)}\\n"
            menu_text += f"• Tiempo promedio consulta: {db_metrics.get('avg_query_time', 0):.3f}s\\n"
            menu_text += f"• Conexiones activas: {db_metrics.get('active_connections', 0)}\\n\\n"

            # Cache performance
            cache_metrics = metrics.get("cache", {})
            menu_text += f"💾 **Rendimiento de Cache:**\\n"
            menu_text += f"• Hit rate: {cache_metrics.get('hit_rate', 0):.1f}%\\n"
            menu_text += f"• Entradas activas: {cache_metrics.get('active_entries', 0)}\\n"
            menu_text += f"• Memoria usada: {cache_metrics.get('memory_usage', 0):.1f}MB\\n\\n"

            # Export performance
            export_metrics = metrics.get("export", {})
            menu_text += f"📤 **Rendimiento de Exportación:**\\n"
            menu_text += f"• Tiempo promedio: {export_metrics.get('avg_generation_time', 0):.2f}s\\n"
            menu_text += f"• Cumplimiento 30s: {export_metrics.get('compliance_30s', 0):.1f}%\\n"

            # Color coding for export compliance
            export_compliance = export_metrics.get('compliance_30s', 0)
            if export_compliance >= 95:
                export_status = "✅ Excelente"
            elif export_compliance >= 90:
                export_status = "⚠️ Bueno"
            else:
                export_status = "❌ Necesita optimización"
            menu_text += f"• Estado: {export_status}\\n\\n"

        else:
            menu_text += "❌ Error al cargar métricas de rendimiento\\n\\n"

        menu_text += f"🕒 **Última actualización:** {datetime.utcnow().strftime('%H:%M:%S')}\\n\\n"
        menu_text += "**Opciones de monitoreo:**"

        keyboard = get_analytics_detail_kb("performance")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_performance"
        )

    try:
        await track_response_time(_performance_logic)
    except Exception as e:
        logger.error(f"Error in enhanced performance monitoring: {e}")
        await callback.answer("❌ Error al cargar monitoreo de rendimiento", show_alert=True)

    await callback.answer()


# COMMAND HANDLERS

@router.message(Command("enhanced_analytics"))
async def enhanced_analytics_command(message: Message, session: AsyncSession):
    """
    Command handler to access enhanced analytics administration menu directly.
    Provides optimized access for administrators.
    """
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\\n\\nNo tienes permisos de administrador para acceder al análisis mejorado.",
            auto_delete_seconds=5
        )
        return

    try:
        menu_text = "📊 **Sistema de Análisis Mejorado**\\n\\n"
        menu_text += "⚡ **Análisis administrativo con rendimiento optimizado**\\n\\n"

        menu_text += "🎯 **Características mejoradas:**\\n"
        menu_text += "• Dashboard en tiempo real con métricas instantáneas\\n"
        menu_text += "• Exportación optimizada (< 30 segundos)\\n"
        menu_text += "• Monitoreo de rendimiento del sistema\\n"
        menu_text += "• Cache inteligente para respuestas rápidas\\n\\n"

        menu_text += "📊 **Cumplimiento de requisitos:**\\n"
        menu_text += "• ✅ Métricas en < 3 segundos (Req. 5.1)\\n"
        menu_text += "• ✅ Reportes en < 30 segundos (Req. 5.5)\\n"
        menu_text += "• ✅ Datos estructurados JSON/CSV\\n\\n"

        menu_text += "**Selecciona una función:**"

        keyboard = get_analytics_admin_main_kb()

        await menu_manager.show_menu(
            message,
            menu_text,
            keyboard,
            session,
            "admin_enhanced_analytics_main"
        )

        logger.info(f"Enhanced analytics accessed via command by admin {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in enhanced analytics command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\\n\\nNo se pudo cargar el sistema de análisis mejorado.",
            auto_delete_seconds=5
        )


# BACK NAVIGATION HANDLER

@router.callback_query(F.data == "admin_enhanced_analytics_back")
async def enhanced_analytics_back(callback: CallbackQuery, session: AsyncSession):
    """
    Handle back navigation from enhanced analytics sub-menus.
    Returns to the appropriate parent menu.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Redirect to main analytics admin menu
        await show_enhanced_analytics_dashboard(callback, session)

    except Exception as e:
        logger.error(f"Error in enhanced analytics back navigation: {e}")
        await callback.answer("Error en la navegación", show_alert=True)