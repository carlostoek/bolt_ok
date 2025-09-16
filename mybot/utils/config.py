import os
from typing import List


BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
if BOT_TOKEN == "YOUR_BOT_TOKEN" or not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN environment variable is not set or contains the default placeholder."
    )

ADMIN_IDS: List[int] = [
    int(uid) for uid in os.environ.get("ADMIN_IDS", "").split(";") if uid.strip()
]

VIP_CHANNEL_ID = int(os.environ.get("VIP_CHANNEL_ID", "0"))
FREE_CHANNEL_ID = int(os.environ.get("FREE_CHANNEL_ID", "0"))
CHANNEL_SCHEDULER_INTERVAL = int(os.environ.get("CHANNEL_SCHEDULER_INTERVAL", "30"))
VIP_SCHEDULER_INTERVAL = int(os.environ.get("VIP_SCHEDULER_INTERVAL", "3600"))
DEFAULT_REACTION_BUTTONS = ["👍", "❤️", "😂", "🔥", "💯"]

class Config:
    BOT_TOKEN = BOT_TOKEN
    ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0
    CHANNEL_ID = VIP_CHANNEL_ID
    FREE_CHANNEL_ID = FREE_CHANNEL_ID

    # SQLite configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///bot.db")
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "5"))

    CHANNEL_SCHEDULER_INTERVAL = CHANNEL_SCHEDULER_INTERVAL
    VIP_SCHEDULER_INTERVAL = VIP_SCHEDULER_INTERVAL

    # ===== NARRATIVE SYSTEM CONFIGURATION =====

    # Performance Configuration
    NARRATIVE_CACHE_TTL = int(os.environ.get("NARRATIVE_CACHE_TTL", "3600"))  # 1 hour
    FRAGMENT_CACHE_SIZE = int(os.environ.get("FRAGMENT_CACHE_SIZE", "1000"))
    ANALYTICS_BATCH_SIZE = int(os.environ.get("ANALYTICS_BATCH_SIZE", "100"))
    ANALYTICS_PROCESSING_INTERVAL = int(os.environ.get("ANALYTICS_PROCESSING_INTERVAL", "300"))  # 5 minutes

    # Database Performance
    DB_ANALYTICS_POOL_SIZE = int(os.environ.get("DB_ANALYTICS_POOL_SIZE", "15"))
    DB_ANALYTICS_MAX_OVERFLOW = int(os.environ.get("DB_ANALYTICS_MAX_OVERFLOW", "10"))
    DB_QUERY_TIMEOUT = int(os.environ.get("DB_QUERY_TIMEOUT", "30"))
    DB_CONNECTION_RECYCLE = int(os.environ.get("DB_CONNECTION_RECYCLE", "3600"))

    # Cache Configuration
    CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "memory")  # memory, redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "10000"))

    # Security Configuration
    ADMIN_SESSION_TIMEOUT = int(os.environ.get("ADMIN_SESSION_TIMEOUT", "1800"))  # 30 minutes
    CONTENT_VALIDATION_ENABLED = os.environ.get("CONTENT_VALIDATION_ENABLED", "true").lower() == "true"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", "5000"))
    RATE_LIMIT_ADMIN_OPERATIONS = int(os.environ.get("RATE_LIMIT_ADMIN_OPERATIONS", "100"))  # per hour
    RATE_LIMIT_USER_INTERACTIONS = int(os.environ.get("RATE_LIMIT_USER_INTERACTIONS", "1000"))  # per hour

    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES = os.environ.get("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif,mp4,mp3,txt,pdf").split(",")
    UPLOAD_PATH = os.environ.get("UPLOAD_PATH", "uploads/narrative/")

    # Analytics Configuration
    ANALYTICS_RETENTION_DAYS = int(os.environ.get("ANALYTICS_RETENTION_DAYS", "365"))
    ANALYTICS_AGGREGATION_ENABLED = os.environ.get("ANALYTICS_AGGREGATION_ENABLED", "true").lower() == "true"
    ANALYTICS_REAL_TIME_ENABLED = os.environ.get("ANALYTICS_REAL_TIME_ENABLED", "true").lower() == "true"

    # Character AI Integration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    AI_REQUEST_TIMEOUT = int(os.environ.get("AI_REQUEST_TIMEOUT", "30"))
    AI_MAX_RETRIES = int(os.environ.get("AI_MAX_RETRIES", "3"))
    AI_FALLBACK_ENABLED = os.environ.get("AI_FALLBACK_ENABLED", "true").lower() == "true"
    AI_RATE_LIMIT_PER_MINUTE = int(os.environ.get("AI_RATE_LIMIT_PER_MINUTE", "60"))

    # CoordinadorCentral Configuration
    COORDINATOR_ENABLED = os.environ.get("COORDINATOR_ENABLED", "true").lower() == "true"
    COORDINATOR_SYNC_INTERVAL = int(os.environ.get("COORDINATOR_SYNC_INTERVAL", "60"))  # seconds
    COORDINATOR_BATCH_OPERATIONS = os.environ.get("COORDINATOR_BATCH_OPERATIONS", "true").lower() == "true"

    # Lore Management Configuration
    LORE_AUTO_UNLOCK_ENABLED = os.environ.get("LORE_AUTO_UNLOCK_ENABLED", "true").lower() == "true"
    LORE_VALIDATION_ENABLED = os.environ.get("LORE_VALIDATION_ENABLED", "true").lower() == "true"
    LORE_CACHE_DURATION = int(os.environ.get("LORE_CACHE_DURATION", "1800"))  # 30 minutes

    # Narrative Progress Configuration
    PROGRESS_AUTO_SAVE_INTERVAL = int(os.environ.get("PROGRESS_AUTO_SAVE_INTERVAL", "120"))  # 2 minutes
    PROGRESS_VALIDATION_ENABLED = os.environ.get("PROGRESS_VALIDATION_ENABLED", "true").lower() == "true"
    CHOICE_TIMEOUT_MINUTES = int(os.environ.get("CHOICE_TIMEOUT_MINUTES", "30"))

    # Admin Panel Configuration
    ADMIN_PAGINATION_SIZE = int(os.environ.get("ADMIN_PAGINATION_SIZE", "20"))
    ADMIN_LOG_RETENTION_DAYS = int(os.environ.get("ADMIN_LOG_RETENTION_DAYS", "90"))
    ADMIN_BACKUP_ENABLED = os.environ.get("ADMIN_BACKUP_ENABLED", "true").lower() == "true"
    ADMIN_BACKUP_INTERVAL_HOURS = int(os.environ.get("ADMIN_BACKUP_INTERVAL_HOURS", "24"))

    # Monitoring and Logging
    MONITORING_ENABLED = os.environ.get("MONITORING_ENABLED", "true").lower() == "true"
    PERFORMANCE_LOGGING_ENABLED = os.environ.get("PERFORMANCE_LOGGING_ENABLED", "true").lower() == "true"
    ERROR_NOTIFICATION_ENABLED = os.environ.get("ERROR_NOTIFICATION_ENABLED", "true").lower() == "true"
    METRICS_COLLECTION_INTERVAL = int(os.environ.get("METRICS_COLLECTION_INTERVAL", "300"))  # 5 minutes
