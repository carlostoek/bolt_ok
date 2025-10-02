import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from database.models import PendingChannelRequest, BotConfig, User
from utils.config import CHANNEL_SCHEDULER_INTERVAL, VIP_SCHEDULER_INTERVAL
from services.config_service import ConfigService
from services.auction_service import AuctionService
from services.free_channel_service import FreeChannelService
from services.subscription_service import SubscriptionService
from services.user_journey_service import UserJourneyService


async def run_channel_request_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Process pending channel requests once using the new FreeChannelService."""
    async with session_factory() as session:
        free_service = FreeChannelService(session, bot)
        processed_count = await free_service.process_pending_requests()
        
        if processed_count > 0:
            logging.info(f"Processed {processed_count} pending channel requests")


async def channel_request_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task processing channel join requests."""
    logging.info("Channel request scheduler started")
    interval = CHANNEL_SCHEDULER_INTERVAL
    try:
        while True:
            await run_channel_request_check(bot, session_factory)
            async with session_factory() as session:
                config_service = ConfigService(session)
                value = await config_service.get_value("channel_scheduler_interval")
                if value and value.isdigit():
                    interval = int(value)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Channel request scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in channel request scheduler")


async def run_vip_subscription_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Check VIP expirations and send reminders once."""
    async with session_factory() as session:
        now = datetime.utcnow()
        remind_threshold = now + timedelta(hours=24)
        config_service = ConfigService(session)
        reminder_msg = await config_service.get_value("vip_reminder_message")
        farewell_msg = await config_service.get_value("vip_farewell_message")
        if not reminder_msg:
            reminder_msg = "Tu suscripción VIP expira pronto."
        if not farewell_msg:
            farewell_msg = "Tu suscripción VIP ha expirado."
        stmt = select(User).where(
            User.role == "vip",
            User.vip_expires_at <= remind_threshold,
            User.vip_expires_at > now,
            (User.last_reminder_sent_at.is_(None))
            | (User.last_reminder_sent_at <= now - timedelta(hours=24)),
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        for user in users:
            try:
                await bot.send_message(user.id, reminder_msg)
                user.last_reminder_sent_at = now
                logging.info("Sent VIP expiry reminder to %s", user.id)
            except Exception as e:
                logging.exception("Failed to send reminder to %s: %s", user.id, e)

        stmt = select(User).where(
            User.role == "vip",
            User.vip_expires_at.is_not(None),
            User.vip_expires_at <= now,
        )
        result = await session.execute(stmt)
        expired_users = result.scalars().all()
        vip_channel_id = await ConfigService(session).get_vip_channel_id()
        for user in expired_users:
            try:
                if vip_channel_id:
                    await bot.ban_chat_member(vip_channel_id, user.id)
                    await bot.unban_chat_member(vip_channel_id, user.id)
            except Exception as e:
                logging.exception("Failed to remove %s from VIP channel: %s", user.id, e)
            user.role = "free"
            await bot.send_message(user.id, farewell_msg)
            logging.info("VIP expired for %s", user.id)
        await session.commit()


async def run_vip_membership_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Ensure users in the VIP channel have valid subscriptions, remove those without."""
    async with session_factory() as session:
        vip_channel_id = await ConfigService(session).get_vip_channel_id()
        if not vip_channel_id:
            return

        # Get all users currently marked as non-VIP
        stmt = select(User).where(User.role != "vip")
        result = await session.execute(stmt)
        users = result.scalars().all()

        updated = 0
        removed = 0
        for user in users:
            try:
                member = await bot.get_chat_member(vip_channel_id, user.id)
                if member.status in {"member", "administrator", "creator"}:
                    # User is in VIP channel but not marked as VIP
                    sub_service = SubscriptionService(session)
                    sub = await sub_service.get_subscription(user.id)

                    # Only sync role if they have a VALID subscription in database
                    if sub and await sub_service.is_subscription_active(user.id):
                        user.role = "vip"
                        updated += 1
                        logging.info(f"Synced user {user.id} to VIP role (has valid subscription)")
                    else:
                        # User is in channel but has no valid subscription - remove them
                        try:
                            await bot.ban_chat_member(vip_channel_id, user.id)
                            await bot.unban_chat_member(vip_channel_id, user.id)
                            removed += 1
                            logging.info(f"Removed user {user.id} from VIP channel (no valid subscription)")
                        except Exception as kick_error:
                            logging.warning(f"Could not remove user {user.id} from VIP channel: {kick_error}")
            except Exception as e:
                logging.debug(f"Error checking user {user.id} in VIP channel: {e}")
                continue

        if updated or removed:
            await session.commit()
            logging.info(f"VIP membership check: synced {updated} users, removed {removed} users")


async def vip_subscription_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task checking VIP subscriptions."""
    logging.info("VIP subscription scheduler started")
    interval = VIP_SCHEDULER_INTERVAL
    try:
        while True:
            await run_vip_subscription_check(bot, session_factory)
            async with session_factory() as session:
                config_service = ConfigService(session)
                value = await config_service.get_value("vip_scheduler_interval")
                if value and value.isdigit():
                    interval = int(value)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("VIP subscription scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in VIP subscription scheduler")


async def vip_membership_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task syncing VIP roles based on channel membership."""
    logging.info("VIP membership scheduler started")
    interval = VIP_SCHEDULER_INTERVAL
    try:
        while True:
            await run_vip_membership_check(bot, session_factory)
            async with session_factory() as session:
                config_service = ConfigService(session)
                value = await config_service.get_value("vip_scheduler_interval")
                if value and value.isdigit():
                    interval = int(value)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("VIP membership scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in VIP membership scheduler")


async def run_auction_monitor_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Check for expired auctions and end them automatically."""
    async with session_factory() as session:
        auction_service = AuctionService(session)
        try:
            expired_auctions = await auction_service.check_expired_auctions(bot)
            if expired_auctions:
                logging.info(f"Auto-ended {len(expired_auctions)} expired auctions")
        except Exception as e:
            logging.exception("Error in auction monitor check: %s", e)


async def auction_monitor_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task monitoring auction expirations."""
    logging.info("Auction monitor scheduler started")
    interval = 60  # Check every minute for auction expirations
    try:
        while True:
            await run_auction_monitor_check(bot, session_factory)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Auction monitor scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in auction monitor scheduler")


async def run_free_channel_cleanup(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Clean up old channel requests periodically."""
    async with session_factory() as session:
        free_service = FreeChannelService(session, bot)
        try:
            cleaned_count = await free_service.cleanup_old_requests(days_old=30)
            if cleaned_count > 0:
                logging.info(f"Cleaned up {cleaned_count} old channel requests")
        except Exception as e:
            logging.exception("Error in free channel cleanup: %s", e)


async def free_channel_cleanup_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task for cleaning up old channel requests."""
    logging.info("Free channel cleanup scheduler started")
    interval = 86400  # Run once per day
    try:
        while True:
            await run_free_channel_cleanup(bot, session_factory)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Free channel cleanup scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in free channel cleanup scheduler")


async def run_user_journey_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Process all pending user journey milestones once."""
    async with session_factory() as session:
        journey_service = UserJourneyService(session)
        try:
            stats = await journey_service.process_all_milestones(bot)

            total_processed = stats["day_1_processed"] + stats["day_7_processed"] + stats["day_30_processed"]

            if total_processed > 0:
                logging.info(
                    f"Journey milestones processed - "
                    f"Day 1: {stats['day_1_processed']}, "
                    f"Day 7: {stats['day_7_processed']}, "
                    f"Day 30: {stats['day_30_processed']}, "
                    f"Errors: {stats['errors']}"
                )
        except Exception as e:
            logging.exception("Error in user journey check: %s", e)


async def user_journey_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task processing user journey milestones daily."""
    logging.info("User journey scheduler started")
    interval = 3600  # Check every hour (can be adjusted)
    try:
        while True:
            await run_user_journey_check(bot, session_factory)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("User journey scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in user journey scheduler")
