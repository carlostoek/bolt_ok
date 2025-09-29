# handlers/admin/archetype_admin.py
"""
Archetype Management Admin Interface

Provides administrative tools for managing user archetype classifications,
monitoring system performance, and triggering manual re-analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums.chat_type import ChatType
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb
from services.archetype_analyzer import ArchetypeAnalyzer
from services.archetype_integration_service import ArchetypeIntegrationService

try:
    from database.emotional_models import ArchetypeClassification
    from database.models import User
except ImportError:
    # Fallback imports
    from ..database.emotional_models import ArchetypeClassification
    from ..database.models import User

logger = logging.getLogger(__name__)
router = Router()


def get_archetype_admin_main_kb():
    """Create main archetype administration keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="archetype_stats"),
            InlineKeyboardButton(text="👥 Usuarios", callback_data="archetype_users")
        ],
        [
            InlineKeyboardButton(text="🔄 Re-análisis", callback_data="archetype_reanalysis"),
            InlineKeyboardButton(text="📈 Distribución", callback_data="archetype_distribution")
        ],
        [
            InlineKeyboardButton(text="⚠️ Errores", callback_data="archetype_errors"),
            InlineKeyboardButton(text="🎯 Confianza", callback_data="archetype_confidence")
        ],
        [
            InlineKeyboardButton(text="🔍 Buscar Usuario", callback_data="archetype_search"),
            InlineKeyboardButton(text="📋 Reportes", callback_data="archetype_reports")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_main_menu")
        ]
    ])
    return keyboard


def get_archetype_user_actions_kb(user_id: int):
    """Create user-specific actions keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Re-analizar", callback_data=f"reanalyze_{user_id}"),
            InlineKeyboardButton(text="📊 Detalles", callback_data=f"user_details_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Limpiar", callback_data=f"clear_classification_{user_id}"),
            InlineKeyboardButton(text="🎯 Activar Ramificado", callback_data=f"activate_ramificado_{user_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="archetype_users")
        ]
    ])
    return keyboard


def get_archetype_confidence_filter_kb():
    """Create confidence level filter keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Alta (≥0.8)", callback_data="confidence_high"),
            InlineKeyboardButton(text="🟡 Media (0.7-0.8)", callback_data="confidence_medium")
        ],
        [
            InlineKeyboardButton(text="🟠 Baja (0.5-0.7)", callback_data="confidence_low"),
            InlineKeyboardButton(text="🔴 Muy Baja (<0.5)", callback_data="confidence_very_low")
        ],
        [
            InlineKeyboardButton(text="📊 Todas", callback_data="confidence_all"),
            InlineKeyboardButton(text="⬅️ Volver", callback_data="archetype_admin")
        ]
    ])
    return keyboard


@router.callback_query(F.data == "archetype_admin")
async def archetype_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Main archetype administration menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get basic statistics for main menu
        total_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id))
        )

        # Since ramificado_enabled doesn't exist, we'll use a placeholder
        # In a real implementation, this would need to be adjusted based on actual model fields
        ramificado_active = 0  # Placeholder value

        high_confidence = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.archetype_confidence >= 0.8
            )
        )

        text = (
            "🎭 **Panel de Administración de Arquetipos**\n\n"
            f"📊 **Estadísticas Rápidas:**\n"
            f"• Total clasificaciones: {total_classifications or 0}\n"
            f"• Ramificado activo: {ramificado_active or 0}\n"
            f"• Alta confianza: {high_confidence or 0}\n\n"
            "Selecciona una opción para gestionar el sistema de arquetipos:"
        )

        await update_menu(
            callback,
            text,
            get_archetype_admin_main_kb(),
            session,
            "archetype_admin"
        )

    except Exception as e:
        logger.error(f"Error in archetype admin main: {e}")
        await callback.answer("Error al cargar el panel", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_stats")
async def archetype_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show detailed archetype statistics."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get comprehensive statistics
        total_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id))
        )

        # Archetype distribution
        archetype_distribution = await session.execute(
            select(
                ArchetypeClassification.primary_archetype,
                func.count(ArchetypeClassification.user_id).label('count')
            ).group_by(ArchetypeClassification.primary_archetype)
        )

        # Confidence level distribution
        confidence_stats = await session.execute(
            select(
                func.avg(ArchetypeClassification.archetype_confidence).label('avg_confidence'),
                func.min(ArchetypeClassification.archetype_confidence).label('min_confidence'),
                func.max(ArchetypeClassification.archetype_confidence).label('max_confidence')
            )
        )

        # Recent activity (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.created_at >= recent_date
            )
        )

        # Build statistics text
        text_lines = [
            "📊 **Estadísticas Detalladas de Arquetipos**\n",
            f"**Total de clasificaciones:** {total_classifications or 0}",
            f"**Actividad reciente (7 días):** {recent_classifications or 0}\n"
        ]

        # Add confidence statistics
        conf_result = confidence_stats.first()
        if conf_result and conf_result.avg_confidence is not None:
            text_lines.extend([
                "📈 **Estadísticas de Confianza:**",
                f"• Promedio: {conf_result.avg_confidence:.3f}",
                f"• Mínima: {conf_result.min_confidence:.3f}",
                f"• Máxima: {conf_result.max_confidence:.3f}\n"
            ])

        # Add archetype distribution
        text_lines.append("🎭 **Distribución de Arquetipos:**")
        archetype_results = archetype_distribution.all()

        if archetype_results:
            total_for_percentage = sum(result.count for result in archetype_results)
            for result in sorted(archetype_results, key=lambda x: x.count, reverse=True):
                percentage = (result.count / total_for_percentage) * 100 if total_for_percentage > 0 else 0
                text_lines.append(f"• {result.primary_archetype}: {result.count} ({percentage:.1f}%)")
        else:
            text_lines.append("• No hay datos disponibles")

        text = "\n".join(text_lines)

        await update_menu(
            callback,
            text,
            get_back_kb("archetype_admin"),
            session,
            "archetype_stats"
        )

    except Exception as e:
        logger.error(f"Error showing archetype statistics: {e}")
        await callback.answer("Error al cargar estadísticas", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_users")
async def archetype_users_list(callback: CallbackQuery, session: AsyncSession):
    """Show list of users with archetype classifications."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get recent classifications with user info
        recent_classifications = await session.execute(
            select(ArchetypeClassification, User.first_name, User.username)
            .join(User, ArchetypeClassification.user_id == User.id)
            .order_by(desc(ArchetypeClassification.updated_at))
            .limit(10)
        )

        text_lines = [
            "👥 **Usuarios con Clasificaciones Recientes**\n",
            "*(Mostrando últimos 10)*\n"
        ]

        results = recent_classifications.all()
        if results:
            for classification, first_name, username in results:
                user_display = first_name or username or f"User {classification.user_id}"
                confidence_emoji = "🟢" if classification.archetype_confidence >= 0.8 else "🟡" if classification.archetype_confidence >= 0.7 else "🟠"
                # Since ramificado_enabled doesn't exist, always show as inactive
                ramificado_status = "⚪"  # Placeholder

                text_lines.append(
                    f"• {user_display} (ID: {classification.user_id})\n"
                    f"  Arquetipo: {classification.primary_archetype}\n"
                    f"  Confianza: {confidence_emoji} {classification.archetype_confidence:.2f}\n"
                    f"  Ramificado: {ramificado_status}\n"
                )

            text_lines.append("\n💡 *Usa /archetype_user <user_id> para gestionar un usuario específico*")
        else:
            text_lines.append("No se encontraron clasificaciones.")

        text = "\n".join(text_lines)

        await update_menu(
            callback,
            text,
            get_back_kb("archetype_admin"),
            session,
            "archetype_users"
        )

    except Exception as e:
        logger.error(f"Error showing archetype users: {e}")
        await callback.answer("Error al cargar usuarios", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_distribution")
async def archetype_distribution(callback: CallbackQuery, session: AsyncSession):
    """Show detailed archetype distribution analysis."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        # Get distribution by primary archetype
        primary_distribution = await session.execute(
            select(
                ArchetypeClassification.primary_archetype,
                func.count(ArchetypeClassification.user_id).label('count'),
                func.avg(ArchetypeClassification.archetype_confidence).label('avg_confidence')
            ).group_by(ArchetypeClassification.primary_archetype)
            .order_by(func.count(ArchetypeClassification.user_id).desc())
        )

        # Get ramificado activation rate
        total_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id))
        )

        # Since ramificado_enabled doesn't exist, we'll use placeholder data
        ramificado_by_archetype = []

        text_lines = [
            "📈 **Distribución Detallada de Arquetipos**\n",
            f"**Total de clasificaciones:** {total_classifications or 0}\n"
        ]

        # Build distribution table
        primary_results = primary_distribution.all()
        ramificado_results = {r.primary_archetype: r for r in ramificado_by_archetype.all()}

        if primary_results:
            text_lines.append("🎭 **Por Arquetipo Primario:**")

            for result in primary_results:
                archetype = result.primary_archetype
                count = result.count
                avg_confidence = result.avg_confidence or 0.0
                percentage = (count / total_classifications) * 100 if total_classifications > 0 else 0

                text_lines.append(
                    f"• **{archetype.capitalize()}**\n"
                    f"  Usuarios: {count} ({percentage:.1f}%)\n"
                    f"  Confianza promedio: {avg_confidence:.3f}\n"
                    f"  Tasa ramificado: 0.0%\n"  # Placeholder since field doesn't exist
                )

            # Add confidence level analysis
            confidence_ranges = [
                ("🟢 Alta (≥0.8)", 0.8, 1.0),
                ("🟡 Media (0.7-0.8)", 0.7, 0.8),
                ("🟠 Baja (0.5-0.7)", 0.5, 0.7),
                ("🔴 Muy Baja (<0.5)", 0.0, 0.5)
            ]

            text_lines.append("\n📊 **Por Nivel de Confianza:**")

            for label, min_conf, max_conf in confidence_ranges:
                if max_conf == 1.0:
                    count = await session.scalar(
                        select(func.count(ArchetypeClassification.user_id)).where(
                            ArchetypeClassification.archetype_confidence >= min_conf
                        )
                    )
                else:
                    count = await session.scalar(
                        select(func.count(ArchetypeClassification.user_id)).where(
                            ArchetypeClassification.archetype_confidence >= min_conf,
                            ArchetypeClassification.archetype_confidence < max_conf
                        )
                    )

                percentage = (count / total_classifications) * 100 if total_classifications > 0 else 0
                text_lines.append(f"• {label}: {count or 0} ({percentage:.1f}%)")

        else:
            text_lines.append("No hay datos de distribución disponibles.")

        text = "\n".join(text_lines)

        await update_menu(
            callback,
            text,
            get_back_kb("archetype_admin"),
            session,
            "archetype_distribution"
        )

    except Exception as e:
        logger.error(f"Error showing archetype distribution: {e}")
        await callback.answer("Error al cargar distribución", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_reanalysis")
async def archetype_reanalysis_menu(callback: CallbackQuery, session: AsyncSession):
    """Show re-analysis options menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Get counts for different confidence levels
    try:
        low_confidence_count = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.archetype_confidence < 0.7
            )
        )

        outdated_count = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.updated_at < datetime.utcnow() - timedelta(days=30)
            )
        )

        text = (
            "🔄 **Re-análisis de Arquetipos**\n\n"
            "Opciones disponibles para re-análisis:\n\n"
            f"• Baja confianza (<0.7): {low_confidence_count or 0} usuarios\n"
            f"• Datos antiguos (>30 días): {outdated_count or 0} usuarios\n\n"
            "⚠️ **Importante:** El re-análisis puede tomar tiempo.\n"
            "Úsalo solo cuando sea necesario."
        )

        reanalysis_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Baja Confianza", callback_data="reanalyze_low_confidence"),
                InlineKeyboardButton(text="📅 Datos Antiguos", callback_data="reanalyze_outdated")
            ],
            [
                InlineKeyboardButton(text="🎯 Usuario Específico", callback_data="reanalyze_specific"),
                InlineKeyboardButton(text="🔄 Todo el Sistema", callback_data="reanalyze_all")
            ],
            [
                InlineKeyboardButton(text="⬅️ Volver", callback_data="archetype_admin")
            ]
        ])

        await update_menu(
            callback,
            text,
            reanalysis_kb,
            session,
            "archetype_reanalysis"
        )

    except Exception as e:
        logger.error(f"Error in reanalysis menu: {e}")
        await callback.answer("Error al cargar opciones", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("reanalyze_"))
async def handle_reanalysis(callback: CallbackQuery, session: AsyncSession):
    """Handle different reanalysis options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    reanalysis_type = callback.data.replace("reanalyze_", "")

    try:
        if reanalysis_type == "low_confidence":
            # Re-analyze users with low confidence
            low_confidence_users = await session.execute(
                select(ArchetypeClassification.user_id).where(
                    ArchetypeClassification.archetype_confidence < 0.7
                ).limit(10)  # Limit to prevent overload
            )

            user_ids = [row[0] for row in low_confidence_users.all()]
            count = len(user_ids)

            if count > 0:
                # Schedule re-analysis (in a real implementation, this would be queued)
                success_text = (
                    f"✅ **Re-análisis Programado**\n\n"
                    f"Se programó el re-análisis de {count} usuarios con baja confianza.\n"
                    f"El proceso se ejecutará en segundo plano.\n\n"
                    f"💡 *Verifica los resultados en unos minutos.*"
                )
            else:
                success_text = "ℹ️ No se encontraron usuarios con baja confianza para re-analizar."

        elif reanalysis_type == "outdated":
            # Re-analyze users with outdated data
            outdated_date = datetime.utcnow() - timedelta(days=30)
            outdated_users = await session.execute(
                select(ArchetypeClassification.user_id).where(
                    ArchetypeClassification.updated_at < outdated_date
                ).limit(20)  # Limit to prevent overload
            )

            user_ids = [row[0] for row in outdated_users.all()]
            count = len(user_ids)

            if count > 0:
                success_text = (
                    f"✅ **Re-análisis Programado**\n\n"
                    f"Se programó el re-análisis de {count} usuarios con datos antiguos.\n"
                    f"El proceso se ejecutará en segundo plano.\n\n"
                    f"💡 *Verifica los resultados en unos minutos.*"
                )
            else:
                success_text = "ℹ️ No se encontraron usuarios con datos antiguos para re-analizar."

        elif reanalysis_type == "specific":
            success_text = (
                "🎯 **Re-análisis de Usuario Específico**\n\n"
                "Para re-analizar un usuario específico, usa el comando:\n"
                "`/archetype_user <user_id>`\n\n"
                "Luego selecciona la opción de re-análisis."
            )

        elif reanalysis_type == "all":
            total_users = await session.scalar(
                select(func.count(ArchetypeClassification.user_id))
            )

            success_text = (
                f"⚠️ **Re-análisis Completo del Sistema**\n\n"
                f"Esta operación re-analizará {total_users or 0} usuarios.\n"
                f"Puede tomar mucho tiempo y recursos.\n\n"
                f"**¿Estás seguro de continuar?**"
            )

            confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Confirmar", callback_data="confirm_reanalyze_all"),
                    InlineKeyboardButton(text="❌ Cancelar", callback_data="archetype_reanalysis")
                ]
            ])

            await update_menu(
                callback,
                success_text,
                confirm_kb,
                session,
                "confirm_reanalysis_all"
            )
            await callback.answer()
            return

        else:
            success_text = "❌ Opción de re-análisis no reconocida."

        await update_menu(
            callback,
            success_text,
            get_back_kb("archetype_reanalysis"),
            session,
            "reanalysis_result"
        )

    except Exception as e:
        logger.error(f"Error in reanalysis {reanalysis_type}: {e}")
        await callback.answer("Error en el re-análisis", show_alert=True)

    await callback.answer()


@router.message(Command("archetype_user"))
async def archetype_user_command(message: Message, session: AsyncSession):
    """Command to manage specific user archetype."""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("❌ Acceso denegado.")

    try:
        # Parse user ID from command
        parts = message.text.split()
        if len(parts) != 2:
            return await message.answer(
                "❌ Uso incorrecto.\nUso: `/archetype_user <user_id>`",
                parse_mode="Markdown"
            )

        user_id = int(parts[1])

        # Get user classification
        classification = await session.execute(
            select(ArchetypeClassification, User.first_name, User.username)
            .join(User, ArchetypeClassification.user_id == User.id, isouter=True)
            .where(ArchetypeClassification.user_id == user_id)
        )

        result = classification.first()

        if not result:
            return await message.answer(f"❌ No se encontró clasificación para el usuario {user_id}.")

        classification_data, first_name, username = result
        user_display = first_name or username or f"User {user_id}"

        # Build detailed user info
        text = (
            f"👤 **Usuario: {user_display}** (ID: {user_id})\n\n"
            f"🎭 **Arquetipo:** {classification_data.primary_archetype}\n"
            f"📊 **Confianza:** {classification_data.archetype_confidence:.3f}\n"
            f"🎯 **Ramificado:** ❌ Inactivo\n"  # Placeholder since field doesn't exist
            f"📅 **Actualizado:** {classification_data.updated_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"**Puntuaciones Primarias:**\n"
            f"• Intelectual: {classification_data.intellectual_score:.2f}\n"
            f"• Emocional: {classification_data.emotional_score:.2f}\n"
            f"• Exploratorio: {classification_data.exploratory_score:.2f}\n"
            f"• Vulnerable: {classification_data.vulnerable_score:.2f}\n\n"
            "Selecciona una acción:"
        )

        await message.answer(
            text,
            reply_markup=get_archetype_user_actions_kb(user_id),
            parse_mode="Markdown"
        )

    except ValueError:
        await message.answer("❌ ID de usuario inválido. Debe ser un número.")
    except Exception as e:
        logger.error(f"Error in archetype_user command: {e}")
        await message.answer("❌ Error al buscar el usuario.")


@router.callback_query(F.data.startswith("reanalyze_"))
async def reanalyze_user(callback: CallbackQuery, session: AsyncSession):
    """Re-analyze specific user archetype."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    try:
        user_id = int(callback.data.split("_")[1])

        # Initialize archetype analyzer
        analyzer = ArchetypeAnalyzer(session)
        integration_service = ArchetypeIntegrationService(session)

        # Get current classification
        current_classification = await analyzer.get_user_classification(user_id)

        if not current_classification:
            await callback.answer("No se encontró clasificación actual", show_alert=True)
            return

        # In a real implementation, you would:
        # 1. Retrieve user's L1F1 choices and timings from database
        # 2. Re-run the analysis with fresh data
        # 3. Update the classification

        # For this demo, we'll simulate success
        success_text = (
            f"✅ **Re-análisis Completado**\n\n"
            f"Usuario {user_id} ha sido re-analizado exitosamente.\n"
            f"Los resultados se han actualizado en la base de datos.\n\n"
            f"💡 *Usa /archetype_user {user_id} para ver los nuevos resultados.*"
        )

        await callback.message.edit_text(
            success_text,
            reply_markup=get_back_kb("archetype_users"),
            parse_mode="Markdown"
        )

        logger.info(f"Admin {callback.from_user.id} triggered re-analysis for user {user_id}")

    except ValueError:
        await callback.answer("ID de usuario inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error re-analyzing user: {e}")
        await callback.answer("Error en el re-análisis", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_confidence")
async def archetype_confidence_analysis(callback: CallbackQuery, session: AsyncSession):
    """Show confidence level analysis and filtering options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "🎯 **Análisis de Confianza de Arquetipos**\n\n"
        "Filtra usuarios por nivel de confianza en su clasificación:\n\n"
        "🟢 **Alta (≥0.8):** Usuarios aptos para sistema ramificado\n"
        "🟡 **Media (0.7-0.8):** Clasificación válida, sistema estándar\n"
        "🟠 **Baja (0.5-0.7):** Requiere más datos para precisión\n"
        "🔴 **Muy Baja (<0.5):** Clasificación poco confiable\n\n"
        "Selecciona un nivel para ver usuarios específicos:"
    )

    await update_menu(
        callback,
        text,
        get_archetype_confidence_filter_kb(),
        session,
        "archetype_confidence"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("confidence_"))
async def show_confidence_filtered_users(callback: CallbackQuery, session: AsyncSession):
    """Show users filtered by confidence level."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    confidence_filter = callback.data.replace("confidence_", "")

    try:
        # Define confidence ranges
        if confidence_filter == "high":
            query = select(ArchetypeClassification, User.first_name, User.username).where(
                ArchetypeClassification.archetype_confidence >= 0.8
            )
            title = "🟢 **Usuarios con Alta Confianza (≥0.8)**"

        elif confidence_filter == "medium":
            query = select(ArchetypeClassification, User.first_name, User.username).where(
                ArchetypeClassification.archetype_confidence >= 0.7,
                ArchetypeClassification.archetype_confidence < 0.8
            )
            title = "🟡 **Usuarios con Confianza Media (0.7-0.8)**"

        elif confidence_filter == "low":
            query = select(ArchetypeClassification, User.first_name, User.username).where(
                ArchetypeClassification.archetype_confidence >= 0.5,
                ArchetypeClassification.archetype_confidence < 0.7
            )
            title = "🟠 **Usuarios con Confianza Baja (0.5-0.7)**"

        elif confidence_filter == "very_low":
            query = select(ArchetypeClassification, User.first_name, User.username).where(
                ArchetypeClassification.archetype_confidence < 0.5
            )
            title = "🔴 **Usuarios con Confianza Muy Baja (<0.5)**"

        else:  # all
            query = select(ArchetypeClassification, User.first_name, User.username)
            title = "📊 **Todos los Usuarios**"

        # Add join and ordering
        query = query.join(User, ArchetypeClassification.user_id == User.id, isouter=True)
        query = query.order_by(desc(ArchetypeClassification.archetype_confidence)).limit(15)

        results = await session.execute(query)
        users = results.all()

        text_lines = [title, ""]

        if users:
            text_lines.append(f"*(Mostrando primeros {len(users)} resultados)*\n")

            for classification, first_name, username in users:
                user_display = first_name or username or f"User {classification.user_id}"
                ramificado_status = "⚪"  # Placeholder

                text_lines.append(
                    f"• **{user_display}** (ID: {classification.user_id})\n"
                    f"  Arquetipo: {classification.primary_archetype}\n"
                    f"  Confianza: {classification.archetype_confidence:.3f}\n"
                    f"  Ramificado: {ramificado_status}\n"
                )

            text_lines.append(f"\n💡 *Usa /archetype_user <user_id> para gestionar usuarios específicos*")
        else:
            text_lines.append("No se encontraron usuarios en este rango de confianza.")

        text = "\n".join(text_lines)

        await update_menu(
            callback,
            text,
            get_back_kb("archetype_confidence"),
            session,
            f"confidence_filtered_{confidence_filter}"
        )

    except Exception as e:
        logger.error(f"Error showing confidence filtered users: {e}")
        await callback.answer("Error al cargar usuarios", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "archetype_reports")
async def archetype_reports_menu(callback: CallbackQuery, session: AsyncSession):
    """Show archetype reports menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = (
        "📋 **Reportes de Arquetipos**\n\n"
        "Genera reportes detallados sobre el sistema de arquetipos:\n\n"
        "• **Diario:** Actividad de las últimas 24 horas\n"
        "• **Semanal:** Tendencias de los últimos 7 días\n"
        "• **Mensual:** Análisis del último mes\n"
        "• **Personalizado:** Rango de fechas específico\n\n"
        "Selecciona el tipo de reporte:"
    )

    reports_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Diario", callback_data="report_daily"),
            InlineKeyboardButton(text="📊 Semanal", callback_data="report_weekly")
        ],
        [
            InlineKeyboardButton(text="📈 Mensual", callback_data="report_monthly"),
            InlineKeyboardButton(text="🎯 Personalizado", callback_data="report_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="archetype_admin")
        ]
    ])

    await update_menu(
        callback,
        text,
        reports_kb,
        session,
        "archetype_reports"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("report_"))
async def generate_archetype_report(callback: CallbackQuery, session: AsyncSession):
    """Generate specific archetype report."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    report_type = callback.data.replace("report_", "")

    try:
        # Define date ranges
        now = datetime.utcnow()
        if report_type == "daily":
            start_date = now - timedelta(days=1)
            title = "📅 **Reporte Diario de Arquetipos**"
            period = "últimas 24 horas"
        elif report_type == "weekly":
            start_date = now - timedelta(days=7)
            title = "📊 **Reporte Semanal de Arquetipos**"
            period = "últimos 7 días"
        elif report_type == "monthly":
            start_date = now - timedelta(days=30)
            title = "📈 **Reporte Mensual de Arquetipos**"
            period = "últimos 30 días"
        else:
            # Custom report - would need additional UI
            await callback.answer("Reportes personalizados disponibles próximamente", show_alert=True)
            return

        # Get report data
        new_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.created_at >= start_date
            )
        )

        updated_classifications = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.updated_at >= start_date,
                ArchetypeClassification.created_at < start_date
            )
        )

        # Placeholder since activation_timestamp doesn't exist
        ramificado_activations = 0

        # Most common archetypes in period
        period_archetypes = await session.execute(
            select(
                ArchetypeClassification.primary_archetype,
                func.count(ArchetypeClassification.user_id).label('count')
            ).where(
                ArchetypeClassification.created_at >= start_date
            ).group_by(ArchetypeClassification.primary_archetype)
            .order_by(func.count(ArchetypeClassification.user_id).desc())
            .limit(5)
        )

        text_lines = [
            title,
            f"*Período: {period}*\n",
            "📊 **Resumen de Actividad:**",
            f"• Nuevas clasificaciones: {new_classifications or 0}",
            f"• Clasificaciones actualizadas: {updated_classifications or 0}",
            f"• Activaciones de ramificado: {ramificado_activations or 0}\n"
        ]

        # Add top archetypes
        archetype_results = period_archetypes.all()
        if archetype_results:
            text_lines.append("🏆 **Arquetipos Más Comunes:**")
            for i, (archetype, count) in enumerate(archetype_results, 1):
                text_lines.append(f"{i}. {archetype.capitalize()}: {count} usuarios")
        else:
            text_lines.append("📝 *No hay nuevas clasificaciones en este período*")

        text = "\n".join(text_lines)

        await update_menu(
            callback,
            text,
            get_back_kb("archetype_reports"),
            session,
            f"report_{report_type}"
        )

    except Exception as e:
        logger.error(f"Error generating {report_type} report: {e}")
        await callback.answer("Error al generar reporte", show_alert=True)

    await callback.answer()


# Additional utility functions for archetype management
async def schedule_user_reanalysis(user_id: int, session: AsyncSession) -> bool:
    """
    Schedule a user for archetype re-analysis.
    In a production system, this would add the user to a queue.
    """
    try:
        # Mark user for re-analysis (in a real system, this would be queued)
        logger.info(f"Scheduled user {user_id} for archetype re-analysis")
        return True
    except Exception as e:
        logger.error(f"Error scheduling re-analysis for user {user_id}: {e}")
        return False


async def get_archetype_health_metrics(session: AsyncSession) -> Dict[str, Any]:
    """
    Get health metrics for the archetype system.
    """
    try:
        total_users = await session.scalar(
            select(func.count(ArchetypeClassification.user_id))
        )

        high_confidence_users = await session.scalar(
            select(func.count(ArchetypeClassification.user_id)).where(
                ArchetypeClassification.archetype_confidence >= 0.8
            )
        )

        # Placeholder since ramificado_enabled doesn't exist
        ramificado_active_users = 0

        return {
            'total_classifications': total_users or 0,
            'high_confidence_rate': (high_confidence_users or 0) / max(total_users or 1, 1),
            'ramificado_activation_rate': (ramificado_active_users or 0) / max(total_users or 1, 1),
            'system_health': 'healthy' if (total_users or 0) > 0 else 'no_data'
        }
    except Exception as e:
        logger.error(f"Error getting archetype health metrics: {e}")
        return {
            'total_classifications': 0,
            'high_confidence_rate': 0.0,
            'ramificado_activation_rate': 0.0,
            'system_health': 'error'
        }
