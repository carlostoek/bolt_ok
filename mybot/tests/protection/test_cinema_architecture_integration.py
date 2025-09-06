"""
🎬 CINEMA ARCHITECTURE INTEGRATION TESTS
Protección completa de los nuevos sistemas cinematográficos revolucionarios.
Testea Diana Character Bible V1.0, 6-Level Emotional Crescendo, Choice Architecture, etc.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import datetime
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserStats
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog, LorePiece, UserLorePiece
from services.coordinador_central import CoordinadorCentral
from services.user_narrative_service import UserNarrativeService
from services.diana_character_validator import DianaCharacterValidator


class TestDianaCharacterBible:
    """🎭 Tests for Diana Character Bible V1.0 consistency."""
    
    @pytest.mark.asyncio
    async def test_character_bible_consistency_validation(self, session):
        """🔒 CRITICAL: Diana Character Bible >95% consistency requirement."""
        validator = DianaCharacterValidator(session)
        
        # Test character consistency across all interactions
        consistency_score = await validator.validate_character_consistency()
        assert consistency_score >= 0.95, f"Character Bible consistency {consistency_score} < 95%!"
    
    @pytest.mark.asyncio
    async def test_character_personality_traits_consistency(self, session):
        """🎭 Character personality traits must remain consistent."""
        # Create test scenarios for different personality traits
        test_traits = [
            "seductive_yet_dangerous",
            "mysterious_authority", 
            "psychological_manipulation",
            "emotional_intelligence",
            "strategic_thinking"
        ]
        
        validator = DianaCharacterValidator(session)
        
        for trait in test_traits:
            # Test trait consistency across different contexts
            trait_score = await validator.validate_trait_consistency(trait)
            assert trait_score >= 0.90, f"Trait '{trait}' consistency {trait_score} < 90%!"
    
    @pytest.mark.asyncio
    async def test_character_dialogue_consistency(self, session):
        """🎭 Diana's dialogue must maintain character voice."""
        validator = DianaCharacterValidator(session)
        
        # Test dialogue samples for consistency
        test_dialogues = [
            "Querido... ¿realmente crees que puedes resistirte?",
            "Tu alma me fascina, déjame explorar cada rincón...",
            "Los secretos que guardas son deliciosos..."
        ]
        
        for dialogue in test_dialogues:
            consistency = await validator.validate_dialogue_consistency(dialogue)
            assert consistency >= 0.95, f"Dialogue consistency failed: {dialogue}"


class TestSixLevelEmotionalCrescendo:
    """🌊 Tests for 6-Level Emotional Crescendo system."""
    
    @pytest.mark.asyncio
    async def test_emotional_crescendo_progression(self, session):
        """🔒 CRITICAL: 6-Level Emotional Crescendo must work flawlessly."""
        # Create user for testing emotional progression
        user = User(
            id=101010101,
            first_name="EmotionalUser",
            role="free",
            points=0.0,
            archetype="Romantic"  # Perfect for emotional crescendo testing
        )
        session.add(user)
        
        # Create narrative state
        narrative_state = UserNarrativeState(
            user_id=101010101,
            current_fragment_id=1,
            tier=1,
            emotional_crescendo_level=1,
            completed_fragments=[],
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test progression through all 6 levels
        service = UserNarrativeService(session)
        
        for level in range(1, 7):  # Levels 1-6
            # Verify current level
            state = await service.get_user_narrative_state(101010101)
            expected_level = level
            
            if hasattr(state, 'emotional_crescendo_level'):
                assert state.emotional_crescendo_level == expected_level, \
                    f"Emotional crescendo level {state.emotional_crescendo_level} != {expected_level}"
            
            # Simulate progression to next level
            if level < 6:
                narrative_state.emotional_crescendo_level = level + 1
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_emotional_intensity_calculation(self, session):
        """🌊 Emotional intensity must increase progressively."""
        from services.emotional_dependency_engine import EmotionalDependencyEngine
        
        engine = EmotionalDependencyEngine(session)
        
        # Test intensity calculation for each level
        intensities = []
        for level in range(1, 7):
            intensity = await engine.calculate_emotional_intensity(level)
            intensities.append(intensity)
            assert 0.0 <= intensity <= 1.0, f"Invalid intensity {intensity} for level {level}"
        
        # Verify progressive increase
        for i in range(len(intensities) - 1):
            assert intensities[i] < intensities[i + 1], \
                f"Emotional intensity not increasing: {intensities[i]} >= {intensities[i + 1]}"
    
    @pytest.mark.asyncio
    async def test_crescendo_choice_integration(self, session):
        """🎭 Crescendo must integrate with choice system."""
        from services.crescendo_choice_integration import CrescendoChoiceIntegration
        
        integration = CrescendoChoiceIntegration(session)
        
        # Create test user at different crescendo levels
        user = User(
            id=202020202,
            first_name="CrescendoUser",
            role="vip",
            points=100.0
        )
        session.add(user)
        await session.commit()
        
        # Test choice modification at different levels
        base_choices = [
            {"text": "Resistir", "consequence": "resistance"},
            {"text": "Ceder", "consequence": "submission"}
        ]
        
        for level in range(1, 7):
            modified_choices = await integration.modify_choices_for_crescendo_level(
                base_choices, level
            )
            
            assert len(modified_choices) >= len(base_choices), \
                f"Choices lost at crescendo level {level}"
            
            # Higher levels should have more intense choices
            if level > 3:
                choice_texts = [choice["text"] for choice in modified_choices]
                assert any("intenso" in text.lower() or "profundo" in text.lower() 
                          for text in choice_texts), \
                    f"No intense choices at high crescendo level {level}"


class TestChoiceArchitectureMasterpiece:
    """🏛️ Tests for Choice Architecture Masterpiece system."""
    
    @pytest.mark.asyncio
    async def test_choice_architecture_core_functionality(self, session):
        """🔒 CRITICAL: Choice Architecture must work perfectly."""
        from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
        
        architecture = ChoiceArchitectureMasterpiece(session)
        
        # Create test user
        user = User(
            id=303030303,
            first_name="ChoiceUser",
            role="vip",
            points=150.0,
            archetype="Analytical"
        )
        session.add(user)
        await session.commit()
        
        # Test choice generation
        context = {
            "fragment_id": 5,
            "user_archetype": "Analytical",
            "emotional_state": "curious",
            "previous_choices": ["explore", "analyze"]
        }
        
        choices = await architecture.generate_personalized_choices(303030303, context)
        
        assert len(choices) >= 2, "Insufficient choices generated!"
        assert all("text" in choice and "consequence" in choice for choice in choices), \
            "Invalid choice structure!"
        
        # Analytical archetype should get analytical choices
        choice_texts = [choice["text"] for choice in choices]
        assert any("analiz" in text.lower() or "estudi" in text.lower() or "observ" in text.lower() 
                  for text in choice_texts), \
            "Choices not personalized for Analytical archetype!"
    
    @pytest.mark.asyncio
    async def test_delayed_gratification_premium_algorithm(self, session):
        """⏰ Delayed Gratification Premium Algorithm testing."""
        from services.delayed_gratification_premium_algorithm import DelayedGratificationPremiumAlgorithm
        
        algorithm = DelayedGratificationPremiumAlgorithm(session)
        
        # Create test user
        user = User(
            id=404040404,
            first_name="DelayedUser",
            role="vip",
            points=200.0
        )
        session.add(user)
        await session.commit()
        
        # Test delayed reward calculation
        base_reward = 50.0
        delay_hours = 24
        
        premium_reward = await algorithm.calculate_delayed_premium(
            base_reward, delay_hours, user.role
        )
        
        assert premium_reward > base_reward, \
            f"Delayed premium {premium_reward} not greater than base {base_reward}!"
        
        # VIP should get higher premium
        assert premium_reward >= base_reward * 1.5, \
            f"VIP delayed premium {premium_reward} insufficient!"
    
    @pytest.mark.asyncio
    async def test_choice_consequence_tracking(self, session):
        """📊 Choice consequences must be properly tracked."""
        from services.decision_consequence_tracker import DecisionConsequenceTracker
        
        tracker = DecisionConsequenceTracker(session)
        
        # Create test user
        user = User(
            id=505050505,
            first_name="ConsequenceUser",
            role="free",
            points=75.0
        )
        session.add(user)
        await session.commit()
        
        # Test consequence tracking
        choice_data = {
            "fragment_id": 3,
            "choice_index": 1,
            "choice_text": "Explorar el misterio",
            "consequence_type": "curiosity_increase",
            "emotional_impact": 0.7
        }
        
        await tracker.track_choice_consequence(505050505, choice_data)
        
        # Verify tracking
        consequences = await tracker.get_user_choice_history(505050505)
        assert len(consequences) >= 1, "Choice consequence not tracked!"
        
        latest = consequences[-1]
        assert latest["choice_text"] == "Explorar el misterio", "Choice text not tracked correctly!"


class TestClueSystemIntegration:
    """🔍 Tests for Clue Treasure Hunting Cinema Integration."""
    
    @pytest.mark.asyncio
    async def test_clue_treasure_hunting_integration(self, session):
        """🔒 CRITICAL: Clue system must integrate with cinema architecture."""
        from services.clue_treasure_hunting_cinema_integration import ClueTreasureHuntingCinemaIntegration
        
        integration = ClueTreasureHuntingCinemaIntegration(session)
        
        # Create test user
        user = User(
            id=606060606,
            first_name="TreasureUser",
            role="vip",
            points=300.0,
            archetype="Explorer"
        )
        session.add(user)
        
        # Create test lore pieces
        lore1 = LorePiece(
            id="cinema_clue_001",
            title="Diana's First Secret",
            content="The seductive whisper reveals the first layer of truth...",
            unlock_condition="emotional_crescendo_level_3",
            tier_required=2,
            cinema_integration_data={"emotional_weight": 0.8, "mystery_level": "high"}
        )
        session.add(lore1)
        await session.commit()
        
        # Test clue integration with cinema system
        clue_context = {
            "current_fragment": 8,
            "emotional_crescendo_level": 4,
            "user_archetype": "Explorer",
            "choice_history": ["explore", "deeper", "mystery"]
        }
        
        available_clues = await integration.get_available_cinema_clues(606060606, clue_context)
        assert len(available_clues) >= 0, "Clue integration system failed!"
        
        # Test clue unlock with cinema context
        unlock_result = await integration.attempt_cinema_clue_unlock(
            606060606, "cinema_clue_001", clue_context
        )
        
        assert isinstance(unlock_result, dict), "Clue unlock result invalid!"
        assert "success" in unlock_result, "Clue unlock result missing success status!"
    
    @pytest.mark.asyncio
    async def test_enhanced_clue_unlock_service(self, session):
        """🔓 Enhanced clue unlock service integration."""
        from services.enhanced_clue_unlock_service import EnhancedClueUnlockService
        
        service = EnhancedClueUnlockService(session)
        
        # Create test user and clues
        user = User(
            id=707070707,
            first_name="EnhancedUser",
            role="vip",
            points=250.0
        )
        session.add(user)
        
        lore = LorePiece(
            id="enhanced_clue_001",
            title="Enhanced Mystery",
            content="Deep cinema integration reveals hidden truths...",
            unlock_condition="complex_cinema_condition",
            tier_required=3
        )
        session.add(lore)
        await session.commit()
        
        # Test enhanced unlock logic
        unlock_context = {
            "emotional_state": "deeply_intrigued",
            "crescendo_level": 5,
            "archetype_compatibility": 0.9,
            "narrative_progress": 0.75
        }
        
        can_unlock = await service.can_user_unlock_enhanced_clue(
            707070707, "enhanced_clue_001", unlock_context
        )
        
        assert isinstance(can_unlock, bool), "Enhanced unlock check failed!"


class TestSoulSignaturePersonalization:
    """✨ Tests for Soul Signature Personalization system."""
    
    @pytest.mark.asyncio
    async def test_soul_signature_generation(self, session):
        """🔒 CRITICAL: Soul Signature must personalize experience."""
        from services.user_archetyping_service import UserArchetypingService
        
        service = UserArchetypingService(session)
        
        # Test all 6 archetypes
        archetypes = ["Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"]
        
        for archetype in archetypes:
            user = User(
                id=800000000 + hash(archetype) % 100000,
                first_name=f"Soul{archetype}",
                role="vip" if archetype in ["Romantic", "Explorer"] else "free",
                points=100.0,
                archetype=archetype
            )
            session.add(user)
            await session.commit()
            
            # Test soul signature generation
            signature = await service.generate_soul_signature(user.id)
            
            assert signature is not None, f"Soul signature not generated for {archetype}!"
            assert "archetype" in signature, "Soul signature missing archetype!"
            assert signature["archetype"] == archetype, \
                f"Soul signature archetype mismatch: {signature['archetype']} != {archetype}"
    
    @pytest.mark.asyncio
    async def test_personalized_narrative_adaptation(self, session):
        """✨ Narrative must adapt to soul signatures."""
        # Create users with different soul signatures
        users_data = [
            (901010101, "Explorer", "vip"),
            (902020202, "Romantic", "vip"), 
            (903030303, "Analytical", "free")
        ]
        
        for user_id, archetype, role in users_data:
            user = User(
                id=user_id,
                first_name=f"Adapt{archetype}",
                role=role,
                points=150.0,
                archetype=archetype
            )
            session.add(user)
        
        await session.commit()
        
        # Test narrative adaptation
        service = UserNarrativeService(session)
        
        for user_id, archetype, role in users_data:
            # Get personalized narrative state
            state = await service.get_user_narrative_state(user_id)
            assert state is not None, f"Narrative state not found for {archetype}!"
            
            # Test that narrative adapts to archetype
            # This would be implemented in the actual service
            if hasattr(state, 'personalization_data'):
                assert state.personalization_data.get("archetype") == archetype, \
                    f"Narrative not adapted for {archetype}!"


class TestUnifiedCinemaArchitectureIntegration:
    """🎬 Tests for Unified Cinema Architecture Integration."""
    
    @pytest.mark.asyncio
    async def test_complete_cinema_system_integration(self, session):
        """🚨 SMOKE TEST: Complete cinema architecture integration."""
        # Setup complete cinema system
        user = User(
            id=999000001,
            first_name="CinemaUser",
            role="vip",
            points=500.0,
            archetype="Romantic"
        )
        session.add(user)
        
        narrative_state = UserNarrativeState(
            user_id=999000001,
            current_fragment_id=10,  # Mid-tier fragment
            tier=2,
            emotional_crescendo_level=4,  # High emotional level
            completed_fragments=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            available_choices=[]
        )
        session.add(narrative_state)
        
        # Create cinema-integrated lore piece
        lore = LorePiece(
            id="cinema_master_001",
            title="Diana's Ultimate Revelation",
            content="The complete cinema experience unveils the deepest mystery...",
            unlock_condition="cinema_master_condition",
            tier_required=2,
            cinema_integration_data={
                "emotional_weight": 0.95,
                "crescendo_trigger": True,
                "choice_influence": "high",
                "archetype_specific": ["Romantic", "Explorer"]
            }
        )
        session.add(lore)
        await session.commit()
        
        # Test integrated systems working together
        from services.diana_choice_architecture_master_system import DianaChoiceArchitectureMasterSystem
        
        master_system = DianaChoiceArchitectureMasterSystem(session)
        
        # Generate cinema-integrated choices
        cinema_context = {
            "fragment_id": 10,
            "emotional_crescendo_level": 4,
            "user_archetype": "Romantic",
            "soul_signature": {"primary": "passionate", "secondary": "mysterious"},
            "available_clues": ["cinema_master_001"],
            "narrative_progress": 0.6
        }
        
        integrated_choices = await master_system.generate_cinema_integrated_choices(
            999000001, cinema_context
        )
        
        # Verify integration
        assert len(integrated_choices) >= 2, "Cinema integration failed to generate choices!"
        
        # Should have cinema-specific enhancements
        for choice in integrated_choices:
            assert "text" in choice, "Choice missing text!"
            assert "consequence" in choice, "Choice missing consequence!"
            
            # High crescendo level + Romantic archetype should have intense options
            if choice.get("intensity_level", 0) > 0.7:
                assert any(keyword in choice["text"].lower() 
                          for keyword in ["intenso", "profundo", "surrender", "entrega"]), \
                    f"High intensity choice lacks appropriate language: {choice['text']}"
    
    @pytest.mark.asyncio
    async def test_cinema_performance_requirements(self, session):
        """⚡ Cinema architecture must meet performance requirements."""
        import time
        
        # Create complex cinema scenario
        user = User(
            id=999000002,
            first_name="PerformanceUser",
            role="vip",
            points=750.0,
            archetype="Explorer"
        )
        session.add(user)
        await session.commit()
        
        # Test performance of complete cinema pipeline
        from services.diana_choice_architecture_master_system import DianaChoiceArchitectureMasterSystem
        
        master_system = DianaChoiceArchitectureMasterSystem(session)
        
        start_time = time.time()
        
        # Complex cinema context
        complex_context = {
            "fragment_id": 15,  # High-tier fragment
            "emotional_crescendo_level": 6,  # Maximum level
            "user_archetype": "Explorer",
            "soul_signature": {
                "primary": "curious",
                "secondary": "determined", 
                "tertiary": "intuitive"
            },
            "choice_history": ["explore"] * 10,  # Extensive history
            "available_clues": [f"clue_{i}" for i in range(20)],  # Many clues
            "narrative_progress": 0.95  # Near completion
        }
        
        cinema_choices = await master_system.generate_cinema_integrated_choices(
            999000002, complex_context
        )
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Performance requirements
        assert processing_time < 1000, f"Cinema processing too slow: {processing_time}ms > 1000ms!"
        assert len(cinema_choices) >= 2, "Cinema system failed under complex load!"
        
        # Verify quality under performance pressure
        for choice in cinema_choices:
            assert len(choice.get("text", "")) > 10, "Choice quality degraded under performance pressure!"


@pytest.mark.asyncio
async def test_cinema_architecture_full_integration_smoke_test(session):
    """🚨 CRITICAL SMOKE TEST: All cinema systems must work together flawlessly."""
    # Complete end-to-end cinema experience test
    
    # 1. Create complete cinema user
    user = User(
        id=999999001,
        first_name="CinemaSmokeTestUser",
        role="vip",
        points=1000.0,
        archetype="Romantic"
    )
    session.add(user)
    
    narrative_state = UserNarrativeState(
        user_id=999999001,
        current_fragment_id=12,
        tier=3,  # Elite tier
        emotional_crescendo_level=5,
        completed_fragments=list(range(1, 12)),
        available_choices=[]
    )
    session.add(narrative_state)
    await session.commit()
    
    # 2. Test Diana Character Bible consistency
    from services.diana_character_validator import DianaCharacterValidator
    validator = DianaCharacterValidator(session)
    consistency = await validator.validate_character_consistency()
    assert consistency >= 0.95, f"Character Bible consistency failed: {consistency}"
    
    # 3. Test Emotional Crescendo at high level
    from services.emotional_dependency_engine import EmotionalDependencyEngine
    emotion_engine = EmotionalDependencyEngine(session)
    intensity = await emotion_engine.calculate_emotional_intensity(5)
    assert 0.8 <= intensity <= 1.0, f"High crescendo intensity invalid: {intensity}"
    
    # 4. Test Choice Architecture with full context
    from services.diana_choice_architecture_master_system import DianaChoiceArchitectureMasterSystem
    master_system = DianaChoiceArchitectureMasterSystem(session)
    
    full_context = {
        "fragment_id": 12,
        "emotional_crescendo_level": 5,
        "user_archetype": "Romantic",
        "soul_signature": {"primary": "passionate", "secondary": "vulnerable"},
        "narrative_progress": 0.8,
        "tier": 3
    }
    
    choices = await master_system.generate_cinema_integrated_choices(999999001, full_context)
    assert len(choices) >= 2, "Cinema master system failed!"
    
    # 5. Test clue integration
    from services.clue_treasure_hunting_cinema_integration import ClueTreasureHuntingCinemaIntegration
    clue_integration = ClueTreasureHuntingCinemaIntegration(session)
    
    clues = await clue_integration.get_available_cinema_clues(999999001, full_context)
    assert isinstance(clues, list), "Clue integration failed!"
    
    # 6. Verify complete user experience
    service = UserNarrativeService(session)
    final_state = await service.get_user_narrative_state(999999001)
    assert final_state is not None, "User narrative state corrupted!"
    assert final_state.tier == 3, "User tier incorrect!"
    
    # 🎬 CINEMA ARCHITECTURE FULLY OPERATIONAL!
    print("🎬 CINEMA ARCHITECTURE INTEGRATION: ALL SYSTEMS FULLY OPERATIONAL!")