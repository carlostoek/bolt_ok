"""
Pruebas para la personalización de mensajes basada en el estado emocional.

Este módulo prueba específicamente las capacidades de Diana para personalizar
mensajes basándose en el estado emocional del usuario, la relación actual,
y las preferencias de adaptación de personalidad.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from datetime import datetime

from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)

# Constantes para pruebas
TEST_USER_ID = 123456789


@pytest.fixture
def mock_session():
    """Crea un mock de la sesión de base de datos."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def diana_service(mock_session):
    """Crea una instancia de DianaEmotionalService con una sesión mock."""
    return DianaEmotionalService(mock_session)


# Pruebas para personalización basada en diferentes relaciones


@pytest.mark.asyncio
async def test_personalization_by_relationship_status(diana_service):
    """Prueba que los mensajes se personalizan según el estado de la relación."""
    # Escenarios de relación a probar
    relationship_scenarios = [
        {
            "status": "initial",
            "trust_level": 0.1,
            "rapport": 0.1,
            "familiarity": 0.0,
            "interaction_count": 2
        },
        {
            "status": "acquaintance",
            "trust_level": 0.3,
            "rapport": 0.3,
            "familiarity": 0.2,
            "interaction_count": 10
        },
        {
            "status": "friendly",
            "trust_level": 0.6,
            "rapport": 0.5,
            "familiarity": 0.5,
            "interaction_count": 25
        },
        {
            "status": "close",
            "trust_level": 0.8,
            "rapport": 0.7,
            "familiarity": 0.8,
            "interaction_count": 50
        },
        {
            "status": "intimate",
            "trust_level": 0.9,
            "rapport": 0.9,
            "familiarity": 0.9,
            "interaction_count": 100
        }
    ]
    
    # Adaptación de personalidad estándar
    adaptation = {
        "warmth": 0.7,
        "formality": 0.4,
        "humor": 0.6,
        "directness": 0.5,
        "emotional_expressiveness": 0.6,
        "emoji_usage": 0.5
    }
    
    # Resultado base a personalizar
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Probar cada escenario de relación
    messages = []
    for relationship in relationship_scenarios:
        result = await diana_service._enhance_reaction_message(
            TEST_USER_ID,
            dict(resultado_base),  # Copia para evitar modificar el original
            relationship,
            adaptation,
            reaction_type="❤️"
        )
        messages.append({
            "status": relationship["status"],
            "message": result["message"]
        })
    
    # Verificaciones
    # 1. Todos los mensajes deben ser diferentes según el estado de la relación
    message_texts = [item["message"] for item in messages]
    assert len(set(message_texts)) >= 3  # Al menos 3 mensajes distintos
    
    # 2. Los mensajes más íntimos deben contener elementos más personales
    intimate_message = messages[-1]["message"]  # El escenario "intimate"
    initial_message = messages[0]["message"]    # El escenario "initial"
    
    # El mensaje íntimo debería ser más elaborado/personal
    assert len(intimate_message) > len(initial_message)
    
    # 3. Todos los mensajes deben contener información sobre los puntos
    for item in messages:
        assert "*+10 besitos* 💋" in item["message"]


@pytest.mark.asyncio
async def test_personalization_by_personality_adaptation(diana_service):
    """Prueba que los mensajes se personalizan según las adaptaciones de personalidad."""
    # Relación estándar
    relationship = {
        "status": "friendly",
        "trust_level": 0.6,
        "rapport": 0.5,
        "familiarity": 0.5,
        "interaction_count": 25,
        "dominant_emotion": "joy"
    }
    
    # Escenarios de adaptación de personalidad
    adaptation_scenarios = [
        {
            "scenario": "formal",
            "adaptation": {
                "warmth": 0.3,
                "formality": 0.9,
                "humor": 0.2,
                "directness": 0.7,
                "emotional_expressiveness": 0.3,
                "emoji_usage": 0.1
            }
        },
        {
            "scenario": "warm",
            "adaptation": {
                "warmth": 0.9,
                "formality": 0.3,
                "humor": 0.5,
                "directness": 0.6,
                "emotional_expressiveness": 0.7,
                "emoji_usage": 0.5
            }
        },
        {
            "scenario": "humorous",
            "adaptation": {
                "warmth": 0.7,
                "formality": 0.3,
                "humor": 0.9,
                "directness": 0.5,
                "emotional_expressiveness": 0.8,
                "emoji_usage": 0.8
            }
        },
        {
            "scenario": "expressive",
            "adaptation": {
                "warmth": 0.7,
                "formality": 0.4,
                "humor": 0.6,
                "directness": 0.7,
                "emotional_expressiveness": 0.9,
                "emoji_usage": 0.9
            }
        }
    ]
    
    # Resultado base a personalizar
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Probar cada escenario de adaptación
    messages = []
    for scenario in adaptation_scenarios:
        result = await diana_service._enhance_reaction_message(
            TEST_USER_ID,
            dict(resultado_base),
            relationship,
            scenario["adaptation"],
            reaction_type="❤️"
        )
        messages.append({
            "scenario": scenario["scenario"],
            "message": result["message"]
        })
    
    # Verificaciones
    # 1. Todos los mensajes deben ser diferentes según la adaptación
    message_texts = [item["message"] for item in messages]
    assert len(set(message_texts)) >= 3  # Al menos 3 mensajes distintos
    
    # 2. El mensaje formal debería contener menos emojis
    formal_message = next(item["message"] for item in messages if item["scenario"] == "formal")
    expressive_message = next(item["message"] for item in messages if item["scenario"] == "expressive")
    
    # Contar emojis en cada mensaje (aproximado)
    emoji_chars = ['✨', '💕', '💖', '💋', '❤️', '😊', '👀', '🌟', '💫']
    formal_emoji_count = sum(formal_message.count(emoji) for emoji in emoji_chars)
    expressive_emoji_count = sum(expressive_message.count(emoji) for emoji in emoji_chars)
    
    # El mensaje expresivo debería tener más emojis
    assert expressive_emoji_count >= formal_emoji_count


@pytest.mark.asyncio
async def test_personalization_by_emotion(diana_service):
    """Prueba que los mensajes se personalizan según la emoción del usuario."""
    # Relación y adaptación estándar
    relationship = {
        "status": "friendly",
        "trust_level": 0.6,
        "rapport": 0.5,
        "familiarity": 0.5,
        "interaction_count": 25
    }
    
    adaptation = {
        "warmth": 0.7,
        "formality": 0.4,
        "humor": 0.6,
        "directness": 0.5,
        "emotional_expressiveness": 0.7,
        "emoji_usage": 0.6
    }
    
    # Resultado base a personalizar
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Escenarios de emociones
    emotion_scenarios = ["joy", "sadness", "fear", "anger", "trust"]
    
    # Configurar mock para memoria contextual
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Probar cada escenario de emoción
    messages = []
    for emotion in emotion_scenarios:
        # Configurar el contexto emocional para esta prueba
        diana_service._get_user_emotional_context = AsyncMock()
        diana_service._get_user_emotional_context.return_value = {
            "primary_emotion": emotion,
            "context": {}
        }
        
        result = await diana_service._enhance_reaction_message(
            TEST_USER_ID,
            dict(resultado_base),
            relationship,
            adaptation,
            reaction_type="❤️"
        )
        messages.append({
            "emotion": emotion,
            "message": result["message"]
        })
    
    # Verificaciones
    # Deberían generarse mensajes diferentes según la emoción
    message_texts = [item["message"] for item in messages]
    assert len(set(message_texts)) >= 2  # Al menos algunos mensajes distintos
    
    # Los mensajes para emociones positivas vs. negativas deberían ser diferentes
    joy_message = next(item["message"] for item in messages if item["emotion"] == "joy")
    sadness_message = next(item["message"] for item in messages if item["emotion"] == "sadness")
    
    assert joy_message != sadness_message


@pytest.mark.asyncio
async def test_personalization_by_reaction_type(diana_service):
    """Prueba que los mensajes se personalizan según el tipo de reacción."""
    # Relación y adaptación estándar
    relationship = {
        "status": "friendly",
        "trust_level": 0.6,
        "rapport": 0.5,
        "familiarity": 0.5,
        "interaction_count": 25
    }
    
    adaptation = {
        "warmth": 0.7,
        "formality": 0.4,
        "humor": 0.6,
        "directness": 0.5,
        "emotional_expressiveness": 0.7,
        "emoji_usage": 0.6
    }
    
    # Resultado base a personalizar
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Tipos de reacción a probar
    reaction_types = ["❤️", "👍", "😂", "😮", "👀"]
    
    # Probar cada tipo de reacción
    messages = []
    for reaction in reaction_types:
        result = await diana_service._enhance_reaction_message(
            TEST_USER_ID,
            dict(resultado_base),
            relationship,
            adaptation,
            reaction_type=reaction
        )
        messages.append({
            "reaction": reaction,
            "message": result["message"]
        })
    
    # Verificaciones
    # Deberían generarse mensajes diferentes según el tipo de reacción
    message_texts = [item["message"] for item in messages]
    assert len(set(message_texts)) >= 3  # Al menos 3 mensajes distintos
    
    # Reacciones románticas vs. divertidas deberían generar respuestas diferentes
    heart_message = next(item["message"] for item in messages if item["reaction"] == "❤️")
    laugh_message = next(item["message"] for item in messages if item["reaction"] == "😂")
    
    assert heart_message != laugh_message


@pytest.mark.asyncio
async def test_personalization_with_memory_reference(diana_service):
    """Prueba que los mensajes pueden incluir referencias a memorias pasadas."""
    # Relación con alta intimidad
    relationship = {
        "status": "intimate",
        "trust_level": 0.9,
        "rapport": 0.8,
        "familiarity": 0.9,
        "interaction_count": 100
    }
    
    # Adaptación que favorece referencias a memorias
    adaptation = {
        "warmth": 0.8,
        "formality": 0.3,
        "humor": 0.6,
        "directness": 0.7,
        "emotional_expressiveness": 0.8,
        "emoji_usage": 0.7,
        "memory_reference_frequency": 0.8
    }
    
    # Resultado base a personalizar
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    # Configurar referencia a memoria
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = "recordando nuestra conversación de anoche"
    
    # Probar la personalización con referencia a memoria
    result = await diana_service._enhance_reaction_message(
        TEST_USER_ID,
        resultado_base,
        relationship,
        adaptation,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert "recordando nuestra conversación de anoche" in result["message"]


@pytest.mark.asyncio
async def test_personalization_consistency(diana_service):
    """Prueba que la personalización mantiene consistencia para los mismos parámetros."""
    # Relación y adaptación
    relationship = {
        "status": "friendly",
        "trust_level": 0.6,
        "rapport": 0.5,
        "familiarity": 0.5,
        "interaction_count": 25
    }
    
    adaptation = {
        "warmth": 0.7,
        "formality": 0.4,
        "humor": 0.6,
        "directness": 0.5,
        "emotional_expressiveness": 0.7,
        "emoji_usage": 0.6
    }
    
    # Resultado base
    resultado_base = {
        "success": True,
        "message": "Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
        "points_awarded": 10
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Realizar la misma llamada varias veces
    results = []
    for _ in range(3):
        result = await diana_service._enhance_reaction_message(
            TEST_USER_ID,
            dict(resultado_base),
            dict(relationship),
            dict(adaptation),
            reaction_type="❤️"
        )
        results.append(result["message"])
    
    # Verificar que los mensajes son consistentes (no varían aleatoriamente)
    assert len(set(results)) == 1  # Todos los mensajes deberían ser iguales


@pytest.mark.asyncio
async def test_personalization_preserves_hint_content(diana_service):
    """Prueba que la personalización preserva el contenido de pistas desbloqueadas."""
    # Relación y adaptación
    relationship = {
        "status": "friendly",
        "trust_level": 0.6,
        "rapport": 0.5,
        "familiarity": 0.5,
        "interaction_count": 25
    }
    
    adaptation = {
        "warmth": 0.7,
        "formality": 0.4,
        "humor": 0.6,
        "directness": 0.5,
        "emotional_expressiveness": 0.7,
        "emoji_usage": 0.6
    }
    
    # Resultado base con pista
    hint_message = "¡Nueva pista desbloqueada!\n\nPista #3: La llave se encuentra escondida detrás del cuadro."
    resultado_base = {
        "success": True,
        "message": f"Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.\n\n{hint_message}",
        "points_awarded": 10,
        "hint_unlocked": True
    }
    
    # Configurar mocks necesarios
    diana_service._get_user_emotional_context = AsyncMock()
    diana_service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    diana_service._get_contextual_memory_reference = AsyncMock()
    diana_service._get_contextual_memory_reference.return_value = ""
    
    # Probar la personalización con una pista
    result = await diana_service._enhance_reaction_message(
        TEST_USER_ID,
        resultado_base,
        relationship,
        adaptation,
        reaction_type="❤️"
    )
    
    # Verificaciones
    assert "Diana" in result["message"]  # El mensaje debe estar personalizado
    assert hint_message in result["message"]  # La pista debe preservarse exactamente
    assert "*+10 besitos* 💋" in result["message"]  # Los puntos deben preservarse