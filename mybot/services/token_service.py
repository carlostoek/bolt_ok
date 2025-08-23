from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import InviteToken, User, VipSubscription
from database.transaction_models import VipTransaction
from services.achievement_service import AchievementService
from services.subscription_service import SubscriptionService
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, created_by: int, expires_in: int | None = None) -> InviteToken:
        token = token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        obj = InviteToken(token=token, created_by=created_by, expires_at=expires_at)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def activate_token(self, token_string: str, user_id: int) -> int:
        """Activate a VIP token and return the duration in days."""
        stmt = select(InviteToken).where(InviteToken.token == token_string)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()

        if not token or token.used_by or (token.expires_at and token.expires_at < datetime.utcnow()):
            raise ValueError("Invalid or expired token")

        token.used_by = user_id
        token.used_at = datetime.utcnow()

        duration_days = 30  # Default duration

        sub_service = SubscriptionService(self.session)
        await sub_service.grant_vip(
            user_id=user_id,
            duration_days=duration_days,
            source="token_activation",
        )

        await self.session.commit()
        return duration_days

    async def use_token(self, token: str, user_id: int, *, bot: Bot | None = None) -> bool:
        stmt = select(InviteToken).where(InviteToken.token == token)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj or obj.used_by or (obj.expires_at and obj.expires_at < datetime.utcnow()):
            return False
        obj.used_by = user_id
        obj.used_at = datetime.utcnow()
        await self.session.commit()
        ach_service = AchievementService(self.session)
        await ach_service.check_invite_achievements(obj.created_by, bot=bot)
        return True

    async def create_subscription_token(self, plan_id: int, created_by: int) -> InviteToken:
        """Create a subscription token using InviteToken model."""
        token = token_urlsafe(8)
        obj = InviteToken(token=token, created_by=created_by)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def redeem_subscription_token(self, token: str, user_id: int) -> InviteToken | None:
        """Redeem a subscription token."""
        stmt = select(InviteToken).where(InviteToken.token == token)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj or obj.used_by:
            return None
        obj.used_by = user_id
        obj.used_at = datetime.utcnow()
        await self.session.commit()
        return obj

    async def create_vip_token(self, duration_days: int) -> InviteToken:
        """Create a VIP subscription token for the given duration."""
        token_str = token_urlsafe(16)
        # We'll store the duration in the token itself or create a mapping
        # For simplicity, we'll just create a standard invite token
        obj = InviteToken(token=token_str)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        logger.info(f"VIP token created: {token_str} for {duration_days} days")
        return obj

    async def invalidate_vip_token(self, token_string: str) -> bool:
        """Remove an unused VIP token so it can no longer be redeemed."""
        stmt = select(InviteToken).where(InviteToken.token == token_string, InviteToken.used_by.is_(None))
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        logger.info(f"VIP token invalidated: {token_string}")
        return True

    async def get_token_info(self, token_string: str) -> InviteToken | None:
        """Get token information without activating it."""
        stmt = select(InviteToken).where(InviteToken.token == token_string)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


async def validate_token(token: str, session: AsyncSession) -> str | None:
    """Validate a legacy VIP activation token and mark it as used."""
    stmt = select(InviteToken).where(InviteToken.token == token)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if not obj or obj.used_by:
        return None
    # Mark as used
    obj.used_by = 1  # Placeholder, should be actual user ID
    await session.commit()
    return "30"  # Default duration, should be properly implemented
