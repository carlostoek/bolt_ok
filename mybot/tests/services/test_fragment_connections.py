"""
Tests para validar el sistema de conexiones entre fragmentos narrativos.
Verifica que las conexiones entre fragmentos son válidas y que el flujo narrativo
se mantiene íntegro.
"""
import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.mark.asyncio
async def test_connection_validation(session: AsyncSession):
    """Verificar que se validan las conexiones entre fragmentos."""
    # Crear fragmentos: uno activo y uno inactivo
    active_fragment = NarrativeFragment(
        title="Fragmento activo origen",
        content="Contenido del fragmento activo",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    inactive_fragment = NarrativeFragment(
        title="Fragmento inactivo destino",
        content="Contenido del fragmento inactivo",
        fragment_type="STORY",
        is_active=False
    )
    
    # Guardar fragmentos
    session.add(active_fragment)
    session.add(inactive_fragment)
    await session.commit()
    await session.refresh(active_fragment)
    await session.refresh(inactive_fragment)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Intentar conectar a un fragmento inactivo debería fallar
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(active_fragment.id, [
            {
                "text": "Ir a fragmento inactivo",
                "next_fragment": inactive_fragment.id
            }
        ])
    
    # Verificar mensaje de error
    assert "inactivo" in str(excinfo.value).lower() or "inactive" in str(excinfo.value).lower()
    
    # Intentar conectar a un fragmento inexistente debería fallar
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(active_fragment.id, [
            {
                "text": "Ir a fragmento inexistente",
                "next_fragment": str(uuid.uuid4())
            }
        ])
    
    # Verificar mensaje de error
    assert "no encontrado" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()
    
    # Intentar conectar sin texto de opción debería fallar
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(active_fragment.id, [
            {
                "text": "",  # Texto vacío
                "next_fragment": active_fragment.id
            }
        ])
    
    # Verificar mensaje de error
    assert "texto" in str(excinfo.value).lower() or "text" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_story_flow_integrity(session: AsyncSession):
    """Verificar la integridad del flujo narrativo."""
    # Crear una cadena de fragmentos interconectados
    fragments = []
    
    # Crear 5 fragmentos para una historia lineal
    for i in range(5):
        fragment = NarrativeFragment(
            title=f"Fragmento {i+1}",
            content=f"Contenido del fragmento {i+1}",
            fragment_type="STORY" if i != 2 else "DECISION",  # El fragmento 3 es una decisión
            choices=[],
            is_active=True
        )
        fragments.append(fragment)
    
    # Añadir a la base de datos
    session.add_all(fragments)
    await session.commit()
    
    # Refrescar para obtener IDs
    for fragment in fragments:
        await session.refresh(fragment)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Conectar los fragmentos en secuencia
    for i in range(4):
        # Si el fragmento es de decisión, añadimos dos opciones
        if fragments[i].fragment_type == "DECISION":
            connections = [
                {
                    "text": f"Opción 1: Ir a fragmento {i+2}",
                    "next_fragment": fragments[i+1].id
                },
                {
                    "text": f"Opción 2: Volver a fragmento {i}",
                    "next_fragment": fragments[i-1].id
                }
            ]
        else:
            # Si es fragmento normal, solo una conexión al siguiente
            connections = [
                {
                    "text": f"Continuar a fragmento {i+2}",
                    "next_fragment": fragments[i+1].id
                }
            ]
        
        # Actualizar conexiones
        await admin_service.update_fragment_connections(fragments[i].id, connections)
    
    # Verificar la estructura de la historia
    for i in range(4):
        # Obtener conexiones del fragmento
        connections = await admin_service.get_fragment_connections(fragments[i].id)
        
        # Verificar que tiene conexiones salientes
        assert len(connections["outgoing_connections"]) > 0
        
        # Si es fragmento de decisión, debe tener 2 conexiones
        if fragments[i].fragment_type == "DECISION":
            assert len(connections["outgoing_connections"]) == 2
            
            # Una conexión debe ir al siguiente fragmento
            next_ids = [conn["id"] for conn in connections["outgoing_connections"]]
            assert fragments[i+1].id in next_ids
            
            # Otra conexión debe ir al fragmento anterior
            assert fragments[i-1].id in next_ids
        else:
            # Si es fragmento normal, debe tener 1 conexión al siguiente
            assert len(connections["outgoing_connections"]) == 1
            assert connections["outgoing_connections"][0]["id"] == fragments[i+1].id
    
    # El fragmento final no debería tener conexiones salientes
    final_connections = await admin_service.get_fragment_connections(fragments[4].id)
    assert len(final_connections["outgoing_connections"]) == 0
    
    # Pero debería tener una conexión entrante desde el penúltimo fragmento
    assert len(final_connections["incoming_connections"]) == 1
    assert final_connections["incoming_connections"][0]["id"] == fragments[3].id


@pytest.mark.asyncio
async def test_multiple_path_flow(session: AsyncSession):
    """Verificar que se pueden crear múltiples caminos a través de la narrativa."""
    # Crear fragmentos para una historia con múltiples caminos
    start = NarrativeFragment(
        title="Inicio",
        content="Fragmento inicial de la historia",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    path_a1 = NarrativeFragment(
        title="Camino A - Parte 1",
        content="Primer fragmento del camino A",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    path_a2 = NarrativeFragment(
        title="Camino A - Parte 2",
        content="Segundo fragmento del camino A",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    path_b1 = NarrativeFragment(
        title="Camino B - Parte 1",
        content="Primer fragmento del camino B",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    path_b2 = NarrativeFragment(
        title="Camino B - Parte 2",
        content="Segundo fragmento del camino B",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    end = NarrativeFragment(
        title="Final",
        content="Fragmento final de la historia",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    # Añadir a la base de datos
    session.add_all([start, path_a1, path_a2, path_b1, path_b2, end])
    await session.commit()
    
    # Refrescar para obtener IDs
    await session.refresh(start)
    await session.refresh(path_a1)
    await session.refresh(path_a2)
    await session.refresh(path_b1)
    await session.refresh(path_b2)
    await session.refresh(end)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Configurar conexiones
    # Inicio -> Camino A1 o Camino B1
    await admin_service.update_fragment_connections(start.id, [
        {
            "text": "Tomar camino A",
            "next_fragment": path_a1.id
        },
        {
            "text": "Tomar camino B",
            "next_fragment": path_b1.id
        }
    ])
    
    # Camino A1 -> Camino A2
    await admin_service.update_fragment_connections(path_a1.id, [
        {
            "text": "Continuar por camino A",
            "next_fragment": path_a2.id
        }
    ])
    
    # Camino A2 -> Final
    await admin_service.update_fragment_connections(path_a2.id, [
        {
            "text": "Llegar al final",
            "next_fragment": end.id
        }
    ])
    
    # Camino B1 -> Camino B2
    await admin_service.update_fragment_connections(path_b1.id, [
        {
            "text": "Continuar por camino B",
            "next_fragment": path_b2.id
        }
    ])
    
    # Camino B2 -> Final
    await admin_service.update_fragment_connections(path_b2.id, [
        {
            "text": "Llegar al final",
            "next_fragment": end.id
        }
    ])
    
    # Verificar las conexiones salientes desde el inicio
    start_connections = await admin_service.get_fragment_connections(start.id)
    assert len(start_connections["outgoing_connections"]) == 2
    
    # Verificar que ambos caminos llevan al final
    # Camino A
    path_a1_connections = await admin_service.get_fragment_connections(path_a1.id)
    assert len(path_a1_connections["outgoing_connections"]) == 1
    assert path_a1_connections["outgoing_connections"][0]["id"] == path_a2.id
    
    path_a2_connections = await admin_service.get_fragment_connections(path_a2.id)
    assert len(path_a2_connections["outgoing_connections"]) == 1
    assert path_a2_connections["outgoing_connections"][0]["id"] == end.id
    
    # Camino B
    path_b1_connections = await admin_service.get_fragment_connections(path_b1.id)
    assert len(path_b1_connections["outgoing_connections"]) == 1
    assert path_b1_connections["outgoing_connections"][0]["id"] == path_b2.id
    
    path_b2_connections = await admin_service.get_fragment_connections(path_b2.id)
    assert len(path_b2_connections["outgoing_connections"]) == 1
    assert path_b2_connections["outgoing_connections"][0]["id"] == end.id
    
    # Verificar que el final tiene dos conexiones entrantes
    end_connections = await admin_service.get_fragment_connections(end.id)
    assert len(end_connections["incoming_connections"]) == 2
    incoming_ids = [conn["id"] for conn in end_connections["incoming_connections"]]
    assert path_a2.id in incoming_ids
    assert path_b2.id in incoming_ids


@pytest.mark.asyncio
async def test_complex_story_graph(session: AsyncSession):
    """Verificar que se pueden crear estructuras narrativas complejas con ciclos y múltiples caminos."""
    # Crear fragmentos para una historia con estructura compleja
    hub = NarrativeFragment(
        title="Hub Central",
        content="Punto central de la historia",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    north = NarrativeFragment(
        title="Norte",
        content="Región norte",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    east = NarrativeFragment(
        title="Este",
        content="Región este",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    south = NarrativeFragment(
        title="Sur",
        content="Región sur",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    west = NarrativeFragment(
        title="Oeste",
        content="Región oeste",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    secret = NarrativeFragment(
        title="Área Secreta",
        content="Área oculta de la historia",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    # Añadir a la base de datos
    session.add_all([hub, north, east, south, west, secret])
    await session.commit()
    
    # Refrescar para obtener IDs
    await session.refresh(hub)
    await session.refresh(north)
    await session.refresh(east)
    await session.refresh(south)
    await session.refresh(west)
    await session.refresh(secret)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Configurar conexiones hub -> direcciones
    await admin_service.update_fragment_connections(hub.id, [
        {
            "text": "Ir al norte",
            "next_fragment": north.id
        },
        {
            "text": "Ir al este",
            "next_fragment": east.id
        },
        {
            "text": "Ir al sur",
            "next_fragment": south.id
        },
        {
            "text": "Ir al oeste",
            "next_fragment": west.id
        }
    ])
    
    # Conexiones Norte
    await admin_service.update_fragment_connections(north.id, [
        {
            "text": "Volver al centro",
            "next_fragment": hub.id
        },
        {
            "text": "Ir al este",
            "next_fragment": east.id
        }
    ])
    
    # Conexiones Este
    await admin_service.update_fragment_connections(east.id, [
        {
            "text": "Volver al centro",
            "next_fragment": hub.id
        },
        {
            "text": "Ir al sur",
            "next_fragment": south.id
        },
        {
            "text": "Explorar área secreta",
            "next_fragment": secret.id
        }
    ])
    
    # Conexiones Sur
    await admin_service.update_fragment_connections(south.id, [
        {
            "text": "Volver al centro",
            "next_fragment": hub.id
        },
        {
            "text": "Ir al oeste",
            "next_fragment": west.id
        }
    ])
    
    # Conexiones Oeste
    await admin_service.update_fragment_connections(west.id, [
        {
            "text": "Volver al centro",
            "next_fragment": hub.id
        },
        {
            "text": "Ir al norte",
            "next_fragment": north.id
        }
    ])
    
    # Conexión área secreta
    await admin_service.update_fragment_connections(secret.id, [
        {
            "text": "Volver al este",
            "next_fragment": east.id
        }
    ])
    
    # Verificar estructura completa
    # 1. Verificar que el hub tiene 4 conexiones salientes
    hub_connections = await admin_service.get_fragment_connections(hub.id)
    assert len(hub_connections["outgoing_connections"]) == 4
    
    # 2. Verificar que todas las direcciones tienen una conexión de vuelta al hub
    for fragment in [north, east, south, west]:
        connections = await admin_service.get_fragment_connections(fragment.id)
        hub_connections = [conn for conn in connections["outgoing_connections"] if conn["id"] == hub.id]
        assert len(hub_connections) == 1
    
    # 3. Verificar conexiones específicas
    # Norte -> Este
    north_connections = await admin_service.get_fragment_connections(north.id)
    assert any(conn["id"] == east.id for conn in north_connections["outgoing_connections"])
    
    # Este -> Sur y Este -> Secreto
    east_connections = await admin_service.get_fragment_connections(east.id)
    assert any(conn["id"] == south.id for conn in east_connections["outgoing_connections"])
    assert any(conn["id"] == secret.id for conn in east_connections["outgoing_connections"])
    
    # Sur -> Oeste
    south_connections = await admin_service.get_fragment_connections(south.id)
    assert any(conn["id"] == west.id for conn in south_connections["outgoing_connections"])
    
    # Oeste -> Norte
    west_connections = await admin_service.get_fragment_connections(west.id)
    assert any(conn["id"] == north.id for conn in west_connections["outgoing_connections"])
    
    # 4. Verificar que se forma un ciclo completo
    # Hub -> Norte -> Este -> Sur -> Oeste -> Norte (ciclo)
    assert any(conn["id"] == north.id for conn in hub_connections["outgoing_connections"])
    assert any(conn["id"] == east.id for conn in north_connections["outgoing_connections"])
    assert any(conn["id"] == south.id for conn in east_connections["outgoing_connections"])
    assert any(conn["id"] == west.id for conn in south_connections["outgoing_connections"])
    assert any(conn["id"] == north.id for conn in west_connections["outgoing_connections"])


@pytest.mark.asyncio
async def test_connection_deletion(session: AsyncSession):
    """Verificar que las conexiones se pueden eliminar correctamente."""
    # Crear fragmentos
    fragment1 = NarrativeFragment(
        title="Fragmento con conexiones",
        content="Contenido del fragmento",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Fragmento destino",
        content="Contenido del fragmento destino",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    # Añadir a la base de datos
    session.add_all([fragment1, fragment2])
    await session.commit()
    
    # Refrescar para obtener IDs
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Añadir conexión
    await admin_service.update_fragment_connections(fragment1.id, [
        {
            "text": "Ir al fragmento destino",
            "next_fragment": fragment2.id
        }
    ])
    
    # Verificar que se creó la conexión
    connections = await admin_service.get_fragment_connections(fragment1.id)
    assert len(connections["outgoing_connections"]) == 1
    assert connections["outgoing_connections"][0]["id"] == fragment2.id
    
    # Eliminar todas las conexiones
    await admin_service.update_fragment_connections(fragment1.id, [])
    
    # Verificar que no hay conexiones
    connections = await admin_service.get_fragment_connections(fragment1.id)
    assert len(connections["outgoing_connections"]) == 0


@pytest.mark.asyncio
async def test_connection_text_update(session: AsyncSession):
    """Verificar que el texto de las conexiones se puede actualizar correctamente."""
    # Crear fragmentos
    fragment1 = NarrativeFragment(
        title="Fragmento origen",
        content="Contenido del fragmento",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Fragmento destino",
        content="Contenido del fragmento destino",
        fragment_type="STORY",
        choices=[],
        is_active=True
    )
    
    # Añadir a la base de datos
    session.add_all([fragment1, fragment2])
    await session.commit()
    
    # Refrescar para obtener IDs
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Añadir conexión inicial
    await admin_service.update_fragment_connections(fragment1.id, [
        {
            "text": "Texto original",
            "next_fragment": fragment2.id
        }
    ])
    
    # Verificar texto original
    connections = await admin_service.get_fragment_connections(fragment1.id)
    assert connections["outgoing_connections"][0]["choice_text"] == "Texto original"
    
    # Actualizar texto de la conexión
    await admin_service.update_fragment_connections(fragment1.id, [
        {
            "text": "Texto actualizado",
            "next_fragment": fragment2.id
        }
    ])
    
    # Verificar texto actualizado
    connections = await admin_service.get_fragment_connections(fragment1.id)
    assert connections["outgoing_connections"][0]["choice_text"] == "Texto actualizado"