from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Boolean, DateTime, Index, Float, Table
from sqlalchemy.orm import relationship
from uuid import uuid4
from sqlalchemy.sql import func
from .base import Base


class UnifiedMission(Base):
    """Modelo unificado para misiones con integración completa de narrativa y recompensas.
    
    Este modelo representa misiones que pueden requerir diferentes tipos de objetivos:
    - Fragmentos narrativos específicos
    - Pistas de lore específicas
    - Acciones específicas del usuario
    
    Cada misión tiene recompensas configurables y puede desbloquear contenido adicional.
    """
    
    __tablename__ = 'unified_missions'
    __table_args__ = (
        Index('ix_unified_missions_active', 'is_active'),
        Index('ix_unified_missions_type', 'mission_type'),
        Index('ix_unified_missions_order', 'order'),
    )

    # UUID primary key for global uniqueness
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    
    # Información básica
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Tipo de misión
    MISSION_TYPES = (
        ('MAIN', 'Misión principal'),
        ('SIDE', 'Misión secundaria'),
        ('DAILY', 'Misión diaria'),
        ('WEEKLY', 'Misión semanal'),
        ('EVENT', 'Misión de evento'),
    )
    mission_type = Column(String(20), nullable=False)
    
    # Requisitos de la misión
    requirements = Column(JSON, default=dict, nullable=False)
    """
    Estructura del campo requirements:
    {
        "narrative_fragments": ["fragment_id1", "fragment_id2", ...],
        "lore_pieces": ["piece_code1", "piece_code2", ...],
        "actions": [
            {"type": "reaction", "count": 5},
            {"type": "checkin", "count": 3},
            ...
        ],
        "missions": ["mission_id1", "mission_id2", ...] # Submisiones requeridas
    }
    """
    
    # Objetivos de la misión (para mostrar al usuario)
    objectives = Column(JSON, default=list, nullable=False)
    """
    Estructura del campo objectives:
    [
        {"description": "Descubre el fragmento X", "complete_key": "narrative_fragments.fragment_id1"},
        {"description": "Encuentra la pista Y", "complete_key": "lore_pieces.piece_code1"},
        {"description": "Realiza 5 reacciones", "complete_key": "actions.reaction", "count": 5},
        ...
    ]
    """
    
    # Recompensas al completar la misión
    rewards = Column(JSON, default=dict, nullable=False)
    """
    Estructura del campo rewards:
    {
        "points": 100,
        "badges": ["badge_id1", "badge_id2"],
        "lore_pieces": ["piece_code1", "piece_code2"],
        "narrative_fragments": ["fragment_id1", "fragment_id2"]
    }
    """
    
    # Duración y expiración
    duration_days = Column(Integer, default=0)  # 0 = sin límite
    expiration_date = Column(DateTime, nullable=True)
    
    # Estado y orden de la misión
    is_active = Column(Boolean, default=True, nullable=False)
    is_repeatable = Column(Boolean, default=False, nullable=False)
    cooldown_hours = Column(Integer, default=0)  # Para misiones repetibles
    order = Column(Integer, default=0)  # Para ordenar misiones
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UnifiedMission(id={self.id}, title='{self.title}', type='{self.mission_type}')>"
    
    @property
    def is_main(self):
        """Check if mission is a main mission."""
        return self.mission_type == 'MAIN'
    
    @property
    def is_side(self):
        """Check if mission is a side mission."""
        return self.mission_type == 'SIDE'
    
    @property
    def is_daily(self):
        """Check if mission is a daily mission."""
        return self.mission_type == 'DAILY'
    
    @property
    def is_weekly(self):
        """Check if mission is a weekly mission."""
        return self.mission_type == 'WEEKLY'
    
    @property
    def is_event(self):
        """Check if mission is an event mission."""
        return self.mission_type == 'EVENT'


class UserMissionProgress(Base):
    """Progreso del usuario en misiones unificadas.
    
    Este modelo rastrea el progreso del usuario en cada misión,
    incluyendo objetivos completados y estado general.
    """
    
    __tablename__ = 'user_mission_progress'
    __table_args__ = (
        Index('ix_user_mission_progress_user', 'user_id'),
        Index('ix_user_mission_progress_mission', 'mission_id'),
        Index('ix_user_mission_progress_complete', 'is_completed'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    mission_id = Column(String, ForeignKey('unified_missions.id', ondelete='CASCADE'), nullable=False)
    
    # Progreso detallado
    progress_data = Column(JSON, default=dict, nullable=False)
    """
    Estructura del campo progress_data:
    {
        "narrative_fragments": ["fragment_id1", ...],  # Fragmentos completados
        "lore_pieces": ["piece_code1", ...],  # Pistas desbloqueadas
        "actions": {
            "reaction": 3,  # Contador de reacciones
            "checkin": 2,   # Contador de check-ins
            ...
        }
    }
    """
    
    # Estado de la misión
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    times_completed = Column(Integer, default=0, nullable=False)  # Para misiones repetibles
    last_reset_at = Column(DateTime, nullable=True)  # Para misiones diarias/semanales
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    user = relationship("User", backref="mission_progress")
    mission = relationship("UnifiedMission", backref="user_progress")
    
    def __repr__(self):
        return f"<UserMissionProgress(user_id={self.user_id}, mission='{self.mission_id}', completed={self.is_completed})>"
    
    def get_completion_percentage(self):
        """Calcula el porcentaje de progreso en la misión.
        
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        if not self.mission or not self.mission.objectives:
            return 0
        
        total_objectives = len(self.mission.objectives)
        if total_objectives == 0:
            return 100  # No hay objetivos, la misión está completada
        
        completed_objectives = 0
        progress_data = self.progress_data or {}
        
        for objective in self.mission.objectives:
            complete_key = objective.get("complete_key", "")
            if not complete_key:
                continue
                
            # Dividir la clave en tipo y valor
            key_parts = complete_key.split(".", 1)
            if len(key_parts) != 2:
                continue
                
            obj_type, obj_value = key_parts
            
            # Verificar si el objetivo está completado según su tipo
            if obj_type == "narrative_fragments":
                if obj_value in progress_data.get("narrative_fragments", []):
                    completed_objectives += 1
            elif obj_type == "lore_pieces":
                if obj_value in progress_data.get("lore_pieces", []):
                    completed_objectives += 1
            elif obj_type == "actions":
                required_count = objective.get("count", 1)
                current_count = progress_data.get("actions", {}).get(obj_value, 0)
                if current_count >= required_count:
                    completed_objectives += 1
        
        return (completed_objectives / total_objectives) * 100