"""
Endpoints REST para el sistema de lore.
Expone operaciones CRUD para piezas de lore.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.lore_service import LoreService
from app.schemas.lore import (
    LoreCreate,
    LoreUpdate,
    LoreResponse,
    LoreListResponse,
    LoreFilterParams
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException
)

logger = logging.getLogger(__name__)

# Crear router para lore
router = APIRouter()


@router.post(
    "",
    response_model=LoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pieza de lore",
    description="Crea una nueva pieza de lore en el sistema."
)
async def create_lore_piece(
    lore_data: LoreCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva pieza de lore.

    Args:
        lore_data: Datos de la pieza de lore a crear
        db: Sesión de base de datos (inyectada)

    Returns:
        Pieza de lore creada

    Raises:
        409: Si el lore_id ya existe
        422: Si hay errores de validación
    """
    try:
        logger.info(f"POST /lore - Creando pieza de lore: {lore_data.lore_id}")

        service = LoreService(db)
        lore_piece = await service.create_lore_piece(lore_data)

        logger.info(f"✅ Pieza de lore '{lore_data.lore_id}' creada exitosamente")
        return lore_piece

    except ValidationException as e:
        logger.warning(f"⚠️  Error de validación: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al crear pieza de lore: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/{lore_id}",
    response_model=LoreResponse,
    summary="Obtener pieza de lore por ID",
    description="Obtiene una pieza de lore específica por su lore_id."
)
async def get_lore_piece(
    lore_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una pieza de lore por su lore_id.

    Args:
        lore_id: ID de negocio de la pieza de lore
        db: Sesión de base de datos (inyectada)

    Returns:
        Pieza de lore encontrada

    Raises:
        404: Si no existe la pieza de lore
    """
    try:
        logger.info(f"GET /lore/{lore_id}")

        service = LoreService(db)
        lore_piece = await service.get_lore_piece(lore_id)

        if not lore_piece:
            raise NotFoundException(f"Pieza de lore con ID '{lore_id}' no encontrada")

        return lore_piece

    except NotFoundException as e:
        logger.warning(f"⚠️  Pieza de lore no encontrada: {lore_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener pieza de lore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener pieza de lore"
        )


@router.get(
    "",
    response_model=LoreListResponse,
    summary="Listar piezas de lore",
    description="Obtiene todas las piezas de lore con filtros y paginación."
)
async def list_lore_pieces(
    is_unlocked_by_default: Optional[bool] = Query(None, description="Filtrar por desbloqueo por defecto"),
    required_role: Optional[str] = Query(None, description="Filtrar por rol requerido"),
    search: Optional[str] = Query(None, description="Buscar en lore_id/título/contenido"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista piezas de lore con filtros y paginación.

    Args:
        is_unlocked_by_default: Filtrar por desbloqueo por defecto
        required_role: Filtrar por rol requerido
        search: Buscar en lore_id/título/contenido
        page: Página
        per_page: Elementos por página
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista paginada de piezas de lore
    """
    try:
        logger.info(f"GET /lore?page={page}&per_page={per_page}")

        # Construir filtros
        filters = LoreFilterParams(
            is_unlocked_by_default=is_unlocked_by_default,
            required_role=required_role,
            search=search
        )

        service = LoreService(db)
        result = await service.list_lore_pieces(filters, page=page, per_page=per_page)

        return LoreListResponse(
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error(f"❌ Error al listar piezas de lore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar piezas de lore"
        )


@router.put(
    "/{lore_id}",
    response_model=LoreResponse,
    summary="Actualizar pieza de lore",
    description="Actualiza una pieza de lore existente. Solo actualiza los campos proporcionados."
)
async def update_lore_piece(
    lore_id: str,
    lore_data: LoreUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza una pieza de lore existente.

    Args:
        lore_id: ID de la pieza de lore a actualizar
        lore_data: Datos de actualización (parciales)
        db: Sesión de base de datos (inyectada)

    Returns:
        Pieza de lore actualizada

    Raises:
        404: Si no existe la pieza de lore
    """
    try:
        logger.info(f"PUT /lore/{lore_id}")

        service = LoreService(db)
        lore_piece = await service.update_lore_piece(lore_id, lore_data)

        return lore_piece

    except NotFoundException as e:
        logger.warning(f"⚠️  Pieza de lore no encontrada: {lore_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al actualizar pieza de lore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar pieza de lore"
        )


@router.delete(
    "/{lore_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar pieza de lore",
    description="Elimina una pieza de lore por su lore_id."
)
async def delete_lore_piece(
    lore_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina una pieza de lore por su lore_id.

    Args:
        lore_id: ID de la pieza de lore a eliminar
        db: Sesión de base de datos (inyectada)

    Returns:
        204 No Content si se eliminó correctamente

    Raises:
        404: Si no existe la pieza de lore
    """
    try:
        logger.info(f"DELETE /lore/{lore_id}")

        service = LoreService(db)
        await service.delete_lore_piece(lore_id)

        logger.info(f"✅ Pieza de lore '{lore_id}' eliminada exitosamente")

    except NotFoundException as e:
        logger.warning(f"⚠️  Pieza de lore no encontrada: {lore_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al eliminar pieza de lore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar pieza de lore"
        )


@router.get(
    "/search",
    response_model=List[LoreResponse],
    summary="Buscar piezas de lore",
    description="Busca piezas de lore por texto en lore_id, título o contenido."
)
async def search_lore_pieces(
    q: str = Query(..., description="Texto a buscar"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca piezas de lore por texto.

    Args:
        q: Texto a buscar
        limit: Límite de resultados
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista de piezas de lore que coinciden con la búsqueda
    """
    try:
        logger.info(f"GET /lore/search?q={q}&limit={limit}")

        service = LoreService(db)
        lore_pieces = await service.search_lore_pieces(q, limit)

        return lore_pieces

    except Exception as e:
        logger.error(f"❌ Error al buscar piezas de lore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al buscar piezas de lore"
        )


@router.get(
    "/statistics",
    summary="Estadísticas del sistema de lore",
    description="Obtiene estadísticas sobre las piezas de lore en el sistema."
)
async def get_lore_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene estadísticas del sistema de lore.

    Args:
        db: Sesión de base de datos (inyectada)

    Returns:
        Estadísticas del sistema de lore
    """
    try:
        logger.info("GET /lore/statistics")

        service = LoreService(db)
        statistics = await service.get_lore_statistics()

        return statistics

    except Exception as e:
        logger.error(f"❌ Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas"
        )