"""
Diana Error Reporting Dashboard

Comprehensive error reporting and analysis dashboard for the Diana menu system.
Provides real-time error monitoring, detailed analytics, and actionable insights.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from services.diana_menu_error_tracker import (
    DianaMenuErrorTracker, ErrorEvent, ErrorCategory, 
    ErrorSeverity, get_error_tracker
)
from services.diana_error_correlation_analyzer import (
    DianaErrorCorrelationAnalyzer, ErrorCorrelation, 
    CorrelationType, ErrorCluster
)

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types of error reports."""
    SUMMARY = "summary"
    DETAILED = "detailed" 
    CORRELATION = "correlation"
    PERFORMANCE = "performance"
    TREND_ANALYSIS = "trend_analysis"
    ROOT_CAUSE = "root_cause"
    ALERT = "alert"

@dataclass
class DashboardMetrics:
    """Key metrics displayed on the dashboard."""
    total_errors: int = 0
    error_rate_per_hour: float = 0.0
    critical_errors: int = 0
    unresolved_errors: int = 0
    performance_violations: int = 0
    affected_users: int = 0
    top_error_category: str = ""
    average_resolution_time: float = 0.0
    system_health_score: float = 100.0
    uptime_percentage: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ErrorTrend:
    """Error trend data over time."""
    time_period: str
    error_count: int
    error_rate: float
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    resolution_rate: float

@dataclass
class PerformanceReport:
    """Performance analysis report."""
    operation: str
    average_duration: float
    max_duration: float
    min_duration: float
    p95_duration: float
    p99_duration: float
    success_rate: float
    error_rate: float
    total_operations: int
    performance_violations: int

class DianaErrorDashboard:
    """
    Comprehensive error reporting dashboard for Diana menu system.
    
    Features:
    - Real-time error monitoring
    - Performance analytics
    - Trend analysis
    - Correlation insights
    - Root cause analysis
    - Alert generation
    """
    
    def __init__(self, error_tracker: Optional[DianaMenuErrorTracker] = None):
        self.error_tracker = error_tracker or get_error_tracker()
        self.correlation_analyzer = DianaErrorCorrelationAnalyzer(self.error_tracker)
        
        # Dashboard state
        self.metrics_cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self.last_cache_update = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            'error_rate_per_hour': 50,
            'critical_errors_per_hour': 5,
            'performance_violations_per_hour': 20,
            'affected_users_per_hour': 100,
            'system_health_score': 80.0
        }
        
        # Historical data storage
        self.trend_history = defaultdict(list)
        self.performance_history = defaultdict(list)
        
        logger.info("Diana Error Dashboard initialized")
    
    async def get_dashboard_metrics(self, hours: int = 24) -> DashboardMetrics:
        """Get current dashboard metrics."""
        cache_key = f"metrics_{hours}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.metrics_cache[cache_key]
        
        # Calculate metrics
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_tracker.errors if e.timestamp >= cutoff]
        
        metrics = DashboardMetrics()
        
        # Basic counts
        metrics.total_errors = len(recent_errors)
        metrics.error_rate_per_hour = metrics.total_errors / max(hours, 1)
        metrics.critical_errors = sum(1 for e in recent_errors if e.severity == ErrorSeverity.CRITICAL)
        metrics.unresolved_errors = sum(1 for e in recent_errors if not e.resolved)
        
        # Performance metrics
        performance_violations = 0
        for error in recent_errors:
            if error.performance.duration and error.performance.duration > 1.0:
                performance_violations += 1
        metrics.performance_violations = performance_violations
        
        # User impact
        affected_users = {e.context.user_id for e in recent_errors if e.context.user_id}
        metrics.affected_users = len(affected_users)
        
        # Top error category
        if recent_errors:
            category_counts = Counter([e.category for e in recent_errors])
            metrics.top_error_category = category_counts.most_common(1)[0][0].value
        
        # Resolution metrics
        resolved_errors = [e for e in recent_errors if e.resolved]
        if resolved_errors:
            # Calculate average resolution time (placeholder - would need actual resolution timestamps)
            metrics.average_resolution_time = 3600.0  # Default 1 hour
        
        # System health score
        metrics.system_health_score = self._calculate_health_score(recent_errors, hours)
        
        # Uptime (placeholder - would need actual system monitoring)
        metrics.uptime_percentage = max(0, 100 - (metrics.error_rate_per_hour / 10))
        
        # Cache the result
        self.metrics_cache[cache_key] = metrics
        self.last_cache_update[cache_key] = datetime.now()
        
        return metrics
    
    def _calculate_health_score(self, errors: List[ErrorEvent], hours: int) -> float:
        """Calculate system health score based on error patterns."""
        if not errors:
            return 100.0
        
        # Base score
        score = 100.0
        
        # Penalty for error rate
        error_rate = len(errors) / max(hours, 1)
        score -= min(50, error_rate * 2)  # Max 50 point penalty
        
        # Penalty for critical errors
        critical_count = sum(1 for e in errors if e.severity == ErrorSeverity.CRITICAL)
        score -= critical_count * 10  # 10 points per critical error
        
        # Penalty for unresolved errors
        unresolved_count = sum(1 for e in errors if not e.resolved)
        score -= min(30, unresolved_count * 2)  # Max 30 point penalty
        
        # Penalty for performance issues
        perf_violations = sum(1 for e in errors if e.performance.duration and e.performance.duration > 1.0)
        score -= min(20, perf_violations)  # Max 20 point penalty
        
        return max(0.0, score)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.metrics_cache:
            return False
        
        last_update = self.last_cache_update.get(cache_key)
        if not last_update:
            return False
        
        return datetime.now() - last_update < self.cache_ttl
    
    async def get_error_trends(self, hours: int = 24, interval_hours: int = 1) -> List[ErrorTrend]:
        """Get error trends over time."""
        trends = []
        end_time = datetime.now()
        
        for i in range(hours // interval_hours):
            period_end = end_time - timedelta(hours=i * interval_hours)
            period_start = period_end - timedelta(hours=interval_hours)
            
            period_errors = [
                e for e in self.error_tracker.errors
                if period_start <= e.timestamp < period_end
            ]
            
            # Calculate trend metrics
            error_count = len(period_errors)
            error_rate = error_count / interval_hours
            
            severity_breakdown = {}
            for severity in ErrorSeverity:
                severity_breakdown[severity.value] = sum(
                    1 for e in period_errors if e.severity == severity
                )
            
            category_breakdown = {}
            for category in ErrorCategory:
                category_breakdown[category.value] = sum(
                    1 for e in period_errors if e.category == category
                )
            
            resolved_count = sum(1 for e in period_errors if e.resolved)
            resolution_rate = (resolved_count / error_count) * 100 if error_count > 0 else 100.0
            
            trend = ErrorTrend(
                time_period=f"{period_start.strftime('%H:%M')} - {period_end.strftime('%H:%M')}",
                error_count=error_count,
                error_rate=error_rate,
                severity_breakdown=severity_breakdown,
                category_breakdown=category_breakdown,
                resolution_rate=resolution_rate
            )
            
            trends.append(trend)
        
        return list(reversed(trends))  # Chronological order
    
    async def get_performance_report(self, hours: int = 24) -> List[PerformanceReport]:
        """Get performance analysis report."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_tracker.errors if e.timestamp >= cutoff]
        
        # Group by operation
        operation_data = defaultdict(list)
        
        for error in recent_errors:
            operation = error.context.operation or "unknown"
            if error.performance.duration is not None:
                operation_data[operation].append(error)
        
        # Also include successful operations from performance history
        for perf_record in self.error_tracker.performance_history:
            if perf_record['timestamp'] >= cutoff:
                operation = perf_record['operation']
                # Create a mock error event for successful operations
                mock_error = type('MockEvent', (), {
                    'performance': type('MockPerf', (), {
                        'duration': perf_record['duration']
                    })()
                })()
                operation_data[operation].append(mock_error)
        
        reports = []
        
        for operation, events in operation_data.items():
            if not events:
                continue
            
            durations = [e.performance.duration for e in events if hasattr(e.performance, 'duration') and e.performance.duration]
            
            if not durations:
                continue
            
            # Calculate statistics
            durations.sort()
            total_ops = len(durations)
            error_count = sum(1 for e in events if hasattr(e, 'severity'))  # Real errors have severity
            success_count = total_ops - error_count
            
            p95_index = int(0.95 * len(durations))
            p99_index = int(0.99 * len(durations))
            
            performance_violations = sum(1 for d in durations if d > 1.0)
            
            report = PerformanceReport(
                operation=operation,
                average_duration=sum(durations) / len(durations),
                max_duration=max(durations),
                min_duration=min(durations),
                p95_duration=durations[p95_index] if p95_index < len(durations) else durations[-1],
                p99_duration=durations[p99_index] if p99_index < len(durations) else durations[-1],
                success_rate=(success_count / total_ops) * 100,
                error_rate=(error_count / total_ops) * 100,
                total_operations=total_ops,
                performance_violations=performance_violations
            )
            
            reports.append(report)
        
        return sorted(reports, key=lambda r: r.error_rate, reverse=True)
    
    async def get_correlation_insights(self, hours: int = 24) -> Dict[str, Any]:
        """Get error correlation insights."""
        correlations = await self.correlation_analyzer.analyze_correlations(hours)
        clusters = await self.correlation_analyzer.cluster_errors(hours)
        
        insights = {
            'total_correlations': len(correlations),
            'correlation_types': Counter([c.correlation_type.value for c in correlations]),
            'high_confidence_correlations': [
                {
                    'id': c.correlation_id,
                    'type': c.correlation_type.value,
                    'strength': c.strength,
                    'confidence': c.confidence,
                    'description': c.description,
                    'hypothesis': c.root_cause_hypothesis
                }
                for c in correlations if c.confidence >= 0.8
            ],
            'error_clusters': [
                {
                    'id': cluster.cluster_id,
                    'size': cluster.cluster_size,
                    'dominant_category': cluster.dominant_category.value,
                    'affected_users': len(cluster.affected_users),
                    'time_span_minutes': cluster.time_span.total_seconds() / 60
                }
                for cluster in clusters
            ],
            'recommendations': self.correlation_analyzer._generate_recommendations(correlations)
        }
        
        return insights
    
    async def get_root_cause_analysis(self, error_id: str) -> Dict[str, Any]:
        """Perform root cause analysis for a specific error."""
        error = self.error_tracker.get_error_details(error_id)
        if not error:
            return {'error': 'Error not found'}
        
        # Find related errors
        related_errors = []
        
        # Temporal neighbors
        time_window = timedelta(minutes=10)
        for other_error in self.error_tracker.errors:
            if other_error.id == error_id:
                continue
            
            if abs((other_error.timestamp - error.timestamp).total_seconds()) <= time_window.total_seconds():
                if other_error.context.user_id == error.context.user_id or \
                   other_error.context.operation == error.context.operation or \
                   other_error.category == error.category:
                    related_errors.append(other_error)
        
        # Find correlations involving this error
        correlations = [
            corr for corr in self.correlation_analyzer.correlations.values()
            if error_id in ([corr.primary_error] + corr.related_errors)
        ]
        
        # Generate root cause hypothesis
        hypothesis = self._generate_root_cause_hypothesis(error, related_errors)
        
        analysis = {
            'error': {
                'id': error.id,
                'timestamp': error.timestamp.isoformat(),
                'category': error.category.value,
                'severity': error.severity.value,
                'message': error.message,
                'function': error.function_name,
                'user_id': error.context.user_id,
                'operation': error.context.operation
            },
            'related_errors': [
                {
                    'id': e.id,
                    'category': e.category.value,
                    'message': e.message,
                    'time_diff_seconds': (e.timestamp - error.timestamp).total_seconds()
                }
                for e in related_errors
            ],
            'correlations': [
                {
                    'type': c.correlation_type.value,
                    'strength': c.strength,
                    'description': c.description
                }
                for c in correlations
            ],
            'root_cause_hypothesis': hypothesis,
            'suggested_actions': self._generate_suggested_actions(error, related_errors),
            'stack_trace': error.stack_trace
        }
        
        return analysis
    
    def _generate_root_cause_hypothesis(self, error: ErrorEvent, related_errors: List[ErrorEvent]) -> str:
        """Generate a root cause hypothesis for an error."""
        hypotheses = {
            ErrorCategory.BASEMODEL: "Data validation or serialization issue, likely due to incorrect parameter types or missing required fields",
            ErrorCategory.DATABASE: "Database connection, transaction, or query execution problem",
            ErrorCategory.SERVICE: "Service dependency failure or initialization issue",
            ErrorCategory.MENU_NAVIGATION: "User interface or state management problem",
            ErrorCategory.CALLBACK_PROCESSING: "Asynchronous callback handling or data processing issue",
            ErrorCategory.CHARACTER_VALIDATION: "Diana character consistency validation failure",
            ErrorCategory.TELEGRAM_API: "External API communication failure or rate limiting",
            ErrorCategory.DEPENDENCY_INJECTION: "Service container or dependency resolution problem",
            ErrorCategory.PERFORMANCE: "Resource exhaustion or timeout issue"
        }
        
        base_hypothesis = hypotheses.get(error.category, "Unknown system error")
        
        # Enhance with context
        if related_errors:
            categories = Counter([e.category for e in related_errors])
            if len(categories) == 1 and error.category in categories:
                base_hypothesis += f" - Pattern suggests systematic issue affecting multiple operations"
            elif len(categories) > 1:
                base_hypothesis += f" - Multiple error types suggest cascading failure or system overload"
        
        if error.context.user_id:
            user_errors = [e for e in self.error_tracker.errors[-100:] if e.context.user_id == error.context.user_id]
            if len(user_errors) > 5:
                base_hypothesis += f" - User has history of {len(user_errors)} recent errors, suggesting account-specific issue"
        
        return base_hypothesis
    
    def _generate_suggested_actions(self, error: ErrorEvent, related_errors: List[ErrorEvent]) -> List[str]:
        """Generate suggested actions for resolving an error."""
        actions = []
        
        # Category-specific actions
        action_map = {
            ErrorCategory.BASEMODEL: [
                "Validate input data types and formats",
                "Check BaseModel field definitions and default values",
                "Review serialization/deserialization logic"
            ],
            ErrorCategory.DATABASE: [
                "Check database connection pool settings",
                "Review transaction isolation levels",
                "Verify database schema and constraints",
                "Check for connection leaks"
            ],
            ErrorCategory.SERVICE: [
                "Verify service dependencies are available",
                "Check service initialization order",
                "Review service configuration and environment variables"
            ],
            ErrorCategory.TELEGRAM_API: [
                "Check API rate limiting and implement backoff",
                "Verify bot token and permissions",
                "Implement retry logic with exponential backoff"
            ]
        }
        
        category_actions = action_map.get(error.category, [])
        actions.extend(category_actions)
        
        # Context-specific actions
        if error.severity == ErrorSeverity.CRITICAL:
            actions.append("CRITICAL: Immediate attention required - may affect system stability")
        
        if len(related_errors) > 5:
            actions.append("High error frequency detected - consider implementing circuit breaker pattern")
        
        if error.performance.duration and error.performance.duration > 2.0:
            actions.append("Performance issue detected - optimize slow operations and add caching")
        
        return actions
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions and return active alerts."""
        alerts = []
        metrics = await self.get_dashboard_metrics(1)  # Last hour
        
        # Error rate alert
        if metrics.error_rate_per_hour > self.alert_thresholds['error_rate_per_hour']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'HIGH',
                'message': f"High error rate: {metrics.error_rate_per_hour:.1f} errors/hour (threshold: {self.alert_thresholds['error_rate_per_hour']})",
                'value': metrics.error_rate_per_hour,
                'threshold': self.alert_thresholds['error_rate_per_hour']
            })
        
        # Critical errors alert
        if metrics.critical_errors > self.alert_thresholds['critical_errors_per_hour']:
            alerts.append({
                'type': 'critical_errors',
                'severity': 'CRITICAL',
                'message': f"Critical errors detected: {metrics.critical_errors} in last hour",
                'value': metrics.critical_errors,
                'threshold': self.alert_thresholds['critical_errors_per_hour']
            })
        
        # Performance violations alert
        if metrics.performance_violations > self.alert_thresholds['performance_violations_per_hour']:
            alerts.append({
                'type': 'performance_issues',
                'severity': 'MEDIUM',
                'message': f"High performance violations: {metrics.performance_violations} in last hour",
                'value': metrics.performance_violations,
                'threshold': self.alert_thresholds['performance_violations_per_hour']
            })
        
        # System health alert
        if metrics.system_health_score < self.alert_thresholds['system_health_score']:
            alerts.append({
                'type': 'low_health_score',
                'severity': 'HIGH',
                'message': f"Low system health score: {metrics.system_health_score:.1f}% (threshold: {self.alert_thresholds['system_health_score']}%)",
                'value': metrics.system_health_score,
                'threshold': self.alert_thresholds['system_health_score']
            })
        
        return alerts
    
    def generate_report(self, report_type: ReportType, hours: int = 24) -> str:
        """Generate formatted report of specified type."""
        if report_type == ReportType.SUMMARY:
            return asyncio.run(self._generate_summary_report(hours))
        elif report_type == ReportType.DETAILED:
            return asyncio.run(self._generate_detailed_report(hours))
        elif report_type == ReportType.PERFORMANCE:
            return asyncio.run(self._generate_performance_report(hours))
        else:
            return f"Report type {report_type.value} not implemented yet"
    
    async def _generate_summary_report(self, hours: int) -> str:
        """Generate summary report."""
        metrics = await self.get_dashboard_metrics(hours)
        alerts = await self.check_alerts()
        
        report = f"""
# Diana Menu System - Error Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {hours} hours

## Key Metrics
- Total Errors: {metrics.total_errors}
- Error Rate: {metrics.error_rate_per_hour:.1f} errors/hour
- Critical Errors: {metrics.critical_errors}
- Unresolved Errors: {metrics.unresolved_errors}
- Performance Violations: {metrics.performance_violations}
- Affected Users: {metrics.affected_users}
- System Health Score: {metrics.system_health_score:.1f}%

## Top Error Category
{metrics.top_error_category}

## Active Alerts
{len(alerts)} alerts active
""" + "\n".join([f"- {alert['severity']}: {alert['message']}" for alert in alerts])
        
        return report.strip()
    
    async def _generate_detailed_report(self, hours: int) -> str:
        """Generate detailed error report."""
        metrics = await self.get_dashboard_metrics(hours)
        trends = await self.get_error_trends(hours, 4)  # 4-hour intervals
        correlations = await self.get_correlation_insights(hours)
        
        report = f"""
# Diana Menu System - Detailed Error Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {hours} hours

## Overview
- Total Errors: {metrics.total_errors}
- Error Rate: {metrics.error_rate_per_hour:.1f} errors/hour
- System Health: {metrics.system_health_score:.1f}%

## Error Trends
"""
        for trend in trends:
            report += f"""
### {trend.time_period}
- Count: {trend.error_count}
- Rate: {trend.error_rate:.1f}/hour
- Resolution Rate: {trend.resolution_rate:.1f}%
"""
        
        report += f"""
## Correlations
- Total: {correlations['total_correlations']}
- High Confidence: {len(correlations['high_confidence_correlations'])}
- Clusters: {len(correlations['error_clusters'])}

## Recommendations
""" + "\n".join([f"- {rec}" for rec in correlations['recommendations']])
        
        return report.strip()
    
    async def _generate_performance_report(self, hours: int) -> str:
        """Generate performance report."""
        performance_reports = await self.get_performance_report(hours)
        
        report = f"""
# Diana Menu System - Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {hours} hours

## Operation Performance
"""
        
        for perf in performance_reports[:10]:  # Top 10
            report += f"""
### {perf.operation}
- Average Duration: {perf.average_duration:.3f}s
- P95 Duration: {perf.p95_duration:.3f}s
- Success Rate: {perf.success_rate:.1f}%
- Performance Violations: {perf.performance_violations}
- Total Operations: {perf.total_operations}
"""
        
        return report.strip()

# Global dashboard instance
_global_dashboard = None

def get_error_dashboard() -> DianaErrorDashboard:
    """Get the global Diana error dashboard instance."""
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = DianaErrorDashboard()
    return _global_dashboard