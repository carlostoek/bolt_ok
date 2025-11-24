"""
Esquemas Pydantic V2 para el sistema de automatización dirigido por eventos.

Soporte completo para Atomic Nested Creation de triggers con sus acciones.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime

from app.models.automation import TriggerEventType, ActionType


# ============================================================================
# NESTED CREATION SCHEMAS - Para crear triggers con acciones inline
# ============================================================================

class ActionCreateNested(BaseModel):
    """
    Schema para crear una acción inline (sin ID previo).

    Usado cuando se quiere crear un trigger Y sus acciones en una sola petición.

    Ejemplo:
        {
            "action_type": "add_points",
            "parameters": {
                "amount": 100,
                "reason": "Recompensa por completar fragmento"
            },
            "execution_order": 1,
            "is_enabled": true
        }
    """
    action_type: str = Field(..., description="Tipo de acción a ejecutar")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    execution_order: int = Field(1, ge=1, le=10)
    is_enabled: bool = True

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        """Valida que el tipo de acción sea válido."""
        valid_types = [action_type.value for action_type in ActionType]
        if v not in valid_types:
            raise ValueError(f"Tipo de acción '{v}' no válido. Válidos: {valid_types}")
        return v

    model_config = ConfigDict(from_attributes=True)


class TriggerCreate(BaseModel):
    """
    Schema principal para creación atómica de triggers con acciones.

    SOPORTA NESTED CREATION:
    - Acciones de automatización (inline)

    Ejemplo completo:
        {
            "name": "recompensa_primer_fragmento",
            "description": "Da 100 puntos al ver el primer fragmento",
            "event_type": "fragment_viewed",
            "conditions": {
                "fragment_key": "WELCOME"
            },
            "is_enabled": true,
            "priority": 1,

            "actions": [
                {
                    "action_type": "add_points",
                    "parameters": {
                        "amount": 100,
                        "reason": "¡Bienvenido a la aventura!"
                    },
                    "execution_order": 1
                }
            ]
        }

    Este payload crea:
    - 1 trigger (recompensa_primer_fragmento)
    - 1 acción nested (add_points) vinculada al trigger

    Todo en una sola transacción atómica.
    """
    # Campos obligatorios
    name: str = Field(..., min_length=1, max_length=255)
    event_type: str = Field(..., description="Tipo de evento que dispara el trigger")
    
    # Campos opcionales
    description: Optional[str] = Field(None, max_length=1000)
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_enabled: bool = True
    priority: int = Field(1, ge=1, le=10)

    # Nested creation - Crear acciones inline
    actions: Optional[List[ActionCreateNested]] = None

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Valida que el tipo de evento sea válido."""
        valid_types = [event_type.value for event_type in TriggerEventType]
        if v not in valid_types:
            raise ValueError(f"Tipo de evento '{v}' no válido. Válidos: {valid_types}")
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STANDARD CRUD SCHEMAS
# ============================================================================

class ActionUpdate(BaseModel):
    """Schema para actualizar una acción existente."""
    action_type: Optional[str] = Field(None, description="Tipo de acción a ejecutar")
    parameters: Optional[Dict[str, Any]] = None
    execution_order: Optional[int] = Field(None, ge=1, le=10)
    is_enabled: Optional[bool] = None

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        """Valida que el tipo de acción sea válido."""
        if v is not None:
            valid_types = [action_type.value for action_type in ActionType]
            if v not in valid_types:
                raise ValueError(f"Tipo de acción '{v}' no válido. Válidos: {valid_types}")
        return v

    model_config = ConfigDict(from_attributes=True)


class TriggerUpdate(BaseModel):
    """Schema para actualizar un trigger existente."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    event_type: Optional[str] = Field(None, description="Tipo de evento que dispara el trigger")
    conditions: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Valida que el tipo de evento sea válido."""
        if v is not None:
            valid_types = [event_type.value for event_type in TriggerEventType]
            if v not in valid_types:
                raise ValueError(f"Tipo de evento '{v}' no válido. Válidos: {valid_types}")
        return v

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ActionResponse(BaseModel):
    """Schema para la respuesta al obtener una acción."""
    id: int
    trigger_id: int
    action_type: str
    parameters: Dict[str, Any]
    execution_order: int
    is_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TriggerResponse(BaseModel):
    """Schema para la respuesta al obtener un trigger."""
    id: int
    name: str
    description: Optional[str]
    event_type: str
    conditions: Dict[str, Any]
    is_enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    actions: List[ActionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TriggerCreateResponse(BaseModel):
    """
    Schema de respuesta al crear un trigger con nested creation.

    Incluye resumen de todas las entidades creadas.
    """
    success: bool
    trigger: TriggerResponse
    created_actions: List[dict] = []
    summary: dict

    model_config = ConfigDict(from_attributes=True)


class AutomationLogResponse(BaseModel):
    """Schema para la respuesta al obtener un log de automatización."""
    id: int
    trigger_id: int
    event_type: str
    user_id: int
    event_context: Dict[str, Any]
    executed_actions: List[Dict[str, Any]]
    execution_success: bool
    error_message: Optional[str]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EVENT EXECUTION SCHEMAS
# ============================================================================

class EventExecutionRequest(BaseModel):
    """
    Schema para simular la ejecución de un evento.

    Usado en el endpoint de prueba para verificar qué triggers se dispararían.
    """
    event_type: str = Field(..., description="Tipo de evento a simular")
    user_id: int = Field(..., description="ID del usuario que dispara el evento")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contexto del evento")

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Valida que el tipo de evento sea válido."""
        valid_types = [event_type.value for event_type in TriggerEventType]
        if v not in valid_types:
            raise ValueError(f"Tipo de evento '{v}' no válido. Válidos: {valid_types}")
        return v

    model_config = ConfigDict(from_attributes=True)


class EventExecutionResponse(BaseModel):
    """
    Schema de respuesta al ejecutar un evento de prueba.

    Muestra qué triggers se dispararon y qué acciones se ejecutarían.
    """
    success: bool
    event_type: str
    user_id: int
    triggers_executed: List[Dict[str, Any]] = []
    total_actions: int
    summary: dict

    model_config = ConfigDict(from_attributes=True)