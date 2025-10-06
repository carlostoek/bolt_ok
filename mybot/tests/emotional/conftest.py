"""
Comprehensive testing configuration for emotional evaluation system.
Fixtures and utilities for testing Diana's emotional intelligence.
"""
import pytest
import asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import json
from dataclasses import dataclass, field

@dataclass
class UserBehaviorProfile:
    """Represents a simulated user's behavioral patterns for testing."""
    archetype: str
    response_time_pattern: str  # "immediate", "thoughtful", "variable"
    emotional_depth: str  # "surface", "moderate", "deep" 
    consistency_level: float  # 0.0 to 1.0
    vulnerability_threshold: float  # 0.0 to 1.0
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def generate_response_time(self) -> float:
        """Generate realistic response time based on pattern."""
        import random
        patterns = {
            "immediate": random.uniform(0.5, 2.0),
            "thoughtful": random.uniform(10.0, 30.0),
            "variable": random.choice([random.uniform(1.0, 3.0), random.uniform(15.0, 45.0)])
        }
        return patterns[self.response_time_pattern]
    
    def generate_emotional_response(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Generate a response based on this profile's characteristics."""
        base_response = {
            "text": "",
            "emotional_markers": [],
            "vulnerability_level": 0.0,
            "authenticity_score": 0.0,
            "response_time": self.generate_response_time()
        }
        
        # Customize based on archetype
        if self.archetype == "explorer_deep":
            base_response["emotional_markers"] = ["curiosity", "depth", "introspection"]
            base_response["vulnerability_level"] = 0.7
            base_response["authenticity_score"] = 0.8
        elif self.archetype == "direct_authentic":
            base_response["emotional_markers"] = ["directness", "honesty", "clarity"]
            base_response["vulnerability_level"] = 0.8
            base_response["authenticity_score"] = 0.9
        elif self.archetype == "poet_desire":
            base_response["emotional_markers"] = ["metaphor", "aesthetics", "longing"]
            base_response["vulnerability_level"] = 0.6
            base_response["authenticity_score"] = 0.7
        elif self.archetype == "analytic_empathic":
            base_response["emotional_markers"] = ["analysis", "empathy", "understanding"]
            base_response["vulnerability_level"] = 0.5
            base_response["authenticity_score"] = 0.8
        elif self.archetype == "persistent_patient":
            base_response["emotional_markers"] = ["patience", "devotion", "persistence"]
            base_response["vulnerability_level"] = 0.4
            base_response["authenticity_score"] = 0.7
        
        return base_response

# Create test user behavior profiles for the 5 archetypes mentioned in the narrative
TEST_USER_ARCHETYPES = {
    "explorer_deep": UserBehaviorProfile(
        archetype="explorer_deep",
        response_time_pattern="thoughtful",
        emotional_depth="deep",
        consistency_level=0.9,
        vulnerability_threshold=0.7
    ),
    "direct_authentic": UserBehaviorProfile(
        archetype="direct_authentic", 
        response_time_pattern="immediate",
        emotional_depth="moderate",
        consistency_level=0.8,
        vulnerability_threshold=0.8
    ),
    "poet_desire": UserBehaviorProfile(
        archetype="poet_desire",
        response_time_pattern="variable", 
        emotional_depth="deep",
        consistency_level=0.7,
        vulnerability_threshold=0.6
    ),
    "analytic_empathic": UserBehaviorProfile(
        archetype="analytic_empathic",
        response_time_pattern="thoughtful",
        emotional_depth="moderate",
        consistency_level=0.9,
        vulnerability_threshold=0.5
    ),
    "persistent_patient": UserBehaviorProfile(
        archetype="persistent_patient",
        response_time_pattern="variable",
        emotional_depth="moderate", 
        consistency_level=0.8,
        vulnerability_threshold=0.4
    )
}

@pytest.fixture
def user_behavior_profiles():
    """Fixture providing test user archetypes."""
    return TEST_USER_ARCHETYPES

@pytest.fixture
async def mock_narrative_engine():
    """Mock narrative engine with emotional evaluation capabilities."""
    engine = AsyncMock()
    engine.current_user_state = {}
    engine.emotional_analysis_results = {}
    engine.archetype_classifications = {}
    
    # Mock methods for emotional evaluation
    engine.analyze_user_response = AsyncMock()
    engine.classify_user_archetype = AsyncMock()
    engine.adapt_narrative_content = AsyncMock()
    engine.validate_emotional_authenticity = AsyncMock()
    
    return engine

@pytest.fixture
async def mock_session():
    """Mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock common database operations
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    session.add = AsyncMock()
    
    return session

@pytest.fixture
def emotional_test_scenarios():
    """Predefined test scenarios for emotional validation."""
    return {
        "cartography_responses": {
            "high_vulnerability": [
                "The last time I wanted something without explanation was when I saw my reflection and felt completely unknown to myself.",
                "I hide the part of me that desperately wants to be understood, even when I'm showing everything.",
                "If I could choose a wound, it would be the one that taught me that love and fear can coexist.",
                "I love like someone who embraces knowing they might have to let go.",
                "Being completely seen terrifies me more than invisibility, because visibility demands truth."
            ],
            "moderate_vulnerability": [
                "I wanted to travel somewhere I'd never been, without knowing why that place called to me.",
                "I keep private the thoughts I have in the moments just before sleep.",
                "The wound I'd choose would be something that made me more compassionate.",
                "I love carefully, with awareness of both connection and autonomy.", 
                "Being seen completely would be challenging but ultimately liberating."
            ],
            "low_vulnerability": [
                "I recently wanted to try a new restaurant for no particular reason.",
                "I don't really hide much when I'm being open with someone.",
                "I wouldn't choose a wound, I prefer to avoid them.",
                "I love openly and expect the same in return.",
                "I'd rather be seen completely than remain invisible."
            ]
        },
        "timing_patterns": {
            "authentic_immediate": [0.5, 1.2, 2.1, 1.8, 1.4],  # Quick but consistent
            "authentic_thoughtful": [15.3, 22.1, 18.7, 25.4, 19.2],  # Consistently thoughtful
            "calculated": [8.5, 12.3, 7.8, 11.9, 9.4],  # Too consistent, likely calculated
            "erratic": [0.3, 45.2, 2.1, 38.7, 1.8]  # Inconsistent, possibly inauthentic
        }
    }

@pytest.fixture
def diana_response_validation():
    """Validation patterns for Diana's adaptive responses."""
    return {
        "recognition_patterns": {
            "high_vulnerability": [
                "Tu honestidad me desarma",
                "una desnudez que va más allá",
                "hay algo perturbador y hermoso",
                "reconocer mi propia hambre reflejada"
            ],
            "thoughtful_pause": [
                "Tu calma me desarma",
                "esa tensión entre deseo y reflexión",
                "comprenden que lo genuino no debe apresurarse",
                "honrar el tiempo"
            ],
            "immediate_authentic": [
                "reaccionaste sin calcularlo",
                "belleza en esa entrega espontánea",
                "impulsivo... pero no inconsciente",
                "más verdad que en mil gestos calculados"
            ]
        },
        "archetype_specific": {
            "explorer_deep": "Tu atención meticulosa me conmueve",
            "direct_authentic": "Tu honestidad sin filtros es refrescante", 
            "poet_desire": "Hablas en el lenguaje del alma",
            "analytic_empathic": "Tu manera de comprender es tanto intelectual como emocional",
            "persistent_patient": "Tu persistencia tiene una calidad de devoción"
        }
    }

@pytest.fixture
def emotional_consistency_validators():
    """Functions to validate emotional consistency across interactions."""
    
    def validate_progression_coherence(interaction_history: List[Dict]) -> Dict[str, Any]:
        """Validate that emotional progression makes logical sense."""
        if len(interaction_history) < 2:
            return {"valid": True, "reason": "insufficient_data"}
        
        # Check for sudden personality changes
        personality_scores = [i.get("personality_consistency", 0.5) for i in interaction_history]
        variance = max(personality_scores) - min(personality_scores)
        
        if variance > 0.3:  # Too much variance indicates inconsistency
            return {"valid": False, "reason": "personality_inconsistency", "variance": variance}
        
        return {"valid": True, "coherence_score": 1.0 - variance}
    
    def validate_archetype_stability(classifications: List[str]) -> Dict[str, Any]:
        """Validate that archetype classification is stable across interactions."""
        if len(set(classifications)) > 2:  # Too many different classifications
            return {"valid": False, "reason": "archetype_instability", "classifications": classifications}
        
        return {"valid": True, "primary_archetype": max(set(classifications), key=classifications.count)}
    
    def validate_emotional_authenticity_progression(authenticity_scores: List[float]) -> Dict[str, Any]:
        """Validate that authenticity scores progress logically."""
        if len(authenticity_scores) < 3:
            return {"valid": True, "reason": "insufficient_data"}
        
        # Authenticity should generally increase or remain stable, not dramatically decrease
        for i in range(1, len(authenticity_scores)):
            if authenticity_scores[i] < authenticity_scores[i-1] - 0.3:  # Significant drop
                return {"valid": False, "reason": "authenticity_regression", "scores": authenticity_scores}
        
        return {"valid": True, "progression_valid": True}
    
    return {
        "validate_progression_coherence": validate_progression_coherence,
        "validate_archetype_stability": validate_archetype_stability, 
        "validate_emotional_authenticity_progression": validate_emotional_authenticity_progression
    }

@pytest.fixture
def performance_benchmarks():
    """Performance benchmarks for emotional analysis components."""
    return {
        "response_time_limits": {
            "emotional_analysis": 0.5,  # seconds
            "archetype_classification": 0.3,
            "narrative_adaptation": 0.8,
            "authenticity_validation": 0.2
        },
        "accuracy_thresholds": {
            "archetype_classification": 0.85,
            "authenticity_detection": 0.80,
            "emotional_depth_analysis": 0.75,
            "consistency_validation": 0.90
        },
        "memory_limits": {
            "max_session_memory_mb": 50,
            "max_user_history_size": 1000
        }
    }

class EmotionalTestDataGenerator:
    """Generates realistic test data for emotional system testing."""
    
    @staticmethod
    def generate_conversation_sequence(
        user_profile: UserBehaviorProfile, 
        num_interactions: int = 5,
        scenario: str = "level_progression"
    ) -> List[Dict[str, Any]]:
        """Generate a realistic conversation sequence for testing."""
        interactions = []
        
        for i in range(num_interactions):
            interaction = {
                "user_id": 12345,
                "timestamp": datetime.utcnow() - timedelta(minutes=(num_interactions - i) * 30),
                "interaction_type": "narrative_response",
                "level": f"level_{min(i + 1, 6)}",
                "user_response": user_profile.generate_emotional_response(
                    f"Level {i + 1} prompt", 
                    {"previous_interactions": interactions}
                ),
                "expected_archetype": user_profile.archetype
            }
            interactions.append(interaction)
        
        return interactions
    
    @staticmethod
    def generate_edge_case_scenarios() -> Dict[str, List[Dict]]:
        """Generate edge case scenarios for robust testing."""
        return {
            "archetype_switching": [
                {"user_id": 123, "responses": ["deep_thoughtful_response"], "expected_archetype": "explorer_deep"},
                {"user_id": 123, "responses": ["direct_quick_response"], "expected_archetype": "direct_authentic"},
                # Should detect inconsistency, not just switch archetypes
            ],
            "emotional_analysis_failures": [
                {"input": "", "expected_result": "insufficient_data"},
                {"input": "test " * 1000, "expected_result": "input_too_long"},
                {"input": None, "expected_result": "invalid_input"}
            ],
            "performance_stress": [
                {"concurrent_users": 100, "expected_response_time": "<2s"},
                {"large_history_size": 500, "expected_memory_usage": "<100MB"}
            ]
        }

@pytest.fixture
def emotional_test_data_generator():
    """Fixture providing the test data generator."""
    return EmotionalTestDataGenerator()

# Integration test helpers
async def setup_test_narrative_state(session: AsyncSession, user_id: int, fragment_key: str):
    """Helper to setup narrative state for testing."""
    from database.narrative_models import UserNarrativeState
    
    state = UserNarrativeState(
        user_id=user_id,
        current_fragment_key=fragment_key,
        choices_made=[],
        fragments_visited=1
    )
    session.add(state)
    await session.commit()
    return state

async def cleanup_test_data(session: AsyncSession):
    """Helper to cleanup test data after tests."""
    # Implementation would clean up test user states, etc.
    pass