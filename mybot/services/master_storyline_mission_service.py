"""
Master Storyline Mission Service

Handles mission validation logic for the 6-level master storyline progression system.
Implements observation, comprehension, and synthesis challenges mapped to user archetyping.

Mission Types:
- Observation: Track user behavior patterns and attention to detail
- Comprehension: Evaluate user understanding through question analysis  
- Synthesis: Validate ability to integrate multiple levels of understanding

Archetyping System:
- Explorer: Searches for details, revisits content multiple times
- Direct: Goes straight to the point, concise interactions
- Romantic: Seeks emotional connection, poetic responses
- Analytical: Reflective responses, seeks intellectual understanding
- Persistent: Doesn't give up easily, multiple attempts
- Patient: Takes time to respond, processes deeply
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc

from database.narrative_unified import (
    UserMissionProgress, 
    UserArchetype, 
    NarrativeFragment,
    UserNarrativeState
)
from database.models import User

logger = logging.getLogger(__name__)

class MissionType(Enum):
    """Mission types aligned with master storyline progression."""
    OBSERVATION = "observation"
    COMPREHENSION = "comprehension"
    SYNTHESIS = "synthesis"

class ArchetypeClass(Enum):
    """User archetype classifications."""
    EXPLORER = "explorer"
    DIRECT = "direct"
    ROMANTIC = "romantic"
    ANALYTICAL = "analytical"
    PERSISTENT = "persistent"
    PATIENT = "patient"

@dataclass
class MissionValidationResult:
    """Result of mission validation process."""
    mission_completed: bool
    score: int  # 0-100
    archetype_indicators: Dict[ArchetypeClass, float]
    performance_metrics: Dict[str, Any]
    next_level_unlocked: bool
    rewards_earned: List[Dict[str, Any]]
    feedback_message: str
    character_consistency_maintained: bool = True

@dataclass
class ObservationMissionResult:
    """Result specific to observation missions."""
    details_found: List[str]
    time_spent_exploring: int  # seconds
    revisit_count: int
    attention_to_detail_score: int  # 0-100
    hidden_elements_discovered: int
    exploration_pattern: str  # linear, thorough, intuitive

@dataclass
class ComprehensionTestResult:
    """Result specific to comprehension tests."""
    questions_answered: int
    correct_answers: int
    understanding_depth_score: int  # 0-100
    emotional_intelligence_indicators: List[str]
    diana_comprehension_accuracy: int  # How well they understand Diana
    response_quality_metrics: Dict[str, float]

@dataclass
class SynthesisChallenge:
    """Result specific to synthesis challenges."""
    concepts_integrated: List[str]
    creativity_score: int  # 0-100
    cross_level_connections: int  # Number of connections made across storyline levels
    narrative_coherence_score: int  # 0-100
    original_insights_generated: int

class MasterStorylineMissionService:
    """
    Service for validating missions in the 6-level master storyline system.
    Handles observation, comprehension, and synthesis challenges while building user archetypes.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Mission difficulty scaling per level
        self.level_difficulty_scaling = {
            1: {'observation': 0.6, 'comprehension': 0.5, 'synthesis': 0.4},
            2: {'observation': 0.7, 'comprehension': 0.6, 'synthesis': 0.5},
            3: {'observation': 0.8, 'comprehension': 0.7, 'synthesis': 0.6},
            4: {'observation': 0.85, 'comprehension': 0.75, 'synthesis': 0.7},  # VIP starts
            5: {'observation': 0.9, 'comprehension': 0.85, 'synthesis': 0.8},
            6: {'observation': 0.95, 'comprehension': 0.9, 'synthesis': 0.9}   # Elite level
        }
        
        # Minimum scores required for level progression
        self.progression_thresholds = {
            1: 60, 2: 65, 3: 70, 4: 75, 5: 80, 6: 85
        }
    
    async def validate_observation_mission(
        self, 
        user_id: int, 
        fragment_id: str,
        interaction_data: Dict[str, Any]
    ) -> MissionValidationResult:
        """
        Validate observation mission performance.
        
        Tracks:
        - Time spent exploring content
        - Number of hidden elements discovered
        - Attention to detail patterns
        - Content revisit behavior
        """
        user_progress = await self._get_user_mission_progress(user_id)
        current_level = user_progress.current_level
        
        # Extract observation metrics
        time_spent = interaction_data.get('time_spent_seconds', 0)
        elements_found = interaction_data.get('hidden_elements_found', [])
        revisit_count = interaction_data.get('content_revisits', 0)
        interaction_pattern = interaction_data.get('exploration_pattern', 'linear')
        
        # Calculate observation score based on current level requirements
        difficulty = self.level_difficulty_scaling[current_level]['observation']
        base_score = self._calculate_observation_score(
            time_spent, len(elements_found), revisit_count, interaction_pattern
        )
        
        # Apply difficulty scaling
        final_score = int(base_score * (1 + difficulty * 0.5))
        final_score = min(final_score, 100)
        
        # Analyze archetype indicators
        archetype_indicators = self._analyze_observation_archetypes(
            time_spent, revisit_count, interaction_pattern, len(elements_found)
        )
        
        # Update user archetype scores
        await self._update_archetype_scores(user_id, archetype_indicators)
        
        # Check if mission completed
        threshold = self.progression_thresholds[current_level]
        mission_completed = final_score >= threshold
        
        # Prepare results
        performance_metrics = {
            'time_spent_seconds': time_spent,
            'hidden_elements_found': len(elements_found),
            'revisit_count': revisit_count,
            'exploration_pattern': interaction_pattern,
            'attention_detail_score': self._calculate_attention_score(elements_found)
        }
        
        # Check for level progression
        next_level_unlocked = False
        if mission_completed:
            observation_missions = user_progress.observation_missions_completed
            if fragment_id not in observation_missions:
                observation_missions.append(fragment_id)
                user_progress.observation_missions_completed = observation_missions
                
                # Check if ready for next level
                if self._check_level_progression_readiness(user_progress, current_level):
                    next_level_unlocked = True
                    user_progress.current_level = current_level + 1
                    user_progress.record_level_progression(
                        current_level + 1, 
                        f"observation_mission_completed_{fragment_id}"
                    )
        
        await self.session.commit()
        
        return MissionValidationResult(
            mission_completed=mission_completed,
            score=final_score,
            archetype_indicators=archetype_indicators,
            performance_metrics=performance_metrics,
            next_level_unlocked=next_level_unlocked,
            rewards_earned=self._calculate_observation_rewards(final_score, current_level),
            feedback_message=self._generate_observation_feedback(
                final_score, archetype_indicators, current_level
            )
        )
    
    async def validate_comprehension_test(
        self,
        user_id: int,
        fragment_id: str,
        test_responses: Dict[str, Any]
    ) -> MissionValidationResult:
        """
        Validate comprehension test performance.
        
        Evaluates:
        - Understanding of Diana's personality and motivations
        - Emotional intelligence in responses
        - Depth of analysis and interpretation
        - Empathy vs possessiveness indicators
        """
        user_progress = await self._get_user_mission_progress(user_id)
        current_level = user_progress.current_level
        
        # Extract comprehension metrics
        total_questions = test_responses.get('total_questions', 0)
        responses = test_responses.get('responses', [])
        response_times = test_responses.get('response_times', [])
        
        # Analyze response quality
        comprehension_score = await self._analyze_comprehension_responses(
            responses, current_level, user_id
        )
        
        # Calculate emotional intelligence indicators
        emotional_patterns = self._analyze_emotional_intelligence(responses)
        
        # Diana-specific comprehension analysis
        diana_understanding_score = self._analyze_diana_comprehension(
            responses, current_level
        )
        
        # Apply level difficulty scaling
        difficulty = self.level_difficulty_scaling[current_level]['comprehension']
        final_score = int(comprehension_score * (1 + difficulty * 0.3))
        final_score = min(final_score, 100)
        
        # Analyze archetype indicators from response patterns
        archetype_indicators = self._analyze_comprehension_archetypes(
            responses, response_times, emotional_patterns
        )
        
        # Update user archetype scores
        await self._update_archetype_scores(user_id, archetype_indicators)
        
        # Check if mission completed
        threshold = self.progression_thresholds[current_level]
        mission_completed = final_score >= threshold
        
        # Prepare performance metrics
        performance_metrics = {
            'total_questions': total_questions,
            'responses_analyzed': len(responses),
            'diana_understanding_score': diana_understanding_score,
            'emotional_intelligence_score': self._calculate_ei_score(emotional_patterns),
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'empathy_indicators': len([p for p in emotional_patterns if 'empathy' in p]),
            'possessiveness_warnings': len([p for p in emotional_patterns if 'possessive' in p])
        }
        
        # Check for level progression
        next_level_unlocked = False
        if mission_completed:
            comprehension_tests = user_progress.comprehension_tests_passed
            if fragment_id not in comprehension_tests:
                comprehension_tests.append(fragment_id)
                user_progress.comprehension_tests_passed = comprehension_tests
                user_progress.diana_comprehension_score = diana_understanding_score
                
                if self._check_level_progression_readiness(user_progress, current_level):
                    next_level_unlocked = True
                    user_progress.current_level = current_level + 1
                    user_progress.record_level_progression(
                        current_level + 1,
                        f"comprehension_test_passed_{fragment_id}"
                    )
        
        await self.session.commit()
        
        return MissionValidationResult(
            mission_completed=mission_completed,
            score=final_score,
            archetype_indicators=archetype_indicators,
            performance_metrics=performance_metrics,
            next_level_unlocked=next_level_unlocked,
            rewards_earned=self._calculate_comprehension_rewards(final_score, current_level),
            feedback_message=self._generate_comprehension_feedback(
                final_score, diana_understanding_score, emotional_patterns, current_level
            )
        )
    
    async def validate_synthesis_challenge(
        self,
        user_id: int,
        fragment_id: str,
        synthesis_data: Dict[str, Any]
    ) -> MissionValidationResult:
        """
        Validate synthesis challenge performance.
        
        Evaluates:
        - Ability to integrate multiple storyline levels
        - Creative connections between concepts
        - Narrative coherence and understanding
        - Original insights and personal growth
        """
        user_progress = await self._get_user_mission_progress(user_id)
        current_level = user_progress.current_level
        
        # Extract synthesis metrics
        concepts_referenced = synthesis_data.get('concepts_referenced', [])
        cross_level_connections = synthesis_data.get('level_connections', [])
        original_insights = synthesis_data.get('original_insights', [])
        narrative_coherence_indicators = synthesis_data.get('coherence_indicators', [])
        
        # Calculate synthesis score
        base_score = self._calculate_synthesis_score(
            concepts_referenced, cross_level_connections, 
            original_insights, narrative_coherence_indicators
        )
        
        # Apply level difficulty scaling
        difficulty = self.level_difficulty_scaling[current_level]['synthesis']
        final_score = int(base_score * (1 + difficulty * 0.4))
        final_score = min(final_score, 100)
        
        # Analyze archetype indicators
        archetype_indicators = self._analyze_synthesis_archetypes(
            concepts_referenced, cross_level_connections, original_insights
        )
        
        # Update user archetype scores
        await self._update_archetype_scores(user_id, archetype_indicators)
        
        # Check if mission completed
        threshold = self.progression_thresholds[current_level]
        mission_completed = final_score >= threshold
        
        # Prepare performance metrics
        performance_metrics = {
            'concepts_integrated': len(concepts_referenced),
            'cross_level_connections': len(cross_level_connections),
            'original_insights': len(original_insights),
            'narrative_coherence_score': self._calculate_coherence_score(narrative_coherence_indicators),
            'creativity_score': self._calculate_creativity_score(original_insights),
            'synthesis_depth': self._calculate_synthesis_depth(concepts_referenced, cross_level_connections)
        }
        
        # Check for level progression and special achievements
        next_level_unlocked = False
        rewards = []
        
        if mission_completed:
            synthesis_challenges = user_progress.synthesis_challenges_completed
            if fragment_id not in synthesis_challenges:
                synthesis_challenges.append(fragment_id)
                user_progress.synthesis_challenges_completed = synthesis_challenges
                user_progress.synthesis_creativity_score = performance_metrics['creativity_score']
                
                # Check for special achievements
                if final_score >= 90 and current_level >= 5:
                    user_progress.circle_intimo_access = True
                    rewards.append({
                        'type': 'special_access',
                        'description': 'Círculo Íntimo de Diana desbloqueado',
                        'value': 'circle_intimo_access'
                    })
                
                if len(synthesis_challenges) >= 3 and current_level == 6:
                    user_progress.guardian_of_secrets_status = True
                    user_progress.narrative_synthesis_completed = True
                    rewards.append({
                        'type': 'achievement',
                        'description': 'Guardián de Secretos - Síntesis Narrativa Completa',
                        'value': 'guardian_of_secrets'
                    })
                
                if self._check_level_progression_readiness(user_progress, current_level):
                    next_level_unlocked = True
                    user_progress.current_level = min(current_level + 1, 6)
                    user_progress.record_level_progression(
                        min(current_level + 1, 6),
                        f"synthesis_challenge_completed_{fragment_id}"
                    )
        
        rewards.extend(self._calculate_synthesis_rewards(final_score, current_level))
        
        await self.session.commit()
        
        return MissionValidationResult(
            mission_completed=mission_completed,
            score=final_score,
            archetype_indicators=archetype_indicators,
            performance_metrics=performance_metrics,
            next_level_unlocked=next_level_unlocked,
            rewards_earned=rewards,
            feedback_message=self._generate_synthesis_feedback(
                final_score, performance_metrics, current_level
            )
        )
    
    async def get_user_archetype_analysis(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive archetype analysis for a user."""
        archetype = await self._get_user_archetype(user_id)
        mission_progress = await self._get_user_mission_progress(user_id)
        
        if not archetype:
            return {
                'dominant_archetype': None,
                'archetype_distribution': {},
                'behavioral_insights': [],
                'personalization_recommendations': []
            }
        
        distribution = archetype.get_archetype_distribution()
        archetype.calculate_dominant_archetype()
        
        return {
            'dominant_archetype': archetype.dominant_archetype,
            'archetype_distribution': distribution,
            'behavioral_insights': self._generate_behavioral_insights(archetype),
            'personalization_recommendations': self._generate_personalization_recommendations(
                archetype, mission_progress
            ),
            'archetype_evolution': self._analyze_archetype_evolution(archetype),
            'diana_interaction_style': self._recommend_diana_interaction_style(archetype)
        }
    
    # Private helper methods
    
    async def _get_user_mission_progress(self, user_id: int) -> UserMissionProgress:
        """Get or create user mission progress."""
        stmt = select(UserMissionProgress).where(UserMissionProgress.user_id == user_id)
        result = await self.session.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = UserMissionProgress(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
        
        return progress
    
    async def _get_user_archetype(self, user_id: int) -> UserArchetype:
        """Get or create user archetype."""
        stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
        result = await self.session.execute(stmt)
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            archetype = UserArchetype(user_id=user_id)
            self.session.add(archetype)
            await self.session.commit()
            await self.session.refresh(archetype)
        
        return archetype
    
    def _calculate_observation_score(
        self, time_spent: int, elements_found: int, revisit_count: int, pattern: str
    ) -> int:
        """Calculate base observation score."""
        # Base score from time spent (0-40 points)
        time_score = min(time_spent / 300, 1.0) * 40  # 5 minutes = max time score
        
        # Elements found score (0-30 points)
        elements_score = min(elements_found * 5, 30)
        
        # Revisit bonus (0-15 points) - shows thoroughness
        revisit_score = min(revisit_count * 3, 15)
        
        # Pattern bonus (0-15 points)
        pattern_bonus = {
            'thorough': 15, 'intuitive': 12, 'systematic': 10, 'linear': 8
        }.get(pattern, 5)
        
        return int(time_score + elements_score + revisit_score + pattern_bonus)
    
    def _analyze_observation_archetypes(
        self, time_spent: int, revisit_count: int, pattern: str, elements_found: int
    ) -> Dict[ArchetypeClass, float]:
        """Analyze archetype indicators from observation behavior."""
        indicators = {}
        
        # Explorer archetype indicators
        if revisit_count > 2 and elements_found > 3:
            indicators[ArchetypeClass.EXPLORER] = 0.8
        elif revisit_count > 0:
            indicators[ArchetypeClass.EXPLORER] = 0.4
        
        # Direct archetype indicators
        if time_spent < 60 and pattern == 'linear':
            indicators[ArchetypeClass.DIRECT] = 0.7
        
        # Analytical archetype indicators  
        if pattern == 'systematic' and time_spent > 180:
            indicators[ArchetypeClass.ANALYTICAL] = 0.8
        
        # Patient archetype indicators
        if time_spent > 300:
            indicators[ArchetypeClass.PATIENT] = 0.6
        
        # Persistent archetype indicators
        if revisit_count > 3:
            indicators[ArchetypeClass.PERSISTENT] = 0.7
        
        return indicators
    
    def _analyze_comprehension_archetypes(
        self, responses: List[str], response_times: List[int], emotional_patterns: List[str]
    ) -> Dict[ArchetypeClass, float]:
        """Analyze archetype indicators from comprehension responses."""
        indicators = {}
        
        # Analyze response content for patterns
        total_words = sum(len(r.split()) for r in responses)
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Romantic archetype indicators
        romantic_words = ['amor', 'corazón', 'alma', 'sentir', 'emoción', 'pasión', 'deseo']
        romantic_count = sum(1 for response in responses for word in romantic_words if word in response.lower())
        if romantic_count > 3 or 'poetic' in emotional_patterns:
            indicators[ArchetypeClass.ROMANTIC] = min(romantic_count * 0.2, 0.9)
        
        # Analytical archetype indicators
        analytical_words = ['análisis', 'comprendo', 'entiendo', 'reflexión', 'considero', 'evalúo']
        analytical_count = sum(1 for response in responses for word in analytical_words if word in response.lower())
        if analytical_count > 2 and avg_response_time > 30:
            indicators[ArchetypeClass.ANALYTICAL] = min(analytical_count * 0.25, 0.9)
        
        # Direct archetype indicators
        if total_words / len(responses) < 20 and avg_response_time < 15:
            indicators[ArchetypeClass.DIRECT] = 0.7
        
        # Patient archetype indicators
        if avg_response_time > 45:
            indicators[ArchetypeClass.PATIENT] = min(avg_response_time / 60, 0.9)
        
        return indicators
    
    def _analyze_synthesis_archetypes(
        self, concepts: List[str], connections: List[str], insights: List[str]
    ) -> Dict[ArchetypeClass, float]:
        """Analyze archetype indicators from synthesis performance."""
        indicators = {}
        
        # Explorer archetype - wide range of concepts
        if len(concepts) > 5:
            indicators[ArchetypeClass.EXPLORER] = min(len(concepts) * 0.1, 0.9)
        
        # Analytical archetype - many connections
        if len(connections) > 3:
            indicators[ArchetypeClass.ANALYTICAL] = min(len(connections) * 0.2, 0.9)
        
        # Romantic archetype - emotional insights
        emotional_insights = [i for i in insights if any(word in i.lower() for word in ['sentir', 'emoción', 'corazón', 'alma'])]
        if len(emotional_insights) > 1:
            indicators[ArchetypeClass.ROMANTIC] = min(len(emotional_insights) * 0.3, 0.9)
        
        return indicators
    
    async def _update_archetype_scores(self, user_id: int, indicators: Dict[ArchetypeClass, float]):
        """Update user archetype scores based on mission performance."""
        archetype = await self._get_user_archetype(user_id)
        
        for archetype_class, score in indicators.items():
            current_score = getattr(archetype, f"{archetype_class.value}_score", 0)
            # Weighted average with new score having 30% influence
            new_score = int(current_score * 0.7 + score * 100 * 0.3)
            setattr(archetype, f"{archetype_class.value}_score", min(new_score, 100))
        
        archetype.calculate_dominant_archetype()
        await self.session.commit()
    
    def _check_level_progression_readiness(self, progress: UserMissionProgress, current_level: int) -> bool:
        """Check if user is ready to progress to next level."""
        if current_level >= 6:  # Max level
            return False
        
        # Require completion of all mission types for current level
        observation_count = len(progress.observation_missions_completed)
        comprehension_count = len(progress.comprehension_tests_passed)
        synthesis_count = len(progress.synthesis_challenges_completed)
        
        # Level progression requirements
        level_requirements = {
            1: {'observation': 1, 'comprehension': 1, 'synthesis': 0},  # Level 1->2
            2: {'observation': 2, 'comprehension': 1, 'synthesis': 1},  # Level 2->3
            3: {'observation': 3, 'comprehension': 2, 'synthesis': 1},  # Level 3->4 (VIP)
            4: {'observation': 2, 'comprehension': 3, 'synthesis': 2},  # Level 4->5
            5: {'observation': 3, 'comprehension': 3, 'synthesis': 3},  # Level 5->6 (Elite)
        }
        
        requirements = level_requirements.get(current_level, {})
        
        return (
            observation_count >= requirements.get('observation', 0) and
            comprehension_count >= requirements.get('comprehension', 0) and
            synthesis_count >= requirements.get('synthesis', 0)
        )
    
    def _calculate_attention_score(self, elements_found: List[str]) -> int:
        """Calculate attention to detail score."""
        if not elements_found:
            return 0
        
        # Score based on difficulty of elements found
        difficulty_scores = {
            'subtle_hint': 5, 'hidden_text': 8, 'color_change': 3,
            'pattern_recognition': 10, 'contextual_clue': 7, 'emotional_subtext': 12
        }
        
        total_score = sum(difficulty_scores.get(element, 5) for element in elements_found)
        return min(total_score, 100)
    
    def _analyze_emotional_intelligence(self, responses: List[str]) -> List[str]:
        """Analyze emotional intelligence indicators in responses."""
        patterns = []
        
        for response in responses:
            response_lower = response.lower()
            
            # Empathy indicators
            if any(word in response_lower for word in ['comprendo', 'entiendo', 'siento', 'me pongo en']):
                patterns.append('empathy')
            
            # Possessiveness warnings
            if any(word in response_lower for word in ['mía', 'mío', 'poseer', 'controlar', 'dominar']):
                patterns.append('possessive')
            
            # Emotional maturity
            if any(word in response_lower for word in ['respeto', 'límites', 'espacio', 'autonomía']):
                patterns.append('emotional_maturity')
            
            # Poetic expression
            if len([w for w in response.split() if len(w) > 6]) > 3:
                patterns.append('poetic')
        
        return patterns
    
    def _analyze_diana_comprehension(self, responses: List[str], level: int) -> int:
        """Analyze how well user understands Diana's character."""
        diana_understanding_indicators = [
            'misterio', 'enigma', 'compleja', 'seductora', 'intelectual',
            'vulnerable', 'profunda', 'contradicción', 'capas', 'distancia'
        ]
        
        total_score = 0
        for response in responses:
            response_lower = response.lower()
            indicators_found = sum(1 for indicator in diana_understanding_indicators if indicator in response_lower)
            total_score += indicators_found * 8  # 8 points per indicator
        
        # Bonus for level-appropriate understanding
        level_bonus = level * 5
        final_score = min(total_score + level_bonus, 100)
        
        return final_score
    
    def _calculate_synthesis_score(
        self, concepts: List[str], connections: List[str], 
        insights: List[str], coherence_indicators: List[str]
    ) -> int:
        """Calculate synthesis challenge score."""
        # Base scores
        concept_score = min(len(concepts) * 8, 32)      # Max 32 points
        connection_score = min(len(connections) * 10, 30)  # Max 30 points
        insight_score = min(len(insights) * 12, 24)     # Max 24 points
        coherence_score = min(len(coherence_indicators) * 7, 14)  # Max 14 points
        
        return int(concept_score + connection_score + insight_score + coherence_score)
    
    def _calculate_observation_rewards(self, score: int, level: int) -> List[Dict[str, Any]]:
        """Calculate rewards for observation mission completion."""
        rewards = []
        
        if score >= 70:
            rewards.append({
                'type': 'points',
                'description': f'Puntos por observación detallada (Nivel {level})',
                'value': level * 50 + score
            })
        
        if score >= 90:
            rewards.append({
                'type': 'clue',
                'description': 'Pista especial desbloqueada por observación excepcional',
                'value': f'observation_master_L{level}'
            })
        
        return rewards
    
    def _calculate_comprehension_rewards(self, score: int, level: int) -> List[Dict[str, Any]]:
        """Calculate rewards for comprehension test completion."""
        rewards = []
        
        if score >= 75:
            rewards.append({
                'type': 'points',
                'description': f'Puntos por comprensión profunda (Nivel {level})',
                'value': level * 75 + score
            })
        
        if score >= 85:
            rewards.append({
                'type': 'unlock',
                'description': 'Contenido personalizado desbloqueado',
                'value': f'personalized_content_L{level}'
            })
        
        return rewards
    
    def _calculate_synthesis_rewards(self, score: int, level: int) -> List[Dict[str, Any]]:
        """Calculate rewards for synthesis challenge completion."""
        rewards = []
        
        if score >= 80:
            rewards.append({
                'type': 'points',
                'description': f'Puntos por síntesis creativa (Nivel {level})',
                'value': level * 100 + score
            })
        
        if score >= 95:
            rewards.append({
                'type': 'achievement',
                'description': 'Maestro de la Síntesis Narrativa',
                'value': 'synthesis_master'
            })
        
        return rewards
    
    def _generate_observation_feedback(
        self, score: int, archetype_indicators: Dict[ArchetypeClass, float], level: int
    ) -> str:
        """Generate personalized feedback for observation mission."""
        dominant_archetype = max(archetype_indicators, key=archetype_indicators.get) if archetype_indicators else None
        
        if score >= 90:
            base_message = "Observación excepcional. Diana nota tu atención a cada detalle."
        elif score >= 75:
            base_message = "Buena observación. Has captado elementos que otros pasan por alto."
        elif score >= 60:
            base_message = "Observación adecuada, pero hay sutilezas que aún te esperan."
        else:
            base_message = "Tu observación necesita profundizar más en los detalles ocultos."
        
        # Add archetype-specific feedback
        if dominant_archetype == ArchetypeClass.EXPLORER:
            base_message += " Tu naturaleza exploradora se nota en cómo examinas cada rincón."
        elif dominant_archetype == ArchetypeClass.PATIENT:
            base_message += " Tu paciencia para observar te revela secretos únicos."
        
        return base_message
    
    def _generate_comprehension_feedback(
        self, score: int, diana_score: int, emotional_patterns: List[str], level: int
    ) -> str:
        """Generate personalized feedback for comprehension test."""
        if score >= 85 and diana_score >= 80:
            return "Comprensión excepcional. Realmente entiendes las capas de Diana."
        elif 'possessive' in emotional_patterns:
            return "Tu comprensión es buena, pero recuerda que Diana valora su autonomía."
        elif 'empathy' in emotional_patterns and 'emotional_maturity' in emotional_patterns:
            return "Demuestras una comprensión madura y empática. Diana aprecia esa profundidad."
        elif score >= 70:
            return "Comprensión sólida. Continúa explorando las motivaciones más profundas."
        else:
            return "Hay aspectos de Diana que aún necesitan mayor exploración."
    
    def _generate_synthesis_feedback(
        self, score: int, performance_metrics: Dict[str, Any], level: int
    ) -> str:
        """Generate personalized feedback for synthesis challenge."""
        creativity = performance_metrics.get('creativity_score', 0)
        connections = performance_metrics.get('cross_level_connections', 0)
        
        if score >= 90 and creativity >= 80:
            return "Síntesis brillante. Has creado conexiones que van más allá de lo esperado."
        elif connections >= 3:
            return "Excelente capacidad de conectar conceptos a través de los niveles narrativos."
        elif score >= 75:
            return "Buena síntesis. Tus insights muestran comprensión profunda del viaje narrativo."
        else:
            return "Tu síntesis necesita integrar más elementos de los diferentes niveles de la historia."
    
    def _calculate_ei_score(self, emotional_patterns: List[str]) -> int:
        """Calculate emotional intelligence score from patterns."""
        positive_patterns = ['empathy', 'emotional_maturity']
        negative_patterns = ['possessive']
        
        positive_count = sum(1 for p in emotional_patterns if p in positive_patterns)
        negative_count = sum(1 for p in emotional_patterns if p in negative_patterns)
        
        base_score = positive_count * 25 - negative_count * 15
        return max(min(base_score, 100), 0)
    
    def _calculate_coherence_score(self, coherence_indicators: List[str]) -> int:
        """Calculate narrative coherence score."""
        return min(len(coherence_indicators) * 15, 100)
    
    def _calculate_creativity_score(self, insights: List[str]) -> int:
        """Calculate creativity score from original insights."""
        if not insights:
            return 0
        
        # Score based on uniqueness and depth
        base_score = len(insights) * 20
        return min(base_score, 100)
    
    def _calculate_synthesis_depth(self, concepts: List[str], connections: List[str]) -> int:
        """Calculate synthesis depth score."""
        if not concepts:
            return 0
        
        connection_ratio = len(connections) / len(concepts) if concepts else 0
        return int(connection_ratio * 100)
    
    def _generate_behavioral_insights(self, archetype: UserArchetype) -> List[str]:
        """Generate behavioral insights from archetype analysis."""
        insights = []
        distribution = archetype.get_archetype_distribution()
        
        for archetype_type, percentage in distribution.items():
            if percentage > 30:
                if archetype_type == 'explorer':
                    insights.append(f"Muestra {percentage}% tendencia exploradora - busca detalles y revisita contenido")
                elif archetype_type == 'romantic':
                    insights.append(f"Demuestra {percentage}% naturaleza romántica - busca conexión emocional profunda")
                elif archetype_type == 'analytical':
                    insights.append(f"Presenta {percentage}% enfoque analítico - procesa información sistemáticamente")
                # Add more archetype insights...
        
        return insights
    
    def _generate_personalization_recommendations(
        self, archetype: UserArchetype, progress: UserMissionProgress
    ) -> List[str]:
        """Generate personalization recommendations."""
        recommendations = []
        
        if archetype.dominant_archetype == 'explorer':
            recommendations.append("Incluir más elementos ocultos y pistas para descubrir")
            recommendations.append("Ofrecer contenido adicional para profundizar")
        elif archetype.dominant_archetype == 'romantic':
            recommendations.append("Enfatizar aspectos emocionales en las interacciones")
            recommendations.append("Usar lenguaje más poético y evocativo")
        elif archetype.dominant_archetype == 'analytical':
            recommendations.append("Proporcionar contexto y explicaciones detalladas")
            recommendations.append("Incluir elementos de reflexión y análisis")
        
        return recommendations
    
    def _analyze_archetype_evolution(self, archetype: UserArchetype) -> Dict[str, Any]:
        """Analyze how user's archetype has evolved over time."""
        # This would analyze historical data to show archetype changes
        # For now, return basic evolution tracking
        return {
            'current_dominant': archetype.dominant_archetype,
            'stability_score': 85,  # How stable the archetype has been
            'evolution_trend': 'growing_more_analytical',
            'recent_changes': []
        }
    
    def _recommend_diana_interaction_style(self, archetype: UserArchetype) -> Dict[str, str]:
        """Recommend Diana interaction style based on user archetype."""
        style_recommendations = {
            'explorer': 'mysterious_revealing',
            'romantic': 'emotionally_intimate',
            'analytical': 'intellectually_challenging',
            'direct': 'straightforward_honest',
            'patient': 'slowly_unfolding',
            'persistent': 'gradually_rewarding'
        }
        
        dominant = archetype.dominant_archetype
        return {
            'recommended_style': style_recommendations.get(dominant, 'balanced'),
            'interaction_approach': f"Adapt Diana's responses to match {dominant} archetype preferences",
            'content_emphasis': self._get_content_emphasis_for_archetype(dominant)
        }
    
    def _get_content_emphasis_for_archetype(self, archetype: str) -> str:
        """Get content emphasis recommendation for archetype."""
        emphases = {
            'explorer': 'hidden_details_and_discoveries',
            'romantic': 'emotional_depth_and_connection',
            'analytical': 'intellectual_complexity',
            'direct': 'clear_progression_markers',
            'patient': 'layered_revelation',
            'persistent': 'challenging_but_achievable'
        }
        return emphases.get(archetype, 'balanced_approach')