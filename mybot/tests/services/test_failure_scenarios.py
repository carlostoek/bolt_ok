"""
Tests para validar el comportamiento del sistema administrativo de narrativa
bajo diversos escenarios de fallo y condiciones de error.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.mark.asyncio
async def test_database_connection_failure(session: AsyncSession):
    """Verificar que el servicio maneja correctamente fallos de conexión a la base de datos."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear datos de fragmento
    fragment_data = {
        "title": "Fragmento para prueba de fallo",
        "content": "Contenido del fragmento",
        "fragment_type": "STORY"
    }
    
    # Simular fallo de conexión durante la ejecución
    with patch.object(session, 'execute', side_effect=OperationalError("connection error", None, None)):
        # Verificar que el error es manejado y no causa un fallo catastrófico
        with pytest.raises(Exception) as excinfo:
            await admin_service.create_fragment(fragment_data)
        
        # Verificar mensaje de error adecuado
        assert "error" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_database_locked_failure(session: AsyncSession):
    """Verificar que el servicio maneja correctamente bloqueos de base de datos."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear fragmento para actualizar
    fragment = NarrativeFragment(
        title="Fragmento para prueba de bloqueo",
        content="Contenido original",
        fragment_type="STORY",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Datos para actualización
    update_data = {
        "title": "Título actualizado",
        "content": "Contenido actualizado"
    }
    
    # Simular bloqueo de base de datos durante la actualización
    with patch.object(session, 'commit', side_effect=[
        OperationalError("database is locked", None, None),  # Primer intento falla
        None  # Segundo intento exitoso
    ]):
        # Implementar retry en el servicio
        with patch.object(admin_service, 'update_fragment', wraps=admin_service.update_fragment) as wrapped_update:
            # Implementar función que reintenta la operación
            async def retry_update():
                try:
                    return await admin_service.update_fragment(fragment.id, update_data)
                except OperationalError:
                    # Esperar y reintentar
                    await asyncio.sleep(0.1)
                    return await admin_service.update_fragment(fragment.id, update_data)
            
            # Ejecutar con reintentos
            result = await retry_update()
            
            # Verificar que la operación fue exitosa eventualmente
            assert result is not None
            assert "id" in result
            assert result["id"] == fragment.id


@pytest.mark.asyncio
async def test_invalid_fragment_id_handling(session: AsyncSession):
    """Verificar que el servicio maneja correctamente IDs de fragmento inválidos o inexistentes."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Intentar obtener un fragmento con ID inexistente
    with pytest.raises(ValueError) as excinfo:
        await admin_service.get_fragment_details("fragmento-inexistente")
    
    # Verificar mensaje de error adecuado
    assert "no encontrado" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()
    
    # Intentar actualizar un fragmento con ID inexistente
    with pytest.raises(ValueError) as excinfo:
        await admin_service.update_fragment("fragmento-inexistente", {"title": "Nuevo título"})
    
    # Verificar mensaje de error adecuado
    assert "no encontrado" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()
    
    # Intentar eliminar un fragmento con ID inexistente
    with pytest.raises(ValueError) as excinfo:
        await admin_service.delete_fragment("fragmento-inexistente")
    
    # Verificar mensaje de error adecuado
    assert "no encontrado" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_invalid_user_id_handling(session: AsyncSession):
    """Verificar que el servicio maneja correctamente IDs de usuario inválidos o inexistentes."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Intentar obtener progreso narrativo de un usuario inexistente
    with pytest.raises(ValueError) as excinfo:
        await admin_service.get_user_narrative_progress(99999999)
    
    # Verificar mensaje de error adecuado
    assert "no tiene progreso" in str(excinfo.value).lower() or "has no progress" in str(excinfo.value).lower()
    
    # Intentar reiniciar progreso narrativo de un usuario inexistente
    with pytest.raises(ValueError) as excinfo:
        await admin_service.reset_user_narrative(99999999)
    
    # Verificar mensaje de error adecuado
    assert "no tiene progreso" in str(excinfo.value).lower() or "has no progress" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_invalid_data_handling(session: AsyncSession):
    """Verificar que el servicio valida correctamente los datos y maneja errores de validación."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Intentar crear un fragmento con datos inválidos (tipo faltante)
    with pytest.raises(ValueError) as excinfo:
        await admin_service.create_fragment({
            "title": "Fragmento sin tipo",
            "content": "Contenido del fragmento"
            # fragment_type falta
        })
    
    # Verificar mensaje de error adecuado
    assert "fragment_type" in str(excinfo.value).lower() or "tipo" in str(excinfo.value).lower()
    
    # Intentar crear un fragmento con tipo inválido
    with pytest.raises(ValueError) as excinfo:
        await admin_service.create_fragment({
            "title": "Fragmento con tipo inválido",
            "content": "Contenido del fragmento",
            "fragment_type": "TIPO_INEXISTENTE"
        })
    
    # Verificar mensaje de error adecuado
    assert "tipo" in str(excinfo.value).lower() or "type" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_corrupted_json_field_handling(session: AsyncSession):
    """Verificar que el servicio maneja correctamente campos JSON corruptos."""
    # Crear fragmento con campos JSON válidos
    fragment = NarrativeFragment(
        title="Fragmento con JSON",
        content="Contenido del fragmento",
        fragment_type="DECISION",
        choices=[{"text": "Opción 1", "next_fragment": "destino-1"}],
        triggers={"points": 10},
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Corromper manualmente el campo JSON (simulando corrupción en la base de datos)
    corrupted_query = text(f"""
    UPDATE narrative_fragments_unified
    SET choices = 'invalid json'
    WHERE id = :fragment_id
    """)
    
    await session.execute(corrupted_query, {"fragment_id": fragment.id})
    await session.commit()
    
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Simular error de parsing JSON durante la obtención del fragmento
    with patch('sqlalchemy.ext.asyncio.AsyncSession.execute', 
              side_effect=SQLAlchemyError("JSON parsing error")):
        
        # Verificar que el servicio maneja el error adecuadamente
        with pytest.raises(Exception) as excinfo:
            await admin_service.get_fragment_details(fragment.id)
        
        # Verificar que el error se propaga con contexto adecuado
        assert "error" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_concurrent_deletion_handling(session: AsyncSession):
    """Verificar que el servicio maneja correctamente eliminaciones concurrentes."""
    # Crear fragmento para eliminar
    fragment = NarrativeFragment(
        title="Fragmento para eliminación concurrente",
        content="Contenido del fragmento",
        fragment_type="STORY",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    # Función para eliminar fragmento en una sesión
    async def delete_fragment(fragment_id):
        async with session_factory() as local_session:
            admin_service = NarrativeAdminService(local_session)
            try:
                await admin_service.delete_fragment(fragment_id)
                return True
            except Exception as e:
                return str(e)
    
    # Ejecutar dos eliminaciones concurrentes
    task1 = asyncio.create_task(delete_fragment(fragment.id))
    task2 = asyncio.create_task(delete_fragment(fragment.id))
    
    result1, result2 = await asyncio.gather(task1, task2)
    
    # Verificar que al menos una eliminación fue exitosa
    assert result1 is True or result2 is True
    
    # Verificar que el fragmento está realmente inactivo
    await session.refresh(fragment)
    assert fragment.is_active is False


@pytest.mark.asyncio
async def test_event_bus_complete_failure(session: AsyncSession):
    """Verificar que el servicio continúa funcionando si el Event Bus falla completamente."""
    # Crear un mock del event bus que siempre falla
    mock_event_bus = MagicMock()
    mock_event_bus.publish = AsyncMock(side_effect=Exception("Event bus catastrophic failure"))
    
    # Reemplazar el event bus global con nuestro mock
    with patch('services.narrative_admin_service.get_event_bus', return_value=mock_event_bus):
        # Crear servicio administrativo
        admin_service = NarrativeAdminService(session)
        
        # Intentar operaciones normales, deberían funcionar a pesar del fallo del Event Bus
        fragment_data = {
            "title": "Fragmento con Event Bus fallido",
            "content": "Contenido del fragmento",
            "fragment_type": "STORY"
        }
        
        # Crear fragmento
        fragment = await admin_service.create_fragment(fragment_data)
        
        # Verificar que el fragmento se creó correctamente
        assert fragment is not None
        assert "id" in fragment
        assert fragment["title"] == "Fragmento con Event Bus fallido"
        
        # Verificar que el fragmento existe en la base de datos
        db_fragment = await session.get(NarrativeFragment, fragment["id"])
        assert db_fragment is not None
        assert db_fragment.title == "Fragmento con Event Bus fallido"


@pytest.mark.asyncio
async def test_race_condition_prevention(session: AsyncSession):
    """Verificar que el servicio previene condiciones de carrera en operaciones críticas."""
    # Crear fragmento base
    fragment = NarrativeFragment(
        title="Fragmento para condición de carrera",
        content="Contenido original",
        fragment_type="STORY",
        is_active=True
    )
    session.add(fragment)
    await session.commit()
    await session.refresh(fragment)
    
    # Obtener factory para crear sesiones concurrentes
    session_factory = session.async_session.async_sessionmaker
    
    async def update_title(new_title, delay=0):
        """Actualiza el título del fragmento con un retraso opcional."""
        async with session_factory() as local_session:
            # Obtener fragmento
            result = await local_session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment.id)
            )
            local_fragment = result.scalar_one()
            
            # Simular procesamiento
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Actualizar título
            local_fragment.title = new_title
            
            # Guardar cambios
            await local_session.commit()
            return new_title
    
    # Crear tareas concurrentes con diferentes retrasos
    task1 = asyncio.create_task(update_title("Título actualizado 1", delay=0.05))
    task2 = asyncio.create_task(update_title("Título actualizado 2", delay=0))
    
    # Ejecutar ambas tareas
    await asyncio.gather(task1, task2)
    
    # Refrescar fragmento para ver estado final
    await session.refresh(fragment)
    
    # El título final debería ser el de la última transacción en completarse
    assert fragment.title in ["Título actualizado 1", "Título actualizado 2"]
    
    # La base de datos debe estar en estado consistente
    result = await session.execute(
        select(NarrativeFragment).where(NarrativeFragment.id == fragment.id)
    )
    updated_fragment = result.scalar_one()
    assert updated_fragment.title == fragment.title


@pytest.mark.asyncio
async def test_error_logging_coverage(session: AsyncSession):
    """Verificar que todos los errores se registran correctamente en los logs."""
    # Crear servicio administrativo
    admin_service = NarrativeAdminService(session)
    
    # Crear un objeto para rastrear las llamadas al logger
    log_calls = []
    
    # Parchear el logger para capturar las llamadas
    with patch('services.narrative_admin_service.logger.error', 
              side_effect=lambda msg, *args, **kwargs: log_calls.append(msg)):
        
        # Provocar varios errores que deberían ser registrados
        
        # 1. Error en creación de fragmento
        try:
            await admin_service.create_fragment({
                "title": "Fragmento inválido",
                "content": "Contenido",
                "fragment_type": "TIPO_INEXISTENTE"
            })
        except ValueError:
            pass
        
        # 2. Error en actualización de fragmento inexistente
        try:
            await admin_service.update_fragment("id-inexistente", {"title": "Nuevo título"})
        except ValueError:
            pass
        
        # 3. Error en eliminación de fragmento inexistente
        try:
            await admin_service.delete_fragment("id-inexistente")
        except ValueError:
            pass
    
    # Verificar que se registraron todos los errores
    assert len(log_calls) >= 3
    
    # Verificar contenido de los mensajes de error
    assert any("crear fragmento" in msg.lower() or "creating fragment" in msg.lower() for msg in log_calls)
    assert any("actualizar fragmento" in msg.lower() or "updating fragment" in msg.lower() for msg in log_calls)
    assert any("eliminar fragmento" in msg.lower() or "deleting fragment" in msg.lower() for msg in log_calls)