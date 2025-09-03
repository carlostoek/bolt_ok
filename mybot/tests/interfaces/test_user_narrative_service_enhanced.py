"""
Tests for IUserNarrativeService Enhanced with emotional context functionality.
Tests the 5 specific enhanced methods with emotional context integration.
"""
import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from services.interfaces.user_narrative_interface import (
    IUserNarrativeService, 
    ContextualizedFragment,
    NarrativeInteractionResult
)
from services.interfaces.emotional_state_interface import (
    EmotionalState, 
    EmotionalContext
)
from database.narrative_unified import UserNarrativeState, NarrativeFragment


class MockUserNarrativeServiceEnhanced(IUserNarrativeService):
    """Mock implementation para testing de la interfaz enhanced."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._mock_fragments = {}
        self._mock_states = {}
        self._emotional_impacts = {}

    async def get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        return self._mock_states.get(user_id, UserNarrativeState(user_id=user_id))

    async def update_current_fragment(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        state = await self.get_or_create_user_state(user_id)
        state.current_fragment_id = fragment_id
        return state

    async def mark_fragment_completed(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        state = await self.get_or_create_user_state(user_id)
        if fragment_id not in state.completed_fragments:
            state.completed_fragments.append(fragment_id)
        return state

    async def unlock_clue(self, user_id: int, clue_code: str) -> UserNarrativeState:
        state = await self.get_or_create_user_state(user_id)
        if clue_code not in state.unlocked_clues:
            state.unlocked_clues.append(clue_code)
        return state

    async def check_user_access(self, user_id: int, fragment_id: str) -> bool:
        return True  # Mock always grants access

    async def get_user_progress_percentage(self, user_id: int) -> float:
        state = await self.get_or_create_user_state(user_id)
        return len(state.completed_fragments) * 10.0  # Mock calculation

    async def reset_user_progress(self, user_id: int) -> UserNarrativeState:
        state = UserNarrativeState(user_id=user_id)
        self._mock_states[user_id] = state
        return state

    # ===== ENHANCED METHODS IMPLEMENTATIONS =====

    async def get_contextualized_fragment(self, user_id: int, fragment_id: str, 
                                        emotional_context: EmotionalContext = None) -> ContextualizedFragment:
        """Implementation with emotional context adaptation."""
        fragment = NarrativeFragment(
            id=fragment_id,
            title="Test Fragment",
            content="Original content for testing",
            fragment_type="STORY"
        )
        
        if emotional_context is None:
            # Return standard content for neutral emotion
            return ContextualizedFragment(
                fragment=fragment,
                adapted_content=fragment.content,
                emotional_tone="neutral",
                personalization_data={}
            )
        
        # Adapt content based on emotional context
        if emotional_context.primary_state == EmotionalState.EXCITED:
            adapted_content = f"¡{fragment.content} Con energía adicional!"
            tone = "energetic"
        elif emotional_context.primary_state == EmotionalState.CONFUSED:
            adapted_content = f"{fragment.content} Con explicaciones adicionales para claridad."
            tone = "supportive"
        else:
            adapted_content = fragment.content
            tone = emotional_context.primary_state.value
            
        return ContextualizedFragment(
            fragment=fragment,
            adapted_content=adapted_content,
            emotional_tone=tone,
            personalization_data={
                "emotional_state": emotional_context.primary_state.value,
                "intensity": emotional_context.intensity,
                "adaptation_applied": True
            }
        )

    async def process_narrative_interaction(self, user_id: int, interaction_data: dict) -> NarrativeInteractionResult:
        """Process interaction and update emotional state."""
        if "choice_id" not in interaction_data:
            raise ValueError("Invalid interaction data - missing choice_id")
            
        state = await self.get_or_create_user_state(user_id)
        
        # Update progress based on choice
        choice_id = interaction_data["choice_id"]
        if "target_fragment" in interaction_data:
            state.current_fragment_id = interaction_data["target_fragment"]
            
        # Determine emotional response based on choice
        emotional_response = EmotionalState.ENGAGED
        if choice_id == "positive_choice":
            emotional_response = EmotionalState.SATISFIED
        elif choice_id == "negative_choice":
            emotional_response = EmotionalState.FRUSTRATED
            
        triggered_effects = [{
            "type": "emotional_update",
            "emotion": emotional_response.value,
            "intensity": 0.7
        }]
        
        # Mock next fragment
        next_fragment = None
        if "target_fragment" in interaction_data:
            next_fragment = NarrativeFragment(
                id=interaction_data["target_fragment"],
                title="Next Fragment",
                content="Next content",
                fragment_type="STORY"
            )
        
        return NarrativeInteractionResult(
            updated_state=state,
            emotional_response=emotional_response,
            triggered_effects=triggered_effects,
            next_fragment=next_fragment
        )

    async def get_personalized_narrative_flow(self, user_id: int, 
                                            emotional_context: EmotionalContext = None) -> list[str]:
        """Get personalized flow considering emotional state."""
        base_flow = ["fragment_1", "fragment_2", "fragment_3", "fragment_4"]
        
        if emotional_context is None:
            return base_flow
            
        # Modify flow based on emotional state
        if emotional_context.primary_state == EmotionalState.EXCITED:
            # Add more engaging fragments for excited users
            return ["fragment_1", "fragment_exciting", "fragment_2", "fragment_action", "fragment_3"]
        elif emotional_context.primary_state == EmotionalState.CONFUSED:
            # Add explanatory fragments for confused users  
            return ["fragment_1", "fragment_explanation", "fragment_2", "fragment_clarification", "fragment_3"]
        elif emotional_context.primary_state == EmotionalState.FRUSTRATED:
            # Skip complex fragments for frustrated users
            return ["fragment_1", "fragment_2", "fragment_4"]
            
        return base_flow

    async def update_narrative_emotional_impact(self, user_id: int, fragment_id: str, 
                                              emotional_response: EmotionalState, intensity: float) -> None:
        """Record emotional impact of narrative fragments."""
        if not (0.0 <= intensity <= 1.0):
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {intensity}")
            
        self._emotional_impacts[(user_id, fragment_id)] = {
            "emotional_response": emotional_response,
            "intensity": intensity,
            "timestamp": datetime.datetime.utcnow()
        }


@pytest.fixture
def mock_session():
    """Mock AsyncSession for testing."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def enhanced_service(mock_session):
    """Enhanced narrative service for testing."""
    return MockUserNarrativeServiceEnhanced(mock_session)


@pytest.fixture
def mock_emotional_context():
    """Mock emotional context for testing."""
    return EmotionalContext(
        primary_state=EmotionalState.EXCITED,
        intensity=0.8,
        secondary_states={EmotionalState.CURIOUS: 0.3},
        last_updated=datetime.datetime.utcnow(),
        triggers=["positive_interaction"]
    )


@pytest.fixture
def neutral_emotional_context():
    """Neutral emotional context for testing."""
    return EmotionalContext(
        primary_state=EmotionalState.NEUTRAL,
        intensity=0.5,
        secondary_states={},
        last_updated=datetime.datetime.utcnow(),
        triggers=[]
    )


# ===== TEST CASES FOR ENHANCED FUNCTIONALITY =====

@pytest.mark.asyncio
async def test_get_contextualized_fragment_with_emotional_context_adapts_content(enhanced_service, mock_emotional_context):
    """Test that contextualized fragments adapt content based on emotional state."""
    user_id = 123456789
    fragment_id = "test_fragment_1"
    
    result = await enhanced_service.get_contextualized_fragment(
        user_id=user_id,
        fragment_id=fragment_id,
        emotional_context=mock_emotional_context
    )
    
    # Verify the fragment was contextualized with emotional adaptation
    assert isinstance(result, ContextualizedFragment)
    assert result.fragment.id == fragment_id
    assert result.emotional_tone == "energetic"  # Based on EXCITED state
    assert "¡" in result.adapted_content  # Spanish excitement marker added
    assert "Con energía adicional!" in result.adapted_content
    assert result.personalization_data["emotional_state"] == "excited"
    assert result.personalization_data["intensity"] == 0.8
    assert result.personalization_data["adaptation_applied"] is True


@pytest.mark.asyncio
async def test_get_contextualized_fragment_neutral_emotion_returns_standard_content(enhanced_service, neutral_emotional_context):
    """Test that neutral emotional state returns standard content without adaptation."""
    user_id = 123456789
    fragment_id = "test_fragment_2"
    
    result = await enhanced_service.get_contextualized_fragment(
        user_id=user_id,
        fragment_id=fragment_id,
        emotional_context=neutral_emotional_context
    )
    
    # Verify neutral context returns standard content
    assert isinstance(result, ContextualizedFragment)
    assert result.fragment.id == fragment_id
    assert result.emotional_tone == "neutral"
    assert result.adapted_content == "Original content for testing"  # No adaptation
    assert result.personalization_data["emotional_state"] == "neutral"
    assert result.personalization_data["intensity"] == 0.5


@pytest.mark.asyncio
async def test_process_narrative_interaction_choice_selection_updates_progress_and_emotion(enhanced_service):
    """Test that narrative interactions update both progress and emotional state."""
    user_id = 123456789
    interaction_data = {
        "choice_id": "positive_choice",
        "target_fragment": "fragment_next",
        "interaction_type": "choice_selection"
    }
    
    result = await enhanced_service.process_narrative_interaction(user_id, interaction_data)
    
    # Verify interaction processing
    assert isinstance(result, NarrativeInteractionResult)
    assert result.updated_state.user_id == user_id
    assert result.updated_state.current_fragment_id == "fragment_next"
    assert result.emotional_response == EmotionalState.SATISFIED  # Positive choice
    assert len(result.triggered_effects) > 0
    assert result.triggered_effects[0]["type"] == "emotional_update"
    assert result.triggered_effects[0]["emotion"] == "satisfied"
    assert result.triggered_effects[0]["intensity"] == 0.7
    assert result.next_fragment is not None
    assert result.next_fragment.id == "fragment_next"


@pytest.mark.asyncio
async def test_get_personalized_narrative_flow_considers_emotional_state(enhanced_service, mock_emotional_context):
    """Test that personalized flow considers user's emotional state."""
    user_id = 123456789
    
    # Test with excited emotional context
    flow = await enhanced_service.get_personalized_narrative_flow(user_id, mock_emotional_context)
    
    # Verify flow adaptation for excited user
    assert isinstance(flow, list)
    assert len(flow) == 5  # More engaging fragments added
    assert "fragment_exciting" in flow
    assert "fragment_action" in flow
    assert flow[0] == "fragment_1"  # Base structure maintained
    
    # Test with confused emotional context
    confused_context = EmotionalContext(
        primary_state=EmotionalState.CONFUSED,
        intensity=0.6,
        secondary_states={},
        last_updated=datetime.datetime.utcnow(),
        triggers=["complex_content"]
    )
    
    confused_flow = await enhanced_service.get_personalized_narrative_flow(user_id, confused_context)
    
    # Verify flow adaptation for confused user
    assert "fragment_explanation" in confused_flow
    assert "fragment_clarification" in confused_flow
    assert len(confused_flow) == 5  # Explanatory fragments added


@pytest.mark.asyncio
async def test_update_narrative_emotional_impact_records_user_response(enhanced_service):
    """Test that emotional impacts are properly recorded for narrative analysis."""
    user_id = 123456789
    fragment_id = "emotional_fragment_1"
    emotional_response = EmotionalState.SATISFIED
    intensity = 0.85
    
    # Should not raise any exception
    await enhanced_service.update_narrative_emotional_impact(
        user_id=user_id,
        fragment_id=fragment_id,
        emotional_response=emotional_response,
        intensity=intensity
    )
    
    # Verify the impact was recorded in the mock service
    impact_key = (user_id, fragment_id)
    assert impact_key in enhanced_service._emotional_impacts
    
    recorded_impact = enhanced_service._emotional_impacts[impact_key]
    assert recorded_impact["emotional_response"] == emotional_response
    assert recorded_impact["intensity"] == intensity
    assert "timestamp" in recorded_impact
    
    # Test invalid intensity raises error
    with pytest.raises(ValueError, match="Intensity must be between 0.0 and 1.0"):
        await enhanced_service.update_narrative_emotional_impact(
            user_id=user_id,
            fragment_id=fragment_id,
            emotional_response=emotional_response,
            intensity=1.5  # Invalid intensity
        )


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_enhanced_service_integration_flow(enhanced_service, mock_emotional_context):
    """Test complete integration flow of enhanced narrative service."""
    user_id = 123456789
    
    # Step 1: Get personalized flow
    flow = await enhanced_service.get_personalized_narrative_flow(user_id, mock_emotional_context)
    assert len(flow) > 0
    
    # Step 2: Get contextualized first fragment  
    first_fragment_id = flow[0]
    contextualized = await enhanced_service.get_contextualized_fragment(
        user_id, first_fragment_id, mock_emotional_context
    )
    assert contextualized.fragment.id == first_fragment_id
    
    # Step 3: Process interaction
    interaction = {
        "choice_id": "positive_choice",
        "target_fragment": flow[1] if len(flow) > 1 else "end_fragment"
    }
    interaction_result = await enhanced_service.process_narrative_interaction(user_id, interaction)
    
    # Step 4: Record emotional impact
    await enhanced_service.update_narrative_emotional_impact(
        user_id, 
        first_fragment_id,
        interaction_result.emotional_response,
        0.75
    )
    
    # Verify integration
    assert interaction_result.updated_state.user_id == user_id
    assert (user_id, first_fragment_id) in enhanced_service._emotional_impacts


@pytest.mark.asyncio 
async def test_enhanced_interface_contract_compliance(enhanced_service):
    """Test that enhanced service complies with interface contract."""
    # Verify all enhanced methods are implemented
    assert hasattr(enhanced_service, 'get_contextualized_fragment')
    assert hasattr(enhanced_service, 'process_narrative_interaction') 
    assert hasattr(enhanced_service, 'get_personalized_narrative_flow')
    assert hasattr(enhanced_service, 'update_narrative_emotional_impact')
    
    # Verify methods are async
    import asyncio
    user_id = 123456789
    
    # Test each enhanced method returns expected types
    contextualized = await enhanced_service.get_contextualized_fragment(user_id, "test")
    assert isinstance(contextualized, ContextualizedFragment)
    
    flow = await enhanced_service.get_personalized_narrative_flow(user_id)
    assert isinstance(flow, list)
    
    interaction_result = await enhanced_service.process_narrative_interaction(
        user_id, {"choice_id": "test_choice", "target_fragment": "test"}
    )
    assert isinstance(interaction_result, NarrativeInteractionResult)
    
    # update_narrative_emotional_impact should not raise
    await enhanced_service.update_narrative_emotional_impact(
        user_id, "test", EmotionalState.NEUTRAL, 0.5
    )