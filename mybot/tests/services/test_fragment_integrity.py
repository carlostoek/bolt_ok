"""
Tests para verificar la integridad estructural de los fragmentos narrativos.
Estos tests garantizan que los fragmentos y sus conexiones mantengan integridad referencial.
"""
import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.mark.asyncio
async def test_fragment_integrity_after_update(session: AsyncSession):
    """Prueba que las actualizaciones de fragmentos mantienen la integridad referencial."""
    # Crear fragmentos interconectados
    fragment1 = NarrativeFragment(
        title="Fragmento origen",
        content="Contenido del fragmento origen",
        fragment_type="DECISION",
        choices=[],  # Inicialmente sin conexiones
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Fragmento destino",
        content="Contenido del fragmento destino",
        fragment_type="STORY",
        is_active=True
    )
    
    # Añadir a la base de datos
    session.add(fragment1)
    session.add(fragment2)
    await session.commit()
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Añadir conexión del fragmento 1 al 2
    update_data = {
        "choices": [
            {
                "text": "Ir al fragmento destino",
                "next_fragment": fragment2.id
            }
        ]
    }
    
    # Actualizar fragmento 1 con la conexión
    await admin_service.update_fragment(fragment1.id, update_data)
    
    # Verificar que la conexión se creó correctamente
    updated_fragment = await session.get(NarrativeFragment, fragment1.id)
    assert len(updated_fragment.choices) == 1
    assert updated_fragment.choices[0]["next_fragment"] == fragment2.id
    
    # Ahora cambiar el título del fragmento destino y verificar que las conexiones se mantienen
    await admin_service.update_fragment(fragment2.id, {"title": "Fragmento destino actualizado"})
    
    # Verificar que la conexión sigue siendo válida
    connections = await admin_service.get_fragment_connections(fragment1.id)
    assert len(connections["outgoing_connections"]) == 1
    assert connections["outgoing_connections"][0]["id"] == fragment2.id
    assert connections["outgoing_connections"][0]["title"] == "Fragmento destino actualizado"


@pytest.mark.asyncio
async def test_fragment_connections_bidirectional_integrity(session: AsyncSession):
    """Garantía de integridad: las conexiones bidireccionales siempre son consistentes."""
    # Crear fragmentos para una estructura bidireccional A <-> B
    fragment_a = NarrativeFragment(
        title="Fragmento A",
        content="Contenido del fragmento A",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    fragment_b = NarrativeFragment(
        title="Fragmento B",
        content="Contenido del fragmento B",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    # Guardar fragmentos
    session.add(fragment_a)
    session.add(fragment_b)
    await session.commit()
    await session.refresh(fragment_a)
    await session.refresh(fragment_b)
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Conectar A -> B
    await admin_service.update_fragment(fragment_a.id, {
        "choices": [
            {
                "text": "Ir a B",
                "next_fragment": fragment_b.id
            }
        ]
    })
    
    # Conectar B -> A
    await admin_service.update_fragment(fragment_b.id, {
        "choices": [
            {
                "text": "Volver a A",
                "next_fragment": fragment_a.id
            }
        ]
    })
    
    # Verificar conexiones de A
    connections_a = await admin_service.get_fragment_connections(fragment_a.id)
    assert len(connections_a["outgoing_connections"]) == 1
    assert connections_a["outgoing_connections"][0]["id"] == fragment_b.id
    assert len(connections_a["incoming_connections"]) == 1
    assert connections_a["incoming_connections"][0]["id"] == fragment_b.id
    
    # Verificar conexiones de B
    connections_b = await admin_service.get_fragment_connections(fragment_b.id)
    assert len(connections_b["outgoing_connections"]) == 1
    assert connections_b["outgoing_connections"][0]["id"] == fragment_a.id
    assert len(connections_b["incoming_connections"]) == 1
    assert connections_b["incoming_connections"][0]["id"] == fragment_a.id


@pytest.mark.asyncio
async def test_anti_abuse_prevents_circular_references(session: AsyncSession):
    """Verificar que se previenen las referencias circulares directas (un fragmento que se apunta a sí mismo)."""
    # Crear fragmento
    fragment = NarrativeFragment(
        title="Fragmento con potencial autorreferencia",
        content="Contenido del fragmento",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    # Guardar fragmento
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Intentar crear una referencia circular (fragmento que se apunta a sí mismo)
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(fragment.id, [
            {
                "text": "Quedarse aquí (circular)",
                "next_fragment": fragment.id
            }
        ])
    
    # Verificar que se lanzó el error adecuado
    assert "circular" in str(excinfo.value).lower() or "auto" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_inactive_fragment_validation(session: AsyncSession):
    """Verificar que no se pueden crear conexiones a fragmentos inactivos."""
    # Crear fragmentos: uno activo y uno inactivo
    active_fragment = NarrativeFragment(
        title="Fragmento activo",
        content="Contenido del fragmento activo",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    inactive_fragment = NarrativeFragment(
        title="Fragmento inactivo",
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
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Intentar conectar a un fragmento inactivo
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(active_fragment.id, [
            {
                "text": "Ir a fragmento inactivo",
                "next_fragment": inactive_fragment.id
            }
        ])
    
    # Verificar que se lanzó el error adecuado
    assert "inactivo" in str(excinfo.value).lower() or "inactive" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_fragment_deletion_maintains_database_integrity(session: AsyncSession):
    """Verificar que al marcar un fragmento como inactivo (borrado lógico) se mantiene la integridad de la base de datos."""
    # Crear fragmentos interconectados
    fragment1 = NarrativeFragment(
        title="Fragmento origen para borrado",
        content="Contenido origen",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Fragmento destino",
        content="Contenido destino",
        fragment_type="STORY",
        is_active=True
    )
    
    # Guardar fragmentos
    session.add(fragment1)
    session.add(fragment2)
    await session.commit()
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Conectar fragment1 -> fragment2
    await admin_service.update_fragment(fragment1.id, {
        "choices": [
            {
                "text": "Ir al destino",
                "next_fragment": fragment2.id
            }
        ]
    })
    
    # Asignar estos fragmentos como actuales a dos usuarios diferentes
    user1_state = UserNarrativeState(
        user_id=1001,
        current_fragment_id=fragment1.id,
        visited_fragments=[fragment1.id],
        completed_fragments=[]
    )
    
    user2_state = UserNarrativeState(
        user_id=1002,
        current_fragment_id=fragment2.id,
        visited_fragments=[fragment1.id, fragment2.id],
        completed_fragments=[fragment1.id]
    )
    
    session.add(user1_state)
    session.add(user2_state)
    await session.commit()
    
    # Borrar lógicamente el fragment1
    await admin_service.delete_fragment(fragment1.id)
    
    # Verificar que el fragmento se marcó como inactivo
    deleted_fragment = await session.get(NarrativeFragment, fragment1.id)
    assert deleted_fragment is not None  # Sigue existiendo en la BD
    assert deleted_fragment.is_active is False  # Pero marcado como inactivo
    
    # Verificar integridad: Los estados de usuario siguen existiendo
    user1_updated = await session.get(UserNarrativeState, 1001)
    user2_updated = await session.get(UserNarrativeState, 1002)
    
    assert user1_updated is not None
    assert user2_updated is not None
    assert user1_updated.current_fragment_id == fragment1.id  # La referencia se mantiene
    assert fragment1.id in user2_updated.visited_fragments  # El historial se mantiene
    assert fragment1.id in user2_updated.completed_fragments  # El historial se mantiene


@pytest.mark.asyncio
async def test_fragment_connection_validation(session: AsyncSession):
    """Verificar que las conexiones entre fragmentos se validan correctamente."""
    # Crear fragmentos
    fragment = NarrativeFragment(
        title="Fragmento con conexiones",
        content="Contenido del fragmento",
        fragment_type="DECISION",
        choices=[],
        is_active=True
    )
    
    # Guardar fragmento
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Intentar crear una conexión a un fragmento inexistente
    nonexistent_id = str(uuid.uuid4())
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment_connections(fragment.id, [
            {
                "text": "Ir a fragmento inexistente",
                "next_fragment": nonexistent_id
            }
        ])
    
    # Verificar que se lanzó el error adecuado
    assert "no encontrado" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_duplicate_fragment_titles_allowed_but_distinguished(session: AsyncSession):
    """Verificar que se permiten títulos duplicados pero son distinguibles por ID."""
    # Crear fragmentos con el mismo título
    fragment1 = NarrativeFragment(
        title="Título duplicado",
        content="Contenido del fragmento 1",
        fragment_type="STORY",
        is_active=True
    )
    
    fragment2 = NarrativeFragment(
        title="Título duplicado",
        content="Contenido del fragmento 2",
        fragment_type="STORY",
        is_active=True
    )
    
    # Guardar fragmentos
    session.add(fragment1)
    session.add(fragment2)
    await session.commit()
    await session.refresh(fragment1)
    await session.refresh(fragment2)
    
    # Verificar que se crearon con el mismo título pero IDs diferentes
    assert fragment1.title == fragment2.title
    assert fragment1.id != fragment2.id
    
    # Crear servicio de administración
    admin_service = NarrativeAdminService(session)
    
    # Buscar fragmentos por título
    results = await admin_service.get_all_fragments(search_query="Título duplicado")
    
    # Verificar que se encontraron ambos fragmentos
    assert results["total"] == 2
    
    # Verificar que se pueden diferenciar por ID
    fragment_ids = [item["id"] for item in results["items"]]
    assert fragment1.id in fragment_ids
    assert fragment2.id in fragment_ids