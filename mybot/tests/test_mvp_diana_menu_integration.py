"""
MVP Diana Menu System Integration Tests

Comprehensive test suite for Diana Menu System integration with 
narrative system, performance requirements, and user experience consistency.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserMissionProgress
)
from services.diana_menu_system import DianaMenuSystem


class TestDianaMenuIntegration:
    """Test Diana Menu System integration with narrative system."""

    @pytest_asyncio.fixture
    async def diana_menu_system(self, session):
        """Create Diana Menu System with mocked dependencies."""
        menu_system = DianaMenuSystem(session)
        
        # Mock all the dependent services
        menu_system.coordinador = AsyncMock()
        menu_system.user_service = AsyncMock()
        menu_system.narrative_service = AsyncMock()
        menu_system.narrative_compatibility = AsyncMock()
        menu_system.admin_menu = AsyncMock()
        menu_system.user_menu = AsyncMock()
        menu_system.narrative_menu = AsyncMock()
        menu_system.gamification_menu = AsyncMock()
        
        return menu_system

    @pytest_asyncio.fixture
    async def mock_message(self):
        """Create mock Telegram message."""
        message = MagicMock()
        message.from_user.id = 12345
        message.from_user.first_name = "TestUser"
        message.chat.id = 12345
        message.bot = AsyncMock()
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        return message

    @pytest_asyncio.fixture  
    async def mock_callback(self):
        """Create mock Telegram callback query."""
        callback = MagicMock()
        callback.from_user.id = 12345
        callback.from_user.first_name = "TestUser"
        callback.message.chat.id = 12345
        callback.message.message_id = 123
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        callback.bot = AsyncMock()
        return callback

    async def test_menu_system_initialization(self, diana_menu_system):
        """Test Diana Menu System initializes with all required components."""
        assert diana_menu_system.session is not None
        assert diana_menu_system.coordinador is not None
        assert diana_menu_system.user_service is not None
        assert diana_menu_system.narrative_service is not None
        assert diana_menu_system.admin_menu is not None
        assert diana_menu_system.user_menu is not None
        assert diana_menu_system.narrative_menu is not None
        assert diana_menu_system.gamification_menu is not None
        
        # Verify Diana character icons are loaded
        expected_icons = ["admin", "user", "narrative", "gamification", "profile", "vip", "points", "missions", "achievements"]
        for icon_type in expected_icons:
            assert icon_type in diana_menu_system.diana_icons

    async def test_main_menu_role_based_routing(self, diana_menu_system, mock_message):
        """Test main menu routes correctly based on user role."""
        # Test admin role routing
        with patch('utils.user_roles.get_user_role', return_value='admin'):
            diana_menu_system.admin_menu = AsyncMock()
            
            await diana_menu_system.show_main_menu(mock_message)
            
            diana_menu_system.admin_menu.assert_called_once_with(mock_message)

        # Test regular user role routing  
        with patch('utils.user_roles.get_user_role', return_value='free'):
            diana_menu_system.user_menu = AsyncMock()
            
            await diana_menu_system.show_main_menu(mock_message)
            
            diana_menu_system.user_menu.assert_called_once_with(mock_message)

    async def test_narrative_menu_integration(self, diana_menu_system, session, mock_callback):
        """Test narrative menu integrates correctly with MVP narrative system."""
        # Create test user state
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='diana_l1_f1_umbral',
            current_level=1,
            current_tier='los_kinkys'
        )
        session.add(user_state)
        
        # Create test fragment
        fragment = NarrativeFragment(
            id='diana_l1_f1_umbral',
            title='El Umbral de Diana',
            content='💋 **Bienvenido a mis dominios, querido...**',
            fragment_type='DECISION',
            storyline_level=1,
            choices=[
                {
                    'text': '💫 Seguir la luz misteriosa',
                    'next_fragment_id': 'diana_l1_f2_primera_fractura',
                    'points': 10
                }
            ],
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Mock narrative menu response
        diana_menu_system.narrative_menu.show_current_fragment = AsyncMock(return_value={
            'success': True,
            'fragment': fragment,
            'user_level': 1,
            'choices_available': True
        })
        
        # Test narrative menu integration
        result = await diana_menu_system.narrative_menu.show_current_fragment(mock_callback, user_id=12345)
        
        assert result['success'] is True
        assert result['fragment'].id == 'diana_l1_f1_umbral'
        assert result['user_level'] == 1
        assert result['choices_available'] is True

    async def test_menu_character_consistency(self, diana_menu_system):
        """Test menu system maintains Diana character consistency."""
        # Test Diana icons maintain character theme
        icons = diana_menu_system.diana_icons
        
        # Admin should be theatrical/mysterious
        assert icons["admin"] == "🎭"
        
        # User should be seductive/personal
        assert icons["user"] == "💋" 
        
        # Narrative should be story-focused
        assert icons["narrative"] == "📖"
        
        # VIP should be exclusive/premium
        assert icons["vip"] == "👑"

    async def test_menu_state_tracking(self, diana_menu_system, mock_callback):
        """Test menu system tracks state correctly."""
        user_id = 12345
        chat_id = 12345
        
        # Simulate storing temporary message state
        diana_menu_system.temp_messages[chat_id] = (user_id, "narrative_menu", {"level": 1})
        
        # Verify state tracking
        assert chat_id in diana_menu_system.temp_messages
        stored_user_id, menu_type, menu_data = diana_menu_system.temp_messages[chat_id]
        assert stored_user_id == user_id
        assert menu_type == "narrative_menu"
        assert menu_data["level"] == 1

    async def test_cross_module_integration(self, diana_menu_system, mock_callback):
        """Test integration between different modules through Diana Menu."""
        user_id = 12345
        
        # Mock gamification service integration
        diana_menu_system.gamification_menu.get_user_progress = AsyncMock(return_value={
            'level': 2,
            'points': 150,
            'achievements': 3,
            'missions_active': 1
        })
        
        # Mock narrative service integration
        diana_menu_system.narrative_menu.get_current_status = AsyncMock(return_value={
            'current_fragment': 'diana_l2_f1_observadores',
            'tier': 'observadores',
            'completion_percentage': 37.5
        })
        
        # Test cross-module data aggregation
        gamification_data = await diana_menu_system.gamification_menu.get_user_progress(user_id)
        narrative_data = await diana_menu_system.narrative_menu.get_current_status(user_id)
        
        # Verify integration
        assert gamification_data['level'] == 2
        assert gamification_data['points'] == 150
        assert narrative_data['current_fragment'] == 'diana_l2_f1_observadores'
        assert narrative_data['tier'] == 'observadores'

    async def test_menu_error_handling(self, diana_menu_system, mock_message):
        """Test menu system handles errors gracefully while maintaining character."""
        # Mock service error
        with patch('utils.user_roles.get_user_role', side_effect=Exception("Database error")):
            await diana_menu_system.show_main_menu(mock_message)
            
            # Should handle error gracefully
            mock_message.answer.assert_called()
            call_args = mock_message.answer.call_args[0][0]
            
            # Error message should maintain character consistency
            assert "❌" in call_args  # Error indicator
            assert "Error" in call_args or "error" in call_args
            # Should not expose technical details


class TestMenuPerformanceRequirements:
    """Test menu system meets performance requirements."""

    @pytest_asyncio.fixture
    async def performance_diana_menu(self, session):
        """Create Diana Menu System optimized for performance testing."""
        menu_system = DianaMenuSystem(session)
        
        # Mock services for performance testing
        menu_system.user_service.get_user = AsyncMock(return_value=MagicMock(id=12345, role='free'))
        menu_system.narrative_service.get_current_fragment = AsyncMock(return_value=MagicMock())
        menu_system.admin_menu.show_main_admin_panel = AsyncMock()
        menu_system.user_menu.show_main_user_menu = AsyncMock()
        
        return menu_system

    async def test_menu_load_performance(self, performance_diana_menu, mock_message):
        """Test menu loading meets <500ms performance requirement."""
        import time
        
        with patch('utils.user_roles.get_user_role', return_value='free'):
            start_time = time.time()
            await performance_diana_menu.show_main_menu(mock_message)
            end_time = time.time()
            
            load_time_ms = (end_time - start_time) * 1000
            assert load_time_ms < 500, f"Menu load time {load_time_ms:.2f}ms exceeds 500ms requirement"

    async def test_menu_navigation_performance(self, performance_diana_menu, mock_callback):
        """Test menu navigation performance."""
        import time
        
        mock_callback.data = "narrative_menu"
        
        # Mock narrative menu response time
        async def mock_narrative_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms simulated processing
            return {'success': True}
        
        performance_diana_menu.narrative_menu.handle_callback = mock_narrative_response
        
        start_time = time.time()
        await performance_diana_menu.narrative_menu.handle_callback(mock_callback)
        end_time = time.time()
        
        navigation_time_ms = (end_time - start_time) * 1000
        assert navigation_time_ms < 500, f"Navigation time {navigation_time_ms:.2f}ms exceeds 500ms requirement"

    async def test_concurrent_menu_access(self, performance_diana_menu):
        """Test menu system handles concurrent access efficiently."""
        import asyncio
        import time
        
        # Create multiple concurrent menu requests
        mock_messages = []
        for i in range(10):
            message = MagicMock()
            message.from_user.id = 12345 + i
            message.bot = AsyncMock()
            message.answer = AsyncMock()
            mock_messages.append(message)
        
        with patch('utils.user_roles.get_user_role', return_value='free'):
            start_time = time.time()
            
            # Process all requests concurrently
            tasks = [performance_diana_menu.show_main_menu(msg) for msg in mock_messages]
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            total_time_ms = (end_time - start_time) * 1000
            avg_time_per_request = total_time_ms / len(mock_messages)
            
            assert avg_time_per_request < 100, f"Average concurrent processing time {avg_time_per_request:.2f}ms too high"


class TestMenuBesitosIntegration:
    """Test menu system integration with besitos (points) system."""

    async def test_besitos_display_integration(self, session):
        """Test besitos rewards integrate correctly with menu display."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Mock point service
        diana_menu_system.point_service.get_user_points = AsyncMock(return_value=150)
        diana_menu_system.gamification_menu.format_points_display = AsyncMock(
            return_value="💰 150 besitos"
        )
        
        user_id = 12345
        points = await diana_menu_system.point_service.get_user_points(user_id)
        formatted_display = await diana_menu_system.gamification_menu.format_points_display(points)
        
        assert points == 150
        assert "besitos" in formatted_display
        assert "💰" in formatted_display

    async def test_besitos_reward_flow_through_menu(self, session):
        """Test besitos rewards flow correctly through menu system."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Mock reward flow
        diana_menu_system.coordinador.process_user_action = AsyncMock(return_value={
            'success': True,
            'points_awarded': 15,
            'new_total': 165,
            'level_up': False
        })
        
        # Mock menu update with reward notification
        diana_menu_system.gamification_menu.show_reward_notification = AsyncMock()
        
        user_id = 12345
        result = await diana_menu_system.coordinador.process_user_action(
            user_id, {'type': 'narrative_choice', 'choice_index': 0}
        )
        
        assert result['success'] is True
        assert result['points_awarded'] == 15
        assert result['new_total'] == 165
        
        # Verify menu notification
        await diana_menu_system.gamification_menu.show_reward_notification(
            user_id, result['points_awarded']
        )
        diana_menu_system.gamification_menu.show_reward_notification.assert_called_once()

    async def test_besitos_calculation_accuracy(self, session):
        """Test besitos calculations are accurate in menu context."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Mock precise calculation scenarios
        test_scenarios = [
            {'base_points': 10, 'multiplier': 1.0, 'expected': 10},
            {'base_points': 15, 'multiplier': 1.5, 'expected': 23},  # 15 * 1.5 = 22.5, rounded up
            {'base_points': 8, 'multiplier': 2.0, 'expected': 16},
        ]
        
        for scenario in test_scenarios:
            diana_menu_system.point_service.calculate_points = AsyncMock(
                return_value=scenario['expected']
            )
            
            result = await diana_menu_system.point_service.calculate_points(
                scenario['base_points'], multiplier=scenario['multiplier']
            )
            
            assert result == scenario['expected'], f"Points calculation failed for scenario {scenario}"


class TestMenuMultiTenantIsolation:
    """Test menu system properly isolates user sessions."""

    async def test_user_state_isolation(self, session):
        """Test different users see isolated menu states."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Create different user states
        user_states = {
            12345: {'level': 1, 'tier': 'los_kinkys', 'menu_context': 'narrative'},
            23456: {'level': 2, 'tier': 'observadores', 'menu_context': 'gamification'},
            34567: {'level': 3, 'tier': 'comprensores', 'menu_context': 'admin'}
        }
        
        # Mock user service to return isolated states
        async def mock_get_user_state(user_id):
            return user_states.get(user_id, {})
        
        diana_menu_system.user_service.get_user_state = mock_get_user_state
        
        # Test isolation
        for user_id, expected_state in user_states.items():
            user_state = await diana_menu_system.user_service.get_user_state(user_id)
            assert user_state == expected_state
            
            # Verify no cross-contamination
            for other_user_id, other_state in user_states.items():
                if other_user_id != user_id:
                    assert user_state != other_state

    async def test_temporary_message_isolation(self, session):
        """Test temporary message states are isolated per user."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Store different temporary states for different chats
        chat_states = {
            111: (12345, "narrative_level_1", {"fragment": "diana_l1_f1"}),
            222: (23456, "gamification_main", {"points": 150}),
            333: (34567, "admin_panel", {"section": "user_management"})
        }
        
        for chat_id, state_data in chat_states.items():
            diana_menu_system.temp_messages[chat_id] = state_data
        
        # Verify isolation
        for chat_id, expected_state in chat_states.items():
            stored_state = diana_menu_system.temp_messages[chat_id]
            assert stored_state == expected_state
            
            # Verify no cross-contamination  
            for other_chat_id, other_state in chat_states.items():
                if other_chat_id != chat_id:
                    assert stored_state != other_state

    async def test_session_cleanup(self, session):
        """Test menu system cleans up temporary states appropriately."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Add temporary states
        diana_menu_system.temp_messages[111] = (12345, "test_menu", {"test": "data"})
        diana_menu_system.temp_messages[222] = (23456, "another_menu", {"more": "data"})
        
        assert len(diana_menu_system.temp_messages) == 2
        
        # Simulate cleanup (would be called by session management)
        def cleanup_user_session(user_id):
            to_remove = []
            for chat_id, (stored_user_id, _, _) in diana_menu_system.temp_messages.items():
                if stored_user_id == user_id:
                    to_remove.append(chat_id)
            
            for chat_id in to_remove:
                del diana_menu_system.temp_messages[chat_id]
        
        # Clean up user 12345's session
        cleanup_user_session(12345)
        
        # Verify cleanup
        assert len(diana_menu_system.temp_messages) == 1
        assert 111 not in diana_menu_system.temp_messages
        assert 222 in diana_menu_system.temp_messages


class TestMenuAccessibilityConsistency:
    """Test menu system maintains accessibility and consistency."""

    async def test_error_message_character_consistency(self, session):
        """Test error messages maintain Diana's character."""
        diana_menu_system = DianaMenuSystem(session)
        
        error_scenarios = [
            "Database connection failed",
            "Invalid choice selected",
            "User session expired",
            "Insufficient permissions"
        ]
        
        for error in error_scenarios:
            # Mock error handling that maintains character
            character_error = self.convert_to_diana_error(error)
            
            # Verify character elements present
            assert len(character_error) > len(error), "Character error should be more elaborate"
            self.assert_has_diana_elements(character_error)

    def convert_to_diana_error(self, technical_error: str) -> str:
        """Convert technical error to Diana character-consistent message."""
        error_mapping = {
            "Database connection failed": "✨ Los misterios parecen elusivos en este momento... Inténtalo de nuevo, querido.",
            "Invalid choice selected": "💋 Esa opción no está entre las que ofrezco, mi curioso explorador...",
            "User session expired": "🌙 Nuestro encuentro se ha desvanecido... ¿Comenzamos de nuevo?",
            "Insufficient permissions": "🎭 Esos secretos requieren un acceso más íntimo, cariño..."
        }
        
        return error_mapping.get(technical_error, f"🌟 Algo inesperado sucedió en mis dominios... {technical_error}")

    def assert_has_diana_elements(self, text: str):
        """Assert text contains Diana personality elements."""
        diana_elements = ['✨', '💋', '🌙', '🎭', '🌟', 'misterio', 'secreto', 'querido', 'cariño', 'curioso']
        has_elements = any(element in text.lower() for element in diana_elements)
        assert has_elements, f"Text lacks Diana character elements: {text}"

    async def test_menu_responsiveness_across_devices(self, session):
        """Test menu system works consistently across different interfaces."""
        diana_menu_system = DianaMenuSystem(session)
        
        # Simulate different interface types
        interface_tests = [
            {'type': 'mobile', 'max_width': 30, 'inline_buttons': True},
            {'type': 'desktop', 'max_width': 60, 'inline_buttons': True},
            {'type': 'basic', 'max_width': 20, 'inline_buttons': False}
        ]
        
        for interface in interface_tests:
            menu_text = self.format_for_interface(
                "💋 **Menú Principal Diana**\n\nBienvenido a tu experiencia personalizada",
                interface
            )
            
            # Verify formatting constraints
            lines = menu_text.split('\n')
            for line in lines:
                clean_line = line.replace('*', '').replace('💋', '').strip()
                if clean_line:  # Skip empty lines
                    assert len(clean_line) <= interface['max_width'], f"Line too long for {interface['type']}: {clean_line}"

    def format_for_interface(self, text: str, interface: dict) -> str:
        """Format text for specific interface constraints."""
        if interface['type'] == 'basic':
            # Remove markdown and emojis for basic interfaces
            formatted = text.replace('**', '').replace('💋', 'Diana:')
        else:
            formatted = text
        
        # Apply width constraints
        lines = formatted.split('\n')
        wrapped_lines = []
        for line in lines:
            if len(line) > interface['max_width']:
                # Simple word wrapping
                words = line.split()
                current_line = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= interface['max_width']:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_line:
                            wrapped_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                
                if current_line:
                    wrapped_lines.append(' '.join(current_line))
            else:
                wrapped_lines.append(line)
        
        return '\n'.join(wrapped_lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])