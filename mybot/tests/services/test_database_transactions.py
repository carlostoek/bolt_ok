"""
Tests para validar la integridad de transacciones de base de datos en el sistema administrativo de narrativa.
Verifica que las transacciones son atómicas y que se aplican correctamente las restricciones.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.mark.asyncio
async def test_atomic_transaction_rollback(session: AsyncSession):
    """Verificar que las transacciones de base de datos son realmente atómicas."""
    # Crear fragmento inicial para contar
    initial_fragment = NarrativeFragment(
        title="Fragmento inicial",
        content="Contenido inicial",
        fragment_type="STORY",
        is_active=True
    )
    session.add(initial_fragment)
    await session.commit()
    
    # Verificar que hay un fragmento en la base de datos
    count_query = select(func.count()).select_from(NarrativeFragment)
    result = await session.execute(count_query)
    initial_count = result.scalar()
    assert initial_count == 1
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear un fragmento que funcionará
    valid_fragment = {
        "title": "Fragmento válido",
        "content": "Contenido del fragmento",
        "fragment_type": "STORY"
    }
    
    # Crear un fragmento con datos inválidos que causará error
    invalid_fragment = {
        "title": "Fragmento inválido",
        "content": "Contenido del fragmento",
        "fragment_type": "TIPO_INVALIDO"  # Esto causará error
    }
    
    # Simular una transacción fallida a mitad de proceso
    with patch.object(session, 'commit', side_effect=[None, SQLAlchemyError("Error simulado")]):
        try:
            # Intentar crear ambos fragmentos en una transacción
            await admin_service.create_fragment(valid_fragment)
            await admin_service.create_fragment(invalid_fragment)  # Esto fallará
        except Exception:
            # Esperamos que se lance excepción
            pass
    
    # Verificar que no se agregó ningún fragmento (rollback completo)
    await session.rollback()  # Asegurar que no hay transacción pendiente
    count_query = select(func.count()).select_from(NarrativeFragment)
    result = await session.execute(count_query)
    final_count = result.scalar()
    
    # Solo debería existir el fragmento inicial
    assert final_count == 1


@pytest.mark.asyncio
async def test_database_constraint_enforcement(session: AsyncSession):
    """Verificar que las restricciones de base de datos previenen la corrupción de datos."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # 1. Intentar crear un fragmento sin título (campo requerido)
    invalid_fragment = {
        "content": "Contenido sin título",
        "fragment_type": "STORY"
    }
    
    with pytest.raises(ValueError) as excinfo:
        await admin_service.create_fragment(invalid_fragment)
    
    assert "título" in str(excinfo.value).lower() or "title" in str(excinfo.value).lower()
    
    # 2. Intentar crear un fragmento sin contenido (campo requerido)
    invalid_fragment = {
        "title": "Título sin contenido",
        "fragment_type": "STORY",
        "content": ""  # Contenido vacío
    }
    
    with pytest.raises(ValueError) as excinfo:
        await admin_service.create_fragment(invalid_fragment)
    
    assert "contenido" in str(excinfo.value).lower() or "content" in str(excinfo.value).lower()
    
    # 3. Intentar crear un fragmento con tipo inválido
    invalid_fragment = {
        "title": "Título con tipo inválido",
        "content": "Contenido del fragmento",
        "fragment_type": "TIPO_INEXISTENTE"
    }
    
    with pytest.raises(ValueError) as excinfo:
        await admin_service.create_fragment(invalid_fragment)
    
    assert "tipo" in str(excinfo.value).lower() or "type" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_transaction_isolation(session: AsyncSession):
    """Verificar que las transacciones están aisladas correctamente."""
    # Crear un fragmento base
    base_fragment = NarrativeFragment(
        title="Fragmento base",
        content="Contenido base",
        fragment_type="STORY",
        is_active=True
    )
    session.add(base_fragment)
    await session.commit()
    await session.refresh(base_fragment)
    
    # Crear una segunda sesión para simular acceso concurrente
    from sqlalchemy.ext.asyncio import async_sessionmaker
    session_factory = session.async_session.async_sessionmaker
    
    async with session_factory() as session2:
        # En la primera sesión, actualizar el fragmento pero no hacer commit
        base_fragment.title = "Título actualizado en sesión 1"
        
        # En la segunda sesión, intentar leer el mismo fragmento
        fragment_query = select(NarrativeFragment).where(NarrativeFragment.id == base_fragment.id)
        result = await session2.execute(fragment_query)
        fragment_in_session2 = result.scalar_one()
        
        # Verificar que en la segunda sesión, el título no ha cambiado
        assert fragment_in_session2.title == "Fragmento base"
        
        # Hacer commit en la primera sesión
        await session.commit()
        
        # Refrescar en la segunda sesión y verificar que ahora sí ve los cambios
        await session2.refresh(fragment_in_session2)
        assert fragment_in_session2.title == "Título actualizado en sesión 1"


@pytest.mark.asyncio
async def test_error_handling_during_fragment_creation(session: AsyncSession):
    """Verificar que los errores durante la creación de fragmentos se manejan correctamente."""
    # Crear servicio administrativo con un event_bus que falla
    admin_service = NarrativeAdminService(session)
    
    # Crear un fragmento
    fragment_data = {
        "title": "Fragmento para probar errores",
        "content": "Contenido del fragmento",
        "fragment_type": "STORY"
    }
    
    # Simular error de base de datos durante el commit
    with patch.object(session, 'commit', side_effect=SQLAlchemyError("Error simulado")):
        with pytest.raises(Exception):
            await admin_service.create_fragment(fragment_data)
    
    # Verificar que se ha hecho rollback y no hay fragmentos
    await session.rollback()  # Asegurar que no hay transacción pendiente
    count_query = select(func.count()).select_from(NarrativeFragment)
    result = await session.execute(count_query)
    count = result.scalar()
    assert count == 0


@pytest.mark.asyncio
async def test_cascade_delete_behavior(session: AsyncSession):
    """Verificar el comportamiento en cascada cuando se desactiva un fragmento."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear varios fragmentos interconectados
    fragment1 = await admin_service.create_fragment({
        "title": "Fragmento 1",
        "content": "Contenido del fragmento 1",
        "fragment_type": "DECISION"
    })
    
    fragment2 = await admin_service.create_fragment({
        "title": "Fragmento 2",
        "content": "Contenido del fragmento 2",
        "fragment_type": "STORY"
    })
    
    fragment3 = await admin_service.create_fragment({
        "title": "Fragmento 3",
        "content": "Contenido del fragmento 3",
        "fragment_type": "STORY"
    })
    
    # Conectar fragmento1 -> fragmento2 y fragmento1 -> fragmento3
    await admin_service.update_fragment_connections(fragment1["id"], [
        {
            "text": "Ir a fragmento 2",
            "next_fragment": fragment2["id"]
        },
        {
            "text": "Ir a fragmento 3",
            "next_fragment": fragment3["id"]
        }
    ])
    
    # Eliminar (desactivar) el fragmento1
    await admin_service.delete_fragment(fragment1["id"])
    
    # Verificar que fragmento1 está inactivo
    fragment1_query = select(NarrativeFragment).where(NarrativeFragment.id == fragment1["id"])
    result = await session.execute(fragment1_query)
    fragment1_db = result.scalar_one()
    assert fragment1_db.is_active is False
    
    # Verificar que fragmento2 y fragmento3 siguen activos
    fragment2_query = select(NarrativeFragment).where(NarrativeFragment.id == fragment2["id"])
    result = await session.execute(fragment2_query)
    fragment2_db = result.scalar_one()
    assert fragment2_db.is_active is True
    
    fragment3_query = select(NarrativeFragment).where(NarrativeFragment.id == fragment3["id"])
    result = await session.execute(fragment3_query)
    fragment3_db = result.scalar_one()
    assert fragment3_db.is_active is True


@pytest.mark.asyncio
async def test_concurrent_fragment_update(session: AsyncSession):
    """Verificar el comportamiento ante actualizaciones concurrentes del mismo fragmento."""
    # Crear un fragmento base
    fragment = NarrativeFragment(
        title="Fragmento para concurrencia",
        content="Contenido original",
        fragment_type="STORY",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Crear dos servicios administrativos con sesiones diferentes
    admin_service1 = NarrativeAdminService(session)
    
    # Crear una segunda sesión
    from sqlalchemy.ext.asyncio import async_sessionmaker
    session_factory = session.async_session.async_sessionmaker
    
    async with session_factory() as session2:
        admin_service2 = NarrativeAdminService(session2)
        
        # Actualizar con el primer servicio
        await admin_service1.update_fragment(fragment.id, {
            "content": "Contenido actualizado por servicio 1"
        })
        
        # Actualizar con el segundo servicio - debería funcionar porque lee el estado más reciente
        await admin_service2.update_fragment(fragment.id, {
            "content": "Contenido actualizado por servicio 2"
        })
        
        # Verificar que el último cambio es el que prevalece
        updated_fragment = await session.get(NarrativeFragment, fragment.id)
        await session.refresh(updated_fragment)
        assert updated_fragment.content == "Contenido actualizado por servicio 2"


@pytest.mark.asyncio
async def test_fragment_json_data_integrity(session: AsyncSession):
    """Verificar que los campos JSON mantienen su integridad estructural."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear un fragmento con datos JSON complejos
    fragment_data = {
        "title": "Fragmento con JSON complejo",
        "content": "Contenido del fragmento",
        "fragment_type": "DECISION",
        "choices": [
            {
                "text": "Opción 1",
                "next_fragment": "id-placeholder-1",
                "requirements": {
                    "points": 100,
                    "clues": ["CLAVE1", "CLAVE2"]
                }
            },
            {
                "text": "Opción 2",
                "next_fragment": "id-placeholder-2",
                "requirements": {
                    "vip": True
                }
            }
        ],
        "triggers": {
            "points": 50,
            "clues": ["NUEVA_PISTA"],
            "achievements": ["LOGRO1"],
            "nested": {
                "level1": {
                    "level2": "valor anidado"
                }
            }
        }
    }
    
    # Crear el fragmento
    created_fragment = await admin_service.create_fragment(fragment_data)
    fragment_id = created_fragment["id"]
    
    # Recuperar el fragmento directamente de la base de datos
    fragment_query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
    result = await session.execute(fragment_query)
    db_fragment = result.scalar_one()
    
    # Verificar que los datos JSON se mantuvieron intactos
    assert len(db_fragment.choices) == 2
    assert db_fragment.choices[0]["text"] == "Opción 1"
    assert db_fragment.choices[0]["requirements"]["clues"] == ["CLAVE1", "CLAVE2"]
    assert db_fragment.choices[1]["requirements"]["vip"] is True
    
    assert db_fragment.triggers["points"] == 50
    assert db_fragment.triggers["clues"] == ["NUEVA_PISTA"]
    assert db_fragment.triggers["nested"]["level1"]["level2"] == "valor anidado"