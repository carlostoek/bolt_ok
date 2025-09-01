"""
Teclados para el sistema de narrativa inmersiva.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_unified import NarrativeFragment

async def get_narrative_keyboard(fragment, session: AsyncSession) -> InlineKeyboardMarkup:
    """Crea el teclado de decisiones para un fragmento narrativo."""
    builder = InlineKeyboardBuilder()
    
    # En el modelo unificado, las opciones están en el campo JSON 'choices'
    choices = fragment.choices or []
    
    # Agregar botones para cada decisión
    for index, choice in enumerate(choices):
        builder.button(
            text=choice.get('text', f'Opción {index + 1}'),
            callback_data=f"narrative_choice:{index}"
        )
    
    # Si no hay decisiones, mostrar botón de continuar o ver historia
    if not choices:
        # En el modelo unificado, la continuación se puede manejar de diferentes formas
        builder.button(
            text="📖 Ver Mi Historia",
            callback_data="narrative_stats"
        )
    
    # Botones de navegación adicionales
    builder.button(
        text="📊 Mi Progreso",
        callback_data="narrative_stats"
    )
    
    builder.button(
        text="❓ Ayuda",
        callback_data="narrative_help"
    )
    
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
