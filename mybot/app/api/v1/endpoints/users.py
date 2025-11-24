"""
Endpoints REST para el sistema de usuarios.
Expone operaciones CRUD para usuarios con soporte de acciones administrativas.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileResponse,
    UserListResponse,
    UserActionRequest,
    UserActionResponse,
    UserFilterParams,
    UserRole
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException
)

logger = logging.getLogger(__name__)

# Crear router para usuarios
router = APIRouter()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario en el sistema."
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo usuario.

    Args:
        user_data: Datos del usuario a crear
        db: Sesión de base de datos (inyectada)

    Returns:
        Usuario creado

    Raises:
        409: Si el usuario ya existe
        422: Si hay errores de validación
    """
    try:
        logger.info(f"POST /users - Creando usuario: {user_data.id}")

        service = UserService(db)
        user = await service.create_user(user_data)

        logger.info(f"✅ Usuario '{user.id}' creado exitosamente")
        return user

    except ValidationException as e:
        logger.warning(f"⚠️  Error de validación: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al crear usuario: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID",
    description="Obtiene un usuario específico por su ID."
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un usuario por su ID.

    Args:
        user_id: ID del usuario (Telegram User ID)
        db: Sesión de base de datos (inyectada)

    Returns:
        Usuario encontrado

    Raises:
        404: Si no existe el usuario
    """
    try:
        logger.info(f"GET /users/{user_id}")

        service = UserService(db)
        user = await service.get_user(user_id)

        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        return user

    except NotFoundException as e:
        logger.warning(f"⚠️  Usuario no encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )


@router.get(
    "/users/{user_id}/profile",
    response_model=UserProfileResponse,
    summary="Obtener perfil completo de usuario",
    description="Obtiene el perfil completo de un usuario incluyendo progreso narrativo e inventario."
)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el perfil completo de un usuario.

    Args:
        user_id: ID del usuario
        db: Sesión de base de datos (inyectada)

    Returns:
        Perfil completo del usuario

    Raises:
        404: Si no existe el usuario
    """
    try:
        logger.info(f"GET /users/{user_id}/profile")

        service = UserService(db)
        profile = await service.get_user_with_profile(user_id)

        if not profile:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        return UserProfileResponse(
            user=profile["user"],
            narrative_progress=profile["narrative_progress"],
            inventory=profile["inventory"],
            missions_completed=profile["missions_completed"],
            achievements_unlocked=profile["achievements_unlocked"]
        )

    except NotFoundException as e:
        logger.warning(f"⚠️  Usuario no encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al obtener perfil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perfil: {str(e)}"
        )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Listar usuarios",
    description="Obtiene todos los usuarios con filtros y paginación."
)
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
    is_banned: Optional[bool] = Query(None, description="Filtrar por estado de baneo"),
    is_vip: Optional[bool] = Query(None, description="Filtrar por estado VIP"),
    min_points: Optional[int] = Query(None, ge=0, description="Puntos mínimos"),
    max_points: Optional[int] = Query(None, ge=0, description="Puntos máximos"),
    search: Optional[str] = Query(None, description="Buscar en username/nombre"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista usuarios con filtros y paginación.

    Args:
        role: Filtrar por rol
        is_banned: Filtrar por estado de baneo
        is_vip: Filtrar por estado VIP
        min_points: Puntos mínimos
        max_points: Puntos máximos
        search: Buscar en username/nombre
        page: Página
        per_page: Elementos por página
        db: Sesión de base de datos (inyectada)

    Returns:
        Lista paginada de usuarios
    """
    try:
        logger.info(f"GET /users?page={page}&per_page={per_page}")

        # Construir filtros
        filters = UserFilterParams(
            role=role,
            is_banned=is_banned,
            is_vip=is_vip,
            min_points=min_points,
            max_points=max_points,
            search=search
        )

        service = UserService(db)
        result = await service.list_users(filters, page=page, per_page=per_page)

        return UserListResponse(
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error(f"❌ Error al listar usuarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar usuarios: {str(e)}"
        )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Actualiza un usuario existente. Solo actualiza los campos proporcionados."
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un usuario existente.

    Args:
        user_id: ID del usuario a actualizar
        user_data: Datos de actualización (parciales)
        db: Sesión de base de datos (inyectada)

    Returns:
        Usuario actualizado

    Raises:
        404: Si no existe el usuario
    """
    try:
        logger.info(f"PUT /users/{user_id}")

        service = UserService(db)
        user = await service.update_user(user_id, user_data)

        return user

    except NotFoundException as e:
        logger.warning(f"⚠️  Usuario no encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al actualizar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )


@router.post(
    "/users/{user_id}/actions",
    response_model=UserActionResponse,
    summary="Ejecutar acción administrativa",
    description="Ejecuta una acción administrativa sobre un usuario (VIP, puntos, baneo, etc.)."
)
async def execute_user_action(
    user_id: int,
    action_data: UserActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta una acción administrativa sobre un usuario.

    Args:
        user_id: ID del usuario
        action_data: Datos de la acción a ejecutar
        db: Sesión de base de datos (inyectada)

    Returns:
        Resultado de la acción

    Raises:
        404: Si no existe el usuario
        422: Si la acción es inválida
    """
    try:
        logger.info(f"POST /users/{user_id}/actions - {action_data.action}")

        service = UserService(db)
        user = None
        message = ""

        # Ejecutar acción según tipo
        if action_data.action == "GRANT_VIP":
            if not action_data.duration_days:
                raise ValidationException("Se requiere duration_days para GRANT_VIP")
            user = await service.grant_vip(user_id, action_data.duration_days)
            message = f"VIP concedido por {action_data.duration_days} días"

        elif action_data.action == "ADD_POINTS":
            if not action_data.amount:
                raise ValidationException("Se requiere amount para ADD_POINTS")
            user = await service.add_points(user_id, action_data.amount)
            message = f"{action_data.amount} puntos añadidos"

        elif action_data.action == "REMOVE_POINTS":
            if not action_data.amount:
                raise ValidationException("Se requiere amount para REMOVE_POINTS")
            user = await service.remove_points(user_id, action_data.amount)
            message = f"{action_data.amount} puntos removidos"

        elif action_data.action == "BAN_USER":
            user = await service.ban_user(user_id)
            message = "Usuario baneado"

        elif action_data.action == "UNBAN_USER":
            user = await service.unban_user(user_id)
            message = "Usuario desbaneado"

        elif action_data.action == "SET_ROLE":
            if not action_data.role:
                raise ValidationException("Se requiere role para SET_ROLE")
            user = await service.set_user_role(user_id, action_data.role)
            message = f"Rol cambiado a {action_data.role}"

        elif action_data.action == "ADD_TO_INVENTORY":
            if not action_data.product_id:
                raise ValidationException("Se requiere product_id para ADD_TO_INVENTORY")
            await service.add_to_inventory(user_id, action_data.product_id)
            user = await service.get_user(user_id)
            message = f"Producto {action_data.product_id} añadido al inventario"

        elif action_data.action == "SET_FRAGMENT":
            if not action_data.fragment_key:
                raise ValidationException("Se requiere fragment_key para SET_FRAGMENT")
            await service.set_current_fragment(user_id, action_data.fragment_key)
            user = await service.get_user(user_id)
            message = f"Fragmento actual cambiado a {action_data.fragment_key}"

        if not user:
            raise ValidationException("Acción no implementada o usuario no encontrado")

        logger.info(f"✅ Acción '{action_data.action}' ejecutada exitosamente para usuario {user_id}")

        return UserActionResponse(
            success=True,
            message=message,
            user=user
        )

    except NotFoundException as e:
        logger.warning(f"⚠️  Usuario no encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except ValidationException as e:
        logger.warning(f"⚠️  Error de validación: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al ejecutar acción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar acción: {str(e)}"
        )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario por su ID."
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un usuario por su ID.

    Args:
        user_id: ID del usuario a eliminar
        db: Sesión de base de datos (inyectada)

    Returns:
        204 No Content si se eliminó correctamente

    Raises:
        404: Si no existe el usuario
    """
    try:
        logger.info(f"DELETE /users/{user_id}")

        service = UserService(db)
        user = await service.get_user(user_id)

        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        # Eliminar usuario y sus datos relacionados
        await service.db.delete(user)
        await service.db.commit()

        logger.info(f"✅ Usuario '{user_id}' eliminado exitosamente")

    except NotFoundException as e:
        logger.warning(f"⚠️  Usuario no encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

    except Exception as e:
        logger.error(f"❌ Error al eliminar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}"
        )