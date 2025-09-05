"""
Comprehensive test suite for Enhanced User System with Diana Character Consistency.
Tests registration, role transitions, menu system, and character validation.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.models import User, UserSession, RoleTransition, Base
from services.enhanced_user_service import (
    EnhancedUserService, 
    RegistrationResult,
    RoleTransitionResult,
    register_user_with_diana_character
)
from services.enhanced_diana_menu_system import (
    EnhancedDianaMenuSystem,
    MenuResponse,
    show_diana_main_menu,
    handle_diana_callback
)
from middlewares.enhanced_user_registration_middleware import (
    EnhancedUserRegistrationMiddleware
)

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

class TestEnhancedUserService:
    """Test suite for Enhanced User Service."""
    
    @pytest_asyncio.fixture(scope="function")
    async def async_session(self):
        """Create test database session."""
        engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session_factory = async_sessionmaker(engine, class_=AsyncSession)
        
        async with async_session_factory() as session:
            yield session
            
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_enhanced_registration_new_user(self, async_session):
        """Test enhanced registration for new user with character consistency."""
        service = EnhancedUserService(async_session)
        
        # Test registration
        result = await service.enhanced_registration(
            telegram_id=123456789,
            first_name="TestUser",
            last_name="Diana",
            username="test_diana",
            initial_role="free"
        )
        
        # Verify registration success
        assert result.success
        assert result.user is not None
        assert result.session is not None
        assert result.user.id == 123456789
        assert result.user.first_name == "TestUser"
        assert result.user.role == "free"
        assert result.character_score >= 95.0  # Character consistency requirement
        assert result.performance_metrics["meets_3s_requirement"]  # Performance requirement
        
        # Verify session creation
        assert result.session.user_id == 123456789
        assert result.session.session_state == "welcome"
        assert "main_menu" in result.session.menu_position["current"]
        
        # Verify welcome message character consistency
        assert "Diana" in result.welcome_message
        assert "misterio" in result.welcome_message.lower() or "secreto" in result.welcome_message.lower()
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_enhanced_registration_existing_user(self, async_session):
        """Test enhanced registration for existing user."""
        service = EnhancedUserService(async_session)
        
        # Create existing user
        await service.enhanced_registration(123456789, "ExistingUser")
        
        # Try to register same user again
        result = await service.enhanced_registration(123456789, "NewName")
        
        # Should return existing user
        assert result.success
        assert result.user.first_name == "ExistingUser"  # Original name preserved
        assert "regresa" in result.welcome_message.lower()  # Returning user message
    
    @pytest.mark.asyncio
    async def test_role_transition_to_vip(self, async_session):
        """Test role transition from free to VIP with audit trail."""
        service = EnhancedUserService(async_session)
        
        # Create user
        reg_result = await service.enhanced_registration(123456789, "TestUser", initial_role="free")
        assert reg_result.success
        
        # Transition to VIP
        transition_result = await service.transition_user_role(
            123456789,
            "vip",
            "User upgrade test",
            performed_by=987654321
        )
        
        # Verify transition
        assert transition_result.success
        assert transition_result.previous_role == "free"
        assert transition_result.new_role == "vip"
        assert transition_result.character_validated
        assert transition_result.transition_id > 0
        
        # Verify user role updated
        updated_user = await service.get_user_with_character_score(123456789)
        assert updated_user["user"].role == "vip"
        
        # Verify audit trail exists
        from sqlalchemy.future import select
        query = select(RoleTransition).where(RoleTransition.user_id == 123456789)
        result = await async_session.execute(query)
        transitions = result.scalars().all()
        
        assert len(transitions) == 2  # Initial registration + VIP upgrade
        vip_transition = next(t for t in transitions if t.new_role == "vip")
        assert vip_transition.previous_role == "free"
        assert vip_transition.performed_by == 987654321
        assert vip_transition.transition_reason == "User upgrade test"
    
    @pytest.mark.asyncio
    async def test_session_state_management(self, async_session):
        """Test session state updates and tracking."""
        service = EnhancedUserService(async_session)
        
        # Create user
        reg_result = await service.enhanced_registration(123456789, "TestUser")
        assert reg_result.success
        
        # Update session state
        success = await service.update_session_state(
            123456789,
            "narrative_menu",
            menu_position={"current": "narrative", "previous": "main"},
            preferences={"theme": "dark", "notifications": False}
        )
        assert success
        
        # Verify session updated
        user_data = await service.get_user_with_character_score(123456789)
        session = user_data["user"].session
        
        assert session.session_state == "narrative_menu"
        assert session.menu_position["current"] == "narrative"
        assert session.menu_position["previous"] == "main"
        assert session.preferences["theme"] == "dark"
        assert session.preferences["notifications"] == False
    
    @pytest.mark.asyncio
    async def test_character_validation_integration(self, async_session):
        """Test character validation integration."""
        service = EnhancedUserService(async_session)
        
        # Create user
        reg_result = await service.enhanced_registration(123456789, "TestUser")
        
        # Test character validation
        result = await service.validate_user_interaction(
            123456789,
            "Hola, ¿cómo estás? Todo está bien.",  # Too casual for Diana
            "greeting"
        )
        
        # Should detect character issues
        assert result.overall_score < 95.0
        assert len(result.violations) > 0
        assert any("casual" in v.lower() for v in result.violations)
        
        # Test good character message
        good_result = await service.validate_user_interaction(
            123456789,
            "Ah... los secretos susurran tu nombre, querido. ¿Qué misterios buscas en las sombras de mi alma?",
            "greeting"
        )
        
        assert good_result.overall_score >= 95.0
        assert good_result.meets_threshold
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, async_session):
        """Test that performance requirements are met."""
        service = EnhancedUserService(async_session)
        
        start_time = datetime.now()
        
        # Registration should complete in <3s
        result = await service.enhanced_registration(123456789, "TestUser")
        registration_time = (datetime.now() - start_time).total_seconds()
        
        assert registration_time < 3.0
        assert result.performance_metrics["meets_3s_requirement"]
        assert result.success

class TestEnhancedDianaMenuSystem:
    """Test suite for Enhanced Diana Menu System."""
    
    @pytest_asyncio.fixture(scope="function")
    async def async_session(self):
        """Create test database session."""
        engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session_factory = async_sessionmaker(engine, class_=AsyncSession)
        
        async with async_session_factory() as session:
            yield session
            
        await engine.dispose()
    
    @pytest_asyncio.fixture
    async def setup_test_user(self, async_session):
        """Setup test user for menu tests."""
        service = EnhancedUserService(async_session)
        result = await service.enhanced_registration(123456789, "TestUser", initial_role="free")
        return result.user
    
    @pytest.mark.asyncio
    async def test_main_menu_display_free_user(self, async_session, setup_test_user):
        """Test main menu display for free user."""
        menu_system = EnhancedDianaMenuSystem(async_session)
        
        # Create mock message
        mock_message = MagicMock()
        mock_message.from_user.id = 123456789
        mock_message.answer = AsyncMock()
        
        # Show main menu
        result = await menu_system.show_main_menu(mock_message, user_role="free")
        
        # Verify menu response
        assert result.success
        assert result.character_score >= 95.0
        assert result.response_time < 1.0  # Performance requirement
        assert result.meets_performance_requirement
        assert result.message_sent
        
        # Verify message was sent with character consistency
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]
        
        assert "Diana" in message_text
        assert "💋" in message_text or "✨" in message_text  # Diana's emojis
        assert "secretos" in message_text.lower() or "misterios" in message_text.lower()
    
    @pytest.mark.asyncio
    async def test_main_menu_display_vip_user(self, async_session, setup_test_user):
        """Test main menu display for VIP user."""
        # Upgrade user to VIP
        service = EnhancedUserService(async_session)
        await service.transition_user_role(123456789, "vip")
        
        menu_system = EnhancedDianaMenuSystem(async_session)
        
        # Create mock message
        mock_message = MagicMock()
        mock_message.from_user.id = 123456789
        mock_message.answer = AsyncMock()
        
        # Show VIP menu
        result = await menu_system.show_main_menu(mock_message, user_role="vip")
        
        assert result.success
        assert result.character_score >= 95.0
        
        # Check VIP-specific content
        call_args = mock_message.answer.call_args
        message_text = call_args[0][0]
        
        assert "👑" in message_text or "VIP" in message_text
        assert "elegido" in message_text.lower() or "íntimo" in message_text.lower()
    
    @pytest.mark.asyncio
    async def test_vip_upgrade_flow(self, async_session, setup_test_user):
        """Test VIP upgrade menu flow."""
        menu_system = EnhancedDianaMenuSystem(async_session)
        
        # Create mock callback query
        mock_callback = MagicMock()
        mock_callback.from_user.id = 123456789
        mock_callback.data = "diana_become_vip"
        mock_callback.answer = AsyncMock()
        
        # Mock safe_edit
        with patch('services.enhanced_diana_menu_system.safe_edit') as mock_safe_edit:
            mock_safe_edit.return_value = None
            
            result = await menu_system._handle_vip_upgrade(mock_callback)
        
        assert result.success
        assert result.character_score >= 90.0  # VIP upgrade messages
        
        # Verify user was upgraded
        service = EnhancedUserService(async_session)
        user_data = await service.get_user_with_character_score(123456789)
        assert user_data["user"].role == "vip"
    
    @pytest.mark.asyncio
    async def test_callback_routing(self, async_session, setup_test_user):
        """Test callback routing and handling."""
        menu_system = EnhancedDianaMenuSystem(async_session)
        
        # Test various callbacks
        test_callbacks = [
            "diana_main_menu",
            "diana_vip_preview", 
            "diana_profile",
            "diana_close"
        ]
        
        for callback_data in test_callbacks:
            mock_callback = MagicMock()
            mock_callback.from_user.id = 123456789
            mock_callback.data = callback_data
            mock_callback.answer = AsyncMock()
            mock_callback.message.delete = AsyncMock()
            
            with patch('services.enhanced_diana_menu_system.safe_edit') as mock_safe_edit:
                mock_safe_edit.return_value = None
                
                result = await menu_system.handle_callback(mock_callback)
            
            assert result.response_time < 1.0  # Performance requirement
            # Some callbacks might delegate, so success isn't always True
            assert len(result.errors) == 0 or result.success
    
    @pytest.mark.asyncio
    async def test_character_consistency_across_menus(self, async_session, setup_test_user):
        """Test character consistency across all menu types."""
        menu_system = EnhancedDianaMenuSystem(async_session)
        
        # Test all role-based menus
        roles = ["free", "vip", "admin"]
        
        for role in roles:
            mock_message = MagicMock()
            mock_message.from_user.id = 123456789
            mock_message.answer = AsyncMock()
            
            result = await menu_system.show_main_menu(mock_message, user_role=role)
            
            # All menus should meet character requirements
            assert result.character_score >= 95.0, f"Character score too low for {role} menu: {result.character_score}"
            assert result.response_time < 1.0, f"Response time too slow for {role} menu: {result.response_time}"

class TestEnhancedUserRegistrationMiddleware:
    """Test suite for Enhanced User Registration Middleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_registration_flow(self):
        """Test middleware registration flow."""
        middleware = EnhancedUserRegistrationMiddleware(require_character_validation=True)
        
        # Create mock objects
        mock_session = AsyncMock()
        mock_handler = AsyncMock()
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_user = MagicMock()
        
        # Setup mock structure
        mock_update.message = mock_message
        mock_message.from_user = mock_user
        mock_user.id = 123456789
        mock_user.first_name = "TestUser"
        mock_user.username = "test_user"
        
        data = {"session": mock_session}
        
        # Mock enhanced user service
        with patch('middlewares.enhanced_user_registration_middleware.EnhancedUserService') as MockService:
            mock_service = MockService.return_value
            mock_registration_result = RegistrationResult(
                user=mock_user,
                session=MagicMock(),
                success=True,
                character_score=96.0,
                welcome_message="Bienvenido, querido...",
                errors=[],
                performance_metrics={"total_time_seconds": 1.5, "meets_3s_requirement": True}
            )
            mock_service.enhanced_registration.return_value = mock_registration_result
            
            # Call middleware
            result = await middleware(mock_handler, mock_update, data)
            
            # Verify service was called
            mock_service.enhanced_registration.assert_called_once()
            
            # Verify data was enriched
            assert "user" in data
            assert "character_score" in data
            assert "registration_result" in data
            assert data["character_score"] == 96.0
    
    @pytest.mark.asyncio
    async def test_middleware_fallback_on_error(self):
        """Test middleware fallback to basic registration on error."""
        middleware = EnhancedUserRegistrationMiddleware()
        
        # Create mock objects
        mock_session = AsyncMock()
        mock_handler = AsyncMock()
        mock_update = MagicMock()
        mock_message = MagicMock()
        mock_user = MagicMock()
        
        mock_update.message = mock_message
        mock_message.from_user = mock_user
        mock_user.id = 123456789
        
        data = {"session": mock_session}
        
        # Mock enhanced service to fail
        with patch('middlewares.enhanced_user_registration_middleware.EnhancedUserService') as MockEnhanced:
            MockEnhanced.return_value.enhanced_registration.side_effect = Exception("Service error")
            
            # Mock fallback service
            with patch('middlewares.enhanced_user_registration_middleware.UserService') as MockBasic:
                mock_basic_service = MockBasic.return_value
                mock_basic_service.get_user.return_value = None
                mock_basic_service.create_user.return_value = mock_user
                
                # Call middleware
                await middleware(mock_handler, mock_update, data)
                
                # Verify fallback was used
                mock_basic_service.create_user.assert_called_once()
                assert data["user"] == mock_user

class TestIntegrationScenarios:
    """Integration tests for complete user flows."""
    
    @pytest_asyncio.fixture(scope="function")
    async def async_session(self):
        """Create test database session."""
        engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session_factory = async_sessionmaker(engine, class_=AsyncSession)
        
        async with async_session_factory() as session:
            yield session
            
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_free_to_vip(self, async_session):
        """Test complete user journey from registration to VIP upgrade."""
        # Step 1: User registration
        registration_result = await register_user_with_diana_character(
            async_session,
            123456789,
            "Journey User",
            "Test",
            "journey_user"
        )
        
        assert registration_result.success
        assert registration_result.character_score >= 95.0
        assert registration_result.performance_metrics["meets_3s_requirement"]
        
        # Step 2: Show main menu
        mock_message = MagicMock()
        mock_message.from_user.id = 123456789
        mock_message.answer = AsyncMock()
        
        menu_result = await show_diana_main_menu(async_session, mock_message, "free")
        assert menu_result.success
        assert menu_result.response_time < 1.0
        
        # Step 3: VIP upgrade
        service = EnhancedUserService(async_session)
        transition_result = await service.transition_user_role(123456789, "vip", "Journey test")
        
        assert transition_result.success
        assert transition_result.new_role == "vip"
        
        # Step 4: Show VIP menu
        vip_menu_result = await show_diana_main_menu(async_session, mock_message, "vip")
        assert vip_menu_result.success
        assert vip_menu_result.character_score >= 95.0
        
        # Step 5: Verify final state
        final_user_data = await service.get_user_with_character_score(123456789)
        assert final_user_data["user"].role == "vip"
        assert final_user_data["character_score"] >= 95.0
    
    @pytest.mark.asyncio
    async def test_performance_under_concurrent_load(self, async_session):
        """Test system performance under concurrent user registrations."""
        user_count = 10
        tasks = []
        
        for i in range(user_count):
            task = register_user_with_diana_character(
                async_session,
                123456789 + i,
                f"ConcurrentUser{i}",
                "Test",
                f"concurrent_user_{i}"
            )
            tasks.append(task)
        
        # Execute all registrations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded and met performance requirements
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == user_count
        
        for result in successful_results:
            assert result.success
            assert result.character_score >= 95.0
            assert result.performance_metrics["meets_3s_requirement"]

# Convenience test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])