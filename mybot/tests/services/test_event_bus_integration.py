"""
Tests para validar la integración del sistema administrativo de narrativa con el Event Bus.
Verifica que los eventos se emitan correctamente y sean recibidos por los suscriptores.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_unified import NarrativeFragment
from services.narrative_admin_service import NarrativeAdminService
from services.event_bus import get_event_bus, reset_event_bus, EventType, Event


@pytest.fixture(autouse=True)
def reset_bus():
    """Reset the global event bus before and after each test."""
    reset_event_bus()
    yield
    reset_event_bus()


@pytest.mark.asyncio
async def test_narrative_admin_event_subscription():
    """Verificar que el servicio se suscribe a los patrones correctos de Event Bus."""
    # Obtener una instancia limpia del event bus
    event_bus = get_event_bus()
    
    # Verificar que no hay suscriptores inicialmente
    assert event_bus.get_subscribers_count(EventType.CONSISTENCY_CHECK) == 0
    
    # Crear un evento de prueba para fragmento creado
    test_event = Event(
        event_type=EventType.CONSISTENCY_CHECK,
        user_id=0,  # System event
        data={
            "action": "fragment_created",
            "fragment_id": "test-uuid",
            "fragment_type": "STORY"
        },
        timestamp=None,
        source="test_event_bus_integration"
    )
    
    # Crear un handler de prueba que verificará la recepción del evento
    handler_called = False
    
    async def test_handler(event: Event):
        nonlocal handler_called
        handler_called = True
        assert event.event_type == EventType.CONSISTENCY_CHECK
        assert event.data["action"] == "fragment_created"
        assert event.data["fragment_id"] == "test-uuid"
    
    # Suscribir el handler
    event_bus.subscribe(EventType.CONSISTENCY_CHECK, test_handler)
    
    # Verificar que la suscripción se registró
    assert event_bus.get_subscribers_count(EventType.CONSISTENCY_CHECK) == 1
    
    # Publicar el evento
    await event_bus.publish(
        EventType.CONSISTENCY_CHECK,
        0,
        test_event.data,
        source="test_event_bus_integration"
    )
    
    # Dar tiempo para que el evento se procese
    await asyncio.sleep(0.1)
    
    # Verificar que el handler fue llamado
    assert handler_called is True


@pytest.mark.asyncio
async def test_narrative_admin_event_publishing(session: AsyncSession):
    """Verificar que el servicio publica eventos correctamente."""
    # Crear un mock del event bus
    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock()
    
    # Reemplazar el event bus global con nuestro mock
    with patch('services.narrative_admin_service.get_event_bus', return_value=mock_event_bus):
        # Crear servicio administrativo de narrativa
        admin_service = NarrativeAdminService(session)
        
        # Crear un fragmento de prueba
        fragment_data = {
            "title": "Fragmento de prueba",
            "content": "Contenido del fragmento",
            "fragment_type": "STORY"
        }
        
        # Crear el fragmento a través del servicio
        await admin_service.create_fragment(fragment_data)
        
        # Verificar que se publicó el evento correcto
        mock_event_bus.publish.assert_called_once()
        
        # Extraer argumentos de la llamada
        call_args = mock_event_bus.publish.call_args[0]
        
        # Verificar que se llamó con los parámetros correctos
        assert call_args[0] == EventType.CONSISTENCY_CHECK  # Tipo de evento
        assert call_args[1] == 0  # ID de sistema
        assert call_args[2]["action"] == "fragment_created"  # Datos
        assert "fragment_id" in call_args[2]  # Debe incluir ID del fragmento
        assert call_args[2]["fragment_type"] == "STORY"  # Tipo de fragmento
        assert call_args[3] == "narrative_admin_service"  # Fuente


@pytest.mark.asyncio
async def test_event_bus_failure_graceful_degradation(session: AsyncSession):
    """Verificar que el servicio maneja fallos de Event Bus con elegancia."""
    # Crear un mock del event bus que lanza excepción
    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock(side_effect=Exception("Error simulado de Event Bus"))
    
    # Reemplazar el event bus global con nuestro mock
    with patch('services.narrative_admin_service.get_event_bus', return_value=mock_event_bus):
        # Crear servicio administrativo de narrativa
        admin_service = NarrativeAdminService(session)
        
        # Crear un fragmento de prueba
        fragment_data = {
            "title": "Fragmento con error de event bus",
            "content": "Contenido del fragmento",
            "fragment_type": "STORY"
        }
        
        # Verificar que el fallo del Event Bus no impide la creación del fragmento
        fragment = await admin_service.create_fragment(fragment_data)
        
        # Verificar que el fragmento se creó correctamente a pesar del error
        assert fragment is not None
        assert fragment["title"] == "Fragmento con error de event bus"
        
        # Verificar que el fragmento existe en la base de datos
        query = f"SELECT * FROM narrative_fragments_unified WHERE title = 'Fragmento con error de event bus'"
        result = await session.execute(query)
        assert result.first() is not None


@pytest.mark.asyncio
async def test_multiple_event_subscriptions(session: AsyncSession):
    """Verificar que múltiples suscriptores reciben el mismo evento."""
    # Obtener una instancia limpia del event bus
    event_bus = get_event_bus()
    
    # Crear contadores para los handlers
    handler1_calls = 0
    handler2_calls = 0
    
    # Crear handlers de prueba
    async def test_handler1(event: Event):
        nonlocal handler1_calls
        handler1_calls += 1
    
    async def test_handler2(event: Event):
        nonlocal handler2_calls
        handler2_calls += 1
    
    # Suscribir ambos handlers al mismo tipo de evento
    event_bus.subscribe(EventType.CONSISTENCY_CHECK, test_handler1)
    event_bus.subscribe(EventType.CONSISTENCY_CHECK, test_handler2)
    
    # Verificar que las suscripciones se registraron
    assert event_bus.get_subscribers_count(EventType.CONSISTENCY_CHECK) == 2
    
    # Crear servicio administrativo de narrativa
    admin_service = NarrativeAdminService(session)
    
    # Crear un fragmento (esto debería publicar un evento)
    fragment_data = {
        "title": "Fragmento para múltiples suscriptores",
        "content": "Contenido del fragmento",
        "fragment_type": "STORY"
    }
    
    await admin_service.create_fragment(fragment_data)
    
    # Dar tiempo para que el evento se procese
    await asyncio.sleep(0.1)
    
    # Verificar que ambos handlers fueron llamados
    assert handler1_calls == 1
    assert handler2_calls == 1


@pytest.mark.asyncio
async def test_event_bus_error_handling(session: AsyncSession):
    """Verificar que los errores en los handlers no afectan al servicio."""
    # Obtener una instancia limpia del event bus
    event_bus = get_event_bus()
    
    # Crear un handler que siempre lanza excepción
    async def failing_handler(event: Event):
        raise Exception("Error simulado en handler")
    
    # Crear otro handler que funciona correctamente
    working_handler_called = False
    
    async def working_handler(event: Event):
        nonlocal working_handler_called
        working_handler_called = True
    
    # Suscribir ambos handlers
    event_bus.subscribe(EventType.CONSISTENCY_CHECK, failing_handler)
    event_bus.subscribe(EventType.CONSISTENCY_CHECK, working_handler)
    
    # Crear servicio administrativo de narrativa
    admin_service = NarrativeAdminService(session)
    
    # Crear un fragmento (esto debería publicar un evento)
    fragment_data = {
        "title": "Fragmento para probar errores",
        "content": "Contenido del fragmento",
        "fragment_type": "STORY"
    }
    
    # Esto no debería lanzar excepción aunque el handler falle
    await admin_service.create_fragment(fragment_data)
    
    # Dar tiempo para que el evento se procese
    await asyncio.sleep(0.1)
    
    # Verificar que el handler que funciona fue llamado a pesar del error en el otro
    assert working_handler_called is True


@pytest.mark.asyncio
async def test_all_narrative_admin_events_are_published(session: AsyncSession):
    """Verificar que todos los eventos relevantes del servicio administrativo se publican."""
    # Crear un mock del event bus
    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock()
    
    # Reemplazar el event bus global con nuestro mock
    with patch('services.narrative_admin_service.get_event_bus', return_value=mock_event_bus):
        # Crear servicio administrativo de narrativa
        admin_service = NarrativeAdminService(session)
        
        # 1. Crear un fragmento
        fragment_data = {
            "title": "Fragmento para eventos",
            "content": "Contenido del fragmento",
            "fragment_type": "STORY"
        }
        
        fragment = await admin_service.create_fragment(fragment_data)
        fragment_id = fragment["id"]
        
        # Verificar evento de creación
        assert mock_event_bus.publish.call_count == 1
        assert mock_event_bus.publish.call_args[0][2]["action"] == "fragment_created"
        
        # Resetear el mock
        mock_event_bus.publish.reset_mock()
        
        # 2. Actualizar el fragmento
        update_data = {
            "title": "Fragmento actualizado",
            "content": "Contenido actualizado"
        }
        
        await admin_service.update_fragment(fragment_id, update_data)
        
        # Verificar evento de actualización
        assert mock_event_bus.publish.call_count == 1
        assert mock_event_bus.publish.call_args[0][2]["action"] == "fragment_updated"
        
        # Resetear el mock
        mock_event_bus.publish.reset_mock()
        
        # 3. Actualizar conexiones del fragmento
        await admin_service.update_fragment_connections(fragment_id, [])
        
        # Verificar evento de actualización de conexiones
        assert mock_event_bus.publish.call_count == 1
        assert mock_event_bus.publish.call_args[0][2]["action"] == "fragment_connections_updated"
        
        # Resetear el mock
        mock_event_bus.publish.reset_mock()
        
        # 4. Eliminar (desactivar) el fragmento
        await admin_service.delete_fragment(fragment_id)
        
        # Verificar evento de eliminación
        assert mock_event_bus.publish.call_count == 1
        assert mock_event_bus.publish.call_args[0][2]["action"] == "fragment_deleted"
        
        # Resetear el mock
        mock_event_bus.publish.reset_mock()
        
        # 5. Reiniciar progreso de usuario
        # Primero creamos un estado de usuario
        from database.narrative_unified import UserNarrativeState
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id=None,
            visited_fragments=[],
            completed_fragments=[]
        )
        session.add(user_state)
        await session.commit()
        
        # Ahora reiniciamos su progreso
        await admin_service.reset_user_narrative(12345)
        
        # Verificar evento de reinicio
        assert mock_event_bus.publish.call_count == 1
        assert mock_event_bus.publish.call_args[0][2]["action"] == "user_narrative_reset"