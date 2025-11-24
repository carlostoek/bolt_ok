"""
Esquemas Pydantic V2 para el sistema de tienda.
DTOs (Data Transfer Objects) para validación de entrada/salida.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# NESTED CREATION SCHEMAS - Para crear productos inline sin ID previo
# ============================================================================

class ProductCreateNested(BaseModel):
    """
    Schema para crear un producto inline (sin ID previo).

    Usado cuando se quiere crear un fragmento narrativo Y su producto
    de desbloqueo en una sola petición.

    Ejemplo:
        {
            "name": "Llave Maestra",
            "description": "Desbloquea el capítulo final",
            "price": 100,
            "is_vip_only": false
        }
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: int = Field(..., ge=0)
    is_vip_only: bool = False
    stock_limit: Optional[int] = Field(None, ge=0)
    max_purchases_per_user: int = Field(1, ge=1)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STANDARD CRUD SCHEMAS
# ============================================================================

class ProductCreate(BaseModel):
    """
    Schema para crear un producto de forma estándar (con FK opcional).

    Si se proporciona unlocks_fragment_key, el fragmento DEBE existir.
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: int = Field(..., ge=0)
    is_vip_only: bool = False
    unlocks_fragment_key: Optional[str] = Field(None, max_length=50)
    stock_limit: Optional[int] = Field(None, ge=0)
    max_purchases_per_user: int = Field(1, ge=1)

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto existente."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[int] = Field(None, ge=0)
    is_vip_only: Optional[bool] = None
    unlocks_fragment_key: Optional[str] = Field(None, max_length=50)
    stock_limit: Optional[int] = Field(None, ge=0)
    max_purchases_per_user: Optional[int] = Field(None, ge=1)

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """Schema para la respuesta al obtener un producto."""
    id: int
    name: str
    description: Optional[str]
    price: int
    is_vip_only: bool
    unlocks_fragment_key: Optional[str]
    stock_limit: Optional[int]
    max_purchases_per_user: int

    model_config = ConfigDict(from_attributes=True)
