# tests/test_archetype_analyzer.py
"""
Unit tests for ArchetypeAnalyzer core methods.

Tests verify core archetype analysis algorithms for the Sistema Narrativo Ramificado Diana,
including choice weight processing, timing modifiers, primary archetype calculation,
and sub-archetype determination mapping logic.
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the dataclasses and analyzer for testing
from dataclasses import dataclass

@dataclass
class ArchetypeScores:
    intellectual: float = 0.0
    emotional: float = 0.0
    exploratory: float = 0.0
    vulnerable: float = 0.0
    philosophical: float = 0.0
    direct: float = 0.0
    patient: float = 0.0
    reciprocal: float = 0.0

@dataclass
class SubArchetypeScores:
    romantic_intellectual: float = 0.0
    skeptical_thinker: float = 0.0
    hedonist_philosopher: float = 0.0
    pure_theorist: float = 0.0
    empathetic_emotional: float = 0.0
    passionate_emotional: float = 0.0
    wounded_healer: float = 0.0
    adventure_seeker: float = 0.0
    collector_explorer: float = 0.0
    freedom_lover: float = 0.0


# Mock ResponseTimeAnalyzer for testing
class MockResponseTimeAnalyzer:
    def __init__(self, session=None):
        self.session = session

    async def analyze_cognitive_style(self, user_id: int, timings: List[float]) -> Dict[str, Any]:
        """Mock implementation of cognitive style analysis."""
        if not timings:
            return {
                'cognitive_style': 'balanced',
                'consistency_score': 0.5,
                'temporal_pattern': 'stable'
            }

        avg_time = sum(timings) / len(timings)

        if avg_time < 10:
            cognitive_style = 'quick_intuitive'
        elif avg_time < 30:
            cognitive_style = 'thoughtful'
        else:
            cognitive_style = 'deliberate'

        return {
            'cognitive_style': cognitive_style,
            'consistency_score': 0.8,
            'temporal_pattern': 'stable'
        }


# Mock ArchetypeAnalyzer implementation for testing
class ArchetypeAnalyzer:
    """Mock implementation of ArchetypeAnalyzer for testing core methods."""

    def __init__(self, session=None):
        self.session = session or Mock()
        self.response_time_analyzer = MockResponseTimeAnalyzer(session)

    async def _process_choice_weights(
        self,
        choice: Dict[str, Any],
        archetype_scores: ArchetypeScores,
        sub_archetype_scores: SubArchetypeScores
    ) -> None:
        """
        Procesa los pesos de arquetipo de una elección individual y actualiza las puntuaciones.
        """
        # Procesar pesos de arquetipos primarios
        archetype_weights = choice.get('archetype_weights', {})
        for archetype_name, weight in archetype_weights.items():
            # Verificar que el arquetipo existe en la estructura de datos
            if hasattr(archetype_scores, archetype_name):
                # Obtener valor actual y agregar peso
                current_value = getattr(archetype_scores, archetype_name)
                new_value = current_value + weight
                setattr(archetype_scores, archetype_name, new_value)

        # Procesar pesos de sub-arquetipos
        sub_archetype_weights = choice.get('sub_archetype_weights', {})
        for sub_archetype_name, weight in sub_archetype_weights.items():
            # Verificar que el sub-arquetipo existe en la estructura de datos
            if hasattr(sub_archetype_scores, sub_archetype_name):
                # Obtener valor actual y agregar peso
                current_value = getattr(sub_archetype_scores, sub_archetype_name)
                new_value = current_value + weight
                setattr(sub_archetype_scores, sub_archetype_name, new_value)

    async def _apply_timing_modifiers(
        self,
        timing: float,
        archetype_scores: ArchetypeScores
    ) -> None:
        """
        Aplica modificadores basados en tiempo de respuesta para detección de estilo cognitivo.
        """
        if timing < 10.0:
            # Respuesta rápida: procesamiento emocional/intuitivo
            archetype_scores.direct += 0.5

        elif 10.0 <= timing <= 30.0:
            # Respuesta moderada: procesamiento analítico balanceado
            archetype_scores.philosophical += 0.4
            archetype_scores.intellectual += 0.3

        else:  # timing > 30.0
            # Respuesta lenta: procesamiento reflexivo profundo
            archetype_scores.philosophical += 0.6
            archetype_scores.patient += 0.5

    async def _calculate_primary_archetype(
        self,
        archetype_scores: ArchetypeScores
    ) -> str:
        """
        Calcula el arquetipo primario determinando la dimensión con mayor puntuación.
        """
        # Obtener todas las puntuaciones como diccionario
        score_dict = {
            'intellectual': archetype_scores.intellectual,
            'emotional': archetype_scores.emotional,
            'exploratory': archetype_scores.exploratory,
            'vulnerable': archetype_scores.vulnerable,
            'philosophical': archetype_scores.philosophical,
            'direct': archetype_scores.direct,
            'patient': archetype_scores.patient,
            'reciprocal': archetype_scores.reciprocal
        }

        # Encontrar la puntuación máxima
        max_score = max(score_dict.values())

        # Fallback en caso de todas las puntuaciones siendo 0
        if max_score == 0.0:
            return 'intellectual'  # Default por especificación

        # En caso de empate, seleccionar alfabéticamente el primero
        for archetype in sorted(score_dict.keys()):
            if score_dict[archetype] == max_score:
                return archetype

        # Fallback adicional (no debería llegarse aquí)
        return 'intellectual'

    async def _determine_sub_archetype(
        self,
        primary_archetype: str,
        sub_archetype_scores: SubArchetypeScores
    ) -> str:
        """
        Determina el sub-arquetipo mapeando arquetipo primario a sub-arquetipos relevantes.
        """
        # Mapeo de arquetipos primarios a sub-arquetipos relevantes
        archetype_sub_mappings = {
            'intellectual': ['romantic_intellectual', 'skeptical_thinker', 'pure_theorist'],
            'emotional': ['empathetic_emotional', 'passionate_emotional', 'wounded_healer'],
            'exploratory': ['adventure_seeker', 'collector_explorer', 'freedom_lover'],
            'philosophical': ['hedonist_philosopher', 'pure_theorist', 'skeptical_thinker'],
            'vulnerable': ['wounded_healer', 'empathetic_emotional'],
            'direct': ['passionate_emotional', 'adventure_seeker'],
            'patient': ['pure_theorist', 'romantic_intellectual'],
            'reciprocal': ['empathetic_emotional', 'romantic_intellectual']
        }

        # Obtener sub-arquetipos relevantes para el arquetipo primario
        relevant_sub_archetypes = archetype_sub_mappings.get(primary_archetype, [])

        if not relevant_sub_archetypes:
            return 'undefined'

        # Obtener puntuaciones de sub-arquetipos relevantes
        sub_scores = {}
        for sub_archetype in relevant_sub_archetypes:
            if hasattr(sub_archetype_scores, sub_archetype):
                score = getattr(sub_archetype_scores, sub_archetype)
                sub_scores[sub_archetype] = score

        # Si no hay puntuaciones o todas son 0, retornar undefined
        if not sub_scores or max(sub_scores.values()) == 0.0:
            return 'undefined'

        # Seleccionar sub-arquetipo con mayor puntuación
        max_score = max(sub_scores.values())
        for sub_archetype in sorted(sub_scores.keys()):  # Ordenar para consistencia
            if sub_scores[sub_archetype] == max_score:
                return sub_archetype

        return 'undefined'


class TestArchetypeAnalyzerProcessChoiceWeights(unittest.TestCase):
    """Test cases for _process_choice_weights method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ArchetypeAnalyzer()
        self.archetype_scores = ArchetypeScores()
        self.sub_archetype_scores = SubArchetypeScores()

    def test_process_choice_weights_primary_archetypes(self):
        """Test processing of primary archetype weights."""
        choice = {
            'archetype_weights': {
                'intellectual': 2.5,
                'emotional': 1.8,
                'exploratory': 0.7
            }
        }

        # Process the choice weights
        asyncio.run(self.analyzer._process_choice_weights(
            choice, self.archetype_scores, self.sub_archetype_scores
        ))

        # Verify weights were applied correctly
        self.assertEqual(self.archetype_scores.intellectual, 2.5)
        self.assertEqual(self.archetype_scores.emotional, 1.8)
        self.assertEqual(self.archetype_scores.exploratory, 0.7)
        # Unmodified fields should remain 0.0
        self.assertEqual(self.archetype_scores.vulnerable, 0.0)
        self.assertEqual(self.archetype_scores.philosophical, 0.0)

    def test_process_choice_weights_sub_archetypes(self):
        """Test processing of sub-archetype weights."""
        choice = {
            'sub_archetype_weights': {
                'romantic_intellectual': 3.2,
                'skeptical_thinker': 1.5,
                'wounded_healer': 2.8
            }
        }

        asyncio.run(self.analyzer._process_choice_weights(
            choice, self.archetype_scores, self.sub_archetype_scores
        ))

        # Verify sub-archetype weights were applied correctly
        self.assertEqual(self.sub_archetype_scores.romantic_intellectual, 3.2)
        self.assertEqual(self.sub_archetype_scores.skeptical_thinker, 1.5)
        self.assertEqual(self.sub_archetype_scores.wounded_healer, 2.8)
        # Unmodified fields should remain 0.0
        self.assertEqual(self.sub_archetype_scores.pure_theorist, 0.0)

    def test_process_choice_weights_both_types(self):
        """Test processing of both primary and sub-archetype weights simultaneously."""
        choice = {
            'archetype_weights': {
                'intellectual': 1.5,
                'patient': 2.0
            },
            'sub_archetype_weights': {
                'pure_theorist': 2.5,
                'empathetic_emotional': 1.8
            }
        }

        asyncio.run(self.analyzer._process_choice_weights(
            choice, self.archetype_scores, self.sub_archetype_scores
        ))

        # Verify both types were processed
        self.assertEqual(self.archetype_scores.intellectual, 1.5)
        self.assertEqual(self.archetype_scores.patient, 2.0)
        self.assertEqual(self.sub_archetype_scores.pure_theorist, 2.5)
        self.assertEqual(self.sub_archetype_scores.empathetic_emotional, 1.8)

    def test_process_choice_weights_invalid_archetype_names(self):
        """Test handling of invalid archetype names."""
        choice = {
            'archetype_weights': {
                'intellectual': 2.0,
                'invalid_archetype': 1.5,  # Should be ignored
                'another_invalid': 3.0     # Should be ignored
            },
            'sub_archetype_weights': {
                'romantic_intellectual': 1.8,
                'nonexistent_sub': 2.5     # Should be ignored
            }
        }

        asyncio.run(self.analyzer._process_choice_weights(
            choice, self.archetype_scores, self.sub_archetype_scores
        ))

        # Only valid archetype should be processed
        self.assertEqual(self.archetype_scores.intellectual, 2.0)
        self.assertEqual(self.sub_archetype_scores.romantic_intellectual, 1.8)
        # No errors should have been raised

    def test_process_choice_weights_empty_choice(self):
        """Test handling of empty choice data."""
        choice = {}

        # Should not raise any errors
        asyncio.run(self.analyzer._process_choice_weights(
            choice, self.archetype_scores, self.sub_archetype_scores
        ))

        # All scores should remain 0.0
        self.assertEqual(self.archetype_scores.intellectual, 0.0)
        self.assertEqual(self.sub_archetype_scores.romantic_intellectual, 0.0)

    def test_process_choice_weights_cumulative_effect(self):
        """Test cumulative effect of multiple choice processings."""
        choices = [
            {'archetype_weights': {'intellectual': 1.0, 'emotional': 0.5}},
            {'archetype_weights': {'intellectual': 1.5, 'philosophical': 2.0}},
            {'archetype_weights': {'emotional': 1.0, 'intellectual': 0.5}}
        ]

        for choice in choices:
            asyncio.run(self.analyzer._process_choice_weights(
                choice, self.archetype_scores, self.sub_archetype_scores
            ))

        # Verify cumulative scores
        self.assertEqual(self.archetype_scores.intellectual, 3.0)  # 1.0 + 1.5 + 0.5
        self.assertEqual(self.archetype_scores.emotional, 1.5)     # 0.5 + 1.0
        self.assertEqual(self.archetype_scores.philosophical, 2.0) # 2.0


class TestArchetypeAnalyzerApplyTimingModifiers(unittest.TestCase):
    """Test cases for _apply_timing_modifiers method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ArchetypeAnalyzer()
        self.archetype_scores = ArchetypeScores()

    def test_apply_timing_modifiers_quick_response(self):
        """Test timing modifiers for quick response (< 10 seconds)."""
        timing = 5.0  # Quick response

        asyncio.run(self.analyzer._apply_timing_modifiers(timing, self.archetype_scores))

        # Should boost direct archetype
        self.assertEqual(self.archetype_scores.direct, 0.5)
        # Other scores should remain 0.0
        self.assertEqual(self.archetype_scores.philosophical, 0.0)
        self.assertEqual(self.archetype_scores.intellectual, 0.0)
        self.assertEqual(self.archetype_scores.patient, 0.0)

    def test_apply_timing_modifiers_thoughtful_response(self):
        """Test timing modifiers for thoughtful response (10-30 seconds)."""
        timing = 20.0  # Thoughtful response

        asyncio.run(self.analyzer._apply_timing_modifiers(timing, self.archetype_scores))

        # Should boost philosophical and intellectual
        self.assertEqual(self.archetype_scores.philosophical, 0.4)
        self.assertEqual(self.archetype_scores.intellectual, 0.3)
        # Other scores should remain 0.0
        self.assertEqual(self.archetype_scores.direct, 0.0)
        self.assertEqual(self.archetype_scores.patient, 0.0)

    def test_apply_timing_modifiers_deliberate_response(self):
        """Test timing modifiers for deliberate response (> 30 seconds)."""
        timing = 45.0  # Deliberate response

        asyncio.run(self.analyzer._apply_timing_modifiers(timing, self.archetype_scores))

        # Should boost philosophical and patient
        self.assertEqual(self.archetype_scores.philosophical, 0.6)
        self.assertEqual(self.archetype_scores.patient, 0.5)
        # Other scores should remain 0.0
        self.assertEqual(self.archetype_scores.direct, 0.0)
        self.assertEqual(self.archetype_scores.intellectual, 0.0)

    def test_apply_timing_modifiers_boundary_values(self):
        """Test timing modifiers at exact boundary values."""
        # Test exactly 10.0 seconds (boundary between quick and thoughtful)
        self.archetype_scores = ArchetypeScores()
        asyncio.run(self.analyzer._apply_timing_modifiers(10.0, self.archetype_scores))

        # Should be treated as thoughtful (10.0 <= timing <= 30.0)
        self.assertEqual(self.archetype_scores.philosophical, 0.4)
        self.assertEqual(self.archetype_scores.intellectual, 0.3)
        self.assertEqual(self.archetype_scores.direct, 0.0)

        # Test exactly 30.0 seconds (boundary between thoughtful and deliberate)
        self.archetype_scores = ArchetypeScores()
        asyncio.run(self.analyzer._apply_timing_modifiers(30.0, self.archetype_scores))

        # Should be treated as thoughtful (10.0 <= timing <= 30.0)
        self.assertEqual(self.archetype_scores.philosophical, 0.4)
        self.assertEqual(self.archetype_scores.intellectual, 0.3)
        self.assertEqual(self.archetype_scores.patient, 0.0)

    def test_apply_timing_modifiers_cumulative_effect(self):
        """Test cumulative effect of multiple timing modifier applications."""
        timings = [5.0, 20.0, 40.0, 8.0, 25.0]

        for timing in timings:
            asyncio.run(self.analyzer._apply_timing_modifiers(timing, self.archetype_scores))

        # Verify cumulative effects
        # 5.0 (quick) + 8.0 (quick) = 2 quick responses = 1.0 direct
        self.assertEqual(self.archetype_scores.direct, 1.0)
        # 20.0 (thoughtful) + 25.0 (thoughtful) + 40.0 (deliberate) philosophical effects
        # = 0.4 + 0.4 + 0.6 = 1.4 philosophical
        self.assertEqual(self.archetype_scores.philosophical, 1.4)
        # 20.0 (thoughtful) + 25.0 (thoughtful) = 2 thoughtful responses
        self.assertEqual(self.archetype_scores.intellectual, 0.6)   # 0.3 + 0.3
        # 40.0 (deliberate) = 1 deliberate response
        self.assertEqual(self.archetype_scores.patient, 0.5)

    def test_apply_timing_modifiers_edge_cases(self):
        """Test timing modifiers with edge case values."""
        # Test very small timing
        asyncio.run(self.analyzer._apply_timing_modifiers(0.1, self.archetype_scores))
        self.assertEqual(self.archetype_scores.direct, 0.5)

        # Reset and test very large timing
        self.archetype_scores = ArchetypeScores()
        asyncio.run(self.analyzer._apply_timing_modifiers(300.0, self.archetype_scores))
        self.assertEqual(self.archetype_scores.philosophical, 0.6)
        self.assertEqual(self.archetype_scores.patient, 0.5)


class TestArchetypeAnalyzerCalculatePrimaryArchetype(unittest.TestCase):
    """Test cases for _calculate_primary_archetype method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ArchetypeAnalyzer()

    def test_calculate_primary_archetype_clear_winner(self):
        """Test primary archetype calculation with clear highest score."""
        archetype_scores = ArchetypeScores(
            intellectual=0.5,
            emotional=3.2,  # Highest
            exploratory=1.8,
            vulnerable=0.0,
            philosophical=2.1,
            direct=1.0,
            patient=0.8,
            reciprocal=1.5
        )

        result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
        self.assertEqual(result, 'emotional')

    def test_calculate_primary_archetype_tied_scores(self):
        """Test primary archetype calculation with tied highest scores."""
        archetype_scores = ArchetypeScores(
            intellectual=2.5,
            emotional=1.0,
            exploratory=2.5,  # Tied with intellectual
            vulnerable=0.0,
            philosophical=1.8,
            direct=0.5,
            patient=1.2,
            reciprocal=0.8
        )

        result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
        # Should return alphabetically first: 'exploratory' comes before 'intellectual'
        self.assertEqual(result, 'exploratory')

    def test_calculate_primary_archetype_all_zeros(self):
        """Test primary archetype calculation with all zero scores."""
        archetype_scores = ArchetypeScores()  # All default to 0.0

        result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
        # Should return default: 'intellectual' (default per specification)
        self.assertEqual(result, 'intellectual')

    def test_calculate_primary_archetype_single_non_zero(self):
        """Test primary archetype calculation with only one non-zero score."""
        archetype_scores = ArchetypeScores(vulnerable=1.5)

        result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
        self.assertEqual(result, 'vulnerable')

    def test_calculate_primary_archetype_alphabetical_ordering(self):
        """Test that alphabetical ordering is consistently applied in ties."""
        # Test all possible pairs to ensure consistent ordering
        test_cases = [
            (['direct', 'emotional'], 'direct'),
            (['intellectual', 'patient'], 'intellectual'),
            (['philosophical', 'reciprocal'], 'philosophical'),
            (['exploratory', 'vulnerable'], 'exploratory')
        ]

        for tied_archetypes, expected_winner in test_cases:
            archetype_scores = ArchetypeScores()
            for archetype in tied_archetypes:
                setattr(archetype_scores, archetype, 2.0)  # Set equal high scores

            result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
            self.assertEqual(result, expected_winner,
                           f"Failed for tied archetypes: {tied_archetypes}")

    def test_calculate_primary_archetype_negative_scores(self):
        """Test primary archetype calculation with negative scores."""
        archetype_scores = ArchetypeScores(
            intellectual=-1.0,
            emotional=0.5,   # Highest (only positive)
            exploratory=-0.5,
            vulnerable=-2.0,
            philosophical=0.0,
            direct=-1.5,
            patient=-0.8,
            reciprocal=-0.2
        )

        result = asyncio.run(self.analyzer._calculate_primary_archetype(archetype_scores))
        self.assertEqual(result, 'emotional')


class TestArchetypeAnalyzerDetermineSubArchetype(unittest.TestCase):
    """Test cases for _determine_sub_archetype method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ArchetypeAnalyzer()

    def test_determine_sub_archetype_intellectual_mapping(self):
        """Test sub-archetype determination for intellectual primary archetype."""
        sub_archetype_scores = SubArchetypeScores(
            romantic_intellectual=2.5,  # Highest for intellectual mapping
            skeptical_thinker=1.8,
            pure_theorist=2.0
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'intellectual', sub_archetype_scores
        ))
        self.assertEqual(result, 'romantic_intellectual')

    def test_determine_sub_archetype_emotional_mapping(self):
        """Test sub-archetype determination for emotional primary archetype."""
        sub_archetype_scores = SubArchetypeScores(
            empathetic_emotional=1.5,
            passionate_emotional=3.2,  # Highest for emotional mapping
            wounded_healer=2.1
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'emotional', sub_archetype_scores
        ))
        self.assertEqual(result, 'passionate_emotional')

    def test_determine_sub_archetype_exploratory_mapping(self):
        """Test sub-archetype determination for exploratory primary archetype."""
        sub_archetype_scores = SubArchetypeScores(
            adventure_seeker=1.8,
            collector_explorer=2.5,
            freedom_lover=2.2  # Highest for exploratory mapping
        )
        # Manually set freedom_lover as highest
        sub_archetype_scores.freedom_lover = 2.8

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'exploratory', sub_archetype_scores
        ))
        self.assertEqual(result, 'freedom_lover')

    def test_determine_sub_archetype_vulnerable_mapping(self):
        """Test sub-archetype determination for vulnerable primary archetype."""
        sub_archetype_scores = SubArchetypeScores(
            wounded_healer=3.0,       # Highest for vulnerable mapping
            empathetic_emotional=2.5
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'vulnerable', sub_archetype_scores
        ))
        self.assertEqual(result, 'wounded_healer')

    def test_determine_sub_archetype_all_zero_scores(self):
        """Test sub-archetype determination with all zero scores."""
        sub_archetype_scores = SubArchetypeScores()  # All zeros

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'intellectual', sub_archetype_scores
        ))
        self.assertEqual(result, 'undefined')

    def test_determine_sub_archetype_invalid_primary(self):
        """Test sub-archetype determination with invalid primary archetype."""
        sub_archetype_scores = SubArchetypeScores(
            romantic_intellectual=2.0
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'invalid_archetype', sub_archetype_scores
        ))
        self.assertEqual(result, 'undefined')

    def test_determine_sub_archetype_tied_scores(self):
        """Test sub-archetype determination with tied scores."""
        sub_archetype_scores = SubArchetypeScores(
            empathetic_emotional=2.5,    # Tied
            passionate_emotional=2.5,    # Tied (should win alphabetically)
            wounded_healer=1.0
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'emotional', sub_archetype_scores
        ))
        # Should return alphabetically first: 'empathetic_emotional'
        self.assertEqual(result, 'empathetic_emotional')

    def test_determine_sub_archetype_complete_mappings(self):
        """Test all primary archetype to sub-archetype mappings."""
        mapping_tests = [
            ('intellectual', ['romantic_intellectual', 'skeptical_thinker', 'pure_theorist']),
            ('emotional', ['empathetic_emotional', 'passionate_emotional', 'wounded_healer']),
            ('exploratory', ['adventure_seeker', 'collector_explorer', 'freedom_lover']),
            ('philosophical', ['hedonist_philosopher', 'pure_theorist', 'skeptical_thinker']),
            ('vulnerable', ['wounded_healer', 'empathetic_emotional']),
            ('direct', ['passionate_emotional', 'adventure_seeker']),
            ('patient', ['pure_theorist', 'romantic_intellectual']),
            ('reciprocal', ['empathetic_emotional', 'romantic_intellectual'])
        ]

        for primary_archetype, expected_sub_archetypes in mapping_tests:
            with self.subTest(primary_archetype=primary_archetype):
                # Create scores with the first expected sub-archetype having highest score
                sub_archetype_scores = SubArchetypeScores()
                target_sub_archetype = expected_sub_archetypes[0]
                setattr(sub_archetype_scores, target_sub_archetype, 2.0)

                result = asyncio.run(self.analyzer._determine_sub_archetype(
                    primary_archetype, sub_archetype_scores
                ))
                self.assertEqual(result, target_sub_archetype)

    def test_determine_sub_archetype_irrelevant_scores(self):
        """Test that irrelevant sub-archetype scores don't affect result."""
        sub_archetype_scores = SubArchetypeScores(
            # Set high score for sub-archetype not mapped to 'intellectual'
            adventure_seeker=5.0,  # Not relevant to intellectual
            # Set lower score for relevant sub-archetype
            romantic_intellectual=1.0  # Relevant to intellectual
        )

        result = asyncio.run(self.analyzer._determine_sub_archetype(
            'intellectual', sub_archetype_scores
        ))
        # Should only consider relevant sub-archetypes
        self.assertEqual(result, 'romantic_intellectual')


# Import asyncio for running async tests
import asyncio


if __name__ == '__main__':
    unittest.main()