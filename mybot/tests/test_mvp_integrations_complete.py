"""
Comprehensive Integration Tests for MVP Narrative System Completions
Tests VIP service integration, achievement service integration, 
database optimization, and memory management implementations.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Import the services we're testing
from services.mvp_decision_tree_service import MVPDecisionTreeService
from services.decision_achievement_integration import DecisionAchievementIntegration
from services.decision_performance_optimizer import DecisionPerformanceOptimizer
from services.vip_tier_management_service import VIPTierManagementService, VIPTier, AccessDecisionReason

# Import database models
from database.narrative_unified import (
    NarrativeFragment, UserNarrativeState, UserDecisionLog,
    UserMissionProgress, UserArchetype
)
from database.models import User, Achievement, UserAchievement

@pytest.fixture
async def mock_session():
    """Create a mock async session with proper context manager support."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.add = AsyncMock()
    
    # Mock context manager behavior
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    return session

@pytest.fixture
def sample_fragment():
    """Create a sample narrative fragment for testing."""
    fragment = MagicMock(spec=NarrativeFragment)
    fragment.id = "test_fragment_vip_01"
    fragment.title = "VIP Test Fragment"
    fragment.content = "This is a VIP fragment for testing"
    fragment.fragment_type = "STORY"
    fragment.requires_vip = True
    fragment.vip_tier_required = 1
    fragment.storyline_level = 4
    fragment.required_clues = []
    fragment.choices = []
    fragment.triggers = {}
    return fragment

@pytest.fixture
def sample_user_state():
    """Create a sample user narrative state."""
    user_state = MagicMock(spec=UserNarrativeState)
    user_state.user_id = 123456789
    user_state.current_level = 3
    user_state.current_tier = "los_kinkys"
    user_state.visited_fragments = []
    user_state.completed_fragments = []
    user_state.unlocked_clues = []
    user_state.has_unlocked_clue = MagicMock(return_value=False)
    return user_state


class TestVIPServiceIntegration:
    """Test VIP service integration in decision tree service."""
    
    @pytest.mark.asyncio
    async def test_vip_access_validation_success(self, mock_session, sample_fragment, sample_user_state):
        """Test successful VIP access validation."""
        # Setup
        decision_service = MVPDecisionTreeService(mock_session)
        
        # Mock VIP service to return access granted
        with patch.object(decision_service.vip_service, 'check_content_access') as mock_vip_check:
            mock_vip_result = MagicMock()
            mock_vip_result.has_access = True
            mock_vip_result.reason = AccessDecisionReason.ACCESS_GRANTED
            mock_vip_check.return_value = mock_vip_result
            
            # Mock fragment service to return fragment
            with patch.object(decision_service.fragment_service, '_get_fragment_cached', return_value=sample_fragment):
                # Execute
                result = await decision_service._validate_user_prerequisites(
                    user_id=123456789,
                    fragment=sample_fragment,
                    selected_choice={},
                    user_state=sample_user_state
                )
                
                # Assert
                assert result['valid'] is True
                mock_vip_check.assert_called_once_with(
                    user_id=123456789,
                    fragment_id="test_fragment_vip_01",
                    context="decision_validation"
                )
    
    @pytest.mark.asyncio
    async def test_vip_access_validation_denied(self, mock_session, sample_fragment, sample_user_state):
        """Test VIP access validation denial with character-consistent response."""
        # Setup
        decision_service = MVPDecisionTreeService(mock_session)
        
        # Mock VIP service to return access denied
        with patch.object(decision_service.vip_service, 'check_content_access') as mock_vip_check:
            mock_vip_result = MagicMock()
            mock_vip_result.has_access = False
            mock_vip_result.reason = AccessDecisionReason.VIP_REQUIRED
            mock_vip_result.narrative_justification = "💎 Este sendero requiere una conexión más profunda conmigo, querido..."
            mock_vip_result.personalized_offer = {"tier": "el_divan", "discount": 20}
            mock_vip_result.unlock_requirements = ["VIP subscription required"]
            mock_vip_check.return_value = mock_vip_result
            
            # Execute
            result = await decision_service._validate_user_prerequisites(
                user_id=123456789,
                fragment=sample_fragment,
                selected_choice={},
                user_state=sample_user_state
            )
            
            # Assert
            assert result['valid'] is False
            assert 'VIP access required' in result['reason']
            assert 'Diana' in result['diana_response'] or 'querido' in result['diana_response']
            assert result['vip_offer'] is not None
            assert result['unlock_requirements'] == ["VIP subscription required"]
            mock_vip_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_non_vip_fragment_skips_validation(self, mock_session, sample_user_state):
        """Test that non-VIP fragments skip VIP validation."""
        # Setup
        non_vip_fragment = MagicMock(spec=NarrativeFragment)
        non_vip_fragment.id = "test_fragment_free_01"
        non_vip_fragment.requires_vip = False
        non_vip_fragment.storyline_level = 2
        non_vip_fragment.required_clues = []
        
        decision_service = MVPDecisionTreeService(mock_session)
        
        # Mock VIP service - should not be called
        with patch.object(decision_service.vip_service, 'check_content_access') as mock_vip_check:
            # Execute
            result = await decision_service._validate_user_prerequisites(
                user_id=123456789,
                fragment=non_vip_fragment,
                selected_choice={},
                user_state=sample_user_state
            )
            
            # Assert
            assert result['valid'] is True
            mock_vip_check.assert_not_called()


class TestAchievementServiceIntegration:
    """Test achievement service integration in decision achievement system."""
    
    @pytest.mark.asyncio
    async def test_achievement_unlocking_success(self, mock_session):
        """Test successful achievement unlocking with proper service integration."""
        # Setup
        achievement_service = DecisionAchievementIntegration(mock_session)
        
        # Mock database queries
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None  # Achievement doesn't exist yet
        mock_session.execute.return_value = mock_result
        
        # Mock achievement service _grant method
        with patch.object(achievement_service.achievement_service, '_grant', return_value=True) as mock_grant:
            with patch.object(achievement_service.point_service, 'add_points') as mock_add_points:
                # Create trigger
                from services.decision_achievement_integration import AchievementTrigger, AchievementTriggerType, AchievementCategory
                
                trigger = AchievementTrigger(
                    trigger_id="test_trigger_01",
                    achievement_id="narrative_explorer",
                    trigger_type=AchievementTriggerType.SINGLE_DECISION,
                    category=AchievementCategory.EXPLORATION,
                    points_reward=50,
                    diana_announcement="✨ Has demostrado ser un verdadero explorador de mis misterios...",
                    lucien_guidance="Well done! Diana values your curiosity.",
                    special_unlocks=["hidden_clue_access"],
                    prerequisites=[],
                    activation_conditions={}
                )
                
                # Execute
                result = await achievement_service._process_triggered_achievements(
                    user_id=123456789,
                    triggers=[trigger],
                    user_context={}
                )
                
                # Assert
                assert len(result['unlocked']) == 1
                assert result['unlocked'][0]['achievement_id'] == "narrative_explorer"
                assert result['unlocked'][0]['points_awarded'] == 50
                assert "Diana" in result['unlocked'][0]['diana_announcement'] or "misterios" in result['unlocked'][0]['diana_announcement']
                assert "Lucien" in result['unlocked'][0]['lucien_guidance'] or "Well done" in result['unlocked'][0]['lucien_guidance']
                assert result['points_awarded'] == 50
                
                mock_grant.assert_called_once()
                mock_add_points.assert_called_once_with(123456789, 50, "achievement_narrative_explorer")
    
    @pytest.mark.asyncio
    async def test_achievement_already_owned(self, mock_session):
        """Test handling of already owned achievements."""
        # Setup
        achievement_service = DecisionAchievementIntegration(mock_session)
        
        # Mock existing achievement in database
        existing_achievement = MagicMock(spec=Achievement)
        existing_achievement.id = "narrative_explorer"
        
        existing_user_achievement = MagicMock(spec=UserAchievement)
        existing_user_achievement.user_id = 123456789
        existing_user_achievement.achievement_id = "narrative_explorer"
        
        # Mock database queries to return existing records
        mock_achievement_result = AsyncMock()
        mock_achievement_result.scalar_one_or_none.return_value = existing_achievement
        
        mock_user_achievement_result = AsyncMock()
        mock_user_achievement_result.scalar_one_or_none.return_value = existing_user_achievement
        
        mock_session.execute.side_effect = [mock_achievement_result, mock_user_achievement_result]
        
        # Create trigger
        from services.decision_achievement_integration import AchievementTrigger, AchievementTriggerType, AchievementCategory
        
        trigger = AchievementTrigger(
            trigger_id="test_trigger_01",
            achievement_id="narrative_explorer",
            trigger_type=AchievementTriggerType.SINGLE_DECISION,
            category=AchievementCategory.EXPLORATION,
            points_reward=50,
            diana_announcement="Already unlocked",
            lucien_guidance="Already unlocked",
            special_unlocks=[],
            prerequisites=[],
            activation_conditions={}
        )
        
        # Execute
        result = await achievement_service._process_triggered_achievements(
            user_id=123456789,
            triggers=[trigger],
            user_context={}
        )
        
        # Assert
        assert len(result['unlocked']) == 0
        assert len(result['already_owned']) == 1
        assert result['already_owned'][0]['achievement_id'] == "narrative_explorer"
        assert result['already_owned'][0]['previously_unlocked'] is True
        assert result['points_awarded'] == 0
    
    @pytest.mark.asyncio
    async def test_achievement_creation_and_unlocking(self, mock_session):
        """Test creation of new achievement and proper unlocking."""
        # Setup
        achievement_service = DecisionAchievementIntegration(mock_session)
        
        # Mock database queries - achievement doesn't exist, user achievement doesn't exist
        mock_empty_result = AsyncMock()
        mock_empty_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_empty_result
        
        # Mock achievement service _grant method
        with patch.object(achievement_service.achievement_service, '_grant', return_value=True) as mock_grant:
            # Create trigger
            from services.decision_achievement_integration import AchievementTrigger, AchievementTriggerType, AchievementCategory
            
            trigger = AchievementTrigger(
                trigger_id="test_trigger_new",
                achievement_id="new_achievement",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.WISDOM,
                points_reward=100,
                diana_announcement="🔮 Has alcanzado un nuevo nivel de comprensión...",
                lucien_guidance="Your wisdom impresses Diana.",
                special_unlocks=["wisdom_path"],
                prerequisites=[],
                activation_conditions={}
            )
            
            # Execute
            result = await achievement_service._process_triggered_achievements(
                user_id=123456789,
                triggers=[trigger],
                user_context={}
            )
            
            # Assert - Achievement was created and granted
            mock_session.add.assert_called()  # Achievement was added to session
            mock_session.flush.assert_called()  # Session was flushed to get ID
            mock_grant.assert_called()
            
            assert len(result['unlocked']) == 1
            assert result['unlocked'][0]['achievement_id'] == "new_achievement"


class TestDatabaseOptimization:
    """Test database query optimization implementations."""
    
    @pytest.mark.asyncio
    async def test_optimized_fragment_query(self, mock_session):
        """Test optimized fragment query with proper model usage."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        # Mock fragment data
        mock_fragment = MagicMock(spec=NarrativeFragment)
        mock_fragment.id = "test_fragment_01"
        mock_fragment.title = "Test Fragment"
        mock_fragment.content = "Test content"
        mock_fragment.fragment_type = "STORY"
        mock_fragment.choices = []
        mock_fragment.triggers = {}
        
        # Mock database result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_fragment
        mock_session.execute.return_value = mock_result
        
        # Mock cache methods
        with patch.object(optimizer, 'get_cached_fragment', return_value=None):
            with patch.object(optimizer, 'cache_fragment') as mock_cache:
                # Execute
                result = await optimizer.optimize_fragment_query("test_fragment_01")
                
                # Assert
                assert result is not None
                assert result['id'] == "test_fragment_01"
                assert result['title'] == "Test Fragment"
                mock_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_hit_optimization(self, mock_session):
        """Test that cache hits skip database queries."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        cached_data = {
            'id': 'cached_fragment_01',
            'title': 'Cached Fragment',
            'content': 'Cached content',
            'fragment_type': 'INFO'
        }
        
        # Mock cache hit
        with patch.object(optimizer, 'get_cached_fragment', return_value=cached_data):
            # Execute
            result = await optimizer.optimize_fragment_query("cached_fragment_01")
            
            # Assert
            assert result == cached_data
            mock_session.execute.assert_not_called()  # Database wasn't queried


class TestMemoryManagement:
    """Test memory management and cache eviction policies."""
    
    @pytest.mark.asyncio
    async def test_memory_limits_configuration(self, mock_session):
        """Test that memory limits are properly configured."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        # Assert
        assert optimizer.max_cache_memory_mb == 50
        assert optimizer.critical_memory_threshold_mb == 40
        assert optimizer.max_cache_memory_mb > optimizer.critical_memory_threshold_mb
    
    @pytest.mark.asyncio
    async def test_cache_size_management(self, mock_session):
        """Test cache size management with entry limits."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        # Fill fragment cache beyond limit
        for i in range(150):  # Exceeds the 100 entry limit
            optimizer.fragment_cache[f"fragment_{i}"] = {
                'data': f'Fragment {i}',
                'last_accessed': datetime.now().timestamp() - i  # Older entries have lower timestamps
            }
        
        # Execute cache management
        await optimizer._manage_cache_size('fragment')
        
        # Assert
        assert len(optimizer.fragment_cache) <= 100  # Should be reduced to limit
    
    @pytest.mark.asyncio
    async def test_emergency_memory_cleanup(self, mock_session):
        """Test emergency memory cleanup procedures."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        # Fill all caches with test data
        for i in range(50):
            optimizer.fragment_cache[f"fragment_{i}"] = {
                'data': f'Fragment {i}',
                'last_accessed': datetime.now().timestamp() - i
            }
            optimizer.state_cache[f"state_{i}"] = {
                'data': f'State {i}',
                'last_accessed': datetime.now().timestamp() - i
            }
            optimizer.validation_cache[f"validation_{i}"] = {
                'data': f'Validation {i}',
                'last_accessed': datetime.now().timestamp() - i
            }
            optimizer.query_cache[f"query_{i}"] = {
                'data': f'Query {i}',
                'last_accessed': datetime.now().timestamp() - i
            }
        
        # Execute emergency cleanup
        await optimizer._emergency_memory_cleanup()
        
        # Assert
        assert len(optimizer.fragment_cache) <= 10  # Reduced to emergency limit
        assert len(optimizer.state_cache) <= 20     # Reduced to emergency limit
        assert len(optimizer.validation_cache) == 0  # Completely cleared
        assert len(optimizer.query_cache) == 0       # Completely cleared
    
    @pytest.mark.asyncio
    async def test_memory_optimization_triggers(self, mock_session):
        """Test memory optimization trigger conditions."""
        # Setup
        optimizer = DecisionPerformanceOptimizer(mock_session)
        
        # Mock memory calculation to exceed thresholds
        with patch.object(optimizer, '_cleanup_oversized_caches') as mock_cleanup:
            with patch.object(optimizer, '_emergency_memory_cleanup') as mock_emergency:
                # Test critical threshold trigger
                context = {'total_cache_size_bytes': 45 * 1024 * 1024}  # 45MB - exceeds critical threshold
                await optimizer._optimize_memory_usage(context)
                mock_cleanup.assert_called_once()
                
                # Reset mocks
                mock_cleanup.reset_mock()
                mock_emergency.reset_mock()
                
                # Test maximum threshold trigger
                context = {'total_cache_size_bytes': 55 * 1024 * 1024}  # 55MB - exceeds maximum
                await optimizer._optimize_memory_usage(context)
                mock_emergency.assert_called_once()


class TestCharacterConsistency:
    """Test character consistency preservation throughout integrations."""
    
    @pytest.mark.asyncio
    async def test_vip_denial_maintains_diana_personality(self, mock_session, sample_fragment, sample_user_state):
        """Test that VIP access denial maintains Diana's mysterious personality."""
        # Setup
        decision_service = MVPDecisionTreeService(mock_session)
        
        # Mock VIP service to return character-consistent denial
        with patch.object(decision_service.vip_service, 'check_content_access') as mock_vip_check:
            mock_vip_result = MagicMock()
            mock_vip_result.has_access = False
            mock_vip_result.reason = AccessDecisionReason.VIP_REQUIRED
            mock_vip_result.narrative_justification = "💎 Los misterios más profundos requieren una conexión especial, querido. ¿Estás preparado para ese nivel de intimidad?"
            mock_vip_check.return_value = mock_vip_result
            
            # Execute
            result = await decision_service._validate_user_prerequisites(
                user_id=123456789,
                fragment=sample_fragment,
                selected_choice={},
                user_state=sample_user_state
            )
            
            # Assert Diana personality elements
            diana_response = result['diana_response']
            assert any(word in diana_response.lower() for word in ['querido', 'misterio', 'secreto', 'profundo'])
            assert '💎' in diana_response or '🔮' in diana_response or '✨' in diana_response  # Diana's signature emojis
    
    @pytest.mark.asyncio
    async def test_achievement_announcements_preserve_character(self, mock_session):
        """Test that achievement announcements preserve Diana/Lucien character voices."""
        # Setup
        achievement_service = DecisionAchievementIntegration(mock_session)
        
        # Mock successful achievement grant
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        with patch.object(achievement_service.achievement_service, '_grant', return_value=True):
            with patch.object(achievement_service.point_service, 'add_points'):
                # Create trigger with character-consistent messaging
                from services.decision_achievement_integration import AchievementTrigger, AchievementTriggerType, AchievementCategory
                
                trigger = AchievementTrigger(
                    trigger_id="character_test",
                    achievement_id="mystery_seeker",
                    trigger_type=AchievementTriggerType.PATTERN_BASED,
                    category=AchievementCategory.CHARACTER_DEVELOPMENT,
                    points_reward=75,
                    diana_announcement="🔮 Ah, querido... has comenzado a ver más allá del velo de la realidad. Tu búsqueda de mis secretos me... intriga.",
                    lucien_guidance="Your dedication to understanding Diana's mysteries has been noted. She values those who seek deeper truths.",
                    special_unlocks=["deeper_insight"],
                    prerequisites=[],
                    activation_conditions={}
                )
                
                # Execute
                result = await achievement_service._process_triggered_achievements(
                    user_id=123456789,
                    triggers=[trigger],
                    user_context={}
                )
                
                # Assert character voice preservation
                unlocked = result['unlocked'][0]
                diana_msg = unlocked['diana_announcement']
                lucien_msg = unlocked['lucien_guidance']
                
                # Diana characteristics: mysterious, seductive, Spanish terms of endearment
                assert any(word in diana_msg.lower() for word in ['querido', 'secreto', 'misterio', 'intriga'])
                assert '🔮' in diana_msg or '💎' in diana_msg or '✨' in diana_msg
                
                # Lucien characteristics: supportive, coordinating, explanatory
                assert 'Diana' in lucien_msg  # Lucien often mentions Diana
                assert any(word in lucien_msg.lower() for word in ['understanding', 'dedication', 'noted', 'values'])


if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([__file__, "-v", "--tb=short"])