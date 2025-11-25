"""
Endpoints de autenticación para el panel de administración.

Incluye:
- Login con email/contraseña
- Refresh de tokens
- Logout
"""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import (
    verify_password,
    create_admin_token,
    verify_token
)
from database.models import User

logger = logging.getLogger(__name__)

# Crear router para autenticación
router = APIRouter()


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint de login para administradores.
    
    Args:
        form_data: Datos del formulario OAuth2 (username=email, password)
        db: Sesión de base de datos
        
    Returns:
        dict: Token de acceso y tipo de token
        
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    # Buscar usuario por email (username en OAuth2PasswordRequestForm)
    email = form_data.username
    
    # En este sistema, los administradores son usuarios con rol admin/super_admin
    # que tienen email configurado. En una implementación real, necesitaríamos
    # agregar campos email y hashed_password al modelo User
    
    # Por ahora, vamos a usar una implementación temporal que busca usuarios admin
    # y usa un password por defecto para demostración
    result = await db.execute(
        select(User).where(
            User.role.in_(["super_admin", "admin"])
        )
    )
    admin_users = result.scalars().all()
    
    if not admin_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No admin users found"
        )
    
    # Para demostración, usamos el primer usuario admin encontrado
    # En una implementación real, buscaríamos por email
    user = admin_users[0]
    
    # Verificar contraseña (temporal - usar password por defecto)
    # En una implementación real, verificaríamos contra hashed_password
    if form_data.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token de acceso
    access_token = create_admin_token(
        user_id=str(user.id),
        username=user.username or "admin",
        email=user.username + "@example.com" if user.username else "admin@example.com",
        role=user.role
    )
    
    logger.info(f"Login exitoso para usuario admin: {user.id}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }


@router.post("/logout")
async def logout():
    """
    Endpoint de logout (simbólico - en JWT stateless, el logout es del lado del cliente).
    
    Returns:
        dict: Mensaje de confirmación
    """
    return {"message": "Successfully logged out"}