"""
Decision ID constants for the narrative system.

This module centralizes all decision IDs used throughout the narrative system.
Using constants instead of magic numbers improves code readability and maintainability.

Auto-generated from decision_requirements.json on: 2025-10-10
"""


class DecisionID:
    """Centralized decision ID constants for narrative system."""

    # Basic narrative decisions
    DIARY_SECRET = 1
    """📖 Diario Secreto - Requires purchasing the diary from shop"""

    DIARY_INTIMATE = 15
    """📓 Diario Íntimo - Requires purchasing the intimate diary (30 besitos)"""

    # Add more decision IDs here as they are configured
    # Format:
    # DECISION_NAME = id
    # """Description of the decision and requirements"""


class ItemName:
    """Centralized item name constants for shop system."""

    DIARY_SECRET = "📖 Diario Secreto"
    """Secret diary item - unlocks basic narrative content"""

    DIARY_INTIMATE = "📓 Diario Íntimo"
    """Intimate diary item - unlocks exclusive intimate content"""


# Reverse mapping for debugging and logging
DECISION_ID_TO_NAME = {
    DecisionID.DIARY_SECRET: "DIARY_SECRET",
    DecisionID.DIARY_INTIMATE: "DIARY_INTIMATE",
}

DECISION_ID_TO_ITEM = {
    DecisionID.DIARY_SECRET: ItemName.DIARY_SECRET,
    DecisionID.DIARY_INTIMATE: ItemName.DIARY_INTIMATE,
}


def get_decision_name(decision_id: int) -> str:
    """
    Get human-readable name for a decision ID.

    Args:
        decision_id: The numeric decision ID

    Returns:
        Human-readable decision name or "UNKNOWN_DECISION_{id}"
    """
    return DECISION_ID_TO_NAME.get(decision_id, f"UNKNOWN_DECISION_{decision_id}")


def get_required_item(decision_id: int) -> str | None:
    """
    Get the required item name for a decision.

    Args:
        decision_id: The numeric decision ID

    Returns:
        Item name string or None if no item required
    """
    return DECISION_ID_TO_ITEM.get(decision_id)
