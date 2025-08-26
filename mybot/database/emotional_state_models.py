"""
Modelos de base de datos para el sistema de estados emocionales.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, BigInteger, Index, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .base import Base


class EmotionalStateEnum(enum.Enum):
    """Estados emocionales disponibles."""
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    ENGAGED = "engaged"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    EXCITED = "excited"


class UserEmotionalState(Base):
    """Modelo para almacenar el estado emocional actual de cada usuario."""
    
    __tablename__ = 'user_emotional_states'
    __table_args__ = (
        Index('ix_user_emotional_states_user_id', 'user_id'),
        Index('ix_user_emotional_states_updated_at', 'updated_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)  # Usuario de Telegram
    primary_state = Column(SqlEnum(EmotionalStateEnum), nullable=False, default=EmotionalStateEnum.NEUTRAL)
    intensity = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    secondary_states = Column(JSON, nullable=False, default=dict)  # Dict[EmotionalState, float]
    triggers = Column(JSON, nullable=False, default=list)  # List[str]
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<UserEmotionalState(user_id={self.user_id}, primary_state={self.primary_state.value}, intensity={self.intensity})>"


class EmotionalStateHistory(Base):
    """Modelo para el historial de cambios de estado emocional."""
    
    __tablename__ = 'emotional_state_history'
    __table_args__ = (
        Index('ix_emotional_state_history_user_id_timestamp', 'user_id', 'timestamp'),
        Index('ix_emotional_state_history_state', 'previous_state', 'new_state'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    previous_state = Column(SqlEnum(EmotionalStateEnum), nullable=True)
    new_state = Column(SqlEnum(EmotionalStateEnum), nullable=False)
    previous_intensity = Column(Float, nullable=True)
    new_intensity = Column(Float, nullable=False)
    trigger = Column(String(500), nullable=False)
    interaction_context = Column(JSON, nullable=True)  # Contexto adicional de la interacción
    
    # Timestamp del cambio
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<EmotionalStateHistory(user_id={self.user_id}, {self.previous_state} -> {self.new_state}, trigger={self.trigger})>"