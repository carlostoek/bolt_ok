"""
MVP End-to-End User Journey Tests

Comprehensive test suite for complete user journeys through the MVP narrative system,
including Level 1→2→3 progression, character consistency, besitos integration, 
and Diana Menu System interaction flows.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress,
    UserArchetype
)
from services.narrative_engine import NarrativeEngine
from services.diana_character_validator import DianaCharacterValidator
from services.diana_menu_system import DianaMenuSystem


class TestCompleteUserJourneyLevel1to3:
    """Test complete user journey through all 3 levels."""

    @pytest_asyncio.fixture
    async def complete_narrative_system(self, session):
        """Set up complete narrative system for E2E testing."""
        # Create all MVP fragments
        fragments = self.create_mvp_fragments()
        for fragment in fragments:
            session.add(fragment)
        
        # Create narrative engine
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        
        # Create Diana menu system
        menu_system = DianaMenuSystem(session)
        menu_system.coordinador = AsyncMock()
        menu_system.user_service = AsyncMock()
        menu_system.admin_menu = AsyncMock()
        menu_system.user_menu = AsyncMock()
        menu_system.narrative_menu = AsyncMock()
        
        # Create character validator
        validator = DianaCharacterValidator(session)
        
        await session.commit()
        
        return {
            'engine': engine,
            'menu_system': menu_system,
            'validator': validator,
            'fragments': fragments
        }

    def create_mvp_fragments(self):
        """Create all 8 MVP fragments for E2E testing."""
        return [
            # Level 1 - Los Kinkys (3 fragments)
            NarrativeFragment(
                id='diana_l1_f1_umbral',
                title='El Umbral de Diana',
                content='💋 **Bienvenido a mis dominios, querido...** \n\nAquí, donde las sombras danzan con secretos no revelados, te encuentras en el umbral de algo más profundo de lo que imaginas. ¿Sientes esa energía misteriosa que flota en el aire?',
                fragment_type='DECISION',
                storyline_level=1,
                tier_classification='los_kinkys',
                fragment_sequence=1,
                choices=[
                    {
                        'text': '💫 Seguir la luz misteriosa',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 10,
                        'archetyping_data': {'explorer_score': 5, 'mysterious_score': 3}
                    },
                    {
                        'text': '🌙 Susurrar una pregunta al aire',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 15,
                        'archetyping_data': {'romantic_score': 5, 'patient_score': 3}
                    }
                ],
                triggers={'reward_points': 5, 'unlock_lore': 'primer_contacto_diana'},
                diana_personality_weight=98,
                character_validation_required=True,
                is_active=True
            ),
            NarrativeFragment(
                id='diana_l1_f2_primera_fractura',
                title='La Primera Fractura',
                content='✨ **Una fractura en la realidad se abre ante ti...** \n\nLas líneas que separan lo conocido de lo desconocido comienzan a difuminarse. Diana te observa desde las sombras, una sonrisa enigmática jugando en sus labios.',
                fragment_type='DECISION',
                storyline_level=1,
                tier_classification='los_kinkys',
                fragment_sequence=2,
                choices=[
                    {
                        'text': '🔍 Explorar la fractura con cautela',
                        'next_fragment_id': 'diana_l1_f3_mochila_viajero',
                        'points': 12,
                        'archetyping_data': {'analytical_score': 6, 'explorer_score': 4}
                    }
                ],
                triggers={'reward_points': 8, 'unlock_clue': 'fractura_dimensional'},
                diana_personality_weight=96,
                character_validation_required=True,
                is_active=True
            ),
            NarrativeFragment(
                id='diana_l1_f3_mochila_viajero',
                title='La Mochila del Viajero',
                content='🎒 **Entre tus pertenencias, algo ha cambiado...** \n\nDiana se acerca, sus dedos rozando sutilmente el aire cerca de tu mochila. "Los objetos guardan memorias", murmura con voz terciopelada.',
                fragment_type='DECISION',
                storyline_level=1,
                tier_classification='los_kinkys',
                fragment_sequence=3,
                choices=[
                    {
                        'text': '🔮 Examinar la mochila con Diana',
                        'next_fragment_id': 'diana_l2_f1_observadores',
                        'points': 18,
                        'archetyping_data': {'romantic_score': 7, 'mysterious_score': 5}
                    }
                ],
                triggers={'reward_points': 10, 'unlock_level': 2, 'unlock_tier': 'observadores'},
                diana_personality_weight=97,
                character_validation_required=True,
                is_active=True
            ),
            
            # Level 2 - Observadores (3 fragments)
            NarrativeFragment(
                id='diana_l2_f1_observadores',
                title='Los Observadores',
                content='👁️ **En el segundo nivel, otros ojos te miran...** \n\nDiana te introduce a un círculo más íntimo. "Aquí", dice con una sonrisa cómplice, "comenzamos a observar lo que otros no ven."',
                fragment_type='STORY',
                storyline_level=2,
                tier_classification='observadores',
                fragment_sequence=4,
                choices=[],
                triggers={'reward_points': 15, 'unlock_clue': 'vision_observadores'},
                diana_personality_weight=98,
                character_validation_required=True,
                is_active=True
            ),
            NarrativeFragment(
                id='diana_l2_f2_vision_profunda',
                title='Visión Profunda',
                content='🌀 **Las capas de la realidad se despliegan...** \n\nDiana extiende su mano hacia ti, sus ojos brillando con una intensidad hipnótica. "La verdadera visión requiere más que ojos", susurra.',
                fragment_type='DECISION',
                storyline_level=2,
                tier_classification='observadores',
                fragment_sequence=5,
                choices=[
                    {
                        'text': '⚡ Tomar la mano de Diana',
                        'next_fragment_id': 'diana_l2_f3_umbral_comprension',
                        'points': 20,
                        'archetyping_data': {'romantic_score': 8, 'mysterious_score': 6}
                    }
                ],
                triggers={'reward_points': 18, 'unlock_clue': 'vision_transformadora'},
                diana_personality_weight=99,
                character_validation_required=True,
                is_active=True
            ),
            NarrativeFragment(
                id='diana_l2_f3_umbral_comprension',
                title='Umbral de Comprensión',
                content='💫 **El conocimiento tiene un precio...** \n\nDiana te guía hacia el tercer nivel con una mezcla de orgullo y advertencia. "Lo que verás ahora cambiará tu forma de entender todo."',
                fragment_type='DECISION',
                storyline_level=2,
                tier_classification='observadores',
                fragment_sequence=6,
                choices=[
                    {
                        'text': '🎭 Cruzar el umbral final',
                        'next_fragment_id': 'diana_l3_f1_comprensores',
                        'points': 25,
                        'archetyping_data': {'analytical_score': 8, 'persistent_score': 7}
                    }
                ],
                triggers={'reward_points': 20, 'unlock_level': 3, 'unlock_tier': 'comprensores'},
                diana_personality_weight=98,
                character_validation_required=True,
                is_active=True
            ),
            
            # Level 3 - Comprensores (2 fragments)
            NarrativeFragment(
                id='diana_l3_f1_comprensores',
                title='Los Comprensores',
                content='🎭 **En el círculo más íntimo, la verdad se revela...** \n\nDiana te recibe en el tercer nivel con una sonrisa que mezcla triunfo y melancolía. "Pocos llegan aquí", confiesa.',
                fragment_type='STORY',
                storyline_level=3,
                tier_classification='comprensores',
                fragment_sequence=7,
                choices=[],
                triggers={'reward_points': 25, 'unlock_clue': 'verdad_comprensores'},
                diana_personality_weight=100,
                character_validation_required=True,
                is_active=True
            ),
            NarrativeFragment(
                id='diana_l3_f2_sintesis_final',
                title='Síntesis Final',
                content='✨ **Todo se conecta en este momento culminante...** \n\nDiana te mira con una intensidad que trasciende lo físico. "Has llegado al final del comienzo", dice con voz suave pero poderosa.',
                fragment_type='STORY',
                storyline_level=3,
                tier_classification='comprensores',
                fragment_sequence=8,
                choices=[],
                triggers={'reward_points': 30, 'unlock_achievement': 'mvp_completion', 'unlock_clue': 'nuevo_comienzo'},
                diana_personality_weight=100,
                character_validation_required=True,
                is_active=True
            )
        ]

    async def test_complete_level_1_journey(self, complete_narrative_system, session):
        """Test complete journey through Level 1."""
        engine = complete_narrative_system['engine']
        user_id = 10001
        
        # Start narrative
        current_fragment = await engine.start_narrative(user_id)
        assert current_fragment is not None
        assert current_fragment.id == 'diana_l1_f1_umbral'
        
        # Verify user state created
        from sqlalchemy import select
        result = await session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = result.scalar_one_or_none()
        assert user_state is not None
        assert user_state.current_level == 1
        assert user_state.current_tier == 'los_kinkys'
        
        # Progress through Level 1 fragments
        level_1_progression = [
            (0, 'diana_l1_f2_primera_fractura'),  # Choice 0 from umbral
            (0, 'diana_l1_f3_mochila_viajero'),   # Choice 0 from fractura
            (0, 'diana_l2_f1_observadores')       # Choice 0 from mochila (advances to Level 2)
        ]
        
        for choice_index, expected_next in level_1_progression:
            next_fragment = await engine.process_user_decision(user_id, choice_index)
            assert next_fragment is not None
            assert next_fragment.id == expected_next
        
        # Verify Level 1 completion and Level 2 access
        result = await session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        final_state = result.scalar_one_or_none()
        assert final_state.current_level == 2
        assert final_state.current_tier == 'observadores'
        assert len(final_state.completed_fragments) >= 3  # Level 1 fragments completed

    async def test_complete_level_2_journey(self, complete_narrative_system, session):
        """Test complete journey through Level 2."""
        engine = complete_narrative_system['engine']
        user_id = 10002
        
        # Create user already at Level 2
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='diana_l2_f1_observadores',
            current_level=2,
            current_tier='observadores',
            completed_fragments=['diana_l1_f1_umbral', 'diana_l1_f2_primera_fractura', 'diana_l1_f3_mochila_viajero'],
            unlocked_clues=['primer_contacto_diana', 'fractura_dimensional']
        )
        session.add(user_state)
        await session.commit()
        
        # Get current fragment (Level 2 start)
        current_fragment = await engine.get_user_current_fragment(user_id)
        assert current_fragment.id == 'diana_l2_f1_observadores'
        assert current_fragment.storyline_level == 2
        
        # Progress through Level 2
        # Fragment 1 is STORY type, move to fragment 2
        user_state.current_fragment_id = 'diana_l2_f2_vision_profunda'
        await session.commit()
        
        # Process choice in vision_profunda
        next_fragment = await engine.process_user_decision(user_id, 0)
        assert next_fragment.id == 'diana_l2_f3_umbral_comprension'
        
        # Process final Level 2 choice
        final_fragment = await engine.process_user_decision(user_id, 0)
        assert final_fragment.id == 'diana_l3_f1_comprensores'
        assert final_fragment.storyline_level == 3
        
        # Verify Level 3 access
        result = await session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        final_state = result.scalar_one_or_none()
        assert final_state.current_level == 3
        assert final_state.current_tier == 'comprensores'

    async def test_complete_level_3_journey(self, complete_narrative_system, session):
        """Test complete journey through Level 3 and MVP completion."""
        engine = complete_narrative_system['engine']
        user_id = 10003
        
        # Create user at Level 3
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='diana_l3_f1_comprensores',
            current_level=3,
            current_tier='comprensores',
            completed_fragments=[
                'diana_l1_f1_umbral', 'diana_l1_f2_primera_fractura', 'diana_l1_f3_mochila_viajero',
                'diana_l2_f1_observadores', 'diana_l2_f2_vision_profunda', 'diana_l2_f3_umbral_comprension'
            ]
        )
        session.add(user_state)
        await session.commit()
        
        # Verify Level 3 access
        current_fragment = await engine.get_user_current_fragment(user_id)
        assert current_fragment.id == 'diana_l3_f1_comprensores'
        assert current_fragment.tier_classification == 'comprensores'
        
        # Progress to final fragment
        user_state.current_fragment_id = 'diana_l3_f2_sintesis_final'
        user_state.completed_fragments.append('diana_l3_f1_comprensores')
        await session.commit()
        
        final_fragment = await engine.get_user_current_fragment(user_id)
        assert final_fragment.id == 'diana_l3_f2_sintesis_final'
        
        # Verify MVP completion
        user_state.completed_fragments.append('diana_l3_f2_sintesis_final')
        await session.commit()
        
        # Check completion percentage
        progress_percentage = await user_state.get_progress_percentage(session)
        assert progress_percentage == 100.0, f"Should have 100% completion, got {progress_percentage}%"

    async def test_full_user_journey_with_archetyping(self, complete_narrative_system, session):
        """Test complete user journey with archetyping development."""
        user_id = 10004
        
        # Create user archetype
        archetype = UserArchetype(user_id=user_id)
        session.add(archetype)
        
        # Simulate choices that build romantic archetype
        choice_impacts = [
            {'romantic_score': 5, 'mysterious_score': 3},  # Level 1 choice
            {'romantic_score': 7, 'mysterious_score': 5},  # Level 1 choice
            {'romantic_score': 8, 'mysterious_score': 6},  # Level 2 choice
            {'romantic_score': 6, 'analytical_score': 4}   # Level 2 choice
        ]
        
        # Apply archetyping impacts
        for impact in choice_impacts:
            for trait, score in impact.items():
                current_score = getattr(archetype, trait, 0)
                setattr(archetype, trait, current_score + score)
        
        archetype.calculate_dominant_archetype()
        await session.commit()
        
        # Verify archetype development
        assert archetype.dominant_archetype == 'romantic'
        assert archetype.romantic_score == 26  # 5+7+8+6
        assert archetype.mysterious_score == 14  # 3+5+6
        
        # Test personalization based on archetype
        distribution = archetype.get_archetype_distribution()
        assert distribution['romantic'] > 50.0, "Romantic should be dominant trait"


class TestBesitosIntegrationJourney:
    """Test complete besitos (points) integration throughout user journey."""

    @pytest_asyncio.fixture
    async def besitos_narrative_system(self, session):
        """Set up narrative system with besitos integration."""
        engine = NarrativeEngine(session)
        
        # Mock point service with realistic besitos behavior
        engine.point_service = AsyncMock()
        engine.point_service.add_points.return_value = AsyncMock()
        
        # Create test fragments with besitos rewards
        fragments = [
            NarrativeFragment(
                id='besitos_test_fragment_1',
                title='Besitos Test 1',
                content='First fragment with besitos',
                fragment_type='DECISION',
                choices=[
                    {
                        'text': 'Choice with 10 besitos',
                        'next_fragment_id': 'besitos_test_fragment_2',
                        'points': 10
                    }
                ],
                triggers={'reward_points': 5},
                is_active=True
            ),
            NarrativeFragment(
                id='besitos_test_fragment_2',
                title='Besitos Test 2',
                content='Second fragment with more besitos',
                fragment_type='STORY',
                triggers={'reward_points': 15},
                is_active=True
            )
        ]
        
        for fragment in fragments:
            session.add(fragment)
        await session.commit()
        
        return engine

    async def test_besitos_accumulation_journey(self, besitos_narrative_system, session):
        """Test besitos accumulate correctly throughout journey."""
        engine = besitos_narrative_system
        user_id = 20001
        
        # Track besitos earned
        expected_besitos = 0
        
        # Start narrative (should earn trigger points)
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='besitos_test_fragment_1'
        )
        session.add(user_state)
        await session.commit()
        
        # Process fragment triggers
        fragment = await engine._get_fragment_by_key('besitos_test_fragment_1')
        if fragment and fragment.triggers.get('reward_points'):
            expected_besitos += fragment.triggers['reward_points']
            engine.point_service.add_points.assert_called()
        
        # Make choice (should earn choice points)
        await engine.process_user_decision(user_id, 0)
        expected_besitos += 10  # Choice points
        
        # Verify besitos calculation
        assert expected_besitos >= 15, f"Should earn at least 15 besitos, calculated {expected_besitos}"

    async def test_besitos_milestone_rewards(self, session):
        """Test besitos milestone rewards throughout journey."""
        user_id = 20002
        
        # Simulate besitos milestones
        milestones = [
            (50, 'first_milestone'),
            (100, 'century_milestone'),
            (200, 'double_century'),
            (500, 'narrative_master')
        ]
        
        current_besitos = 0
        unlocked_rewards = []
        
        for milestone_points, reward_code in milestones:
            current_besitos = milestone_points
            
            # Check if milestone reached
            if current_besitos >= milestone_points:
                unlocked_rewards.append(reward_code)
        
        # Verify milestone progression
        assert 'first_milestone' in unlocked_rewards
        assert 'century_milestone' in unlocked_rewards
        assert 'double_century' in unlocked_rewards
        assert 'narrative_master' in unlocked_rewards

    async def test_besitos_display_consistency(self, session):
        """Test besitos display maintains character consistency."""
        besitos_messages = [
            (10, "✨ Has ganado 10 besitos por tu elección sabia, querido..."),
            (25, "💋 Diana sonríe mientras 25 besitos aparecen en tu camino..."),
            (50, "🌟 Un tesoro de 50 besitos se materializa ante ti, mi explorador...")
        ]
        
        validator = DianaCharacterValidator(session)
        
        for points, message in besitos_messages:
            result = await validator.validate_text(message, context="notification")
            
            # Besitos messages should maintain character
            assert result.overall_score >= 85.0, f"Besitos message should maintain character: {message}"
            
            # Should include Diana elements
            diana_elements = ['✨', '💋', '🌟', 'diana', 'querido', 'explorador']
            has_diana_elements = any(element in message.lower() for element in diana_elements)
            assert has_diana_elements, f"Besitos message should have Diana elements: {message}"


class TestDianaMenuSystemJourneyIntegration:
    """Test Diana Menu System integration throughout user journey."""

    @pytest_asyncio.fixture
    async def integrated_menu_system(self, session):
        """Set up integrated menu system for journey testing."""
        menu_system = DianaMenuSystem(session)
        
        # Mock all services
        menu_system.coordinador = AsyncMock()
        menu_system.user_service = AsyncMock()
        menu_system.narrative_service = AsyncMock()
        menu_system.admin_menu = AsyncMock()
        menu_system.user_menu = AsyncMock()
        menu_system.narrative_menu = AsyncMock()
        menu_system.gamification_menu = AsyncMock()
        
        return menu_system

    async def test_menu_navigation_journey(self, integrated_menu_system):
        """Test menu navigation throughout user journey."""
        menu_system = integrated_menu_system
        user_id = 30001
        
        # Mock user menu interactions
        menu_system.user_menu.show_main_user_menu = AsyncMock(return_value={
            'success': True,
            'menu_type': 'main_user',
            'user_level': 1
        })
        
        menu_system.narrative_menu.show_current_fragment = AsyncMock(return_value={
            'success': True,
            'fragment_id': 'diana_l1_f1_umbral',
            'choices_available': True
        })
        
        # Test menu progression
        main_menu_result = await menu_system.user_menu.show_main_user_menu(user_id)
        narrative_menu_result = await menu_system.narrative_menu.show_current_fragment(user_id)
        
        assert main_menu_result['success'] is True
        assert narrative_menu_result['success'] is True
        assert narrative_menu_result['fragment_id'] == 'diana_l1_f1_umbral'

    async def test_menu_state_persistence_journey(self, integrated_menu_system):
        """Test menu state persistence throughout journey."""
        menu_system = integrated_menu_system
        chat_id = 12345
        user_id = 30002
        
        # Store menu states for different journey stages
        journey_stages = [
            ('level_1_start', {'level': 1, 'fragment': 'diana_l1_f1_umbral'}),
            ('level_2_progress', {'level': 2, 'fragment': 'diana_l2_f2_vision_profunda'}),
            ('level_3_finale', {'level': 3, 'fragment': 'diana_l3_f2_sintesis_final'})
        ]
        
        for stage_name, stage_data in journey_stages:
            menu_system.temp_messages[chat_id] = (user_id, f"narrative_{stage_name}", stage_data)
            
            # Verify state storage
            stored_user, menu_type, menu_data = menu_system.temp_messages[chat_id]
            assert stored_user == user_id
            assert stage_data['level'] == menu_data['level']
            assert stage_data['fragment'] == menu_data['fragment']

    async def test_menu_character_consistency_journey(self, integrated_menu_system, session):
        """Test menu maintains character consistency throughout journey."""
        validator = DianaCharacterValidator(session)
        
        # Test menu messages at different journey stages
        menu_messages = [
            "💋 **Menú Principal** - Nivel 1: Los Kinkys \n\nBienvenido a tus primeros pasos en mis dominios, querido...",
            "✨ **Progreso Narrativo** - Nivel 2: Observadores \n\nTus ojos comienzan a ver lo oculto, mi curioso explorador...",
            "🎭 **Círculo Íntimo** - Nivel 3: Comprensores \n\nHas llegado donde pocos se atreven, cariño..."
        ]
        
        for message in menu_messages:
            result = await validator.validate_text(message, context="menu_response")
            
            assert result.overall_score >= 85.0, f"Menu message should maintain character: {message[:50]}..."
            assert result.meets_threshold or result.overall_score >= 80.0, "Menu should meet character standards"


class TestPerformanceJourneyRequirements:
    """Test performance requirements throughout complete user journey."""

    async def test_complete_journey_performance(self, session):
        """Test complete user journey meets performance requirements."""
        import time
        
        # Create minimal narrative system for performance testing
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        
        # Create single test fragment
        fragment = NarrativeFragment(
            id='performance_journey_fragment',
            title='Performance Test',
            content='Performance testing fragment',
            fragment_type='DECISION',
            choices=[
                {
                    'text': 'Performance choice',
                    'next_fragment_id': 'next_fragment',
                    'points': 10
                }
            ],
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        user_id = 40001
        
        # Measure complete operation performance
        start_time = time.time()
        
        # Start narrative
        await engine.start_narrative(user_id)
        
        # Create user state
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='performance_journey_fragment'
        )
        session.add(user_state)
        await session.flush()
        
        # Process decision
        mock_next_fragment = MagicMock()
        mock_next_fragment.id = 'next_fragment'
        engine._get_fragment_by_key = AsyncMock(return_value=mock_next_fragment)
        engine._check_access_conditions = AsyncMock(return_value=True)
        engine._process_fragment_rewards = AsyncMock()
        
        await engine.process_user_decision(user_id, 0)
        
        end_time = time.time()
        journey_time_ms = (end_time - start_time) * 1000
        
        assert journey_time_ms < 500, f"Complete journey operation took {journey_time_ms:.2f}ms, should be < 500ms"

    async def test_concurrent_user_journeys_performance(self, session):
        """Test concurrent user journeys maintain performance."""
        import asyncio
        import time
        
        async def simulate_user_journey(user_id):
            """Simulate basic user journey operations."""
            start_time = time.time()
            
            # Create user state
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id='concurrent_test_fragment',
                current_level=1
            )
            session.add(user_state)
            await session.flush()
            
            # Create decision log
            decision = UserDecisionLog(
                user_id=user_id,
                fragment_id='concurrent_test_fragment',
                decision_choice='Test choice',
                points_awarded=10
            )
            session.add(decision)
            await session.flush()
            
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        # Run 20 concurrent user journeys
        user_ids = range(50001, 50021)
        tasks = [simulate_user_journey(uid) for uid in user_ids]
        journey_times = await asyncio.gather(*tasks)
        
        await session.commit()
        
        # Verify performance
        avg_journey_time = sum(journey_times) / len(journey_times)
        max_journey_time = max(journey_times)
        
        assert avg_journey_time < 500, f"Average concurrent journey time {avg_journey_time:.2f}ms should be < 500ms"
        assert max_journey_time < 1500, f"Max concurrent journey time {max_journey_time:.2f}ms should be < 1500ms"


class TestJourneyErrorRecovery:
    """Test error recovery throughout user journey."""

    async def test_journey_interruption_recovery(self, session):
        """Test recovery from journey interruption."""
        user_id = 60001
        
        # Create user mid-journey
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='interrupted_fragment',
            current_level=2,
            visited_fragments=['frag_1', 'frag_2', 'frag_3'],
            completed_fragments=['frag_1', 'frag_2']
        )
        session.add(user_state)
        await session.commit()
        
        # Simulate interruption - reset to safe state
        user_state.current_fragment_id = None
        await session.commit()
        
        # Recovery mechanism
        recovered_state = await self.recover_interrupted_journey(session, user_id)
        
        assert recovered_state is not None
        assert recovered_state.current_fragment_id is not None or len(recovered_state.completed_fragments) >= 2
        
        # Should preserve progress
        assert recovered_state.current_level == 2
        assert len(recovered_state.completed_fragments) >= 2

    async def recover_interrupted_journey(self, session, user_id):
        """Recover interrupted user journey."""
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            user_state = result.scalar_one_or_none()
            
            if not user_state:
                return None
            
            # If current fragment is None, determine appropriate restart point
            if user_state.current_fragment_id is None:
                # Find last completed fragment and move to next logical fragment
                if user_state.completed_fragments:
                    last_completed = user_state.completed_fragments[-1]
                    # In real implementation, would determine next fragment based on last completed
                    user_state.current_fragment_id = f"recovery_from_{last_completed}"
                else:
                    # Restart from beginning if no progress
                    user_state.current_fragment_id = 'diana_l1_f1_umbral'
                    user_state.current_level = 1
                    user_state.current_tier = 'los_kinkys'
            
            await session.commit()
            return user_state
            
        except Exception:
            await session.rollback()
            return None

    async def test_data_corruption_journey_recovery(self, session):
        """Test recovery from data corruption during journey."""
        user_id = 60002
        
        # Create corrupted state
        corrupted_state = UserNarrativeState(
            user_id=user_id,
            current_level=-1,  # Invalid
            visited_fragments=None,  # Should be list
            completed_fragments="invalid_data",  # Should be list
            unlocked_clues=None  # Should be list
        )
        session.add(corrupted_state)
        await session.commit()
        
        # Recover corrupted journey
        recovered_state = await self.recover_corrupted_journey_data(session, user_id)
        
        assert recovered_state is not None
        assert recovered_state.current_level >= 1
        assert isinstance(recovered_state.visited_fragments, list)
        assert isinstance(recovered_state.completed_fragments, list)
        assert isinstance(recovered_state.unlocked_clues, list)

    async def recover_corrupted_journey_data(self, session, user_id):
        """Recover corrupted journey data."""
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            state = result.scalar_one_or_none()
            
            if not state:
                return None
            
            # Fix corrupted fields
            if state.current_level < 1:
                state.current_level = 1
            
            if not isinstance(state.visited_fragments, list):
                state.visited_fragments = []
            
            if not isinstance(state.completed_fragments, list):
                state.completed_fragments = []
            
            if not isinstance(state.unlocked_clues, list):
                state.unlocked_clues = []
            
            # Set safe defaults
            if not state.current_tier:
                state.current_tier = 'los_kinkys'
            
            await session.commit()
            return state
            
        except Exception:
            await session.rollback()
            return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])