"""
Endpoints REST para el sistema de tienda.
Expone operaciones CRUD para productos con soporte de nested creation.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.shop_service import ShopService
from app.schemas.shop import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductCreateResponse
)
from app.core.exceptions import (
    AppException,
    DuplicateKeyException,
    ProductNotFoundException,
    NestedCreationException
)

logger = logging.getLogger(__name__)

# Crear router para tienda
router = APIRouter()


@router.post(
    "/items",
    response_model=ProductCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto con fragmento anidado",
    description="""
    Crea un producto de tienda con soporte completo de **Atomic Nested Creation**.

    ## Características

    - ✅ Crear fragmento de desbloqueo inline (sin key previa)
    - ✅ Transacción atómica (todo se crea o nada)
    - ✅ Sin copy-paste de keys

    ## Ejemplo de Payload

    ```json
    {
      "name": "Llave Maestra",
      "description": "Desbloquea el capítulo final de la historia",
      "price": 100,
      "is_vip_only": false,
      "stock_limit": 50,
      "max_purchases_per_user": 1,

      "unlocks_fragment": {
        "key": "CAPITULO_FINAL",
        "text": "Has llegado al capítulo final de la historia...",
        "reward_besitos": 100
      }
    }
    ```

    ## Resultado

    - 1 producto creado ("Llave Maestra")
    - 1 fragmento nested creado ("CAPITULO_FINAL")
    - Producto vinculado automáticamente al fragmento

    Todo en una única transacción atómica.
    """
)
async def create_product_with_nested(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para crear productos con nested creation.

    Args:
        data: Datos del producto con fragmento anidado opcional
        db: Sesión de base de datos (inyectada)

    Returns:
        Producto creado con resumen de entidades anidadas

    Raises:
        409: Si la key del fragmento ya existe
        422: Si hay errores de validación
        500: Si falla la transacción
    """
    try:
        logger.info(f"POST /items - Creando producto: {data.name}")

        # Instanciar servicio con la sesión de BD
        service = ShopService(db)

        # Ejecutar creación anidada atómica
        result = await service.create_product_with_nested(data)

        # Construir respuesta
        product = result["product"]
        created_fragment = result["created_fragment"]
        summary = result["summary"]

        response = ProductCreateResponse(
            success=True,
            product=product,
            created_fragment=created_fragment,
            summary=summary
        )

        logger.info(
            f"✅ Producto '{data.name}' creado exitosamente - "
            f"{summary['total_entities']} entidades creadas"
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
            detail="Error interno del servidor."
        )


@router.get(
    "/items/{product_id}",
    response_model=ProductResponse,
    summary="Obtener producto por ID",
    description="Obtiene un producto específico por su ID."
)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un producto por su ID.

    Args:
        product_id: ID del producto
        db: Sesión de base de datos (inyectada)

    Returns:
        Producto encontrado

    Raises:
        404: Si no existe el producto
    """
    try:
        logger.info(f"GET /items/{product_id}")

        service = ShopService(db)
        product = await service.get_product(product_id)

        if not product:
            raise ProductNotFoundException(product_id)

        return product

    except ProductNotFoundException as e:
        logger.warning(f"⚠️  Producto no encontrado: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener producto: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.get(
    "/items",
    response_model=List[ProductResponse],
    summary="Listar productos",
    description="Obtiene todos los productos con filtros opcionales."
)
async def list_products(
    is_vip_only: Optional[bool] = Query(None, description="Filtrar por productos VIP"),
    in_stock: Optional[bool] = Query(None, description="Filtrar por productos en stock"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los productos con filtros opcionales.

    Args:
        is_vip_only: Filtrar por productos VIP
        in_stock: Filtrar por productos en stock
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista de productos
    """
    try:
        logger.info(f"GET /items?is_vip_only={is_vip_only}&in_stock={in_stock}")

        service = ShopService(db)
        products = await service.get_all_products(
            is_vip_only=is_vip_only,
            in_stock=in_stock
        )

        return products

    except Exception as e:
        logger.error(f"❌ Error al listar productos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.put(
    "/items/{product_id}",
    response_model=ProductResponse,
    summary="Actualizar producto",
    description="Actualiza un producto existente. Solo actualiza los campos proporcionados."
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un producto existente.

    Args:
        product_id: ID del producto a actualizar
        data: Datos de actualización (parciales)
        db: Sesión de base de datos (inyectada)

    Returns:
        Producto actualizado

    Raises:
        404: Si no existe el producto
    """
    try:
        logger.info(f"PUT /items/{product_id}")

        service = ShopService(db)
        product = await service.update_product(product_id, data)

        if not product:
            raise ProductNotFoundException(product_id)

        return product

    except ProductNotFoundException as e:
        logger.warning(f"⚠️  Producto no encontrado: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al actualizar producto: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )


@router.delete(
    "/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar producto",
    description="Elimina un producto por su ID."
)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un producto por su ID.

    Args:
        product_id: ID del producto a eliminar
        db: Sesión de base de datos (inyectada)

    Returns:
        204 No Content si se eliminó correctamente

    Raises:
        404: Si no existe el producto
    """
    try:
        logger.info(f"DELETE /items/{product_id}")

        service = ShopService(db)
        deleted = await service.delete_product(product_id)

        if not deleted:
            raise ProductNotFoundException(product_id)

        logger.info(f"✅ Producto '{product_id}' eliminado exitosamente")

    except ProductNotFoundException as e:
        logger.warning(f"⚠️  Producto no encontrado: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al eliminar producto: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )