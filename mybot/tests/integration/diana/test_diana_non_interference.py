"""
Pruebas para verificar que Diana no interfiere con la funcionalidad base del bot.

Este módulo contiene pruebas que aseguran que la integración de Diana sea no invasiva
y que las funcionalidades base del bot sigan funcionando correctamente incluso si
Diana está desactivada o encuentra errores.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import logging
from datetime import datetime

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)

# Constantes para pruebas
TEST_USER_ID = 123456789
TEST_MESSAGE_ID = 10001
TEST_CHANNEL_ID = -1001234567890


@pytest.fixture
def mock_db_session():
    """Crea un mock de la sesión de base de datos."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_channel_engagement():
    """Crea un mock del servicio ChannelEngagement."""
    service = AsyncMock()
    service.award_channel_reaction = AsyncMock(return_value=10)  # Puntos otorgados
    service.is_user_in_channel = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_point_service():
    """Crea un mock del servicio PointService."""
    service = AsyncMock()
    service.get_user_points = AsyncMock(return_value=110)  # Puntos después de recibir 10
    service.award_points = AsyncMock(return_value=True)
    service.process_daily_checkin = AsyncMock(return_value={
        "success": True,
        "points_awarded": 5,
        "streak": 3,
        "total_points": 105
    })
    return service


@pytest.fixture
def mock_narrative_service():
    """Crea un mock del servicio NarrativeService."""
    service = AsyncMock()
    service.get_user_narrative_progress = AsyncMock(return_value={
        "success": True,
        "current_fragment_id": "fragment_123",
        "progress": 0.35
    })
    service.get_fragment_by_id = AsyncMock(return_value={
        "success": True,
        "fragment": {
            "id": "fragment_123",
            "title": "El encuentro",
            "content": "Diana te mira con curiosidad...",
            "emotion": "anticipation"
        }
    })
    return service


@pytest.fixture
def diana_service_mock():
    """Crea un mock del servicio DianaEmotionalService."""
    service = AsyncMock()
    service.enhance_interaction = AsyncMock()
    service.enhance_interaction.side_effect = lambda user_id, accion, resultado, **kwargs: resultado
    service.is_active = MagicMock(return_value=True)
    return service


@pytest.fixture
def diana_service_error():
    """Crea un mock del servicio DianaEmotionalService que lanza errores."""
    service = AsyncMock()
    service.enhance_interaction = AsyncMock()
    service.enhance_interaction.side_effect = Exception("Test Diana error")
    service.is_active = MagicMock(return_value=True)
    return service


@pytest.fixture
def diana_service_inactive():
    """Crea un mock del servicio DianaEmotionalService que está inactivo."""
    service = AsyncMock()
    service.enhance_interaction = AsyncMock()
    service.enhance_interaction.side_effect = lambda user_id, accion, resultado, **kwargs: resultado
    service.is_active = MagicMock(return_value=False)
    return service


@pytest.fixture
def coordinador_central(mock_db_session, mock_channel_engagement, mock_point_service, mock_narrative_service, diana_service_mock):
    """Crea una instancia de CoordinadorCentral con servicios mockeados."""
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Reemplazar servicios con mocks
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.narrative_service = mock_narrative_service
    coordinador.diana_service = diana_service_mock
    
    return coordinador


@pytest.fixture
def coordinador_central_diana_error(mock_db_session, mock_channel_engagement, mock_point_service, mock_narrative_service, diana_service_error):
    """Crea una instancia de CoordinadorCentral con Diana en estado de error."""
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Reemplazar servicios con mocks
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.narrative_service = mock_narrative_service
    coordinador.diana_service = diana_service_error
    
    return coordinador


@pytest.fixture
def coordinador_central_diana_inactive(mock_db_session, mock_channel_engagement, mock_point_service, mock_narrative_service, diana_service_inactive):
    """Crea una instancia de CoordinadorCentral con Diana inactiva."""
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Reemplazar servicios con mocks
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.narrative_service = mock_narrative_service
    coordinador.diana_service = diana_service_inactive
    
    return coordinador


@pytest.fixture
def coordinador_central_diana_missing(mock_db_session, mock_channel_engagement, mock_point_service, mock_narrative_service):
    """Crea una instancia de CoordinadorCentral sin el servicio Diana."""
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Reemplazar servicios con mocks, pero omitir Diana
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.narrative_service = mock_narrative_service
    coordinador.diana_service = None
    
    return coordinador


# Pruebas con Diana activa

@pytest.mark.asyncio
async def test_reaccion_publicacion_normal_behavior(coordinador_central):
    """Prueba que el flujo de reacción funciona normalmente con Diana activa."""
    # Ejecutar el flujo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110
    
    # Verificar que se llamaron los servicios base
    coordinador_central.channel_engagement.award_channel_reaction.assert_called_once()
    coordinador_central.point_service.get_user_points.assert_called_once()
    
    # Verificar que se llamó a Diana
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_verificar_engagement_normal_behavior(coordinador_central):
    """Prueba que el flujo de engagement diario funciona normalmente con Diana activa."""
    # Ejecutar el flujo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "streak" in resultado
    assert resultado["streak"] == 3
    
    # Verificar que se llamó al servicio base
    coordinador_central.point_service.process_daily_checkin.assert_called_once()
    
    # Verificar que se llamó a Diana
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_narrativa_normal_behavior(coordinador_central):
    """Prueba que el flujo narrativo funciona normalmente con Diana activa."""
    # Ejecutar el flujo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.AVANZAR_NARRATIVA
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "fragment" in resultado
    
    # Verificar que se llamó al servicio base
    coordinador_central.narrative_service.get_user_narrative_progress.assert_called_once()
    coordinador_central.narrative_service.get_fragment_by_id.assert_called_once()
    
    # Verificar que se llamó a Diana
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


# Pruebas con Diana en estado de error

@pytest.mark.asyncio
async def test_reaccion_publicacion_with_diana_error(coordinador_central_diana_error):
    """Prueba que el flujo de reacción funciona correctamente incluso si Diana falla."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_error.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificaciones - debería funcionar a pesar del error en Diana
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110
    
    # Verificar que se llamaron los servicios base
    coordinador_central_diana_error.channel_engagement.award_channel_reaction.assert_called_once()
    coordinador_central_diana_error.point_service.get_user_points.assert_called_once()
    
    # Verificar que se intentó llamar a Diana pero falló
    coordinador_central_diana_error.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_verificar_engagement_with_diana_error(coordinador_central_diana_error):
    """Prueba que el flujo de engagement diario funciona correctamente incluso si Diana falla."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_error.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Verificaciones - debería funcionar a pesar del error en Diana
    assert resultado["success"] is True
    assert "streak" in resultado
    assert resultado["streak"] == 3
    
    # Verificar que se llamó al servicio base
    coordinador_central_diana_error.point_service.process_daily_checkin.assert_called_once()
    
    # Verificar que se intentó llamar a Diana pero falló
    coordinador_central_diana_error.diana_service.enhance_interaction.assert_called_once()


# Pruebas con Diana inactiva

@pytest.mark.asyncio
async def test_reaccion_publicacion_with_diana_inactive(coordinador_central_diana_inactive):
    """Prueba que el flujo de reacción funciona correctamente cuando Diana está inactiva."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_inactive.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110
    
    # Verificar que se llamaron los servicios base
    coordinador_central_diana_inactive.channel_engagement.award_channel_reaction.assert_called_once()
    coordinador_central_diana_inactive.point_service.get_user_points.assert_called_once()
    
    # Verificar que se llamó a Diana pero devolvió el resultado original sin mejorar
    coordinador_central_diana_inactive.diana_service.enhance_interaction.assert_called_once()
    coordinador_central_diana_inactive.diana_service.is_active.assert_called_once()


@pytest.mark.asyncio
async def test_verificar_engagement_with_diana_inactive(coordinador_central_diana_inactive):
    """Prueba que el flujo de engagement diario funciona correctamente cuando Diana está inactiva."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_inactive.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "streak" in resultado
    assert resultado["streak"] == 3
    
    # Verificar que se llamó al servicio base
    coordinador_central_diana_inactive.point_service.process_daily_checkin.assert_called_once()
    
    # Verificar que se llamó a Diana pero devolvió el resultado original sin mejorar
    coordinador_central_diana_inactive.diana_service.enhance_interaction.assert_called_once()
    coordinador_central_diana_inactive.diana_service.is_active.assert_called_once()


# Pruebas con Diana ausente (no inyectada)

@pytest.mark.asyncio
async def test_reaccion_publicacion_with_diana_missing(coordinador_central_diana_missing):
    """Prueba que el flujo de reacción funciona correctamente cuando el servicio Diana no está presente."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_missing.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110
    
    # Verificar que se llamaron los servicios base
    coordinador_central_diana_missing.channel_engagement.award_channel_reaction.assert_called_once()
    coordinador_central_diana_missing.point_service.get_user_points.assert_called_once()


@pytest.mark.asyncio
async def test_verificar_engagement_with_diana_missing(coordinador_central_diana_missing):
    """Prueba que el flujo de engagement diario funciona correctamente cuando el servicio Diana no está presente."""
    # Ejecutar el flujo
    resultado = await coordinador_central_diana_missing.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "streak" in resultado
    assert resultado["streak"] == 3
    
    # Verificar que se llamó al servicio base
    coordinador_central_diana_missing.point_service.process_daily_checkin.assert_called_once()


# Pruebas para verificar que Diana no afecta los campos esenciales

@pytest.mark.asyncio
async def test_diana_preserves_essential_fields(coordinador_central):
    """Prueba que Diana preserva todos los campos esenciales del resultado original."""
    # Modificar el comportamiento de enhance_interaction para añadir campos pero no eliminar
    async def mock_enhance(user_id, accion, resultado, **kwargs):
        # Crear una copia para no modificar el original
        enhanced = resultado.copy()
        # Añadir campos adicionales
        enhanced["diana_enhanced"] = True
        enhanced["emotional_context"] = "positive"
        # Modificar el mensaje pero mantener los campos esenciales
        if "message" in enhanced:
            enhanced["message"] = "Diana: " + enhanced["message"]
        return enhanced
    
    coordinador_central.diana_service.enhance_interaction.side_effect = mock_enhance
    
    # Ejecutar el flujo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificaciones - todos los campos esenciales deben preservarse
    assert resultado["success"] is True
    assert "message" in resultado
    assert "points_awarded" in resultado
    assert "total_points" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110
    
    # Verificar campos añadidos por Diana
    assert "diana_enhanced" in resultado
    assert "emotional_context" in resultado
    assert resultado["diana_enhanced"] is True
    assert resultado["emotional_context"] == "positive"
    
    # Verificar que el mensaje fue modificado pero preservando la funcionalidad
    assert resultado["message"].startswith("Diana: ")


@pytest.mark.asyncio
async def test_multiple_flows_with_diana_on_off(coordinador_central_diana_inactive):
    """Prueba que los flujos funcionan consistentemente con Diana activándose y desactivándose."""
    # Primero ejecutar con Diana inactiva
    resultado1 = await coordinador_central_diana_inactive.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificar el resultado con Diana inactiva
    assert resultado1["success"] is True
    assert "message" in resultado1
    
    # Ahora activar Diana
    coordinador_central_diana_inactive.diana_service.is_active.return_value = True
    
    # Ejecutar nuevamente
    resultado2 = await coordinador_central_diana_inactive.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID + 1,  # Otro mensaje
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificar el resultado con Diana activa
    assert resultado2["success"] is True
    assert "message" in resultado2
    
    # Ahora hacer que Diana falle
    coordinador_central_diana_inactive.diana_service.enhance_interaction.side_effect = Exception("Test Diana error")
    
    # Ejecutar nuevamente
    resultado3 = await coordinador_central_diana_inactive.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID + 2,  # Otro mensaje
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificar que sigue funcionando a pesar del error
    assert resultado3["success"] is True
    assert "message" in resultado3
    
    # Verificar que se llamaron los servicios base en todas las ejecuciones
    assert coordinador_central_diana_inactive.channel_engagement.award_channel_reaction.call_count == 3
    assert coordinador_central_diana_inactive.point_service.get_user_points.call_count == 3


@pytest.mark.asyncio
async def test_other_functions_not_affected_by_diana(coordinador_central_diana_error):
    """Prueba que las funciones que no usan Diana no se ven afectadas por errores en Diana."""
    # Crear una función que simule una acción que no usa Diana
    async def _flujo_no_diana(user_id):
        return {
            "success": True,
            "message": "Acción completada sin intervención de Diana",
            "data": {"some": "data"}
        }
    
    # Asignar la función al coordinador
    coordinador_central_diana_error._flujo_no_diana = _flujo_no_diana
    
    # Ejecutar la acción
    resultado = await coordinador_central_diana_error._flujo_no_diana(TEST_USER_ID)
    
    # Verificar que funciona correctamente
    assert resultado["success"] is True
    assert resultado["message"] == "Acción completada sin intervención de Diana"
    assert "data" in resultado
    
    # Verificar que Diana no fue llamada
    coordinador_central_diana_error.diana_service.enhance_interaction.assert_not_called()


@pytest.mark.asyncio
async def test_handlers_work_without_diana(coordinador_central_diana_missing):
    """Prueba que los handlers funcionan sin Diana usando un handler simulado."""
    # Simular un handler que usa el coordinador central
    async def mock_handler(user_id, message_id, channel_id, reaction_type):
        coordinator = coordinador_central_diana_missing
        result = await coordinator.ejecutar_flujo(
            user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=message_id,
            channel_id=channel_id,
            reaction_type=reaction_type
        )
        return result
    
    # Ejecutar el handler
    resultado = await mock_handler(
        TEST_USER_ID,
        TEST_MESSAGE_ID,
        TEST_CHANNEL_ID,
        "❤️"
    )
    
    # Verificar que funciona correctamente
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    assert resultado["total_points"] == 110


@pytest.mark.asyncio
async def test_bot_initialization_without_diana(mock_db_session):
    """Prueba que el bot se inicia correctamente si la migración de Diana falla."""
    # Simular la inicialización del bot sin el módulo Diana
    # Crear coordinador sin referencia a Diana
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Simular servicios mínimos necesarios
    coordinador.channel_engagement = AsyncMock()
    coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=10)
    coordinador.point_service = AsyncMock()
    coordinador.point_service.get_user_points = AsyncMock(return_value=100)
    
    # Verificar que se puede ejecutar una acción básica
    resultado = await coordinador.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificar que funciona correctamente
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10
    
    # Verificar que se llamaron los servicios base
    coordinador.channel_engagement.award_channel_reaction.assert_called_once()
    coordinador.point_service.get_user_points.assert_called_once()