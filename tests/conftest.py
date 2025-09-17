"""
Main pytest configuration and fixtures for integration testing.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import Optional

from database.models import User, UserStats, NarrativeFragment
from database.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def create_test_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def session_factory():
        async with async_session() as session:
            yield session
            await session.rollback()

    return session_factory


@pytest.fixture
async def create_test_user():
    """Create a test user."""
    async def user_factory(session: AsyncSession, user_id: int, role: str = "free", **kwargs):
        user = User(
            id=user_id,
            username=kwargs.get("username", f"test_user_{user_id}"),
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "User"),
            points=kwargs.get("points", 0),
            level=kwargs.get("level", 1),
            role=role,
            menu_state=kwargs.get("menu_state", "root"),
            achievements=kwargs.get("achievements", {}),
            missions_completed=kwargs.get("missions_completed", {}),
            created_at=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    return user_factory


@pytest.fixture
async def create_test_user_stats():
    """Create test user stats."""
    async def stats_factory(session: AsyncSession, user_id: int, **kwargs):
        stats = UserStats(
            user_id=user_id,
            last_checkin_at=kwargs.get("last_checkin_at"),
            checkin_streak=kwargs.get("checkin_streak", 0),
            total_reactions=kwargs.get("total_reactions", 0),
            total_messages=kwargs.get("total_messages", 0),
            created_at=datetime.utcnow()
        )
        session.add(stats)
        await session.commit()
        await session.refresh(stats)
        return stats

    return stats_factory


@pytest.fixture
def mock_bot():
    """Mock Telegram bot for testing."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot


@pytest.fixture
def test_narrative_data():
    """Test narrative fragments and data."""
    return {
        "fragments": {
            "TEST_START": {
                "key": "TEST_START",
                "level": 1,
                "character": "Lucien",
                "text": "Welcome to our test narrative journey. How do you wish to begin?",
                "choices": [
                    {"text": "Explore cautiously", "destination": "CAUTIOUS_PATH", "emotional_weight": 0.3},
                    {"text": "Dive deep immediately", "destination": "DEEP_PATH", "emotional_weight": 0.8}
                ],
                "requires_item": None,
                "teaser_content": None
            },
            "CAUTIOUS_PATH": {
                "key": "CAUTIOUS_PATH",
                "level": 2,
                "character": "Diana",
                "text": "Your cautious approach reveals hidden depths. What resonates with you?",
                "choices": [
                    {"text": "Share a vulnerable memory", "destination": "VULNERABILITY_TEST", "emotional_weight": 0.9},
                    {"text": "Keep exploring safely", "destination": "SAFE_EXPLORATION", "emotional_weight": 0.2}
                ],
                "requires_item": None,
                "teaser_content": None
            },
            "DEEP_PATH": {
                "key": "DEEP_PATH",
                "level": 2,
                "character": "Diana",
                "text": "You dive into the depths immediately. I sense your hunger for truth.",
                "choices": [
                    {"text": "Tell me about desire", "destination": "DESIRE_EXPLORATION", "emotional_weight": 0.7},
                    {"text": "I want to understand intimacy", "destination": "INTIMACY_PATH", "emotional_weight": 0.8}
                ],
                "requires_item": None,
                "teaser_content": None
            },
            "RESTRICTED_CONTENT": {
                "key": "RESTRICTED_CONTENT",
                "level": 3,
                "character": "Diana",
                "text": "This is where we explore the deepest territories of human connection...",
                "choices": [
                    {"text": "Continue this journey", "destination": "DEEPER_RESTRICTED", "emotional_weight": 0.9}
                ],
                "requires_item": "VIP_ACCESS_KEY",
                "teaser_content": {
                    "text": "I can sense you're ready for deeper exploration, but this territory requires a special key. In the shop, you'll find what unlocks these intimate conversations...",
                    "character": "Diana",
                    "shop_item_hint": "VIP_ACCESS_KEY",
                    "emotional_hook": "Your responses tell me you have the depth for what lies beyond this threshold."
                }
            }
        },
        "shop_items": {
            "VIP_ACCESS_KEY": {
                "id": 1,
                "code_name": "VIP_ACCESS_KEY",
                "name": "Key to Deeper Connection",
                "price": 200,
                "description": "Unlocks intimate narrative territories where vulnerability and connection deepen."
            },
            "EMOTIONAL_AMPLIFIER": {
                "id": 2,
                "code_name": "EMOTIONAL_AMPLIFIER",
                "name": "Emotional Resonance Amplifier",
                "price": 150,
                "description": "Enhances the emotional depth of character responses to your choices."
            }
        },
        "character_voices": {
            "Diana": {
                "base_personality": "intuitive, emotionally intelligent, direct about desire",
                "adaptation_patterns": {
                    "explorer_deep": "becomes more introspective and philosophical",
                    "direct_authentic": "matches directness with raw honesty",
                    "poet_desire": "speaks in metaphors and deeper imagery"
                }
            },
            "Lucien": {
                "base_personality": "analytical, guiding, intellectually curious",
                "adaptation_patterns": {
                    "analytic_empathic": "becomes more systematically empathetic",
                    "persistent_patient": "shows appreciation for dedication"
                }
            }
        }
    }


@pytest.fixture
def user_archetype_profiles():
    """User archetype profiles for testing."""
    return {
        "explorer_deep": {
            "characteristics": ["thoughtful", "introspective", "values depth"],
            "response_patterns": ["long response times", "detailed answers", "philosophical"],
            "emotional_markers": ["curiosity", "vulnerability", "authenticity"]
        },
        "direct_authentic": {
            "characteristics": ["straightforward", "honest", "quick decisions"],
            "response_patterns": ["immediate responses", "clear statements", "no hedging"],
            "emotional_markers": ["directness", "honesty", "clarity"]
        },
        "poet_desire": {
            "characteristics": ["aesthetic", "metaphorical", "romantic"],
            "response_patterns": ["poetic language", "emotional imagery", "artistic expression"],
            "emotional_markers": ["beauty", "desire", "artistic expression"]
        }
    }