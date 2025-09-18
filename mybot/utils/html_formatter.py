"""
HTML Message Formatter Utility for Enhanced Admin Interface.

This module provides HTML-formatted messaging functions for DianaBot's
Channel Administration Module to improve text rendering and user experience.
Implements HTML formatting for admin menus, confirmations, and error messages
instead of Markdown for enhanced administrative interfaces.
"""

from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class HTMLMessageFormatter:
    """
    HTML message formatter for administrative interfaces.
    Provides enhanced text rendering using HTML tags for improved readability
    and user experience in admin menus and system messages.
    """

    @staticmethod
    def format_admin_menu(menu_data: Dict[str, Any], user_context: Optional[Dict] = None) -> str:
        """
        Format administrative menu data using HTML tags for enhanced display.

        Args:
            menu_data: Dictionary containing menu information
                - title: Main menu title
                - description: Optional menu description
                - sections: List of menu sections with options
                - stats: Optional statistics to display
            user_context: Optional user information for personalization
                - user_name: Admin user name
                - role: Admin role
                - last_action: Last administrative action

        Returns:
            HTML-formatted menu string with proper styling
        """
        try:
            formatted_text = []

            # Main title with bold formatting
            if 'title' in menu_data:
                title = sanitize_text(menu_data['title'])
                formatted_text.append(f"<b>🛠️ {title}</b>\n")

            # User context information
            if user_context and 'user_name' in user_context:
                user_name = sanitize_text(user_context['user_name'])
                role = user_context.get('role', 'Admin')
                formatted_text.append(f"<i>👋 Bienvenido, {user_name} ({role})</i>\n")

            # Menu description
            if 'description' in menu_data:
                description = sanitize_text(menu_data['description'])
                formatted_text.append(f"{description}\n")

            # Statistics section if available
            if 'stats' in menu_data and menu_data['stats']:
                formatted_text.append("\n<u>📊 Estadísticas Rápidas:</u>")
                stats = menu_data['stats']
                for key, value in stats.items():
                    label = sanitize_text(str(key).replace('_', ' ').title())
                    formatted_text.append(f"• <b>{label}:</b> <code>{value}</code>")
                formatted_text.append("")

            # Menu sections
            if 'sections' in menu_data:
                for section in menu_data['sections']:
                    if 'title' in section:
                        section_title = sanitize_text(section['title'])
                        formatted_text.append(f"\n<u>🔹 {section_title}</u>")

                    if 'options' in section:
                        for option in section['options']:
                            if isinstance(option, dict):
                                icon = option.get('icon', '•')
                                text = sanitize_text(option.get('text', ''))
                                formatted_text.append(f"• <b>{icon} {text}</b>")
                            else:
                                option_text = sanitize_text(str(option))
                                formatted_text.append(f"• <b>{option_text}</b>")

            # Footer with timestamp
            timestamp = datetime.now().strftime("%H:%M")
            formatted_text.append(f"\n<i>⏰ Actualizado: {timestamp}</i>")

            return "\n".join(formatted_text)

        except Exception as e:
            logger.error(f"Error formatting admin menu: {e}")
            return "<b>⚠️ Error de Formato</b>\n\nNo se pudo cargar el menú administrativo."

    @staticmethod
    def format_confirmation_message(
        action: str,
        result: Any,
        auto_delete: bool = True,
        details: Optional[Dict] = None
    ) -> str:
        """
        Format confirmation message for administrative actions.

        Args:
            action: The action that was performed
            result: The result of the action (success/failure/data)
            auto_delete: Whether message should auto-delete
            details: Optional additional details to display

        Returns:
            HTML-formatted confirmation message
        """
        try:
            formatted_text = []

            # Success or failure icon and main message
            if isinstance(result, bool):
                if result:
                    formatted_text.append("<b>✅ Acción Completada</b>\n")
                    formatted_text.append(f"<i>Se ejecutó correctamente:</i> <code>{sanitize_text(action)}</code>")
                else:
                    formatted_text.append("<b>❌ Acción Fallida</b>\n")
                    formatted_text.append(f"<i>No se pudo ejecutar:</i> <code>{sanitize_text(action)}</code>")
            else:
                # Result contains data
                formatted_text.append("<b>📋 Resultado de Acción</b>\n")
                formatted_text.append(f"<i>Acción:</i> <code>{sanitize_text(action)}</code>")

                if isinstance(result, (int, float)):
                    formatted_text.append(f"<b>Resultado:</b> <code>{result}</code>")
                elif isinstance(result, str):
                    formatted_text.append(f"<b>Resultado:</b> {sanitize_text(result)}")
                elif isinstance(result, dict):
                    formatted_text.append("\n<u>📊 Detalles:</u>")
                    for key, value in result.items():
                        key_text = sanitize_text(str(key).replace('_', ' ').title())
                        formatted_text.append(f"• <b>{key_text}:</b> <code>{value}</code>")

            # Additional details
            if details:
                formatted_text.append("\n<u>ℹ️ Información Adicional:</u>")
                for key, value in details.items():
                    key_text = sanitize_text(str(key).replace('_', ' ').title())
                    formatted_text.append(f"• <b>{key_text}:</b> <code>{value}</code>")

            # Auto-delete notice
            if auto_delete:
                formatted_text.append("\n<i>🕐 Este mensaje se eliminará automáticamente en 7 segundos</i>")

            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_text.append(f"\n<i>⏰ {timestamp}</i>")

            return "\n".join(formatted_text)

        except Exception as e:
            logger.error(f"Error formatting confirmation message: {e}")
            return f"<b>✅ Acción completada</b>\n<i>{sanitize_text(action)}</i>"

    @staticmethod
    def format_error_message(
        error_code: str,
        details: str,
        recovery_options: Optional[List[str]] = None
    ) -> str:
        """
        Format error message with HTML styling for admin interfaces.

        Args:
            error_code: Error code identifier
            details: Error details and description
            recovery_options: List of suggested recovery actions

        Returns:
            HTML-formatted error message with recovery options
        """
        try:
            formatted_text = []

            # Error header
            formatted_text.append("<b>🚨 Error Administrativo</b>\n")

            # Error code
            error_code_clean = sanitize_text(error_code)
            formatted_text.append(f"<b>Código:</b> <code>{error_code_clean}</code>")

            # Error details
            details_clean = sanitize_text(details)
            formatted_text.append(f"<b>Detalles:</b> <i>{details_clean}</i>")

            # Recovery options
            if recovery_options:
                formatted_text.append("\n<u>🔧 Opciones de Recuperación:</u>")
                for i, option in enumerate(recovery_options, 1):
                    option_clean = sanitize_text(option)
                    formatted_text.append(f"{i}. <b>{option_clean}</b>")
            else:
                formatted_text.append("\n<u>🔧 Acciones Sugeridas:</u>")
                formatted_text.append("1. <b>Verificar conexión del bot</b>")
                formatted_text.append("2. <b>Reintentar la operación</b>")
                formatted_text.append("3. <b>Contactar soporte técnico</b>")

            # Support information
            formatted_text.append("\n<i>💡 Si el problema persiste, revisa los logs del sistema o contacta al desarrollador.</i>")

            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_text.append(f"\n<i>⏰ Error registrado: {timestamp}</i>")

            return "\n".join(formatted_text)

        except Exception as e:
            logger.error(f"Error formatting error message: {e}")
            return f"<b>🚨 Error del Sistema</b>\n<code>{error_code}</code>\n<i>{details}</i>"

    @staticmethod
    def format_analytics_summary(analytics_data: Dict[str, Any]) -> str:
        """
        Format analytics data for admin dashboard display.

        Args:
            analytics_data: Dictionary containing analytics metrics

        Returns:
            HTML-formatted analytics summary
        """
        try:
            formatted_text = []

            # Analytics header
            formatted_text.append("<b>📊 Panel de Analíticas</b>\n")

            # Key metrics section
            if 'metrics' in analytics_data:
                formatted_text.append("<u>📈 Métricas Clave:</u>")
                metrics = analytics_data['metrics']
                for metric_name, metric_value in metrics.items():
                    name_clean = sanitize_text(str(metric_name).replace('_', ' ').title())
                    formatted_text.append(f"• <b>{name_clean}:</b> <code>{metric_value}</code>")
                formatted_text.append("")

            # Revenue section
            if 'revenue' in analytics_data:
                formatted_text.append("<u>💰 Ingresos:</u>")
                revenue_data = analytics_data['revenue']
                for period, amount in revenue_data.items():
                    period_clean = sanitize_text(str(period).replace('_', ' ').title())
                    formatted_text.append(f"• <b>{period_clean}:</b> <code>${amount}</code>")
                formatted_text.append("")

            # User engagement
            if 'engagement' in analytics_data:
                formatted_text.append("<u>👥 Participación de Usuarios:</u>")
                engagement = analytics_data['engagement']
                for key, value in engagement.items():
                    key_clean = sanitize_text(str(key).replace('_', ' ').title())
                    formatted_text.append(f"• <b>{key_clean}:</b> <code>{value}</code>")

            # Update timestamp
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            formatted_text.append(f"\n<i>🕐 Última actualización: {timestamp}</i>")

            return "\n".join(formatted_text)

        except Exception as e:
            logger.error(f"Error formatting analytics summary: {e}")
            return "<b>📊 Analíticas</b>\n<i>No se pudieron cargar los datos.</i>"

    @staticmethod
    def format_vip_status_list(vip_users: List[Dict[str, Any]]) -> str:
        """
        Format VIP users status list for admin display.

        Args:
            vip_users: List of VIP user data dictionaries

        Returns:
            HTML-formatted VIP users list
        """
        try:
            formatted_text = []

            # Header
            formatted_text.append("<b>👑 Estado de Usuarios VIP</b>\n")

            if not vip_users:
                formatted_text.append("<i>No hay usuarios VIP activos actualmente.</i>")
                return "\n".join(formatted_text)

            # VIP users list
            formatted_text.append(f"<u>📋 Total de usuarios VIP: {len(vip_users)}</u>\n")

            for user in vip_users:
                user_name = sanitize_text(user.get('name', 'Usuario'))
                user_id = user.get('id', 'N/A')
                expires_at = user.get('expires_at', 'N/A')
                days_remaining = user.get('days_remaining', 0)

                # Status indicator
                if days_remaining <= 1:
                    status_icon = "🔴"
                elif days_remaining <= 3:
                    status_icon = "🟡"
                else:
                    status_icon = "🟢"

                formatted_text.append(f"{status_icon} <b>{user_name}</b> (ID: <code>{user_id}</code>)")
                formatted_text.append(f"   └ <i>Expira:</i> <code>{expires_at}</code> ({days_remaining} días)")
                formatted_text.append("")

            # Summary
            active_count = len([u for u in vip_users if u.get('days_remaining', 0) > 1])
            expiring_count = len([u for u in vip_users if u.get('days_remaining', 0) <= 3])

            formatted_text.append("<u>📊 Resumen:</u>")
            formatted_text.append(f"• <b>Activos:</b> <code>{active_count}</code>")
            formatted_text.append(f"• <b>Por expirar (≤3 días):</b> <code>{expiring_count}</code>")

            return "\n".join(formatted_text)

        except Exception as e:
            logger.error(f"Error formatting VIP status list: {e}")
            return "<b>👑 Estado de Usuarios VIP</b>\n<i>Error al cargar la lista.</i>"


# Convenience functions for backward compatibility
def format_admin_menu(menu_data: Dict[str, Any], user_context: Optional[Dict] = None) -> str:
    """Convenience function for formatting admin menus."""
    return HTMLMessageFormatter.format_admin_menu(menu_data, user_context)


def format_confirmation_message(
    action: str,
    result: Any,
    auto_delete: bool = True,
    details: Optional[Dict] = None
) -> str:
    """Convenience function for formatting confirmation messages."""
    return HTMLMessageFormatter.format_confirmation_message(action, result, auto_delete, details)


def format_error_message(
    error_code: str,
    details: str,
    recovery_options: Optional[List[str]] = None
) -> str:
    """Convenience function for formatting error messages."""
    return HTMLMessageFormatter.format_error_message(error_code, details, recovery_options)


# Additional methods for automation handlers

def format_vip_expiration_reminder(
    days_remaining: int,
    user_name: str,
    expiration_date: datetime
) -> str:
    """Format VIP expiration reminder message."""
    try:
        formatted_text = []

        # Urgency indicator
        if days_remaining == 1:
            urgency_icon = "🚨"
            urgency_text = "URGENTE"
        elif days_remaining <= 3:
            urgency_icon = "⚠️"
            urgency_text = "Importante"
        else:
            urgency_icon = "💎"
            urgency_text = "Recordatorio"

        formatted_text.append(f"<b>{urgency_icon} {urgency_text} - Suscripción VIP</b>\n")

        # Personalized greeting
        user_name_clean = sanitize_text(user_name)
        formatted_text.append(f"Hola <b>{user_name_clean}</b>,\n")

        # Expiration notice
        days_text = "día" if days_remaining == 1 else "días"
        formatted_text.append(f"Tu suscripción VIP expira en <b>{days_remaining} {days_text}</b>.")

        # Expiration date
        expiration_str = expiration_date.strftime("%d/%m/%Y")
        formatted_text.append(f"📅 <b>Fecha de expiración:</b> <code>{expiration_str}</code>\n")

        # Benefits reminder
        formatted_text.append("<u>💎 Beneficios VIP que perderás:</u>")
        formatted_text.append("• Acceso a contenido exclusivo")
        formatted_text.append("• Fragmentos narrativos premium")
        formatted_text.append("• Interacciones especiales con Diana")
        formatted_text.append("• Tienda VIP con artículos únicos\n")

        # Call to action
        formatted_text.append("<b>🔄 ¡Renueva ahora!</b>")
        formatted_text.append("Usa <code>/vip</code> para renovar tu suscripción y mantener todos tus beneficios.")

        return "\n".join(formatted_text)

    except Exception as e:
        logger.error(f"Error formatting VIP reminder: {e}")
        return f"⚠️ Tu suscripción VIP expira en {days_remaining} días. Usa /vip para renovar."


def format_automation_status(
    action: str,
    started_tasks: int,
    total_tasks: int,
    details: Optional[Dict] = None
) -> str:
    """Format automation task status message."""
    try:
        formatted_text = []

        # Action header
        if action == "started":
            formatted_text.append("<b>✅ Automatización Iniciada</b>\n")
        elif action == "stopped":
            formatted_text.append("<b>⏹️ Automatización Detenida</b>\n")
        else:
            formatted_text.append(f"<b>🤖 {sanitize_text(action.title())}</b>\n")

        # Success rate
        success_rate = (started_tasks / total_tasks * 100) if total_tasks > 0 else 0
        formatted_text.append(f"<b>Estado:</b> {started_tasks}/{total_tasks} tareas afectadas ({success_rate:.0f}%)")

        # Task breakdown if provided
        if details and 'task_breakdown' in details:
            formatted_text.append("\n<u>📋 Detalle de Tareas:</u>")
            for task_name, status in details['task_breakdown'].items():
                task_clean = sanitize_text(task_name.replace('_', ' ').title())
                status_icon = "✅" if status else "❌"
                formatted_text.append(f"• {status_icon} <b>{task_clean}</b>")

        # Additional details
        if details and 'intervals' in details:
            formatted_text.append("\n<u>⏱️ Intervalos de Ejecución:</u>")
            for task, interval in details['intervals'].items():
                task_clean = sanitize_text(task.replace('_', ' ').title())
                formatted_text.append(f"• <b>{task_clean}:</b> <code>{interval}</code>")

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text.append(f"\n<i>🕐 {timestamp}</i>")

        return "\n".join(formatted_text)

    except Exception as e:
        logger.error(f"Error formatting automation status: {e}")
        return f"<b>🤖 Automatización</b>\n{started_tasks}/{total_tasks} tareas procesadas."