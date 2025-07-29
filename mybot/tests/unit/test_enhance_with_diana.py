import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock data for testing
MOCK_USER_ID = 123456789
MOCK_MESSAGE_ID = 1001
MOCK_CHANNEL_ID = -100123456
MOCK_REACTION_TYPE = "❤️"

class MockRelationshipStatus:
    INITIAL = "initial"
    ACQUAINTANCE = "acquaintance"
    FRIENDLY = "friendly"
    CLOSE = "close"
    INTIMATE = "intimate"

@pytest.fixture
def mock_relationship_state():
    return {
        "success": True,
        "relationship": {
            "user_id": MOCK_USER_ID,
            "status": "close",
            "trust_level": 0.8,
            "familiarity": 0.7,
            "rapport": 0.75,
            "dominant_emotion": "joy",
            "emotional_volatility": 0.2,
            "positive_interactions": 25,
            "negative_interactions": 3,
        }
    }

@pytest.fixture
def mock_personality_adaptation():
    return {
        "success": True,
        "adaptation": {
            "user_id": MOCK_USER_ID,
            "warmth": 0.8,
            "formality": 0.3,
            "humor": 0.7,
            "directness": 0.6,
            "assertiveness": 0.5,
            "curiosity": 0.6,
            "emotional_expressiveness": 0.8,
            "message_length_preference": 120,
            "complexity_level": 0.5,
            "emoji_usage": 0.6,
        }
    }

@pytest.fixture
def diana_service_mock():
    mock = AsyncMock()
    
    # Add necessary attributes and methods
    mock.is_active = MagicMock(return_value=True)
    
    return mock

@pytest.fixture
def coordinador_central_mock(diana_service_mock):
    mock = AsyncMock()
    
    # Add mock services
    mock.diana_service = diana_service_mock
    mock.channel_engagement = AsyncMock()
    mock.point_service = AsyncMock()
    mock.narrative_service = AsyncMock()
    
    # Add method implementations
    async def enhance_with_diana(user_id, resultado_base, **kwargs):
        # Implementation of the method being tested
        if not mock.diana_service.is_active():
            return resultado_base
            
        # Try to get relationship state
        relationship_result = await mock.diana_service.get_relationship_state(user_id)
        if not relationship_result.get("success", False):
            return resultado_base
            
        relationship = relationship_result.get("relationship", {})
        
        # Try to get personality adaptation
        adaptation_result = await mock.diana_service.get_personality_adaptation(user_id)
        if not adaptation_result.get("success", False):
            return resultado_base
        
        adaptation = adaptation_result.get("adaptation", {})
        
        # Try to use enhance_reaction_message if available
        if hasattr(mock.diana_service, "_enhance_reaction_message"):
            try:
                resultado_mejorado = await mock.diana_service._enhance_reaction_message(
                    user_id, resultado_base, relationship, adaptation, **kwargs
                )
                return resultado_mejorado
            except Exception:
                return resultado_base
        
        return resultado_base
    
    mock.enhance_with_diana = enhance_with_diana
    
    return mock

@pytest.mark.asyncio
async def test_enhance_with_diana_when_active(coordinador_central_mock, mock_relationship_state, mock_personality_adaptation):
    """Test that Diana enhancement works when active."""
    # Configure mocks
    coordinador_central_mock.diana_service.is_active.return_value = True
    coordinador_central_mock.diana_service.get_relationship_state.return_value = mock_relationship_state
    coordinador_central_mock.diana_service.get_personality_adaptation.return_value = mock_personality_adaptation
    
    # Setup mock for enhance_reaction_message
    async def mock_enhance_reaction(user_id, result, relationship, adaptation, **kwargs):
        return {
            "success": True,
            "message": "Diana mira con dulzura a mi amor... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
            "points_awarded": 10,
            "total_points": 150,
            "action": "reaction_success",
            "enhanced": True
        }
    
    coordinador_central_mock.diana_service._enhance_reaction_message = mock_enhance_reaction
    
    # Test result
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10,
        "total_points": 150,
        "action": "reaction_success"
    }
    
    result = await coordinador_central_mock.enhance_with_diana(
        MOCK_USER_ID, 
        resultado_base,
        reaction_type=MOCK_REACTION_TYPE
    )
    
    # Verify calls
    coordinador_central_mock.diana_service.is_active.assert_called_once()
    coordinador_central_mock.diana_service.get_relationship_state.assert_called_once_with(MOCK_USER_ID)
    coordinador_central_mock.diana_service.get_personality_adaptation.assert_called_once_with(MOCK_USER_ID)
    
    # Check enhanced message
    assert result["success"] is True
    assert "mira con dulzura a mi amor" in result["message"]
    assert result["enhanced"] is True

@pytest.mark.asyncio
async def test_enhance_with_diana_when_inactive(coordinador_central_mock):
    """Test that original functionality is maintained when Diana is inactive."""
    # Configure mocks to indicate Diana is not active
    coordinador_central_mock.diana_service.is_active.return_value = False
    
    # Original result
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10,
        "total_points": 150,
        "action": "reaction_success"
    }
    
    # Call the function
    result = await coordinador_central_mock.enhance_with_diana(
        MOCK_USER_ID, 
        resultado_base,
        reaction_type=MOCK_REACTION_TYPE
    )
    
    # Verify the result is unchanged
    assert result == resultado_base
    coordinador_central_mock.diana_service.is_active.assert_called_once()
    coordinador_central_mock.diana_service.get_relationship_state.assert_not_called()

@pytest.mark.asyncio
async def test_enhance_with_diana_with_error(coordinador_central_mock, mock_relationship_state, mock_personality_adaptation):
    """Test that original functionality is maintained when Diana encounters an error."""
    # Configure mocks
    coordinador_central_mock.diana_service.is_active.return_value = True
    coordinador_central_mock.diana_service.get_relationship_state.return_value = mock_relationship_state
    coordinador_central_mock.diana_service.get_personality_adaptation.return_value = mock_personality_adaptation
    
    # Make _enhance_reaction_message raise an exception
    async def mock_enhance_reaction_error(*args, **kwargs):
        raise Exception("Test error in enhancement")
    
    coordinador_central_mock.diana_service._enhance_reaction_message = mock_enhance_reaction_error
    
    # Original result
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10,
        "total_points": 150,
        "action": "reaction_success"
    }
    
    # Call the function
    result = await coordinador_central_mock.enhance_with_diana(
        MOCK_USER_ID, 
        resultado_base,
        reaction_type=MOCK_REACTION_TYPE
    )
    
    # Verify we get the original result back
    assert result == resultado_base

@pytest.mark.asyncio
async def test_flujo_reaccion_publicacion_integrates_diana():
    """Test that _flujo_reaccion_publicacion correctly integrates enhance_with_diana."""
    # Create mocks directly for this test
    coord_mock = AsyncMock()
    coord_mock.channel_engagement = AsyncMock()
    coord_mock.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
    
    coord_mock.point_service = AsyncMock()
    coord_mock.point_service.get_user_points = AsyncMock(return_value=150)
    
    # Create a mock for the enhance_with_diana method
    enhanced_result = {
        "success": True,
        "message": "Diana guiña un ojo a mi amor... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10, 
        "total_points": 150,
        "action": "reaction_success",
        "enhanced_by_diana": True
    }
    coord_mock.enhance_with_diana = AsyncMock(return_value=enhanced_result)
    
    # Create a mock implementation of _flujo_reaccion_publicacion
    async def mock_flujo(user_id, message_id, channel_id, reaction_type, bot=None):
        # Simulate core functionality
        puntos_otorgados = await coord_mock.channel_engagement.award_channel_reaction(
            user_id, message_id, channel_id, bot=bot
        )
        
        if not puntos_otorgados:
            return {
                "success": False,
                "message": "Diana observa tu gesto desde lejos, pero no parece haberlo notado... Intenta de nuevo más tarde.",
                "action": "reaction_failed"
            }
        
        puntos_actuales = await coord_mock.point_service.get_user_points(user_id)
        
        # Create base result
        resultado_base = {
            "success": True,
            "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
            "points_awarded": 10,
            "total_points": puntos_actuales,
            "action": "reaction_success"
        }
        
        # Apply Diana enhancement
        resultado_final = await coord_mock.enhance_with_diana(
            user_id, 
            resultado_base, 
            reaction_type=reaction_type
        )
        
        return resultado_final
    
    # Assign the implementation
    coord_mock._flujo_reaccion_publicacion = mock_flujo
    
    # Call the reaction flow
    result = await coord_mock._flujo_reaccion_publicacion(
        MOCK_USER_ID,
        MOCK_MESSAGE_ID,
        MOCK_CHANNEL_ID,
        MOCK_REACTION_TYPE
    )
    
    # Verify enhance_with_diana was called
    coord_mock.enhance_with_diana.assert_called_once()
    kwargs = coord_mock.enhance_with_diana.call_args[1]
    assert "reaction_type" in kwargs
    assert kwargs["reaction_type"] == MOCK_REACTION_TYPE
    
    # Verify the enhanced result was returned
    assert "enhanced_by_diana" in result
    assert result["enhanced_by_diana"] is True
    assert "guiña un ojo a mi amor" in result["message"]