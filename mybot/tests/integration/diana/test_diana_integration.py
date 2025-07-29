"""
Pruebas de integración para Diana con el Coordinador Central.

Este módulo contiene pruebas que verifican la correcta integración de Diana
con el coordinador central y otros componentes del sistema.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from datetime import datetime

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    DianaEmotionalMemory,
    DianaRelationshipState,
    DianaPersonalityAdaptation,
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)
from database.models import User

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
    
    # Configurar comportamiento básico para las consultas
    async def mock_execute(query):
        # Devolver resultados basados en el tipo de consulta
        mock_result = AsyncMock()
        
        # Simular búsqueda de usuario
        if "User" in str(query):
            mock_result.scalar_one_or_none.return_value = MagicMock(spec=User)
            mock_result.scalar_one_or_none.return_value.id = TEST_USER_ID
            mock_result.scalar_one_or_none.return_value.points = 100
            
        # Simular búsqueda de relación
        elif "DianaRelationshipState" in str(query):
            mock_result.scalar_one_or_none.return_value = None  # Por defecto, sin relación
            
        # Simular búsqueda de adaptación
        elif "DianaPersonalityAdaptation" in str(query):
            mock_result.scalar_one_or_none.return_value = None  # Por defecto, sin adaptación
            
        return mock_result
    
    session.execute.side_effect = mock_execute
    return session


@pytest.fixture
def mock_channel_engagement():
    """Crea un mock del servicio ChannelEngagement."""
    service = AsyncMock()
    service.award_channel_reaction.return_value = 10  # Puntos otorgados
    service.is_user_in_channel.return_value = True
    return service


@pytest.fixture
def mock_point_service():
    """Crea un mock del servicio PointService."""
    service = AsyncMock()
    service.get_user_points.return_value = 110  # Puntos después de recibir 10
    service.award_points.return_value = True
    return service


@pytest.fixture
def diana_service(mock_db_session):
    """Crea una instancia real del servicio de Diana con sesión mockeada."""
    service = DianaEmotionalService(mock_db_session)
    
    # Sobreescribir algunos métodos para evitar accesos reales a la BD
    service._create_default_relationship_state = AsyncMock()
    service._create_default_relationship_state.return_value = MagicMock(spec=DianaRelationshipState)
    service._create_default_relationship_state.return_value.user_id = TEST_USER_ID
    service._create_default_relationship_state.return_value.status = RelationshipStatus.INITIAL
    service._create_default_relationship_state.return_value.trust_level = 0.1
    
    service._create_default_personality_adaptation = AsyncMock()
    service._create_default_personality_adaptation.return_value = MagicMock(spec=DianaPersonalityAdaptation)
    service._create_default_personality_adaptation.return_value.user_id = TEST_USER_ID
    service._create_default_personality_adaptation.return_value.warmth = 0.5
    
    # Patch para método que depende de una entrada específica del usuario
    service._get_user_emotional_context = AsyncMock()
    service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    service._get_contextual_memory_reference = AsyncMock()
    service._get_contextual_memory_reference.return_value = ""
    
    # Asegurarse de que Diana esté activa
    service.is_active = MagicMock(return_value=True)
    
    return service


@pytest.fixture
def coordinador_central(mock_db_session, mock_channel_engagement, mock_point_service, diana_service):
    """Crea una instancia de CoordinadorCentral con servicios mockeados."""
    coordinador = CoordinadorCentral(mock_db_session)
    
    # Reemplazar servicios con mocks
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.diana_service = diana_service
    
    return coordinador


@pytest.mark.asyncio
async def test_reaccion_publicacion_with_diana(coordinador_central):
    """Prueba la integración de Diana en el flujo de reacción a publicación."""
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
    
    # Verificar que Diana haya mejorado el mensaje (debe ser diferente al predeterminado)
    assert "Diana" in resultado["message"]  # El mensaje debe contener Diana
    assert "*+10 besitos* 💋" in resultado["message"]  # Debe mantener los puntos
    
    # Verificar que se llamaron los métodos del servicio de Diana
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_reaccion_publicacion_with_diana_inactive(coordinador_central):
    """Prueba que el flujo de reacción funciona cuando Diana está inactiva."""
    # Configurar Diana como inactiva
    coordinador_central.diana_service.is_active = MagicMock(return_value=False)
    
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
    
    # El mensaje no debería tener mejoras personalizadas de Diana
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_verificar_engagement_with_diana(coordinador_central):
    """Prueba la integración de Diana en el flujo de verificación de engagement."""
    # Configurar el point_service para el caso de verificación de engagement
    coordinador_central.point_service.process_daily_checkin = AsyncMock()
    coordinador_central.point_service.process_daily_checkin.return_value = {
        "success": True,
        "points_awarded": 5,
        "streak": 3,
        "total_points": 105
    }
    
    # Ejecutar el flujo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    # Verificaciones
    assert resultado["success"] is True
    assert "message" in resultado
    assert "streak" in resultado
    assert resultado["streak"] == 3
    
    # Verificar que Diana intentó mejorar el mensaje
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_diana_enhance_interaction_functionality(coordinador_central):
    """Prueba directamente la funcionalidad enhance_interaction de Diana."""
    # Resultado original a mejorar
    resultado_original = {
        "success": True,
        "message": "Mensaje original sin personalización",
        "points_awarded": 10,
        "total_points": 100
    }
    
    # Llamar directamente al método
    resultado_mejorado = await coordinador_central.diana_service.enhance_interaction(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        resultado_original,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert resultado_mejorado["success"] is True
    assert "message" in resultado_mejorado
    assert resultado_mejorado["message"] != resultado_original["message"]
    
    # Verificar que se llamaron los métodos necesarios
    coordinador_central.diana_service.get_relationship_state.assert_called_once()
    coordinador_central.diana_service.get_personality_adaptation.assert_called_once()
    coordinador_central.diana_service.record_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_diana_enhance_interaction_with_error_handling(coordinador_central):
    """Prueba el manejo de errores en enhance_interaction de Diana."""
    # Resultado original a mejorar
    resultado_original = {
        "success": True,
        "message": "Mensaje original sin personalización",
        "points_awarded": 10,
        "total_points": 100
    }
    
    # Hacer que get_relationship_state lance una excepción
    coordinador_central.diana_service.get_relationship_state = AsyncMock()
    coordinador_central.diana_service.get_relationship_state.side_effect = Exception("Test error")
    
    # Llamar directamente al método
    resultado_mejorado = await coordinador_central.diana_service.enhance_interaction(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        resultado_original,
        reaction_type="❤️"
    )
    
    # Verificar que devuelve el resultado original cuando hay error
    assert resultado_mejorado == resultado_original


@pytest.mark.asyncio
async def test_complex_integration_flow(coordinador_central):
    """Prueba un flujo más complejo con múltiples acciones e interacciones."""
    # 1. Primera interacción: reacción a publicación
    resultado1 = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    assert resultado1["success"] is True
    
    # 2. Segunda interacción: verificación de engagement
    coordinador_central.point_service.process_daily_checkin = AsyncMock()
    coordinador_central.point_service.process_daily_checkin.return_value = {
        "success": True,
        "points_awarded": 5,
        "streak": 1,
        "total_points": 115
    }
    
    resultado2 = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.VERIFICAR_ENGAGEMENT
    )
    
    assert resultado2["success"] is True
    
    # Verificar que se llamó enhance_interaction para ambas acciones
    assert coordinador_central.diana_service.enhance_interaction.call_count == 2


@pytest.mark.asyncio
async def test_diana_with_narrative_integration(coordinador_central):
    """Prueba la integración de Diana con el sistema narrativo."""
    # Configurar mock para el servicio narrativo
    mock_narrative_service = AsyncMock()
    mock_narrative_service.get_user_narrative_progress.return_value = {
        "success": True,
        "current_fragment_id": "fragment_123",
        "progress": 0.35
    }
    
    mock_narrative_service.get_fragment_by_id.return_value = {
        "success": True,
        "fragment": {
            "id": "fragment_123",
            "title": "El encuentro",
            "content": "Diana te mira con curiosidad...",
            "emotion": "anticipation"
        }
    }
    
    coordinador_central.narrative_service = mock_narrative_service
    
    # Ejecutar flujo narrativo
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.AVANZAR_NARRATIVA
    )
    
    # Verificar que Diana intentó mejorar el resultado
    coordinador_central.diana_service.enhance_interaction.assert_called_once()


@pytest.mark.asyncio
async def test_integration_with_non_diana_action(coordinador_central):
    """Prueba que las acciones no soportadas por Diana funcionan normalmente."""
    # Crear una acción no soportada específicamente por Diana
    coordinador_central.ejecutar_accion_generica = AsyncMock()
    coordinador_central.ejecutar_accion_generica.return_value = {
        "success": True,
        "message": "Acción genérica completada",
        "code": "GENERIC_ACTION"
    }
    
    # Ejecutar una acción no específica de Diana
    resultado = await coordinador_central.ejecutar_flujo(
        TEST_USER_ID,
        "ACCION_GENERICA"  # No es un AccionUsuario reconocido para Diana
    )
    
    # Verificar que la acción se completó pero Diana no la mejoró
    assert resultado["success"] is True
    assert resultado["code"] == "GENERIC_ACTION"
    
    # El enhance_interaction no debería haberse llamado para acciones no soportadas
    coordinador_central.diana_service.enhance_interaction.assert_not_called()


@pytest.mark.asyncio
async def test_graceful_failure_with_missing_diana_service(mock_db_session, mock_channel_engagement, mock_point_service):
    """Prueba que el sistema funciona incluso si el servicio de Diana no está disponible."""
    # Crear coordinador sin servicio de Diana
    coordinador = CoordinadorCentral(mock_db_session)
    coordinador.channel_engagement = mock_channel_engagement
    coordinador.point_service = mock_point_service
    coordinador.diana_service = None  # Diana no está disponible
    
    # Ejecutar flujo
    resultado = await coordinador.ejecutar_flujo(
        TEST_USER_ID,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=TEST_MESSAGE_ID,
        channel_id=TEST_CHANNEL_ID,
        reaction_type="❤️"
    )
    
    # Verificar que el flujo completa normalmente sin Diana
    assert resultado["success"] is True
    assert "message" in resultado
    assert resultado["points_awarded"] == 10