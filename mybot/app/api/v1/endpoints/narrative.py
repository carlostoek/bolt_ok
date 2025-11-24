"""
Endpoints REST para el sistema narrativo.
Expone operaciones CRUD para fragmentos con soporte de nested creation.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.narrative_service import NarrativeService
from app.schemas.narrative import (
    FragmentCreate,
    FragmentUpdate,
    FragmentResponse,
    FragmentCreateResponse,
    ChoiceResponse
)
from app.core.exceptions import (
    AppException,
    DuplicateKeyException,
    FragmentNotFoundException,
    NestedCreationException
)

logger = logging.getLogger(__name__)

# Crear router para narrativa
router = APIRouter()


@router.post(
    "/fragments",
    response_model=FragmentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear fragmento con entidades anidadas",
    description="""
    Crea un fragmento narrativo con soporte completo de **Atomic Nested Creation**.

    ## Características

    - ✅ Crear producto de desbloqueo inline (sin ID previo)
    - ✅ Crear decisiones inline
    - ✅ Crear fragmentos destino inline (recursivo)
    - ✅ Transacción atómica (todo se crea o nada)
    - ✅ Sin copy-paste de IDs

    ## Ejemplo de Payload

    ```json
    {
      "key": "CAP_FINAL",
      "text": "Entrada al castillo oscuro...",
      "reward_besitos": 50,

      "unlock_product": {
        "name": "Llave Maestra",
        "price": 100,
        "is_vip_only": false
      },

      "choices": [
        {
          "text": "Entrar al salón del trono",
          "destination_fragment": {
            "key": "SALON_TRONO",
            "text": "El rey te espera...",
            "reward_besitos": 20
          }
        }
      ]
    }
    ```

    ## Resultado

    - 1 producto creado ("Llave Maestra")
    - 1 fragmento principal creado ("CAP_FINAL")
    - 1 fragmento destino creado ("SALON_TRONO")
    - 1 decisión creada vinculando CAP_FINAL → SALON_TRONO

    Todo en una única transacción atómica.
    """
)
async def create_fragment_with_nested(
    data: FragmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear fragmentos con nested creation.

    Args:
        data: Datos del fragmento con entidades anidadas opcionales
        db: Sesión de base de datos (inyectada)

    Returns:
        Fragmento creado con resumen de entidades anidadas

    Raises:
        409: Si la key del fragmento ya existe
        422: Si hay errores de validación
        500: Si falla la transacción
    """
    try:
        logger.info(f"POST /fragments - Creando fragmento: {data.key}")

        # Instanciar servicio con la sesión de BD
        service = NarrativeService(db)

        # Ejecutar creación anidada atómica
        result = await service.create_fragment_with_nested(data)

        # Construir respuesta
        fragment = result["fragment"]
        created_product = result["created_product"]
        created_choices = result["created_choices"]
        summary = result["summary"]

        response = FragmentCreateResponse(
            success=True,
            fragment=FragmentResponse(
                id=fragment.id,
                key=fragment.key,
                text=fragment.text,
                image_url=fragment.image_url,
                min_besitos=fragment.min_besitos,
                required_role=fragment.required_role,
                reward_besitos=fragment.reward_besitos,
                auto_next_fragment_key=fragment.auto_next_fragment_key,
                choices=[
                    ChoiceResponse(
                        id=choice.id,
                        text=choice.text,
                        destination_fragment_key=choice.destination_fragment_key,
                        required_besitos=choice.required_besitos,
                        required_role=choice.required_role,
                        is_hidden=choice.is_hidden
                    )
                    for choice in created_choices
                ]
            ),
            created_product={
                "id": created_product.id,
                "name": created_product.name,
                "price": created_product.price,
                "unlocks_fragment_key": created_product.unlocks_fragment_key
            } if created_product else None,
            created_choices=[
                {
                    "id": choice.id,
                    "text": choice.text,
                    "destination": choice.destination_fragment_key
                }
                for choice in created_choices
            ],
            summary=summary
        )

        logger.info(
            f"✅ Fragmento '{data.key}' creado exitosamente - "
            f"{summary['fragments_created']} fragmentos, "
            f"{summary['products_created']} productos, "
            f"{summary['choices_created']} decisiones"
        )

        return response

    except DuplicateKeyException as e:
        logger.warning(f"⚠️  Key duplicada: {e.message}")
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
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/fragments/{key}",
    response_model=FragmentResponse,
    summary="Obtener fragmento por key",
    description="Obtiene un fragmento narrativo específico por su key única."
)
async def get_fragment(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un fragmento por su key.

    Args:
        key: Key única del fragmento
        db: Sesión de base de datos (inyectada)

    Returns:
        Fragmento encontrado con sus decisiones

    Raises:
        404: Si no existe el fragmento
    """
    try:
        logger.info(f"GET /fragments/{key}")

        service = NarrativeService(db)
        fragment = await service.get_fragment_by_key(key)

        return FragmentResponse(
            id=fragment.id,
            key=fragment.key,
            text=fragment.text,
            image_url=fragment.image_url,
            min_besitos=fragment.min_besitos,
            required_role=fragment.required_role,
            reward_besitos=fragment.reward_besitos,
            auto_next_fragment_key=fragment.auto_next_fragment_key,
            choices=[
                ChoiceResponse(
                    id=choice.id,
                    text=choice.text,
                    destination_fragment_key=choice.destination_fragment_key,
                    required_besitos=choice.required_besitos,
                    required_role=choice.required_role,
                    is_hidden=choice.is_hidden
                )
                for choice in fragment.choices
            ]
        )

    except FragmentNotFoundException as e:
        logger.warning(f"⚠️  Fragmento no encontrado: {key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener fragmento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener fragmento: {str(e)}"
        )


@router.get(
    "/fragments",
    response_model=List[FragmentResponse],
    summary="Listar fragmentos",
    description="Obtiene todos los fragmentos con paginación."
)
async def list_fragments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los fragmentos con paginación.

    Args:
        skip: Número de fragmentos a saltar (default: 0)
        limit: Número máximo de fragmentos a devolver (default: 100)
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista de fragmentos
    """
    try:
        logger.info(f"GET /fragments?skip={skip}&limit={limit}")

        service = NarrativeService(db)
        fragments = await service.get_all_fragments(skip=skip, limit=limit)

        return [
            FragmentResponse(
                id=fragment.id,
                key=fragment.key,
                text=fragment.text,
                image_url=fragment.image_url,
                min_besitos=fragment.min_besitos,
                required_role=fragment.required_role,
                reward_besitos=fragment.reward_besitos,
                auto_next_fragment_key=fragment.auto_next_fragment_key,
                choices=[
                    ChoiceResponse(
                        id=choice.id,
                        text=choice.text,
                        destination_fragment_key=choice.destination_fragment_key,
                        required_besitos=choice.required_besitos,
                        required_role=choice.required_role,
                        is_hidden=choice.is_hidden
                    )
                    for choice in fragment.choices
                ]
            )
            for fragment in fragments
        ]

    except Exception as e:
        logger.error(f"❌ Error al listar fragmentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar fragmentos: {str(e)}"
        )


@router.put(
    "/fragments/{key}",
    response_model=FragmentResponse,
    summary="Actualizar fragmento",
    description="Actualiza un fragmento existente. Solo actualiza los campos proporcionados."
)
async def update_fragment(
    key: str,
    data: FragmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un fragmento existente.

    Args:
        key: Key del fragmento a actualizar
        data: Datos de actualización (parciales)
        db: Sesión de base de datos (inyectada)

    Returns:
        Fragmento actualizado

    Raises:
        404: Si no existe el fragmento
        409: Si la nueva key ya existe
    """
    try:
        logger.info(f"PUT /fragments/{key}")

        service = NarrativeService(db)
        fragment = await service.update_fragment(key, data)

        return FragmentResponse(
            id=fragment.id,
            key=fragment.key,
            text=fragment.text,
            image_url=fragment.image_url,
            min_besitos=fragment.min_besitos,
            required_role=fragment.required_role,
            reward_besitos=fragment.reward_besitos,
            auto_next_fragment_key=fragment.auto_next_fragment_key,
            choices=[
                ChoiceResponse(
                    id=choice.id,
                    text=choice.text,
                    destination_fragment_key=choice.destination_fragment_key,
                    required_besitos=choice.required_besitos,
                    required_role=choice.required_role,
                    is_hidden=choice.is_hidden
                )
                for choice in fragment.choices
            ]
        )

    except FragmentNotFoundException as e:
        logger.warning(f"⚠️  Fragmento no encontrado: {key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except DuplicateKeyException as e:
        logger.warning(f"⚠️  Key duplicada: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al actualizar fragmento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar fragmento: {str(e)}"
        )


@router.delete(
    "/fragments/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar fragmento",
    description="Elimina un fragmento por su key. También elimina sus decisiones asociadas (cascade)."
)
async def delete_fragment(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un fragmento por su key.

    Args:
        key: Key del fragmento a eliminar
        db: Sesión de base de datos (inyectada)

    Returns:
        204 No Content si se eliminó correctamente

    Raises:
        404: Si no existe el fragmento
    """
    try:
        logger.info(f"DELETE /fragments/{key}")

        service = NarrativeService(db)
        await service.delete_fragment(key)

        logger.info(f"✅ Fragmento '{key}' eliminado exitosamente")

    except FragmentNotFoundException as e:
        logger.warning(f"⚠️  Fragmento no encontrado: {key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al eliminar fragmento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar fragmento: {str(e)}"
        )
