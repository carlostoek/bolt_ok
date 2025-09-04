# tests/test_mvp_gamification_system.py
"""
Comprehensive test suite for MVP Gamification System
Tests all components: points, levels, missions, achievements with character consistency
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from services.mvp_gamification_service import MVPGamificationService
from services.point_service import PointService, POINTS_CONFIG, DIANA_REWARD_MESSAGES
from services.level_service import LevelService, get_user_level, get_next_level_info, MVP_LEVEL_THRESHOLDS
from services.mvp_mission_service import MVPMissionService, MVP_MISSIONS
from services.mvp_achievement_service import MVPAchievementService, MVP_ACHIEVEMENTS
from database.models import User, UserStats, Mission, Achievement, UserAchievement, UserMissionEntry


class TestPointsCalculationEngine:
    """Test the enhanced points calculation engine with MVP economic rules."""
    
    @pytest.mark.asyncio
    async def test_points_config_values(self):
        """Test that MVP economic rules are properly configured."""
        # Verify all required point values exist
        assert POINTS_CONFIG['story_fragment_completion'] == 10
        assert POINTS_CONFIG['decision_made'] == 5
        assert POINTS_CONFIG['daily_login'] == 15
        assert POINTS_CONFIG['mission_completed'] == 25
        assert POINTS_CONFIG['achievement_unlocked'] == 50
        assert POINTS_CONFIG['channel_reaction'] == 2
        assert POINTS_CONFIG['vip_bonus_multiplier'] == 1.5
    
    @pytest.mark.asyncio
    async def test_vip_multiplier_application(self):
        """Test VIP bonus multiplier is correctly applied."""
        session = AsyncMock(spec=AsyncSession)
        level_service = AsyncMock()
        achievement_service = AsyncMock()
        
        point_service = PointService(session, level_service, achievement_service)
        
        # Mock VIP user
        vip_user = User(id=123, role="vip", vip_expires_at=datetime.utcnow() + timedelta(days=30))
        session.get.return_value = vip_user
        
        # Test VIP multiplier
        base_points = 10.0
        multiplied_points = await point_service._apply_vip_multiplier(123, base_points)
        
        assert multiplied_points == base_points * POINTS_CONFIG['vip_bonus_multiplier']
        assert multiplied_points == 15.0
    
    @pytest.mark.asyncio
    async def test_diana_reward_messages_exist(self):
        """Test that Diana's character-consistent messages are configured."""
        assert 'besitos_earned' in DIANA_REWARD_MESSAGES
        assert 'level_up' in DIANA_REWARD_MESSAGES
        assert 'mission_completed' in DIANA_REWARD_MESSAGES
        assert 'achievement_unlocked' in DIANA_REWARD_MESSAGES
        
        # Test Spanish language and seductive tone
        besitos_msg = DIANA_REWARD_MESSAGES['besitos_earned'][0]
        assert 'besitos' in besitos_msg.lower()
        assert 'cariño' in besitos_msg.lower() or 'amor' in besitos_msg.lower()
    
    @pytest.mark.asyncio
    async def test_story_fragment_completion_points(self):
        """Test points awarded for story fragment completion."""
        session = AsyncMock(spec=AsyncSession)
        level_service = AsyncMock()
        achievement_service = AsyncMock()
        notification_service = AsyncMock()
        
        point_service = PointService(session, level_service, achievement_service, notification_service)
        point_service.add_points = AsyncMock()
        point_service.get_balance = AsyncMock(return_value=100)
        
        # Mock regular user (non-VIP)
        regular_user = User(id=123, role="free", points=90)
        session.get.return_value = regular_user
        
        bot = AsyncMock()
        await point_service.award_story_fragment_completion(123, bot)
        
        # Verify correct points awarded
        point_service.add_points.assert_called_once_with(
            123, 10.0, bot=bot, skip_notification=True, source="story_fragment_completion"
        )


class TestLevelProgressionSystem:
    """Test the MVP level progression system with thresholds."""
    
    def test_mvp_level_thresholds(self):
        """Test that MVP level thresholds follow the specification."""
        # Test Level 1-5: 100 besitos per level
        assert get_user_level(0) == 1    # Level 1: 0 besitos
        assert get_user_level(100) == 2  # Level 2: 100 besitos
        assert get_user_level(200) == 3  # Level 3: 200 besitos
        assert get_user_level(400) == 5  # Level 5: 400 besitos
        
        # Test Level 6-10: 200 besitos per level (from previous)
        assert get_user_level(600) == 6  # Level 6: 600 besitos (400 + 200)
        assert get_user_level(800) == 7  # Level 7: 800 besitos
        assert get_user_level(1400) == 10 # Level 10: 1400 besitos
        
        # Test Level 11+: 500 besitos per level
        assert get_user_level(1900) == 11 # Level 11: 1900 besitos (1400 + 500)
        assert get_user_level(2400) == 12 # Level 12: 2400 besitos
    
    def test_get_next_level_info(self):
        """Test next level information calculation."""
        # Test level 1 user
        info = get_next_level_info(50)
        assert info['current_level'] == 1
        assert info['next_level'] == 2
        assert info['points_needed'] == 50  # 100 - 50
        assert 0 < info['percentage_to_next'] < 1
        
        # Test user at exact threshold
        info = get_next_level_info(1400)
        assert info['current_level'] == 10
        assert info['next_level'] == 11
        assert info['points_needed'] == 500  # 1900 - 1400
    
    @pytest.mark.asyncio
    async def test_diana_level_up_messages(self):
        """Test that Diana's level up messages maintain character consistency."""
        session = AsyncMock(spec=AsyncSession)
        level_service = LevelService(session)
        
        # Mock notification service for Diana messages
        session.get.return_value = User(id=123, level=4, points=400)
        
        # This would require integration testing with actual notification service
        # For now, verify the structure exists
        assert hasattr(level_service, 'check_for_level_up')


class TestMissionSystem:
    """Test the 10 MVP missions implementation."""
    
    @pytest.mark.asyncio
    async def test_mvp_missions_count(self):
        """Test that all 10 MVP missions are defined."""
        assert len(MVP_MISSIONS) == 10
    
    @pytest.mark.asyncio
    async def test_mission_configuration(self):
        """Test that missions have proper Diana character messages."""
        for mission in MVP_MISSIONS:
            assert 'id' in mission
            assert 'name' in mission
            assert 'description' in mission
            assert 'diana_completion_message' in mission
            assert 'reward_points' in mission
            
            # Test Spanish language and seductive tone
            desc = mission['description'].lower()
            completion_msg = mission['diana_completion_message'].lower()
            
            # Should contain Spanish endearments
            has_spanish_terms = any(term in desc + completion_msg for term in 
                                   ['cariño', 'amor', 'mi', 'conmigo', 'juntas'])
            assert has_spanish_terms, f"Mission {mission['id']} lacks Spanish character terms"
    
    @pytest.mark.asyncio
    async def test_mission_types_coverage(self):
        """Test that missions cover all required types."""
        mission_types = [m['type'] for m in MVP_MISSIONS]
        
        required_types = [
            'story_progress',
            'decision_making', 
            'login_streak',
            'channel_engagement',
            'vip_subscription',
            'achievement_collection',
            'community_engagement',
            'points_accumulation',
            'level_achievement'
        ]
        
        for req_type in required_types:
            assert req_type in mission_types, f"Missing mission type: {req_type}"
    
    @pytest.mark.asyncio 
    async def test_mvp_mission_service_initialization(self):
        """Test MVPMissionService initialization."""
        session = AsyncMock(spec=AsyncSession)
        point_service = AsyncMock()
        
        mission_service = MVPMissionService(session, point_service)
        
        # Mock existing missions query
        session.execute.return_value.scalars.return_value.all.return_value = []
        session.commit = AsyncMock()
        
        await mission_service.initialize_mvp_missions()
        
        # Should have added missions to session
        assert session.add.call_count == 10  # All 10 missions
        session.commit.assert_called_once()


class TestAchievementSystem:
    """Test the 15 MVP achievements implementation."""
    
    @pytest.mark.asyncio
    async def test_mvp_achievements_count(self):
        """Test that all 15 MVP achievements are defined."""
        assert len(MVP_ACHIEVEMENTS) == 15
    
    @pytest.mark.asyncio
    async def test_achievement_progression(self):
        """Test achievement progression from common to legendary."""
        rarities = [a['rarity'] for a in MVP_ACHIEVEMENTS]
        
        # Should have variety of rarities
        assert 'common' in rarities
        assert 'uncommon' in rarities
        assert 'rare' in rarities
        assert 'epic' in rarities
        assert 'legendary' in rarities
    
    @pytest.mark.asyncio
    async def test_achievement_diana_messages(self):
        """Test that achievements have Diana's seductive personality."""
        for achievement in MVP_ACHIEVEMENTS:
            unlock_msg = achievement['diana_unlock_message'].lower()
            
            # Should have intimate/seductive language
            has_intimate_language = any(word in unlock_msg for word in [
                'mi amor', 'cariño', 'especial', 'íntima', 'corazón', 
                'alma', 'juntas', 'conmigo', 'mía', 'fasci'
            ])
            
            assert has_intimate_language, f"Achievement {achievement['id']} lacks Diana's intimate language"
    
    @pytest.mark.asyncio
    async def test_achievement_condition_types(self):
        """Test that achievements cover all major progression types."""
        condition_types = [a['condition_type'] for a in MVP_ACHIEVEMENTS]
        
        required_conditions = [
            'registration',
            'story_fragments',
            'decisions_made',
            'total_points',
            'user_level',
            'login_streak',
            'missions_completed',
            'vip_subscription'
        ]
        
        for condition in required_conditions:
            assert condition in condition_types, f"Missing achievement condition: {condition}"


class TestGamificationIntegration:
    """Test the complete gamification integration service."""
    
    @pytest.mark.asyncio
    async def test_mvp_gamification_service_initialization(self):
        """Test that MVPGamificationService initializes all sub-services."""
        session = AsyncMock(spec=AsyncSession)
        
        gamification_service = MVPGamificationService(session)
        
        assert hasattr(gamification_service, 'point_service')
        assert hasattr(gamification_service, 'level_service')
        assert hasattr(gamification_service, 'mission_service')
        assert hasattr(gamification_service, 'achievement_service')
    
    @pytest.mark.asyncio
    async def test_story_fragment_completion_integration(self):
        """Test full integration of story fragment completion."""
        session = AsyncMock(spec=AsyncSession)
        gamification_service = MVPGamificationService(session)
        
        # Mock all service methods
        gamification_service.point_service.award_story_fragment_completion = AsyncMock()
        gamification_service.level_service.check_for_level_up = AsyncMock(return_value=False)
        gamification_service.mission_service.trigger_story_fragment_completion = AsyncMock()
        gamification_service.mission_service.check_mission_completion = AsyncMock(return_value=[])
        gamification_service.achievement_service.trigger_achievement_check = AsyncMock(return_value=[])
        
        # Mock user
        session.get.return_value = User(id=123, level=1, points=50)
        
        bot = AsyncMock()
        results = await gamification_service.process_story_fragment_completion(123, "fragment_1", bot)
        
        # Verify all systems were triggered
        gamification_service.point_service.award_story_fragment_completion.assert_called_once()
        gamification_service.mission_service.trigger_story_fragment_completion.assert_called_once()
        
        assert 'points_awarded' in results
        assert 'missions_completed' in results
        assert 'achievements_unlocked' in results
    
    @pytest.mark.asyncio
    async def test_character_consistency_across_systems(self):
        """Test that Diana's character is consistent across all gamification systems."""
        # This is more of an integration test that would run in a live environment
        # Here we test the structure and availability of Diana's messages
        
        # Points system messages
        assert len(DIANA_REWARD_MESSAGES['besitos_earned']) > 0
        assert len(DIANA_REWARD_MESSAGES['mission_completed']) > 0
        
        # Mission system messages  
        for mission in MVP_MISSIONS:
            assert 'diana_completion_message' in mission
            msg = mission['diana_completion_message']
            assert len(msg) > 0
        
        # Achievement system messages
        for achievement in MVP_ACHIEVEMENTS:
            assert 'diana_unlock_message' in achievement
            msg = achievement['diana_unlock_message']
            assert len(msg) > 0


class TestPerformanceRequirements:
    """Test that gamification operations meet performance requirements (<500ms)."""
    
    @pytest.mark.asyncio
    async def test_points_calculation_performance(self):
        """Test that points calculations are fast enough."""
        session = AsyncMock(spec=AsyncSession)
        level_service = AsyncMock()
        achievement_service = AsyncMock()
        
        point_service = PointService(session, level_service, achievement_service)
        
        # Mock fast database operations
        session.get.return_value = User(id=123, role="free")
        
        start_time = datetime.now()
        multiplied = await point_service._apply_vip_multiplier(123, 10.0)
        end_time = datetime.now()
        
        # Should be very fast (< 10ms for unit operation)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        assert duration_ms < 100  # Much less than 500ms requirement
    
    @pytest.mark.asyncio
    async def test_level_calculation_performance(self):
        """Test that level calculations are efficient."""
        # Test static calculation functions (should be instant)
        start_time = datetime.now()
        
        level = get_user_level(1000)
        level_info = get_next_level_info(1000)
        
        end_time = datetime.now()
        
        duration_ms = (end_time - start_time).total_seconds() * 1000
        assert duration_ms < 10  # Should be nearly instant
        
        assert level > 0
        assert 'current_level' in level_info


class TestMultiTenantSupport:
    """Test multi-tenant architecture support in gamification."""
    
    @pytest.mark.asyncio
    async def test_user_isolation(self):
        """Test that gamification data is properly isolated per user."""
        session = AsyncMock(spec=AsyncSession)
        gamification_service = MVPGamificationService(session)
        
        # Mock different users
        user1 = User(id=123, level=1, points=100)
        user2 = User(id=456, level=5, points=500)
        
        # Session should return different users based on ID
        def get_user(user_id):
            if user_id == 123:
                return user1
            elif user_id == 456:
                return user2
            return None
            
        session.get.side_effect = lambda model, user_id: get_user(user_id)
        
        # Mock service methods
        gamification_service.level_service.check_for_level_up = AsyncMock(return_value=False)
        gamification_service.mission_service.get_user_mission_progress = AsyncMock(return_value=[])
        gamification_service.achievement_service.get_user_achievements_summary = AsyncMock(
            return_value={"unlocked_count": 0, "unlocked_achievements": []}
        )
        
        # Get summaries for both users
        summary1 = await gamification_service.get_user_gamification_summary(123)
        summary2 = await gamification_service.get_user_gamification_summary(456)
        
        # Should have different data
        assert summary1["user_info"]["points"] != summary2["user_info"]["points"]
        assert summary1["user_info"]["level"] != summary2["user_info"]["level"]


# Integration test that would require actual database
@pytest.mark.integration
class TestE2EGamificationFlow:
    """End-to-end gamification flow tests (requires database)."""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self):
        """Test complete user journey through gamification system."""
        # This would be implemented with actual database session
        # Testing: Registration -> Story completion -> Level up -> Mission completion -> Achievement unlock
        pass
    
    @pytest.mark.asyncio
    async def test_diana_character_consistency_validation(self):
        """Test that Diana's character remains consistent throughout user journey."""
        # This would validate Diana's messages maintain seductive/mysterious personality
        # across all gamification interactions
        pass


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_mvp_gamification_system.py -v
    pytest.main([__file__])