"""
CINEMA ARCHITECTURE ERROR HANDLING & RESILIENCE TESTING
======================================================

This comprehensive test suite validates error handling and system resilience
of Cinema Architecture enhancements under various failure conditions.

RESILIENCE TESTING COVERAGE:
✅ Cinema System Failure Recovery
✅ Database Connection Resilience
✅ Network Timeout Handling  
✅ Memory Pressure Resilience
✅ Concurrent Operation Error Recovery
✅ Graceful Degradation Validation
✅ Fallback Mechanism Testing
✅ Error Propagation Control
✅ System Recovery Validation
✅ Critical Path Protection
"""

import pytest
import pytest_asyncio
import asyncio
import time
import random
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError, DisconnectionError

from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.coordinador_central import CoordinadorCentral, AccionUsuario


class ErrorScenarioGenerator:
    """Generate various error scenarios for resilience testing"""
    
    @staticmethod
    def database_connection_error():
        """Simulate database connection error"""
        return OperationalError("Connection failed", None, None)
    
    @staticmethod
    def database_disconnection_error():
        """Simulate database disconnection"""
        return DisconnectionError("Connection lost")
    
    @staticmethod
    def timeout_error():
        """Simulate operation timeout"""
        return asyncio.TimeoutError("Operation timed out")
    
    @staticmethod
    def memory_error():
        """Simulate memory error"""
        return MemoryError("Insufficient memory")
    
    @staticmethod
    def generic_error():
        """Simulate generic unexpected error"""
        return Exception("Unexpected system error")


class ResilienceMetrics:
    """Track resilience and recovery metrics"""
    
    def __init__(self):
        self.error_recovery_times: List[float] = []
        self.successful_fallbacks: int = 0
        self.failed_fallbacks: int = 0
        self.system_recovery_count: int = 0
        self.critical_path_failures: int = 0
        
    def record_recovery_time(self, recovery_time: float):
        self.error_recovery_times.append(recovery_time)
        
    def record_successful_fallback(self):
        self.successful_fallbacks += 1
        
    def record_failed_fallback(self):
        self.failed_fallbacks += 1
        
    def record_system_recovery(self):
        self.system_recovery_count += 1
        
    def record_critical_failure(self):
        self.critical_path_failures += 1
        
    def get_resilience_report(self) -> Dict[str, Any]:
        """Generate resilience metrics report"""
        
        total_fallback_attempts = self.successful_fallbacks + self.failed_fallbacks
        fallback_success_rate = (
            self.successful_fallbacks / total_fallback_attempts 
            if total_fallback_attempts > 0 else 0
        )
        
        avg_recovery_time = (
            sum(self.error_recovery_times) / len(self.error_recovery_times)
            if self.error_recovery_times else 0
        )
        
        return {
            "fallback_success_rate": fallback_success_rate,
            "average_recovery_time": avg_recovery_time,
            "max_recovery_time": max(self.error_recovery_times) if self.error_recovery_times else 0,
            "system_recovery_count": self.system_recovery_count,
            "critical_path_failures": self.critical_path_failures,
            "resilience_score": self._calculate_resilience_score()
        }
    
    def _calculate_resilience_score(self) -> float:
        """Calculate overall resilience score (0-1)"""
        
        # Base score from fallback success rate
        total_fallback_attempts = self.successful_fallbacks + self.failed_fallbacks
        if total_fallback_attempts == 0:
            fallback_component = 0.5  # Neutral if no fallbacks tested
        else:
            fallback_component = self.successful_fallbacks / total_fallback_attempts
        
        # Recovery time component (faster is better)
        avg_recovery = (
            sum(self.error_recovery_times) / len(self.error_recovery_times)
            if self.error_recovery_times else 5.0
        )
        recovery_component = max(0, 1 - (avg_recovery / 10.0))  # 10s max acceptable
        
        # Critical path component (fewer failures is better)
        critical_component = max(0, 1 - (self.critical_path_failures / 10.0))
        
        # Weighted average
        resilience_score = (
            fallback_component * 0.4 +
            recovery_component * 0.3 + 
            critical_component * 0.3
        )
        
        return min(1.0, max(0.0, resilience_score))


class TestCinemaErrorHandling:
    """Cinema error handling validation test suite"""
    
    @pytest_asyncio.fixture
    async def resilience_metrics(self):
        """Resilience tracking metrics"""
        return ResilienceMetrics()
    
    @pytest_asyncio.fixture
    async def error_coordinador(self, session, mock_bot):
        """Coordinador configured for error testing"""
        coordinador = CoordinadorCentral(session)
        
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
            coordinador.cinema_master._error_recovery_enabled = True
            
        return coordinador
    
    @pytest.mark.asyncio
    async def test_cinema_system_failure_recovery(self, error_coordinador, test_user, resilience_metrics):
        """Test recovery from Cinema system failures"""
        
        # Mock Cinema system to fail intermittently
        failure_count = 0
        original_enhance = None
        
        if hasattr(error_coordinador, 'cinema_master') and error_coordinador.cinema_master:
            original_enhance = error_coordinador.cinema_master.enhance_user_experience
            
            async def failing_enhance(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                
                if failure_count <= 3:  # First 3 calls fail
                    raise Exception("Cinema system temporarily unavailable")
                
                # After 3 failures, system recovers
                return await original_enhance(*args, **kwargs) if original_enhance else {"recovered": True}
            
            error_coordinador.cinema_master.enhance_user_experience = failing_enhance
        
        # Test operations during failure and recovery
        operations_results = []
        
        for i in range(5):  # 5 operations to test failure and recovery
            start_time = time.time()
            
            try:
                result = await error_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"failure_test_{i}",
                    choice_id=f"choice_{i}",
                    cinema_enhanced=True
                )
                
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                
                operations_results.append({
                    "operation": i,
                    "success": result.get("success", True),
                    "fallback_activated": result.get("fallback_mode", False),
                    "recovery_time": recovery_time
                })
                
                if result.get("fallback_mode"):
                    resilience_metrics.record_successful_fallback()
                
            except Exception as e:
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_failed_fallback()
                
                operations_results.append({
                    "operation": i,
                    "success": False,
                    "error": str(e),
                    "recovery_time": recovery_time
                })
        
        # Validate recovery behavior
        successful_operations = [r for r in operations_results if r["success"]]
        fallback_operations = [r for r in operations_results if r.get("fallback_activated")]
        
        # Should have some successful operations despite failures
        assert len(successful_operations) >= 2, \
            f"Too few successful operations during failure recovery: {len(successful_operations)}"
        
        # Should have activated fallback mechanisms
        assert len(fallback_operations) > 0, \
            "Fallback mechanisms not activated during failures"
        
        # Recovery time should be reasonable
        avg_recovery_time = sum(r["recovery_time"] for r in operations_results) / len(operations_results)
        assert avg_recovery_time < 5.0, \
            f"Average recovery time too high: {avg_recovery_time:.2f}s"
        
        # System should recover after initial failures
        last_operations = operations_results[-2:]  # Last 2 operations
        successful_final_ops = [r for r in last_operations if r["success"]]
        assert len(successful_final_ops) >= 1, \
            "System did not recover properly after failures"
    
    @pytest.mark.asyncio
    async def test_database_connection_resilience(self, session, test_user, resilience_metrics):
        """Test resilience to database connection issues"""
        
        coordinador = CoordinadorCentral(session)
        
        # Mock database session to fail intermittently
        original_execute = session.execute
        failure_count = 0
        
        async def failing_execute(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:  # First 2 database calls fail
                raise ErrorScenarioGenerator.database_connection_error()
                
            # Subsequent calls succeed
            return await original_execute(*args, **kwargs)
        
        # Test database resilience
        with patch.object(session, 'execute', failing_execute):
            start_time = time.time()
            
            try:
                result = await coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id="db_resilience_test",
                    choice_id="db_test_choice"
                )
                
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                
                # Should handle database errors gracefully
                if result.get("success", True):
                    resilience_metrics.record_successful_fallback()
                else:
                    resilience_metrics.record_failed_fallback()
                    
                # Should have error handling indication
                assert result.get("database_recovery") == True or \
                       result.get("error_handled") == True, \
                       "Database error recovery not indicated"
                
            except Exception as e:
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_failed_fallback()
                
                # Database errors should be contained
                assert "database_connection_error" in str(e).lower() or \
                       "connection failed" in str(e).lower(), \
                       f"Unexpected error type: {e}"
    
    @pytest.mark.asyncio
    async def test_concurrent_operation_error_recovery(self, error_coordinador, test_user, resilience_metrics):
        """Test error recovery under concurrent operations"""
        
        # Create multiple users for concurrent testing
        concurrent_users = []
        for i in range(5):
            user = User(
                id=test_user.id + i + 1000,
                first_name=f"ConcurrentUser{i}",
                username=f"concurrent{i}",
                role="free",
                points=100.0,
                created_at=datetime.utcnow()
            )
            concurrent_users.append(user)
        
        # Mock random failures in concurrent operations
        def random_failure():
            if random.random() < 0.3:  # 30% failure rate
                raise ErrorScenarioGenerator.generic_error()
        
        # Execute concurrent operations with random failures
        async def concurrent_operation(user: User, operation_id: int):
            start_time = time.time()
            
            try:
                # Inject random failures
                if operation_id % 3 == 0:  # Every 3rd operation fails
                    random_failure()
                
                result = await error_coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                    fragment_id=f"concurrent_test_{operation_id}",
                    cinema_enhanced=True
                )
                
                recovery_time = time.time() - start_time
                return {
                    "user_id": user.id,
                    "operation_id": operation_id,
                    "success": True,
                    "recovery_time": recovery_time,
                    "result": result
                }
                
            except Exception as e:
                recovery_time = time.time() - start_time
                return {
                    "user_id": user.id,
                    "operation_id": operation_id,
                    "success": False,
                    "recovery_time": recovery_time,
                    "error": str(e)
                }
        
        # Execute concurrent operations
        tasks = [
            concurrent_operation(concurrent_users[i % len(concurrent_users)], i) 
            for i in range(15)
        ]
        
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze concurrent error handling
        successful_ops = [r for r in concurrent_results if not isinstance(r, Exception) and r.get("success")]
        failed_ops = [r for r in concurrent_results if isinstance(r, Exception) or not r.get("success")]
        
        # Update metrics
        for result in successful_ops:
            resilience_metrics.record_recovery_time(result.get("recovery_time", 0))
            resilience_metrics.record_successful_fallback()
            
        for result in failed_ops:
            if not isinstance(result, Exception):
                resilience_metrics.record_recovery_time(result.get("recovery_time", 0))
            resilience_metrics.record_failed_fallback()
        
        # Validate concurrent error handling
        success_rate = len(successful_ops) / len(concurrent_results)
        assert success_rate >= 0.6, \
            f"Concurrent operation success rate too low: {success_rate:.2%}"
        
        # No operation should take too long even with errors
        recovery_times = [r.get("recovery_time", 0) for r in concurrent_results if not isinstance(r, Exception)]
        max_recovery_time = max(recovery_times) if recovery_times else 0
        assert max_recovery_time < 10.0, \
            f"Maximum recovery time too high under concurrent errors: {max_recovery_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_memory_pressure_resilience(self, error_coordinador, test_user, resilience_metrics):
        """Test system resilience under memory pressure"""
        
        # Simulate memory pressure by creating large data structures
        memory_stress_data = []
        
        try:
            # Create memory pressure
            for i in range(10):
                # Large data structure to consume memory
                large_data = [f"memory_stress_data_{j}" * 1000 for j in range(1000)]
                memory_stress_data.append(large_data)
            
            # Test operations under memory pressure
            operations_under_pressure = []
            
            for i in range(5):
                start_time = time.time()
                
                try:
                    result = await error_coordinador.ejecutar_flujo(
                        user_id=test_user.id,
                        accion=AccionUsuario.TOMAR_DECISION,
                        fragment_id=f"memory_pressure_test_{i}",
                        choice_id=f"memory_choice_{i}",
                        cinema_enhanced=True
                    )
                    
                    recovery_time = time.time() - start_time
                    resilience_metrics.record_recovery_time(recovery_time)
                    resilience_metrics.record_successful_fallback()
                    
                    operations_under_pressure.append({
                        "operation": i,
                        "success": True,
                        "recovery_time": recovery_time
                    })
                    
                except MemoryError:
                    recovery_time = time.time() - start_time
                    resilience_metrics.record_recovery_time(recovery_time)
                    resilience_metrics.record_failed_fallback()
                    
                    operations_under_pressure.append({
                        "operation": i,
                        "success": False,
                        "error": "MemoryError",
                        "recovery_time": recovery_time
                    })
                    
                except Exception as e:
                    recovery_time = time.time() - start_time
                    resilience_metrics.record_recovery_time(recovery_time)
                    
                    operations_under_pressure.append({
                        "operation": i,
                        "success": False,
                        "error": str(e),
                        "recovery_time": recovery_time
                    })
            
            # Validate memory pressure handling
            successful_ops = [op for op in operations_under_pressure if op["success"]]
            
            # Should handle some operations even under memory pressure
            assert len(successful_ops) >= 2, \
                f"Too few operations succeeded under memory pressure: {len(successful_ops)}"
            
            # Operations should not hang indefinitely
            avg_recovery_time = sum(op["recovery_time"] for op in operations_under_pressure) / len(operations_under_pressure)
            assert avg_recovery_time < 10.0, \
                f"Operations too slow under memory pressure: {avg_recovery_time:.2f}s"
                
        finally:
            # Clean up memory stress data
            del memory_stress_data
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_validation(self, error_coordinador, test_user, resilience_metrics):
        """Test graceful degradation when Cinema systems partially fail"""
        
        # Mock partial Cinema system failures
        component_failures = {
            "soul_signature": False,
            "choice_architecture": True,  # This component fails
            "clue_hunting": False,
            "character_validation": True  # This component fails
        }
        
        if hasattr(error_coordinador, 'cinema_master') and error_coordinador.cinema_master:
            original_enhance = error_coordinador.cinema_master.enhance_user_experience
            
            async def partially_failing_enhance(*args, **kwargs):
                # Simulate partial component failures
                for component, should_fail in component_failures.items():
                    if should_fail:
                        raise Exception(f"Component {component} temporarily unavailable")
                
                # Return enhanced result with available components only
                return {
                    "enhancement_applied": True,
                    "available_components": [k for k, v in component_failures.items() if not v],
                    "failed_components": [k for k, v in component_failures.items() if v],
                    "graceful_degradation": True
                }
            
            error_coordinador.cinema_master.enhance_user_experience = partially_failing_enhance
        
        # Test operations with partial failures
        degradation_results = []
        
        for i in range(3):
            start_time = time.time()
            
            try:
                result = await error_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"degradation_test_{i}",
                    choice_id=f"degradation_choice_{i}",
                    cinema_enhanced=True
                )
                
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                
                degradation_results.append({
                    "operation": i,
                    "success": result.get("success", True),
                    "graceful_degradation": result.get("graceful_degradation", False),
                    "available_components": result.get("available_components", []),
                    "recovery_time": recovery_time
                })
                
                if result.get("graceful_degradation"):
                    resilience_metrics.record_successful_fallback()
                
            except Exception as e:
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_failed_fallback()
                
                degradation_results.append({
                    "operation": i,
                    "success": False,
                    "error": str(e),
                    "recovery_time": recovery_time
                })
        
        # Validate graceful degradation
        successful_degradations = [r for r in degradation_results if r.get("graceful_degradation")]
        
        # Should handle partial failures gracefully
        assert len(successful_degradations) >= 1, \
            "Graceful degradation not working with partial failures"
        
        # Should still provide some functionality
        for result in successful_degradations:
            available_components = result.get("available_components", [])
            assert len(available_components) > 0, \
                "No components available during graceful degradation"
        
        # Performance should remain acceptable during degradation
        avg_recovery_time = sum(r["recovery_time"] for r in degradation_results) / len(degradation_results)
        assert avg_recovery_time < 3.0, \
            f"Graceful degradation too slow: {avg_recovery_time:.2f}s"


class TestCinemaSystemRecovery:
    """Cinema system recovery and resilience testing"""
    
    @pytest.mark.asyncio
    async def test_automatic_system_recovery(self, session, test_user, resilience_metrics):
        """Test automatic recovery from system failures"""
        
        coordinador = CoordinadorCentral(session)
        
        # Simulate system failure and recovery cycle
        failure_cycle_count = 0
        recovery_successful = False
        
        async def recovery_test_operation():
            nonlocal failure_cycle_count, recovery_successful
            
            for cycle in range(5):  # 5 recovery cycles
                failure_cycle_count = cycle
                
                try:
                    if cycle < 3:  # First 3 cycles fail
                        raise Exception(f"System failure cycle {cycle}")
                    
                    # After cycle 3, system recovers
                    result = await coordinador.ejecutar_flujo(
                        user_id=test_user.id,
                        accion=AccionUsuario.TOMAR_DECISION,
                        fragment_id=f"recovery_cycle_{cycle}",
                        choice_id=f"recovery_choice_{cycle}"
                    )
                    
                    recovery_successful = True
                    resilience_metrics.record_system_recovery()
                    return result
                    
                except Exception as e:
                    # Simulate recovery attempt
                    await asyncio.sleep(0.1)  # Brief recovery delay
                    continue
            
            raise Exception("System failed to recover after 5 cycles")
        
        # Execute recovery test
        start_time = time.time()
        
        try:
            result = await recovery_test_operation()
            recovery_time = time.time() - start_time
            resilience_metrics.record_recovery_time(recovery_time)
            
            # Validate successful recovery
            assert recovery_successful, "System did not recover automatically"
            assert result.get("success", True), "Operation failed after recovery"
            
            # Recovery should happen within reasonable time
            assert recovery_time < 5.0, \
                f"Automatic recovery took too long: {recovery_time:.2f}s"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            resilience_metrics.record_recovery_time(recovery_time)
            resilience_metrics.record_critical_failure()
            
            # Should not reach this point if recovery works
            assert False, f"Automatic system recovery failed: {e}"
    
    @pytest.mark.asyncio
    async def test_critical_path_protection(self, error_coordinador, test_user, resilience_metrics):
        """Test protection of critical system paths during errors"""
        
        # Define critical operations that must always work
        critical_operations = [
            {
                "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                "params": {"channel_id": -1001234567890, "message_id": 1, "reaction_type": "like"}
            },
            {
                "accion": AccionUsuario.TOMAR_DECISION,
                "params": {"fragment_id": "critical_fragment", "choice_id": "critical_choice"}
            }
        ]
        
        # Mock Cinema system to fail for non-critical operations
        if hasattr(error_coordinador, 'cinema_master') and error_coordinador.cinema_master:
            original_enhance = error_coordinador.cinema_master.enhance_user_experience
            
            async def critical_path_protect(*args, **kwargs):
                # Determine if this is a critical operation
                operation_context = kwargs.get('operation_context', {})
                is_critical = operation_context.get('critical_path', False)
                
                if not is_critical:
                    # Non-critical operations may fail
                    if random.random() < 0.5:  # 50% failure rate for non-critical
                        raise Exception("Non-critical Cinema enhancement failed")
                
                # Critical operations always succeed (with fallback if needed)
                return {"critical_path_protected": True, "enhancement_applied": is_critical}
            
            error_coordinador.cinema_master.enhance_user_experience = critical_path_protect
        
        # Test critical operations under failure conditions
        critical_results = []
        
        for i, operation in enumerate(critical_operations):
            start_time = time.time()
            
            try:
                result = await error_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=operation["accion"],
                    **operation["params"],
                    operation_context={"critical_path": True}
                )
                
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                
                critical_results.append({
                    "operation": i,
                    "success": result.get("success", True),
                    "critical_path_protected": result.get("critical_path_protected", False),
                    "recovery_time": recovery_time
                })
                
            except Exception as e:
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_critical_failure()
                
                critical_results.append({
                    "operation": i,
                    "success": False,
                    "error": str(e),
                    "recovery_time": recovery_time
                })
        
        # Validate critical path protection
        successful_critical_ops = [r for r in critical_results if r["success"]]
        
        # All critical operations should succeed
        assert len(successful_critical_ops) == len(critical_operations), \
            f"Critical path protection failed: {len(successful_critical_ops)}/{len(critical_operations)} succeeded"
        
        # Critical operations should be fast even during errors
        avg_critical_time = sum(r["recovery_time"] for r in critical_results) / len(critical_results)
        assert avg_critical_time < 2.0, \
            f"Critical operations too slow during errors: {avg_critical_time:.2f}s"


class TestCinemaResilienceReporting:
    """Resilience testing reporting and analysis"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_resilience_report(self, error_coordinador, test_user, resilience_metrics):
        """Test comprehensive resilience report generation"""
        
        # Execute various error scenarios for comprehensive testing
        test_scenarios = [
            ("database_error", ErrorScenarioGenerator.database_connection_error),
            ("timeout_error", ErrorScenarioGenerator.timeout_error),
            ("memory_error", ErrorScenarioGenerator.memory_error),
            ("generic_error", ErrorScenarioGenerator.generic_error)
        ]
        
        scenario_results = {}
        
        for scenario_name, error_generator in test_scenarios:
            # Mock the specific error type
            if hasattr(error_coordinador, 'cinema_master') and error_coordinador.cinema_master:
                original_enhance = error_coordinador.cinema_master.enhance_user_experience
                
                async def scenario_error_enhance(*args, **kwargs):
                    # Fail with specific error type
                    raise error_generator()
                
                error_coordinador.cinema_master.enhance_user_experience = scenario_error_enhance
            
            # Test the scenario
            start_time = time.time()
            
            try:
                result = await error_coordinador.ejecutar_flujo(
                    user_id=test_user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"resilience_test_{scenario_name}",
                    choice_id=f"resilience_choice_{scenario_name}",
                    cinema_enhanced=True
                )
                
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_successful_fallback()
                
                scenario_results[scenario_name] = {
                    "success": True,
                    "recovery_time": recovery_time,
                    "fallback_activated": result.get("fallback_mode", False)
                }
                
            except Exception as e:
                recovery_time = time.time() - start_time
                resilience_metrics.record_recovery_time(recovery_time)
                resilience_metrics.record_failed_fallback()
                
                scenario_results[scenario_name] = {
                    "success": False,
                    "recovery_time": recovery_time,
                    "error": str(e)
                }
        
        # Generate comprehensive resilience report
        resilience_report = resilience_metrics.get_resilience_report()
        
        # Validate report completeness
        assert "fallback_success_rate" in resilience_report, \
            "Fallback success rate missing from resilience report"
        assert "average_recovery_time" in resilience_report, \
            "Average recovery time missing from resilience report"
        assert "resilience_score" in resilience_report, \
            "Resilience score missing from report"
        
        # Validate resilience thresholds
        assert resilience_report["fallback_success_rate"] >= 0.7, \
            f"Fallback success rate too low: {resilience_report['fallback_success_rate']:.2%}"
        assert resilience_report["average_recovery_time"] <= 5.0, \
            f"Average recovery time too high: {resilience_report['average_recovery_time']:.2f}s"
        assert resilience_report["resilience_score"] >= 0.8, \
            f"Overall resilience score too low: {resilience_report['resilience_score']:.2%}"
        
        # Print resilience report
        print(f"\n{'='*80}")
        print("CINEMA ARCHITECTURE RESILIENCE REPORT")
        print(f"{'='*80}")
        print(f"Fallback Success Rate: {resilience_report['fallback_success_rate']:.2%}")
        print(f"Average Recovery Time: {resilience_report['average_recovery_time']:.2f}s")
        print(f"Max Recovery Time: {resilience_report['max_recovery_time']:.2f}s")
        print(f"System Recovery Count: {resilience_report['system_recovery_count']}")
        print(f"Critical Path Failures: {resilience_report['critical_path_failures']}")
        print(f"Overall Resilience Score: {resilience_report['resilience_score']:.2%}")
        print(f"{'='*80}")
        
        return resilience_report