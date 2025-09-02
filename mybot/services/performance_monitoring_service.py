"""Performance monitoring service for production optimization.

This service tracks:
- Response time monitoring (<2s requirement)
- Error rate tracking (<0.1% target)
- Diana character consistency alerts
- Database performance metrics
- Cache performance monitoring
- Multi-tenant performance isolation

Key Features:
- Real-time performance alerts
- Character consistency degradation detection
- Automated performance optimization triggers
- Production health dashboards
"""
import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    metric_type: str
    value: float
    user_id: Optional[int] = None
    handler_name: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    metric_type: str
    warning_threshold: float
    critical_threshold: float
    evaluation_window_minutes: int
    min_samples: int


class PerformanceMonitoringService:
    """Service for comprehensive performance monitoring and alerting."""
    
    def __init__(self):
        # Metric storage (in production, would use dedicated time-series DB)
        self.metrics_buffer = deque(maxlen=10000)  # Store last 10k metrics
        self.metrics_by_type = defaultdict(lambda: deque(maxlen=1000))
        self.user_metrics = defaultdict(lambda: deque(maxlen=100))
        
        # Alert configuration
        self.alert_thresholds = {
            'response_time': AlertThreshold(
                metric_type='response_time',
                warning_threshold=1.5,  # 1.5 seconds warning
                critical_threshold=2.0,  # 2.0 seconds critical
                evaluation_window_minutes=5,
                min_samples=10
            ),
            'error_rate': AlertThreshold(
                metric_type='error_rate',
                warning_threshold=0.05,  # 0.05% warning
                critical_threshold=0.1,  # 0.1% critical
                evaluation_window_minutes=10,
                min_samples=50
            ),
            'character_consistency': AlertThreshold(
                metric_type='character_consistency',
                warning_threshold=92.0,  # 92% warning
                critical_threshold=90.0,  # 90% critical
                evaluation_window_minutes=15,
                min_samples=5
            ),
            'database_query_time': AlertThreshold(
                metric_type='database_query_time',
                warning_threshold=0.8,  # 800ms warning
                critical_threshold=1.2,  # 1.2s critical
                evaluation_window_minutes=5,
                min_samples=20
            ),
            'cache_hit_rate': AlertThreshold(
                metric_type='cache_hit_rate',
                warning_threshold=70.0,  # 70% hit rate warning
                critical_threshold=50.0,  # 50% hit rate critical
                evaluation_window_minutes=10,
                min_samples=100
            )
        }
        
        # Alert callbacks
        self.alert_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Performance statistics
        self.stats = {
            'total_requests': 0,
            'total_errors': 0,
            'avg_response_time': 0.0,
            'p95_response_time': 0.0,
            'p99_response_time': 0.0,
            'character_consistency_avg': 0.0,
            'database_query_avg': 0.0,
            'cache_hit_rate_avg': 0.0,
            'alerts_triggered': 0,
            'last_alert_time': None
        }
        
        # Monitoring state
        self.monitoring_active = True
        self.background_tasks = set()
    
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        logger.info("🚀 Starting performance monitoring service")
        
        # Start alert evaluation task
        task = asyncio.create_task(self._alert_evaluation_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Start metrics cleanup task
        cleanup_task = asyncio.create_task(self._metrics_cleanup_loop())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("✅ Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        logger.info("🛑 Stopping performance monitoring service")
        
        self.monitoring_active = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("✅ Performance monitoring stopped")
    
    @asynccontextmanager
    async def monitor_request(
        self,
        handler_name: str,
        user_id: Optional[int] = None
    ):
        """Context manager for monitoring request performance.
        
        Args:
            handler_name: Name of the handler being monitored
            user_id: User identifier for per-user metrics
        """
        start_time = time.time()
        error_occurred = False
        
        try:
            yield
            
        except Exception as e:
            error_occurred = True
            await self.record_error(handler_name, str(e), user_id)
            raise
            
        finally:
            response_time = time.time() - start_time
            
            # Record response time metric
            await self.record_metric(
                'response_time',
                response_time,
                user_id=user_id,
                handler_name=handler_name
            )
            
            # Update request statistics
            self.stats['total_requests'] += 1
            if error_occurred:
                self.stats['total_errors'] += 1
    
    async def record_metric(
        self,
        metric_type: str,
        value: float,
        user_id: Optional[int] = None,
        handler_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric.
        
        Args:
            metric_type: Type of metric (response_time, error_rate, etc.)
            value: Metric value
            user_id: User identifier
            handler_name: Handler name
            metadata: Additional metadata
        """
        if not self.monitoring_active:
            return
        
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            handler_name=handler_name,
            metadata=metadata or {}
        )
        
        # Store metric
        self.metrics_buffer.append(metric)
        self.metrics_by_type[metric_type].append(metric)
        
        if user_id:
            self.user_metrics[user_id].append(metric)
        
        # Update running statistics
        await self._update_statistics(metric)
        
        logger.debug(f"📊 Recorded {metric_type} metric: {value}")
    
    async def record_character_consistency(
        self,
        consistency_score: float,
        user_id: Optional[int] = None,
        fragment_id: Optional[str] = None,
        validation_details: Optional[Dict[str, Any]] = None
    ):
        """Record Diana character consistency metric.
        
        Args:
            consistency_score: Character consistency score (0-100)
            user_id: User identifier
            fragment_id: Narrative fragment ID
            validation_details: Detailed validation results
        """
        metadata = {
            'fragment_id': fragment_id,
            'validation_details': validation_details or {}
        }
        
        await self.record_metric(
            'character_consistency',
            consistency_score,
            user_id=user_id,
            metadata=metadata
        )
        
        # Alert if consistency drops below threshold
        if consistency_score < 95.0:
            await self._trigger_character_consistency_alert(
                consistency_score, user_id, fragment_id
            )
    
    async def record_database_query(
        self,
        query_name: str,
        query_time: float,
        user_id: Optional[int] = None,
        row_count: Optional[int] = None
    ):
        """Record database query performance metric.
        
        Args:
            query_name: Name of the query
            query_time: Query execution time in seconds
            user_id: User identifier
            row_count: Number of rows returned
        """
        metadata = {
            'query_name': query_name,
            'row_count': row_count
        }
        
        await self.record_metric(
            'database_query_time',
            query_time,
            user_id=user_id,
            metadata=metadata
        )
    
    async def record_cache_performance(
        self,
        operation_type: str,
        hit_rate: float,
        operation_time: Optional[float] = None
    ):
        """Record cache performance metrics.
        
        Args:
            operation_type: Cache operation type (get, set, delete)
            hit_rate: Cache hit rate percentage
            operation_time: Cache operation time in seconds
        """
        metadata = {
            'operation_type': operation_type,
            'operation_time': operation_time
        }
        
        await self.record_metric(
            'cache_hit_rate',
            hit_rate,
            metadata=metadata
        )
    
    async def record_error(
        self,
        handler_name: str,
        error_message: str,
        user_id: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """Record an error occurrence.
        
        Args:
            handler_name: Handler where error occurred
            error_message: Error message
            user_id: User identifier
            error_type: Type of error
        """
        metadata = {
            'handler_name': handler_name,
            'error_message': error_message,
            'error_type': error_type
        }
        
        await self.record_metric(
            'error',
            1.0,  # Error count
            user_id=user_id,
            handler_name=handler_name,
            metadata=metadata
        )
        
        logger.error(f"❌ Error recorded: {handler_name} - {error_message}")
    
    async def get_performance_summary(
        self,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance summary for specified time window.
        
        Args:
            time_window_minutes: Time window in minutes
            
        Returns:
            Performance summary
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.metrics_buffer
            if m.timestamp >= cutoff_time
        ]
        
        # Calculate summary statistics
        response_times = [
            m.value for m in recent_metrics
            if m.metric_type == 'response_time'
        ]
        
        consistency_scores = [
            m.value for m in recent_metrics
            if m.metric_type == 'character_consistency'
        ]
        
        query_times = [
            m.value for m in recent_metrics
            if m.metric_type == 'database_query_time'
        ]
        
        cache_hit_rates = [
            m.value for m in recent_metrics
            if m.metric_type == 'cache_hit_rate'
        ]
        
        errors = [
            m for m in recent_metrics
            if m.metric_type == 'error'
        ]
        
        # Calculate statistics
        summary = {
            'time_window_minutes': time_window_minutes,
            'total_requests': len(response_times),
            'total_errors': len(errors),
            'error_rate_percentage': round(
                (len(errors) / max(1, len(response_times))) * 100, 3
            ),
            'response_time_stats': {
                'avg': round(sum(response_times) / max(1, len(response_times)), 3),
                'p95': self._calculate_percentile(response_times, 95),
                'p99': self._calculate_percentile(response_times, 99),
                'max': max(response_times) if response_times else 0,
                'count': len(response_times)
            },
            'character_consistency_stats': {
                'avg': round(sum(consistency_scores) / max(1, len(consistency_scores)), 1),
                'min': min(consistency_scores) if consistency_scores else 0,
                'count': len(consistency_scores),
                'below_threshold_count': len([s for s in consistency_scores if s < 95.0])
            },
            'database_performance': {
                'avg_query_time': round(sum(query_times) / max(1, len(query_times)), 3),
                'p95_query_time': self._calculate_percentile(query_times, 95),
                'slow_queries_count': len([q for q in query_times if q > 1.0]),
                'total_queries': len(query_times)
            },
            'cache_performance': {
                'avg_hit_rate': round(sum(cache_hit_rates) / max(1, len(cache_hit_rates)), 1),
                'min_hit_rate': min(cache_hit_rates) if cache_hit_rates else 0,
                'samples': len(cache_hit_rates)
            },
            'alerts_triggered': self.stats['alerts_triggered'],
            'last_alert_time': self.stats['last_alert_time']
        }
        
        return summary
    
    async def get_user_performance_profile(
        self,
        user_id: int,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance profile for specific user.
        
        Args:
            user_id: User identifier
            time_window_minutes: Time window in minutes
            
        Returns:
            User-specific performance profile
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        user_recent_metrics = [
            m for m in self.user_metrics[user_id]
            if m.timestamp >= cutoff_time
        ]
        
        # Analyze user-specific metrics
        user_response_times = [
            m.value for m in user_recent_metrics
            if m.metric_type == 'response_time'
        ]
        
        user_consistency = [
            m.value for m in user_recent_metrics
            if m.metric_type == 'character_consistency'
        ]
        
        user_errors = [
            m for m in user_recent_metrics
            if m.metric_type == 'error'
        ]
        
        profile = {
            'user_id': user_id,
            'time_window_minutes': time_window_minutes,
            'total_interactions': len(user_response_times),
            'avg_response_time': round(
                sum(user_response_times) / max(1, len(user_response_times)), 3
            ),
            'character_consistency_avg': round(
                sum(user_consistency) / max(1, len(user_consistency)), 1
            ),
            'error_count': len(user_errors),
            'performance_issues': [],
            'recommendations': []
        }
        
        # Add performance issues and recommendations
        if profile['avg_response_time'] > 2.0:
            profile['performance_issues'].append('slow_response_times')
            profile['recommendations'].append('consider_cache_warming')
        
        if profile['character_consistency_avg'] < 95.0:
            profile['performance_issues'].append('character_consistency_degradation')
            profile['recommendations'].append('validate_narrative_fragments')
        
        if profile['error_count'] > 0:
            profile['performance_issues'].append('user_errors_detected')
            profile['recommendations'].append('review_error_handling')
        
        return profile
    
    async def register_alert_handler(
        self,
        alert_type: str,
        handler: Callable[[str, Dict[str, Any]], None]
    ):
        """Register an alert handler callback.
        
        Args:
            alert_type: Type of alert (warning, critical)
            handler: Callback function for alerts
        """
        self.alert_handlers[alert_type].append(handler)
        logger.info(f"📢 Registered alert handler for {alert_type}")
    
    async def _alert_evaluation_loop(self):
        """Background task for evaluating alert conditions."""
        while self.monitoring_active:
            try:
                await self._evaluate_alerts()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Alert evaluation error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _metrics_cleanup_loop(self):
        """Background task for cleaning up old metrics."""
        while self.monitoring_active:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Metrics cleanup error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _evaluate_alerts(self):
        """Evaluate all alert thresholds and trigger alerts if needed."""
        for threshold in self.alert_thresholds.values():
            await self._evaluate_threshold(threshold)
    
    async def _evaluate_threshold(self, threshold: AlertThreshold):
        """Evaluate a specific alert threshold.
        
        Args:
            threshold: Alert threshold configuration
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=threshold.evaluation_window_minutes)
        
        # Get recent metrics of this type
        recent_metrics = [
            m for m in self.metrics_by_type[threshold.metric_type]
            if m.timestamp >= cutoff_time
        ]
        
        if len(recent_metrics) < threshold.min_samples:
            return  # Not enough samples for evaluation
        
        # Calculate average value
        avg_value = sum(m.value for m in recent_metrics) / len(recent_metrics)
        
        # Check thresholds
        alert_level = None
        if avg_value >= threshold.critical_threshold:
            alert_level = 'critical'
        elif avg_value >= threshold.warning_threshold:
            alert_level = 'warning'
        
        if alert_level:
            await self._trigger_alert(
                alert_level,
                threshold.metric_type,
                avg_value,
                threshold,
                recent_metrics
            )
    
    async def _trigger_alert(
        self,
        alert_level: str,
        metric_type: str,
        current_value: float,
        threshold: AlertThreshold,
        recent_metrics: List[PerformanceMetric]
    ):
        """Trigger an alert.
        
        Args:
            alert_level: Alert severity level
            metric_type: Type of metric that triggered alert
            current_value: Current metric value
            threshold: Alert threshold configuration
            recent_metrics: Recent metrics for context
        """
        alert_data = {
            'alert_level': alert_level,
            'metric_type': metric_type,
            'current_value': current_value,
            'threshold_value': threshold.critical_threshold if alert_level == 'critical' else threshold.warning_threshold,
            'evaluation_window_minutes': threshold.evaluation_window_minutes,
            'sample_count': len(recent_metrics),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log alert
        logger.warning(
            f"🚨 {alert_level.upper()} ALERT: {metric_type} = {current_value:.3f} "
            f"(threshold: {alert_data['threshold_value']:.3f})"
        )
        
        # Update statistics
        self.stats['alerts_triggered'] += 1
        self.stats['last_alert_time'] = datetime.utcnow()
        
        # Call registered alert handlers
        for handler in self.alert_handlers[alert_level]:
            try:
                await asyncio.create_task(handler(alert_level, alert_data))
            except Exception as e:
                logger.error(f"❌ Alert handler error: {e}")
    
    async def _trigger_character_consistency_alert(
        self,
        consistency_score: float,
        user_id: Optional[int],
        fragment_id: Optional[str]
    ):
        """Trigger immediate character consistency alert.
        
        Args:
            consistency_score: Character consistency score
            user_id: User identifier
            fragment_id: Fragment identifier
        """
        alert_data = {
            'alert_level': 'critical' if consistency_score < 90.0 else 'warning',
            'metric_type': 'character_consistency',
            'current_value': consistency_score,
            'user_id': user_id,
            'fragment_id': fragment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'immediate_action_required': True
        }
        
        logger.error(
            f"🎭 CHARACTER CONSISTENCY ALERT: Score {consistency_score}% for user {user_id}, fragment {fragment_id}"
        )
        
        # Call alert handlers
        for handler in self.alert_handlers['critical']:
            try:
                await asyncio.create_task(handler('character_consistency_critical', alert_data))
            except Exception as e:
                logger.error(f"❌ Character consistency alert handler error: {e}")
    
    async def _update_statistics(self, metric: PerformanceMetric):
        """Update running statistics with new metric.
        
        Args:
            metric: New performance metric
        """
        # This would be more sophisticated in production
        # For now, just update basic stats
        if metric.metric_type == 'response_time':
            current_avg = self.stats['avg_response_time']
            total_requests = self.stats['total_requests'] + 1
            self.stats['avg_response_time'] = (
                (current_avg * (total_requests - 1) + metric.value) / total_requests
            )
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * (len(sorted_values) - 1))
        return round(sorted_values[index], 3)
    
    async def _cleanup_old_metrics(self, keep_hours: int = 24):
        """Clean up metrics older than specified hours.
        
        Args:
            keep_hours: Hours of metrics to keep
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=keep_hours)
        
        # Clean main buffer
        original_count = len(self.metrics_buffer)
        self.metrics_buffer = deque(
            (m for m in self.metrics_buffer if m.timestamp >= cutoff_time),
            maxlen=self.metrics_buffer.maxlen
        )
        
        # Clean type-specific buffers
        for metric_type in self.metrics_by_type:
            self.metrics_by_type[metric_type] = deque(
                (m for m in self.metrics_by_type[metric_type] if m.timestamp >= cutoff_time),
                maxlen=self.metrics_by_type[metric_type].maxlen
            )
        
        # Clean user-specific buffers
        for user_id in list(self.user_metrics.keys()):
            self.user_metrics[user_id] = deque(
                (m for m in self.user_metrics[user_id] if m.timestamp >= cutoff_time),
                maxlen=self.user_metrics[user_id].maxlen
            )
            
            # Remove empty user buffers
            if not self.user_metrics[user_id]:
                del self.user_metrics[user_id]
        
        cleaned_count = original_count - len(self.metrics_buffer)
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned {cleaned_count} old performance metrics")


# Global performance monitoring service instance
performance_monitoring_service = PerformanceMonitoringService()