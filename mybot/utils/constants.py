"""
Centralized constants to eliminate magic strings throughout the codebase.
"""
from enum import Enum


class UserRole(str, Enum):
    """User role constants."""
    VIP = "vip"
    FREE = "free"


class Archetype(str, Enum):
    """User archetype constants."""
    ADVENTURER = "adventurer"
    ROMANTIC = "romantic"
    EXPLORER = "explorer"
    BALANCED = "balanced"


class ConditionOperator(str, Enum):
    """Condition operator constants."""
    AND = "AND"
    OR = "OR"


class ConditionType(str, Enum):
    """Condition type constants."""
    LEVEL = "level"
    VIP_STATUS = "vip_status"
    OWNS_ITEM = "owns_item"
    POINTS = "points"
    OWNS_LORE_PIECE = "owns_lore_piece"
    COMPLETED_MISSION = "completed_mission"


class ComparisonOperator(str, Enum):
    """Comparison operator constants."""
    GREATER_EQUAL = ">="
    GREATER = ">"
    EQUAL = "=="
    LESS_EQUAL = "<="
    LESS = "<"


class ContentType(str, Enum):
    """Content type constants."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MissionType(str, Enum):
    """Mission type constants."""
    REACTION = "reaction"
    MESSAGES = "messages"
    LOGIN_STREAK = "login_streak"
    CUSTOM = "custom"


class CharacterType(str, Enum):
    """Character type constants."""
    DIANA = "Diana"
    LUCIEN = "Lucien"


class LoreCategory(str, Enum):
    """Lore piece category constants."""
    FRAGMENTOS = "fragmentos"
    MEMORIAS = "memorias"
    SECRETOS = "secretos"
    LLAVES = "llaves"


class NarrativeAction(str, Enum):
    """Narrative action constants."""
    TOMAR_DECISION = "tomar_decision"
    ACCEDER_NARRATIVA_VIP = "acceder_narrativa_vip"


class ShopItemStatus(str, Enum):
    """Shop item status constants."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class NotificationType(str, Enum):
    """Notification type constants."""
    NARRATIVE = "narrative"
    MISSION = "mission"
    ACHIEVEMENT = "achievement"
    SHOP = "shop"
