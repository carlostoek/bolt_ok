"""
Tests for the Reaction System.
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import sys
import os

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.mission_service import MissionService
from services.point_service import PointService


class TestReactionSystem(unittest.TestCase):
    """Test cases for the reaction system with inline and native reactions."""
    
    def setUp(self):
        """Set up test environment."""
        self.session_mock = MagicMock()
        self.coordinador = CoordinadorCentral(self.session_mock)
        
        # Setup mocks for internal services
        self.coordinador.mission_service = MagicMock(spec=MissionService)
        self.coordinador.mission_service.check_and_complete_missions = AsyncMock(
            return_value={
                "success": True,
                "missions_completed": [
                    {"id": "test_mission", "name": "Test Mission", "points": 20}
                ],
                "total_mission_points": 20
            }
        )
        
        self.coordinador.point_service = MagicMock(spec=PointService)
        self.coordinador.point_service.award_points = AsyncMock(
            return_value={
                "success": True,
                "points_awarded": 10,
                "total_points": 100
            }
        )
        self.coordinador.point_service.get_user_points = AsyncMock(return_value=100)
        
        # Mock narrative service
        self.coordinador.narrative_service = MagicMock()
        self.coordinador.narrative_service.get_user_current_fragment = AsyncMock(return_value=None)
        
        # Message service mock
        self.message_service_mock = MagicMock()
        self.message_service_mock.update_reaction_markup = AsyncMock()
        
        # Bot mock
        self.bot_mock = MagicMock()
        
        # Notification service mock
        self.notification_service_mock = MagicMock()
        self.notification_service_mock.add_notification = AsyncMock()
        self.notification_service_mock.send_unified_notification = AsyncMock()
        
    def tearDown(self):
        """Clean up after tests."""
        pass
        
    def test_reaction_inline_vs_native_params(self):
        """Test the parameters for inline vs native reactions."""
        # Verify inline reaction is defined
        self.assertTrue(hasattr(AccionUsuario, 'REACCIONAR_PUBLICACION_INLINE'))
        self.assertEqual(AccionUsuario.REACCIONAR_PUBLICACION_INLINE.value, "reaccionar_publicacion_inline")
        
        # Verify native reaction is defined
        self.assertTrue(hasattr(AccionUsuario, 'REACCIONAR_PUBLICACION_NATIVA'))
        self.assertEqual(AccionUsuario.REACCIONAR_PUBLICACION_NATIVA.value, "reaccionar_publicacion_nativa")
        
    async def _test_inline_reaction(self):
        """Test inline reaction (button) flow."""
        with patch('services.message_service.MessageService', return_value=self.message_service_mock):
            with patch('services.notification_service.NotificationService', return_value=self.notification_service_mock):
                result = await self.coordinador.ejecutar_flujo(
                    user_id=123,
                    accion=AccionUsuario.REACCIONAR_PUBLICACION_INLINE,
                    message_id=456,
                    channel_id=789,
                    reaction_type="👍",
                    bot=self.bot_mock
                )
                
                # Verify result structure
                self.assertTrue(result["success"])
                self.assertEqual(result["points_awarded"], 0)  # No direct points
                self.assertGreater(result["mission_points_awarded"], 0)  # Mission points
                self.assertEqual(result["action"], "reaction_inline_success")
                
                # Verify method calls
                self.coordinador.mission_service.check_and_complete_missions.assert_called_once()
                self.message_service_mock.update_reaction_markup.assert_called_once()
                
    async def _test_native_reaction(self):
        """Test native reaction flow."""
        with patch('services.notification_service.NotificationService', return_value=self.notification_service_mock):
            result = await self.coordinador.ejecutar_flujo(
                user_id=123,
                accion=AccionUsuario.REACCIONAR_PUBLICACION_NATIVA,
                message_id=456,
                channel_id=789,
                reaction_type="👍",
                bot=self.bot_mock,
                points_to_award=10
            )
                
            # Verify result structure
            self.assertTrue(result["success"])
            self.assertEqual(result["points_awarded"], 10)  # Direct points
            self.assertEqual(len(result["missions_completed"]), 0)  # No missions
            self.assertEqual(result["action"], "reaction_native_success")
                
            # Verify method calls
            self.coordinador.point_service.award_points.assert_called_once()
                
    def test_reactions(self):
        """Run both reaction tests."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_inline_reaction())
        loop.run_until_complete(self._test_native_reaction())
    
    async def _test_send_unified_notification(self):
        """Test the unified notification function for reactions."""
        from services.notification_service import NotificationService
        
        # Create a notification service instance
        notification_service = NotificationService(self.session_mock, self.bot_mock)
        
        # Test data for inline reaction
        inline_data = {
            'reaction_type': '👍',
            'is_native': False,
            'missions_completed': [
                {'name': 'Test Mission', 'points': 20}
            ],
            'mission_points_awarded': 20,
        }
        
        # Test data for native reaction
        native_data = {
            'reaction_type': '👍',
            'is_native': True,
            'points_awarded': 10,
            'total_points': 100,
        }
        
        # Mock safe_send_message to avoid actual sending
        with patch('services.notification_service.safe_send_message', new_callable=AsyncMock) as mock_send:
            # Test inline reaction notification
            await notification_service.send_unified_notification(123, inline_data, self.bot_mock)
            mock_send.assert_called_once()
            # Reset mock for next test
            mock_send.reset_mock()
            
            # Test native reaction notification
            await notification_service.send_unified_notification(123, native_data, self.bot_mock)
            mock_send.assert_called_once()
    
    def test_unified_notification(self):
        """Run the unified notification test."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_send_unified_notification())


if __name__ == '__main__':
    unittest.main()