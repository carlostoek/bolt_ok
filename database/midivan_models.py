"""
Database models for Mi Diván VIP exclusive features.

Includes:
- Compatibility quizzes with Diana
- Anonymous messages to Diana
- Quiz results and analytics
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base


class CompatibilityQuiz(Base):
    """
    Compatibility quiz with Diana - VIP exclusive feature.

    Each quiz has multiple questions that assess user's compatibility
    with Diana across different dimensions (personality, interests, values).
    """
    __tablename__ = "compatibility_quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Rewards
    besitos_reward = Column(Integer, default=50, nullable=False)

    # Metadata
    total_questions = Column(Integer, default=0, nullable=False)
    average_completion_time = Column(Integer, nullable=True)  # seconds

    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """
    Individual question in a compatibility quiz.

    Each question has multiple answer options, each with a compatibility score.
    """
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("compatibility_quizzes.id"), nullable=False)
    question_number = Column(Integer, nullable=False)  # Order in quiz
    question_text = Column(Text, nullable=False)

    # Optional: Question category for analytics
    category = Column(String(50), nullable=True)  # e.g., "personality", "interests", "values"

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    quiz = relationship("CompatibilityQuiz", back_populates="questions")
    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")


class QuizOption(Base):
    """
    Answer option for a quiz question.

    Each option has a compatibility score (0-100) indicating how well
    this answer aligns with Diana's preferences.
    """
    __tablename__ = "quiz_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    option_number = Column(Integer, nullable=False)  # Order in question (A, B, C, D)
    option_text = Column(Text, nullable=False)
    compatibility_score = Column(Integer, nullable=False, default=50)  # 0-100

    # Optional: Personalized response from Diana based on this choice
    diana_response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    question = relationship("QuizQuestion", back_populates="options")


class QuizAttempt(Base):
    """
    User's attempt at a compatibility quiz.

    Tracks answers, score, and completion status.
    """
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("compatibility_quizzes.id"), nullable=False)

    # Progress
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    current_question_number = Column(Integer, default=1, nullable=False)

    # Results
    total_score = Column(Float, default=0.0, nullable=False)  # 0-100 percentage
    compatibility_level = Column(String(50), nullable=True)  # "Perfect Match", "Great Match", etc.

    # User's answers (JSON: {question_id: option_id})
    answers = Column(JSON, default=dict, nullable=False)

    # Rewards
    besitos_earned = Column(Integer, default=0, nullable=False)
    reward_claimed = Column(Boolean, default=False, nullable=False)

    # Analytics
    completion_time_seconds = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User")
    quiz = relationship("CompatibilityQuiz", back_populates="attempts")


class AnonymousMessage(Base):
    """
    Anonymous messages sent to Diana by VIP users.

    Users can send anonymous messages that Diana will read and respond to.
    The system maintains anonymity while allowing Diana to respond through the bot.
    """
    __tablename__ = "anonymous_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Message content
    message_text = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=func.now(), nullable=False)

    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    is_responded = Column(Boolean, default=False, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Diana's response
    response_text = Column(Text, nullable=True)
    response_sent_to_user = Column(Boolean, default=False, nullable=False)
    response_sent_at = Column(DateTime, nullable=True)

    # Metadata
    message_length = Column(Integer, nullable=False)
    sentiment = Column(String(20), nullable=True)  # "positive", "neutral", "negative", "flirty", etc.

    # Admin notes (visible only to Diana/admin)
    admin_notes = Column(Text, nullable=True)
    flagged_for_review = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User")


class DivanActivity(Base):
    """
    Track user engagement with Mi Diván features.

    Analytics for VIP exclusive features usage.
    """
    __tablename__ = "divan_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Activity type
    activity_type = Column(String(50), nullable=False)  # "quiz_started", "quiz_completed", "message_sent", etc.
    activity_timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Activity details (JSON)
    activity_data = Column(JSON, default=dict, nullable=False)

    # Relationships
    user = relationship("User")
