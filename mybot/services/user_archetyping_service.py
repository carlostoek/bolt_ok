"""
User Archetyping System for Master Storyline

Analyzes user behavior patterns to classify them into archetypes and adapt
Diana's personality responses accordingly. Provides real-time behavior analysis
and personalized content recommendations.

Archetyping Classes:
- Explorer: Searches for details, revisits content multiple times
- Direct: Goes straight to the point, concise interactions  
- Romantic: Seeks emotional connection, poetic responses
- Analytical: Reflective responses, seeks intellectual understanding
- Persistent: Doesn't give up easily, multiple attempts
- Patient: Takes time to respond, processes deeply

This system ensures Diana's responses are tailored to each user's interaction style
while maintaining her core personality traits and mystery.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json
import re
from statistics import mean, median
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc, text

from database.narrative_unified import (
    UserArchetype, 
    UserNarrativeState,
    UserDecisionLog
)
from database.models import User

logger = logging.getLogger(__name__)

class ArchetypeClass(Enum):
    """User archetype classifications with behavioral patterns."""
    EXPLORER = "explorer"
    DIRECT = "direct" 
    ROMANTIC = "romantic"
    ANALYTICAL = "analytical"
    PERSISTENT = "persistent"
    PATIENT = "patient"

@dataclass
class BehaviorAnalysisResult:
    """Result of user behavior analysis for archetyping."""
    archetype_scores: Dict[ArchetypeClass, float]
    dominant_archetype: Optional[ArchetypeClass]
    confidence_score: float  # 0-1 confidence in the classification
    behavioral_patterns: Dict[str, Any]
    interaction_insights: List[str]
    personalization_recommendations: List[str]

@dataclass
class InteractionPattern:
    """Detailed analysis of a user's interaction pattern."""
    avg_response_time: float  # Average seconds to respond
    content_engagement_depth: float  # How deeply they engage (0-1)
    revisit_frequency: float  # How often they revisit content
    question_asking_tendency: float  # Tendency to ask questions
    detail_attention_score: float  # Attention to details (0-1)
    emotional_vocabulary_richness: float  # Use of emotional language
    exploration_breadth: float  # Range of content explored
    persistence_indicators: float  # Indicators of not giving up easily

class UserArchetypingService:
    """
    Service for analyzing user behavior and classifying into archetypes.
    Provides personalized Diana interaction recommendations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Behavioral pattern thresholds for archetype classification
        self.archetype_thresholds = {
            ArchetypeClass.EXPLORER: {
                'content_revisit_rate': 0.3,  # Revisits 30%+ of content
                'exploration_breadth': 0.7,   # Explores 70%+ of available content
                'detail_attention': 0.8,      # High attention to details
                'time_spent_exploring': 300   # Spends 5+ minutes exploring
            },
            ArchetypeClass.DIRECT: {
                'avg_response_time': 15,      # Responds within 15 seconds
                'message_length': 50,         # Short messages (<50 chars avg)
                'skip_optional_content': 0.7, # Skips 70%+ optional content
                'linear_progression': 0.8     # Follows linear path 80%+ time
            },
            ArchetypeClass.ROMANTIC: {
                'emotional_vocabulary': 0.6,  # High use of emotional words
                'personal_sharing': 0.5,      # Shares personal thoughts 50%+ time
                'connection_seeking': 0.7,    # Seeks emotional connection
                'poetic_expression': 0.4      # Uses poetic language 40%+ time
            },
            ArchetypeClass.ANALYTICAL: {
                'avg_response_time': 45,      # Takes time to respond (45+ sec)
                'question_frequency': 0.4,    # Asks questions 40%+ of interactions
                'depth_analysis': 0.8,        # Provides deep analysis
                'concept_connections': 0.6    # Makes connections between concepts
            },
            ArchetypeClass.PERSISTENT: {
                'retry_attempts': 3,          # Tries again 3+ times on challenges
                'long_session_duration': 1800, # Sessions 30+ minutes
                'completion_rate': 0.9,       # Completes 90%+ of started content
                'challenge_acceptance': 0.8   # Accepts challenges 80%+ time
            },
            ArchetypeClass.PATIENT: {
                'avg_response_time': 60,      # Takes 60+ seconds to respond
                'content_processing_time': 120, # Spends 2+ minutes on each piece
                'thorough_reading': 0.8,      # Shows thorough reading patterns
                'reflection_indicators': 0.6  # Shows reflection in responses
            }
        }
        
        # Diana personality adaptation patterns per archetype
        self.diana_adaptations = {
            ArchetypeClass.EXPLORER: {
                'mystery_level': 0.9,         # Maximum mystery and hints
                'hidden_content_ratio': 0.8,  # 80% content has hidden elements
                'revelation_pace': 'gradual', # Slow revelation of secrets
                'interaction_style': 'hint_based'
            },
            ArchetypeClass.DIRECT: {
                'mystery_level': 0.6,         # Balanced mystery
                'clarity_balance': 0.7,       # More direct but still mysterious
                'progression_markers': True,   # Clear progression indicators
                'interaction_style': 'guided_direct'
            },
            ArchetypeClass.ROMANTIC: {
                'emotional_intimacy': 0.9,    # High emotional connection
                'poetic_language': 0.8,       # More poetic expression
                'vulnerability_sharing': 0.7, # Shows more vulnerability
                'interaction_style': 'emotionally_intimate'
            },
            ArchetypeClass.ANALYTICAL: {
                'intellectual_depth': 0.9,    # Maximum intellectual engagement
                'complexity_level': 0.8,      # Complex concepts and analysis
                'reasoning_transparency': 0.6, # Shows some reasoning
                'interaction_style': 'intellectually_stimulating'
            },
            ArchetypeClass.PERSISTENT: {
                'challenge_difficulty': 0.8,  # Higher difficulty challenges
                'reward_delay': 0.7,          # Delayed but greater rewards
                'achievement_recognition': 0.9, # Strong recognition for persistence
                'interaction_style': 'progressively_challenging'
            },
            ArchetypeClass.PATIENT: {
                'content_depth': 0.9,         # Deep, layered content
                'pacing': 'slow',             # Slow, thoughtful pacing
                'reflection_prompts': 0.8,    # Many reflection opportunities
                'interaction_style': 'contemplative'
            }
        }
    
    async def analyze_user_behavior(
        self, 
        user_id: int, 
        session_data: Optional[Dict[str, Any]] = None
    ) -> BehaviorAnalysisResult:
        """
        Perform comprehensive user behavior analysis for archetyping.
        
        Args:
            user_id: User ID to analyze
            session_data: Optional current session data for real-time analysis
            
        Returns:
            BehaviorAnalysisResult with archetype classification and recommendations
        """
        # Get user's historical behavior data
        narrative_state = await self._get_user_narrative_state(user_id)
        current_archetype = await self._get_user_archetype(user_id)
        interaction_history = await self._get_user_interaction_history(user_id)
        
        # Analyze interaction patterns
        patterns = await self._analyze_interaction_patterns(
            user_id, narrative_state, interaction_history, session_data
        )
        
        # Calculate archetype scores
        archetype_scores = self._calculate_archetype_scores(patterns)
        
        # Determine dominant archetype and confidence
        dominant_archetype, confidence = self._determine_dominant_archetype(archetype_scores)
        
        # Generate behavioral insights
        behavioral_patterns = self._extract_behavioral_patterns(patterns)
        interaction_insights = self._generate_interaction_insights(patterns, archetype_scores)
        
        # Generate personalization recommendations
        personalization_recs = self._generate_personalization_recommendations(
            dominant_archetype, archetype_scores, patterns
        )
        
        # Update user archetype in database
        if dominant_archetype and confidence > 0.7:
            await self._update_user_archetype(user_id, archetype_scores, patterns)
        
        return BehaviorAnalysisResult(
            archetype_scores=archetype_scores,
            dominant_archetype=dominant_archetype,
            confidence_score=confidence,
            behavioral_patterns=behavioral_patterns,
            interaction_insights=interaction_insights,
            personalization_recommendations=personalization_recs
        )
    
    async def get_diana_adaptation_strategy(
        self, 
        user_id: int,
        context: str = "general"
    ) -> Dict[str, Any]:
        """
        Get Diana personality adaptation strategy for a specific user.
        
        Args:
            user_id: User ID
            context: Interaction context (fragment, menu, error, etc.)
            
        Returns:
            Dictionary with Diana adaptation parameters
        """
        # Get current user archetype
        archetype = await self._get_user_archetype(user_id)
        
        if not archetype or not archetype.dominant_archetype:
            # Default balanced approach for unclassified users
            return self._get_default_diana_strategy()
        
        dominant_type = ArchetypeClass(archetype.dominant_archetype)
        base_strategy = self.diana_adaptations.get(dominant_type, {})
        
        # Context-specific adaptations
        context_adaptations = self._get_context_specific_adaptations(context, dominant_type)
        
        # Combine base strategy with context adaptations
        strategy = {**base_strategy, **context_adaptations}
        
        # Add archetype distribution for nuanced adaptation
        distribution = archetype.get_archetype_distribution()
        strategy['archetype_distribution'] = distribution
        strategy['adaptation_confidence'] = self._calculate_adaptation_confidence(archetype)
        
        return strategy
    
    async def track_real_time_behavior(
        self,
        user_id: int,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track real-time behavior for immediate archetype adjustment.
        
        Args:
            user_id: User ID
            interaction_type: Type of interaction (decision, exploration, question, etc.)
            interaction_data: Data about the interaction
            
        Returns:
            Dictionary with immediate behavior insights and archetype adjustments
        """
        # Get current narrative state
        narrative_state = await self._get_user_narrative_state(user_id)
        
        # Update behavior tracking data
        if not narrative_state.response_time_tracking:
            narrative_state.response_time_tracking = []
        if not narrative_state.interaction_patterns:
            narrative_state.interaction_patterns = {}
        if not narrative_state.content_engagement_depth:
            narrative_state.content_engagement_depth = {}
        
        # Track response time if provided
        response_time = interaction_data.get('response_time_seconds')
        if response_time:
            narrative_state.response_time_tracking.append({
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': response_time,
                'interaction_type': interaction_type
            })
            
            # Keep only last 50 response times for performance
            if len(narrative_state.response_time_tracking) > 50:
                narrative_state.response_time_tracking = narrative_state.response_time_tracking[-50:]
        
        # Track interaction patterns
        pattern_key = f"{interaction_type}_pattern"
        if pattern_key not in narrative_state.interaction_patterns:
            narrative_state.interaction_patterns[pattern_key] = []
        
        narrative_state.interaction_patterns[pattern_key].append({
            'timestamp': datetime.utcnow().isoformat(),
            'data': interaction_data
        })
        
        # Track content engagement
        content_id = interaction_data.get('content_id')
        if content_id:
            if content_id not in narrative_state.content_engagement_depth:
                narrative_state.content_engagement_depth[content_id] = {
                    'visits': 0,
                    'total_time': 0,
                    'interactions': []
                }
            
            narrative_state.content_engagement_depth[content_id]['visits'] += 1
            narrative_state.content_engagement_depth[content_id]['total_time'] += interaction_data.get('time_spent', 0)
            narrative_state.content_engagement_depth[content_id]['interactions'].append({
                'type': interaction_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': interaction_data
            })
        
        await self.session.commit()
        
        # Perform quick archetype analysis
        quick_analysis = self._perform_quick_archetype_analysis(
            interaction_type, interaction_data, narrative_state
        )
        
        return {
            'behavior_indicators': quick_analysis,
            'immediate_adaptations': self._suggest_immediate_adaptations(quick_analysis),
            'archetype_confidence_change': self._calculate_confidence_change(quick_analysis)
        }
    
    async def get_archetype_evolution_report(self, user_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive archetype evolution report for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with evolution analysis and trends
        """
        archetype = await self._get_user_archetype(user_id)
        narrative_state = await self._get_user_narrative_state(user_id)
        
        if not archetype:
            return {'error': 'User archetype not found'}
        
        # Analyze historical progression
        evolution_analysis = await self._analyze_archetype_evolution(user_id)
        
        # Current archetype status
        current_status = {
            'dominant_archetype': archetype.dominant_archetype,
            'distribution': archetype.get_archetype_distribution(),
            'behavioral_metrics': {
                'avg_response_time': archetype.avg_response_time,
                'content_revisit_count': archetype.content_revisit_count,
                'deep_exploration_sessions': archetype.deep_exploration_sessions,
                'question_engagement_rate': archetype.question_engagement_rate,
                'emotional_vocabulary_usage': archetype.emotional_vocabulary_usage
            }
        }
        
        # Stability analysis
        stability_analysis = self._analyze_archetype_stability(archetype, narrative_state)
        
        # Future predictions
        evolution_predictions = self._predict_archetype_evolution(archetype, narrative_state)
        
        return {
            'current_status': current_status,
            'evolution_analysis': evolution_analysis,
            'stability_analysis': stability_analysis,
            'predictions': evolution_predictions,
            'adaptation_effectiveness': self._measure_adaptation_effectiveness(user_id),
            'recommendations': self._generate_evolution_recommendations(archetype, narrative_state)
        }
    
    # Private helper methods
    
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
    
    async def _get_user_archetype(self, user_id: int) -> UserArchetype:
        """Get user archetype."""
        stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
        result = await self.session.execute(stmt)
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            archetype = UserArchetype(user_id=user_id)
            self.session.add(archetype)
            await self.session.commit()
            await self.session.refresh(archetype)
        
        return archetype
    
    async def _get_user_interaction_history(self, user_id: int) -> List[UserDecisionLog]:
        """Get user interaction history."""
        stmt = select(UserDecisionLog).where(
            UserDecisionLog.user_id == user_id
        ).order_by(desc(UserDecisionLog.made_at)).limit(100)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _analyze_interaction_patterns(
        self,
        user_id: int,
        narrative_state: UserNarrativeState,
        interaction_history: List[UserDecisionLog],
        session_data: Optional[Dict[str, Any]] = None
    ) -> InteractionPattern:
        """Analyze user interaction patterns for archetyping."""
        
        # Calculate average response time
        response_times = []
        if narrative_state.response_time_tracking:
            response_times = [rt['response_time'] for rt in narrative_state.response_time_tracking if 'response_time' in rt]
        avg_response_time = mean(response_times) if response_times else 30.0
        
        # Calculate content engagement depth
        engagement_scores = []
        if narrative_state.content_engagement_depth:
            for content_id, data in narrative_state.content_engagement_depth.items():
                engagement_score = min(data['visits'] * 0.2 + data['total_time'] / 60 * 0.1, 1.0)
                engagement_scores.append(engagement_score)
        content_engagement_depth = mean(engagement_scores) if engagement_scores else 0.5
        
        # Calculate revisit frequency
        total_visits = sum(data['visits'] for data in narrative_state.content_engagement_depth.values()) if narrative_state.content_engagement_depth else 0
        unique_content = len(narrative_state.content_engagement_depth) if narrative_state.content_engagement_depth else 1
        revisit_frequency = max(0, (total_visits - unique_content) / unique_content) if unique_content > 0 else 0
        
        # Analyze decision patterns from history
        decision_analysis = self._analyze_decision_patterns(interaction_history)
        
        # Calculate detail attention score
        detail_attention = self._calculate_detail_attention_score(narrative_state, session_data)
        
        # Calculate emotional vocabulary richness
        emotional_vocabulary = self._calculate_emotional_vocabulary_richness(interaction_history)
        
        # Calculate exploration breadth
        exploration_breadth = len(narrative_state.visited_fragments) / max(len(narrative_state.completed_fragments) + 1, 1)
        
        # Calculate persistence indicators
        persistence_indicators = self._calculate_persistence_indicators(narrative_state, interaction_history)
        
        return InteractionPattern(
            avg_response_time=avg_response_time,
            content_engagement_depth=content_engagement_depth,
            revisit_frequency=revisit_frequency,
            question_asking_tendency=decision_analysis.get('question_tendency', 0.3),
            detail_attention_score=detail_attention,
            emotional_vocabulary_richness=emotional_vocabulary,
            exploration_breadth=min(exploration_breadth, 1.0),
            persistence_indicators=persistence_indicators
        )
    
    def _calculate_archetype_scores(self, patterns: InteractionPattern) -> Dict[ArchetypeClass, float]:
        """Calculate archetype scores based on interaction patterns."""
        scores = {}
        
        # Explorer archetype scoring
        explorer_score = 0.0
        if patterns.revisit_frequency > 0.3:
            explorer_score += 0.3
        if patterns.exploration_breadth > 0.7:
            explorer_score += 0.3
        if patterns.detail_attention_score > 0.8:
            explorer_score += 0.4
        scores[ArchetypeClass.EXPLORER] = min(explorer_score, 1.0)
        
        # Direct archetype scoring  
        direct_score = 0.0
        if patterns.avg_response_time < 15:
            direct_score += 0.4
        if patterns.content_engagement_depth < 0.4:
            direct_score += 0.3
        if patterns.exploration_breadth < 0.5:
            direct_score += 0.3
        scores[ArchetypeClass.DIRECT] = min(direct_score, 1.0)
        
        # Romantic archetype scoring
        romantic_score = 0.0
        if patterns.emotional_vocabulary_richness > 0.6:
            romantic_score += 0.4
        if patterns.content_engagement_depth > 0.7:
            romantic_score += 0.3
        if patterns.avg_response_time > 20:  # Takes time for emotional responses
            romantic_score += 0.3
        scores[ArchetypeClass.ROMANTIC] = min(romantic_score, 1.0)
        
        # Analytical archetype scoring
        analytical_score = 0.0
        if patterns.avg_response_time > 45:
            analytical_score += 0.3
        if patterns.question_asking_tendency > 0.4:
            analytical_score += 0.4
        if patterns.content_engagement_depth > 0.8:
            analytical_score += 0.3
        scores[ArchetypeClass.ANALYTICAL] = min(analytical_score, 1.0)
        
        # Persistent archetype scoring
        persistent_score = patterns.persistence_indicators
        scores[ArchetypeClass.PERSISTENT] = min(persistent_score, 1.0)
        
        # Patient archetype scoring
        patient_score = 0.0
        if patterns.avg_response_time > 60:
            patient_score += 0.4
        if patterns.content_engagement_depth > 0.8:
            patient_score += 0.3
        if patterns.revisit_frequency > 0.4:
            patient_score += 0.3
        scores[ArchetypeClass.PATIENT] = min(patient_score, 1.0)
        
        return scores
    
    def _determine_dominant_archetype(
        self, 
        archetype_scores: Dict[ArchetypeClass, float]
    ) -> Tuple[Optional[ArchetypeClass], float]:
        """Determine dominant archetype and confidence score."""
        if not archetype_scores or all(score < 0.3 for score in archetype_scores.values()):
            return None, 0.0
        
        # Find highest scoring archetype
        dominant = max(archetype_scores, key=archetype_scores.get)
        max_score = archetype_scores[dominant]
        
        # Calculate confidence based on score separation
        sorted_scores = sorted(archetype_scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            confidence = min(max_score, (sorted_scores[0] - sorted_scores[1]) + 0.5)
        else:
            confidence = max_score
        
        return dominant, confidence
    
    def _extract_behavioral_patterns(self, patterns: InteractionPattern) -> Dict[str, Any]:
        """Extract behavioral patterns for analysis."""
        return {
            'response_speed': 'fast' if patterns.avg_response_time < 20 else 'slow' if patterns.avg_response_time > 60 else 'moderate',
            'exploration_style': 'thorough' if patterns.exploration_breadth > 0.7 else 'focused' if patterns.exploration_breadth < 0.4 else 'balanced',
            'engagement_depth': 'deep' if patterns.content_engagement_depth > 0.7 else 'shallow' if patterns.content_engagement_depth < 0.4 else 'moderate',
            'attention_to_detail': 'high' if patterns.detail_attention_score > 0.8 else 'low' if patterns.detail_attention_score < 0.4 else 'moderate',
            'emotional_expression': 'rich' if patterns.emotional_vocabulary_richness > 0.6 else 'limited' if patterns.emotional_vocabulary_richness < 0.3 else 'moderate',
            'persistence_level': 'high' if patterns.persistence_indicators > 0.7 else 'low' if patterns.persistence_indicators < 0.3 else 'moderate'
        }
    
    def _generate_interaction_insights(
        self, 
        patterns: InteractionPattern, 
        archetype_scores: Dict[ArchetypeClass, float]
    ) -> List[str]:
        """Generate human-readable insights about user interaction patterns."""
        insights = []
        
        # Response time insights
        if patterns.avg_response_time < 15:
            insights.append("Usuario responde muy rápidamente - indica naturaleza directa")
        elif patterns.avg_response_time > 60:
            insights.append("Usuario toma tiempo para responder - indica procesamiento reflexivo")
        
        # Exploration insights
        if patterns.exploration_breadth > 0.8:
            insights.append("Usuario explora ampliamente - busca experiencias completas")
        elif patterns.exploration_breadth < 0.3:
            insights.append("Usuario se enfoca en objetivos específicos - progresión lineal preferida")
        
        # Engagement insights
        if patterns.content_engagement_depth > 0.8:
            insights.append("Usuario muestra engagement profundo - aprecia contenido rico")
        
        # Detail attention insights
        if patterns.detail_attention_score > 0.8:
            insights.append("Usuario presta mucha atención a detalles - personalidad observadora")
        
        # Emotional vocabulary insights
        if patterns.emotional_vocabulary_richness > 0.6:
            insights.append("Usuario usa vocabulario emocional rico - busca conexión emocional")
        
        # Archetype-specific insights
        dominant_archetype = max(archetype_scores, key=archetype_scores.get)
        if archetype_scores[dominant_archetype] > 0.7:
            archetype_insights = {
                ArchetypeClass.EXPLORER: "Naturaleza exploradora dominante - necesita misterio y descubrimiento",
                ArchetypeClass.DIRECT: "Personalidad directa dominante - prefiere claridad y progresión",
                ArchetypeClass.ROMANTIC: "Tendencia romántica dominante - busca conexión emocional profunda",
                ArchetypeClass.ANALYTICAL: "Enfoque analítico dominante - necesita complejidad intelectual",
                ArchetypeClass.PERSISTENT: "Persistencia dominante - acepta desafíos y no se rinde fácilmente",
                ArchetypeClass.PATIENT: "Paciencia dominante - procesa información lenta y profundamente"
            }
            insights.append(archetype_insights[dominant_archetype])
        
        return insights
    
    def _generate_personalization_recommendations(
        self,
        dominant_archetype: Optional[ArchetypeClass],
        archetype_scores: Dict[ArchetypeClass, float],
        patterns: InteractionPattern
    ) -> List[str]:
        """Generate personalization recommendations based on archetype analysis."""
        recommendations = []
        
        if not dominant_archetype:
            recommendations.append("Usar enfoque balanceado hasta establecer patrón claro")
            return recommendations
        
        # Archetype-specific recommendations
        if dominant_archetype == ArchetypeClass.EXPLORER:
            recommendations.extend([
                "Incluir múltiples elementos ocultos para descubrir",
                "Proporcionar contenido adicional opcional",
                "Usar pistas y misterios como motivadores principales",
                "Permitir múltiples rutas de exploración"
            ])
        
        elif dominant_archetype == ArchetypeClass.DIRECT:
            recommendations.extend([
                "Proporcionar objetivos claros y marcadores de progreso",
                "Minimizar contenido opcional y distracciones",
                "Usar comunicación directa pero mantener personalidad de Diana",
                "Implementar progresión lineal clara"
            ])
        
        elif dominant_archetype == ArchetypeClass.ROMANTIC:
            recommendations.extend([
                "Enfatizar conexión emocional en todas las interacciones",
                "Usar lenguaje poético y evocativo",
                "Incluir más momentos de vulnerabilidad e intimidad",
                "Personalizar el contenido con referencias emocionales"
            ])
        
        elif dominant_archetype == ArchetypeClass.ANALYTICAL:
            recommendations.extend([
                "Proporcionar contexto detallado y explicaciones",
                "Incluir elementos de reflexión y análisis",
                "Ofrecer múltiples perspectivas sobre situaciones",
                "Estimular el pensamiento crítico con preguntas complejas"
            ])
        
        elif dominant_archetype == ArchetypeClass.PERSISTENT:
            recommendations.extend([
                "Diseñar desafíos escalados que requieran persistencia",
                "Implementar recompensas retardadas pero significativas",
                "Reconocer específicamente los esfuerzos sostenidos",
                "Crear contenido que recompense la determinación"
            ])
        
        elif dominant_archetype == ArchetypeClass.PATIENT:
            recommendations.extend([
                "Usar ritmo más lento con pausa para reflexión",
                "Incluir contenido profundo y estratificado",
                "Proporcionar tiempo para procesamiento entre revelaciones",
                "Enfatizar la calidad sobre la cantidad de interacciones"
            ])
        
        # Secondary archetype influence
        secondary_scores = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)
        if len(secondary_scores) > 1 and secondary_scores[1][1] > 0.4:
            secondary_archetype = secondary_scores[1][0]
            recommendations.append(f"Incorporar elementos de personalidad {secondary_archetype.value} como influencia secundaria")
        
        return recommendations
    
    async def _update_user_archetype(
        self,
        user_id: int,
        archetype_scores: Dict[ArchetypeClass, float],
        patterns: InteractionPattern
    ):
        """Update user archetype in database with new analysis."""
        archetype = await self._get_user_archetype(user_id)
        
        # Update archetype scores with weighted average (70% existing, 30% new)
        for archetype_class, new_score in archetype_scores.items():
            current_score = getattr(archetype, f"{archetype_class.value}_score", 0)
            updated_score = int(current_score * 0.7 + new_score * 100 * 0.3)
            setattr(archetype, f"{archetype_class.value}_score", min(updated_score, 100))
        
        # Update behavioral metrics
        archetype.avg_response_time = int(patterns.avg_response_time)
        archetype.content_revisit_count = int(patterns.revisit_frequency * 100)
        archetype.question_engagement_rate = int(patterns.question_asking_tendency * 100)
        archetype.emotional_vocabulary_usage = int(patterns.emotional_vocabulary_richness * 100)
        
        # Calculate and update dominant archetype
        archetype.calculate_dominant_archetype()
        
        await self.session.commit()
    
    def _get_default_diana_strategy(self) -> Dict[str, Any]:
        """Get default Diana interaction strategy for unclassified users."""
        return {
            'mystery_level': 0.7,
            'emotional_intimacy': 0.6,
            'intellectual_depth': 0.6,
            'clarity_balance': 0.5,
            'interaction_style': 'balanced_mysterious',
            'adaptation_confidence': 0.3
        }
    
    def _get_context_specific_adaptations(
        self, 
        context: str, 
        archetype: ArchetypeClass
    ) -> Dict[str, Any]:
        """Get context-specific adaptations for Diana's behavior."""
        adaptations = {}
        
        if context == "error":
            if archetype == ArchetypeClass.DIRECT:
                adaptations['error_style'] = 'clear_guidance'
            elif archetype == ArchetypeClass.ROMANTIC:
                adaptations['error_style'] = 'gentle_encouragement'
            elif archetype == ArchetypeClass.ANALYTICAL:
                adaptations['error_style'] = 'detailed_explanation'
            else:
                adaptations['error_style'] = 'mysterious_redirection'
        
        elif context == "achievement":
            if archetype == ArchetypeClass.PERSISTENT:
                adaptations['achievement_recognition'] = 'high_celebration'
            elif archetype == ArchetypeClass.PATIENT:
                adaptations['achievement_recognition'] = 'thoughtful_acknowledgment'
            else:
                adaptations['achievement_recognition'] = 'balanced_praise'
        
        elif context == "fragment":
            if archetype == ArchetypeClass.EXPLORER:
                adaptations['fragment_complexity'] = 'high_hidden_elements'
            elif archetype == ArchetypeClass.DIRECT:
                adaptations['fragment_complexity'] = 'clear_progression'
            else:
                adaptations['fragment_complexity'] = 'balanced_mystery'
        
        return adaptations
    
    def _calculate_adaptation_confidence(self, archetype: UserArchetype) -> float:
        """Calculate confidence in archetype-based adaptations."""
        if not archetype.dominant_archetype:
            return 0.0
        
        distribution = archetype.get_archetype_distribution()
        max_percentage = max(distribution.values()) if distribution else 0
        
        # High confidence if one archetype is clearly dominant (>60%)
        if max_percentage > 60:
            return 0.9
        elif max_percentage > 40:
            return 0.7
        elif max_percentage > 25:
            return 0.5
        else:
            return 0.3
    
    def _perform_quick_archetype_analysis(
        self,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        narrative_state: UserNarrativeState
    ) -> Dict[str, float]:
        """Perform quick archetype analysis for real-time adaptation."""
        indicators = {}
        
        response_time = interaction_data.get('response_time_seconds', 30)
        content_id = interaction_data.get('content_id')
        
        # Quick response time indicators
        if response_time < 10:
            indicators['direct_tendency'] = 0.8
        elif response_time > 90:
            indicators['patient_tendency'] = 0.7
            indicators['analytical_tendency'] = 0.6
        
        # Content revisit indicators
        if content_id and content_id in narrative_state.content_engagement_depth:
            visits = narrative_state.content_engagement_depth[content_id]['visits']
            if visits > 2:
                indicators['explorer_tendency'] = 0.7
                indicators['persistent_tendency'] = 0.6
        
        # Interaction type specific indicators
        if interaction_type == 'question':
            indicators['analytical_tendency'] = 0.6
        elif interaction_type == 'emotional_response':
            indicators['romantic_tendency'] = 0.8
        elif interaction_type == 'detail_discovery':
            indicators['explorer_tendency'] = 0.9
        
        return indicators
    
    def _suggest_immediate_adaptations(self, quick_analysis: Dict[str, float]) -> Dict[str, Any]:
        """Suggest immediate Diana adaptations based on quick analysis."""
        adaptations = {}
        
        # Find strongest tendency
        if quick_analysis:
            strongest_tendency = max(quick_analysis, key=quick_analysis.get)
            strength = quick_analysis[strongest_tendency]
            
            if strength > 0.7:
                if 'direct_tendency' in strongest_tendency:
                    adaptations['response_style'] = 'more_direct'
                    adaptations['mystery_reduction'] = 0.2
                elif 'romantic_tendency' in strongest_tendency:
                    adaptations['response_style'] = 'more_intimate'
                    adaptations['emotional_emphasis'] = 0.3
                elif 'explorer_tendency' in strongest_tendency:
                    adaptations['response_style'] = 'more_mysterious'
                    adaptations['hidden_content_bonus'] = True
                elif 'analytical_tendency' in strongest_tendency:
                    adaptations['response_style'] = 'more_complex'
                    adaptations['intellectual_depth_bonus'] = 0.2
        
        return adaptations
    
    def _calculate_confidence_change(self, quick_analysis: Dict[str, float]) -> float:
        """Calculate how much confidence in archetype classification should change."""
        if not quick_analysis:
            return 0.0
        
        max_tendency = max(quick_analysis.values()) if quick_analysis else 0
        
        # Strong indicators increase confidence
        if max_tendency > 0.8:
            return 0.1  # Increase confidence by 10%
        elif max_tendency > 0.6:
            return 0.05  # Increase confidence by 5%
        else:
            return 0.0  # No significant change
    
    def _analyze_decision_patterns(self, interaction_history: List[UserDecisionLog]) -> Dict[str, float]:
        """Analyze patterns in user decision making."""
        if not interaction_history:
            return {'question_tendency': 0.3}
        
        # Count question-type interactions vs statement-type
        question_indicators = 0
        total_interactions = len(interaction_history)
        
        for interaction in interaction_history:
            if '?' in interaction.decision_choice:
                question_indicators += 1
        
        question_tendency = question_indicators / total_interactions if total_interactions > 0 else 0.3
        
        return {
            'question_tendency': question_tendency,
            'interaction_consistency': self._calculate_interaction_consistency(interaction_history)
        }
    
    def _calculate_detail_attention_score(
        self, 
        narrative_state: UserNarrativeState, 
        session_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate user's attention to detail score."""
        score = 0.5  # Default moderate attention
        
        # Check for hidden elements discovery in session data
        if session_data and 'hidden_elements_found' in session_data:
            elements_found = len(session_data['hidden_elements_found'])
            score += min(elements_found * 0.1, 0.4)
        
        # Check historical engagement depth
        if narrative_state.content_engagement_depth:
            avg_visits = mean([data['visits'] for data in narrative_state.content_engagement_depth.values()])
            if avg_visits > 1.5:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_emotional_vocabulary_richness(self, interaction_history: List[UserDecisionLog]) -> float:
        """Calculate richness of emotional vocabulary in user responses."""
        if not interaction_history:
            return 0.3
        
        emotional_words = [
            'siento', 'emoción', 'corazón', 'alma', 'amor', 'deseo', 'pasión',
            'melancolía', 'nostalgia', 'anhelo', 'esperanza', 'temor', 'vulnerabilidad'
        ]
        
        total_words = 0
        emotional_word_count = 0
        
        for interaction in interaction_history:
            words = interaction.decision_choice.lower().split()
            total_words += len(words)
            emotional_word_count += sum(1 for word in words if word in emotional_words)
        
        if total_words == 0:
            return 0.3
        
        return min(emotional_word_count / total_words * 10, 1.0)  # Scale up for visibility
    
    def _calculate_persistence_indicators(
        self, 
        narrative_state: UserNarrativeState, 
        interaction_history: List[UserDecisionLog]
    ) -> float:
        """Calculate indicators of user persistence."""
        persistence_score = 0.5  # Default moderate persistence
        
        # Check completion rate
        if narrative_state.visited_fragments and narrative_state.completed_fragments:
            completion_rate = len(narrative_state.completed_fragments) / len(narrative_state.visited_fragments)
            persistence_score += completion_rate * 0.3
        
        # Check for retry patterns in interaction history
        if interaction_history:
            # Look for similar fragments attempted multiple times
            fragment_attempts = {}
            for interaction in interaction_history:
                fragment_id = interaction.fragment_id
                fragment_attempts[fragment_id] = fragment_attempts.get(fragment_id, 0) + 1
            
            retry_rate = sum(1 for attempts in fragment_attempts.values() if attempts > 1) / len(fragment_attempts)
            persistence_score += retry_rate * 0.2
        
        return min(persistence_score, 1.0)
    
    def _calculate_interaction_consistency(self, interaction_history: List[UserDecisionLog]) -> float:
        """Calculate consistency in user interaction patterns."""
        if len(interaction_history) < 3:
            return 0.5
        
        # Analyze timing consistency
        time_intervals = []
        for i in range(1, len(interaction_history)):
            interval = (interaction_history[i-1].made_at - interaction_history[i].made_at).total_seconds()
            time_intervals.append(abs(interval))
        
        if time_intervals:
            avg_interval = mean(time_intervals)
            interval_variance = sum((x - avg_interval) ** 2 for x in time_intervals) / len(time_intervals)
            consistency = max(0, 1 - (interval_variance / avg_interval**2)) if avg_interval > 0 else 0.5
            return min(consistency, 1.0)
        
        return 0.5
    
    async def _analyze_archetype_evolution(self, user_id: int) -> Dict[str, Any]:
        """Analyze how user's archetype has evolved over time."""
        # This would analyze historical archetype data over time
        # For now, return basic evolution framework
        return {
            'evolution_detected': False,
            'dominant_changes': [],
            'stability_periods': [],
            'influencing_factors': []
        }
    
    def _analyze_archetype_stability(
        self, 
        archetype: UserArchetype, 
        narrative_state: UserNarrativeState
    ) -> Dict[str, Any]:
        """Analyze stability of user's archetype classification."""
        distribution = archetype.get_archetype_distribution()
        
        # Calculate stability metrics
        max_percentage = max(distribution.values()) if distribution else 0
        
        stability = 'high' if max_percentage > 60 else 'medium' if max_percentage > 40 else 'low'
        
        return {
            'stability_level': stability,
            'dominant_percentage': max_percentage,
            'secondary_influence': sorted(distribution.items(), key=lambda x: x[1], reverse=True)[1] if len(distribution) > 1 else None,
            'volatility_indicators': []
        }
    
    def _predict_archetype_evolution(
        self, 
        archetype: UserArchetype, 
        narrative_state: UserNarrativeState
    ) -> Dict[str, Any]:
        """Predict potential archetype evolution based on current trends."""
        current_level = narrative_state.current_level
        tier = narrative_state.current_tier
        
        predictions = {
            'likely_evolution': 'stable',
            'confidence': 0.7,
            'influencing_factors': []
        }
        
        # As users progress through VIP tiers, they might become more analytical or romantic
        if tier == 'el_divan' and current_level >= 4:
            predictions['likely_evolution'] = 'more_analytical_or_romantic'
            predictions['influencing_factors'].append('VIP tier deepening experience')
        
        if current_level >= 5:
            predictions['likely_evolution'] = 'synthesis_of_archetypes'
            predictions['influencing_factors'].append('Advanced narrative complexity')
        
        return predictions
    
    def _measure_adaptation_effectiveness(self, user_id: int) -> Dict[str, float]:
        """Measure how effective archetype-based adaptations have been."""
        # This would measure actual effectiveness through user engagement metrics
        # For now, return placeholder metrics
        return {
            'engagement_improvement': 0.85,
            'satisfaction_score': 0.80,
            'retention_improvement': 0.75,
            'completion_rate_improvement': 0.70
        }
    
    def _generate_evolution_recommendations(
        self, 
        archetype: UserArchetype, 
        narrative_state: UserNarrativeState
    ) -> List[str]:
        """Generate recommendations for archetype evolution and adaptation."""
        recommendations = []
        
        current_level = narrative_state.current_level
        distribution = archetype.get_archetype_distribution()
        
        # Recommendations based on current level
        if current_level >= 4:  # VIP level
            recommendations.append("Introducir elementos de múltiples arquetipos para enriquecer la experiencia")
        
        if current_level >= 6:  # Elite level
            recommendations.append("Enfocarse en síntesis de arquetipos para experiencia altamente personalizada")
        
        # Recommendations based on archetype distribution
        max_archetype = max(distribution, key=distribution.get)
        if distribution[max_archetype] < 50:
            recommendations.append("Usuario muestra arquetipo mixto - usar enfoque adaptativo balanceado")
        
        return recommendations