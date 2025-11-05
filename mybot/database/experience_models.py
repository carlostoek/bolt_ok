"""
Modelos de base de datos para el sistema de experiencias unificadas.
Permite configurar experiencias completas que integran narrativa, gamificación y tienda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class UnifiedExperience(Base):
    __tablename__ = "unified_experiences"
    
    id = Column(String(50), primary_key=True)  # ej: "diana_first_encounter"
    name = Column(String(100), nullable=False)  # "Primer Encuentro con Diana"
    description = Column(Text)
    
    # Configuración centralizada
    requirements = Column(JSON, default=dict)  # Requisitos compuestos para acceder
    triggers = Column(JSON, default=dict)      # Qué desencadena la experiencia
    rewards = Column(JSON, default=dict)       # Recompensas automáticas
    narrative_flow = Column(JSON, default=dict) # Flujo narrativo asociado
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones con elementos creados automáticamente
    created_fragments = relationship(
        "StoryFragment", 
        backref="source_experience",
        foreign_keys="StoryFragment.experience_id",
        lazy="selectin"
    )
    
    created_shop_items = relationship(
        "ShopItem",
        backref="source_experience", 
        foreign_keys="ShopItem.experience_id",
        lazy="selectin"
    )
    
    created_missions = relationship(
        "Mission",
        backref="source_experience",
        foreign_keys="Mission.experience_id", 
        lazy="selectin"
    )


class ExperienceDependency(Base):
    __tablename__ = "experience_dependencies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(String(50), ForeignKey("unified_experiences.id", ondelete="CASCADE"))
    
    # Tipo de dependencia
    dependency_type = Column(String(50), nullable=False)  # "fragment", "shop_item", "mission", "achievement"
    dependency_id = Column(String(100), nullable=False)   # ID del elemento dependiente
    dependency_name = Column(String(100), nullable=False) # Nombre para mostrar
    
    # Relación
    experience = relationship("UnifiedExperience", backref="dependencies")