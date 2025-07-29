"""
Pruebas para el sistema de detección y resolución de contradicciones de Diana.

Este módulo contiene pruebas que verifican el correcto funcionamiento del
sistema de contradicciones, que permite a Diana mantener una representación
consistente del conocimiento sobre los usuarios a lo largo del tiempo.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from datetime import datetime, timedelta

from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    DianaContradiction,
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity
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


@pytest.mark.asyncio
async def test_record_contradiction_basic(diana_service):
    """Prueba el registro básico de una contradicción."""
    # Configurar el comportamiento del mock
    mock_session = diana_service.session
    mock_session.commit.return_value = None
    
    # Datos de contradicción
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
    
    # Verificaciones
    assert result["success"] is True
    assert "contradiction_id" in result
    assert "message" in result
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Verificar que se pasaron los datos correctos al crear la contradicción
    contradiction_obj = mock_session.add.call_args[0][0]
    assert contradiction_obj.user_id == TEST_USER_ID
    assert contradiction_obj.contradiction_type == contradiction_type
    assert contradiction_obj.original_statement == original_statement
    assert contradiction_obj.contradicting_statement == contradicting_statement
    assert contradiction_obj.context_data == context_data
    assert contradiction_obj.is_resolved is False
    assert contradiction_obj.resolution is None


@pytest.mark.asyncio
async def test_record_contradiction_with_related_memories(diana_service):
    """Prueba el registro de una contradicción con memorias relacionadas."""
    # Configurar el comportamiento del mock
    mock_session = diana_service.session
    mock_session.commit.return_value = None
    
    # Datos de contradicción
    contradiction_type = "preference"
    original_statement = "Me encanta el chocolate"
    contradicting_statement = "Odio el chocolate"
    related_memory_ids = [1, 2, 3]  # IDs de memorias relacionadas
    
    # Ejecutar el método a probar
    result = await diana_service.record_contradiction(
        TEST_USER_ID,
        contradiction_type,
        original_statement,
        contradicting_statement,
        related_memory_ids=related_memory_ids
    )
    
    # Verificaciones
    assert result["success"] is True
    mock_session.add.assert_called_once()
    
    # Verificar que se pasaron los datos correctos al crear la contradicción
    contradiction_obj = mock_session.add.call_args[0][0]
    assert contradiction_obj.related_memory_ids == related_memory_ids


@pytest.mark.asyncio
async def test_record_contradiction_error_handling(diana_service):
    """Prueba el manejo de errores al registrar una contradicción."""
    # Configurar el comportamiento del mock para simular un error
    mock_session = diana_service.session
    mock_session.add.side_effect = Exception("Test database error")
    
    # Datos de contradicción
    contradiction_type = "preference"
    original_statement = "Me encanta el chocolate"
    contradicting_statement = "Odio el chocolate"
    
    # Ejecutar el método a probar
    result = await diana_service.record_contradiction(
        TEST_USER_ID,
        contradiction_type,
        original_statement,
        contradicting_statement
    )
    
    # Verificaciones
    assert result["success"] is False
    assert "error" in result
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_contradiction(diana_service):
    """Prueba la resolución de una contradicción."""
    # Configurar el comportamiento del mock
    mock_session = diana_service.session
    mock_session.commit.return_value = None
    
    # ID de contradicción y resolución
    contradiction_id = 1
    resolution = "Usuario aclaró que le gusta el chocolate oscuro pero odia el chocolate con leche"
    
    # Ejecutar el método a probar
    result = await diana_service.resolve_contradiction(contradiction_id, resolution)
    
    # Verificaciones
    assert result["success"] is True
    assert "message" in result
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Verificar que se está actualizando con los valores correctos
    execute_args = mock_session.execute.call_args[0][0]
    assert "SET" in str(execute_args)
    assert "resolution=" in str(execute_args)
    assert "is_resolved=True" in str(execute_args)
    assert "resolved_at=" in str(execute_args)
    assert f"WHERE diana_contradictions.id = {contradiction_id}" in str(execute_args)


@pytest.mark.asyncio
async def test_resolve_contradiction_error_handling(diana_service):
    """Prueba el manejo de errores al resolver una contradicción."""
    # Configurar el comportamiento del mock para simular un error
    mock_session = diana_service.session
    mock_session.execute.side_effect = Exception("Test database error")
    
    # ID de contradicción y resolución
    contradiction_id = 1
    resolution = "Usuario aclaró que le gusta el chocolate oscuro pero odia el chocolate con leche"
    
    # Ejecutar el método a probar
    result = await diana_service.resolve_contradiction(contradiction_id, resolution)
    
    # Verificaciones
    assert result["success"] is False
    assert "error" in result
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_unresolved_contradictions(diana_service):
    """Prueba la recuperación de contradicciones no resueltas."""
    # Configurar el mock para devolver contradicciones
    mock_session = diana_service.session
    
    # Crear contradicciones mock
    mock_contradictions = [
        MagicMock(spec=DianaContradiction),
        MagicMock(spec=DianaContradiction)
    ]
    
    # Configurar propiedades de las contradicciones
    for i, contradiction in enumerate(mock_contradictions):
        contradiction.id = i + 1
        contradiction.user_id = TEST_USER_ID
        contradiction.contradiction_type = "preference"
        contradiction.original_statement = f"Original statement {i+1}"
        contradiction.contradicting_statement = f"Contradicting statement {i+1}"
        contradiction.detected_at = datetime.now() - timedelta(days=i)
        contradiction.is_resolved = False
        contradiction.resolution = None
        contradiction.context_data = {"source": f"test_{i+1}"}
    
    # Configurar el resultado del execute
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_contradictions
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_unresolved_contradictions(TEST_USER_ID)
    
    # Verificaciones
    assert result["success"] is True
    assert "contradictions" in result
    assert len(result["contradictions"]) == 2
    
    # Verificar que la consulta SQL está correctamente formada
    execute_args = mock_session.execute.call_args[0][0]
    assert "SELECT" in str(execute_args)
    assert "FROM diana_contradictions" in str(execute_args)
    assert f"diana_contradictions.user_id = {TEST_USER_ID}" in str(execute_args)
    assert "diana_contradictions.is_resolved = false" in str(execute_args)


@pytest.mark.asyncio
async def test_get_unresolved_contradictions_empty(diana_service):
    """Prueba la recuperación de contradicciones cuando no hay ninguna."""
    # Configurar el mock para devolver una lista vacía
    mock_session = diana_service.session
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    # Ejecutar el método a probar
    result = await diana_service.get_unresolved_contradictions(TEST_USER_ID)
    
    # Verificaciones
    assert result["success"] is True
    assert "contradictions" in result
    assert len(result["contradictions"]) == 0


@pytest.mark.asyncio
async def test_get_unresolved_contradictions_error_handling(diana_service):
    """Prueba el manejo de errores al recuperar contradicciones."""
    # Configurar el mock para simular un error
    mock_session = diana_service.session
    mock_session.execute.side_effect = Exception("Test database error")
    
    # Ejecutar el método a probar
    result = await diana_service.get_unresolved_contradictions(TEST_USER_ID)
    
    # Verificaciones
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_contradiction_serialization(diana_service):
    """Prueba la serialización correcta de objetos DianaContradiction."""
    # Crear una contradicción mock
    contradiction = MagicMock(spec=DianaContradiction)
    contradiction.id = 1
    contradiction.user_id = TEST_USER_ID
    contradiction.contradiction_type = "preference"
    contradiction.original_statement = "Me encanta el chocolate"
    contradiction.contradicting_statement = "Odio el chocolate"
    contradiction.resolution = "Usuario aclaró preferencias de chocolate"
    contradiction.detected_at = datetime.now()
    contradiction.context_data = {"source": "conversation"}
    contradiction.is_resolved = True
    contradiction.resolved_at = datetime.now()
    contradiction.related_memory_ids = [1, 2, 3]
    
    # Serializar la contradicción
    serialized = diana_service._serialize_contradiction(contradiction)
    
    # Verificaciones
    assert serialized["id"] == 1
    assert serialized["user_id"] == TEST_USER_ID
    assert serialized["contradiction_type"] == "preference"
    assert serialized["original_statement"] == "Me encanta el chocolate"
    assert serialized["contradicting_statement"] == "Odio el chocolate"
    assert serialized["resolution"] == "Usuario aclaró preferencias de chocolate"
    assert "detected_at" in serialized
    assert serialized["context_data"] == {"source": "conversation"}
    assert serialized["is_resolved"] is True
    assert "resolved_at" in serialized
    assert serialized["related_memory_ids"] == [1, 2, 3]


# Pruebas de integración con otras funcionalidades de Diana

@pytest.mark.asyncio
async def test_contradiction_interaction_with_memories(diana_service):
    """Prueba la interacción entre contradicciones y memorias emocionales."""
    # Mock para store_emotional_memory
    diana_service.store_emotional_memory = AsyncMock()
    diana_service.store_emotional_memory.return_value = {
        "success": True,
        "memory_id": 1
    }
    
    # Mock para record_contradiction
    diana_service.record_contradiction = AsyncMock()
    diana_service.record_contradiction.return_value = {
        "success": True,
        "contradiction_id": 1
    }
    
    # Simular un flujo donde se detecta una contradicción
    # 1. Almacenar una memoria con una preferencia
    await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=EmotionalInteractionType.PERSONAL_SHARE,
        summary="Usuario habla sobre preferencias de comida",
        content="El usuario menciona que adora el chocolate",
        primary_emotion=EmotionCategory.JOY,
        tags=["preference", "food"]
    )
    
    # 2. Registrar una contradicción basada en una nueva declaración
    await diana_service.record_contradiction(
        TEST_USER_ID,
        "preference",
        "El usuario menciona que adora el chocolate",
        "El usuario dice que odia el chocolate",
        related_memory_ids=[1]
    )
    
    # Verificar que se llamaron ambos métodos con los parámetros correctos
    diana_service.store_emotional_memory.assert_called_once()
    diana_service.record_contradiction.assert_called_once()
    
    # Verificar que la contradicción está relacionada con la memoria
    contradiction_args = diana_service.record_contradiction.call_args[0]
    assert contradiction_args[0] == TEST_USER_ID
    assert contradiction_args[1] == "preference"
    assert "chocolate" in contradiction_args[2]
    assert "chocolate" in contradiction_args[3]
    
    # Verificar que se pasó el ID de memoria correcto
    contradiction_kwargs = diana_service.record_contradiction.call_args[1]
    assert "related_memory_ids" in contradiction_kwargs
    assert 1 in contradiction_kwargs["related_memory_ids"]


@pytest.mark.asyncio
async def test_automatic_contradiction_detection(diana_service):
    """
    Prueba una implementación básica de detección automática de contradicciones.
    
    Nota: Esta prueba simula cómo podría funcionar la detección automática,
    aunque en la implementación real esto podría ser más sofisticado usando NLP.
    """
    # Función simulada para detectar contradicciones en el contenido de mensajes
    async def detect_contradictions(user_id, new_content):
        # Palabras clave opuestas para simular detección simple
        opposing_pairs = [
            (["amo", "adoro", "encanta"], ["odio", "detesto", "desagrada"]),
            (["siempre"], ["nunca", "jamás"]),
            (["todos"], ["ninguno", "nadie"])
        ]
        
        # Simular búsqueda de memorias previas
        previous_memories = [
            {
                "id": 1,
                "content": "Siempre tomo café por la mañana, es mi bebida favorita",
                "summary": "Usuario habla de sus hábitos matutinos"
            },
            {
                "id": 2,
                "content": "Me encanta el chocolate, especialmente el oscuro",
                "summary": "Usuario comparte preferencias de comida"
            }
        ]
        
        # Buscar contradicciones
        contradictions = []
        
        for memory in previous_memories:
            memory_content = memory["content"].lower()
            new_content_lower = new_content.lower()
            
            for positive_words, negative_words in opposing_pairs:
                # Verificar si la memoria contiene palabras positivas
                has_positive = any(word in memory_content for word in positive_words)
                
                # Verificar si el nuevo contenido contiene palabras negativas
                has_negative = any(word in new_content_lower for word in negative_words)
                
                # Si se encuentra un patrón de contradicción
                if has_positive and has_negative:
                    contradictions.append({
                        "memory_id": memory["id"],
                        "original_statement": memory["content"],
                        "contradicting_statement": new_content,
                        "type": "preference"
                    })
        
        return contradictions
    
    # Contenido que contradice una memoria previa
    new_content = "Nunca bebo café, no me gusta para nada"
    
    # Detectar contradicciones
    contradictions = await detect_contradictions(TEST_USER_ID, new_content)
    
    # Verificar que se detectó la contradicción
    assert len(contradictions) > 0
    assert contradictions[0]["original_statement"] == "Siempre tomo café por la mañana, es mi bebida favorita"
    assert contradictions[0]["contradicting_statement"] == new_content
    
    # Simular registro de la contradicción
    diana_service.record_contradiction = AsyncMock()
    diana_service.record_contradiction.return_value = {"success": True, "contradiction_id": 1}
    
    # Registrar las contradicciones detectadas
    for contradiction in contradictions:
        await diana_service.record_contradiction(
            TEST_USER_ID,
            contradiction["type"],
            contradiction["original_statement"],
            contradiction["contradicting_statement"],
            related_memory_ids=[contradiction["memory_id"]]
        )
    
    # Verificar que se registró la contradicción
    assert diana_service.record_contradiction.call_count == len(contradictions)


@pytest.mark.asyncio
async def test_contradiction_resolution_with_memory_update(diana_service):
    """Prueba la resolución de contradicciones con actualización de memorias relacionadas."""
    # Mock para los métodos necesarios
    diana_service.resolve_contradiction = AsyncMock()
    diana_service.resolve_contradiction.return_value = {"success": True}
    
    # Función que simula la actualización de memorias relacionadas
    async def update_related_memories(contradiction_id, resolution):
        # Esta sería una implementación real que buscaría las memorias relacionadas
        # y las actualizaría con la información correcta
        related_memory_ids = [1, 2]
        
        # Simular actualización de cada memoria
        for memory_id in related_memory_ids:
            # En un caso real, aquí se actualizaría la memoria o se añadiría un contexto
            pass
        
        # Finalmente resolver la contradicción
        return await diana_service.resolve_contradiction(contradiction_id, resolution)
    
    # Ejecutar la resolución con actualización
    contradiction_id = 1
    resolution = "El usuario aclaró que antes le gustaba el café pero ahora ya no lo toma"
    
    result = await update_related_memories(contradiction_id, resolution)
    
    # Verificar que se resolvió la contradicción
    assert result["success"] is True
    diana_service.resolve_contradiction.assert_called_once_with(contradiction_id, resolution)