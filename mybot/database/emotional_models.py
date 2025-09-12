"""
Emotional Analysis Database Models

Models to track user emotional patterns, vulnerability progression,
and interaction analytics for personalized narrative experiences.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class ResponseType(enum.Enum):
    """User response timing classification"""
    IMPULSO_AUTENTICO = "impulso_autentico"    # < 3 seconds
    PAUSA_REFLEXIVA = "pausa_reflexiva"        # 3-15 seconds  
    CONTEMPLACION = "contemplacion"            # 15-60 seconds
    ABANDONO = "abandono"                      # > 60 seconds


class VulnerabilityLevel(enum.Enum):
    """User vulnerability exhibition levels"""
    SURFACE = "surface"                        # Basic engagement
    TENTATIVE = "tentative"                   # Some emotional opening
    GENUINE = "genuine"                       # Authentic vulnerability
    DEEP = "deep"                            # Profound emotional engagement
    INTIMATE = "intimate"                     # Complete emotional openness


class EmotionalIntensity(enum.Enum):
    """Emotional intensity levels in interactions"""
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"


class UserEmotionalProfile(Base):
    """
    User's overall emotional interaction profile
    Tracks patterns, preferences, and psychological tendencies
    """
    __tablename__ = 'user_emotional_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Response Pattern Percentages (must sum to 100.0)
    impulso_autentico_percentage = Column(Float, default=25.0)
    pausa_reflexiva_percentage = Column(Float, default=50.0) 
    contemplacion_percentage = Column(Float, default=20.0)
    abandono_percentage = Column(Float, default=5.0)
    
    # Behavioral Metrics
    consistency_score = Column(Float, default=0.5)           # 0.0 - 1.0
    vulnerability_progression = Column(Float, default=0.0)    # 0.0 - 1.0
    authenticity_score = Column(Float, default=0.5)         # 0.0 - 1.0
    
    # Current State
    dominant_emotional_pattern = Column(Enum(ResponseType), default=ResponseType.PAUSA_REFLEXIVA)
    current_vulnerability_level = Column(Enum(VulnerabilityLevel), default=VulnerabilityLevel.SURFACE)
    emotional_growth_trajectory = Column(Float, default=0.0)  # -1.0 to 1.0
    
    # Statistical Data
    total_interactions = Column(Integer, default=0)
    average_response_time = Column(Float, default=8.0)       # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = relationship("EmotionalInteraction", back_populates="profile")


class EmotionalInteraction(Base):
    """
    Individual emotional interaction record
    Captures specific moments of user emotional engagement
    """
    __tablename__ = 'emotional_interactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_emotional_profiles.user_id'), nullable=False)
    
    # Interaction Context
    interaction_type = Column(String(50), nullable=False)     # decision, reaction, participation
    fragment_key = Column(String(100))                        # narrative fragment if applicable
    context_data = Column(Text)                               # JSON string for additional context
    
    # Timing Analysis
    response_time = Column(Float, nullable=False)             # seconds
    response_type = Column(Enum(ResponseType), nullable=False)
    
    # Emotional Metrics
    emotional_intensity = Column(Enum(EmotionalIntensity), default=EmotionalIntensity.MODERATE)
    vulnerability_exhibited = Column(Enum(VulnerabilityLevel), default=VulnerabilityLevel.SURFACE)
    engagement_depth = Column(Float, default=0.5)             # 0.0 - 1.0
    authenticity_score = Column(Float, default=0.5)           # 0.0 - 1.0
    
    # Content Analysis (if applicable)
    content_length = Column(Integer, default=0)
    emotional_keywords_detected = Column(Text)                # JSON array of detected keywords
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserEmotionalProfile", back_populates="interactions")


class InteractionType(enum.Enum):
    """Types of user interactions tracked"""
    REACTION = "reaction"
    DECISION = "decision"
    PARTICIPATION = "participation"
    MESSAGE = "message"
    ENGAGEMENT = "engagement"


class ConversationMemory(Base):
    """
    Stores conversation context for emotional continuity
    """
    __tablename__ = 'conversation_memories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    conversation_id = Column(String(100), nullable=False)
    
    # Memory Content
    context_summary = Column(Text)                            # Summary of conversation context
    emotional_state_snapshot = Column(Text)                   # JSON of emotional state at time
    key_moments = Column(Text)                                # JSON array of significant moments
    
    # Metadata
    interaction_count = Column(Integer, default=0)
    last_interaction_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmotionalTrigger(Base):
    """
    Tracks emotional triggers and responses for users
    """
    __tablename__ = 'emotional_triggers'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Trigger Information
    trigger_type = Column(String(50), nullable=False)         # curiosity, romance, mystery, etc.
    trigger_content = Column(String(200))                     # Content that triggered response
    response_intensity = Column(Enum(EmotionalIntensity), default=EmotionalIntensity.MODERATE)
    
    # Context
    fragment_key = Column(String(100))                        # Where trigger occurred
    response_time = Column(Float)                             # Response time in seconds
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)


class EmotionalAnalysisSession(Base):
    """
    Tracks emotional analysis sessions for performance monitoring
    """
    __tablename__ = 'emotional_analysis_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Session Metrics
    analysis_type = Column(String(50), nullable=False)        # timing, vulnerability, patterns
    processing_time_ms = Column(Float)                        # Analysis performance
    success = Column(Integer, default=1)                      # 1 for success, 0 for failure
    
    # Results
    confidence_score = Column(Float, default=0.5)             # 0.0 - 1.0
    insights_generated = Column(Integer, default=0)           # Number of insights
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class ArchetypeClassification(Base):
    """
    User personality archetype classification
    """
    __tablename__ = 'archetype_classifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Primary Archetype
    primary_archetype = Column(String(50))                    # explorer, romantic, seeker, etc.
    archetype_confidence = Column(Float, default=0.5)         # 0.0 - 1.0
    
    # Secondary Traits
    secondary_traits = Column(Text)                           # JSON array of secondary traits
    trait_strengths = Column(Text)                            # JSON mapping trait -> strength
    
    # Evolution Tracking
    archetype_stability = Column(Float, default=0.5)          # How stable classification is
    last_classification_change = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmotionalState(Base):
    """
    Current emotional state snapshots
    """
    __tablename__ = 'emotional_states'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # State Components
    current_mood = Column(String(50))                         # excited, contemplative, vulnerable, etc.
    engagement_level = Column(Float, default=0.5)             # 0.0 - 1.0
    vulnerability_openness = Column(Float, default=0.5)       # 0.0 - 1.0
    emotional_stability = Column(Float, default=0.5)          # 0.0 - 1.0
    
    # Context
    triggered_by = Column(String(100))                        # What triggered this state
    expected_duration_minutes = Column(Integer)               # How long state might last
    
    # Timestamps
    state_started_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)