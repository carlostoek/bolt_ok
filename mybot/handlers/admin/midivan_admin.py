"""
Admin panel for Diana to manage Mi Diván features.

Allows Diana/admins to:
- View and respond to anonymous messages
- Create and manage compatibility quizzes
- View analytics and engagement stats
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from services.midivan_service import MiDivanService
from utils.user_roles import is_admin

logger = logging.getLogger(__name__)
router = Router()


# ==================== FSM STATES ====================

class RespondMessageStates(StatesGroup):
    """States for responding to anonymous messages."""
    writing_response = State()


class CreateQuizStates(StatesGroup):
    """States for creating quiz."""
    entering_title = State()
    entering_description = State()
    entering_questions = State()


# ==================== MAIN ADMIN MENU ====================

@router.callback_query(F.data == "admin:midivan")
async def midivan_admin_menu(callback: CallbackQuery, session: AsyncSession):
    """Main admin menu for Mi Diván management."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        midivan_service = MiDivanService(session)

        # Get pending messages count
        pending_messages = await midivan_service.get_pending_messages(unread_only=True)
        pending_count = len(pending_messages)

        text = f"""🎯 **Panel de Mi Diván**

━━━━━━━━━━━━━━━━━━━━━

**📊 Resumen:**

✉️ **Mensajes Anónimos**
• Pendientes de leer: {pending_count}
• Esperando respuesta: {len([m for m in pending_messages if m.is_read and not m.is_responded])}

💘 **Quizzes de Compatibilidad**
• Quiz activo disponible
• Estadísticas y análisis disponibles

━━━━━━━━━━━━━━━━━━━━━

**¿Qué deseas hacer?**"""

        builder = InlineKeyboardBuilder()

        # Messages section
        builder.button(
            text=f"📬 Ver Mensajes ({pending_count} nuevos)",
            callback_data="admin:midivan:messages"
        )
        builder.button(
            text="📊 Estadísticas de Mensajes",
            callback_data="admin:midivan:message_stats"
        )

        # Quiz section
        builder.button(
            text="💘 Gestionar Quizzes",
            callback_data="admin:midivan:quizzes"
        )
        builder.button(
            text="📈 Estadísticas de Quizzes",
            callback_data="admin:midivan:quiz_stats"
        )

        # Back
        builder.button(
            text="← Volver al Panel Admin",
            callback_data="admin_main_menu"
        )

        builder.adjust(2, 2, 1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing Mi Diván admin menu: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar el panel. Intenta nuevamente.",
            show_alert=True
        )


# ==================== MESSAGE MANAGEMENT ====================

@router.callback_query(F.data == "admin:midivan:messages")
async def show_pending_messages(callback: CallbackQuery, session: AsyncSession):
    """Show list of pending anonymous messages."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        midivan_service = MiDivanService(session)
        messages = await midivan_service.get_pending_messages(limit=20, unread_only=False)

        if not messages:
            text = """📬 **Mensajes Anónimos**

━━━━━━━━━━━━━━━━━━━━━

No hay mensajes pendientes.

¡Todos los mensajes han sido respondidos! 🎉"""

            builder = InlineKeyboardBuilder()
            builder.button(text="← Volver", callback_data="admin:midivan")
            builder.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Separate by status
        unread = [m for m in messages if not m.is_read]
        read_pending = [m for m in messages if m.is_read and not m.is_responded]
        responded = [m for m in messages if m.is_responded][:5]  # Only recent 5

        message_parts = [
            "📬 **Mensajes Anónimos**",
            "",
            "━━━━━━━━━━━━━━━━━━━━━"
        ]

        if unread:
            message_parts.extend([
                "",
                f"**🆕 Sin Leer ({len(unread)})**",
                ""
            ])
            for msg in unread[:5]:
                preview = msg.message_text[:40] + "..." if len(msg.message_text) > 40 else msg.message_text
                sent_date = msg.sent_at.strftime("%d/%m %H:%M")
                message_parts.append(f"• {sent_date} - _{preview}_")

        if read_pending:
            message_parts.extend([
                "",
                f"**👁️ Leídos sin Responder ({len(read_pending)})**",
                ""
            ])
            for msg in read_pending[:5]:
                preview = msg.message_text[:40] + "..." if len(msg.message_text) > 40 else msg.message_text
                sent_date = msg.sent_at.strftime("%d/%m %H:%M")
                message_parts.append(f"• {sent_date} - _{preview}_")

        if responded:
            message_parts.extend([
                "",
                f"**✅ Respondidos Recientemente**",
                ""
            ])
            for msg in responded:
                preview = msg.message_text[:40] + "..." if len(msg.message_text) > 40 else msg.message_text
                sent_date = msg.sent_at.strftime("%d/%m %H:%M")
                message_parts.append(f"• {sent_date} - _{preview}_")

        message_parts.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            "Selecciona un mensaje para ver detalles y responder:"
        ])

        text = "\n".join(message_parts)

        # Build keyboard
        builder = InlineKeyboardBuilder()

        # Show unread first
        for msg in unread[:3]:
            builder.button(
                text=f"🆕 {msg.sent_at.strftime('%d/%m %H:%M')}",
                callback_data=f"admin:midivan:view:{msg.id}"
            )

        # Then read pending
        for msg in read_pending[:3]:
            builder.button(
                text=f"👁️ {msg.sent_at.strftime('%d/%m %H:%M')}",
                callback_data=f"admin:midivan:view:{msg.id}"
            )

        # Navigation
        builder.button(text="🔄 Actualizar", callback_data="admin:midivan:messages")
        builder.button(text="← Volver", callback_data="admin:midivan")

        builder.adjust(1, 1, 1, 2)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing messages: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar mensajes. Intenta nuevamente.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("admin:midivan:view:"))
async def view_message_detail(callback: CallbackQuery, session: AsyncSession):
    """View message detail and respond."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        message_id = int(callback.data.split(":")[3])
        midivan_service = MiDivanService(session)

        # Get message
        from database.midivan_models import AnonymousMessage
        msg = await session.get(AnonymousMessage, message_id)

        if not msg:
            await callback.answer("❌ Mensaje no encontrado.", show_alert=True)
            return

        # Mark as read
        if not msg.is_read:
            await midivan_service.mark_message_read(message_id)
            msg.is_read = True
            msg.read_at = datetime.utcnow()

        # Build message detail
        sent_date = msg.sent_at.strftime("%d/%m/%Y %H:%M")

        message_parts = [
            "📧 **Mensaje Anónimo - Vista Admin**",
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"**📅 Recibido:** {sent_date}",
            f"**📏 Longitud:** {msg.message_length} caracteres"
        ]

        if msg.is_read:
            read_date = msg.read_at.strftime("%d/%m/%Y %H:%M")
            message_parts.append(f"**👁️ Leído:** {read_date}")

        if msg.is_responded:
            resp_date = msg.responded_at.strftime("%d/%m/%Y %H:%M")
            message_parts.extend([
                f"**✅ Respondido:** {resp_date}",
                f"**📤 Enviado al usuario:** {'Sí' if msg.response_sent_to_user else 'No'}"
            ])

        message_parts.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            "**💬 Mensaje del usuario:**",
            "",
            f"{msg.message_text}",
            ""
        ])

        if msg.is_responded and msg.response_text:
            message_parts.extend([
                "━━━━━━━━━━━━━━━━━━━━━",
                "",
                "**💕 Tu respuesta:**",
                "",
                f"{msg.response_text}",
                ""
            ])

        if msg.admin_notes:
            message_parts.extend([
                "━━━━━━━━━━━━━━━━━━━━━",
                "",
                f"**📝 Notas:** {msg.admin_notes}",
                ""
            ])

        message_parts.append("━━━━━━━━━━━━━━━━━━━━━")

        text = "\n".join(message_parts)

        # Build keyboard
        builder = InlineKeyboardBuilder()

        if not msg.is_responded:
            builder.button(
                text="💬 Responder a este mensaje",
                callback_data=f"admin:midivan:respond:{msg.id}"
            )

        builder.button(
            text="🚩 Marcar para revisión",
            callback_data=f"admin:midivan:flag:{msg.id}"
        )

        builder.button(text="📬 Ver Lista", callback_data="admin:midivan:messages")
        builder.button(text="← Volver", callback_data="admin:midivan")

        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error viewing message detail: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar mensaje. Intenta nuevamente.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("admin:midivan:respond:"))
async def start_response(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start responding to anonymous message."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        message_id = int(callback.data.split(":")[3])

        # Store message_id in state
        await state.update_data(responding_to_message_id=message_id)
        await state.set_state(RespondMessageStates.writing_response)

        # Get message for context
        from database.midivan_models import AnonymousMessage
        msg = await session.get(AnonymousMessage, message_id)

        text = f"""✍️ **Responder a Mensaje Anónimo**

━━━━━━━━━━━━━━━━━━━━━

**Mensaje del usuario:**
_{msg.message_text[:200]}{'...' if len(msg.message_text) > 200 else ''}_

━━━━━━━━━━━━━━━━━━━━━

**Escribe tu respuesta ahora.**

El usuario recibirá tu respuesta de forma anónima en Mi Diván.

💡 Consejos:
• Sé empática y auténtica
• Usa tu voz personal (Diana)
• El mensaje se enviará tal cual lo escribas"""

        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancelar", callback_data="admin:midivan:messages")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting response: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al iniciar respuesta. Intenta nuevamente.",
            show_alert=True
        )


@router.message(RespondMessageStates.writing_response)
async def save_response(message: Message, session: AsyncSession, state: FSMContext):
    """Save Diana's response to anonymous message."""
    user_id = message.from_user.id

    if not await is_admin(user_id, session):
        await message.answer("⛔ Acceso denegado.")
        return

    try:
        # Get message_id from state
        data = await state.get_data()
        message_id = data.get("responding_to_message_id")

        if not message_id:
            await message.answer("❌ Error: No se encontró el mensaje a responder.")
            await state.clear()
            return

        response_text = message.text

        if not response_text or len(response_text) < 10:
            await message.answer("⚠️ La respuesta es muy corta. Escribe al menos 10 caracteres.")
            return

        # Save response
        midivan_service = MiDivanService(session)
        success = await midivan_service.respond_to_message(message_id, response_text)

        if success:
            # Get message to get user_id for notification
            from database.midivan_models import AnonymousMessage
            msg = await session.get(AnonymousMessage, message_id)

            text = f"""✅ **Respuesta Enviada**

━━━━━━━━━━━━━━━━━━━━━

Tu respuesta ha sido guardada y el usuario será notificado.

**Tu respuesta:**
_{response_text[:200]}{'...' if len(response_text) > 200 else ''}_

━━━━━━━━━━━━━━━━━━━━━

El usuario verá tu respuesta la próxima vez que visite Mi Diván."""

            builder = InlineKeyboardBuilder()
            builder.button(text="📬 Ver Mensajes", callback_data="admin:midivan:messages")
            builder.button(text="← Panel Mi Diván", callback_data="admin:midivan")
            builder.adjust(1)

            await message.answer(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )

            # TODO: Send notification to user about new response
            # This would require access to bot instance

            logger.info(f"Admin {user_id} responded to message {message_id}")

        else:
            await message.answer("❌ Error al guardar la respuesta. Intenta nuevamente.")

        await state.clear()

    except Exception as e:
        logger.error(f"Error saving response: {e}", exc_info=True)
        await message.answer("❌ Error al guardar respuesta. Intenta nuevamente.")
        await state.clear()


@router.callback_query(F.data == "admin:midivan:message_stats")
async def show_message_stats(callback: CallbackQuery, session: AsyncSession):
    """Show statistics for anonymous messages."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        from sqlalchemy import select, func
        from database.midivan_models import AnonymousMessage

        # Total messages
        stmt = select(func.count(AnonymousMessage.id))
        result = await session.execute(stmt)
        total = result.scalar() or 0

        # Responded
        stmt = select(func.count(AnonymousMessage.id)).where(AnonymousMessage.is_responded == True)
        result = await session.execute(stmt)
        responded = result.scalar() or 0

        # Pending
        pending = total - responded

        # Average response time (in hours)
        stmt = select(
            func.avg(
                func.extract('epoch', AnonymousMessage.responded_at - AnonymousMessage.sent_at) / 3600
            )
        ).where(AnonymousMessage.is_responded == True)
        result = await session.execute(stmt)
        avg_response_time = result.scalar() or 0

        # Messages today
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(AnonymousMessage.id)).where(
            AnonymousMessage.sent_at >= today_start
        )
        result = await session.execute(stmt)
        today_count = result.scalar() or 0

        response_rate = (responded / total * 100) if total > 0 else 0

        text = f"""📊 **Estadísticas de Mensajes Anónimos**

━━━━━━━━━━━━━━━━━━━━━

**📬 Mensajes Totales:** {total}
**✅ Respondidos:** {responded} ({response_rate:.1f}%)
**⏳ Pendientes:** {pending}

**📅 Hoy:** {today_count} mensajes nuevos

**⏱️ Tiempo de Respuesta:**
Promedio: {avg_response_time:.1f} horas

━━━━━━━━━━━━━━━━━━━━━

**Engagement VIP**
Los mensajes anónimos son una de las features más populares de Mi Diván."""

        builder = InlineKeyboardBuilder()
        builder.button(text="📬 Ver Mensajes", callback_data="admin:midivan:messages")
        builder.button(text="← Volver", callback_data="admin:midivan")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing message stats: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar estadísticas. Intenta nuevamente.",
            show_alert=True
        )


# ==================== QUIZ MANAGEMENT ====================

@router.callback_query(F.data == "admin:midivan:quizzes")
async def manage_quizzes(callback: CallbackQuery, session: AsyncSession):
    """Manage compatibility quizzes."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        from sqlalchemy import select
        from database.midivan_models import CompatibilityQuiz, QuizAttempt

        # Get all quizzes
        stmt = select(CompatibilityQuiz).order_by(CompatibilityQuiz.created_at.desc())
        result = await session.execute(stmt)
        quizzes = result.scalars().all()

        if not quizzes:
            text = """💘 **Gestión de Quizzes**

━━━━━━━━━━━━━━━━━━━━━

No hay quizzes creados todavía.

Usa el botón de abajo para crear el primer quiz."""

            builder = InlineKeyboardBuilder()
            builder.button(text="➕ Crear Nuevo Quiz", callback_data="admin:midivan:create_quiz")
            builder.button(text="← Volver", callback_data="admin:midivan")
            builder.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Build quiz list
        message_parts = [
            "💘 **Gestión de Quizzes**",
            "",
            "━━━━━━━━━━━━━━━━━━━━━"
        ]

        for quiz in quizzes:
            # Get attempt count
            stmt = select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz.id)
            result = await session.execute(stmt)
            attempt_count = result.scalar() or 0

            status = "✅ Activo" if quiz.is_active else "⏸️ Pausado"
            message_parts.extend([
                "",
                f"**{quiz.title}**",
                f"• Estado: {status}",
                f"• Preguntas: {quiz.total_questions}",
                f"• Intentos: {attempt_count}",
                f"• Recompensa: {quiz.besitos_reward} besitos"
            ])

        message_parts.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            "Selecciona una acción:"
        ])

        text = "\n".join(message_parts)

        builder = InlineKeyboardBuilder()

        # Quiz actions
        for quiz in quizzes[:3]:  # Max 3 quizzes
            action_text = "⏸️ Pausar" if quiz.is_active else "▶️ Activar"
            builder.button(
                text=f"{action_text} - {quiz.title[:20]}...",
                callback_data=f"admin:midivan:toggle:{quiz.id}"
            )

        builder.button(text="📊 Ver Estadísticas", callback_data="admin:midivan:quiz_stats")
        builder.button(text="← Volver", callback_data="admin:midivan")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error managing quizzes: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar quizzes. Intenta nuevamente.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("admin:midivan:toggle:"))
async def toggle_quiz_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle quiz active status."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        quiz_id = int(callback.data.split(":")[3])

        from database.midivan_models import CompatibilityQuiz
        quiz = await session.get(CompatibilityQuiz, quiz_id)

        if not quiz:
            await callback.answer("❌ Quiz no encontrado.", show_alert=True)
            return

        # Toggle status
        quiz.is_active = not quiz.is_active
        await session.commit()

        status_text = "activado" if quiz.is_active else "pausado"
        await callback.answer(f"✅ Quiz {status_text} exitosamente.", show_alert=True)

        # Refresh list
        await manage_quizzes(callback, session)

    except Exception as e:
        logger.error(f"Error toggling quiz: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cambiar estado. Intenta nuevamente.",
            show_alert=True
        )


@router.callback_query(F.data == "admin:midivan:quiz_stats")
async def show_quiz_stats(callback: CallbackQuery, session: AsyncSession):
    """Show quiz statistics."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        from sqlalchemy import select, func
        from database.midivan_models import CompatibilityQuiz, QuizAttempt

        # Total attempts
        stmt = select(func.count(QuizAttempt.id))
        result = await session.execute(stmt)
        total_attempts = result.scalar() or 0

        # Completed attempts
        stmt = select(func.count(QuizAttempt.id)).where(QuizAttempt.is_completed == True)
        result = await session.execute(stmt)
        completed = result.scalar() or 0

        # Completion rate
        completion_rate = (completed / total_attempts * 100) if total_attempts > 0 else 0

        # Average score
        stmt = select(func.avg(QuizAttempt.total_score)).where(QuizAttempt.is_completed == True)
        result = await session.execute(stmt)
        avg_score = result.scalar() or 0

        # Compatibility level distribution
        stmt = select(
            QuizAttempt.compatibility_level,
            func.count(QuizAttempt.id)
        ).where(
            QuizAttempt.is_completed == True
        ).group_by(QuizAttempt.compatibility_level)
        result = await session.execute(stmt)
        level_distribution = dict(result.all())

        # Attempts today
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(QuizAttempt.id)).where(
            QuizAttempt.started_at >= today_start
        )
        result = await session.execute(stmt)
        today_attempts = result.scalar() or 0

        text = f"""📊 **Estadísticas de Quizzes de Compatibilidad**

━━━━━━━━━━━━━━━━━━━━━

**📈 Intentos Totales:** {total_attempts}
**✅ Completados:** {completed} ({completion_rate:.1f}%)
**⏳ En Progreso:** {total_attempts - completed}

**📅 Hoy:** {today_attempts} intentos

**🎯 Puntuación Promedio:** {avg_score:.1f}%

━━━━━━━━━━━━━━━━━━━━━

**💘 Niveles de Compatibilidad:**"""

        # Add distribution
        if level_distribution:
            for level, count in level_distribution.items():
                text += f"\n• {level or 'Sin nivel'}: {count} usuarios"
        else:
            text += "\n_No hay datos disponibles todavía_"

        text += """

━━━━━━━━━━━━━━━━━━━━━

**Engagement VIP**
Los quizzes son una excelente forma de conectar con tus usuarios VIP."""

        builder = InlineKeyboardBuilder()
        builder.button(text="💘 Gestionar Quizzes", callback_data="admin:midivan:quizzes")
        builder.button(text="← Volver", callback_data="admin:midivan")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing quiz stats: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar estadísticas. Intenta nuevamente.",
            show_alert=True
        )


@router.callback_query(F.data == "admin:midivan:create_quiz")
async def create_quiz_info(callback: CallbackQuery, session: AsyncSession):
    """Show information about creating quizzes."""
    user_id = callback.from_user.id

    if not await is_admin(user_id, session):
        await callback.answer("⛔ Acceso denegado.", show_alert=True)
        return

    try:
        text = """💘 **Crear Nuevo Quiz de Compatibilidad**

━━━━━━━━━━━━━━━━━━━━━

**📋 Cómo Crear un Quiz**

Tienes 2 opciones para crear quizzes:

**Opción 1 - Wrapper Script (Más Fácil):**
```bash
./crear_quiz.sh
```

**Opción 2 - Directamente con Python:**
```bash
python scripts/create_initial_quiz.py
```

**📝 Estructura del Quiz**

El script te permite definir:
• **Título** del quiz
• **Descripción** atractiva
• **Número de preguntas** (recomendado: 8-12)
• **Categorías**: personality, interests, values
• **Opciones** por pregunta (3-5 opciones)
• **Puntuación** de compatibilidad por opción (0-100)
• **Respuesta de Diana** personalizada por opción
• **Recompensa** en besitos

**🎯 Tips para Buenos Quizzes**

✅ Preguntas que revelen personalidad genuina
✅ Opciones balanceadas (sin respuestas "obviamente correctas")
✅ Respuestas de Diana auténticas y personales
✅ Categorías variadas para análisis completo
✅ Puntuaciones que reflejen compatibilidad real

**💡 Próximas Mejoras**

Estamos trabajando en un creador de quizzes desde el panel admin para facilitar la creación sin necesidad de scripts.

━━━━━━━━━━━━━━━━━━━━━

**¿Necesitas ayuda?**

Consulta el script en:
`scripts/create_initial_quiz.py`

Puedes duplicarlo y modificarlo para crear nuevos quizzes personalizados."""

        builder = InlineKeyboardBuilder()
        builder.button(text="📖 Ver Quiz Actual", callback_data="admin:midivan:quizzes")
        builder.button(text="← Volver", callback_data="admin:midivan")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing create quiz info: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al cargar información. Intenta nuevamente.",
            show_alert=True
        )
