"""
Modelos de base de datos para los requisitos de las decisiones narrativas.
"""
from .base import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class DecisionRequirement(Base):
    __tablename__ = 'decision_requirements'

    id = Column(Integer, primary_key=True)
    choice_id = Column(Integer, ForeignKey('narrative_choices.id', ondelete='CASCADE'), unique=True, nullable=False)
    shop_item_id = Column(Integer, ForeignKey('shop_items.id', ondelete='CASCADE'), nullable=False)
    teaser_fragment_key = Column(String(50), ForeignKey('story_fragments.key', ondelete='CASCADE'), nullable=False)

    # Relationships
    choice = relationship("NarrativeChoice", back_populates="requirement")
    shop_item = relationship("ShopItem")
    teaser_fragment = relationship("StoryFragment", foreign_keys=[teaser_fragment_key])
