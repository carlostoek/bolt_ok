"""
Test suite for Gift Service
Tests manual gift sending, automatic triggers, and message formatting
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from database.models import Base, User, ContentSet, GiftRecord
from services.gift_service import GiftService, GIFT_MESSAGES
from services.content_service import ContentService


async def create_test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def setup_test_data(session: AsyncSession):
    """Setup test users and content sets"""
    print("\n📦 Setting up test data...")

    # Create test user
    user = User(
        id=123456789,
        username="test_user",
        first_name="Test",
        points=1000,
        level=5
    )
    session.add(user)

    # Create content sets for different gift types
    content_sets = [
        ContentSet(
            id="auction_winner_gift",
            name="Premio Subasta VIP",
            description="Set especial para ganadores de subasta",
            type="photo_set",
            tier="gift",
            category="gift",
            for_archetype="all",
            file_ids=["test_file_1", "test_file_2"],
            is_active=True
        ),
        ContentSet(
            id="shop_purchase_gift",
            name="Sorpresa por Compra",
            description="Regalo por comprar en la tienda",
            type="mixed",
            tier="gift",
            category="surprise",
            for_archetype="all",
            file_ids=["test_file_3", "test_file_4"],
            is_active=True
        ),
        ContentSet(
            id="level_milestone_gift",
            name="Milestone Nivel 5",
            description="Regalo por alcanzar nivel especial",
            type="video",
            tier="gift",
            category="milestone",
            for_archetype="all",
            file_ids=["test_file_5"],
            is_active=True
        ),
        ContentSet(
            id="surprise_gift",
            name="Sorpresa Espontánea",
            description="Regalo sorpresa de Diana",
            type="photo_set",
            tier="gift",
            category="surprise",
            for_archetype="all",
            file_ids=["test_file_6", "test_file_7"],
            is_active=True
        )
    ]

    for cs in content_sets:
        session.add(cs)

    await session.commit()
    print(f"✅ Created test user: {user.username}")
    print(f"✅ Created {len(content_sets)} content sets for gifts")

    return user, content_sets


def test_message_templates():
    """Test that all message templates are properly formatted"""
    print("\n🧪 Testing message templates...")

    test_contexts = {
        "auction_won": {"username": "TestUser", "item_name": "Set Exclusivo VIP"},
        "shop_purchase": {"username": "TestUser", "item_name": "Diario Secreto"},
        "level_reached": {"username": "TestUser", "level": 5},
        "milestone": {"username": "TestUser", "milestone_name": "100 Días Activo"},
        "surprise": {"username": "TestUser"},
        "loyalty": {"username": "TestUser", "days": 30},
        "birthday": {"username": "TestUser"},
        "custom": {"username": "TestUser"}
    }

    for event_type, context_data in test_contexts.items():
        template = GIFT_MESSAGES.get(event_type)
        if not template:
            print(f"❌ Missing template for: {event_type}")
            continue

        try:
            title = template["title"]
            message = template["message"].format(**context_data)
            print(f"✅ {event_type}: {title[:30]}...")
        except KeyError as e:
            print(f"❌ {event_type}: Missing key {e}")
        except Exception as e:
            print(f"❌ {event_type}: {e}")

    print(f"\n✅ Total message templates: {len(GIFT_MESSAGES)}")


async def test_send_gift(session: AsyncSession, user: User, content_set: ContentSet):
    """Test sending a gift"""
    print(f"\n🧪 Testing gift send: {content_set.name}")

    gift_service = GiftService(session)

    # Mock bot (we won't actually send messages)
    class MockBot:
        async def send_photo(self, *args, **kwargs):
            print(f"   📸 [MOCK] Would send photo to user")
            return None

        async def send_video(self, *args, **kwargs):
            print(f"   🎬 [MOCK] Would send video to user")
            return None

        async def send_message(self, *args, **kwargs):
            print(f"   💬 [MOCK] Would send message: {kwargs.get('text', '')[:50]}...")
            return None

    bot = MockBot()

    # Test basic gift send
    result = await gift_service.send_gift(
        user_id=user.id,
        content_set_id=content_set.id,
        event_type="surprise",
        bot=bot,
        context_data={"username": user.first_name}
    )

    if result:
        print(f"✅ Gift sent successfully")

        # Verify gift was recorded
        stmt = select(GiftRecord).where(
            GiftRecord.user_id == user.id,
            GiftRecord.content_set_id == content_set.id
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            print(f"✅ Gift record created: context={record.context}, trigger={record.trigger_type} at {record.sent_at}")
        else:
            print("❌ Gift record not found")
    else:
        print("❌ Gift send failed")


async def test_helper_methods(session: AsyncSession, user: User):
    """Test helper methods for specific events"""
    print("\n🧪 Testing helper methods...")

    gift_service = GiftService(session)

    class MockBot:
        async def send_photo(self, *args, **kwargs):
            return None
        async def send_video(self, *args, **kwargs):
            return None
        async def send_message(self, *args, **kwargs):
            return None

    bot = MockBot()

    # Test auction won gift
    result = await gift_service.send_auction_won_gift(
        user_id=user.id,
        auction_name="Subasta Test VIP",
        bot=bot
    )
    print(f"   {'✅' if result else '❌'} send_auction_won_gift")

    # Test shop purchase gift (override default content_set_id)
    result = await gift_service.send_shop_purchase_gift(
        user_id=user.id,
        item_name="Item Test",
        bot=bot,
        content_set_id="shop_purchase_gift"  # Use our test content set
    )
    print(f"   {'✅' if result else '❌'} send_shop_purchase_gift")

    # Test level reached gift
    result = await gift_service.send_level_reached_gift(
        user_id=user.id,
        level=5,
        bot=bot
    )
    print(f"   {'✅' if result else '❌'} send_level_reached_gift")

    # Test surprise gift (requires content_set_id)
    result = await gift_service.send_surprise_gift(
        user_id=user.id,
        content_set_id="surprise_gift",  # Required parameter
        bot=bot
    )
    print(f"   {'✅' if result else '❌'} send_surprise_gift")


async def test_duplicate_prevention(session: AsyncSession, user: User):
    """Test that duplicate gifts are prevented"""
    print("\n🧪 Testing duplicate prevention...")

    gift_service = GiftService(session)

    class MockBot:
        async def send_photo(self, *args, **kwargs):
            return None
        async def send_message(self, *args, **kwargs):
            return None

    bot = MockBot()

    # Send first gift
    result1 = await gift_service.send_auction_won_gift(
        user_id=user.id,
        auction_name="Test Auction",
        bot=bot,
        content_set_id="auction_winner_gift"  # Use test content set
    )

    # Try to send same gift again for same event
    has_received = await gift_service.has_received_gift_for_event(
        user_id=user.id,
        event_type="auction_won",
        content_set_id="auction_winner_gift"
    )

    if has_received:
        print("✅ Duplicate detection working correctly")
    else:
        print("❌ Duplicate detection failed")


async def test_stats(session: AsyncSession):
    """Test gift statistics"""
    print("\n🧪 Testing statistics...")

    gift_service = GiftService(session)

    stats = await gift_service.get_gift_stats()

    print(f"   Total gifts sent: {stats['total_gifts']}")
    print(f"   Unique users: {stats['unique_users']}")
    print(f"   By event type: {stats['gifts_by_type']}")
    print(f"   Admin gifts: {stats['admin_gifts']}")
    print(f"   Automatic gifts: {stats['automatic_gifts']}")

    if stats['total_gifts'] > 0:
        print("✅ Statistics generated successfully")
    else:
        print("⚠️  No gifts sent yet")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🎁 GIFT SERVICE TEST SUITE")
    print("=" * 60)

    # Create test database
    engine = await create_test_db()
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        # Setup
        user, content_sets = await setup_test_data(session)

        # Run tests
        test_message_templates()
        await test_send_gift(session, user, content_sets[0])
        await test_helper_methods(session, user)
        await test_duplicate_prevention(session, user)
        await test_stats(session)

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
