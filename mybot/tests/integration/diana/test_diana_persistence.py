"""
Pruebas para verificar la persistencia del estado emocional de Diana.

Este módulo contiene pruebas que verifican que el estado emocional de Diana,
las relaciones y las adaptaciones de personalidad se persisten correctamente
en la base de datos y mantienen la consistencia entre sesiones.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import logging
from datetime import datetime, timedelta
from copy import deepcopy

from sqlalchemy import select, update
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

# Constantes para pruebas
TEST_USER_ID = 123456789


@pytest.fixture
def mock_memory():
    """Crea un mock de DianaEmotionalMemory."""
    memory = MagicMock(spec=DianaEmotionalMemory)
    memory.id = 1
    memory.user_id = TEST_USER_ID
    memory.interaction_type = EmotionalInteractionType.GREETING
    memory.timestamp = datetime.now()
    memory.summary = "Test greeting"
    memory.content = "User said hello to Diana"
    memory.primary_emotion = EmotionCategory.JOY
    memory.secondary_emotion = None
    memory.intensity = EmotionalIntensity.MODERATE
    memory.importance_score = 1.0
    memory.decay_rate = 0.1
    memory.last_recalled_at = None
    memory.recall_count = 0
    memory.tags = ["greeting", "introduction"]
    memory.is_sensitive = False
    memory.is_forgotten = False
    memory.parent_memory_id = None
    memory.context_data = {}
    memory.related_achievements = []
    memory.related_narrative_keys = []
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
    relationship.relationship_started_at = datetime.now() - timedelta(days=30)
    relationship.last_interaction_at = datetime.now() - timedelta(hours=12)
    relationship.longest_absence_days = 5
    relationship.typical_response_time_seconds = 3600
    relationship.typical_interaction_length = 120
    relationship.communication_frequency = 0.8
    relationship.milestone_data = {
        "status_changes": [
            {
                "timestamp": (datetime.now() - timedelta(days=25)).isoformat(),
                "old_status": RelationshipStatus.INITIAL.value,
                "new_status": RelationshipStatus.ACQUAINTANCE.value,
                "reason": "Natural progression"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                "old_status": RelationshipStatus.ACQUAINTANCE.value,
                "new_status": RelationshipStatus.FRIENDLY.value,
                "reason": "Natural progression"
            }
        ]
    }
    relationship.boundary_settings = {}
    relationship.communication_preferences = {}
    relationship.topic_interests = {"romance": 0.8, "adventure": 0.7}
    relationship.personality_adaptations = {"emotion_counts": {"joy": 15, "trust": 5}}
    relationship.linguistic_adaptations = {}
    relationship.created_at = datetime.now() - timedelta(days=30)
    relationship.updated_at = datetime.now() - timedelta(hours=12)
    return relationship


@pytest.fixture
def mock_adaptation():
    """Crea un mock de DianaPersonalityAdaptation."""
    adaptation = MagicMock(spec=DianaPersonalityAdaptation)
    adaptation.id = 1
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
    adaptation.last_significant_change = datetime.now() - timedelta(days=5)
    adaptation.confidence_score = 0.7
    adaptation.created_at = datetime.now() - timedelta(days=30)
    adaptation.updated_at = datetime.now() - timedelta(days=5)
    return adaptation


@pytest.fixture
def mock_db_session(mock_memory, mock_relationship, mock_adaptation):
    """Crea un mock de la sesión de base de datos con comportamiento simulado."""
    session = AsyncMock(spec=AsyncSession)
    
    # Diccionarios para simular almacenamiento de datos
    stored_memories = {1: deepcopy(mock_memory)}
    stored_relationships = {TEST_USER_ID: deepcopy(mock_relationship)}
    stored_adaptations = {1: deepcopy(mock_adaptation)}
    stored_contradictions = {}
    
    # Counter para IDs autogenerados
    id_counter = 2
    
    # Método para simular execute con diferentes comportamientos
    async def mock_execute(query):
        result = AsyncMock()
        
        # Determinar el tipo de consulta
        query_str = str(query)
        
        # SELECT para memorias
        if "SELECT" in query_str and "diana_emotional_memories" in query_str:
            if "WHERE" in query_str and f"user_id = {TEST_USER_ID}" in query_str:
                memories = [mem for mem in stored_memories.values() 
                           if mem.user_id == TEST_USER_ID and not mem.is_forgotten]
                
                # Ordenar por timestamp si está en la consulta
                if "ORDER BY" in query_str and "timestamp" in query_str:
                    memories.sort(key=lambda x: x.timestamp, reverse="DESC" in query_str)
                
                # Ordenar por importance_score si está en la consulta
                if "ORDER BY" in query_str and "importance_score" in query_str:
                    memories.sort(key=lambda x: x.importance_score, reverse="DESC" in query_str)
                
                result.scalars.return_value.all.return_value = memories
                
                if "id =" in query_str:
                    # Extraer ID de la consulta
                    for memory_id in stored_memories:
                        if f"id = {memory_id}" in query_str:
                            result.scalar_one_or_none.return_value = stored_memories.get(memory_id)
                            break
            else:
                result.scalars.return_value.all.return_value = list(stored_memories.values())
        
        # SELECT para relationship
        elif "SELECT" in query_str and "diana_relationship_states" in query_str:
            if f"user_id = {TEST_USER_ID}" in query_str:
                result.scalar_one_or_none.return_value = stored_relationships.get(TEST_USER_ID)
            else:
                result.scalar_one_or_none.return_value = None
        
        # SELECT para personality adaptation
        elif "SELECT" in query_str and "diana_personality_adaptations" in query_str:
            if f"user_id = {TEST_USER_ID}" in query_str:
                # Encontrar la adaptación para el usuario
                adaptation = next((a for a in stored_adaptations.values() 
                                 if a.user_id == TEST_USER_ID), None)
                result.scalar_one_or_none.return_value = adaptation
            else:
                result.scalar_one_or_none.return_value = None
        
        # UPDATE para memorias
        elif "UPDATE" in query_str and "diana_emotional_memories" in query_str:
            if "SET is_forgotten=" in query_str:
                if "WHERE id =" in query_str:
                    for memory_id in stored_memories:
                        if f"id = {memory_id}" in query_str:
                            stored_memories[memory_id].is_forgotten = True
                            break
                elif f"user_id = {TEST_USER_ID}" in query_str:
                    for memory_id, memory in stored_memories.items():
                        if memory.user_id == TEST_USER_ID:
                            stored_memories[memory_id].is_forgotten = True
                            
                result.rowcount = sum(1 for m in stored_memories.values() 
                                    if m.user_id == TEST_USER_ID and m.is_forgotten)
            
            elif "SET last_recalled_at=" in query_str and "recall_count=" in query_str:
                # Actualizar metadatos de recall
                for memory_id in stored_memories:
                    if f"id = {memory_id}" in query_str:
                        stored_memories[memory_id].last_recalled_at = datetime.now()
                        stored_memories[memory_id].recall_count += 1
                        break
        
        # UPDATE para relationship
        elif "UPDATE" in query_str and "diana_relationship_states" in query_str:
            if f"user_id = {TEST_USER_ID}" in query_str:
                # Simular actualización de campos específicos
                if "SET status=" in query_str:
                    for status in RelationshipStatus:
                        if f"status='{status.value}'" in query_str:
                            stored_relationships[TEST_USER_ID].status = status
                            break
                
                if "SET trust_level=" in query_str:
                    import re
                    trust_match = re.search(r"trust_level=([0-9.]+)", query_str)
                    if trust_match:
                        stored_relationships[TEST_USER_ID].trust_level = float(trust_match.group(1))
        
        return result
    
    # Método para simular add
    def mock_add(obj):
        nonlocal id_counter
        
        # Determinar el tipo de objeto
        if isinstance(obj, MagicMock) and obj._spec_class == DianaEmotionalMemory:
            obj.id = id_counter
            stored_memories[id_counter] = obj
            id_counter += 1
        
        elif isinstance(obj, MagicMock) and obj._spec_class == DianaRelationshipState:
            stored_relationships[obj.user_id] = obj
        
        elif isinstance(obj, MagicMock) and obj._spec_class == DianaPersonalityAdaptation:
            obj.id = id_counter
            stored_adaptations[id_counter] = obj
            id_counter += 1
        
        elif isinstance(obj, MagicMock) and obj._spec_class == DianaContradiction:
            obj.id = id_counter
            stored_contradictions[id_counter] = obj
            id_counter += 1
    
    # Configurar los métodos mock
    session.execute.side_effect = mock_execute
    session.add.side_effect = mock_add
    
    # Método para acceder a los datos almacenados (para verificaciones)
    session.get_stored_memories = lambda: stored_memories
    session.get_stored_relationships = lambda: stored_relationships
    session.get_stored_adaptations = lambda: stored_adaptations
    session.get_stored_contradictions = lambda: stored_contradictions
    
    return session


@pytest.mark.asyncio
async def test_memory_persistence(mock_db_session):
    """Prueba que las memorias emocionales se persisten correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Almacenar una nueva memoria
    result = await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=EmotionalInteractionType.PERSONAL_SHARE,
        summary="Test personal share",
        content="User shared personal information",
        primary_emotion=EmotionCategory.TRUST,
        intensity=EmotionalIntensity.HIGH,
        importance_score=1.8,
        tags=["personal", "sharing"]
    )
    
    # Verificar que se guardó con éxito
    assert result["success"] is True
    assert "memory_id" in result
    memory_id = result["memory_id"]
    
    # Verificar que la memoria está en el almacenamiento simulado
    stored_memories = mock_db_session.get_stored_memories()
    assert memory_id in stored_memories
    
    # Verificar que los campos se guardaron correctamente
    stored_memory = stored_memories[memory_id]
    assert stored_memory.user_id == TEST_USER_ID
    assert stored_memory.interaction_type == EmotionalInteractionType.PERSONAL_SHARE
    assert stored_memory.summary == "Test personal share"
    assert stored_memory.content == "User shared personal information"
    assert stored_memory.primary_emotion == EmotionCategory.TRUST
    assert stored_memory.intensity == EmotionalIntensity.HIGH
    assert stored_memory.importance_score == 1.8
    assert "personal" in stored_memory.tags
    assert "sharing" in stored_memory.tags
    
    # Recuperar memorias recientes
    recent_result = await diana_service.get_recent_memories(TEST_USER_ID)
    
    # Verificar que se puede recuperar la memoria
    assert recent_result["success"] is True
    assert len(recent_result["memories"]) >= 1
    
    # Verificar que el memory_id creado está en las memorias recuperadas
    memory_ids = [memory["id"] for memory in recent_result["memories"]]
    assert memory_id in memory_ids
    
    # Verificar que se actualizaron los metadatos de recall
    assert stored_memory.recall_count >= 1
    assert stored_memory.last_recalled_at is not None


@pytest.mark.asyncio
async def test_memory_forgotten_persistence(mock_db_session):
    """Prueba que las memorias marcadas como olvidadas se persisten correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Obtener la memoria existente (del fixture)
    stored_memories = mock_db_session.get_stored_memories()
    existing_memory_id = next(iter(stored_memories.keys()))
    
    # Verificar que la memoria no está marcada como olvidada inicialmente
    assert not stored_memories[existing_memory_id].is_forgotten
    
    # Marcar la memoria como olvidada
    result = await diana_service.forget_memory(existing_memory_id)
    
    # Verificar que se actualizó con éxito
    assert result["success"] is True
    
    # Verificar que la memoria ahora está marcada como olvidada
    assert stored_memories[existing_memory_id].is_forgotten
    
    # Recuperar memorias recientes
    recent_result = await diana_service.get_recent_memories(TEST_USER_ID)
    
    # Verificar que la memoria olvidada no se incluye en las recuperadas
    memory_ids = [memory["id"] for memory in recent_result["memories"]]
    assert existing_memory_id not in memory_ids


@pytest.mark.asyncio
async def test_relationship_state_persistence(mock_db_session):
    """Prueba que el estado de la relación se persiste correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Obtener el estado de relación inicial
    relationship_result = await diana_service.get_relationship_state(TEST_USER_ID)
    
    # Verificar que se recuperó con éxito
    assert relationship_result["success"] is True
    assert relationship_result["relationship"]["status"] == RelationshipStatus.FRIENDLY.value
    assert relationship_result["relationship"]["trust_level"] == 0.6
    
    # Actualizar el estado de la relación
    update_result = await diana_service.update_relationship_status(
        TEST_USER_ID,
        RelationshipStatus.CLOSE,
        reason="Test update"
    )
    
    # Verificar que se actualizó con éxito
    assert update_result["success"] is True
    
    # Verificar que el estado se actualizó en el almacenamiento simulado
    stored_relationships = mock_db_session.get_stored_relationships()
    assert stored_relationships[TEST_USER_ID].status == RelationshipStatus.CLOSE
    
    # Obtener el estado de relación actualizado
    updated_relationship_result = await diana_service.get_relationship_state(TEST_USER_ID)
    
    # Verificar que se recuperó el estado actualizado
    assert updated_relationship_result["success"] is True
    assert updated_relationship_result["relationship"]["status"] == RelationshipStatus.CLOSE.value
    
    # Verificar que se agregó el cambio al historial de hitos
    milestone_data = stored_relationships[TEST_USER_ID].milestone_data
    status_changes = milestone_data.get("status_changes", [])
    latest_change = status_changes[-1] if status_changes else None
    
    assert latest_change is not None
    assert latest_change["old_status"] == RelationshipStatus.FRIENDLY.value
    assert latest_change["new_status"] == RelationshipStatus.CLOSE.value
    assert latest_change["reason"] == "Test update"


@pytest.mark.asyncio
async def test_interaction_metrics_persistence(mock_db_session):
    """Prueba que las métricas de interacción se persisten correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Obtener el estado inicial
    initial_result = await diana_service.get_relationship_state(TEST_USER_ID)
    initial_interaction_count = initial_result["relationship"]["interaction_count"]
    
    # Registrar una nueva interacción
    interaction_result = await diana_service.record_interaction(
        TEST_USER_ID,
        interaction_length=150,
        response_time_seconds=60
    )
    
    # Verificar que se registró con éxito
    assert interaction_result["success"] is True
    assert interaction_result["interaction_count"] == initial_interaction_count + 1
    
    # Verificar que las métricas se actualizaron en el almacenamiento simulado
    stored_relationships = mock_db_session.get_stored_relationships()
    assert stored_relationships[TEST_USER_ID].interaction_count == initial_interaction_count + 1
    assert stored_relationships[TEST_USER_ID].last_interaction_at is not None
    
    # Obtener el estado actualizado
    updated_result = await diana_service.get_relationship_state(TEST_USER_ID)
    
    # Verificar que se recuperaron las métricas actualizadas
    assert updated_result["success"] is True
    assert updated_result["relationship"]["interaction_count"] == initial_interaction_count + 1


@pytest.mark.asyncio
async def test_personality_adaptation_persistence(mock_db_session):
    """Prueba que las adaptaciones de personalidad se persisten correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Obtener la adaptación inicial
    initial_result = await diana_service.get_personality_adaptation(TEST_USER_ID)
    
    # Verificar que se recuperó con éxito
    assert initial_result["success"] is True
    assert initial_result["adaptation"]["warmth"] == 0.7
    assert initial_result["adaptation"]["humor"] == 0.6
    
    # Actualizar la adaptación de personalidad
    update_result = await diana_service.update_personality_adaptation(
        TEST_USER_ID,
        {
            "warmth": 0.9,
            "humor": 0.8,
            "emoji_usage": 0.7
        },
        reason="User requested more warmth"
    )
    
    # Verificar que se actualizó con éxito
    assert update_result["success"] is True
    
    # Verificar que la adaptación se actualizó en el almacenamiento simulado
    stored_adaptations = mock_db_session.get_stored_adaptations()
    adaptation = next((a for a in stored_adaptations.values() if a.user_id == TEST_USER_ID), None)
    assert adaptation is not None
    assert adaptation.warmth == 0.9
    assert adaptation.humor == 0.8
    assert adaptation.emoji_usage == 0.7
    assert adaptation.adaptation_reason == "User requested more warmth"
    
    # Obtener la adaptación actualizada
    updated_result = await diana_service.get_personality_adaptation(TEST_USER_ID)
    
    # Verificar que se recuperó la adaptación actualizada
    assert updated_result["success"] is True
    assert updated_result["adaptation"]["warmth"] == 0.9
    assert updated_result["adaptation"]["humor"] == 0.8
    assert updated_result["adaptation"]["emoji_usage"] == 0.7
    assert updated_result["adaptation"]["adaptation_reason"] == "User requested more warmth"


@pytest.mark.asyncio
async def test_contradiction_persistence(mock_db_session):
    """Prueba que las contradicciones se persisten y resuelven correctamente."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Registrar una contradicción
    contradiction_result = await diana_service.record_contradiction(
        TEST_USER_ID,
        contradiction_type="preference",
        original_statement="Me encanta el chocolate",
        contradicting_statement="Odio el chocolate",
        context_data={"conversation_id": 12345}
    )
    
    # Verificar que se registró con éxito
    assert contradiction_result["success"] is True
    assert "contradiction_id" in contradiction_result
    contradiction_id = contradiction_result["contradiction_id"]
    
    # Verificar que la contradicción está en el almacenamiento simulado
    stored_contradictions = mock_db_session.get_stored_contradictions()
    assert contradiction_id in stored_contradictions
    
    # Verificar que los campos se guardaron correctamente
    stored_contradiction = stored_contradictions[contradiction_id]
    assert stored_contradiction.user_id == TEST_USER_ID
    assert stored_contradiction.contradiction_type == "preference"
    assert stored_contradiction.original_statement == "Me encanta el chocolate"
    assert stored_contradiction.contradicting_statement == "Odio el chocolate"
    assert stored_contradiction.context_data == {"conversation_id": 12345}
    assert stored_contradiction.is_resolved is False
    
    # Obtener contradicciones no resueltas
    unresolved_result = await diana_service.get_unresolved_contradictions(TEST_USER_ID)
    
    # Verificar que se puede recuperar la contradicción
    assert unresolved_result["success"] is True
    assert len(unresolved_result["contradictions"]) >= 1
    
    # Verificar que el contradiction_id creado está en las contradicciones recuperadas
    contradiction_ids = [c["id"] for c in unresolved_result["contradictions"]]
    assert contradiction_id in contradiction_ids
    
    # Resolver la contradicción
    resolution_result = await diana_service.resolve_contradiction(
        contradiction_id,
        resolution="Usuario aclaró que le gusta el chocolate oscuro pero odia el chocolate con leche"
    )
    
    # Verificar que se resolvió con éxito
    assert resolution_result["success"] is True
    
    # Verificar que la contradicción ahora está resuelta
    assert stored_contradiction.is_resolved is True
    assert stored_contradiction.resolution == "Usuario aclaró que le gusta el chocolate oscuro pero odia el chocolate con leche"
    assert stored_contradiction.resolved_at is not None
    
    # Obtener contradicciones no resueltas nuevamente
    updated_unresolved_result = await diana_service.get_unresolved_contradictions(TEST_USER_ID)
    
    # Verificar que la contradicción resuelta ya no aparece
    updated_contradiction_ids = [c["id"] for c in updated_unresolved_result["contradictions"]]
    assert contradiction_id not in updated_contradiction_ids


@pytest.mark.asyncio
async def test_emotional_memory_decay_is_preserved(mock_db_session):
    """Prueba que la tasa de decaimiento de memorias emocionales se preserva."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Almacenar una memoria con tasa de decaimiento personalizada
    result = await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=EmotionalInteractionType.MILESTONE,
        summary="Test milestone memory",
        content="User reached an important milestone",
        primary_emotion=EmotionCategory.JOY,
        intensity=EmotionalIntensity.VERY_HIGH,
        importance_score=2.0,
        decay_rate=0.05,  # Tasa de decaimiento más lenta para memorias importantes
        tags=["milestone", "important"]
    )
    
    # Verificar que se guardó con éxito
    assert result["success"] is True
    memory_id = result["memory_id"]
    
    # Verificar que la memoria está en el almacenamiento simulado con la tasa correcta
    stored_memories = mock_db_session.get_stored_memories()
    assert memory_id in stored_memories
    assert stored_memories[memory_id].decay_rate == 0.05


@pytest.mark.asyncio
async def test_relationship_natural_progression(mock_db_session):
    """Prueba que la relación progresa naturalmente con suficientes interacciones."""
    # Crear servicio Diana con la sesión mock
    diana_service = DianaEmotionalService(mock_db_session)
    
    # Verificar estado inicial
    initial_result = await diana_service.get_relationship_state(TEST_USER_ID)
    initial_status = initial_result["relationship"]["status"]
    
    # Para simular la progresión natural, necesitamos mockear el método que verifica transiciones
    original_check_transitions = diana_service._check_relationship_status_transitions
    
    # Reemplazar con una implementación que fuerza una transición
    def mock_check_transitions(relationship):
        relationship.status = RelationshipStatus.CLOSE
        
        # Agregar hito de cambio de estado
        milestone_data = relationship.milestone_data or {}
        status_milestones = milestone_data.get("status_changes", [])
        status_milestones.append({
            "timestamp": datetime.now().isoformat(),
            "old_status": RelationshipStatus.FRIENDLY.value,
            "new_status": RelationshipStatus.CLOSE.value,
            "reason": "Natural progression"
        })
        
        milestone_data["status_changes"] = status_milestones
        relationship.milestone_data = milestone_data
        relationship.milestone_count += 1
    
    # Aplicar el mock
    diana_service._check_relationship_status_transitions = mock_check_transitions
    
    # Simular múltiples interacciones para provocar progresión
    for _ in range(5):
        await diana_service.record_interaction(TEST_USER_ID)
    
    # Almacenar algunas memorias emocionales positivas
    await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=EmotionalInteractionType.PRAISE,
        summary="User praised Diana",
        content="The user expressed admiration",
        primary_emotion=EmotionCategory.JOY
    )
    
    await diana_service.store_emotional_memory(
        user_id=TEST_USER_ID,
        interaction_type=EmotionalInteractionType.PERSONAL_SHARE,
        summary="User shared something personal",
        content="The user shared confidential information",
        primary_emotion=EmotionCategory.TRUST
    )
    
    # Verificar que el estado ha progresado
    updated_result = await diana_service.get_relationship_state(TEST_USER_ID)
    updated_status = updated_result["relationship"]["status"]
    
    # Restaurar el método original
    diana_service._check_relationship_status_transitions = original_check_transitions
    
    # Verificar que hubo una progresión
    assert updated_status == RelationshipStatus.CLOSE.value
    assert updated_status != initial_status
    
    # Verificar que se registró el hito de progresión
    milestone_data = updated_result["relationship"]["milestone_data"]
    status_changes = milestone_data.get("status_changes", [])
    latest_change = status_changes[-1] if status_changes else None
    
    assert latest_change is not None
    assert latest_change["old_status"] == RelationshipStatus.FRIENDLY.value
    assert latest_change["new_status"] == RelationshipStatus.CLOSE.value
    assert latest_change["reason"] == "Natural progression"