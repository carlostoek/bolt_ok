"""
Comprehensive test suite for HTMLMessageFormatter

Tests cover all core functionality including:
- Admin menu formatting with various configurations
- Confirmation message formatting with different result types
- Error message formatting with recovery options
- Analytics summary formatting with multiple data types
- VIP status list formatting with various user states
- Automation status formatting for task tracking
- VIP expiration reminder formatting
- Edge cases and error handling
- HTML sanitization and security
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create mock pytest decorators for compatibility
    class MockPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

        @staticmethod
        def mark(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = MockPytest()

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the formatter and related modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock configuration before importing the formatter
with patch.dict(os.environ, {'BOT_TOKEN': 'test_token', 'ADMIN_IDS': '123;456'}):
    from utils.html_formatter import (
        HTMLMessageFormatter,
        format_admin_menu,
        format_confirmation_message,
        format_error_message,
        format_vip_expiration_reminder,
        format_automation_status
    )


class TestHTMLMessageFormatter(unittest.TestCase):
    """Test suite for HTMLMessageFormatter core functionality"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.formatter = HTMLMessageFormatter()

        # Sample menu data for testing
        self.sample_menu_data = {
            'title': 'Panel de Administración',
            'description': 'Gestión avanzada de canales y suscripciones',
            'stats': {
                'active_users': 1247,
                'vip_users': 89,
                'daily_messages': 543
            },
            'sections': [
                {
                    'title': 'Gestión de Usuarios',
                    'options': [
                        {'icon': '👑', 'text': 'Usuarios VIP'},
                        {'icon': '👥', 'text': 'Usuarios Free'},
                        {'icon': '📊', 'text': 'Estadísticas'}
                    ]
                },
                {
                    'title': 'Configuración',
                    'options': [
                        'Ajustes del Bot',
                        'Respaldos',
                        'Logs del Sistema'
                    ]
                }
            ]
        }

        # Sample user context
        self.sample_user_context = {
            'user_name': 'Admin Diana',
            'role': 'Super Admin',
            'last_action': 'Token generation'
        }

        # Sample VIP users data
        self.sample_vip_users = [
            {
                'name': 'Usuario Activo',
                'id': 12345,
                'expires_at': '2024-12-25',
                'days_remaining': 30
            },
            {
                'name': 'Usuario Por Expirar',
                'id': 67890,
                'expires_at': '2024-10-05',
                'days_remaining': 2
            },
            {
                'name': 'Usuario Crítico',
                'id': 11111,
                'expires_at': '2024-10-02',
                'days_remaining': 1
            }
        ]

    def test_format_admin_menu_complete(self):
        """Test complete admin menu formatting with all sections."""
        result = self.formatter.format_admin_menu(self.sample_menu_data, self.sample_user_context)

        # Check that all major components are present
        self.assertIn('<b>🛠️ Panel de Administración</b>', result)
        self.assertIn('<i>👋 Bienvenido, Admin Diana (Super Admin)</i>', result)
        self.assertIn('Gestión avanzada de canales y suscripciones', result)
        self.assertIn('<u>📊 Estadísticas Rápidas:</u>', result)
        self.assertIn('<b>Active Users:</b> <code>1247</code>', result)
        self.assertIn('<u>🔹 Gestión de Usuarios</u>', result)
        self.assertIn('<b>👑 Usuarios VIP</b>', result)
        self.assertIn('<i>⏰ Actualizado:', result)

    def test_format_admin_menu_minimal(self):
        """Test admin menu formatting with minimal data."""
        minimal_data = {'title': 'Simple Menu'}
        result = self.formatter.format_admin_menu(minimal_data)

        self.assertIn('<b>🛠️ Simple Menu</b>', result)
        self.assertIn('<i>⏰ Actualizado:', result)
        self.assertNotIn('Estadísticas Rápidas', result)

    def test_format_admin_menu_no_user_context(self):
        """Test admin menu formatting without user context."""
        result = self.formatter.format_admin_menu(self.sample_menu_data)

        self.assertIn('<b>🛠️ Panel de Administración</b>', result)
        self.assertNotIn('Bienvenido', result)
        self.assertIn('Gestión avanzada de canales y suscripciones', result)

    def test_format_admin_menu_empty_stats(self):
        """Test admin menu formatting with empty stats."""
        data_no_stats = self.sample_menu_data.copy()
        data_no_stats['stats'] = {}
        result = self.formatter.format_admin_menu(data_no_stats)

        self.assertNotIn('Estadísticas Rápidas', result)
        self.assertIn('<b>🛠️ Panel de Administración</b>', result)

    @patch('utils.html_formatter.logger')
    def test_format_admin_menu_error_handling(self, mock_logger):
        """Test admin menu formatting error handling."""
        # Test with data that would actually cause an exception
        with patch('utils.html_formatter.sanitize_text') as mock_sanitize:
            mock_sanitize.side_effect = Exception("Test error")
            result = self.formatter.format_admin_menu({'title': 'test'})

            # Should return error message
            self.assertIn('<b>⚠️ Error de Formato</b>', result)

    def test_format_confirmation_message_boolean_success(self):
        """Test confirmation message with boolean success result."""
        result = self.formatter.format_confirmation_message(
            'Crear token VIP', True, True, {'token_count': 5}
        )

        self.assertIn('<b>✅ Acción Completada</b>', result)
        self.assertIn('<code>Crear token VIP</code>', result)
        self.assertIn('<b>Token Count:</b> <code>5</code>', result)
        self.assertIn('Este mensaje se eliminará automáticamente', result)

    def test_format_confirmation_message_boolean_failure(self):
        """Test confirmation message with boolean failure result."""
        result = self.formatter.format_confirmation_message(
            'Eliminar usuario', False, False
        )

        self.assertIn('<b>❌ Acción Fallida</b>', result)
        self.assertIn('<code>Eliminar usuario</code>', result)
        self.assertNotIn('Este mensaje se eliminará', result)

    def test_format_confirmation_message_string_result(self):
        """Test confirmation message with string result."""
        result = self.formatter.format_confirmation_message(
            'Generar reporte', 'Reporte generado exitosamente'
        )

        self.assertIn('<b>📋 Resultado de Acción</b>', result)
        self.assertIn('<code>Generar reporte</code>', result)
        self.assertIn('Reporte generado exitosamente', result)

    def test_format_confirmation_message_numeric_result(self):
        """Test confirmation message with numeric result."""
        result = self.formatter.format_confirmation_message(
            'Contar usuarios', 1247
        )

        self.assertIn('<b>📋 Resultado de Acción</b>', result)
        self.assertIn('<b>Resultado:</b> <code>1247</code>', result)

    def test_format_confirmation_message_dict_result(self):
        """Test confirmation message with dictionary result."""
        dict_result = {
            'users_created': 5,
            'tokens_generated': 10,
            'revenue_estimated': 150.50
        }
        result = self.formatter.format_confirmation_message(
            'Operación batch', dict_result
        )

        self.assertIn('<u>📊 Detalles:</u>', result)
        self.assertIn('<b>Users Created:</b> <code>5</code>', result)
        self.assertIn('<b>Tokens Generated:</b> <code>10</code>', result)
        self.assertIn('<b>Revenue Estimated:</b> <code>150.5</code>', result)

    @patch('utils.html_formatter.logger')
    def test_format_confirmation_message_error_handling(self, mock_logger):
        """Test confirmation message error handling."""
        # Force an exception by patching datetime
        with patch('utils.html_formatter.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Test error")
            result = self.formatter.format_confirmation_message('test', True)

            self.assertIn('<b>✅ Acción completada</b>', result)
            self.assertIn('<i>test</i>', result)

    def test_format_error_message_with_recovery_options(self):
        """Test error message formatting with recovery options."""
        recovery_options = [
            'Verificar conexión a la base de datos',
            'Reiniciar el servicio de tokens',
            'Contactar al administrador del sistema'
        ]
        result = self.formatter.format_error_message(
            'DB_CONNECTION_FAILED',
            'No se pudo conectar a la base de datos principal',
            recovery_options
        )

        self.assertIn('<b>🚨 Error Administrativo</b>', result)
        self.assertIn('<code>DB_CONNECTION_FAILED</code>', result)
        self.assertIn('No se pudo conectar a la base de datos principal', result)
        self.assertIn('<u>🔧 Opciones de Recuperación:</u>', result)
        self.assertIn('1. <b>Verificar conexión a la base de datos</b>', result)
        self.assertIn('2. <b>Reiniciar el servicio de tokens</b>', result)

    def test_format_error_message_without_recovery_options(self):
        """Test error message formatting without recovery options."""
        result = self.formatter.format_error_message(
            'UNKNOWN_ERROR',
            'Error inesperado en el sistema'
        )

        self.assertIn('<b>🚨 Error Administrativo</b>', result)
        self.assertIn('<u>🔧 Acciones Sugeridas:</u>', result)
        self.assertIn('1. <b>Verificar conexión del bot</b>', result)
        self.assertIn('2. <b>Reintentar la operación</b>', result)
        self.assertIn('3. <b>Contactar soporte técnico</b>', result)

    @patch('utils.html_formatter.logger')
    def test_format_error_message_error_handling(self, mock_logger):
        """Test error message formatting error handling."""
        with patch('utils.html_formatter.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Test error")
            result = self.formatter.format_error_message('TEST', 'details')

            self.assertIn('<b>🚨 Error del Sistema</b>', result)
            self.assertIn('<code>TEST</code>', result)

    def test_format_analytics_summary_complete(self):
        """Test analytics summary formatting with complete data."""
        analytics_data = {
            'metrics': {
                'daily_active_users': 1205,
                'message_volume': 8432,
                'bot_uptime': '99.8%'
            },
            'revenue': {
                'daily': 145.50,
                'weekly': 980.25,
                'monthly': 4200.00
            },
            'engagement': {
                'avg_session_duration': '12.5 min',
                'bounce_rate': '15%',
                'conversion_rate': '8.2%'
            }
        }
        result = self.formatter.format_analytics_summary(analytics_data)

        self.assertIn('<b>📊 Panel de Analíticas</b>', result)
        self.assertIn('<u>📈 Métricas Clave:</u>', result)
        self.assertIn('<b>Daily Active Users:</b> <code>1205</code>', result)
        self.assertIn('<u>💰 Ingresos:</u>', result)
        self.assertIn('<b>Daily:</b> <code>$145.5</code>', result)
        self.assertIn('<u>👥 Participación de Usuarios:</u>', result)
        self.assertIn('<b>Avg Session Duration:</b> <code>12.5 min</code>', result)

    def test_format_analytics_summary_partial(self):
        """Test analytics summary formatting with partial data."""
        partial_data = {
            'metrics': {
                'users': 100
            }
        }
        result = self.formatter.format_analytics_summary(partial_data)

        self.assertIn('<b>📊 Panel de Analíticas</b>', result)
        self.assertIn('<u>📈 Métricas Clave:</u>', result)
        self.assertNotIn('Ingresos', result)
        self.assertNotIn('Participación', result)

    @patch('utils.html_formatter.logger')
    def test_format_analytics_summary_error_handling(self, mock_logger):
        """Test analytics summary error handling."""
        with patch('utils.html_formatter.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Test error")
            result = self.formatter.format_analytics_summary({})

            self.assertIn('<b>📊 Analíticas</b>', result)
            self.assertIn('No se pudieron cargar los datos', result)

    def test_format_vip_status_list_complete(self):
        """Test VIP status list formatting with multiple users."""
        result = self.formatter.format_vip_status_list(self.sample_vip_users)

        self.assertIn('<b>👑 Estado de Usuarios VIP</b>', result)
        self.assertIn('<u>📋 Total de usuarios VIP: 3</u>', result)
        self.assertIn('🟢 <b>Usuario Activo</b> (ID: <code>12345</code>)', result)
        self.assertIn('🟡 <b>Usuario Por Expirar</b>', result)
        self.assertIn('🔴 <b>Usuario Crítico</b>', result)
        self.assertIn('<u>📊 Resumen:</u>', result)
        self.assertIn('<b>Activos:</b> <code>2</code>', result)
        self.assertIn('<b>Por expirar (≤3 días):</b> <code>2</code>', result)

    def test_format_vip_status_list_empty(self):
        """Test VIP status list formatting with no users."""
        result = self.formatter.format_vip_status_list([])

        self.assertIn('<b>👑 Estado de Usuarios VIP</b>', result)
        self.assertIn('No hay usuarios VIP activos actualmente', result)

    def test_format_vip_status_list_status_indicators(self):
        """Test VIP status list status indicator logic."""
        test_users = [
            {'name': 'Expired', 'id': 1, 'expires_at': '2024-10-01', 'days_remaining': 0},
            {'name': 'Critical', 'id': 2, 'expires_at': '2024-10-02', 'days_remaining': 1},
            {'name': 'Warning', 'id': 3, 'expires_at': '2024-10-04', 'days_remaining': 3},
            {'name': 'Active', 'id': 4, 'expires_at': '2024-11-01', 'days_remaining': 30}
        ]
        result = self.formatter.format_vip_status_list(test_users)

        self.assertIn('🔴 <b>Expired</b>', result)
        self.assertIn('🔴 <b>Critical</b>', result)
        self.assertIn('🟡 <b>Warning</b>', result)
        self.assertIn('🟢 <b>Active</b>', result)

    @patch('utils.html_formatter.logger')
    def test_format_vip_status_list_error_handling(self, mock_logger):
        """Test VIP status list error handling."""
        # Force an error by making sanitize_text fail
        with patch('utils.html_formatter.sanitize_text') as mock_sanitize:
            mock_sanitize.side_effect = Exception("Test error")
            result = self.formatter.format_vip_status_list([{'name': 'test'}])

            self.assertIn('<b>👑 Estado de Usuarios VIP</b>', result)
            self.assertIn('Error al cargar la lista', result)

    def test_convenience_functions(self):
        """Test convenience functions are working properly."""
        # Test format_admin_menu convenience function
        result = format_admin_menu(self.sample_menu_data)
        self.assertIn('<b>🛠️ Panel de Administración</b>', result)

        # Test format_confirmation_message convenience function
        result = format_confirmation_message('test action', True)
        self.assertIn('<b>✅ Acción Completada</b>', result)

        # Test format_error_message convenience function
        result = format_error_message('TEST_ERROR', 'Test details')
        self.assertIn('<b>🚨 Error Administrativo</b>', result)

    def test_format_vip_expiration_reminder_urgent(self):
        """Test VIP expiration reminder formatting for urgent cases."""
        expiration_date = datetime.now() + timedelta(days=1)
        result = format_vip_expiration_reminder(1, 'Diana Usuario', expiration_date)

        self.assertIn('<b>🚨 URGENTE - Suscripción VIP</b>', result)
        self.assertIn('Hola <b>Diana Usuario</b>', result)
        self.assertIn('expira en <b>1 día</b>', result)
        self.assertIn('<u>💎 Beneficios VIP que perderás:</u>', result)
        self.assertIn('Acceso a contenido exclusivo', result)

    def test_format_vip_expiration_reminder_warning(self):
        """Test VIP expiration reminder formatting for warning cases."""
        expiration_date = datetime.now() + timedelta(days=3)
        result = format_vip_expiration_reminder(3, 'Test User', expiration_date)

        self.assertIn('<b>⚠️ Importante - Suscripción VIP</b>', result)
        self.assertIn('expira en <b>3 días</b>', result)

    def test_format_vip_expiration_reminder_normal(self):
        """Test VIP expiration reminder formatting for normal cases."""
        expiration_date = datetime.now() + timedelta(days=7)
        result = format_vip_expiration_reminder(7, 'Test User', expiration_date)

        self.assertIn('<b>💎 Recordatorio - Suscripción VIP</b>', result)

    @patch('utils.html_formatter.logger')
    def test_format_vip_expiration_reminder_error_handling(self, mock_logger):
        """Test VIP expiration reminder error handling."""
        with patch('utils.html_formatter.sanitize_text') as mock_sanitize:
            mock_sanitize.side_effect = Exception("Test error")
            result = format_vip_expiration_reminder(5, 'User', datetime.now())

            self.assertIn('Tu suscripción VIP expira en 5 días', result)

    def test_format_automation_status_started(self):
        """Test automation status formatting for started tasks."""
        details = {
            'task_breakdown': {
                'vip_reminders': True,
                'cleanup_old_messages': True,
                'sync_user_permissions': False
            },
            'intervals': {
                'vip_reminders': 'cada 6 horas',
                'cleanup_old_messages': 'cada 24 horas'
            }
        }
        result = format_automation_status('started', 2, 3, details)

        self.assertIn('<b>✅ Automatización Iniciada</b>', result)
        self.assertIn('2/3 tareas afectadas (67%)', result)
        self.assertIn('<u>📋 Detalle de Tareas:</u>', result)
        self.assertIn('✅ <b>Vip Reminders</b>', result)
        self.assertIn('❌ <b>Sync User Permissions</b>', result)
        self.assertIn('<u>⏱️ Intervalos de Ejecución:</u>', result)

    def test_format_automation_status_stopped(self):
        """Test automation status formatting for stopped tasks."""
        result = format_automation_status('stopped', 5, 5)

        self.assertIn('<b>⏹️ Automatización Detenida</b>', result)
        self.assertIn('5/5 tareas afectadas (100%)', result)

    def test_format_automation_status_custom_action(self):
        """Test automation status formatting for custom actions."""
        result = format_automation_status('restarted', 3, 4)

        self.assertIn('<b>🤖 Restarted</b>', result)
        self.assertIn('3/4 tareas afectadas (75%)', result)

    @patch('utils.html_formatter.logger')
    def test_format_automation_status_error_handling(self, mock_logger):
        """Test automation status error handling."""
        with patch('utils.html_formatter.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Test error")
            result = format_automation_status('test', 1, 2)

            self.assertIn('<b>🤖 Automatización</b>', result)
            self.assertIn('1/2 tareas procesadas', result)

    def test_text_sanitization(self):
        """Test that HTML text is properly sanitized."""
        # Test menu with special characters
        menu_with_special_chars = {
            'title': 'Menu <script>alert("xss")</script>',
            'description': 'Test & validation'
        }

        with patch('utils.html_formatter.sanitize_text') as mock_sanitize:
            mock_sanitize.side_effect = lambda x: x.replace('<script>', '').replace('</script>', '').replace('&', '&amp;')
            result = self.formatter.format_admin_menu(menu_with_special_chars)

            # Verify sanitization was called
            self.assertTrue(mock_sanitize.called)

    def test_edge_cases_empty_data(self):
        """Test edge cases with empty or minimal data."""
        # Empty menu data
        result = self.formatter.format_admin_menu({})
        self.assertIn('<i>⏰ Actualizado:', result)

        # Empty analytics data
        result = self.formatter.format_analytics_summary({})
        self.assertIn('<b>📊 Panel de Analíticas</b>', result)

        # None values
        result = self.formatter.format_confirmation_message('', None)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_html_tag_formatting(self):
        """Test proper HTML tag usage in formatting."""
        result = self.formatter.format_admin_menu(self.sample_menu_data, self.sample_user_context)

        # Check for proper HTML tags
        self.assertIn('<b>', result)
        self.assertIn('</b>', result)
        self.assertIn('<i>', result)
        self.assertIn('</i>', result)
        self.assertIn('<u>', result)
        self.assertIn('</u>', result)
        self.assertIn('<code>', result)
        self.assertIn('</code>', result)

        # Ensure no markdown syntax
        self.assertNotIn('**', result)
        self.assertNotIn('*', result.replace('•', ''))  # Exclude bullet points
        self.assertNotIn('```', result)

    @patch('utils.html_formatter.datetime')
    def test_timestamp_formatting(self, mock_datetime):
        """Test timestamp formatting in messages."""
        mock_now = datetime(2024, 10, 1, 14, 30, 45)
        mock_datetime.now.return_value = mock_now

        result = self.formatter.format_admin_menu({'title': 'Test'})
        self.assertIn('14:30', result)

        result = self.formatter.format_confirmation_message('test', True)
        self.assertIn('14:30:45', result)


# Additional test runner for standalone execution
if __name__ == '__main__':
    # Setup test discovery
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHTMLMessageFormatter)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")