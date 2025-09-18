"""
Enhanced VIP Handlers for Channel Administration Module

This module implements enhanced VIP subscription management with batch operations,
comprehensive analytics, and HTML-formatted interfaces. Implements requirements
2.1 (Advanced VIP Token Generation) and 2.5 (VIP User Tracking and Analytics).

Leverages existing VIP infrastructure while providing enhanced administrative capabilities.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

# Core imports for existing architecture integration
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from database.models import User, Tariff, Token, VipSubscription

# Import enhanced VIP service
from services.enhanced_vip_service import EnhancedVIPService

# Import HTML formatting
try:
    from utils.html_formatter import HTMLMessageFormatter
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logging.warning("HTMLMessageFormatter not available - falling back to Markdown")

# Import CoordinadorCentral for integration
try:
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    COORDINATOR_AVAILABLE = True
except ImportError:
    COORDINATOR_AVAILABLE = False
    logging.warning("CoordinadorCentral not available")

logger = logging.getLogger(__name__)
router = Router()

# Enhanced VIP Management Functions

async def create_enhanced_vip_menu(
    session: AsyncSession,
    admin_id: int,
    bot: Bot = None
) -> Tuple[str, InlineKeyboardBuilder]:
    """
    Create enhanced VIP management menu with real-time statistics.
    Implements requirement 2.1 - Advanced VIP Subscription Management.

    Args:
        session: Database session
        admin_id: Administrator user ID
        bot: Bot instance

    Returns:
        Tuple of (menu_text, keyboard_builder)
    """
    try:
        # Get VIP service instance
        vip_service = EnhancedVIPService(session, bot)

        # Get comprehensive analytics
        analytics = await vip_service.get_vip_analytics(metrics_type="comprehensive")

        # Get basic subscription stats
        from services import get_admin_statistics
        basic_stats = await get_admin_statistics(session)

        # Create menu data for HTML formatting
        menu_data = {
            "title": "💎 Panel VIP Avanzado",
            "description": "Gestión integral de suscripciones VIP con analytics avanzados y operaciones en lote.",
            "stats": {},
            "sections": [
                {
                    "title": "Gestión de Tokens",
                    "options": [
                        {"icon": "🎫", "text": "Generar Token Individual"},
                        {"icon": "📦", "text": "Generación en Lote (hasta 50)"},
                        {"icon": "🔍", "text": "Validar y Gestionar Tokens"}
                    ]
                },
                {
                    "title": "Analytics y Usuarios",
                    "options": [
                        {"icon": "📊", "text": "Métricas Completas"},
                        {"icon": "👥", "text": "Lista de Usuarios VIP"},
                        {"icon": "📈", "text": "Tendencias y Proyecciones"}
                    ]
                },
                {
                    "title": "Automatización",
                    "options": [
                        {"icon": "🔔", "text": "Recordatorios Automáticos"},
                        {"icon": "🎯", "text": "Gestión de Expiración"},
                        {"icon": "⚙️", "text": "Configuración Avanzada"}
                    ]
                }
            ]
        }

        # Extract stats from analytics
        if analytics.get("status") == "success":
            # Revenue stats
            revenue_analytics = analytics.get("revenue_analytics", {})
            if revenue_analytics.get("status") == "success":
                revenue_metrics = revenue_analytics.get("revenue_metrics", {})
                menu_data["stats"]["ingresos_totales"] = f"${revenue_metrics.get('total_revenue', 0)}"
                menu_data["stats"]["ingresos_mes"] = f"${revenue_metrics.get('monthly_projection', 0)}"

            # Subscription stats
            subscription_analytics = analytics.get("subscription_analytics", {})
            if subscription_analytics.get("status") == "success":
                current_metrics = subscription_analytics.get("current_metrics", {})
                menu_data["stats"]["usuarios_vip"] = current_metrics.get("active_subscriptions", 0)
                menu_data["stats"]["por_expirar"] = current_metrics.get("expiring_soon_7_days", 0)

            # Engagement stats
            engagement_analytics = analytics.get("engagement_analytics", {})
            if engagement_analytics.get("status") == "success":
                vip_metrics = engagement_analytics.get("vip_user_metrics", {})
                menu_data["stats"]["engagement"] = f"{vip_metrics.get('engagement_rate', 0)}%"
        else:
            # Fallback to basic stats
            menu_data["stats"] = {
                "usuarios_vip": basic_stats.get("subscriptions_active", 0),
                "tokens_generados": basic_stats.get("tokens_total", 0),
                "ingresos_totales": f"${basic_stats.get('revenue_total', 0)}"
            }

        # Format menu text
        if HTML_AVAILABLE:
            try:
                admin_user = await session.get(User, admin_id)
                admin_name = admin_user.username if admin_user else "Admin"

                menu_text = HTMLMessageFormatter.format_admin_menu(
                    menu_data,
                    user_context={"user_name": admin_name, "role": "VIP Admin"}
                )
            except Exception as format_error:
                logger.warning(f"HTML formatting failed, using fallback: {format_error}")
                menu_text = None
        else:
            menu_text = None

        # Fallback formatting
        if menu_text is None:
            stats = menu_data["stats"]
            menu_text = (
                f"💎 **Panel VIP Avanzado**\n\n"
                f"Gestión integral de suscripciones VIP con herramientas avanzadas.\n\n"
                f"**📊 Estado Actual:**\n"
                f"• Usuarios VIP: {stats.get('usuarios_vip', 0)}\n"
                f"• Ingresos totales: {stats.get('ingresos_totales', '$0')}\n"
                f"• Engagement: {stats.get('engagement', '0%')}\n"
                f"• Por expirar: {stats.get('por_expirar', 0)}\n\n"
                f"**Selecciona una opción para continuar:**"
            )

        # Create enhanced keyboard
        keyboard = InlineKeyboardBuilder()

        # Row 1: Token generation
        keyboard.button(text="🎫 Token Individual", callback_data="vip_enhanced_single_token")
        keyboard.button(text="📦 Lote de Tokens", callback_data="vip_enhanced_batch_tokens")

        # Row 2: Analytics and users
        keyboard.button(text="📊 Analytics", callback_data="vip_enhanced_analytics")
        keyboard.button(text="👥 Usuarios VIP", callback_data="vip_enhanced_users_list")

        # Row 3: Automation and management
        keyboard.button(text="🔔 Recordatorios", callback_data="vip_enhanced_reminders")
        keyboard.button(text="🎯 Gestión", callback_data="vip_enhanced_management")

        # Row 4: Navigation
        keyboard.button(text="🔄 Actualizar", callback_data="vip_enhanced_refresh")
        keyboard.button(text="🔙 Volver", callback_data="admin_main_menu")

        keyboard.adjust(2, 2, 2, 2)

        return menu_text, keyboard

    except Exception as e:
        logger.error(f"Error creating enhanced VIP menu: {e}")
        # Fallback menu
        fallback_text = (
            "💎 **Panel VIP**\n\n"
            "Error al cargar estadísticas avanzadas.\n"
            "Menú básico disponible."
        )
        fallback_keyboard = InlineKeyboardBuilder()
        fallback_keyboard.button(text="🔙 Volver", callback_data="admin_main_menu")
        return fallback_text, fallback_keyboard

# Main VIP Enhancement Handlers

@router.callback_query(F.data == "admin_vip_enhanced")
async def show_enhanced_vip_menu(callback: CallbackQuery, session: AsyncSession):
    """Display the enhanced VIP management menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        menu_text, keyboard = await create_enhanced_vip_menu(
            session, callback.from_user.id, callback.bot
        )

        parse_mode = "HTML" if HTML_AVAILABLE else "Markdown"

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard.as_markup(),
            session,
            "vip_enhanced_main",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing enhanced VIP menu: {e}")
        await callback.answer("Error al cargar el panel VIP avanzado", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "vip_enhanced_refresh")
async def refresh_enhanced_vip_menu(callback: CallbackQuery, session: AsyncSession):
    """Refresh the enhanced VIP menu with updated data."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await show_enhanced_vip_menu(callback, session)

# Batch Token Generation (Requirement 2.1)

@router.callback_query(F.data == "vip_enhanced_batch_tokens")
async def show_batch_token_menu(callback: CallbackQuery, session: AsyncSession):
    """Show batch token generation interface."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get available tariffs
        result = await session.execute(select(Tariff))
        tariffs = result.scalars().all()

        if not tariffs:
            await callback.answer(
                "❌ No hay tarifas configuradas. Configura las tarifas primero.",
                show_alert=True
            )
            return

        # Create tariff selection menu
        menu_text = (
            "📦 **Generación de Tokens en Lote**\n\n"
            "Genera hasta 50 tokens simultáneamente para una tarifa específica.\n\n"
            "**💡 Ventajas de la generación en lote:**\n"
            "• Proceso optimizado y rápido\n"
            "• Enlaces generados automáticamente\n"
            "• Exportación en formato organizado\n"
            "• Auditoría completa de operaciones\n\n"
            "**Selecciona la tarifa:**"
        )

        keyboard = InlineKeyboardBuilder()
        for tariff in tariffs:
            keyboard.button(
                text=f"💎 {tariff.name} - {tariff.duration_days}d (${tariff.price})",
                callback_data=f"vip_batch_tariff_{tariff.id}"
            )
        keyboard.button(text="🔙 Volver", callback_data="admin_vip_enhanced")
        keyboard.adjust(1)

        parse_mode = "HTML" if HTML_AVAILABLE else "Markdown"

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard.as_markup(),
            session,
            "vip_batch_tariff_select",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing batch token menu: {e}")
        await callback.answer("Error al cargar la generación en lote", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("vip_batch_tariff_"))
async def select_batch_quantity(callback: CallbackQuery, session: AsyncSession):
    """Allow selection of batch quantity for token generation."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        tariff_id = int(callback.data.split("_")[-1])
        tariff = await session.get(Tariff, tariff_id)

        if not tariff:
            await callback.answer("❌ Tarifa no encontrada", show_alert=True)
            return

        # Create quantity selection menu
        menu_text = (
            f"📦 **Cantidad de Tokens**\n\n"
            f"**Tarifa seleccionada:** {tariff.name}\n"
            f"**Duración:** {tariff.duration_days} días\n"
            f"**Precio por token:** ${tariff.price}\n\n"
            f"**Selecciona la cantidad de tokens a generar:**"
        )

        keyboard = InlineKeyboardBuilder()

        # Predefined quantities
        quantities = [5, 10, 25, 50]
        for qty in quantities:
            total_value = qty * tariff.price
            keyboard.button(
                text=f"{qty} tokens (${total_value})",
                callback_data=f"vip_batch_generate_{tariff_id}_{qty}"
            )

        # Custom quantity option
        keyboard.button(
            text="✏️ Cantidad personalizada",
            callback_data=f"vip_batch_custom_{tariff_id}"
        )
        keyboard.button(text="🔙 Volver", callback_data="vip_enhanced_batch_tokens")
        keyboard.adjust(2, 1, 1)

        parse_mode = "HTML" if HTML_AVAILABLE else "Markdown"

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard.as_markup(),
            session,
            "vip_batch_quantity_select",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error in batch quantity selection: {e}")
        await callback.answer("Error al seleccionar cantidad", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("vip_batch_generate_"))
async def generate_batch_tokens(callback: CallbackQuery, session: AsyncSession):
    """Generate batch of VIP tokens."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Parse callback data
        parts = callback.data.split("_")
        tariff_id = int(parts[3])
        quantity = int(parts[4])

        if quantity > 50:
            await callback.answer("❌ Máximo 50 tokens por lote", show_alert=True)
            return

        # Show progress feedback by updating the menu
        loading_menu_data = {
            "title": "📦 Generando Tokens en Lote...",
            "description": f"Por favor, espere mientras se generan {quantity} tokens. Esta operación puede tardar unos segundos.",
            "sections": [{"title": "Progreso", "options": [{"icon": "⏳", "text": "Operación en curso..."}]}]
        }
        if HTML_AVAILABLE:
            loading_text = HTMLMessageFormatter.format_admin_menu(loading_menu_data)
            parse_mode = "HTML"
        else:
            loading_text = f"📦 **Generando Tokens en Lote...**\n\nPor favor, espere mientras se generan {quantity} tokens."
            parse_mode = "Markdown"

        await menu_manager.update_menu(
            callback,
            loading_text,
            None,
            session,
            "vip_batch_generating",
            parse_mode=parse_mode
        )

        # Add a small delay to make the loading message visible on fast operations
        if quantity <= 10:
            await asyncio.sleep(1.5)
        else:
            await asyncio.sleep(3)

        # Generate tokens using enhanced service
        vip_service = EnhancedVIPService(session, callback.bot)

        try:
            tokens = await vip_service.generate_batch_tokens(
                tariff_id=tariff_id,
                admin_id=callback.from_user.id,
                count=quantity
            )

            # Get bot username for links
            bot_username = (await callback.bot.get_me()).username

            # Create results message
            tariff = await session.get(Tariff, tariff_id)
            total_value = quantity * tariff.price

            if HTML_AVAILABLE:
                result_text = await format_batch_tokens_result(
                    tokens, tariff, bot_username, total_value, quantity
                )
                parse_mode = "HTML"
            else:
                # Fallback formatting
                result_text = (
                    f"✅ **Tokens Generados Exitosamente**\n\n"
                    f"📋 **Resumen:**\n"
                    f"• Cantidad: {quantity} tokens\n"
                    f"• Tarifa: {tariff.name} ({tariff.duration_days}d)\n"
                    f"• Valor total: ${total_value}\n\n"
                    f"**Enlaces generados:**\n"
                )

                for i, token in enumerate(tokens[:10], 1):  # Show first 10
                    link = f"https://t.me/{bot_username}?start={token.token_string}"
                    result_text += f"{i}. `{link}`\n"

                if len(tokens) > 10:
                    result_text += f"\n... y {len(tokens) - 10} tokens más\n"

                result_text += (
                    f"\n⚠️ **Importante:**\n"
                    f"• Cada token es de un solo uso\n"
                    f"• Comparte los enlaces directamente con los clientes\n"
                    f"• Los tokens no tienen fecha de caducidad"
                )
                parse_mode = "Markdown"

            # Create keyboard with options
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📋 Exportar Lista", callback_data=f"vip_batch_export_{tariff_id}_{quantity}")
            keyboard.button(text="📊 Ver Analytics", callback_data="vip_enhanced_analytics")
            keyboard.button(text="🔄 Generar Más", callback_data="vip_enhanced_batch_tokens")
            keyboard.button(text="🔙 Volver", callback_data="admin_vip_enhanced")
            keyboard.adjust(2, 2)

            await menu_manager.update_menu(
                callback,
                result_text,
                keyboard.as_markup(),
                session,
                "vip_batch_generated",
                parse_mode=parse_mode
            )

            # Log the operation
            logger.info(f"Admin {callback.from_user.id} generated {quantity} tokens for tariff {tariff.name}")

        except Exception as service_error:
            logger.error(f"Error in batch token generation service: {service_error}")
            await callback.answer(
                f"❌ Error al generar tokens: {str(service_error)}",
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Error in batch token generation: {e}")
        await callback.answer("Error al generar tokens en lote", show_alert=True)

    await callback.answer()

async def format_batch_tokens_result(
    tokens: List[Token],
    tariff: Tariff,
    bot_username: str,
    total_value: float,
    quantity: int
) -> str:
    """Format batch token generation results with HTML."""
    try:
        # Create HTML-formatted result
        result_lines = [
            "<b>✅ Tokens Generados Exitosamente</b>",
            "",
            "<u>📋 Resumen de Generación:</u>",
            f"• <b>Cantidad:</b> <code>{quantity}</code> tokens",
            f"• <b>Tarifa:</b> {tariff.name} ({tariff.duration_days} días)",
            f"• <b>Precio unitario:</b> <code>${tariff.price}</code>",
            f"• <b>Valor total:</b> <code>${total_value}</code>",
            f"• <b>Generado por:</b> Administrador",
            f"• <b>Fecha:</b> <i>{datetime.now().strftime('%d/%m/%Y %H:%M')}</i>",
            "",
            "<u>🔗 Enlaces de Activación:</u>"
        ]

        # Add first 10 token links
        for i, token in enumerate(tokens[:10], 1):
            link = f"https://t.me/{bot_username}?start={token.token_string}"
            short_token = token.token_string[:8] + "..."
            result_lines.append(f"{i}. <code>{short_token}</code>")
            result_lines.append(f"   <i>{link}</i>")

        if len(tokens) > 10:
            result_lines.extend([
                "",
                f"<i>... y {len(tokens) - 10} tokens adicionales</i>"
            ])

        result_lines.extend([
            "",
            "<u>⚠️ Información Importante:</u>",
            "• Cada token es válido para <b>un solo uso</b>",
            "• Los tokens no tienen fecha de expiración",
            "• Comparte los enlaces directamente con los clientes",
            "• Mantén un registro de a quién envías cada token",
            "",
            "<i>💡 Tip: Usa 'Exportar Lista' para obtener todos los enlaces organizados</i>"
        ])

        return "\n".join(result_lines)

    except Exception as e:
        logger.error(f"Error formatting batch tokens result: {e}")
        return f"✅ {quantity} tokens generados exitosamente para {tariff.name}"

# VIP User Tracking and Analytics (Requirement 2.5)

@router.callback_query(F.data == "vip_enhanced_analytics")
async def show_vip_analytics(callback: CallbackQuery, session: AsyncSession):
    """Display comprehensive VIP analytics dashboard."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Show loading message
        await callback.answer("📊 Cargando analytics...", show_alert=False)

        # Get comprehensive analytics
        vip_service = EnhancedVIPService(session, callback.bot)
        analytics = await vip_service.get_vip_analytics(metrics_type="comprehensive")

        if analytics.get("status") != "success":
            await callback.answer("❌ Error al cargar analytics", show_alert=True)
            return

        # Format analytics data
        if HTML_AVAILABLE:
            analytics_text = await format_vip_analytics_html(analytics)
            parse_mode = "HTML"
        else:
            analytics_text = await format_vip_analytics_markdown(analytics)
            parse_mode = "Markdown"

        # Create navigation keyboard
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💰 Ingresos", callback_data="vip_analytics_revenue")
        keyboard.button(text="📈 Tendencias", callback_data="vip_analytics_trends")
        keyboard.button(text="👥 Engagement", callback_data="vip_analytics_engagement")
        keyboard.button(text="📊 Resumen", callback_data="vip_analytics_summary")
        keyboard.button(text="📋 Exportar", callback_data="vip_analytics_export")
        keyboard.button(text="🔙 Volver", callback_data="admin_vip_enhanced")
        keyboard.adjust(2, 2, 2)

        await menu_manager.update_menu(
            callback,
            analytics_text,
            keyboard.as_markup(),
            session,
            "vip_analytics_main",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing VIP analytics: {e}")
        await callback.answer("Error al cargar analytics", show_alert=True)

    await callback.answer()

async def format_vip_analytics_html(analytics: Dict[str, Any]) -> str:
    """Format VIP analytics data with HTML formatting."""
    try:
        lines = [
            "<b>📊 Analytics VIP Comprehensive</b>",
            "",
            "<i>Panel de métricas avanzadas para gestión VIP</i>",
            ""
        ]

        # Period info
        period = analytics.get("period", {})
        if period:
            days = period.get("days", 0)
            lines.append(f"<u>📅 Período Analizado:</u> {days} días")
            lines.append("")

        # Revenue analytics
        revenue_analytics = analytics.get("revenue_analytics", {})
        if revenue_analytics.get("status") == "success":
            revenue_metrics = revenue_analytics.get("revenue_metrics", {})
            token_metrics = revenue_analytics.get("token_metrics", {})

            lines.extend([
                "<u>💰 Métricas de Ingresos:</u>",
                f"• <b>Ingresos totales:</b> <code>${revenue_metrics.get('total_revenue', 0)}</code>",
                f"• <b>Proyección mensual:</b> <code>${revenue_metrics.get('monthly_projection', 0)}</code>",
                f"• <b>Promedio por token:</b> <code>${revenue_metrics.get('average_revenue_per_token', 0)}</code>",
                f"• <b>Tasa de conversión:</b> <code>{token_metrics.get('conversion_rate', 0)}%</code>",
                ""
            ])

        # Subscription analytics
        subscription_analytics = analytics.get("subscription_analytics", {})
        if subscription_analytics.get("status") == "success":
            current_metrics = subscription_analytics.get("current_metrics", {})
            trend_analysis = subscription_analytics.get("trend_analysis", {})

            lines.extend([
                "<u>👥 Métricas de Suscripciones:</u>",
                f"• <b>Suscripciones activas:</b> <code>{current_metrics.get('active_subscriptions', 0)}</code>",
                f"• <b>Expiran pronto (7 días):</b> <code>{current_metrics.get('expiring_soon_7_days', 0)}</code>",
                f"• <b>Tasa de retención:</b> <code>{trend_analysis.get('retention_rate', 0)}%</code>",
                f"• <b>Renovaciones únicas:</b> <code>{trend_analysis.get('unique_renewers', 0)}</code>",
                ""
            ])

        # Engagement analytics
        engagement_analytics = analytics.get("engagement_analytics", {})
        if engagement_analytics.get("status") == "success":
            vip_metrics = engagement_analytics.get("vip_user_metrics", {})
            engagement_distribution = engagement_analytics.get("engagement_distribution", {})

            lines.extend([
                "<u>📈 Métricas de Engagement:</u>",
                f"• <b>Usuarios VIP totales:</b> <code>{vip_metrics.get('total_vip_users', 0)}</code>",
                f"• <b>Tasa de engagement:</b> <code>{vip_metrics.get('engagement_rate', 0)}%</code>",
                f"• <b>Altamente activos:</b> <code>{engagement_distribution.get('highly_engaged', 0)}</code>",
                f"• <b>Puntos promedio:</b> <code>{vip_metrics.get('average_points', 0)}</code>",
                ""
            ])

        # Summary insights
        summary_insights = analytics.get("summary_insights", {})
        if summary_insights:
            overall_health = summary_insights.get("overall_health", "good")
            health_emoji = "🟢" if overall_health == "excellent" else "🟡" if overall_health == "good" else "🔴"

            lines.extend([
                "<u>🎯 Resumen Ejecutivo:</u>",
                f"• <b>Salud general:</b> {health_emoji} <i>{overall_health.title()}</i>",
                ""
            ])

            # Alerts
            alerts = summary_insights.get("alerts", [])
            if alerts:
                lines.append("<u>⚠️ Alertas:</u>")
                for alert in alerts[:3]:  # Show max 3 alerts
                    lines.append(f"• <i>{alert}</i>")
                lines.append("")

            # Recommendations
            recommendations = summary_insights.get("recommendations", [])
            if recommendations:
                lines.append("<u>💡 Recomendaciones:</u>")
                for rec in recommendations[:2]:  # Show max 2 recommendations
                    lines.append(f"• <i>{rec}</i>")

        # Footer
        generated_at = analytics.get("generated_at", "")
        if generated_at:
            timestamp = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            lines.extend([
                "",
                f"<i>🕐 Generado: {timestamp.strftime('%d/%m/%Y %H:%M UTC')}</i>"
            ])

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error formatting VIP analytics HTML: {e}")
        return "<b>📊 Analytics VIP</b>\n\nError al formatear los datos analíticos."

async def format_vip_analytics_markdown(analytics: Dict[str, Any]) -> str:
    """Format VIP analytics data with Markdown formatting."""
    try:
        lines = [
            "📊 **Analytics VIP Comprehensive**",
            "",
            "_Panel de métricas avanzadas para gestión VIP_",
            ""
        ]

        # Period info
        period = analytics.get("period", {})
        if period:
            days = period.get("days", 0)
            lines.append(f"**📅 Período:** {days} días")
            lines.append("")

        # Revenue metrics summary
        revenue_analytics = analytics.get("revenue_analytics", {})
        if revenue_analytics.get("status") == "success":
            revenue_metrics = revenue_analytics.get("revenue_metrics", {})
            lines.extend([
                "**💰 Ingresos:**",
                f"• Total: ${revenue_metrics.get('total_revenue', 0)}",
                f"• Proyección mensual: ${revenue_metrics.get('monthly_projection', 0)}",
                ""
            ])

        # Subscription metrics summary
        subscription_analytics = analytics.get("subscription_analytics", {})
        if subscription_analytics.get("status") == "success":
            current_metrics = subscription_analytics.get("current_metrics", {})
            lines.extend([
                "**👥 Suscripciones:**",
                f"• Activas: {current_metrics.get('active_subscriptions', 0)}",
                f"• Expiran pronto: {current_metrics.get('expiring_soon_7_days', 0)}",
                ""
            ])

        # Engagement metrics summary
        engagement_analytics = analytics.get("engagement_analytics", {})
        if engagement_analytics.get("status") == "success":
            vip_metrics = engagement_analytics.get("vip_user_metrics", {})
            lines.extend([
                "**📈 Engagement:**",
                f"• Usuarios VIP: {vip_metrics.get('total_vip_users', 0)}",
                f"• Tasa de engagement: {vip_metrics.get('engagement_rate', 0)}%",
                ""
            ])

        lines.append("_Selecciona una categoría para ver detalles completos_")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error formatting VIP analytics Markdown: {e}")
        return "📊 **Analytics VIP**\n\nError al formatear los datos analíticos."

@router.callback_query(F.data == "vip_enhanced_users_list")
async def show_vip_users_list(callback: CallbackQuery, session: AsyncSession):
    """Display list of VIP users with management options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Show loading
        await callback.answer("👥 Cargando usuarios VIP...", show_alert=False)

        # Get active VIP users
        now = datetime.utcnow()
        vip_users_stmt = (
            select(User, VipSubscription)
            .join(VipSubscription, User.id == VipSubscription.user_id)
            .where(
                or_(
                    VipSubscription.expires_at.is_(None),
                    VipSubscription.expires_at > now
                )
            )
            .order_by(VipSubscription.expires_at.asc())
        )

        result = await session.execute(vip_users_stmt)
        vip_users_data = result.all()

        if not vip_users_data:
            await callback.answer("ℹ️ No hay usuarios VIP activos", show_alert=True)
            return

        # Format user list
        if HTML_AVAILABLE:
            users_text = await format_vip_users_list_html(vip_users_data)
            parse_mode = "HTML"
        else:
            users_text = await format_vip_users_list_markdown(vip_users_data)
            parse_mode = "Markdown"

        # Create management keyboard
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📊 Estadísticas", callback_data="vip_users_stats")
        keyboard.button(text="⚠️ Por Expirar", callback_data="vip_users_expiring")
        keyboard.button(text="🔔 Recordatorios", callback_data="vip_enhanced_reminders")
        keyboard.button(text="📋 Exportar", callback_data="vip_users_export")
        keyboard.button(text="🔄 Actualizar", callback_data="vip_enhanced_users_list")
        keyboard.button(text="🔙 Volver", callback_data="admin_vip_enhanced")
        keyboard.adjust(2, 2, 2)

        await menu_manager.update_menu(
            callback,
            users_text,
            keyboard.as_markup(),
            session,
            "vip_users_list",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing VIP users list: {e}")
        await callback.answer("Error al cargar lista de usuarios", show_alert=True)

    await callback.answer()

async def format_vip_users_list_html(vip_users_data: List[Tuple[User, VipSubscription]]) -> str:
    """Format VIP users list with HTML formatting."""
    try:
        lines = [
            "<b>👥 Usuarios VIP Activos</b>",
            "",
            f"<i>Total de usuarios: {len(vip_users_data)}</i>",
            ""
        ]

        now = datetime.utcnow()

        # Group users by expiration status
        expiring_soon = []
        active_users = []

        for user, vip_sub in vip_users_data:
            if vip_sub.expires_at:
                days_remaining = (vip_sub.expires_at - now).days
                if days_remaining <= 7:
                    expiring_soon.append((user, vip_sub, days_remaining))
                else:
                    active_users.append((user, vip_sub, days_remaining))
            else:
                active_users.append((user, vip_sub, None))

        # Show users expiring soon first
        if expiring_soon:
            lines.append("<u>⚠️ Expiran Pronto (≤7 días):</u>")
            for user, vip_sub, days in expiring_soon[:5]:  # Show max 5
                status_icon = "🔴" if days <= 1 else "🟡" if days <= 3 else "🟠"
                user_name = user.username or f"ID: {user.id}"
                expires_date = vip_sub.expires_at.strftime("%d/%m")
                lines.append(f"{status_icon} <b>{user_name}</b> - Expira {expires_date} ({days}d)")

            if len(expiring_soon) > 5:
                lines.append(f"<i>... y {len(expiring_soon) - 5} más</i>")
            lines.append("")

        # Show sample of active users
        if active_users:
            lines.append("<u>✅ Usuarios Activos:</u>")
            for user, vip_sub, days in active_users[:10]:  # Show max 10
                user_name = user.username or f"ID: {user.id}"
                if days:
                    expires_info = f"({days}d restantes)"
                else:
                    expires_info = "(Sin expiración)"
                lines.append(f"🟢 <b>{user_name}</b> - {expires_info}")

            if len(active_users) > 10:
                lines.append(f"<i>... y {len(active_users) - 10} más</i>")

        # Summary
        lines.extend([
            "",
            "<u>📊 Resumen:</u>",
            f"• <b>Expiran pronto:</b> <code>{len(expiring_soon)}</code>",
            f"• <b>Usuarios activos:</b> <code>{len(active_users)}</code>",
            f"• <b>Total:</b> <code>{len(vip_users_data)}</code>"
        ])

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error formatting VIP users list HTML: {e}")
        return f"<b>👥 Usuarios VIP</b>\n\nTotal: {len(vip_users_data)} usuarios activos"

async def format_vip_users_list_markdown(vip_users_data: List[Tuple[User, VipSubscription]]) -> str:
    """Format VIP users list with Markdown formatting."""
    try:
        lines = [
            "👥 **Usuarios VIP Activos**",
            "",
            f"_Total de usuarios: {len(vip_users_data)}_",
            ""
        ]

        # Sample of users
        for i, (user, vip_sub) in enumerate(vip_users_data[:10], 1):
            user_name = user.username or f"ID: {user.id}"
            if vip_sub.expires_at:
                days = (vip_sub.expires_at - datetime.utcnow()).days
                status = "⚠️" if days <= 7 else "✅"
                expires_info = f"({days}d restantes)"
            else:
                status = "✅"
                expires_info = "(Sin expiración)"

            lines.append(f"{i}. {status} **{user_name}** - {expires_info}")

        if len(vip_users_data) > 10:
            lines.append(f"\n_... y {len(vip_users_data) - 10} usuarios más_")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error formatting VIP users list Markdown: {e}")
        return f"👥 **Usuarios VIP**\n\nTotal: {len(vip_users_data)} usuarios activos"

# Reminder Management

@router.callback_query(F.data == "vip_enhanced_reminders")
async def show_reminder_management(callback: CallbackQuery, session: AsyncSession):
    """Show VIP reminder management interface."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get reminder status
        vip_service = EnhancedVIPService(session, callback.bot)
        reminder_status = await vip_service.get_reminder_status()

        # Format reminder management menu
        status_text = "running" if reminder_status.get("automation_active") else "stopped"
        status_icon = "🟢" if status_text == "running" else "🔴"

        menu_text = (
            f"🔔 **Gestión de Recordatorios VIP**\n\n"
            f"Sistema automatizado de recordatorios para suscripciones próximas a expirar.\n\n"
            f"**Estado del sistema:** {status_icon} {status_text.title()}\n"
            f"**Recordatorios activos:** {reminder_status.get('tracked_reminders', 0)}\n\n"
            f"**📋 Configuración actual:**\n"
            f"• Recordatorio 3 días antes\n"
            f"• Recordatorio 1 día antes\n"
            f"• Notificación de expiración\n\n"
            f"**Selecciona una acción:**"
        )

        keyboard = InlineKeyboardBuilder()

        if status_text == "stopped":
            keyboard.button(text="▶️ Iniciar Recordatorios", callback_data="vip_reminders_start")
        else:
            keyboard.button(text="⏸️ Pausar Recordatorios", callback_data="vip_reminders_stop")

        keyboard.button(text="🔄 Estado", callback_data="vip_reminders_status")
        keyboard.button(text="⚙️ Configurar", callback_data="vip_reminders_config")
        keyboard.button(text="📊 Historial", callback_data="vip_reminders_history")
        keyboard.button(text="🔙 Volver", callback_data="admin_vip_enhanced")
        keyboard.adjust(2, 2, 1)

        parse_mode = "HTML" if HTML_AVAILABLE else "Markdown"

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard.as_markup(),
            session,
            "vip_reminders_manage",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing reminder management: {e}")
        await callback.answer("Error al cargar gestión de recordatorios", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "vip_reminders_start")
async def start_vip_reminders(callback: CallbackQuery, session: AsyncSession):
    """Start VIP reminder automation."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        vip_service = EnhancedVIPService(session, callback.bot)
        result = await vip_service.start_reminder_automation(check_interval_minutes=60)

        if result.get("status") == "started":
            await callback.answer("✅ Recordatorios iniciados correctamente", show_alert=True)
        elif result.get("status") == "already_running":
            await callback.answer("ℹ️ Los recordatorios ya están activos", show_alert=True)
        else:
            await callback.answer("❌ Error al iniciar recordatorios", show_alert=True)

        # Refresh the menu
        await show_reminder_management(callback, session)

    except Exception as e:
        logger.error(f"Error starting VIP reminders: {e}")
        await callback.answer("Error al iniciar recordatorios", show_alert=True)

@router.callback_query(F.data == "vip_reminders_stop")
async def stop_vip_reminders(callback: CallbackQuery, session: AsyncSession):
    """Stop VIP reminder automation."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        vip_service = EnhancedVIPService(session, callback.bot)
        result = await vip_service.stop_reminder_automation()

        if result.get("status") == "stopped":
            await callback.answer("⏸️ Recordatorios pausados correctamente", show_alert=True)
        elif result.get("status") == "not_running":
            await callback.answer("ℹ️ Los recordatorios ya están inactivos", show_alert=True)
        else:
            await callback.answer("❌ Error al pausar recordatorios", show_alert=True)

        # Refresh the menu
        await show_reminder_management(callback, session)

    except Exception as e:
        logger.error(f"Error stopping VIP reminders: {e}")
        await callback.answer("Error al pausar recordatorios", show_alert=True)

# Integration with existing VIP menu

@router.callback_query(F.data == "admin_vip")
async def enhanced_vip_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Enhanced version of the main VIP menu with additional options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get basic stats for the enhanced menu
        from services import get_admin_statistics
        stats = await get_admin_statistics(session)

        # Create enhanced VIP menu
        menu_text = (
            f"💎 **Administración Canal VIP**\n\n"
            f"Panel avanzado de gestión VIP con herramientas mejoradas.\n\n"
            f"**📊 Estado actual:**\n"
            f"• Suscripciones activas: {stats.get('subscriptions_active', 0)}\n"
            f"• Total de usuarios: {stats.get('users_total', 0)}\n"
            f"• Ingresos generados: ${stats.get('revenue_total', 0)}\n\n"
            f"**Selecciona una opción:**"
        )

        keyboard = InlineKeyboardBuilder()

        # Enhanced options first
        keyboard.button(text="⭐ Panel VIP Avanzado", callback_data="admin_vip_enhanced")
        keyboard.button(text="📦 Tokens en Lote", callback_data="vip_enhanced_batch_tokens")

        # Standard options
        keyboard.button(text="🎫 Token Individual", callback_data="vip_generate_token")
        keyboard.button(text="📊 Estadísticas", callback_data="vip_stats")
        keyboard.button(text="👥 Usuarios VIP", callback_data="vip_enhanced_users_list")
        keyboard.button(text="🔔 Recordatorios", callback_data="vip_enhanced_reminders")

        # Navigation
        keyboard.button(text="🔙 Volver", callback_data="admin_main_menu")

        keyboard.adjust(2, 2, 2, 1)

        parse_mode = "HTML" if HTML_AVAILABLE else "Markdown"

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard.as_markup(),
            session,
            "admin_vip_enhanced_main",
            parse_mode=parse_mode
        )

    except Exception as e:
        logger.error(f"Error showing enhanced VIP main menu: {e}")
        await callback.answer("Error al cargar el panel VIP", show_alert=True)

    await callback.answer()

# Command handlers

@router.message(Command("vip_analytics"))
async def cmd_vip_analytics(message: Message, session: AsyncSession):
    """Command to quickly access VIP analytics."""
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Create callback-like object for reusing existing logic
        from aiogram.types import CallbackQuery

        # Show analytics directly
        vip_service = EnhancedVIPService(session, message.bot)
        analytics = await vip_service.get_vip_analytics(metrics_type="comprehensive")

        if analytics.get("status") != "success":
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error**\n\nNo se pudieron cargar las analíticas VIP.",
                auto_delete_seconds=5
            )
            return

        # Format and send analytics
        if HTML_AVAILABLE:
            analytics_text = await format_vip_analytics_html(analytics)
            parse_mode = "HTML"
        else:
            analytics_text = await format_vip_analytics_markdown(analytics)
            parse_mode = "Markdown"

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔄 Panel Completo", callback_data="admin_vip_enhanced")
        keyboard.adjust(1)

        await menu_manager.show_menu(
            message=message,
            text=analytics_text,
            keyboard=keyboard.as_markup(),
            session=session,
            menu_state="vip_analytics_cmd",
            parse_mode=parse_mode,
            delete_origin_message=True
        )

    except Exception as e:
        logger.error(f"Error in VIP analytics command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error**\n\nError al cargar las analíticas.",
            auto_delete_seconds=5
        )