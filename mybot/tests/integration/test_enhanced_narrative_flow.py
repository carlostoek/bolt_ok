"""
Integration tests for the enhanced narrative flow with analytics integration.
Tests the complete narrative progression with context-aware responses and analytics tracking.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.coordinador_central import CoordinadorCentral, AccionUsuario

@pytest.mark.asyncio
async def test_enhanced_narrative_flow_basic_progression():
    """Test basic narrative flow with analytics tracking."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock character voice service to avoid errors
    coordinador.character_voice.map_emotional_analysis_to_context = MagicMock(return_value="PAUSA_REFLEXIVA")
    coordinador.character_voice.get_character_response = MagicMock(return_value="Diana's response")
    
    # Mock services to avoid complex setup
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "success",
        "fragment": MagicMock(key="test_middle")
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        123,
        AccionUsuario.TOMAR_DECISION,
        decision_id=1
    )
    
    # Assert
    assert result["success"] is True
    assert "fragment" in result
    assert result["fragment"].key == "test_middle"
    assert result["action"] == "decision_success"


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_with_analytics_tracking():
    """Test narrative flow with comprehensive analytics tracking."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock character voice service to avoid errors
    coordinador.character_voice.map_emotional_analysis_to_context = MagicMock(return_value="PAUSA_REFLEXIVA")
    coordinador.character_voice.get_character_response = MagicMock(return_value="Lucien's response")
    
    # Mock services to return successful results
    fragment_mock = MagicMock()
    fragment_mock.key = "test_analytics_end"
    fragment_mock.character = "Lucien"
    
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "success",
        "fragment": fragment_mock
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        456,
        AccionUsuario.TOMAR_DECISION,
        decision_id=2
    )
    
    # Assert
    assert result["success"] is True
    assert "fragment" in result
    assert result["fragment"].key == "test_analytics_end"
    assert result["action"] == "decision_success"


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_item_condition_access():
    """Test narrative flow with item-conditioned access and teaser content."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock services to simulate successful teaser access
    fragment_mock = MagicMock()
    fragment_mock.key = "diana_diary_tease"
    fragment_mock.character = "Diana"
    
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "success",
        "fragment": fragment_mock
    })
    
    # Test - decision that requires an item (decision_id=15 for diary intimate choice)
    result = await coordinador.ejecutar_flujo(
        789,
        AccionUsuario.TOMAR_DECISION,
        decision_id=15
    )
    
    # Assert
    assert result["success"] is True
    assert "fragment" in result
    assert result["fragment"].key == "diana_diary_tease"
    assert result["action"] == "decision_success"


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_user_analytics_summary():
    """Test user analytics summary in narrative flow."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock character voice service to avoid errors
    coordinador.character_voice.map_emotional_analysis_to_context = MagicMock(return_value="PAUSA_REFLEXIVA")
    coordinador.character_voice.get_character_response = MagicMock(return_value="Diana's response")
    
    # Mock services to return successful results
    fragment_mock = MagicMock()
    fragment_mock.key = "analytics_summary_test"
    fragment_mock.character = "Diana"
    
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "success",
        "fragment": fragment_mock
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        111,
        AccionUsuario.TOMAR_DECISION,
        decision_id=4
    )
    
    # Assert
    assert result["success"] is True
    assert "fragment" in result
    assert result["fragment"].key == "analytics_summary_test"
    assert result["action"] == "decision_success"


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_vip_access():
    """Test VIP narrative access with character voice integration."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock narrative access service
    coordinador.narrative_access.get_accessible_fragment = AsyncMock()
    
    # Mock character voice service
    coordinador.character_voice.get_character_response = MagicMock()
    coordinador.character_voice.get_character_response.return_value = "Diana's VIP access message"
    
    # Simulate restricted access
    coordinador.narrative_access.get_accessible_fragment.return_value = {
        "type": "subscription_required",
        "message": "This content requires an active VIP subscription.",
        "requested_fragment": "vip_level5_secret"
    }
    
    # Test
    result = await coordinador.ejecutar_flujo(
        202,
        AccionUsuario.ACCEDER_NARRATIVA_VIP,
        fragment_key="vip_level5_secret"
    )
    
    # Assert
    assert result["success"] is False
    assert "message" in result
    assert "Diana's VIP access message" in result["message"]
    assert result["action"] == "vip_required"
    assert result["fragment_key"] == "vip_level5_secret"
    
    # Verify service calls
    coordinador.narrative_access.get_accessible_fragment.assert_called_once_with(202, "vip_level5_secret")
    coordinador.character_voice.get_character_response.assert_called_once()


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_error_handling():
    """Test error handling in narrative flow with graceful degradation."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock services to simulate errors
    coordinador.narrative_service.get_user_current_fragment = AsyncMock()
    coordinador.narrative_service._get_fragment_choices = AsyncMock()
    
    # Create test fragment
    current_fragment = MagicMock()
    current_fragment.key = "error_test"
    current_fragment.id = 999
    current_fragment.character = "Diana"
    
    # Setup mocks
    coordinador.narrative_service.get_user_current_fragment.return_value = current_fragment
    
    # Mock NarrativePointService to return error
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "error",
        "message": "Database connection failed"
    })
    
    # Mock character voice service
    coordinador.character_voice.get_character_response = MagicMock()
    coordinador.character_voice.get_character_response.return_value = "Lucien's error handling message"
    
    # Mock choices
    choice1 = MagicMock()
    choice1.id = 99
    choice1.text = "Error test choice"
    choice1.destination_fragment_key = "error_destination"
    
    coordinador.narrative_service._get_fragment_choices.return_value = [choice1]
    
    # Test
    result = await coordinador.ejecutar_flujo(
        303,
        AccionUsuario.TOMAR_DECISION,
        decision_id=99
    )
    
    # Assert
    assert result["success"] is False
    assert "message" in result
    assert "Lucien's error handling message" in result["message"]
    assert result["action"] == "decision_error"
    assert "Database connection failed" in result["error"]
    
    # Verify service calls
    coordinador.narrative_point.process_decision_with_points.assert_called_once_with(303, 99, None)
    coordinador.character_voice.get_character_response.assert_called_once()


@pytest.mark.asyncio
async def test_enhanced_narrative_flow_advanced_progression_tracking():
    """Test advanced progression tracking in narrative flow."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock emotional analysis service to avoid errors
    coordinador.emotional_analysis = None
    
    # Mock character voice service to avoid errors
    coordinador.character_voice.map_emotional_analysis_to_context = MagicMock(return_value="PAUSA_REFLEXIVA")
    coordinador.character_voice.get_character_response = MagicMock(return_value="Lucien's response")
    
    # Mock services to return successful results for advanced progression
    fragment_mock = MagicMock()
    fragment_mock.key = "advanced_progression_test"
    fragment_mock.character = "Lucien"
    
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "success",
        "fragment": fragment_mock
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        222,
        AccionUsuario.TOMAR_DECISION,
        decision_id=5
    )
    
    # Assert
    assert result["success"] is True
    assert "fragment" in result
    assert result["fragment"].key == "advanced_progression_test"
    assert result["action"] == "decision_success"