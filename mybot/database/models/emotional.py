"""
Database models for the emotional system.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Float
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

class CharacterEmotionalState(Base):
    """
    Model for storing character emotional states toward users.
    """
    __tablename__ = 'character_emotional_states'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    character_name = Column(String(50), nullable=False, index=True)
    
    # Emotional state values
    joy = Column(Float, default=50.0)
    trust = Column(Float, default=30.0)
    fear = Column(Float, default=20.0)
    sadness = Column(Float, default=15.0)
    anger = Column(Float, default=10.0)
    surprise = Column(Float, default=25.0)
    anticipation = Column(Float, default=40.0)
    disgust = Column(Float, default=5.0)
    
    # Additional metadata
    dominant_emotion = Column(String(20), default="neutral")
    relationship_level = Column(Integer, default=1)  # 1-5 scale
    relationship_status = Column(String(20), default="neutral")
    
    # Historical data reference
    history_entries = Column(JSON, default=list)  # List of historical data points
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to user
    user = relationship(
        "User",
        back_populates="emotional_states",
        lazy="joined"
    )
    
    def __repr__(self):
        return f"<CharacterEmotionalState user_id={self.user_id} character={self.character_name} dominant={self.dominant_emotion}>"


class EmotionalHistoryEntry(Base):
    """
    Model for storing historical emotional state entries.
    Allows tracking emotional changes over time.
    """
    __tablename__ = 'emotional_history_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    character_name = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # The JSON representation of the emotional state at this point
    emotional_state = Column(JSON, nullable=False)
    
    # Context of this emotional state change
    context_type = Column(String(50), nullable=False, default="interaction")  # interaction, decision, narrative, etc.
    context_description = Column(Text, nullable=True)
    context_reference_id = Column(String(50), nullable=True)  # e.g., choice_id, fragment_key
    
    # Relationship to user
    user = relationship(
        "User",
        back_populates="emotional_history",
        lazy="joined"
    )
    
    def __repr__(self):
        return f"<EmotionalHistoryEntry user_id={self.user_id} character={self.character_name} timestamp={self.timestamp}>"


class EmotionalResponseTemplate(Base):
    """
    Model for storing emotional response templates.
    Used for generating character responses based on emotional states.
    """
    __tablename__ = 'emotional_response_templates'
    
    id = Column(Integer, primary_key=True)
    character_name = Column(String(50), nullable=False, index=True)
    emotion = Column(String(20), nullable=False, index=True)  # joy, trust, fear, etc.
    intensity_level = Column(String(10), nullable=False)  # low, medium, high
    
    # Template components
    text_prefixes = Column(JSON, default=list)  # List of possible text prefixes
    text_suffixes = Column(JSON, default=list)  # List of possible text suffixes
    style_suggestions = Column(JSON, default=list)  # List of style modifiers
    emoji_suggestions = Column(JSON, default=list)  # List of suggested emojis
    
    # Sample phrases for this emotional state
    sample_phrases = Column(JSON, default=list)  # List of example phrases
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<EmotionalResponseTemplate character={self.character_name} emotion={self.emotion} level={self.intensity_level}>"