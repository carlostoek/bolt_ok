# services/archetype_monitoring_service.py
"""
Archetype Classification Monitoring and Alerting Service

Monitors archetype system health, performance metrics, and classification success rates.
Provides real-time monitoring, alerting for unusual patterns, and performance tracking
for the Sistema Narrativo Ramificado Diana.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from enum import Enum

try:
    from .archetype_analyzer import ArchetypeAnalyzer
    from .archetype_integration_service import ArchetypeIntegrationService
    from ..database.emotional_models import ArchetypeClassification
    from ..database.models import User
except ImportError:
    # Fallback imports
    from services.archetype_analyzer import ArchetypeAnalyzer
    from services.archetype_integration_service import ArchetypeIntegrationService
    from database.emotional_models import ArchetypeClassification
    from database.models import User

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringMetric(Enum):
    """Types of monitoring metrics."""
    CLASSIFICATION_SUCCESS_RATE = "classification_success_rate"
    CONFIDENCE_DISTRIBUTION = "confidence_distribution"
    RAMIFICADO_ACTIVATION_RATE = "ramificado_activation_rate"
    SYSTEM_PERFORMANCE = "system_performance"
    ERROR_PATTERNS = "error_patterns"
    USER_ENGAGEMENT = "user_engagement"


@dataclass
class PerformanceMetrics:
    """Performance metrics structure."""
    timestamp: datetime
    total_classifications: int
    successful_classifications: int
    failed_classifications: int
    average_confidence: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    ramificado_activations: int
    fallback_usage_count: int
    error_count: int
    average_analysis_time: Optional[float] = None
    memory_usage_mb: Optional[float] = None


@dataclass
class Alert:
    """Alert structure for monitoring system."""
    id: str
    timestamp: datetime
    level: AlertLevel
    metric: MonitoringMetric
    title: str
    description: str
    current_value: Any
    threshold_value: Any
    affected_users: Optional[int] = None
    recommended_actions: List[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MonitoringThresholds:
    """Monitoring thresholds configuration."""
    # Success rate thresholds
    min_success_rate: float = 0.95
    critical_success_rate: float = 0.85

    # Confidence distribution thresholds
    min_high_confidence_rate: float = 0.40
    max_fallback_rate: float = 0.30

    # Performance thresholds
    max_analysis_time_seconds: float = 2.0
    max_error_rate: float = 0.05

    # Ramificado activation thresholds
    min_ramificado_activation_rate: float = 0.30
    max_ramificado_activation_rate: float = 0.80

    # Volume thresholds
    min_daily_classifications: int = 1
    max_daily_classifications: int = 10000


class ArchetypeMonitoringService:
    """
    Comprehensive monitoring service for archetype classification system.

    Tracks system health, performance metrics, classification success rates,
    and provides intelligent alerting for unusual patterns or failures.
    """

    def __init__(self, session: AsyncSession, thresholds: Optional[MonitoringThresholds] = None):
        """
        Initialize monitoring service.

        Args:
            session: Database session
            thresholds: Custom monitoring thresholds (optional)
        """
        self.session = session
        self.thresholds = thresholds or MonitoringThresholds()
        self.archetype_analyzer = ArchetypeAnalyzer(session)
        self.integration_service = ArchetypeIntegrationService(session)

        # Alert tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Performance tracking
        self.metrics_history: List[PerformanceMetrics] = []

    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics for the archetype system.

        Returns:
            PerformanceMetrics with current system state
        """
        try:
            logger.info("Collecting archetype system performance metrics")

            # Basic classification counts
            total_classifications = await self.session.scalar(
                select(func.count(ArchetypeClassification.user_id))
            )

            # Recent activity (last 24 hours)
            recent_threshold = datetime.utcnow() - timedelta(days=1)

            recent_classifications = await self.session.scalar(
                select(func.count(ArchetypeClassification.user_id)).where(
                    ArchetypeClassification.updated_at >= recent_threshold
                )
            )

            # Confidence distribution
            confidence_stats = await self.session.execute(
                select(
                    func.avg(ArchetypeClassification.archetype_confidence).label('avg_confidence'),
                    func.count(func.case((ArchetypeClassification.archetype_confidence >= 0.8, 1))).label('high_conf'),
                    func.count(func.case((and_(
                        ArchetypeClassification.archetype_confidence >= 0.7,
                        ArchetypeClassification.archetype_confidence < 0.8
                    ), 1))).label('medium_conf'),
                    func.count(func.case((ArchetypeClassification.archetype_confidence < 0.7, 1))).label('low_conf')
                )
            )

            conf_result = confidence_stats.first()

            # Ramificado activations
            ramificado_activations = await self.session.scalar(
                select(func.count(ArchetypeClassification.user_id)).where(
                    ArchetypeClassification.ramificado_enabled == True
                )
            )

            # Error estimation (based on extremely low confidence or missing data)
            error_count = await self.session.scalar(
                select(func.count(ArchetypeClassification.user_id)).where(
                    or_(
                        ArchetypeClassification.archetype_confidence < 0.1,
                        ArchetypeClassification.primary_archetype.is_(None)
                    )
                )
            )

            # Build metrics object
            metrics = PerformanceMetrics(
                timestamp=datetime.utcnow(),
                total_classifications=total_classifications or 0,
                successful_classifications=max(0, (total_classifications or 0) - (error_count or 0)),
                failed_classifications=error_count or 0,
                average_confidence=conf_result.avg_confidence if conf_result and conf_result.avg_confidence else 0.0,
                high_confidence_count=conf_result.high_conf if conf_result else 0,
                medium_confidence_count=conf_result.medium_conf if conf_result else 0,
                low_confidence_count=conf_result.low_conf if conf_result else 0,
                ramificado_activations=ramificado_activations or 0,
                fallback_usage_count=max(0, (total_classifications or 0) - (ramificado_activations or 0)),
                error_count=error_count or 0
            )

            # Store metrics for trend analysis
            self.metrics_history.append(metrics)

            # Keep only recent metrics (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history
                if m.timestamp >= cutoff_time
            ]

            logger.info(f"Collected metrics: {metrics.successful_classifications}/{metrics.total_classifications} successful, "
                       f"avg confidence: {metrics.average_confidence:.3f}")

            return metrics

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            # Return minimal metrics in case of error
            return PerformanceMetrics(
                timestamp=datetime.utcnow(),
                total_classifications=0,
                successful_classifications=0,
                failed_classifications=1,  # Count this as a failure
                average_confidence=0.0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                ramificado_activations=0,
                fallback_usage_count=0,
                error_count=1
            )

    async def monitor_classification_success_rates(self) -> List[Alert]:
        """
        Monitor classification success rates and generate alerts for anomalies.

        Returns:
            List of generated alerts
        """
        try:
            logger.debug("Monitoring classification success rates")
            alerts = []

            # Get current metrics
            metrics = await self.collect_performance_metrics()

            if metrics.total_classifications == 0:
                # No data to analyze
                return alerts

            # Calculate success rate
            success_rate = metrics.successful_classifications / metrics.total_classifications

            # Check against thresholds
            if success_rate < self.thresholds.critical_success_rate:
                alert = Alert(
                    id=f"success_rate_critical_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.CRITICAL,
                    metric=MonitoringMetric.CLASSIFICATION_SUCCESS_RATE,
                    title="Critical Classification Success Rate",
                    description=f"Classification success rate ({success_rate:.2%}) is below critical threshold",
                    current_value=success_rate,
                    threshold_value=self.thresholds.critical_success_rate,
                    affected_users=metrics.failed_classifications,
                    recommended_actions=[
                        "Check system health immediately",
                        "Review error logs for patterns",
                        "Consider enabling emergency fallback mode",
                        "Investigate database connectivity"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            elif success_rate < self.thresholds.min_success_rate:
                alert = Alert(
                    id=f"success_rate_warning_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.WARNING,
                    metric=MonitoringMetric.CLASSIFICATION_SUCCESS_RATE,
                    title="Low Classification Success Rate",
                    description=f"Classification success rate ({success_rate:.2%}) is below normal threshold",
                    current_value=success_rate,
                    threshold_value=self.thresholds.min_success_rate,
                    affected_users=metrics.failed_classifications,
                    recommended_actions=[
                        "Monitor system performance",
                        "Check for recent configuration changes",
                        "Review L1F1 choice data quality"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            return alerts

        except Exception as e:
            logger.error(f"Error monitoring success rates: {e}")
            return []

    async def monitor_confidence_score_distribution(self) -> List[Alert]:
        """
        Monitor confidence score distribution for unusual patterns.

        Returns:
            List of generated alerts
        """
        try:
            logger.debug("Monitoring confidence score distribution")
            alerts = []

            metrics = await self.collect_performance_metrics()

            if metrics.total_classifications == 0:
                return alerts

            # Calculate confidence distribution rates
            high_confidence_rate = metrics.high_confidence_count / metrics.total_classifications
            fallback_rate = metrics.fallback_usage_count / metrics.total_classifications

            # Check high confidence rate
            if high_confidence_rate < self.thresholds.min_high_confidence_rate:
                alert = Alert(
                    id=f"low_confidence_rate_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.WARNING,
                    metric=MonitoringMetric.CONFIDENCE_DISTRIBUTION,
                    title="Low High-Confidence Classification Rate",
                    description=f"High-confidence rate ({high_confidence_rate:.2%}) is below threshold",
                    current_value=high_confidence_rate,
                    threshold_value=self.thresholds.min_high_confidence_rate,
                    affected_users=metrics.total_classifications - metrics.high_confidence_count,
                    recommended_actions=[
                        "Review archetype weight calibration",
                        "Check L1F1 choice design effectiveness",
                        "Consider adjusting confidence calculation",
                        "Analyze user interaction patterns"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            # Check excessive fallback usage
            if fallback_rate > self.thresholds.max_fallback_rate:
                alert = Alert(
                    id=f"high_fallback_rate_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.WARNING,
                    metric=MonitoringMetric.CONFIDENCE_DISTRIBUTION,
                    title="High Fallback System Usage",
                    description=f"Fallback usage rate ({fallback_rate:.2%}) is above threshold",
                    current_value=fallback_rate,
                    threshold_value=self.thresholds.max_fallback_rate,
                    affected_users=metrics.fallback_usage_count,
                    recommended_actions=[
                        "Investigate why users aren't qualifying for ramificado",
                        "Review confidence thresholds",
                        "Check data quality in L1F1 interactions",
                        "Consider enhancing choice validation"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            return alerts

        except Exception as e:
            logger.error(f"Error monitoring confidence distribution: {e}")
            return []

    async def detect_unusual_classification_patterns(self) -> List[Alert]:
        """
        Detect unusual patterns in archetype classifications.

        Returns:
            List of generated alerts for unusual patterns
        """
        try:
            logger.debug("Detecting unusual classification patterns")
            alerts = []

            # Get recent archetype distribution (last 7 days)
            recent_threshold = datetime.utcnow() - timedelta(days=7)

            archetype_distribution = await self.session.execute(
                select(
                    ArchetypeClassification.primary_archetype,
                    func.count(ArchetypeClassification.user_id).label('count')
                ).where(
                    ArchetypeClassification.created_at >= recent_threshold
                ).group_by(ArchetypeClassification.primary_archetype)
            )

            distribution_results = archetype_distribution.all()

            if not distribution_results:
                return alerts

            total_recent = sum(result.count for result in distribution_results)

            # Check for extreme archetype dominance (one archetype > 60% of all classifications)
            for archetype, count in distribution_results:
                percentage = count / total_recent
                if percentage > 0.6:
                    alert = Alert(
                        id=f"archetype_dominance_{archetype}_{int(datetime.utcnow().timestamp())}",
                        timestamp=datetime.utcnow(),
                        level=AlertLevel.WARNING,
                        metric=MonitoringMetric.ERROR_PATTERNS,
                        title=f"Unusual {archetype.capitalize()} Archetype Dominance",
                        description=f"Archetype '{archetype}' represents {percentage:.1%} of recent classifications",
                        current_value=percentage,
                        threshold_value=0.6,
                        affected_users=count,
                        recommended_actions=[
                            "Review choice weight balance",
                            "Check for bias in L1F1 choice design",
                            "Analyze user input patterns",
                            "Consider recalibrating archetype weights"
                        ]
                    )
                    alerts.append(alert)
                    self.active_alerts[alert.id] = alert

            # Check for missing archetypes (no classifications in expected archetypes)
            expected_archetypes = {'intellectual', 'emotional', 'exploratory', 'philosophical'}
            found_archetypes = {result.primary_archetype for result in distribution_results}
            missing_archetypes = expected_archetypes - found_archetypes

            if missing_archetypes and total_recent > 10:  # Only alert if we have meaningful data
                alert = Alert(
                    id=f"missing_archetypes_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.INFO,
                    metric=MonitoringMetric.ERROR_PATTERNS,
                    title="Missing Archetype Classifications",
                    description=f"No recent classifications for archetypes: {', '.join(missing_archetypes)}",
                    current_value=list(missing_archetypes),
                    threshold_value="expected_variety",
                    recommended_actions=[
                        "Check choice variety in L1F1",
                        "Review archetype weight distribution",
                        "Ensure all archetype paths are accessible"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            return alerts

        except Exception as e:
            logger.error(f"Error detecting unusual patterns: {e}")
            return []

    async def monitor_ramificado_activation_health(self) -> List[Alert]:
        """
        Monitor ramificado system activation health and rates.

        Returns:
            List of alerts related to ramificado activation
        """
        try:
            logger.debug("Monitoring ramificado activation health")
            alerts = []

            metrics = await self.collect_performance_metrics()

            if metrics.total_classifications == 0:
                return alerts

            # Calculate ramificado activation rate
            activation_rate = metrics.ramificado_activations / metrics.total_classifications

            # Check for low activation rate
            if activation_rate < self.thresholds.min_ramificado_activation_rate:
                alert = Alert(
                    id=f"low_ramificado_rate_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.WARNING,
                    metric=MonitoringMetric.RAMIFICADO_ACTIVATION_RATE,
                    title="Low Ramificado Activation Rate",
                    description=f"Ramificado activation rate ({activation_rate:.2%}) is below threshold",
                    current_value=activation_rate,
                    threshold_value=self.thresholds.min_ramificado_activation_rate,
                    affected_users=metrics.total_classifications - metrics.ramificado_activations,
                    recommended_actions=[
                        "Review confidence calculation accuracy",
                        "Check ramificado activation criteria",
                        "Analyze choice quality and user engagement",
                        "Consider adjusting activation thresholds"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            # Check for unexpectedly high activation rate
            elif activation_rate > self.thresholds.max_ramificado_activation_rate:
                alert = Alert(
                    id=f"high_ramificado_rate_{int(datetime.utcnow().timestamp())}",
                    timestamp=datetime.utcnow(),
                    level=AlertLevel.INFO,
                    metric=MonitoringMetric.RAMIFICADO_ACTIVATION_RATE,
                    title="High Ramificado Activation Rate",
                    description=f"Ramificado activation rate ({activation_rate:.2%}) is above expected range",
                    current_value=activation_rate,
                    threshold_value=self.thresholds.max_ramificado_activation_rate,
                    affected_users=metrics.ramificado_activations,
                    recommended_actions=[
                        "Verify activation criteria are appropriate",
                        "Monitor system performance under high load",
                        "Ensure quality of ramificado experiences"
                    ]
                )
                alerts.append(alert)
                self.active_alerts[alert.id] = alert

            return alerts

        except Exception as e:
            logger.error(f"Error monitoring ramificado activation: {e}")
            return []

    async def generate_comprehensive_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for the archetype system.

        Returns:
            Dictionary with complete system health analysis
        """
        try:
            logger.info("Generating comprehensive archetype system health report")

            # Collect current metrics
            current_metrics = await self.collect_performance_metrics()

            # Run all monitoring checks
            success_alerts = await self.monitor_classification_success_rates()
            confidence_alerts = await self.monitor_confidence_score_distribution()
            pattern_alerts = await self.detect_unusual_classification_patterns()
            ramificado_alerts = await self.monitor_ramificado_activation_health()

            all_alerts = success_alerts + confidence_alerts + pattern_alerts + ramificado_alerts

            # Calculate overall health score
            health_score = self._calculate_health_score(current_metrics, all_alerts)

            # Get trend analysis
            trend_analysis = self._analyze_trends()

            # Recent activity summary (last 24 hours)
            recent_threshold = datetime.utcnow() - timedelta(days=1)
            recent_activity = await self.session.execute(
                select(
                    func.count(ArchetypeClassification.user_id).label('total'),
                    func.count(func.case((ArchetypeClassification.ramificado_enabled == True, 1))).label('ramificado'),
                    func.avg(ArchetypeClassification.archetype_confidence).label('avg_confidence')
                ).where(ArchetypeClassification.updated_at >= recent_threshold)
            )

            recent_stats = recent_activity.first()

            # Build comprehensive report
            report = {
                'timestamp': datetime.utcnow(),
                'overall_health_score': health_score,
                'system_status': self._get_system_status(health_score),
                'current_metrics': asdict(current_metrics),
                'recent_activity': {
                    'total_classifications_24h': recent_stats.total if recent_stats else 0,
                    'ramificado_activations_24h': recent_stats.ramificado if recent_stats else 0,
                    'average_confidence_24h': recent_stats.avg_confidence if recent_stats and recent_stats.avg_confidence else 0.0
                },
                'active_alerts': {
                    'total': len(all_alerts),
                    'critical': len([a for a in all_alerts if a.level == AlertLevel.CRITICAL]),
                    'warning': len([a for a in all_alerts if a.level == AlertLevel.WARNING]),
                    'info': len([a for a in all_alerts if a.level == AlertLevel.INFO]),
                    'alerts': [asdict(alert) for alert in all_alerts[-10:]]  # Last 10 alerts
                },
                'trend_analysis': trend_analysis,
                'recommendations': self._generate_recommendations(current_metrics, all_alerts),
                'thresholds': asdict(self.thresholds)
            }

            logger.info(f"Health report generated: score {health_score:.2f}, {len(all_alerts)} alerts")

            return report

        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                'timestamp': datetime.utcnow(),
                'overall_health_score': 0.0,
                'system_status': 'error',
                'error': str(e),
                'recommendations': ['Check system logs', 'Verify database connectivity']
            }

    async def check_system_performance(self) -> Dict[str, Any]:
        """
        Perform system performance check with timing measurements.

        Returns:
            Dictionary with performance analysis results
        """
        try:
            logger.info("Performing archetype system performance check")

            start_time = datetime.utcnow()

            # Test basic database connectivity and query performance
            db_start = datetime.utcnow()
            total_classifications = await self.session.scalar(
                select(func.count(ArchetypeClassification.user_id))
            )
            db_end = datetime.utcnow()
            db_query_time = (db_end - db_start).total_seconds()

            # Test archetype analyzer initialization
            analyzer_start = datetime.utcnow()
            try:
                test_analyzer = ArchetypeAnalyzer(self.session)
                analyzer_init_success = True
            except Exception as e:
                analyzer_init_success = False
                logger.error(f"Analyzer initialization failed: {e}")
            analyzer_end = datetime.utcnow()
            analyzer_init_time = (analyzer_end - analyzer_start).total_seconds()

            # Test integration service
            integration_start = datetime.utcnow()
            try:
                test_integration = ArchetypeIntegrationService(self.session)
                integration_init_success = True
            except Exception as e:
                integration_init_success = False
                logger.error(f"Integration service initialization failed: {e}")
            integration_end = datetime.utcnow()
            integration_init_time = (integration_end - integration_start).total_seconds()

            end_time = datetime.utcnow()
            total_check_time = (end_time - start_time).total_seconds()

            # Performance assessment
            performance_status = "excellent"
            if db_query_time > 1.0 or total_check_time > 5.0:
                performance_status = "degraded"
            elif db_query_time > 0.5 or total_check_time > 2.0:
                performance_status = "suboptimal"

            return {
                'timestamp': datetime.utcnow(),
                'overall_status': performance_status,
                'total_check_time': total_check_time,
                'database_performance': {
                    'query_time': db_query_time,
                    'status': 'good' if db_query_time < 0.5 else 'slow',
                    'total_records': total_classifications or 0
                },
                'service_initialization': {
                    'analyzer_success': analyzer_init_success,
                    'analyzer_time': analyzer_init_time,
                    'integration_success': integration_init_success,
                    'integration_time': integration_init_time
                },
                'performance_recommendations': self._get_performance_recommendations(
                    db_query_time, total_check_time, analyzer_init_success, integration_init_success
                )
            }

        except Exception as e:
            logger.error(f"Error in performance check: {e}")
            return {
                'timestamp': datetime.utcnow(),
                'overall_status': 'error',
                'error': str(e),
                'performance_recommendations': ['Check system logs', 'Verify all services are running']
            }

    def _calculate_health_score(self, metrics: PerformanceMetrics, alerts: List[Alert]) -> float:
        """Calculate overall health score from metrics and alerts."""
        try:
            if metrics.total_classifications == 0:
                return 0.5  # Neutral score for no data

            # Base score from success rate
            success_rate = metrics.successful_classifications / metrics.total_classifications
            base_score = success_rate

            # Adjust for confidence distribution
            if metrics.total_classifications > 0:
                high_conf_rate = metrics.high_confidence_count / metrics.total_classifications
                confidence_boost = min(0.2, high_conf_rate * 0.5)
                base_score += confidence_boost

            # Penalty for alerts
            critical_alerts = len([a for a in alerts if a.level == AlertLevel.CRITICAL])
            warning_alerts = len([a for a in alerts if a.level == AlertLevel.WARNING])

            alert_penalty = (critical_alerts * 0.3) + (warning_alerts * 0.1)
            final_score = max(0.0, min(1.0, base_score - alert_penalty))

            return final_score

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0

    def _get_system_status(self, health_score: float) -> str:
        """Get system status description from health score."""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.8:
            return "good"
        elif health_score >= 0.7:
            return "fair"
        elif health_score >= 0.5:
            return "degraded"
        else:
            return "critical"

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends from historical metrics."""
        if len(self.metrics_history) < 2:
            return {"status": "insufficient_data"}

        try:
            # Get recent and older metrics for comparison
            recent_metrics = self.metrics_history[-3:]  # Last 3 measurements
            older_metrics = self.metrics_history[-6:-3] if len(self.metrics_history) >= 6 else []

            if not older_metrics:
                return {"status": "insufficient_historical_data"}

            # Calculate trends
            recent_avg_confidence = sum(m.average_confidence for m in recent_metrics) / len(recent_metrics)
            older_avg_confidence = sum(m.average_confidence for m in older_metrics) / len(older_metrics)

            recent_success_rate = sum(
                m.successful_classifications / max(m.total_classifications, 1) for m in recent_metrics
            ) / len(recent_metrics)

            older_success_rate = sum(
                m.successful_classifications / max(m.total_classifications, 1) for m in older_metrics
            ) / len(older_metrics)

            return {
                "status": "analysis_complete",
                "confidence_trend": "improving" if recent_avg_confidence > older_avg_confidence else "declining",
                "confidence_change": recent_avg_confidence - older_avg_confidence,
                "success_rate_trend": "improving" if recent_success_rate > older_success_rate else "declining",
                "success_rate_change": recent_success_rate - older_success_rate,
                "data_points": len(self.metrics_history)
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_recommendations(self, metrics: PerformanceMetrics, alerts: List[Alert]) -> List[str]:
        """Generate actionable recommendations based on current state."""
        recommendations = []

        try:
            # Success rate recommendations
            if metrics.total_classifications > 0:
                success_rate = metrics.successful_classifications / metrics.total_classifications
                if success_rate < 0.9:
                    recommendations.append("Investigate and address classification failures")

            # Confidence recommendations
            if metrics.total_classifications > 0:
                high_conf_rate = metrics.high_confidence_count / metrics.total_classifications
                if high_conf_rate < 0.4:
                    recommendations.append("Review and improve choice weight calibration")

            # Alert-based recommendations
            if any(a.level == AlertLevel.CRITICAL for a in alerts):
                recommendations.append("Address critical alerts immediately")

            # Performance recommendations
            if len(self.metrics_history) > 1:
                trend_analysis = self._analyze_trends()
                if trend_analysis.get("confidence_trend") == "declining":
                    recommendations.append("Monitor confidence score trends and investigate causes")

            # General recommendations
            if not recommendations:
                recommendations.append("System appears healthy - continue regular monitoring")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Check system logs for errors"]

    def _get_performance_recommendations(
        self,
        db_time: float,
        total_time: float,
        analyzer_success: bool,
        integration_success: bool
    ) -> List[str]:
        """Generate performance-specific recommendations."""
        recommendations = []

        if db_time > 1.0:
            recommendations.append("Database queries are slow - consider indexing optimization")
        elif db_time > 0.5:
            recommendations.append("Monitor database performance")

        if total_time > 5.0:
            recommendations.append("System performance is degraded - investigate resource usage")

        if not analyzer_success:
            recommendations.append("ArchetypeAnalyzer initialization failed - check dependencies")

        if not integration_success:
            recommendations.append("Integration service failed - verify configuration")

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations

    async def start_continuous_monitoring(self, interval_minutes: int = 15) -> None:
        """
        Start continuous monitoring loop.

        Args:
            interval_minutes: Minutes between monitoring cycles
        """
        logger.info(f"Starting continuous archetype monitoring (interval: {interval_minutes} minutes)")

        while True:
            try:
                # Generate health report
                health_report = await self.generate_comprehensive_health_report()

                # Log key metrics
                logger.info(f"System health: {health_report.get('overall_health_score', 0):.2f} "
                           f"({health_report.get('system_status', 'unknown')})")

                # Check for critical alerts
                critical_alerts = [
                    alert for alert in self.active_alerts.values()
                    if alert.level == AlertLevel.CRITICAL and not alert.resolved
                ]

                if critical_alerts:
                    logger.error(f"CRITICAL ALERTS ACTIVE: {len(critical_alerts)} alerts require attention")
                    for alert in critical_alerts:
                        logger.error(f"  - {alert.title}: {alert.description}")

                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error before retrying