from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base, TimestampMixin


class StoryFragment(Base, TimestampMixin):
    __tablename__ = 'story_fragments'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    fragment_type = Column(String(50), default='story')  # story, choice_point, ending
    is_published = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    author = relationship("User", back_populates="story_fragments")
    narrative_choices = relationship("NarrativeChoice", back_populates="source_fragment", foreign_keys="NarrativeChoice.source_fragment_id")
    user_views = relationship("UserFragmentView", back_populates="fragment")


class NarrativeChoice(Base, TimestampMixin):
    __tablename__ = 'narrative_choices'
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'))
    target_fragment_id = Column(Integer, ForeignKey('story_fragments.id'))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    source_fragment = relationship("StoryFragment", back_populates="narrative_choices", foreign_keys=[source_fragment_id])
    target_fragment = relationship("StoryFragment", foreign_keys=[target_fragment_id])


class UserNarrativeState(Base, TimestampMixin):
    __tablename__ = 'user_narrative_states'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    current_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    progress_percentage = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="narrative_states")
    current_fragment = relationship("StoryFragment")