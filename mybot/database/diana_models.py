from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    JSON,
    Text,
    ForeignKey,
    Float,
    Index,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base


class EmotionalInteractionType(enum.Enum):
    """Types of emotional interactions tracked in the system."""
    
    GREETING = "greeting"
    HELP_REQUEST = "help_request"
    FEEDBACK = "feedback"
    PERSONAL_SHARE = "personal_share"
    MILESTONE = "milestone"
    CONFLICT = "conflict"
    RESOLUTION = "resolution"
    PRAISE = "praise"
    CRITICISM = "criticism"
    CONFESSION = "confession"
    STORYTELLING = "storytelling"
    ADVICE_SEEKING = "advice_seeking"
    ADVICE_GIVING = "advice_giving"


class EmotionalIntensity(enum.Enum):
    """Intensity levels for emotional interactions."""
    
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class EmotionCategory(enum.Enum):
    """Primary emotion categories for classification."""
    
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    NEUTRAL = "neutral"


class RelationshipStatus(enum.Enum):
    """Possible states of a user-Diana relationship."""
    
    INITIAL = "initial"               # First interactions
    ACQUAINTANCE = "acquaintance"     # Getting to know each other
    FRIENDLY = "friendly"             # Regular positive interactions
    CLOSE = "close"                   # Significant trust established
    INTIMATE = "intimate"             # Deep trust and disclosure
    STRAINED = "strained"             # Relationship under tension
    REPAIRED = "repaired"             # Recovered from strain
    DISTANT = "distant"               # Reduced interaction frequency
    COMPLEX = "complex"               # Mixed positive and negative elements


class DianaEmotionalMemory(Base):
    """
    Stores emotional interaction memories between Diana and users.
    Optimized for fast emotional context retrieval with time-based decay.
    """
    
    __tablename__ = "diana_emotional_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Core memory attributes
    interaction_type = Column(Enum(EmotionalInteractionType), nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    summary = Column(String(255), nullable=False)  # Brief description of interaction
    content = Column(Text, nullable=True)  # Detailed content (may be encrypted)
    
    # Emotional categorization
    primary_emotion = Column(Enum(EmotionCategory), nullable=False)
    secondary_emotion = Column(Enum(EmotionCategory), nullable=True)
    intensity = Column(Enum(EmotionalIntensity), default=EmotionalIntensity.MODERATE)
    
    # Context information
    context_data = Column(JSON, default=dict)  # Additional structured context
    related_achievements = Column(JSON, default=list)  # IDs of related achievements
    related_narrative_keys = Column(JSON, default=list)  # Keys of related narrative fragments
    
    # Memory importance and decay parameters
    importance_score = Column(Float, default=1.0)  # Higher = more important
    decay_rate = Column(Float, default=0.1)  # How quickly memory fades (0.0-1.0)
    last_recalled_at = Column(DateTime, nullable=True)  # When this memory was last accessed
    recall_count = Column(Integer, default=0)  # How often this memory has been recalled
    
    # Memory tags for quick filtering and search
    tags = Column(JSON, default=list)  # Array of string tags
    
    # Privacy and compliance
    is_sensitive = Column(Boolean, default=False)  # Flag for sensitive content
    is_forgotten = Column(Boolean, default=False)  # For GDPR compliance
    
    # Relationships
    user = relationship("User", lazy="joined")
    
    # Memory linking (self-referential)
    parent_memory_id = Column(Integer, ForeignKey("diana_emotional_memories.id"), nullable=True)
    child_memories = relationship(
        "DianaEmotionalMemory",
        backref="parent_memory",
        remote_side=[id],
        lazy="selectin"
    )
    
    # Indices for fast retrieval patterns
    __table_args__ = (
        # Primary access pattern: user_id + recency
        Index("ix_diana_emotional_memories_user_id_timestamp", user_id, timestamp.desc()),
        
        # Emotional search patterns
        Index("ix_diana_emotional_memories_user_id_emotion", user_id, primary_emotion),
        Index("ix_diana_emotional_memories_user_id_intensity", user_id, intensity),
        
        # Important memories retrieval
        Index("ix_diana_emotional_memories_user_id_importance", 
              user_id, importance_score.desc()),
        
        # Recently recalled memories
        Index("ix_diana_emotional_memories_user_id_recalled", 
              user_id, last_recalled_at.desc()),
    )


class DianaRelationshipState(Base):
    """
    Represents the current state of relationship between Diana and a user.
    Aggregates emotional history into actionable relationship metrics.
    """
    
    __tablename__ = "diana_relationship_states"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    
    # Core relationship attributes
    status = Column(Enum(RelationshipStatus), default=RelationshipStatus.INITIAL)
    trust_level = Column(Float, default=0.0)  # 0.0-1.0 scale
    familiarity = Column(Float, default=0.0)  # How well Diana knows the user (0.0-1.0)
    rapport = Column(Float, default=0.0)  # Quality of communication (0.0-1.0)
    
    # Emotional patterns
    dominant_emotion = Column(Enum(EmotionCategory), default=EmotionCategory.NEUTRAL)
    emotional_volatility = Column(Float, default=0.0)  # How much emotions fluctuate
    positive_interactions = Column(Integer, default=0)
    negative_interactions = Column(Integer, default=0)
    
    # Timeline tracking
    relationship_started_at = Column(DateTime, default=func.now())
    last_interaction_at = Column(DateTime, default=func.now())
    longest_absence_days = Column(Integer, default=0)
    
    # Communication patterns
    typical_response_time_seconds = Column(Integer, default=0)
    typical_interaction_length = Column(Integer, default=0)  # Avg message length
    communication_frequency = Column(Float, default=0.0)  # Interactions per day
    
    # Relationship progression
    interaction_count = Column(Integer, default=0)
    milestone_count = Column(Integer, default=0)
    milestone_data = Column(JSON, default=dict)  # Record of relationship milestones
    
    # User preferences and boundaries
    boundary_settings = Column(JSON, default=dict)
    communication_preferences = Column(JSON, default=dict)
    topic_interests = Column(JSON, default=dict)  # Topics with interest scores
    
    # Adaptations
    personality_adaptations = Column(JSON, default=dict)
    linguistic_adaptations = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", lazy="joined")
    
    # Update timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DianaContradiction(Base):
    """
    Records contradictions in Diana's knowledge about users.
    Helps maintain consistent interactions over time.
    """
    
    __tablename__ = "diana_contradictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Contradiction details
    contradiction_type = Column(String(50), nullable=False)
    original_statement = Column(Text, nullable=False)
    contradicting_statement = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    
    # Context of contradiction
    detected_at = Column(DateTime, default=func.now())
    context_data = Column(JSON, default=dict)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Link to related memories
    related_memory_ids = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", lazy="joined")
    
    # Indices
    __table_args__ = (
        Index("ix_diana_contradictions_user_id", user_id),
        Index("ix_diana_contradictions_user_id_resolved", user_id, is_resolved),
    )


class DianaPersonalityAdaptation(Base):
    """
    Tracks how Diana adapts her personality to match user preferences.
    Enables personalization of responses and interaction style.
    """
    
    __tablename__ = "diana_personality_adaptations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Personality dimensions (0.0-1.0 scales)
    warmth = Column(Float, default=0.5)
    formality = Column(Float, default=0.5)
    humor = Column(Float, default=0.5)
    directness = Column(Float, default=0.5)
    assertiveness = Column(Float, default=0.5)
    curiosity = Column(Float, default=0.5)
    emotional_expressiveness = Column(Float, default=0.5)
    
    # Communication style adaptations
    message_length_preference = Column(Integer, default=100)  # Optimal message length
    complexity_level = Column(Float, default=0.5)  # 0.0 (simple) to 1.0 (complex)
    emoji_usage = Column(Float, default=0.5)  # 0.0 (none) to 1.0 (frequent)
    response_delay = Column(Integer, default=0)  # Artificial delay in seconds
    
    # Content adaptations
    topic_preferences = Column(JSON, default=dict)
    taboo_topics = Column(JSON, default=list)
    memory_reference_frequency = Column(Float, default=0.3)  # How often to reference past
    
    # Adaptation metadata
    adaptation_reason = Column(Text, nullable=True)
    last_significant_change = Column(DateTime, nullable=True)
    confidence_score = Column(Float, default=0.5)  # How confident in adaptation
    
    # Relationships
    user = relationship("User", lazy="joined")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", name="uix_diana_personality_adaptation_user"),
        Index("ix_diana_personality_adaptations_user_id", user_id),
    )