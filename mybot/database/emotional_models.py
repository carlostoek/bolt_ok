"""
Emotional Analysis Database Models

This module defines the database schema for the emotional analysis system.
It tracks user interaction patterns, response timing, behavioral consistency,
and emotional evolution throughout the narrative experience.
"""

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, BigInteger, 
    JSON, Float, Boolean, DateTime, Enum, Index
)
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from .base import Base
import enum


class EmotionalIntensity(enum.Enum):
    """Enum for emotional intensity levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ResponseType(enum.Enum):
    """Enum for response types"""
    IMPULSO_AUTENTICO = "impulso_autentico"  # Quick, authentic response <3s
    PAUSA_REFLEXIVA = "pausa_reflexiva"      # Thoughtful response 3-15s
    CONTEMPLACION = "contemplacion"          # Deep consideration >15s
    ABANDONO = "abandono"                    # Session abandonment


class VulnerabilityLevel(enum.Enum):
    """Enum for vulnerability authenticity levels"""
    SURFACE = "surface"           # Surface-level engagement
    TENTATIVE = "tentative"       # Cautious exploration
    GENUINE = "genuine"           # Authentic vulnerability
    DEEP_INTIMATE = "deep_intimate"  # Profound intimacy


class UserEmotionalProfile(Base):
    """
    Core emotional profile tracking for each user.
    Stores aggregated emotional patterns and behavioral tendencies.
    """
    __tablename__ = 'user_emotional_profiles'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    
    # Response Pattern Analysis
    impulso_autentico_percentage = Column(Float, default=0.0)  # % of quick responses
    pausa_reflexiva_percentage = Column(Float, default=0.0)    # % of thoughtful responses
    contemplacion_percentage = Column(Float, default=0.0)      # % of deep responses
    abandono_percentage = Column(Float, default=0.0)          # % of abandonments
    
    # Behavioral Consistency Metrics
    consistency_score = Column(Float, default=0.0)            # 0-1 behavioral consistency
    vulnerability_progression = Column(Float, default=0.0)     # 0-1 openness progression
    authenticity_score = Column(Float, default=0.0)           # 0-1 authenticity measure
    
    # Emotional Evolution Tracking
    dominant_emotional_pattern = Column(Enum(ResponseType), default=ResponseType.PAUSA_REFLEXIVA)
    current_vulnerability_level = Column(Enum(VulnerabilityLevel), default=VulnerabilityLevel.SURFACE)
    emotional_growth_trajectory = Column(Float, default=0.0)   # Rate of emotional development
    
    # Session Statistics
    total_interactions = Column(Integer, default=0)
    total_session_time = Column(Float, default=0.0)           # Total time in seconds
    average_response_time = Column(Float, default=0.0)        # Average response time
    peak_engagement_time = Column(DateTime, nullable=True)     # Time of highest engagement
    
    # Timestamps
    profile_created_at = Column(DateTime, default=func.now())
    last_analysis_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to user
    user = relationship(
        "User",
        back_populates="emotional_profile",
        lazy="joined",
        single_parent=True
    )


class EmotionalInteraction(Base):
    """
    Individual emotional interaction tracking.
    Records each user interaction with detailed emotional metadata.
    """
    __tablename__ = 'emotional_interactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    
    # Context Information
    fragment_key = Column(String(50), nullable=True)           # Current narrative fragment
    interaction_type = Column(String(30), nullable=False)      # 'decision', 'reaction', 'message'
    interaction_content = Column(Text, nullable=True)          # User's response/choice
    
    # Timing Analysis
    response_time = Column(Float, nullable=False)              # Time to respond in seconds
    response_type = Column(Enum(ResponseType), nullable=False) # Classified response type
    session_duration = Column(Float, nullable=True)           # Total session duration
    time_since_last_interaction = Column(Float, nullable=True) # Gap between interactions
    
    # Emotional Metrics
    emotional_intensity = Column(Enum(EmotionalIntensity), nullable=True)
    vulnerability_exhibited = Column(Enum(VulnerabilityLevel), nullable=True)
    authenticity_indicators = Column(JSON, nullable=True)      # Specific authenticity markers
    behavioral_flags = Column(JSON, nullable=True)             # Pattern recognition flags
    
    # Advanced Analysis
    sentiment_score = Column(Float, nullable=True)             # -1 to 1 sentiment
    engagement_depth = Column(Float, nullable=True)            # 0-1 engagement measure
    narrative_resonance = Column(Float, nullable=True)         # Story connection strength
    decision_confidence = Column(Float, nullable=True)         # Certainty in choices
    
    # Context Metadata
    device_context = Column(JSON, nullable=True)               # Device/environment info
    interaction_context = Column(JSON, nullable=True)          # Additional context data
    
    # Timestamps
    interaction_timestamp = Column(DateTime, default=func.now(), index=True)
    analysis_processed_at = Column(DateTime, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_user_timestamp', 'user_id', 'interaction_timestamp'),
        Index('idx_response_analysis', 'response_type', 'emotional_intensity'),
    )


class EmotionalEvolution(Base):
    """
    Tracks emotional evolution over time periods.
    Captures progression snapshots and milestone achievements.
    """
    __tablename__ = 'emotional_evolution'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    
    # Evolution Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)           # 'daily', 'weekly', 'milestone'
    
    # Evolution Metrics
    vulnerability_growth = Column(Float, default=0.0)          # Change in vulnerability level
    authenticity_improvement = Column(Float, default=0.0)      # Authenticity development
    consistency_trend = Column(Float, default=0.0)             # Behavioral consistency trend
    engagement_evolution = Column(Float, default=0.0)          # Engagement depth change
    
    # Pattern Changes
    response_pattern_shift = Column(JSON, nullable=True)       # Changes in response patterns
    emotional_milestones = Column(JSON, nullable=True)         # Achieved milestones
    breakthrough_indicators = Column(JSON, nullable=True)      # Emotional breakthroughs
    regression_flags = Column(JSON, nullable=True)             # Warning signs
    
    # Predictive Indicators
    future_engagement_prediction = Column(Float, nullable=True) # Predicted engagement
    vulnerability_trajectory = Column(Float, nullable=True)     # Projected vulnerability
    risk_assessment = Column(Float, nullable=True)             # Risk of disengagement
    
    # Timestamps
    evolution_calculated_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_user_period', 'user_id', 'period_type', 'period_start'),
    )


class EmotionalTrigger(Base):
    """
    Identifies and tracks emotional triggers and catalysts.
    Maps specific content/situations to emotional responses.
    """
    __tablename__ = 'emotional_triggers'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    
    # Trigger Identification
    trigger_type = Column(String(50), nullable=False)          # 'narrative_theme', 'choice_type', 'character'
    trigger_content = Column(Text, nullable=False)             # Specific trigger content
    trigger_context = Column(JSON, nullable=True)              # Additional context
    
    # Response Pattern
    typical_response_type = Column(Enum(ResponseType), nullable=False)
    emotional_intensity_triggered = Column(Enum(EmotionalIntensity), nullable=False)
    vulnerability_impact = Column(Float, nullable=False)       # -1 to 1 impact on vulnerability
    
    # Trigger Statistics
    activation_count = Column(Integer, default=1)              # How often triggered
    last_activation = Column(DateTime, default=func.now())     # Most recent activation
    average_response_time = Column(Float, nullable=True)       # Average response to this trigger
    consistency_score = Column(Float, default=1.0)             # Consistency of response
    
    # Learning and Adaptation
    trigger_strength = Column(Float, default=1.0)              # How strong the trigger is
    adaptation_rate = Column(Float, default=0.0)               # How user adapts to trigger
    desensitization_level = Column(Float, default=0.0)         # Reduced response over time
    
    # Discovery and Update
    first_detected = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    confidence_score = Column(Float, default=1.0)              # Confidence in trigger identification
    
    # Indexes
    __table_args__ = (
        Index('idx_user_trigger_type', 'user_id', 'trigger_type'),
        Index('idx_trigger_strength', 'trigger_strength', 'activation_count'),
    )


class EmotionalInsight(Base):
    """
    Generated insights and recommendations based on emotional analysis.
    Provides actionable intelligence for narrative adaptation.
    """
    __tablename__ = 'emotional_insights'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    
    # Insight Classification
    insight_type = Column(String(50), nullable=False)          # 'pattern', 'opportunity', 'risk', 'milestone'
    insight_category = Column(String(30), nullable=False)      # 'vulnerability', 'engagement', 'authenticity'
    priority_level = Column(Integer, default=5)                # 1-10 priority
    
    # Insight Content
    insight_title = Column(String(200), nullable=False)
    insight_description = Column(Text, nullable=False)
    supporting_data = Column(JSON, nullable=True)              # Data supporting the insight
    confidence_score = Column(Float, nullable=False)           # 0-1 confidence
    
    # Actionable Recommendations
    recommended_actions = Column(JSON, nullable=True)          # Suggested actions
    narrative_adaptations = Column(JSON, nullable=True)        # Story modifications
    engagement_strategies = Column(JSON, nullable=True)        # Engagement approaches
    
    # Implementation Tracking
    is_implemented = Column(Boolean, default=False)
    implementation_date = Column(DateTime, nullable=True)
    effectiveness_score = Column(Float, nullable=True)         # Post-implementation effectiveness
    
    # Lifecycle
    insight_generated_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)               # When insight becomes stale
    last_reviewed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_priority', 'user_id', 'priority_level'),
        Index('idx_insight_type_category', 'insight_type', 'insight_category'),
    )