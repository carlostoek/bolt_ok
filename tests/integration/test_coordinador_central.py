"""
Tests para el CoordinadorCentral.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mybot.services.coordinador_central import CoordinadorCentral, AccionUsuario

@pytest.mark.asyncio
async def test_flujo_reaccion_publicacion_exitoso():
    """Test del flujo de reacción a publicación exitoso."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock de servicios
    coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
    coordinador.point_service.get_user_points = AsyncMock(return_value=65)
    coordinador.narrative_service.get_user_current_fragment = AsyncMock()
    fragment_mock = MagicMock()
    fragment_mock.key = "level2_test"
    coordinador.narrative_service.get_user_current_fragment.return_value = fragment_mock
    
    # Test
    result = await coordinador.ejecutar_flujo(
        123,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=456,
        channel_id=789,
        reaction_type="like"
    )
    
    # Assert
    assert result["success"] is True
    assert "message" in result
    assert "hint_unlocked" in result
    assert result["points_awarded"] == 10
    coordinador.channel_engagement.award_channel_reaction.assert_called_once()

@pytest.mark.asyncio
async def test_flujo_acceso_narrativa_vip_denegado():
    """Test del flujo de acceso a narrativa VIP denegado."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock de servicios
    coordinador.narrative_access.get_accessible_fragment = AsyncMock(return_value={
        "type": "subscription_required",
        "message": "Este contenido requiere una suscripción VIP activa.",
        "requested_fragment": "level4_test"
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        123,
        AccionUsuario.ACCEDER_NARRATIVA_VIP,
        fragment_key="level4_test"
    )
    
    # Assert
    assert result["success"] is False
    assert "message" in result
    assert result["action"] == "vip_required"
    coordinador.narrative_access.get_accessible_fragment.assert_called_once()

@pytest.mark.asyncio
async def test_flujo_tomar_decision_puntos_insuficientes():
    """Test del flujo de tomar decisión con puntos insuficientes."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock de servicios
    coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
        "type": "points_required",
        "message": "No tienes suficientes puntos para esta decisión.",
        "decision_id": 456
    })
    
    # Test
    result = await coordinador.ejecutar_flujo(
        123,
        AccionUsuario.TOMAR_DECISION,
        decision_id=456
    )
    
    # Assert
    assert result["success"] is False
    assert "message" in result
    assert result["action"] == "points_required"
    coordinador.narrative_point.process_decision_with_points.assert_called_once()

@pytest.mark.asyncio
async def test_flujo_verificar_engagement_exitoso():
    """Test del flujo de verificación de engagement diario exitoso."""
    # Setup
    session_mock = AsyncMock()
    coordinador = CoordinadorCentral(session_mock)
    
    # Mock de servicios
    coordinador.channel_engagement.check_daily_engagement = AsyncMock(return_value=True)
    
    progress_mock = MagicMock()
    progress_mock.checkin_streak = 7
    coordinador.point_service.get_user_progress = AsyncMock(return_value=progress_mock)
    
    # Test
    result = await coordinador.ejecutar_flujo(
        123,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Assert
    assert result["success"] is True
    assert "message" in result
    assert result["streak"] == 7
    assert result["points_awarded"] == 25  # Bonus semanal
    coordinador.channel_engagement.check_daily_engagement.assert_called_once()
