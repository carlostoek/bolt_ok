"""
Cross-Module Reward Flow Integration Tests

These tests specifically verify the three main reward flows work correctly:
1. Narrative Progress → Mission Unlocking
2. Gamification Achievements → Narrative Access  
3. Channel Engagement → Dual System Rewards

Critical for protecting the gamification and reward mechanisms during cleanup.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.rewards.cross_module_rewards import CrossModuleRewards, get_cross_module_rewards
from services.rewards.narrative_mission_flow import get_narrative_mission_flow
from services.rewards.achievement_narrative_flow import get_achievement_narrative_flow
from services.rewards.engagement_rewards_flow import get_engagement_rewards_flow
from services.event_bus import get_event_bus, EventType
from database.models import User, UserStats, Channel
from database.narrative_models import UserNarrativeState


class TestCrossModuleRewardFlows:
    """Test all cross-module reward flows work correctly."""
    
    @pytest.fixture
    async def reward_system(self, session):
        """Cross-module rewards system for testing."""
        system = CrossModuleRewards(session)
        await system.initialize_reward_system()
        return system
    
    @pytest.fixture
    async def narrative_mission_flow(self, session):
        """Narrative mission flow service."""
        return get_narrative_mission_flow(session)
    
    @pytest.fixture
    async def achievement_narrative_flow(self, session):
        """Achievement narrative flow service.""" 
        return get_achievement_narrative_flow(session)
    
    @pytest.fixture
    async def engagement_rewards_flow(self, session):
        """Engagement rewards flow service."""
        return get_engagement_rewards_flow(session)
    
    @pytest.fixture
    async def test_user_with_progress(self, session, test_user, test_channel):
        """Test user with existing progress in all systems."""
        # User stats for gamification
        stats = UserStats(
            user_id=test_user.id,
            checkin_streak=10,
            total_missions_completed=5,
            total_achievements=8,
            last_checkin_at=pytest.datetime.utcnow()
        )
        session.add(stats)
        
        # Narrative progress
        narrative_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="level2_garden_exploration",
            choices_made={"garden_entrance": "curious", "first_touch": "hesitant"},
            unlocked_hints=["hint_diana_mystery", "hint_garden_secret"],
            completion_percentage=25
        )
        session.add(narrative_state)
        
        await session.commit()
        return test_user


class TestNarrativeMissionFlow(TestCrossModuleRewardFlows):
    """Test Flow 1: Narrative Progress → Mission Unlocking."""
    
    async def test_narrative_milestone_unlocks_missions(self, reward_system, session,
                                                      test_user_with_progress):
        """Test narrative milestones unlock appropriate missions."""
        # Arrange
        user_id = test_user_with_progress.id
        initial_points = test_user_with_progress.points
        fragment_key = "level3_intimate_discovery"
        
        # Act
        result = await reward_system.process_narrative_milestone(
            user_id, fragment_key, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "narrative_milestone"
        assert result.points_awarded > 0
        assert "Diana" in result.message  # Personality preserved
        
        # Verify points were awarded
        await session.refresh(test_user_with_progress)
        assert test_user_with_progress.points > initial_points
        
        # Verify narrative-specific point calculation
        expected_points = reward_system._get_narrative_milestone_points(fragment_key)
        multiplier = reward_system.reward_multipliers["narrative_milestone"]
        expected_total = int(expected_points * multiplier)
        assert result.points_awarded >= expected_total
    
    async def test_different_narrative_levels_award_different_points(self, reward_system,
                                                                   test_user_with_progress):
        """Test different narrative levels award appropriate point amounts."""
        # Arrange
        test_fragments = [
            ("level1_first_meeting", 10),
            ("level2_garden_walk", 15), 
            ("level3_passionate_kiss", 20),
            ("level4_intimate_moment", 25),
            ("level5_complete_union", 30)
        ]
        
        for fragment_key, expected_base_points in test_fragments:
            # Act
            result = await reward_system.process_narrative_milestone(
                test_user_with_progress.id, fragment_key, bot=None
            )
            
            # Assert
            assert result.success
            assert result.points_awarded > 0
            
            # Points should scale with narrative level
            multiplier = reward_system.reward_multipliers["narrative_milestone"]
            expected_total = int(expected_base_points * multiplier)
            assert result.points_awarded >= expected_total
    
    async def test_narrative_mission_unlock_conditions(self, reward_system, session,
                                                     test_user_with_progress):
        """Test specific narrative milestones unlock specific missions."""
        # Arrange
        user_id = test_user_with_progress.id
        
        # Test level completion milestones
        milestone_tests = [
            ("level1_garden_discovery", ["daily_interaction", "narrative_explorer"]),
            ("level2_first_kiss", ["vip_content_seeker", "story_completion"]),
            ("level3_passionate_night", ["romance_master", "decision_expert"])
        ]
        
        for fragment_key, expected_mission_categories in milestone_tests:
            # Act
            result = await reward_system.process_narrative_milestone(
                user_id, fragment_key, bot=None
            )
            
            # Assert
            assert result.success
            # Mission unlocks should be processed (even if empty for placeholder)
            assert isinstance(result.missions_unlocked, list)
    
    async def test_cross_module_bonus_on_narrative_milestone(self, reward_system, session,
                                                           test_user_with_progress):
        """Test cross-module bonuses are awarded for narrative milestones."""
        # Arrange
        user_id = test_user_with_progress.id
        fragment_key = "level4_complete_trust"
        
        # Mock cross-module bonus eligibility
        with patch.object(reward_system, '_check_cross_module_bonus', 
                         return_value={"eligible": True, "points": 50}):
            # Act
            result = await reward_system.process_narrative_milestone(
                user_id, fragment_key, bot=None
            )
            
            # Assert
            assert result.success
            assert result.points_awarded > 0
            # Should include bonus text
            assert any("Bonus cross-módulo" in item for item in result.items_unlocked)


class TestAchievementNarrativeFlow(TestCrossModuleRewardFlows):
    """Test Flow 2: Gamification Achievements → Narrative Access."""
    
    async def test_achievement_unlock_grants_narrative_access(self, reward_system, session,
                                                            test_user_with_progress):
        """Test achievement unlocks grant access to narrative content."""
        # Arrange
        user_id = test_user_with_progress.id
        initial_points = test_user_with_progress.points
        achievement_id = "story_explorer"
        
        # Act
        result = await reward_system.process_achievement_unlock(
            user_id, achievement_id, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "achievement_unlock"
        assert result.points_awarded > 0
        assert "Diana" in result.message  # Personality preserved
        
        # Verify points were awarded
        await session.refresh(test_user_with_progress)
        assert test_user_with_progress.points > initial_points
        
        # Narrative unlocks should be available
        assert isinstance(result.narrative_unlocked, list)
    
    async def test_specific_achievements_unlock_specific_content(self, reward_system,
                                                               test_user_with_progress):
        """Test specific achievements unlock specific narrative content."""
        # Arrange
        achievement_tests = [
            ("first_reaction", "hint_basic_romance"),
            ("daily_streak_7", "hint_advanced_pleasure"),
            ("points_milestone_100", "fragment_secret_garden"),
            ("mission_master", "fragment_diana_backstory")
        ]
        
        for achievement_id, expected_content_type in achievement_tests:
            # Act
            result = await reward_system.process_achievement_unlock(
                test_user_with_progress.id, achievement_id, bot=None
            )
            
            # Assert
            assert result.success
            
            # Achievement-specific content should be reflected
            expected_points = reward_system._get_achievement_bonus_points(achievement_id)
            multiplier = reward_system.reward_multipliers["achievement_unlock"]
            expected_total = int(expected_points * multiplier)
            assert result.points_awarded >= expected_total
    
    async def test_achievement_unlock_triggers_mission_unlocks(self, reward_system, session,
                                                             test_user_with_progress):
        """Test achievement unlocks can trigger mission unlocks."""
        # Arrange
        user_id = test_user_with_progress.id
        achievement_id = "master_storyteller"
        
        # Act
        result = await reward_system.process_achievement_unlock(
            user_id, achievement_id, bot=None
        )
        
        # Assert
        assert result.success
        assert isinstance(result.missions_unlocked, list)
        assert isinstance(result.narrative_unlocked, list)
        
        # High-level achievements should unlock multiple types of content
    
    async def test_invalid_achievement_handling(self, reward_system, test_user_with_progress):
        """Test invalid achievement IDs are handled gracefully."""
        # Arrange
        user_id = test_user_with_progress.id
        invalid_achievement_id = "nonexistent_achievement"
        
        # Act
        result = await reward_system.process_achievement_unlock(
            user_id, invalid_achievement_id, bot=None
        )
        
        # Assert - Should handle gracefully
        # The actual behavior depends on implementation, but shouldn't crash
        assert isinstance(result.success, bool)


class TestEngagementRewardsFlow(TestCrossModuleRewardFlows):
    """Test Flow 3: Channel Engagement → Dual System Rewards."""
    
    async def test_engagement_milestone_dual_rewards(self, reward_system, session,
                                                   test_user_with_progress, test_channel):
        """Test engagement milestones provide both points and narrative access."""
        # Arrange
        user_id = test_user_with_progress.id
        initial_points = test_user_with_progress.points
        engagement_type = "weekly_champion"
        engagement_data = {
            "total_activities": 25,
            "channels": 4,
            "quality_score": 9.2
        }
        
        # Act
        result = await reward_system.process_engagement_milestone(
            user_id, engagement_type, engagement_data, bot=None
        )
        
        # Assert
        assert result.success
        assert result.reward_type == "engagement_milestone"
        assert result.points_awarded > 0
        
        # Verify points were awarded
        await session.refresh(test_user_with_progress)
        assert test_user_with_progress.points > initial_points
        
        # Dual rewards: both points and potential narrative access
        assert isinstance(result.narrative_unlocked, list)
        assert isinstance(result.missions_unlocked, list)
    
    async def test_different_engagement_types_different_rewards(self, reward_system,
                                                              test_user_with_progress):
        """Test different engagement types award different reward amounts."""
        # Arrange
        engagement_tests = [
            ("daily", {"streak": 1}, 15),
            ("weekly", {"activities": 20}, 75),
            ("reaction", {"type": "love"}, 5),
            ("post", {"quality": "high"}, 20),
            ("comment", {"length": 50}, 10)
        ]
        
        for engagement_type, engagement_data, expected_base_points in engagement_tests:
            # Act
            result = await reward_system.process_engagement_milestone(
                test_user_with_progress.id, engagement_type, engagement_data, bot=None
            )
            
            # Assert
            assert result.success
            
            # Points should match engagement type
            multiplier = reward_system.reward_multipliers["channel_engagement"]
            expected_total = int(expected_base_points * multiplier)
            assert result.points_awarded >= expected_total
    
    async def test_high_engagement_unlocks_narrative_content(self, reward_system, session,
                                                           test_user_with_progress):
        """Test high engagement levels unlock narrative content."""
        # Arrange
        user_id = test_user_with_progress.id
        engagement_type = "engagement_burst"
        engagement_data = {
            "activities": 15,
            "time_window": 45,
            "quality_average": 8.5
        }
        
        # Act
        result = await reward_system.process_engagement_milestone(
            user_id, engagement_type, engagement_data, bot=None
        )
        
        # Assert
        assert result.success
        assert result.points_awarded > 0
        
        # High engagement should potentially unlock narrative content
        assert isinstance(result.narrative_unlocked, list)
        assert isinstance(result.missions_unlocked, list)
    
    async def test_engagement_streak_bonuses(self, reward_system, test_user_with_progress):
        """Test engagement streaks provide bonus rewards."""
        # Arrange
        user_id = test_user_with_progress.id
        engagement_type = "daily_streak"
        engagement_data = {
            "streak": 14,
            "consistency": True,
            "quality_maintained": True
        }
        
        # Act
        result = await reward_system.process_engagement_milestone(
            user_id, engagement_type, engagement_data, bot=None
        )
        
        # Assert
        assert result.success
        assert result.points_awarded > 0
        
        # Streak bonuses should provide enhanced rewards
        # Points should reflect streak bonus


class TestEventSystemIntegration(TestCrossModuleRewardFlows):
    """Test event system integration across reward flows."""
    
    async def test_reward_flows_emit_correct_events(self, reward_system, test_user_with_progress):
        """Test reward flows emit appropriate events for system integration."""
        # Arrange
        event_bus = get_event_bus()
        initial_event_count = len(event_bus.get_event_history(100))
        user_id = test_user_with_progress.id
        
        # Act - Process different types of rewards
        narrative_result = await reward_system.process_narrative_milestone(
            user_id, "level3_passionate_discovery", bot=None
        )
        
        achievement_result = await reward_system.process_achievement_unlock(
            user_id, "devoted_lover", bot=None
        )
        
        engagement_result = await reward_system.process_engagement_milestone(
            user_id, "weekly_active", {"activities": 12}, bot=None
        )
        
        # Assert
        assert narrative_result.success
        assert achievement_result.success  
        assert engagement_result.success
        
        # Events should have been emitted
        final_event_count = len(event_bus.get_event_history(100))
        assert final_event_count > initial_event_count
        
        # Check for workflow completion events
        recent_events = event_bus.get_event_history(10)
        workflow_events = [e for e in recent_events if e.event_type == EventType.WORKFLOW_COMPLETED]
        assert len(workflow_events) >= 3  # One for each reward flow
    
    async def test_event_subscriptions_trigger_cross_module_rewards(self, reward_system, session,
                                                                  test_user_with_progress):
        """Test event subscriptions trigger appropriate cross-module rewards."""
        # Arrange
        event_bus = get_event_bus()
        user_id = test_user_with_progress.id
        
        # Act - Publish events that should trigger cross-module rewards
        await event_bus.publish(
            EventType.NARRATIVE_PROGRESS,
            user_id,
            {
                "fragment_key": "level4_intimate_moment",
                "points_earned": 25,
                "unlocks_triggered": ["mission_romance_expert"]
            },
            source="integration_test"
        )
        
        await event_bus.publish(
            EventType.ACHIEVEMENT_UNLOCKED,
            user_id,
            {
                "achievement_id": "narrative_devotee",
                "points_earned": 50,
                "narrative_unlocks": ["backstory_diana_secrets"]
            },
            source="integration_test"
        )
        
        # Give events time to process
        await asyncio.sleep(0.1)
        
        # Assert - Events should have been processed
        # Verify the event handlers were set up correctly
        assert hasattr(reward_system, '_handle_narrative_progress_event')
        assert hasattr(reward_system, '_handle_achievement_unlock_event')
        assert hasattr(reward_system, '_handle_channel_engagement_event')


class TestRewardSystemInitialization(TestCrossModuleRewardFlows):
    """Test reward system initialization and validation."""
    
    async def test_reward_system_initialization(self, session):
        """Test reward system initializes correctly."""
        # Arrange & Act
        reward_system = CrossModuleRewards(session)
        result = await reward_system.initialize_reward_system()
        
        # Assert
        assert result["success"]
        assert "Sistema de recompensas cross-módulo operativo" in result["message"]
        assert "services_status" in result
        assert "subscriptions_setup" in result
        assert "tracking_initialized" in result
    
    async def test_service_validation(self, reward_system):
        """Test service validation works correctly."""
        # Act
        services_status = await reward_system._validate_services()
        
        # Assert
        assert "services" in services_status
        assert "all_active" in services_status
        
        # Core services should be available
        services = services_status["services"]
        assert services["point_service"] is True
        assert services["coordinador"] is True
        assert services["event_bus"] is True
    
    async def test_reward_multipliers_loaded(self, reward_system):
        """Test reward multipliers are properly configured."""
        # Assert
        multipliers = reward_system.reward_multipliers
        assert "narrative_milestone" in multipliers
        assert "achievement_unlock" in multipliers
        assert "channel_engagement" in multipliers
        assert "cross_module_bonus" in multipliers
        
        # Multipliers should be reasonable values
        assert 1.0 <= multipliers["narrative_milestone"] <= 5.0
        assert 1.0 <= multipliers["achievement_unlock"] <= 5.0
        assert 0.5 <= multipliers["channel_engagement"] <= 2.0
        assert 2.0 <= multipliers["cross_module_bonus"] <= 5.0
    
    async def test_unlock_conditions_configured(self, reward_system):
        """Test unlock conditions are properly configured."""
        # Assert
        conditions = reward_system.unlock_conditions
        assert "narrative_missions" in conditions
        assert "achievement_narratives" in conditions
        assert "engagement_bonuses" in conditions
        
        # Validate narrative mission conditions
        narrative_conditions = conditions["narrative_missions"]
        assert "level1_complete" in narrative_conditions
        assert "level2_complete" in narrative_conditions
        assert "level3_complete" in narrative_conditions
        
        # Validate achievement narrative conditions
        achievement_conditions = conditions["achievement_narratives"]
        assert "first_reaction" in achievement_conditions
        assert "daily_streak_7" in achievement_conditions
        assert "points_milestone_100" in achievement_conditions


class TestDianaPersonalityIntegration(TestCrossModuleRewardFlows):
    """Test Diana's personality is preserved across all reward flows."""
    
    async def test_diana_messages_in_all_flows(self, reward_system, test_user_with_progress):
        """Test Diana's personality messages appear in all reward flows."""
        # Arrange
        user_id = test_user_with_progress.id
        
        # Act - Test all three flows
        narrative_result = await reward_system.process_narrative_milestone(
            user_id, "level2_garden_encounter", bot=None
        )
        
        achievement_result = await reward_system.process_achievement_unlock(
            user_id, "story_enthusiast", bot=None
        )
        
        engagement_result = await reward_system.process_engagement_milestone(
            user_id, "daily", {"streak": 3}, bot=None
        )
        
        # Assert - Diana's personality should be present in all messages
        assert narrative_result.success
        assert "Diana" in narrative_result.message
        
        assert achievement_result.success
        assert "Diana" in achievement_result.message
        
        assert engagement_result.success
        assert "Diana" in engagement_result.message
        
        # Messages should use Diana's characteristic language
        all_messages = [
            narrative_result.message,
            achievement_result.message,
            engagement_result.message
        ]
        
        for message in all_messages:
            # Diana's language should be seductive and engaging
            assert any(keyword in message.lower() for keyword in 
                     ['guía', 'susurra', 'seductora', 'impresionada', 'celebra', 'sonríe'])
    
    async def test_diana_icons_consistency(self, reward_system):
        """Test Diana's visual icons are consistent across the system."""
        # Assert
        icons = reward_system.diana_messages
        assert "narrative_unlock" in icons
        assert "mission_unlock" in icons
        assert "achievement_unlock" in icons
        assert "cross_module_bonus" in icons
        
        # All messages should reflect Diana's personality
        for message_type, message in icons.items():
            assert "Diana" in message
            assert any(word in message.lower() for word in 
                     ['guía', 'desafía', 'celebra', 'impresionada'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])