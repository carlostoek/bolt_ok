"""
Modelos ORM para el sistema de automatización dirigido por eventos.

Reemplaza la lógica hardcodeada con un motor configurable dinámico.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.database.session import Base


class TriggerEventType(enum.Enum):
    """Tipos de eventos que pueden disparar automatizaciones."""
    FRAGMENT_VIEWED = "fragment_viewed"
    PURCHASE_COMPLETED = "purchase_completed"
    USER_REGISTERED = "user_registered"
    VIP_SUBSCRIPTION_STARTED = "vip_subscription_started"
    VIP_SUBSCRIPTION_ENDED = "vip_subscription_ended"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    DAILY_LOGIN = "daily_login"
    STREAK_BROKEN = "streak_broken"
    CUSTOM_EVENT = "custom_event"


class ActionType(enum.Enum):
    """Tipos de acciones que se pueden ejecutar."""
    GIVE_PRODUCT = "give_product"
    GRANT_VIP = "grant_vip"
    SEND_MESSAGE = "send_message"
    ADD_POINTS = "add_points"
    UNLOCK_FRAGMENT = "unlock_fragment"
    GRANT_BADGE = "grant_badge"
    TRIGGER_NARRATIVE = "trigger_narrative"
    EXECUTE_WEBHOOK = "execute_webhook"


class AutomationTrigger(Base):
    """
    Define CUÁNDO se dispara una automatización.
    
    Contiene las condiciones y el tipo de evento que activa las acciones.
    """
    __tablename__ = 'automation_triggers'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información básica
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Configuración del evento
    event_type = Column(String(50), nullable=False)  # Usamos String para compatibilidad con Enum
    
    # Condiciones específicas del evento (JSON flexible)
    conditions = Column(JSON, nullable=True, default=dict)
    
    # Control de estado
    is_enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)  # Prioridad de ejecución
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    actions = relationship(
        "TriggerAction",
        back_populates="trigger",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<AutomationTrigger(id={self.id}, name='{self.name}', event_type='{self.event_type}', enabled={self.is_enabled})>"


class TriggerAction(Base):
    """
    Define QUÉ se ejecuta cuando se dispara un trigger.
    
    Relación 1:N con AutomationTrigger.
    """
    __tablename__ = 'trigger_actions'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    trigger_id = Column(Integer, ForeignKey('automation_triggers.id', ondelete='CASCADE'), nullable=False)

    # Configuración de la acción
    action_type = Column(String(50), nullable=False)  # Usamos String para compatibilidad con Enum
    
    # Parámetros específicos de la acción (JSON flexible)
    parameters = Column(JSON, nullable=True, default=dict)
    
    # Orden de ejecución
    execution_order = Column(Integer, nullable=False, default=1)
    
    # Control de estado
    is_enabled = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    trigger = relationship("AutomationTrigger", back_populates="actions")

    def __repr__(self):
        return f"<TriggerAction(id={self.id}, trigger_id={self.trigger_id}, action_type='{self.action_type}', order={self.execution_order})>"


class AutomationLog(Base):
    """
    Log de ejecuciones de automatizaciones para auditoría y debugging.
    """
    __tablename__ = 'automation_logs'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información del evento
    trigger_id = Column(Integer, ForeignKey('automation_triggers.id'), nullable=False)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=False)
    
    # Contexto del evento
    event_context = Column(JSON, nullable=True, default=dict)
    
    # Resultado de la ejecución
    executed_actions = Column(JSON, nullable=True, default=list)
    execution_success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        status = "SUCCESS" if self.execution_success else "FAILED"
        return f"<AutomationLog(id={self.id}, trigger_id={self.trigger_id}, user_id={self.user_id}, status={status})>"