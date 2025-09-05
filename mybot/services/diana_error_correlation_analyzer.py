"""
Diana Error Correlation Analyzer

Advanced error correlation and pattern analysis system for identifying
relationships between different types of errors in the Diana menu system.
"""

import asyncio
import logging
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Any
from enum import Enum

from services.diana_menu_error_tracker import (
    DianaMenuErrorTracker, ErrorEvent, ErrorCategory, 
    ErrorSeverity, ErrorPattern, get_error_tracker
)

logger = logging.getLogger(__name__)

class CorrelationType(Enum):
    """Types of error correlations."""
    TEMPORAL = "temporal"  # Errors occurring close in time
    CAUSAL = "causal"  # One error leading to another
    USER_BASED = "user_based"  # Errors affecting the same user
    OPERATION_BASED = "operation_based"  # Errors in related operations
    CASCADING = "cascading"  # Error cascades through system
    PATTERN_BASED = "pattern_based"  # Similar error patterns

@dataclass
class ErrorCorrelation:
    """Represents a correlation between errors."""
    correlation_id: str
    correlation_type: CorrelationType
    primary_error: str  # Error ID
    related_errors: List[str]  # List of related error IDs
    strength: float  # Correlation strength (0.0 to 1.0)
    confidence: float  # Confidence in correlation (0.0 to 1.0)
    time_window: timedelta
    description: str
    root_cause_hypothesis: str
    suggested_actions: List[str] = field(default_factory=list)
    verified: bool = False

@dataclass
class ErrorCluster:
    """Represents a cluster of related errors."""
    cluster_id: str
    errors: List[str]  # Error IDs
    centroid_features: Dict[str, Any]
    cluster_size: int
    time_span: timedelta
    dominant_category: ErrorCategory
    severity_distribution: Dict[ErrorSeverity, int]
    affected_users: Set[int]
    common_operations: List[str]
    
class DianaErrorCorrelationAnalyzer:
    """
    Advanced error correlation analyzer for the Diana menu system.
    
    Features:
    - Temporal correlation analysis
    - Causal relationship detection
    - Error clustering and pattern matching
    - Root cause hypothesis generation
    - Cascading failure detection
    """
    
    def __init__(self, error_tracker: Optional[DianaMenuErrorTracker] = None):
        self.error_tracker = error_tracker or get_error_tracker()
        self.correlations: Dict[str, ErrorCorrelation] = {}
        self.clusters: Dict[str, ErrorCluster] = {}
        
        # Analysis parameters
        self.temporal_window = timedelta(minutes=5)  # 5 minutes for temporal correlation
        self.causal_window = timedelta(seconds=30)   # 30 seconds for causal relationships
        self.min_correlation_strength = 0.3
        self.min_cluster_size = 3
        
        # Feature extractors for clustering
        self.feature_extractors = {
            'category': lambda e: e.category.value,
            'severity': lambda e: e.severity.value,
            'exception_type': lambda e: e.exception_type,
            'function_name': lambda e: e.function_name,
            'user_id': lambda e: e.context.user_id or 0,
            'operation': lambda e: e.context.operation or '',
            'hour_of_day': lambda e: e.timestamp.hour,
            'day_of_week': lambda e: e.timestamp.weekday(),
        }
        
        logger.info("Diana Error Correlation Analyzer initialized")
    
    async def analyze_correlations(self, hours: int = 24) -> List[ErrorCorrelation]:
        """Perform comprehensive correlation analysis on recent errors."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_tracker.errors if e.timestamp >= cutoff]
        
        if len(recent_errors) < 2:
            logger.info("Not enough errors for correlation analysis")
            return []
        
        correlations = []
        
        # Temporal correlation analysis
        temporal_corrs = await self._analyze_temporal_correlations(recent_errors)
        correlations.extend(temporal_corrs)
        
        # Causal relationship detection
        causal_corrs = await self._analyze_causal_relationships(recent_errors)
        correlations.extend(causal_corrs)
        
        # User-based correlation
        user_corrs = await self._analyze_user_based_correlations(recent_errors)
        correlations.extend(user_corrs)
        
        # Operation-based correlation
        operation_corrs = await self._analyze_operation_based_correlations(recent_errors)
        correlations.extend(operation_corrs)
        
        # Pattern-based correlation
        pattern_corrs = await self._analyze_pattern_based_correlations(recent_errors)
        correlations.extend(pattern_corrs)
        
        # Store correlations
        for corr in correlations:
            self.correlations[corr.correlation_id] = corr
        
        logger.info(f"Found {len(correlations)} error correlations")
        return correlations
    
    async def _analyze_temporal_correlations(self, errors: List[ErrorEvent]) -> List[ErrorCorrelation]:
        """Analyze errors that occur close in time."""
        correlations = []
        
        # Sort errors by timestamp
        errors.sort(key=lambda e: e.timestamp)
        
        for i, error in enumerate(errors[:-1]):
            related_errors = []
            
            # Look for errors within the temporal window
            for j in range(i + 1, len(errors)):
                other_error = errors[j]
                
                if other_error.timestamp - error.timestamp > self.temporal_window:
                    break
                
                # Calculate temporal correlation strength
                time_diff = (other_error.timestamp - error.timestamp).total_seconds()
                strength = max(0, 1.0 - (time_diff / self.temporal_window.total_seconds()))
                
                if strength >= self.min_correlation_strength:
                    related_errors.append(other_error.id)
            
            if related_errors:
                correlation = ErrorCorrelation(
                    correlation_id=f"temp_{error.id}_{len(related_errors)}",
                    correlation_type=CorrelationType.TEMPORAL,
                    primary_error=error.id,
                    related_errors=related_errors,
                    strength=min(1.0, len(related_errors) / 5.0),  # Normalize by expected max
                    confidence=0.7,
                    time_window=self.temporal_window,
                    description=f"Temporal cluster of {len(related_errors) + 1} errors within {self.temporal_window}",
                    root_cause_hypothesis=await self._generate_temporal_hypothesis(error, [e for e in errors if e.id in related_errors])
                )
                correlations.append(correlation)
        
        return correlations
    
    async def _analyze_causal_relationships(self, errors: List[ErrorEvent]) -> List[ErrorCorrelation]:
        """Detect potential causal relationships between errors."""
        correlations = []
        
        # Group errors by user and sort by time
        user_errors = defaultdict(list)
        for error in errors:
            if error.context.user_id:
                user_errors[error.context.user_id].append(error)
        
        for user_id, user_error_list in user_errors.items():
            user_error_list.sort(key=lambda e: e.timestamp)
            
            for i, error in enumerate(user_error_list[:-1]):
                for j in range(i + 1, len(user_error_list)):
                    next_error = user_error_list[j]
                    
                    if next_error.timestamp - error.timestamp > self.causal_window:
                        break
                    
                    # Check for causal patterns
                    causal_strength = await self._calculate_causal_strength(error, next_error)
                    
                    if causal_strength >= self.min_correlation_strength:
                        correlation = ErrorCorrelation(
                            correlation_id=f"causal_{error.id}_{next_error.id}",
                            correlation_type=CorrelationType.CAUSAL,
                            primary_error=error.id,
                            related_errors=[next_error.id],
                            strength=causal_strength,
                            confidence=0.8,
                            time_window=self.causal_window,
                            description=f"Potential causal relationship: {error.category.value} → {next_error.category.value}",
                            root_cause_hypothesis=await self._generate_causal_hypothesis(error, next_error)
                        )
                        correlations.append(correlation)
        
        return correlations
    
    async def _analyze_user_based_correlations(self, errors: List[ErrorEvent]) -> List[ErrorCorrelation]:
        """Analyze errors affecting the same users."""
        correlations = []
        
        # Group errors by user
        user_errors = defaultdict(list)
        for error in errors:
            if error.context.user_id:
                user_errors[error.context.user_id].append(error)
        
        for user_id, user_error_list in user_errors.items():
            if len(user_error_list) >= 3:  # At least 3 errors for the same user
                # Calculate error diversity and patterns
                categories = [e.category for e in user_error_list]
                category_counts = Counter(categories)
                
                # High correlation if same types of errors
                if len(category_counts) <= 2:  # Same or similar error types
                    primary_error = user_error_list[0]
                    related_errors = [e.id for e in user_error_list[1:]]
                    
                    correlation = ErrorCorrelation(
                        correlation_id=f"user_{user_id}_{len(user_error_list)}",
                        correlation_type=CorrelationType.USER_BASED,
                        primary_error=primary_error.id,
                        related_errors=related_errors,
                        strength=min(1.0, len(user_error_list) / 10.0),
                        confidence=0.9,
                        time_window=user_error_list[-1].timestamp - user_error_list[0].timestamp,
                        description=f"User {user_id} experiencing {len(user_error_list)} related errors",
                        root_cause_hypothesis=await self._generate_user_based_hypothesis(user_id, user_error_list)
                    )
                    correlations.append(correlation)
        
        return correlations
    
    async def _analyze_operation_based_correlations(self, errors: List[ErrorEvent]) -> List[ErrorCorrelation]:
        """Analyze errors in related operations."""
        correlations = []
        
        # Group errors by operation
        operation_errors = defaultdict(list)
        for error in errors:
            if error.context.operation:
                operation_errors[error.context.operation].append(error)
        
        for operation, operation_error_list in operation_errors.items():
            if len(operation_error_list) >= 3:  # At least 3 errors in same operation
                # Look for error patterns within the operation
                severity_counts = Counter([e.severity for e in operation_error_list])
                exception_counts = Counter([e.exception_type for e in operation_error_list])
                
                # High correlation if consistent error patterns
                if len(exception_counts) <= 2 or max(severity_counts.values()) >= len(operation_error_list) * 0.7:
                    primary_error = operation_error_list[0]
                    related_errors = [e.id for e in operation_error_list[1:]]
                    
                    correlation = ErrorCorrelation(
                        correlation_id=f"op_{operation}_{len(operation_error_list)}",
                        correlation_type=CorrelationType.OPERATION_BASED,
                        primary_error=primary_error.id,
                        related_errors=related_errors,
                        strength=min(1.0, len(operation_error_list) / 8.0),
                        confidence=0.85,
                        time_window=operation_error_list[-1].timestamp - operation_error_list[0].timestamp,
                        description=f"Operation '{operation}' experiencing {len(operation_error_list)} errors",
                        root_cause_hypothesis=await self._generate_operation_based_hypothesis(operation, operation_error_list)
                    )
                    correlations.append(correlation)
        
        return correlations
    
    async def _analyze_pattern_based_correlations(self, errors: List[ErrorEvent]) -> List[ErrorCorrelation]:
        """Analyze errors with similar patterns."""
        correlations = []
        
        # Create feature vectors for each error
        error_features = {}
        for error in errors:
            features = {}
            for feature_name, extractor in self.feature_extractors.items():
                features[feature_name] = extractor(error)
            error_features[error.id] = features
        
        # Find similar errors based on feature similarity
        processed_errors = set()
        
        for error in errors:
            if error.id in processed_errors:
                continue
            
            similar_errors = []
            base_features = error_features[error.id]
            
            for other_error in errors:
                if other_error.id == error.id or other_error.id in processed_errors:
                    continue
                
                other_features = error_features[other_error.id]
                similarity = self._calculate_feature_similarity(base_features, other_features)
                
                if similarity >= 0.7:  # High similarity threshold
                    similar_errors.append(other_error.id)
            
            if len(similar_errors) >= 2:  # At least 2 similar errors
                correlation = ErrorCorrelation(
                    correlation_id=f"pattern_{error.id}_{len(similar_errors)}",
                    correlation_type=CorrelationType.PATTERN_BASED,
                    primary_error=error.id,
                    related_errors=similar_errors,
                    strength=min(1.0, len(similar_errors) / 6.0),
                    confidence=0.75,
                    time_window=timedelta(hours=1),  # Pattern-based doesn't depend on time
                    description=f"Pattern-based cluster of {len(similar_errors) + 1} similar errors",
                    root_cause_hypothesis=await self._generate_pattern_based_hypothesis(error, [e for e in errors if e.id in similar_errors])
                )
                correlations.append(correlation)
                
                # Mark all errors in this pattern as processed
                processed_errors.add(error.id)
                processed_errors.update(similar_errors)
        
        return correlations
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature sets."""
        common_features = set(features1.keys()) & set(features2.keys())
        if not common_features:
            return 0.0
        
        matches = sum(1 for key in common_features if features1[key] == features2[key])
        return matches / len(common_features)
    
    async def _calculate_causal_strength(self, error1: ErrorEvent, error2: ErrorEvent) -> float:
        """Calculate the strength of a potential causal relationship."""
        strength = 0.0
        
        # Time-based factor (closer in time = higher strength)
        time_diff = (error2.timestamp - error1.timestamp).total_seconds()
        time_factor = max(0, 1.0 - (time_diff / self.causal_window.total_seconds()))
        strength += time_factor * 0.3
        
        # Category relationship factor
        causal_relationships = {
            (ErrorCategory.DATABASE, ErrorCategory.SERVICE): 0.8,
            (ErrorCategory.SERVICE, ErrorCategory.MENU_NAVIGATION): 0.7,
            (ErrorCategory.BASEMODEL, ErrorCategory.MENU_NAVIGATION): 0.6,
            (ErrorCategory.DEPENDENCY_INJECTION, ErrorCategory.SERVICE): 0.9,
            (ErrorCategory.CHARACTER_VALIDATION, ErrorCategory.SERVICE): 0.5,
        }
        
        category_pair = (error1.category, error2.category)
        if category_pair in causal_relationships:
            strength += causal_relationships[category_pair] * 0.4
        
        # Severity escalation factor
        severity_order = {
            ErrorSeverity.INFO: 0, ErrorSeverity.LOW: 1, ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 3, ErrorSeverity.CRITICAL: 4
        }
        
        if severity_order[error2.severity] > severity_order[error1.severity]:
            strength += 0.3  # Escalating severity suggests causality
        
        return min(1.0, strength)
    
    async def _generate_temporal_hypothesis(self, primary_error: ErrorEvent, related_errors: List[ErrorEvent]) -> str:
        """Generate root cause hypothesis for temporal correlations."""
        categories = [e.category for e in related_errors + [primary_error]]
        category_counts = Counter(categories)
        
        dominant_category = category_counts.most_common(1)[0][0]
        
        hypotheses = {
            ErrorCategory.DATABASE: "Potential database connection pool exhaustion or transaction deadlock",
            ErrorCategory.BASEMODEL: "Data validation pipeline issue affecting multiple operations",
            ErrorCategory.SERVICE: "Service dependency failure cascading through system",
            ErrorCategory.TELEGRAM_API: "Telegram API rate limiting or network connectivity issues",
            ErrorCategory.PERFORMANCE: "System overload causing multiple timeout errors",
        }
        
        return hypotheses.get(dominant_category, "System-wide issue affecting multiple components simultaneously")
    
    async def _generate_causal_hypothesis(self, cause_error: ErrorEvent, effect_error: ErrorEvent) -> str:
        """Generate root cause hypothesis for causal relationships."""
        return f"Initial {cause_error.category.value} error in {cause_error.function_name} " \
               f"likely triggered subsequent {effect_error.category.value} error in {effect_error.function_name}"
    
    async def _generate_user_based_hypothesis(self, user_id: int, errors: List[ErrorEvent]) -> str:
        """Generate root cause hypothesis for user-based correlations."""
        categories = Counter([e.category for e in errors])
        operations = Counter([e.context.operation for e in errors if e.context.operation])
        
        if len(categories) == 1:
            category = list(categories.keys())[0]
            return f"User {user_id} has persistent {category.value} issues, possibly due to invalid user state or permissions"
        
        return f"User {user_id} experiencing multiple error types, suggesting account-specific configuration or data issues"
    
    async def _generate_operation_based_hypothesis(self, operation: str, errors: List[ErrorEvent]) -> str:
        """Generate root cause hypothesis for operation-based correlations."""
        exception_types = Counter([e.exception_type for e in errors])
        
        if len(exception_types) == 1:
            exception_type = list(exception_types.keys())[0]
            return f"Operation '{operation}' consistently failing with {exception_type}, indicating specific logic or dependency issue"
        
        return f"Operation '{operation}' unstable with multiple failure modes, suggesting complex system interaction problem"
    
    async def _generate_pattern_based_hypothesis(self, primary_error: ErrorEvent, similar_errors: List[ErrorEvent]) -> str:
        """Generate root cause hypothesis for pattern-based correlations."""
        return f"Recurring pattern of {primary_error.category.value} errors with {primary_error.exception_type} " \
               f"suggests systematic issue in {primary_error.function_name} or related code path"
    
    async def cluster_errors(self, hours: int = 24) -> List[ErrorCluster]:
        """Perform error clustering to identify groups of related errors."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_tracker.errors if e.timestamp >= cutoff]
        
        if len(recent_errors) < self.min_cluster_size:
            return []
        
        # Extract features for clustering
        error_features = []
        error_ids = []
        
        for error in recent_errors:
            features = [
                hash(error.category.value) % 1000,
                hash(error.exception_type) % 1000,
                hash(error.function_name) % 1000,
                error.timestamp.hour,
                error.timestamp.weekday(),
                error.context.user_id or 0,
            ]
            error_features.append(features)
            error_ids.append(error.id)
        
        # Simple clustering based on feature similarity
        clusters = []
        used_errors = set()
        
        for i, error_id in enumerate(error_ids):
            if error_id in used_errors:
                continue
            
            cluster_errors = [error_id]
            cluster_features = [error_features[i]]
            
            for j, other_error_id in enumerate(error_ids[i+1:], i+1):
                if other_error_id in used_errors:
                    continue
                
                # Calculate feature distance
                distance = sum(abs(a - b) for a, b in zip(error_features[i], error_features[j]))
                
                if distance < 500:  # Similarity threshold
                    cluster_errors.append(other_error_id)
                    cluster_features.append(error_features[j])
            
            if len(cluster_errors) >= self.min_cluster_size:
                # Calculate cluster properties
                cluster_error_objects = [e for e in recent_errors if e.id in cluster_errors]
                
                cluster = ErrorCluster(
                    cluster_id=f"cluster_{i}_{len(cluster_errors)}",
                    errors=cluster_errors,
                    centroid_features=self._calculate_centroid(cluster_features),
                    cluster_size=len(cluster_errors),
                    time_span=max(e.timestamp for e in cluster_error_objects) - min(e.timestamp for e in cluster_error_objects),
                    dominant_category=Counter([e.category for e in cluster_error_objects]).most_common(1)[0][0],
                    severity_distribution=Counter([e.severity for e in cluster_error_objects]),
                    affected_users={e.context.user_id for e in cluster_error_objects if e.context.user_id},
                    common_operations=[e.context.operation for e in cluster_error_objects if e.context.operation]
                )
                
                clusters.append(cluster)
                used_errors.update(cluster_errors)
        
        # Store clusters
        for cluster in clusters:
            self.clusters[cluster.cluster_id] = cluster
        
        logger.info(f"Created {len(clusters)} error clusters")
        return clusters
    
    def _calculate_centroid(self, features_list: List[List[float]]) -> Dict[str, float]:
        """Calculate the centroid of a cluster."""
        if not features_list:
            return {}
        
        centroid = {}
        num_features = len(features_list[0])
        
        for i in range(num_features):
            centroid[f'feature_{i}'] = sum(features[i] for features in features_list) / len(features_list)
        
        return centroid
    
    def get_correlation_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a comprehensive correlation analysis report."""
        recent_correlations = [
            corr for corr in self.correlations.values()
            if any(
                error.timestamp >= datetime.now() - timedelta(hours=hours)
                for error in self.error_tracker.errors
                if error.id == corr.primary_error
            )
        ]
        
        report = {
            'analysis_period_hours': hours,
            'total_correlations': len(recent_correlations),
            'correlations_by_type': Counter([c.correlation_type.value for c in recent_correlations]),
            'high_strength_correlations': len([c for c in recent_correlations if c.strength >= 0.7]),
            'verified_correlations': len([c for c in recent_correlations if c.verified]),
            'top_correlations': sorted(recent_correlations, key=lambda c: c.strength, reverse=True)[:10],
            'clusters': len(self.clusters),
            'recommendations': self._generate_recommendations(recent_correlations)
        }
        
        return report
    
    def _generate_recommendations(self, correlations: List[ErrorCorrelation]) -> List[str]:
        """Generate actionable recommendations based on correlation analysis."""
        recommendations = []
        
        # Count correlation types
        type_counts = Counter([c.correlation_type for c in correlations])
        
        if type_counts[CorrelationType.TEMPORAL] > 5:
            recommendations.append("High temporal correlation suggests system overload - consider implementing rate limiting or load balancing")
        
        if type_counts[CorrelationType.CAUSAL] > 3:
            recommendations.append("Multiple causal relationships detected - review error handling and implement circuit breakers")
        
        if type_counts[CorrelationType.USER_BASED] > 2:
            recommendations.append("User-specific error patterns detected - review user data validation and session management")
        
        if type_counts[CorrelationType.PATTERN_BASED] > 4:
            recommendations.append("Recurring error patterns identified - prioritize fixing these systematic issues")
        
        # High-strength correlations
        high_strength = [c for c in correlations if c.strength >= 0.8]
        if len(high_strength) > 3:
            recommendations.append("Multiple high-strength correlations suggest critical system issues requiring immediate attention")
        
        return recommendations