"""
Interactive quiz handlers for compatibility quiz with Diana.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.midivan_service import MiDivanService
from utils.user_roles import get_user_role
from utils.localization import get_text

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("quiz:start:"))
async def start_quiz(callback: CallbackQuery, session: AsyncSession):
    """Start a new quiz attempt."""
    user_id = callback.from_user.id
    quiz_id = int(callback.data.split(":")[2])

    # Verify VIP status
    role = await get_user_role(callback.bot, user_id, session=session)
    if role != "vip":
        await callback.answer(
            get_text("midivan.vip_only"),
            show_alert=True
        )
        return

    try:
        midivan_service = MiDivanService(session)

        # Start quiz
        attempt = await midivan_service.start_quiz(user_id, quiz_id)

        # Show first question
        await show_question(callback, session, attempt.id, 1)

    except Exception as e:
        logger.error(f"Error starting quiz {quiz_id} for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.quiz_start_error"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("quiz:continue:"))
async def continue_quiz(callback: CallbackQuery, session: AsyncSession):
    """Continue an incomplete quiz."""
    user_id = callback.from_user.id
    quiz_id = int(callback.data.split(":")[2])

    # Verify VIP status
    role = await get_user_role(callback.bot, user_id, session=session)
    if role != "vip":
        await callback.answer(
            get_text("midivan.vip_only"),
            show_alert=True
        )
        return

    try:
        midivan_service = MiDivanService(session)

        # Get existing attempt
        attempt = await midivan_service.get_user_quiz_attempt(user_id, quiz_id, only_incomplete=True)

        if not attempt:
            await callback.answer(
                get_text("midivan.quiz_no_progress"),
                show_alert=True
            )
            return

        # Show current question
        await show_question(callback, session, attempt.id, attempt.current_question_number)

    except Exception as e:
        logger.error(f"Error continuing quiz {quiz_id} for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.quiz_continue_error"),
            show_alert=True
        )


async def show_question(callback: CallbackQuery, session: AsyncSession, attempt_id: int, question_number: int):
    """Display a quiz question with answer options."""
    try:
        midivan_service = MiDivanService(session)

        # Get attempt
        from database.midivan_models import QuizAttempt
        attempt = await session.get(QuizAttempt, attempt_id)
        if not attempt:
            await callback.answer(get_text("midivan.quiz_not_found"), show_alert=True)
            return

        # Get quiz and question
        quiz = await midivan_service.get_active_quiz()
        if not quiz:
            await callback.answer(get_text("midivan.quiz_not_available"), show_alert=True)
            return

        question = await midivan_service.get_quiz_question(attempt.quiz_id, question_number)
        if not question:
            await callback.answer(get_text("midivan.question_not_found"), show_alert=True)
            return

        # Get options
        options = await midivan_service.get_question_options(question.id)
        if not options:
            await callback.answer(get_text("midivan.no_options_available"), show_alert=True)
            return

        # Build question text
        progress = f"{question_number}/{quiz.total_questions}"
        progress_bar = _build_progress_bar(question_number, quiz.total_questions)
        divider = get_text("midivan.divider")

        text = f"""{get_text("midivan.quiz_question_title")}

{divider}

{get_text("midivan.quiz_question_progress", progress=progress)}
{progress_bar}

{question.question_text}

{divider}

{get_text("midivan.quiz_choose_option")}"""

        # Build keyboard with options
        builder = InlineKeyboardBuilder()

        option_labels = ["A", "B", "C", "D", "E", "F"]
        for idx, option in enumerate(options):
            label = option_labels[idx] if idx < len(option_labels) else str(idx + 1)
            builder.button(
                text=f"{label}. {option.option_text[:40]}{'...' if len(option.option_text) > 40 else ''}",
                callback_data=f"quiz:answer:{attempt_id}:{question.id}:{option.id}"
            )

        # Add exit button
        builder.button(text=get_text("midivan.button_back_midivan"), callback_data="midivan:main")

        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing question {question_number} for attempt {attempt_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.quiz_question_error"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("quiz:answer:"))
async def submit_answer(callback: CallbackQuery, session: AsyncSession):
    """Submit answer and move to next question or show results."""
    try:
        parts = callback.data.split(":")
        attempt_id = int(parts[2])
        question_id = int(parts[3])
        option_id = int(parts[4])

        midivan_service = MiDivanService(session)

        # Submit answer
        is_completed, diana_response = await midivan_service.submit_answer(
            attempt_id,
            question_id,
            option_id
        )

        # Show Diana's response if available (brief feedback)
        if diana_response:
            await callback.answer(get_text("midivan.diana_response", response=diana_response[:100]), show_alert=False)
        else:
            await callback.answer(get_text("midivan.answer_saved"), show_alert=False)

        if is_completed:
            # Show final results
            from database.midivan_models import QuizAttempt
            attempt = await session.get(QuizAttempt, attempt_id)
            await show_quiz_final_results(callback, session, attempt)
        else:
            # Get attempt to find next question
            from database.midivan_models import QuizAttempt
            attempt = await session.get(QuizAttempt, attempt_id)

            # Show next question
            await show_question(callback, session, attempt_id, attempt.current_question_number)

    except Exception as e:
        logger.error(f"Error submitting answer: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.quiz_answer_error"),
            show_alert=True
        )


async def show_quiz_final_results(callback: CallbackQuery, session: AsyncSession, attempt):
    """Show final quiz results with detailed analysis."""
    score = attempt.total_score
    level = attempt.compatibility_level
    besitos = attempt.besitos_earned
    divider = get_text("midivan.divider")

    # Build result message
    text = f"""{get_text("midivan.quiz_final_title")}

{divider}

{get_text("midivan.quiz_final_compatibility")}

{level}

**{score:.1f}%**

{divider}

{_get_detailed_compatibility_message(score)}

{divider}

{get_text("midivan.quiz_final_rewards")}
{get_text("midivan.quiz_final_besitos", besitos=besitos)}
{get_text("midivan.quiz_final_analysis")}

{divider}

{_get_compatibility_advice(score)}

{divider}

{get_text("midivan.quiz_final_thanks")}"""

    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("midivan.button_send_to_diana"), callback_data="midivan:message")
    builder.button(text=get_text("midivan.button_view_stats"), callback_data="midivan:stats")
    builder.button(text=get_text("midivan.button_back_midivan"), callback_data="midivan:main")
    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


def _get_detailed_compatibility_message(score: float) -> str:
    """Get detailed message based on compatibility score."""
    if score >= 90:
        return get_text("midivan.detailed_compat_90")
    elif score >= 80:
        return get_text("midivan.detailed_compat_80")
    elif score >= 70:
        return get_text("midivan.detailed_compat_70")
    elif score >= 60:
        return get_text("midivan.detailed_compat_60")
    elif score >= 50:
        return get_text("midivan.detailed_compat_50")
    else:
        return get_text("midivan.detailed_compat_low")


def _get_compatibility_advice(score: float) -> str:
    """Get advice based on compatibility score."""
    if score >= 80:
        return get_text("midivan.advice_high")
    elif score >= 60:
        return get_text("midivan.advice_medium")
    else:
        return get_text("midivan.advice_low")


def _build_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Build visual progress bar."""
    filled = int((current / total) * length)
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}] {current}/{total}"
