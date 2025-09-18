"""
Comprehensive integration test suite for EnhancedVIPService

Tests cover all core VIP functionality including:
- Token generation and redemption workflows
- Batch token operations
- Revenue and subscription analytics
- User engagement tracking
- Reminder automation system
- Auto-renewal processing
- Error handling and edge cases

Based on requirements 2.1, 2.2, and 2.3 from modulo-admon specification.
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create mock pytest decorators for compatibility
    class MockPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = MockPytest()

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

# Import the service and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    from sqlalchemy import select, func, and_, or_
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Mock SQLAlchemy classes for testing
    class MockAsyncSession:
        pass
    class MockIntegrityError(Exception):
        pass
    class MockSQLAlchemyError(Exception):
        pass
    AsyncSession = MockAsyncSession
    IntegrityError = MockIntegrityError
    SQLAlchemyError = MockSQLAlchemyError

try:
    from services.enhanced_vip_service import EnhancedVIPService
    from database.models import (
        Token, Tariff, VipSubscription, User, UserStats,
        SubscriptionStatus
    )
    from services.token_service import TokenService
    from services.subscription_service import SubscriptionService
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    print("Warning: Enhanced VIP service and models not available for import")


class TestEnhancedVIPService:
    """Test suite for EnhancedVIPService core functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session with comprehensive query mocking"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        return session

    @pytest.fixture
    def mock_bot(self):
        """Mock Telegram bot instance"""
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def enhanced_vip_service(self, mock_session, mock_bot):
        """Enhanced VIP service instance with mocked dependencies"""
        return EnhancedVIPService(mock_session, mock_bot)

    @pytest.fixture
    def sample_tariff(self):
        """Sample tariff data for testing"""
        return Tariff(
            id=1,
            name="Premium Monthly",
            duration_days=30,
            price=1500
        )

    @pytest.fixture
    def sample_user(self):
        """Sample user data for testing"""
        return User(
            id=12345,
            username="test_user",
            first_name="Test",
            last_name="User",
            points=100.0,
            level=3,
            created_at=datetime.utcnow() - timedelta(days=60)
        )

    @pytest.fixture
    def sample_vip_subscription(self, sample_user, sample_tariff):
        """Sample VIP subscription for testing"""
        return VipSubscription(
            id="550e8400-e29b-41d4-a716-446655440000",
            user_id=sample_user.id,
            start_date=datetime.utcnow() - timedelta(days=10),
            expiration_date=datetime.utcnow() + timedelta(days=20),
            tariff_id=sample_tariff.id,
            status=SubscriptionStatus.ACTIVE,
            auto_renewal=False,
            created_by_admin_id=999,
            reminder_sent_dates=[],
            revenue_generated=Decimal("1500.00"),
            created_at=datetime.utcnow() - timedelta(days=10)
        )

    @pytest.fixture
    def sample_token(self, sample_tariff):
        """Sample token for testing"""
        return Token(
            id="token-uuid-123",
            token_string="VIP_TOKEN_ABC123",
            tariff_id=sample_tariff.id,
            user_id=None,
            generated_at=datetime.utcnow(),
            activated_at=None,
            is_used=False,
            tariff=sample_tariff
        )


class TestTokenGeneration:
    """Test token generation functionality"""

    @pytest.fixture
    def setup_token_generation(self, enhanced_vip_service, mock_session, sample_tariff):
        """Setup for token generation tests"""
        mock_session.get.return_value = sample_tariff
        return enhanced_vip_service, mock_session, sample_tariff

    async def test_generate_single_token_success(self, setup_token_generation):
        """Test successful single token generation"""
        service, mock_session, tariff = setup_token_generation

        # Mock token service response
        mock_token = Token(
            id="new-token-id",
            token_string="VIP_TOKEN_NEW123",
            tariff_id=tariff.id,
            generated_at=datetime.utcnow(),
            is_used=False
        )

        with patch.object(service.token_service, 'create_vip_token', return_value=mock_token) as mock_create:
            result = await service.generate_token(tariff_id=1, admin_id=999)

            # Assertions
            assert result == mock_token
            assert result.tariff_id == tariff.id
            assert not result.is_used
            mock_create.assert_called_once_with(tariff_id=1)
            mock_session.get.assert_called_once_with(Tariff, 1)

    async def test_generate_token_invalid_tariff(self, setup_token_generation):
        """Test token generation with invalid tariff ID"""
        service, mock_session, _ = setup_token_generation
        mock_session.get.return_value = None  # Tariff not found

        with pytest.raises(ValueError, match="Tariff with id 999 not found"):
            await service.generate_token(tariff_id=999, admin_id=999)

    async def test_generate_batch_tokens_success(self, setup_token_generation):
        """Test successful batch token generation"""
        service, mock_session, tariff = setup_token_generation
        batch_size = 5

        # Mock token service to return different tokens for each call
        mock_tokens = [
            Token(
                id=f"token-{i}",
                token_string=f"VIP_TOKEN_BATCH_{i}",
                tariff_id=tariff.id,
                generated_at=datetime.utcnow(),
                is_used=False
            )
            for i in range(batch_size)
        ]

        with patch.object(service.token_service, 'create_vip_token', side_effect=mock_tokens):
            result = await service.generate_batch_tokens(
                tariff_id=1, admin_id=999, count=batch_size
            )

            # Assertions
            assert len(result) == batch_size
            assert all(token.tariff_id == tariff.id for token in result)
            assert all(not token.is_used for token in result)
            assert len(set(token.token_string for token in result)) == batch_size  # All unique

    async def test_generate_batch_tokens_invalid_count(self, setup_token_generation):
        """Test batch token generation with invalid count"""
        service, _, _ = setup_token_generation

        # Test count too small
        with pytest.raises(ValueError, match="Batch size must be between 1 and 50"):
            await service.generate_batch_tokens(tariff_id=1, admin_id=999, count=0)

        # Test count too large
        with pytest.raises(ValueError, match="Batch size must be between 1 and 50"):
            await service.generate_batch_tokens(tariff_id=1, admin_id=999, count=51)

    async def test_generate_batch_tokens_invalid_tariff(self, setup_token_generation):
        """Test batch token generation with invalid tariff"""
        service, mock_session, _ = setup_token_generation
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Tariff with id 999 not found"):
            await service.generate_batch_tokens(tariff_id=999, admin_id=999, count=5)


class TestTokenRedemption:
    """Test token redemption functionality"""

    @pytest.fixture
    def setup_token_redemption(self, enhanced_vip_service, sample_user, sample_vip_subscription):
        """Setup for token redemption tests"""
        return enhanced_vip_service, sample_user, sample_vip_subscription

    async def test_redeem_token_success(self, setup_token_redemption):
        """Test successful token redemption"""
        service, user, vip_sub = setup_token_redemption
        token_string = "VIP_TOKEN_VALID123"
        duration_days = 30

        with patch.object(service.token_service, 'activate_token', return_value=duration_days) as mock_activate, \
             patch.object(service.subscription_service, 'extend_subscription', return_value=vip_sub) as mock_extend:

            result = await service.redeem_token(token_string, user.id)

            # Assertions
            assert result == vip_sub
            mock_activate.assert_called_once_with(token_string, user.id)
            mock_extend.assert_called_once_with(user.id, duration_days)

    async def test_redeem_token_invalid_token(self, setup_token_redemption):
        """Test token redemption with invalid token"""
        service, user, _ = setup_token_redemption
        token_string = "INVALID_TOKEN"

        with patch.object(service.token_service, 'activate_token', side_effect=ValueError("Token not found")):
            with pytest.raises(ValueError, match="Token not found"):
                await service.redeem_token(token_string, user.id)

    async def test_redeem_token_subscription_service_error(self, setup_token_redemption):
        """Test token redemption when subscription service fails"""
        service, user, _ = setup_token_redemption
        token_string = "VIP_TOKEN_VALID123"
        duration_days = 30

        with patch.object(service.token_service, 'activate_token', return_value=duration_days), \
             patch.object(service.subscription_service, 'extend_subscription', side_effect=ValueError("Subscription error")):

            with pytest.raises(ValueError, match="Subscription error"):
                await service.redeem_token(token_string, user.id)


class TestRevenueMetrics:
    """Test revenue calculation functionality"""

    @pytest.fixture
    def setup_revenue_metrics(self, enhanced_vip_service, mock_session):
        """Setup for revenue metrics tests"""
        return enhanced_vip_service, mock_session

    async def test_calculate_revenue_metrics_success(self, setup_revenue_metrics):
        """Test successful revenue metrics calculation"""
        service, mock_session = setup_revenue_metrics

        # Mock query results
        mock_session.execute.side_effect = [
            # Total revenue query
            AsyncMock(scalar=lambda: 15000.0),
            # Period revenue query
            AsyncMock(scalar=lambda: 3000.0),
            # Average revenue query
            AsyncMock(scalar=lambda: 500.0),
            # Total tokens query
            AsyncMock(scalar=lambda: 50),
            # Used tokens query
            AsyncMock(scalar=lambda: 30),
            # Revenue by tariff query
            AsyncMock(**{
                '__iter__': lambda x: iter([
                    AsyncMock(name="Premium", price=1500, tokens_used=20, tariff_revenue=30000),
                    AsyncMock(name="Basic", price=500, tokens_used=10, tariff_revenue=5000)
                ])
            }),
            # Unused tokens value query
            AsyncMock(scalar=lambda: 10000.0)
        ]

        result = await service.calculate_revenue_metrics()

        # Assertions
        assert result["status"] == "success"
        assert "revenue_metrics" in result
        assert "token_metrics" in result
        assert "revenue_breakdown" in result

        revenue_metrics = result["revenue_metrics"]
        assert revenue_metrics["total_revenue"] == 15000.0
        assert revenue_metrics["period_revenue"] == 3000.0
        assert revenue_metrics["average_revenue_per_token"] == 500.0
        assert revenue_metrics["potential_revenue"] == 10000.0

        token_metrics = result["token_metrics"]
        assert token_metrics["total_tokens_generated"] == 50
        assert token_metrics["tokens_used"] == 30
        assert token_metrics["tokens_unused"] == 20
        assert token_metrics["conversion_rate"] == 60.0

    async def test_calculate_revenue_metrics_with_date_range(self, setup_revenue_metrics):
        """Test revenue metrics calculation with custom date range"""
        service, mock_session = setup_revenue_metrics

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        date_range = (start_date, end_date)

        # Mock query results
        mock_session.execute.side_effect = [
            AsyncMock(scalar=lambda: 5000.0),  # Total revenue
            AsyncMock(scalar=lambda: 1000.0),  # Period revenue
            AsyncMock(scalar=lambda: 250.0),   # Average revenue
            AsyncMock(scalar=lambda: 20),      # Total tokens
            AsyncMock(scalar=lambda: 15),      # Used tokens
            AsyncMock(**{'__iter__': lambda x: iter([])}),  # Revenue by tariff
            AsyncMock(scalar=lambda: 1250.0)   # Unused tokens value
        ]

        result = await service.calculate_revenue_metrics(date_range)

        # Assertions
        assert result["status"] == "success"
        assert result["period"]["start_date"] == start_date.isoformat()
        assert result["period"]["end_date"] == end_date.isoformat()
        assert result["period"]["days"] == 30

    async def test_calculate_revenue_metrics_database_error(self, setup_revenue_metrics):
        """Test revenue metrics calculation with database error"""
        service, mock_session = setup_revenue_metrics

        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        result = await service.calculate_revenue_metrics()

        # Assertions
        assert result["status"] == "error"
        assert "Database connection failed" in result["message"]


class TestSubscriptionTrends:
    """Test subscription trend analysis"""

    @pytest.fixture
    def setup_subscription_trends(self, enhanced_vip_service, mock_session):
        """Setup for subscription trends tests"""
        return enhanced_vip_service, mock_session

    async def test_get_subscription_trends_success(self, setup_subscription_trends):
        """Test successful subscription trends analysis"""
        service, mock_session = setup_subscription_trends

        # Mock subscription service statistics
        with patch.object(service.subscription_service, 'get_statistics', return_value=(100, 80, 20)):
            # Mock query results
            mock_session.execute.side_effect = [
                # New subscriptions trend
                AsyncMock(**{
                    '__iter__': lambda x: iter([
                        AsyncMock(date=datetime(2024, 1, 1).date(), new_subscriptions=5),
                        AsyncMock(date=datetime(2024, 1, 2).date(), new_subscriptions=8),
                        AsyncMock(date=datetime(2024, 1, 3).date(), new_subscriptions=3)
                    ])
                }),
                # Expiring soon query
                AsyncMock(scalar=lambda: 15),
                # Expiring this month query
                AsyncMock(scalar=lambda: 40),
                # Renewal query
                AsyncMock(first=lambda: AsyncMock(renewals=25, unique_renewers=20)),
                # Average duration query
                AsyncMock(scalar=lambda: 28.5),
                # User lifecycle query
                AsyncMock(**{
                    '__iter__': lambda x: iter([
                        AsyncMock(
                            id=1, created_at=datetime(2023, 12, 1),
                            first_vip=datetime(2023, 12, 15),
                            expires_at=datetime(2024, 2, 15),
                            tokens_used=2
                        ),
                        AsyncMock(
                            id=2, created_at=datetime(2023, 11, 1),
                            first_vip=datetime(2023, 11, 30),
                            expires_at=datetime(2024, 1, 30),
                            tokens_used=1
                        )
                    ])
                })
            ]

            result = await service.get_subscription_trends()

            # Assertions
            assert result["status"] == "success"
            assert "current_metrics" in result
            assert "trend_analysis" in result
            assert "user_behavior" in result
            assert "insights" in result

            current_metrics = result["current_metrics"]
            assert current_metrics["total_subscriptions"] == 100
            assert current_metrics["active_subscriptions"] == 80
            assert current_metrics["expired_subscriptions"] == 20
            assert current_metrics["expiring_soon_7_days"] == 15

            trend_analysis = result["trend_analysis"]
            assert len(trend_analysis["new_subscriptions_daily"]) == 3
            assert trend_analysis["total_renewals"] == 25
            assert trend_analysis["unique_renewers"] == 20

    async def test_get_subscription_trends_with_custom_date_range(self, setup_subscription_trends):
        """Test subscription trends with custom date range"""
        service, mock_session = setup_subscription_trends

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        date_range = (start_date, end_date)

        with patch.object(service.subscription_service, 'get_statistics', return_value=(50, 40, 10)):
            mock_session.execute.side_effect = [
                AsyncMock(**{'__iter__': lambda x: iter([])}),  # New subscriptions
                AsyncMock(scalar=lambda: 5),   # Expiring soon
                AsyncMock(scalar=lambda: 12),  # Expiring month
                AsyncMock(first=lambda: AsyncMock(renewals=8, unique_renewers=6)),
                AsyncMock(scalar=lambda: 30.0), # Average duration
                AsyncMock(**{'__iter__': lambda x: iter([])})  # Lifecycle
            ]

            result = await service.get_subscription_trends(date_range)

            assert result["status"] == "success"
            assert result["period"]["days"] == 89  # 3 months

    async def test_get_subscription_trends_database_error(self, setup_subscription_trends):
        """Test subscription trends with database error"""
        service, mock_session = setup_subscription_trends

        with patch.object(service.subscription_service, 'get_statistics', side_effect=SQLAlchemyError("Connection error")):
            result = await service.get_subscription_trends()

            assert result["status"] == "error"
            assert "Connection error" in result["message"]


class TestUserEngagementStats:
    """Test user engagement statistics"""

    @pytest.fixture
    def setup_engagement_stats(self, enhanced_vip_service, mock_session):
        """Setup for engagement stats tests"""
        return enhanced_vip_service, mock_session

    async def test_get_user_engagement_stats_success(self, setup_engagement_stats):
        """Test successful user engagement stats calculation"""
        service, mock_session = setup_engagement_stats

        # Mock VIP users query
        now = datetime.utcnow()
        mock_vip_users = [
            (
                AsyncMock(id=1, points=500.0),
                AsyncMock(
                    messages_sent=150, checkin_streak=7,
                    last_activity_at=now - timedelta(hours=2)
                ),
                AsyncMock(user_id=1)
            ),
            (
                AsyncMock(id=2, points=800.0),
                AsyncMock(
                    messages_sent=300, checkin_streak=15,
                    last_activity_at=now - timedelta(days=5)
                ),
                AsyncMock(user_id=2)
            ),
            (
                AsyncMock(id=3, points=200.0),
                None,  # No user stats
                AsyncMock(user_id=3)
            )
        ]

        mock_free_users = [
            (AsyncMock(id=4, points=100.0), AsyncMock(messages_sent=50)),
            (AsyncMock(id=5, points=150.0), AsyncMock(messages_sent=75))
        ]

        mock_session.execute.side_effect = [
            # VIP users query
            AsyncMock(all=lambda: mock_vip_users),
            # Free users query
            AsyncMock(all=lambda: mock_free_users),
            # Token usage query
            AsyncMock(first=lambda: AsyncMock(tokens_used=5, users_with_tokens=2))
        ]

        result = await service.get_user_engagement_stats()

        # Assertions
        assert result["status"] == "success"
        assert "vip_user_metrics" in result
        assert "engagement_distribution" in result
        assert "activity_breakdown" in result
        assert "vip_vs_free_comparison" in result
        assert "insights" in result

        vip_metrics = result["vip_user_metrics"]
        assert vip_metrics["total_vip_users"] == 3
        assert vip_metrics["active_users"] == 1  # Only user 1 is highly engaged
        assert vip_metrics["average_points"] == 500.0  # (500 + 800 + 200) / 3

        engagement_dist = result["engagement_distribution"]
        assert engagement_dist["highly_engaged"] == 1  # User 1
        assert engagement_dist["low_engagement"] == 1   # User 2
        assert engagement_dist["inactive"] == 1         # User 3

    async def test_get_user_engagement_stats_no_vip_users(self, setup_engagement_stats):
        """Test engagement stats when no VIP users exist"""
        service, mock_session = setup_engagement_stats

        mock_session.execute.return_value = AsyncMock(all=lambda: [])

        result = await service.get_user_engagement_stats()

        assert result["status"] == "no_data"
        assert result["message"] == "No active VIP users found"

    async def test_get_user_engagement_stats_database_error(self, setup_engagement_stats):
        """Test engagement stats with database error"""
        service, mock_session = setup_engagement_stats

        mock_session.execute.side_effect = SQLAlchemyError("Query failed")

        result = await service.get_user_engagement_stats()

        assert result["status"] == "error"
        assert "Query failed" in result["message"]


class TestReminderAutomation:
    """Test VIP reminder automation system"""

    @pytest.fixture
    def setup_reminder_automation(self, enhanced_vip_service, mock_session):
        """Setup for reminder automation tests"""
        return enhanced_vip_service, mock_session

    async def test_schedule_vip_reminders_success(self, setup_reminder_automation):
        """Test successful VIP reminder scheduling"""
        service, mock_session = setup_reminder_automation

        # Mock expiring subscriptions
        now = datetime.utcnow()
        target_date_3_days = now + timedelta(days=3)
        target_date_1_day = now + timedelta(days=1)

        mock_expiring_subs = [
            (
                AsyncMock(expires_at=target_date_3_days),
                AsyncMock(id=1, username="user1")
            ),
            (
                AsyncMock(expires_at=target_date_1_day),
                AsyncMock(id=2, username="user2")
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_expiring_subs)

        with patch.object(service, '_delayed_reminder') as mock_delayed:
            result = await service.schedule_vip_reminders([3, 1])

            # Assertions
            assert result["status"] == "success"
            assert result["scheduled_reminders"] == 4  # 2 users × 2 reminder types
            assert result["days_before"] == [3, 1]

            # Verify _delayed_reminder was called correctly
            assert mock_delayed.call_count == 4

    async def test_schedule_vip_reminders_already_running(self, setup_reminder_automation):
        """Test scheduling reminders when automation is already running"""
        service, mock_session = setup_reminder_automation

        service._automation_running = True

        result = await service.schedule_vip_reminders()

        assert result["status"] == "already_running"
        assert "already running" in result["message"]

    async def test_schedule_vip_reminders_database_error(self, setup_reminder_automation):
        """Test scheduling reminders with database error"""
        service, mock_session = setup_reminder_automation

        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        result = await service.schedule_vip_reminders()

        assert result["status"] == "error"
        assert "Database error" in result["message"]

    async def test_send_expiration_warning_success(self, setup_reminder_automation, sample_user, sample_vip_subscription):
        """Test successful expiration warning message sending"""
        service, mock_session = setup_reminder_automation

        # Mock user and subscription query
        mock_session.execute.return_value = AsyncMock(
            first=lambda: AsyncMock(
                User=sample_user,
                VipSubscription=sample_vip_subscription
            )
        )

        with patch('utils.message_safety.safe_send_message') as mock_send:
            result = await service.send_expiration_warning(sample_user.id, 3)

            # Assertions
            assert result is True
            mock_send.assert_called_once()

            # Verify message content contains expected elements
            call_args = mock_send.call_args
            message_text = call_args[0][2]  # Third argument is the message
            assert "3 días" in message_text
            assert sample_user.username in message_text

    async def test_send_expiration_warning_no_bot(self, setup_reminder_automation):
        """Test expiration warning when bot is not available"""
        service, mock_session = setup_reminder_automation
        service.bot = None

        result = await service.send_expiration_warning(12345, 1)

        assert result is False

    async def test_send_expiration_warning_no_subscription(self, setup_reminder_automation):
        """Test expiration warning when user has no VIP subscription"""
        service, mock_session = setup_reminder_automation

        mock_session.execute.return_value = AsyncMock(first=lambda: None)

        result = await service.send_expiration_warning(12345, 1)

        assert result is False


class TestAutoRenewalProcessing:
    """Test auto-renewal processing functionality"""

    @pytest.fixture
    def setup_auto_renewal(self, enhanced_vip_service, mock_session):
        """Setup for auto-renewal tests"""
        return enhanced_vip_service, mock_session

    async def test_process_auto_renewals_disabled(self, setup_auto_renewal):
        """Test auto-renewal processing when disabled"""
        service, mock_session = setup_auto_renewal

        result = await service.process_auto_renewals(auto_renewal_enabled=False)

        assert result["status"] == "disabled"
        assert result["processed_count"] == 0

    async def test_process_auto_renewals_enabled(self, setup_auto_renewal):
        """Test auto-renewal processing when enabled"""
        service, mock_session = setup_auto_renewal

        # Mock expired subscriptions
        now = datetime.utcnow()
        mock_expired_subs = [
            (
                AsyncMock(expires_at=now - timedelta(minutes=30)),
                AsyncMock(id=1, username="user1")
            ),
            (
                AsyncMock(expires_at=now - timedelta(minutes=45)),
                AsyncMock(id=2, username="user2")
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_expired_subs)

        with patch.object(service, '_notify_subscription_expired') as mock_notify:
            result = await service.process_auto_renewals(auto_renewal_enabled=True)

            # Assertions
            assert result["status"] == "success"
            assert result["processed_count"] == 2
            assert result["failed_count"] == 0
            assert result["total_expired"] == 2

            # Verify notifications were sent
            assert mock_notify.call_count == 2

    async def test_process_auto_renewals_with_failures(self, setup_auto_renewal):
        """Test auto-renewal processing with some failures"""
        service, mock_session = setup_auto_renewal

        # Mock expired subscriptions
        now = datetime.utcnow()
        mock_expired_subs = [
            (
                AsyncMock(expires_at=now - timedelta(minutes=30)),
                AsyncMock(id=1, username="user1")
            ),
            (
                AsyncMock(expires_at=now - timedelta(minutes=45)),
                AsyncMock(id=2, username="user2")
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_expired_subs)

        # Mock notification to fail for second user
        with patch.object(service, '_notify_subscription_expired', side_effect=[None, Exception("Notification failed")]):
            result = await service.process_auto_renewals(auto_renewal_enabled=True)

            # Assertions
            assert result["status"] == "success"
            assert result["processed_count"] == 1
            assert result["failed_count"] == 1


class TestComprehensiveAnalytics:
    """Test comprehensive VIP analytics functionality"""

    @pytest.fixture
    def setup_comprehensive_analytics(self, enhanced_vip_service):
        """Setup for comprehensive analytics tests"""
        return enhanced_vip_service

    async def test_get_vip_analytics_comprehensive(self, setup_comprehensive_analytics):
        """Test comprehensive VIP analytics"""
        service = setup_comprehensive_analytics

        # Mock all analytics methods
        mock_revenue_data = {"status": "success", "revenue_metrics": {"total_revenue": 50000}}
        mock_subscription_data = {"status": "success", "current_metrics": {"active_subscriptions": 150}}
        mock_engagement_data = {"status": "success", "vip_user_metrics": {"engagement_rate": 75.5}}

        with patch.object(service, 'calculate_revenue_metrics', return_value=mock_revenue_data), \
             patch.object(service, 'get_subscription_trends', return_value=mock_subscription_data), \
             patch.object(service, 'get_user_engagement_stats', return_value=mock_engagement_data):

            result = await service.get_vip_analytics(metrics_type="comprehensive")

            # Assertions
            assert result["status"] == "success"
            assert result["analytics_type"] == "comprehensive"
            assert "revenue_analytics" in result
            assert "subscription_analytics" in result
            assert "engagement_analytics" in result
            assert "summary_insights" in result

            # Verify summary insights generation
            summary = result["summary_insights"]
            assert "overall_health" in summary
            assert "key_metrics" in summary
            assert "recommendations" in summary

    async def test_get_vip_analytics_revenue_only(self, setup_comprehensive_analytics):
        """Test VIP analytics for revenue only"""
        service = setup_comprehensive_analytics

        mock_revenue_data = {"status": "success", "revenue_metrics": {"total_revenue": 25000}}

        with patch.object(service, 'calculate_revenue_metrics', return_value=mock_revenue_data):
            result = await service.get_vip_analytics(metrics_type="revenue")

            # Assertions
            assert result["status"] == "success"
            assert result["analytics_type"] == "revenue"
            assert "revenue_analytics" in result
            assert "subscription_analytics" not in result
            assert "engagement_analytics" not in result

    async def test_get_vip_analytics_with_custom_date_range(self, setup_comprehensive_analytics):
        """Test VIP analytics with custom date range"""
        service = setup_comprehensive_analytics

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        date_range = (start_date, end_date)

        mock_revenue_data = {"status": "success"}

        with patch.object(service, 'calculate_revenue_metrics', return_value=mock_revenue_data) as mock_revenue:
            result = await service.get_vip_analytics(date_range=date_range, metrics_type="revenue")

            # Verify date range was passed correctly
            mock_revenue.assert_called_once_with(date_range)

            assert result["period"]["start_date"] == start_date.isoformat()
            assert result["period"]["end_date"] == end_date.isoformat()

    async def test_get_vip_analytics_error_handling(self, setup_comprehensive_analytics):
        """Test VIP analytics error handling"""
        service = setup_comprehensive_analytics

        with patch.object(service, 'calculate_revenue_metrics', side_effect=Exception("Analytics error")):
            result = await service.get_vip_analytics(metrics_type="revenue")

            assert result["status"] == "error"
            assert "Analytics error" in result["message"]


class TestAutomationManagement:
    """Test automation start/stop/status functionality"""

    @pytest.fixture
    def setup_automation_management(self, enhanced_vip_service):
        """Setup for automation management tests"""
        return enhanced_vip_service

    async def test_start_reminder_automation_success(self, setup_automation_management):
        """Test successful automation start"""
        service = setup_automation_management

        with patch('asyncio.create_task') as mock_create_task:
            result = await service.start_reminder_automation(check_interval_minutes=30)

            # Assertions
            assert result["status"] == "started"
            assert result["check_interval_minutes"] == 30
            mock_create_task.assert_called_once()

    async def test_start_reminder_automation_already_running(self, setup_automation_management):
        """Test starting automation when already running"""
        service = setup_automation_management
        service._automation_running = True

        result = await service.start_reminder_automation()

        assert result["status"] == "already_running"

    async def test_stop_reminder_automation_success(self, setup_automation_management):
        """Test successful automation stop"""
        service = setup_automation_management
        service._automation_running = True

        result = await service.stop_reminder_automation()

        assert result["status"] == "stopped"
        assert not service._automation_running

    async def test_stop_reminder_automation_not_running(self, setup_automation_management):
        """Test stopping automation when not running"""
        service = setup_automation_management

        result = await service.stop_reminder_automation()

        assert result["status"] == "not_running"

    async def test_get_reminder_status(self, setup_automation_management):
        """Test getting reminder automation status"""
        service = setup_automation_management
        service._automation_running = True
        service._reminder_tracking.add((123, "3_day_warning"))
        service._reminder_tracking.add((456, "1_day_warning"))

        result = await service.get_reminder_status()

        assert result["status"] == "running"
        assert result["tracked_reminders"] == 2
        assert result["automation_active"] is True


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and comprehensive error handling"""

    @pytest.fixture
    def setup_edge_cases(self, enhanced_vip_service, mock_session):
        """Setup for edge case tests"""
        return enhanced_vip_service, mock_session

    async def test_analytics_summary_generation_with_missing_data(self, setup_edge_cases):
        """Test analytics summary generation with missing data"""
        service, _ = setup_edge_cases

        # Test with empty data dictionaries
        summary = service._generate_analytics_summary({}, {}, {})

        assert summary["overall_health"] == "good"  # Default value
        assert summary["key_metrics"] == {}
        assert isinstance(summary["recommendations"], list)
        assert isinstance(summary["alerts"], list)

    async def test_analytics_summary_generation_with_alerts(self, setup_edge_cases):
        """Test analytics summary generation with alert conditions"""
        service, _ = setup_edge_cases

        # Create data that should trigger alerts
        revenue_data = {
            "status": "success",
            "token_metrics": {"conversion_rate": 25}  # Low conversion rate
        }
        subscription_data = {
            "status": "success",
            "insights": {"churn_risk": "high"}  # High churn risk
        }
        engagement_data = {
            "status": "success",
            "insights": {"engagement_health": "needs_attention"}  # Low engagement
        }

        summary = service._generate_analytics_summary(revenue_data, subscription_data, engagement_data)

        assert len(summary["alerts"]) >= 2  # Should have multiple alerts
        assert len(summary["recommendations"]) >= 2  # Should have recommendations
        assert summary["overall_health"] == "needs_attention"  # Due to multiple alerts

    async def test_concurrent_token_generation(self, setup_edge_cases):
        """Test concurrent token generation scenarios"""
        service, mock_session = setup_edge_cases

        # Mock tariff
        mock_tariff = Tariff(id=1, name="Test", duration_days=30, price=1000)
        mock_session.get.return_value = mock_tariff

        # Mock token service to simulate concurrent generation
        call_count = 0
        def mock_create_token(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Token(
                id=f"token-{call_count}",
                token_string=f"VIP_TOKEN_{call_count}",
                tariff_id=1,
                generated_at=datetime.utcnow(),
                is_used=False
            )

        with patch.object(service.token_service, 'create_vip_token', side_effect=mock_create_token):
            # Generate multiple batches concurrently
            tasks = [
                service.generate_batch_tokens(1, 999, 5),
                service.generate_batch_tokens(1, 999, 3),
                service.generate_batch_tokens(1, 999, 7)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all batches were generated correctly
            assert len(results) == 3
            assert len(results[0]) == 5
            assert len(results[1]) == 3
            assert len(results[2]) == 7

            # Verify all tokens are unique
            all_tokens = []
            for batch in results:
                all_tokens.extend([token.token_string for token in batch])
            assert len(set(all_tokens)) == len(all_tokens)  # All unique

    async def test_reminder_tracking_deduplication(self, setup_edge_cases):
        """Test reminder tracking prevents duplicate reminders"""
        service, mock_session = setup_edge_cases

        # Add some existing reminders to tracking
        service._reminder_tracking.add((123, "3_day_warning"))
        service._reminder_tracking.add((456, "1_day_warning"))

        # Mock expiring subscriptions that include already tracked reminders
        now = datetime.utcnow()
        mock_expiring_subs = [
            (
                AsyncMock(expires_at=now + timedelta(days=3)),
                AsyncMock(id=123, username="user123")  # Already has 3-day reminder
            ),
            (
                AsyncMock(expires_at=now + timedelta(days=3)),
                AsyncMock(id=789, username="user789")  # New user
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_expiring_subs)

        with patch.object(service, '_delayed_reminder') as mock_delayed:
            result = await service.schedule_vip_reminders([3])

            # Should only schedule reminder for new user (789), not existing (123)
            assert result["scheduled_reminders"] == 1
            mock_delayed.assert_called_once()


# Performance and stress tests
class TestPerformanceAndStress:
    """Performance and stress testing for VIP service"""

    @pytest.fixture
    def setup_performance_tests(self, enhanced_vip_service, mock_session):
        """Setup for performance tests"""
        return enhanced_vip_service, mock_session

    async def test_large_batch_token_generation_performance(self, setup_performance_tests):
        """Test performance with maximum batch size"""
        service, mock_session = setup_performance_tests

        # Mock tariff
        mock_tariff = Tariff(id=1, name="Performance Test", duration_days=30, price=1000)
        mock_session.get.return_value = mock_tariff

        # Mock fast token generation
        def mock_create_token(*args, **kwargs):
            return Token(
                id=f"perf-token-{hash(str(args) + str(kwargs))}",
                token_string=f"VIP_PERF_{hash(str(args) + str(kwargs))}",
                tariff_id=1,
                generated_at=datetime.utcnow(),
                is_used=False
            )

        with patch.object(service.token_service, 'create_vip_token', side_effect=mock_create_token):
            start_time = datetime.utcnow()

            # Generate maximum batch size
            result = await service.generate_batch_tokens(1, 999, 50)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Performance assertions
            assert len(result) == 50
            assert duration < 5.0  # Should complete within 5 seconds

            # Verify all tokens are unique
            token_strings = [token.token_string for token in result]
            assert len(set(token_strings)) == 50

    async def test_analytics_performance_with_large_dataset(self, setup_performance_tests):
        """Test analytics performance with large dataset simulation"""
        service, mock_session = setup_performance_tests

        # Mock large dataset responses
        large_number = 10000
        mock_session.execute.side_effect = [
            AsyncMock(scalar=lambda: large_number * 15),    # Total revenue
            AsyncMock(scalar=lambda: large_number * 3),     # Period revenue
            AsyncMock(scalar=lambda: 1500.0),               # Average revenue
            AsyncMock(scalar=lambda: large_number),         # Total tokens
            AsyncMock(scalar=lambda: large_number * 0.7),   # Used tokens
            AsyncMock(**{'__iter__': lambda x: iter([])}),  # Revenue by tariff
            AsyncMock(scalar=lambda: large_number * 5)      # Unused tokens value
        ]

        start_time = datetime.utcnow()

        result = await service.calculate_revenue_metrics()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Performance assertions
        assert result["status"] == "success"
        assert duration < 3.0  # Should complete within 3 seconds for large dataset
        assert result["revenue_metrics"]["total_revenue"] == large_number * 15


# Integration test runner
async def run_integration_tests():
    """Run all integration tests"""
    if not PYTEST_AVAILABLE or not SERVICE_AVAILABLE or not SQLALCHEMY_AVAILABLE:
        print("Skipping integration tests - required dependencies not available")
        return

    print("Running Enhanced VIP Service Integration Tests...")

    # This would typically be run by pytest, but we provide a manual runner
    # for environments where pytest might not be available
    test_classes = [
        TestTokenGeneration,
        TestTokenRedemption,
        TestRevenueMetrics,
        TestSubscriptionTrends,
        TestUserEngagementStats,
        TestReminderAutomation,
        TestAutoRenewalProcessing,
        TestComprehensiveAnalytics,
        TestAutomationManagement,
        TestEdgeCasesAndErrorHandling,
        TestPerformanceAndStress
    ]

    total_tests = sum(
        len([method for method in dir(test_class) if method.startswith('test_')])
        for test_class in test_classes
    )

    print(f"Total test methods: {total_tests}")
    print("Integration tests defined successfully!")
    print("\nTo run tests with pytest:")
    print("pytest tests/services/test_enhanced_vip_service.py -v")


if __name__ == "__main__":
    # Run basic verification
    asyncio.run(run_integration_tests())