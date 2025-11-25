"""
Check database schema to see what columns exist.
"""
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal


async def check_user_table():
    """Check the structure of the users table."""
    async with AsyncSessionLocal() as session:
        # Get table info for users
        result = await session.execute(text("PRAGMA table_info(users)"))
        columns = result.fetchall()
        
        print("Users table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check if is_banned column exists
        column_names = [col[1] for col in columns]
        if "is_banned" in column_names:
            print("✅ is_banned column exists")
        else:
            print("❌ is_banned column does NOT exist")


async def main():
    """Run the check."""
    print("Checking database schema...")
    await check_user_table()


if __name__ == "__main__":
    asyncio.run(main())