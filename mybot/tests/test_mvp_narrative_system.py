"""
MVP Narrative System Tests
Comprehensive testing framework for the MVP narrative implementation.
"""

import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress,
    UserArchetype
)
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
from services.mvp_narrative_progression_service import MVPNarrativeProgressionService

@pytest_asyncio.fixture
async def mock_session():
    """Mock async session for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session

@pytest_asyncio.fixture
async def sample_fragment():
    """Sample fragment for testing."""
    return NarrativeFragment(
        id='diana_l1_f1_umbral',
        title='El Umbral de Diana',
        content='💋 **Bienvenido a mis dominios, querido...**',
        fragment_type='DECISION',
        storyline_level=1,
        tier_classification='los_kinkys',
        fragment_sequence=1,
        choices=[
            {
                'text': '💫 Seguir la luz misteriosa',
                'next_fragment_id': 'diana_l1_f2_primera_fractura',
                'points': 10,
                'archetyping_data': {'explorer_score': 5}
            }
        ],
        triggers={'reward_points': 5, 'unlock_lore': 'primer_contacto_diana'},
        diana_personality_weight=98,
        character_validation_required=True,
        is_active=True
    )

@pytest_asyncio.fixture
async def sample_user_state():
    """Sample user state for testing."""
    return UserNarrativeState(
        user_id=12345,
        current_fragment_id='diana_l1_f1_umbral',
        visited_fragments=[],
        completed_fragments=[],
        unlocked_clues=[],
        current_level=1,
        current_tier='los_kinkys'
    )

class TestMVPNarrativeFragmentService:
    """Test suite for MVP narrative fragment service."""
    
    @pytest_asyncio.fixture
    async def fragment_service(self, mock_session):
        """Fragment service with mocked session."""
        return MVPNarrativeFragmentService(mock_session)
    
    async def test_initialize_mvp_fragments_success(self, fragment_service, mock_session):
        """Test successful fragment initialization."""
        # Mock character validator
        with patch.object(fragment_service, 'character_validator') as mock_validator:
            mock_validation = AsyncMock()
            mock_validation.overall_score = 95.0
            mock_validator.validate_text.return_value = mock_validation
            
            # Mock fragment existence check
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # Run initialization
            results = await fragment_service.initialize_mvp_fragments()
            
            # Verify results
            assert results['fragments_processed'] == 8  # All MVP fragments
            assert results['fragments_created'] > 0
            assert len(results['validation_results']) == 8
            assert all(v['meets_requirement'] for v in results['validation_results'])
            
            # Verify database interactions
            assert mock_session.add.call_count == 8
            mock_session.commit.assert_called_once()
    
    async def test_get_user_current_fragment_new_user(self, fragment_service, mock_session, sample_fragment):
        """Test getting current fragment for new user."""
        # Mock user state creation
        fragment_service._get_or_create_user_state = AsyncMock(return_value=UserNarrativeState(
            user_id=12345,
            current_fragment_id=None
        ))
        
        # Mock fragment retrieval
        fragment_service._get_fragment_cached = AsyncMock(return_value=sample_fragment)
        
        result = await fragment_service.get_user_current_fragment(12345)
        
        assert result is not None
        assert result.id == 'diana_l1_f1_umbral'
        fragment_service._get_fragment_cached.assert_called_with('diana_l1_f1_umbral')
    
    async def test_process_user_choice_success(self, fragment_service, mock_session, sample_fragment):
        """Test successful user choice processing."""
        # Setup mocks
        fragment_service.get_user_current_fragment = AsyncMock(return_value=sample_fragment)
        fragment_service._get_fragment_cached = AsyncMock(return_value=sample_fragment)
        fragment_service._get_or_create_user_state = AsyncMock(return_value=UserNarrativeState(
            user_id=12345,
            current_fragment_id='diana_l1_f1_umbral',
            visited_fragments=[],
            completed_fragments=[]
        ))
        fragment_service._check_level_progression = AsyncMock(return_value={'progressed': False})
        fragment_service._process_choice_rewards = AsyncMock(return_value={'success': True, 'points_awarded': 10})
        
        result = await fragment_service.process_user_choice(12345, 0)
        
        assert result['success'] is True
        assert result['points_awarded'] == 10
        assert result['next_fragment'] is not None
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    async def test_process_user_choice_invalid_index(self, fragment_service, sample_fragment):
        """Test choice processing with invalid index."""
        fragment_service.get_user_current_fragment = AsyncMock(return_value=sample_fragment)
        
        result = await fragment_service.process_user_choice(12345, 99)  # Invalid index
        
        assert result['success'] is False
        assert 'Invalid choice index' in result['error']
    
    async def test_get_user_progress_summary(self, fragment_service, mock_session):
        """Test user progress summary generation."""
        # Mock user state
        user_state = UserNarrativeState(
            user_id=12345,
            current_level=2,
            current_tier='observadores',
            visited_fragments=['diana_l1_f1_umbral', 'diana_l1_f2_primera_fractura'],
            completed_fragments=['diana_l1_f1_umbral'],
            unlocked_clues=['primer_contacto_diana']
        )
        fragment_service._get_or_create_user_state = AsyncMock(return_value=user_state)
        fragment_service._get_or_create_mission_progress = AsyncMock(return_value=UserMissionProgress(user_id=12345))
        
        result = await fragment_service.get_user_progress_summary(12345)
        
        assert result['current_level'] == 2
        assert result['current_tier'] == 'observadores'
        assert result['current_tier_name'] == 'Observadores'
        assert result['fragments_completed'] == 1
        assert result['total_mvp_fragments'] == 8
        assert 'primer_contacto_diana' in result['unlocked_clues']

class TestMVPNarrativeProgressionService:
    """Test suite for MVP narrative progression service."""
    
    @pytest_asyncio.fixture
    async def progression_service(self, mock_session):
        """Progression service with mocked session."""
        service = MVPNarrativeProgressionService(mock_session)
        service.fragment_service = AsyncMock()
        service.point_service = AsyncMock()
        return service
    
    async def test_start_user_narrative_success(self, progression_service, sample_fragment):
        """Test successful narrative start for new user."""
        # Setup mocks
        progression_service.fragment_service._get_or_create_user_state = AsyncMock(return_value=UserNarrativeState(
            user_id=12345,
            current_fragment_id=None
        ))
        progression_service.fragment_service._get_or_create_mission_progress = AsyncMock(return_value=UserMissionProgress(user_id=12345))
        progression_service.fragment_service._get_fragment_cached = AsyncMock(return_value=sample_fragment)
        progression_service._initialize_user_archetype = AsyncMock()
        
        result = await progression_service.start_user_narrative(12345)
        
        assert result['success'] is True
        assert result['fragment'] == sample_fragment
        assert result['user_level'] == 1
        assert result['user_tier'] == 'los_kinkys'
        progression_service._initialize_user_archetype.assert_called_with(12345)
    
    async def test_process_user_choice_advanced_performance(self, progression_service, mock_session):
        """Test advanced choice processing meets performance requirements."""
        # Mock successful choice processing
        progression_service.fragment_service.get_user_current_fragment = AsyncMock(return_value=NarrativeFragment(
            id='test_fragment',
            fragment_type='DECISION',
            choices=[{'text': 'Test choice', 'points': 10}],
            is_active=True
        ))
        progression_service.fragment_service.process_user_choice = AsyncMock(return_value={
            'success': True,
            'next_fragment': None,
            'points_awarded': 10
        })
        progression_service._update_user_archetype = AsyncMock()
        progression_service._track_interaction_patterns = AsyncMock()
        progression_service.get_comprehensive_progress = AsyncMock(return_value={'current_level': 1})
        
        start_time = time.time()
        result = await progression_service.process_user_choice_advanced(12345, 0)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert result['success'] is True
        assert result['performance_ms'] < 500  # Should meet performance requirement
        assert result['meets_performance_target'] is True
    
    async def test_get_comprehensive_progress(self, progression_service):
        """Test comprehensive progress retrieval."""
        # Setup mocks
        progression_service.fragment_service.get_user_progress_summary = AsyncMock(return_value={
            'current_level': 2,
            'current_tier': 'observadores',
            'fragments_completed': 3,
            'total_mvp_fragments': 8
        })
        progression_service._get_user_archetype_summary = AsyncMock(return_value={
            'dominant_archetype': 'explorer',
            'distribution': {'explorer': 60, 'romantic': 40}
        })
        progression_service._get_interaction_patterns = AsyncMock(return_value={
            'avg_response_time_ms': 15000,
            'engagement_depth': 'highly_engaged'
        })
        progression_service._estimate_level_completion_time = AsyncMock(return_value={
            'estimated_minutes': 5
        })
        
        result = await progression_service.get_comprehensive_progress(12345)
        
        assert result['current_level'] == 2
        assert result['archetype_profile']['dominant_archetype'] == 'explorer'
        assert result['interaction_patterns']['engagement_depth'] == 'highly_engaged'
        assert 'mvp_completion_percentage' in result
    
    async def test_get_next_recommended_action_personalized(self, progression_service, sample_fragment):
        """Test personalized action recommendation based on archetype."""
        progression_service.fragment_service.get_user_current_fragment = AsyncMock(return_value=sample_fragment)
        progression_service._get_user_archetype_summary = AsyncMock(return_value={
            'dominant_archetype': 'romantic'
        })
        
        result = await progression_service.get_next_recommended_action(12345)
        
        assert result['action'] == 'continue_narrative'
        assert result['personalized_for_archetype'] == 'romantic'
        assert '💕' in result['message']  # Should contain romantic-themed message

class TestPerformanceRequirements:
    """Test suite for performance requirements compliance."""
    
    @pytest_asyncio.fixture
    async def services(self, mock_session):
        """Setup services for performance testing."""
        fragment_service = MVPNarrativeFragmentService(mock_session)
        progression_service = MVPNarrativeProgressionService(mock_session)
        return fragment_service, progression_service
    
    async def test_fragment_retrieval_performance(self, services):
        """Test fragment retrieval meets <500ms requirement."""
        fragment_service, _ = services
        
        # Mock fast fragment retrieval
        fragment_service._get_fragment_cached = AsyncMock(return_value=NarrativeFragment(
            id='test_fragment',
            title='Test',
            content='Test content',
            fragment_type='STORY',
            is_active=True
        ))
        fragment_service._get_or_create_user_state = AsyncMock(return_value=UserNarrativeState(
            user_id=12345,
            current_fragment_id='test_fragment'
        ))
        
        # Measure performance
        start_time = time.time()
        await fragment_service.get_user_current_fragment(12345)
        end_time = time.time()
        
        performance_ms = (end_time - start_time) * 1000
        assert performance_ms < 500  # Should meet <500ms requirement
    
    async def test_choice_processing_performance(self, services):
        """Test choice processing performance."""
        fragment_service, progression_service = services
        
        # Setup mocks for fast processing
        test_fragment = NarrativeFragment(
            id='test_fragment',
            fragment_type='DECISION',
            choices=[{'text': 'Test', 'next_fragment_id': 'next_fragment', 'points': 10}],
            is_active=True
        )
        
        fragment_service.get_user_current_fragment = AsyncMock(return_value=test_fragment)
        fragment_service._get_fragment_cached = AsyncMock(return_value=test_fragment)
        fragment_service._get_or_create_user_state = AsyncMock(return_value=UserNarrativeState(user_id=12345))
        fragment_service._check_level_progression = AsyncMock(return_value={'progressed': False})
        fragment_service._process_choice_rewards = AsyncMock(return_value={'success': True})
        
        start_time = time.time()
        result = await fragment_service.process_user_choice(12345, 0)
        end_time = time.time()
        
        performance_ms = (end_time - start_time) * 1000
        assert performance_ms < 500
        assert result['success'] is True

class TestCharacterConsistency:
    """Test suite for character consistency validation."""
    
    async def test_fragment_content_character_validation(self):
        """Test that fragment content meets character consistency requirements."""
        service = MVPNarrativeFragmentService(AsyncMock())
        
        # Get MVP fragment definitions
        fragment_definitions = service._get_mvp_fragment_definitions()
        
        # Verify all fragments have required character elements
        for fragment_data in fragment_definitions:
            content = fragment_data['content']
            
            # Check for Diana personality elements
            assert fragment_data['diana_personality_weight'] >= 95
            assert fragment_data['character_validation_required'] is True
            
            # Check content has character-consistent elements
            diana_elements = ['Diana', 'querido', 'secreto', 'misterio']
            has_diana_elements = any(element.lower() in content.lower() for element in diana_elements)
            assert has_diana_elements, f"Fragment {fragment_data['id']} lacks Diana personality elements"
            
            # Check for proper emotional tone
            emotional_elements = ['💋', '✨', '🌟', '💫', '🌙']
            has_emotional_elements = any(element in content for element in emotional_elements)
            assert has_emotional_elements, f"Fragment {fragment_data['id']} lacks emotional elements"
    
    async def test_level_progression_consistency(self):
        """Test that level progression maintains character consistency."""
        service = MVPNarrativeFragmentService(AsyncMock())
        fragment_definitions = service._get_mvp_fragment_definitions()
        
        # Group by level
        levels = {}
        for fragment in fragment_definitions:
            level = fragment['storyline_level']
            if level not in levels:
                levels[level] = []
            levels[level].append(fragment)
        
        # Verify progression makes narrative sense
        assert 1 in levels and len(levels[1]) == 3  # Level 1: 3 fragments
        assert 2 in levels and len(levels[2]) == 3  # Level 2: 3 fragments  
        assert 3 in levels and len(levels[3]) == 2  # Level 3: 2 fragments
        
        # Verify tier classifications match levels
        for level, fragments in levels.items():
            for fragment in fragments:
                if level == 1:
                    assert fragment['tier_classification'] == 'los_kinkys'
                elif level == 2:
                    assert fragment['tier_classification'] == 'observadores'
                elif level == 3:
                    assert fragment['tier_classification'] == 'comprensores'

class TestIntegrationFlow:
    """Integration tests for complete narrative flow."""
    
    @pytest_asyncio.fixture
    async def integrated_services(self, mock_session):
        """Setup integrated services for flow testing."""
        fragment_service = MVPNarrativeFragmentService(mock_session)
        progression_service = MVPNarrativeProgressionService(mock_session)
        
        # Connect services
        progression_service.fragment_service = fragment_service
        
        return fragment_service, progression_service
    
    async def test_complete_level_1_flow(self, integrated_services, mock_session):
        """Test complete Level 1 narrative flow."""
        fragment_service, progression_service = integrated_services
        
        # Mock fragment definitions loading
        with patch.object(fragment_service, '_get_mvp_fragment_definitions') as mock_get_fragments:
            mock_get_fragments.return_value = fragment_service._get_mvp_fragment_definitions()[:3]  # Level 1 only
            
            # Mock database interactions
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.execute.return_value.scalars.return_value.all.return_value = []
            
            # Test initialization
            results = await fragment_service.initialize_mvp_fragments()
            assert results['fragments_processed'] == 3
            
            # Test user progression through Level 1
            user_id = 12345
            
            # Start narrative
            fragment_service._get_fragment_cached = AsyncMock(side_effect=[
                # Simulate fragment progression
                NarrativeFragment(id='diana_l1_f1_umbral', fragment_type='DECISION', choices=[{'next_fragment_id': 'diana_l1_f2_primera_fractura'}], is_active=True),
                NarrativeFragment(id='diana_l1_f2_primera_fractura', fragment_type='DECISION', choices=[{'next_fragment_id': 'diana_l1_f3_mochila_viajero'}], is_active=True),
                NarrativeFragment(id='diana_l1_f3_mochila_viajero', fragment_type='STORY', is_active=True)
            ])
            
            # Mock user state management
            user_states = []
            def mock_get_user_state(user_id):
                if not user_states:
                    state = UserNarrativeState(user_id=user_id, current_fragment_id=None, completed_fragments=[], current_level=1)
                    user_states.append(state)
                return AsyncMock(return_value=user_states[0])()
            
            fragment_service._get_or_create_user_state = mock_get_user_state
            
            # Simulate user making choices through Level 1
            start_result = await progression_service.start_user_narrative(user_id)
            assert start_result['success'] is True
            assert start_result['user_level'] == 1
            
            # This integration test verifies the flow structure is correct
            # In a real environment, this would test actual database interactions

if __name__ == "__main__":
    pytest.main([__file__, "-v"])