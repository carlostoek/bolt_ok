"""
Módulo de seguridad para el panel de administración.

Incluye:
- Hash de contraseñas con bcrypt
- Generación y verificación de tokens JWT
- Utilidades de autenticación
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# Contexto para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Algoritmo para JWT
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña
        
    Returns:
        bool: True si la contraseña coincide
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera el hash de una contraseña.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de acceso.
    
    Args:
        data: Datos a incluir en el token (sub, role, etc.)
        expires_delta: Tiempo de expiración del token
        
    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verifica y decodifica un token JWT.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        dict: Datos decodificados del token
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if user_id is None or role is None:
            raise credentials_exception
            
        return {
            "user_id": str(user_id),
            "role": str(role),
            "username": str(payload.get("username", "")),
            "email": str(payload.get("email", ""))
        }
        
    except JWTError:
        raise credentials_exception


def create_admin_token(user_id: str, username: str, email: str, role: str) -> str:
    """
    Crea un token JWT específico para administradores.
    
    Args:
        user_id: ID del usuario
        username: Nombre de usuario
        email: Email del administrador
        role: Rol del usuario (super_admin, content_admin, analyst)
        
    Returns:
        str: Token JWT de acceso
    """
    data = {
        "sub": user_id,
        "username": username,
        "email": email,
        "role": role
    }
    
    return create_access_token(data)


def validate_admin_role(current_role: str, required_roles: list[str]) -> bool:
    """
    Valida si el rol actual tiene permisos para acceder a un recurso.
    
    Args:
        current_role: Rol actual del usuario
        required_roles: Lista de roles permitidos
        
    Returns:
        bool: True si tiene permisos
    """
    # Jerarquía de roles (de mayor a menor privilegio)
    role_hierarchy = {
        "super_admin": 3,
        "admin": 2,
        "user": 1
    }
    
    # Si el rol actual está en la lista requerida, tiene acceso
    if current_role in required_roles:
        return True
    
    # Si el rol actual es superior a alguno de los requeridos, tiene acceso
    current_level = role_hierarchy.get(current_role, 0)
    for required_role in required_roles:
        required_level = role_hierarchy.get(required_role, 0)
        if current_level >= required_level:
            return True
    
    return False