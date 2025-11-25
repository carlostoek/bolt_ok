"""
Dependencias de autenticación y autorización para FastAPI.

Incluye:
- get_current_user: Valida token JWT y obtiene usuario
- require_role: Factory para verificar roles
- Dependencias para diferentes niveles de acceso
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_token, validate_admin_role
from app.database import get_db
from app.models.user import User

# Esquema de autenticación Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependencia que valida el token Bearer y obtiene el usuario actual.
    
    Args:
        credentials: Credenciales de autenticación Bearer
        db: Sesión de base de datos
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    # Verificar token
    token_data = verify_token(credentials.credentials)
    
    # Buscar usuario en la base de datos
    user_id = token_data["user_id"]
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    
    # Buscar usuario por ID
    result = await db.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verificar que el usuario no esté baneado
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia que verifica que el usuario esté activo.
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario activo
        
    Raises:
        HTTPException: Si el usuario está inactivo
    """
    # En este sistema, todos los usuarios están activos por defecto
    # Podemos agregar lógica adicional aquí si es necesario
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia que verifica que el usuario sea administrador.
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    # Verificar que el usuario tenga rol de administrador
    admin_roles = ["super_admin", "admin"]
    
    if current_user.role.value not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return current_user


async def get_current_super_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia que verifica que el usuario sea super administrador.
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario super administrador
        
    Raises:
        HTTPException: Si el usuario no es super administrador
    """
    if current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    
    return current_user


async def get_current_content_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia que verifica que el usuario sea admin o superior.
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario admin o superior
        
    Raises:
        HTTPException: Si el usuario no tiene permisos suficientes
    """
    allowed_roles = ["super_admin", "admin"]
    
    if current_user.role.value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def get_current_analyst(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia que verifica que el usuario sea admin o superior.
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario admin o superior
        
    Raises:
        HTTPException: Si el usuario no tiene permisos suficientes
    """
    allowed_roles = ["super_admin", "admin"]
    
    if current_user.role.value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def require_role(required_roles: list[str]):
    """
    Factory de dependencias que verifica roles específicos.
    
    Args:
        required_roles: Lista de roles permitidos
        
    Returns:
        Dependencia que verifica los roles
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        """
        Verifica que el usuario tenga uno de los roles requeridos.
        """
        if not validate_admin_role(current_user.role.value, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


# Tipos anotados para uso en endpoints
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
CurrentSuperAdmin = Annotated[User, Depends(get_current_super_admin)]
CurrentContentAdmin = Annotated[User, Depends(get_current_content_admin)]
CurrentAnalyst = Annotated[User, Depends(get_current_analyst)]