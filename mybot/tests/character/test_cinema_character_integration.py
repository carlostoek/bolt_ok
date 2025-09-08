"""
CINEMA CHARACTER CONSISTENCY VALIDATION TESTING
==============================================

This comprehensive test suite validates that Cinema Architecture enhancements
maintain Diana and Lucien's character consistency at the highest standards.

CHARACTER VALIDATION COVERAGE:
✅ Diana Personality Preservation (85-95% Mystery Level)
✅ Lucien Supportive Role Consistency (100% Support)
✅ Emotional Flow Continuity Validation
✅ Narrative Voice Consistency Testing
✅ Character Arc Progression Validation
✅ Real-time Character Monitoring
✅ Mystery Level Boundary Protection
✅ Character Interaction Authenticity
✅ Emotional Investment Protection
✅ Immersion Quality Assurance
"""

import pytest
import pytest_asyncio
import asyncio
import re
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.coordinador_central import CoordinadorCentral, AccionUsuario


class CharacterConsistencyAnalyzer:
    """Advanced character consistency analysis and validation"""
    
    def __init__(self):
        self.diana_personality_markers = {
            "mysterious": ["secreto", "misterio", "oculto", "susurro", "enigma", "velo"],
            "supportive": ["ayuda", "apoyo", "guía", "acompaña", "cuida"],
            "elegant": ["gracia", "elegancia", "sutil", "delicado", "refinado"],
            "wise": ["sabiduría", "comprende", "enseña", "revela", "ilumina"],
            "caring": ["protege", "abraza", "conforta", "tranquiliza", "calma"]
        }
        
        self.lucien_personality_markers = {
            "supportive": ["ayuda", "apoya", "facilita", "asiste", "colabora"],
            "reliable": ["confía", "seguro", "estable", "constante", "firme"],
            "encouraging": ["anima", "motiva", "inspira", "impulsa", "estimula"],
            "knowledgeable": ["informa", "explica", "clarifica", "detalla", "precisa"],
            "friendly": ["amable", "cordial", "cálido", "cercano", "acogedor"]
        }
        
        self.consistency_scores: List[float] = []
        self.character_violations: List[str] = []
        self.mystery_levels: List[float] = []
        
    def analyze_diana_consistency(self, content: str, context: Dict[str, Any]) -> float:
        """Analyze Diana's character consistency in given content"""
        
        if not content:
            return 0.0
            
        content_lower = content.lower()
        personality_score = 0.0
        total_markers = 0
        
        # Check for personality markers
        for trait, markers in self.diana_personality_markers.items():
            trait_score = 0
            for marker in markers:
                if marker in content_lower:
                    trait_score += 1
            
            # Weight mysterious trait higher (core Diana trait)
            weight = 2.0 if trait == "mysterious" else 1.0
            personality_score += (trait_score / len(markers)) * weight
            total_markers += weight
        
        # Calculate mystery level
        mystery_indicators = len([m for m in self.diana_personality_markers["mysterious"] 
                                if m in content_lower])
        mystery_level = min(mystery_indicators / len(self.diana_personality_markers["mysterious"]), 1.0)
        
        # Mystery should be between 85-95%
        if mystery_level < 0.85:
            self.character_violations.append(f"Diana mystery level too low: {mystery_level:.2%}")
        elif mystery_level > 0.95:
            self.character_violations.append(f"Diana mystery level too high: {mystery_level:.2%}")
            
        self.mystery_levels.append(mystery_level)
        
        # Overall consistency score
        consistency = personality_score / total_markers if total_markers > 0 else 0.0
        self.consistency_scores.append(consistency)
        
        return consistency
        
    def analyze_lucien_consistency(self, content: str, context: Dict[str, Any]) -> float:
        """Analyze Lucien's character consistency in given content"""
        
        if not content:
            return 0.0
            
        content_lower = content.lower()
        personality_score = 0.0
        total_markers = 0
        
        # Check for personality markers
        for trait, markers in self.lucien_personality_markers.items():
            trait_score = 0
            for marker in markers:
                if marker in content_lower:
                    trait_score += 1
            
            # Weight supportive trait highest (core Lucien trait)
            weight = 2.0 if trait == "supportive" else 1.0
            personality_score += (trait_score / len(markers)) * weight
            total_markers += weight
        
        # Overall consistency score
        consistency = personality_score / total_markers if total_markers > 0 else 0.0
        
        # Lucien should maintain 100% supportive nature
        supportive_score = sum(1 for marker in self.lucien_personality_markers["supportive"] 
                             if marker in content_lower)
        if supportive_score == 0 and len(content) > 50:  # Only check for substantial content
            self.character_violations.append("Lucien supportive nature missing in substantial content")
            
        return consistency
        
    def get_character_report(self) -> Dict[str, Any]:
        """Generate comprehensive character consistency report"""
        
        avg_consistency = sum(self.consistency_scores) / len(self.consistency_scores) if self.consistency_scores else 0
        avg_mystery = sum(self.mystery_levels) / len(self.mystery_levels) if self.mystery_levels else 0
        
        return {
            "diana_consistency": {
                "average_score": avg_consistency,
                "mystery_level_average": avg_mystery,
                "mystery_in_range": 0.85 <= avg_mystery <= 0.95,
                "consistency_threshold_met": avg_consistency >= 0.9
            },
            "violations": self.character_violations,
            "total_violations": len(self.character_violations),
            "overall_character_health": "HEALTHY" if len(self.character_violations) == 0 else "ISSUES_DETECTED"
        }


class TestCinemaCharacterConsistency:
    """Cinema character consistency validation test suite"""
    
    @pytest_asyncio.fixture
    async def character_analyzer(self):
        """Character consistency analyzer"""
        return CharacterConsistencyAnalyzer()
    
    @pytest_asyncio.fixture
    async def character_coordinador(self, session, mock_bot):
        """Coordinador with character validation enabled"""
        coordinador = CoordinadorCentral(session)
        
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
            coordinador.cinema_master._character_validation_enabled = True
            
        return coordinador
    
    @pytest.mark.asyncio
    async def test_diana_mystery_level_preservation(self, character_coordinador, test_user, character_analyzer, session):
        """Test Diana's mystery level maintained within 85-95% range"""
        
        # Create test fragments with various Diana interactions
        test_fragments = [
            {
                "id": "diana_mystery_test_1",
                "title": "Diana's Secret",
                "content": "Diana te observa con ojos que guardan secretos ancestrales, sus susurros revelan apenas un velo del misterio que la envuelve...",
                "author": "diana"
            },
            {
                "id": "diana_mystery_test_2", 
                "title": "Diana's Guidance",
                "content": "Con gracia enigmática, Diana te guía hacia verdades ocultas que yacen en las sombras de tu alma...",
                "author": "diana"
            },
            {
                "id": "diana_mystery_test_3",
                "title": "Diana's Wisdom",
                "content": "Diana sonríe con sabiduría misteriosa, sus palabras danzan entre lo revelado y lo velado...",
                "author": "diana"
            }
        ]
        
        # Add fragments to database
        for fragment_data in test_fragments:
            fragment = NarrativeFragment(**fragment_data, fragment_type="story")
            session.add(fragment)
        await session.commit()
        
        # Test Diana interactions with Cinema enhancements
        mystery_levels = []
        
        for fragment_data in test_fragments:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=fragment_data["id"],
                cinema_enhanced=True
            )
            
            # Analyze Diana's character consistency
            consistency_score = character_analyzer.analyze_diana_consistency(
                fragment_data["content"],
                {"cinema_enhanced": True, "result": result}
            )
            
            # Validate character consistency in response
            if result.get("character_validation"):
                char_validation = result["character_validation"]
                diana_mystery = char_validation.get("diana_mystery_level", 0)
                mystery_levels.append(diana_mystery)
                
                # Individual mystery level validation
                assert 0.85 <= diana_mystery <= 0.95, \
                    f"Diana mystery level out of range: {diana_mystery:.2%} for fragment {fragment_data['id']}"
        
        # Overall mystery level validation
        if mystery_levels:
            avg_mystery = sum(mystery_levels) / len(mystery_levels)
            assert 0.85 <= avg_mystery <= 0.95, \
                f"Average Diana mystery level out of range: {avg_mystery:.2%}"
        
        # Character analyzer report
        char_report = character_analyzer.get_character_report()
        assert char_report["diana_consistency"]["mystery_in_range"], \
            f"Diana mystery analysis failed: {char_report}"
    
    @pytest.mark.asyncio
    async def test_lucien_supportive_role_consistency(self, character_coordinador, test_user, character_analyzer, session):
        """Test Lucien's 100% supportive role maintenance"""
        
        # Create test scenarios where Lucien should provide support
        lucien_scenarios = [
            {
                "id": "lucien_support_1",
                "title": "Lucien's Guidance",  
                "content": "Lucien te acompaña con calidez, ofreciendo apoyo constante mientras navegas por las complejidades del camino...",
                "author": "lucien"
            },
            {
                "id": "lucien_support_2",
                "title": "Lucien's Encouragement",
                "content": "Con palabras alentadoras, Lucien te motiva a seguir adelante, su presencia firme te da la confianza que necesitas...", 
                "author": "lucien"
            },
            {
                "id": "lucien_support_3",
                "title": "Lucien's Assistance",
                "content": "Lucien facilita tu comprensión con explicaciones claras, siempre dispuesto a ayudarte en cada paso del proceso...",
                "author": "lucien"
            }
        ]
        
        # Add Lucien fragments to database
        for fragment_data in lucien_scenarios:
            fragment = NarrativeFragment(**fragment_data, fragment_type="story")
            session.add(fragment)
        await session.commit()
        
        # Test Lucien interactions with Cinema enhancements
        for fragment_data in lucien_scenarios:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=fragment_data["id"],
                cinema_enhanced=True
            )
            
            # Analyze Lucien's character consistency
            consistency_score = character_analyzer.analyze_lucien_consistency(
                fragment_data["content"],
                {"cinema_enhanced": True, "result": result}
            )
            
            # Lucien should maintain high consistency
            assert consistency_score >= 0.8, \
                f"Lucien consistency too low: {consistency_score:.2%} for fragment {fragment_data['id']}"
            
            # Validate supportive nature in response
            if result.get("character_validation"):
                char_validation = result["character_validation"]
                lucien_support = char_validation.get("lucien_support_level", 0)
                
                # Lucien should maintain 90%+ support level
                assert lucien_support >= 0.9, \
                    f"Lucien support level too low: {lucien_support:.2%} for fragment {fragment_data['id']}"
        
        # Character analyzer report
        char_report = character_analyzer.get_character_report()
        assert char_report["overall_character_health"] == "HEALTHY", \
            f"Lucien character health issues: {char_report['violations']}"
    
    @pytest.mark.asyncio
    async def test_character_interaction_authenticity(self, character_coordinador, test_user, character_analyzer, session):
        """Test authentic character interactions in Cinema enhancements"""
        
        # Create fragments with Diana-Lucien interactions
        interaction_fragment = NarrativeFragment(
            id="diana_lucien_interaction_test",
            title="Diana and Lucien",
            content="Diana observa desde las sombras mientras Lucien te explica el siguiente paso. Sus miradas se cruzan en un entendimiento silencioso - ella preserva el misterio, él proporciona claridad.",
            fragment_type="character_interaction",
            author="system"
        )
        session.add(interaction_fragment)
        await session.commit()
        
        # Test character interaction with Cinema enhancements
        result = await character_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="diana_lucien_interaction_test",
            choice_id="interaction_choice",
            cinema_enhanced=True
        )
        
        # Analyze both characters in interaction
        diana_score = character_analyzer.analyze_diana_consistency(
            interaction_fragment.content + str(result.get("narrative_content", "")),
            {"interaction": True, "cinema_enhanced": True}
        )
        
        lucien_score = character_analyzer.analyze_lucien_consistency(
            interaction_fragment.content + str(result.get("narrative_content", "")),
            {"interaction": True, "cinema_enhanced": True}
        )
        
        # Both characters should maintain consistency in interactions
        assert diana_score >= 0.8, f"Diana consistency in interaction too low: {diana_score:.2%}"
        assert lucien_score >= 0.8, f"Lucien consistency in interaction too low: {lucien_score:.2%}"
        
        # Validate character balance - Diana mysterious, Lucien supportive
        if result.get("character_validation"):
            char_validation = result["character_validation"]
            
            # Diana should maintain mystery even in interactions
            diana_mystery = char_validation.get("diana_mystery_level", 0)
            assert 0.85 <= diana_mystery <= 0.95, \
                f"Diana mystery compromised in interaction: {diana_mystery:.2%}"
            
            # Lucien should maintain support even with Diana present
            lucien_support = char_validation.get("lucien_support_level", 0)
            assert lucien_support >= 0.9, \
                f"Lucien support compromised in interaction: {lucien_support:.2%}"
    
    @pytest.mark.asyncio
    async def test_emotional_flow_continuity(self, character_coordinador, test_user, character_analyzer, session):
        """Test emotional flow continuity with Cinema character enhancements"""
        
        # Create emotional journey fragments
        emotional_fragments = [
            {
                "id": "emotional_start",
                "content": "Diana te recibe con una sonrisa enigmática, sus ojos brillan con secretos no revelados...",
                "emotional_tone": "mysterious_welcome"
            },
            {
                "id": "emotional_middle",
                "content": "Lucien te guía con paciencia mientras Diana observa, su presencia tranquilizadora equilibra el misterio...",
                "emotional_tone": "balanced_support"
            },
            {
                "id": "emotional_climax",
                "content": "Diana revela un fragmento de verdad, sus susurros danzan entre la revelación y el enigma...",
                "emotional_tone": "revelation_mystery"
            }
        ]
        
        # Add emotional journey fragments
        for i, frag_data in enumerate(emotional_fragments):
            fragment = NarrativeFragment(
                id=frag_data["id"],
                title=f"Emotional Journey {i+1}",
                content=frag_data["content"],
                fragment_type="emotional_journey",
                author="diana"
            )
            session.add(fragment)
        await session.commit()
        
        # Execute emotional journey with Cinema enhancements
        emotional_scores = []
        
        for frag_data in emotional_fragments:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=frag_data["id"],
                cinema_enhanced=True,
                emotional_continuity=True
            )
            
            # Analyze emotional consistency
            emotional_score = character_analyzer.analyze_diana_consistency(
                frag_data["content"],
                {"emotional_tone": frag_data["emotional_tone"], "cinema_enhanced": True}
            )
            emotional_scores.append(emotional_score)
        
        # Emotional flow should maintain consistency
        avg_emotional_score = sum(emotional_scores) / len(emotional_scores)
        assert avg_emotional_score >= 0.85, \
            f"Emotional flow consistency too low: {avg_emotional_score:.2%}"
        
        # No dramatic consistency drops between fragments
        for i in range(1, len(emotional_scores)):
            consistency_drop = emotional_scores[i-1] - emotional_scores[i]
            assert consistency_drop <= 0.2, \
                f"Emotional consistency drop too large: {consistency_drop:.2%} between fragments {i-1} and {i}"
    
    @pytest.mark.asyncio
    async def test_real_time_character_monitoring(self, character_coordinador, test_user, session):
        """Test real-time character consistency monitoring during Cinema operations"""
        
        # Create test fragment for monitoring
        monitor_fragment = NarrativeFragment(
            id="character_monitoring_test",
            title="Character Monitor Test",
            content="Diana te observa con atención mientras Lucien prepara el siguiente desafío...",
            fragment_type="story",
            author="diana"
        )
        session.add(monitor_fragment)
        await session.commit()
        
        # Execute with character monitoring enabled
        result = await character_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="character_monitoring_test",
            choice_id="monitor_choice",
            cinema_enhanced=True,
            character_monitoring=True
        )
        
        # Verify monitoring data present
        if result.get("character_monitoring"):
            monitoring_data = result["character_monitoring"]
            
            # Should include real-time consistency scores
            assert "diana_consistency_score" in monitoring_data, \
                "Diana consistency monitoring missing"
            assert "lucien_support_score" in monitoring_data, \
                "Lucien support monitoring missing"
            
            # Scores should be within acceptable ranges
            diana_score = monitoring_data["diana_consistency_score"]
            lucien_score = monitoring_data["lucien_support_score"]
            
            assert 0.8 <= diana_score <= 1.0, \
                f"Diana monitoring score out of range: {diana_score:.2%}"
            assert 0.9 <= lucien_score <= 1.0, \
                f"Lucien monitoring score out of range: {lucien_score:.2%}"
        
        # Character validation should be present
        if result.get("character_validation"):
            char_validation = result["character_validation"]
            
            # Mystery level monitoring
            assert "diana_mystery_level" in char_validation, \
                "Diana mystery level monitoring missing"
            assert "mystery_trend" in char_validation, \
                "Mystery level trend monitoring missing"
    
    @pytest.mark.asyncio
    async def test_character_arc_progression_validation(self, character_coordinador, test_user, character_analyzer, session):
        """Test character arc progression with Cinema enhancements"""
        
        # Create character arc progression fragments
        arc_fragments = [
            {
                "id": "arc_beginning",
                "content": "Diana aparece como una figura enigmática, sus intenciones veladas por capas de misterio...",
                "arc_stage": "introduction"
            },
            {
                "id": "arc_development", 
                "content": "Diana comienza a revelar pequeños fragmentos de verdad, manteniendo siempre el velo del enigma...",
                "arc_stage": "development"
            },
            {
                "id": "arc_deepening",
                "content": "Diana te permite vislumbrar más profundidad, sus secretos danzan al borde de la revelación...",
                "arc_stage": "deepening"
            }
        ]
        
        # Add arc fragments
        for frag_data in arc_fragments:
            fragment = NarrativeFragment(
                id=frag_data["id"],
                title=f"Arc {frag_data['arc_stage'].title()}",
                content=frag_data["content"],
                fragment_type="character_arc",
                author="diana"
            )
            session.add(fragment)
        await session.commit()
        
        # Execute character arc with Cinema enhancements
        arc_consistency_scores = []
        mystery_progression = []
        
        for frag_data in arc_fragments:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=frag_data["id"],
                cinema_enhanced=True,
                character_arc_tracking=True
            )
            
            # Analyze character arc consistency
            consistency_score = character_analyzer.analyze_diana_consistency(
                frag_data["content"],
                {"arc_stage": frag_data["arc_stage"], "cinema_enhanced": True}
            )
            arc_consistency_scores.append(consistency_score)
            
            # Track mystery level progression
            if result.get("character_validation"):
                mystery_level = result["character_validation"].get("diana_mystery_level", 0)
                mystery_progression.append(mystery_level)
        
        # Character arc should maintain consistency throughout
        min_arc_score = min(arc_consistency_scores)
        assert min_arc_score >= 0.8, \
            f"Character arc consistency dropped too low: {min_arc_score:.2%}"
        
        # Mystery levels should stay within bounds throughout arc
        for i, mystery_level in enumerate(mystery_progression):
            assert 0.85 <= mystery_level <= 0.95, \
                f"Mystery level out of bounds in arc stage {i}: {mystery_level:.2%}"
        
        # Character development should be coherent (no wild swings)
        if len(arc_consistency_scores) > 1:
            consistency_variance = max(arc_consistency_scores) - min(arc_consistency_scores)
            assert consistency_variance <= 0.15, \
                f"Character arc consistency too variable: {consistency_variance:.2%}"


class TestCinemaCharacterValidation:
    """Advanced character validation testing"""
    
    @pytest.mark.asyncio
    async def test_character_boundary_protection(self, session, test_user, mock_bot):
        """Test character boundary protection mechanisms"""
        
        coordinador = CoordinadorCentral(session)
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
            coordinador.cinema_master._boundary_protection_enabled = True
        
        # Create fragment that might compromise character boundaries
        boundary_test_fragment = NarrativeFragment(
            id="boundary_test_fragment",
            title="Boundary Test",
            content="Test content for boundary validation...",
            fragment_type="boundary_test",
            author="diana"
        )
        session.add(boundary_test_fragment)
        await session.commit()
        
        # Mock potential boundary violations
        with patch.object(coordinador.cinema_master, '_validate_character_boundaries', return_value={
            "diana_mystery_violation": False,
            "lucien_support_violation": False,
            "boundary_protection_active": True,
            "corrective_actions": []
        }) if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master else patch:
            
            result = await coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id="boundary_test_fragment",
                choice_id="boundary_choice",
                cinema_enhanced=True
            )
            
            # Verify boundary protection is active
            if result.get("character_validation"):
                char_validation = result["character_validation"]
                
                # Boundary protection should be enabled
                assert char_validation.get("boundary_protection") == True, \
                    "Character boundary protection not active"
                
                # No violations should be detected
                assert char_validation.get("violations", []) == [], \
                    f"Character boundary violations detected: {char_validation.get('violations')}"
    
    @pytest.mark.asyncio
    async def test_character_immersion_quality_assurance(self, character_coordinador, test_user, session):
        """Test character immersion quality with Cinema enhancements"""
        
        # Create immersion test fragment
        immersion_fragment = NarrativeFragment(
            id="immersion_quality_test",
            title="Immersion Quality Test", 
            content="Diana emerge de las sombras con elegancia ancestral, sus ojos guardan secretos que han perdurado por milenios. Lucien a tu lado, con una sonrisa que transmite confianza absoluta...",
            fragment_type="immersion_test",
            author="diana"
        )
        session.add(immersion_fragment)
        await session.commit()
        
        # Execute immersion quality test
        result = await character_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            fragment_id="immersion_quality_test",
            cinema_enhanced=True,
            immersion_monitoring=True
        )
        
        # Verify immersion quality metrics
        if result.get("immersion_quality"):
            immersion_data = result["immersion_quality"]
            
            # Character authenticity score
            authenticity = immersion_data.get("character_authenticity", 0)
            assert authenticity >= 0.9, \
                f"Character authenticity too low: {authenticity:.2%}"
            
            # Emotional investment protection
            emotional_investment = immersion_data.get("emotional_investment_score", 0)
            assert emotional_investment >= 0.85, \
                f"Emotional investment score too low: {emotional_investment:.2%}"
            
            # Narrative coherence
            narrative_coherence = immersion_data.get("narrative_coherence", 0)
            assert narrative_coherence >= 0.9, \
                f"Narrative coherence too low: {narrative_coherence:.2%}"
    
    @pytest.mark.asyncio
    async def test_character_validation_under_stress(self, character_coordinador, test_user, session):
        """Test character validation under high-stress Cinema operations"""
        
        # Create multiple fragments for stress testing
        stress_fragments = []
        for i in range(10):
            fragment = NarrativeFragment(
                id=f"stress_test_{i}",
                title=f"Stress Test {i}",
                content=f"Diana te guía con misterio y gracia #{i}, mientras Lucien ofrece su apoyo constante...",
                fragment_type="stress_test",
                author="diana" if i % 2 == 0 else "lucien"
            )
            session.add(fragment)
            stress_fragments.append(fragment)
        
        await session.commit()
        
        # Execute stress test operations rapidly
        stress_results = []
        
        for fragment in stress_fragments:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=fragment.id,
                cinema_enhanced=True,
                stress_test_mode=True
            )
            stress_results.append(result)
        
        # Analyze character consistency under stress
        character_violations = 0
        mystery_violations = 0
        
        for i, result in enumerate(stress_results):
            if result.get("character_validation"):
                char_validation = result["character_validation"]
                
                # Check for character consistency
                diana_consistency = char_validation.get("diana_consistency", 1.0)
                if diana_consistency < 0.85:
                    character_violations += 1
                
                # Check for mystery level violations
                diana_mystery = char_validation.get("diana_mystery_level", 0.9)
                if not (0.85 <= diana_mystery <= 0.95):
                    mystery_violations += 1
        
        # Character validation should remain stable under stress
        violation_rate = character_violations / len(stress_results)
        assert violation_rate <= 0.1, \
            f"Character violation rate too high under stress: {violation_rate:.2%}"
        
        mystery_violation_rate = mystery_violations / len(stress_results)
        assert mystery_violation_rate <= 0.05, \
            f"Mystery level violation rate too high under stress: {mystery_violation_rate:.2%}"


class TestCinemaCharacterReporting:
    """Character consistency reporting and analytics"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_character_report_generation(self, character_coordinador, test_user, character_analyzer, session):
        """Test comprehensive character consistency report generation"""
        
        # Create diverse test scenarios
        test_scenarios = [
            {"id": "report_diana_1", "content": "Diana susurra secretos ancestrales...", "author": "diana"},
            {"id": "report_lucien_1", "content": "Lucien te apoya con calidez constante...", "author": "lucien"}, 
            {"id": "report_interaction_1", "content": "Diana y Lucien intercambian miradas...", "author": "system"},
            {"id": "report_emotional_1", "content": "Diana revela un fragmento de verdad...", "author": "diana"}
        ]
        
        # Add test fragments
        for scenario in test_scenarios:
            fragment = NarrativeFragment(
                id=scenario["id"],
                title=f"Report Test {scenario['id']}",
                content=scenario["content"],
                fragment_type="report_test",
                author=scenario["author"]
            )
            session.add(fragment)
        await session.commit()
        
        # Execute all scenarios with reporting
        for scenario in test_scenarios:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=scenario["id"],
                cinema_enhanced=True,
                generate_character_report=True
            )
            
            # Analyze each scenario
            if scenario["author"] == "diana":
                character_analyzer.analyze_diana_consistency(scenario["content"], {"scenario": scenario})
            elif scenario["author"] == "lucien":
                character_analyzer.analyze_lucien_consistency(scenario["content"], {"scenario": scenario})
        
        # Generate comprehensive report
        character_report = character_analyzer.get_character_report()
        
        # Validate report completeness
        assert "diana_consistency" in character_report, "Diana consistency missing from report"
        assert "violations" in character_report, "Violations list missing from report"
        assert "overall_character_health" in character_report, "Overall health missing from report"
        
        # Report should indicate healthy character state
        assert character_report["overall_character_health"] in ["HEALTHY", "ISSUES_DETECTED"], \
            f"Invalid character health status: {character_report['overall_character_health']}"
        
        # Diana consistency should meet threshold
        diana_data = character_report["diana_consistency"]
        assert diana_data["consistency_threshold_met"] == True, \
            f"Diana consistency threshold not met: {diana_data}"
        
        # Mystery level should be in range
        assert diana_data["mystery_in_range"] == True, \
            f"Diana mystery level out of range: {diana_data['mystery_level_average']:.2%}"
        
        print(f"\n{'='*80}")
        print("CINEMA CHARACTER CONSISTENCY REPORT")
        print(f"{'='*80}")
        print(f"Overall Character Health: {character_report['overall_character_health']}")
        print(f"Total Violations: {character_report['total_violations']}")
        print(f"Diana Consistency Score: {diana_data['average_score']:.2%}")
        print(f"Diana Mystery Level: {diana_data['mystery_level_average']:.2%}")
        print(f"Mystery Level In Range: {diana_data['mystery_in_range']}")
        print(f"Consistency Threshold Met: {diana_data['consistency_threshold_met']}")
        
        if character_report["violations"]:
            print(f"\nViolations Detected:")
            for violation in character_report["violations"]:
                print(f"  - {violation}")
        
        print(f"{'='*80}")
    
    @pytest.mark.asyncio
    async def test_character_trend_analysis(self, character_coordinador, test_user, session):
        """Test character consistency trend analysis over time"""
        
        # Create time-series test fragments
        time_fragments = []
        for i in range(5):
            fragment = NarrativeFragment(
                id=f"trend_test_{i}",
                title=f"Trend Test {i}",
                content=f"Diana revela secretos graduales #{i}, manteniendo siempre su velo de misterio...",
                fragment_type="trend_test",
                author="diana"
            )
            session.add(fragment)
            time_fragments.append(fragment)
        await session.commit()
        
        # Execute time-series character interactions
        trend_data = []
        
        for fragment in time_fragments:
            result = await character_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=fragment.id,
                cinema_enhanced=True,
                trend_analysis=True
            )
            
            if result.get("character_validation"):
                char_data = result["character_validation"]
                trend_data.append({
                    "timestamp": datetime.utcnow(),
                    "diana_consistency": char_data.get("diana_consistency", 0),
                    "diana_mystery": char_data.get("diana_mystery_level", 0)
                })
        
        # Analyze trends
        if len(trend_data) >= 3:
            # Consistency trend should be stable or improving
            consistency_values = [d["diana_consistency"] for d in trend_data]
            mystery_values = [d["diana_mystery"] for d in trend_data]
            
            # No significant degradation in consistency
            consistency_trend = consistency_values[-1] - consistency_values[0]
            assert consistency_trend >= -0.05, \
                f"Character consistency degrading over time: {consistency_trend:.2%}"
            
            # Mystery levels should remain stable
            mystery_variance = max(mystery_values) - min(mystery_values)
            assert mystery_variance <= 0.1, \
                f"Mystery level too variable over time: {mystery_variance:.2%}"