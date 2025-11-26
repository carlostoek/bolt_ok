# tests/test_shop_flow.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from app.services.shop_service import ShopService
from database.models import User, ShopItem

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def seeded_shop_db_session(db_session: AsyncSession):
    """Seed the database with a user and a shop item for testing."""
    # Create a user with enough points
    user = User(id=12345, username="testuser", points=1000)
    db_session.add(user)

    # Create a shop item
    item = ShopItem(
        id=1,
        name="Test Item",
        description="A cool item for testing.",
        price=100,
        is_active=True
    )
    db_session.add(item)
    
    await db_session.commit()
    return db_session

async def test_successful_purchase(seeded_shop_db_session: AsyncSession, mock_callback_query):
    """
    Test case for a successful item purchase.
    - GIVEN a user with sufficient points and an available shop item.
    - WHEN the user triggers the 'buy_item' callback.
    - THEN the user's points should be deducted.
    - AND a UserPurchase record should be created.
    - AND the user should receive a success message.
    """
    from handlers.shop_handlers import handle_purchase
    
    # Set the callback data for the item to be purchased
    mock_callback_query.data = "buy_item:1"
    
    # Initial state verification
    service = ShopService(seeded_shop_db_session)
    user_points_before = await service.get_user_points(12345)
    has_purchased_before, _ = await service.has_user_purchased_item(12345, 1)
    
    assert user_points_before == 1000
    assert not has_purchased_before

    # Call the handler
    await handle_purchase(mock_callback_query, db=seeded_shop_db_session)

    # ASSERT
    # 1. Check that a success message was sent
    mock_callback_query.message.edit_text.assert_called_once()
    args, _ = mock_callback_query.message.edit_text.call_args
    assert "¡Compra Exitosa!" in args[0]
    
    # 2. Check user's points after purchase
    user_points_after = await service.get_user_points(12345)
    assert user_points_after == 900  # 1000 - 100

    # 3. Check if the purchase was recorded in the database
    has_purchased_after, purchase_count = await service.has_user_purchased_item(12345, 1)
    assert has_purchased_after
    assert purchase_count == 1
