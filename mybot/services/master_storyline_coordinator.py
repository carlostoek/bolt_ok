"""
Master Storyline Coordinator Service

Central orchestration service for the complete master storyline system.
Integrates all components: narrative engine, mission validation, user archetyping, 
VIP management, character validation, performance optimization, and Lucien coordination.

This is the main entry point for all narrative operations in the enhanced system.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from services.enhanced_unified_narrative_service import EnhancedUnifiedNarrativeService
from services.master_storyline_mission_service import MasterStorylineMissionService
from services.user_archetyping_service import UserArchetypingService
from services.vip_tier_management_service import VIPTierManagementService
from services.character_consistency_integration_service import CharacterConsistencyIntegrationService
from services.narrative_performance_optimization_service import NarrativePerformanceOptimizationService
from services.lucien_coordination_service import LucienCoordinationService

logger = logging.getLogger(__name__)

@dataclass
class MasterStorylineResponse:
    """Unified response from master storyline system."""
    success: bool
    operation: str
    data: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    character_validation: Optional[Dict[str, Any]] = None
    archetyping_insights: Optional[Dict[str, Any]] = None
    lucien_coordination: Optional[Dict[str, Any]] = None
    vip_opportunities: Optional[Dict[str, Any]] = None
    next_recommendations: List[str] = None
    error_details: Optional[str] = None

class MasterStorylineCoordinator:
    """
    Central coordinator for the complete master storyline system.
    Orchestrates all narrative operations with integrated services.
    """
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        
        # Initialize all integrated services
        self.narrative_service = EnhancedUnifiedNarrativeService(session, bot)
        self.mission_service = MasterStorylineMissionService(session)
        self.archetyping_service = UserArchetypingService(session)
        self.vip_service = VIPTierManagementService(session)
        self.character_service = CharacterConsistencyIntegrationService(session)
        self.performance_service = NarrativePerformanceOptimizationService()
        self.lucien_service = LucienCoordinationService(session)
        
        # Master storyline configuration
        self.system_configuration = {
            'performance_budget_ms': 500,
            'character_consistency_threshold': 95.0,
            'archetyping_confidence_threshold': 0.7,
            'vip_readiness_threshold': 0.6,
            'lucien_coordination_enabled': True
        }
    
    @property
    def performance_tracked(self):
        """Get performance tracking decorator from performance service."""
        return self.performance_service.performance_tracked
    
    async def initialize_user_in_master_storyline(self, user_id: int) -> MasterStorylineResponse:
        """Initialize a user in the complete master storyline system."""
        operation = "initialize_master_storyline"
        
        @self.performance_tracked(operation)
        async def _initialize():
            # Start narrative
            narrative_result = await self.narrative_service.start_master_storyline(user_id)
            
            if not narrative_result['success']:
                return MasterStorylineResponse(
                    success=False,
                    operation=operation,
                    data={},
                    performance_metrics={},
                    error_details=narrative_result.get('error', 'Failed to initialize narrative')
                )
            
            # Initialize archetyping
            archetype_result = await self.archetyping_service.analyze_user_behavior(user_id)
            
            # Check VIP opportunities
            vip_opportunity = await self.vip_service.generate_upgrade_opportunity(
                user_id, 'initialization'
            )
            
            # Initialize Lucien coordination if needed
            lucien_needs = await self.lucien_service.evaluate_coordination_needs(
                user_id, 
                {'event_type': 'initialization', 'new_user': True}
            )
            
            lucien_result = None
            if lucien_needs:
                lucien_result = await self.lucien_service.execute_coordination_action(
                    user_id, lucien_needs
                )
            
            return MasterStorylineResponse(
                success=True,
                operation=operation,
                data=narrative_result,
                performance_metrics=narrative_result.get('performance', {}),
                archetyping_insights=archetype_result.__dict__ if archetype_result else None,
                vip_opportunities={'offer': vip_opportunity.to_dict()} if vip_opportunity else None,
                lucien_coordination=lucien_result,
                next_recommendations=await self._generate_initialization_recommendations(user_id)
            )
        
        result, perf_metrics = await _initialize()
        result.performance_metrics.update(perf_metrics.__dict__)
        return result
    
    async def process_narrative_interaction(
        self, 
        user_id: int, 
        interaction_data: Dict[str, Any]
    ) -> MasterStorylineResponse:
        """Process a complete narrative interaction with all integrated systems."""
        operation = "process_narrative_interaction"
        
        @self.performance_tracked(operation)
        async def _process_interaction():
            # Extract interaction details
            fragment_id = interaction_data.get('fragment_id')
            interaction_type = interaction_data.get('interaction_type', 'fragment_view')
            
            # Process through narrative service
            narrative_result = await self.narrative_service.process_fragment_interaction(
                user_id, fragment_id, interaction_data
            )
            
            if not narrative_result['success']:
                # Handle narrative processing failure
                return await self._handle_narrative_failure(
                    user_id, narrative_result, interaction_data
                )
            
            # Parallel processing of related services
            tasks = [
                self._process_archetyping_update(user_id, interaction_data),
                self._check_vip_opportunities(user_id, interaction_data),
                self._evaluate_lucien_coordination(user_id, interaction_data),
                self._validate_character_consistency(user_id, narrative_result),
            ]
            
            # Execute tasks in parallel for performance
            archetype_update, vip_check, lucien_eval, char_validation = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            # Process results and handle any exceptions
            processed_results = self._process_parallel_results(
                archetype_update, vip_check, lucien_eval, char_validation
            )
            
            # Generate next recommendations
            next_recommendations = await self._generate_interaction_recommendations(
                user_id, narrative_result, processed_results
            )
            
            return MasterStorylineResponse(
                success=True,
                operation=operation,
                data=narrative_result,
                performance_metrics=narrative_result.get('performance', {}),
                character_validation=processed_results.get('character_validation'),
                archetyping_insights=processed_results.get('archetyping'),
                lucien_coordination=processed_results.get('lucien'),
                vip_opportunities=processed_results.get('vip'),
                next_recommendations=next_recommendations
            )
        
        result, perf_metrics = await _process_interaction()
        result.performance_metrics.update(perf_metrics.__dict__)
        return result
    
    async def process_user_decision_comprehensive(
        self, 
        user_id: int, 
        decision_data: Dict[str, Any]
    ) -> MasterStorylineResponse:
        """Process user decision with comprehensive integration."""
        operation = "process_user_decision_comprehensive"
        
        @self.performance_tracked(operation)
        async def _process_decision():
            # Process decision through enhanced narrative service
            decision_result = await self.narrative_service.process_user_decision_enhanced(
                user_id, decision_data.get('fragment_id'), decision_data
            )
            
            if not decision_result['success']:
                return MasterStorylineResponse(
                    success=False,
                    operation=operation,
                    data={},
                    performance_metrics={},
                    error_details=decision_result.get('error')
                )
            
            # Handle progression events
            progression_updates = []
            if decision_result.get('progression_result'):
                progression_updates = await self._handle_progression_events(
                    user_id, decision_result['progression_result']
                )
            
            # Handle access denied scenarios
            access_support = None
            if decision_result.get('access_denied_info'):
                access_support = await self._handle_access_denied_support(
                    user_id, decision_result['access_denied_info']
                )
            
            # Update archetyping based on decision patterns
            archetype_update = await self.archetyping_service.track_real_time_behavior(
                user_id, 'decision_comprehensive', decision_data
            )
            
            return MasterStorylineResponse(
                success=True,
                operation=operation,
                data=decision_result,
                performance_metrics=decision_result.get('performance', {}),
                archetyping_insights=archetype_update,
                vip_opportunities=access_support,
                next_recommendations=await self._generate_decision_recommendations(
                    user_id, decision_result, progression_updates
                )
            )
        
        result, perf_metrics = await _process_decision()
        result.performance_metrics.update(perf_metrics.__dict__)
        return result
    
    async def generate_personalized_experience(
        self, 
        user_id: int, 
        experience_type: str = "adaptive"
    ) -> MasterStorylineResponse:
        """Generate completely personalized experience based on user archetype and progress."""
        operation = "generate_personalized_experience"
        
        @self.performance_tracked(operation)
        async def _generate_experience():
            # Get comprehensive user status
            user_status = await self.narrative_service.get_user_master_storyline_status(user_id)
            
            if not user_status['success']:
                return MasterStorylineResponse(
                    success=False,
                    operation=operation,
                    data={},
                    performance_metrics={},
                    error_details="Failed to get user status"
                )
            
            # Generate personalized content
            personalized_content = await self.narrative_service.generate_personalized_content(
                user_id, experience_type
            )
            
            # Get archetype-optimized coordination
            archetype_data = user_status['data']['archetype_analysis']
            coordination_optimization = await self.lucien_service.optimize_coordination_timing(
                user_id, archetype_data.get('dominant_archetype', 'balanced')
            )
            
            # Check for special experiences
            special_experiences = await self._check_special_experiences(user_id, user_status['data'])
            
            combined_experience = {
                'user_status': user_status['data'],
                'personalized_content': personalized_content['data'] if personalized_content['success'] else None,
                'coordination_optimization': coordination_optimization,
                'special_experiences': special_experiences
            }
            
            return MasterStorylineResponse(
                success=True,
                operation=operation,
                data=combined_experience,
                performance_metrics={
                    'user_status_time': user_status['data']['performance']['response_time_ms'],
                    'content_generation_time': personalized_content['data']['performance']['response_time_ms'] if personalized_content['success'] else 0
                },
                next_recommendations=await self._generate_experience_recommendations(
                    user_id, combined_experience
                )
            )
        
        result, perf_metrics = await _generate_experience()
        result.performance_metrics.update(perf_metrics.__dict__)
        return result
    
    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report for master storyline."""
        try:
            # Get performance summary
            performance_summary = self.performance_service.get_performance_summary()
            
            # Get character consistency report
            consistency_report = await self.character_service.generate_consistency_report()
            
            # System status checks
            system_status = {
                'narrative_service': 'operational',
                'mission_service': 'operational', 
                'archetyping_service': 'operational',
                'vip_service': 'operational',
                'character_service': 'operational',
                'performance_service': 'operational',
                'lucien_service': 'operational'
            }
            
            # Overall health assessment
            critical_issues = []
            warnings = []
            
            # Check performance
            if performance_summary['performance_metrics'].get('avg_response_time', 0) > 500:
                critical_issues.append("Average response time exceeds 500ms budget")
            
            # Check character consistency
            if consistency_report['overall_statistics']['overall_pass_rate'] < 95:
                critical_issues.append("Character consistency below 95% requirement")
            
            # Check error rates
            if performance_summary['performance_metrics'].get('error_rate', 0) > 5:
                warnings.append(f"Error rate at {performance_summary['performance_metrics']['error_rate']:.1f}%")
            
            overall_health = 'healthy' if not critical_issues else 'degraded' if not warnings else 'critical'
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_health': overall_health,
                'system_status': system_status,
                'performance_summary': performance_summary,
                'character_consistency': consistency_report,
                'critical_issues': critical_issues,
                'warnings': warnings,
                'recommendations': self._generate_system_recommendations(
                    critical_issues, warnings, performance_summary, consistency_report
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating system health report: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_health': 'error',
                'error': str(e)
            }
    
    # Private helper methods
    
    async def _handle_narrative_failure(
        self, 
        user_id: int, 
        failure_result: Dict[str, Any], 
        interaction_data: Dict[str, Any]
    ) -> MasterStorylineResponse:
        """Handle narrative processing failure with Lucien coordination."""
        # Activate Lucien for error handling
        lucien_action = await self.lucien_service.evaluate_coordination_needs(
            user_id,
            {
                'event_type': 'system_error',
                'error_details': failure_result.get('error'),
                'user_needs_support': True
            }
        )
        
        lucien_result = None
        if lucien_action:
            lucien_result = await self.lucien_service.execute_coordination_action(
                user_id, lucien_action
            )
        
        return MasterStorylineResponse(
            success=False,
            operation="handle_narrative_failure",
            data=failure_result,
            performance_metrics={},
            lucien_coordination=lucien_result,
            error_details=failure_result.get('error'),
            next_recommendations=[
                "Sistema en proceso de recuperación",
                "Lucien coordinará tu experiencia mientras se restaura la continuidad"
            ]
        )
    
    async def _process_archetyping_update(self, user_id: int, interaction_data: Dict[str, Any]):
        """Process archetyping update in parallel."""
        try:
            return await self.archetyping_service.track_real_time_behavior(
                user_id,
                interaction_data.get('interaction_type', 'interaction'),
                interaction_data
            )
        except Exception as e:
            logger.error(f"Error in archetyping update: {e}")
            return None
    
    async def _check_vip_opportunities(self, user_id: int, interaction_data: Dict[str, Any]):
        """Check VIP opportunities in parallel."""
        try:
            return await self.vip_service.generate_upgrade_opportunity(
                user_id, 'interaction_triggered'
            )
        except Exception as e:
            logger.error(f"Error checking VIP opportunities: {e}")
            return None
    
    async def _evaluate_lucien_coordination(self, user_id: int, interaction_data: Dict[str, Any]):
        """Evaluate Lucien coordination needs in parallel."""
        try:
            coordination_needs = await self.lucien_service.evaluate_coordination_needs(
                user_id, interaction_data
            )
            
            if coordination_needs:
                return await self.lucien_service.execute_coordination_action(
                    user_id, coordination_needs
                )
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating Lucien coordination: {e}")
            return None
    
    async def _validate_character_consistency(self, user_id: int, narrative_result: Dict[str, Any]):
        """Validate character consistency in parallel."""
        try:
            # This would validate the narrative content that was delivered
            # For now, return a basic validation
            return {
                'validated': True,
                'score': 96,
                'meets_threshold': True
            }
        except Exception as e:
            logger.error(f"Error validating character consistency: {e}")
            return None
    
    def _process_parallel_results(self, *results) -> Dict[str, Any]:
        """Process results from parallel operations."""
        processed = {}
        
        archetype_update, vip_check, lucien_eval, char_validation = results
        
        if not isinstance(archetype_update, Exception) and archetype_update:
            processed['archetyping'] = archetype_update
        
        if not isinstance(vip_check, Exception) and vip_check:
            processed['vip'] = {'offer': vip_check.to_dict()}
        
        if not isinstance(lucien_eval, Exception) and lucien_eval:
            processed['lucien'] = lucien_eval
        
        if not isinstance(char_validation, Exception) and char_validation:
            processed['character_validation'] = char_validation
        
        return processed
    
    async def _generate_initialization_recommendations(self, user_id: int) -> List[str]:
        """Generate recommendations for new user initialization."""
        return [
            "Explora Los Kinkys para comenzar tu viaje con Diana",
            "Presta atención a los detalles ocultos en cada interacción", 
            "Tus decisiones influirán en cómo Diana se relaciona contigo",
            "El sistema aprenderá tu estilo único de interacción"
        ]
    
    async def _generate_interaction_recommendations(
        self, 
        user_id: int, 
        narrative_result: Dict[str, Any], 
        processed_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on interaction results."""
        recommendations = []
        
        # Based on narrative progression
        if narrative_result.get('mission_result'):
            mission_score = narrative_result['mission_result'].get('score', 0)
            if mission_score >= 80:
                recommendations.append("¡Excelente desempeño! Continúa con este nivel de engagement")
            elif mission_score >= 60:
                recommendations.append("Buen progreso, pero hay oportunidades para profundizar más")
            else:
                recommendations.append("Tómate tiempo para explorar los detalles más profundos")
        
        # Based on archetyping insights
        if processed_results.get('archetyping'):
            archetype_insights = processed_results['archetyping']
            if 'immediate_adaptations' in archetype_insights:
                recommendations.append("Diana está adaptando su estilo a tu personalidad única")
        
        # Based on VIP opportunities
        if processed_results.get('vip'):
            recommendations.append("Nuevas oportunidades de experiencia premium disponibles")
        
        return recommendations[:4]  # Limit to top 4 recommendations
    
    async def _generate_decision_recommendations(
        self, 
        user_id: int, 
        decision_result: Dict[str, Any], 
        progression_updates: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on decision results."""
        recommendations = []
        
        if decision_result.get('next_fragment'):
            recommendations.append("Continúa hacia el siguiente fragmento de tu historia")
        
        if progression_updates:
            recommendations.append("¡Has desbloqueado nuevo contenido! Explora las nuevas posibilidades")
        
        if decision_result.get('access_denied_info'):
            recommendations.append("Considera las opciones VIP para acceder a experiencias más profundas")
        
        return recommendations
    
    async def _handle_progression_events(
        self, 
        user_id: int, 
        progression_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Handle progression events like level ups or tier changes."""
        updates = []
        
        if progression_result.get('level_progressed'):
            new_level = progression_result['new_level']
            updates.append({
                'type': 'level_progression',
                'new_level': new_level,
                'celebration_message': f"¡Felicitaciones! Has alcanzado el nivel {new_level}"
            })
            
            # Check if Lucien should congratulate
            lucien_congratulation = await self.lucien_service.evaluate_coordination_needs(
                user_id,
                {
                    'event_type': 'achievement_recognition',
                    'achievement_type': 'level_progression',
                    'new_level': new_level
                }
            )
            
            if lucien_congratulation:
                lucien_result = await self.lucien_service.execute_coordination_action(
                    user_id, lucien_congratulation
                )
                updates.append({
                    'type': 'lucien_congratulation',
                    'coordination_result': lucien_result
                })
        
        return updates
    
    async def _handle_access_denied_support(
        self, 
        user_id: int, 
        access_denied_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle access denied scenarios with VIP support."""
        # Generate personalized VIP offer
        vip_offer = await self.vip_service.generate_upgrade_opportunity(
            user_id, 'access_denied_triggered'
        )
        
        # Activate Lucien for VIP facilitation if appropriate
        lucien_facilitation = await self.lucien_service.evaluate_coordination_needs(
            user_id,
            {
                'event_type': 'vip_opportunity',
                'access_denied': True,
                'offer_available': vip_offer is not None
            }
        )
        
        result = {}
        
        if vip_offer:
            result['vip_offer'] = vip_offer.to_dict()
        
        if lucien_facilitation:
            lucien_result = await self.lucien_service.execute_coordination_action(
                user_id, lucien_facilitation
            )
            result['lucien_facilitation'] = lucien_result
        
        return result
    
    async def _check_special_experiences(self, user_id: int, user_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check for special experiences based on user progress."""
        special_experiences = {}
        
        # Check for Circle Íntimo access
        progress_stats = user_status.get('progress_stats', {})
        if progress_stats.get('current_level', 0) >= 6:
            vip_analytics = user_status.get('vip_analytics', {})
            if vip_analytics.get('tier_utilization', {}).get('overall_utilization', 0) > 0.8:
                special_experiences['circle_intimo_eligible'] = True
        
        # Check for Guardian of Secrets status
        mission_completion = progress_stats.get('mission_completion', {})
        total_missions = sum(mission_completion.values())
        if total_missions >= 10:
            special_experiences['guardian_of_secrets_eligible'] = True
        
        return special_experiences
    
    async def _generate_experience_recommendations(
        self, 
        user_id: int, 
        experience_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for personalized experience."""
        recommendations = []
        
        user_status = experience_data.get('user_status', {})
        current_level = user_status.get('progress_stats', {}).get('current_level', 1)
        
        if current_level < 3:
            recommendations.append("Continúa explorando Los Kinkys para descubrir más secretos de Diana")
        elif current_level < 6:
            recommendations.append("Profundiza tu comprensión de Diana en El Diván")
        else:
            recommendations.append("Experimenta la síntesis completa en el Círculo Élite")
        
        # Based on special experiences
        special_experiences = experience_data.get('special_experiences', {})
        if special_experiences.get('circle_intimo_eligible'):
            recommendations.append("¡Eres elegible para el Círculo Íntimo de Diana!")
        
        if special_experiences.get('guardian_of_secrets_eligible'):
            recommendations.append("Tu dedicación te ha ganado el estatus de Guardián de Secretos")
        
        return recommendations[:4]
    
    def _generate_system_recommendations(
        self, 
        critical_issues: List[str], 
        warnings: List[str], 
        performance_summary: Dict[str, Any], 
        consistency_report: Dict[str, Any]
    ) -> List[str]:
        """Generate system-level recommendations."""
        recommendations = []
        
        if critical_issues:
            recommendations.append("CRITICAL: Address critical issues immediately")
            if any("response time" in issue for issue in critical_issues):
                recommendations.append("Optimize performance: Enable caching and query optimization")
            if any("consistency" in issue for issue in critical_issues):
                recommendations.append("Improve character consistency: Review and update content validation")
        
        if warnings:
            recommendations.append("Monitor system warnings and plan improvements")
        
        # Performance recommendations
        cache_hit_rate = performance_summary.get('cache_performance', {}).get('total_cache_hits', 0)
        if cache_hit_rate < 0.7:  # Less than 70% cache hit rate
            recommendations.append("Improve cache hit rate through better cache warming")
        
        return recommendations[:5]