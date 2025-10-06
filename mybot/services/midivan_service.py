"""
Service for Mi Diván VIP exclusive features.

Handles:
- Compatibility quizzes with Diana
- Anonymous messaging
- Activity tracking
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from database.midivan_models import (
    CompatibilityQuiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    AnonymousMessage,
    DivanActivity
)
from database.models import User
from services.point_service import PointService

logger = logging.getLogger(__name__)


class MiDivanService:
    """Service for managing Mi Diván VIP features."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    # ==================== COMPATIBILITY QUIZ ====================

    async def get_active_quiz(self) -> Optional[CompatibilityQuiz]:
        """Get the currently active compatibility quiz."""
        stmt = select(CompatibilityQuiz).where(
            CompatibilityQuiz.is_active == True
        ).order_by(CompatibilityQuiz.created_at.desc())

        result = await self.session.execute(stmt)

        # Handle multiple active quizzes by returning the most recent one
        # This prevents errors if there are duplicates
        quizzes = result.scalars().all()

        if not quizzes:
            return None

        if len(quizzes) > 1:
            logger.warning(f"Multiple active quizzes found ({len(quizzes)}). Returning most recent.")

        return quizzes[0]

    async def get_user_quiz_attempt(
        self,
        user_id: int,
        quiz_id: int,
        only_incomplete: bool = False
    ) -> Optional[QuizAttempt]:
        """Get user's quiz attempt."""
        stmt = select(QuizAttempt).where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.quiz_id == quiz_id
        )

        if only_incomplete:
            stmt = stmt.where(QuizAttempt.is_completed == False)

        stmt = stmt.order_by(QuizAttempt.started_at.desc())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def start_quiz(self, user_id: int, quiz_id: int) -> QuizAttempt:
        """Start a new quiz attempt for user."""
        # Check if user has incomplete attempt
        existing = await self.get_user_quiz_attempt(user_id, quiz_id, only_incomplete=True)
        if existing:
            logger.info(f"User {user_id} resuming quiz {quiz_id}")
            return existing

        # Create new attempt
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            current_question_number=1,
            answers={}
        )

        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)

        # Track activity
        await self._track_activity(user_id, "quiz_started", {"quiz_id": quiz_id})

        logger.info(f"User {user_id} started quiz {quiz_id}")
        return attempt

    async def get_quiz_question(
        self,
        quiz_id: int,
        question_number: int
    ) -> Optional[QuizQuestion]:
        """Get specific question from quiz."""
        stmt = select(QuizQuestion).where(
            and_(
                QuizQuestion.quiz_id == quiz_id,
                QuizQuestion.question_number == question_number
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_question_options(self, question_id: int) -> List[QuizOption]:
        """Get all options for a question."""
        stmt = select(QuizOption).where(
            QuizOption.question_id == question_id
        ).order_by(QuizOption.option_number)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def submit_answer(
        self,
        attempt_id: int,
        question_id: int,
        option_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Submit answer for a quiz question.

        Returns:
            (is_quiz_completed, diana_response)
        """
        attempt = await self.session.get(QuizAttempt, attempt_id)
        if not attempt or attempt.is_completed:
            return False, None

        # Get option to check validity and score
        option = await self.session.get(QuizOption, option_id)
        if not option or option.question_id != question_id:
            logger.warning(f"Invalid option {option_id} for question {question_id}")
            return False, None

        # Store answer
        answers = attempt.answers or {}
        answers[str(question_id)] = option_id
        attempt.answers = answers

        # Update score
        attempt.total_score += option.compatibility_score

        # Get quiz to check total questions
        quiz = await self.session.get(CompatibilityQuiz, attempt.quiz_id)
        if not quiz:
            return False, None

        # Move to next question
        attempt.current_question_number += 1

        # Check if quiz is complete
        if attempt.current_question_number > quiz.total_questions:
            await self._complete_quiz(attempt, quiz)
            await self.session.commit()
            return True, option.diana_response

        await self.session.commit()
        return False, option.diana_response

    async def _complete_quiz(self, attempt: QuizAttempt, quiz: CompatibilityQuiz):
        """Complete quiz and award rewards."""
        attempt.is_completed = True
        attempt.completed_at = datetime.utcnow()

        # Calculate completion time
        if attempt.started_at:
            delta = datetime.utcnow() - attempt.started_at
            attempt.completion_time_seconds = int(delta.total_seconds())

        # Calculate final score percentage
        max_possible_score = quiz.total_questions * 100
        attempt.total_score = (attempt.total_score / max_possible_score) * 100

        # Determine compatibility level
        attempt.compatibility_level = self._get_compatibility_level(attempt.total_score)

        # Award besitos
        attempt.besitos_earned = quiz.besitos_reward
        await self.point_service.add_points(
            attempt.user_id,
            quiz.besitos_reward
        )

        # Track activity
        await self._track_activity(
            attempt.user_id,
            "quiz_completed",
            {
                "quiz_id": quiz.id,
                "score": attempt.total_score,
                "level": attempt.compatibility_level,
                "besitos_earned": quiz.besitos_reward
            }
        )

        logger.info(
            f"User {attempt.user_id} completed quiz {quiz.id} "
            f"with {attempt.total_score:.1f}% compatibility"
        )

    def _get_compatibility_level(self, score: float) -> str:
        """Determine compatibility level from score."""
        if score >= 90:
            return "💘 Alma Gemela"
        elif score >= 80:
            return "💖 Match Perfecto"
        elif score >= 70:
            return "💕 Gran Conexión"
        elif score >= 60:
            return "💗 Buena Compatibilidad"
        elif score >= 50:
            return "💓 Hay Química"
        else:
            return "💝 Por Conocerse"

    async def get_user_quiz_stats(self, user_id: int) -> Dict:
        """Get user's quiz statistics."""
        # Count completed quizzes
        stmt = select(func.count(QuizAttempt.id)).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.is_completed == True
            )
        )
        result = await self.session.execute(stmt)
        total_completed = result.scalar() or 0

        # Get average score
        stmt = select(func.avg(QuizAttempt.total_score)).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.is_completed == True
            )
        )
        result = await self.session.execute(stmt)
        avg_score = result.scalar() or 0

        # Get best score
        stmt = select(func.max(QuizAttempt.total_score)).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.is_completed == True
            )
        )
        result = await self.session.execute(stmt)
        best_score = result.scalar() or 0

        return {
            "total_completed": total_completed,
            "average_score": round(avg_score, 1) if avg_score else 0,
            "best_score": round(best_score, 1) if best_score else 0,
            "compatibility_level": self._get_compatibility_level(best_score) if best_score else "💝 Por Conocerse"
        }

    # ==================== ANONYMOUS MESSAGES ====================

    async def send_anonymous_message(
        self,
        user_id: int,
        message_text: str
    ) -> AnonymousMessage:
        """Send anonymous message to Diana."""
        message = AnonymousMessage(
            user_id=user_id,
            message_text=message_text,
            message_length=len(message_text)
        )

        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        # Track activity
        await self._track_activity(
            user_id,
            "message_sent",
            {"message_id": message.id, "length": len(message_text)}
        )

        logger.info(f"User {user_id} sent anonymous message {message.id}")
        return message

    async def get_pending_messages(
        self,
        limit: int = 50,
        unread_only: bool = True
    ) -> List[AnonymousMessage]:
        """Get messages pending Diana's review."""
        stmt = select(AnonymousMessage)

        if unread_only:
            stmt = stmt.where(AnonymousMessage.is_read == False)

        stmt = stmt.order_by(AnonymousMessage.sent_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_message_read(self, message_id: int):
        """Mark message as read by Diana."""
        message = await self.session.get(AnonymousMessage, message_id)
        if message and not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()
            await self.session.commit()
            logger.info(f"Message {message_id} marked as read")

    async def respond_to_message(
        self,
        message_id: int,
        response_text: str
    ) -> bool:
        """Diana responds to anonymous message."""
        message = await self.session.get(AnonymousMessage, message_id)
        if not message:
            return False

        message.response_text = response_text
        message.is_responded = True
        message.responded_at = datetime.utcnow()

        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()

        await self.session.commit()
        logger.info(f"Diana responded to message {message_id}")
        return True

    async def get_user_messages(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[AnonymousMessage]:
        """Get user's anonymous messages and responses."""
        stmt = select(AnonymousMessage).where(
            AnonymousMessage.user_id == user_id
        ).order_by(AnonymousMessage.sent_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_message_with_response(self, message_id: int) -> Optional[AnonymousMessage]:
        """Get message with Diana's response."""
        message = await self.session.get(AnonymousMessage, message_id)
        if message and message.is_responded and not message.response_sent_to_user:
            message.response_sent_to_user = True
            message.response_sent_at = datetime.utcnow()
            await self.session.commit()
        return message

    async def get_user_message_stats(self, user_id: int) -> Dict:
        """Get user's messaging statistics."""
        # Total messages sent
        stmt = select(func.count(AnonymousMessage.id)).where(
            AnonymousMessage.user_id == user_id
        )
        result = await self.session.execute(stmt)
        total_sent = result.scalar() or 0

        # Messages with responses
        stmt = select(func.count(AnonymousMessage.id)).where(
            and_(
                AnonymousMessage.user_id == user_id,
                AnonymousMessage.is_responded == True
            )
        )
        result = await self.session.execute(stmt)
        total_responded = result.scalar() or 0

        # Pending responses
        pending = total_sent - total_responded

        return {
            "total_sent": total_sent,
            "total_responded": total_responded,
            "pending_responses": pending
        }

    # ==================== ACTIVITY TRACKING ====================

    async def _track_activity(
        self,
        user_id: int,
        activity_type: str,
        activity_data: Dict
    ):
        """Track user activity in Mi Diván."""
        activity = DivanActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data
        )
        self.session.add(activity)
        await self.session.commit()

    async def get_user_activity_summary(self, user_id: int) -> Dict:
        """Get summary of user's Mi Diván engagement."""
        quiz_stats = await self.get_user_quiz_stats(user_id)
        message_stats = await self.get_user_message_stats(user_id)

        return {
            "quizzes": quiz_stats,
            "messages": message_stats
        }
