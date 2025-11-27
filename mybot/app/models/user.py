from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    
    # Relationships
    story_fragments = relationship("StoryFragment", back_populates="author")
    narrative_states = relationship("UserNarrativeState", back_populates="user")
    inventory_items = relationship("InventoryItem", back_populates="user")
    purchases = relationship("UserPurchase", back_populates="user")
    mission_entries = relationship("UserMissionEntry", back_populates="user")
    fragment_views = relationship("UserFragmentView", back_populates="user")
    lore_pieces = relationship("UserLorePiece", back_populates="user")


class UserMissionEntry(Base, TimestampMixin):
    __tablename__ = 'user_mission_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mission_id = Column(Integer, ForeignKey('missions.id'))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)  # Percentage of completion
    
    # Relationships
    user = relationship("User", back_populates="mission_entries")
    mission = relationship("Mission")


class UserFragmentView(Base, TimestampMixin):
    __tablename__ = 'user_fragment_views'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    fragment_id = Column(Integer, ForeignKey('story_fragments.id'))
    view_count = Column(Integer, default=1)
    last_viewed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    fragment = relationship("StoryFragment", back_populates="user_views")