from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from .base import Base


class NarrativeFragment(Base):
    """Modelo unificado para fragmentos narrativos con soporte para historia, decisiones e información.
    
    Este modelo representa fragmentos narrativos que pueden ser de diferentes tipos:
    - STORY: Fragmentos de historia principal
    - DECISION: Puntos de decisión con opciones
    - INFO: Fragmentos informativos
    
    Cada fragmento puede tener requerimientos (pistas necesarias) y triggers (recompensas/pistas).
    """
    
    __tablename__ = 'narrative_fragments_unified'
    __table_args__ = (
        Index('ix_narrative_fragments_unified_type_active', 'fragment_type', 'is_active'),
        Index('ix_narrative_fragments_unified_active', 'is_active'),
    )

    # UUID primary key for global uniqueness
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Fragment type classification
    FRAGMENT_TYPES = (
        ('STORY', 'Fragmento de historia'),
        ('DECISION', 'Punto de decisión'),
        ('INFO', 'Fragmento informativo'),
    )
    fragment_type = Column(String(20), nullable=False)
    
    # Choices for decision points (JSON field)
    choices = Column(JSON, default=list, nullable=False)
    
    # Triggers for rewards and other effects (JSON field)
    triggers = Column(JSON, default=dict, nullable=False)
    
    # Required clues/pistas for unlocking this fragment
    required_clues = Column(JSON, default=list, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Active status
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<NarrativeFragment(id={self.id}, title='{self.title}', type='{self.fragment_type}')>"

    @property
    def is_story(self):
        """Check if fragment is a story fragment."""
        return self.fragment_type == 'STORY'

    @property
    def is_decision(self):
        """Check if fragment is a decision point."""
        return self.fragment_type == 'DECISION'

    @property
    def is_info(self):
        """Check if fragment is an info fragment."""
        return self.fragment_type == 'INFO'