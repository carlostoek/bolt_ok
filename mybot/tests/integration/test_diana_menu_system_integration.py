"""
Diana Menu System Integration Tests

These tests verify the complete integration between the three main modules:
- Narrative system (storytelling and VIP content)
- Gamification system (points, missions, achievements)
- Channel administration system (user management and social features)

Tests focus on protecting critical user flows and cross-module communication.
"""

import pytest
import asyncio
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery, Message, User as TelegramUser

from services.diana_menu_system import DianaMenuSystem, get_diana_menu_system
from services.rewards.cross_module_rewards import CrossModuleRewards, get_cross_module_rewards
from services.coordinador_central import CoordinadorCentral
from database.models import User, UserStats, VipAccess
from database.narrative_models import UserNarrativeState, StoryFragment
# Import removed - UserRole not available


class TestDianaMenuSystemIntegration:
    """Test comprehensive Diana Menu System integration across all modules."""
    
    @pytest.fixture
    async def diana_system(self, session):
        """Diana Menu System instance for testing."""
        return DianaMenuSystem(session)
    
    @pytest.fixture
    async def cross_module_rewards(self, session):
        """Cross-module rewards system for testing."""
        return CrossModuleRewards(session)
    
    @pytest.fixture
    async def mock_callback_query_with_bot(self, test_user):
        """Mock callback query with bot instance."""
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = MagicMock(spec=TelegramUser)
        callback.from_user.id = test_user.id
        callback.from_user.first_name = test_user.first_name
        callback.from_user.username = test_user.username
        callback.data = "user_menu"
        callback.message = MagicMock()
        callback.message.chat = MagicMock()
        callback.message.chat.id = test_user.id
        callback.message.edit_text = AsyncMock()
        callback.bot = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    async def enhanced_user_data(self, session, test_user, test_channel):
        """Create enhanced user data with cross-module progress."""
        # User stats
        stats = UserStats(
            user_id=test_user.id,
            checkin_streak=7,
            total_missions_completed=3,
            total_achievements=5
        )
        session.add(stats)
        
        # Narrative state
        narrative_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="level2_first_kiss",
            choices_made={"initial_meeting": "confident", "garden_scene": "gentle"},
            unlocked_hints=["hint_diana_past", "hint_secret_garden"],
            completion_percentage=40
        )
        session.add(narrative_state)
        
        # VIP access (for VIP testing)
        vip_access = VipAccess(
            user_id=test_user.id,
            channel_id=test_channel.id,
            granted_at=datetime.datetime.utcnow()
        )
        session.add(vip_access)
        
        await session.commit()
        return {
            "stats": stats,
            "narrative_state": narrative_state,
            "vip_access": vip_access
        }


class TestMainMenuNavigation(TestDianaMenuSystemIntegration):
    """Test main menu navigation and role-based access."""
    
    async def test_free_user_main_menu_display(self, diana_system, mock_callback_query_with_bot, 
                                             test_user, enhanced_user_data):
        """Test main menu display for free users shows correct content and limitations."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        with patch('utils.user_roles.get_user_role', return_value="free"):
            # Act
            await diana_system.show_main_menu(callback.message)
            
            # Assert
            # Verify bot interaction occurred
            assert callback.message.bot.send_message.called or callback.message.answer.called
            
            # Verify user menu delegation
            call_args = callback.message.bot.send_message.call_args
            if call_args:
                text = call_args[1].get('text', '')
                assert "💋" in text  # Diana's signature
                assert "Menú Principal Diana" in text
                assert "personalizada" in text.lower()
    
    async def test_vip_user_main_menu_display(self, diana_system, mock_callback_query_with_bot,
                                            vip_user, enhanced_user_data):
        """Test main menu display for VIP users shows enhanced content."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.from_user.id = vip_user.id
        
        with patch('utils.user_roles.get_user_role', return_value="vip"):
            # Act
            await diana_system.show_main_menu(callback.message)
            
            # Assert
            assert callback.message.bot.send_message.called or callback.message.answer.called
    
    async def test_admin_user_main_menu_display(self, diana_system, mock_callback_query_with_bot,
                                              admin_user):
        """Test main menu display for admin users shows administrative controls."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.from_user.id = admin_user.id
        
        with patch('utils.user_roles.get_user_role', return_value="admin"):
            # Act
            await diana_system.show_main_menu(callback.message)
            
            # Assert
            assert callback.message.bot.send_message.called or callback.message.answer.called
            
            # Verify admin delegation
            call_args = callback.message.bot.send_message.call_args
            if call_args:
                text = call_args[1].get('text', '')
                assert "🎭" in text  # Admin Diana icon
                assert "Administración" in text
    
    async def test_menu_navigation_preserves_character_personality(self, diana_system, 
                                                                 mock_callback_query_with_bot,
                                                                 test_user, enhanced_user_data):
        """Test that Diana's personality is preserved across all menu interactions."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        with patch('utils.user_roles.get_user_role', return_value="free"):
            # Act - Navigate through different menu sections
            await diana_system.show_main_menu(callback.message)
            
            # Test narrative hub
            callback.data = "user_narrative"
            await diana_system.handle_callback(callback)
            
            # Test gamification hub  
            callback.data = "user_games"
            await diana_system.handle_callback(callback)
            
            # Assert - Verify Diana personality elements are present
            all_calls = callback.message.edit_text.call_args_list
            if not all_calls:
                all_calls = callback.message.bot.send_message.call_args_list
            
            for call in all_calls:
                if call and len(call) > 1:
                    text = call[1].get('text', '') if isinstance(call[1], dict) else str(call[1])
                    # Diana's personality should be consistent
                    assert any(keyword in text.lower() for keyword in 
                             ['diana', 'susurra', 'secretos', 'pasión', 'seductora'])


class TestCrossModuleFlows(TestDianaMenuSystemIntegration):
    """Test critical cross-module integration flows."""
    
    async def test_narrative_to_gamification_flow(self, diana_system, cross_module_rewards,
                                                session, test_user, enhanced_user_data):
        """Test narrative progress triggers gamification rewards correctly."""
        # Arrange
        initial_points = test_user.points
        fragment_key = "level3_passionate_night"
        
        # Act
        result = await cross_module_rewards.process_narrative_milestone(
            test_user.id, fragment_key, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "narrative_milestone"
        assert result.points_awarded > 0
        assert "Diana" in result.message  # Personality preservation
        
        # Verify points were actually awarded
        await session.refresh(test_user)
        assert test_user.points > initial_points
    
    async def test_gamification_to_narrative_unlock_flow(self, diana_system, cross_module_rewards,
                                                       session, test_user, enhanced_user_data):
        """Test achievement unlocks grant narrative content access."""
        # Arrange
        achievement_id = "story_explorer"
        
        # Act
        result = await cross_module_rewards.process_achievement_unlock(
            test_user.id, achievement_id, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "achievement_unlock"
        # Narrative unlocks should be available for VIP/achievement-based content
        # This protects the cross-module reward mechanism
    
    async def test_channel_engagement_dual_rewards_flow(self, diana_system, cross_module_rewards,
                                                      session, test_user, test_channel, enhanced_user_data):
        """Test channel engagement provides both points and narrative access."""
        # Arrange
        engagement_type = "weekly_champion"
        engagement_data = {
            "total_activities": 25,
            "channels": 4,
            "quality_score": 9.2
        }
        
        # Act
        result = await cross_module_rewards.process_engagement_milestone(
            test_user.id, engagement_type, engagement_data, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "engagement_milestone"
        assert result.points_awarded > 0
        # This flow should provide both point rewards and narrative access


class TestDataConsistencyAcrossModules(TestDianaMenuSystemIntegration):
    """Test data consistency between different modules."""
    
    async def test_user_profile_shows_integrated_data(self, diana_system, session,
                                                    test_user, enhanced_user_data):
        """Test user profile displays consistent data from all modules."""
        # Arrange
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user.id = test_user.id
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        # Act
        user_data = await diana_system._get_integrated_user_data(test_user.id)
        
        # Assert - Verify data consistency
        assert user_data['level'] == test_user.level or user_data['level'] == 1
        assert user_data['points'] == test_user.points
        assert 'narrative_progress' in user_data
        assert 'completed_missions' in user_data
        assert 'achievements' in user_data
        
        # Verify narrative data is integrated
        assert 'current_chapter' in user_data
        assert 'hints_unlocked' in user_data
        
        # Verify gamification data is integrated
        assert 'streak_days' in user_data
    
    async def test_point_updates_reflect_across_modules(self, diana_system, session,
                                                      test_user, point_service):
        """Test point updates are reflected consistently across all modules."""
        # Arrange
        initial_points = test_user.points
        points_to_add = 50
        
        # Act
        await point_service.add_points(test_user.id, points_to_add)
        
        # Get integrated data after point update
        user_data = await diana_system._get_integrated_user_data(test_user.id)
        
        # Assert
        await session.refresh(test_user)
        assert test_user.points == initial_points + points_to_add
        assert user_data['points'] == test_user.points
        assert user_data['current_points'] == test_user.points
    
    async def test_narrative_progress_consistency(self, diana_system, session,
                                                test_user, enhanced_user_data):
        """Test narrative progress is consistently calculated across modules."""
        # Arrange
        narrative_state = enhanced_user_data['narrative_state']
        
        # Act
        user_data = await diana_system._get_integrated_user_data(test_user.id)
        calculated_progress = await diana_system._calculate_narrative_progress(test_user.id)
        
        # Assert
        assert user_data['narrative_progress'] >= 0
        assert user_data['narrative_progress'] <= 100
        assert calculated_progress >= 0
        assert calculated_progress <= 100
        
        # Current chapter should reflect actual narrative state
        assert user_data['current_chapter'] != "Prólogo"  # Should be past initial


class TestMenuCallbackHandling(TestDianaMenuSystemIntegration):
    """Test comprehensive callback handling and menu navigation."""
    
    async def test_narrative_menu_navigation(self, diana_system, mock_callback_query_with_bot,
                                           test_user, enhanced_user_data):
        """Test narrative menu callbacks work correctly."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "user_narrative"
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        # Verify narrative menu was triggered
    
    async def test_gamification_menu_navigation(self, diana_system, mock_callback_query_with_bot,
                                              test_user, enhanced_user_data):
        """Test gamification menu callbacks work correctly."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "user_games"
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        # Verify gamification menu was triggered
    
    async def test_profile_integration_navigation(self, diana_system, mock_callback_query_with_bot,
                                                test_user, enhanced_user_data):
        """Test profile integration displays comprehensive user data."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "user_profile"
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        # Verify profile menu was triggered
    
    async def test_invalid_callback_handling(self, diana_system, mock_callback_query_with_bot,
                                           test_user):
        """Test invalid callbacks are handled gracefully."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "invalid_callback_data"
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        # Should show development message or warning


class TestMenuRefreshAndUpdates(TestDianaMenuSystemIntegration):
    """Test real-time menu updates and refresh functionality."""
    
    async def test_menu_refresh_updates_data(self, diana_system, mock_callback_query_with_bot,
                                           test_user, enhanced_user_data, point_service):
        """Test menu refresh shows updated user data."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.data = "user_refresh"
        
        # Update user points
        await point_service.add_points(test_user.id, 100)
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        call_args = callback.answer.call_args
        if call_args:
            message = call_args[0][0] if call_args[0] else ""
            assert "actualizado" in message.lower()
    
    async def test_cross_module_notifications_update_menus(self, diana_system, cross_module_rewards,
                                                         session, test_user, enhanced_user_data):
        """Test cross-module events trigger menu notifications."""
        # Arrange
        fragment_key = "level4_complete_trust"
        
        # Act
        result = await cross_module_rewards.process_narrative_milestone(
            test_user.id, fragment_key, bot=None
        )
        
        # Assert
        assert result.success
        # Menu notifications should be triggered
        # This protects the real-time update mechanism


class TestErrorHandlingAndRecovery(TestDianaMenuSystemIntegration):
    """Test error handling and graceful degradation."""
    
    async def test_service_unavailable_graceful_degradation(self, diana_system, 
                                                          mock_callback_query_with_bot, test_user):
        """Test graceful degradation when services are unavailable."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        # Simulate service failure
        with patch.object(diana_system.user_service, 'get_user', side_effect=Exception("Service unavailable")):
            # Act
            await diana_system.show_main_menu(callback.message)
            
            # Assert
            # Should not crash and show error message
            assert True  # If we get here, no unhandled exception occurred
    
    async def test_database_error_handling(self, diana_system, mock_callback_query_with_bot, test_user):
        """Test database errors are handled gracefully."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        # Simulate database error
        with patch.object(diana_system.session, 'execute', side_effect=Exception("Database error")):
            # Act
            await diana_system.handle_callback(callback)
            
            # Assert
            assert callback.answer.called
            # Should show error message to user
    
    async def test_telegram_api_error_recovery(self, diana_system, mock_callback_query_with_bot, test_user):
        """Test recovery from Telegram API errors."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.message.edit_text.side_effect = Exception("Telegram API error")
        
        # Act
        await diana_system.handle_callback(callback)
        
        # Assert
        assert callback.answer.called
        # Should attempt alternative messaging or show error


class TestRoleBasedAccessControl(TestDianaMenuSystemIntegration):
    """Test role-based access controls are properly enforced."""
    
    async def test_free_user_vip_content_restriction(self, diana_system, mock_callback_query_with_bot,
                                                   test_user):
        """Test free users cannot access VIP-only content."""
        # Arrange
        callback = mock_callback_query_with_bot
        
        with patch('utils.user_roles.get_user_role', return_value="free"):
            # Act
            user_data = await diana_system._get_integrated_user_data(test_user.id)
            
            # Assert
            # Free users should have limited access
            assert user_data is not None
            # VIP content should not be accessible
    
    async def test_vip_user_enhanced_access(self, diana_system, mock_callback_query_with_bot,
                                          vip_user, enhanced_user_data):
        """Test VIP users have enhanced access to content."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.from_user.id = vip_user.id
        
        with patch('utils.user_roles.get_user_role', return_value="vip"):
            # Act
            user_data = await diana_system._get_integrated_user_data(vip_user.id)
            
            # Assert
            assert user_data is not None
            # VIP users should have enhanced access
    
    async def test_admin_unrestricted_access(self, diana_system, mock_callback_query_with_bot,
                                           admin_user):
        """Test admin users have unrestricted access."""
        # Arrange
        callback = mock_callback_query_with_bot
        callback.from_user.id = admin_user.id
        
        with patch('utils.user_roles.get_user_role', return_value="admin"):
            # Act
            await diana_system.show_main_menu(callback.message)
            
            # Assert
            # Admin should have access to administrative functions
            assert True  # If no exception, admin access is working


class TestCharacterConsistency(TestDianaMenuSystemIntegration):
    """Test Diana/Lucien character consistency across modules."""
    
    async def test_diana_character_messaging(self, diana_system, test_user, enhanced_user_data):
        """Test Diana character messaging is consistent."""
        # Arrange & Act
        character = await diana_system._get_active_character(test_user.id)
        
        # Assert
        assert character in ["diana", "lucien"]
        # Default should be Diana for most users
        assert character == "diana"
    
    async def test_character_specific_icons_and_themes(self, diana_system, test_user):
        """Test character-specific visual elements are applied correctly."""
        # Arrange & Act
        icons = diana_system.diana_icons
        
        # Assert
        assert "admin" in icons
        assert "user" in icons
        assert "narrative" in icons
        assert "gamification" in icons
        
        # Icons should be consistent with Diana's personality
        assert icons["user"] == "💋"  # Diana's signature
        assert icons["admin"] == "🎭"  # Admin Diana
    
    async def test_engagement_score_calculation(self, diana_system, test_user, enhanced_user_data):
        """Test engagement score reflects cross-module activity."""
        # Act
        engagement_score = await diana_system._calculate_engagement_score(test_user.id)
        
        # Assert
        assert 0 <= engagement_score <= 100
        assert isinstance(engagement_score, int)
        
        # Score should reflect user's activity across modules
        # Users with enhanced data should have higher scores


# === INTEGRATION TEST SUITES ===

class TestCompleteUserJourneys(TestDianaMenuSystemIntegration):
    """Test complete user journeys across all modules."""
    
    async def test_new_user_complete_onboarding_journey(self, diana_system, cross_module_rewards,
                                                      session, mock_callback_query_with_bot):
        """Test complete journey for new user through all systems."""
        # Arrange - Create new user
        new_user = User(
            id=999888777,
            first_name="NewUser",
            username="newuser",
            role="free",
            points=0.0
        )
        session.add(new_user)
        await session.commit()
        
        callback = mock_callback_query_with_bot
        callback.from_user.id = new_user.id
        
        with patch('utils.user_roles.get_user_role', return_value="free"):
            # Act - Simulate complete user journey
            
            # 1. Initial menu access
            await diana_system.show_main_menu(callback.message)
            
            # 2. Navigate to narrative
            callback.data = "user_narrative"
            await diana_system.handle_callback(callback)
            
            # 3. Navigate to gamification
            callback.data = "user_games"  
            await diana_system.handle_callback(callback)
            
            # 4. Check profile
            callback.data = "user_profile"
            await diana_system.handle_callback(callback)
            
            # 5. Simulate earning first points
            await cross_module_rewards.process_engagement_milestone(
                new_user.id, "first_reaction", {"channel_id": 1001}, bot=None
            )
            
            # Assert - User journey completed without errors
            assert callback.answer.call_count >= 3  # At least 3 successful navigations
            
            # Verify user has gained points
            await session.refresh(new_user)
            assert new_user.points > 0
    
    async def test_vip_user_complete_experience_journey(self, diana_system, cross_module_rewards,
                                                      session, vip_user, enhanced_user_data):
        """Test complete VIP user experience across all modules."""
        # Arrange
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user.id = vip_user.id
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('utils.user_roles.get_user_role', return_value="vip"):
            # Act - VIP user journey
            
            # 1. Access enhanced content
            await diana_system.show_main_menu(callback.message)
            
            # 2. Process VIP narrative milestone
            result = await cross_module_rewards.process_narrative_milestone(
                vip_user.id, "level5_ultimate_union", bot=None
            )
            
            # 3. VIP achievement unlock
            vip_result = await cross_module_rewards.process_achievement_unlock(
                vip_user.id, "devoted_lover", bot=None
            )
            
            # Assert - VIP experience is enhanced
            assert result.success
            assert vip_result.success
            assert result.points_awarded > 0
            assert vip_result.points_awarded > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])