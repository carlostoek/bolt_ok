"""Esquemas Pydantic para validación de datos."""

from app.schemas.narrative import (
    FragmentCreate,
    FragmentUpdate,
    FragmentResponse,
    FragmentCreateResponse,
    FragmentCreateNested,
    ChoiceCreateNested,
    ChoiceResponse
)
from app.schemas.shop import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductCreateNested
)

__all__ = [
    # Narrative
    "FragmentCreate",
    "FragmentUpdate",
    "FragmentResponse",
    "FragmentCreateResponse",
    "FragmentCreateNested",
    "ChoiceCreateNested",
    "ChoiceResponse",
    # Shop
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductCreateNested"
]
