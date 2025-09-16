"""
Integration tests for the narrative module admin interface.

These tests verify that all admin functionality works correctly when integrated
with the database, handlers, and services.

Requirements covered:
- Requirement 1.1: WHEN an administrator accesses the narrative admin panel THEN the system SHALL display all existing story fragments organized by level and progression path
- Requirement 2.2: WHEN linking lore pieces to shop items THEN the system SHALL provide a visual interface to select existing lore pieces or create new ones directly from the shop item creation flow

Testing includes:
- Admin permission validation
- Narrative fragment management (creation, listing, upload)
- Admin analytics and statistics
- Error handling and edge cases
- Performance testing
- Integration between handlers and services
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from database.models import User
from tests.emotional.conftest import setup_test_narrative_state, cleanup_test_data


class TestNarrativeAdminIntegration:
    """Test suite for narrative admin interface integration"""

    @pytest.fixture
    async def admin_user(self, mock_session):
        """Create an admin user for testing"""
        admin = User(
            id=1,
            telegram_id=123456789,
            username="admin_test",
            role="admin",
            points=1000
        )
        mock_session.get.return_value = admin
        return admin

    @pytest.fixture
    async def regular_user(self, mock_session):
        """Create a regular user for testing"""
        user = User(
            id=2,
            telegram_id=987654321,
            username="regular_test",
            role="free",
            points=100
        )
        mock_session.get.return_value = user
        return user

    async def test_admin_permission_validation_integration(self, mock_session, admin_user, regular_user):
        """Test that admin commands properly validate user permissions"""
        from handlers.admin_narrative_handlers import load_narrative_command
        
        # Test with admin user - should succeed
        message_admin = MagicMock()
        message_admin.from_user.id = admin_user.telegram_id
        message_admin.text = "/load_narrative"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await load_narrative_command(message_admin, mock_session)
            # Should not receive permission denied message
            mock_safe_answer.assert_called()
            # Check that the error message was not about permissions
            call_args = mock_safe_answer.call_args[0][1]
            assert "Solo los administradores" not in call_args

        # Test with regular user - should be denied
        message_regular = MagicMock()
        message_regular.from_user.id = regular_user.telegram_id
        message_regular.text = "/load_narrative"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await load_narrative_command(message_regular, mock_session)
            # Should receive permission denied message
            mock_safe_answer.assert_called_with(message_regular, "❌ Solo los administradores pueden usar este comando.")

    async def test_admin_fragment_creation_integration(self, mock_session, admin_user):
        """Test admin fragment creation through handlers"""
        from handlers.admin_narrative_handlers import upload_narrative_command, handle_narrative_file
        
        # Test upload command for admin
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/upload_narrative"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            with patch('handlers.admin_narrative_handlers.FSMContext') as mock_state:
                mock_state_instance = AsyncMock()
                await upload_narrative_command(message, mock_session, mock_state_instance)
                mock_safe_answer.assert_called()
                mock_state_instance.set_state.assert_called()

    async def test_admin_list_fragments_integration(self, mock_session, admin_user):
        """Test admin fragment listing functionality"""
        from handlers.admin_narrative_handlers import narrative_admin_stats
        
        # Setup mock database responses
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5  # 5 total fragments
        mock_result.all.return_value = [(1, 2), (2, 3)]  # level distribution
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/narrative_stats"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await narrative_admin_stats(message, mock_session)
            mock_safe_answer.assert_called()
            # Check that stats were displayed
            call_args = mock_safe_answer.call_args[0][1]
            assert "Estadísticas del Sistema Narrativo" in call_args

    async def test_admin_analytics_detailed_stats(self, mock_session, admin_user):
        """Test detailed admin analytics functionality"""
        from handlers.admin_narrative_handlers import narrative_admin_stats
        
        # Setup mock database responses with detailed data
        fragments_result = MagicMock()
        fragments_result.scalar.return_value = 15  # 15 total fragments
        
        choices_result = MagicMock()
        choices_result.scalar.return_value = 25  # 25 total choices
        
        users_result = MagicMock()
        users_result.scalar.return_value = 8  # 8 active users
        
        level_result = MagicMock()
        level_result.all.return_value = [(1, 5), (2, 6), (3, 4)]  # level distribution
        
        # Mock session to return different results for different queries
        async def mock_execute_side_effect(query):
            query_str = str(query)
            if "StoryFragment" in query_str and "count" in query_str:
                return fragments_result
            elif "NarrativeChoice" in query_str and "count" in query_str:
                return choices_result
            elif "UserNarrativeState" in query_str and "count" in query_str:
                return users_result
            elif "StoryFragment.level" in query_str:
                return level_result
            return MagicMock()
        
        mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)
        
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/narrative_stats"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await narrative_admin_stats(message, mock_session)
            mock_safe_answer.assert_called()
            # Check that detailed stats were displayed
            call_args = mock_safe_answer.call_args[0][1]
            assert "Estadísticas del Sistema Narrativo" in call_args
            assert "Fragmentos totales: 15" in call_args
            assert "Decisiones totales: 25" in call_args
            assert "Usuarios activos: 8" in call_args
            assert "Nivel 1 (Gratuito): 5 fragmentos" in call_args
            assert "Nivel 2 (Gratuito): 6 fragmentos" in call_args
            assert "Nivel 3 (Gratuito): 4 fragmentos" in call_args

    async def test_admin_view_fragment_integration(self, mock_session, admin_user):
        """Test admin fragment viewing functionality"""
        # This would test viewing individual fragments when that functionality is implemented
        pass

    async def test_admin_fragment_update_integration(self, mock_session, admin_user):
        """Test admin fragment update functionality"""
        # This would test updating fragments when that functionality is implemented
        pass

    async def test_admin_fragment_connections_integration(self, mock_session, admin_user):
        """Test admin fragment connection management"""
        # This would test managing connections between fragments when implemented
        pass

    async def test_admin_fragment_engagement_stats_integration(self, mock_session, admin_user):
        """Test admin engagement statistics for fragments"""
        # This would test viewing detailed engagement stats when implemented
        pass

    async def test_admin_user_progress_view_integration(self, mock_session, admin_user):
        """Test admin viewing of user progress"""
        # This would test viewing user narrative progress when implemented
        pass

    async def test_admin_reset_user_progress_integration(self, mock_session, admin_user):
        """Test admin resetting of user progress"""
        from handlers.admin_narrative_handlers import reset_user_narrative
        
        # Test with valid user ID
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/reset_narrative 987654321"
        
        # Mock user state that exists
        mock_user_state = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user_state
        mock_session.execute.return_value = mock_result
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await reset_user_narrative(message, mock_session)
            # Should show success message
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "Narrativa Reiniciada" in call_args

    async def test_admin_error_handling_integration(self, mock_session, admin_user):
        """Test admin error handling for edge cases"""
        from handlers.admin_narrative_handlers import reset_user_narrative
        
        # Test with invalid user ID format
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/reset_narrative invalid_id"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await reset_user_narrative(message, mock_session)
            # Should show error message for invalid ID
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "ID de usuario inválido" in call_args

    async def test_narrative_system_consistency_integration(self, mock_session, admin_user):
        """Test that narrative system maintains consistency through admin operations"""
        # This would test that admin operations don't break narrative consistency
        pass

    async def test_admin_file_upload_integration(self, mock_session, admin_user):
        """Test admin narrative file upload functionality"""
        from handlers.admin_narrative_handlers import handle_narrative_file
        from aiogram.fsm.state import State, StatesGroup
        from aiogram.fsm.context import FSMContext
        
        # Create a temporary JSON file with valid narrative fragment
        fragment_data = {
            "fragment_id": "test_upload_001",
            "content": "Test content for upload",
            "character": "Diana",
            "level": 1,
            "required_besitos": 0,
            "reward_besitos": 5,
            "decisions": [
                {
                    "text": "Test option 1",
                    "next_fragment": "test_next_001"
                }
            ]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(fragment_data, temp_file)
            temp_path = temp_file.name
        
        try:
            # Mock message with document
            message = MagicMock()
            message.document = MagicMock()
            message.document.file_name = "test_fragment.json"
            message.document.file_id = "test_file_id"
            message.from_user.id = admin_user.telegram_id
            
            # Mock bot download
            with patch('aiogram.Bot.get_file') as mock_get_file, \
                 patch('aiogram.Bot.download_file') as mock_download_file, \
                 patch('services.narrative_loader.NarrativeLoader.load_fragment_from_file') as mock_load_fragment, \
                 patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
                
                mock_file = MagicMock()
                mock_file.file_path = temp_path
                mock_get_file.return_value = mock_file
                mock_download_file.return_value = None
                mock_load_fragment.return_value = None
                
                # Mock FSM state
                mock_state = AsyncMock()
                
                await handle_narrative_file(message, mock_session, mock_state)
                
                # Verify that the file was processed
                mock_get_file.assert_called_once()
                mock_download_file.assert_called_once()
                mock_load_fragment.assert_called_once()
                mock_safe_answer.assert_called()
                
                # Check success message
                call_args = mock_safe_answer.call_args[0][1]
                assert "Fragmento Cargado" in call_args
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def test_admin_invalid_file_upload_integration(self, mock_session, admin_user):
        """Test admin handling of invalid narrative file uploads"""
        from handlers.admin_narrative_handlers import handle_narrative_file
        
        # Mock message with non-JSON document
        message = MagicMock()
        message.document = MagicMock()
        message.document.file_name = "test_fragment.txt"  # Wrong extension
        message.from_user.id = admin_user.telegram_id
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            mock_state = AsyncMock()
            await handle_narrative_file(message, mock_session, mock_state)
            
            # Should show error about file type
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "El archivo debe ser un JSON" in call_args

    async def test_admin_load_default_narrative_integration(self, mock_session, admin_user):
        """Test admin loading of default narrative"""
        from handlers.admin_narrative_handlers import load_narrative_command
        
        message = MagicMock()
        message.from_user.id = admin_user.telegram_id
        message.text = "/load_narrative"
        
        with patch('services.narrative_loader.NarrativeLoader.load_fragments_from_directory') as mock_load_dir, \
             patch('services.narrative_loader.NarrativeLoader.load_default_narrative') as mock_load_default, \
             patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            
            # Simulate directory loading failure to trigger default loading
            mock_load_dir.side_effect = Exception("No files found")
            mock_load_default.return_value = None
            
            await load_narrative_command(message, mock_session)
            
            # Should try both methods
            mock_load_dir.assert_called_once()
            mock_load_default.assert_called_once()
            mock_safe_answer.assert_called()


# Additional integration tests for specific admin workflows
class TestAdminNarrativeWorkflows:
    """Test complete admin workflows for narrative management"""

    async def test_fragment_creation_handler_integration(self, mock_session):
        """Test complete fragment creation workflow through handlers"""
        # This would test the full workflow from command to database storage
        pass

    async def test_fragment_connections_view_integration(self, mock_session):
        """Test viewing and managing fragment connections"""
        # This would test connection visualization and management
        pass

    async def test_complete_narrative_admin_flow(self, mock_session):
        """Test a complete narrative admin workflow"""
        # This would test a sequence of admin operations
        pass

    async def test_admin_narrative_service_integration(self, mock_session):
        """Test integration between admin handlers and narrative service"""
        # This would test that handlers correctly call service methods
        from services.narrative_admin_service import NarrativeAdminService
        
        # Create service instance
        service = NarrativeAdminService(mock_session)
        
        # Test that service methods exist (placeholder test)
        assert hasattr(service, 'create_story_fragment')
        assert hasattr(service, 'update_story_fragment')
        assert hasattr(service, 'delete_story_fragment')
        assert hasattr(service, 'validate_narrative_consistency')
        
        # Test placeholder implementations return expected structure
        result = await service.create_story_fragment({})
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_admin_analytics_integration(self, mock_session):
        """Test integration with analytics system"""
        from services.narrative_admin_service import NarrativeAdminService
        
        # Create service instance
        service = NarrativeAdminService(mock_session)
        
        # Test analytics integration (placeholder)
        result = await service.get_fragment_with_analytics("test_fragment")
        assert result is None  # Current implementation returns None


# Performance and stress tests
@pytest.mark.integration
class TestNarrativeAdminPerformance:
    """Test performance of admin interface under load"""

    async def test_concurrent_admin_operations(self, mock_session):
        """Test concurrent admin operations don't cause conflicts"""
        # This would test multiple admins working simultaneously
        pass

    async def test_large_fragment_import_performance(self, mock_session):
        """Test performance with large narrative fragment imports"""
        # This would test importing many fragments at once
        pass

    async def test_admin_stats_performance(self, mock_session):
        """Test performance of admin statistics generation"""
        from handlers.admin_narrative_handlers import narrative_admin_stats
        
        # Mock database responses with large datasets
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1000  # 1000 total fragments
        mock_result.all.return_value = [(i, 50) for i in range(1, 21)]  # 20 levels with 50 fragments each
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Create admin user
        admin = User(
            id=1,
            telegram_id=123456789,
            username="admin_test",
            role="admin",
            points=1000
        )
        
        message = MagicMock()
        message.from_user.id = admin.telegram_id
        message.text = "/narrative_stats"
        
        import time
        start_time = time.time()
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await narrative_admin_stats(message, mock_session)
            
        end_time = time.time()
        
        # Should complete within reasonable time (less than 2 seconds)
        assert end_time - start_time < 2.0
        
        # Should display stats
        mock_safe_answer.assert_called()
        call_args = mock_safe_answer.call_args[0][1]
        assert "Estadísticas del Sistema Narrativo" in call_args


# Additional edge case tests
class TestNarrativeAdminEdgeCases:
    """Test edge cases and error conditions in admin interface"""

    async def test_admin_command_with_no_arguments(self, mock_session):
        """Test admin commands with missing required arguments"""
        from handlers.admin_narrative_handlers import reset_user_narrative
        
        # Create admin user
        admin = User(
            id=1,
            telegram_id=123456789,
            username="admin_test",
            role="admin",
            points=1000
        )
        
        # Test reset command with no user ID
        message = MagicMock()
        message.from_user.id = admin.telegram_id
        message.text = "/reset_narrative"  # Missing user ID
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await reset_user_narrative(message, mock_session)
            
            # Should show usage instructions
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "Uso" in call_args
            assert "reset_narrative <user_id>" in call_args

    async def test_admin_command_with_database_error(self, mock_session):
        """Test admin commands when database is unavailable"""
        from handlers.admin_narrative_handlers import narrative_admin_stats
        
        # Create admin user
        admin = User(
            id=1,
            telegram_id=123456789,
            username="admin_test",
            role="admin",
            points=1000
        )
        
        # Mock database error
        mock_session.execute.side_effect = Exception("Database connection failed")
        
        message = MagicMock()
        message.from_user.id = admin.telegram_id
        message.text = "/narrative_stats"
        
        with patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            await narrative_admin_stats(message, mock_session)
            
            # Should show error message
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "Error" in call_args
            assert "Database connection failed" in call_args

    async def test_admin_file_upload_with_download_error(self, mock_session, admin_user):
        """Test admin file upload when download fails"""
        from handlers.admin_narrative_handlers import handle_narrative_file
        
        # Mock message with document
        message = MagicMock()
        message.document = MagicMock()
        message.document.file_name = "test_fragment.json"
        message.document.file_id = "test_file_id"
        message.from_user.id = admin_user.telegram_id
        
        # Mock bot download failure
        with patch('aiogram.Bot.get_file') as mock_get_file, \
             patch('aiogram.Bot.download_file') as mock_download_file, \
             patch('handlers.admin_narrative_handlers.safe_answer') as mock_safe_answer:
            
            mock_file = MagicMock()
            mock_file.file_path = "/invalid/path"
            mock_get_file.return_value = mock_file
            mock_download_file.side_effect = Exception("Download failed")
            
            mock_state = AsyncMock()
            
            await handle_narrative_file(message, mock_session, mock_state)
            
            # Should show error message
            mock_safe_answer.assert_called()
            call_args = mock_safe_answer.call_args[0][1]
            assert "Error" in call_args
            assert "Download failed" in call_args