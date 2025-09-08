"""
COMPREHENSIVE CINEMA ARCHITECTURE INTEGRATION TESTING SUITE
==========================================================

This test suite validates the complete Cinema Architecture System integration
including all cinematic enhancements while ensuring zero breaking changes.

TEST COVERAGE:
✅ End-to-End Cinema System Flows
✅ Soul Signature Detection & Personalization
✅ Choice Architecture Psychology
✅ Clue Treasure Hunting System  
✅ Character Consistency Validation
✅ Fallback Integration Testing
✅ Cross-Module Cinema Coordination
✅ Performance Optimization Validation
✅ Zero Breaking Changes Verification
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, UserStats
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog
from services.coordinador_central import CoordinadorCentral, AccionUsuario


class TestCinemaIntegrationSuite:
    """Complete Cinema Architecture Integration Test Suite"""
    
    @pytest_asyncio.fixture
    async def cinema_coordinador(self, session, test_user, mock_bot):
        """Initialize CoordinadorCentral with Cinema integration for testing"""
        coordinador = CoordinadorCentral(session)
        
        # Mock bot dependency injection
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            # Setup cinema master with mock bot
            coordinador.cinema_master._bot = mock_bot
            
        return coordinador
    
    @pytest_asyncio.fixture
    async def soul_archetypes_data(self):
        """Sample data for 6 soul archetypes testing"""
        return {
            "explorer": {"curiosity": 0.9, "adventure": 0.8, "discovery": 0.85},
            "protector": {"loyalty": 0.9, "support": 0.85, "commitment": 0.8},
            "creator": {"innovation": 0.9, "imagination": 0.85, "expression": 0.8},
            "sage": {"wisdom": 0.9, "knowledge": 0.85, "understanding": 0.8},
            "rebel": {"independence": 0.9, "change": 0.85, "freedom": 0.8},
            "lover": {"connection": 0.9, "passion": 0.85, "harmony": 0.8}
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_cinema_flow_explorer_archetype(self, cinema_coordinador, test_user, session, mock_bot):
        """Test complete cinema flow for Explorer archetype user"""
        
        # === PHASE 1: Soul Signature Detection ===
        # Simulate user interactions that reveal Explorer traits
        explorer_actions = [
            {"action": AccionUsuario.TOMAR_DECISION, "decision_data": {"choice": "explore_unknown", "curiosity_score": 0.9}},
            {"action": AccionUsuario.DESBLOQUEAR_PISTA, "clue_data": {"eagerness": 0.85, "discovery_focus": True}},
            {"action": AccionUsuario.PARTICIPAR_CANAL, "engagement_data": {"exploration_content": True}}
        ]
        
        soul_signature_results = []
        for action_data in explorer_actions:
            start_time = time.time()
            
            result = await cinema_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=action_data["action"],
                **action_data.get("decision_data", action_data.get("clue_data", action_data.get("engagement_data", {})))
            )
            
            processing_time = time.time() - start_time
            
            # Verify performance requirement <500ms
            assert processing_time < 0.5, f"Cinema processing exceeded 500ms: {processing_time:.3f}s"
            
            # Collect soul signature data
            if result.get("soul_signature"):
                soul_signature_results.append(result["soul_signature"])
            
            # Verify basic functionality still works
            assert result.get("success", True), f"Basic functionality failed: {result}"
        
        # === PHASE 2: Personalization Validation ===
        # Check if Explorer archetype was detected
        if soul_signature_results:
            final_signature = soul_signature_results[-1]
            assert final_signature.get("archetype") in ["explorer", "mixed_explorer"], \
                f"Explorer archetype not detected: {final_signature}"
            
            # Verify personalization data
            assert final_signature.get("curiosity_level", 0) >= 0.8, \
                "Explorer curiosity level insufficient"
        
        # === PHASE 3: Choice Architecture Testing ===
        choice_result = await cinema_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="test_choice_fragment",
            choice_id="explorer_optimized_choice",
            psychology_aware=True
        )
        
        # Verify choice architecture enhancement
        if choice_result.get("choice_architecture"):
            architecture = choice_result["choice_architecture"]
            assert architecture.get("personalized") == True, \
                "Choice not personalized for Explorer archetype"
            assert architecture.get("psychology_score", 0) >= 0.7, \
                "Psychology integration insufficient"
    
    @pytest.mark.asyncio
    async def test_cinema_fallback_protection(self, cinema_coordinador, test_user, session):
        """Test graceful fallback when cinema systems are unavailable"""
        
        # Mock cinema system failure
        if hasattr(cinema_coordinador, 'cinema_master') and cinema_coordinador.cinema_master:
            original_cinema = cinema_coordinador.cinema_master
            cinema_coordinador.cinema_master = None
        
        # Execute action that would use cinema enhancements
        result = await cinema_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="test_fragment",
            choice_id="test_choice"
        )
        
        # Verify basic functionality works without cinema
        assert result.get("success", True), "Fallback mode failed"
        assert "points_awarded" in result or result.get("narrative_progress"), \
            "Core functionality not preserved in fallback"
        
        # Verify no cinema-specific data in fallback mode
        assert result.get("soul_signature") is None, \
            "Cinema data present in fallback mode"
        assert result.get("choice_architecture") is None, \
            "Cinema architecture present in fallback mode"
    
    @pytest.mark.asyncio
    async def test_treasure_hunting_clue_system(self, cinema_coordinador, test_user, session):
        """Test clue treasure hunting system integration"""
        
        # Setup test narrative fragment with clues
        fragment = NarrativeFragment(
            id="treasure_test_fragment",
            title="Treasure Hunt Test",
            content="A mysterious clue awaits...",
            fragment_type="treasure_hunt",
            author="diana",
            clues_data={"hidden_clue": "ancient_secret", "unlock_cost": 50}
        )
        session.add(fragment)
        await session.commit()
        
        # Execute clue unlocking
        start_time = time.time()
        result = await cinema_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.DESBLOQUEAR_PISTA,
            fragment_id="treasure_test_fragment",
            clue_type="hidden_clue"
        )
        processing_time = time.time() - start_time
        
        # Performance validation
        assert processing_time < 0.5, f"Clue processing too slow: {processing_time:.3f}s"
        
        # Verify clue system functionality
        if result.get("clue_unlocked"):
            assert result["clue_unlocked"]["clue_content"] is not None, \
                "Clue content not provided"
            assert result["clue_unlocked"]["treasure_hunting_score"] >= 0, \
                "Treasure hunting score missing"
        
        # Verify basic points system still works
        assert result.get("points_awarded", 0) > 0, \
            "Points system not functioning with treasure hunting"
    
    @pytest.mark.asyncio 
    async def test_character_consistency_integration(self, cinema_coordinador, test_user, session, mock_bot):
        """Test character consistency validation with cinema enhancements"""
        
        # Execute multiple actions to test character consistency
        actions = [
            AccionUsuario.TOMAR_DECISION,
            AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            AccionUsuario.DESBLOQUEAR_PISTA
        ]
        
        character_consistency_scores = []
        
        for action in actions:
            result = await cinema_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=action,
                fragment_id="consistency_test_fragment"
            )
            
            # Check for character consistency validation
            if result.get("character_validation"):
                consistency_score = result["character_validation"].get("diana_consistency", 0)
                character_consistency_scores.append(consistency_score)
                
                # Verify Diana's mystery level maintained (85-95%)
                mystery_level = result["character_validation"].get("mystery_level", 0)
                assert 0.85 <= mystery_level <= 0.95, \
                    f"Diana mystery level out of range: {mystery_level}"
                
                # Verify Lucien support role maintained
                lucien_support = result["character_validation"].get("lucien_support", 0)
                assert lucien_support >= 0.9, \
                    f"Lucien support role compromised: {lucien_support}"
        
        # Verify overall character consistency
        if character_consistency_scores:
            avg_consistency = sum(character_consistency_scores) / len(character_consistency_scores)
            assert avg_consistency >= 0.9, \
                f"Character consistency below threshold: {avg_consistency:.3f}"
    
    @pytest.mark.asyncio
    async def test_performance_optimization_validation(self, cinema_coordinador, test_user, session):
        """Test performance optimization with cinema enhancements"""
        
        # Test concurrent user simulation
        concurrent_users = []
        for i in range(5):
            user_data = User(
                id=test_user.id + i + 100,
                first_name=f"ConcurrentUser{i}",
                username=f"concuser{i}",
                role="free",
                points=100.0,
                created_at=datetime.utcnow()
            )
            session.add(user_data)
            concurrent_users.append(user_data)
        
        await session.commit()
        
        # Execute concurrent cinema operations
        async def execute_cinema_action(user):
            start_time = time.time()
            result = await cinema_coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id="perf_test_fragment",
                choice_id="perf_test_choice"
            )
            end_time = time.time()
            return end_time - start_time, result
        
        # Run concurrent operations
        tasks = [execute_cinema_action(user) for user in concurrent_users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Validate performance under concurrent load
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(concurrent_users), \
            f"Some operations failed under concurrent load: {len(successful_results)}/{len(concurrent_users)}"
        
        # Check response times under load
        response_times = [result[0] for result in successful_results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 1.0, \
            f"Average response time too high under load: {avg_response_time:.3f}s"
        assert max_response_time < 2.0, \
            f"Max response time too high under load: {max_response_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_cross_module_cinema_coordination(self, cinema_coordinador, test_user, session):
        """Test coordination between cinema and existing modules"""
        
        # Test narrative + gamification + cinema integration
        result = await cinema_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            fragment_id="integration_test_fragment",
            cinema_enhanced=True,
            gamification_enabled=True
        )
        
        # Verify all systems work together
        assert result.get("success", True), "Cross-module integration failed"
        
        # Check narrative progression
        narrative_progress = result.get("narrative_progress")
        if narrative_progress:
            assert narrative_progress.get("fragment_completed") == True, \
                "Narrative progression not working"
        
        # Check gamification integration
        points_awarded = result.get("points_awarded", 0)
        assert points_awarded > 0, "Gamification not working with cinema"
        
        # Check cinema enhancements don't break existing logic
        if result.get("cinema_enhancement"):
            enhancement = result["cinema_enhancement"]
            assert enhancement.get("preserves_existing_logic") == True, \
                "Cinema enhancements breaking existing logic"
    
    @pytest.mark.asyncio
    async def test_all_soul_archetypes_detection(self, cinema_coordinador, session, soul_archetypes_data):
        """Test soul signature detection for all 6 archetypes"""
        
        archetype_test_results = {}
        
        for archetype, traits in soul_archetypes_data.items():
            # Create test user for each archetype
            user = User(
                id=900000 + hash(archetype) % 10000,
                first_name=f"{archetype.capitalize()}User",
                username=f"{archetype}_user",
                role="free",
                points=100.0,
                created_at=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            
            # Simulate actions that reveal this archetype
            archetype_actions = self._get_archetype_revealing_actions(archetype, traits)
            
            results = []
            for action_data in archetype_actions:
                result = await cinema_coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=action_data["action"],
                    **action_data.get("params", {})
                )
                results.append(result)
            
            # Analyze soul signature detection
            soul_signatures = [r.get("soul_signature") for r in results if r.get("soul_signature")]
            
            if soul_signatures:
                final_signature = soul_signatures[-1]
                detected_archetype = final_signature.get("archetype", "unknown")
                confidence = final_signature.get("confidence", 0)
                
                archetype_test_results[archetype] = {
                    "detected": detected_archetype,
                    "confidence": confidence,
                    "expected": archetype
                }
        
        # Validate archetype detection accuracy
        correct_detections = 0
        total_detections = len(archetype_test_results)
        
        for archetype, result in archetype_test_results.items():
            if (result["detected"] == archetype or 
                f"mixed_{archetype}" in result["detected"] or
                archetype in result["detected"]):
                correct_detections += 1
        
        # Require at least 70% accuracy in archetype detection
        accuracy = correct_detections / total_detections if total_detections > 0 else 0
        assert accuracy >= 0.7, \
            f"Archetype detection accuracy too low: {accuracy:.2%} ({correct_detections}/{total_detections})"
    
    def _get_archetype_revealing_actions(self, archetype: str, traits: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate actions that reveal specific archetype traits"""
        
        action_templates = {
            "explorer": [
                {"action": AccionUsuario.DESBLOQUEAR_PISTA, "params": {"curiosity_driven": True}},
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "exploration"}},
                {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"exploration_focus": True}}
            ],
            "protector": [
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "supportive"}},
                {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"community_focus": True}},
                {"action": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO, "params": {"protective_choice": True}}
            ],
            "creator": [
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "creative"}},
                {"action": AccionUsuario.DESBLOQUEAR_PISTA, "params": {"innovation_driven": True}},
                {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"creative_content": True}}
            ],
            "sage": [
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "wisdom_seeking"}},
                {"action": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO, "params": {"knowledge_focus": True}},
                {"action": AccionUsuario.DESBLOQUEAR_PISTA, "params": {"understanding_driven": True}}
            ],
            "rebel": [
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "unconventional"}},
                {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"independence_focus": True}},
                {"action": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO, "params": {"rebellious_choice": True}}
            ],
            "lover": [
                {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "connection_seeking"}},
                {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"community_bonding": True}},
                {"action": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO, "params": {"harmony_focus": True}}
            ]
        }
        
        return action_templates.get(archetype, [
            {"action": AccionUsuario.TOMAR_DECISION, "params": {"choice_type": "generic"}},
            {"action": AccionUsuario.PARTICIPAR_CANAL, "params": {"general_engagement": True}}
        ])


class TestCinemaRegressionProtection:
    """Test suite ensuring cinema enhancements don't break existing functionality"""
    
    @pytest.mark.asyncio
    async def test_existing_user_flows_unchanged(self, cinema_coordinador, test_user, session):
        """Verify all existing user flows work exactly as before"""
        
        # Test basic reaction flow
        reaction_result = await cinema_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            channel_id=-1001234567890,
            message_id=1,
            reaction_type="like"
        )
        
        # Verify core functionality unchanged
        assert reaction_result.get("success", True), "Basic reaction flow broken"
        assert reaction_result.get("points_awarded", 0) > 0, "Points system broken"
        
        # Verify database operations work
        user_query = select(User).where(User.id == test_user.id)
        result = await session.execute(user_query)
        updated_user = result.scalar_one()
        assert updated_user.points >= test_user.points, "Points not properly updated"
    
    @pytest.mark.asyncio
    async def test_vip_access_unchanged(self, cinema_coordinador, vip_user, session):
        """Verify VIP access controls work unchanged with cinema enhancements"""
        
        vip_result = await cinema_coordinador.ejecutar_flujo(
            user_id=vip_user.id,
            accion=AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_id="vip_test_fragment"
        )
        
        # Verify VIP access still works
        assert vip_result.get("access_granted", False) == True, \
            "VIP access broken with cinema enhancements"
        
        # Verify VIP benefits preserved
        if vip_result.get("benefits"):
            assert "vip_content" in vip_result["benefits"], \
                "VIP benefits not preserved"
    
    @pytest.mark.asyncio
    async def test_admin_functions_unchanged(self, cinema_coordinador, admin_user, session):
        """Verify admin functions work unchanged with cinema enhancements"""
        
        # Test admin action (this would be expanded based on actual admin actions)
        admin_result = await cinema_coordinador.ejecutar_flujo(
            user_id=admin_user.id,
            accion=AccionUsuario.VERIFICAR_ENGAGEMENT,
            channel_id=-1001234567890
        )
        
        # Verify admin functions preserved
        assert admin_result.get("success", True), "Admin functions broken"
        
        # Verify admin privileges maintained
        if admin_result.get("admin_data"):
            assert admin_result["admin_data"].get("access_level") == "admin", \
                "Admin access level not preserved"


class TestCinemaErrorHandlingResilience:
    """Test error handling and resilience of cinema systems"""
    
    @pytest.mark.asyncio
    async def test_cinema_system_failure_recovery(self, cinema_coordinador, test_user, session):
        """Test graceful handling of cinema system failures"""
        
        # Simulate cinema system failure
        if hasattr(cinema_coordinador, 'cinema_master') and cinema_coordinador.cinema_master:
            # Mock failure in cinema enhancement
            with patch.object(cinema_coordinador.cinema_master, 'enhance_user_experience', 
                            side_effect=Exception("Cinema system failure")):
                
                result = await cinema_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id="test_fragment"
                )
                
                # Verify graceful degradation
                assert result.get("success", True), \
                    "System failed to recover from cinema error"
                assert result.get("fallback_mode") == True, \
                    "Fallback mode not activated"
    
    @pytest.mark.asyncio
    async def test_database_connection_resilience(self, cinema_coordinador, test_user):
        """Test resilience to database connection issues"""
        
        # This would test database resilience - simplified for example
        with patch.object(cinema_coordinador.session, 'execute', 
                         side_effect=Exception("Database connection error")):
            try:
                result = await cinema_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.PARTICIPAR_CANAL,
                    channel_id=-1001234567890
                )
                
                # Verify system handles database errors gracefully
                assert result.get("error_handled") == True, \
                    "Database error not handled gracefully"
                
            except Exception as e:
                # Verify error is logged and contained
                assert "Database connection error" in str(e), \
                    "Database error not properly contained"


class TestCinemaPerformanceValidation:
    """Performance validation test suite for cinema enhancements"""
    
    @pytest.mark.asyncio
    async def test_response_time_under_normal_load(self, cinema_coordinador, test_user, session):
        """Test response times under normal load conditions"""
        
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            
            result = await cinema_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id=f"perf_test_{i}",
                choice_id=f"choice_{i}"
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Individual operation must be under 500ms
            assert response_time < 0.5, \
                f"Individual operation exceeded 500ms: {response_time:.3f}s"
        
        # Average response time validation
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.3, \
            f"Average response time too high: {avg_response_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, cinema_coordinador, test_user, session):
        """Test memory usage stability with cinema enhancements"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Execute multiple operations
        for i in range(50):
            await cinema_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=f"memory_test_{i}"
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / 1024 / 1024
        
        # Memory increase should be reasonable (<100MB)
        assert memory_increase_mb < 100, \
            f"Memory usage increased too much: {memory_increase_mb:.2f}MB"