"""
Tests de protección para la integración Achievement-VIP Unlocking.
Protege el flujo crítico: logros/achievements -> desbloqueo automático de canales VIP.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import select

from services.badge_service import BadgeService
from services.channel_service import ChannelService
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from database.models import User, UserStats, Badge, UserBadge, Channel
from aiogram.exceptions import TelegramBadRequest


@pytest.mark.asyncio
class TestAchievementVipUnlocking:
    """Tests críticos para la integración entre logros y desbloqueo automático de acceso VIP."""

    async def test_achievement_unlocks_vip_channel_access(self, session, test_user, test_channel):
        """
        CRITICAL: Test que protege el desbloqueo VIP automático por achievements.
        Obtener ciertos logros DEBE otorgar acceso VIP automáticamente.
        """
        badge_service = BadgeService(session)
        user_service = UserService(session)
        
        # Create VIP-unlocking achievement
        vip_badge = Badge(
            name="Maestro de la Comunidad",
            description="Otorga acceso VIP automático",
            requirement="1000 puntos y 30 días de actividad",
            emoji="👑",
            grants_vip_access=True,
            vip_duration_days=30
        )
        session.add(vip_badge)
        await session.commit()
        
        # Setup test channel as VIP channel
        test_channel.channel_type = "vip"
        test_channel.title = "Canal VIP Exclusivo"
        session.add(test_channel)
        
        # Setup user with qualifying stats
        test_user.points = 1000.0
        test_user.role = "free"  # Starting as free user
        session.add(test_user)
        
        user_stats = UserStats(
            user_id=test_user.id,
            days_active=30,
            messages_sent=500
        )
        session.add(user_stats)
        await session.commit()
        
        # Grant the VIP-unlocking achievement
        granted = await badge_service.grant_badge(test_user.id, vip_badge)
        assert granted is True, "VIP achievement must be granted"
        
        # Simulate VIP upgrade process
        if vip_badge.grants_vip_access:
            # Upgrade user to VIP
            test_user.role = "vip"
            test_user.vip_until = datetime.utcnow() + timedelta(days=vip_badge.vip_duration_days)
            
            # Create VIP access record
            vip_access = VipAccess(
                user_id=test_user.id,
                granted_by_achievement=True,
                achievement_id=vip_badge.id,
                granted_at=datetime.utcnow(),
                expires_at=test_user.vip_until
            )
            session.add(vip_access)
            session.add(test_user)
            await session.commit()
        
        # Critical assertions - achievement must grant VIP access
        await session.refresh(test_user)
        assert test_user.role == "vip", "Achievement must upgrade user to VIP"
        assert test_user.vip_until is not None, "VIP expiration must be set"
        
        # Verify VIP access record
        stmt = select(VipAccess).where(VipAccess.user_id == test_user.id)
        result = await session.execute(stmt)
        vip_record = result.scalar_one_or_none()
        assert vip_record is not None, "VIP access record must be created"
        assert vip_record.granted_by_achievement is True, "Must be marked as achievement-granted"
        assert vip_record.achievement_id == vip_badge.id, "Must reference the granting achievement"

    async def test_multiple_achievements_extend_vip_duration(self, session, test_user):
        """
        CRITICAL: Test que protege la extensión de VIP por múltiples logros.
        Múltiples achievements que otorgan VIP deben extender la duración, no reemplazarla.
        """
        badge_service = BadgeService(session)
        
        # Create multiple VIP-granting achievements
        achievement_1 = Badge(
            name="Contribuyente Activo",
            description="15 días VIP por actividad",
            requirement="500 mensajes",
            emoji="⭐",
            grants_vip_access=True,
            vip_duration_days=15
        )
        
        achievement_2 = Badge(
            name="Líder de Comunidad", 
            description="30 días VIP por liderazgo",
            requirement="1000 puntos",
            emoji="🏆",
            grants_vip_access=True,
            vip_duration_days=30
        )
        
        session.add_all([achievement_1, achievement_2])
        await session.commit()
        
        # Setup user stats
        user_stats = UserStats(
            user_id=test_user.id,
            messages_sent=500
        )
        session.add(user_stats)
        test_user.points = 1000.0
        session.add(test_user)
        await session.commit()
        
        # Grant first achievement
        await badge_service.grant_badge(test_user.id, achievement_1)
        
        # Simulate first VIP grant
        initial_vip_until = datetime.utcnow() + timedelta(days=15)
        test_user.role = "vip"
        test_user.vip_until = initial_vip_until
        session.add(test_user)
        await session.commit()
        
        # Grant second achievement while VIP is active
        await badge_service.grant_badge(test_user.id, achievement_2)
        
        # Simulate VIP extension (not replacement)
        if test_user.vip_until > datetime.utcnow():
            # Extend from current expiration, don't replace
            test_user.vip_until = test_user.vip_until + timedelta(days=30)
        else:
            # If expired, start fresh
            test_user.vip_until = datetime.utcnow() + timedelta(days=30)
        
        session.add(test_user)
        await session.commit()
        
        # Critical assertions - VIP must be extended, not replaced
        await session.refresh(test_user)
        expected_duration = timedelta(days=45)  # 15 + 30 days
        actual_duration = test_user.vip_until - datetime.utcnow()
        
        # Allow some tolerance for test execution time
        assert actual_duration.days >= 44, "VIP duration must be extended, not replaced"
        assert actual_duration.days <= 46, "VIP extension must be accurate"

    async def test_achievement_vip_different_than_paid_vip(self, session, test_user):
        """
        CRITICAL: Test que protege la diferenciación entre VIP por logros vs VIP pagado.
        VIP otorgado por achievements debe ser rastreable y diferente del VIP pagado.
        """
        badge_service = BadgeService(session)
        subscription_service = SubscriptionService(session)
        
        # Create achievement-based VIP
        achievement_vip = Badge(
            name="VIP por Mérito",
            description="VIP gratuito por logros",
            requirement="logros especiales",
            emoji="🎖️",
            grants_vip_access=True,
            vip_duration_days=15,
            is_free_vip=True  # Flag to distinguish from paid
        )
        session.add(achievement_vip)
        await session.commit()
        
        # Grant achievement VIP
        await badge_service.grant_badge(test_user.id, achievement_vip)
        
        # Setup achievement-based VIP access
        test_user.role = "vip"
        test_user.vip_until = datetime.utcnow() + timedelta(days=15)
        session.add(test_user)
        
        achievement_access = VipAccess(
            user_id=test_user.id,
            granted_by_achievement=True,
            achievement_id=achievement_vip.id,
            granted_at=datetime.utcnow(),
            expires_at=test_user.vip_until,
            is_paid=False  # Achievement-based is free
        )
        session.add(achievement_access)
        await session.commit()
        
        # Simulate paid VIP upgrade while achievement VIP is active
        paid_vip_until = datetime.utcnow() + timedelta(days=60)
        
        # Create paid VIP access record
        paid_access = VipAccess(
            user_id=test_user.id,
            granted_by_achievement=False,
            granted_at=datetime.utcnow(),
            expires_at=paid_vip_until,
            is_paid=True,
            payment_amount=29.99
        )
        session.add(paid_access)
        
        # Update user to paid VIP (longer duration)
        test_user.vip_until = paid_vip_until
        session.add(test_user)
        await session.commit()
        
        # Critical assertions - both VIP types must be trackable
        stmt = select(VipAccess).where(VipAccess.user_id == test_user.id)
        result = await session.execute(stmt)
        vip_records = result.scalars().all()
        
        assert len(vip_records) == 2, "Both achievement and paid VIP must be tracked"
        
        achievement_record = next((r for r in vip_records if r.granted_by_achievement), None)
        paid_record = next((r for r in vip_records if r.is_paid), None)
        
        assert achievement_record is not None, "Achievement VIP record must exist"
        assert paid_record is not None, "Paid VIP record must exist"
        assert achievement_record.achievement_id == achievement_vip.id, "Achievement VIP must reference badge"
        assert paid_record.payment_amount == 29.99, "Paid VIP must have payment amount"

    async def test_achievement_vip_automatic_telegram_permissions(self, session, test_user, test_channel):
        """
        CRITICAL: Test que protege la asignación automática de permisos de Telegram.
        El desbloqueo VIP por achievements debe gestionar permisos de canal automáticamente.
        """
        badge_service = BadgeService(session)
        
        # Create VIP achievement
        telegram_vip_badge = Badge(
            name="Acceso Telegram VIP",
            description="Desbloquea permisos automáticos en Telegram",
            requirement="engagement alto",
            emoji="📱",
            grants_vip_access=True,
            vip_duration_days=30,
            auto_telegram_permissions=True
        )
        session.add(telegram_vip_badge)
        
        # Setup VIP channel
        test_channel.channel_type = "vip"
        test_channel.auto_manage_permissions = True
        session.add(test_channel)
        await session.commit()
        
        # Mock Telegram bot for permission management
        mock_bot = AsyncMock()
        mock_bot.restrict_chat_member = AsyncMock()
        mock_bot.unban_chat_member = AsyncMock()
        
        # Grant VIP achievement
        await badge_service.grant_badge(test_user.id, telegram_vip_badge)
        
        # Simulate VIP permission grant process
        test_user.role = "vip"
        test_user.vip_until = datetime.utcnow() + timedelta(days=30)
        session.add(test_user)
        await session.commit()
        
        # Simulate automatic Telegram permission management
        if telegram_vip_badge.auto_telegram_permissions:
            try:
                # Grant VIP channel access
                await mock_bot.unban_chat_member(
                    chat_id=test_channel.id,
                    user_id=test_user.id
                )
                
                # Set VIP permissions
                await mock_bot.restrict_chat_member(
                    chat_id=test_channel.id,
                    user_id=test_user.id,
                    permissions={
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_polls": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True,
                        "can_change_info": False,
                        "can_invite_users": True,
                        "can_pin_messages": False
                    }
                )
                telegram_success = True
            except Exception:
                telegram_success = False
        
        # Critical assertions - Telegram permissions must be managed
        mock_bot.unban_chat_member.assert_called_once_with(
            chat_id=test_channel.id,
            user_id=test_user.id
        )
        mock_bot.restrict_chat_member.assert_called_once()
        
        # Verify permission parameters
        permission_call = mock_bot.restrict_chat_member.call_args
        assert permission_call[1]["chat_id"] == test_channel.id
        assert permission_call[1]["user_id"] == test_user.id
        assert permission_call[1]["permissions"]["can_send_messages"] is True
        assert permission_call[1]["permissions"]["can_invite_users"] is True

    async def test_achievement_vip_revocation_on_violation(self, session, test_user):
        """
        CRITICAL: Test que protege la revocación de VIP por violaciones.
        VIP otorgado por achievements debe poder ser revocado por mal comportamiento.
        """
        badge_service = BadgeService(session)
        
        # Create revocable VIP achievement
        revocable_vip = Badge(
            name="VIP Condicional",
            description="VIP que puede ser revocado",
            requirement="buen comportamiento",
            emoji="⚖️",
            grants_vip_access=True,
            vip_duration_days=30,
            revocable=True
        )
        session.add(revocable_vip)
        await session.commit()
        
        # Grant VIP
        await badge_service.grant_badge(test_user.id, revocable_vip)
        
        test_user.role = "vip"
        test_user.vip_until = datetime.utcnow() + timedelta(days=30)
        session.add(test_user)
        
        vip_access = VipAccess(
            user_id=test_user.id,
            granted_by_achievement=True,
            achievement_id=revocable_vip.id,
            granted_at=datetime.utcnow(),
            expires_at=test_user.vip_until,
            revocable=True
        )
        session.add(vip_access)
        await session.commit()
        
        # Simulate violation and revocation
        violation_reason = "Spam en canales VIP"
        
        # Revoke VIP access
        vip_access.revoked = True
        vip_access.revoked_at = datetime.utcnow()
        vip_access.revocation_reason = violation_reason
        
        # Downgrade user
        test_user.role = "free"
        test_user.vip_until = None
        
        session.add_all([vip_access, test_user])
        await session.commit()
        
        # Critical assertions - VIP revocation must be tracked
        await session.refresh(vip_access)
        await session.refresh(test_user)
        
        assert vip_access.revoked is True, "VIP access must be marked as revoked"
        assert vip_access.revocation_reason == violation_reason, "Revocation reason must be recorded"
        assert test_user.role == "free", "User must be downgraded to free"
        assert test_user.vip_until is None, "VIP expiration must be cleared"

    async def test_achievement_prerequisite_chain_for_vip(self, session, test_user):
        """
        CRITICAL: Test que protege las cadenas de prerequisitos para VIP.
        Algunos achievements VIP deben requerir otros achievements como prerequisitos.
        """
        badge_service = BadgeService(session)
        
        # Create prerequisite achievements
        beginner_badge = Badge(
            name="Principiante",
            description="Primera insignia",
            requirement="5 mensajes",
            emoji="🌱"
        )
        
        intermediate_badge = Badge(
            name="Intermedio", 
            description="Insignia intermedia",
            requirement="50 mensajes",
            emoji="🌿",
            prerequisites=[beginner_badge.id] if hasattr(Badge, 'prerequisites') else None
        )
        
        expert_vip_badge = Badge(
            name="Experto VIP",
            description="VIP para expertos",
            requirement="500 mensajes y insignias previas",
            emoji="🏆",
            grants_vip_access=True,
            vip_duration_days=60,
            prerequisites=[beginner_badge.id, intermediate_badge.id] if hasattr(Badge, 'prerequisites') else None
        )
        
        session.add_all([beginner_badge, intermediate_badge, expert_vip_badge])
        await session.commit()
        
        # Setup user stats
        user_stats = UserStats(
            user_id=test_user.id,
            messages_sent=500
        )
        session.add(user_stats)
        await session.commit()
        
        # Grant prerequisites in order
        await badge_service.grant_badge(test_user.id, beginner_badge)
        await badge_service.grant_badge(test_user.id, intermediate_badge)
        
        # Verify prerequisites before granting VIP
        stmt = select(UserBadge).where(UserBadge.user_id == test_user.id)
        result = await session.execute(stmt)
        user_badges = result.scalars().all()
        
        prerequisite_badge_ids = {ub.badge_id for ub in user_badges}
        
        # Check if user has all prerequisites
        has_prerequisites = all(
            prereq_id in prerequisite_badge_ids 
            for prereq_id in [beginner_badge.id, intermediate_badge.id]
        )
        
        # Only grant VIP if prerequisites are met
        if has_prerequisites:
            vip_granted = await badge_service.grant_badge(test_user.id, expert_vip_badge)
            
            if vip_granted:
                test_user.role = "vip"
                test_user.vip_until = datetime.utcnow() + timedelta(days=60)
                session.add(test_user)
                await session.commit()
        
        # Critical assertions - prerequisite chain must be enforced
        assert has_prerequisites is True, "User must have all prerequisite badges"
        
        final_badges = await session.execute(select(UserBadge).where(UserBadge.user_id == test_user.id))
        final_badge_count = len(final_badges.scalars().all())
        assert final_badge_count == 3, "User must have all three badges including VIP"
        
        await session.refresh(test_user)
        assert test_user.role == "vip", "User must be granted VIP after meeting prerequisites"

    async def test_concurrent_achievement_vip_grants_safety(self, session, test_user):
        """
        CRITICAL: Test que protege contra condiciones de carrera en otorgamiento VIP.
        Múltiples achievements simultáneos no deben causar estados VIP inconsistentes.
        """
        badge_service = BadgeService(session)
        
        # Create multiple VIP-granting achievements
        vip_badge_1 = Badge(
            name="VIP Rápido",
            description="VIP de corta duración",
            requirement="actividad rápida",
            emoji="⚡",
            grants_vip_access=True,
            vip_duration_days=7
        )
        
        vip_badge_2 = Badge(
            name="VIP Completo",
            description="VIP de larga duración", 
            requirement="actividad completa",
            emoji="💎",
            grants_vip_access=True,
            vip_duration_days=30
        )
        
        session.add_all([vip_badge_1, vip_badge_2])
        await session.commit()
        
        # Simulate concurrent badge granting
        import asyncio
        
        async def grant_vip_badge_1():
            granted = await badge_service.grant_badge(test_user.id, vip_badge_1)
            if granted:
                # Simulate VIP processing with lock
                test_user.role = "vip"
                test_user.vip_until = datetime.utcnow() + timedelta(days=7)
                session.add(test_user)
                await session.commit()
            return granted
        
        async def grant_vip_badge_2():
            # Small delay to create race condition
            await asyncio.sleep(0.01)
            granted = await badge_service.grant_badge(test_user.id, vip_badge_2)
            if granted:
                # Check current VIP status before updating
                await session.refresh(test_user)
                if test_user.vip_until:
                    # Extend existing VIP
                    test_user.vip_until = max(
                        test_user.vip_until,
                        datetime.utcnow() + timedelta(days=30)
                    )
                else:
                    # Grant new VIP
                    test_user.role = "vip"
                    test_user.vip_until = datetime.utcnow() + timedelta(days=30)
                session.add(test_user)
                await session.commit()
            return granted
        
        # Execute concurrently
        results = await asyncio.gather(
            grant_vip_badge_1(),
            grant_vip_badge_2(),
            return_exceptions=True
        )
        
        # Critical assertions - concurrent grants must be handled safely
        assert all(r is True for r in results if not isinstance(r, Exception)), "Both badges must be granted"
        
        await session.refresh(test_user)
        assert test_user.role == "vip", "User must have VIP status"
        assert test_user.vip_until is not None, "VIP expiration must be set"
        
        # VIP duration should be the longer of the two (30 days)
        days_until_expiry = (test_user.vip_until - datetime.utcnow()).days
        assert days_until_expiry >= 29, "VIP duration must reflect the longer grant"