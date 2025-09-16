"""
Integration tests for enhanced narrative flow functionality.
Tests interaction between narrative service, shop integration, and user progression.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import asyncio

@pytest.fixture
def mock_narrative_service():
    """Mock narrative service for integration testing."""
    service = AsyncMock()
    service.get_user_current_fragment = AsyncMock()
    service.set_user_current_fragment = AsyncMock()
    service.process_narrative_choice = AsyncMock()
    return service

@pytest.fixture
def mock_shop_service():
    """Mock shop service for integration testing."""
    service = AsyncMock()
    service.has_item_in_inventory = AsyncMock(return_value=False)
    service.purchase_item = AsyncMock()
    return service

@pytest.fixture
def mock_character_voice_service():
    """Mock character voice service for integration testing."""
    service = AsyncMock()
    service.get_character_response = AsyncMock(return_value={
        "text": "Mock character response",
        "emotional_tone": "neutral"
    })
    return service

@pytest.fixture
def mock_coordinador_central(mock_narrative_service, mock_shop_service, mock_character_voice_service):
    """Mock coordinador central with injected services."""
    coordinador = AsyncMock()
    coordinador.narrative_service = mock_narrative_service
    coordinador.shop_service = mock_shop_service
    coordinador.character_voice_service = mock_character_voice_service
    coordinador.ejecutar_flujo = AsyncMock()
    return coordinador

@pytest.mark.asyncio
async def test_narrative_progression_integration(mock_coordinador_central, mock_narrative_service):
    """Test integrated narrative progression flow."""
    # Setup mock responses
    mock_narrative_service.get_user_current_fragment.return_value = MagicMock(
        key="TEST_FRAGMENT_1",
        choices=[{"text": "Continue", "destination_key": "TEST_FRAGMENT_2"}]
    )
    
    mock_coordinador_central.ejecutar_flujo.return_value = {
        "success": True,
        "next_fragment": "TEST_FRAGMENT_2",
        "message": "Progression successful"
    }
    
    # Execute narrative flow
    result = await mock_coordinador_central.ejecutar_flujo(
        user_id=123,
        accion="narrative_choice",
        choice_index=0,
        current_fragment_key="TEST_FRAGMENT_1"
    )
    
    # Verify integration
    assert result["success"] is True
    assert result["next_fragment"] == "TEST_FRAGMENT_2"
    mock_coordinador_central.ejecutar_flujo.assert_called_once()

@pytest.mark.asyncio
async def test_item_restricted_narrative_access(mock_coordinador_central, mock_shop_service, mock_narrative_service):
    """Test narrative access with item restrictions."""
    # Setup item restriction scenario
    mock_narrative_service.get_user_current_fragment.return_value = MagicMock(
        key="RESTRICTED_FRAGMENT",
        required_item="SPECIAL_KEY",
        choices=[{"text": "Unlock", "destination_key": "SECRET_CONTENT"}]
    )
    
    # First attempt without item (should fail)
    mock_shop_service.has_item_in_inventory.return_value = False
    mock_coordinador_central.ejecutar_flujo.return_value = {
        "success": False,
        "message": "Item required: SPECIAL_KEY",
        "teaser": "This content is locked behind a special item..."
    }
    
    result = await mock_coordinador_central.ejecutar_flujo(
        user_id=123,
        accion="narrative_choice",
        choice_index=0,
        current_fragment_key="RESTRICTED_FRAGMENT"
    )
    
    assert not result["success"]
    assert "Item required" in result["message"]
    
    # Second attempt with item (should succeed)
    mock_shop_service.has_item_in_inventory.return_value = True
    mock_coordinador_central.ejecutar_flujo.return_value = {
        "success": True,
        "next_fragment": "SECRET_CONTENT",
        "message": "Access granted!"
    }
    
    result = await mock_coordinador_central.ejecutar_flujo(
        user_id=123,
        accion="narrative_choice",
        choice_index=0,
        current_fragment_key="RESTRICTED_FRAGMENT"
    )
    
    assert result["success"]
    assert result["next_fragment"] == "SECRET_CONTENT"

@pytest.mark.asyncio
async def test_character_voice_integration_with_narrative(mock_coordinador_central, mock_character_voice_service):
    """Test character voice integration in narrative responses."""
    # Setup character response
    mock_character_voice_service.get_character_response.return_value = {
        "text": "Diana's personalized response based on your journey",
        "emotional_tone": "intimate",
        "vulnerability_level": 0.7
    }
    
    mock_coordinador_central.ejecutar_flujo.return_value = {
        "success": True,
        "character_response": "Diana's personalized response based on your journey",
        "emotional_context": {"tone": "intimate", "vulnerability": 0.7}
    }
    
    result = await mock_coordinador_central.ejecutar_flujo(
        user_id=123,
        accion="character_interaction",
        character="Diana",
        context={"user_progress": "advanced", "emotional_state": "engaged"}
    )
    
    assert result["success"]
    assert "Diana's personalized" in result["character_response"]
    mock_character_voice_service.get_character_response.assert_called_once()

@pytest.mark.asyncio
async def test_narrative_choice_analytics_tracking(mock_coordinador_central, mock_narrative_service):
    """Test that narrative choices are tracked for analytics."""
    mock_narrative_service.process_narrative_choice.return_value = {
        "choice_made": "option_a",
        "timestamp": datetime.utcnow(),
        "user_id": 123,
        "fragment_key": "TEST_FRAGMENT",
        "analytics_data": {
            "choice_pattern": "exploratory",
            "time_taken": 15.2,
            "emotional_response": "positive"
        }
    }
    
    result = await mock_narrative_service.process_narrative_choice(
        user_id=123,
        fragment_key="TEST_FRAGMENT",
        choice_index=0,
        choice_data={"option": "option_a"}
    )
    
    assert "analytics_data" in result
    assert result["choice_made"] == "option_a"
    mock_narrative_service.process_narrative_choice.assert_called_once()

@pytest.mark.asyncio
async def test_user_archetype_adaptation_in_narrative(mock_coordinador_central, mock_narrative_service):
    """Test narrative adaptation based on user archetype."""
    # Mock different responses based on archetype
    archetype_responses = {
        "explorer_deep": {
            "text": "For curious minds like yours, there's always more to discover...",
            "complexity": "high"
        },
        "direct_authentic": {
            "text": "I appreciate your directness. Here's what you need to know...",
            "complexity": "medium"
        }
    }
    
    mock_narrative_service.get_archetype_adapted_content = AsyncMock(
        side_effect=lambda user_id, fragment_key, archetype: archetype_responses.get(archetype, {})
    )
    
    # Test for explorer archetype
    explorer_response = await mock_narrative_service.get_archetype_adapted_content(
        user_id=123,
        fragment_key="ADAPTIVE_FRAGMENT",
        archetype="explorer_deep"
    )
    
    assert "curious minds" in explorer_response["text"]
    assert explorer_response["complexity"] == "high"
    
    # Test for direct archetype
    direct_response = await mock_narrative_service.get_archetype_adapted_content(
        user_id=123,
        fragment_key="ADAPTIVE_FRAGMENT",
        archetype="direct_authentic"
    )
    
    assert "directness" in direct_response["text"]
    assert direct_response["complexity"] == "medium"

# Test scenarios for different user behavior patterns
@pytest.mark.parametrize("user_archetype,expected_pattern", [
    ("explorer_deep", "exploratory"),
    ("direct_authentic", "direct"),
    ("poet_desire", "emotional"),
    ("analytic_empathic", "analytical"),
    ("persistent_patient", "patient")
])
@pytest.mark.asyncio
async def test_archetype_based_narrative_patterns(user_archetype, expected_pattern, mock_narrative_service):
    """Test narrative patterns adapt to different user archetypes."""
    mock_narrative_service.analyze_choice_pattern = AsyncMock(return_value=expected_pattern)
    
    pattern = await mock_narrative_service.analyze_choice_pattern(
        user_id=123,
        archetype=user_archetype,
        choice_history=[{"choice": "option_a", "time_taken": 10.5}]
    )
    
    assert pattern == expected_pattern
    mock_narrative_service.analyze_choice_pattern.assert_called_once()
