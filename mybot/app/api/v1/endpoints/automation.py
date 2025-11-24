"""
Endpoints REST para el sistema de automatización dirigido por eventos.
Expone operaciones CRUD para triggers con soporte de nested creation.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.automation_service import AutomationService
from app.schemas.automation import (
    TriggerCreate,
    TriggerUpdate,
    TriggerResponse,
    TriggerCreateResponse,
    EventExecutionRequest,
    EventExecutionResponse
)
from app.core.exceptions import (
    AppException,
    DuplicateKeyException,
    TriggerNotFoundException,
    NestedCreationException,
    DatabaseException
)

logger = logging.getLogger(__name__)

# Crear router para automatización
router = APIRouter()


@router.post(
    "/triggers",
    response_model=TriggerCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear trigger con acciones anidadas",
    description="""
    Crea un trigger de automatización con soporte completo de **Atomic Nested Creation**.

    ## Características

    - ✅ Crear acciones inline (sin ID previo)
    - ✅ Transacción atómica (todo se crea o nada)
    - ✅ Evaluación de condiciones configurable

    ## Ejemplo de Payload

    ```json
    {
      "name": "recompensa_primer_fragmento",
      "description": "Da 100 puntos al ver el primer fragmento",
      "event_type": "fragment_viewed",
      "conditions": {
        "fragment_key": "WELCOME"
      },
      "is_enabled": true,
      "priority": 1,

      "actions": [
        {
          "action_type": "add_points",
          "parameters": {
            "amount": 100,
            "reason": "¡Bienvenido a la aventura!"
          },
          "execution_order": 1
        }
      ]
    }
    ```

    ## Resultado

    - 1 trigger creado ("recompensa_primer_fragmento")
    - 1 acción nested creada ("add_points")
    - Trigger vinculado automáticamente a la acción

    Todo en una única transacción atómica.
    """
)
async def create_trigger_with_actions(
    data: TriggerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear triggers con nested creation.

    Args:
        data: Datos del trigger con acciones anidadas opcionales
        db: Sesión de base de datos (inyectada)

    Returns:
        Trigger creado con resumen de entidades anidadas

    Raises:
        409: Si el nombre del trigger ya existe
        422: Si hay errores de validación
        500: Si falla la transacción
    """
    try:
        logger.info(f"POST /triggers - Creando trigger: {data.name}")

        # Instanciar servicio con la sesión de BD
        service = AutomationService(db)

        # Ejecutar creación anidada atómica
        result = await service.create_trigger_with_actions(data)

        # Construir respuesta
        trigger = result["trigger"]
        created_actions = result["created_actions"]
        summary = result["summary"]

        response = TriggerCreateResponse(
            success=True,
            trigger=trigger,
            created_actions=created_actions,
            summary=summary
        )

        logger.info(
            f"✅ Trigger '{data.name}' creado exitosamente - "
            f"{summary['total_entities']} entidades creadas"
        )

        return response

    except DuplicateKeyException as e:
        logger.warning(f"⚠️  Nombre duplicado: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )

    except NestedCreationException as e:
        logger.error(f"❌ Error en creación anidada: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )

    except AppException as e:
        logger.error(f"❌ Error de aplicación: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.post(
    "/test-event",
    response_model=EventExecutionResponse,
    summary="Probar ejecución de evento",
    description="""
    Simula la ejecución de un evento para verificar qué triggers se dispararían.

    ## Características

    - ✅ Simula ejecución sin efectos reales
    - ✅ Muestra qué triggers cumplen condiciones
    - ✅ Muestra qué acciones se ejecutarían
    - ✅ Útil para testing y debugging

    ## Ejemplo de Payload

    ```json
    {
      "event_type": "fragment_viewed",
      "user_id": 123,
      "context": {
        "fragment_key": "WELCOME",
        "chapter": "introduccion"
      }
    }
    ```

    ## Resultado

    - Lista de triggers que se dispararían
    - Acciones que se ejecutarían
    - Resumen de la simulación
    """
)
async def test_event_execution(
    data: EventExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para probar la ejecución de un evento.

    Args:
        data: Datos del evento a simular
        db: Sesión de base de datos (inyectada)

    Returns:
        Resultado de la simulación con triggers ejecutados
    """
    try:
        logger.info(
            f"POST /test-event - Probando evento: {data.event_type} "
            f"(usuario: {data.user_id})"
        )

        service = AutomationService(db)
        result = await service.execute_triggers(
            event_type=data.event_type,
            user_id=data.user_id,
            context=data.context
        )

        response = EventExecutionResponse(
            success=True,
            event_type=data.event_type,
            user_id=data.user_id,
            triggers_executed=result["triggers_executed"],
            total_actions=result["total_actions"],
            summary=result["summary"]
        )

        logger.info(
            f"✅ Simulación completada: {len(result['triggers_executed'])} triggers, "
            f"{result['total_actions']} acciones"
        )

        return response

    except DatabaseException as e:
        logger.error(f"❌ Error en simulación: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error inesperado en simulación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.get(
    "/triggers/{trigger_id}",
    response_model=TriggerResponse,
    summary="Obtener trigger por ID",
    description="Obtiene un trigger específico por su ID con todas sus acciones."
)
async def get_trigger(
    trigger_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un trigger por su ID.

    Args:
        trigger_id: ID del trigger
        db: Sesión de base de datos (inyectada)

    Returns:
        Trigger encontrado con sus acciones

    Raises:
        404: Si no existe el trigger
    """
    try:
        logger.info(f"GET /triggers/{trigger_id}")

        service = AutomationService(db)
        trigger = await service.get_trigger(trigger_id)

        if not trigger:
            raise TriggerNotFoundException(trigger_id)

        return trigger

    except TriggerNotFoundException as e:
        logger.warning(f"⚠️  Trigger no encontrado: {trigger_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener trigger: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.get(
    "/triggers",
    response_model=List[TriggerResponse],
    summary="Listar triggers",
    description="Obtiene todos los triggers con filtros opcionales."
)
async def list_triggers(
    event_type: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    is_enabled: Optional[bool] = Query(None, description="Filtrar por estado habilitado"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los triggers con filtros opcionales.

    Args:
        event_type: Filtrar por tipo de evento
        is_enabled: Filtrar por estado habilitado
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista de triggers
    """
    try:
        logger.info(f"GET /triggers?event_type={event_type}&is_enabled={is_enabled}")

        service = AutomationService(db)
        triggers = await service.get_all_triggers(
            event_type=event_type,
            is_enabled=is_enabled
        )

        return triggers

    except Exception as e:
        logger.error(f"❌ Error al listar triggers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.put(
    "/triggers/{trigger_id}",
    response_model=TriggerResponse,
    summary="Actualizar trigger",
    description="Actualiza un trigger existente. Solo actualiza los campos proporcionados."
)
async def update_trigger(
    trigger_id: int,
    data: TriggerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un trigger existente.

    Args:
        trigger_id: ID del trigger a actualizar
        data: Datos de actualización (parciales)
        db: Sesión de base de datos (inyectada)

    Returns:
        Trigger actualizado

    Raises:
        404: Si no existe el trigger
    """
    try:
        logger.info(f"PUT /triggers/{trigger_id}")

        service = AutomationService(db)
        trigger = await service.update_trigger(trigger_id, data)

        if not trigger:
            raise TriggerNotFoundException(trigger_id)

        return trigger

    except TriggerNotFoundException as e:
        logger.warning(f"⚠️  Trigger no encontrado: {trigger_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al actualizar trigger: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.delete(
    "/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar trigger",
    description="Elimina un trigger por su ID."
)
async def delete_trigger(
    trigger_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un trigger por su ID.

    Args:
        trigger_id: ID del trigger a eliminar
        db: Sesión de base de datos (inyectada)

    Returns:
        204 No Content si se eliminó correctamente

    Raises:
        404: Si no existe el trigger
    """
    try:
        logger.info(f"DELETE /triggers/{trigger_id}")

        service = AutomationService(db)
        deleted = await service.delete_trigger(trigger_id)

        if not deleted:
            raise TriggerNotFoundException(trigger_id)

        logger.info(f"✅ Trigger '{trigger_id}' eliminado exitosamente")

    except TriggerNotFoundException as e:
        logger.warning(f"⚠️  Trigger no encontrado: {trigger_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al eliminar trigger: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )