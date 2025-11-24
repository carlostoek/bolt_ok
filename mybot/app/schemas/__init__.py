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
from app.schemas.lore import (
    LoreCreate,
    LoreUpdate,
    LoreResponse,
    LoreListResponse,
    LoreFilterParams
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
    "ProductCreateNested",
    # Users
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfileResponse",
    "UserListResponse",
    "UserActionRequest",
    "UserActionResponse",
    "UserFilterParams",
    "UserRole",
    # Lore
    "LoreCreate",
    "LoreUpdate",
    "LoreResponse",
    "LoreListResponse",
    "LoreFilterParams"
]
