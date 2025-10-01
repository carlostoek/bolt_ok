"""
Teclados para el sistema de narrativa inmersiva.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_models import NarrativeChoice

async def get_narrative_keyboard(fragment, session: AsyncSession, user_id: int = None) -> InlineKeyboardMarkup:
    """Crea el teclado de decisiones para un fragmento narrativo."""
    builder = InlineKeyboardBuilder()

    # Obtener las opciones de decisión para este fragmento
    stmt = select(NarrativeChoice).where(
        NarrativeChoice.source_fragment_id == fragment.id
    ).order_by(NarrativeChoice.id)
    result = await session.execute(stmt)
    choices = result.scalars().all()

    # Agregar botones para cada decisión
    for index, choice in enumerate(choices):
        builder.button(
            text=choice.text,
            callback_data=f"narrative_choice:{index}"
        )

    # Si no hay decisiones, verificar si hay continuación automática
    if not choices:
        if fragment.auto_next_fragment_key:
            builder.button(
                text="➡️ Continuar",
                callback_data="narrative_auto_continue"
            )
        else:
            builder.button(
                text="📖 Ver Mi Historia",
                callback_data="narrative_stats"
            )

    # Fila de navegación: Atrás y Progreso
    nav_row = []

    # Botón "Atrás" si el usuario puede retroceder
    if user_id:
        from services.narrative_service import NarrativeService
        narrative_service = NarrativeService(session)
        can_go_back = await narrative_service.can_go_back(user_id)

        if can_go_back:
            nav_row.append(("⬅️ Atrás", "narrative_go_back"))

    # Botón de progreso
    nav_row.append(("📊 Progreso", "narrative_stats"))

    # Agregar fila de navegación
    for text, callback in nav_row:
        builder.button(text=text, callback_data=callback)

    # Fila de utilidades
    builder.button(text="❓ Ayuda", callback_data="narrative_help")
    builder.button(text="🏠 Menú", callback_data="narrative_main_menu")

    builder.adjust(1)  # Un botón por fila para mejor legibilidad
    return builder.as_markup()

def get_narrative_stats_keyboard() -> InlineKeyboardMarkup:
    """Teclado para las estadísticas narrativas."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📖 Continuar Historia", callback_data="continue_narrative")
    builder.button(text="❓ Ayuda", callback_data="narrative_help")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1)
    return builder.as_markup()

def get_narrative_choice_keyboard(choices: list) -> InlineKeyboardMarkup:
    """Crea teclado específico para decisiones narrativas."""
    builder = InlineKeyboardBuilder()
    
    for index, choice_text in enumerate(choices):
        builder.button(
            text=choice_text,
            callback_data=f"narrative_choice:{index}"
        )
    
    builder.adjust(1)
    return builder.as_markup()
