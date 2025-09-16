from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from .base import Base

class StoryFragment(Base):
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)  # Cambiado de fragment_id a key
    text = Column(Text, nullable=False)  # Cambiado de content a text
    character = Column(String(50), default="Lucien")
    level = Column(Integer, default=1)
    min_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True, index=True)
    reward_besitos = Column(Integer, default=0)
    unlocks_achievement_id = Column(
        String, 
        ForeignKey('achievements.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # Auto-next para fragmentos sin decisiones
    auto_next_fragment_key = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    choices = relationship(
        "NarrativeChoice", 
        back_populates="source_fragment", 
        foreign_keys="NarrativeChoice.source_fragment_id",
        cascade="all, delete-orphan"
    )

    achievement_link = relationship(
        "Achievement",
        foreign_keys=[unlocks_achievement_id],
        back_populates="story_fragments",
        lazy="joined"
    )


class NarrativeChoice(Base):
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_key = Column(String(50), nullable=False)  # Referencia por key, no por ID
    text = Column(String, nullable=False)
    
    # Condiciones opcionales para la decisión
    required_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())

    source_fragment = relationship(
        "StoryFragment", 
        back_populates="choices", 
        foreign_keys=[source_fragment_id]
    )


class UserNarrativeState(Base):
    __tablename__ = 'user_narrative_states'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_key = Column(String(50), nullable=True)  # Referencia por key
    choices_made = Column(JSON, default=list)
    
    # Estadísticas adicionales
    fragments_visited = Column(Integer, default=0)
    total_besitos_earned = Column(Integer, default=0)
    narrative_started_at = Column(DateTime, default=func.now())
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship(
        "User",
        back_populates="narrative_state",
        lazy="joined",
        single_parent=True
    )


class FragmentAnalytics(Base):
    """
    Analytics data for individual story fragments.
    Tracks engagement metrics, choice patterns, and user behavior.
    """
    __tablename__ = 'fragment_analytics'

    id = Column(Integer, primary_key=True)
    fragment_key = Column(String(50), ForeignKey('story_fragments.key'), nullable=False, index=True)

    # Engagement metrics
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    drop_off_count = Column(Integer, default=0)
    average_time_spent = Column(Integer, default=0)  # in seconds

    # Choice analytics
    choice_distribution = Column(JSON, default=dict)  # {"choice_id": count}
    most_popular_choice_id = Column(Integer, nullable=True)

    # Progression analytics
    users_progressed_from = Column(Integer, default=0)
    users_returned_to = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_analyzed_at = Column(DateTime, default=func.now())

    # Relationships
    fragment = relationship("StoryFragment", foreign_keys=[fragment_key])


class UserJourneyAnalytics(Base):
    """
    Analytics for tracking individual user journeys through the narrative.
    Provides insights into user behavior patterns and progression paths.
    """
    __tablename__ = 'user_journey_analytics'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)

    # Journey tracking
    fragments_visited = Column(JSON, default=list)  # [{"fragment_key": "x", "timestamp": "..."}]
    choices_made = Column(JSON, default=list)  # [{"choice_id": 1, "fragment_key": "x", "timestamp": "..."}]
    progression_path = Column(JSON, default=list)  # ["fragment1", "fragment2", ...]

    # Time analytics
    total_time_spent = Column(Integer, default=0)  # in seconds
    session_count = Column(Integer, default=0)
    average_session_duration = Column(Integer, default=0)  # in seconds

    # Behavioral patterns
    backtrack_count = Column(Integer, default=0)  # times user went back
    exploration_score = Column(Integer, default=0)  # 0-100 based on choices diversity
    engagement_level = Column(String(20), default="new")  # new, engaged, highly_engaged, stalled

    # Completion tracking
    fragments_completed = Column(Integer, default=0)
    narrative_completion_percentage = Column(Integer, default=0)
    last_fragment_key = Column(String(50), nullable=True)

    # Emotional progression (for requirement 4.3)
    emotional_states = Column(JSON, default=list)  # [{"fragment": "x", "emotion": "happy", "intensity": 0.8}]
    character_interaction_count = Column(JSON, default=dict)  # {"Lucien": 5, "Diana": 3}

    # Timestamps
    journey_started_at = Column(DateTime, default=func.now())
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
