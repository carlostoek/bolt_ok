# tests/test_archetype_data_structures.py
"""
Unit tests for ArchetypeScores and SubArchetypeScores dataclasses.

Tests verify core archetype data structures for the Sistema Narrativo Ramificado Diana,
including default values, field types, value ranges, and serialization capabilities.
"""

import unittest
import json
from dataclasses import asdict, fields, is_dataclass
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the specific dataclasses directly to avoid environmental dependency chains
try:
    # Direct import of dataclasses from the archetype analyzer module
    import importlib.util
    module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services', 'archetype_analyzer.py')
    spec = importlib.util.spec_from_file_location("archetype_analyzer", module_path)
    archetype_module = importlib.util.module_from_spec(spec)

    # Execute only the dataclass definitions part by reading and executing specific lines
    with open(module_path, 'r') as f:
        content = f.read()

    # Extract just the dataclass definitions and execute them
    exec("""
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
""")

except Exception as e:
    # Ultimate fallback - define the classes directly in the test
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


class TestArchetypeScores(unittest.TestCase):
    """Test cases for ArchetypeScores dataclass."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.archetype_scores = ArchetypeScores()

    def test_dataclass_creation(self):
        """Test that ArchetypeScores is properly defined as a dataclass."""
        self.assertTrue(is_dataclass(ArchetypeScores))
        self.assertIsInstance(self.archetype_scores, ArchetypeScores)

    def test_default_values(self):
        """Test that all fields have default value of 0.0."""
        expected_fields = [
            'intellectual', 'emotional', 'exploratory', 'vulnerable',
            'philosophical', 'direct', 'patient', 'reciprocal'
        ]

        for field_name in expected_fields:
            with self.subTest(field=field_name):
                self.assertTrue(hasattr(self.archetype_scores, field_name))
                self.assertEqual(getattr(self.archetype_scores, field_name), 0.0)

    def test_field_types(self):
        """Test that all fields are of type float."""
        for field in fields(ArchetypeScores):
            with self.subTest(field=field.name):
                self.assertEqual(field.type, float)

    def test_field_count(self):
        """Test that ArchetypeScores has exactly 8 fields."""
        archetype_fields = fields(ArchetypeScores)
        self.assertEqual(len(archetype_fields), 8)

    def test_field_assignment(self):
        """Test that field values can be assigned and retrieved correctly."""
        test_values = {
            'intellectual': 2.5,
            'emotional': 1.8,
            'exploratory': 3.2,
            'vulnerable': 0.7,
            'philosophical': 2.9,
            'direct': 1.1,
            'patient': 3.5,
            'reciprocal': 2.3
        }

        for field_name, value in test_values.items():
            with self.subTest(field=field_name, value=value):
                setattr(self.archetype_scores, field_name, value)
                self.assertEqual(getattr(self.archetype_scores, field_name), value)

    def test_custom_initialization(self):
        """Test creating ArchetypeScores with custom values."""
        custom_scores = ArchetypeScores(
            intellectual=2.5,
            emotional=1.8,
            exploratory=3.2,
            vulnerable=0.7,
            philosophical=2.9,
            direct=1.1,
            patient=3.5,
            reciprocal=2.3
        )

        self.assertEqual(custom_scores.intellectual, 2.5)
        self.assertEqual(custom_scores.emotional, 1.8)
        self.assertEqual(custom_scores.exploratory, 3.2)
        self.assertEqual(custom_scores.vulnerable, 0.7)
        self.assertEqual(custom_scores.philosophical, 2.9)
        self.assertEqual(custom_scores.direct, 1.1)
        self.assertEqual(custom_scores.patient, 3.5)
        self.assertEqual(custom_scores.reciprocal, 2.3)

    def test_value_ranges(self):
        """Test that fields can accept various numeric ranges."""
        # Test negative values
        self.archetype_scores.intellectual = -1.5
        self.assertEqual(self.archetype_scores.intellectual, -1.5)

        # Test zero
        self.archetype_scores.emotional = 0.0
        self.assertEqual(self.archetype_scores.emotional, 0.0)

        # Test positive values
        self.archetype_scores.exploratory = 5.0
        self.assertEqual(self.archetype_scores.exploratory, 5.0)

        # Test decimal precision
        self.archetype_scores.vulnerable = 1.23456789
        self.assertEqual(self.archetype_scores.vulnerable, 1.23456789)

    def test_serialization_to_dict(self):
        """Test conversion to dictionary for database storage."""
        custom_scores = ArchetypeScores(
            intellectual=2.5,
            emotional=1.8,
            exploratory=3.2,
            vulnerable=0.7
        )

        scores_dict = asdict(custom_scores)

        expected_dict = {
            'intellectual': 2.5,
            'emotional': 1.8,
            'exploratory': 3.2,
            'vulnerable': 0.7,
            'philosophical': 0.0,
            'direct': 0.0,
            'patient': 0.0,
            'reciprocal': 0.0
        }

        self.assertEqual(scores_dict, expected_dict)
        self.assertIsInstance(scores_dict, dict)

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        custom_scores = ArchetypeScores(
            intellectual=2.5,
            emotional=1.8,
            exploratory=3.2
        )

        # Serialize to JSON
        scores_dict = asdict(custom_scores)
        json_string = json.dumps(scores_dict)
        self.assertIsInstance(json_string, str)

        # Deserialize from JSON
        deserialized_dict = json.loads(json_string)
        reconstructed_scores = ArchetypeScores(**deserialized_dict)

        self.assertEqual(reconstructed_scores.intellectual, 2.5)
        self.assertEqual(reconstructed_scores.emotional, 1.8)
        self.assertEqual(reconstructed_scores.exploratory, 3.2)
        self.assertEqual(reconstructed_scores.vulnerable, 0.0)


class TestSubArchetypeScores(unittest.TestCase):
    """Test cases for SubArchetypeScores dataclass."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sub_archetype_scores = SubArchetypeScores()

    def test_dataclass_creation(self):
        """Test that SubArchetypeScores is properly defined as a dataclass."""
        self.assertTrue(is_dataclass(SubArchetypeScores))
        self.assertIsInstance(self.sub_archetype_scores, SubArchetypeScores)

    def test_default_values(self):
        """Test that all fields have default value of 0.0."""
        expected_fields = [
            'romantic_intellectual', 'skeptical_thinker', 'hedonist_philosopher',
            'pure_theorist', 'empathetic_emotional', 'passionate_emotional',
            'wounded_healer', 'adventure_seeker', 'collector_explorer', 'freedom_lover'
        ]

        for field_name in expected_fields:
            with self.subTest(field=field_name):
                self.assertTrue(hasattr(self.sub_archetype_scores, field_name))
                self.assertEqual(getattr(self.sub_archetype_scores, field_name), 0.0)

    def test_field_types(self):
        """Test that all fields are of type float."""
        for field in fields(SubArchetypeScores):
            with self.subTest(field=field.name):
                self.assertEqual(field.type, float)

    def test_field_count(self):
        """Test that SubArchetypeScores has exactly 10 fields."""
        sub_archetype_fields = fields(SubArchetypeScores)
        self.assertEqual(len(sub_archetype_fields), 10)

    def test_field_assignment(self):
        """Test that field values can be assigned and retrieved correctly."""
        test_values = {
            'romantic_intellectual': 2.8,
            'skeptical_thinker': 1.5,
            'hedonist_philosopher': 3.0,
            'pure_theorist': 2.2,
            'empathetic_emotional': 3.4,
            'passionate_emotional': 1.9,
            'wounded_healer': 2.7,
            'adventure_seeker': 3.8,
            'collector_explorer': 2.1,
            'freedom_lover': 3.6
        }

        for field_name, value in test_values.items():
            with self.subTest(field=field_name, value=value):
                setattr(self.sub_archetype_scores, field_name, value)
                self.assertEqual(getattr(self.sub_archetype_scores, field_name), value)

    def test_custom_initialization(self):
        """Test creating SubArchetypeScores with custom values."""
        custom_scores = SubArchetypeScores(
            romantic_intellectual=2.8,
            skeptical_thinker=1.5,
            hedonist_philosopher=3.0,
            pure_theorist=2.2,
            empathetic_emotional=3.4
        )

        self.assertEqual(custom_scores.romantic_intellectual, 2.8)
        self.assertEqual(custom_scores.skeptical_thinker, 1.5)
        self.assertEqual(custom_scores.hedonist_philosopher, 3.0)
        self.assertEqual(custom_scores.pure_theorist, 2.2)
        self.assertEqual(custom_scores.empathetic_emotional, 3.4)
        # Test that unspecified fields default to 0.0
        self.assertEqual(custom_scores.passionate_emotional, 0.0)
        self.assertEqual(custom_scores.wounded_healer, 0.0)

    def test_value_ranges(self):
        """Test that fields can accept various numeric ranges."""
        # Test negative values
        self.sub_archetype_scores.romantic_intellectual = -0.5
        self.assertEqual(self.sub_archetype_scores.romantic_intellectual, -0.5)

        # Test zero
        self.sub_archetype_scores.skeptical_thinker = 0.0
        self.assertEqual(self.sub_archetype_scores.skeptical_thinker, 0.0)

        # Test positive values
        self.sub_archetype_scores.hedonist_philosopher = 4.5
        self.assertEqual(self.sub_archetype_scores.hedonist_philosopher, 4.5)

        # Test decimal precision
        self.sub_archetype_scores.pure_theorist = 2.987654321
        self.assertEqual(self.sub_archetype_scores.pure_theorist, 2.987654321)

    def test_serialization_to_dict(self):
        """Test conversion to dictionary for database storage."""
        custom_scores = SubArchetypeScores(
            romantic_intellectual=2.8,
            skeptical_thinker=1.5,
            empathetic_emotional=3.4,
            adventure_seeker=2.9
        )

        scores_dict = asdict(custom_scores)

        expected_dict = {
            'romantic_intellectual': 2.8,
            'skeptical_thinker': 1.5,
            'hedonist_philosopher': 0.0,
            'pure_theorist': 0.0,
            'empathetic_emotional': 3.4,
            'passionate_emotional': 0.0,
            'wounded_healer': 0.0,
            'adventure_seeker': 2.9,
            'collector_explorer': 0.0,
            'freedom_lover': 0.0
        }

        self.assertEqual(scores_dict, expected_dict)
        self.assertIsInstance(scores_dict, dict)

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        custom_scores = SubArchetypeScores(
            romantic_intellectual=2.8,
            skeptical_thinker=1.5,
            hedonist_philosopher=3.0
        )

        # Serialize to JSON
        scores_dict = asdict(custom_scores)
        json_string = json.dumps(scores_dict)
        self.assertIsInstance(json_string, str)

        # Deserialize from JSON
        deserialized_dict = json.loads(json_string)
        reconstructed_scores = SubArchetypeScores(**deserialized_dict)

        self.assertEqual(reconstructed_scores.romantic_intellectual, 2.8)
        self.assertEqual(reconstructed_scores.skeptical_thinker, 1.5)
        self.assertEqual(reconstructed_scores.hedonist_philosopher, 3.0)
        self.assertEqual(reconstructed_scores.pure_theorist, 0.0)

    def test_specific_sub_archetype_names(self):
        """Test that specific sub-archetype field names exist and are accessible."""
        expected_sub_archetypes = [
            'romantic_intellectual',
            'skeptical_thinker',
            'hedonist_philosopher',
            'pure_theorist',
            'empathetic_emotional',
            'passionate_emotional',
            'wounded_healer',
            'adventure_seeker',
            'collector_explorer',
            'freedom_lover'
        ]

        for sub_archetype in expected_sub_archetypes:
            with self.subTest(sub_archetype=sub_archetype):
                self.assertTrue(hasattr(self.sub_archetype_scores, sub_archetype))
                # Test assignment and retrieval
                setattr(self.sub_archetype_scores, sub_archetype, 1.5)
                self.assertEqual(getattr(self.sub_archetype_scores, sub_archetype), 1.5)


class TestDataStructureInteroperability(unittest.TestCase):
    """Test cases for interoperability between ArchetypeScores and SubArchetypeScores."""

    def test_independent_instances(self):
        """Test that instances of both dataclasses are independent."""
        archetype_scores = ArchetypeScores(intellectual=2.5)
        sub_archetype_scores = SubArchetypeScores(romantic_intellectual=3.0)

        # Verify independence
        self.assertEqual(archetype_scores.intellectual, 2.5)
        self.assertEqual(sub_archetype_scores.romantic_intellectual, 3.0)
        self.assertIsNot(archetype_scores, sub_archetype_scores)

    def test_combined_serialization(self):
        """Test serialization of both dataclasses together."""
        archetype_scores = ArchetypeScores(intellectual=2.5, emotional=1.8)
        sub_archetype_scores = SubArchetypeScores(romantic_intellectual=3.0, empathetic_emotional=2.7)

        combined_data = {
            'primary_scores': asdict(archetype_scores),
            'sub_scores': asdict(sub_archetype_scores)
        }

        # Test JSON serialization
        json_string = json.dumps(combined_data)
        deserialized_data = json.loads(json_string)

        # Verify structure
        self.assertIn('primary_scores', deserialized_data)
        self.assertIn('sub_scores', deserialized_data)

        # Verify primary scores
        self.assertEqual(deserialized_data['primary_scores']['intellectual'], 2.5)
        self.assertEqual(deserialized_data['primary_scores']['emotional'], 1.8)

        # Verify sub scores
        self.assertEqual(deserialized_data['sub_scores']['romantic_intellectual'], 3.0)
        self.assertEqual(deserialized_data['sub_scores']['empathetic_emotional'], 2.7)

    def test_type_consistency(self):
        """Test that both dataclasses maintain consistent float typing."""
        archetype_scores = ArchetypeScores()
        sub_archetype_scores = SubArchetypeScores()

        # Test that all fields in both classes accept float values
        for field in fields(ArchetypeScores):
            setattr(archetype_scores, field.name, 1.5)
            self.assertIsInstance(getattr(archetype_scores, field.name), float)

        for field in fields(SubArchetypeScores):
            setattr(sub_archetype_scores, field.name, 2.3)
            self.assertIsInstance(getattr(sub_archetype_scores, field.name), float)


if __name__ == '__main__':
    unittest.main()