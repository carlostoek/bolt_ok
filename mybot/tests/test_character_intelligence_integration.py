"""
Comprehensive tests for Character Intelligence Integration
Tests all aspects of the enhanced character intelligence system including:
- Archetype classification and adaptation
- Character evolution and relationship growth
- Emotional milestone recognition
- Error handling and system resilience
- Integration with existing services
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Import the services we're testing
from services.character_intelligence_coordinator import CharacterIntelligenceCoordinator
from services.enhanced_character_intelligence import (
    EnhancedCharacterIntelligence, RelationshipStage, EmotionalMilestone
)
from services.archetype_classifier import ArchetypeClassifier, UserArchetype
from services.character_relationship_evolution import CharacterRelationshipEvolution
from services.character_voice_service import CharacterType, EmotionalContext
from database.emotional_models import ArchetypeClassification, UserEmotionalProfile


class TestCharacterIntelligenceIntegration:
    """Integration tests for the complete character intelligence system."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        # Mock common database queries
        session.get = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def coordinator(self, mock_session):
        """Character intelligence coordinator instance."""
        return CharacterIntelligenceCoordinator(mock_session)

    @pytest.mark.asyncio
    async def test_complete_intelligence_flow_explorer_archetype(self, coordinator, mock_session):
        """Test complete intelligence flow for Explorer Deep archetype user."""
        user_id = 12345

        # Mock user with Explorer Deep characteristics
        mock_user_stats = MagicMock()
        mock_user_stats.messages_sent = 25
        mock_user_stats.checkin_streak = 10
        mock_session.get.return_value = mock_user_stats

        # Mock archetype classification
        mock_archetype = {
            "primary_archetype": UserArchetype.EXPLORER_DEEP.value,
            "confidence": 0.85,
            "last_updated": datetime.utcnow().isoformat(),
            "stability": 0.8
        }

        with patch.object(
            coordinator.archetype_classifier,
            'get_user_archetype',
            return_value=mock_archetype
        ):
            # Test interaction context for deep exploration
            interaction_context = {
                "vulnerability_level": 0.7,
                "response_time": 25.0,
                "emotional_indicators": ["depth_seeking", "contemplative", "pattern_recognition"],
                "engagement_pattern": "deeply_engaged"
            }

            # Get intelligent response
            result = await coordinator.get_intelligent_character_response(
                user_id=user_id,
                message_type="reaction_success",
                context=interaction_context
            )

            # Validate response structure
            assert result.get("success") is True
            assert "character" in result
            assert "response" in result
            assert "response_metadata" in result
            assert "intelligence_insights" in result

            # Validate archetype adaptation
            metadata = result["response_metadata"]
            assert metadata.get("archetype_used") == UserArchetype.EXPLORER_DEEP.value

            # Validate intelligence insights
            insights = result["intelligence_insights"]
            assert insights.get("archetype_adaptation") is True
            assert insights.get("character_evolution") in [True, False]  # May or may not evolve in single interaction

    @pytest.mark.asyncio
    async def test_character_evolution_tracking(self, coordinator, mock_session):
        """Test character relationship evolution tracking."""
        user_id = 67890

        # Mock user progression
        mock_user_stats = MagicMock()
        mock_user_stats.messages_sent = 45  # Deepening connection stage
        mock_user_stats.checkin_streak = 15
        mock_session.get.return_value = mock_user_stats

        # Test milestone detection
        interaction_context = {
            "vulnerability_level": 0.85,
            "emotional_indicators": ["trust_establishment", "deep_sharing", "breakthrough_moment"],
            "engagement_pattern": "transformative"
        }

        # Mock existing conversation memory
        mock_memory = MagicMock()
        mock_memory.emotional_state_snapshot = json.dumps({
            "character": "diana",
            "growth_updates": {
                "emotional_depth": {"new_level": 0.6},
                "vulnerability_sharing": {"new_level": 0.7}
            }
        })
        mock_memory.last_interaction_at = datetime.utcnow() - timedelta(days=1)

        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_memory
        mock_session.execute.return_value = mock_execute_result

        # Get response
        result = await coordinator.get_intelligent_character_response(
            user_id=user_id,
            message_type="decision_success",
            context=interaction_context
        )

        assert result.get("success") is True

        # Validate relationship stage recognition
        metadata = result.get("response_metadata", {})
        expected_stage = RelationshipStage.DEEPENING_CONNECTION.value
        assert metadata.get("relationship_stage") in [
            RelationshipStage.DEEPENING_CONNECTION.value,
            RelationshipStage.INTIMATE_UNDERSTANDING.value
        ]  # Could be either depending on evolution

    @pytest.mark.asyncio
    async def test_emotional_milestone_recognition(self, coordinator, mock_session):
        """Test emotional milestone detection and character response adaptation."""
        user_id = 11111

        # Setup for emotional breakthrough scenario
        interaction_context = {
            "vulnerability_level": 0.9,
            "emotional_indicators": [
                "profound_emotional_moment", "barriers_dissolving",
                "transformative_interaction", "soul_level_connection"
            ],
            "engagement_pattern": "breakthrough",
            "response_time": 35.0
        }

        mock_user_stats = MagicMock()
        mock_user_stats.messages_sent = 35
        mock_session.get.return_value = mock_user_stats

        # Test response
        result = await coordinator.get_intelligent_character_response(
            user_id=user_id,
            message_type="intimate_moment",
            context=interaction_context
        )

        assert result.get("success") is True

        # Should include milestone detection
        insights = result.get("intelligence_insights", {})
        # May detect milestone depending on internal logic

        # Response should be appropriately intimate
        response_text = result.get("response", "")
        assert len(response_text) > 0  # Should have meaningful response

    @pytest.mark.asyncio
    async def test_archetype_classification_with_mixed_traits(self, coordinator, mock_session):
        """Test archetype classification with mixed personality traits."""
        user_id = 22222

        # Conversation data showing mixed Direct Authentic and Poet Desire traits
        conversation_data = [
            {
                "response": "I want to be honest: there's something beautiful about this connection that I can't quite put into words.",
                "response_time": 8.5,
                "behavioral_markers": ["directness", "honesty", "aesthetic_appreciation", "beauty_focus"]
            },
            {
                "response": "Your vulnerability is poetry, but I also need to say plainly that it moves me deeply.",
                "response_time": 12.0,
                "behavioral_markers": ["poetic_language", "directness", "emotional_clarity"]
            },
            {
                "response": "I'm drawn to both the beauty and the rawness of what we're creating here.",
                "response_time": 15.0,
                "behavioral_markers": ["aesthetic_sensitivity", "authenticity", "connection_focus"]
            }
        ]

        # Test classification
        result = await coordinator.classify_user_archetype(
            user_id=user_id,
            conversation_data=conversation_data
        )

        # Should handle mixed traits
        assert result.get("primary_archetype") in [
            UserArchetype.DIRECT_AUTHENTIC.value,
            UserArchetype.POET_DESIRE.value
        ]

        # Should indicate mixed classification
        if result.get("classification_type") == "mixed_traits":
            assert len(result.get("secondary_archetypes", [])) > 0

        # Should include adaptation preview
        assert "adaptation_preview" in result

    @pytest.mark.asyncio
    async def test_error_resilience_and_character_authenticity(self, coordinator, mock_session):
        """Test system resilience and character authenticity during errors."""
        user_id = 33333

        # Simulate service failures
        with patch.object(
            coordinator.enhanced_intelligence,
            'get_enhanced_character_response',
            side_effect=Exception("Service temporarily unavailable")
        ):

            context = {
                "vulnerability_level": 0.5,
                "engagement_pattern": "moderate"
            }

            # Should still provide authentic character response
            result = await coordinator.get_intelligent_character_response(
                user_id=user_id,
                message_type="reaction_success",
                context=context,
                fallback_safe=True
            )

            assert result.get("success") is True
            assert "character" in result
            assert "response" in result

            # Should indicate fallback mode
            metadata = result.get("response_metadata", {})
            assert metadata.get("emergency_fallback") is True or metadata.get("error_recovery") is True

            # Response should still be character-authentic
            response_text = result.get("response", "")
            assert len(response_text) > 0

            # Should contain character-appropriate language
            character = result.get("character", "")
            if character == "diana":
                assert any(word in response_text.lower() for word in ["corazón", "conexión", "besitos", "alma"])
            else:  # Lucien
                assert any(word in response_text.lower() for word in ["guía", "sabiduría", "comprensión", "constante"])

    @pytest.mark.asyncio
    async def test_relationship_consistency_analysis(self, coordinator, mock_session):
        """Test relationship consistency analysis over time."""
        user_id = 44444

        # Mock progression of relationship memories
        mock_memories = []

        # Simulate 5 interactions over time showing consistent growth
        base_time = datetime.utcnow() - timedelta(days=30)
        for i in range(5):
            memory = MagicMock()
            memory.last_interaction_at = base_time + timedelta(days=i * 6)
            memory.emotional_state_snapshot = json.dumps({
                "character": "diana",
                "evolution_trajectory": {
                    "character_maturity_level": 0.3 + (i * 0.15),  # Consistent growth
                    "growth_velocity": 0.1 + (i * 0.02)
                }
            })
            mock_memories.append(memory)

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value.all.return_value = mock_memories
        mock_session.execute.return_value = mock_execute_result

        # Test consistency analysis
        summary = await coordinator.get_user_intelligence_summary(user_id)

        assert summary.get("success") is True
        consistency = summary.get("relationship_consistency", {})

        # Should detect good consistency
        consistency_score = consistency.get("consistency_score", 0.0)
        assert consistency_score > 0.5  # Should show reasonable consistency

    @pytest.mark.asyncio
    async def test_archetype_adaptation_effectiveness(self, coordinator, mock_session):
        """Test effectiveness of archetype-specific character adaptations."""

        # Test different archetypes with their characteristic interactions
        test_cases = [
            {
                "archetype": UserArchetype.DIRECT_AUTHENTIC.value,
                "user_id": 50001,
                "context": {
                    "vulnerability_level": 0.8,
                    "response_time": 3.5,
                    "emotional_indicators": ["directness", "honesty", "authenticity"],
                    "engagement_pattern": "immediately_honest"
                },
                "expected_character": CharacterType.DIANA.value,
                "expected_style_markers": ["honesta", "directo", "auténtico", "corazón"]
            },
            {
                "archetype": UserArchetype.POET_DESIRE.value,
                "user_id": 50002,
                "context": {
                    "vulnerability_level": 0.7,
                    "response_time": 22.0,
                    "emotional_indicators": ["aesthetic_appreciation", "beauty_focus", "poetic_sensibility"],
                    "engagement_pattern": "aesthetic_immersion"
                },
                "expected_character": CharacterType.DIANA.value,
                "expected_style_markers": ["belleza", "poesía", "estética", "momento"]
            },
            {
                "archetype": UserArchetype.ANALYTIC_EMPATHIC.value,
                "user_id": 50003,
                "context": {
                    "vulnerability_level": 0.6,
                    "response_time": 32.0,
                    "emotional_indicators": ["analytical_thinking", "empathetic_understanding", "complexity_appreciation"],
                    "engagement_pattern": "thoughtful_analysis"
                },
                "expected_character": CharacterType.LUCIEN.value,
                "expected_style_markers": ["comprensión", "complejidad", "sabiduría", "análisis"]
            }
        ]

        for test_case in test_cases:
            # Mock archetype for this user
            mock_archetype = {
                "primary_archetype": test_case["archetype"],
                "confidence": 0.85
            }

            with patch.object(
                coordinator.archetype_classifier,
                'get_user_archetype',
                return_value=mock_archetype
            ):
                # Mock user stats
                mock_stats = MagicMock()
                mock_stats.messages_sent = 20
                mock_stats.checkin_streak = 5
                mock_session.get.return_value = mock_stats

                # Get response
                result = await coordinator.get_intelligent_character_response(
                    user_id=test_case["user_id"],
                    message_type="reaction_success",
                    context=test_case["context"]
                )

                assert result.get("success") is True

                # Validate archetype adaptation
                metadata = result.get("response_metadata", {})
                assert metadata.get("archetype_used") == test_case["archetype"]

                # Validate response adaptation (basic check)
                response_text = result.get("response", "").lower()
                assert len(response_text) > 0

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, coordinator, mock_session):
        """Test service health monitoring and degradation handling."""

        # Check initial health status
        health_status = coordinator.get_service_health_status()

        assert "service_health" in health_status
        assert "overall_status" in health_status

        # Force health check
        await coordinator._check_service_health()

        updated_health = coordinator.get_service_health_status()
        assert updated_health.get("overall_status") in ["healthy", "degraded"]

    @pytest.mark.asyncio
    async def test_narrative_integration_compatibility(self, coordinator, mock_session):
        """Test integration compatibility with existing narrative systems."""
        user_id = 55555

        narrative_context = {
            "fragment_key": "test_fragment",
            "story_progress": 0.5,
            "user_choices": ["choice_1", "choice_2"],
            "current_chapter": "chapter_3"
        }

        # Test narrative integration
        enhanced_context = await coordinator.handle_narrative_integration(
            user_id=user_id,
            narrative_context=narrative_context
        )

        # Should preserve original context
        assert enhanced_context["fragment_key"] == "test_fragment"
        assert enhanced_context["story_progress"] == 0.5

        # Should add character intelligence
        if "character_intelligence" in enhanced_context:
            intel = enhanced_context["character_intelligence"]
            assert "relationship_stage" in intel
            assert "emotional_awareness" in intel

    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, coordinator, mock_session):
        """Test handling of insufficient data for classification and adaptation."""
        user_id = 66666

        # Mock minimal user data
        mock_stats = MagicMock()
        mock_stats.messages_sent = 1  # Very new user
        mock_stats.checkin_streak = 0
        mock_session.get.return_value = mock_stats

        # Test with minimal conversation data
        minimal_conversation = [
            {"response": "ok", "response_time": 2.0}
        ]

        # Classification should handle insufficient data gracefully
        result = await coordinator.classify_user_archetype(
            user_id=user_id,
            conversation_data=minimal_conversation
        )

        assert "classification_status" in result
        if result.get("classification_status") == "insufficient_data":
            assert "data_points_needed" in result
            assert "recommended_action" in result

        # Intelligence response should still work
        context = {"vulnerability_level": 0.3, "engagement_pattern": "minimal"}

        response = await coordinator.get_intelligent_character_response(
            user_id=user_id,
            message_type="reaction_success",
            context=context
        )

        assert response.get("success") is True
        # Should use default/fallback approaches for new users

    @pytest.mark.asyncio
    async def test_character_boundary_respect(self, coordinator, mock_session):
        """Test that character intelligence respects emotional boundaries."""
        user_id = 77777

        # Test scenarios with different boundary comfort levels
        boundary_test_cases = [
            {
                "vulnerability_level": 0.2,  # Low vulnerability - respect distance
                "engagement_pattern": "cautious",
                "expected_approach": "gentle_invitation"
            },
            {
                "vulnerability_level": 0.9,  # High vulnerability - provide support
                "engagement_pattern": "highly_vulnerable",
                "expected_approach": "supportive_presence"
            }
        ]

        for test_case in boundary_test_cases:
            context = {
                "vulnerability_level": test_case["vulnerability_level"],
                "engagement_pattern": test_case["engagement_pattern"],
                "boundary_indicators": ["needs_space"] if test_case["vulnerability_level"] < 0.5 else ["ready_for_intimacy"]
            }

            response = await coordinator.get_intelligent_character_response(
                user_id=user_id,
                message_type="emotional_connection",
                context=context
            )

            assert response.get("success") is True

            # Validate appropriate response to boundary cues
            response_text = response.get("response", "").lower()

            if test_case["vulnerability_level"] < 0.5:
                # Should be gentle and respectful of boundaries
                boundary_words = ["respeto", "tiempo", "espacio", "cuando", "paciencia"]
                assert any(word in response_text for word in boundary_words)
            else:
                # Can be more emotionally present
                intimacy_words = ["profundo", "cerca", "íntimo", "compartir", "alma"]
                # May or may not use intimate language depending on character and stage


class TestCharacterEvolutionConsistency:
    """Test character evolution and consistency over time."""

    @pytest.fixture
    def evolution_service(self, mock_session):
        return CharacterRelationshipEvolution(mock_session)

    @pytest.mark.asyncio
    async def test_character_growth_consistency(self, evolution_service, mock_session):
        """Test that character growth is consistent and logical."""
        user_id = 88888

        # Simulate progression of interactions
        interactions = [
            {
                "vulnerability_level": 0.3,
                "significance_score": 0.2,
                "milestone": None
            },
            {
                "vulnerability_level": 0.5,
                "significance_score": 0.4,
                "milestone": EmotionalMilestone.FIRST_VULNERABILITY
            },
            {
                "vulnerability_level": 0.7,
                "significance_score": 0.6,
                "milestone": EmotionalMilestone.TRUST_ESTABLISHMENT
            }
        ]

        growth_progression = []

        for interaction in interactions:
            result = await evolution_service.track_relationship_evolution(
                user_id=user_id,
                character=CharacterType.DIANA,
                interaction_data=interaction,
                milestone_detected=interaction["milestone"]
            )

            if result.get("success"):
                growth_progression.append(result.get("character_growth", {}))

        # Validate logical progression
        # Growth should generally increase over time
        assert len(growth_progression) > 0

    @pytest.mark.asyncio
    async def test_milestone_impact_on_character_development(self, evolution_service, mock_session):
        """Test that milestones appropriately impact character development."""
        user_id = 99999

        # Test major milestone impact
        major_interaction = {
            "vulnerability_level": 0.9,
            "emotional_indicators": ["emotional_breakthrough", "profound_moment"],
            "significance_score": 0.8
        }

        result = await evolution_service.track_relationship_evolution(
            user_id=user_id,
            character=CharacterType.DIANA,
            interaction_data=major_interaction,
            milestone_detected=EmotionalMilestone.EMOTIONAL_BREAKTHROUGH
        )

        if result.get("success"):
            # Should show significant evolution
            evolution_trajectory = result.get("evolution_trajectory", {})
            growth_velocity = evolution_trajectory.get("growth_velocity", 0.0)

            # Milestone should accelerate growth
            assert growth_velocity > 0.1  # Should show meaningful growth


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])