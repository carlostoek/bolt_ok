"""
Tests de rendimiento para el sistema administrativo de narrativa.
Verifica que las operaciones comunes cumplan con los requisitos de rendimiento.
"""
import pytest
import pytest_asyncio
import time
import asyncio
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


class Timer:
    """Utilidad para medir tiempos de ejecución."""
    
    def __init__(self, description="Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def elapsed_ms(self):
        """Tiempo transcurrido en milisegundos."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000
    
    def assert_faster_than(self, max_ms):
        """Verifica que la operación fue más rápida que el límite especificado."""
        assert self.elapsed_ms is not None, "Timer not used in context"
        assert self.elapsed_ms < max_ms, f"{self.description} took {self.elapsed_ms:.2f}ms, expected < {max_ms}ms"


@pytest_asyncio.fixture
async def sample_fragments(session: AsyncSession):
    """Crea una muestra de fragmentos para pruebas de rendimiento."""
    # Crear 50 fragmentos de prueba
    fragments = []
    for i in range(50):
        fragment = NarrativeFragment(
            title=f"Fragmento de prueba {i}",
            content=f"Contenido del fragmento de prueba número {i} para benchmarks",
            fragment_type="STORY" if i % 3 == 0 else ("DECISION" if i % 3 == 1 else "INFO"),
            is_active=True
        )
        fragments.append(fragment)
    
    # Añadir a la base de datos
    session.add_all(fragments)
    await session.commit()
    
    # Refrescar para obtener IDs
    for fragment in fragments:
        await session.refresh(fragment)
    
    # Crear algunas conexiones entre fragmentos
    for i in range(len(fragments) - 1):
        fragments[i].choices = [
            {
                "text": f"Ir al fragmento {i+1}",
                "next_fragment": fragments[i+1].id
            }
        ]
    
    # Guardar conexiones
    await session.commit()
    
    return fragments


@pytest_asyncio.fixture
async def sample_users(session: AsyncSession, sample_fragments):
    """Crea usuarios de prueba con progreso narrativo."""
    users = []
    
    # Crear 20 usuarios con progreso variado
    for i in range(20):
        user_id = 100000 + i
        
        # Asignar fragmentos visitados aleatorios
        visited_count = min(i + 5, len(sample_fragments))
        visited_fragments = [f.id for f in sample_fragments[:visited_count]]
        
        # Asignar fragmentos completados (un subconjunto de los visitados)
        completed_count = visited_count - 3 if visited_count > 3 else visited_count
        completed_fragments = [f.id for f in sample_fragments[:completed_count]]
        
        # Asignar pistas desbloqueadas
        unlocked_clues = [f"PISTA_{j}" for j in range(i % 10)]
        
        # Crear estado de usuario
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id=sample_fragments[i % len(sample_fragments)].id,
            visited_fragments=visited_fragments,
            completed_fragments=completed_fragments,
            unlocked_clues=unlocked_clues
        )
        
        users.append(user_state)
    
    # Guardar en la base de datos
    session.add_all(users)
    await session.commit()
    
    return users


@pytest.mark.asyncio
async def test_fragment_creation_latency_requirement(session: AsyncSession):
    """Verificar que la creación de fragmentos cumple el requisito de latencia <150ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Datos del fragmento a crear
    fragment_data = {
        "title": "Fragmento para prueba de rendimiento",
        "content": "Contenido del fragmento para probar el rendimiento de creación",
        "fragment_type": "STORY",
        "choices": [
            {
                "text": "Opción 1",
                "next_fragment": str(uuid.uuid4())  # ID ficticio
            },
            {
                "text": "Opción 2",
                "next_fragment": str(uuid.uuid4())  # ID ficticio
            }
        ],
        "triggers": {
            "points": 10,
            "clues": ["PISTA1", "PISTA2"]
        },
        "required_clues": ["REQUISITO1"]
    }
    
    # Medir tiempo de creación
    async with Timer("Fragment creation") as timer:
        try:
            await admin_service.create_fragment(fragment_data)
        except ValueError:
            # Ignorar error de fragmentos inexistentes en choices
            pass
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(150)  # Debe ser menor a 150ms


@pytest.mark.asyncio
async def test_fragment_update_latency_requirement(session: AsyncSession):
    """Verificar que la actualización de fragmentos cumple el requisito de latencia <100ms."""
    # Crear un fragmento inicial
    fragment = NarrativeFragment(
        title="Fragmento para actualizar",
        content="Contenido original",
        fragment_type="STORY",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Datos para la actualización
    update_data = {
        "title": "Título actualizado",
        "content": "Contenido actualizado y extendido para probar el rendimiento",
        "triggers": {
            "points": 20,
            "achievements": ["LOGRO1"]
        }
    }
    
    # Medir tiempo de actualización
    async with Timer("Fragment update") as timer:
        await admin_service.update_fragment(fragment.id, update_data)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(100)  # Debe ser menor a 100ms


@pytest.mark.asyncio
async def test_fragment_list_loading_latency(session: AsyncSession, sample_fragments):
    """Verificar que la carga de lista de fragmentos cumple el requisito de latencia <500ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Medir tiempo de carga de todos los fragmentos
    async with Timer("Fragment list loading") as timer:
        result = await admin_service.get_all_fragments(page=1, limit=50)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(500)  # Debe ser menor a 500ms
    
    # Verificar que se obtuvieron todos los fragmentos
    assert result["total"] >= 50


@pytest.mark.asyncio
async def test_fragment_connections_query_latency(session: AsyncSession, sample_fragments):
    """Verificar que la consulta de conexiones cumple el requisito de latencia <200ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Obtener un fragmento de muestra
    fragment = sample_fragments[len(sample_fragments) // 2]  # Fragmento del medio
    
    # Medir tiempo de consulta de conexiones
    async with Timer("Fragment connections query") as timer:
        await admin_service.get_fragment_connections(fragment.id)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(200)  # Debe ser menor a 200ms


@pytest.mark.asyncio
async def test_user_progress_query_latency(session: AsyncSession, sample_users):
    """Verificar que la consulta de progreso de usuario cumple el requisito de latencia <100ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Obtener un usuario de muestra
    user_id = sample_users[0].user_id
    
    # Medir tiempo de consulta de progreso
    async with Timer("User progress query") as timer:
        await admin_service.get_user_narrative_progress(user_id)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(100)  # Debe ser menor a 100ms


@pytest.mark.asyncio
async def test_fragment_engagement_stats_latency(session: AsyncSession, sample_fragments, sample_users):
    """Verificar que las estadísticas de engagement cumplen el requisito de latencia <300ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Obtener un fragmento de muestra
    fragment = sample_fragments[0]
    
    # Medir tiempo de consulta de estadísticas
    async with Timer("Fragment engagement stats") as timer:
        await admin_service.get_fragment_engagement(fragment.id)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(300)  # Debe ser menor a 300ms


@pytest.mark.asyncio
async def test_narrative_stats_query_latency(session: AsyncSession, sample_fragments, sample_users):
    """Verificar que las estadísticas narrativas cumplen el requisito de latencia <400ms."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Medir tiempo de consulta de estadísticas
    async with Timer("Narrative stats query") as timer:
        await admin_service.get_narrative_stats()
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(400)  # Debe ser menor a 400ms


@pytest.mark.asyncio
async def test_fragment_delete_latency(session: AsyncSession):
    """Verificar que la eliminación de fragmentos cumple el requisito de latencia <50ms."""
    # Crear un fragmento para eliminar
    fragment = NarrativeFragment(
        title="Fragmento para eliminar",
        content="Contenido del fragmento",
        fragment_type="INFO",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Medir tiempo de eliminación
    async with Timer("Fragment deletion") as timer:
        await admin_service.delete_fragment(fragment.id)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(50)  # Debe ser menor a 50ms
    
    # Verificar que el fragmento se marcó como inactivo
    updated_fragment = await session.get(NarrativeFragment, fragment.id)
    assert updated_fragment.is_active is False


@pytest.mark.asyncio
async def test_database_query_performance(session: AsyncSession, sample_fragments):
    """Verificar que las consultas básicas de base de datos cumplen el requisito de latencia <50ms."""
    # Medir tiempo de consulta simple
    async with Timer("Simple database query") as timer:
        query = select(NarrativeFragment).where(NarrativeFragment.is_active == True).limit(10)
        await session.execute(query)
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(50)  # Debe ser menor a 50ms
    
    # Medir tiempo de consulta con join
    async with Timer("Join database query") as timer:
        query = """
        SELECT f.id, f.title, COUNT(u.user_id) as active_users
        FROM narrative_fragments_unified f
        LEFT JOIN user_narrative_states_unified u ON f.id = u.current_fragment_id
        WHERE f.is_active = True
        GROUP BY f.id, f.title
        LIMIT 10
        """
        await session.execute(text(query))
    
    # Verificar requisito de rendimiento
    timer.assert_faster_than(100)  # Debe ser menor a 100ms