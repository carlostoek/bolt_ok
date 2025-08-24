from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Boolean, Float, Index
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship, declared_attr, validates
from sqlalchemy.sql import func
from .base import Base


class StoryFragment(Base):
    """Interactive story fragments with character dialogue and branching choices.
    
    This model represents individual narrative segments that can be linked together
    to create an interactive story experience. Each fragment can have multiple
    choices leading to different story paths.
    """
    __tablename__ = 'story_fragments'
    __table_args__ = (
        Index('idx_story_fragment_key', 'key'),
        Index('idx_story_fragment_role', 'required_role'),
        Index('idx_story_fragment_level', 'level'),
    )

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)
    character = Column(String(100), default="Lucien", nullable=False)
    level = Column(Integer, default=1, nullable=False)
    min_besitos = Column(Integer, default=0, nullable=False)
    required_role = Column(String(20), nullable=True, index=True)
    reward_besitos = Column(Integer, default=0, nullable=False)
    unlocks_achievement_id = Column(
        String(100), 
        ForeignKey('achievements.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # Auto-next for fragments without decisions
    auto_next_fragment_key = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    choices = relationship(
        "NarrativeChoice", 
        back_populates="source_fragment", 
        foreign_keys="NarrativeChoice.source_fragment_id",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    achievement_link = relationship(
        "Achievement",
        foreign_keys=[unlocks_achievement_id],
        back_populates="story_fragments",
        lazy="joined"
    )

    @validates('key')
    def validate_key(self, key, value):
        """Ensure fragment key follows naming convention."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Fragment key cannot be empty")
        if len(value) > 100:
            raise ValueError("Fragment key too long (max 100 characters)")
        return value.strip()

    @validates('required_role')
    def validate_role(self, key, value):
        """Validate role is one of the allowed values."""
        if value is not None:
            allowed_roles = {'admin', 'vip', 'free'}
            if value not in allowed_roles:
                raise ValueError(f"Invalid role: {value}. Must be one of {allowed_roles}")
        return value

    @validates('level')
    def validate_level(self, key, value):
        """Ensure level is positive."""
        if value < 1:
            raise ValueError("Level must be positive")
        return value

    @validates('min_besitos', 'reward_besitos')
    def validate_besitos(self, key, value):
        """Ensure besitos values are non-negative."""
        if value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


class NarrativeChoice(Base):
    """Player choices within story fragments that lead to different narrative paths.
    
    Each choice represents a decision point where players can influence the story
    direction. Choices can have requirements (points, role) that gate access.
    """
    __tablename__ = 'narrative_choices'
    __table_args__ = (
        Index('idx_narrative_choice_source', 'source_fragment_id'),
        Index('idx_narrative_choice_dest', 'destination_fragment_key'),
    )

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(
        Integer, 
        ForeignKey('story_fragments.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    destination_fragment_key = Column(String(100), nullable=False, index=True)
    text = Column(Text, nullable=False)
    
    # Optional conditions for the choice
    required_besitos = Column(Integer, default=0, nullable=False)
    required_role = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    source_fragment = relationship(
        "StoryFragment", 
        back_populates="choices", 
        foreign_keys=[source_fragment_id]
    )

    @validates('text')
    def validate_text(self, key, value):
        """Ensure choice text is not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Choice text cannot be empty")
        return value.strip()

    @validates('destination_fragment_key')
    def validate_destination(self, key, value):
        """Ensure destination key is not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Destination fragment key cannot be empty")
        return value.strip()

    @validates('required_role')
    def validate_role(self, key, value):
        """Validate role is one of the allowed values."""
        if value is not None:
            allowed_roles = {'admin', 'vip', 'free'}
            if value not in allowed_roles:
                raise ValueError(f"Invalid role: {value}. Must be one of {allowed_roles}")
        return value

    @validates('required_besitos')
    def validate_required_besitos(self, key, value):
        """Ensure required besitos is non-negative."""
        if value < 0:
            raise ValueError("Required besitos must be non-negative")
        return value


class UserNarrativeState(Base):
    """Tracks individual user progress through the interactive narrative system.
    
    Maintains user's current position, choices made, and progression statistics.
    Prevents race conditions during reward processing.
    """
    __tablename__ = 'user_narrative_states'
    __table_args__ = (
        Index('idx_user_narrative_current', 'current_fragment_key'),
        Index('idx_user_narrative_activity', 'last_activity_at'),
    )

    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        primary_key=True
    )
    current_fragment_key = Column(String(100), nullable=True, index=True)
    choices_made = Column(JSON, default=list, nullable=False)
    
    # Statistics
    fragments_visited = Column(Integer, default=0, nullable=False)
    fragments_completed = Column(Integer, default=0, nullable=False)
    narrative_started_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    processing_reward = Column(Boolean, default=False, nullable=False)  # Race condition protection

    user = relationship(
        "User", 
        back_populates="narrative_state",
        lazy="joined",
        single_parent=True
    )

    @validates('choices_made')
    def validate_choices(self, key, value):
        """Ensure choices_made is always a list."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("choices_made must be a list")
        return value

    @validates('fragments_visited', 'fragments_completed')
    def validate_positive_integers(self, key, value):
        """Ensure integer fields are non-negative."""
        if value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


# Enhanced narrative system for advanced features and integration testing

class NarrativeFragment(Base):
    """Enhanced narrative fragments with engagement and milestone tracking.
    
    This model extends the basic StoryFragment with additional features for
    engagement tracking, milestones, and advanced reward mechanisms.
    Used primarily for integration testing and advanced narrative features.
    """
    
    __tablename__ = 'narrative_fragments'
    __table_args__ = (
        Index('idx_narrative_fragment_key', 'key'),
        Index('idx_narrative_fragment_vip', 'vip_only'),
        Index('idx_narrative_fragment_milestone', 'is_milestone'),
    )
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    completion_points = Column(Integer, default=0, nullable=False)
    is_completion_point = Column(Boolean, default=False, nullable=False)
    requires_engagement = Column(Boolean, default=False, nullable=False)
    engagement_threshold = Column(Integer, default=0, nullable=False)
    vip_only = Column(Boolean, default=False, nullable=False)
    is_milestone = Column(Boolean, default=False, nullable=False)
    base_points = Column(Integer, default=0, nullable=False)
    karma_multiplier = Column(Boolean, default=False, nullable=False)
    one_time_reward = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @validates('key')
    def validate_key(self, key, value):
        """Ensure fragment key follows naming convention."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Fragment key cannot be empty")
        if len(value) > 100:
            raise ValueError("Fragment key too long (max 100 characters)")
        return value.strip()

    @validates('title')
    def validate_title(self, key, value):
        """Ensure title is not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Fragment title cannot be empty")
        return value.strip()

    @validates('content')
    def validate_content(self, key, value):
        """Ensure content is not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Fragment content cannot be empty")
        return value.strip()

    @validates('engagement_threshold', 'completion_points', 'base_points')
    def validate_non_negative_integers(self, key, value):
        """Ensure integer fields are non-negative."""
        if value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


class NarrativeDecision(Base):
    """Enhanced narrative decisions with engagement and karma effects.
    
    This model extends basic choices with karma modifiers, engagement effects,
    and future reward implications. Used for complex narrative interactions.
    """
    
    __tablename__ = 'narrative_decisions'
    __table_args__ = (
        Index('idx_narrative_decision_fragment', 'fragment_key'),
        Index('idx_narrative_decision_next', 'next_fragment_key'),
    )
    
    id = Column(Integer, primary_key=True)
    fragment_key = Column(String(100), nullable=False, index=True)
    text = Column(Text, nullable=False)
    next_fragment_key = Column(String(100), nullable=False, index=True)
    points_reward = Column(Integer, default=0, nullable=False)
    karma_modifier = Column(Integer, default=0, nullable=False)
    affects_engagement = Column(Boolean, default=False, nullable=False)
    engagement_multiplier = Column(Float, default=1.0, nullable=False)
    affects_future_rewards = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)

    @validates('text')
    def validate_text(self, key, value):
        """Ensure decision text is not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Decision text cannot be empty")
        return value.strip()

    @validates('fragment_key', 'next_fragment_key')
    def validate_fragment_keys(self, key, value):
        """Ensure fragment keys are not empty."""
        if not value or len(value.strip()) == 0:
            raise ValueError(f"{key} cannot be empty")
        return value.strip()

    @validates('engagement_multiplier')
    def validate_engagement_multiplier(self, key, value):
        """Ensure engagement multiplier is positive."""
        if value <= 0:
            raise ValueError("Engagement multiplier must be positive")
        return value

    @validates('points_reward')
    def validate_points_reward(self, key, value):
        """Ensure points reward is non-negative."""
        if value < 0:
            raise ValueError("Points reward must be non-negative")
        return value


class UserDecisionLog(Base):
    """Log of user decisions in enhanced narrative system.
    
    Tracks all user decisions for analytics, progression tracking,
    and preventing duplicate rewards.
    """
    
    __tablename__ = 'user_decision_log'
    __table_args__ = (
        Index('idx_user_decision_user', 'user_id'),
        Index('idx_user_decision_time', 'made_at'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    decision_id = Column(
        Integer, 
        ForeignKey('narrative_decisions.id', ondelete='CASCADE'), 
        nullable=False
    )
    made_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", lazy="selectin")
    decision = relationship("NarrativeDecision", lazy="selectin")