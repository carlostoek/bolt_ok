"""
Handlers for Mi Diván - VIP exclusive features hub.

Includes:
- Enhanced subscription info display
- Compatibility quiz with Diana
- Anonymous messaging to Diana
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.midivan_service import MiDivanService
from services.subscription_service import SubscriptionService
from database.models import User
from utils.user_roles import get_user_role
from utils.localization import get_text

logger = logging.getLogger(__name__)
router = Router()


# ==================== FSM STATES ====================

class QuizStates(StatesGroup):
    """States for quiz flow."""
    taking_quiz = State()


class MessageStates(StatesGroup):
    """States for anonymous messaging."""
    writing_message = State()


# ==================== MI DIVÁN MAIN MENU ====================

@router.callback_query(F.data == "midivan:main")
async def midivan_main_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Mi Diván main menu - VIP exclusive features hub.

    Displays:
    - Enhanced subscription information
    - Compatibility quiz option
    - Anonymous messaging option
    - Quick stats
    """
    user_id = callback.from_user.id

    # Verify VIP status
    role = await get_user_role(callback.bot, user_id, session=session)
    if role != "vip":
        await callback.answer(
            get_text("midivan.vip_only"),
            show_alert=True
        )
        return

    try:
        # Get subscription info
        sub_service = SubscriptionService(session)
        subscription = await sub_service.get_subscription(user_id)

        # Get Mi Diván stats
        midivan_service = MiDivanService(session)
        activity_summary = await midivan_service.get_user_activity_summary(user_id)

        # Build enhanced message
        message_parts = [
            get_text("midivan.main_title"),
            get_text("midivan.divider")
        ]

        # Subscription section
        if subscription:
            expires_at = subscription.expires_at
            if expires_at:
                days_remaining = (expires_at - datetime.utcnow()).days
                if days_remaining > 30:
                    status_emoji = "✨"
                    status_text = get_text("midivan.status_active")
                elif days_remaining > 7:
                    status_emoji = "⏰"
                    status_text = get_text("midivan.status_expires_soon", days=days_remaining)
                else:
                    status_emoji = "⚠️"
                    status_text = get_text("midivan.status_expires_warning", days=days_remaining)

                expires_str = expires_at.strftime("%d/%m/%Y")
            else:
                status_emoji = "👑"
                status_text = get_text("midivan.status_permanent")
                expires_str = get_text("midivan.expires_unlimited")

            message_parts.extend([
                get_text("midivan.subscription_title"),
                f"{status_emoji} Estado: {status_text}",
                get_text("midivan.valid_until", date=expires_str)
            ])
        else:
            message_parts.extend([
                get_text("midivan.subscription_title"),
                get_text("midivan.status_verified"),
                get_text("midivan.status_field")
            ])

        message_parts.append(f"\n{get_text('midivan.divider')}")

        # Activity stats section
        quiz_stats = activity_summary.get("quizzes", {})
        message_stats = activity_summary.get("messages", {})

        message_parts.extend([
            get_text("midivan.activity_title"),
            get_text("midivan.quizzes_completed", count=quiz_stats.get('total_completed', 0)),
            get_text("midivan.best_compatibility", level=quiz_stats.get('compatibility_level', '💝 Por Conocerse')),
            get_text("midivan.messages_sent", count=message_stats.get('total_sent', 0)),
            get_text("midivan.responses_received", count=message_stats.get('total_responded', 0))
        ])

        # Pending responses notification
        pending = message_stats.get('pending_responses', 0)
        if pending > 0:
            message_parts.append(get_text("midivan.pending_notification", count=pending))

        message_parts.extend([
            f"\n{get_text('midivan.divider')}",
            get_text("midivan.what_to_do")
        ])

        text = "\n".join(message_parts)

        # Build keyboard
        builder = InlineKeyboardBuilder()

        # Main features
        builder.button(
            text=get_text("midivan.button_compatibility_test"),
            callback_data="midivan:quiz"
        )
        builder.button(
            text=get_text("midivan.button_anonymous_message"),
            callback_data="midivan:message"
        )

        # Secondary features
        builder.button(
            text=get_text("midivan.button_my_messages"),
            callback_data="midivan:my_messages"
        )
        builder.button(
            text=get_text("midivan.button_my_stats"),
            callback_data="midivan:stats"
        )

        # Back button
        builder.button(
            text=get_text("midivan.button_back_menu"),
            callback_data="vip_menu"
        )

        builder.adjust(2, 2, 1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing Mi Diván menu for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.error_loading"),
            show_alert=True
        )


# ==================== COMPATIBILITY QUIZ ====================

@router.callback_query(F.data == "midivan:quiz")
async def show_quiz_intro(callback: CallbackQuery, session: AsyncSession):
    """Show compatibility quiz introduction."""
    user_id = callback.from_user.id

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

        # Get active quiz
        quiz = await midivan_service.get_active_quiz()
        if not quiz:
            await callback.answer(
                get_text("midivan.quiz_no_available"),
                show_alert=True
            )
            return

        # Check if user has completed this quiz
        attempt = await midivan_service.get_user_quiz_attempt(user_id, quiz.id)
        if attempt and attempt.is_completed:
            # Show results instead
            await show_quiz_results(callback, session, attempt)
            return

        # Show introduction
        divider = get_text("midivan.divider")
        description = quiz.description or get_text("midivan.quiz_intro_description")

        text = f"""{get_text("midivan.quiz_intro_title", title=quiz.title)}

{description}

{divider}

{get_text("midivan.quiz_details_title")}
{get_text("midivan.quiz_questions_count", count=quiz.total_questions)}
{get_text("midivan.quiz_time_estimate", minutes=quiz.total_questions)}
{get_text("midivan.quiz_reward", besitos=quiz.besitos_reward)}

{get_text("midivan.quiz_how_works_title")}
{get_text("midivan.quiz_how_works_text")}

{divider}

{get_text("midivan.quiz_ready_question")}"""

        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("midivan.button_start_quiz"), callback_data=f"quiz:start:{quiz.id}")

        if attempt and not attempt.is_completed:
            builder.button(text=get_text("midivan.button_continue_quiz"), callback_data=f"quiz:continue:{quiz.id}")

        builder.button(text=get_text("midivan.button_back"), callback_data="midivan:main")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing quiz intro for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.quiz_error_loading"),
            show_alert=True
        )


async def show_quiz_results(callback: CallbackQuery, session: AsyncSession, attempt):
    """Show completed quiz results."""
    divider = get_text("midivan.divider")

    text = f"""{get_text("midivan.quiz_results_title")}

{divider}

{get_text("midivan.quiz_compatibility_title")}
{attempt.compatibility_level}

{get_text("midivan.quiz_score", score=f"{attempt.total_score:.1f}")}

{divider}

{_get_compatibility_message(attempt.total_score)}

{divider}

{get_text("midivan.quiz_completed")}
{get_text("midivan.quiz_besitos_earned", besitos=attempt.besitos_earned)}

{get_text("midivan.quiz_try_other")}"""

    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("midivan.button_send_message"), callback_data="midivan:message")
    builder.button(text=get_text("midivan.button_back_midivan"), callback_data="midivan:main")
    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


def _get_compatibility_message(score: float) -> str:
    """Get personalized message based on compatibility score."""
    if score >= 90:
        return get_text("midivan.compat_90_title") + get_text("midivan.compat_90_message")
    elif score >= 80:
        return get_text("midivan.compat_80_title") + get_text("midivan.compat_80_message")
    elif score >= 70:
        return get_text("midivan.compat_70_title") + get_text("midivan.compat_70_message")
    elif score >= 60:
        return get_text("midivan.compat_60_title") + get_text("midivan.compat_60_message")
    elif score >= 50:
        return get_text("midivan.compat_50_title") + get_text("midivan.compat_50_message")
    else:
        return get_text("midivan.compat_low_title") + get_text("midivan.compat_low_message")


# ==================== ANONYMOUS MESSAGING ====================

@router.callback_query(F.data == "midivan:message")
async def start_anonymous_message(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start anonymous message to Diana."""
    user_id = callback.from_user.id

    # Verify VIP status
    role = await get_user_role(callback.bot, user_id, session=session)
    if role != "vip":
        await callback.answer(
            get_text("midivan.vip_only"),
            show_alert=True
        )
        return

    divider = get_text("midivan.divider")

    text = f"""{get_text("midivan.message_title")}

{divider}

{get_text("midivan.message_privacy_title")}
{get_text("midivan.message_privacy_text")}

{get_text("midivan.message_what_write_title")}
{get_text("midivan.message_what_write_list")}

{get_text("midivan.message_instructions_title")}
{get_text("midivan.message_instructions_text")}

{get_text("midivan.message_important_title")}
{get_text("midivan.message_important_list")}

{divider}

{get_text("midivan.message_write_now")}"""

    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("midivan.button_cancel"), callback_data="midivan:main")
    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(MessageStates.writing_message)
    await callback.answer()


@router.message(MessageStates.writing_message)
async def receive_anonymous_message(message: Message, session: AsyncSession, state: FSMContext):
    """Receive and save anonymous message."""
    user_id = message.from_user.id
    message_text = message.text

    if not message_text or len(message_text) < 10:
        await message.answer(get_text("midivan.message_too_short"))
        return

    if len(message_text) > 1000:
        await message.answer(get_text("midivan.message_too_long"))
        return

    try:
        midivan_service = MiDivanService(session)
        saved_message = await midivan_service.send_anonymous_message(user_id, message_text)

        divider = get_text("midivan.divider")

        text = f"""{get_text("midivan.message_sent_title")}

{divider}

{get_text("midivan.message_sent_text")}

{get_text("midivan.message_status_waiting")}
{get_text("midivan.message_notification")}

{get_text("midivan.message_view_anytime")}

{divider}

{get_text("midivan.message_thanks")}"""

        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("midivan.button_view_messages"), callback_data="midivan:my_messages")
        builder.button(text=get_text("midivan.button_back_midivan"), callback_data="midivan:main")
        builder.adjust(1)

        await message.answer(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

        # Clear state
        await state.clear()

        logger.info(f"User {user_id} sent anonymous message {saved_message.id}")

    except Exception as e:
        logger.error(f"Error saving anonymous message for user {user_id}: {e}", exc_info=True)
        await message.answer(get_text("midivan.message_send_error"))


@router.callback_query(F.data == "midivan:my_messages")
async def show_user_messages(callback: CallbackQuery, session: AsyncSession):
    """Show user's anonymous messages and responses."""
    user_id = callback.from_user.id

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
        messages = await midivan_service.get_user_messages(user_id, limit=10)

        if not messages:
            divider = get_text("midivan.divider")

            text = f"""{get_text("midivan.my_messages_title")}

{divider}

{get_text("midivan.no_messages_text")}

{get_text("midivan.no_messages_question")}"""

            builder = InlineKeyboardBuilder()
            builder.button(text=get_text("midivan.button_send_first_message"), callback_data="midivan:message")
            builder.button(text=get_text("midivan.button_back"), callback_data="midivan:main")
            builder.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Build message list
        divider = get_text("midivan.divider")
        message_parts = [
            get_text("midivan.my_messages_title"),
            "",
            divider,
            ""
        ]

        for idx, msg in enumerate(messages[:5], 1):
            sent_date = msg.sent_at.strftime("%d/%m %H:%M")
            preview = msg.message_text[:50] + "..." if len(msg.message_text) > 50 else msg.message_text

            if msg.is_responded:
                status = get_text("midivan.status_responded")
            elif msg.is_read:
                status = get_text("midivan.status_read")
            else:
                status = get_text("midivan.status_sent")

            message_parts.extend([
                f"**{idx}. {sent_date}** - {status}",
                f"_{preview}_",
                ""
            ])

        message_parts.append(divider)
        message_parts.append(get_text("midivan.select_message_text"))

        text = "\n".join(message_parts)

        # Build keyboard with message buttons
        builder = InlineKeyboardBuilder()

        for idx, msg in enumerate(messages[:5], 1):
            emoji = "💬" if msg.is_responded else "📤"
            builder.button(
                text=get_text("midivan.button_message_num", emoji=emoji, num=idx),
                callback_data=f"midivan:view_msg:{msg.id}"
            )

        builder.button(text=get_text("midivan.button_new_message"), callback_data="midivan:message")
        builder.button(text=get_text("midivan.button_back"), callback_data="midivan:main")

        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing messages for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.messages_load_error"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("midivan:view_msg:"))
async def view_message_detail(callback: CallbackQuery, session: AsyncSession):
    """View detailed message and response."""
    user_id = callback.from_user.id
    message_id = int(callback.data.split(":")[2])

    try:
        midivan_service = MiDivanService(session)
        msg = await midivan_service.get_message_with_response(message_id)

        if not msg or msg.user_id != user_id:
            await callback.answer(
                get_text("midivan.message_not_found"),
                show_alert=True
            )
            return

        sent_date = msg.sent_at.strftime("%d/%m/%Y %H:%M")
        divider = get_text("midivan.divider")

        message_parts = [
            get_text("midivan.message_detail_title"),
            "",
            divider,
            "",
            get_text("midivan.message_sent_date", date=sent_date),
            ""
        ]

        # Show status
        if msg.is_responded:
            resp_date = msg.responded_at.strftime("%d/%m/%Y %H:%M")
            message_parts.extend([
                get_text("midivan.message_status_responded", date=resp_date),
                ""
            ])
        elif msg.is_read:
            read_date = msg.read_at.strftime("%d/%m/%Y %H:%M")
            message_parts.extend([
                get_text("midivan.message_status_read", date=read_date),
                ""
            ])
        else:
            message_parts.extend([
                get_text("midivan.message_status_waiting"),
                ""
            ])

        message_parts.extend([
            divider,
            "",
            get_text("midivan.your_message_label"),
            f"_{msg.message_text}_",
            ""
        ])

        # Show response if available
        if msg.is_responded and msg.response_text:
            message_parts.extend([
                divider,
                "",
                get_text("midivan.diana_response_label"),
                f"{msg.response_text}",
                ""
            ])

        message_parts.append(divider)

        text = "\n".join(message_parts)

        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("midivan.button_my_messages"), callback_data="midivan:my_messages")
        builder.button(text=get_text("midivan.button_back_midivan"), callback_data="midivan:main")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error viewing message {message_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.message_view_error"),
            show_alert=True
        )


@router.callback_query(F.data == "midivan:stats")
async def show_user_stats(callback: CallbackQuery, session: AsyncSession):
    """Show detailed user statistics for Mi Diván."""
    user_id = callback.from_user.id

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
        activity_summary = await midivan_service.get_user_activity_summary(user_id)

        quiz_stats = activity_summary.get("quizzes", {})
        message_stats = activity_summary.get("messages", {})
        divider = get_text("midivan.divider")

        text = f"""{get_text("midivan.stats_title")}

{divider}

{get_text("midivan.stats_quiz_title")}
{get_text("midivan.stats_quiz_completed", count=quiz_stats.get('total_completed', 0))}
{get_text("midivan.stats_quiz_average", score=f"{quiz_stats.get('average_score', 0):.1f}")}
{get_text("midivan.stats_quiz_best", score=f"{quiz_stats.get('best_score', 0):.1f}")}
{get_text("midivan.stats_quiz_level", level=quiz_stats.get('compatibility_level', '💝 Por Conocerse'))}

{get_text("midivan.stats_messages_title")}
{get_text("midivan.stats_messages_sent", count=message_stats.get('total_sent', 0))}
{get_text("midivan.stats_messages_responded", count=message_stats.get('total_responded', 0))}
{get_text("midivan.stats_messages_pending", count=message_stats.get('pending_responses', 0))}

{divider}

{get_text("midivan.stats_encouragement")}"""

        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("midivan.button_do_quiz"), callback_data="midivan:quiz")
        builder.button(text=get_text("midivan.button_anonymous_message"), callback_data="midivan:message")
        builder.button(text=get_text("midivan.button_back"), callback_data="midivan:main")
        builder.adjust(2, 1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing stats for user {user_id}: {e}", exc_info=True)
        await callback.answer(
            get_text("midivan.stats_error"),
            show_alert=True
        )
