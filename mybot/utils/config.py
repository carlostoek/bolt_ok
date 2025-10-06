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
