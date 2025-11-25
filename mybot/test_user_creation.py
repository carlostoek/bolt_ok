"""
Test script to create a user without ShopItem conflicts.
"""
import asyncio
import logging
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_user_creation():
    """Test creating a user to check for ShopItem conflicts."""
    try:
        async with AsyncSessionLocal() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.id == 999999999)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info(f"Test user already exists: {existing_user}")
                return existing_user
            
            # Create test user
            test_user = User(
                id=999999999,
                username="testuser",
                first_name="Test",
                last_name="User",
                role=UserRole.USER,
                is_banned=False,
                is_vip=False,
                points=100,
                level=1
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            logger.info(f"Test user created successfully: {test_user}")
            return test_user
            
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise


async def main():
    """Run the test."""
    logger.info("Testing user creation...")
    try:
        user = await test_user_creation()
        logger.info(f"✅ SUCCESS: User created: {user}")
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())