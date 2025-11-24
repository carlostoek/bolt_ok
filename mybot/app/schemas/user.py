"""
Esquemas Pydantic para el módulo de usuarios.
Incluye modelos de request/response para la API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario disponibles."""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserBase(BaseModel):
    """Esquema base para usuarios."""
    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    is_banned: bool = Field(default=False)
    is_vip: bool = Field(default=False)
    vip_expires_at: Optional[datetime] = None
    points: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)


class UserCreate(UserBase):
    """Esquema para crear un usuario."""
    id: int = Field(..., description="Telegram User ID", gt=0)


class UserUpdate(BaseModel):
    """Esquema para actualizar un usuario."""
    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_banned: Optional[bool] = None
    is_vip: Optional[bool] = None
    vip_expires_at: Optional[datetime] = None
    points: Optional[int] = Field(None, ge=0)
    level: Optional[int] = Field(None, ge=1)


class UserResponse(UserBase):
    """Esquema de respuesta para usuarios."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserNarrativeProgress(BaseModel):
    """Progreso narrativo de un usuario."""
    current_fragment_key: Optional[str]
    fragments_viewed: int
    choices_made: int
    unlocked_fragments: List[str]
    completion_percentage: float = Field(..., ge=0, le=1)


class InventoryItemResponse(BaseModel):
    """Ítem en el inventario de un usuario."""
    product_id: int
    product_name: str
    acquired_at: datetime
    quantity: int

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Perfil completo de un usuario."""
    user: UserResponse
    narrative_progress: UserNarrativeProgress
    inventory: List[InventoryItemResponse]
    missions_completed: int
    achievements_unlocked: int


class UserListResponse(BaseModel):
    """Respuesta paginada para listar usuarios."""
    data: List[UserResponse]
    pagination: Dict[str, Any]


class UserActionRequest(BaseModel):
    """Request para ejecutar acciones administrativas sobre usuarios."""
    action: str = Field(..., description="Tipo de acción a ejecutar")
    duration_days: Optional[int] = Field(None, ge=1, description="Duración en días para VIP")
    amount: Optional[int] = Field(None, ge=0, description="Cantidad de puntos")
    product_id: Optional[int] = Field(None, gt=0, description="ID del producto")
    fragment_key: Optional[str] = Field(None, description="Key del fragmento")
    reason: Optional[str] = Field(None, description="Razón de la acción")

    @validator('action')
    def validate_action(cls, v):
        valid_actions = [
            'GRANT_VIP', 'ADD_POINTS', 'REMOVE_POINTS', 
            'BAN_USER', 'UNBAN_USER', 'SET_ROLE',
            'ADD_TO_INVENTORY', 'SET_FRAGMENT'
        ]
        if v not in valid_actions:
            raise ValueError(f'Acción inválida. Válidas: {valid_actions}')
        return v


class UserActionResponse(BaseModel):
    """Respuesta después de ejecutar una acción administrativa."""
    success: bool
    message: str
    user: UserResponse


class UserFilterParams(BaseModel):
    """Parámetros de filtro para listar usuarios."""
    role: Optional[UserRole] = None
    is_banned: Optional[bool] = None
    is_vip: Optional[bool] = None
    min_points: Optional[int] = Field(None, ge=0)
    max_points: Optional[int] = Field(None, ge=0)
    search: Optional[str] = None
    registered_after: Optional[datetime] = None
    registered_before: Optional[datetime] = None

    class Config:
        extra = "forbid"