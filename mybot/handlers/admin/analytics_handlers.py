"""
Analytics admin handlers router and menu implementation.
Provides comprehensive analytics dashboard for administrators.
Implements requirements 4.1 (Analytics and User Journey Tracking) and 4.3 (Character Voice Analytics).
"""
import logging
from datetime import datetime, timedelta
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

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_analytics_main")
async def show_analytics_admin_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display the main analytics administration menu with navigation options.

    This handler serves as the entry point for all analytics features,
    providing access to user journey tracking, narrative analysis, and
    character voice analytics as specified in requirements 4.1 and 4.3.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize analytics service
        analytics_service = AnalyticsService(session)

        # Get quick dashboard overview
        dashboard_result = await analytics_service.get_comprehensive_dashboard_data()

        # Build the analytics admin menu text
        menu_text = "📊 **Panel de Análisis Narrativo**\n\n"
        menu_text += "Analiza el comportamiento de usuarios, efectividad narrativa y progresión emocional.\n\n"

        if dashboard_result.get("status") == "success":
            summary = dashboard_result.get("summary", {})
            data_availability = summary.get("data_availability", {})

            menu_text += "📈 **Estado de Datos:**\n"
            menu_text += f"• Segmentos de usuarios: {'✅' if data_availability.get('user_segments') else '❌'}\n"
            menu_text += f"• Patrones de decisiones: {'✅' if data_availability.get('choice_patterns') else '❌'}\n"
            menu_text += f"• Análisis de personajes: {'✅' if data_availability.get('character_voice') else '❌'}\n"
            menu_text += f"• Detección de problemas: {'✅' if data_availability.get('bottlenecks') else '❌'}\n\n"

            last_updated = summary.get("last_updated")
            if last_updated:
                try:
                    update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    menu_text += f"🕒 **Última actualización:** {update_time.strftime('%d/%m/%Y %H:%M')}\n\n"
                except:
                    pass
        else:
            menu_text += "📊 **Datos:** Preparando análisis...\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the analytics admin main keyboard
        keyboard = get_analytics_admin_main_kb()

        # Update the menu using existing menu manager pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_main"
        )

        logger.info(f"Analytics admin menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing analytics admin menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el menú de análisis", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_analytics_back")
async def analytics_admin_back(callback: CallbackQuery, session: AsyncSession):
    """
    Handle back navigation from analytics admin sub-menus.
    Returns to the main analytics admin menu.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Redirect to main analytics admin menu
        await show_analytics_admin_menu(callback, session)

    except Exception as e:
        logger.error(f"Error in analytics admin back navigation: {e}")
        await callback.answer("Error en la navegación", show_alert=True)


@router.message(Command("analytics_admin"))
async def analytics_admin_command(message: Message, session: AsyncSession):
    """
    Command handler to access analytics administration menu directly.
    Provides alternative access method for administrators.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador para acceder al análisis narrativo.",
            auto_delete_seconds=5
        )
        return

    try:
        # Initialize analytics service
        analytics_service = AnalyticsService(session)

        # Get quick dashboard overview
        dashboard_result = await analytics_service.get_comprehensive_dashboard_data()

        # Build the analytics admin menu text
        menu_text = "📊 **Panel de Análisis Narrativo**\n\n"
        menu_text += "Analiza el comportamiento de usuarios, efectividad narrativa y progresión emocional.\n\n"

        if dashboard_result.get("status") == "success":
            summary = dashboard_result.get("summary", {})
            data_availability = summary.get("data_availability", {})

            menu_text += "📈 **Estado de Datos:**\n"
            available_features = sum(1 for available in data_availability.values() if available)
            total_features = len(data_availability)
            menu_text += f"• Funciones disponibles: {available_features}/{total_features}\n\n"
        else:
            menu_text += "📊 **Datos:** Preparando análisis inicial...\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the analytics admin main keyboard
        keyboard = get_analytics_admin_main_kb()

        # Show the menu using existing menu manager pattern
        await menu_manager.show_menu(
            message,
            menu_text,
            keyboard,
            session,
            "admin_analytics_main"
        )

        logger.info(f"Analytics admin menu accessed via command by admin {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in analytics admin command for user {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de análisis narrativo.",
            auto_delete_seconds=5
        )


# DASHBOARD AND OVERVIEW HANDLERS

@router.callback_query(F.data == "admin_analytics_dashboard")
async def show_analytics_dashboard(callback: CallbackQuery, session: AsyncSession):
    """
    Display comprehensive analytics dashboard with all key metrics.
    Implements requirement 4.1 - Comprehensive Analytics.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        analytics_service = AnalyticsService(session)
        dashboard_data = await analytics_service.get_comprehensive_dashboard_data()

        menu_text = "📊 **Dashboard de Análisis Completo**\n\n"

        if dashboard_data.get("status") == "success":
            # User segments summary
            user_segments = dashboard_data.get("user_segments", {})
            if user_segments.get("status") == "success":
                segment_counts = user_segments.get("segment_counts", {})
                menu_text += "👥 **Segmentos de Usuarios:**\n"
                menu_text += f"• Whales: {segment_counts.get('whales', 0)}\n"
                menu_text += f"• Exploradores: {segment_counts.get('explorers', 0)}\n"
                menu_text += f"• Altamente activos: {segment_counts.get('highly_engaged', 0)}\n"
                menu_text += f"• Estancados: {segment_counts.get('stalled', 0)}\n"
                menu_text += f"• Nuevos: {segment_counts.get('new_users', 0)}\n\n"

            # Choice patterns summary
            choice_patterns = dashboard_data.get("choice_patterns", {})
            if choice_patterns.get("status") == "success":
                summary = choice_patterns.get("summary", {})
                menu_text += "🎯 **Patrones de Decisiones:**\n"
                menu_text += f"• Total decisiones: {summary.get('total_choices_made', 0)}\n"
                menu_text += f"• Fragmentos analizados: {summary.get('fragments_analyzed', 0)}\n"
                menu_text += f"• Opciones únicas: {summary.get('unique_choices', 0)}\n\n"

            # Bottlenecks summary
            bottlenecks = dashboard_data.get("bottlenecks", {})
            if bottlenecks.get("status") == "success":
                bottleneck_summary = bottlenecks.get("summary", {})
                menu_text += "⚠️ **Cuellos de Botella:**\n"
                menu_text += f"• Críticos: {bottleneck_summary.get('critical_bottlenecks', 0)}\n"
                menu_text += f"• Advertencias: {bottleneck_summary.get('warning_bottlenecks', 0)}\n"
                menu_text += f"• Usuarios estancados: {bottleneck_summary.get('stalled_users_count', 0)}\n\n"

            # Character voice summary
            character_voice = dashboard_data.get("character_voice", {})
            if character_voice.get("status") == "success":
                insights = character_voice.get("insights", {})
                menu_text += "🎭 **Análisis de Personajes:**\n"
                menu_text += f"• Interacciones totales: {insights.get('total_tracked_interactions', 0)}\n"
                menu_text += f"• Emociones rastreadas: {insights.get('emotions_tracked', 0)}\n"

                most_effective = insights.get("most_effective_character")
                if most_effective:
                    menu_text += f"• Más efectivo: {most_effective.get('name', 'N/A')}\n\n"
                else:
                    menu_text += "\n"
        else:
            menu_text += "❌ Error al cargar datos del dashboard.\n\n"

        keyboard = get_analytics_detail_kb("dashboard")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_dashboard"
        )

    except Exception as e:
        logger.error(f"Error showing analytics dashboard: {e}")
        await callback.answer("Error al cargar el dashboard", show_alert=True)

    await callback.answer()


# USER SEGMENTS HANDLERS

@router.callback_query(F.data == "admin_analytics_segments")
async def show_user_segments(callback: CallbackQuery, session: AsyncSession):
    """
    Display user segmentation analysis menu.
    Implements requirement 4.1 - User Journey Tracking.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        analytics_service = AnalyticsService(session)
        segments_data = await analytics_service.generate_user_segment_analysis()

        menu_text = "👥 **Análisis de Segmentos de Usuarios**\n\n"

        if segments_data.get("status") == "success":
            segment_counts = segments_data.get("segment_counts", {})
            total_users = sum(segment_counts.values())

            menu_text += f"📊 **Total de usuarios analizados:** {total_users}\n\n"

            for segment, count in segment_counts.items():
                percentage = round((count / total_users * 100), 1) if total_users > 0 else 0
                segment_emoji = {
                    "whales": "🐋",
                    "explorers": "🗺️",
                    "highly_engaged": "🔥",
                    "stalled": "😴",
                    "new_users": "👶",
                    "inactive": "💤"
                }

                emoji = segment_emoji.get(segment, "👤")
                segment_name = segment.replace("_", " ").title()
                menu_text += f"{emoji} **{segment_name}:** {count} ({percentage}%)\n"

            menu_text += f"\n🕒 **Generado:** {segments_data.get('generated_at', 'N/A')}\n\n"
        else:
            menu_text += "❌ No hay datos de segmentación disponibles.\n\n"

        menu_text += "**Selecciona un segmento para análisis detallado:**"

        keyboard = get_user_segments_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_segments"
        )

    except Exception as e:
        logger.error(f"Error showing user segments: {e}")
        await callback.answer("Error al cargar segmentos", show_alert=True)

    await callback.answer()


# FRAGMENT ANALYTICS HANDLERS

@router.callback_query(F.data == "admin_analytics_fragments")
async def show_fragment_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display fragment analytics and engagement metrics.
    Implements requirement 4.1 - Narrative branch popularity tracking.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "📖 **Análisis de Fragmentos Narrativos**\n\n"
        menu_text += "Analiza el rendimiento individual de cada fragmento de la narrativa.\n\n"

        menu_text += "📊 **Métricas disponibles:**\n"
        menu_text += "• Engagement y tiempo de permanencia\n"
        menu_text += "• Puntos de entrada y salida\n"
        menu_text += "• Popularidad y problemas detectados\n"
        menu_text += "• Comparativas entre fragmentos\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_fragment_analytics_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_fragments"
        )

    except Exception as e:
        logger.error(f"Error showing fragment analytics: {e}")
        await callback.answer("Error al cargar análisis de fragmentos", show_alert=True)

    await callback.answer()


# CHOICE PATTERNS HANDLERS

@router.callback_query(F.data == "admin_analytics_choices")
async def show_choice_patterns(callback: CallbackQuery, session: AsyncSession):
    """
    Display choice distribution patterns and decision analysis.
    Implements requirement 4.1 - Choice patterns tracking.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        analytics_service = AnalyticsService(session)
        choice_data = await analytics_service.analyze_choice_distribution_patterns()

        menu_text = "🎯 **Análisis de Patrones de Decisiones**\n\n"

        if choice_data.get("status") == "success":
            summary = choice_data.get("summary", {})
            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Total decisiones tomadas: {summary.get('total_choices_made', 0)}\n"
            menu_text += f"• Fragmentos analizados: {summary.get('fragments_analyzed', 0)}\n"
            menu_text += f"• Opciones únicas: {summary.get('unique_choices', 0)}\n\n"

            # Show top choices
            most_popular = choice_data.get("most_popular_choices", [])
            if most_popular:
                menu_text += "⭐ **Decisiones más populares:**\n"
                for i, (choice_id, count) in enumerate(most_popular[:3], 1):
                    menu_text += f"{i}. Opción {choice_id}: {count} veces\n"
                menu_text += "\n"

            menu_text += f"🕒 **Generado:** {choice_data.get('generated_at', 'N/A')}\n\n"
        else:
            menu_text += "❌ No hay datos de patrones de decisiones disponibles.\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_choice_patterns_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_choices"
        )

    except Exception as e:
        logger.error(f"Error showing choice patterns: {e}")
        await callback.answer("Error al cargar patrones de decisiones", show_alert=True)

    await callback.answer()


# BOTTLENECKS HANDLERS

@router.callback_query(F.data == "admin_analytics_bottlenecks")
async def show_bottlenecks_analysis(callback: CallbackQuery, session: AsyncSession):
    """
    Display narrative bottlenecks and problem detection.
    Implements requirement 4.1 - Drop-off points and progression issues.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        analytics_service = AnalyticsService(session)
        bottlenecks_data = await analytics_service.identify_narrative_bottlenecks()

        menu_text = "⚠️ **Análisis de Cuellos de Botella**\n\n"

        if bottlenecks_data.get("status") == "success":
            summary = bottlenecks_data.get("summary", {})
            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Fragmentos analizados: {summary.get('total_fragments_analyzed', 0)}\n"
            menu_text += f"• Problemas críticos: {summary.get('critical_bottlenecks', 0)}\n"
            menu_text += f"• Advertencias: {summary.get('warning_bottlenecks', 0)}\n"
            menu_text += f"• Usuarios estancados: {summary.get('stalled_users_count', 0)}\n\n"

            # Show critical bottlenecks
            bottlenecks = bottlenecks_data.get("bottlenecks", [])
            critical_bottlenecks = [b for b in bottlenecks if b.get("severity") == "critical"]

            if critical_bottlenecks:
                menu_text += "🔴 **Problemas críticos detectados:**\n"
                for bottleneck in critical_bottlenecks[:3]:
                    fragment_key = bottleneck.get("fragment_key", "N/A")
                    drop_off_rate = bottleneck.get("drop_off_rate", 0)
                    menu_text += f"• {fragment_key}: {drop_off_rate}% abandono\n"
                menu_text += "\n"

            # Show recommendations
            recommendations = bottlenecks_data.get("recommendations", [])
            if recommendations:
                menu_text += "💡 **Recomendaciones:**\n"
                for i, rec in enumerate(recommendations[:2], 1):
                    menu_text += f"{i}. {rec}\n"
                menu_text += "\n"

            menu_text += f"🕒 **Generado:** {bottlenecks_data.get('generated_at', 'N/A')}\n\n"
        else:
            menu_text += "❌ No hay datos de cuellos de botella disponibles.\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_bottlenecks_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_bottlenecks"
        )

    except Exception as e:
        logger.error(f"Error showing bottlenecks analysis: {e}")
        await callback.answer("Error al cargar análisis de cuellos de botella", show_alert=True)

    await callback.answer()


# CHARACTER VOICE ANALYTICS HANDLERS

@router.callback_query(F.data == "admin_analytics_characters")
async def show_character_voice_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display character voice and emotional progression analytics.
    Implements requirement 4.3 - Character Voice and Emotional Intelligence Analytics.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        analytics_service = AnalyticsService(session)
        character_data = await analytics_service.get_character_voice_analytics()

        menu_text = "🎭 **Análisis de Voz de Personajes**\n\n"

        if character_data.get("status") == "success":
            insights = character_data.get("insights", {})

            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Interacciones totales: {insights.get('total_tracked_interactions', 0)}\n"
            menu_text += f"• Emociones rastreadas: {insights.get('emotions_tracked', 0)}\n\n"

            # Most effective character
            most_effective = insights.get("most_effective_character")
            if most_effective:
                menu_text += f"🏆 **Personaje más efectivo:**\n"
                menu_text += f"• {most_effective.get('name', 'N/A')}\n"
                menu_text += f"• Score: {most_effective.get('engagement_score', 0)}\n\n"

            # Dominant emotion
            dominant_emotion = insights.get("dominant_emotion")
            if dominant_emotion:
                menu_text += f"💭 **Emoción dominante:**\n"
                menu_text += f"• {dominant_emotion.get('emotion', 'N/A')}\n"
                menu_text += f"• Ocurrencias: {dominant_emotion.get('occurrences', 0)}\n"
                menu_text += f"• Intensidad promedio: {dominant_emotion.get('average_intensity', 0)}\n\n"

            # Character effectiveness
            character_analytics = character_data.get("character_analytics", {})
            if character_analytics:
                menu_text += "🎯 **Efectividad por personaje:**\n"
                for char_name, stats in list(character_analytics.items())[:3]:
                    interactions = stats.get("total_interactions", 0)
                    score = stats.get("engagement_score", 0)
                    menu_text += f"• {char_name}: {interactions} interacciones ({score:.1f}%)\n"
                menu_text += "\n"

            menu_text += f"🕒 **Generado:** {character_data.get('generated_at', 'N/A')}\n\n"
        else:
            menu_text += "❌ No hay datos de análisis de personajes disponibles.\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_character_voice_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_characters"
        )

    except Exception as e:
        logger.error(f"Error showing character voice analytics: {e}")
        await callback.answer("Error al cargar análisis de personajes", show_alert=True)

    await callback.answer()


# EXPORT HANDLERS

@router.callback_query(F.data.startswith("admin_analytics_export"))
async def handle_analytics_export(callback: CallbackQuery, session: AsyncSession):
    """
    Handle analytics data export requests.
    Implements requirement 4.1 - Exportable analytics data.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        export_type = callback.data.split("_")[-1]  # json, csv, etc.

        if export_type in ["json", "csv"]:
            # Show export options
            menu_text = f"📤 **Exportar Datos - Formato {export_type.upper()}**\n\n"
            menu_text += "Selecciona el rango de fechas y tipo de datos a exportar.\n\n"
            menu_text += "**Opciones disponibles:**\n"
            menu_text += "• Datos de la última semana\n"
            menu_text += "• Datos del último mes\n"
            menu_text += "• Solo datos de usuarios\n"
            menu_text += "• Solo datos de fragmentos\n\n"
            menu_text += "**Selecciona una opción:**"

            keyboard = get_export_options_kb()

            await menu_manager.update_menu(
                callback,
                menu_text,
                keyboard,
                session,
                f"admin_analytics_export_{export_type}"
            )
        else:
            await callback.answer("Formato de exportación no soportado", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling analytics export: {e}")
        await callback.answer("Error en la exportación", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("admin_analytics_export_"))
async def process_analytics_export(callback: CallbackQuery, session: AsyncSession):
    """
    Process specific export requests with date ranges.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        export_params = callback.data.replace("admin_analytics_export_", "")

        # Determine date range
        now = datetime.utcnow()
        if "week" in export_params:
            start_date = now - timedelta(days=7)
            range_name = "última semana"
        elif "month" in export_params:
            start_date = now - timedelta(days=30)
            range_name = "último mes"
        else:
            start_date = now - timedelta(days=7)  # Default
            range_name = "última semana"

        # Determine format
        format_type = "json" if "json" in export_params else "csv"

        analytics_service = AnalyticsService(session)
        export_result = await analytics_service.export_analytics_data(
            (start_date.isoformat(), now.isoformat()),
            format_type
        )

        if isinstance(export_result, dict) and export_result.get("status") == "error":
            await callback.answer(f"Error en exportación: {export_result.get('message')}", show_alert=True)
        else:
            # For demo purposes, show confirmation
            menu_text = f"✅ **Exportación Completada**\n\n"
            menu_text += f"📅 **Período:** {range_name}\n"
            menu_text += f"📄 **Formato:** {format_type.upper()}\n"
            menu_text += f"🕒 **Generado:** {now.strftime('%d/%m/%Y %H:%M')}\n\n"

            if format_type == "json":
                data_size = len(str(export_result)) if export_result else 0
                menu_text += f"📊 **Tamaño:** ~{data_size:,} caracteres\n\n"
            else:
                menu_text += "📊 **Archivos:** fragment_analytics.csv, user_journey_analytics.csv\n\n"

            menu_text += "Los datos han sido preparados para exportación."

            keyboard = get_back_kb("admin_analytics_main")

            await menu_manager.update_menu(
                callback,
                menu_text,
                keyboard,
                session,
                "admin_analytics_export_complete"
            )

            logger.info(f"Analytics export completed for admin {callback.from_user.id}: {format_type}, {range_name}")

    except Exception as e:
        logger.error(f"Error processing analytics export: {e}")
        await callback.answer("Error al procesar la exportación", show_alert=True)

    await callback.answer()


# NEW ENHANCED ANALYTICS HANDLERS

@router.callback_query(F.data.startswith("admin_analytics_char_"))
async def handle_character_specific_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Handle character-specific analytics requests.
    Implements requirement 4.3 - Character Voice Analytics.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Parse character name from callback data
        callback_parts = callback.data.split("_")
        if len(callback_parts) >= 4:
            character_name = callback_parts[3]  # admin_analytics_char_{character_name}

            if character_name in ["diana", "lucien", "others"]:
                menu_text = f"🎭 **Análisis de {character_name.title()}**\n\n"
                menu_text += f"Análisis detallado del personaje {character_name.title()} en la narrativa.\n\n"

                # Get character-specific data
                analytics_service = AnalyticsService(session)
                character_data = await analytics_service.get_character_voice_analytics()

                if character_data.get("status") == "success":
                    character_analytics = character_data.get("character_analytics", {})

                    # Find character data
                    char_stats = None
                    for char_key, stats in character_analytics.items():
                        if character_name.lower() in char_key.lower():
                            char_stats = stats
                            break

                    if char_stats:
                        menu_text += f"📊 **Métricas del personaje:**\n"
                        menu_text += f"• Interacciones totales: {char_stats.get('total_interactions', 0)}\n"
                        menu_text += f"• Usuarios únicos: {char_stats.get('unique_users', 0)}\n"
                        menu_text += f"• Promedio por usuario: {char_stats.get('average_interactions_per_user', 0)}\n"
                        menu_text += f"• Score de engagement: {char_stats.get('engagement_score', 0):.1f}%\n\n"
                    else:
                        menu_text += "📊 **Sin datos disponibles para este personaje.**\n\n"
                else:
                    menu_text += "❌ Error al cargar datos del personaje.\n\n"

                menu_text += "**Selecciona el tipo de análisis:**"

                keyboard = get_character_specific_kb(character_name)

                await menu_manager.update_menu(
                    callback,
                    menu_text,
                    keyboard,
                    session,
                    f"admin_analytics_char_{character_name}"
                )
            else:
                await callback.answer("Personaje no reconocido", show_alert=True)
        else:
            await callback.answer("Formato de callback inválido", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling character specific analytics: {e}")
        await callback.answer("Error al cargar análisis del personaje", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_analytics_journey")
async def show_user_journey_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display enhanced user journey analytics.
    Implements requirement 4.1 - Advanced User Journey Tracking.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "🗺️ **Análisis de Recorridos de Usuario**\n\n"
        menu_text += "Análisis detallado de las rutas que toman los usuarios a través de la narrativa.\n\n"

        # Get basic journey statistics
        analytics_service = AnalyticsService(session)
        dashboard_data = await analytics_service.get_comprehensive_dashboard_data()

        if dashboard_data.get("status") == "success":
            user_segments = dashboard_data.get("user_segments", {})
            if user_segments.get("status") == "success":
                segment_counts = user_segments.get("segment_counts", {})
                total_users = sum(segment_counts.values())

                menu_text += f"📊 **Estadísticas generales:**\n"
                menu_text += f"• Total usuarios analizados: {total_users}\n"
                menu_text += f"• Exploradores activos: {segment_counts.get('explorers', 0)}\n"
                menu_text += f"• Usuarios altamente comprometidos: {segment_counts.get('highly_engaged', 0)}\n"
                menu_text += f"• Usuarios estancados: {segment_counts.get('stalled', 0)}\n\n"
        else:
            menu_text += "📊 **Preparando análisis de recorridos...**\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_user_journey_analytics_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_journey"
        )

    except Exception as e:
        logger.error(f"Error showing user journey analytics: {e}")
        await callback.answer("Error al cargar análisis de recorridos", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_analytics_reports")
async def show_report_generation(callback: CallbackQuery, session: AsyncSession):
    """
    Display report generation options.
    Implements enhanced reporting capabilities.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "📋 **Generación de Reportes Analíticos**\n\n"
        menu_text += "Crea reportes personalizados con datos analíticos detallados.\n\n"

        menu_text += "📊 **Tipos de reportes disponibles:**\n"
        menu_text += "• Reportes ejecutivos - Resúmenes de alto nivel\n"
        menu_text += "• Reportes detallados - Análisis completo\n"
        menu_text += "• Reportes de KPIs - Métricas clave\n"
        menu_text += "• Reportes por período - Diario, semanal, mensual\n"
        menu_text += "• Reportes personalizados - Configuración avanzada\n\n"

        menu_text += "**Selecciona el tipo de reporte:**"

        keyboard = get_report_generation_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_reports"
        )

    except Exception as e:
        logger.error(f"Error showing report generation: {e}")
        await callback.answer("Error al cargar generación de reportes", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_analytics_insights")
async def show_analytics_insights(callback: CallbackQuery, session: AsyncSession):
    """
    Display AI-powered analytics insights.
    Implements advanced analytics with AI recommendations.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "💡 **Insights y Recomendaciones IA**\n\n"
        menu_text += "Análisis automatizado con recomendaciones inteligentes para optimizar la narrativa.\n\n"

        # Get insights from analytics data
        analytics_service = AnalyticsService(session)
        dashboard_data = await analytics_service.get_comprehensive_dashboard_data()

        insights_generated = 0
        if dashboard_data.get("status") == "success":
            # Count available insights
            bottlenecks = dashboard_data.get("bottlenecks", {})
            if bottlenecks.get("status") == "success":
                recommendations = bottlenecks.get("recommendations", [])
                insights_generated += len(recommendations)

            character_data = dashboard_data.get("character_voice", {})
            if character_data.get("status") == "success":
                insights = character_data.get("insights", {})
                if insights:
                    insights_generated += 1

        menu_text += f"🤖 **Estado de insights:**\n"
        menu_text += f"• Insights generados: {insights_generated}\n"
        menu_text += f"• Análisis IA disponible: {'✅' if insights_generated > 0 else '⏳'}\n"
        menu_text += f"• Recomendaciones activas: {insights_generated}\n\n"

        menu_text += "**Selecciona el tipo de análisis:**"

        keyboard = get_analytics_insights_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_insights"
        )

    except Exception as e:
        logger.error(f"Error showing analytics insights: {e}")
        await callback.answer("Error al cargar insights", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_analytics_realtime")
async def show_realtime_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display real-time analytics monitoring.
    Implements real-time analytics dashboard.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "⚡ **Análisis en Tiempo Real**\n\n"
        menu_text += "Monitoreo en vivo de la actividad narrativa y métricas en tiempo real.\n\n"

        # Get real-time metrics (simulated for now)
        current_time = datetime.utcnow()
        menu_text += f"🕒 **Estado actual:** {current_time.strftime('%H:%M:%S UTC')}\n"
        menu_text += f"👥 **Usuarios activos:** Detectando...\n"
        menu_text += f"📊 **Métricas en vivo:** Actualizando...\n"
        menu_text += f"🔔 **Alertas activas:** 0\n\n"

        menu_text += "**Funciones de monitoreo:**\n"
        menu_text += "• Dashboard en vivo con métricas actualizadas\n"
        menu_text += "• Monitoreo de usuarios activos\n"
        menu_text += "• Detección de picos de actividad\n"
        menu_text += "• Alertas automáticas de problemas\n\n"

        menu_text += "**Selecciona una opción de monitoreo:**"

        keyboard = get_real_time_analytics_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_analytics_realtime"
        )

    except Exception as e:
        logger.error(f"Error showing realtime analytics: {e}")
        await callback.answer("Error al cargar análisis en tiempo real", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("admin_analytics_export_"))
async def handle_enhanced_export(callback: CallbackQuery, session: AsyncSession):
    """
    Handle enhanced export functionality with multiple format support.
    Implements requirement 4.1 and 4.3 - Enhanced Export Capabilities.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        export_type = callback.data.replace("admin_analytics_export_", "")

        if export_type == "options":
            # Show enhanced export options
            menu_text = "📤 **Opciones de Exportación Avanzadas**\n\n"
            menu_text += "Exporta datos analíticos en múltiples formatos con configuración personalizada.\n\n"

            menu_text += "📊 **Formatos disponibles:**\n"
            menu_text += "• JSON - Datos estructurados completos\n"
            menu_text += "• CSV - Formato tabular para análisis\n"
            menu_text += "• Excel - Hojas de cálculo avanzadas\n"
            menu_text += "• PDF - Reportes visuales\n\n"

            menu_text += "📅 **Rangos de fecha:**\n"
            menu_text += "• Última semana, mes o trimestre\n"
            menu_text += "• Configuración personalizada\n\n"

            menu_text += "**Selecciona una opción de exportación:**"

            keyboard = get_export_options_kb()

            await menu_manager.update_menu(
                callback,
                menu_text,
                keyboard,
                session,
                "admin_analytics_export_options"
            )

        elif export_type == "configure":
            # Show advanced export configuration
            menu_text = "⚙️ **Configuración Avanzada de Exportación**\n\n"
            menu_text += "Personaliza tu exportación con opciones avanzadas.\n\n"

            menu_text += "⚙️ **Opciones de configuración:**\n"
            menu_text += "• Selección de campos específicos\n"
            menu_text += "• Filtros por usuario, fecha o tags\n"
            menu_text += "• Agregaciones y cálculos personalizados\n"
            menu_text += "• Formato visual y presentación\n"
            menu_text += "• Configuración de entrega (email, descarga)\n\n"

            menu_text += "**Configura tu exportación:**"

            keyboard = get_advanced_export_kb()

            await menu_manager.update_menu(
                callback,
                menu_text,
                keyboard,
                session,
                "admin_analytics_export_configure"
            )

        elif export_type == "characters":
            # Character-specific export
            analytics_service = AnalyticsService(session)

            # Show loading message
            await callback.answer("Preparando exportación de personajes...", show_alert=False)

            # Export character data
            export_result = await analytics_service.export_character_analytics_data(
                character_name=None,  # All characters
                format="json"
            )

            menu_text = "🎭 **Exportación de Datos de Personajes**\n\n"

            if isinstance(export_result, str):
                # Successfully exported
                data_size = len(export_result)
                menu_text += f"✅ **Exportación completada**\n"
                menu_text += f"📊 **Formato:** JSON\n"
                menu_text += f"📏 **Tamaño:** ~{data_size:,} caracteres\n"
                menu_text += f"🕒 **Generado:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}\n\n"
                menu_text += "Los datos de análisis de personajes han sido exportados exitosamente."
            else:
                menu_text += f"❌ **Error en la exportación**\n"
                menu_text += f"Detalle: {export_result.get('message', 'Error desconocido')}"

            keyboard = get_back_kb("admin_analytics_export_options")

            await menu_manager.update_menu(
                callback,
                menu_text,
                keyboard,
                session,
                "admin_analytics_export_characters_complete"
            )

        else:
            await callback.answer("Opción de exportación no reconocida", show_alert=True)

    except Exception as e:
        logger.error(f"Error handling enhanced export: {e}")
        await callback.answer("Error en la exportación", show_alert=True)

    await callback.answer()