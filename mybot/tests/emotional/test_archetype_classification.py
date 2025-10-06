"""
Comprehensive tests for archetype classification system.
Tests the 5-archetype system with diverse user behavior simulation.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import random
from dataclasses import dataclass, field

from services.archetype_classifier import ArchetypeClassifier
from .conftest import TEST_USER_ARCHETYPES, UserBehaviorProfile, EmotionalTestDataGenerator


class TestArchetypeClassificationCore:
    """Core tests for the 5-archetype classification system."""

    @pytest.fixture
    def archetype_classifier(self, mock_session):
        """Setup archetype classifier for testing."""
        return ArchetypeClassifier(mock_session)

    @pytest.mark.asyncio
    async def test_explorer_deep_classification_accuracy(self, archetype_classifier, user_behavior_profiles):
        """Test accurate classification of Explorer Deep archetype."""
        profile = user_behavior_profiles["explorer_deep"]
        
        # Generate realistic Explorer Deep conversation
        conversation_data = [
            {
                "response": "I find myself returning to this not for more content, but for deeper understanding of what's happening between us.",
                "response_time": 22.3,
                "behavioral_markers": ["revisitation_pattern", "depth_seeking", "introspective_language"],
                "engagement_pattern": "sustained_attention"
            },
            {
                "response": "There's something fascinating about how you reveal yourself in layers. I want to understand not just what you show, but what you choose not to show.",
                "response_time": 35.1,
                "behavioral_markers": ["meta_analysis", "pattern_recognition", "curiosity_about_complexity"],
                "engagement_pattern": "analytical_depth"
            },
            {
                "response": "I notice I pause before responding because I want to honor what you're sharing with the attention it deserves.",
                "response_time": 28.7,
                "behavioral_markers": ["self_awareness", "respect_for_process", "mindful_engagement"],
                "engagement_pattern": "thoughtful_processing"
            }
        ]
        
        result = await archetype_classifier.classify_user(12345, conversation_data)
        
        assert result["primary_archetype"] == "explorer_deep"
        assert result["confidence_score"] > 0.85
        assert result["key_traits"]["attention_to_detail"] > 0.8
        assert result["key_traits"]["depth_seeking"] > 0.9
        assert result["key_traits"]["pattern_recognition"] > 0.8

    @pytest.mark.asyncio
    async def test_direct_authentic_classification_accuracy(self, archetype_classifier, user_behavior_profiles):
        """Test accurate classification of Direct Authentic archetype."""
        profile = user_behavior_profiles["direct_authentic"]
        
        conversation_data = [
            {
                "response": "I'm not here for games. There's something real happening and I want to engage with it honestly.",
                "response_time": 3.2,
                "behavioral_markers": ["directness", "authenticity_declaration", "no_pretense"],
                "engagement_pattern": "immediate_honest"
            },
            {
                "response": "Your vulnerability touches something in me I didn't expect. I appreciate when someone is real.",
                "response_time": 4.8,
                "behavioral_markers": ["emotional_directness", "appreciation_for_authenticity", "mutual_recognition"],
                "engagement_pattern": "emotionally_direct"
            },
            {
                "response": "I don't need elaborate mysteries. What draws me is this genuine connection I feel developing.",
                "response_time": 2.9,
                "behavioral_markers": ["preference_for_simplicity", "connection_focused", "genuine_response"],
                "engagement_pattern": "straightforward_emotional"
            }
        ]
        
        result = await archetype_classifier.classify_user(67890, conversation_data)
        
        assert result["primary_archetype"] == "direct_authentic"
        assert result["confidence_score"] > 0.85
        assert result["key_traits"]["directness"] > 0.9
        assert result["key_traits"]["authenticity"] > 0.85
        assert result["key_traits"]["emotional_clarity"] > 0.8

    @pytest.mark.asyncio
    async def test_poet_desire_classification_accuracy(self, archetype_classifier, user_behavior_profiles):
        """Test accurate classification of Poet of Desire archetype."""
        profile = user_behavior_profiles["poet_desire"]
        
        conversation_data = [
            {
                "response": "You speak in whispers that reach the places words usually can't touch. There's poetry in your shadows.",
                "response_time": 18.5,
                "behavioral_markers": ["metaphorical_language", "aesthetic_appreciation", "poetic_expression"],
                "engagement_pattern": "artistic_response"
            },
            {
                "response": "I'm drawn to the spaces between your words, the meanings that live in silence and suggestion.",
                "response_time": 25.2,
                "behavioral_markers": ["subtlety_appreciation", "meaning_seeking", "aesthetic_sensitivity"],
                "engagement_pattern": "contemplative_aesthetic"
            },
            {
                "response": "Beauty and longing interweave here in ways that make me want to linger in each moment.",
                "response_time": 21.8,
                "behavioral_markers": ["beauty_focus", "longing_expression", "moment_appreciation"],
                "engagement_pattern": "aesthetic_immersion"
            }
        ]
        
        result = await archetype_classifier.classify_user(11111, conversation_data)
        
        assert result["primary_archetype"] == "poet_desire"
        assert result["confidence_score"] > 0.80
        assert result["key_traits"]["aesthetic_sensitivity"] > 0.9
        assert result["key_traits"]["metaphorical_thinking"] > 0.85
        assert result["key_traits"]["beauty_appreciation"] > 0.8

    @pytest.mark.asyncio
    async def test_analytic_empathic_classification_accuracy(self, archetype_classifier, user_behavior_profiles):
        """Test accurate classification of Analytic Empathic archetype."""
        profile = user_behavior_profiles["analytic_empathic"]
        
        conversation_data = [
            {
                "response": "I understand that your need for distance is actually a form of intimacy - a way of loving that preserves autonomy.",
                "response_time": 31.4,
                "behavioral_markers": ["analytical_understanding", "empathetic_insight", "paradox_comprehension"],
                "engagement_pattern": "thoughtful_analysis"
            },
            {
                "response": "Your contradictions don't need resolving. They're what make you human and complex and worth knowing.",
                "response_time": 27.9,
                "behavioral_markers": ["acceptance_of_complexity", "empathetic_validation", "intellectual_emotional_integration"],
                "engagement_pattern": "wise_acceptance"
            },
            {
                "response": "I see how you use mystery as both shield and invitation. It's a sophisticated form of emotional intelligence.",
                "response_time": 33.2,
                "behavioral_markers": ["pattern_analysis", "emotional_intelligence_recognition", "sophisticated_understanding"],
                "engagement_pattern": "insightful_analysis"
            }
        ]
        
        result = await archetype_classifier.classify_user(22222, conversation_data)
        
        assert result["primary_archetype"] == "analytic_empathic"
        assert result["confidence_score"] > 0.85
        assert result["key_traits"]["analytical_thinking"] > 0.9
        assert result["key_traits"]["empathetic_understanding"] > 0.85
        assert result["key_traits"]["paradox_acceptance"] > 0.8

    @pytest.mark.asyncio
    async def test_persistent_patient_classification_accuracy(self, archetype_classifier, user_behavior_profiles):
        """Test accurate classification of Persistent Patient archetype."""
        profile = user_behavior_profiles["persistent_patient"]
        
        conversation_data = [
            {
                "response": "I keep returning not out of obsession, but because I sense there's something here worth the patience it requires.",
                "response_time": 15.7,
                "behavioral_markers": ["persistence_explanation", "patience_value", "long_term_thinking"],
                "engagement_pattern": "steady_commitment"
            },
            {
                "response": "I'm willing to wait for you to open at your own pace. Some things can't be rushed, and I respect that.",
                "response_time": 12.3,
                "behavioral_markers": ["respect_for_timing", "willingness_to_wait", "process_respect"],
                "engagement_pattern": "patient_devotion"
            },
            {
                "response": "Each interaction builds on the last. I'm here for the long journey, not quick revelations.",
                "response_time": 19.1,
                "behavioral_markers": ["cumulative_approach", "long_term_commitment", "journey_over_destination"],
                "engagement_pattern": "building_continuity"
            }
        ]
        
        result = await archetype_classifier.classify_user(33333, conversation_data)
        
        assert result["primary_archetype"] == "persistent_patient"
        assert result["confidence_score"] > 0.85
        assert result["key_traits"]["persistence"] > 0.9
        assert result["key_traits"]["patience"] > 0.85
        assert result["key_traits"]["commitment"] > 0.8


class TestArchetypeEvolutionAndStability:
    """Test archetype evolution and stability over time."""

    @pytest.fixture
    def archetype_classifier(self, mock_session):
        return ArchetypeClassifier(mock_session)

    @pytest.mark.asyncio
    async def test_archetype_stability_over_time(self, archetype_classifier):
        """Test that archetype classification remains stable for consistent users."""
        user_id = 12345
        
        # Generate consistent Explorer Deep behavior over time
        time_periods = [
            {"days_ago": 30, "interactions": 5},
            {"days_ago": 14, "interactions": 3},
            {"days_ago": 7, "interactions": 4},
            {"days_ago": 1, "interactions": 2}
        ]
        
        classifications_over_time = []
        
        for period in time_periods:
            conversation_data = []
            for i in range(period["interactions"]):
                conversation_data.append({
                    "response": f"Deep thoughtful response {i} showing consistent depth-seeking behavior",
                    "response_time": random.uniform(15.0, 30.0),  # Consistent thoughtful timing
                    "timestamp": datetime.utcnow() - timedelta(days=period["days_ago"]),
                    "behavioral_markers": ["depth_seeking", "thoughtful_engagement", "pattern_recognition"]
                })
            
            result = await archetype_classifier.classify_user(user_id, conversation_data)
            classifications_over_time.append(result)
        
        # Should show stable classification
        archetypes = [c["primary_archetype"] for c in classifications_over_time]
        assert all(archetype == "explorer_deep" for archetype in archetypes)
        
        # Confidence should increase over time (more data)
        confidences = [c["confidence_score"] for c in classifications_over_time]
        assert confidences[-1] > confidences[0]  # Most recent should be most confident

    @pytest.mark.asyncio
    async def test_natural_archetype_evolution(self, archetype_classifier):
        """Test natural evolution from one archetype to a related one."""
        user_id = 44444
        
        # Simulate evolution from cautious explorer to deep explorer
        evolution_stages = [
            {
                "stage": "initial_cautious",
                "responses": [
                    {"response": "This is intriguing, I'm curious to see where it leads", "response_time": 8.0},
                    {"response": "I'm interested but want to proceed carefully", "response_time": 12.0}
                ],
                "expected_archetype": "explorer_cautious"
            },
            {
                "stage": "growing_comfort",
                "responses": [
                    {"response": "I'm finding myself more drawn to understanding the deeper layers here", "response_time": 18.0},
                    {"response": "There's more complexity here than I first realized, and I want to explore it", "response_time": 22.0}
                ],
                "expected_archetype": "explorer_transitional"
            },
            {
                "stage": "deep_engagement",
                "responses": [
                    {"response": "I find myself returning not just for content but for the deepening understanding of what this connection means", "response_time": 28.0},
                    {"response": "Every interaction reveals new layers that I want to explore with the attention they deserve", "response_time": 31.0}
                ],
                "expected_archetype": "explorer_deep"
            }
        ]
        
        evolution_results = []
        
        for stage in evolution_stages:
            result = await archetype_classifier.classify_user(user_id, stage["responses"])
            evolution_results.append(result)
        
        # Should show logical progression
        final_result = await archetype_classifier.analyze_archetype_evolution(user_id, evolution_results)
        
        assert final_result["evolution_detected"] is True
        assert final_result["evolution_type"] == "natural_deepening"
        assert final_result["final_archetype"] == "explorer_deep"
        assert final_result["evolution_coherence_score"] > 0.8

    @pytest.mark.asyncio
    async def test_inconsistent_archetype_detection(self, archetype_classifier):
        """Test detection of inconsistent/erratic archetype patterns."""
        user_id = 55555
        
        # Generate erratic, inconsistent behavior
        erratic_conversations = [
            {
                "timestamp": datetime.utcnow() - timedelta(days=5),
                "responses": [
                    {"response": "Deep thoughtful analysis of emotional complexity", "response_time": 35.0}
                ],
                "expected_archetype": "analytic_empathic"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(days=3),
                "responses": [
                    {"response": "Cool whatever", "response_time": 0.8}
                ],
                "expected_archetype": "disengaged"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "responses": [
                    {"response": "You are so perfect Diana I love you", "response_time": 1.2}
                ],
                "expected_archetype": "idealization"
            }
        ]
        
        classifications = []
        for conv in erratic_conversations:
            result = await archetype_classifier.classify_user(user_id, conv["responses"])
            classifications.append(result)
        
        stability_analysis = await archetype_classifier.analyze_archetype_stability(user_id, classifications)
        
        assert stability_analysis["stability_score"] < 0.3
        assert stability_analysis["consistency_flags"]["erratic_behavior"] is True
        assert stability_analysis["recommended_action"] == "requires_observation"


class TestArchetypeClassificationEdgeCases:
    """Test edge cases in archetype classification."""

    @pytest.fixture
    def archetype_classifier(self, mock_session):
        return ArchetypeClassifier(mock_session)

    @pytest.mark.asyncio
    async def test_mixed_archetype_traits(self, archetype_classifier):
        """Test classification of users showing mixed archetype traits."""
        user_id = 66666
        
        # User showing both Direct Authentic and Poet Desire traits
        mixed_conversation = [
            {
                "response": "I want to be honest: there's something beautiful and raw about this interaction that I can't quite capture in words.",
                "response_time": 8.5,  # Direct timing
                "behavioral_markers": ["directness", "honesty", "aesthetic_appreciation", "beauty_focus"]
            },
            {
                "response": "Your vulnerability is poetry, but I also need to say plainly that it moves me.",
                "response_time": 12.0,  # Moderate timing
                "behavioral_markers": ["poetic_language", "directness", "emotional_clarity", "aesthetic_sensitivity"]
            }
        ]
        
        result = await archetype_classifier.classify_user(user_id, mixed_conversation)
        
        assert result["classification_type"] == "mixed_traits"
        assert len(result["primary_traits"]) >= 2
        assert result["primary_archetype"] in ["direct_authentic", "poet_desire"]
        assert len(result["secondary_archetypes"]) > 0
        assert result["confidence_score"] < 0.8  # Lower confidence for mixed patterns

    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, archetype_classifier):
        """Test handling of insufficient data for classification."""
        user_id = 77777
        
        # Very minimal interaction data
        minimal_conversation = [
            {"response": "ok", "response_time": 2.0}
        ]
        
        result = await archetype_classifier.classify_user(user_id, minimal_conversation)
        
        assert result["classification_status"] == "insufficient_data"
        assert result["confidence_score"] < 0.5
        assert result["recommended_action"] == "gather_more_data"
        assert "data_points_needed" in result

    @pytest.mark.asyncio
    async def test_artificial_behavior_detection(self, archetype_classifier):
        """Test detection of artificial/bot-like behavior patterns."""
        user_id = 88888
        
        # Artificially perfect responses
        artificial_conversation = [
            {"response": "This is exactly what I expected from this experience", "response_time": 3.0},
            {"response": "You are precisely what I was hoping to find", "response_time": 3.1},
            {"response": "This interaction is perfect in every way", "response_time": 2.9},
            {"response": "I appreciate this exactly as much as intended", "response_time": 3.0}
        ]
        
        result = await archetype_classifier.classify_user(user_id, artificial_conversation)
        
        assert result["artificial_behavior_flags"]["too_consistent_timing"] is True
        assert result["artificial_behavior_flags"]["generic_language"] is True
        assert result["artificial_behavior_flags"]["lack_of_genuine_markers"] is True
        assert result["overall_authenticity_score"] < 0.4

    @pytest.mark.asyncio
    async def test_cultural_linguistic_variations(self, archetype_classifier):
        """Test archetype classification across different linguistic patterns."""
        # Note: This is important for a Spanish-speaking bot
        
        cultural_variations = [
            {
                "user_id": 91000,
                "language_pattern": "formal_spanish",
                "responses": [
                    {"response": "Me encuentro profundamente conmovido por la complejidad emocional de esta experiencia", "response_time": 25.0},
                    {"response": "Deseo comprender las capas más profundas de lo que está ocurriendo entre nosotros", "response_time": 30.0}
                ],
                "expected_archetype": "analytic_empathic"
            },
            {
                "user_id": 91001,
                "language_pattern": "informal_spanish",
                "responses": [
                    {"response": "Esto me llega de verdad, sin rollos", "response_time": 4.0},
                    {"response": "Me gusta que seas real, así sin máscaras", "response_time": 3.5}
                ],
                "expected_archetype": "direct_authentic"
            }
        ]
        
        for variation in cultural_variations:
            result = await archetype_classifier.classify_user(
                variation["user_id"], 
                variation["responses"]
            )
            
            assert result["primary_archetype"] == variation["expected_archetype"]
            assert result["language_pattern_detected"] == variation["language_pattern"]
            assert result["cultural_adaptation_applied"] is True


class TestArchetypeUserBehaviorSimulation:
    """Test comprehensive user behavior simulation for archetype validation."""

    @pytest.fixture
    def behavior_simulator(self, mock_session):
        """Setup behavior simulator for testing."""
        from services.user_behavior_simulator import UserBehaviorSimulator
        return UserBehaviorSimulator(mock_session)

    @pytest.mark.asyncio
    async def test_comprehensive_archetype_journey_simulation(self, behavior_simulator, archetype_classifier):
        """Test complete user journey simulation for each archetype."""
        
        archetype_scenarios = {
            "explorer_deep": {
                "journey_stages": ["curiosity", "investigation", "deep_exploration", "meaningful_connection"],
                "expected_final_traits": ["depth_seeking", "pattern_recognition", "thoughtful_engagement"],
                "typical_response_times": [15.0, 25.0, 35.0, 28.0],
                "expected_confidence": 0.9
            },
            "direct_authentic": {
                "journey_stages": ["immediate_honesty", "emotional_directness", "authentic_connection", "mutual_recognition"],
                "expected_final_traits": ["directness", "authenticity", "emotional_clarity"],
                "typical_response_times": [3.0, 4.0, 2.5, 3.5],
                "expected_confidence": 0.85
            },
            "poet_desire": {
                "journey_stages": ["aesthetic_appreciation", "metaphorical_engagement", "beauty_focus", "artistic_connection"],
                "expected_final_traits": ["aesthetic_sensitivity", "metaphorical_thinking", "beauty_appreciation"],
                "typical_response_times": [18.0, 22.0, 20.0, 25.0],
                "expected_confidence": 0.8
            }
        }
        
        for archetype, scenario in archetype_scenarios.items():
            # Simulate complete user journey
            user_id = hash(archetype) % 100000  # Generate unique user ID
            
            simulated_journey = await behavior_simulator.simulate_archetype_journey(
                user_id=user_id,
                target_archetype=archetype,
                journey_stages=scenario["journey_stages"],
                interaction_count=len(scenario["journey_stages"]) * 3
            )
            
            # Classify the simulated user
            result = await archetype_classifier.classify_user(user_id, simulated_journey["conversation_data"])
            
            # Validate classification accuracy
            assert result["primary_archetype"] == archetype
            assert result["confidence_score"] >= scenario["expected_confidence"] - 0.1
            
            for trait in scenario["expected_final_traits"]:
                assert result["key_traits"][trait] > 0.7
            
            # Validate journey coherence
            journey_analysis = await behavior_simulator.analyze_journey_coherence(simulated_journey)
            assert journey_analysis["coherence_score"] > 0.8
            assert journey_analysis["archetype_consistency"] > 0.85

    @pytest.mark.asyncio
    async def test_archetype_stress_testing(self, behavior_simulator, archetype_classifier):
        """Stress test archetype classification with edge case behaviors."""
        
        stress_test_scenarios = [
            {
                "name": "rapid_archetype_switching",
                "description": "User showing different archetype traits in rapid succession",
                "behavior_pattern": "inconsistent",
                "expected_classification": "unstable"
            },
            {
                "name": "extreme_response_times",
                "description": "User with extremely variable response times",
                "behavior_pattern": "erratic_timing",
                "expected_classification": "timing_inconsistent"  
            },
            {
                "name": "minimal_emotional_markers",
                "description": "User with very few emotional indicators",
                "behavior_pattern": "emotionally_flat",
                "expected_classification": "insufficient_emotional_data"
            }
        ]
        
        for scenario in stress_test_scenarios:
            user_id = hash(scenario["name"]) % 100000
            
            stress_behavior = await behavior_simulator.simulate_stress_test_behavior(
                user_id=user_id,
                behavior_pattern=scenario["behavior_pattern"],
                interaction_count=10
            )
            
            result = await archetype_classifier.classify_user(user_id, stress_behavior["conversation_data"])
            
            # Should handle edge cases gracefully
            assert result["classification_status"] in ["low_confidence", "mixed_traits", "insufficient_data"]
            assert result["confidence_score"] < 0.7
            assert len(result["classification_warnings"]) > 0

    @pytest.mark.asyncio
    async def test_population_level_archetype_distribution(self, behavior_simulator, archetype_classifier):
        """Test archetype classification across a simulated user population."""
        
        # Simulate population of 500 users across all archetypes
        population_size = 500
        expected_distribution = {
            "explorer_deep": 0.35,      # Most common - depth seekers
            "direct_authentic": 0.25,   # Second most - honest connectors  
            "analytic_empathic": 0.15,  # Thoughtful analyzers
            "poet_desire": 0.15,        # Aesthetic appreciators
            "persistent_patient": 0.10  # Devoted followers
        }
        
        simulated_population = []
        
        # Generate users according to expected distribution
        for archetype, proportion in expected_distribution.items():
            user_count = int(population_size * proportion)
            
            for i in range(user_count):
                user_id = len(simulated_population) + 10000
                
                user_journey = await behavior_simulator.simulate_archetype_journey(
                    user_id=user_id,
                    target_archetype=archetype,
                    journey_stages=["initial", "development", "mature"],
                    interaction_count=random.randint(5, 15)
                )
                
                simulated_population.append({
                    "user_id": user_id,
                    "target_archetype": archetype,
                    "conversation_data": user_journey["conversation_data"]
                })
        
        # Classify entire population
        classification_results = []
        
        for user in simulated_population:
            result = await archetype_classifier.classify_user(
                user["user_id"], 
                user["conversation_data"]
            )
            
            classification_results.append({
                "user_id": user["user_id"],
                "target_archetype": user["target_archetype"],
                "classified_archetype": result["primary_archetype"],
                "confidence": result["confidence_score"]
            })
        
        # Analyze classification accuracy
        correct_classifications = sum(
            1 for r in classification_results 
            if r["target_archetype"] == r["classified_archetype"]
        )
        accuracy = correct_classifications / len(classification_results)
        
        # Should achieve high overall accuracy
        assert accuracy > 0.85, f"Population classification accuracy too low: {accuracy}"
        
        # Analyze distribution
        classified_distribution = {}
        for archetype in expected_distribution.keys():
            count = sum(1 for r in classification_results if r["classified_archetype"] == archetype)
            classified_distribution[archetype] = count / len(classification_results)
        
        # Distribution should be reasonably close to expected
        for archetype, expected_prop in expected_distribution.items():
            actual_prop = classified_distribution.get(archetype, 0)
            assert abs(actual_prop - expected_prop) < 0.1, f"Distribution deviation too large for {archetype}"

    @pytest.mark.asyncio
    async def test_archetype_classification_performance_at_scale(self, behavior_simulator, archetype_classifier):
        """Test archetype classification performance with large-scale data."""
        
        # Generate large dataset
        large_dataset = []
        for i in range(1000):  # 1000 users
            user_id = 20000 + i
            archetype = random.choice(list(TEST_USER_ARCHETYPES.keys()))
            
            # Generate 5-10 interactions per user
            interaction_count = random.randint(5, 10)
            
            user_data = await behavior_simulator.simulate_archetype_journey(
                user_id=user_id,
                target_archetype=archetype,
                journey_stages=["initial", "development", "mature"],
                interaction_count=interaction_count
            )
            
            large_dataset.append({
                "user_id": user_id,
                "conversation_data": user_data["conversation_data"]
            })
        
        # Measure performance
        import time
        start_time = time.time()
        
        # Process all classifications
        tasks = [
            archetype_classifier.classify_user(user["user_id"], user["conversation_data"])
            for user in large_dataset
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance requirements
        assert total_time < 30.0, f"Classification took too long: {total_time}s for 1000 users"
        assert len(results) == 1000
        assert all(result["primary_archetype"] is not None for result in results if result)
        
        # Average time per classification should be reasonable
        avg_time_per_classification = total_time / 1000
        assert avg_time_per_classification < 0.03, f"Average time too high: {avg_time_per_classification}s per user"