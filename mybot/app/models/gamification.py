from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin


class Mission(Base, TimestampMixin):
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    reward_points = Column(Integer, default=0)
    reward_currency = Column(Numeric(10, 2), default=0)
    completion_conditions = Column(Text)  # JSON or description of conditions
    is_active = Column(Boolean, default=True)
    is_repeatable = Column(Boolean, default=False)
    
    # Relationships
    user_entries = relationship("UserMissionEntry", back_populates="mission")
    rewards = relationship("Reward", back_populates="mission")


class Reward(Base, TimestampMixin):
    __tablename__ = 'rewards'
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey('missions.id'))
    reward_type = Column(String(50), nullable=False)  # points, currency, item
    reward_value = Column(Integer)  # Could be points, currency amount, or item ID
    reward_item_id = Column(Integer)  # Reference to shop_item if reward_type is 'item'
    
    # Relationships
    mission = relationship("Mission", back_populates="rewards")


class Achievement(Base, TimestampMixin):
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    points = Column(Integer, default=0)
    badge_id = Column(Integer, ForeignKey('badges.id'))
    trigger_condition = Column(Text)  # Condition to unlock achievement
    
    # Relationships
    badge = relationship("Badge")


class Badge(Base, TimestampMixin):
    __tablename__ = 'badges'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_path = Column(String(500))  # Path to badge image
    rarity = Column(String(50), default='common')  # common, rare, epic, legendary