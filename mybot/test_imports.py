"""
Test file to validate type checking compatibility and imports
"""
from app.core.database import (
    engine, SessionLocal, Base, TimestampMixin, SoftDeleteMixin, 
    get_db, get_db_session, execute_with_retry, configure_engine
)
from app.core.sqlite_optimizations import (
    enable_wal_mode, optimize_sqlite_pragmas, auto_vacuum_database,
    integrity_check, optimize_sqlite_for_termux, cleanup_sqlite_logs
)
from app.models.narrative import StoryFragment, NarrativeChoice, UserNarrativeState
from app.models.shop import ShopItem, ProductFile, InventoryItem, UserPurchase
from app.models.gamification import Mission, Reward, Achievement, Badge
from app.models.automation import AutomationTrigger, TriggerAction, TriggerExecutionLog
from app.models.user import User, UserMissionEntry, UserFragmentView
from app.models.lore import LorePiece, UserLorePiece

print("All imports successful - type checking validation passed!")