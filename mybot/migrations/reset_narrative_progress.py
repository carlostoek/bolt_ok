#!/usr/bin/env python3
"""
Script para resetear el progreso narrativo de todos los usuarios.

Esto borra:
- Estados narrativos de usuarios (current_fragment_key, choices_made, etc.)
- Mantiene intactos: usuarios, suscripciones, puntos, compras, etc.

Uso:
    python migrations/reset_narrative_progress.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, delete
from database.setup import get_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reset_narrative_progress():
    """Reset all users' narrative progress."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            logger.info("🔄 Resetting narrative progress for all users...")

            # Option 1: Delete all narrative states (clean slate)
            result = await session.execute(
                text("DELETE FROM user_narrative_states")
            )
            deleted_count = result.rowcount

            await session.commit()

            logger.info(f"✅ Successfully reset narrative progress for {deleted_count} users")
            logger.info("📝 All users will start from the beginning when they access /historia")
            return True

        except Exception as e:
            logger.error(f"❌ Error resetting narrative progress: {e}")
            await session.rollback()
            return False


async def reset_specific_user(user_id: int):
    """Reset narrative progress for a specific user."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            logger.info(f"🔄 Resetting narrative progress for user {user_id}...")

            result = await session.execute(
                text("DELETE FROM user_narrative_states WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            await session.commit()

            if result.rowcount > 0:
                logger.info(f"✅ Successfully reset narrative progress for user {user_id}")
            else:
                logger.info(f"ℹ️ No narrative progress found for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Error resetting user {user_id}: {e}")
            await session.rollback()
            return False


async def view_current_progress():
    """View current narrative progress for all users."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            result = await session.execute(
                text("""
                    SELECT
                        user_id,
                        current_fragment_key,
                        fragments_visited,
                        shop_redirect_fragment_key,
                        pending_decision_id
                    FROM user_narrative_states
                    ORDER BY last_activity_at DESC
                """)
            )

            rows = result.fetchall()

            if not rows:
                logger.info("ℹ️ No users have narrative progress")
                return

            logger.info(f"\n📊 Current narrative progress ({len(rows)} users):")
            logger.info("=" * 80)
            for row in rows:
                logger.info(
                    f"User {row[0]}: "
                    f"fragment={row[1]}, "
                    f"visited={row[2]}, "
                    f"shop_redirect={row[3]}, "
                    f"pending_decision={row[4]}"
                )
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Error viewing progress: {e}")


async def main():
    """Main entry point."""
    from database.setup import init_db
    await init_db()

    logger.info("=" * 80)
    logger.info("🔄 NARRATIVE PROGRESS RESET TOOL")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Options:")
    logger.info("  1. View current narrative progress")
    logger.info("  2. Reset ALL users' narrative progress")
    logger.info("  3. Reset specific user's narrative progress")
    logger.info("  4. Exit")
    logger.info("")

    choice = input("Enter your choice (1-4): ").strip()

    if choice == "1":
        await view_current_progress()

    elif choice == "2":
        confirm = input("\n⚠️  This will reset ALL users' narrative progress. Are you sure? (yes/no): ").strip().lower()
        if confirm == "yes":
            success = await reset_narrative_progress()
            if success:
                logger.info("\n✅ All narrative progress has been reset")
        else:
            logger.info("❌ Operation cancelled")

    elif choice == "3":
        try:
            user_id = int(input("\nEnter user ID: ").strip())
            await reset_specific_user(user_id)
        except ValueError:
            logger.error("❌ Invalid user ID")

    elif choice == "4":
        logger.info("👋 Goodbye!")

    else:
        logger.error("❌ Invalid choice")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
