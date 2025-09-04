"""
MVP Narrative Fragment Validation Tests

Comprehensive test suite for validating the 8 MVP narrative fragments
including character consistency, JSON structure, and database operations.
"""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    NarrativeCharacterValidation
)
from services.diana_character_validator import (
    DianaCharacterValidator, 
    DianaPersonalityTrait,
    CharacterValidationResult
)


class TestMVPFragmentStructure:
    """Test MVP fragment structure and validation."""

    def get_mvp_fragment_definitions(self):
        """Get the 8 MVP fragment definitions based on system documentation."""
        return [
            {
                'id': 'diana_l1_f1_umbral',
                'title': 'El Umbral de Diana',
                'content': '💋 **Bienvenido a mis dominios, querido...** \n\nAquí, donde las sombras danzan con secretos no revelados, te encuentras en el umbral de algo más profundo de lo que imaginas. ¿Sientes esa energía misteriosa que flota en el aire? Es solo el comienzo...',
                'fragment_type': 'DECISION',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys',
                'fragment_sequence': 1,
                'choices': [
                    {
                        'text': '💫 Seguir la luz misteriosa',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura',
                        'points': 10,
                        'archetyping_data': {'explorer_score': 5}
                    },
                    {
                        'text': '🌙 Susurrar una pregunta al aire',
                        'next_fragment_id': 'diana_l1_f2_primera_fractura', 
                        'points': 15,
                        'archetyping_data': {'romantic_score': 5, 'mysterious_score': 3}
                    }
                ],
                'triggers': {'reward_points': 5, 'unlock_lore': 'primer_contacto_diana'},
                'diana_personality_weight': 98,
                'character_validation_required': True
            },
            {
                'id': 'diana_l1_f2_primera_fractura',
                'title': 'La Primera Fractura',
                'content': '✨ **Una fractura en la realidad se abre ante ti...** \n\nLas líneas que separan lo conocido de lo desconocido comienzan a difuminarse. Diana te observa desde las sombras, una sonrisa enigmática jugando en sus labios. "¿Acaso pensaste que sería tan simple?", susurra.',
                'fragment_type': 'STORY',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys', 
                'fragment_sequence': 2,
                'choices': [],
                'triggers': {'reward_points': 8, 'unlock_clue': 'fractura_dimensional'},
                'diana_personality_weight': 96,
                'character_validation_required': True
            },
            {
                'id': 'diana_l1_f3_mochila_viajero',
                'title': 'La Mochila del Viajero',
                'content': '🎒 **Entre tus pertenencias, algo ha cambiado...** \n\nDiana se acerca, sus dedos rozando sutilmente el aire cerca de tu mochila. "Los objetos guardan memorias", murmura con voz terciopelada. "¿Qué secretos llevas contigo sin saberlo?"',
                'fragment_type': 'DECISION',
                'storyline_level': 1,
                'tier_classification': 'los_kinkys',
                'fragment_sequence': 3,
                'choices': [
                    {
                        'text': '🔍 Examinar la mochila cuidadosamente',
                        'next_fragment_id': 'diana_l2_f1_observadores',
                        'points': 12,
                        'archetyping_data': {'analytical_score': 6, 'explorer_score': 3}
                    }
                ],
                'triggers': {'reward_points': 6, 'unlock_level': 2},
                'diana_personality_weight': 95,
                'character_validation_required': True
            },
            {
                'id': 'diana_l2_f1_observadores',
                'title': 'Los Observadores',
                'content': '👁️ **En el segundo nivel, otros ojos te miran...** \n\nDiana te introduce a un círculo más íntimo. "Aquí", dice con una sonrisa cómplice, "comenzamos a observar lo que otros no ven. ¿Tienes el valor de mirar más allá del velo?"',
                'fragment_type': 'DECISION',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 4,
                'choices': [
                    {
                        'text': '🔮 Acepto el desafío de ver más allá',
                        'next_fragment_id': 'diana_l2_f2_vision_profunda',
                        'points': 18,
                        'archetyping_data': {'mysterious_score': 7, 'analytical_score': 4}
                    }
                ],
                'triggers': {'reward_points': 10, 'unlock_tier': 'observadores'},
                'diana_personality_weight': 97,
                'character_validation_required': True
            },
            {
                'id': 'diana_l2_f2_vision_profunda',
                'title': 'Visión Profunda',
                'content': '🌀 **Las capas de la realidad se despliegan...** \n\nDiana extiende su mano hacia ti, sus ojos brillando con una intensidad hipnótica. "La verdadera visión requiere más que ojos", susurra. "Requiere alma dispuesta a ser transformada."',
                'fragment_type': 'STORY',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 5,
                'choices': [],
                'triggers': {'reward_points': 15, 'unlock_clue': 'vision_transformadora'},
                'diana_personality_weight': 98,
                'character_validation_required': True
            },
            {
                'id': 'diana_l2_f3_umbral_comprension',
                'title': 'Umbral de Comprensión',
                'content': '💫 **El conocimiento tiene un precio...** \n\nDiana te guía hacia el tercer nivel con una mezcla de orgullo y advertencia. "Lo que verás ahora cambiará tu forma de entender todo", dice, su voz cargada de misterio y promesa.',
                'fragment_type': 'DECISION',
                'storyline_level': 2,
                'tier_classification': 'observadores',
                'fragment_sequence': 6,
                'choices': [
                    {
                        'text': '⚡ Cruzar el umbral de la comprensión',
                        'next_fragment_id': 'diana_l3_f1_comprensores',
                        'points': 25,
                        'archetyping_data': {'analytical_score': 8, 'persistent_score': 5}
                    }
                ],
                'triggers': {'reward_points': 12, 'unlock_level': 3},
                'diana_personality_weight': 96,
                'character_validation_required': True
            },
            {
                'id': 'diana_l3_f1_comprensores',
                'title': 'Los Comprensores',
                'content': '🎭 **En el círculo más íntimo, la verdad se revela...** \n\nDiana te recibe en el tercer nivel con una sonrisa que mezcla triunfo y melancolía. "Pocos llegan aquí", confiesa, "porque la comprensión verdadera exige renunciar a las ilusiones cómodas."',
                'fragment_type': 'STORY',
                'storyline_level': 3,
                'tier_classification': 'comprensores',
                'fragment_sequence': 7,
                'choices': [],
                'triggers': {'reward_points': 20, 'unlock_tier': 'comprensores', 'unlock_clue': 'verdad_profunda'},
                'diana_personality_weight': 99,
                'character_validation_required': True
            },
            {
                'id': 'diana_l3_f2_sintesis_final',
                'title': 'Síntesis Final',
                'content': '✨ **Todo se conecta en este momento culminante...** \n\nDiana te mira con una intensidad que trasciende lo físico. "Has llegado al final del comienzo", dice con voz suave pero poderosa. "Ahora comprendes que el verdadero viaje apenas comienza..." Sus ojos brillan con secretos aún no revelados.',
                'fragment_type': 'STORY',
                'storyline_level': 3,
                'tier_classification': 'comprensores',
                'fragment_sequence': 8,
                'choices': [],
                'triggers': {'reward_points': 30, 'unlock_achievement': 'mvp_completion', 'unlock_clue': 'nuevo_comienzo'},
                'diana_personality_weight': 100,
                'character_validation_required': True
            }
        ]

    async def test_fragment_count_validation(self):
        """Test that exactly 8 MVP fragments are defined."""
        fragments = self.get_mvp_fragment_definitions()
        assert len(fragments) == 8, f"Expected 8 MVP fragments, got {len(fragments)}"

    async def test_fragment_structure_validation(self):
        """Test that all fragments have required structure."""
        fragments = self.get_mvp_fragment_definitions()
        
        required_fields = [
            'id', 'title', 'content', 'fragment_type', 'storyline_level',
            'tier_classification', 'fragment_sequence', 'choices', 'triggers',
            'diana_personality_weight', 'character_validation_required'
        ]
        
        for fragment in fragments:
            for field in required_fields:
                assert field in fragment, f"Fragment {fragment.get('id', 'unknown')} missing field: {field}"

    async def test_fragment_sequence_validation(self):
        """Test that fragment sequences are correct and complete."""
        fragments = self.get_mvp_fragment_definitions()
        sequences = [f['fragment_sequence'] for f in fragments]
        
        assert sorted(sequences) == list(range(1, 9)), "Fragment sequences must be 1-8"
        assert len(set(sequences)) == 8, "All fragment sequences must be unique"

    async def test_level_progression_structure(self):
        """Test that level progression follows correct structure."""
        fragments = self.get_mvp_fragment_definitions()
        
        # Group by level
        levels = {}
        for fragment in fragments:
            level = fragment['storyline_level']
            if level not in levels:
                levels[level] = []
            levels[level].append(fragment)
        
        # Verify structure
        assert 1 in levels and len(levels[1]) == 3, "Level 1 should have 3 fragments"
        assert 2 in levels and len(levels[2]) == 3, "Level 2 should have 3 fragments"
        assert 3 in levels and len(levels[3]) == 2, "Level 3 should have 2 fragments"

    async def test_tier_classification_validation(self):
        """Test that tier classifications match expected progression."""
        fragments = self.get_mvp_fragment_definitions()
        
        expected_tiers = {
            1: 'los_kinkys',
            2: 'observadores', 
            3: 'comprensores'
        }
        
        for fragment in fragments:
            level = fragment['storyline_level']
            tier = fragment['tier_classification']
            expected_tier = expected_tiers[level]
            assert tier == expected_tier, f"Fragment {fragment['id']} level {level} should have tier {expected_tier}, got {tier}"

    async def test_choice_structure_validation(self):
        """Test that choices have correct structure."""
        fragments = self.get_mvp_fragment_definitions()
        
        for fragment in fragments:
            choices = fragment['choices']
            assert isinstance(choices, list), f"Fragment {fragment['id']} choices must be a list"
            
            for i, choice in enumerate(choices):
                required_choice_fields = ['text', 'next_fragment_id', 'points']
                for field in required_choice_fields:
                    assert field in choice, f"Fragment {fragment['id']} choice {i} missing field: {field}"
                
                # Validate archetyping data if present
                if 'archetyping_data' in choice:
                    assert isinstance(choice['archetyping_data'], dict), "Archetyping data must be dict"

    async def test_character_consistency_requirements(self):
        """Test that all fragments meet character consistency requirements."""
        fragments = self.get_mvp_fragment_definitions()
        
        for fragment in fragments:
            # All fragments should require character validation
            assert fragment['character_validation_required'] is True, f"Fragment {fragment['id']} should require character validation"
            
            # All fragments should have high Diana personality weight (>= 95)
            weight = fragment['diana_personality_weight']
            assert weight >= 95, f"Fragment {fragment['id']} Diana personality weight {weight} below minimum 95"

    async def test_content_quality_validation(self):
        """Test content quality meets MVP standards."""
        fragments = self.get_mvp_fragment_definitions()
        
        for fragment in fragments:
            content = fragment['content']
            title = fragment['title']
            
            # Content should not be empty
            assert len(content.strip()) > 0, f"Fragment {fragment['id']} has empty content"
            assert len(title.strip()) > 0, f"Fragment {fragment['id']} has empty title"
            
            # Content should be substantial (MVP requirement)
            assert len(content) >= 100, f"Fragment {fragment['id']} content too short: {len(content)} chars"
            
            # Should contain Diana personality elements
            diana_elements = ['diana', 'susurra', 'murmura', 'misterio', 'secreto']
            has_diana_element = any(element.lower() in content.lower() for element in diana_elements)
            assert has_diana_element, f"Fragment {fragment['id']} lacks Diana personality elements"

    async def test_triggers_validation(self):
        """Test that triggers are properly structured."""
        fragments = self.get_mvp_fragment_definitions()
        
        for fragment in fragments:
            triggers = fragment['triggers']
            assert isinstance(triggers, dict), f"Fragment {fragment['id']} triggers must be dict"
            
            # Should have reward_points
            assert 'reward_points' in triggers, f"Fragment {fragment['id']} missing reward_points in triggers"
            assert isinstance(triggers['reward_points'], int), "reward_points must be integer"
            assert triggers['reward_points'] >= 0, "reward_points must be non-negative"


class TestFragmentCharacterValidation:
    """Test character consistency validation for MVP fragments."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        """Create character validator with session."""
        return DianaCharacterValidator(session)

    async def test_fragment_character_consistency(self, character_validator):
        """Test that all MVP fragments pass character consistency validation."""
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        for fragment_data in fragments:
            # Test content validation
            content = fragment_data['content']
            result = await character_validator.validate_text(content, context="narrative_fragment")
            
            assert result.meets_threshold, f"Fragment {fragment_data['id']} fails character validation: score {result.overall_score}"
            assert result.overall_score >= 95.0, f"Fragment {fragment_data['id']} score {result.overall_score} below 95"

    async def test_choice_text_character_validation(self, character_validator):
        """Test that choice texts maintain character consistency."""
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        for fragment_data in fragments:
            for i, choice in enumerate(fragment_data['choices']):
                choice_text = choice['text']
                result = await character_validator.validate_text(choice_text, context="menu_response")
                
                # Choices can have slightly lower threshold but should still be consistent
                assert result.overall_score >= 85.0, f"Fragment {fragment_data['id']} choice {i} score {result.overall_score} below 85"

    async def test_title_character_validation(self, character_validator):
        """Test that fragment titles maintain character consistency."""
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        for fragment_data in fragments:
            title = fragment_data['title']
            result = await character_validator.validate_text(title, context="narrative_fragment")
            
            # Titles should maintain mysterious quality
            mysterious_score = result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)
            assert mysterious_score >= 15.0, f"Fragment {fragment_data['id']} title lacks mystery: score {mysterious_score}"


class TestFragmentDatabaseOperations:
    """Test database operations for MVP fragments."""

    @pytest_asyncio.fixture
    async def mock_fragment_service(self, session):
        """Create mock fragment service for testing."""
        from services.diana_character_validator import DianaCharacterValidator
        
        service = MagicMock()
        service.session = session
        service.character_validator = DianaCharacterValidator(session)
        return service

    async def test_fragment_database_storage(self, session):
        """Test storing fragments in database."""
        test_structure = TestMVPFragmentStructure()
        fragment_data = test_structure.get_mvp_fragment_definitions()[0]  # Test with first fragment
        
        # Create NarrativeFragment from definition
        fragment = NarrativeFragment(
            id=fragment_data['id'],
            title=fragment_data['title'],
            content=fragment_data['content'],
            fragment_type=fragment_data['fragment_type'],
            storyline_level=fragment_data['storyline_level'],
            tier_classification=fragment_data['tier_classification'],
            fragment_sequence=fragment_data['fragment_sequence'],
            choices=fragment_data['choices'],
            triggers=fragment_data['triggers'],
            diana_personality_weight=fragment_data['diana_personality_weight'],
            character_validation_required=fragment_data['character_validation_required'],
            is_active=True
        )
        
        # Test database operations
        session.add(fragment)
        await session.commit()
        
        # Verify storage
        result = await session.execute(select(NarrativeFragment).where(NarrativeFragment.id == fragment_data['id']))
        stored_fragment = result.scalar_one_or_none()
        
        assert stored_fragment is not None, "Fragment should be stored in database"
        assert stored_fragment.id == fragment_data['id'], "Fragment ID should match"
        assert stored_fragment.diana_personality_weight == fragment_data['diana_personality_weight'], "Character weight should be preserved"

    async def test_fragment_json_serialization(self):
        """Test that fragment data can be properly JSON serialized."""
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        for fragment_data in fragments:
            # Test JSON serialization of choices and triggers
            choices_json = json.dumps(fragment_data['choices'])
            triggers_json = json.dumps(fragment_data['triggers'])
            
            # Should not raise exceptions
            assert isinstance(choices_json, str), f"Fragment {fragment_data['id']} choices not JSON serializable"
            assert isinstance(triggers_json, str), f"Fragment {fragment_data['id']} triggers not JSON serializable"
            
            # Test deserialization
            parsed_choices = json.loads(choices_json)
            parsed_triggers = json.loads(triggers_json)
            
            assert parsed_choices == fragment_data['choices'], "Choices should survive JSON round-trip"
            assert parsed_triggers == fragment_data['triggers'], "Triggers should survive JSON round-trip"

    async def test_fragment_retrieval_performance(self, session):
        """Test that fragment retrieval meets performance requirements."""
        import time
        
        test_structure = TestMVPFragmentStructure()
        fragment_data = test_structure.get_mvp_fragment_definitions()[0]
        
        # Store fragment
        fragment = NarrativeFragment(
            id=fragment_data['id'],
            title=fragment_data['title'],
            content=fragment_data['content'],
            fragment_type=fragment_data['fragment_type'],
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Test retrieval performance
        start_time = time.time()
        result = await session.execute(select(NarrativeFragment).where(NarrativeFragment.id == fragment_data['id']))
        retrieved_fragment = result.scalar_one_or_none()
        end_time = time.time()
        
        retrieval_time_ms = (end_time - start_time) * 1000
        
        assert retrieved_fragment is not None, "Fragment should be retrievable"
        assert retrieval_time_ms < 100, f"Fragment retrieval took {retrieval_time_ms:.2f}ms, should be < 100ms"


class TestFragmentValidationIntegration:
    """Integration tests for fragment validation workflow."""

    async def test_complete_fragment_validation_workflow(self, session):
        """Test complete validation workflow for all MVP fragments."""
        character_validator = DianaCharacterValidator(session)
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        validation_results = []
        
        for fragment_data in fragments:
            # Create fragment object
            fragment = NarrativeFragment(
                id=fragment_data['id'],
                title=fragment_data['title'],
                content=fragment_data['content'],
                fragment_type=fragment_data['fragment_type'],
                storyline_level=fragment_data['storyline_level'],
                tier_classification=fragment_data['tier_classification'],
                diana_personality_weight=fragment_data['diana_personality_weight'],
                character_validation_required=fragment_data['character_validation_required'],
                is_active=True
            )
            
            # Validate fragment
            result = await character_validator.validate_narrative_fragment(fragment)
            validation_results.append(result)
            
            # Store validation result
            validation_record = NarrativeCharacterValidation(
                fragment_id=fragment_data['id'],
                validated_content=fragment_data['content'],
                content_type='narrative_fragment',
                consistency_score=int(result.overall_score),
                mysterious_score=int(result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)),
                seductive_score=int(result.trait_scores.get(DianaPersonalityTrait.SEDUCTIVE, 0)),
                emotional_complexity_score=int(result.trait_scores.get(DianaPersonalityTrait.EMOTIONALLY_COMPLEX, 0)),
                intellectual_engagement_score=int(result.trait_scores.get(DianaPersonalityTrait.INTELLECTUALLY_ENGAGING, 0)),
                meets_threshold=result.meets_threshold,
                violations_detected=result.violations,
                recommendations=result.recommendations
            )
            
            session.add(validation_record)
        
        await session.commit()
        
        # Verify overall validation success
        passing_validations = len([r for r in validation_results if r.meets_threshold])
        total_validations = len(validation_results)
        passing_percentage = (passing_validations / total_validations) * 100
        
        assert passing_percentage >= 95.0, f"Only {passing_percentage:.1f}% of fragments pass validation, need >= 95%"
        assert passing_validations == 8, f"Expected all 8 fragments to pass validation, got {passing_validations}"

    async def test_fragment_character_consistency_automation(self, session):
        """Test automated character consistency validation."""
        validator = DianaCharacterValidator(session)
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        # Batch validate all fragment content
        content_pairs = [(f['id'], f['content']) for f in fragments]
        results = await validator.batch_validate_content(content_pairs)
        
        # Verify all results
        assert len(results) == 8, "Should validate all 8 fragments"
        
        for fragment_id, result in results.items():
            assert result.meets_threshold, f"Fragment {fragment_id} fails batch validation"
            assert result.overall_score >= 95.0, f"Fragment {fragment_id} batch score {result.overall_score} below 95"

    async def test_validation_report_generation(self, session):
        """Test generation of comprehensive validation report."""
        validator = DianaCharacterValidator(session)
        test_structure = TestMVPFragmentStructure()
        fragments = test_structure.get_mvp_fragment_definitions()
        
        # Collect validation results
        validation_results = []
        for fragment_data in fragments:
            result = await validator.validate_text(fragment_data['content'], context="narrative_fragment")
            validation_results.append(result)
        
        # Generate report
        report = validator.generate_character_report(validation_results)
        
        # Verify report structure
        assert 'summary' in report, "Report should include summary"
        assert 'trait_performance' in report, "Report should include trait performance"
        assert 'common_violations' in report, "Report should include violations analysis"
        assert 'recommendations' in report, "Report should include recommendations"
        
        # Verify MVP compliance
        summary = report['summary']
        assert summary['meets_mvp_requirement'] is True, "MVP should meet character consistency requirement"
        assert summary['passing_percentage'] >= 95.0, "Should have >= 95% passing rate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])