"""
Esquemas Pydantic para el módulo de lore.
Incluye modelos de request/response para la API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LoreBase(BaseModel):
    """Esquema base para piezas de lore."""
    lore_id: str = Field(..., max_length=50, description="Identificador único del lore")
    title: str = Field(..., max_length=255, description="Título del lore")
    content: str = Field(..., description="Contenido del lore")
    image_url: Optional[str] = Field(None, max_length=500, description="URL de imagen asociada")
    is_unlocked_by_default: bool = Field(default=False, description="Si está desbloqueado por defecto")
    required_role: Optional[str] = Field(None, max_length=50, description="Rol requerido para desbloquear")


class LoreCreate(LoreBase):
    """Esquema para crear una pieza de lore."""
    pass


class LoreUpdate(BaseModel):
    """Esquema para actualizar una pieza de lore."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_unlocked_by_default: Optional[bool] = None
    required_role: Optional[str] = Field(None, max_length=50)


class LoreResponse(LoreBase):
    """Esquema de respuesta para piezas de lore."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoreListResponse(BaseModel):
    """Respuesta paginada para listar piezas de lore."""
    data: List[LoreResponse]
    pagination: Dict[str, Any]


class LoreFilterParams(BaseModel):
    """Parámetros de filtro para listar piezas de lore."""
    is_unlocked_by_default: Optional[bool] = None
    required_role: Optional[str] = None
    search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    class Config:
        extra = "forbid"