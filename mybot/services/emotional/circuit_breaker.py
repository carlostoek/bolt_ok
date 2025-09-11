"""
Circuit Breaker Pattern for Emotional System
Protects core functionality from emotional system failures
"""
import asyncio
import logging
import time
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, circuit open
    HALF_OPEN = "half_open"  # Testing if system has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Number of failures before opening
    recovery_timeout: int = 60        # Seconds to wait before trying again
    request_timeout: float = 5.0      # Timeout for individual requests
    success_threshold: int = 3        # Successes needed to close from half-open
    failure_rate_threshold: float = 0.5  # Failure rate (0.0-1.0) to open circuit
    min_requests: int = 10            # Minimum requests before calculating failure rate


class EmotionalSystemUnavailableError(Exception):
    """Exception raised when emotional system is unavailable due to circuit breaker"""
    pass


class EmotionalSystemTimeoutError(Exception):
    """Exception raised when emotional system operation times out"""
    pass


class EmotionalSystemCircuitBreaker:
    """
    Circuit breaker for emotional system operations.
    
    Provides:
    - Automatic failure detection
    - Circuit opening when failure threshold exceeded
    - Automatic recovery testing
    - Request timeout protection
    - Failure rate monitoring
    - Per-operation circuit tracking
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        
        # Circuit state tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_request_time = None
        
        # Request tracking for failure rate calculation
        self.recent_requests = []  # List of (timestamp, success_bool)
        self.request_window = 300  # 5 minutes
        
        # Per-operation tracking
        self.operation_stats = defaultdict(lambda: {
            'failures': 0,
            'successes': 0,
            'last_failure': None
        })
        
        # Recovery testing
        self.recovery_start_time = None

    async def call(self, operation: Callable, operation_name: str = "unknown") -> Any:
        """
        Execute an operation through the circuit breaker.
        
        Args:
            operation: Async callable to execute
            operation_name: Name of the operation for tracking
            
        Returns:
            Result of the operation
            
        Raises:
            EmotionalSystemUnavailableError: When circuit is open
            EmotionalSystemTimeoutError: When operation times out
        """
        # Check if circuit should be opened based on current state
        await self._check_circuit_state()
        
        if self.state == CircuitState.OPEN:
            raise EmotionalSystemUnavailableError(
                f"Emotional system circuit is open due to failures. "
                f"Last failure: {self.last_failure_time}"
            )
        
        start_time = time.time()
        self.last_request_time = start_time
        
        try:
            # Execute operation with timeout
            result = await asyncio.wait_for(
                operation(),
                timeout=self.config.request_timeout
            )
            
            # Record success
            await self._record_success(operation_name, time.time() - start_time)
            return result
            
        except asyncio.TimeoutError:
            error = EmotionalSystemTimeoutError(
                f"Emotional system operation '{operation_name}' timed out after "
                f"{self.config.request_timeout} seconds"
            )
            await self._record_failure(operation_name, error, time.time() - start_time)
            raise error
            
        except Exception as e:
            await self._record_failure(operation_name, e, time.time() - start_time)
            raise e

    def is_healthy(self) -> bool:
        """Check if the circuit breaker considers the system healthy"""
        return self.state == CircuitState.CLOSED or (
            self.state == CircuitState.HALF_OPEN and 
            self.success_count >= self.config.success_threshold
        )

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        failure_rate = self._calculate_failure_rate()
        
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_rate": failure_rate,
            "last_failure_time": self.last_failure_time,
            "last_request_time": self.last_request_time,
            "operation_stats": dict(self.operation_stats),
            "total_recent_requests": len(self.recent_requests),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "request_timeout": self.config.request_timeout,
                "success_threshold": self.config.success_threshold,
                "failure_rate_threshold": self.config.failure_rate_threshold
            }
        }

    async def reset(self):
        """Reset circuit breaker to closed state (for admin use)"""
        logger.info("Circuit breaker manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.recovery_start_time = None
        self.recent_requests.clear()
        self.operation_stats.clear()

    async def force_open(self):
        """Force circuit breaker to open state (for emergency use)"""
        logger.warning("Circuit breaker manually forced open")
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()

    # Private methods
    async def _check_circuit_state(self):
        """Check and update circuit state based on current conditions"""
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            # Check if we should try recovery
            if (self.last_failure_time and 
                current_time - self.last_failure_time >= self.config.recovery_timeout):
                logger.info("Circuit breaker entering half-open state for recovery testing")
                self.state = CircuitState.HALF_OPEN
                self.recovery_start_time = current_time
                self.success_count = 0
        
        elif self.state == CircuitState.HALF_OPEN:
            # Check if we should close (enough successes) or open (any failure)
            if self.success_count >= self.config.success_threshold:
                logger.info("Circuit breaker closing - recovery successful")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.recovery_start_time = None
        
        elif self.state == CircuitState.CLOSED:
            # Check if we should open due to failures
            should_open = (
                self.failure_count >= self.config.failure_threshold or
                self._should_open_due_to_failure_rate()
            )
            
            if should_open:
                logger.warning(
                    f"Circuit breaker opening - failures: {self.failure_count}, "
                    f"failure rate: {self._calculate_failure_rate():.2f}"
                )
                self.state = CircuitState.OPEN
                self.last_failure_time = current_time

    def _should_open_due_to_failure_rate(self) -> bool:
        """Check if circuit should open due to high failure rate"""
        failure_rate = self._calculate_failure_rate()
        request_count = len(self.recent_requests)
        
        return (
            request_count >= self.config.min_requests and
            failure_rate >= self.config.failure_rate_threshold
        )

    def _calculate_failure_rate(self) -> float:
        """Calculate failure rate over recent requests"""
        self._clean_old_requests()
        
        if not self.recent_requests:
            return 0.0
        
        failures = sum(1 for _, success in self.recent_requests if not success)
        return failures / len(self.recent_requests)

    def _clean_old_requests(self):
        """Remove old requests from tracking window"""
        current_time = time.time()
        cutoff_time = current_time - self.request_window
        
        self.recent_requests = [
            (timestamp, success) 
            for timestamp, success in self.recent_requests
            if timestamp > cutoff_time
        ]

    async def _record_success(self, operation_name: str, duration: float):
        """Record a successful operation"""
        current_time = time.time()
        
        # Update global counters
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on successful operations
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
        
        # Update operation-specific stats
        self.operation_stats[operation_name]['successes'] += 1
        
        # Update recent requests for failure rate calculation
        self.recent_requests.append((current_time, True))
        self._clean_old_requests()
        
        logger.debug(f"Circuit breaker: Success for '{operation_name}' in {duration:.2f}s")

    async def _record_failure(self, operation_name: str, error: Exception, duration: float):
        """Record a failed operation"""
        current_time = time.time()
        
        # Update global counters
        self.failure_count += 1
        self.last_failure_time = current_time
        
        # In half-open state, any failure immediately opens the circuit
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker opening - failure during recovery testing")
            self.state = CircuitState.OPEN
        
        # Update operation-specific stats
        self.operation_stats[operation_name]['failures'] += 1
        self.operation_stats[operation_name]['last_failure'] = current_time
        
        # Update recent requests for failure rate calculation
        self.recent_requests.append((current_time, False))
        self._clean_old_requests()
        
        logger.warning(
            f"Circuit breaker: Failure for '{operation_name}' in {duration:.2f}s - {error}"
        )


# Global instance for the emotional system
_global_circuit_breaker = None


def get_emotional_circuit_breaker() -> EmotionalSystemCircuitBreaker:
    """Get the global emotional system circuit breaker instance"""
    global _global_circuit_breaker
    
    if _global_circuit_breaker is None:
        _global_circuit_breaker = EmotionalSystemCircuitBreaker()
    
    return _global_circuit_breaker


async def with_circuit_breaker(operation: Callable, operation_name: str = "emotional_operation") -> Any:
    """
    Convenience function to execute operation with circuit breaker protection.
    
    Usage:
        result = await with_circuit_breaker(
            lambda: my_emotional_operation(args),
            "emotional_analysis"
        )
    """
    circuit_breaker = get_emotional_circuit_breaker()
    return await circuit_breaker.call(operation, operation_name)