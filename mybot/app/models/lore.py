from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin


class LorePiece(Base, TimestampMixin):
    __tablename__ = 'lore_pieces'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))  # world, character, event, etc.
    is_published = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    author = relationship("User")
    user_lore_pieces = relationship("UserLorePiece", back_populates="lore_piece")


class UserLorePiece(Base, TimestampMixin):
    __tablename__ = 'user_lore_pieces'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    lore_piece_id = Column(Integer, ForeignKey('lore_pieces.id'))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="lore_pieces")
    lore_piece = relationship("LorePiece", back_populates="user_lore_pieces")