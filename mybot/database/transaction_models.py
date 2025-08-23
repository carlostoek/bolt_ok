from sqlalchemy import Column, Integer, BigInteger, Float, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from .base import Base


class PointTransaction(Base):
    """Transaction log for all point operations.
    
    Records every point addition/deduction with full audit trail.
    """
    __tablename__ = "point_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Positive for additions, negative for deductions
    balance_after = Column(Float, nullable=False)  # User's balance after this transaction
    source = Column(String(50), nullable=False)  # e.g., "message", "reaction", "daily_checkin"
    description = Column(Text, nullable=True)  # Detailed description of the transaction
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, source='{self.source}')>"


class VipTransaction(Base):
    """Auditoría completa de estado VIP"""
    __tablename__ = "vip_transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    action = Column(String)  # "grant", "revoke", "expire", "extend"
    source = Column(String)  # "subscription", "badge", "promotion", "admin"
    source_id = Column(Integer)  # ID del badge o token que lo otorgó
    duration_days = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    notes = Column(String, nullable=True)