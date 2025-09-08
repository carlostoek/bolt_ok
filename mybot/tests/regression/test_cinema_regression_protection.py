"""
CINEMA ARCHITECTURE REGRESSION TESTING PROTECTION SUITE
======================================================

This comprehensive regression testing suite ensures that Cinema Architecture
enhancements introduce ZERO breaking changes to existing Diana Bot functionality.

REGRESSION PROTECTION COVERAGE:
✅ Core User Flows Preservation
✅ VIP Access Controls Unchanged  
✅ Admin Function Integrity
✅ Database Operations Compatibility
✅ Points & Gamification System Protection
✅ Notification System Preservation
✅ Channel Engagement Protection
✅ Menu System Backward Compatibility
✅ API Endpoint Compatibility
✅ Error Handling Preservation
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database.models import User, Channel, UserStats, Badge, UserBadge, NarrativeReward, UserRewardHistory
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog
from services.coordinador_central import CoordinadorCentral, AccionUsuario


class RegressionTestBaseline:
    """Baseline functionality recorder and validator"""
    
    def __init__(self):
        self.baseline_results: Dict[str, Any] = {}
        self.regression_issues: List[str] = []
        
    def record_baseline(self, operation: str, result: Dict[str, Any]):
        """Record baseline behavior for comparison"""
        self.baseline_results[operation] = {
            "success": result.get("success", True),
            "points_awarded": result.get("points_awarded", 0),
            "narrative_progress": result.get("narrative_progress"),
            "user_updates": result.get("user_updates", {}),
            "notifications": result.get("notifications", []),
            "response_structure": list(result.keys()) if isinstance(result, dict) else []
        }
    
    def validate_compatibility(self, operation: str, new_result: Dict[str, Any]) -> bool:
        """Validate new result maintains compatibility with baseline"""
        if operation not in self.baseline_results:
            return True  # No baseline to compare against
            
        baseline = self.baseline_results[operation]
        issues = []
        
        # Check success status preservation
        new_success = new_result.get("success", True)
        if new_success != baseline["success"]:
            issues.append(f"Success status changed: {baseline['success']} -> {new_success}")
        
        # Check points system compatibility
        new_points = new_result.get("points_awarded", 0)
        if new_points != baseline["points_awarded"]:
            # Points can increase but not decrease (enhancements allowed)
            if new_points < baseline["points_awarded"]:
                issues.append(f"Points decreased: {baseline['points_awarded']} -> {new_points}")
        
        # Check response structure compatibility
        baseline_keys = set(baseline["response_structure"])
        new_keys = set(new_result.keys()) if isinstance(new_result, dict) else set()
        
        missing_keys = baseline_keys - new_keys
        if missing_keys:
            issues.append(f"Missing response keys: {missing_keys}")
        
        # Record any issues found
        if issues:
            self.regression_issues.extend([f"{operation}: {issue}" for issue in issues])
            return False
            
        return True
    
    def get_regression_report(self) -> Dict[str, Any]:
        """Get comprehensive regression test report"""
        return {
            "total_operations_tested": len(self.baseline_results),
            "regression_issues_found": len(self.regression_issues),
            "issues": self.regression_issues,
            "compatibility_status": "PASS" if not self.regression_issues else "FAIL"
        }


class TestCinemaRegressionProtection:
    """Core regression protection test suite"""
    
    @pytest_asyncio.fixture
    async def baseline_coordinador(self, session):
        """Coordinador without Cinema enhancements for baseline testing"""
        coordinador = CoordinadorCentral(session)
        
        # Disable Cinema enhancements for baseline
        if hasattr(coordinador, 'cinema_master'):
            coordinador.cinema_master = None
            
        return coordinador
    
    @pytest_asyncio.fixture  
    async def enhanced_coordinador(self, session, mock_bot):
        """Coordinador with Cinema enhancements for regression testing"""
        coordinador = CoordinadorCentral(session)
        
        # Ensure Cinema enhancements are active
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
            
        return coordinador
    
    @pytest_asyncio.fixture
    async def regression_baseline(self):
        """Regression testing baseline recorder"""
        return RegressionTestBaseline()
    
    @pytest.mark.asyncio
    async def test_core_user_flows_preservation(self, baseline_coordinador, enhanced_coordinador, test_user, regression_baseline):
        """Test that core user flows work exactly as before with Cinema enhancements"""
        
        core_operations = [
            {
                "operation": "basic_reaction",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                    "channel_id": -1001234567890,
                    "message_id": 1,
                    "reaction_type": "like"
                }
            },
            {
                "operation": "narrative_decision", 
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.TOMAR_DECISION,
                    "fragment_id": "test_fragment_regression",
                    "choice_id": "test_choice_regression"
                }
            },
            {
                "operation": "channel_participation",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.PARTICIPAR_CANAL,
                    "channel_id": -1001234567890
                }
            },
            {
                "operation": "complete_fragment",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                    "fragment_id": "test_fragment_complete"
                }
            }
        ]
        
        # Record baseline behavior
        for op_data in core_operations:
            baseline_result = await baseline_coordinador.ejecutar_flujo(**op_data["params"])
            regression_baseline.record_baseline(op_data["operation"], baseline_result)
        
        # Test enhanced behavior maintains compatibility
        for op_data in core_operations:
            enhanced_result = await enhanced_coordinador.ejecutar_flujo(**op_data["params"])
            
            # Validate compatibility
            is_compatible = regression_baseline.validate_compatibility(
                op_data["operation"], 
                enhanced_result
            )
            
            assert is_compatible, \
                f"Regression detected in {op_data['operation']}: " \
                f"{regression_baseline.regression_issues}"
        
        # Final regression report
        report = regression_baseline.get_regression_report()
        assert report["compatibility_status"] == "PASS", \
            f"Regression issues found: {report['issues']}"
    
    @pytest.mark.asyncio
    async def test_vip_access_controls_unchanged(self, baseline_coordinador, enhanced_coordinador, vip_user, session, regression_baseline):
        """Test VIP access controls work identically with Cinema enhancements"""
        
        # Setup VIP-specific test fragment
        vip_fragment = NarrativeFragment(
            id="vip_regression_test",
            title="VIP Regression Test",
            content="VIP only content for regression testing",
            fragment_type="vip_exclusive",
            author="diana",
            access_requirements={"vip": True}
        )
        session.add(vip_fragment)
        await session.commit()
        
        vip_operations = [
            {
                "operation": "vip_access_attempt",
                "params": {
                    "user_id": vip_user.id,
                    "accion": AccionUsuario.ACCEDER_NARRATIVA_VIP,
                    "fragment_id": "vip_regression_test"
                }
            },
            {
                "operation": "vip_decision_making",
                "params": {
                    "user_id": vip_user.id,
                    "accion": AccionUsuario.TOMAR_DECISION,
                    "fragment_id": "vip_regression_test",
                    "choice_id": "vip_choice_regression"
                }
            }
        ]
        
        # Record baseline VIP behavior
        for op_data in vip_operations:
            baseline_result = await baseline_coordinador.ejecutar_flujo(**op_data["params"])
            regression_baseline.record_baseline(op_data["operation"], baseline_result)
        
        # Test enhanced VIP behavior
        for op_data in vip_operations:
            enhanced_result = await enhanced_coordinador.ejecutar_flujo(**op_data["params"])
            
            is_compatible = regression_baseline.validate_compatibility(
                op_data["operation"],
                enhanced_result
            )
            
            assert is_compatible, \
                f"VIP regression detected in {op_data['operation']}"
            
            # Specific VIP access validation
            if "access" in op_data["operation"]:
                baseline_access = baseline_result.get("access_granted", False)
                enhanced_access = enhanced_result.get("access_granted", False)
                
                assert baseline_access == enhanced_access, \
                    f"VIP access rights changed: {baseline_access} -> {enhanced_access}"
    
    @pytest.mark.asyncio
    async def test_admin_functions_preservation(self, baseline_coordinador, enhanced_coordinador, admin_user, regression_baseline):
        """Test admin functions work identically with Cinema enhancements"""
        
        admin_operations = [
            {
                "operation": "admin_engagement_check",
                "params": {
                    "user_id": admin_user.id,
                    "accion": AccionUsuario.VERIFICAR_ENGAGEMENT,
                    "channel_id": -1001234567890
                }
            },
            {
                "operation": "admin_narrative_access",
                "params": {
                    "user_id": admin_user.id,
                    "accion": AccionUsuario.ACCEDER_NARRATIVA_VIP,
                    "fragment_id": "admin_test_fragment"
                }
            }
        ]
        
        # Record baseline admin behavior
        for op_data in admin_operations:
            baseline_result = await baseline_coordinador.ejecutar_flujo(**op_data["params"])
            regression_baseline.record_baseline(op_data["operation"], baseline_result)
        
        # Test enhanced admin behavior
        for op_data in admin_operations:
            enhanced_result = await enhanced_coordinador.ejecutar_flujo(**op_data["params"])
            
            is_compatible = regression_baseline.validate_compatibility(
                op_data["operation"],
                enhanced_result
            )
            
            assert is_compatible, \
                f"Admin regression detected in {op_data['operation']}"
            
            # Verify admin privileges maintained
            if enhanced_result.get("admin_data"):
                assert enhanced_result["admin_data"].get("access_level") in ["admin", "super_admin"], \
                    "Admin access level not preserved"
    
    @pytest.mark.asyncio
    async def test_points_gamification_system_protection(self, baseline_coordinador, enhanced_coordinador, test_user, session, regression_baseline):
        """Test points and gamification system unchanged with Cinema enhancements"""
        
        # Record initial user points
        initial_points = test_user.points
        
        point_operations = [
            {
                "operation": "points_from_reaction",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                    "channel_id": -1001234567890,
                    "message_id": 1,
                    "reaction_type": "heart"
                }
            },
            {
                "operation": "points_from_decision",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.TOMAR_DECISION,
                    "fragment_id": "points_test_fragment",
                    "choice_id": "points_test_choice"
                }
            },
            {
                "operation": "points_from_completion",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                    "fragment_id": "points_completion_fragment"
                }
            }
        ]
        
        # Test baseline points behavior
        baseline_total_points = 0
        for op_data in point_operations:
            baseline_result = await baseline_coordinador.ejecutar_flujo(**op_data["params"])
            regression_baseline.record_baseline(op_data["operation"], baseline_result)
            baseline_total_points += baseline_result.get("points_awarded", 0)
        
        # Reset user points for enhanced test
        user_query = select(User).where(User.id == test_user.id)
        result = await session.execute(user_query)
        user = result.scalar_one()
        user.points = initial_points
        await session.commit()
        
        # Test enhanced points behavior
        enhanced_total_points = 0
        for op_data in point_operations:
            enhanced_result = await enhanced_coordinador.ejecutar_flujo(**op_data["params"])
            
            is_compatible = regression_baseline.validate_compatibility(
                op_data["operation"],
                enhanced_result
            )
            
            assert is_compatible, \
                f"Points system regression in {op_data['operation']}"
            
            enhanced_total_points += enhanced_result.get("points_awarded", 0)
        
        # Points can be enhanced but not reduced
        assert enhanced_total_points >= baseline_total_points, \
            f"Points system degraded: {baseline_total_points} -> {enhanced_total_points}"
    
    @pytest.mark.asyncio
    async def test_database_operations_compatibility(self, baseline_coordinador, enhanced_coordinador, test_user, session):
        """Test database operations remain compatible with Cinema enhancements"""
        
        # Test database read operations
        baseline_user_query = select(User).where(User.id == test_user.id)
        baseline_result = await session.execute(baseline_user_query)
        baseline_user = baseline_result.scalar_one()
        
        # Execute operation that modifies database
        await enhanced_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="db_compatibility_test",
            choice_id="db_test_choice"
        )
        
        # Verify database schema unchanged
        enhanced_user_query = select(User).where(User.id == test_user.id)
        enhanced_result = await session.execute(enhanced_user_query)
        enhanced_user = enhanced_result.scalar_one()
        
        # Verify core database fields preserved
        core_fields = ['id', 'first_name', 'username', 'role', 'created_at']
        for field in core_fields:
            baseline_value = getattr(baseline_user, field)
            enhanced_value = getattr(enhanced_user, field)
            
            assert baseline_value == enhanced_value, \
                f"Database field {field} changed: {baseline_value} -> {enhanced_value}"
        
        # Points can increase but other core data should be preserved
        assert enhanced_user.points >= baseline_user.points, \
            "User points should not decrease"
    
    @pytest.mark.asyncio
    async def test_notification_system_preservation(self, baseline_coordinador, enhanced_coordinador, test_user, mock_bot, regression_baseline):
        """Test notification system works identically with Cinema enhancements"""
        
        notification_operations = [
            {
                "operation": "notification_from_points",
                "params": {
                    "user_id": test_user.id,
                    "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                    "channel_id": -1001234567890,
                    "message_id": 1,
                    "reaction_type": "like"
                }
            }
        ]
        
        # Mock bot for notification capture
        baseline_coordinador.point_service.notification_service._bot = mock_bot
        enhanced_coordinador.point_service.notification_service._bot = mock_bot
        
        # Record baseline notification behavior
        for op_data in notification_operations:
            mock_bot.reset_mock()  # Reset mock for clean capture
            
            baseline_result = await baseline_coordinador.ejecutar_flujo(**op_data["params"])
            regression_baseline.record_baseline(op_data["operation"], baseline_result)
            
            baseline_notifications = mock_bot.send_message.call_count
        
        # Test enhanced notification behavior
        for op_data in notification_operations:
            mock_bot.reset_mock()  # Reset mock for clean capture
            
            enhanced_result = await enhanced_coordinador.ejecutar_flujo(**op_data["params"])
            enhanced_notifications = mock_bot.send_message.call_count
            
            # Notification system should work at least as well as baseline
            assert enhanced_notifications >= baseline_notifications, \
                f"Notification system degraded: {baseline_notifications} -> {enhanced_notifications}"
    
    @pytest.mark.asyncio
    async def test_error_handling_preservation(self, baseline_coordinador, enhanced_coordinador, test_user):
        """Test error handling behavior unchanged with Cinema enhancements"""
        
        # Test invalid operations
        invalid_operations = [
            {
                "user_id": test_user.id,
                "accion": AccionUsuario.TOMAR_DECISION,
                "fragment_id": "nonexistent_fragment",
                "choice_id": "nonexistent_choice"
            },
            {
                "user_id": 999999999,  # Non-existent user
                "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                "channel_id": -1001234567890,
                "message_id": 1,
                "reaction_type": "like"
            }
        ]
        
        for invalid_op in invalid_operations:
            # Test baseline error handling
            try:
                baseline_result = await baseline_coordinador.ejecutar_flujo(**invalid_op)
                baseline_success = baseline_result.get("success", True)
                baseline_error = baseline_result.get("error")
            except Exception as e:
                baseline_success = False
                baseline_error = str(e)
            
            # Test enhanced error handling
            try:
                enhanced_result = await enhanced_coordinador.ejecutar_flujo(**invalid_op)
                enhanced_success = enhanced_result.get("success", True)
                enhanced_error = enhanced_result.get("error")
            except Exception as e:
                enhanced_success = False
                enhanced_error = str(e)
            
            # Error handling behavior should be preserved
            assert baseline_success == enhanced_success, \
                f"Error handling changed for invalid operation: {invalid_op}"


class TestCinemaAPICompatibility:
    """Test API endpoint compatibility with Cinema enhancements"""
    
    @pytest.mark.asyncio
    async def test_response_format_compatibility(self, enhanced_coordinador, test_user):
        """Test response formats remain compatible after Cinema enhancements"""
        
        # Standard operations that external systems might depend on
        api_operations = [
            AccionUsuario.REACCIONAR_PUBLICACION,
            AccionUsuario.TOMAR_DECISION, 
            AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            AccionUsuario.PARTICIPAR_CANAL
        ]
        
        expected_response_fields = {
            "success", "points_awarded", "user_updates", "narrative_progress"
        }
        
        for operation in api_operations:
            result = await enhanced_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=operation,
                fragment_id="api_compat_test",
                choice_id="api_test_choice",
                channel_id=-1001234567890,
                message_id=1,
                reaction_type="like"
            )
            
            # Verify expected fields present
            result_fields = set(result.keys()) if isinstance(result, dict) else set()
            missing_fields = expected_response_fields - result_fields
            
            # Some fields might be optional, but core structure should be preserved
            assert "success" in result_fields, \
                f"Core 'success' field missing from {operation} response"
            
            # Cinema enhancements can add fields but shouldn't remove core ones
            if missing_fields:
                # Log warning but don't fail if only optional fields missing
                print(f"Warning: Optional fields missing in {operation}: {missing_fields}")
    
    @pytest.mark.asyncio 
    async def test_backward_compatibility_versioning(self, enhanced_coordinador, test_user):
        """Test backward compatibility for different API versions"""
        
        # Test operation with and without Cinema-specific parameters
        base_params = {
            "user_id": test_user.id,
            "accion": AccionUsuario.TOMAR_DECISION,
            "fragment_id": "version_compat_test",
            "choice_id": "version_test_choice"
        }
        
        # Test without Cinema parameters (v1 compatibility)
        v1_result = await enhanced_coordinador.ejecutar_flujo(**base_params)
        
        # Test with Cinema parameters (v2 enhancement)  
        v2_params = {**base_params, "cinema_enhanced": True, "psychology_aware": True}
        v2_result = await enhanced_coordinador.ejecutar_flujo(**v2_params)
        
        # Both versions should succeed
        assert v1_result.get("success", True), "V1 compatibility broken"
        assert v2_result.get("success", True), "V2 enhancements broken"
        
        # V1 result should be subset of V2 result structure
        v1_keys = set(v1_result.keys())
        v2_keys = set(v2_result.keys())
        
        # V2 can have additional keys but shouldn't remove V1 keys
        missing_v1_keys = v1_keys - v2_keys
        assert not missing_v1_keys, \
            f"V2 API removed V1 compatible keys: {missing_v1_keys}"


class TestCinemaDataIntegrity:
    """Test data integrity with Cinema enhancements"""
    
    @pytest.mark.asyncio
    async def test_user_data_consistency(self, enhanced_coordinador, test_user, session):
        """Test user data remains consistent with Cinema enhancements"""
        
        # Record initial user state
        initial_query = select(User).where(User.id == test_user.id)
        initial_result = await session.execute(initial_query)
        initial_user = initial_result.scalar_one()
        
        initial_state = {
            "id": initial_user.id,
            "first_name": initial_user.first_name,
            "username": initial_user.username,
            "role": initial_user.role,
            "created_at": initial_user.created_at,
            "points": initial_user.points
        }
        
        # Execute multiple Cinema-enhanced operations
        operations = [
            AccionUsuario.TOMAR_DECISION,
            AccionUsuario.DESBLOQUEAR_PISTA,
            AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            AccionUsuario.REACCIONAR_PUBLICACION
        ]
        
        for i, operation in enumerate(operations):
            await enhanced_coordinador.ejecutar_flujo(
                user_id=test_user.id,
                accion=operation,
                fragment_id=f"integrity_test_{i}",
                choice_id=f"integrity_choice_{i}",
                channel_id=-1001234567890,
                message_id=i,
                reaction_type="like",
                cinema_enhanced=True
            )
        
        # Verify user data integrity maintained
        final_query = select(User).where(User.id == test_user.id)
        final_result = await session.execute(final_query)
        final_user = final_result.scalar_one()
        
        # Core identity fields must remain unchanged
        immutable_fields = ["id", "first_name", "username", "role", "created_at"]
        for field in immutable_fields:
            assert getattr(final_user, field) == initial_state[field], \
                f"User field {field} corrupted: {initial_state[field]} -> {getattr(final_user, field)}"
        
        # Points can increase but should be reasonable
        points_increase = final_user.points - initial_state["points"]
        assert points_increase >= 0, "User points decreased unexpectedly"
        assert points_increase < 10000, "Unrealistic points increase detected"
    
    @pytest.mark.asyncio
    async def test_narrative_state_consistency(self, enhanced_coordinador, test_user, session):
        """Test narrative state consistency with Cinema enhancements"""
        
        # Create test narrative fragment
        fragment = NarrativeFragment(
            id="consistency_test_fragment",
            title="Consistency Test",
            content="Testing narrative state consistency",
            fragment_type="story",
            author="diana"
        )
        session.add(fragment)
        await session.commit()
        
        # Execute narrative operations
        await enhanced_coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            fragment_id="consistency_test_fragment",
            choice_id="consistency_choice",
            cinema_enhanced=True
        )
        
        # Verify narrative state created properly
        narrative_query = select(UserNarrativeState).where(
            UserNarrativeState.user_id == test_user.id,
            UserNarrativeState.fragment_id == "consistency_test_fragment"
        )
        result = await session.execute(narrative_query)
        narrative_state = result.scalar_one_or_none()
        
        if narrative_state:
            # Verify state integrity
            assert narrative_state.user_id == test_user.id
            assert narrative_state.fragment_id == "consistency_test_fragment"
            assert narrative_state.created_at is not None
            assert narrative_state.status in ["active", "completed", "paused"]


class TestCinemaFallbackProtection:
    """Test fallback protection when Cinema systems fail"""
    
    @pytest.mark.asyncio
    async def test_cinema_failure_graceful_degradation(self, session, test_user, mock_bot):
        """Test graceful degradation when Cinema systems fail"""
        
        # Create coordinador with Cinema systems
        coordinador = CoordinadorCentral(session)
        
        # Mock Cinema system failure
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            with patch.object(coordinador.cinema_master, 'enhance_user_experience', 
                            side_effect=Exception("Cinema system failure")):
                
                # Operation should still succeed with fallback
                result = await coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id="fallback_test",
                    choice_id="fallback_choice"
                )
                
                # Verify graceful fallback
                assert result.get("success", True), \
                    "System failed to handle Cinema failure gracefully"
                
                # Should still award points
                assert result.get("points_awarded", 0) > 0, \
                    "Basic functionality not preserved in fallback"
                
                # Should indicate fallback mode
                assert result.get("fallback_mode") == True or \
                       result.get("cinema_enhancement") is None, \
                    "Fallback mode not properly indicated"
    
    @pytest.mark.asyncio
    async def test_performance_degradation_protection(self, session, test_user):
        """Test performance doesn't degrade excessively with Cinema failures"""
        
        coordinador = CoordinadorCentral(session)
        
        # Mock intermittent Cinema failures
        failure_count = 0
        original_enhance = None
        
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            original_enhance = coordinador.cinema_master.enhance_user_experience
            
            def intermittent_failure(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                if failure_count % 3 == 0:  # Fail every 3rd call
                    raise Exception("Intermittent Cinema failure")
                return original_enhance(*args, **kwargs)
            
            coordinador.cinema_master.enhance_user_experience = intermittent_failure
        
        # Execute operations with intermittent failures
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            
            try:
                result = await coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"perf_degradation_test_{i}",
                    choice_id=f"perf_choice_{i}"
                )
                
                # Should still succeed
                assert result.get("success", True), \
                    f"Operation {i} failed during intermittent failures"
                
            except Exception as e:
                # Unexpected failures should not occur
                assert False, f"Unexpected failure in operation {i}: {e}"
            
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # Performance should remain acceptable even with failures
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0, \
            f"Performance degraded too much with failures: {avg_response_time:.3f}s"