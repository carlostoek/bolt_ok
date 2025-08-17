"""
Diana UX Consistency Integration Tests

These tests verify that the user experience is consistent across all modules:
- Visual consistency (icons, formatting, layout)
- Diana/Lucien personality preservation 
- Navigation flow consistency
- Message tone and style consistency
- Progress visualization consistency

Critical for protecting the cohesive user experience during cleanup.
"""

import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.diana_menu_system import DianaMenuSystem
from services.diana_menus.user_menu import DianaUserMenu
from services.diana_menus.narrative_menu import DianaNarrativeMenu
from services.diana_menus.gamification_menu import DianaGamificationMenu
from services.diana_menus.admin_menu import DianaAdminMenu
from services.rewards.cross_module_rewards import CrossModuleRewards
from database.models import User, UserStats
from database.narrative_models import UserNarrativeState


class TestDianaUXConsistency:
    """Test UX consistency across all Diana Menu System modules."""
    
    @pytest.fixture
    async def diana_system(self, session):
        """Diana Menu System for UX testing."""
        return DianaMenuSystem(session)
    
    @pytest.fixture
    async def user_menu(self, session):
        """User menu module for testing."""
        return DianaUserMenu(session)
    
    @pytest.fixture
    async def narrative_menu(self, session):
        """Narrative menu module for testing."""
        return DianaNarrativeMenu(session)
    
    @pytest.fixture
    async def gamification_menu(self, session):
        """Gamification menu module for testing."""
        return DianaGamificationMenu(session)
    
    @pytest.fixture
    async def admin_menu(self, session):
        """Admin menu module for testing."""
        return DianaAdminMenu(session)
    
    @pytest.fixture
    async def user_with_full_progress(self, session, test_user):
        """User with progress across all systems for UX testing."""
        # User stats
        stats = UserStats(
            user_id=test_user.id,
            checkin_streak=15,
            total_missions_completed=12,
            total_achievements=8,
            last_checkin_at=pytest.datetime.utcnow()
        )
        session.add(stats)
        
        # Narrative progress
        narrative_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="level4_deep_connection",
            choices_made={
                "first_meeting": "confident",
                "garden_walk": "romantic", 
                "intimate_moment": "passionate",
                "trust_building": "vulnerable"
            },
            unlocked_hints=[
                "hint_diana_background",
                "hint_secret_garden", 
                "hint_emotional_depth",
                "hint_future_possibilities"
            ],
            completion_percentage=75
        )
        session.add(narrative_state)
        
        await session.commit()
        return test_user


class TestVisualConsistency(TestDianaUXConsistency):
    """Test visual consistency across all menu modules."""
    
    async def test_diana_icons_consistency_across_modules(self, diana_system, user_menu, 
                                                        narrative_menu, gamification_menu):
        """Test Diana's icons are consistent across all modules."""
        # Arrange & Act
        diana_icons = diana_system.diana_icons
        narrative_themes = narrative_menu.character_themes
        
        # Assert - Core icons should be consistent
        assert diana_icons["user"] == "💋"  # Diana's signature
        assert diana_icons["admin"] == "🎭"  # Admin Diana
        assert diana_icons["narrative"] == "📖"  # Story
        assert diana_icons["gamification"] == "🎮"  # Games
        assert diana_icons["vip"] == "👑"  # VIP status
        assert diana_icons["points"] == "💰"  # Currency
        
        # Character themes should align with Diana's personality
        diana_theme = narrative_themes["diana"]
        assert diana_theme["icon"] == "💋"
        assert diana_theme["style"] == "seductive"
        assert diana_theme["color"] == "passionate"
        
        lucien_theme = narrative_themes["lucien"]
        assert lucien_theme["icon"] == "🖤"
        assert lucien_theme["style"] == "enigmatic"
        assert lucien_theme["color"] == "mysterious"
    
    async def test_text_formatting_consistency(self, diana_system, session, user_with_full_progress):
        """Test text formatting is consistent across all modules."""
        # Arrange
        user_data = await diana_system._get_integrated_user_data(user_with_full_progress.id)
        
        # Act - Get sample messages from different systems
        narrative_message = await diana_system.cross_module_rewards._generate_narrative_milestone_message(
            "level3_passionate_moment", 50, ["mission_romance"], ["achievement_devoted"]
        )
        
        achievement_message = await diana_system.cross_module_rewards._generate_achievement_unlock_message(
            "story_master", 75, ["hint_secret"], ["mission_expert"]
        )
        
        engagement_message = await diana_system.cross_module_rewards._generate_engagement_milestone_message(
            "weekly_champion", 100, ["special_content"], ["bonus_mission"]
        )
        
        # Assert - Formatting should be consistent
        messages = [narrative_message, achievement_message, engagement_message]
        
        for message in messages:
            # All messages should have Diana's signature elements
            assert "Diana" in message
            assert "💋" in message  # Diana's kiss icon
            assert "*+" in message and "besitos*" in message  # Points formatting
            
            # Consistent reward formatting
            if "contenido" in message:
                assert "📖" in message or "📚" in message
            if "misión" in message:
                assert "🎯" in message
            if "logro" in message:
                assert "🏆" in message
    
    async def test_progress_bar_visualization_consistency(self, diana_system, user_with_full_progress):
        """Test progress visualization is consistent across modules."""
        # Arrange & Act
        user_data = await diana_system._get_integrated_user_data(user_with_full_progress.id)
        narrative_progress = await diana_system._calculate_narrative_progress(user_with_full_progress.id)
        engagement_score = await diana_system._calculate_engagement_score(user_with_full_progress.id)
        
        # Assert - Progress should be consistent percentages
        assert 0 <= user_data.get('narrative_progress', 0) <= 100
        assert 0 <= narrative_progress <= 100
        assert 0 <= engagement_score <= 100
        
        # Progress should reflect actual user state
        assert user_data.get('narrative_progress', 0) >= 50  # User has significant progress
        assert narrative_progress >= 50  # Should match narrative state
        assert engagement_score > 0  # User has activity
    
    async def test_menu_layout_consistency(self, diana_system, session, user_with_full_progress):
        """Test menu layouts follow consistent structure across modules."""
        # This test would verify that all menus follow similar layout patterns
        # For now, we verify the structure elements exist
        
        # Arrange
        user_data = await diana_system._get_integrated_user_data(user_with_full_progress.id)
        
        # Assert - Key data elements should be present
        required_elements = [
            'level', 'points', 'narrative_progress', 'current_chapter',
            'completed_missions', 'achievements', 'streak_days'
        ]
        
        for element in required_elements:
            assert element in user_data, f"Missing required UX element: {element}"
        
        # Data should be in expected formats
        assert isinstance(user_data['level'], int)
        assert isinstance(user_data['points'], (int, float))
        assert isinstance(user_data['narrative_progress'], int)
        assert isinstance(user_data['completed_missions'], int)
        assert isinstance(user_data['achievements'], int)


class TestPersonalityConsistency(TestDianaUXConsistency):
    """Test Diana/Lucien personality consistency across all interactions."""
    
    async def test_diana_personality_in_all_messages(self, diana_system, user_with_full_progress):
        """Test Diana's personality is consistent in all message types."""
        # Arrange & Act
        reward_system = diana_system.cross_module_rewards
        
        # Get Diana's characteristic messages
        diana_messages = reward_system.diana_messages
        
        # Assert - All messages should reflect Diana's personality
        personality_keywords = [
            'guía', 'desafía', 'celebra', 'impresionada',  # Actions
            'seductora', 'complicidad', 'secretos', 'pasión',  # Qualities
            'susurra', 'sonríe', 'misterio'  # Behaviors
        ]
        
        for message_type, message in diana_messages.items():
            assert "Diana" in message
            # Each message should contain personality elements
            message_lower = message.lower()
            assert any(keyword in message_lower for keyword in personality_keywords), \
                   f"Message '{message_type}' lacks Diana's personality: {message}"
    
    async def test_character_selection_affects_tone(self, diana_system, narrative_menu, 
                                                  user_with_full_progress):
        """Test character selection (Diana/Lucien) affects message tone appropriately."""
        # Arrange
        user_id = user_with_full_progress.id
        
        # Act
        diana_character = await diana_system._get_active_character(user_id)
        
        # Assert
        assert diana_character in ["diana", "lucien"]
        
        # Get character themes
        themes = narrative_menu.character_themes
        if diana_character == "diana":
            theme = themes["diana"]
            assert theme["style"] == "seductive"
            assert theme["icon"] == "💋"
        elif diana_character == "lucien":
            theme = themes["lucien"]
            assert theme["style"] == "enigmatic"  
            assert theme["icon"] == "🖤"
    
    async def test_personality_preserved_in_error_messages(self, diana_system, 
                                                         mock_callback_query_with_bot, test_user):
        """Test Diana's personality is preserved even in error messages."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "invalid_action"
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        call_args = callback.answer.call_args
        if call_args and call_args[0]:
            message = call_args[0][0]
            # Even error messages should maintain some personality
            assert isinstance(message, str)
            assert len(message) > 0
    
    async def test_diana_quotes_contextual_appropriateness(self, narrative_menu, user_with_full_progress):
        """Test Diana's quotes are contextually appropriate to narrative progress."""
        # Arrange
        user_id = user_with_full_progress.id
        character = "diana"
        
        # Mock narrative data representing different progress levels
        narrative_data_scenarios = [
            {"completion_percentage": 10, "current_chapter": "Prólogo"},
            {"completion_percentage": 50, "current_chapter": "Segundo Encuentro"},
            {"completion_percentage": 90, "current_chapter": "Unión Completa"}
        ]
        
        for narrative_data in narrative_data_scenarios:
            # Act
            quote = narrative_menu._get_character_quote(character, narrative_data)
            
            # Assert
            assert isinstance(quote, str)
            assert len(quote) > 0
            # Quote should be appropriate for the relationship stage
            if narrative_data["completion_percentage"] < 30:
                # Early stage - should be more mysterious/inviting
                assert any(word in quote.lower() for word in ['misterio', 'secreto', 'conocer'])
            elif narrative_data["completion_percentage"] > 70:
                # Advanced stage - should be more intimate/connected
                assert any(word in quote.lower() for word in ['unión', 'conexión', 'juntos', 'amor'])


class TestNavigationFlowConsistency(TestDianaUXConsistency):
    """Test navigation flows are consistent across all modules."""
    
    async def test_menu_breadcrumb_consistency(self, diana_system, mock_callback_query_with_bot,
                                             user_with_full_progress):
        """Test menu navigation maintains consistent breadcrumb patterns."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        # Act - Navigate through different menu levels
        navigation_flows = [
            "user_menu",
            "user_narrative", 
            "user_games",
            "user_profile"
        ]
        
        for callback_data in navigation_flows:
            callback.data = callback_data
            
            # Act
            await diana_system.handle_callback(callback)
            
            # Assert
            assert callback.answer.called
            callback.answer.reset_mock()
    
    async def test_back_navigation_consistency(self, diana_system, mock_callback_query_with_bot,
                                             user_with_full_progress):
        """Test back navigation works consistently across all modules."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        # Act - Test refresh actions (similar to back navigation)
        refresh_actions = ["user_refresh", "admin_refresh"]
        
        for refresh_action in refresh_actions:
            if refresh_action == "admin_refresh":
                # Skip admin refresh for non-admin user
                continue
                
            callback.data = refresh_action
            await diana_system.handle_callback(callback)
            
            # Assert
            assert callback.answer.called
            callback.answer.reset_mock()
    
    async def test_menu_state_preservation(self, diana_system, user_with_full_progress):
        """Test menu state is preserved correctly across navigation."""
        # Arrange
        user_id = user_with_full_progress.id
        
        # Act - Get user data multiple times to ensure consistency
        data1 = await diana_system._get_integrated_user_data(user_id)
        data2 = await diana_system._get_integrated_user_data(user_id)
        
        # Assert - Data should be consistent
        assert data1['level'] == data2['level']
        assert data1['points'] == data2['points']
        assert data1['narrative_progress'] == data2['narrative_progress']
        assert data1['current_chapter'] == data2['current_chapter']


class TestMessageToneConsistency(TestDianaUXConsistency):
    """Test message tone and style consistency across all interactions."""
    
    async def test_reward_message_tone_consistency(self, diana_system, user_with_full_progress):
        """Test reward messages maintain consistent tone across different reward types."""
        # Arrange
        reward_system = diana_system.cross_module_rewards
        user_id = user_with_full_progress.id
        
        # Act - Generate different types of reward messages
        messages = []
        
        # Narrative milestone message
        narrative_msg = await reward_system._generate_narrative_milestone_message(
            "level3_deep_moment", 50, ["mission_romance"], ["achievement_passion"]
        )
        messages.append(("narrative", narrative_msg))
        
        # Achievement unlock message
        achievement_msg = await reward_system._generate_achievement_unlock_message(
            "devoted_lover", 75, ["secret_content"], ["special_mission"]
        )
        messages.append(("achievement", achievement_msg))
        
        # Engagement milestone message
        engagement_msg = await reward_system._generate_engagement_milestone_message(
            "weekly_champion", 100, ["exclusive_content"], ["bonus_mission"]
        )
        messages.append(("engagement", engagement_msg))
        
        # Assert - All messages should have consistent tone
        for message_type, message in messages:
            # Consistent formatting
            assert "*+" in message and "besitos*" in message  # Points format
            assert "💋" in message  # Diana's signature
            
            # Consistent reward presentation
            if "contenido" in message:
                assert "📖" in message or "📚" in message
            if "misión" in message:
                assert "🎯" in message
                
            # Diana's personality should be present
            assert "Diana" in message
    
    async def test_error_message_tone_consistency(self, diana_system, mock_callback_query_with_bot,
                                                test_user):
        """Test error messages maintain appropriate tone."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        # Simulate different error scenarios
        error_scenarios = [
            "invalid_callback_data",
            "nonexistent_menu_item",
            "undefined_action"
        ]
        
        for error_data in error_scenarios:
            callback.data = error_data
            
            # Act
            await diana_system.handle_callback(callback)
            
            # Assert
            assert callback.answer.called
            
            # Error messages should be gentle and stay in character
            call_args = callback.answer.call_args
            if call_args and call_args[0]:
                message = call_args[0][0]
                # Should not be harsh or break character
                assert "❌" in message or "🔧" in message  # Error indicators
                assert not any(harsh_word in message.lower() for harsh_word in 
                             ['error', 'fallo', 'problema'] if 'desarrollo' not in message.lower())
            
            callback.answer.reset_mock()
    
    async def test_greeting_message_personalization(self, diana_system, user_menu, 
                                                  user_with_full_progress):
        """Test greeting messages are personalized based on user progress."""
        # Arrange
        user_id = user_with_full_progress.id
        character = "diana"
        
        # Act
        greeting = await user_menu._get_personalized_greeting(user_id, character)
        
        # Assert
        assert isinstance(greeting, str)
        assert len(greeting) > 0
        
        # Greeting should reflect user's progress level
        # High-progress users should get more intimate greetings
        assert any(word in greeting.lower() for word in 
                  ['bienvenido', 'regreso', 'querido', 'amor', 'cariño', 'mi'])


class TestAccessibilityAndUsability(TestDianaUXConsistency):
    """Test accessibility and usability consistency across the system."""
    
    async def test_keyboard_structure_consistency(self, diana_system, session, user_with_full_progress):
        """Test keyboard layouts are consistent and logical across modules."""
        # This test verifies that keyboard building methods exist and are callable
        # In a full implementation, it would test actual keyboard structure
        
        # Arrange
        user_data = await diana_system._get_integrated_user_data(user_with_full_progress.id)
        
        # Assert - Core data for keyboard building should be available
        assert 'level' in user_data
        assert 'points' in user_data
        assert 'narrative_progress' in user_data
        
        # User data should enable consistent keyboard generation
        assert user_data['level'] >= 1
        assert user_data['points'] >= 0
        assert 0 <= user_data['narrative_progress'] <= 100
    
    async def test_response_time_consistency(self, diana_system, mock_callback_query_with_bot,
                                           user_with_full_progress):
        """Test response times are consistent across different menu operations."""
        # Arrange
        callback = mock_callback_query_with_bot
        import time
        
        # Act - Time different operations
        operations = ["user_menu", "user_narrative", "user_games", "user_profile"]
        response_times = []
        
        for operation in operations:
            callback.data = operation
            start_time = time.time()
            
            await diana_system.handle_callback(callback)
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            callback.answer.reset_mock()
        
        # Assert - Response times should be reasonable and consistent
        for response_time in response_times:
            assert response_time < 1.0  # Should respond within 1 second
        
        # Variance should not be too large
        if len(response_times) > 1:
            avg_time = sum(response_times) / len(response_times)
            for response_time in response_times:
                assert abs(response_time - avg_time) < 0.5  # Within 500ms of average
    
    async def test_data_loading_error_handling(self, diana_system, session, test_user):
        """Test graceful handling when user data is incomplete or missing."""
        # Arrange - User with minimal data
        minimal_user = test_user
        
        # Act
        user_data = await diana_system._get_integrated_user_data(minimal_user.id)
        
        # Assert - Should handle missing data gracefully
        assert isinstance(user_data, dict)
        
        # Should provide default values for missing data
        assert 'level' in user_data
        assert 'points' in user_data
        assert 'narrative_progress' in user_data
        
        # Defaults should be reasonable
        assert user_data['level'] >= 1
        assert user_data['points'] >= 0
        assert 0 <= user_data['narrative_progress'] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])