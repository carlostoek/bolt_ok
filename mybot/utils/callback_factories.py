"""
Factories para callbacks estructurados en botones inline.
Proporciona una forma tipada y segura de crear y analizar callbacks.
"""

from typing import Optional, ClassVar, Any
from aiogram.filters.callback_data import CallbackData


class MissionCallbackFactory(CallbackData, prefix="mission"):
    """Factory para callbacks relacionados con misiones unificadas."""
    
    action: str  # list, details, complete, narrative_connect
    mission_id: Optional[str] = None
    mission_type: Optional[str] = None
    page: Optional[int] = None


class NarrativeCallbackFactory(CallbackData, prefix="narrative"):
    """Factory para callbacks relacionados con narrativa unificada."""
    
    action: str  # start, continue, choice, stats
    fragment_id: Optional[str] = None
    choice_index: Optional[int] = None
    page: Optional[int] = None