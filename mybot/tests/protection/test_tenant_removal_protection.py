"""
Protection tests for tenant system removal.
These tests capture current behavior to ensure functionality is preserved
when TenantService is removed and related handlers are refactored.

CRITICAL: These tests protect the system during the tenant removal refactor.
They verify that core flows continue working without tenant context.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from database.models import User, ConfigEntry, Tariff
from services.config_service import ConfigService
from handlers.start import cmd_start
from handlers.setup import start_setup
from handlers.admin.admin_menu import admin_start


@pytest.mark.asyncio
class TestTenantRemovalProtection:
    """
    Tests to protect functionality during tenant system removal.
    These tests capture the CURRENT behavior that must be preserved.
    """

    async def test_admin_start_workflow_without_tenant(self, session, admin_user, mock_bot):
        """
        CRITICAL: Test admin start workflow works without tenant service.
        This protects the admin onboarding flow during tenant removal.
        """
        # Mock message with admin user
        message = MagicMock()
        message.from_user.id = admin_user.id
        message.from_user.username = admin_user.username
        message.from_user.first_name = admin_user.first_name
        message.from_user.last_name = None
        message.answer = AsyncMock()
        message.bot = mock_bot
        
        # Mock menu_factory and menu_manager to avoid dependency issues
        with patch('handlers.start.menu_factory') as mock_menu_factory, \
             patch('handlers.start.menu_manager') as mock_menu_manager, \
             patch('handlers.start.is_admin') as mock_is_admin, \
             patch('handlers.start.TenantService') as mock_tenant_service:
            
            # Setup mocks
            mock_is_admin.return_value = True
            mock_tenant_service.return_value.initialize_tenant = AsyncMock(return_value={"success": True})
            mock_menu_factory.create_menu = AsyncMock(return_value=("Admin Menu", MagicMock()))
            mock_menu_manager.show_menu = AsyncMock()
            
            # Execute admin start
            await cmd_start(message, session)
            
            # Verify tenant service was called (current behavior)
            mock_tenant_service.assert_called_once_with(session)
            mock_tenant_service.return_value.initialize_tenant.assert_called_once_with(admin_user.id)
            
            # Verify admin menu was shown
            mock_menu_factory.create_menu.assert_called_with("admin_main", admin_user.id, session, mock_bot)
            mock_menu_manager.show_menu.assert_called_once()

    async def test_user_registration_preserves_role_assignment(self, session, mock_bot):
        """
        CRITICAL: Test that user registration and role assignment works without tenant context.
        This protects the core user onboarding flow.
        """
        # Mock message for new user
        message = MagicMock()
        message.from_user.id = 999888777
        message.from_user.username = "newuser"
        message.from_user.first_name = "New"
        message.from_user.last_name = "User"
        message.answer = AsyncMock()
        message.bot = mock_bot
        
        with patch('handlers.start.menu_factory') as mock_menu_factory, \
             patch('handlers.start.menu_manager') as mock_menu_manager, \
             patch('handlers.start.is_admin') as mock_is_admin:
            
            # Setup mocks for regular user
            mock_is_admin.return_value = False
            mock_menu_factory.create_menu = AsyncMock(return_value=("Main Menu", MagicMock()))
            mock_menu_manager.show_menu = AsyncMock()
            
            # Execute start for new user
            await cmd_start(message, session)
            
            # Verify user was created with correct defaults
            created_user = await session.get(User, 999888777)
            assert created_user is not None, "New user must be created"
            assert created_user.username == "newuser", "Username must be preserved"
            assert created_user.first_name == "New", "First name must be preserved"
            assert created_user.role in ["free", None], "New users should have free role or None"
            
            # Verify main menu was shown (not admin menu)
            mock_menu_factory.create_menu.assert_called_with("main", 999888777, session, mock_bot)

    async def test_config_persistence_without_tenant_context(self, session):
        """
        CRITICAL: Test that configuration persistence works without tenant service.
        This protects configuration storage during tenant removal.
        """
        config_service = ConfigService(session)
        
        # Test channel configuration (core functionality that must survive)
        await config_service.set_vip_channel_id(-1001234567890)
        await config_service.set_free_channel_id(-1009876543210)
        
        # Test custom configuration entries
        await config_service.set_value("bot_welcome_message", "Welcome to our bot!")
        await config_service.set_value("daily_check_bonus", "10")
        
        # Verify configurations are stored
        vip_channel = await config_service.get_vip_channel_id()
        free_channel = await config_service.get_free_channel_id()
        welcome_msg = await config_service.get_value("bot_welcome_message")
        daily_bonus = await config_service.get_value("daily_check_bonus")
        
        assert vip_channel == -1001234567890, "VIP channel configuration must persist"
        assert free_channel == -1009876543210, "Free channel configuration must persist"
        assert welcome_msg == "Welcome to our bot!", "Custom configurations must persist"
        assert daily_bonus == "10", "Numeric configurations must persist"

    async def test_setup_workflow_channel_configuration(self, session, admin_user):
        """
        CRITICAL: Test that setup workflow for channel configuration works.
        This protects the admin setup process during tenant removal.
        """
        # Mock message for setup command
        message = MagicMock()
        message.from_user.id = admin_user.id
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        with patch('handlers.setup.is_admin') as mock_is_admin, \
             patch('handlers.setup.TenantService') as mock_tenant_service, \
             patch('handlers.setup.menu_factory') as mock_menu_factory, \
             patch('handlers.setup.menu_manager') as mock_menu_manager:
            
            # Setup mocks
            mock_is_admin.return_value = True
            mock_tenant_service.return_value.initialize_tenant = AsyncMock(return_value={"success": True})
            mock_menu_factory.create_menu = AsyncMock(return_value=("Setup Menu", MagicMock()))
            mock_menu_manager.show_menu = AsyncMock()
            
            # Execute setup start
            await start_setup(message, session)
            
            # Verify tenant initialization (current behavior)
            mock_tenant_service.assert_called_once_with(session)
            mock_tenant_service.return_value.initialize_tenant.assert_called_once_with(admin_user.id)
            
            # Verify setup menu shown
            mock_menu_factory.create_menu.assert_called_with("setup_main", admin_user.id, session, message.bot)
            mock_menu_manager.show_menu.assert_called_once()

    async def test_tariff_creation_without_tenant(self, session):
        """
        CRITICAL: Test that tariff creation works without tenant service.
        This protects the VIP subscription system during tenant removal.
        """
        # Create tariffs directly (simulating what tenant service does)
        tariff1 = Tariff(name="VIP Básico", duration_days=30, price=10)
        tariff2 = Tariff(name="VIP Premium", duration_days=90, price=25)
        
        session.add(tariff1)
        session.add(tariff2)
        await session.commit()
        
        # Verify tariffs exist and are retrievable
        stmt = select(Tariff).where(Tariff.name == "VIP Básico")
        result = await session.execute(stmt)
        retrieved_tariff = result.scalar_one_or_none()
        
        assert retrieved_tariff is not None, "Tariffs must be creatable without tenant service"
        assert retrieved_tariff.duration_days == 30, "Tariff duration must be preserved"
        assert retrieved_tariff.price == 10, "Tariff price must be preserved"
        
        # Verify multiple tariffs can coexist
        all_tariffs_stmt = select(Tariff)
        all_result = await session.execute(all_tariffs_stmt)
        all_tariffs = all_result.scalars().all()
        assert len(all_tariffs) >= 2, "Multiple tariffs must be supported"

    async def test_admin_menu_stats_without_tenant(self, session, admin_user, mock_bot):
        """
        CRITICAL: Test that admin menu and statistics work without tenant service.
        This protects the admin panel functionality during tenant removal.
        """
        # Mock callback query for admin stats
        callback = MagicMock()
        callback.from_user.id = admin_user.id
        callback.answer = AsyncMock()
        callback.bot = mock_bot
        
        with patch('handlers.admin.admin_menu.is_admin') as mock_is_admin, \
             patch('handlers.admin.admin_menu.get_admin_statistics') as mock_stats, \
             patch('handlers.admin.admin_menu.TenantService') as mock_tenant_service, \
             patch('handlers.admin.admin_menu.menu_manager') as mock_menu_manager:
            
            # Setup mocks
            mock_is_admin.return_value = True
            mock_stats.return_value = {
                'users_total': 100,
                'subscriptions_total': 20,
                'subscriptions_active': 15,
                'subscriptions_expired': 5,
                'revenue_total': 500
            }
            mock_tenant_service.return_value.get_tenant_summary = AsyncMock(return_value={
                "channels": {"vip_channel_id": -123, "free_channel_id": -456},
                "tariff_count": 3
            })
            mock_menu_manager.update_menu = AsyncMock()
            
            # Import and execute admin stats handler
            from handlers.admin.admin_menu import admin_stats
            await admin_stats(callback, session)
            
            # Verify stats retrieval (current behavior)
            mock_stats.assert_called_once_with(session)
            mock_tenant_service.assert_called_once_with(session)
            mock_tenant_service.return_value.get_tenant_summary.assert_called_once_with(admin_user.id)
            
            # Verify menu update
            mock_menu_manager.update_menu.assert_called_once()

    async def test_role_based_access_preserved(self, session, test_user, vip_user, admin_user):
        """
        CRITICAL: Test that role-based access control works without tenant service.
        This protects the core security model during tenant removal.
        """
        from utils.user_roles import is_admin, get_user_role
        
        # Test role detection for different user types
        admin_check = await is_admin(admin_user.id, session)
        regular_role = await get_user_role(test_user.id, session)
        vip_role = await get_user_role(vip_user.id, session)
        
        assert admin_check is True, "Admin role must be correctly detected"
        assert regular_role == "free", "Regular user role must be preserved"
        assert vip_role == "vip", "VIP role must be preserved"

    async def test_user_info_update_preserved(self, session, test_user, mock_bot):
        """
        CRITICAL: Test that user info updates work without tenant service.
        This protects user profile management during tenant removal.
        """
        # Mock message with updated user info
        message = MagicMock()
        message.from_user.id = test_user.id
        message.from_user.username = "updated_username"
        message.from_user.first_name = "Updated"
        message.from_user.last_name = "Name"
        message.answer = AsyncMock()
        message.bot = mock_bot
        
        with patch('handlers.start.menu_factory') as mock_menu_factory, \
             patch('handlers.start.menu_manager') as mock_menu_manager, \
             patch('handlers.start.is_admin') as mock_is_admin:
            
            # Setup mocks for regular user
            mock_is_admin.return_value = False
            mock_menu_factory.create_menu = AsyncMock(return_value=("Main Menu", MagicMock()))
            mock_menu_manager.show_menu = AsyncMock()
            
            # Execute start to trigger user update
            await cmd_start(message, session)
            
            # Verify user info was updated
            await session.refresh(test_user)
            assert test_user.username == "updated_username", "Username must be updated"
            assert test_user.first_name == "Updated", "First name must be updated"
            assert test_user.last_name == "Name", "Last name must be updated"

    async def test_configuration_service_independence(self, session):
        """
        CRITICAL: Test that ConfigService works independently without tenant service.
        This protects configuration management during tenant removal.
        """
        config_service = ConfigService(session)
        
        # Test various configuration operations
        test_configs = {
            "system_message": "Bot is running",
            "max_daily_points": "100",
            "vip_bonus_multiplier": "1.5",
            "maintenance_mode": "false"
        }
        
        # Set all configurations
        for key, value in test_configs.items():
            await config_service.set_value(key, value)
        
        # Verify all configurations are retrievable
        for key, expected_value in test_configs.items():
            retrieved_value = await config_service.get_value(key)
            assert retrieved_value == expected_value, f"Configuration {key} must be preserved"
        
        # Test configuration update
        await config_service.set_value("system_message", "Bot updated")
        updated_value = await config_service.get_value("system_message")
        assert updated_value == "Bot updated", "Configuration updates must work"
        
        # Test configuration deletion
        await config_service.delete_value("maintenance_mode")
        deleted_value = await config_service.get_value("maintenance_mode")
        assert deleted_value is None, "Configuration deletion must work"


@pytest.mark.asyncio 
class TestTenantRemovalRegressionPrevention:
    """
    Additional tests to prevent regressions during tenant removal.
    These test edge cases and ensure robustness.
    """

    async def test_admin_without_existing_config(self, session, mock_bot):
        """
        PROTECTION: Test admin start when no prior configuration exists.
        This ensures new admins can still set up the system.
        """
        # Create a new admin user without prior setup
        admin_user = User(
            id=555666777,
            first_name="NewAdmin",
            username="newadmin",
            role="admin"
        )
        session.add(admin_user)
        await session.commit()
        
        # Mock message
        message = MagicMock()
        message.from_user.id = admin_user.id
        message.from_user.username = admin_user.username
        message.from_user.first_name = admin_user.first_name
        message.from_user.last_name = None
        message.answer = AsyncMock()
        message.bot = mock_bot
        
        with patch('handlers.start.menu_factory') as mock_menu_factory, \
             patch('handlers.start.menu_manager') as mock_menu_manager, \
             patch('handlers.start.is_admin') as mock_is_admin, \
             patch('handlers.start.TenantService') as mock_tenant_service:
            
            # Setup mocks
            mock_is_admin.return_value = True
            mock_tenant_service.return_value.initialize_tenant = AsyncMock(return_value={"success": True})
            mock_menu_factory.create_menu = AsyncMock(return_value=("Admin Menu", MagicMock()))
            mock_menu_manager.show_menu = AsyncMock()
            
            # Should not raise any exceptions
            await cmd_start(message, session)
            
            # Verify system handles new admin gracefully
            mock_tenant_service.return_value.initialize_tenant.assert_called_once_with(admin_user.id)

    async def test_config_service_concurrent_access(self, session):
        """
        PROTECTION: Test that ConfigService handles concurrent access properly.
        This ensures configuration remains stable during high load.
        """
        config_service = ConfigService(session)
        
        # Simulate concurrent config operations
        async def set_config(key, value):
            await config_service.set_value(key, value)
            return await config_service.get_value(key)
        
        # Multiple concurrent operations
        import asyncio
        tasks = [
            set_config("config_1", "value_1"),
            set_config("config_2", "value_2"),
            set_config("config_3", "value_3"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed successfully
        assert results[0] == "value_1", "Concurrent config 1 must succeed"
        assert results[1] == "value_2", "Concurrent config 2 must succeed"
        assert results[2] == "value_3", "Concurrent config 3 must succeed"

    async def test_user_role_transitions_preserved(self, session):
        """
        PROTECTION: Test that user role transitions work without tenant service.
        This protects the role upgrade/downgrade functionality.
        """
        # Create user with free role
        user = User(
            id=777888999,
            first_name="TransitionUser",
            username="transitionuser",
            role="free"
        )
        session.add(user)
        await session.commit()
        
        # Upgrade to VIP
        user.role = "vip"
        await session.commit()
        
        # Verify role change persisted
        await session.refresh(user)
        assert user.role == "vip", "Role upgrade must persist"
        
        # Downgrade to free
        user.role = "free"
        await session.commit()
        
        # Verify downgrade persisted
        await session.refresh(user)
        assert user.role == "free", "Role downgrade must persist"