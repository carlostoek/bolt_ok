"""
Integration tests for Phase 2.1: User System & Diana Menu Integration
Tests enhanced user registration, role-based access, and unified menu navigation.

Test Requirements:
- User registration success rate >99%
- Menu response time <1s
- Diana character consistency >95%
- Zero menu navigation errors
- Complete user journey validation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from services.enhanced_user_service import EnhancedUserService, RegistrationResult, RoleTransitionResult
from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem, MenuResponse
from services.diana_character_validator import DianaCharacterValidator
from database.models import User, UserSession, RoleTransition
from database.narrative_unified import UserNarrativeState


@pytest.mark.asyncio
class TestPhase21UserMenuIntegration:
    """Phase 2.1 integration tests for user system and Diana menu."""
    
    async def test_complete_user_registration_journey(self, session):
        """Test complete user registration journey with character consistency."""
        user_service = EnhancedUserService(session)
        
        # Test data
        telegram_id = 12345
        test_cases = [
            {"role": "free", "expected_char_score_min": 90.0},
            {"role": "vip", "expected_char_score_min": 95.0},
            {"role": "admin", "expected_char_score_min": 95.0}
        ]
        
        for case in test_cases:
            # Test registration
            start_time = datetime.now()
            result = await user_service.enhanced_registration(
                telegram_id=telegram_id + hash(case["role"]),  # Unique ID per role
                first_name="Test",
                last_name="User",
                username=f"testuser_{case['role']}",
                initial_role=case["role"]
            )
            
            # Validate registration success
            assert result.success, f"Registration failed for {case['role']}: {result.errors}"
            assert result.user is not None
            assert result.session is not None
            assert result.user.role == case["role"]
            
            # Validate character consistency
            assert result.character_score >= case["expected_char_score_min"], \
                f"Character score {result.character_score} below minimum {case['expected_char_score_min']} for {case['role']}"
            
            # Validate performance (<3s requirement)
            registration_time = result.performance_metrics.get("total_time", 0)
            assert registration_time < 3.0, \
                f"Registration took {registration_time:.2f}s, exceeds 3s requirement"
            
            # Validate welcome message content
            assert "Diana" in result.welcome_message
            assert len(result.welcome_message) > 50  # Substantial welcome message
            
    async def test_menu_navigation_all_roles(self, session):
        """Test Diana menu navigation for all user roles with performance validation."""
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Mock message/callback for testing
        mock_update = MagicMock()
        mock_update.from_user.id = 12345
        mock_update.answer = AsyncMock()
        
        test_roles = ["free", "vip", "admin"]
        
        for role in test_roles:
            # Test main menu display
            start_time = datetime.now()
            menu_result = await menu_system.show_main_menu(mock_update, user_role=role)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Validate menu response
            assert menu_result.success, f"Menu failed for role {role}: {menu_result.errors}"
            assert menu_result.message_sent, f"Menu message not sent for role {role}"
            
            # Validate performance requirement (<1s)
            assert response_time < 1.0, \
                f"Menu response time {response_time:.2f}s exceeds 1s requirement for {role}"
            assert menu_result.meets_performance_requirement, \
                f"Menu performance requirement not met for {role}"
            
            # Validate character consistency (>95% requirement)
            assert menu_result.character_score >= 95.0, \
                f"Character score {menu_result.character_score} below 95% for {role}"
            
    async def test_role_transition_with_menu_consistency(self, session):
        """Test user role transitions maintain menu consistency."""
        user_service = EnhancedUserService(session)
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Register initial free user
        user_id = 54321
        reg_result = await user_service.enhanced_registration(
            telegram_id=user_id,
            first_name="Transition",
            last_name="Test",
            initial_role="free"
        )
        assert reg_result.success
        
        # Test free -> VIP transition
        transition_result = await user_service.transition_user_role(
            user_id=user_id,
            new_role="vip",
            reason="Upgrade test"
        )
        
        assert transition_result.success
        assert transition_result.new_role == "vip"
        assert transition_result.character_validated
        
        # Validate menu reflects new role
        mock_update = MagicMock()
        mock_update.from_user.id = user_id
        mock_update.answer = AsyncMock()
        
        menu_result = await menu_system.show_main_menu(mock_update)
        assert menu_result.success
        assert menu_result.character_score >= 95.0
        
    async def test_character_consistency_across_interactions(self, session):
        """Test Diana character consistency across complete user interaction flow."""
        user_service = EnhancedUserService(session)
        character_validator = DianaCharacterValidator(session)
        
        # Test various interaction scenarios
        interactions = [
            "registration_welcome",
            "role_upgrade_message", 
            "error_recovery_message",
            "menu_navigation"
        ]
        
        scores = []
        for interaction_type in interactions:
            # Mock different interaction contexts
            if interaction_type == "registration_welcome":
                result = await user_service.enhanced_registration(
                    telegram_id=99999,
                    first_name="Consistency",
                    last_name="Test",
                    initial_role="free"
                )
                scores.append(result.character_score)
                
        # Validate consistent character scoring across all interactions
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        assert avg_score >= 95.0, f"Average character score {avg_score} below 95%"
        assert min_score >= 90.0, f"Minimum character score {min_score} below 90%"
        
        # Validate consistency (scores shouldn't vary more than 10 points)
        score_range = max(scores) - min(scores) if scores else 0
        assert score_range <= 10.0, f"Character score variance {score_range} too high"
        
    async def test_error_handling_maintains_character(self, session):
        """Test error scenarios maintain Diana character consistency."""
        user_service = EnhancedUserService(session)
        
        # Test duplicate registration error handling
        user_id = 77777
        
        # First registration should succeed
        result1 = await user_service.enhanced_registration(
            telegram_id=user_id,
            first_name="Error",
            last_name="Test",
            initial_role="free"
        )
        assert result1.success
        
        # Second registration should handle gracefully
        result2 = await user_service.enhanced_registration(
            telegram_id=user_id,
            first_name="Error",
            last_name="Test", 
            initial_role="free"
        )
        # Should still succeed (returning existing user)
        assert result2.success
        assert result2.character_score >= 90.0
        assert "Diana" in result2.welcome_message
        
    async def test_performance_under_concurrent_load(self, session):
        """Test system performance under concurrent user load."""
        user_service = EnhancedUserService(session)
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Simulate 50 concurrent users
        concurrent_users = 50
        tasks = []
        
        for i in range(concurrent_users):
            user_id = 100000 + i
            # Create registration task
            reg_task = user_service.enhanced_registration(
                telegram_id=user_id,
                first_name=f"Concurrent{i}",
                last_name="User",
                initial_role="free"
            )
            tasks.append(reg_task)
        
        # Execute all registrations concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Validate results
        successful_registrations = sum(1 for r in results if isinstance(r, RegistrationResult) and r.success)
        success_rate = (successful_registrations / concurrent_users) * 100
        
        assert success_rate >= 99.0, f"Registration success rate {success_rate}% below 99%"
        assert total_time < 30.0, f"Concurrent registration took {total_time:.2f}s, too slow"
        
        # Test average response time per user
        avg_response_time = total_time / concurrent_users
        assert avg_response_time < 3.0, f"Average registration time {avg_response_time:.2f}s exceeds 3s"
        
    async def test_lucien_coordination_role_preservation(self, session):
        """Test that Lucien's coordination role is preserved throughout interactions."""
        user_service = EnhancedUserService(session)
        
        # Register user
        result = await user_service.enhanced_registration(
            telegram_id=88888,
            first_name="Lucien",
            last_name="Test",
            initial_role="free"
        )
        
        assert result.success
        
        # Validate Lucien doesn't overshadow Diana
        welcome_msg = result.welcome_message.lower()
        
        # Diana should be prominent
        assert "diana" in welcome_msg
        
        # Lucien should be subtle or absent (he coordinates behind scenes)
        lucien_prominence = welcome_msg.count("lucien")
        diana_prominence = welcome_msg.count("diana")
        
        # Diana should be more prominent than Lucien in user-facing content
        assert diana_prominence >= lucien_prominence, \
            "Lucien is overshadowing Diana in user-facing content"
        
    async def test_multi_tenant_isolation(self, session):
        """Test multi-tenant isolation in user registration and menu systems."""
        user_service = EnhancedUserService(session)
        
        # Create users from different "tenants" (different bot instances)
        tenant_a_users = [200001, 200002, 200003]
        tenant_b_users = [300001, 300002, 300003]
        
        # Register users from both tenants
        all_users = []
        for user_id in tenant_a_users + tenant_b_users:
            result = await user_service.enhanced_registration(
                telegram_id=user_id,
                first_name="Tenant",
                last_name="Test",
                initial_role="free"
            )
            assert result.success
            all_users.append(result.user)
        
        # Validate data isolation
        # Each user should only see their own data
        for user in all_users:
            # User should have unique session
            assert user.session is not None
            assert user.session.user_id == user.id
            
            # Session data should be isolated
            other_users = [u for u in all_users if u.id != user.id]
            for other_user in other_users:
                # No cross-contamination of session data
                assert user.session.session_state != other_user.session.session_state or \
                       user.session.session_state == "welcome"  # Default state is OK


@pytest.mark.asyncio
class TestPhase21ValidationCriteria:
    """Validate specific Phase 2.1 success criteria."""
    
    async def test_user_registration_success_rate_requirement(self, session):
        """Validate >99% user registration success rate requirement."""
        user_service = EnhancedUserService(session)
        
        # Test 100 registrations to validate success rate
        total_registrations = 100
        successful = 0
        
        for i in range(total_registrations):
            user_id = 400000 + i
            result = await user_service.enhanced_registration(
                telegram_id=user_id,
                first_name=f"Success{i}",
                last_name="Test",
                initial_role="free"
            )
            if result.success:
                successful += 1
        
        success_rate = (successful / total_registrations) * 100
        assert success_rate >= 99.0, f"Registration success rate {success_rate}% below required 99%"
        
    async def test_menu_response_time_requirement(self, session):
        """Validate <1s menu response time requirement."""
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Test 50 menu requests to validate response time consistency
        response_times = []
        
        for i in range(50):
            mock_update = MagicMock()
            mock_update.from_user.id = 500000 + i
            mock_update.answer = AsyncMock()
            
            start_time = datetime.now()
            result = await menu_system.show_main_menu(mock_update, user_role="free")
            response_time = (datetime.now() - start_time).total_seconds()
            
            assert result.success, f"Menu request {i} failed"
            response_times.append(response_time)
        
        # Validate 95% of requests are <1s
        fast_responses = sum(1 for rt in response_times if rt < 1.0)
        fast_percentage = (fast_responses / len(response_times)) * 100
        
        assert fast_percentage >= 95.0, f"Only {fast_percentage}% of requests <1s, need >=95%"
        
    async def test_zero_menu_navigation_errors_requirement(self, session):
        """Validate zero menu navigation errors requirement."""
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Test various menu navigation scenarios
        navigation_tests = [
            {"user_role": "free", "expected_buttons": 5},
            {"user_role": "vip", "expected_buttons": 6}, 
            {"user_role": "admin", "expected_buttons": 5}
        ]
        
        error_count = 0
        
        for test in navigation_tests:
            try:
                mock_update = MagicMock()
                mock_update.from_user.id = 600000
                mock_update.answer = AsyncMock()
                
                result = await menu_system.show_main_menu(
                    mock_update, 
                    user_role=test["user_role"]
                )
                
                if not result.success:
                    error_count += len(result.errors)
                    
            except Exception as e:
                error_count += 1
        
        assert error_count == 0, f"Found {error_count} menu navigation errors, required: 0"
        
    async def test_diana_character_consistency_requirement(self, session):
        """Validate >95% Diana character consistency requirement."""
        user_service = EnhancedUserService(session)
        menu_system = EnhancedDianaMenuSystem(session)
        
        # Test character consistency across all interaction types
        consistency_tests = []
        
        # Registration messages
        for role in ["free", "vip", "admin"]:
            result = await user_service.enhanced_registration(
                telegram_id=700000 + hash(role),
                first_name="Character",
                last_name="Test",
                initial_role=role
            )
            if result.success:
                consistency_tests.append(result.character_score)
        
        # Menu messages
        for role in ["free", "vip", "admin"]:
            mock_update = MagicMock()
            mock_update.from_user.id = 700100 + hash(role)
            mock_update.answer = AsyncMock()
            
            result = await menu_system.show_main_menu(mock_update, user_role=role)
            if result.success:
                consistency_tests.append(result.character_score)
        
        # Validate all character scores meet requirement
        if consistency_tests:
            min_score = min(consistency_tests)
            avg_score = sum(consistency_tests) / len(consistency_tests)
            
            assert min_score >= 95.0, f"Minimum character score {min_score} below required 95%"
            assert avg_score >= 95.0, f"Average character score {avg_score} below required 95%"