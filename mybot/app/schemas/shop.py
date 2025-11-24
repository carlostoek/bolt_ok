"""
Esquemas Pydantic V2 para el sistema de tienda.
DTOs (Data Transfer Objects) para validación de entrada/salida.
"""
from typing import Optional, ForwardRef
from pydantic import BaseModel, Field, ConfigDict, model_validator


# ============================================================================
# FORWARD REFERENCES - Para resolver dependencias circulares
# ============================================================================

# FragmentCreateNested se usa dentro de ProductCreate
FragmentCreateNestedRef = ForwardRef('FragmentCreateNested')


# ============================================================================
# NESTED CREATION SCHEMAS - Para crear entidades inline
# ============================================================================

class FragmentCreateNested(BaseModel):
    """
    Schema para crear un fragmento narrativo inline (sin ID previo).

    Usado como fragmento de desbloqueo cuando se crea un producto
    y su fragmento destino aún no existe.

    Ejemplo:
        {
            "key": "CAPITULO_FINAL",
            "text": "Has llegado al capítulo final de la historia...",
            "reward_besitos": 100
        }
    """
    key: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=1)
    image_url: Optional[str] = Field(None, max_length=500)
    min_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = Field(None, max_length=50)
    reward_besitos: int = Field(0, ge=0)
    auto_next_fragment_key: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


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
    Schema principal para creación atómica de productos de tienda.

    SOPORTA NESTED CREATION:
    - Fragmento de desbloqueo (inline)

    Ejemplo completo:
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

    Este payload crea:
    - 1 producto (Llave Maestra)
    - 1 fragmento nested (CAPITULO_FINAL) vinculado al producto

    Todo en una sola transacción atómica.
    """
    # Campos obligatorios
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: int = Field(..., ge=0)
    is_vip_only: bool = False
    max_purchases_per_user: int = Field(1, ge=1)

    # Campos opcionales
    stock_limit: Optional[int] = Field(None, ge=0)

    # Referencias a entidades existentes
    unlocks_fragment_key: Optional[str] = Field(None, max_length=50)

    # Nested creation - Crear fragmento inline
    unlocks_fragment: Optional['FragmentCreateNested'] = None

    @model_validator(mode='after')
    def validate_unlocks_fragment(self):
        """
        Valida que NO se proporcionen ambos:
        - unlocks_fragment_key (referencia)
        - unlocks_fragment (nested creation)
        """
        has_key = self.unlocks_fragment_key is not None
        has_fragment = self.unlocks_fragment is not None

        if has_key and has_fragment:
            raise ValueError(
                "No se puede proporcionar tanto 'unlocks_fragment_key' "
                "como 'unlocks_fragment'. Elige uno."
            )

        return self

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


class ProductCreateResponse(BaseModel):
    """
    Schema de respuesta al crear un producto con nested creation.

    Incluye resumen de todas las entidades creadas.
    """
    success: bool
    product: ProductResponse
    created_fragment: Optional[dict] = None
    summary: dict

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RESOLVER FORWARD REFERENCES
# ============================================================================

# IMPORTANTE: Actualizar las referencias circulares después de definir todos los modelos
ProductCreate.model_rebuild()
