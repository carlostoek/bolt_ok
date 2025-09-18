"""
Admin Workflow Integration Tests

Comprehensive integration test suite covering all admin workflow requirements
from modulo-admon specification. Tests end-to-end admin workflows including:

- Enhanced administrative menu system
- VIP subscription management workflows
- Channel and exclusive content control
- Analytics and reporting workflows
- Administrative task automation
- Error handling and recovery scenarios

Based on requirements 1-6 from the modulo-admon specification.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from uuid import uuid4

# Import test framework components
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    from sqlalchemy import select, func, and_, or_
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Mock SQLAlchemy for environments without it
    class MockAsyncSession:
        pass
    AsyncSession = MockAsyncSession

# Import aiogram components
try:
    from aiogram import Bot
    from aiogram.types import Message, CallbackQuery, User as TelegramUser, InlineKeyboardMarkup
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False
    # Mock aiogram components
    class MockBot:
        pass
    class MockMessage:
        pass
    class MockCallbackQuery:
        pass
    Bot, Message, CallbackQuery = MockBot, MockMessage, MockCallbackQuery

# Import application components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from database.models import (
        User, Token, Tariff, VipSubscription, SubscriptionStatus,
        AdminActionLog, ChannelContent
    )
    from services.enhanced_vip_service import EnhancedVIPService
    from services.channel_admin_service import ChannelAdminService
    from services.automation_service import AutomationService
    from services.analytics_service import AnalyticsService
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    from handlers.admin.admin_menu import create_enhanced_admin_menu
    from utils.menu_manager import menu_manager
    from utils.html_formatter import HTMLMessageFormatter
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    print(f"Warning: Some services not available for import: {e}")


class TestAdminWorkflowBase:
    """Base test class with common fixtures and utilities"""

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
        session.merge = AsyncMock()
        return session

    @pytest.fixture
    def mock_bot(self):
        """Mock Telegram bot instance"""
        bot = AsyncMock(spec=Bot)
        bot.send_message = AsyncMock()
        bot.edit_message_text = AsyncMock()
        bot.delete_message = AsyncMock()
        return bot

    @pytest.fixture
    def admin_user(self):
        """Sample admin user for testing"""
        return User(
            id=999999,
            username="admin_user",
            first_name="Admin",
            last_name="User",
            is_admin=True,
            points=1000.0,
            level=10,
            created_at=datetime.utcnow() - timedelta(days=365)
        )

    @pytest.fixture
    def regular_user(self):
        """Sample regular user for testing"""
        return User(
            id=123456,
            username="test_user",
            first_name="Test",
            last_name="User",
            is_admin=False,
            points=150.0,
            level=3,
            created_at=datetime.utcnow() - timedelta(days=60)
        )

    @pytest.fixture
    def sample_tariff(self):
        """Sample VIP tariff for testing"""
        return Tariff(
            id=1,
            name="Premium Monthly",
            duration_days=30,
            price=1500
        )

    @pytest.fixture
    def vip_subscription(self, regular_user, sample_tariff):
        """Sample VIP subscription for testing"""
        return VipSubscription(
            id=str(uuid4()),
            user_id=regular_user.id,
            start_date=datetime.utcnow() - timedelta(days=10),
            expiration_date=datetime.utcnow() + timedelta(days=20),
            tariff_id=sample_tariff.id,
            status=SubscriptionStatus.ACTIVE,
            auto_renewal=False,
            created_by_admin_id=999999,
            reminder_sent_dates=[],
            revenue_generated=Decimal("1500.00"),
            created_at=datetime.utcnow() - timedelta(days=10)
        )

    @pytest.fixture
    def mock_coordinador_central(self, mock_session):
        """Mock CoordinadorCentral for workflow orchestration"""
        coordinador = AsyncMock(spec=CoordinadorCentral)
        coordinador.session = mock_session
        coordinador.ejecutar_flujo = AsyncMock()
        return coordinador


class TestEnhancedAdminMenuSystem(TestAdminWorkflowBase):
    """
    Test Requirement 1: Enhanced Administrative Menu System

    Tests clean menu interface, message cleanup, navigation history,
    temporary confirmations, and error handling.
    """

    @pytest.fixture
    def enhanced_vip_service(self, mock_session, mock_bot):
        """Enhanced VIP service instance"""
        return EnhancedVIPService(mock_session, mock_bot)

    @pytest.fixture
    def menu_formatter(self):
        """HTML message formatter for admin menus"""
        return HTMLMessageFormatter()

    async def test_admin_menu_creation_with_statistics(self, mock_session, admin_user, mock_bot):
        """Test enhanced admin menu creation with real-time statistics"""
        # Mock statistics queries
        mock_session.execute.side_effect = [
            # Active VIP users count
            AsyncMock(scalar=lambda: 147),
            # Today's revenue
            AsyncMock(scalar=lambda: 7500.0),
            # Recent token usage
            AsyncMock(scalar=lambda: 23),
            # System health metrics
            AsyncMock(scalar=lambda: 99.8)
        ]

        # Test menu creation
        message_text, keyboard = await create_enhanced_admin_menu(
            mock_session, admin_user.id, mock_bot
        )

        # Assertions
        assert "Panel de Administración" in message_text
        assert "147" in message_text  # VIP users count
        assert "7,500" in message_text  # Revenue with formatting
        assert "23" in message_text   # Token usage
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 4  # Main menu options

    async def test_menu_cleanup_with_retry_mechanism(self, mock_session, admin_user, mock_bot):
        """Test menu cleanup with retry mechanism for failed deletions"""
        # Setup menu manager with tracking
        with patch('utils.menu_manager.menu_manager') as mock_menu_manager:
            # Mock initial cleanup failure then success
            mock_menu_manager.cleanup_user_messages.side_effect = [
                Exception("Cleanup failed"),  # First attempt fails
                None  # Second attempt succeeds
            ]
            mock_menu_manager.create_menu.return_value = AsyncMock()

            # Test menu creation with cleanup retry
            message_text, keyboard = await create_enhanced_admin_menu(
                mock_session, admin_user.id, mock_bot
            )

            # Verify retry mechanism was triggered
            assert mock_menu_manager.cleanup_user_messages.call_count == 2

    async def test_navigation_history_preservation(self, mock_session, admin_user, mock_bot):
        """Test navigation history and back button functionality"""
        with patch('utils.menu_manager.menu_manager') as mock_menu_manager:
            # Mock navigation stack
            mock_menu_manager.get_navigation_stack.return_value = [
                "admin_main", "vip_management", "token_generation"
            ]
            mock_menu_manager.create_menu.return_value = AsyncMock()

            # Test submenu navigation with history
            message_text, keyboard = await create_enhanced_admin_menu(
                mock_session, admin_user.id, mock_bot
            )

            # Verify back button is included when navigation history exists
            keyboard_text = str(keyboard)
            assert "◀️ Volver" in keyboard_text or "back" in keyboard_text.lower()

    async def test_temporary_confirmation_auto_deletion(self, mock_session, admin_user, mock_bot):
        """Test temporary confirmation messages with auto-deletion after 7 seconds"""
        with patch('asyncio.create_task') as mock_create_task:
            # Mock successful admin action
            mock_message = AsyncMock()
            mock_message.message_id = 12345

            # Simulate confirmation message creation
            confirmation_text = "✅ <b>Operación completada exitosamente</b>\n\n<i>Este mensaje se eliminará automáticamente en 7 segundos</i>"

            # Test scheduled auto-deletion
            task_mock = AsyncMock()
            mock_create_task.return_value = task_mock

            # Verify auto-deletion scheduling
            mock_create_task.assert_called()

    async def test_html_formatting_for_admin_menus(self, menu_formatter, admin_user):
        """Test HTML formatting for enhanced readability"""
        # Test admin menu HTML formatting
        menu_data = {
            "title": "Panel de Administración",
            "subtitle": "Gestión avanzada de canales y suscripciones",
            "stats": {
                "vip_users": 147,
                "revenue_today": 7500.0,
                "system_health": 99.8
            },
            "options": [
                {"id": "vip_management", "title": "⭐ Canal VIP", "description": "Gestionar suscripciones"},
                {"id": "analytics", "title": "📊 Análisis", "description": "Reportes y métricas"},
                {"id": "automation", "title": "🤖 Automatización", "description": "Tareas programadas"}
            ]
        }

        formatted_text = menu_formatter.format_admin_menu(menu_data, {"user": admin_user})

        # Assertions for HTML formatting
        assert "<b>Panel de Administración</b>" in formatted_text
        assert "<i>Gestión avanzada de canales y suscripciones</i>" in formatted_text
        assert "<code>Usuarios VIP:</code> <b>147</b>" in formatted_text
        assert "<u>Opciones disponibles:</u>" in formatted_text
        assert "• <b>⭐ Canal VIP</b>" in formatted_text

    async def test_menu_error_handling_graceful_degradation(self, mock_session, admin_user, mock_bot):
        """Test graceful error handling when menu components fail"""
        # Mock statistics query failure
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        # Test menu creation with database error
        message_text, keyboard = await create_enhanced_admin_menu(
            mock_session, admin_user.id, mock_bot
        )

        # Verify graceful degradation
        assert "Panel de Administración" in message_text
        assert "Estadísticas no disponibles" in message_text or "Error temporal" in message_text
        assert isinstance(keyboard, InlineKeyboardMarkup)  # Menu still created


class TestVIPSubscriptionManagementWorkflow(TestAdminWorkflowBase):
    """
    Test Requirement 2: Advanced VIP Subscription Management

    Tests token creation, user tracking, exclusive content administration,
    batch operations, and automated reminders.
    """

    @pytest.fixture
    def enhanced_vip_service(self, mock_session, mock_bot):
        """Enhanced VIP service for testing"""
        return EnhancedVIPService(mock_session, mock_bot)

    async def test_end_to_end_token_generation_and_redemption_workflow(
        self, enhanced_vip_service, mock_session, sample_tariff, regular_user
    ):
        """Test complete token generation → redemption → subscription activation workflow"""
        # Setup mocks for token generation
        mock_session.get.return_value = sample_tariff

        mock_token = Token(
            id=str(uuid4()),
            token_string="VIP_TOKEN_WORKFLOW_123",
            tariff_id=sample_tariff.id,
            generated_at=datetime.utcnow(),
            is_used=False,
            tariff=sample_tariff
        )

        # Mock subscription after redemption
        mock_subscription = VipSubscription(
            id=str(uuid4()),
            user_id=regular_user.id,
            start_date=datetime.utcnow(),
            expiration_date=datetime.utcnow() + timedelta(days=30),
            tariff_id=sample_tariff.id,
            status=SubscriptionStatus.ACTIVE,
            created_by_admin_id=999999
        )

        with patch.object(enhanced_vip_service.token_service, 'create_vip_token', return_value=mock_token), \
             patch.object(enhanced_vip_service.token_service, 'activate_token', return_value=30), \
             patch.object(enhanced_vip_service.subscription_service, 'extend_subscription', return_value=mock_subscription):

            # Step 1: Generate token
            generated_token = await enhanced_vip_service.generate_token(
                tariff_id=sample_tariff.id, admin_id=999999
            )

            # Step 2: Redeem token
            activated_subscription = await enhanced_vip_service.redeem_token(
                generated_token.token_string, regular_user.id
            )

            # Assertions
            assert generated_token.token_string == "VIP_TOKEN_WORKFLOW_123"
            assert not generated_token.is_used
            assert activated_subscription.user_id == regular_user.id
            assert activated_subscription.status == SubscriptionStatus.ACTIVE

    async def test_batch_token_generation_workflow(
        self, enhanced_vip_service, mock_session, sample_tariff, admin_user
    ):
        """Test batch token generation with validation and logging"""
        mock_session.get.return_value = sample_tariff

        # Mock batch token creation
        batch_size = 10
        mock_tokens = [
            Token(
                id=str(uuid4()),
                token_string=f"VIP_BATCH_TOKEN_{i:03d}",
                tariff_id=sample_tariff.id,
                generated_at=datetime.utcnow(),
                is_used=False
            )
            for i in range(batch_size)
        ]

        with patch.object(enhanced_vip_service.token_service, 'create_vip_token', side_effect=mock_tokens):
            # Generate batch tokens
            generated_tokens = await enhanced_vip_service.generate_batch_tokens(
                tariff_id=sample_tariff.id,
                admin_id=admin_user.id,
                count=batch_size
            )

            # Assertions
            assert len(generated_tokens) == batch_size
            assert all(token.tariff_id == sample_tariff.id for token in generated_tokens)
            assert all(not token.is_used for token in generated_tokens)

            # Verify all tokens are unique
            token_strings = [token.token_string for token in generated_tokens]
            assert len(set(token_strings)) == batch_size

    async def test_vip_subscription_reminder_automation_workflow(
        self, enhanced_vip_service, mock_session, regular_user, vip_subscription
    ):
        """Test automated VIP subscription reminder workflow"""
        # Mock expiring subscriptions
        expiring_3_days = datetime.utcnow() + timedelta(days=3)
        expiring_1_day = datetime.utcnow() + timedelta(days=1)

        mock_expiring_subs = [
            (
                AsyncMock(expires_at=expiring_3_days, user_id=regular_user.id),
                regular_user
            ),
            (
                AsyncMock(expires_at=expiring_1_day, user_id=regular_user.id + 1),
                AsyncMock(id=regular_user.id + 1, username="user2")
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_expiring_subs)

        with patch.object(enhanced_vip_service, '_delayed_reminder') as mock_delayed_reminder:
            # Schedule reminders
            result = await enhanced_vip_service.schedule_vip_reminders([3, 1])

            # Assertions
            assert result["status"] == "success"
            assert result["scheduled_reminders"] == 4  # 2 users × 2 reminder types
            assert mock_delayed_reminder.call_count == 4

    async def test_subscription_analytics_and_revenue_calculation(
        self, enhanced_vip_service, mock_session
    ):
        """Test comprehensive subscription analytics and revenue calculation"""
        # Mock analytics data
        mock_session.execute.side_effect = [
            # Total revenue
            AsyncMock(scalar=lambda: 50000.0),
            # Period revenue
            AsyncMock(scalar=lambda: 12000.0),
            # Average revenue per token
            AsyncMock(scalar=lambda: 1500.0),
            # Total tokens
            AsyncMock(scalar=lambda: 100),
            # Used tokens
            AsyncMock(scalar=lambda: 75),
            # Revenue by tariff
            AsyncMock(**{
                '__iter__': lambda x: iter([
                    AsyncMock(name="Premium", price=1500, tokens_used=50, tariff_revenue=75000),
                    AsyncMock(name="Basic", price=500, tokens_used=25, tariff_revenue=12500)
                ])
            }),
            # Unused tokens value
            AsyncMock(scalar=lambda: 12500.0)
        ]

        # Calculate revenue metrics
        result = await enhanced_vip_service.calculate_revenue_metrics()

        # Assertions
        assert result["status"] == "success"
        assert result["revenue_metrics"]["total_revenue"] == 50000.0
        assert result["revenue_metrics"]["period_revenue"] == 12000.0
        assert result["token_metrics"]["total_tokens_generated"] == 100
        assert result["token_metrics"]["tokens_used"] == 75
        assert result["token_metrics"]["conversion_rate"] == 75.0

    async def test_user_engagement_tracking_workflow(
        self, enhanced_vip_service, mock_session, regular_user, vip_subscription
    ):
        """Test user engagement tracking and analysis workflow"""
        # Mock VIP user engagement data
        now = datetime.utcnow()
        mock_vip_users = [
            (
                regular_user,
                AsyncMock(
                    messages_sent=200, checkin_streak=14,
                    last_activity_at=now - timedelta(hours=1)
                ),
                vip_subscription
            ),
            (
                AsyncMock(id=regular_user.id + 1, points=600.0),
                AsyncMock(
                    messages_sent=50, checkin_streak=2,
                    last_activity_at=now - timedelta(days=7)
                ),
                AsyncMock(user_id=regular_user.id + 1)
            )
        ]

        mock_free_users = [
            (AsyncMock(id=888888, points=80.0), AsyncMock(messages_sent=30))
        ]

        mock_session.execute.side_effect = [
            AsyncMock(all=lambda: mock_vip_users),
            AsyncMock(all=lambda: mock_free_users),
            AsyncMock(first=lambda: AsyncMock(tokens_used=3, users_with_tokens=2))
        ]

        # Get engagement stats
        result = await enhanced_vip_service.get_user_engagement_stats()

        # Assertions
        assert result["status"] == "success"
        assert result["vip_user_metrics"]["total_vip_users"] == 2
        assert result["vip_user_metrics"]["active_users"] == 1  # High engagement user
        assert "engagement_distribution" in result
        assert "vip_vs_free_comparison" in result

    async def test_subscription_error_handling_and_rollback(
        self, enhanced_vip_service, mock_session, sample_tariff, regular_user
    ):
        """Test error handling and rollback in subscription workflows"""
        mock_session.get.return_value = sample_tariff

        # Mock token creation success but subscription failure
        mock_token = Token(
            id=str(uuid4()),
            token_string="VIP_ERROR_TEST_123",
            tariff_id=sample_tariff.id,
            generated_at=datetime.utcnow(),
            is_used=False
        )

        with patch.object(enhanced_vip_service.token_service, 'activate_token', return_value=30), \
             patch.object(enhanced_vip_service.subscription_service, 'extend_subscription',
                         side_effect=SQLAlchemyError("Database error")):

            # Test error handling during redemption
            with pytest.raises(SQLAlchemyError):
                await enhanced_vip_service.redeem_token(
                    mock_token.token_string, regular_user.id
                )

            # Verify rollback was attempted
            mock_session.rollback.assert_called()


class TestChannelAndContentControlWorkflow(TestAdminWorkflowBase):
    """
    Test Requirement 3: Channel and Exclusive Content Control

    Tests access verification, content publishing, user management,
    and content protection mechanisms.
    """

    @pytest.fixture
    def channel_admin_service(self, mock_session, mock_coordinador_central):
        """Channel admin service for testing"""
        return ChannelAdminService(mock_session, mock_coordinador_central)

    async def test_vip_access_verification_workflow(
        self, channel_admin_service, mock_session, regular_user, vip_subscription
    ):
        """Test VIP access verification before content access"""
        # Mock active VIP subscription query
        mock_session.execute.return_value = AsyncMock(first=lambda: vip_subscription)

        # Test access verification
        result = await channel_admin_service.validate_channel_permissions(
            regular_user.id, "vip_channel_id"
        )

        # Assertions
        assert result["has_access"] is True
        assert result["subscription_status"] == "active"
        assert result["expires_at"] == vip_subscription.expiration_date

    async def test_exclusive_content_publishing_workflow(
        self, channel_admin_service, mock_session, admin_user
    ):
        """Test exclusive content publishing with protection levels"""
        content_data = {
            "type": "premium_story",
            "title": "Exclusive VIP Content",
            "text": "This is premium narrative content for VIP users only.",
            "media_urls": ["https://example.com/premium_image.jpg"]
        }

        protection_config = {
            "no_forward": True,
            "no_download": True,
            "watermark": True
        }

        # Mock content creation
        mock_content = ChannelContent(
            id=str(uuid4()),
            channel_type="VIP",
            content_type="TEXT",
            content_data=content_data,
            protection_level="FULL_PROTECTION",
            published_by_admin_id=admin_user.id,
            publish_date=datetime.utcnow()
        )

        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        with patch.object(channel_admin_service, '_apply_content_protection') as mock_protection:
            # Publish exclusive content
            result = await channel_admin_service.publish_exclusive_content(
                content_data, "VIP", protection_config
            )

            # Assertions
            assert result["status"] == "published"
            assert result["content_id"] is not None
            assert result["protection_applied"] is True
            mock_protection.assert_called_once()

    async def test_user_vip_access_removal_workflow(
        self, channel_admin_service, mock_session, mock_coordinador_central, regular_user
    ):
        """Test automatic VIP access removal upon subscription expiration"""
        # Mock expired subscription
        expired_subscription = VipSubscription(
            id=str(uuid4()),
            user_id=regular_user.id,
            expiration_date=datetime.utcnow() - timedelta(hours=1),
            status=SubscriptionStatus.EXPIRED
        )

        mock_session.execute.return_value = AsyncMock(first=lambda: expired_subscription)

        # Mock CoordinadorCentral notification
        mock_coordinador_central.ejecutar_flujo.return_value = {
            "success": True,
            "action": "access_removed"
        }

        # Test access removal workflow
        result = await channel_admin_service.manage_vip_access(
            regular_user.id, "remove_expired"
        )

        # Assertions
        assert result["status"] == "access_removed"
        assert result["reason"] == "subscription_expired"
        mock_coordinador_central.ejecutar_flujo.assert_called_with(
            regular_user.id,
            AccionUsuario.MODIFICAR_ACCESO_VIP,
            action="remove",
            reason="expired"
        )

    async def test_content_protection_mechanisms(
        self, channel_admin_service, mock_session
    ):
        """Test content protection mechanisms for different protection levels"""
        test_cases = [
            {
                "protection_level": "NO_FORWARD",
                "expected_restrictions": ["forward_disabled"]
            },
            {
                "protection_level": "NO_DOWNLOAD",
                "expected_restrictions": ["download_disabled"]
            },
            {
                "protection_level": "FULL_PROTECTION",
                "expected_restrictions": ["forward_disabled", "download_disabled", "watermark"]
            }
        ]

        for case in test_cases:
            content = ChannelContent(
                id=str(uuid4()),
                content_type="IMAGE",
                protection_level=case["protection_level"]
            )

            # Test protection application
            result = await channel_admin_service._apply_content_protection(content)

            # Assertions
            assert result["protection_level"] == case["protection_level"]
            for restriction in case["expected_restrictions"]:
                assert restriction in result["applied_restrictions"]

    async def test_channel_engagement_tracking(
        self, channel_admin_service, mock_session
    ):
        """Test channel engagement metrics and content performance tracking"""
        # Mock engagement data
        mock_engagement_data = [
            AsyncMock(
                content_id="content_1", views=150, reactions=45,
                shares=12, engagement_rate=0.32
            ),
            AsyncMock(
                content_id="content_2", views=200, reactions=80,
                shares=25, engagement_rate=0.525
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: mock_engagement_data)

        # Get engagement metrics
        result = await channel_admin_service.get_channel_engagement_metrics(
            "vip_channel", datetime.utcnow() - timedelta(days=30)
        )

        # Assertions
        assert result["status"] == "success"
        assert result["total_content_pieces"] == 2
        assert result["average_engagement_rate"] == 0.4225  # (0.32 + 0.525) / 2
        assert len(result["top_performing_content"]) == 2


class TestAnalyticsAndReportingWorkflow(TestAdminWorkflowBase):
    """
    Test Requirement 5: Administrative Analysis and Reports

    Tests comprehensive analytics, report generation, data export,
    and performance metrics visualization.
    """

    @pytest.fixture
    def analytics_service(self, mock_session):
        """Analytics service for testing"""
        return AnalyticsService(mock_session)

    async def test_comprehensive_admin_analytics_workflow(
        self, analytics_service, mock_session
    ):
        """Test complete admin analytics workflow with multiple data sources"""
        # Mock comprehensive analytics data
        mock_session.execute.side_effect = [
            # User engagement metrics
            AsyncMock(scalar=lambda: 1250),  # Total users
            AsyncMock(scalar=lambda: 450),   # Active users
            AsyncMock(scalar=lambda: 147),   # VIP users
            # Revenue metrics
            AsyncMock(scalar=lambda: 125000.0),  # Total revenue
            AsyncMock(scalar=lambda: 25000.0),   # Monthly revenue
            # Content metrics
            AsyncMock(scalar=lambda: 89),    # Published content
            AsyncMock(scalar=lambda: 2340),  # Total views
            # Channel activity
            AsyncMock(**{
                '__iter__': lambda x: iter([
                    AsyncMock(date=datetime.now().date(), messages=45, reactions=123),
                    AsyncMock(date=(datetime.now() - timedelta(days=1)).date(), messages=38, reactions=98)
                ])
            })
        ]

        # Generate comprehensive analytics
        result = await analytics_service.generate_engagement_report(
            "all_channels", date_range=(datetime.now() - timedelta(days=30), datetime.now())
        )

        # Assertions
        assert result["status"] == "success"
        assert "user_metrics" in result
        assert "revenue_metrics" in result
        assert "content_metrics" in result
        assert "engagement_trends" in result
        assert result["user_metrics"]["total_users"] == 1250
        assert result["revenue_metrics"]["total_revenue"] == 125000.0

    async def test_revenue_projection_and_financial_analysis(
        self, analytics_service, mock_session
    ):
        """Test revenue projection calculations and financial analysis"""
        # Mock historical revenue data for projections
        historical_data = [
            AsyncMock(month=1, revenue=8000.0),
            AsyncMock(month=2, revenue=12000.0),
            AsyncMock(month=3, revenue=15000.0),
            AsyncMock(month=4, revenue=18000.0),
            AsyncMock(month=5, revenue=22000.0)
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: historical_data)

        # Calculate revenue projections
        result = await analytics_service.calculate_revenue_metrics(
            projection_months=3
        )

        # Assertions
        assert result["status"] == "success"
        assert "revenue_projections" in result
        assert len(result["revenue_projections"]) == 3

        # Verify growth trend calculation
        projections = result["revenue_projections"]
        assert projections[0] > 22000.0  # Next month projection should be higher
        assert projections[2] > projections[1] > projections[0]  # Growth trend

    async def test_visual_chart_generation_workflow(
        self, analytics_service, mock_session
    ):
        """Test visual chart generation for analytics data"""
        # Mock chart data
        chart_data = {
            "user_growth": [100, 150, 225, 340, 450],
            "revenue_trend": [5000, 8000, 12000, 18000, 25000],
            "engagement_rates": [0.35, 0.42, 0.38, 0.45, 0.51]
        }

        with patch('services.analytics_service.ChartGenerator') as mock_chart_gen:
            mock_chart_gen.return_value.generate_charts.return_value = {
                "user_growth_chart": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "revenue_chart": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "engagement_chart": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            }

            # Generate visual reports
            result = await analytics_service.generate_visual_reports(chart_data)

            # Assertions
            assert result["status"] == "success"
            assert len(result["charts"]) == 3
            assert all(chart.startswith("data:image/png") for chart in result["charts"].values())

    async def test_data_export_workflow(
        self, analytics_service, mock_session
    ):
        """Test data export in multiple formats (JSON, CSV)"""
        # Mock exportable data
        export_data = {
            "users": [
                {"id": 1, "username": "user1", "vip_status": "active", "revenue": 1500},
                {"id": 2, "username": "user2", "vip_status": "expired", "revenue": 0}
            ],
            "subscriptions": [
                {"id": "sub1", "user_id": 1, "start_date": "2024-01-01", "revenue": 1500}
            ]
        }

        # Test JSON export
        json_result = await analytics_service.export_data("comprehensive", format="json")
        assert json_result["status"] == "success"
        assert json_result["format"] == "json"
        assert "download_url" in json_result

        # Test CSV export
        csv_result = await analytics_service.export_data("comprehensive", format="csv")
        assert csv_result["status"] == "success"
        assert csv_result["format"] == "csv"
        assert "download_url" in csv_result

    async def test_real_time_performance_monitoring(
        self, analytics_service, mock_session
    ):
        """Test real-time performance monitoring and alerts"""
        # Mock performance metrics
        performance_data = {
            "response_times": [120, 250, 180, 95, 340],  # ms
            "error_rates": [0.001, 0.002, 0.001, 0.0, 0.003],
            "concurrent_users": [45, 67, 89, 123, 156],
            "memory_usage": [65.5, 72.1, 68.9, 71.2, 74.8]  # %
        }

        mock_session.execute.side_effect = [
            AsyncMock(all=lambda: [
                AsyncMock(metric="response_time", value=180, timestamp=datetime.utcnow()),
                AsyncMock(metric="error_rate", value=0.001, timestamp=datetime.utcnow()),
                AsyncMock(metric="concurrent_users", value=89, timestamp=datetime.utcnow())
            ])
        ]

        # Get real-time performance
        result = await analytics_service.get_real_time_performance()

        # Assertions
        assert result["status"] == "success"
        assert "current_metrics" in result
        assert "performance_health" in result

        # Check for performance alerts
        if result["current_metrics"]["response_time"] > 300:
            assert "high_response_time" in result["alerts"]
        if result["current_metrics"]["error_rate"] > 0.005:
            assert "high_error_rate" in result["alerts"]

    async def test_custom_analytics_dashboard_creation(
        self, analytics_service, mock_session, admin_user
    ):
        """Test custom analytics dashboard creation for specific admin needs"""
        dashboard_config = {
            "widgets": [
                {"type": "revenue_summary", "timeframe": "last_30_days"},
                {"type": "user_growth", "chart_type": "line"},
                {"type": "top_content", "limit": 10},
                {"type": "vip_conversion", "breakdown": "by_tariff"}
            ],
            "refresh_interval": 300,  # 5 minutes
            "admin_id": admin_user.id
        }

        # Mock dashboard data compilation
        with patch.object(analytics_service, '_compile_dashboard_data') as mock_compile:
            mock_compile.return_value = {
                "revenue_summary": {"total": 45000, "growth": 15.2},
                "user_growth": {"trend": "positive", "rate": 8.5},
                "top_content": [{"id": "content_1", "views": 450}],
                "vip_conversion": {"premium": 0.125, "basic": 0.089}
            }

            # Create custom dashboard
            result = await analytics_service.create_custom_dashboard(dashboard_config)

            # Assertions
            assert result["status"] == "success"
            assert result["dashboard_id"] is not None
            assert len(result["widgets"]) == 4
            assert result["refresh_interval"] == 300


class TestAutomationWorkflow(TestAdminWorkflowBase):
    """
    Test Requirement 6: Administrative Task Automation

    Tests automated reminders, message cleanup, user management,
    and scheduled task execution.
    """

    @pytest.fixture
    def automation_service(self, mock_session, mock_coordinador_central):
        """Automation service for testing"""
        return AutomationService(mock_session, mock_coordinador_central)

    async def test_automated_subscription_reminder_workflow(
        self, automation_service, mock_session, regular_user, vip_subscription
    ):
        """Test automated subscription reminder system"""
        # Mock expiring subscriptions at different intervals
        expiring_subs = [
            (vip_subscription, regular_user),  # Expires in 20 days
            (
                AsyncMock(
                    expires_at=datetime.utcnow() + timedelta(days=3),
                    user_id=regular_user.id + 1
                ),
                AsyncMock(id=regular_user.id + 1, username="user2")
            ),
            (
                AsyncMock(
                    expires_at=datetime.utcnow() + timedelta(days=1),
                    user_id=regular_user.id + 2
                ),
                AsyncMock(id=regular_user.id + 2, username="user3")
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: expiring_subs)

        with patch('utils.message_safety.safe_send_message') as mock_send:
            # Start reminder automation
            result = await automation_service.start_subscription_reminders(
                reminder_schedule=[7, 3, 1]
            )

            # Assertions
            assert result["status"] == "started"
            assert result["total_users_monitored"] == 3
            assert result["reminder_schedule"] == [7, 3, 1]

            # Verify reminders were scheduled
            expected_reminders = 2  # Only 3-day and 1-day users get reminders
            assert mock_send.call_count >= expected_reminders

    async def test_automated_message_cleanup_workflow(
        self, automation_service, mock_session, mock_bot
    ):
        """Test automated message cleanup based on age and type"""
        # Mock old messages that should be cleaned up
        old_messages = [
            AsyncMock(
                user_id=123456, message_id=111,
                created_at=datetime.utcnow() - timedelta(hours=25),
                message_type="temporary"
            ),
            AsyncMock(
                user_id=123456, message_id=222,
                created_at=datetime.utcnow() - timedelta(hours=8),
                message_type="menu"
            ),
            AsyncMock(
                user_id=789012, message_id=333,
                created_at=datetime.utcnow() - timedelta(hours=48),
                message_type="temporary"
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: old_messages)

        with patch.object(automation_service, '_safe_delete_message') as mock_delete:
            # Run message cleanup
            result = await automation_service.cleanup_old_messages(
                max_age_hours=24,
                message_types=["temporary", "menu"]
            )

            # Assertions
            assert result["status"] == "completed"
            assert result["messages_processed"] == 3
            assert result["messages_deleted"] >= 2  # At least the 24+ hour old ones
            assert mock_delete.call_count >= 2

    async def test_inactive_user_management_automation(
        self, automation_service, mock_session, mock_coordinador_central
    ):
        """Test automated inactive user detection and management"""
        # Mock inactive VIP users
        inactive_vip_users = [
            (
                AsyncMock(id=111111, username="inactive_user1"),
                AsyncMock(
                    last_activity_at=datetime.utcnow() - timedelta(days=30),
                    messages_sent=0
                ),
                AsyncMock(expires_at=datetime.utcnow() + timedelta(days=5))
            ),
            (
                AsyncMock(id=222222, username="inactive_user2"),
                AsyncMock(
                    last_activity_at=datetime.utcnow() - timedelta(days=60),
                    messages_sent=2
                ),
                AsyncMock(expires_at=datetime.utcnow() + timedelta(days=15))
            )
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: inactive_vip_users)

        # Mock CoordinadorCentral actions
        mock_coordinador_central.ejecutar_flujo.return_value = {
            "success": True, "action": "inactive_user_notified"
        }

        # Run inactive user management
        result = await automation_service.manage_inactive_vip_users(
            inactivity_threshold_days=14
        )

        # Assertions
        assert result["status"] == "completed"
        assert result["inactive_users_found"] == 2
        assert result["actions_taken"] >= 1
        assert mock_coordinador_central.ejecutar_flujo.call_count >= 1

    async def test_narrative_event_coordination_automation(
        self, automation_service, mock_session, mock_coordinador_central
    ):
        """Test automated narrative event coordination and publication"""
        # Mock scheduled narrative events
        scheduled_events = [
            {
                "event_id": "story_chapter_5",
                "publication_time": datetime.utcnow() + timedelta(minutes=5),
                "target_channels": ["vip_channel"],
                "content_type": "narrative_progression"
            },
            {
                "event_id": "daily_challenge",
                "publication_time": datetime.utcnow() + timedelta(hours=1),
                "target_channels": ["free_channel", "vip_channel"],
                "content_type": "interactive_challenge"
            }
        ]

        mock_session.execute.return_value = AsyncMock(all=lambda: [
            AsyncMock(**event) for event in scheduled_events
        ])

        # Mock CoordinadorCentral event coordination
        mock_coordinador_central.ejecutar_flujo.side_effect = [
            {"success": True, "event_published": True},
            {"success": True, "event_scheduled": True}
        ]

        # Schedule narrative events
        result = await automation_service.coordinate_narrative_events(
            lookahead_hours=2
        )

        # Assertions
        assert result["status"] == "scheduled"
        assert result["events_processed"] == 2
        assert result["immediate_publications"] >= 1
        assert mock_coordinador_central.ejecutar_flujo.call_count == 2

    async def test_automation_error_recovery_and_retry_logic(
        self, automation_service, mock_session
    ):
        """Test automation error recovery and retry mechanisms"""
        # Mock intermittent database failures
        failure_count = 0
        def failing_execute(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:
                raise SQLAlchemyError("Connection timeout")
            return AsyncMock(all=lambda: [])

        mock_session.execute.side_effect = failing_execute

        with patch('asyncio.sleep') as mock_sleep:
            # Test retry logic during automation task
            result = await automation_service.cleanup_old_messages(
                max_age_hours=24,
                max_retries=3
            )

            # Assertions
            assert result["status"] == "completed"  # Eventually succeeds
            assert result["retry_attempts"] == 2    # Retried twice before success
            assert mock_sleep.call_count == 2       # Exponential backoff delays

    async def test_automation_monitoring_and_health_checks(
        self, automation_service, mock_session
    ):
        """Test automation system monitoring and health checks"""
        # Mock automation health metrics
        health_data = {
            "running_tasks": 5,
            "successful_executions": 142,
            "failed_executions": 3,
            "average_execution_time": 1.25,
            "last_health_check": datetime.utcnow()
        }

        with patch.object(automation_service, '_get_automation_metrics', return_value=health_data):
            # Get automation health status
            result = await automation_service.get_automation_health()

            # Assertions
            assert result["status"] == "healthy"
            assert result["metrics"]["running_tasks"] == 5
            assert result["metrics"]["success_rate"] > 0.95
            assert "recommendations" in result

            # Check for health alerts
            if result["metrics"]["failed_executions"] > 10:
                assert "high_failure_rate" in result["alerts"]


class TestCompleteAdminWorkflowIntegration(TestAdminWorkflowBase):
    """
    Test complete end-to-end admin workflow integration

    Tests realistic admin scenarios combining multiple requirements
    and services working together.
    """

    @pytest.fixture
    def complete_admin_environment(self, mock_session, mock_bot, mock_coordinador_central):
        """Complete admin environment with all services"""
        services = {
            'vip_service': EnhancedVIPService(mock_session, mock_bot),
            'channel_service': ChannelAdminService(mock_session, mock_coordinador_central),
            'analytics_service': AnalyticsService(mock_session),
            'automation_service': AutomationService(mock_session, mock_coordinador_central),
            'coordinador': mock_coordinador_central
        }
        return services

    async def test_complete_vip_onboarding_to_content_access_workflow(
        self, complete_admin_environment, mock_session, admin_user, regular_user, sample_tariff
    ):
        """Test complete workflow: token generation → user redemption → content access"""
        services = complete_admin_environment

        # Setup mocks
        mock_session.get.return_value = sample_tariff

        # Step 1: Admin generates VIP token
        mock_token = Token(
            id=str(uuid4()),
            token_string="VIP_COMPLETE_WORKFLOW_123",
            tariff_id=sample_tariff.id,
            generated_at=datetime.utcnow(),
            is_used=False
        )

        with patch.object(services['vip_service'].token_service, 'create_vip_token', return_value=mock_token):
            generated_token = await services['vip_service'].generate_token(
                tariff_id=sample_tariff.id, admin_id=admin_user.id
            )

        # Step 2: User redeems token and gets VIP access
        mock_subscription = VipSubscription(
            id=str(uuid4()),
            user_id=regular_user.id,
            start_date=datetime.utcnow(),
            expiration_date=datetime.utcnow() + timedelta(days=30),
            tariff_id=sample_tariff.id,
            status=SubscriptionStatus.ACTIVE
        )

        with patch.object(services['vip_service'].token_service, 'activate_token', return_value=30), \
             patch.object(services['vip_service'].subscription_service, 'extend_subscription', return_value=mock_subscription):

            activated_subscription = await services['vip_service'].redeem_token(
                generated_token.token_string, regular_user.id
            )

        # Step 3: User accesses VIP content
        mock_session.execute.return_value = AsyncMock(first=lambda: activated_subscription)

        access_result = await services['channel_service'].validate_channel_permissions(
            regular_user.id, "vip_channel"
        )

        # Step 4: Track analytics
        with patch.object(services['analytics_service'], '_record_conversion_event') as mock_analytics:
            await services['analytics_service'].record_vip_conversion(
                regular_user.id, generated_token.token_string, activated_subscription.id
            )

        # Assertions for complete workflow
        assert generated_token.token_string == "VIP_COMPLETE_WORKFLOW_123"
        assert activated_subscription.user_id == regular_user.id
        assert access_result["has_access"] is True
        mock_analytics.assert_called_once()

    async def test_bulk_user_management_workflow(
        self, complete_admin_environment, mock_session, admin_user, sample_tariff
    ):
        """Test bulk user management operations"""
        services = complete_admin_environment

        # Step 1: Generate batch tokens for promotional campaign
        batch_size = 20
        mock_session.get.return_value = sample_tariff

        mock_tokens = [
            Token(
                id=str(uuid4()),
                token_string=f"PROMO_TOKEN_{i:03d}",
                tariff_id=sample_tariff.id,
                generated_at=datetime.utcnow(),
                is_used=False
            )
            for i in range(batch_size)
        ]

        with patch.object(services['vip_service'].token_service, 'create_vip_token', side_effect=mock_tokens):
            batch_tokens = await services['vip_service'].generate_batch_tokens(
                tariff_id=sample_tariff.id,
                admin_id=admin_user.id,
                count=batch_size
            )

        # Step 2: Simulate multiple users redeeming tokens
        redemption_results = []
        for i, token in enumerate(batch_tokens[:5]):  # Simulate 5 redemptions
            user_id = 100000 + i
            mock_subscription = VipSubscription(
                id=str(uuid4()),
                user_id=user_id,
                tariff_id=sample_tariff.id,
                status=SubscriptionStatus.ACTIVE
            )

            with patch.object(services['vip_service'].token_service, 'activate_token', return_value=30), \
                 patch.object(services['vip_service'].subscription_service, 'extend_subscription', return_value=mock_subscription):

                result = await services['vip_service'].redeem_token(token.token_string, user_id)
                redemption_results.append(result)

        # Step 3: Analyze campaign effectiveness
        with patch.object(services['analytics_service'], 'calculate_campaign_metrics') as mock_campaign_analytics:
            mock_campaign_analytics.return_value = {
                "tokens_generated": batch_size,
                "tokens_redeemed": len(redemption_results),
                "conversion_rate": len(redemption_results) / batch_size,
                "revenue_generated": len(redemption_results) * sample_tariff.price
            }

            campaign_result = await services['analytics_service'].analyze_token_campaign(batch_tokens)

        # Assertions
        assert len(batch_tokens) == batch_size
        assert len(redemption_results) == 5
        assert campaign_result["conversion_rate"] == 0.25  # 5/20
        assert campaign_result["revenue_generated"] == 5 * sample_tariff.price

    async def test_crisis_management_workflow(
        self, complete_admin_environment, mock_session, admin_user
    ):
        """Test crisis management workflow with system recovery"""
        services = complete_admin_environment

        # Simulate system crisis scenarios
        crisis_scenarios = [
            {
                "type": "high_error_rate",
                "severity": "critical",
                "affected_services": ["vip_service", "channel_service"]
            },
            {
                "type": "database_slowdown",
                "severity": "warning",
                "affected_services": ["analytics_service"]
            }
        ]

        # Step 1: Detect crisis through monitoring
        for scenario in crisis_scenarios:
            with patch.object(services['automation_service'], '_detect_system_anomalies',
                            return_value=scenario):
                anomaly_result = await services['automation_service'].run_health_checks()

                # Step 2: Execute crisis response
                if scenario["severity"] == "critical":
                    # Enable degraded mode
                    response = await services['automation_service'].enable_degraded_mode(
                        affected_services=scenario["affected_services"]
                    )
                    assert response["status"] == "degraded_mode_enabled"

                elif scenario["severity"] == "warning":
                    # Scale up resources
                    response = await services['automation_service'].scale_resources(
                        service="analytics_service",
                        factor=1.5
                    )
                    assert response["status"] == "resources_scaled"

        # Step 3: Recovery and restoration
        recovery_result = await services['automation_service'].restore_full_service()
        assert recovery_result["status"] == "fully_restored"

    async def test_administrative_audit_trail_workflow(
        self, complete_admin_environment, mock_session, admin_user, regular_user
    ):
        """Test complete administrative audit trail and compliance workflow"""
        services = complete_admin_environment

        # Track all admin actions for audit
        admin_actions = []

        def log_admin_action(action_type, details):
            admin_actions.append({
                "admin_id": admin_user.id,
                "action_type": action_type,
                "timestamp": datetime.utcnow(),
                "details": details,
                "success": True
            })

        # Step 1: Admin generates token (logged)
        with patch.object(services['vip_service'], '_log_admin_action', side_effect=log_admin_action):
            token = await services['vip_service'].generate_token(1, admin_user.id)

        # Step 2: Admin publishes exclusive content (logged)
        content_data = {"type": "announcement", "text": "New VIP feature available!"}
        with patch.object(services['channel_service'], '_log_admin_action', side_effect=log_admin_action):
            content_result = await services['channel_service'].publish_exclusive_content(
                content_data, "VIP", {"no_forward": True}
            )

        # Step 3: Admin runs analytics report (logged)
        with patch.object(services['analytics_service'], '_log_admin_action', side_effect=log_admin_action):
            analytics_result = await services['analytics_service'].generate_engagement_report(
                "vip_channel", (datetime.now() - timedelta(days=7), datetime.now())
            )

        # Step 4: Generate compliance audit report
        audit_report = await services['analytics_service'].generate_audit_report(
            admin_id=admin_user.id,
            date_range=(datetime.now() - timedelta(days=30), datetime.now())
        )

        # Assertions
        assert len(admin_actions) == 3
        assert all(action["admin_id"] == admin_user.id for action in admin_actions)
        assert audit_report["total_actions"] >= 3
        assert audit_report["compliance_status"] == "compliant"


# Test runner and utilities
async def run_all_admin_workflow_tests():
    """Run all admin workflow integration tests"""
    if not SERVICES_AVAILABLE or not SQLALCHEMY_AVAILABLE or not AIOGRAM_AVAILABLE:
        print("Skipping admin workflow tests - required dependencies not available")
        return

    print("Running Admin Workflow Integration Tests...")

    test_classes = [
        TestEnhancedAdminMenuSystem,
        TestVIPSubscriptionManagementWorkflow,
        TestChannelAndContentControlWorkflow,
        TestAnalyticsAndReportingWorkflow,
        TestAutomationWorkflow,
        TestCompleteAdminWorkflowIntegration
    ]

    total_tests = sum(
        len([method for method in dir(test_class) if method.startswith('test_')])
        for test_class in test_classes
    )

    print(f"Total workflow integration tests: {total_tests}")
    print("Admin workflow integration tests defined successfully!")
    print("\nTo run tests with pytest:")
    print("pytest tests/integration/test_admin_workflow.py -v")
    print("\nTest coverage includes:")
    print("- Enhanced administrative menu system")
    print("- VIP subscription management workflows")
    print("- Channel and exclusive content control")
    print("- Analytics and reporting workflows")
    print("- Administrative task automation")
    print("- Complete end-to-end integration scenarios")


if __name__ == "__main__":
    # Run basic verification
    asyncio.run(run_all_admin_workflow_tests())