"""
Character Consistency Integration Service

Provides real-time character validation integration for the master storyline system.
Ensures Diana maintains >95% character consistency across all interactions while
supporting dynamic adaptation based on user archetypes.

Key Features:
- Real-time validation during narrative interactions
- Character consistency scoring and monitoring
- Automatic fallback mechanisms for consistency failures
- Integration with user archetyping for personalized adaptations
- Performance optimization for <500ms response requirements
- Comprehensive reporting and analytics
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc

from database.narrative_unified import (
    NarrativeCharacterValidation,
    UserNarrativeState,
    NarrativeFragment,
    UserArchetype
)
from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult
from services.user_archetyping_service import UserArchetypingService

logger = logging.getLogger(__name__)

class ValidationTrigger(Enum):
    """Triggers for character consistency validation."""
    FRAGMENT_DISPLAY = "fragment_display"
    USER_INTERACTION = "user_interaction" 
    MENU_RESPONSE = "menu_response"
    ERROR_MESSAGE = "error_message"
    VIP_OFFER = "vip_offer"
    MISSION_FEEDBACK = "mission_feedback"
    PERSONALIZED_CONTENT = "personalized_content"

class ConsistencyLevel(Enum):
    """Character consistency levels."""
    CRITICAL = "critical"      # >95% required
    HIGH = "high"             # >90% required
    STANDARD = "standard"     # >85% required
    RELAXED = "relaxed"       # >80% required

@dataclass
class ValidationRequest:
    """Request for character validation."""
    content: str
    context: str
    user_id: Optional[int] = None
    fragment_id: Optional[str] = None
    trigger: ValidationTrigger = ValidationTrigger.FRAGMENT_DISPLAY
    consistency_level: ConsistencyLevel = ConsistencyLevel.CRITICAL
    archetype_adaptation: Optional[Dict[str, Any]] = None

@dataclass
class ValidationResponse:
    """Response from character validation."""
    is_valid: bool
    consistency_score: float
    meets_threshold: bool
    validation_details: CharacterValidationResult
    fallback_content: Optional[str] = None
    improvement_suggestions: List[str] = None
    performance_metrics: Dict[str, Any] = None

@dataclass 
class ConsistencyMonitoringResult:
    """Result from consistency monitoring analysis."""
    overall_consistency: float
    trend_analysis: Dict[str, Any]
    problem_areas: List[str]
    improvement_recommendations: List[str]
    archetype_adaptation_effectiveness: float

class CharacterConsistencyIntegrationService:
    """
    Service for real-time character consistency validation and integration.
    Ensures Diana maintains her personality across all user interactions.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_validator = DianaCharacterValidator(session)
        self.archetyping_service = UserArchetypingService(session)
        
        # Consistency thresholds by validation level
        self.consistency_thresholds = {
            ConsistencyLevel.CRITICAL: 95.0,
            ConsistencyLevel.HIGH: 90.0,
            ConsistencyLevel.STANDARD: 85.0,
            ConsistencyLevel.RELAXED: 80.0
        }
        
        # Fallback content templates by context
        self.fallback_templates = {
            'fragment_display': "Diana permanece en las sombras, observándote con interés...",
            'user_interaction': "Diana sonríe misteriosamente, considerando tu respuesta...",
            'menu_response': "Diana te guía sutilmente hacia las opciones disponibles...",
            'error_message': "Diana susurra... 'Algo ha interrumpido nuestro momento, pero volveremos a conectar.'",
            'vip_offer': "Diana te mira con ojos conocedores... 'Hay niveles más profundos de experiencia esperándote.'",
            'mission_feedback': "Diana evalúa tu progreso con una mezcla de aprobación y misterio...",
            'personalized_content': "Diana adapta su presencia a tu energía única..."
        }
        
        # Performance tracking
        self._validation_cache = {}
        self._cache_expiry = 300  # 5 minutes
        
    async def validate_content_real_time(
        self, 
        request: ValidationRequest
    ) -> ValidationResponse:
        """
        Perform real-time character consistency validation.
        
        Args:
            request: Validation request with content and context
            
        Returns:
            ValidationResponse with validation results and fallback if needed
        """
        start_time = datetime.utcnow()
        
        try:
            # Check cache first for performance
            cache_key = self._generate_cache_key(request)
            if cache_key in self._validation_cache:
                cached_result = self._validation_cache[cache_key]
                if (datetime.utcnow() - cached_result['timestamp']).seconds < self._cache_expiry:
                    logger.debug(f"Using cached validation result for {cache_key}")
                    cached_result['response'].performance_metrics = {
                        'validation_time_ms': 1,  # Cache hit
                        'cache_hit': True
                    }
                    return cached_result['response']
            
            # Perform validation
            validation_result = await self._perform_validation(request)
            
            # Determine if content meets threshold
            required_threshold = self.consistency_thresholds[request.consistency_level]
            meets_threshold = validation_result.overall_score >= required_threshold
            
            # Generate fallback content if validation fails
            fallback_content = None
            if not meets_threshold:
                fallback_content = await self._generate_fallback_content(request)
                logger.warning(
                    f"Content validation failed: {validation_result.overall_score:.1f}% < {required_threshold}% "
                    f"for context '{request.context}'"
                )
            
            # Create response
            response = ValidationResponse(
                is_valid=meets_threshold,
                consistency_score=validation_result.overall_score,
                meets_threshold=meets_threshold,
                validation_details=validation_result,
                fallback_content=fallback_content,
                improvement_suggestions=validation_result.recommendations,
                performance_metrics={
                    'validation_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    'cache_hit': False
                }
            )
            
            # Cache successful validations
            if meets_threshold and len(request.content) < 1000:  # Don't cache very long content
                self._validation_cache[cache_key] = {
                    'response': response,
                    'timestamp': datetime.utcnow()
                }
            
            # Record validation in database for monitoring
            if request.user_id:
                await self._record_validation_result(request, validation_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in real-time validation: {e}")
            # Return emergency fallback
            return ValidationResponse(
                is_valid=False,
                consistency_score=0.0,
                meets_threshold=False,
                validation_details=None,
                fallback_content=await self._generate_emergency_fallback(request.context),
                improvement_suggestions=["System error - content validation failed"],
                performance_metrics={
                    'validation_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    'error': str(e)
                }
            )
    
    async def validate_fragment_with_adaptation(
        self, 
        fragment: NarrativeFragment, 
        user_id: int
    ) -> ValidationResponse:
        """
        Validate fragment content with archetype-based adaptation.
        
        Args:
            fragment: Narrative fragment to validate
            user_id: User ID for archetype adaptation
            
        Returns:
            ValidationResponse with adapted content if needed
        """
        # Get user archetype for adaptation
        archetype_analysis = await self.archetyping_service.get_user_archetype_analysis(user_id)
        diana_strategy = await self.archetyping_service.get_diana_adaptation_strategy(user_id, 'fragment')
        
        # Create validation request
        request = ValidationRequest(
            content=f"{fragment.title}\n\n{fragment.content}",
            context="narrative_fragment",
            user_id=user_id,
            fragment_id=fragment.id,
            trigger=ValidationTrigger.FRAGMENT_DISPLAY,
            consistency_level=ConsistencyLevel.CRITICAL,
            archetype_adaptation=diana_strategy
        )
        
        # Perform validation
        validation_response = await self.validate_content_real_time(request)
        
        # If validation fails but we have archetype data, try adaptation
        if not validation_response.meets_threshold and diana_strategy:
            adapted_content = await self._adapt_content_for_consistency(
                fragment.content, diana_strategy, validation_response.validation_details
            )
            
            if adapted_content != fragment.content:
                # Re-validate adapted content
                adapted_request = ValidationRequest(
                    content=f"{fragment.title}\n\n{adapted_content}",
                    context="narrative_fragment_adapted",
                    user_id=user_id,
                    fragment_id=fragment.id,
                    trigger=ValidationTrigger.FRAGMENT_DISPLAY,
                    consistency_level=ConsistencyLevel.CRITICAL,
                    archetype_adaptation=diana_strategy
                )
                
                adapted_validation = await self.validate_content_real_time(adapted_request)
                if adapted_validation.meets_threshold:
                    validation_response.fallback_content = adapted_content
                    validation_response.is_valid = True
                    validation_response.consistency_score = adapted_validation.consistency_score
                    logger.info(f"Successfully adapted fragment {fragment.id} for user {user_id}")
        
        return validation_response
    
    async def monitor_user_consistency_trends(
        self, 
        user_id: int, 
        days_back: int = 30
    ) -> ConsistencyMonitoringResult:
        """
        Monitor character consistency trends for a specific user.
        
        Args:
            user_id: User ID to analyze
            days_back: Number of days to analyze
            
        Returns:
            ConsistencyMonitoringResult with trend analysis
        """
        try:
            # Get validation history
            since_date = datetime.utcnow() - timedelta(days=days_back)
            stmt = select(NarrativeCharacterValidation).where(
                and_(
                    NarrativeCharacterValidation.user_id == user_id,
                    NarrativeCharacterValidation.validated_at >= since_date
                )
            ).order_by(desc(NarrativeCharacterValidation.validated_at))
            
            result = await self.session.execute(stmt)
            validations = result.scalars().all()
            
            if not validations:
                return ConsistencyMonitoringResult(
                    overall_consistency=0.0,
                    trend_analysis={'trend': 'no_data', 'validations_count': 0},
                    problem_areas=[],
                    improvement_recommendations=['No validation data available'],
                    archetype_adaptation_effectiveness=0.0
                )
            
            # Calculate overall consistency
            overall_consistency = sum(v.consistency_score for v in validations) / len(validations)
            
            # Analyze trends
            trend_analysis = self._analyze_consistency_trends(validations)
            
            # Identify problem areas
            problem_areas = self._identify_problem_areas(validations)
            
            # Generate recommendations
            improvement_recommendations = self._generate_consistency_recommendations(
                validations, trend_analysis, problem_areas
            )
            
            # Measure archetype adaptation effectiveness
            archetype_effectiveness = await self._measure_archetype_adaptation_effectiveness(user_id, validations)
            
            return ConsistencyMonitoringResult(
                overall_consistency=overall_consistency,
                trend_analysis=trend_analysis,
                problem_areas=problem_areas,
                improvement_recommendations=improvement_recommendations,
                archetype_adaptation_effectiveness=archetype_effectiveness
            )
            
        except Exception as e:
            logger.error(f"Error monitoring consistency trends for user {user_id}: {e}")
            return ConsistencyMonitoringResult(
                overall_consistency=0.0,
                trend_analysis={'trend': 'error', 'message': str(e)},
                problem_areas=[],
                improvement_recommendations=['Error analyzing consistency trends'],
                archetype_adaptation_effectiveness=0.0
            )
    
    async def generate_consistency_report(
        self, 
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate comprehensive character consistency report.
        
        Args:
            time_period_days: Time period for report analysis
            
        Returns:
            Dictionary with comprehensive consistency report
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            # Get all validations in period
            stmt = select(NarrativeCharacterValidation).where(
                NarrativeCharacterValidation.validated_at >= since_date
            )
            result = await self.session.execute(stmt)
            validations = result.scalars().all()
            
            if not validations:
                return {
                    'period_days': time_period_days,
                    'total_validations': 0,
                    'message': 'No validation data available for specified period'
                }
            
            # Overall statistics
            total_validations = len(validations)
            passing_validations = len([v for v in validations if v.meets_threshold])
            overall_pass_rate = (passing_validations / total_validations) * 100
            
            # Average scores by trait
            avg_scores = {
                'overall': sum(v.consistency_score for v in validations) / total_validations,
                'mysterious': sum(v.mysterious_score for v in validations) / total_validations,
                'seductive': sum(v.seductive_score for v in validations) / total_validations,
                'emotional_complexity': sum(v.emotional_complexity_score for v in validations) / total_validations,
                'intellectual_engagement': sum(v.intellectual_engagement_score for v in validations) / total_validations
            }
            
            # Content type breakdown
            content_type_stats = {}
            for validation in validations:
                content_type = validation.content_type
                if content_type not in content_type_stats:
                    content_type_stats[content_type] = {
                        'count': 0,
                        'avg_score': 0,
                        'pass_rate': 0
                    }
                content_type_stats[content_type]['count'] += 1
            
            for content_type in content_type_stats:
                type_validations = [v for v in validations if v.content_type == content_type]
                content_type_stats[content_type]['avg_score'] = sum(v.consistency_score for v in type_validations) / len(type_validations)
                content_type_stats[content_type]['pass_rate'] = (len([v for v in type_validations if v.meets_threshold]) / len(type_validations)) * 100
            
            # Common violations analysis
            all_violations = []
            for validation in validations:
                if validation.violations_detected:
                    all_violations.extend(validation.violations_detected)
            
            violation_frequency = {}
            for violation in all_violations:
                violation_frequency[violation] = violation_frequency.get(violation, 0) + 1
            
            # Most common violations (top 10)
            common_violations = sorted(
                violation_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Performance analysis
            performance_stats = {
                'avg_validation_time': 'N/A',  # Would need to track validation times
                'cache_hit_rate': len(self._validation_cache) / max(total_validations, 1) * 100,
                'fallback_usage_rate': len([v for v in validations if not v.meets_threshold]) / total_validations * 100
            }
            
            # Recommendations
            system_recommendations = self._generate_system_recommendations(
                overall_pass_rate, avg_scores, common_violations, content_type_stats
            )
            
            return {
                'report_period': {
                    'days': time_period_days,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                },
                'overall_statistics': {
                    'total_validations': total_validations,
                    'passing_validations': passing_validations,
                    'overall_pass_rate': round(overall_pass_rate, 2),
                    'meets_mvp_requirement': overall_pass_rate >= 95.0
                },
                'trait_performance': {k: round(v, 2) for k, v in avg_scores.items()},
                'content_type_analysis': content_type_stats,
                'common_violations': [{'violation': v, 'frequency': f} for v, f in common_violations],
                'performance_metrics': performance_stats,
                'system_recommendations': system_recommendations,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating consistency report: {e}")
            return {
                'error': f"Failed to generate consistency report: {str(e)}",
                'generated_at': datetime.utcnow().isoformat()
            }
    
    # Private helper methods
    
    def _generate_cache_key(self, request: ValidationRequest) -> str:
        """Generate cache key for validation request."""
        content_hash = hash(request.content)
        archetype_hash = hash(str(request.archetype_adaptation)) if request.archetype_adaptation else 0
        return f"{request.context}_{content_hash}_{archetype_hash}"
    
    async def _perform_validation(self, request: ValidationRequest) -> CharacterValidationResult:
        """Perform the actual character validation."""
        return await self.character_validator.validate_text(request.content, request.context)
    
    async def _generate_fallback_content(self, request: ValidationRequest) -> str:
        """Generate fallback content when validation fails."""
        base_fallback = self.fallback_templates.get(request.context, 
                                                   "Diana permanece enigmática...")
        
        # Add archetype-specific adaptation if available
        if request.archetype_adaptation:
            interaction_style = request.archetype_adaptation.get('interaction_style', 'balanced')
            if interaction_style == 'mysterious_revealing':
                base_fallback += " Sus ojos sugieren secretos por descubrir."
            elif interaction_style == 'emotionally_intimate':
                base_fallback += " Su presencia transmite calidez y comprensión."
            elif interaction_style == 'intellectually_challenging':
                base_fallback += " Su mirada invita a una reflexión más profunda."
        
        return base_fallback
    
    async def _generate_emergency_fallback(self, context: str) -> str:
        """Generate emergency fallback for system errors."""
        return "Diana sonríe misteriosamente mientras el momento se recompone..."
    
    async def _record_validation_result(
        self, 
        request: ValidationRequest, 
        validation_result: CharacterValidationResult
    ):
        """Record validation result in database."""
        if not request.user_id:
            return
        
        # Get user archetype for context
        archetype = await self.archetyping_service._get_user_archetype(request.user_id)
        
        validation_record = NarrativeCharacterValidation(
            fragment_id=request.fragment_id,
            user_id=request.user_id,
            validated_content=request.content,
            content_type=request.context,
            consistency_score=int(validation_result.overall_score),
            mysterious_score=int(validation_result.trait_scores.get('mysterious', 0) * 4),
            seductive_score=int(validation_result.trait_scores.get('seductive', 0) * 4),
            emotional_complexity_score=int(validation_result.trait_scores.get('emotionally_complex', 0) * 4),
            intellectual_engagement_score=int(validation_result.trait_scores.get('intellectually_engaging', 0) * 4),
            meets_threshold=validation_result.meets_threshold,
            violations_detected=validation_result.violations,
            recommendations=validation_result.recommendations,
            validation_context={'trigger': request.trigger.value},
            archetype_influence=archetype.dominant_archetype if archetype else None
        )
        
        self.session.add(validation_record)
        await self.session.commit()
    
    async def _adapt_content_for_consistency(
        self,
        content: str,
        diana_strategy: Dict[str, Any],
        validation_details: CharacterValidationResult
    ) -> str:
        """Adapt content to improve character consistency."""
        adapted_content = content
        
        # Analyze specific validation failures
        violations = validation_details.violations if validation_details else []
        
        # Apply archetype-specific adaptations
        interaction_style = diana_strategy.get('interaction_style', 'balanced')
        
        if interaction_style == 'mysterious_revealing':
            # Add mystery elements if lacking
            if any('mystery' in v.lower() for v in violations):
                adapted_content += "... *[Diana deja caer una pista sutil]*"
        
        elif interaction_style == 'emotionally_intimate':
            # Add emotional depth if lacking
            if any('emotional' in v.lower() for v in violations):
                adapted_content += " *[Sus ojos revelan una profundidad emocional inesperada]*"
        
        elif interaction_style == 'intellectually_challenging':
            # Add intellectual complexity if lacking
            if any('intellectual' in v.lower() for v in violations):
                adapted_content += " *[Las palabras contienen capas de significado esperando ser exploradas]*"
        
        # Apply general consistency improvements
        if any('seductive' in v.lower() for v in violations):
            adapted_content = f"Diana te mira con ojos conocedores... {adapted_content}"
        
        if any('direct' in v.lower() for v in violations):
            # Make content less direct
            adapted_content = adapted_content.replace('.', '...', 1)  # Add ellipsis
        
        return adapted_content
    
    def _analyze_consistency_trends(self, validations: List[NarrativeCharacterValidation]) -> Dict[str, Any]:
        """Analyze consistency trends from validation history."""
        if len(validations) < 2:
            return {'trend': 'insufficient_data', 'validations_count': len(validations)}
        
        # Sort by date
        sorted_validations = sorted(validations, key=lambda v: v.validated_at)
        
        # Calculate trend (simple linear trend)
        scores = [v.consistency_score for v in sorted_validations]
        n = len(scores)
        
        # Simple trend calculation
        first_half_avg = sum(scores[:n//2]) / (n//2) if n >= 2 else scores[0]
        second_half_avg = sum(scores[n//2:]) / (n - n//2) if n >= 2 else scores[-1]
        
        trend_direction = 'improving' if second_half_avg > first_half_avg else 'declining' if second_half_avg < first_half_avg else 'stable'
        trend_magnitude = abs(second_half_avg - first_half_avg)
        
        return {
            'trend': trend_direction,
            'magnitude': trend_magnitude,
            'first_half_avg': first_half_avg,
            'second_half_avg': second_half_avg,
            'validations_count': len(validations),
            'latest_score': scores[-1],
            'best_score': max(scores),
            'worst_score': min(scores)
        }
    
    def _identify_problem_areas(self, validations: List[NarrativeCharacterValidation]) -> List[str]:
        """Identify problem areas from validation history."""
        problem_areas = []
        
        # Analyze trait performance
        trait_averages = {
            'mysterious': sum(v.mysterious_score for v in validations) / len(validations),
            'seductive': sum(v.seductive_score for v in validations) / len(validations),
            'emotional_complexity': sum(v.emotional_complexity_score for v in validations) / len(validations),
            'intellectual_engagement': sum(v.intellectual_engagement_score for v in validations) / len(validations)
        }
        
        for trait, avg_score in trait_averages.items():
            if avg_score < 80:  # Threshold for concern
                problem_areas.append(f"Low {trait} scores (avg: {avg_score:.1f})")
        
        # Analyze content type performance
        content_types = {}
        for validation in validations:
            content_type = validation.content_type
            if content_type not in content_types:
                content_types[content_type] = []
            content_types[content_type].append(validation.consistency_score)
        
        for content_type, scores in content_types.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 85:  # Threshold for concern
                problem_areas.append(f"Poor performance in {content_type} (avg: {avg_score:.1f}%)")
        
        return problem_areas
    
    def _generate_consistency_recommendations(
        self, 
        validations: List[NarrativeCharacterValidation],
        trend_analysis: Dict[str, Any],
        problem_areas: List[str]
    ) -> List[str]:
        """Generate recommendations for consistency improvement."""
        recommendations = []
        
        # Trend-based recommendations
        if trend_analysis['trend'] == 'declining':
            recommendations.append(f"Address declining consistency trend (dropped {trend_analysis['magnitude']:.1f} points)")
        
        # Problem area recommendations
        for problem in problem_areas:
            if 'mysterious' in problem.lower():
                recommendations.append("Increase mystery elements: use more ellipsis, indirect language, and hints")
            elif 'seductive' in problem.lower():
                recommendations.append("Enhance seductive charm: add more intimate language and emotional connection")
            elif 'emotional_complexity' in problem.lower():
                recommendations.append("Deepen emotional content: show inner conflicts and vulnerability")
            elif 'intellectual_engagement' in problem.lower():
                recommendations.append("Stimulate intellect: pose more questions and philosophical thoughts")
        
        # Performance-based recommendations
        avg_score = sum(v.consistency_score for v in validations) / len(validations)
        if avg_score < 95:
            recommendations.append(f"Overall consistency below MVP requirement: {avg_score:.1f}% < 95%")
        
        return recommendations[:5]  # Top 5 recommendations
    
    async def _measure_archetype_adaptation_effectiveness(
        self, 
        user_id: int, 
        validations: List[NarrativeCharacterValidation]
    ) -> float:
        """Measure effectiveness of archetype-based adaptations."""
        if not validations:
            return 0.0
        
        # Get user's archetype
        archetype = await self.archetyping_service._get_user_archetype(user_id)
        if not archetype or not archetype.dominant_archetype:
            return 0.5  # Default effectiveness
        
        # Analyze validation scores for content with archetype influence
        archetype_influenced = [v for v in validations if v.archetype_influence == archetype.dominant_archetype]
        non_influenced = [v for v in validations if v.archetype_influence != archetype.dominant_archetype or v.archetype_influence is None]
        
        if not archetype_influenced:
            return 0.5  # No data
        
        # Compare performance
        influenced_avg = sum(v.consistency_score for v in archetype_influenced) / len(archetype_influenced)
        
        if non_influenced:
            non_influenced_avg = sum(v.consistency_score for v in non_influenced) / len(non_influenced)
            effectiveness = min((influenced_avg / non_influenced_avg), 2.0) if non_influenced_avg > 0 else 1.0
        else:
            effectiveness = influenced_avg / 100  # Normalize to 0-1 scale
        
        return min(effectiveness, 1.0)
    
    def _generate_system_recommendations(
        self,
        overall_pass_rate: float,
        avg_scores: Dict[str, float],
        common_violations: List[Tuple[str, int]],
        content_type_stats: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate system-level recommendations."""
        recommendations = []
        
        # Overall performance recommendations
        if overall_pass_rate < 95:
            recommendations.append(f"CRITICAL: Overall pass rate {overall_pass_rate:.1f}% below MVP requirement (95%)")
        elif overall_pass_rate < 98:
            recommendations.append(f"Improve overall pass rate from {overall_pass_rate:.1f}% toward 98%+ target")
        
        # Trait-specific recommendations
        for trait, score in avg_scores.items():
            if trait != 'overall' and score < 90:
                recommendations.append(f"Focus on improving {trait} trait (current avg: {score:.1f})")
        
        # Violation-based recommendations
        if common_violations:
            most_common_violation = common_violations[0][0]
            recommendations.append(f"Address most common violation: '{most_common_violation}'")
        
        # Content type recommendations
        worst_content_type = None
        worst_score = 100
        for content_type, stats in content_type_stats.items():
            if stats['avg_score'] < worst_score:
                worst_score = stats['avg_score']
                worst_content_type = content_type
        
        if worst_content_type and worst_score < 85:
            recommendations.append(f"Improve {worst_content_type} content quality (avg: {worst_score:.1f}%)")
        
        return recommendations[:5]  # Top 5 recommendations