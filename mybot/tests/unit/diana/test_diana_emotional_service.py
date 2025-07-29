"""
Pruebas unitarias para el servicio DianaEmotionalService.

Este módulo contiene las pruebas unitarias para validar el funcionamiento correcto
del servicio emocional de Diana, asegurando que todas sus funciones principales
operen como se espera y manejen adecuadamente los errores.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    DianaEmotionalMemory,
    DianaRelationshipState,
    DianaContradiction,
    DianaPersonalityAdaptation,
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)

# Datos de prueba constantes
TEST_USER_ID = 123456789
TEST_INTERACTION_TYPE = EmotionalInteractionType.GREETING
TEST_SUMMARY = "Test memory summary"
TEST_CONTENT = "Test memory content"
TEST_PRIMARY_EMOTION = EmotionCategory.JOY
TEST_SECONDARY_EMOTION = EmotionCategory.TRUST
TEST_INTENSITY = EmotionalIntensity.MODERATE
TEST_IMPORTANCE = 1.5
TEST_TAGS = ["test", "greeting"]

# Fixtures para pruebas


@pytest.fixture
def mock_session():
    """Crea un mock de la sesión de base de datos."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def diana_service(mock_session):
    """Crea una instancia de DianaEmotionalService con una sesión mock."""
    return DianaEmotionalService(mock_session)


@pytest.fixture
def mock_memory():
    """Crea un mock de DianaEmotionalMemory."""
    memory = MagicMock(spec=DianaEmotionalMemory)
    memory.id = 1
    memory.user_id = TEST_USER_ID
    memory.interaction_type = TEST_INTERACTION_TYPE
    memory.timestamp = datetime.now()
    memory.summary = TEST_SUMMARY
    memory.content = TEST_CONTENT
    memory.primary_emotion = TEST_PRIMARY_EMOTION
    memory.secondary_emotion = TEST_SECONDARY_EMOTION
    memory.intensity = TEST_INTENSITY
    memory.importance_score = TEST_IMPORTANCE
    memory.tags = TEST_TAGS
    memory.is_forgotten = False
    memory.recall_count = 1
    memory.last_recalled_at = datetime.now()
    return memory


@pytest.fixture
def mock_relationship():
    """Crea un mock de DianaRelationshipState."""
    relationship = MagicMock(spec=DianaRelationshipState)
    relationship.user_id = TEST_USER_ID
    relationship.status = RelationshipStatus.FRIENDLY
    relationship.trust_level = 0.6
    relationship.familiarity = 0.5
    relationship.rapport = 0.7
    relationship.dominant_emotion = EmotionCategory.JOY
    relationship.emotional_volatility = 0.3
    relationship.positive_interactions = 20
    relationship.negative_interactions = 5
    relationship.interaction_count = 25
    relationship.milestone_count = 2
    relationship.milestone_data = {
        "status_changes": [
            {
                "timestamp": datetime.now().isoformat(),
                "old_status": RelationshipStatus.INITIAL.value,
                "new_status": RelationshipStatus.ACQUAINTANCE.value,
                "reason": "Natural progression"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "old_status": RelationshipStatus.ACQUAINTANCE.value,
                "new_status": RelationshipStatus.FRIENDLY.value,
                "reason": "Natural progression"
            }
        ]
    }
    relationship.personality_adaptations = {"emotion_counts": {"joy": 15, "trust": 5}}
    return relationship


@pytest.fixture
def mock_adaptation():
    """Crea un mock de DianaPersonalityAdaptation."""
    adaptation = MagicMock(spec=DianaPersonalityAdaptation)
    adaptation.user_id = TEST_USER_ID
    adaptation.warmth = 0.7
    adaptation.formality = 0.4
    adaptation.humor = 0.6
    adaptation.directness = 0.5
    adaptation.assertiveness = 0.5
    adaptation.curiosity = 0.7
    adaptation.emotional_expressiveness = 0.8
    adaptation.message_length_preference = 120
    adaptation.complexity_level = 0.5
    adaptation.emoji_usage = 0.6
    adaptation.response_delay = 0
    adaptation.topic_preferences = {"romance": 0.9, "adventure": 0.7}
    adaptation.taboo_topics = ["politics"]
    adaptation.memory_reference_frequency = 0.3
    adaptation.adaptation_reason = "User preferences"
    adaptation.confidence_score = 0.7
    return adaptation


@pytest.mark.asyncio
async def test_store_emotional_memory_success(diana_service, mock_session):
    """Prueba la creación exitosa de una memoria emocional."""
    # Configurar el comportamiento del mock
    mock_session.flush.return_value = None
    mock_session.commit.return_value = None
    
    # Ejecutar el método a probar
    result = await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=TEST_INTERACTION_TYPE,
        summary=TEST_SUMMARY,
        content=TEST_CONTENT,
        primary_emotion=TEST_PRIMARY_EMOTION,
        secondary_emotion=TEST_SECONDARY_EMOTION,
        intensity=TEST_INTENSITY,
        importance_score=TEST_IMPORTANCE,
        tags=TEST_TAGS
    )
    
    # Verificar resultados
    assert result["success"] is True
    assert "memory_id" in result
    assert "message" in result
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_store_emotional_memory_error(diana_service, mock_session):
    """Prueba el manejo de errores al crear una memoria emocional."""
    # Configurar el comportamiento del mock para simular un error
    mock_session.flush.side_effect = Exception("Database error")
    
    # Ejecutar el método a probar
    result = await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=TEST_INTERACTION_TYPE,
        summary=TEST_SUMMARY,
        content=TEST_CONTENT,
        primary_emotion=TEST_PRIMARY_EMOTION
    )
    
    # Verificar resultados
    assert result["success"] is False
    assert "error" in result
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_memories_success(diana_service, mock_session, mock_memory):
    """Prueba la recuperación exitosa de memorias recientes."""
    # Configurar el comportamiento del mock
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = [mock_memory]
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_recent_memories(TEST_USER_ID, limit=5)
    
    # Verificar resultados
    assert result["success"] is True
    assert "memories" in result
    assert len(result["memories"]) == 1
    assert result["memories"][0]["user_id"] == TEST_USER_ID
    assert result["memories"][0]["primary_emotion"] == TEST_PRIMARY_EMOTION.value
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_memories_empty(diana_service, mock_session):
    """Prueba la recuperación de memorias cuando no hay resultados."""
    # Configurar el comportamiento del mock para devolver una lista vacía
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_recent_memories(TEST_USER_ID, limit=5)
    
    # Verificar resultados
    assert result["success"] is True
    assert "memories" in result
    assert len(result["memories"]) == 0
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_relationship_state_existing(diana_service, mock_session, mock_relationship):
    """Prueba la recuperación de un estado de relación existente."""
    # Configurar el comportamiento del mock
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_relationship
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_relationship_state(TEST_USER_ID)
    
    # Verificar resultados
    assert result["success"] is True
    assert "relationship" in result
    assert result["relationship"]["user_id"] == TEST_USER_ID
    assert result["relationship"]["status"] == RelationshipStatus.FRIENDLY.value
    assert result["relationship"]["trust_level"] == 0.6
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_relationship_state_create_new(diana_service, mock_session):
    """Prueba la creación de un nuevo estado de relación cuando no existe."""
    # Configurar el comportamiento del mock para simular que no existe
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Mock para el método _create_default_relationship_state
    diana_service._create_default_relationship_state = AsyncMock()
    diana_service._create_default_relationship_state.return_value = mock_relationship = MagicMock()
    mock_relationship.user_id = TEST_USER_ID
    mock_relationship.status = RelationshipStatus.INITIAL
    
    # Ejecutar el método a probar
    result = await diana_service.get_relationship_state(TEST_USER_ID)
    
    # Verificar resultados
    assert result["success"] is True
    assert "relationship" in result
    diana_service._create_default_relationship_state.assert_called_once_with(TEST_USER_ID)


@pytest.mark.asyncio
async def test_get_personality_adaptation_existing(diana_service, mock_session, mock_adaptation):
    """Prueba la recuperación de una adaptación de personalidad existente."""
    # Configurar el comportamiento del mock
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_adaptation
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_personality_adaptation(TEST_USER_ID)
    
    # Verificar resultados
    assert result["success"] is True
    assert "adaptation" in result
    assert result["adaptation"]["user_id"] == TEST_USER_ID
    assert result["adaptation"]["warmth"] == 0.7
    assert result["adaptation"]["emoji_usage"] == 0.6
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_enhance_interaction_success(diana_service, mock_session):
    """Prueba el proceso de mejora de interacción cuando Diana está activa."""
    # Mock de los métodos necesarios
    diana_service.get_relationship_state = AsyncMock(return_value={
        "success": True,
        "relationship": {"status": "friendly", "trust_level": 0.6}
    })
    diana_service.get_personality_adaptation = AsyncMock(return_value={
        "success": True,
        "adaptation": {"warmth": 0.7, "emoji_usage": 0.6}
    })
    diana_service.record_interaction = AsyncMock()
    diana_service._store_interaction_memory = AsyncMock()
    diana_service.is_active = MagicMock(return_value=True)
    diana_service._enhance_by_action_type = AsyncMock(return_value={
        "success": True,
        "message": "Mensaje mejorado por Diana",
        "enhanced_by_diana": True
    })
    
    # Resultado original a mejorar
    resultado_original = {
        "success": True,
        "message": "Mensaje original",
        "points_awarded": 10
    }
    
    # Ejecutar el método a probar
    result = await diana_service.enhance_interaction(
        TEST_USER_ID,
        "reaccionar_publicacion",
        resultado_original,
        reaction_type="❤️"
    )
    
    # Verificar resultados
    assert result["success"] is True
    assert "message" in result
    assert result["enhanced_by_diana"] is True
    assert result["message"] == "Mensaje mejorado por Diana"
    diana_service.get_relationship_state.assert_called_once_with(TEST_USER_ID)
    diana_service.get_personality_adaptation.assert_called_once_with(TEST_USER_ID)
    diana_service.record_interaction.assert_called_once_with(TEST_USER_ID)


@pytest.mark.asyncio
async def test_enhance_interaction_inactive(diana_service, mock_session):
    """Prueba que la mejora de interacción devuelve el resultado original cuando Diana está inactiva."""
    # Mock de los métodos necesarios
    diana_service.get_relationship_state = AsyncMock(return_value={
        "success": True,
        "relationship": {"status": "friendly", "trust_level": 0.6}
    })
    diana_service.get_personality_adaptation = AsyncMock(return_value={
        "success": True,
        "adaptation": {"warmth": 0.7, "emoji_usage": 0.6}
    })
    diana_service.record_interaction = AsyncMock()
    diana_service._store_interaction_memory = AsyncMock()
    diana_service.is_active = MagicMock(return_value=False)
    
    # Resultado original
    resultado_original = {
        "success": True,
        "message": "Mensaje original",
        "points_awarded": 10
    }
    
    # Ejecutar el método a probar
    result = await diana_service.enhance_interaction(
        TEST_USER_ID,
        "reaccionar_publicacion",
        resultado_original,
        reaction_type="❤️"
    )
    
    # Verificar resultados
    assert result == resultado_original
    diana_service.get_relationship_state.assert_called_once_with(TEST_USER_ID)
    diana_service.get_personality_adaptation.assert_called_once_with(TEST_USER_ID)
    diana_service.record_interaction.assert_called_once_with(TEST_USER_ID)
    diana_service._enhance_by_action_type.assert_not_called()


@pytest.mark.asyncio
async def test_enhance_reaction_message(diana_service, mock_session):
    """Prueba la personalización de mensajes de reacción."""
    # Datos de prueba
    relationship = {
        "status": "close",
        "trust_level": 0.8,
        "rapport": 0.7,
        "familiarity": 0.8,
        "dominant_emotion": "joy",
        "positive_interactions": 30,
        "negative_interactions": 5,
        "interaction_count": 35
    }
    
    adaptation = {
        "warmth": 0.8,
        "formality": 0.3,
        "humor": 0.7,
        "directness": 0.6,
        "emotional_expressiveness": 0.8,
        "emoji_usage": 0.7
    }
    
    # Mock necesario para _get_user_emotional_context
    diana_service._get_user_emotional_context = AsyncMock(return_value={
        "primary_emotion": "joy",
        "context": {}
    })
    
    diana_service._get_contextual_memory_reference = AsyncMock(return_value="recordando tu dulce gesto anterior")
    
    # Resultado original
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Ejecutar el método a probar
    result = await diana_service._enhance_reaction_message(
        TEST_USER_ID,
        resultado_base,
        relationship,
        adaptation,
        reaction_type="❤️"
    )
    
    # Verificar resultados
    assert result["success"] is True
    assert "message" in result
    # Verificar que el mensaje se ha personalizado (contiene algún elemento personalizado)
    assert result["message"] != resultado_base["message"]
    assert "*+10 besitos* 💋" in result["message"]  # Asegurarse que mantiene los puntos


@pytest.mark.asyncio
async def test_record_contradiction(diana_service, mock_session):
    """Prueba el registro de contradicciones en el conocimiento de Diana."""
    # Configurar el comportamiento del mock
    mock_session.commit.return_value = None
    
    # Datos de prueba
    contradiction_type = "preference"
    original_statement = "Me encanta el chocolate"
    contradicting_statement = "Odio el chocolate"
    context_data = {"conversation_id": 12345}
    
    # Ejecutar el método a probar
    result = await diana_service.record_contradiction(
        TEST_USER_ID,
        contradiction_type,
        original_statement,
        contradicting_statement,
        context_data
    )
    
    # Verificar resultados
    assert result["success"] is True
    assert "contradiction_id" in result
    assert "message" in result
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_personality_adaptation(diana_service, mock_session, mock_adaptation):
    """Prueba la actualización de la adaptación de personalidad."""
    # Configurar mocks
    diana_service._get_or_create_personality_adaptation = AsyncMock(return_value=mock_adaptation)
    mock_session.commit.return_value = None
    
    # Datos de actualización
    adaptation_data = {
        "warmth": 0.9,
        "humor": 0.8,
        "emoji_usage": 0.7
    }
    reason = "User explicitly requested more warmth"
    
    # Ejecutar el método a probar
    result = await diana_service.update_personality_adaptation(
        TEST_USER_ID,
        adaptation_data,
        reason
    )
    
    # Verificar resultados
    assert result["success"] is True
    assert "adaptation" in result
    assert "message" in result
    
    # Verificar que los atributos se actualizaron
    assert mock_adaptation.warmth == 0.9
    assert mock_adaptation.humor == 0.8
    assert mock_adaptation.emoji_usage == 0.7
    assert mock_adaptation.adaptation_reason == reason
    
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_forget_memory(diana_service, mock_session):
    """Prueba marcar una memoria como olvidada (para cumplimiento GDPR)."""
    # Configurar mocks
    mock_session.execute.return_value = MagicMock()
    mock_session.commit.return_value = None
    
    # Ejecutar el método a probar
    result = await diana_service.forget_memory(memory_id=1)
    
    # Verificar resultados
    assert result["success"] is True
    assert "message" in result
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_forget_all_user_memories(diana_service, mock_session):
    """Prueba marcar todas las memorias de un usuario como olvidadas."""
    # Configurar mocks
    mock_result = MagicMock()
    mock_result.rowcount = 10
    mock_session.execute.return_value = mock_result
    mock_session.commit.return_value = None
    
    # Ejecutar el método a probar
    result = await diana_service.forget_all_user_memories(TEST_USER_ID)
    
    # Verificar resultados
    assert result["success"] is True
    assert result["count"] == 10
    assert "message" in result
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()