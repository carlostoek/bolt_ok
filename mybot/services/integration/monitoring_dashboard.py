"""
Integration Monitoring Dashboard
Comprehensive monitoring for emotional system integration
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text

from database.models import User, ButtonReaction, UserStats
from services.emotional.circuit_breaker import get_emotional_circuit_breaker
from services.emotional.feature_flags import EmotionalFeatureFlags

logger = logging.getLogger(__name__)


@dataclass
class HealthMetric:
    """Health metric data structure"""
    name: str
    value: float
    threshold: float
    status: str  # "healthy", "warning", "critical"
    timestamp: datetime
    details: Dict[str, Any] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    operation: str
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    total_requests: int
    timestamp: datetime


@dataclass
class IntegrationAlert:
    """Integration alert data structure"""
    alert_id: str
    severity: str  # "info", "warning", "critical"
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class IntegrationMonitoring:
    """
    Comprehensive monitoring system for emotional integration.
    
    Monitors:
    - Core functionality health
    - Performance impact
    - Feature flag usage
    - Circuit breaker status
    - User satisfaction metrics
    - Error rates and patterns
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Metrics storage
        self.health_metrics = deque(maxlen=1000)
        self.performance_metrics = deque(maxlen=1000)
        self.active_alerts = []
        self.resolved_alerts = deque(maxlen=100)
        
        # Performance tracking
        self.response_times = defaultdict(lambda: deque(maxlen=100))
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Health thresholds
        self.thresholds = {
            "core_functionality_success_rate": 99.0,
            "emotional_enhancement_success_rate": 95.0,
            "average_response_time_ms": 500.0,
            "p95_response_time_ms": 1000.0,
            "error_rate_percentage": 1.0,
            "circuit_breaker_failure_rate": 0.1,
            "feature_flag_rollout_health": 95.0
        }

    async def collect_health_metrics(self) -> List[HealthMetric]:
        """Collect current health metrics"""
        metrics = []
        now = datetime.now()
        
        try:
            # Core functionality success rate
            core_success_rate = await self._measure_core_success_rate()
            metrics.append(HealthMetric(
                name="core_functionality_success_rate",
                value=core_success_rate,
                threshold=self.thresholds["core_functionality_success_rate"],
                status=self._get_status(core_success_rate, self.thresholds["core_functionality_success_rate"]),
                timestamp=now,
                details={"measurement_window": "last_hour"}
            ))
            
            # Emotional enhancement success rate
            emotional_success_rate = await self._measure_emotional_success_rate()
            metrics.append(HealthMetric(
                name="emotional_enhancement_success_rate",
                value=emotional_success_rate,
                threshold=self.thresholds["emotional_enhancement_success_rate"],
                status=self._get_status(emotional_success_rate, self.thresholds["emotional_enhancement_success_rate"]),
                timestamp=now
            ))
            
            # Response time metrics
            avg_response_time = self._calculate_average_response_time()
            metrics.append(HealthMetric(
                name="average_response_time_ms",
                value=avg_response_time,
                threshold=self.thresholds["average_response_time_ms"],
                status=self._get_status(avg_response_time, self.thresholds["average_response_time_ms"], inverse=True),
                timestamp=now
            ))
            
            # P95 response time
            p95_response_time = self._calculate_p95_response_time()
            metrics.append(HealthMetric(
                name="p95_response_time_ms",
                value=p95_response_time,
                threshold=self.thresholds["p95_response_time_ms"],
                status=self._get_status(p95_response_time, self.thresholds["p95_response_time_ms"], inverse=True),
                timestamp=now
            ))
            
            # Error rate
            error_rate = await self._calculate_error_rate()
            metrics.append(HealthMetric(
                name="error_rate_percentage",
                value=error_rate,
                threshold=self.thresholds["error_rate_percentage"],
                status=self._get_status(error_rate, self.thresholds["error_rate_percentage"], inverse=True),
                timestamp=now
            ))
            
            # Circuit breaker health
            circuit_breaker_health = await self._measure_circuit_breaker_health()
            metrics.append(HealthMetric(
                name="circuit_breaker_health",
                value=circuit_breaker_health,
                threshold=90.0,
                status=self._get_status(circuit_breaker_health, 90.0),
                timestamp=now
            ))
            
            # Feature flag health
            feature_flag_health = await self._measure_feature_flag_health()
            metrics.append(HealthMetric(
                name="feature_flag_health",
                value=feature_flag_health,
                threshold=self.thresholds["feature_flag_rollout_health"],
                status=self._get_status(feature_flag_health, self.thresholds["feature_flag_rollout_health"]),
                timestamp=now
            ))
            
            # Store metrics
            self.health_metrics.extend(metrics)
            
            # Check for alerts
            await self._check_health_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            return []

    async def collect_performance_metrics(self) -> List[PerformanceMetric]:
        """Collect performance metrics for all operations"""
        metrics = []
        now = datetime.now()
        
        try:
            operations = [
                "emotional_reaction_analysis",
                "narrative_adaptation",
                "archetype_determination",
                "emotional_context_analysis",
                "personalization_engine"
            ]
            
            for operation in operations:
                if operation in self.response_times and self.response_times[operation]:
                    times = list(self.response_times[operation])
                    
                    metric = PerformanceMetric(
                        operation=operation,
                        avg_response_time=sum(times) / len(times),
                        p95_response_time=self._calculate_percentile(times, 95),
                        p99_response_time=self._calculate_percentile(times, 99),
                        success_rate=self._calculate_success_rate(operation),
                        total_requests=self.operation_counts[operation],
                        timestamp=now
                    )
                    
                    metrics.append(metric)
            
            self.performance_metrics.extend(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return []

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            health_metrics = await self.collect_health_metrics()
            performance_metrics = await self.collect_performance_metrics()
            
            # Get circuit breaker stats
            circuit_breaker = get_emotional_circuit_breaker()
            circuit_stats = circuit_breaker.get_stats()
            
            # Get feature flag status
            feature_flags = await self._get_feature_flag_status()
            
            # Get recent alerts
            recent_alerts = [alert for alert in self.active_alerts[-10:]]
            
            # Get user adoption metrics
            adoption_metrics = await self._get_adoption_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_health": self._calculate_overall_health(health_metrics),
                "health_metrics": [asdict(metric) for metric in health_metrics],
                "performance_metrics": [asdict(metric) for metric in performance_metrics],
                "circuit_breaker": circuit_stats,
                "feature_flags": feature_flags,
                "active_alerts": [asdict(alert) for alert in recent_alerts],
                "adoption_metrics": adoption_metrics,
                "system_info": await self._get_system_info()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def record_operation_time(self, operation: str, duration_ms: float, success: bool = True):
        """Record operation timing"""
        self.response_times[operation].append(duration_ms)
        self.operation_counts[operation] += 1
        
        if not success:
            self.error_counts[operation] += 1

    async def check_integration_health(self) -> Dict[str, Any]:
        """Check overall integration health and return status"""
        health_metrics = await self.collect_health_metrics()
        
        critical_issues = [m for m in health_metrics if m.status == "critical"]
        warning_issues = [m for m in health_metrics if m.status == "warning"]
        
        overall_status = "healthy"
        if critical_issues:
            overall_status = "critical"
        elif warning_issues:
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "healthy_metrics": len([m for m in health_metrics if m.status == "healthy"]),
            "total_metrics": len(health_metrics),
            "details": {
                "critical": [{"name": m.name, "value": m.value, "threshold": m.threshold} for m in critical_issues],
                "warnings": [{"name": m.name, "value": m.value, "threshold": m.threshold} for m in warning_issues]
            }
        }

    async def emergency_health_check(self) -> bool:
        """Quick emergency health check - returns True if system is healthy enough to continue"""
        try:
            # Quick checks for critical functionality
            core_success_rate = await self._measure_core_success_rate()
            if core_success_rate < 95.0:  # Critical threshold
                return False
            
            # Check circuit breaker status
            circuit_breaker = get_emotional_circuit_breaker()
            if not circuit_breaker.is_healthy():
                logger.warning("Circuit breaker is not healthy, but core functionality should continue")
            
            # Check error rate
            error_rate = await self._calculate_error_rate()
            if error_rate > 5.0:  # Critical error rate
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Emergency health check failed: {e}")
            return False

    # Private methods
    async def _measure_core_success_rate(self) -> float:
        """Measure core functionality success rate"""
        try:
            # This would measure actual success rate of core operations
            # For now, simulate based on recent operations
            total_operations = sum(self.operation_counts.values())
            total_errors = sum(self.error_counts.values())
            
            if total_operations == 0:
                return 100.0
            
            return ((total_operations - total_errors) / total_operations) * 100.0
            
        except Exception:
            return 100.0  # Assume healthy if we can't measure

    async def _measure_emotional_success_rate(self) -> float:
        """Measure emotional enhancement success rate"""
        try:
            # Measure success rate of emotional enhancements
            emotional_operations = ["emotional_reaction_analysis", "narrative_adaptation", "archetype_determination"]
            
            total_emotional = sum(self.operation_counts.get(op, 0) for op in emotional_operations)
            total_emotional_errors = sum(self.error_counts.get(op, 0) for op in emotional_operations)
            
            if total_emotional == 0:
                return 100.0
            
            return ((total_emotional - total_emotional_errors) / total_emotional) * 100.0
            
        except Exception:
            return 100.0

    def _calculate_average_response_time(self) -> float:
        """Calculate average response time across all operations"""
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)
        
        if not all_times:
            return 0.0
        
        return sum(all_times) / len(all_times)

    def _calculate_p95_response_time(self) -> float:
        """Calculate 95th percentile response time"""
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)
        
        return self._calculate_percentile(all_times, 95)

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100.0)
        f = int(k)
        c = k - f
        
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c

    async def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        total_operations = sum(self.operation_counts.values())
        total_errors = sum(self.error_counts.values())
        
        if total_operations == 0:
            return 0.0
        
        return (total_errors / total_operations) * 100.0

    def _calculate_success_rate(self, operation: str) -> float:
        """Calculate success rate for specific operation"""
        total = self.operation_counts.get(operation, 0)
        errors = self.error_counts.get(operation, 0)
        
        if total == 0:
            return 100.0
        
        return ((total - errors) / total) * 100.0

    async def _measure_circuit_breaker_health(self) -> float:
        """Measure circuit breaker health"""
        try:
            circuit_breaker = get_emotional_circuit_breaker()
            stats = circuit_breaker.get_stats()
            
            if stats["state"] == "closed":
                return 100.0
            elif stats["state"] == "half_open":
                return 70.0
            else:  # open
                return 30.0
                
        except Exception:
            return 50.0

    async def _measure_feature_flag_health(self) -> float:
        """Measure feature flag system health"""
        try:
            # Check if feature flag system is responsive
            test_flag = await EmotionalFeatureFlags.is_enabled("test_flag", session=self.session)
            return 100.0  # If we got here, system is working
            
        except Exception:
            return 0.0

    async def _get_feature_flag_status(self) -> Dict[str, Any]:
        """Get current feature flag status"""
        try:
            flags = {
                "emotional_system": await EmotionalFeatureFlags.is_enabled(
                    EmotionalFeatureFlags.EMOTIONAL_SYSTEM_ENABLED, session=self.session
                ),
                "narrative_adaptation": await EmotionalFeatureFlags.is_enabled(
                    EmotionalFeatureFlags.NARRATIVE_ADAPTATION_ENABLED, session=self.session
                ),
                "archetype_system": await EmotionalFeatureFlags.is_enabled(
                    EmotionalFeatureFlags.ARCHETYPE_SYSTEM_ENABLED, session=self.session
                )
            }
            
            return flags
            
        except Exception as e:
            logger.error(f"Error getting feature flag status: {e}")
            return {}

    async def _get_adoption_metrics(self) -> Dict[str, Any]:
        """Get user adoption metrics"""
        try:
            # Get user stats from database
            result = await self.session.execute(select(func.count(User.id)))
            total_users = result.scalar() or 0
            
            # This would calculate actual adoption metrics
            return {
                "total_users": total_users,
                "emotional_feature_users": 0,  # Would calculate actual number
                "adoption_rate": 0.0,
                "engagement_improvement": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting adoption metrics: {e}")
            return {}

    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "integration_version": "1.0.0",
            "monitoring_started": datetime.now().isoformat(),
            "metrics_collected": len(self.health_metrics) + len(self.performance_metrics),
            "active_alerts": len(self.active_alerts)
        }

    def _get_status(self, value: float, threshold: float, inverse: bool = False) -> str:
        """Determine status based on value and threshold"""
        if inverse:
            # For metrics where lower is better (like response time)
            if value <= threshold:
                return "healthy"
            elif value <= threshold * 1.5:
                return "warning"
            else:
                return "critical"
        else:
            # For metrics where higher is better (like success rate)
            if value >= threshold:
                return "healthy"
            elif value >= threshold * 0.9:
                return "warning"
            else:
                return "critical"

    def _calculate_overall_health(self, metrics: List[HealthMetric]) -> str:
        """Calculate overall health status"""
        if not metrics:
            return "unknown"
        
        critical_count = sum(1 for m in metrics if m.status == "critical")
        warning_count = sum(1 for m in metrics if m.status == "warning")
        
        if critical_count > 0:
            return "critical"
        elif warning_count > 0:
            return "warning"
        else:
            return "healthy"

    async def _check_health_alerts(self, metrics: List[HealthMetric]):
        """Check metrics and generate alerts if needed"""
        for metric in metrics:
            if metric.status in ["critical", "warning"]:
                alert_id = f"{metric.name}_{metric.status}_{int(time.time())}"
                
                alert = IntegrationAlert(
                    alert_id=alert_id,
                    severity=metric.status,
                    title=f"{metric.name.replace('_', ' ').title()} Issue",
                    description=f"{metric.name} is {metric.value:.2f}, threshold is {metric.threshold}",
                    timestamp=metric.timestamp
                )
                
                self.active_alerts.append(alert)
                
                # Log alert
                if metric.status == "critical":
                    logger.error(f"CRITICAL ALERT: {alert.title} - {alert.description}")
                else:
                    logger.warning(f"WARNING ALERT: {alert.title} - {alert.description}")


# Global monitoring instance
_global_monitoring = None


async def get_integration_monitoring(session: AsyncSession) -> IntegrationMonitoring:
    """Get global integration monitoring instance"""
    global _global_monitoring
    
    if _global_monitoring is None:
        _global_monitoring = IntegrationMonitoring(session)
    
    return _global_monitoring