"""
Pruebas de carga y estrés para el sistema emocional de Diana.

Este módulo contiene pruebas que simulan altas cargas de trabajo para verificar
el rendimiento y la estabilidad del sistema emocional de Diana bajo estrés.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import random
from datetime import datetime, timedelta

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
BASE_USER_ID = 100000000
TEST_ITERATIONS = 5  # Reducido para pruebas rápidas, aumentar para pruebas de carga reales


@pytest.fixture
def mock_session():
    """Crea un mock de la sesión de base de datos optimizado para pruebas de carga."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    
    # Diccionarios para simular almacenamiento de datos
    stored_memories = {}
    stored_relationships = {}
    stored_adaptations = {}
    
    # Contador para IDs autogenerados
    id_counter = 1
    
    # Simular execute con respuestas rápidas
    async def mock_execute(query):
        result = AsyncMock()
        
        # Determinar el tipo de consulta basado en la cadena
        query_str = str(query)
        
        # SELECT para relationship
        if "SELECT" in query_str and "diana_relationship_states" in query_str:
            if "user_id =" in query_str:
                for user_id in stored_relationships:
                    if f"user_id = {user_id}" in query_str:
                        result.scalar_one_or_none.return_value = stored_relationships.get(user_id)
                        break
                else:
                    result.scalar_one_or_none.return_value = None
        
        # SELECT para adaptación
        elif "SELECT" in query_str and "diana_personality_adaptations" in query_str:
            if "user_id =" in query_str:
                for user_id in stored_adaptations:
                    if f"user_id = {user_id}" in query_str:
                        result.scalar_one_or_none.return_value = stored_adaptations.get(user_id)
                        break
                else:
                    result.scalar_one_or_none.return_value = None
        
        # SELECT para memorias
        elif "SELECT" in query_str and "diana_emotional_memories" in query_str:
            if "user_id =" in query_str:
                user_memories = []
                for memory in stored_memories.values():
                    for user_id in range(BASE_USER_ID, BASE_USER_ID + TEST_ITERATIONS):
                        if f"user_id = {user_id}" in query_str and memory.user_id == user_id:
                            user_memories.append(memory)
                
                # Simular LIMIT
                if "LIMIT" in query_str:
                    import re
                    limit_match = re.search(r"LIMIT\s+(\d+)", query_str)
                    if limit_match:
                        limit = int(limit_match.group(1))
                        user_memories = user_memories[:limit]
                
                result.scalars.return_value.all.return_value = user_memories
        
        return result
    
    # Simular add
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
            stored_adaptations[obj.user_id] = obj
    
    # Configurar los métodos mock
    session.execute.side_effect = mock_execute
    session.add.side_effect = mock_add
    
    # Métricas para pruebas de rendimiento
    session.metrics = {
        "add_calls": 0,
        "execute_calls": 0,
        "commit_calls": 0,
        "rollback_calls": 0
    }
    
    # Envolver métodos para contar llamadas
    original_add = session.add
    original_execute = session.execute
    original_commit = session.commit
    original_rollback = session.rollback
    
    def count_add(obj):
        session.metrics["add_calls"] += 1
        return original_add(obj)
    
    async def count_execute(query):
        session.metrics["execute_calls"] += 1
        return await original_execute(query)
    
    async def count_commit():
        session.metrics["commit_calls"] += 1
        return await original_commit()
    
    async def count_rollback():
        session.metrics["rollback_calls"] += 1
        return await original_rollback()
    
    session.add = count_add
    session.execute = count_execute
    session.commit = count_commit
    session.rollback = count_rollback
    
    return session


@pytest.fixture
def diana_service(mock_session):
    """Crea una instancia de DianaEmotionalService con una sesión mock."""
    service = DianaEmotionalService(mock_session)
    
    # Reemplazar métodos lentos con versiones optimizadas para pruebas
    service._create_default_relationship_state = AsyncMock()
    service._create_default_relationship_state.side_effect = lambda user_id: MagicMock(
        spec=DianaRelationshipState,
        user_id=user_id,
        status=RelationshipStatus.INITIAL,
        trust_level=0.1,
        rapport=0.1,
        familiarity=0.1,
        interaction_count=0,
        milestone_count=0,
        dominant_emotion=EmotionCategory.NEUTRAL,
        milestone_data={"status_changes": []},
        personality_adaptations={"emotion_counts": {}}
    )
    
    service._create_default_personality_adaptation = AsyncMock()
    service._create_default_personality_adaptation.side_effect = lambda user_id: MagicMock(
        spec=DianaPersonalityAdaptation,
        user_id=user_id,
        warmth=0.5,
        formality=0.5,
        humor=0.5,
        directness=0.5,
        emotional_expressiveness=0.5,
        emoji_usage=0.5
    )
    
    service._get_user_emotional_context = AsyncMock()
    service._get_user_emotional_context.return_value = {
        "primary_emotion": "joy",
        "context": {}
    }
    
    service._get_contextual_memory_reference = AsyncMock()
    service._get_contextual_memory_reference.return_value = ""
    
    # Patch para _enhance_by_action_type que es llamado pero no es crucial para las pruebas de carga
    service._enhance_by_action_type = AsyncMock()
    service._enhance_by_action_type.side_effect = lambda user_id, accion, resultado, *args, **kwargs: resultado
    
    return service


@pytest.mark.asyncio
async def test_concurrent_memory_storage(diana_service):
    """Prueba el almacenamiento concurrente de memorias emocionales."""
    start_time = time.time()
    
    # Crear tareas concurrentes para almacenar memorias
    tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        
        # Crear 3 memorias por usuario
        for j in range(3):
            interaction_type = random.choice(list(EmotionalInteractionType))
            primary_emotion = random.choice(list(EmotionCategory))
            intensity = random.choice(list(EmotionalIntensity))
            
            task = diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=interaction_type,
                summary=f"Test memory {j} for user {user_id}",
                content=f"Content for memory {j}, user {user_id}",
                primary_emotion=primary_emotion,
                intensity=intensity,
                importance_score=random.uniform(0.5, 2.0),
                tags=[f"tag{j}", "test"]
            )
            tasks.append(task)
    
    # Ejecutar todas las tareas concurrentemente
    results = await asyncio.gather(*tasks)
    
    # Verificar que todas las memorias se almacenaron con éxito
    success_count = sum(1 for result in results if result["success"])
    assert success_count == len(tasks)
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo de ejecución para almacenar {len(tasks)} memorias: {execution_time:.2f} segundos")
    
    # Verificar número de llamadas a la base de datos
    db_calls = diana_service.session.metrics["add_calls"]
    assert db_calls >= len(tasks)  # Al menos una llamada add por memoria
    
    # La ejecución debe ser razonablemente rápida
    assert execution_time < 2.0  # Ajustar según las expectativas de rendimiento


@pytest.mark.asyncio
async def test_concurrent_memory_retrieval(diana_service):
    """Prueba la recuperación concurrente de memorias emocionales."""
    # Primero, almacenar algunas memorias para tener datos que recuperar
    setup_tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        
        # Crear algunas memorias por usuario
        for j in range(3):
            task = diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=EmotionalInteractionType.GREETING,
                summary=f"Setup memory {j} for user {user_id}",
                content=f"Content for setup memory {j}, user {user_id}",
                primary_emotion=EmotionCategory.JOY,
                intensity=EmotionalIntensity.MODERATE
            )
            setup_tasks.append(task)
    
    # Esperar a que se completen las tareas de configuración
    await asyncio.gather(*setup_tasks)
    
    # Resetear métricas para la prueba real
    diana_service.session.metrics = {
        "add_calls": 0,
        "execute_calls": 0,
        "commit_calls": 0,
        "rollback_calls": 0
    }
    
    start_time = time.time()
    
    # Crear tareas concurrentes para recuperar memorias
    tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        
        # Diferentes tipos de consultas de memoria
        tasks.append(diana_service.get_recent_memories(user_id, limit=5))
        tasks.append(diana_service.get_memories_by_emotion(user_id, EmotionCategory.JOY, limit=5))
        tasks.append(diana_service.get_important_memories(user_id, min_importance=0.5, limit=5))
        tasks.append(diana_service.get_contextual_memories(user_id, tags=["test"], limit=5))
    
    # Ejecutar todas las tareas concurrentemente
    results = await asyncio.gather(*tasks)
    
    # Verificar que todas las consultas se completaron con éxito
    success_count = sum(1 for result in results if result["success"])
    assert success_count == len(tasks)
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo de ejecución para {len(tasks)} consultas de memoria: {execution_time:.2f} segundos")
    
    # Verificar número de llamadas a la base de datos
    db_calls = diana_service.session.metrics["execute_calls"]
    assert db_calls >= len(tasks)  # Al menos una llamada execute por consulta
    
    # La ejecución debe ser razonablemente rápida
    assert execution_time < 2.0  # Ajustar según las expectativas de rendimiento


@pytest.mark.asyncio
async def test_relationship_state_under_load(diana_service):
    """Prueba el rendimiento del sistema de relaciones bajo carga."""
    start_time = time.time()
    
    # Crear tareas concurrentes para actualizar relaciones
    tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        
        # Obtener estado inicial
        tasks.append(diana_service.get_relationship_state(user_id))
        
        # Registrar interacción
        tasks.append(diana_service.record_interaction(user_id))
        
        # Actualizar estado
        tasks.append(diana_service.update_relationship_status(
            user_id,
            random.choice([
                RelationshipStatus.ACQUAINTANCE,
                RelationshipStatus.FRIENDLY,
                RelationshipStatus.CLOSE
            ]),
            reason="Load test update"
        ))
    
    # Ejecutar todas las tareas concurrentemente
    results = await asyncio.gather(*tasks)
    
    # Verificar que todas las operaciones se completaron con éxito
    success_count = sum(1 for result in results if result["success"])
    assert success_count == len(tasks)
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo de ejecución para {len(tasks)} operaciones de relación: {execution_time:.2f} segundos")
    
    # La ejecución debe ser razonablemente rápida
    assert execution_time < 2.0  # Ajustar según las expectativas de rendimiento


@pytest.mark.asyncio
async def test_enhance_interaction_performance(diana_service):
    """Prueba el rendimiento de enhance_interaction bajo carga."""
    # Crear resultados base para mejorar
    base_results = [
        {
            "success": True,
            "message": f"Mensaje original #{i}",
            "points_awarded": 10,
            "total_points": 100 + i
        }
        for i in range(TEST_ITERATIONS)
    ]
    
    start_time = time.time()
    
    # Crear tareas concurrentes para mejorar interacciones
    tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        reaction_types = ["❤️", "👍", "😂", "😮", "👀"]
        
        task = diana_service.enhance_interaction(
            user_id,
            "reaccionar_publicacion",
            base_results[i],
            reaction_type=random.choice(reaction_types)
        )
        tasks.append(task)
    
    # Ejecutar todas las tareas concurrentemente
    results = await asyncio.gather(*tasks)
    
    # Verificar que todas las mejoras se completaron
    for i, result in enumerate(results):
        assert result["success"] is True
        assert "message" in result
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo de ejecución para {len(tasks)} mejoras de interacción: {execution_time:.2f} segundos")
    
    # La mejora de interacción implica varias operaciones, por lo que debe ser más lenta
    # pero aún razonablemente rápida
    assert execution_time < 3.0  # Ajustar según las expectativas de rendimiento


@pytest.mark.asyncio
async def test_mixed_operation_performance(diana_service):
    """Prueba el rendimiento con una mezcla de operaciones típicas de un flujo real."""
    start_time = time.time()
    
    # Simular varios usuarios interactuando con el sistema simultáneamente
    tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        
        # Secuencia de operaciones que simula un flujo típico
        async def user_flow(user_id):
            # 1. Obtener estado de relación
            relationship_result = await diana_service.get_relationship_state(user_id)
            
            # 2. Registrar interacción
            await diana_service.record_interaction(user_id)
            
            # 3. Almacenar una memoria emocional
            emotion = random.choice(list(EmotionCategory))
            await diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=EmotionalInteractionType.PERSONAL_SHARE,
                summary=f"User {user_id} shared something",
                content=f"Content for user {user_id}",
                primary_emotion=emotion
            )
            
            # 4. Mejorar una interacción
            base_result = {
                "success": True,
                "message": f"Mensaje original para usuario {user_id}",
                "points_awarded": 10
            }
            
            enhanced_result = await diana_service.enhance_interaction(
                user_id,
                "reaccionar_publicacion",
                base_result,
                reaction_type="❤️"
            )
            
            # 5. Obtener memoria reciente
            await diana_service.get_recent_memories(user_id)
            
            return {
                "user_id": user_id,
                "relationship": relationship_result.get("success"),
                "enhanced": enhanced_result.get("success")
            }
        
        tasks.append(user_flow(user_id))
    
    # Ejecutar todos los flujos de usuario concurrentemente
    results = await asyncio.gather(*tasks)
    
    # Verificar que todos los flujos se completaron
    for result in results:
        assert "user_id" in result
        assert result["relationship"] is True
        assert result["enhanced"] is True
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo de ejecución para {len(tasks)} flujos de usuario completos: {execution_time:.2f} segundos")
    
    # Este es un flujo completo con varias operaciones, por lo que tomará más tiempo
    assert execution_time < 5.0  # Ajustar según las expectativas de rendimiento
    
    # Verificar métricas de base de datos
    print(f"Llamadas a la base de datos: add={diana_service.session.metrics['add_calls']}, "
          f"execute={diana_service.session.metrics['execute_calls']}, "
          f"commit={diana_service.session.metrics['commit_calls']}")


@pytest.mark.asyncio
async def test_error_resilience_under_load(diana_service):
    """Prueba la resiliencia a errores bajo carga."""
    # Modificar algunos métodos para que fallen ocasionalmente
    original_store_memory = diana_service.store_emotional_memory
    original_get_relationship = diana_service.get_relationship_state
    
    # Hacer que store_emotional_memory falle aleatoriamente
    async def failing_store_memory(*args, **kwargs):
        if random.random() < 0.3:  # 30% de probabilidad de fallo
            raise Exception("Simulated random failure")
        return await original_store_memory(*args, **kwargs)
    
    # Hacer que get_relationship_state falle aleatoriamente
    async def failing_get_relationship(*args, **kwargs):
        if random.random() < 0.3:  # 30% de probabilidad de fallo
            raise Exception("Simulated random failure")
        return await original_get_relationship(*args, **kwargs)
    
    # Aplicar los mocks
    diana_service.store_emotional_memory = failing_store_memory
    diana_service.get_relationship_state = failing_get_relationship
    
    try:
        # Crear tareas que deben ser resilientes a fallos
        tasks = []
        for i in range(TEST_ITERATIONS):
            user_id = BASE_USER_ID + i
            
            # enhance_interaction debe manejar fallos internos
            base_result = {
                "success": True,
                "message": f"Mensaje original para usuario {user_id}",
                "points_awarded": 10
            }
            
            task = diana_service.enhance_interaction(
                user_id,
                "reaccionar_publicacion",
                base_result,
                reaction_type="❤️"
            )
            tasks.append(task)
        
        # Ejecutar tareas con posibles fallos internos
        results = await asyncio.gather(*tasks)
        
        # Verificar que todas las operaciones devolvieron resultados, incluso con fallos
        assert len(results) == len(tasks)
        
        # Los resultados deben mantener al menos el mensaje original
        for i, result in enumerate(results):
            assert result["success"] is True
            assert "message" in result
            assert "points_awarded" in result
            assert result["points_awarded"] == 10
        
    finally:
        # Restaurar los métodos originales
        diana_service.store_emotional_memory = original_store_memory
        diana_service.get_relationship_state = original_get_relationship


@pytest.mark.asyncio
async def test_memory_recall_update_performance(diana_service):
    """Prueba el rendimiento de las actualizaciones de recuerdo de memoria."""
    # Primero, almacenar algunas memorias
    setup_tasks = []
    for i in range(TEST_ITERATIONS):
        user_id = BASE_USER_ID + i
        task = diana_service.store_emotional_memory(
            user_id=user_id,
            interaction_type=EmotionalInteractionType.GREETING,
            summary=f"Memory for recall test, user {user_id}",
            content=f"Content for memory recall test, user {user_id}",
            primary_emotion=EmotionCategory.JOY
        )
        setup_tasks.append(task)
    
    setup_results = await asyncio.gather(*setup_tasks)
    memory_ids = [result["memory_id"] for result in setup_results if result["success"]]
    
    # Resetear métricas
    diana_service.session.metrics = {
        "add_calls": 0,
        "execute_calls": 0,
        "commit_calls": 0,
        "rollback_calls": 0
    }
    
    start_time = time.time()
    
    # Actualizar metadatos de recuerdo para todas las memorias
    await diana_service._update_memory_recall_metadata(memory_ids)
    
    # Verificar tiempo de ejecución
    execution_time = time.time() - start_time
    print(f"Tiempo para actualizar {len(memory_ids)} memorias: {execution_time:.2f} segundos")
    
    # Verificar llamadas a la base de datos - debería ser eficiente
    execute_calls = diana_service.session.metrics["execute_calls"]
    commit_calls = diana_service.session.metrics["commit_calls"]
    
    # La operación debe ser eficiente, haciendo pocas llamadas por memoria
    assert execute_calls <= len(memory_ids) * 2
    assert commit_calls <= 2
    
    # La ejecución debe ser rápida
    assert execution_time < 1.0  # Ajustar según las expectativas de rendimiento