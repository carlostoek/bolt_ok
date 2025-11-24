"""
Esquemas Pydantic V2 para el sistema narrativo.
Incluye soporte completo para Atomic Nested Creation.
"""
from typing import Optional, List, ForwardRef
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from app.schemas.shop import ProductCreateNested


# ============================================================================
# FORWARD REFERENCES - Para resolver dependencias circulares
# ============================================================================

# FragmentCreateNested se usa dentro de ChoiceCreateNested
# y ChoiceCreateNested se usa dentro de FragmentCreateNested
FragmentCreateNestedRef = ForwardRef('FragmentCreateNested')


# ============================================================================
# NESTED CREATION SCHEMAS - Para crear entidades inline
# ============================================================================

class FragmentCreateNested(BaseModel):
    """
    Schema para crear un fragmento inline (sin ID previo).

    Usado como destino de decisiones narrativas cuando el fragmento
    destino aún no existe.

    Ejemplo:
        {
            "key": "SALON_TRONO",
            "text": "El rey te espera sentado en su trono...",
            "reward_besitos": 20
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


class ChoiceCreateNested(BaseModel):
    """
    Schema para crear una decisión narrativa inline.

    IMPORTANTE: Se debe proporcionar SOLO UNO de estos campos:
    - destination_fragment_key: Referencia a un fragmento existente
    - destination_fragment: Crea un nuevo fragmento destino inline

    Ejemplos:

    1. Referencia a fragmento existente:
        {
            "text": "Entrar al castillo",
            "destination_fragment_key": "CASTILLO_ENTRADA",
            "required_besitos": 50
        }

    2. Crear fragmento destino inline:
        {
            "text": "Explorar el sótano",
            "destination_fragment": {
                "key": "SOTANO_OSCURO",
                "text": "Desciendes por unas escaleras húmedas..."
            }
        }
    """
    text: str = Field(..., min_length=1, max_length=255)
    destination_fragment_key: Optional[str] = Field(None, max_length=50)
    destination_fragment: Optional[FragmentCreateNestedRef] = None
    required_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = Field(None, max_length=50)
    is_hidden: bool = False

    @model_validator(mode='after')
    def validate_destination(self):
        """
        Valida que se proporcione EXACTAMENTE uno de:
        - destination_fragment_key
        - destination_fragment
        """
        has_key = self.destination_fragment_key is not None
        has_fragment = self.destination_fragment is not None

        if has_key and has_fragment:
            raise ValueError(
                "No se puede proporcionar tanto 'destination_fragment_key' "
                "como 'destination_fragment'. Elige uno."
            )

        if not has_key and not has_fragment:
            raise ValueError(
                "Se debe proporcionar 'destination_fragment_key' "
                "o 'destination_fragment'"
            )

        return self

    model_config = ConfigDict(from_attributes=True)


class FragmentCreate(BaseModel):
    """
    Schema principal para creación atómica de fragmentos narrativos.

    SOPORTA NESTED CREATION:
    - Producto de desbloqueo (inline)
    - Decisiones narrativas (inline)
    - Fragmentos destino de decisiones (inline recursivo)

    Ejemplo completo:
        {
            "key": "CAP_FINAL",
            "text": "Entrada al castillo oscuro...",
            "min_besitos": 0,
            "reward_besitos": 50,

            "unlock_product": {
                "name": "Llave Maestra",
                "description": "Desbloquea el capítulo final",
                "price": 100,
                "is_vip_only": false
            },

            "choices": [
                {
                    "text": "Entrar al salón del trono",
                    "destination_fragment": {
                        "key": "SALON_TRONO",
                        "text": "El rey te espera...",
                        "reward_besitos": 20
                    }
                }
            ]
        }

    Este payload crea:
    - 1 fragmento principal (CAP_FINAL)
    - 1 producto nested (Llave Maestra) vinculado al fragmento
    - 1 decisión nested
    - 1 fragmento destino nested (SALON_TRONO)

    Todo en una sola transacción atómica.
    """
    # Campos obligatorios
    key: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=1)

    # Campos opcionales
    image_url: Optional[str] = Field(None, max_length=500)
    min_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = Field(None, max_length=50)
    reward_besitos: int = Field(0, ge=0)
    auto_next_fragment_key: Optional[str] = Field(None, max_length=50)

    # Referencias a entidades existentes
    unlock_product_id: Optional[int] = Field(None, ge=1)

    # Nested creation - Crear entidades inline
    unlock_product: Optional[ProductCreateNested] = None
    choices: Optional[List[ChoiceCreateNested]] = None

    @field_validator('unlock_product_id')
    @classmethod
    def validate_unlock_product(cls, v, info):
        """
        Valida que NO se proporcionen ambos:
        - unlock_product_id (referencia)
        - unlock_product (nested creation)
        """
        unlock_product = info.data.get('unlock_product')

        if v and unlock_product:
            raise ValueError(
                "No se puede proporcionar tanto 'unlock_product_id' "
                "como 'unlock_product'. Elige uno."
            )

        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STANDARD CRUD SCHEMAS
# ============================================================================

class FragmentUpdate(BaseModel):
    """Schema para actualizar un fragmento existente."""
    key: Optional[str] = Field(None, min_length=1, max_length=50)
    text: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, max_length=500)
    min_besitos: Optional[int] = Field(None, ge=0)
    required_role: Optional[str] = Field(None, max_length=50)
    reward_besitos: Optional[int] = Field(None, ge=0)
    auto_next_fragment_key: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


class ChoiceResponse(BaseModel):
    """Schema para la respuesta al obtener una decisión."""
    id: int
    text: str
    destination_fragment_key: str
    required_besitos: int
    required_role: Optional[str]
    is_hidden: bool

    model_config = ConfigDict(from_attributes=True)


class FragmentResponse(BaseModel):
    """Schema para la respuesta al obtener un fragmento."""
    id: int
    key: str
    text: str
    image_url: Optional[str]
    min_besitos: int
    required_role: Optional[str]
    reward_besitos: int
    auto_next_fragment_key: Optional[str]
    choices: List[ChoiceResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FragmentCreateResponse(BaseModel):
    """
    Schema de respuesta al crear un fragmento con nested creation.

    Incluye resumen de todas las entidades creadas.
    """
    success: bool
    fragment: FragmentResponse
    created_product: Optional[dict] = None
    created_choices: List[dict] = []
    summary: dict

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RESOLVER FORWARD REFERENCES
# ============================================================================

# IMPORTANTE: Actualizar las referencias circulares después de definir todos los modelos
ChoiceCreateNested.model_rebuild()
FragmentCreate.model_rebuild()
