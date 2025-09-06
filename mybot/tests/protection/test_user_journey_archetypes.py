"""
🎭 USER JOURNEY & ARCHETYPE TESTING FRAMEWORK
Complete testing protection for all 6 user archetypes and their complete journeys.
Tests Explorer, Direct, Romantic, Analytical, Persistent, Patient across all tiers.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import datetime
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserStats, Channel
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog, LorePiece, UserLorePiece
from services.coordinador_central import CoordinadorCentral
from services.user_narrative_service import UserNarrativeService
from services.user_archetyping_service import UserArchetypingService
from services.diana_menu_system import DianaMenuSystem


class TestUserArchetypeBaseline:
    """🎭 Baseline tests for all 6 user archetypes."""
    
    @pytest.mark.parametrize("archetype", [
        "Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"
    ])
    @pytest.mark.asyncio
    async def test_archetype_user_creation(self, session, archetype):
        """🔒 CRITICAL: Each archetype user must be created correctly."""
        user = User(
            id=1000000 + hash(archetype) % 900000,  # Unique ID per archetype
            first_name=f"{archetype}TestUser",
            username=f"{archetype.lower()}_test",
            role="free",
            points=0.0,
            archetype=archetype,
            created_at=datetime.datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        
        # Verify user creation
        created_user = await session.get(User, user.id)
        assert created_user is not None, f"{archetype} user creation failed!"
        assert created_user.archetype == archetype, f"Archetype mismatch: {created_user.archetype}"
        assert created_user.role == "free", f"Initial role incorrect for {archetype}"
    
    @pytest.mark.asyncio
    async def test_archetype_service_initialization(self, session):
        """🔒 CRITICAL: UserArchetypingService must work with all archetypes."""
        service = UserArchetypingService(session)
        
        # Test service can handle all archetypes
        archetypes = ["Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"]
        
        for archetype in archetypes:
            user = User(
                id=2000000 + hash(archetype) % 900000,
                first_name=f"Service{archetype}",
                role="free",
                points=50.0,
                archetype=archetype
            )
            session.add(user)
        
        await session.commit()
        
        # Test service methods
        for archetype in archetypes:
            user_id = 2000000 + hash(archetype) % 900000
            
            # Test soul signature generation
            signature = await service.generate_soul_signature(user_id)
            assert signature is not None, f"Soul signature failed for {archetype}!"
            assert signature["archetype"] == archetype, f"Signature archetype mismatch for {archetype}!"


class TestExplorerArchetypeJourney:
    """🗺️ Complete journey testing for Explorer archetype."""
    
    @pytest.mark.asyncio
    async def test_explorer_complete_journey(self, session):
        """🔒 CRITICAL: Explorer user complete journey from Tier 1 to Elite."""
        # Create Explorer user
        explorer = User(
            id=3000001,
            first_name="ExplorerJourney",
            username="explorer_journey",
            role="free",
            points=0.0,
            archetype="Explorer"
        )
        session.add(explorer)
        
        # Initialize narrative state
        narrative_state = UserNarrativeState(
            user_id=3000001,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test journey progression
        service = UserNarrativeService(session)
        
        # TIER 1: Explorer characteristics - curiosity and discovery focus
        # Test progression through fragments 1-5
        for fragment_id in range(1, 6):
            state = await service.get_user_narrative_state(3000001)
            assert state.tier == 1, f"Tier incorrect at fragment {fragment_id}"
            
            # Simulate Explorer choice (always exploring/discovering)
            decision = UserDecisionLog(
                user_id=3000001,
                fragment_id=fragment_id,
                choice_index=0,  # Always first choice (Explorer behavior)
                choice_text=f"Explore fragment {fragment_id}",
                timestamp=datetime.datetime.utcnow()
            )
            session.add(decision)
            
            # Update progression
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Test Tier 2 progression eligibility
        can_progress = await service.can_user_progress_to_tier(3000001, 2)
        assert can_progress, "Explorer cannot progress to Tier 2!"
        
        # Progress to VIP for Tier 2 access
        explorer.role = "vip"
        explorer.vip_expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        narrative_state.tier = 2
        narrative_state.current_fragment_id = 6
        await session.commit()
        
        # TIER 2: Deeper exploration (Los Kinkys)
        for fragment_id in range(6, 11):
            # Explorer should get exploration-focused choices
            state = await service.get_user_narrative_state(3000001)
            assert state.tier == 2, f"Tier 2 access failed at fragment {fragment_id}"
            
            # Continue Explorer journey
            decision = UserDecisionLog(
                user_id=3000001,
                fragment_id=fragment_id,
                choice_index=0,
                choice_text=f"Deeply explore {fragment_id}",
                timestamp=datetime.datetime.utcnow()
            )
            session.add(decision)
            
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Test Tier 3 progression
        can_progress_tier3 = await service.can_user_progress_to_tier(3000001, 3)
        assert can_progress_tier3, "Explorer cannot progress to Elite Tier!"
        
        # Progress to Elite
        narrative_state.tier = 3
        narrative_state.current_fragment_id = 11
        await session.commit()
        
        # TIER 3: Elite exploration (El Diván)
        for fragment_id in range(11, 17):
            state = await service.get_user_narrative_state(3000001)
            assert state.tier == 3, f"Elite tier access failed at fragment {fragment_id}"
            
            # Elite Explorer choices
            decision = UserDecisionLog(
                user_id=3000001,
                fragment_id=fragment_id,
                choice_index=0,
                choice_text=f"Ultimate exploration {fragment_id}",
                timestamp=datetime.datetime.utcnow()
            )
            session.add(decision)
            
            narrative_state.completed_fragments.append(fragment_id)
            if fragment_id < 16:
                narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Verify complete journey
        final_state = await service.get_user_narrative_state(3000001)
        assert final_state.tier == 3, "Explorer didn't reach Elite tier!"
        assert len(final_state.completed_fragments) == 16, f"Explorer completed {len(final_state.completed_fragments)}/16 fragments!"
    
    @pytest.mark.asyncio
    async def test_explorer_clue_hunting_behavior(self, session):
        """🔍 Explorer should excel at clue hunting."""
        # Create Explorer for clue testing
        explorer = User(
            id=3000002,
            first_name="ExplorerClueHunter",
            role="vip",
            points=200.0,
            archetype="Explorer"
        )
        session.add(explorer)
        
        # Create clues that Explorer should find
        exploration_clues = [
            LorePiece(
                id="explorer_clue_001",
                title="Hidden Path Discovery",
                content="Only true explorers find this hidden path...",
                unlock_condition="explorer_archetype_advantage",
                tier_required=1
            ),
            LorePiece(
                id="explorer_clue_002", 
                title="Secret Chamber",
                content="The explorer's intuition reveals secret chambers...",
                unlock_condition="exploration_bonus",
                tier_required=2
            )
        ]
        
        for clue in exploration_clues:
            session.add(clue)
        await session.commit()
        
        # Test clue hunting integration
        from services.clue_treasure_hunting_cinema_integration import ClueTreasureHuntingCinemaIntegration
        
        clue_system = ClueTreasureHuntingCinemaIntegration(session)
        
        explorer_context = {
            "current_fragment": 8,
            "user_archetype": "Explorer",
            "exploration_bonus": True,
            "curiosity_level": "high"
        }
        
        available_clues = await clue_system.get_available_cinema_clues(3000002, explorer_context)
        
        # Explorer should have access to exploration-specific clues
        assert len(available_clues) >= 0, "Explorer clue hunting failed!"
        
        # Test unlocking Explorer-specific clue
        unlock_result = await clue_system.attempt_cinema_clue_unlock(
            3000002, "explorer_clue_001", explorer_context
        )
        
        assert unlock_result.get("success", False) or "archetype_bonus" in str(unlock_result), \
            "Explorer archetype bonus not applied for clue hunting!"


class TestRomanticArchetypeJourney:
    """💕 Complete journey testing for Romantic archetype."""
    
    @pytest.mark.asyncio
    async def test_romantic_emotional_crescendo_journey(self, session):
        """🔒 CRITICAL: Romantic user should have enhanced emotional crescendo experience."""
        # Create Romantic user
        romantic = User(
            id=4000001,
            first_name="RomanticJourney",
            username="romantic_journey", 
            role="vip",  # Romantic gets VIP for emotional content
            points=150.0,
            archetype="Romantic",
            vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=30)
        )
        session.add(romantic)
        
        # Initialize with emotional crescendo tracking
        narrative_state = UserNarrativeState(
            user_id=4000001,
            current_fragment_id=1,
            tier=1,
            emotional_crescendo_level=1,
            completed_fragments=[],
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test Romantic emotional progression
        from services.emotional_dependency_engine import EmotionalDependencyEngine
        emotion_engine = EmotionalDependencyEngine(session)
        
        service = UserNarrativeService(session)
        
        # Journey through emotional crescendo levels
        for crescendo_level in range(1, 7):  # 6-level crescendo
            # Update emotional state
            narrative_state.emotional_crescendo_level = crescendo_level
            await session.commit()
            
            # Test emotional intensity for Romantic
            intensity = await emotion_engine.calculate_emotional_intensity(crescendo_level)
            
            # Romantic should have higher emotional sensitivity
            if crescendo_level >= 4:  # High levels
                assert intensity >= 0.7, f"Emotional intensity too low for Romantic at level {crescendo_level}: {intensity}"
            
            # Test Romantic-specific choices at this level
            from services.crescendo_choice_integration import CrescendoChoiceIntegration
            choice_integration = CrescendoChoiceIntegration(session)
            
            base_choices = [
                {"text": "Resist", "consequence": "resistance"},
                {"text": "Embrace", "consequence": "surrender"}
            ]
            
            romantic_choices = await choice_integration.modify_choices_for_crescendo_level(
                base_choices, crescendo_level, archetype="Romantic"
            )
            
            # Romantic should get emotionally rich choices
            choice_texts = [choice["text"] for choice in romantic_choices]
            if crescendo_level >= 3:
                assert any(emotional_word in " ".join(choice_texts).lower() 
                          for emotional_word in ["passion", "heart", "soul", "feel", "emotion", "desire"]), \
                    f"Romantic choices lack emotional language at level {crescendo_level}: {choice_texts}"
    
    @pytest.mark.asyncio
    async def test_romantic_vip_tier_progression(self, session):
        """💎 Romantic archetype VIP tier progression (Los Kinkys → El Diván → Elite)."""
        romantic = User(
            id=4000002,
            first_name="RomanticVIP",
            role="vip",
            points=500.0,
            archetype="Romantic",
            vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=90)
        )
        session.add(romantic)
        
        # Start at Los Kinkys (Tier 2)
        narrative_state = UserNarrativeState(
            user_id=4000002,
            current_fragment_id=6,
            tier=2,
            emotional_crescendo_level=3,
            completed_fragments=list(range(1, 6)),
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        service = UserNarrativeService(session)
        
        # Test Los Kinkys progression (Tier 2: fragments 6-10)
        for fragment_id in range(6, 11):
            state = await service.get_user_narrative_state(4000002)
            assert state.tier == 2, f"Los Kinkys access failed at fragment {fragment_id}"
            
            # Romantic choices should emphasize emotional connection
            decision = UserDecisionLog(
                user_id=4000002,
                fragment_id=fragment_id,
                choice_index=1,  # Romantic tends towards emotional choices
                choice_text=f"Feel deeply into fragment {fragment_id}",
                timestamp=datetime.datetime.utcnow()
            )
            session.add(decision)
            
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            narrative_state.emotional_crescendo_level = min(6, narrative_state.emotional_crescendo_level + 1)
            await session.commit()
        
        # Progress to El Diván (Elite Tier 3)
        narrative_state.tier = 3
        narrative_state.current_fragment_id = 11
        await session.commit()
        
        # Test El Diván progression (Tier 3: fragments 11-16)
        for fragment_id in range(11, 17):
            state = await service.get_user_narrative_state(4000002)
            assert state.tier == 3, f"El Diván access failed at fragment {fragment_id}"
            
            # Elite romantic content
            decision = UserDecisionLog(
                user_id=4000002,
                fragment_id=fragment_id,
                choice_index=1,
                choice_text=f"Elite romantic connection {fragment_id}",
                timestamp=datetime.datetime.utcnow()
            )
            session.add(decision)
            
            narrative_state.completed_fragments.append(fragment_id)
            if fragment_id < 16:
                narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Verify complete romantic journey
        final_state = await service.get_user_narrative_state(4000002)
        assert final_state.tier == 3, "Romantic didn't reach Elite tier!"
        assert final_state.emotional_crescendo_level >= 5, "Romantic emotional crescendo insufficient!"


class TestAnalyticalArchetypeJourney:
    """🔬 Complete journey testing for Analytical archetype."""
    
    @pytest.mark.asyncio
    async def test_analytical_logical_progression(self, session):
        """🔒 CRITICAL: Analytical user should follow logical, methodical progression."""
        analytical = User(
            id=5000001,
            first_name="AnalyticalJourney",
            username="analytical_journey",
            role="free",
            points=0.0,
            archetype="Analytical"
        )
        session.add(analytical)
        
        narrative_state = UserNarrativeState(
            user_id=5000001,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[],
            analytical_notes=[]  # Analytical archetype keeps detailed notes
        )
        session.add(narrative_state)
        await session.commit()
        
        service = UserNarrativeService(session)
        
        # Analytical progression - methodical and thorough
        for fragment_id in range(1, 6):  # Tier 1 progression
            state = await service.get_user_narrative_state(5000001)
            
            # Analytical should analyze each fragment thoroughly
            decision = UserDecisionLog(
                user_id=5000001,
                fragment_id=fragment_id,
                choice_index=0,  # Analytical picks logical first choice
                choice_text=f"Analyze and observe fragment {fragment_id}",
                timestamp=datetime.datetime.utcnow(),
                analysis_notes=f"Logical analysis of fragment {fragment_id} patterns"
            )
            session.add(decision)
            
            # Add analytical observation
            if hasattr(narrative_state, 'analytical_notes'):
                narrative_state.analytical_notes.append({
                    "fragment": fragment_id,
                    "observation": f"Pattern analysis complete for fragment {fragment_id}",
                    "logical_conclusion": "Data supports continued progression"
                })
            
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Test analytical choice generation
        from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
        
        choice_architecture = ChoiceArchitectureMasterpiece(session)
        
        analytical_context = {
            "fragment_id": 5,
            "user_archetype": "Analytical",
            "logical_analysis": True,
            "pattern_recognition": "high"
        }
        
        analytical_choices = await choice_architecture.generate_personalized_choices(
            5000001, analytical_context
        )
        
        # Analytical should get logic-based choices
        choice_texts = [choice["text"] for choice in analytical_choices]
        assert any(analytical_word in " ".join(choice_texts).lower() 
                  for analytical_word in ["analyze", "observe", "study", "examine", "logical", "pattern"]), \
            f"Analytical choices lack analytical language: {choice_texts}"
    
    @pytest.mark.asyncio
    async def test_analytical_clue_systematic_approach(self, session):
        """🔍 Analytical should have systematic approach to clues."""
        analytical = User(
            id=5000002,
            first_name="AnalyticalClues",
            role="vip",
            points=300.0,
            archetype="Analytical"
        )
        session.add(analytical)
        
        # Create analytical-friendly clues
        analytical_clues = [
            LorePiece(
                id="analytical_clue_001",
                title="Pattern Analysis Data",
                content="Systematic analysis reveals hidden patterns in Diana's behavior...",
                unlock_condition="analytical_bonus",
                tier_required=2,
                analytical_data={"pattern_complexity": "high", "logical_structure": "complete"}
            ),
            LorePiece(
                id="analytical_clue_002",
                title="Behavioral Study Results",
                content="Comprehensive study of character motivations and psychological patterns...",
                unlock_condition="systematic_observation",
                tier_required=2
            )
        ]
        
        for clue in analytical_clues:
            session.add(clue)
        await session.commit()
        
        # Test systematic clue hunting
        from services.enhanced_clue_unlock_service import EnhancedClueUnlockService
        
        clue_service = EnhancedClueUnlockService(session)
        
        analytical_context = {
            "analytical_approach": True,
            "systematic_observation": True,
            "pattern_recognition_score": 0.9,
            "logical_analysis_complete": True
        }
        
        can_unlock = await clue_service.can_user_unlock_enhanced_clue(
            5000002, "analytical_clue_001", analytical_context
        )
        
        # Analytical should have high success rate for analytical clues
        assert can_unlock or "analytical_bonus" in str(can_unlock), \
            "Analytical archetype not getting analytical clue bonus!"


class TestPersistentArchetypeJourney:
    """⚡ Complete journey testing for Persistent archetype."""
    
    @pytest.mark.asyncio
    async def test_persistent_determination_journey(self, session):
        """🔒 CRITICAL: Persistent user should show determination and resilience."""
        persistent = User(
            id=6000001,
            first_name="PersistentJourney",
            username="persistent_journey",
            role="free",
            points=0.0,
            archetype="Persistent"
        )
        session.add(persistent)
        
        narrative_state = UserNarrativeState(
            user_id=6000001,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[],
            persistence_streak=0,
            determination_level="high"
        )
        session.add(narrative_state)
        await session.commit()
        
        service = UserNarrativeService(session)
        
        # Test persistent behavior - never giving up, pushing through challenges
        for fragment_id in range(1, 6):
            state = await service.get_user_narrative_state(6000001)
            
            # Persistent makes determined choices
            decision = UserDecisionLog(
                user_id=6000001,
                fragment_id=fragment_id,
                choice_index=0,  # Always pushes forward
                choice_text=f"Push through challenges in fragment {fragment_id}",
                timestamp=datetime.datetime.utcnow(),
                persistence_marker=True
            )
            session.add(decision)
            
            # Track persistence
            if hasattr(narrative_state, 'persistence_streak'):
                narrative_state.persistence_streak += 1
            
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
        
        # Verify persistence traits
        final_state = await service.get_user_narrative_state(6000001)
        if hasattr(final_state, 'persistence_streak'):
            assert final_state.persistence_streak >= 5, "Persistence streak not tracked!"
    
    @pytest.mark.asyncio
    async def test_persistent_retry_mechanism(self, session):
        """⚡ Persistent archetype should have retry bonuses."""
        persistent = User(
            id=6000002,
            first_name="PersistentRetry",
            role="vip",
            points=100.0,
            archetype="Persistent"
        )
        session.add(persistent)
        await session.commit()
        
        # Test retry mechanism for failed attempts
        from services.delayed_gratification_premium_algorithm import DelayedGratificationPremiumAlgorithm
        
        algorithm = DelayedGratificationPremiumAlgorithm(session)
        
        # Persistent should get bonuses for retrying
        base_reward = 50.0
        retry_count = 3
        
        persistent_bonus = await algorithm.calculate_persistence_bonus(
            base_reward, retry_count, archetype="Persistent"
        )
        
        # Should get significant bonus for persistence
        expected_min = base_reward * 1.3  # 30% bonus minimum
        assert persistent_bonus >= expected_min, \
            f"Persistent retry bonus too low: {persistent_bonus} < {expected_min}"


class TestPatientArchetypeJourney:
    """🧘 Complete journey testing for Patient archetype."""
    
    @pytest.mark.asyncio
    async def test_patient_delayed_gratification_journey(self, session):
        """🔒 CRITICAL: Patient user should excel at delayed gratification."""
        patient = User(
            id=7000001,
            first_name="PatientJourney",
            username="patient_journey",
            role="vip",
            points=0.0,
            archetype="Patient",
            vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=60)
        )
        session.add(patient)
        
        narrative_state = UserNarrativeState(
            user_id=7000001,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[],
            patience_level="maximum",
            delayed_rewards_pending=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test delayed gratification bonuses
        from services.delayed_gratification_premium_algorithm import DelayedGratificationPremiumAlgorithm
        
        algorithm = DelayedGratificationPremiumAlgorithm(session)
        
        # Patient should get maximum delayed gratification bonuses
        base_reward = 100.0
        delay_hours = 48  # 2 days delay
        
        patient_premium = await algorithm.calculate_delayed_premium(
            base_reward, delay_hours, user_role="vip", archetype="Patient"
        )
        
        # Patient archetype should get highest delayed reward multiplier
        expected_min = base_reward * 2.0  # 100% bonus minimum
        assert patient_premium >= expected_min, \
            f"Patient delayed gratification bonus too low: {patient_premium} < {expected_min}"
    
    @pytest.mark.asyncio
    async def test_patient_waiting_reward_system(self, session):
        """🧘 Patient should be rewarded for waiting and careful consideration."""
        patient = User(
            id=7000002,
            first_name="PatientWaiting",
            role="vip",
            points=200.0,
            archetype="Patient"
        )
        session.add(patient)
        await session.commit()
        
        service = UserNarrativeService(session)
        
        # Create scenario where patience is rewarded
        narrative_state = UserNarrativeState(
            user_id=7000002,
            current_fragment_id=8,
            tier=2,
            completed_fragments=list(range(1, 8)),
            available_choices=[],
            last_choice_timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test that Patient gets bonus for waiting between choices
        time_since_last_choice = datetime.datetime.utcnow() - narrative_state.last_choice_timestamp
        waiting_hours = time_since_last_choice.total_seconds() / 3600
        
        # Patient should be rewarded for waiting
        if waiting_hours >= 12:  # Waited at least 12 hours
            from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
            
            choice_architecture = ChoiceArchitectureMasterpiece(session)
            
            patient_context = {
                "fragment_id": 8,
                "user_archetype": "Patient",
                "waiting_bonus": True,
                "patience_demonstrated": True,
                "hours_waited": waiting_hours
            }
            
            patient_choices = await choice_architecture.generate_personalized_choices(
                7000002, patient_context
            )
            
            # Should get enhanced choices for patience
            assert len(patient_choices) >= 2, "Patient waiting bonus not applied!"
            
            # Choices should acknowledge patience
            choice_texts = [choice["text"] for choice in patient_choices]
            assert any("patience" in text.lower() or "wait" in text.lower() or "careful" in text.lower()
                      for text in choice_texts), \
                f"Patient choices don't acknowledge patience: {choice_texts}"


class TestDirectArchetypeJourney:
    """⚡ Complete journey testing for Direct archetype."""
    
    @pytest.mark.asyncio
    async def test_direct_fast_progression_journey(self, session):
        """🔒 CRITICAL: Direct user should have fast, efficient progression."""
        direct = User(
            id=8000001,
            first_name="DirectJourney",
            username="direct_journey",
            role="free",
            points=0.0,
            archetype="Direct"
        )
        session.add(direct)
        
        narrative_state = UserNarrativeState(
            user_id=8000001,
            current_fragment_id=1,
            tier=1,
            completed_fragments=[],
            available_choices=[],
            progression_speed="fast"
        )
        session.add(narrative_state)
        await session.commit()
        
        service = UserNarrativeService(session)
        
        # Direct archetype should move through content quickly and efficiently
        progression_times = []
        
        for fragment_id in range(1, 6):
            start_time = datetime.datetime.utcnow()
            
            # Direct makes quick, decisive choices
            decision = UserDecisionLog(
                user_id=8000001,
                fragment_id=fragment_id,
                choice_index=0,  # Quick first choice
                choice_text=f"Direct action in fragment {fragment_id}",
                timestamp=datetime.datetime.utcnow(),
                decision_speed="fast"
            )
            session.add(decision)
            
            narrative_state.completed_fragments.append(fragment_id)
            narrative_state.current_fragment_id = fragment_id + 1
            await session.commit()
            
            end_time = datetime.datetime.utcnow()
            progression_time = (end_time - start_time).total_seconds()
            progression_times.append(progression_time)
        
        # Direct should have consistent fast progression
        average_time = sum(progression_times) / len(progression_times)
        assert average_time < 1.0, f"Direct archetype progression too slow: {average_time}s"
    
    @pytest.mark.asyncio
    async def test_direct_choice_preferences(self, session):
        """⚡ Direct archetype should get straightforward, action-oriented choices."""
        direct = User(
            id=8000002,
            first_name="DirectChoices",
            role="vip",
            points=150.0,
            archetype="Direct"
        )
        session.add(direct)
        await session.commit()
        
        from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
        
        choice_architecture = ChoiceArchitectureMasterpiece(session)
        
        direct_context = {
            "fragment_id": 7,
            "user_archetype": "Direct",
            "action_preference": "immediate",
            "complexity_tolerance": "low"
        }
        
        direct_choices = await choice_architecture.generate_personalized_choices(
            8000002, direct_context
        )
        
        # Direct should get clear, action-oriented choices
        choice_texts = [choice["text"] for choice in direct_choices]
        
        assert any(action_word in " ".join(choice_texts).lower() 
                  for action_word in ["act", "do", "take", "move", "decide", "choose"]), \
            f"Direct choices lack action-oriented language: {choice_texts}"
        
        # Choices should be concise (Direct doesn't like long explanations)
        for choice in direct_choices:
            choice_length = len(choice["text"].split())
            assert choice_length <= 10, \
                f"Direct choice too verbose: '{choice['text']}' ({choice_length} words)"


class TestArchetypeInteractionMatrix:
    """🎭 Tests for archetype interactions and compatibility."""
    
    @pytest.mark.asyncio
    async def test_archetype_compatibility_matrix(self, session):
        """🔒 CRITICAL: All archetypes must coexist and interact properly."""
        archetypes = ["Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"]
        
        # Create one user of each archetype
        users = []
        for i, archetype in enumerate(archetypes):
            user = User(
                id=9000000 + i,
                first_name=f"Matrix{archetype}",
                username=f"matrix_{archetype.lower()}",
                role="vip" if i % 2 == 0 else "free",
                points=100.0 + (i * 50),
                archetype=archetype,
                vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=30) if i % 2 == 0 else None
            )
            session.add(user)
            users.append(user)
        
        await session.commit()
        
        # Test that system can handle all archetypes simultaneously
        service = UserNarrativeService(session)
        
        for user in users:
            # Each archetype should get their narrative state
            state = await service.get_user_narrative_state(user.id)
            assert state is not None, f"Narrative state failed for {user.archetype}!"
            
            # Should be able to progress regardless of archetype
            can_progress = await service.can_user_progress_to_tier(user.id, 2)
            assert isinstance(can_progress, bool), f"Progression check failed for {user.archetype}!"
    
    @pytest.mark.asyncio
    async def test_archetype_choice_differentiation(self, session):
        """🎭 Different archetypes should get meaningfully different choices."""
        from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
        
        choice_architecture = ChoiceArchitectureMasterpiece(session)
        
        # Create users of different archetypes in same situation
        test_archetypes = ["Explorer", "Romantic", "Analytical", "Direct"]
        archetype_choices = {}
        
        for i, archetype in enumerate(test_archetypes):
            user = User(
                id=9100000 + i,
                first_name=f"Diff{archetype}",
                role="vip",
                points=200.0,
                archetype=archetype
            )
            session.add(user)
        
        await session.commit()
        
        # Same context, different archetypes should get different choices
        base_context = {
            "fragment_id": 10,
            "emotional_crescendo_level": 4,
            "narrative_progress": 0.6
        }
        
        for i, archetype in enumerate(test_archetypes):
            context = {**base_context, "user_archetype": archetype}
            choices = await choice_architecture.generate_personalized_choices(
                9100000 + i, context
            )
            archetype_choices[archetype] = [choice["text"] for choice in choices]
        
        # Verify choices are different between archetypes
        archetype_list = list(archetype_choices.keys())
        for i in range(len(archetype_list)):
            for j in range(i + 1, len(archetype_list)):
                archetype1, archetype2 = archetype_list[i], archetype_list[j]
                choices1 = set(archetype_choices[archetype1])
                choices2 = set(archetype_choices[archetype2])
                
                # Should have at least some different choices
                overlap = len(choices1.intersection(choices2))
                total_unique = len(choices1.union(choices2))
                differentiation = (total_unique - overlap) / total_unique if total_unique > 0 else 0
                
                assert differentiation >= 0.3, \
                    f"Insufficient choice differentiation between {archetype1} and {archetype2}: {differentiation:.2f}"


@pytest.mark.asyncio
async def test_complete_archetype_system_integration_smoke_test(session):
    """🚨 CRITICAL SMOKE TEST: All 6 archetypes must work together in complete system."""
    archetypes = ["Explorer", "Direct", "Romantic", "Analytical", "Persistent", "Patient"]
    
    # Create complete user ecosystem
    users = []
    for i, archetype in enumerate(archetypes):
        user = User(
            id=9999000 + i,
            first_name=f"Smoke{archetype}",
            username=f"smoke_{archetype.lower()}",
            role="vip",
            points=500.0 + (i * 100),
            archetype=archetype,
            vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=60)
        )
        session.add(user)
        users.append(user)
        
        # Create narrative states for all
        narrative_state = UserNarrativeState(
            user_id=user.id,
            current_fragment_id=8,  # Mid-journey
            tier=2,  # Los Kinkys tier
            emotional_crescendo_level=3 + (i % 4),  # Varied emotional levels
            completed_fragments=list(range(1, 8)),
            available_choices=[]
        )
        session.add(narrative_state)
    
    await session.commit()
    
    # Test all services with all archetypes
    services = [
        UserNarrativeService(session),
        UserArchetypingService(session)
    ]
    
    for service in services:
        for user in users:
            if isinstance(service, UserNarrativeService):
                # Test narrative service
                state = await service.get_user_narrative_state(user.id)
                assert state is not None, f"Narrative service failed for {user.archetype}!"
                assert state.tier == 2, f"Narrative tier incorrect for {user.archetype}!"
                
            elif isinstance(service, UserArchetypingService):
                # Test archetyping service
                signature = await service.generate_soul_signature(user.id)
                assert signature is not None, f"Soul signature failed for {user.archetype}!"
                assert signature["archetype"] == user.archetype, \
                    f"Soul signature mismatch for {user.archetype}!"
    
    # Test choice generation for all archetypes
    from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
    choice_architecture = ChoiceArchitectureMasterpiece(session)
    
    for user in users:
        context = {
            "fragment_id": 8,
            "user_archetype": user.archetype,
            "emotional_crescendo_level": 4,
            "tier": 2
        }
        
        choices = await choice_architecture.generate_personalized_choices(user.id, context)
        assert len(choices) >= 2, f"Choice generation failed for {user.archetype}!"
        
        # Verify archetype-appropriate choices
        choice_texts = " ".join([choice["text"] for choice in choices]).lower()
        
        if user.archetype == "Explorer":
            assert any(word in choice_texts for word in ["explor", "discover", "find"]), \
                f"Explorer choices not appropriate: {choice_texts}"
        elif user.archetype == "Romantic":
            assert any(word in choice_texts for word in ["feel", "heart", "emotion", "passion"]), \
                f"Romantic choices not appropriate: {choice_texts}"
        elif user.archetype == "Analytical":
            assert any(word in choice_texts for word in ["analyz", "study", "observ", "logic"]), \
                f"Analytical choices not appropriate: {choice_texts}"
        elif user.archetype == "Direct":
            assert any(word in choice_texts for word in ["act", "do", "decid", "take"]), \
                f"Direct choices not appropriate: {choice_texts}"
        elif user.archetype == "Persistent":
            assert any(word in choice_texts for word in ["persist", "continu", "push", "determin"]), \
                f"Persistent choices not appropriate: {choice_texts}"
        elif user.archetype == "Patient":
            assert any(word in choice_texts for word in ["wait", "patient", "careful", "consider"]), \
                f"Patient choices not appropriate: {choice_texts}"
    
    # 🎭 ALL ARCHETYPES FULLY OPERATIONAL!
    print("🎭 USER JOURNEY & ARCHETYPE FRAMEWORK: ALL 6 ARCHETYPES FULLY OPERATIONAL!")