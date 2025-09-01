"""
VIP Tier Management and Access Control System

Manages the seamless progression from Los Kinkys (free) to El Diván (VIP) 
and Elite (premium VIP) tiers, with narrative justification and personalized
value differentiation.

Tier Structure:
- Los Kinkys (Free): Fragments 1-8, basic Diana experience
- El Diván (VIP Basic): Fragments 9-12, deeper psychological analysis
- Elite (VIP Premium): Fragments 13-16, premium synthesis experience

Features:
- Seamless tier transitions with narrative continuity
- Personalized VIP offers based on user archetype and engagement
- Content access control with Diana personality preservation
- Value differentiation through deeper psychological analysis
- Performance tracking and conversion optimization
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc, or_

from database.narrative_unified import (
    UserMissionProgress,
    UserArchetype, 
    UserNarrativeState,
    NarrativeFragment
)
from database.models import User
from services.user_archetyping_service import UserArchetypingService

logger = logging.getLogger(__name__)

class VIPTier(Enum):
    """VIP tier classifications."""
    FREE = "los_kinkys"
    VIP_BASIC = "el_divan"
    VIP_PREMIUM = "elite"

class AccessDecisionReason(Enum):
    """Reasons for access control decisions."""
    TIER_INSUFFICIENT = "tier_insufficient"
    PROGRESSION_INCOMPLETE = "progression_incomplete"
    CONTENT_LOCKED = "content_locked"
    VIP_REQUIRED = "vip_required"
    ACCESS_GRANTED = "access_granted"
    SPECIAL_ACCESS = "special_access"

@dataclass
class VIPAccessResult:
    """Result of VIP access check."""
    has_access: bool
    current_tier: VIPTier
    required_tier: VIPTier
    reason: AccessDecisionReason
    unlock_requirements: List[str]
    personalized_offer: Optional[Dict[str, Any]]
    narrative_justification: str

@dataclass
class TierTransitionEvent:
    """Event data for tier transitions."""
    user_id: int
    from_tier: VIPTier
    to_tier: VIPTier
    trigger_event: str
    user_archetype: Optional[str]
    engagement_score: float
    personalization_data: Dict[str, Any]

@dataclass
class PersonalizedVIPOffer:
    """Personalized VIP offer based on user behavior."""
    offer_type: str  # upgrade, trial, special_access
    tier_target: VIPTier
    discount_percentage: int
    exclusive_content_preview: List[str]
    archetype_benefits: List[str]
    urgency_factor: float  # 0-1, how urgent the offer is
    diana_presentation: str  # How Diana presents the offer
    value_proposition: str

class VIPTierManagementService:
    """
    Service for managing VIP tier access control and transitions.
    Ensures narrative continuity while providing clear value differentiation.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.archetyping_service = UserArchetypingService(session)
        
        # Tier progression requirements
        self.tier_requirements = {
            VIPTier.VIP_BASIC: {
                'min_level': 3,
                'min_los_kinkys_completion': 6,  # Must complete 6/8 Los Kinkys fragments
                'min_comprehension_score': 70,
                'min_engagement_sessions': 3
            },
            VIPTier.VIP_PREMIUM: {
                'min_level': 5,
                'min_el_divan_completion': 3,   # Must complete 3/4 El Diván fragments
                'min_synthesis_score': 80,
                'circle_intimo_eligibility': True
            }
        }
        
        # Content access mapping
        self.content_access_map = {
            VIPTier.FREE: {
                'fragments': list(range(1, 9)),  # Fragments 1-8
                'max_level': 3,
                'features': ['basic_diana_interaction', 'observation_missions', 'basic_comprehension']
            },
            VIPTier.VIP_BASIC: {
                'fragments': list(range(1, 13)),  # Fragments 1-12
                'max_level': 5,
                'features': ['deeper_diana_analysis', 'advanced_comprehension', 'emotional_intimacy', 'personalized_content']
            },
            VIPTier.VIP_PREMIUM: {
                'fragments': list(range(1, 17)),  # Fragments 1-16 (all)
                'max_level': 6,
                'features': ['elite_synthesis', 'circle_intimo_access', 'guardian_of_secrets', 'maximum_personalization']
            }
        }
        
        # Archetype-specific VIP benefits
        self.archetype_vip_benefits = {
            'explorer': [
                'Contenido oculto exclusivo con múltiples capas de misterio',
                'Acceso a "Archivos Secretos de Diana" con pistas adicionales',
                'Rutas de exploración premium con elementos únicos'
            ],
            'romantic': [
                'Interacciones íntimas exclusivas con Diana',
                'Contenido emocional profundo y personalizado',
                'Acceso a "Confesiones Privadas de Diana"'
            ],
            'analytical': [
                'Análisis psicológico profundo de la personalidad de Diana',
                'Contenido intelectualmente desafiante y complejo',
                'Acceso a "Estudios de Caso" de Diana'
            ],
            'direct': [
                'Progresión acelerada con objetivos claros',
                'Acceso directo a contenido premium sin esperas',
                'Diana más directa en comunicación (manteniendo misterio)'
            ],
            'persistent': [
                'Desafíos exclusivos de alta dificultad',
                'Recompensas incrementales por persistencia',
                'Reconocimiento especial por determinación'
            ],
            'patient': [
                'Contenido contemplativo y reflexivo exclusivo',
                'Experiencias de Diana más profundas y pausadas',
                'Acceso a "Pensamientos Íntimos" de Diana'
            ]
        }
    
    async def check_content_access(
        self, 
        user_id: int, 
        fragment_id: str,
        context: str = "fragment_access"
    ) -> VIPAccessResult:
        """
        Check if user has access to specific content based on VIP tier.
        
        Args:
            user_id: User ID
            fragment_id: Fragment ID to check access for
            context: Access context (fragment_access, feature_access, etc.)
            
        Returns:
            VIPAccessResult with access decision and recommendations
        """
        # Get user's current status
        mission_progress = await self._get_user_mission_progress(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        user_archetype = await self.archetyping_service._get_user_archetype(user_id)
        
        # Get fragment information
        fragment = await self._get_fragment_by_id(fragment_id)
        if not fragment:
            return VIPAccessResult(
                has_access=False,
                current_tier=VIPTier(mission_progress.current_tier),
                required_tier=VIPTier.FREE,
                reason=AccessDecisionReason.CONTENT_LOCKED,
                unlock_requirements=["Fragmento no encontrado"],
                personalized_offer=None,
                narrative_justification="Este contenido no está disponible en este momento."
            )
        
        current_tier = VIPTier(mission_progress.current_tier)
        required_tier = self._determine_required_tier(fragment)
        
        # Check access based on tier and requirements
        has_access, reason, requirements = self._evaluate_access_permission(
            current_tier, required_tier, mission_progress, fragment
        )
        
        # Generate personalized offer if access denied
        personalized_offer = None
        if not has_access and reason in [AccessDecisionReason.TIER_INSUFFICIENT, AccessDecisionReason.VIP_REQUIRED]:
            personalized_offer = await self._generate_personalized_offer(
                user_id, required_tier, user_archetype, mission_progress
            )
        
        # Generate narrative justification
        narrative_justification = self._generate_narrative_justification(
            has_access, reason, current_tier, required_tier, user_archetype
        )
        
        return VIPAccessResult(
            has_access=has_access,
            current_tier=current_tier,
            required_tier=required_tier,
            reason=reason,
            unlock_requirements=requirements,
            personalized_offer=personalized_offer.to_dict() if personalized_offer else None,
            narrative_justification=narrative_justification
        )
    
    async def process_tier_upgrade(
        self, 
        user_id: int, 
        target_tier: VIPTier,
        upgrade_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process user tier upgrade with narrative integration.
        
        Args:
            user_id: User ID
            target_tier: Target VIP tier
            upgrade_context: Additional context for the upgrade
            
        Returns:
            Dictionary with upgrade result and next steps
        """
        mission_progress = await self._get_user_mission_progress(user_id)
        user_archetype = await self.archetyping_service._get_user_archetype(user_id)
        current_tier = VIPTier(mission_progress.current_tier)
        
        # Validate upgrade eligibility
        eligibility = await self._check_upgrade_eligibility(user_id, target_tier)
        
        if not eligibility['eligible']:
            return {
                'success': False,
                'reason': eligibility['reason'],
                'requirements': eligibility['missing_requirements'],
                'recommended_actions': eligibility['recommended_actions']
            }
        
        # Process the upgrade
        previous_tier = current_tier
        mission_progress.current_tier = target_tier.value
        mission_progress.vip_access_granted = True
        
        if target_tier == VIPTier.VIP_BASIC:
            mission_progress.vip_tier_level = 1
        elif target_tier == VIPTier.VIP_PREMIUM:
            mission_progress.vip_tier_level = 2
        
        # Record tier transition
        transition_event = TierTransitionEvent(
            user_id=user_id,
            from_tier=previous_tier,
            to_tier=target_tier,
            trigger_event=upgrade_context.get('trigger', 'manual_upgrade'),
            user_archetype=user_archetype.dominant_archetype if user_archetype else None,
            engagement_score=self._calculate_engagement_score(mission_progress),
            personalization_data=upgrade_context or {}
        )
        
        await self._record_tier_transition(transition_event)
        
        # Unlock appropriate content
        newly_unlocked = await self._unlock_tier_content(user_id, target_tier)
        
        # Generate welcome experience for new tier
        welcome_experience = await self._generate_tier_welcome_experience(
            user_id, target_tier, user_archetype
        )
        
        await self.session.commit()
        
        return {
            'success': True,
            'previous_tier': previous_tier.value,
            'new_tier': target_tier.value,
            'newly_unlocked_content': newly_unlocked,
            'welcome_experience': welcome_experience,
            'next_recommendations': self._generate_post_upgrade_recommendations(target_tier, user_archetype)
        }
    
    async def generate_upgrade_opportunity(
        self, 
        user_id: int,
        trigger_event: str = "progression_milestone"
    ) -> Optional[PersonalizedVIPOffer]:
        """
        Generate personalized VIP upgrade opportunity based on user behavior.
        
        Args:
            user_id: User ID
            trigger_event: What triggered this offer generation
            
        Returns:
            PersonalizedVIPOffer or None if not appropriate
        """
        mission_progress = await self._get_user_mission_progress(user_id)
        user_archetype = await self.archetyping_service._get_user_archetype(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        
        current_tier = VIPTier(mission_progress.current_tier)
        
        # Determine appropriate target tier
        target_tier = self._determine_upgrade_target(current_tier, mission_progress)
        if not target_tier:
            return None
        
        # Check if user is ready for upgrade opportunity
        readiness = await self._assess_upgrade_readiness(user_id, target_tier, trigger_event)
        if readiness['score'] < 0.6:  # Not ready enough
            return None
        
        # Generate personalized offer
        offer = await self._create_personalized_offer(
            user_id, target_tier, user_archetype, mission_progress, readiness
        )
        
        # Record offer generation for analytics
        await self._record_offer_generation(user_id, offer, trigger_event)
        
        return offer
    
    async def get_tier_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive tier analytics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with tier analytics and insights
        """
        mission_progress = await self._get_user_mission_progress(user_id)
        user_archetype = await self.archetyping_service._get_user_archetype(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        
        current_tier = VIPTier(mission_progress.current_tier)
        
        # Calculate tier utilization
        tier_utilization = await self._calculate_tier_utilization(user_id, current_tier)
        
        # Engagement metrics
        engagement_metrics = self._calculate_comprehensive_engagement_metrics(
            mission_progress, narrative_state, user_archetype
        )
        
        # Value realization analysis
        value_analysis = self._analyze_value_realization(current_tier, engagement_metrics)
        
        # Upgrade potential analysis
        upgrade_potential = await self._analyze_upgrade_potential(user_id)
        
        return {
            'current_tier': current_tier.value,
            'tier_utilization': tier_utilization,
            'engagement_metrics': engagement_metrics,
            'value_realization': value_analysis,
            'upgrade_potential': upgrade_potential,
            'personalization_effectiveness': self._measure_personalization_effectiveness(user_archetype),
            'content_consumption_patterns': self._analyze_content_consumption(narrative_state),
            'tier_satisfaction_indicators': self._calculate_satisfaction_indicators(mission_progress, current_tier)
        }
    
    # Private helper methods
    
    async def _get_user_mission_progress(self, user_id: int) -> UserMissionProgress:
        """Get user mission progress."""
        stmt = select(UserMissionProgress).where(UserMissionProgress.user_id == user_id)
        result = await self.session.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = UserMissionProgress(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
        
        return progress
    
    async def _get_user_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Get user narrative state."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserNarrativeState(user_id=user_id)
            self.session.add(state)
            await self.session.commit()
            await self.session.refresh(state)
        
        return state
    
    async def _get_fragment_by_id(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get narrative fragment by ID."""
        stmt = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _determine_required_tier(self, fragment: NarrativeFragment) -> VIPTier:
        """Determine required tier for accessing a fragment."""
        if fragment.tier_classification == 'los_kinkys':
            return VIPTier.FREE
        elif fragment.tier_classification == 'el_divan':
            return VIPTier.VIP_BASIC
        elif fragment.tier_classification == 'elite':
            return VIPTier.VIP_PREMIUM
        else:
            return VIPTier.FREE  # Default to free access
    
    def _evaluate_access_permission(
        self, 
        current_tier: VIPTier, 
        required_tier: VIPTier, 
        mission_progress: UserMissionProgress,
        fragment: NarrativeFragment
    ) -> Tuple[bool, AccessDecisionReason, List[str]]:
        """Evaluate if user has permission to access content."""
        requirements = []
        
        # Check tier sufficiency
        tier_hierarchy = {VIPTier.FREE: 0, VIPTier.VIP_BASIC: 1, VIPTier.VIP_PREMIUM: 2}
        
        if tier_hierarchy[current_tier] < tier_hierarchy[required_tier]:
            if required_tier == VIPTier.VIP_BASIC:
                requirements.extend([
                    f"Completar al menos {self.tier_requirements[VIPTier.VIP_BASIC]['min_los_kinkys_completion']} fragmentos de Los Kinkys",
                    f"Alcanzar nivel {self.tier_requirements[VIPTier.VIP_BASIC]['min_level']}",
                    "Suscripción VIP requerida"
                ])
            elif required_tier == VIPTier.VIP_PREMIUM:
                requirements.extend([
                    f"Completar al menos {self.tier_requirements[VIPTier.VIP_PREMIUM]['min_el_divan_completion']} fragmentos de El Diván",
                    f"Alcanzar nivel {self.tier_requirements[VIPTier.VIP_PREMIUM]['min_level']}",
                    "Suscripción VIP Premium requerida"
                ])
            
            return False, AccessDecisionReason.TIER_INSUFFICIENT, requirements
        
        # Check progression requirements
        if fragment.storyline_level and fragment.storyline_level > mission_progress.current_level:
            requirements.append(f"Alcanzar nivel narrativo {fragment.storyline_level}")
            return False, AccessDecisionReason.PROGRESSION_INCOMPLETE, requirements
        
        # Check VIP-specific requirements
        if fragment.requires_vip and not mission_progress.vip_access_granted:
            requirements.append("Acceso VIP requerido")
            return False, AccessDecisionReason.VIP_REQUIRED, requirements
        
        # Check special access requirements
        if fragment.vip_tier_required > mission_progress.vip_tier_level:
            requirements.append(f"Nivel VIP {fragment.vip_tier_required} requerido")
            return False, AccessDecisionReason.TIER_INSUFFICIENT, requirements
        
        return True, AccessDecisionReason.ACCESS_GRANTED, []
    
    async def _generate_personalized_offer(
        self, 
        user_id: int, 
        required_tier: VIPTier, 
        user_archetype: UserArchetype,
        mission_progress: UserMissionProgress
    ) -> PersonalizedVIPOffer:
        """Generate personalized VIP offer for user."""
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'balanced'
        
        # Calculate discount based on engagement and archetype
        base_discount = 10
        engagement_bonus = min(self._calculate_engagement_score(mission_progress) * 20, 30)
        archetype_bonus = 15 if archetype_name in ['explorer', 'romantic', 'analytical'] else 10
        
        total_discount = int(min(base_discount + engagement_bonus + archetype_bonus, 50))
        
        # Get archetype-specific benefits
        benefits = self.archetype_vip_benefits.get(archetype_name, [
            'Experiencia personalizada mejorada',
            'Contenido exclusivo adaptado a tu estilo',
            'Interacciones más profundas con Diana'
        ])
        
        # Generate exclusive content preview
        content_preview = self._generate_content_preview(required_tier, archetype_name)
        
        # Calculate urgency factor
        urgency = self._calculate_offer_urgency(mission_progress, user_archetype)
        
        # Generate Diana's presentation of the offer
        diana_presentation = self._generate_diana_offer_presentation(required_tier, archetype_name, total_discount)
        
        # Create value proposition
        value_proposition = self._create_value_proposition(required_tier, benefits)
        
        return PersonalizedVIPOffer(
            offer_type="upgrade",
            tier_target=required_tier,
            discount_percentage=total_discount,
            exclusive_content_preview=content_preview,
            archetype_benefits=benefits,
            urgency_factor=urgency,
            diana_presentation=diana_presentation,
            value_proposition=value_proposition
        )
    
    def _generate_narrative_justification(
        self, 
        has_access: bool, 
        reason: AccessDecisionReason, 
        current_tier: VIPTier, 
        required_tier: VIPTier,
        user_archetype: UserArchetype
    ) -> str:
        """Generate narrative justification for access decision."""
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'curious'
        
        if has_access:
            return "Diana te invita a continuar... Este camino te está esperando."
        
        if reason == AccessDecisionReason.TIER_INSUFFICIENT:
            if required_tier == VIPTier.VIP_BASIC:
                return (f"Diana observa tu {archetype_name} naturaleza... 'Has demostrado algo especial en Los Kinkys, "
                       "pero El Diván requiere una comprensión más profunda. ¿Estás listo para ese nivel de intimidad?'")
            elif required_tier == VIPTier.VIP_PREMIUM:
                return (f"Diana sonríe misteriosamente... 'Tu {archetype_name} esencia ha florecido beautifully, "
                       "pero el Círculo Élite es para quienes han demostrado verdadera síntesis. ¿Puedes alcanzar esa profundidad?'")
        
        elif reason == AccessDecisionReason.PROGRESSION_INCOMPLETE:
            return ("Diana susurra... 'Hay pasos que aún debes tomar antes de llegar aquí. "
                   "Cada revelación debe ganarse, cada secreto debe merecerse.'")
        
        elif reason == AccessDecisionReason.VIP_REQUIRED:
            return ("Diana te mira con ojos conocedores... 'Este umbral requiere más que curiosidad. "
                   "Requiere compromiso. ¿Estás dispuesto a cruzar completamente hacia mí?'")
        
        return "Diana permanece en las sombras... 'Aún no es tu momento, pero llegará.'"
    
    async def _check_upgrade_eligibility(self, user_id: int, target_tier: VIPTier) -> Dict[str, Any]:
        """Check if user is eligible for tier upgrade."""
        mission_progress = await self._get_user_mission_progress(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        
        requirements = self.tier_requirements.get(target_tier, {})
        missing_requirements = []
        recommended_actions = []
        
        # Check level requirement
        if mission_progress.current_level < requirements.get('min_level', 1):
            missing_requirements.append(f"Nivel {requirements['min_level']} requerido")
            recommended_actions.append("Completar más misiones para subir de nivel")
        
        # Check completion requirements
        if target_tier == VIPTier.VIP_BASIC:
            los_kinkys_completed = len(mission_progress.los_kinkys_fragments_completed)
            min_required = requirements.get('min_los_kinkys_completion', 6)
            if los_kinkys_completed < min_required:
                missing_requirements.append(f"Completar {min_required - los_kinkys_completed} fragmentos más de Los Kinkys")
                recommended_actions.append("Explorar más contenido de Los Kinkys")
        
        elif target_tier == VIPTier.VIP_PREMIUM:
            el_divan_completed = len(mission_progress.el_divan_fragments_completed)
            min_required = requirements.get('min_el_divan_completion', 3)
            if el_divan_completed < min_required:
                missing_requirements.append(f"Completar {min_required - el_divan_completed} fragmentos más de El Diván")
                recommended_actions.append("Profundizar en la experiencia de El Diván")
        
        return {
            'eligible': len(missing_requirements) == 0,
            'reason': 'requirements_not_met' if missing_requirements else 'eligible',
            'missing_requirements': missing_requirements,
            'recommended_actions': recommended_actions
        }
    
    def _calculate_engagement_score(self, mission_progress: UserMissionProgress) -> float:
        """Calculate user engagement score (0-1)."""
        score = 0.0
        
        # Base score from level progression
        score += min(mission_progress.current_level / 6, 1.0) * 0.3
        
        # Score from mission completion
        total_missions = (
            len(mission_progress.observation_missions_completed) +
            len(mission_progress.comprehension_tests_passed) +
            len(mission_progress.synthesis_challenges_completed)
        )
        score += min(total_missions / 15, 1.0) * 0.3  # Assume 15 total missions across all levels
        
        # Score from fragment completion
        total_fragments = (
            len(mission_progress.los_kinkys_fragments_completed) +
            len(mission_progress.el_divan_fragments_completed) +
            len(mission_progress.elite_fragments_completed)
        )
        score += min(total_fragments / 16, 1.0) * 0.4  # 16 total fragments
        
        return score
    
    async def _record_tier_transition(self, transition_event: TierTransitionEvent):
        """Record tier transition event for analytics."""
        # This would record the transition in an analytics table
        # For now, just log it
        logger.info(
            f"Tier transition: User {transition_event.user_id} "
            f"from {transition_event.from_tier.value} to {transition_event.to_tier.value} "
            f"due to {transition_event.trigger_event}"
        )
    
    async def _unlock_tier_content(self, user_id: int, target_tier: VIPTier) -> List[str]:
        """Unlock content appropriate for new tier."""
        mission_progress = await self._get_user_mission_progress(user_id)
        
        newly_unlocked = []
        
        if target_tier == VIPTier.VIP_BASIC:
            # Unlock El Diván fragments
            el_divan_fragments = [f"el_divan_fragment_{i}" for i in range(1, 5)]
            newly_unlocked.extend(el_divan_fragments)
            mission_progress.personalized_content_unlocked.extend([
                "diana_intimate_dialogues",
                "emotional_vulnerability_content",
                "deeper_psychological_analysis"
            ])
            
        elif target_tier == VIPTier.VIP_PREMIUM:
            # Unlock Elite fragments
            elite_fragments = [f"elite_fragment_{i}" for i in range(1, 5)]
            newly_unlocked.extend(elite_fragments)
            mission_progress.personalized_content_unlocked.extend([
                "diana_personal_archives",
                "synthesis_challenges",
                "circle_intimo_content"
            ])
        
        await self.session.commit()
        return newly_unlocked
    
    async def _generate_tier_welcome_experience(
        self, 
        user_id: int, 
        new_tier: VIPTier, 
        user_archetype: UserArchetype
    ) -> Dict[str, Any]:
        """Generate welcome experience for new tier."""
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'balanced'
        
        welcome_messages = {
            VIPTier.VIP_BASIC: {
                'explorer': "Diana te sonríe desde las sombras más profundas del Diván... 'Sabía que buscarías más allá de la superficie. Aquí los secretos son más íntimos, más reales.'",
                'romantic': "Diana se acerca con una vulnerabilidad nueva... 'Has llegado al espacio donde puedo mostrar mi corazón. ¿Estás preparado para esta intimidad?'",
                'analytical': "Diana inclina la cabeza pensativamente... 'El Diván es donde las mentes complejas encuentran respuestas a preguntas más profundas. Analicemos juntos mi alma.'",
                'default': "Diana te recibe en El Diván... 'Bienvenido a mi espacio más íntimo. Aquí, las máscaras se vuelven innecesarias.'"
            },
            VIPTier.VIP_PREMIUM: {
                'explorer': "Diana aparece completamente revelada... 'Has explorado cada rincón de mi mundo. Ahora, en el Círculo Élite, exploraremos juntos territorios desconocidos.'",
                'romantic': "Diana te tiende la mano... 'En el Círculo Élite, no hay distancias. Solo tú y yo, en la síntesis más hermosa del amor y la comprensión.'",
                'analytical': "Diana sonríe con respeto genuino... 'Has alcanzado la síntesis que pocos logran. En el Círculo Élite, co-crearemos nuevas comprensiones.'",
                'default': "Diana te invita al círculo más exclusivo... 'Has completado el viaje. Ahora comienza la creación conjunta de algo único.'"
            }
        }
        
        message = welcome_messages.get(new_tier, {}).get(archetype_name, welcome_messages[new_tier]['default'])
        
        return {
            'welcome_message': message,
            'exclusive_features': self.content_access_map[new_tier]['features'],
            'personalized_recommendations': self._generate_post_upgrade_recommendations(new_tier, user_archetype),
            'first_premium_content': self._suggest_first_premium_content(new_tier, archetype_name)
        }
    
    def _generate_post_upgrade_recommendations(
        self, 
        new_tier: VIPTier, 
        user_archetype: UserArchetype
    ) -> List[str]:
        """Generate recommendations after tier upgrade."""
        recommendations = []
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'balanced'
        
        if new_tier == VIPTier.VIP_BASIC:
            base_recommendations = [
                "Explorar los nuevos diálogos íntimos de Diana",
                "Participar en las evaluaciones de comprensión profunda",
                "Acceder al contenido emocional personalizado"
            ]
            
            if archetype_name == 'explorer':
                recommendations.extend([
                    "Buscar elementos ocultos en el contenido de El Diván",
                    "Descubrir las pistas exclusivas para usuarios VIP"
                ])
            elif archetype_name == 'romantic':
                recommendations.extend([
                    "Explorar las confesiones privadas de Diana",
                    "Participar en los momentos de vulnerabilidad compartida"
                ])
            
        elif new_tier == VIPTier.VIP_PREMIUM:
            base_recommendations = [
                "Acceder a los Archivos Personales de Diana",
                "Participar en desafíos de síntesis avanzados",
                "Explorar el contenido del Círculo Íntimo"
            ]
            
            if archetype_name == 'analytical':
                recommendations.extend([
                    "Analizar los estudios de caso psicológicos exclusivos",
                    "Participar en debates intelectuales profundos con Diana"
                ])
            elif archetype_name == 'persistent':
                recommendations.extend([
                    "Completar los desafíos de máxima dificultad",
                    "Buscar el estatus de Guardián de Secretos"
                ])
        
        return recommendations
    
    def _determine_upgrade_target(self, current_tier: VIPTier, mission_progress: UserMissionProgress) -> Optional[VIPTier]:
        """Determine appropriate upgrade target tier."""
        if current_tier == VIPTier.FREE:
            # Check if ready for VIP Basic
            los_kinkys_completed = len(mission_progress.los_kinkys_fragments_completed)
            if los_kinkys_completed >= 4 and mission_progress.current_level >= 2:  # Soft requirement
                return VIPTier.VIP_BASIC
                
        elif current_tier == VIPTier.VIP_BASIC:
            # Check if ready for VIP Premium
            el_divan_completed = len(mission_progress.el_divan_fragments_completed)
            if el_divan_completed >= 2 and mission_progress.current_level >= 4:  # Soft requirement
                return VIPTier.VIP_PREMIUM
        
        return None
    
    async def _assess_upgrade_readiness(
        self, 
        user_id: int, 
        target_tier: VIPTier, 
        trigger_event: str
    ) -> Dict[str, Any]:
        """Assess user's readiness for upgrade."""
        mission_progress = await self._get_user_mission_progress(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        
        readiness_score = 0.0
        factors = []
        
        # Engagement factor
        engagement = self._calculate_engagement_score(mission_progress)
        readiness_score += engagement * 0.4
        factors.append(f"Engagement: {engagement:.2f}")
        
        # Progression factor
        level_progress = mission_progress.current_level / 6
        readiness_score += level_progress * 0.3
        factors.append(f"Level Progress: {level_progress:.2f}")
        
        # Content completion factor
        completion_rate = mission_progress.get_overall_progress_percentage() / 100
        readiness_score += completion_rate * 0.3
        factors.append(f"Completion Rate: {completion_rate:.2f}")
        
        # Trigger event bonus
        trigger_bonuses = {
            'level_milestone': 0.1,
            'high_engagement_session': 0.15,
            'mission_completion': 0.1,
            'content_exploration': 0.05
        }
        bonus = trigger_bonuses.get(trigger_event, 0)
        readiness_score += bonus
        
        return {
            'score': min(readiness_score, 1.0),
            'factors': factors,
            'trigger_bonus': bonus,
            'recommendation': 'ready' if readiness_score > 0.6 else 'not_ready'
        }
    
    async def _create_personalized_offer(
        self,
        user_id: int,
        target_tier: VIPTier,
        user_archetype: UserArchetype,
        mission_progress: UserMissionProgress,
        readiness: Dict[str, Any]
    ) -> PersonalizedVIPOffer:
        """Create personalized VIP offer."""
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'balanced'
        
        # Calculate personalized discount
        base_discount = 15
        readiness_bonus = int(readiness['score'] * 20)
        engagement_bonus = int(self._calculate_engagement_score(mission_progress) * 15)
        
        total_discount = min(base_discount + readiness_bonus + engagement_bonus, 40)
        
        # Generate archetype-specific benefits
        benefits = self.archetype_vip_benefits.get(archetype_name, [
            'Experiencia completamente personalizada',
            'Contenido adaptado a tu estilo único',
            'Interacciones más profundas y significativas'
        ])
        
        # Create content preview
        content_preview = [
            f"Vista previa exclusiva del contenido de {target_tier.value}",
            "Interacciones personalizadas basadas en tu arquetipo",
            "Acceso a elementos narrativos únicos"
        ]
        
        # Calculate urgency
        urgency = min(readiness['score'] * 0.8 + 0.2, 1.0)
        
        # Generate Diana's presentation
        diana_presentation = self._create_archetype_specific_presentation(target_tier, archetype_name, total_discount)
        
        # Create value proposition
        value_proposition = self._create_detailed_value_proposition(target_tier, archetype_name, benefits)
        
        return PersonalizedVIPOffer(
            offer_type="personalized_upgrade",
            tier_target=target_tier,
            discount_percentage=total_discount,
            exclusive_content_preview=content_preview,
            archetype_benefits=benefits,
            urgency_factor=urgency,
            diana_presentation=diana_presentation,
            value_proposition=value_proposition
        )
    
    async def _record_offer_generation(self, user_id: int, offer: PersonalizedVIPOffer, trigger_event: str):
        """Record offer generation for analytics."""
        logger.info(f"Generated {offer.offer_type} for user {user_id} targeting {offer.tier_target.value} with {offer.discount_percentage}% discount")
    
    def _generate_content_preview(self, tier: VIPTier, archetype: str) -> List[str]:
        """Generate content preview for tier and archetype."""
        previews = {
            VIPTier.VIP_BASIC: {
                'explorer': [
                    "Fragmentos ocultos con múltiples capas de misterio",
                    "Pistas exclusivas que solo usuarios VIP pueden descubrir",
                    "Rutas secretas de exploración en El Diván"
                ],
                'romantic': [
                    "Diálogos íntimos exclusivos con Diana", 
                    "Momentos de vulnerabilidad emocional compartida",
                    "Confesiones privadas que revelan el corazón de Diana"
                ],
                'analytical': [
                    "Análisis psicológico profundo de la personalidad de Diana",
                    "Estudios de caso emocionales complejos",
                    "Perspectivas intelectuales sobre motivaciones ocultas"
                ]
            },
            VIPTier.VIP_PREMIUM: {
                'explorer': [
                    "Acceso completo a los Archivos Secretos de Diana",
                    "Exploración de territorios narrativos inexplorados",
                    "Creación colaborativa de nuevas experiencias"
                ],
                'romantic': [
                    "Síntesis emocional completa en el Círculo Íntimo",
                    "Co-creación de experiencias románticas únicas",
                    "Acceso a la vulnerabilidad más profunda de Diana"
                ],
                'analytical': [
                    "Síntesis intelectual de todos los elementos narrativos",
                    "Análisis colaborativo de patrones psicológicos complejos",
                    "Desarrollo conjunto de nuevas teorías sobre conexión humana"
                ]
            }
        }
        
        return previews.get(tier, {}).get(archetype, [
            "Contenido exclusivo personalizado",
            "Experiencias adaptadas a tu estilo",
            "Acceso premium a Diana"
        ])
    
    def _calculate_offer_urgency(self, mission_progress: UserMissionProgress, user_archetype: UserArchetype) -> float:
        """Calculate urgency factor for offer."""
        urgency = 0.3  # Base urgency
        
        # High engagement users get higher urgency
        engagement = self._calculate_engagement_score(mission_progress)
        urgency += engagement * 0.4
        
        # Users close to level completion get higher urgency
        level_progress = mission_progress.current_level / 6
        if level_progress > 0.8:  # Near completion
            urgency += 0.3
        
        return min(urgency, 1.0)
    
    def _generate_diana_offer_presentation(self, tier: VIPTier, archetype: str, discount: int) -> str:
        """Generate Diana's presentation of the offer."""
        presentations = {
            VIPTier.VIP_BASIC: {
                'explorer': f"Diana emerge de las sombras con una sonrisa misteriosa... 'Has explorado Los Kinkys con una curiosidad que me fascina. El Diván te espera con secretos más profundos. Te ofrezco {discount}% de descuento porque veo en ti un verdadero explorador de almas.'",
                'romantic': f"Diana te mira con ojos llenos de promesas... 'Tu corazón ha resonado con el mío en Los Kinkys. En El Diván puedo mostrarte mi vulnerabilidad real. {discount}% de descuento para alguien que comprende que el amor verdadero requiere profundidad.'",
                'analytical': f"Diana inclina la cabeza pensativamente... 'Tu mente analítica ha diseccionado cada pista en Los Kinkys. El Diván ofrece complejidades psicológicas que solo tú puedes apreciar. {discount}% de descuento para una mente tan perspicaz.'"
            },
            VIPTier.VIP_PREMIUM: {
                'explorer': f"Diana aparece completamente revelada... 'Has explorado hasta los rincones más íntimos del Diván. El Círculo Élite es donde exploramos juntos lo desconocido. {discount}% de descuento para quien ha demostrado persistencia excepcional.'",
                'romantic': f"Diana extiende su mano... 'Hemos compartido vulnerabilidades en El Diván. El Círculo Élite es donde las almas se fusionan completamente. {discount}% de descuento para quien entiende el amor sin límites.'",
                'analytical': f"Diana sonríe con respeto profundo... 'Has sintetizado cada elemento del Diván. En el Círculo Élite, co-crearemos nuevas comprensiones. {discount}% de descuento para una mente que ha alcanzado la síntesis.'"
            }
        }
        
        return presentations.get(tier, {}).get(archetype, 
                                             f"Diana te invita... 'Has demostrado algo especial. Te ofrezco {discount}% de descuento para continuar este viaje juntos.'")
    
    def _create_value_proposition(self, tier: VIPTier, benefits: List[str]) -> str:
        """Create value proposition for tier."""
        tier_values = {
            VIPTier.VIP_BASIC: "El Diván ofrece intimidad psicológica profunda, contenido emocional personalizado, y acceso a la verdadera vulnerabilidad de Diana.",
            VIPTier.VIP_PREMIUM: "El Círculo Élite proporciona síntesis narrativa completa, co-creación de experiencias únicas, y acceso permanente al círculo más íntimo de Diana."
        }
        
        base_value = tier_values.get(tier, "Experiencia premium personalizada con Diana")
        benefits_text = " • " + " • ".join(benefits[:3])  # Top 3 benefits
        
        return f"{base_value}\n\nBeneficios exclusivos:\n{benefits_text}"
    
    def _create_archetype_specific_presentation(self, tier: VIPTier, archetype: str, discount: int) -> str:
        """Create archetype-specific offer presentation."""
        return self._generate_diana_offer_presentation(tier, archetype, discount)
    
    def _create_detailed_value_proposition(self, tier: VIPTier, archetype: str, benefits: List[str]) -> str:
        """Create detailed value proposition."""
        base_prop = self._create_value_proposition(tier, benefits)
        
        archetype_additions = {
            'explorer': "\n\nPara ti, explorador incansable: acceso a contenido con múltiples capas de descubrimiento.",
            'romantic': "\n\nPara tu corazón romántico: intimidad emocional sin precedentes con Diana.",
            'analytical': "\n\nPara tu mente analítica: complejidad psicológica y profundidad intelectual excepcionales."
        }
        
        addition = archetype_additions.get(archetype, "\n\nPersonalizado específicamente para tu estilo único de interacción.")
        
        return base_prop + addition
    
    async def _calculate_tier_utilization(self, user_id: int, current_tier: VIPTier) -> Dict[str, float]:
        """Calculate how well user is utilizing their current tier."""
        mission_progress = await self._get_user_mission_progress(user_id)
        available_features = self.content_access_map[current_tier]['features']
        available_fragments = self.content_access_map[current_tier]['fragments']
        
        # Calculate feature utilization
        features_used = 0
        if current_tier != VIPTier.FREE:
            if len(mission_progress.personalized_content_unlocked) > 0:
                features_used += 1
            if mission_progress.diana_comprehension_score > 0:
                features_used += 1
            if len(mission_progress.synthesis_challenges_completed) > 0:
                features_used += 1
        
        feature_utilization = features_used / len(available_features) if available_features else 0
        
        # Calculate content utilization
        if current_tier == VIPTier.FREE:
            completed = len(mission_progress.los_kinkys_fragments_completed)
            available = 8
        elif current_tier == VIPTier.VIP_BASIC:
            completed = len(mission_progress.los_kinkys_fragments_completed) + len(mission_progress.el_divan_fragments_completed)
            available = 12
        else:  # VIP_PREMIUM
            completed = (len(mission_progress.los_kinkys_fragments_completed) + 
                        len(mission_progress.el_divan_fragments_completed) + 
                        len(mission_progress.elite_fragments_completed))
            available = 16
        
        content_utilization = completed / available if available else 0
        
        return {
            'feature_utilization': feature_utilization,
            'content_utilization': content_utilization,
            'overall_utilization': (feature_utilization + content_utilization) / 2
        }
    
    def _calculate_comprehensive_engagement_metrics(
        self, 
        mission_progress: UserMissionProgress, 
        narrative_state: UserNarrativeState,
        user_archetype: UserArchetype
    ) -> Dict[str, Any]:
        """Calculate comprehensive engagement metrics."""
        return {
            'overall_engagement_score': self._calculate_engagement_score(mission_progress),
            'session_frequency': len(narrative_state.response_time_tracking) / 30 if narrative_state.response_time_tracking else 0,  # Sessions per month estimate
            'content_depth_engagement': len(narrative_state.content_engagement_depth) / 16 if narrative_state.content_engagement_depth else 0,  # Depth across all content
            'mission_completion_rate': (len(mission_progress.observation_missions_completed) + 
                                      len(mission_progress.comprehension_tests_passed) + 
                                      len(mission_progress.synthesis_challenges_completed)) / 15,  # Estimate total missions
            'archetype_consistency': user_archetype.get_archetype_distribution() if user_archetype else {},
            'progression_velocity': mission_progress.current_level / max(len(mission_progress.level_progression_history), 1)
        }
    
    def _analyze_value_realization(self, current_tier: VIPTier, engagement_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze value realization for current tier."""
        expected_engagement = {
            VIPTier.FREE: 0.4,
            VIPTier.VIP_BASIC: 0.7,
            VIPTier.VIP_PREMIUM: 0.9
        }
        
        actual_engagement = engagement_metrics['overall_engagement_score']
        expected = expected_engagement[current_tier]
        
        value_realization = actual_engagement / expected if expected > 0 else 0
        
        return {
            'value_realization_score': min(value_realization, 1.0),
            'expected_engagement': expected,
            'actual_engagement': actual_engagement,
            'tier_satisfaction': 'high' if value_realization > 0.8 else 'medium' if value_realization > 0.6 else 'low',
            'improvement_opportunities': self._identify_improvement_opportunities(value_realization, current_tier)
        }
    
    async def _analyze_upgrade_potential(self, user_id: int) -> Dict[str, Any]:
        """Analyze user's potential for tier upgrade."""
        mission_progress = await self._get_user_mission_progress(user_id)
        current_tier = VIPTier(mission_progress.current_tier)
        
        if current_tier == VIPTier.VIP_PREMIUM:
            return {
                'upgrade_potential': 'max_tier_reached',
                'recommendation': 'focus_on_elite_content_completion'
            }
        
        target_tier = VIPTier.VIP_BASIC if current_tier == VIPTier.FREE else VIPTier.VIP_PREMIUM
        readiness = await self._assess_upgrade_readiness(user_id, target_tier, 'potential_analysis')
        
        return {
            'upgrade_potential': 'high' if readiness['score'] > 0.7 else 'medium' if readiness['score'] > 0.4 else 'low',
            'target_tier': target_tier.value,
            'readiness_score': readiness['score'],
            'blocking_factors': readiness.get('factors', []),
            'recommended_actions': self._suggest_upgrade_preparation_actions(target_tier, readiness)
        }
    
    def _measure_personalization_effectiveness(self, user_archetype: UserArchetype) -> Dict[str, float]:
        """Measure effectiveness of personalization."""
        if not user_archetype or not user_archetype.dominant_archetype:
            return {
                'personalization_confidence': 0.3,
                'adaptation_success_rate': 0.5,
                'user_satisfaction_proxy': 0.6
            }
        
        distribution = user_archetype.get_archetype_distribution()
        max_percentage = max(distribution.values()) if distribution else 0
        
        return {
            'personalization_confidence': max_percentage / 100,
            'adaptation_success_rate': min(max_percentage / 80, 1.0),  # How well adaptations likely work
            'user_satisfaction_proxy': (max_percentage + sum(distribution.values())) / 200  # Overall satisfaction proxy
        }
    
    def _analyze_content_consumption(self, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Analyze user's content consumption patterns."""
        if not narrative_state.content_engagement_depth:
            return {
                'consumption_pattern': 'minimal',
                'depth_preference': 'unknown',
                'revisit_tendency': 'low'
            }
        
        total_visits = sum(data['visits'] for data in narrative_state.content_engagement_depth.values())
        unique_content = len(narrative_state.content_engagement_depth)
        avg_time_per_content = sum(data['total_time'] for data in narrative_state.content_engagement_depth.values()) / unique_content if unique_content > 0 else 0
        
        return {
            'consumption_pattern': 'deep' if avg_time_per_content > 120 else 'broad' if unique_content > 8 else 'focused',
            'depth_preference': 'high' if avg_time_per_content > 180 else 'medium' if avg_time_per_content > 60 else 'low',
            'revisit_tendency': 'high' if total_visits / unique_content > 1.5 else 'low',
            'content_breadth': unique_content,
            'engagement_depth': avg_time_per_content
        }
    
    def _calculate_satisfaction_indicators(self, mission_progress: UserMissionProgress, current_tier: VIPTier) -> Dict[str, float]:
        """Calculate satisfaction indicators for current tier."""
        # This would ideally use actual user feedback data
        # For now, we'll proxy satisfaction through engagement and completion
        
        completion_satisfaction = mission_progress.get_overall_progress_percentage() / 100
        progression_satisfaction = mission_progress.current_level / 6
        
        # Tier-specific satisfaction adjustments
        tier_adjustment = {
            VIPTier.FREE: 1.0,      # Free users have baseline expectations
            VIPTier.VIP_BASIC: 1.2, # VIP users have higher expectations
            VIPTier.VIP_PREMIUM: 1.4 # Premium users have highest expectations
        }
        
        base_satisfaction = (completion_satisfaction + progression_satisfaction) / 2
        adjusted_satisfaction = base_satisfaction / tier_adjustment[current_tier]
        
        return {
            'overall_satisfaction': min(adjusted_satisfaction, 1.0),
            'completion_satisfaction': completion_satisfaction,
            'progression_satisfaction': progression_satisfaction,
            'tier_value_satisfaction': min(base_satisfaction * tier_adjustment[current_tier], 1.0)
        }
    
    def _identify_improvement_opportunities(self, value_realization: float, current_tier: VIPTier) -> List[str]:
        """Identify opportunities to improve value realization."""
        opportunities = []
        
        if value_realization < 0.6:
            opportunities.extend([
                "Aumentar engagement con contenido disponible",
                "Explorar características no utilizadas del tier actual"
            ])
        
        if current_tier == VIPTier.VIP_BASIC and value_realization < 0.7:
            opportunities.extend([
                "Profundizar en análisis psicológicos disponibles",
                "Participar más en contenido emocional personalizado"
            ])
        
        elif current_tier == VIPTier.VIP_PREMIUM and value_realization < 0.8:
            opportunities.extend([
                "Completar desafíos de síntesis avanzados",
                "Acceder al contenido del Círculo Íntimo"
            ])
        
        return opportunities
    
    def _suggest_upgrade_preparation_actions(self, target_tier: VIPTier, readiness: Dict[str, Any]) -> List[str]:
        """Suggest actions to prepare for tier upgrade."""
        actions = []
        
        if target_tier == VIPTier.VIP_BASIC:
            actions.extend([
                "Completar más fragmentos de Los Kinkys",
                "Mejorar puntuación en pruebas de comprensión",
                "Aumentar engagement con contenido actual"
            ])
            
        elif target_tier == VIPTier.VIP_PREMIUM:
            actions.extend([
                "Completar fragmentos restantes de El Diván",
                "Participar en desafíos de síntesis",
                "Demostrar comprensión profunda de Diana"
            ])
        
        # Add readiness-specific actions
        if readiness['score'] < 0.5:
            actions.append("Aumentar tiempo de engagement con el contenido actual")
        
        return actions
    
    def _suggest_first_premium_content(self, tier: VIPTier, archetype: str) -> str:
        """Suggest first premium content to explore."""
        suggestions = {
            VIPTier.VIP_BASIC: {
                'explorer': "Comienza explorando 'Los Secretos Ocultos del Diván' - contenido con múltiples capas",
                'romantic': "Inicia con 'Confesiones Íntimas de Diana' - vulnerabilidad emocional profunda",
                'analytical': "Empieza con 'Análisis Psicológico Profundo' - comprensión compleja de Diana"
            },
            VIPTier.VIP_PREMIUM: {
                'explorer': "Accede a 'Archivos Personales de Diana' - exploración sin límites",
                'romantic': "Explora 'Síntesis Emocional Completa' - conexión total",
                'analytical': "Inicia 'Creación Colaborativa de Comprensión' - síntesis intelectual"
            }
        }
        
        return suggestions.get(tier, {}).get(archetype, "Explora el contenido premium personalizado para ti")

# Extension for PersonalizedVIPOffer dataclass
def _add_to_dict_method():
    def to_dict(self) -> Dict[str, Any]:
        """Convert PersonalizedVIPOffer to dictionary."""
        return {
            'offer_type': self.offer_type,
            'tier_target': self.tier_target.value,
            'discount_percentage': self.discount_percentage,
            'exclusive_content_preview': self.exclusive_content_preview,
            'archetype_benefits': self.archetype_benefits,
            'urgency_factor': self.urgency_factor,
            'diana_presentation': self.diana_presentation,
            'value_proposition': self.value_proposition
        }
    return to_dict

PersonalizedVIPOffer.to_dict = _add_to_dict_method()