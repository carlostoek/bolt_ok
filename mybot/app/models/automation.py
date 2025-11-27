from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin


class AutomationTrigger(Base, TimestampMixin):
    __tablename__ = 'automation_triggers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(100), nullable=False)  # daily, weekly, event-based, etc.
    trigger_condition = Column(Text)  # Condition that triggers the automation
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime)  # When to start the trigger
    end_time = Column(DateTime)  # When to end the trigger
    
    # Relationships
    actions = relationship("TriggerAction", back_populates="trigger")


class TriggerAction(Base, TimestampMixin):
    __tablename__ = 'trigger_actions'
    
    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey('automation_triggers.id'))
    action_type = Column(String(100), nullable=False)  # send_message, update_status, etc.
    action_params = Column(JSON)  # Parameters for the action
    execution_order = Column(Integer, default=0)  # Order to execute actions
    
    # Relationships
    trigger = relationship("AutomationTrigger", back_populates="actions")
    execution_logs = relationship("TriggerExecutionLog", back_populates="action")


class TriggerExecutionLog(Base, TimestampMixin):
    __tablename__ = 'trigger_execution_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey('trigger_actions.id'))
    execution_time = Column(DateTime)
    is_successful = Column(Boolean, default=False)
    error_message = Column(Text)
    execution_duration = Column(Integer)  # Duration in milliseconds