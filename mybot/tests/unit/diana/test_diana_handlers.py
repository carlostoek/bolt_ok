"""
Pruebas unitarias para los handlers de Diana.

Este módulo contiene pruebas para verificar que los handlers de Diana 
funcionen correctamente y respondan a los comandos y mensajes de los usuarios
como se espera.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from aiogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.diana_test_handler import (
    diana_test_command,
    diana_daily_test,
    diana_message_handler
)

from handlers.diana_emotional_handlers import (
    handle_relationship_status,
    handle_recent_memories,
    handle_personality_preferences,
    handle_general_message
)

from services.diana_emotional_service import DianaEmotionalService
from services.coordinador_central import CoordinadorCentral, AccionUsuario

# Configuración de pruebas
TEST_USER_ID = 123456789


@pytest.fixture
def mock_message():
    """Crea un mock de un mensaje de Telegram."""
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = TEST_USER_ID
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.text = "/test_command"
    return message


@pytest.fixture
def mock_session():
    """Crea un mock de la sesión de base de datos."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_coordinador():
    """Crea un mock del CoordinadorCentral."""
    coordinador = AsyncMock(spec=CoordinadorCentral)
    
    # Configurar el comportamiento para ejecutar_flujo
    async def mock_ejecutar_flujo(user_id, accion, **kwargs):
        # Simular diferentes acciones
        if accion == AccionUsuario.REACCIONAR_PUBLICACION:
            return {
                "success": True,
                "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
                "points_awarded": 10,
                "total_points": 150,
                "diana_active": True
            }
        elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
            return {
                "success": True,
                "message": "¡Bienvenido de nuevo! *+5 besitos* 💋 por tu visita diaria.",
                "points_awarded": 5,
                "streak": 3,
                "diana_active": True
            }
        else:
            return {
                "success": False,
                "message": "Acción no reconocida",
                "diana_active": False
            }
    
    coordinador.ejecutar_flujo = mock_ejecutar_flujo
    return coordinador


@pytest.fixture
def mock_diana_service():
    """Crea un mock del servicio emocional de Diana."""
    service = AsyncMock(spec=DianaEmotionalService)
    
    # Configurar comportamientos para diferentes métodos
    service.get_relationship_state.return_value = {
        "success": True,
        "relationship": {
            "status": "friendly",
            "trust_level": 0.6,
            "rapport": 0.5,
            "interaction_count": 15,
            "dominant_emotion": "joy",
            "milestone_count": 2,
            "milestone_data": {
                "status_changes": [
                    {
                        "timestamp": "2023-01-01T12:00:00",
                        "old_status": "initial",
                        "new_status": "acquaintance",
                        "reason": "Natural progression"
                    },
                    {
                        "timestamp": "2023-02-01T12:00:00",
                        "old_status": "acquaintance",
                        "new_status": "friendly",
                        "reason": "Natural progression"
                    }
                ]
            }
        }
    }
    
    service.get_recent_memories.return_value = {
        "success": True,
        "memories": [
            {
                "id": 1,
                "user_id": TEST_USER_ID,
                "summary": "El usuario reaccionó con ❤️ a una publicación",
                "content": "El usuario reaccionó con ❤️ a una publicación de Diana",
                "primary_emotion": "joy",
                "timestamp": "2023-07-10T14:30:00",
                "interaction_type": "feedback"
            },
            {
                "id": 2,
                "user_id": TEST_USER_ID,
                "summary": "Diana y el usuario conversaron sobre su día",
                "content": "El usuario compartió que tuvo un buen día",
                "primary_emotion": "trust",
                "timestamp": "2023-07-09T18:45:00",
                "interaction_type": "personal_share"
            }
        ]
    }
    
    service.get_personality_adaptation.return_value = {
        "success": True,
        "adaptation": {
            "warmth": 0.7,
            "formality": 0.4,
            "humor": 0.6,
            "emotional_expressiveness": 0.8,
            "emoji_usage": 0.6
        }
    }
    
    service.record_interaction.return_value = {
        "success": True,
        "interaction_count": 16,
        "message": "Interaction recorded successfully"
    }
    
    service.store_emotional_memory.return_value = {
        "success": True,
        "memory_id": 3,
        "message": "Emotional memory stored successfully"
    }
    
    return service


# Pruebas para los handlers de comandos de prueba


@pytest.mark.asyncio
async def test_diana_test_command(mock_message, mock_session, monkeypatch):
    """Prueba el comando /diana_test."""
    # Patch para el CoordinadorCentral
    mock_coord = AsyncMock(spec=CoordinadorCentral)
    mock_coord.ejecutar_flujo.return_value = {
        "success": True,
        "message": "Diana sonríe dulcemente... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10,
        "diana_active": True
    }
    
    # Monkeypatch para evitar crear un coordinador real
    monkeypatch.setattr(
        "handlers.diana_test_handler.CoordinadorCentral",
        lambda session: mock_coord
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_test_handler.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await diana_test_command(mock_message, mock_session)
    
    # Verificaciones
    mock_coord.ejecutar_flujo.assert_called_once()
    args, kwargs = mock_coord.ejecutar_flujo.call_args
    assert kwargs["reaction_type"] == "❤️"  # Verificar que se pasa el mock_reaction
    
    # Verificar que se llama a safe_answer con un mensaje que incluye los puntos
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Diana sonríe dulcemente" in response_message
    assert "*+10 besitos*" in response_message
    assert "Prueba de Diana: True" in response_message


@pytest.mark.asyncio
async def test_diana_daily_test(mock_message, mock_session, monkeypatch):
    """Prueba el comando /diana_daily."""
    # Patch para el CoordinadorCentral
    mock_coord = AsyncMock(spec=CoordinadorCentral)
    mock_coord.ejecutar_flujo.return_value = {
        "success": True,
        "message": "¡Bienvenido de nuevo! *+5 besitos* 💋 por tu visita diaria.",
        "points_awarded": 5,
        "streak": 3,
        "diana_active": True
    }
    
    # Monkeypatch para evitar crear un coordinador real
    monkeypatch.setattr(
        "handlers.diana_test_handler.CoordinadorCentral",
        lambda session: mock_coord
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_test_handler.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await diana_daily_test(mock_message, mock_session)
    
    # Verificaciones
    mock_coord.ejecutar_flujo.assert_called_once()
    args, kwargs = mock_coord.ejecutar_flujo.call_args
    assert args[1] == AccionUsuario.VERIFICAR_ENGAGEMENT
    
    # Verificar que se llama a safe_answer con un mensaje que incluye la racha
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "¡Bienvenido de nuevo!" in response_message
    assert "Racha actual: 3 días" in response_message


@pytest.mark.asyncio
async def test_diana_message_handler(mock_message, mock_session, monkeypatch):
    """Prueba el handler de mensajes que mencionan a Diana."""
    # Modificar el mensaje para que contenga el nombre Diana
    mock_message.text = "Hola Diana, ¿cómo estás?"
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_test_handler.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await diana_message_handler(mock_message, mock_session)
    
    # Verificaciones
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Diana nota que has mencionado su nombre" in response_message


# Pruebas para los handlers emocionales


@pytest.mark.asyncio
async def test_handle_relationship_status(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba el handler de estado de relación."""
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await handle_relationship_status(mock_message, mock_session)
    
    # Verificaciones
    mock_diana_service.get_relationship_state.assert_called_once_with(TEST_USER_ID)
    mock_diana_service.record_interaction.assert_called_once()
    mock_diana_service.store_emotional_memory.assert_called_once()
    
    # Verificar que se llama a safe_answer con un mensaje que incluye el estado de la relación
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Mi relación contigo" in response_message
    assert "Somos amigos" in response_message  # Basado en el status "friendly"
    assert "Confianza" in response_message


@pytest.mark.asyncio
async def test_handle_recent_memories_with_memories(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba el handler de memorias recientes cuando hay memorias."""
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await handle_recent_memories(mock_message, mock_session)
    
    # Verificaciones
    mock_diana_service.get_recent_memories.assert_called_once_with(TEST_USER_ID, limit=5)
    mock_diana_service.record_interaction.assert_called_once()
    mock_diana_service.store_emotional_memory.assert_called_once()
    
    # Verificar que se llama a safe_answer con un mensaje que incluye las memorias
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Recuerdos recientes" in response_message
    assert "El usuario reaccionó con ❤️" in response_message
    assert "alegría" in response_message  # Traducción de "joy"


@pytest.mark.asyncio
async def test_handle_recent_memories_without_memories(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba el handler de memorias recientes cuando no hay memorias."""
    # Modificar el mock para que no haya memorias
    mock_diana_service.get_recent_memories.return_value = {
        "success": True,
        "memories": []
    }
    
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await handle_recent_memories(mock_message, mock_session)
    
    # Verificaciones
    mock_diana_service.get_recent_memories.assert_called_once_with(TEST_USER_ID, limit=5)
    
    # Verificar que se llama a safe_answer con un mensaje sobre no tener memorias
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Aún no tenemos recuerdos significativos" in response_message


@pytest.mark.asyncio
async def test_handle_personality_preferences(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba el handler de preferencias de personalidad."""
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Patch para safe_answer
    safe_answer_mock = AsyncMock()
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.safe_answer",
        safe_answer_mock
    )
    
    # Ejecutar el handler
    await handle_personality_preferences(mock_message, mock_session)
    
    # Verificaciones
    mock_diana_service.get_personality_adaptation.assert_called_once_with(TEST_USER_ID)
    mock_diana_service.record_interaction.assert_called_once()
    mock_diana_service.store_emotional_memory.assert_called_once()
    
    # Verificar que se llama a safe_answer con un mensaje que incluye las preferencias
    safe_answer_mock.assert_called_once()
    response_message = safe_answer_mock.call_args[0][1]
    assert "Cómo me adapto a ti" in response_message
    assert "Calidez" in response_message
    assert "Uso de emojis" in response_message


@pytest.mark.asyncio
async def test_handle_general_message(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba el handler general de mensajes para el procesamiento emocional."""
    # Configurar el mensaje de prueba
    mock_message.text = "Me siento muy feliz hoy, ha sido un gran día!"
    
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Ejecutar el handler
    await handle_general_message(mock_message, mock_session)
    
    # Verificaciones
    mock_diana_service.record_interaction.assert_called_once_with(
        TEST_USER_ID, 
        interaction_length=len(mock_message.text)
    )
    
    # Verificar que se almacena la memoria emocional
    mock_diana_service.store_emotional_memory.assert_called_once()
    args, kwargs = mock_diana_service.store_emotional_memory.call_args
    assert kwargs["user_id"] == TEST_USER_ID
    assert "tags" in kwargs and "message" in kwargs["tags"]


@pytest.mark.asyncio
async def test_handle_general_message_skips_non_text(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba que el handler general de mensajes ignora mensajes sin texto."""
    # Configurar el mensaje sin texto
    mock_message.text = None
    
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Ejecutar el handler
    await handle_general_message(mock_message, mock_session)
    
    # Verificar que no se procesó el mensaje
    mock_diana_service.record_interaction.assert_not_called()
    mock_diana_service.store_emotional_memory.assert_not_called()


@pytest.mark.asyncio
async def test_handle_general_message_with_error(mock_message, mock_session, mock_diana_service, monkeypatch):
    """Prueba que el handler general maneja errores silenciosamente."""
    # Configurar el mensaje de prueba
    mock_message.text = "Este mensaje causará un error"
    
    # Hacer que record_interaction lance una excepción
    mock_diana_service.record_interaction.side_effect = Exception("Test error")
    
    # Monkeypatch para evitar crear un servicio real
    monkeypatch.setattr(
        "handlers.diana_emotional_handlers.DianaEmotionalService",
        lambda session: mock_diana_service
    )
    
    # Ejecutar el handler - no debería lanzar excepción
    await handle_general_message(mock_message, mock_session)
    
    # Verificar que se intentó procesar pero no continuó
    mock_diana_service.record_interaction.assert_called_once()
    mock_diana_service.store_emotional_memory.assert_not_called()