"""
Tests para verificar el comportamiento del sistema administrativo de narrativa
bajo operaciones concurrentes y cargas de trabajo simultáneas.
"""
import pytest
import asyncio
import uuid
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.fixture
async def fragment_template() -> Dict[str, Any]:
    """Template para crear fragmentos de prueba."""
    return {
        "title": "Fragmento concurrente",
        "content": "Contenido del fragmento para pruebas concurrentes",
        "fragment_type": "STORY",
        "is_active": True
    }


@pytest.mark.asyncio
async def test_concurrent_admin_operations(session: AsyncSession, fragment_template):
    """Verificar que el sistema maneja 50+ operaciones administrativas concurrentes."""
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    # Crear fragmento base para pruebas de actualización
    base_fragment = NarrativeFragment(**fragment_template)
    session.add(base_fragment)
    await session.commit()
    await session.refresh(base_fragment)
    base_fragment_id = base_fragment.id
    
    async def create_fragment(index: int) -> str:
        """Tarea para crear un fragmento."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            fragment_data = {
                "title": f"Fragmento concurrente {index}",
                "content": f"Contenido del fragmento concurrente {index}",
                "fragment_type": "STORY" if index % 3 == 0 else ("DECISION" if index % 3 == 1 else "INFO")
            }
            result = await admin_service.create_fragment(fragment_data)
            return result["id"]
    
    async def update_fragment(index: int) -> None:
        """Tarea para actualizar un fragmento."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            update_data = {
                "title": f"Fragmento base actualizado {index}",
                "content": f"Contenido actualizado concurrentemente {index}"
            }
            await admin_service.update_fragment(base_fragment_id, update_data)
    
    async def get_fragments() -> int:
        """Tarea para obtener la lista de fragmentos."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            result = await admin_service.get_all_fragments(page=1, limit=100)
            return result["total"]
    
    async def get_fragment_details(fragment_id: str) -> Dict[str, Any]:
        """Tarea para obtener detalles de un fragmento."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            return await admin_service.get_fragment_details(fragment_id)
    
    # Crear 25 fragmentos concurrentemente
    creation_tasks = [create_fragment(i) for i in range(25)]
    created_ids = await asyncio.gather(*creation_tasks)
    
    # Verificar que se crearon todos los fragmentos
    assert len(created_ids) == 25
    assert all(isinstance(id, str) for id in created_ids)
    
    # Realizar 10 actualizaciones concurrentes del mismo fragmento
    update_tasks = [update_fragment(i) for i in range(10)]
    await asyncio.gather(*update_tasks)
    
    # Realizar 15 consultas concurrentes
    query_tasks = [get_fragments() for _ in range(15)]
    query_results = await asyncio.gather(*query_tasks)
    
    # Verificar que todas las consultas retornaron al menos 25 fragmentos
    assert all(count >= 25 for count in query_results)
    
    # Obtener detalles de fragmentos concurrentemente
    detail_tasks = [get_fragment_details(id) for id in created_ids[:10]]
    detail_results = await asyncio.gather(*detail_tasks)
    
    # Verificar que se obtuvieron los detalles correctamente
    assert len(detail_results) == 10
    assert all(isinstance(result, dict) for result in detail_results)
    assert all("title" in result for result in detail_results)


@pytest.mark.asyncio
async def test_concurrent_connection_updates(session: AsyncSession, fragment_template):
    """Verificar que las actualizaciones concurrentes de conexiones se manejan correctamente."""
    # Crear varios fragmentos para las pruebas
    fragments = []
    for i in range(5):
        fragment = NarrativeFragment(
            title=f"Fragmento para conexiones {i}",
            content=f"Contenido del fragmento {i}",
            fragment_type="DECISION" if i % 2 == 0 else "STORY",
            is_active=True
        )
        fragments.append(fragment)
    
    session.add_all(fragments)
    await session.commit()
    
    for fragment in fragments:
        await session.refresh(fragment)
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    async def update_connections(source_index: int, target_indices: List[int]) -> None:
        """Tarea para actualizar conexiones de un fragmento."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            
            connections = []
            for idx in target_indices:
                if idx < len(fragments):
                    connections.append({
                        "text": f"Ir a fragmento {idx}",
                        "next_fragment": fragments[idx].id
                    })
            
            if source_index < len(fragments):
                await admin_service.update_fragment_connections(fragments[source_index].id, connections)
    
    # Realizar actualizaciones concurrentes de conexiones
    connection_tasks = [
        update_connections(0, [1, 2]),
        update_connections(0, [3, 4]),  # Conflicto deliberado con la tarea anterior
        update_connections(2, [0, 4]),
        update_connections(3, [0, 1])
    ]
    
    await asyncio.gather(*connection_tasks)
    
    # Verificar el estado final de las conexiones
    for fragment in fragments:
        await session.refresh(fragment)
    
    # El fragmento 0 debería tener las conexiones de la última actualización (3 y 4)
    assert len(fragments[0].choices) == 2
    target_ids = [choice["next_fragment"] for choice in fragments[0].choices]
    assert fragments[3].id in target_ids or fragments[4].id in target_ids


@pytest.mark.asyncio
async def test_concurrent_user_narrative_updates(session: AsyncSession, fragment_template):
    """Verificar que las actualizaciones concurrentes de estados narrativos de usuario se manejan correctamente."""
    # Crear fragmentos para las pruebas
    fragments = []
    for i in range(3):
        fragment = NarrativeFragment(
            title=f"Fragmento para usuarios {i}",
            content=f"Contenido del fragmento {i}",
            fragment_type="STORY",
            is_active=True
        )
        fragments.append(fragment)
    
    session.add_all(fragments)
    await session.commit()
    
    for fragment in fragments:
        await session.refresh(fragment)
    
    # Crear estado narrativo de usuario
    user_id = 12345
    user_state = UserNarrativeState(
        user_id=user_id,
        current_fragment_id=fragments[0].id,
        visited_fragments=[fragments[0].id],
        completed_fragments=[],
        unlocked_clues=[]
    )
    
    session.add(user_state)
    await session.commit()
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    class TestNarrativeService:
        """Servicio de prueba para simular actualizaciones de progreso."""
        
        def __init__(self, session):
            self.session = session
        
        async def update_visited_fragments(self, user_id, fragment_id):
            """Actualiza fragmentos visitados del usuario."""
            query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(query)
            state = result.scalar_one_or_none()
            
            if not state:
                return False
            
            if fragment_id not in state.visited_fragments:
                state.visited_fragments.append(fragment_id)
            
            state.current_fragment_id = fragment_id
            await self.session.commit()
            return True
        
        async def update_completed_fragments(self, user_id, fragment_id):
            """Actualiza fragmentos completados del usuario."""
            query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(query)
            state = result.scalar_one_or_none()
            
            if not state:
                return False
            
            if fragment_id not in state.completed_fragments:
                state.completed_fragments.append(fragment_id)
            
            await self.session.commit()
            return True
        
        async def update_unlocked_clues(self, user_id, clue_code):
            """Actualiza pistas desbloqueadas del usuario."""
            query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(query)
            state = result.scalar_one_or_none()
            
            if not state:
                return False
            
            if clue_code not in state.unlocked_clues:
                state.unlocked_clues.append(clue_code)
            
            await self.session.commit()
            return True
    
    async def update_user_visits(fragment_index: int) -> None:
        """Tarea para actualizar fragmentos visitados."""
        async with session_factory() as local_session:
            service = TestNarrativeService(local_session)
            await service.update_visited_fragments(user_id, fragments[fragment_index].id)
    
    async def update_user_completions(fragment_index: int) -> None:
        """Tarea para actualizar fragmentos completados."""
        async with session_factory() as local_session:
            service = TestNarrativeService(local_session)
            await service.update_completed_fragments(user_id, fragments[fragment_index].id)
    
    async def update_user_clues(clue_index: int) -> None:
        """Tarea para actualizar pistas desbloqueadas."""
        async with session_factory() as local_session:
            service = TestNarrativeService(local_session)
            await service.update_unlocked_clues(user_id, f"PISTA_{clue_index}")
    
    # Realizar actualizaciones concurrentes
    update_tasks = [
        update_user_visits(1),
        update_user_visits(2),
        update_user_completions(0),
        update_user_completions(1),
        update_user_clues(1),
        update_user_clues(2)
    ]
    
    await asyncio.gather(*update_tasks)
    
    # Verificar el estado final del usuario
    await session.refresh(user_state)
    
    # Verificar visitados (debe incluir todos)
    for fragment in fragments:
        assert fragment.id in user_state.visited_fragments
    
    # Verificar completados (debe incluir al menos 0 y 1)
    assert fragments[0].id in user_state.completed_fragments
    assert fragments[1].id in user_state.completed_fragments
    
    # Verificar pistas (debe incluir PISTA_1 y PISTA_2)
    assert "PISTA_1" in user_state.unlocked_clues
    assert "PISTA_2" in user_state.unlocked_clues


@pytest.mark.asyncio
async def test_concurrent_fragment_stats_queries(session: AsyncSession, fragment_template):
    """Verificar que las consultas concurrentes de estadísticas no interfieren entre sí."""
    # Crear un fragmento con varios usuarios
    fragment = NarrativeFragment(**fragment_template)
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear varios estados de usuario que referencian al fragmento
    user_states = []
    for i in range(20):
        user_state = UserNarrativeState(
            user_id=20000 + i,
            current_fragment_id=fragment.id if i < 10 else None,
            visited_fragments=[fragment.id],
            completed_fragments=[fragment.id] if i < 15 else [],
            unlocked_clues=[]
        )
        user_states.append(user_state)
    
    session.add_all(user_states)
    await session.commit()
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    async def get_fragment_stats() -> Dict[str, Any]:
        """Tarea para obtener estadísticas del fragmento."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            return await admin_service.get_fragment_engagement(fragment.id)
    
    async def get_narrative_stats() -> Dict[str, Any]:
        """Tarea para obtener estadísticas narrativas globales."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            return await admin_service.get_narrative_stats()
    
    # Realizar consultas concurrentes
    query_tasks = []
    for _ in range(10):
        query_tasks.append(get_fragment_stats())
    for _ in range(10):
        query_tasks.append(get_narrative_stats())
    
    results = await asyncio.gather(*query_tasks)
    
    # Verificar que todas las consultas retornaron resultados válidos
    for result in results[:10]:  # Resultados de get_fragment_stats
        assert result["fragment_id"] == fragment.id
        assert result["visited_users"] == 20
        assert result["completed_users"] == 15
        assert result["active_users"] == 10
    
    for result in results[10:]:  # Resultados de get_narrative_stats
        assert result["total_fragments"] >= 1
        assert result["users_in_narrative"] >= 20


@pytest.mark.asyncio
async def test_concurrent_event_emission(session: AsyncSession, fragment_template):
    """Verificar que la emisión concurrente de eventos se maneja correctamente."""
    # Crear un mock del event bus con contador
    event_count = 0
    
    class MockEventBus:
        async def publish(self, *args, **kwargs):
            nonlocal event_count
            event_count += 1
    
    mock_event_bus = MockEventBus()
    
    with patch('services.narrative_admin_service.get_event_bus', return_value=mock_event_bus):
        # Obtener factory para crear sesiones concurrentes
        session_factory = session.async_session.async_sessionmaker
        
        async def create_and_update_fragment():
            """Tarea para crear y actualizar un fragmento."""
            async with session_factory() as local_session:
                admin_service = NarrativeAdminService(local_session)
                
                # Crear fragmento
                data = {
                    "title": f"Fragmento evento {uuid.uuid4()}",
                    "content": "Contenido de prueba",
                    "fragment_type": "STORY"
                }
                fragment = await admin_service.create_fragment(data)
                
                # Actualizar fragmento
                await admin_service.update_fragment(fragment["id"], {
                    "title": "Título actualizado"
                })
                
                # Eliminar fragmento
                await admin_service.delete_fragment(fragment["id"])
        
        # Ejecutar operaciones concurrentes que emiten eventos
        tasks = [create_and_update_fragment() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Verificar que se emitieron todos los eventos esperados
        # Cada tarea emite 3 eventos (crear, actualizar, eliminar)
        assert event_count == 15


@pytest.mark.asyncio
async def test_stress_test_multiple_operations(session: AsyncSession):
    """Prueba de estrés con múltiples operaciones concurrentes de diferentes tipos."""
    # Crear fragmentos iniciales
    fragments = []
    for i in range(10):
        fragment = NarrativeFragment(
            title=f"Fragmento de estrés {i}",
            content=f"Contenido del fragmento {i}",
            fragment_type="STORY" if i % 3 == 0 else ("DECISION" if i % 3 == 1 else "INFO"),
            is_active=True
        )
        fragments.append(fragment)
    
    session.add_all(fragments)
    await session.commit()
    
    for fragment in fragments:
        await session.refresh(fragment)
    
    # Crear usuarios iniciales
    user_states = []
    for i in range(10):
        user_state = UserNarrativeState(
            user_id=30000 + i,
            current_fragment_id=fragments[i % len(fragments)].id,
            visited_fragments=[fragments[j].id for j in range(min(i+1, len(fragments)))],
            completed_fragments=[fragments[j].id for j in range(min(i, len(fragments)))],
            unlocked_clues=[f"PISTA_{j}" for j in range(i % 5)]
        )
        user_states.append(user_state)
    
    session.add_all(user_states)
    await session.commit()
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    async def random_operation(index: int):
        """Realiza una operación aleatoria basada en el índice."""
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            
            # Distribuir operaciones según el índice
            operation_type = index % 8
            
            if operation_type == 0:
                # Crear fragmento
                data = {
                    "title": f"Nuevo fragmento {index}",
                    "content": f"Contenido del nuevo fragmento {index}",
                    "fragment_type": "STORY"
                }
                return await admin_service.create_fragment(data)
            
            elif operation_type == 1:
                # Actualizar fragmento
                fragment_index = index % len(fragments)
                fragment_id = fragments[fragment_index].id
                data = {
                    "title": f"Fragmento actualizado {index}",
                    "content": f"Contenido actualizado {index}"
                }
                return await admin_service.update_fragment(fragment_id, data)
            
            elif operation_type == 2:
                # Obtener fragmento
                fragment_index = index % len(fragments)
                fragment_id = fragments[fragment_index].id
                return await admin_service.get_fragment_details(fragment_id)
            
            elif operation_type == 3:
                # Listar fragmentos
                return await admin_service.get_all_fragments(page=1, limit=10)
            
            elif operation_type == 4:
                # Obtener conexiones
                fragment_index = index % len(fragments)
                fragment_id = fragments[fragment_index].id
                return await admin_service.get_fragment_connections(fragment_id)
            
            elif operation_type == 5:
                # Actualizar conexiones
                fragment_index = index % len(fragments)
                target_index = (index + 1) % len(fragments)
                fragment_id = fragments[fragment_index].id
                target_id = fragments[target_index].id
                
                connections = [{
                    "text": f"Conexión de estrés {index}",
                    "next_fragment": target_id
                }]
                
                return await admin_service.update_fragment_connections(fragment_id, connections)
            
            elif operation_type == 6:
                # Obtener progreso de usuario
                user_index = index % len(user_states)
                user_id = user_states[user_index].user_id
                return await admin_service.get_user_narrative_progress(user_id)
            
            else:
                # Obtener estadísticas
                return await admin_service.get_narrative_stats()
    
    # Ejecutar múltiples operaciones concurrentes
    tasks = [random_operation(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verificar que no hubo excepciones fatales
    for result in results:
        assert not isinstance(result, Exception) or "no encontrado" in str(result).lower() or "not found" in str(result).lower()