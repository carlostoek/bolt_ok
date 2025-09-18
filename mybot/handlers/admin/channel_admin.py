from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from keyboards.admin_channels_kb import get_admin_channels_kb, get_wait_time_kb, get_enhanced_channel_kb
from keyboards.common import get_back_kb
from services.channel_service import ChannelService
from services.config_service import ConfigService
from services.channel_admin_service import ChannelAdminService
from database.models import BotConfig

router = Router()


class ChannelStates(StatesGroup):
    waiting_for_vip_channel_id = State()
    waiting_for_free_channel_id = State()


@router.callback_query(F.data == "admin_channels")
async def channels_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = ChannelService(session)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = "Administrar canales\n\n" + "\n".join(lines)
    else:
        text = "Administrar canales\n\nNo hay canales configurados."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_channel")
async def prompt_add_channel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el ID del canal VIP o reenv\u00eda un mensaje del canal aqu\u00ed.\n"
        "Puedes escribir directamente el ID del canal (debes ser administrador del canal para obtenerlo), "
        "o puedes reenviar un mensaje del canal aqu\u00ed y el bot extraer\u00e1 autom\u00e1ticamente el ID del remitente.",
        reply_markup=get_back_kb("admin_channels"),
    )
    await state.set_state(ChannelStates.waiting_for_vip_channel_id)
    await callback.answer()


@router.message(ChannelStates.waiting_for_vip_channel_id)
async def receive_vip_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    chat_id = None
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await send_temporary_reply(message, "ID inválido. Intenta de nuevo.")
            return
    await state.update_data(vip_channel_id=chat_id)
    await message.answer(
        "Ahora ingresa el ID del canal FREE o reenv\u00eda un mensaje del canal.",
        reply_markup=get_back_kb("admin_channels"),
    )
    await state.set_state(ChannelStates.waiting_for_free_channel_id)


@router.message(ChannelStates.waiting_for_free_channel_id)
async def receive_free_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    chat_id = None
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await send_temporary_reply(message, "ID inválido. Intenta de nuevo.")
            return
    data = await state.get_data()
    vip_id = int(data.get("vip_channel_id"))
    config = ConfigService(session)
    await config.set_vip_channel_id(vip_id)
    await config.set_free_channel_id(chat_id)

    channel_service = ChannelService(session)
    await channel_service.add_channel(vip_id)
    await channel_service.add_channel(chat_id)

    await message.answer(
        f"Canales registrados correctamente. Canal VIP: {vip_id}, Canal FREE: {chat_id}",
        reply_markup=get_admin_channels_kb(await channel_service.list_channels()),
    )
    await state.clear()


@router.callback_query(F.data == "admin_wait_time")
async def wait_time_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    config = await session.get(BotConfig, 1)
    current = config.free_channel_wait_time_minutes if config else 0
    await update_menu(
        callback,
        f"Tiempo actual: {current} minutos",
        get_wait_time_kb(),
        session,
        "admin_wait_time",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wait_"))
async def set_wait_time(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    minutes = int(callback.data.split("_")[1])
    config = await session.get(BotConfig, 1)
    if not config:
        config = BotConfig(id=1)
        session.add(config)
    config.free_channel_wait_time_minutes = minutes
    await session.commit()
    service = ChannelService(session)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = f"Tiempo actualizado a {minutes} minutos.\n\n" + "\n".join(lines)
    else:
        text = f"Tiempo actualizado a {minutes} minutos."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_channel_"))
async def remove_channel(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    chat_id = int(callback.data.split("_")[-1])
    service = ChannelService(session)
    await service.remove_channel(chat_id)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = "Canales actualizados:\n\n" + "\n".join(lines)
    else:
        text = "No hay canales configurados."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer("Canal eliminado")


@router.callback_query(F.data == "admin_channel_enhanced")
async def show_enhanced_channel_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Enhanced channel administration menu with bulk operations and content protection.
    Connects to existing channel_admin_service functionality.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    # Initialize enhanced channel admin service
    channel_admin_service = ChannelAdminService(session)

    # Get basic channel information
    channel_service = ChannelService(session)
    channels = await channel_service.list_channels()

    # Get channel analytics overview
    config_service = ConfigService(session)
    vip_channel_id = await config_service.get_vip_channel_id()
    free_channel_id = await config_service.get_free_channel_id()

    # Create enhanced menu text with current status
    text_lines = [
        "🏢 <b>Administración Avanzada de Canales</b>",
        "",
        "📊 <b>Estado Actual:</b>"
    ]

    if channels:
        text_lines.append(f"• Canales configurados: {len(channels)}")
        if vip_channel_id:
            text_lines.append(f"• Canal VIP: <code>{vip_channel_id}</code>")
        if free_channel_id:
            text_lines.append(f"• Canal FREE: <code>{free_channel_id}</code>")
    else:
        text_lines.append("• No hay canales configurados")

    text_lines.extend([
        "",
        "🔧 <b>Funciones Disponibles:</b>",
        "• Gestión masiva de acceso VIP",
        "• Protección avanzada de contenido",
        "• Analytics y reportes detallados",
        "• Publicación de contenido exclusivo",
        "",
        "Selecciona una opción para continuar:"
    ])

    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced",
    )
    await callback.answer()


@router.callback_query(F.data == "channel_vip_management")
async def channel_vip_management(callback: CallbackQuery, session: AsyncSession):
    """Handle VIP access management for channels."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)

    # Get VIP channel analytics
    config_service = ConfigService(session)
    vip_channel_id = await config_service.get_vip_channel_id()

    if not vip_channel_id:
        await update_menu(
            callback,
            "❌ Canal VIP no configurado.\n\nConfigura un canal VIP primero en la configuración de canales.",
            get_enhanced_channel_kb(),
            session,
            "admin_channel_enhanced"
        )
        return await callback.answer()

    # Get channel analytics
    analytics_result = await channel_admin_service.get_channel_analytics(vip_channel_id)

    text_lines = [
        "👤 <b>Gestión de Acceso VIP</b>",
        "",
        "📊 <b>Estadísticas del Canal VIP:</b>"
    ]

    if analytics_result["success"]:
        analytics = analytics_result["analytics"]
        subscription_metrics = analytics.get("subscription_metrics", {})

        text_lines.extend([
            f"• Suscripciones totales: {subscription_metrics.get('total_subscriptions', 0)}",
            f"• Suscripciones activas: {subscription_metrics.get('active_subscriptions', 0)}",
            f"• Tasa de actividad: {subscription_metrics.get('subscription_rate', 0)}%",
            f"• Usuarios activos: {analytics.get('active_subscriber_count', 0)}"
        ])
    else:
        text_lines.append("• Error al obtener estadísticas")

    text_lines.extend([
        "",
        "🔧 <b>Operaciones Disponibles:</b>",
        "• Acceso desde Ops. Masivas para gestión en lote",
        "• Revisa Analytics para métricas detalladas",
        "• Usa Protección para configurar contenido exclusivo"
    ])

    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_analytics")
async def channel_analytics(callback: CallbackQuery, session: AsyncSession):
    """Display detailed channel analytics."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)

    # Generate comprehensive analytics report
    report_result = await channel_admin_service.generate_channel_analytics_report(
        period_days=30,
        report_type="comprehensive"
    )

    text_lines = [
        "📊 <b>Analytics de Canales (30 días)</b>",
        ""
    ]

    if report_result.get("status") == "success":
        # Financial metrics
        financial_data = report_result.get("financial_metrics", {})
        if financial_data.get("success"):
            financial_metrics = financial_data["financial_metrics"]
            revenue_summary = financial_metrics.get("revenue_summary", {})
            user_metrics = financial_metrics.get("user_metrics", {})

            text_lines.extend([
                "💰 <b>Métricas Financieras:</b>",
                f"• Ingresos totales: {revenue_summary.get('total_revenue', 0)} besitos",
                f"• Ingresos por tokens: {revenue_summary.get('token_revenue', 0)} besitos",
                f"• ARPU: {user_metrics.get('arpu', 0)} besitos",
                f"• Usuarios pagadores: {user_metrics.get('unique_paying_users', 0)}",
                ""
            ])

        # Engagement data
        engagement_data = report_result.get("all_channels_engagement", {})
        if engagement_data:
            vip_engagement = engagement_data.get("vip_channel", {})
            if vip_engagement and vip_engagement.get("success"):
                vip_analytics = vip_engagement["analytics"]["engagement_summary"]
                text_lines.extend([
                    "📈 <b>Engagement VIP:</b>",
                    f"• Reacciones totales: {vip_analytics.get('total_reactions', 0)}",
                    f"• Usuarios únicos: {vip_analytics.get('unique_users', 0)}",
                    f"• Promedio por usuario: {vip_analytics.get('average_reactions_per_user', 0)}",
                    ""
                ])

        # Summary insights
        insights = report_result.get("summary_insights", {})
        if insights:
            highlights = insights.get("performance_highlights", [])
            if highlights:
                text_lines.extend([
                    "✨ <b>Puntos Destacados:</b>"
                ])
                for highlight in highlights[:3]:  # Show top 3
                    text_lines.append(f"• {highlight}")
                text_lines.append("")
    else:
        text_lines.extend([
            "❌ Error al generar analytics:",
            f"• {report_result.get('message', 'Error desconocido')}"
        ])

    text_lines.append("🔄 Los datos se actualizan automáticamente cada hora.")
    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_content_protection")
async def channel_content_protection(callback: CallbackQuery, session: AsyncSession):
    """Configure content protection for channels."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)
    config_service = ConfigService(session)

    # Get protection status for configured channels
    vip_channel_id = await config_service.get_vip_channel_id()
    free_channel_id = await config_service.get_free_channel_id()

    text_lines = [
        "🛡️ <b>Protección de Contenido</b>",
        "",
        "📋 <b>Estado de Protección:</b>"
    ]

    if vip_channel_id:
        vip_protection = await channel_admin_service.get_content_protection_status(vip_channel_id)
        if vip_protection["success"]:
            status = vip_protection["protection_status"]
            text_lines.extend([
                f"• Canal VIP (<code>{vip_channel_id}</code>):",
                f"  - Protección: {'✅ Activa' if status['protection_enabled'] else '❌ Inactiva'}",
                f"  - Nivel: {status['default_protection_level']}",
                f"  - Anti-forwarding: {'✅' if status['available_protection_features']['forwarding_protection'] else '❌'}",
                f"  - Anti-download: {'✅' if status['available_protection_features']['download_protection'] else '❌'}"
            ])

    if free_channel_id:
        free_protection = await channel_admin_service.get_content_protection_status(free_channel_id)
        if free_protection["success"]:
            status = free_protection["protection_status"]
            text_lines.extend([
                f"• Canal FREE (<code>{free_channel_id}</code>):",
                f"  - Protección: {'✅ Activa' if status['protection_enabled'] else '❌ Inactiva'}",
                f"  - Nivel: {status['default_protection_level']}"
            ])

    text_lines.extend([
        "",
        "🔧 <b>Configuración:</b>",
        "• VIP: Protección completa habilitada",
        "• FREE: Protección básica",
        "• Exclusive: Máxima protección + watermarks",
        "",
        "ℹ️ La protección se aplica automáticamente",
        "según el tipo de canal y contenido."
    ])

    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_analytics_enhanced")
async def channel_analytics_enhanced(callback: CallbackQuery, session: AsyncSession):
    """Enhanced channel analytics with routing to analytics service."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    try:
        channel_admin_service = ChannelAdminService(session)

        # Generate comprehensive analytics with enhanced metrics
        report_result = await channel_admin_service.generate_channel_analytics_report(
            period_days=30,
            report_type="comprehensive"
        )

        text_lines = [
            "📊 <b>Analytics Avanzados de Canales</b>",
            "",
            "🔗 <b>Integración con Analytics Service</b>",
            ""
        ]

        if report_result.get("status") == "success":
            # Enhanced financial metrics section
            financial_data = report_result.get("financial_metrics", {})
            if financial_data.get("success"):
                financial_metrics = financial_data["financial_metrics"]
                revenue_summary = financial_metrics.get("revenue_summary", {})
                user_metrics = financial_metrics.get("user_metrics", {})
                conversion_metrics = financial_metrics.get("conversion_metrics", {})

                text_lines.extend([
                    "💰 <b>PERFORMANCE FINANCIERO:</b>",
                    f"• Revenue Total: {revenue_summary.get('total_revenue', 0)} besitos",
                    f"• ARPU: {user_metrics.get('arpu', 0)} besitos/usuario",
                    f"• Conversión VIP: {conversion_metrics.get('token_conversion_rate', 0)}%",
                    f"• Usuarios Pagadores: {user_metrics.get('unique_paying_users', 0)}",
                    ""
                ])

            # Enhanced engagement metrics
            engagement_data = report_result.get("all_channels_engagement", {})
            if engagement_data:
                vip_engagement = engagement_data.get("vip_channel", {})
                if vip_engagement and vip_engagement.get("success"):
                    vip_analytics = vip_engagement["analytics"]["engagement_summary"]
                    vip_segmentation = vip_engagement["analytics"]["user_segmentation"]

                    text_lines.extend([
                        "📈 <b>ENGAGEMENT AVANZADO:</b>",
                        f"• Reacciones VIP: {vip_analytics.get('total_reactions', 0)}",
                        f"• Rate VIP: {vip_segmentation.get('vip_engagement_rate', 0):.2f}",
                        f"• Usuarios Únicos: {vip_analytics.get('unique_users', 0)}",
                        ""
                    ])

            # Add bulk operations context
            text_lines.extend([
                "🔄 <b>OPERACIONES MASIVAS:</b>",
                f"• Servicio batch_manage_vip_access() disponible",
                f"• Validación automática de permisos integrada",
                f"• Tracking de operaciones en analytics",
                ""
            ])

            # Analytics service integration points
            text_lines.extend([
                "🔗 <b>INTEGRACIÓN ANALYTICS SERVICE:</b>",
                f"• Routing automático a analytics_handlers",
                f"• Métricas exportables a dashboard central",
                f"• API de analytics disponible para reportes",
                f"• Coordinación con sistema central",
                ""
            ])

            # Quick access to bulk operations
            text_lines.extend([
                "⚡ <b>ACCESO RÁPIDO:</b>",
                f"• Usa 'Ops. Masivas' para gestión en lote",
                f"• Accede a 'Analytics' para métricas detalladas",
                f"• 'Protección' para configuración de contenido"
            ])

        else:
            text_lines.extend([
                "❌ Error al generar analytics avanzados:",
                f"• {report_result.get('message', 'Error desconocido')}"
            ])

        text = "\n".join(text_lines)

        # Create enhanced navigation with analytics service integration
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Analytics service integration buttons
        builder.button(text="📊 Analytics Service", callback_data="admin_analytics_main")
        builder.button(text="🔄 Ops. Masivas", callback_data="channel_bulk_operations")

        # Channel management options
        builder.button(text="👤 Gestión VIP", callback_data="channel_vip_management")
        builder.button(text="🛡️ Protección", callback_data="channel_content_protection")

        # Navigation
        builder.button(text="↩️ Canales", callback_data="admin_channel_enhanced")
        builder.button(text="🏠 Principal", callback_data="admin_main_menu")

        builder.adjust(2, 2, 2)

        await update_menu(
            callback,
            text,
            builder.as_markup(),
            session,
            "channel_analytics_enhanced"
        )

    except Exception as e:
        logger.exception(f"Error in enhanced channel analytics: {e}")
        await update_menu(
            callback,
            "❌ Error al cargar analytics avanzados de canales.",
            get_enhanced_channel_kb(),
            session,
            "admin_channel_enhanced"
        )

    await callback.answer()


# Additional handlers for enhanced channel administration
# These should be appended to channel_admin.py

@router.callback_query(F.data == "channel_bulk_operations")
async def channel_bulk_operations(callback: CallbackQuery, session: AsyncSession):
    """Handle bulk VIP access management operations with enhanced functionality."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)
    config_service = ConfigService(session)

    # Get channel configuration for context
    vip_channel_id = await config_service.get_vip_channel_id()
    free_channel_id = await config_service.get_free_channel_id()

    text_lines = [
        "🔄 <b>Operaciones Masivas de Canales</b>",
        "",
        "🎯 <b>Centro de Gestión en Lote</b>",
        ""
    ]

    # Add channel status
    text_lines.extend([
        "📊 <b>Estado de Canales:</b>",
        f"• Canal VIP: {'✅ ' + str(vip_channel_id) if vip_channel_id else '❌ No configurado'}",
        f"• Canal Free: {'✅ ' + str(free_channel_id) if free_channel_id else '❌ No configurado'}",
        ""
    ])

    text_lines.extend([
        "🎯 <b>Gestión VIP en Lote:</b>",
        "• <b>batch_manage_vip_access()</b> - Función principal",
        "• Otorgar acceso VIP a múltiples usuarios",
        "• Extender suscripciones existentes masivamente",
        "• Revocar acceso VIP por lotes",
        "• Migración de usuarios entre niveles",
        "",
        "📊 <b>Funciones Avanzadas:</b>",
        "• Procesamiento asíncrono en segundo plano",
        "• Reportes de progreso en tiempo real",
        "• Validación automática de permisos administrativos",
        "• Rollback automático en caso de errores",
        "• Logging completo de todas las operaciones",
        "",
        "🛡️ <b>Protección y Control:</b>",
        "• Validación de permisos antes de cada operación",
        "• Control de acceso basado en roles",
        "• Tracking de operaciones para auditoría",
        "• Integración con sistema de analytics",
        "",
        "⚡ <b>Casos de Uso Comunes:</b>",
        "• Promociones masivas de VIP",
        "• Migración de usuarios desde otros sistemas",
        "• Mantenimiento programado de suscripciones",
        "• Gestión de campañas de marketing",
        "• Renovaciones automáticas en lote",
        "",
        "🔗 <b>Integración con Analytics:</b>",
        "• Tracking automático en analytics service",
        "• Métricas de rendimiento de operaciones",
        "• Reportes de conversión y engagement",
        "• Datos exportables para análisis",
        "",
        "💡 <b>Herramientas Disponibles:</b>",
        "• API batch_manage_vip_access() lista para usar",
        "• Validación de consistencia automática",
        "• Interface de administración integrada",
        "• Coordinación con sistema central"
    ])

    text = "\n".join(text_lines)

    # Create enhanced bulk operations keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Primary bulk operations
    builder.button(text="⚡ Batch VIP", callback_data="channel_bulk_vip_access")
    builder.button(text="👤 Gestión VIP", callback_data="channel_vip_management")

    # Analytics and reporting
    builder.button(text="📊 Analytics", callback_data="channel_analytics_enhanced")
    builder.button(text="📈 Reportes", callback_data="channel_generate_report")

    # Content and protection
    builder.button(text="🛡️ Protección", callback_data="channel_content_protection")
    builder.button(text="📝 Contenido", callback_data="channel_publish_content")

    # Navigation
    builder.button(text="↩️ Canales", callback_data="admin_channel_enhanced")
    builder.button(text="🏠 Principal", callback_data="admin_main_menu")

    builder.adjust(2, 2, 2, 2)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "channel_bulk_operations"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_bulk_vip_access")
async def channel_bulk_vip_access(callback: CallbackQuery, session: AsyncSession):
    """Direct access to bulk VIP access management operations."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)
    config_service = ConfigService(session)

    # Get VIP channel configuration
    vip_channel_id = await config_service.get_vip_channel_id()

    text_lines = [
        "⚡ <b>Gestión Masiva de Acceso VIP</b>",
        "",
        "🎯 <b>Operaciones Disponibles:</b>",
        ""
    ]

    if vip_channel_id:
        # Get current VIP statistics
        analytics_result = await channel_admin_service.get_channel_analytics(vip_channel_id)

        if analytics_result["success"]:
            analytics = analytics_result["analytics"]
            subscription_metrics = analytics.get("subscription_metrics", {})
            active_count = subscription_metrics.get("active_subscriptions", 0)
            total_count = subscription_metrics.get("total_subscriptions", 0)

            text_lines.extend([
                f"📊 <b>Estado Actual VIP:</b>",
                f"• Canal VIP: <code>{vip_channel_id}</code>",
                f"• Suscripciones activas: {active_count}",
                f"• Suscripciones totales: {total_count}",
                ""
            ])

    text_lines.extend([
        "🔄 <b>Funciones de Batch:</b>",
        "• <b>batch_manage_vip_access()</b> - Operaciones en lote",
        "• Otorgar acceso VIP múltiple",
        "• Extender suscripciones existentes",
        "• Revocar acceso masivamente",
        "• Validación automática de permisos",
        "",
        "⚙️ <b>Características:</b>",
        "• Procesamiento en segundo plano",
        "• Reportes de progreso en tiempo real",
        "• Rollback automático en errores",
        "• Logging completo de operaciones",
        "",
        "📋 <b>Ejemplos de Uso:</b>",
        "• Migración de usuarios desde otro sistema",
        "• Promociones masivas y campañas",
        "• Mantenimiento de suscripciones",
        "• Gestión de acceso por grupos",
        "",
        "💡 <b>Próximamente:</b>",
        "• Interface gráfica para operaciones batch",
        "• Templates de operaciones predefinidas",
        "• Programación de tareas automáticas",
        "• Integración con analytics avanzados"
    ])

    text = "\n".join(text_lines)

    # Create bulk operations specific keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Direct access to batch functions
    builder.button(text="🔄 Ops. Masivas", callback_data="channel_bulk_operations")
    builder.button(text="📊 VIP Analytics", callback_data="channel_vip_management")

    # Analytics and reporting
    builder.button(text="📈 Ver Reportes", callback_data="channel_generate_report")
    builder.button(text="📊 Analytics Plus", callback_data="channel_analytics_enhanced")

    # Navigation
    builder.button(text="↩️ Canales", callback_data="admin_channel_enhanced")
    builder.button(text="🏠 Principal", callback_data="admin_main_menu")

    builder.adjust(2, 2, 2)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "channel_bulk_vip_access"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_publish_content")
async def channel_publish_content(callback: CallbackQuery, session: AsyncSession):
    """Handle exclusive content publishing."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    channel_admin_service = ChannelAdminService(session)
    config_service = ConfigService(session)

    # Get channel configuration
    vip_channel_id = await config_service.get_vip_channel_id()
    free_channel_id = await config_service.get_free_channel_id()

    text_lines = [
        "📝 <b>Publicación de Contenido Exclusivo</b>",
        "",
        "🎯 <b>Canales Disponibles:</b>"
    ]

    if vip_channel_id:
        text_lines.append(f"• Canal VIP: <code>{vip_channel_id}</code> ✅")
    else:
        text_lines.append("• Canal VIP: ❌ No configurado")

    if free_channel_id:
        text_lines.append(f"• Canal FREE: <code>{free_channel_id}</code> ✅")
    else:
        text_lines.append("• Canal FREE: ❌ No configurado")

    text_lines.extend([
        "",
        "🛡️ <b>Niveles de Protección:</b>",
        "• <b>Standard:</b> Protección básica",
        "• <b>Protected:</b> Sin forwarding + logging",
        "• <b>Secured:</b> Sin forwarding/download + watermark",
        "• <b>Exclusive:</b> Máxima protección + screenshots",
        "",
        "📋 <b>Funciones Implementadas:</b>",
        "• publish_exclusive_content() - Publicación automática",
        "• apply_content_visibility_restriction() - Control de acceso",
        "• configure_content_protection() - Protección avanzada",
        "",
        "💡 <b>Próximamente:</b>",
        "Interface para crear y publicar contenido directamente"
    ])

    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_generate_report")
async def channel_generate_report(callback: CallbackQuery, session: AsyncSession):
    """Generate comprehensive channel reports."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    # Show loading message
    await callback.message.edit_text("📊 Generando reporte detallado...\n\n⏳ Esto puede tomar unos segundos.")

    channel_admin_service = ChannelAdminService(session)

    # Generate comprehensive report with financial metrics
    report_result = await channel_admin_service.generate_channel_analytics_report(
        period_days=30,
        report_type="comprehensive"
    )

    text_lines = [
        "📈 <b>Reporte Completo de Canales</b>",
        f"📅 <b>Período:</b> Últimos 30 días",
        f"🕐 <b>Generado:</b> {report_result.get('generated_at', 'N/A')[:16]}",
        ""
    ]

    if report_result.get("status") == "success":
        # Financial Summary
        financial_data = report_result.get("financial_metrics", {})
        if financial_data.get("success"):
            financial_metrics = financial_data["financial_metrics"]
            revenue_summary = financial_metrics.get("revenue_summary", {})
            user_metrics = financial_metrics.get("user_metrics", {})
            conversion_metrics = financial_metrics.get("conversion_metrics", {})

            text_lines.extend([
                "💰 <b>RESUMEN FINANCIERO:</b>",
                f"• Ingresos Totales: {revenue_summary.get('total_revenue', 0)} besitos",
                f"• Ingresos por Tokens: {revenue_summary.get('token_revenue', 0)} besitos",
                f"• Ingresos por Tienda: {revenue_summary.get('shop_revenue', 0)} besitos",
                f"• ARPU: {user_metrics.get('arpu', 0)} besitos/usuario",
                f"• Usuarios Pagadores: {user_metrics.get('unique_paying_users', 0)}",
                f"• Conversión Tokens: {conversion_metrics.get('token_conversion_rate', 0)}%",
                ""
            ])

            # Token breakdown
            token_metrics = financial_metrics.get("token_metrics", {})
            text_lines.extend([
                "🎫 <b>MÉTRICAS DE TOKENS:</b>",
                f"• Tokens Utilizados: {token_metrics.get('tokens_used', 0)}",
                f"• Precio Promedio: {token_metrics.get('average_token_price', 0)} besitos",
                ""
            ])

        # Engagement Summary
        engagement_data = report_result.get("all_channels_engagement", {})
        if engagement_data:
            vip_engagement = engagement_data.get("vip_channel", {})
            free_engagement = engagement_data.get("free_channel", {})

            text_lines.append("📊 <b>ENGAGEMENT:</b>")

            if vip_engagement and vip_engagement.get("success"):
                vip_summary = vip_engagement["analytics"]["engagement_summary"]
                vip_segmentation = vip_engagement["analytics"]["user_segmentation"]
                text_lines.extend([
                    f"• VIP - Reacciones: {vip_summary.get('total_reactions', 0)}",
                    f"• VIP - Usuarios: {vip_summary.get('unique_users', 0)}",
                    f"• VIP - Rate: {vip_segmentation.get('vip_engagement_rate', 0):.2f}"
                ])

            if free_engagement and free_engagement.get("success"):
                free_summary = free_engagement["analytics"]["engagement_summary"]
                text_lines.extend([
                    f"• FREE - Reacciones: {free_summary.get('total_reactions', 0)}",
                    f"• FREE - Usuarios: {free_summary.get('unique_users', 0)}"
                ])

            text_lines.append("")

        # Insights
        insights = report_result.get("summary_insights", {})
        if insights:
            highlights = insights.get("performance_highlights", [])
            improvements = insights.get("areas_for_improvement", [])

            if highlights:
                text_lines.extend(["✨ <b>PUNTOS DESTACADOS:</b>"])
                for highlight in highlights[:2]:
                    text_lines.append(f"• {highlight}")
                text_lines.append("")

            if improvements:
                text_lines.extend(["⚠️ <b>ÁREAS DE MEJORA:</b>"])
                for improvement in improvements[:2]:
                    text_lines.append(f"• {improvement}")
                text_lines.append("")

        # Projections
        financial_metrics = financial_data.get("financial_metrics", {}) if financial_data.get("success") else {}
        projections = financial_metrics.get("projections", {})
        if projections:
            next_30 = projections.get("30_days", {})
            text_lines.extend([
                "🔮 <b>PROYECCIÓN (30 días):</b>",
                f"• Ingresos Proyectados: {next_30.get('projected_total_revenue', 0)} besitos",
                f"• Confianza: {next_30.get('confidence_level', 'N/A')}",
                ""
            ])

    else:
        text_lines.extend([
            "❌ <b>Error al generar reporte:</b>",
            f"• {report_result.get('message', 'Error desconocido')}",
            ""
        ])

    text_lines.extend([
        "📋 <b>ACCIONES DISPONIBLES:</b>",
        "• Revisa Analytics para datos en tiempo real",
        "• Usa Ops. Masivas para ajustar acceso VIP",
        "• Configura Protección para contenido exclusivo"
    ])

    text = "\n".join(text_lines)

    await update_menu(
        callback,
        text,
        get_enhanced_channel_kb(),
        session,
        "admin_channel_enhanced"
    )
    await callback.answer()