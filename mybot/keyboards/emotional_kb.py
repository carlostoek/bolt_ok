"""
Keyboards for emotional system integration.
Provides keyboards for emotional state visualization and interaction.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_emotional_status_keyboard(character_name: str) -> InlineKeyboardMarkup:
    """
    Keyboard for the emotional status view.
    
    Args:
        character_name: Name of the character (Diana or Lucien)
    
    Returns:
        InlineKeyboardMarkup with emotional status options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="Ver Relación", 
                callback_data=f"emotional_relationship:{character_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Historial Emocional", 
                callback_data=f"emotional_history:{character_name}"
            )
        ]
    ]
    
    # Add buttons to switch between characters
    other_character = "Lucien" if character_name == "Diana" else "Diana"
    keyboard.append([
        InlineKeyboardButton(
            text=f"Ver {other_character}", 
            callback_data=f"emotional_switch:{other_character}"
        )
    ])
    
    # Add button to continue story if available
    keyboard.append([
        InlineKeyboardButton(
            text="Continuar Historia", 
            callback_data="continue_narrative"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_character_relationship_keyboard(character_name: str) -> InlineKeyboardMarkup:
    """
    Keyboard for the character relationship view.
    
    Args:
        character_name: Name of the character (Diana or Lucien)
    
    Returns:
        InlineKeyboardMarkup with relationship options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="Ver Estado Emocional", 
                callback_data="emotional_back_to_status"
            )
        ],
        [
            InlineKeyboardButton(
                text="Historial Emocional", 
                callback_data=f"emotional_history:{character_name}"
            )
        ]
    ]
    
    # Add buttons to switch between characters
    other_character = "Lucien" if character_name == "Diana" else "Diana"
    keyboard.append([
        InlineKeyboardButton(
            text=f"Ver {other_character}", 
            callback_data=f"emotional_relationship:{other_character}"
        )
    ])
    
    # Add button to continue story if available
    keyboard.append([
        InlineKeyboardButton(
            text="Continuar Historia", 
            callback_data="continue_narrative"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_enhanced_narrative_keyboard(fragment, emotional_context, session=None) -> InlineKeyboardMarkup:
    """
    Enhanced narrative keyboard that includes emotional indicators.
    
    Args:
        fragment: The narrative fragment
        emotional_context: Emotional context data
        session: Optional database session
        
    Returns:
        InlineKeyboardMarkup with choices and emotional indicators
    """
    from keyboards.narrative_kb import get_narrative_keyboard
    
    # First get the base narrative keyboard
    # We'll modify this implementation when integrating with the narrative system
    keyboard = []
    
    # Add choices with emotional indicators
    if hasattr(fragment, 'choices') and fragment.choices:
        for choice in fragment.choices:
            # Format choice text with emotional indicator if available
            choice_text = choice.text
            
            # In a real implementation, we would check emotional impact
            # and add indicators, but for now just use the base text
            keyboard.append([
                InlineKeyboardButton(
                    text=choice_text,
                    callback_data=f"narrative_choice:{choice.id}"
                )
            ])
    
    # Add auto-continue button if applicable
    if hasattr(fragment, 'auto_next_fragment_key') and fragment.auto_next_fragment_key:
        keyboard.append([
            InlineKeyboardButton(
                text="Continuar...",
                callback_data="narrative_auto_continue"
            )
        ])
    
    # Add emotional status button
    keyboard.append([
        InlineKeyboardButton(
            text=f"Estado Emocional de {fragment.character}",
            callback_data=f"emotional_status:{fragment.character}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_emotional_history_keyboard(character_name: str) -> InlineKeyboardMarkup:
    """
    Keyboard for emotional history view.
    
    Args:
        character_name: Name of the character
        
    Returns:
        InlineKeyboardMarkup with history options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="Volver a Relación", 
                callback_data=f"emotional_relationship:{character_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Ver Estado Actual", 
                callback_data="emotional_back_to_status"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)