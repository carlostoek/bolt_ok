# services/emotional_service.py
"""
Emotional Intelligence Service
Integrates seamlessly with existing User and UserStats models.
Provides emotional tracking without breaking current functionality.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from database.models import User, UserStats
from database.emotional_models import (
    UserEmotionalProfile,
    EmotionalInteraction,
    ConversationMemory,
    EmotionalTrigger,
    EmotionalAnalysisSession,
    ArchetypeClassification,
    EmotionalState,
    InteractionType
)
from typing import Optional, List, Dict, Tuple
import datetime
import logging
import json

logger = logging.getLogger(__name__)


class EmotionalService:
    """
    Provides emotional intelligence capabilities that extend existing user tracking.
    All methods are optional - system continues working without emotional data.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model_version = "1.0"
    
    # CORE PROFILE MANAGEMENT
    
    async def get_or_create_emotional_profile(self, user_id: int) -> UserEmotionalProfile:
        """
        Gets existing emotional profile or creates new one.
        Integrates with existing User model via foreign key.
        """
        try:
            # First ensure user exists in main User table
            user = await self.session.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} not found in main User table")
                return None
            
            # Get or create emotional profile
            profile = await self.session.get(UserEmotionalProfile, user_id)
            if not profile:
                profile = UserEmotionalProfile(
                    user_id=user_id,
                    archetype_classification=ArchetypeClassification.UNDEFINED,
                    emotional_signature={},
                    vulnerability_level=0.0,
                    authenticity_score=0.5,
                    response_time_pattern={},
                    classification_version=self.model_version
                )
                self.session.add(profile)
                await self.session.commit()
                await self.session.refresh(profile)
                logger.info(f"Created new emotional profile for user {user_id}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error managing emotional profile for user {user_id}: {e}")
            await self.session.rollback()
            return None
    
    async def update_archetype(self, user_id: int, new_archetype: ArchetypeClassification, 
                             confidence: float = 0.8) -> bool:
        """Updates user's archetype classification based on behavioral analysis"""
        try:
            profile = await self.get_or_create_emotional_profile(user_id)
            if not profile:
                return False
            
            # Only update if confidence is higher than current
            if confidence > profile.archetype_confidence:
                old_archetype = profile.archetype_classification
                profile.archetype_classification = new_archetype
                profile.archetype_confidence = confidence
                profile.last_updated_at = datetime.datetime.utcnow()
                
                await self.session.commit()
                logger.info(f"✨ Diana ha ajustado su percepción de ti: {old_archetype} cambió a {new_archetype} (confianza: {confidence})")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error updating archetype for user {user_id}: {e}")
            await self.session.rollback()
            return False
    
    # INTERACTION TRACKING
    
    async def record_interaction(
        self,
        user_id: int,
        interaction_type: InteractionType,
        emotional_state: Optional[EmotionalState] = None,
        response_timing: Optional[float] = None,
        vulnerability_level: float = 0.0,
        authenticity_score: float = 0.5,
        context_data: Optional[Dict] = None
    ) -> bool:
        """
        Records emotional interaction without breaking existing functionality.
        All parameters except user_id and interaction_type are optional.
        """
        try:
            # Verify user exists (integration with existing User model)
            user = await self.session.get(User, user_id)
            if not user:
                logger.warning(f"Cannot record interaction for non-existent user {user_id}")
                return False
            
            interaction = EmotionalInteraction(
                user_id=user_id,
                interaction_type=interaction_type,
                emotional_context=emotional_state,
                response_timing=response_timing,
                vulnerability_displayed=vulnerability_level,
                authenticity_score=authenticity_score,
                interaction_metadata=context_data or {}
            )
            
            self.session.add(interaction)
            
            # Update profile counters
            profile = await self.get_or_create_emotional_profile(user_id)
            if profile:
                profile.total_interactions_analyzed += 1
                profile.last_updated_at = datetime.datetime.utcnow()
                if emotional_state:
                    profile.last_emotion_detected_at = datetime.datetime.utcnow()
                    
                # Update emotional signature
                signature = profile.emotional_signature or {}
                emotion_key = emotional_state.value if emotional_state else "neutral"
                signature[emotion_key] = signature.get(emotion_key, 0) + 1
                profile.emotional_signature = signature
            
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error recording interaction for user {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def create_memory(
        self,
        user_id: int,
        conversation_point: str,
        emotional_state: EmotionalState,
        memory_content: str,
        emotional_impact: float = 0.5,
        narrative_fragment: Optional[str] = None,
        is_core_memory: bool = False
    ) -> bool:
        """Creates significant conversation memory for future narrative personalization"""
        try:
            memory = ConversationMemory(
                user_id=user_id,
                conversation_point=conversation_point,
                emotional_state=emotional_state,
                memory_reference=memory_content,
                emotional_impact=emotional_impact,
                narrative_fragment_key=narrative_fragment,
                is_core_memory=is_core_memory,
                affects_future_narrative=True
            )
            
            self.session.add(memory)
            await self.session.commit()
            
            logger.info(f"Created memory for user {user_id}: {conversation_point}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating memory for user {user_id}: {e}")
            await self.session.rollback()
            return False
    
    # ANALYSIS AND INSIGHTS
    
    async def analyze_user_emotional_patterns(self, user_id: int) -> Optional[Dict]:
        """
        Analyzes user's emotional patterns without affecting existing functionality.
        Returns insights for narrative personalization.
        """
        try:
            # Get recent interactions
            interactions_query = select(EmotionalInteraction).where(
                and_(
                    EmotionalInteraction.user_id == user_id,
                    EmotionalInteraction.interaction_timestamp >= datetime.datetime.utcnow() - datetime.timedelta(days=30)
                )
            ).order_by(desc(EmotionalInteraction.interaction_timestamp)).limit(100)
            
            result = await self.session.execute(interactions_query)
            interactions = result.scalars().all()
            
            if not interactions:
                return {"status": "insufficient_data", "interactions_count": 0}
            
            # Analyze patterns
            emotions_count = {}
            total_vulnerability = 0.0
            total_authenticity = 0.0
            response_times = []
            
            for interaction in interactions:
                if interaction.emotional_context:
                    emotion = interaction.emotional_context.value
                    emotions_count[emotion] = emotions_count.get(emotion, 0) + 1
                
                total_vulnerability += interaction.vulnerability_displayed or 0.0
                total_authenticity += interaction.authenticity_score or 0.5
                
                if interaction.response_timing:
                    response_times.append(interaction.response_timing)
            
            # Calculate insights
            dominant_emotion = max(emotions_count.items(), key=lambda x: x[1])[0] if emotions_count else "neutral"
            avg_vulnerability = total_vulnerability / len(interactions)
            avg_authenticity = total_authenticity / len(interactions)
            avg_response_time = sum(response_times) / len(response_times) if response_times else None
            
            analysis_result = {
                "status": "success",
                "analysis_date": datetime.datetime.utcnow().isoformat(),
                "interactions_analyzed": len(interactions),
                "dominant_emotion": dominant_emotion,
                "emotional_distribution": emotions_count,
                "average_vulnerability": round(avg_vulnerability, 3),
                "average_authenticity": round(avg_authenticity, 3),
                "average_response_time": round(avg_response_time, 2) if avg_response_time else None,
                "emotional_consistency": self._calculate_consistency(emotions_count),
                "narrative_recommendations": self._generate_narrative_recommendations(
                    dominant_emotion, avg_vulnerability, avg_authenticity
                )
            }
            
            # Record analysis session
            await self._record_analysis_session(user_id, "pattern_analysis", analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing emotional patterns for user {user_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_user_memories_for_narrative(self, user_id: int, limit: int = 10) -> List[ConversationMemory]:
        """
        Retrieves significant memories for narrative personalization.
        Integrates with existing narrative system.
        """
        try:
            memories_query = select(ConversationMemory).where(
                and_(
                    ConversationMemory.user_id == user_id,
                    ConversationMemory.affects_future_narrative == True
                )
            ).order_by(
                desc(ConversationMemory.emotional_impact),
                desc(ConversationMemory.memory_created_at)
            ).limit(limit)
            
            result = await self.session.execute(memories_query)
            memories = result.scalars().all()
            
            # Update last_referenced_at
            for memory in memories:
                memory.last_referenced_at = datetime.datetime.utcnow()
            
            await self.session.commit()
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            return []
    
    async def get_emotional_triggers(self, user_id: int) -> List[EmotionalTrigger]:
        """Gets known emotional triggers for careful narrative handling"""
        try:
            triggers_query = select(EmotionalTrigger).where(
                EmotionalTrigger.user_id == user_id
            ).order_by(desc(EmotionalTrigger.trigger_strength))
            
            result = await self.session.execute(triggers_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving triggers for user {user_id}: {e}")
            return []
    
    # INTEGRATION HELPERS
    
    async def enhance_user_stats_with_emotion(self, user_id: int) -> Optional[Dict]:
        """
        Combines existing UserStats with emotional intelligence data.
        Provides enriched user understanding without breaking existing code.
        """
        try:
            # Get existing user stats (from existing system)
            user_stats = await self.session.get(UserStats, user_id)
            user = await self.session.get(User, user_id)
            emotional_profile = await self.session.get(UserEmotionalProfile, user_id)
            
            if not user:
                return None
            
            # Create enhanced profile
            enhanced_stats = {
                # Existing stats (safe to access)
                "user_id": user_id,
                "level": user.level,
                "points": user.points,
                "role": user.role,
                "messages_sent": user_stats.messages_sent if user_stats else 0,
                "last_activity": user_stats.last_activity_at.isoformat() if user_stats and user_stats.last_activity_at else None,
                
                # Enhanced emotional data (optional)
                "emotional_profile": {
                    "archetype": emotional_profile.archetype_classification.value if emotional_profile else "undefined",
                    "archetype_confidence": emotional_profile.archetype_confidence if emotional_profile else 0.0,
                    "vulnerability_level": emotional_profile.vulnerability_level if emotional_profile else 0.0,
                    "authenticity_score": emotional_profile.authenticity_score if emotional_profile else 0.5,
                    "dominant_emotion": emotional_profile.dominant_emotion.value if emotional_profile and emotional_profile.dominant_emotion else "neutral",
                    "total_emotional_interactions": emotional_profile.total_interactions_analyzed if emotional_profile else 0
                }
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"Error enhancing user stats for user {user_id}: {e}")
            return None
    
    # PRIVATE HELPER METHODS
    
    def _calculate_consistency(self, emotions_count: Dict) -> float:
        """Calculates emotional consistency score"""
        if not emotions_count:
            return 0.0
        
        total = sum(emotions_count.values())
        if total == 0:
            return 0.0
        
        # Calculate entropy (lower entropy = more consistent)
        import math
        entropy = 0
        for count in emotions_count.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Convert to consistency (0-1, where 1 is most consistent)
        max_entropy = math.log2(len(emotions_count)) if len(emotions_count) > 1 else 1
        consistency = 1 - (entropy / max_entropy) if max_entropy > 0 else 1
        
        return round(consistency, 3)
    
    def _generate_narrative_recommendations(self, dominant_emotion: str, vulnerability: float, authenticity: float) -> Dict:
        """Generates recommendations for narrative adaptation"""
        recommendations = {
            "tone_preference": "neutral",
            "vulnerability_comfort": "medium",
            "interaction_style": "standard",
            "narrative_depth": "medium"
        }
        
        # Tone based on dominant emotion
        if dominant_emotion in ["excited", "playful", "curious"]:
            recommendations["tone_preference"] = "lighthearted"
        elif dominant_emotion in ["contemplative", "serious", "nostalgic"]:
            recommendations["tone_preference"] = "thoughtful"
        elif dominant_emotion in ["anxious", "vulnerable"]:
            recommendations["tone_preference"] = "gentle"
        
        # Vulnerability handling
        if vulnerability > 0.7:
            recommendations["vulnerability_comfort"] = "high"
            recommendations["interaction_style"] = "supportive"
        elif vulnerability < 0.3:
            recommendations["vulnerability_comfort"] = "low"
            recommendations["interaction_style"] = "casual"
        
        # Narrative depth based on authenticity
        if authenticity > 0.8:
            recommendations["narrative_depth"] = "deep"
        elif authenticity < 0.4:
            recommendations["narrative_depth"] = "surface"
        
        return recommendations
    
    async def _record_analysis_session(self, user_id: int, analysis_type: str, results: Dict):
        """Records analysis session for monitoring and improvement"""
        try:
            session_record = EmotionalAnalysisSession(
                user_id=user_id,
                analysis_type=analysis_type,
                model_version=self.model_version,
                emotions_detected=results.get("emotional_distribution", {}),
                confidence_scores={"overall": results.get("average_authenticity", 0.5)},
                interactions_processed=results.get("interactions_analyzed", 0),
                session_completed_at=datetime.datetime.utcnow()
            )
            
            self.session.add(session_record)
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording analysis session: {e}")
            # Don't re-raise - this is just for monitoring
    
    # INTEGRATION WITH EXISTING SERVICES
    
    async def integrate_with_point_service(self, user_id: int, points_awarded: float, context: str = ""):
        """
        Example integration with existing PointService.
        Records emotional context when points are awarded.
        """
        try:
            # This would be called from PointService.add_points() 
            # to add emotional context to point awards
            emotional_state = EmotionalState.EXCITED  # Could be determined by context
            
            await self.record_interaction(
                user_id=user_id,
                interaction_type=InteractionType.ACHIEVEMENT_RESPONSE,
                emotional_state=emotional_state,
                authenticity_score=0.8,  # High authenticity for achievements
                context_data={
                    "points_awarded": points_awarded,
                    "context": context,
                    "source": "point_service_integration"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with point service: {e}")
            return False
    
    async def integrate_with_narrative_choice(self, user_id: int, fragment_key: str, choice_made: str, response_time: float):
        """
        Example integration with narrative system.
        Records emotional context of narrative choices.
        """
        try:
            # Analyze choice for emotional context
            emotional_state = self._analyze_choice_emotion(choice_made)
            vulnerability = self._assess_choice_vulnerability(choice_made)
            
            await self.record_interaction(
                user_id=user_id,
                interaction_type=InteractionType.CHOICE_SELECTION,
                emotional_state=emotional_state,
                response_timing=response_time,
                vulnerability_level=vulnerability,
                context_data={
                    "fragment_key": fragment_key,
                    "choice_made": choice_made,
                    "source": "narrative_integration"
                }
            )
            
            # Create memory if significant choice
            if vulnerability > 0.5:
                await self.create_memory(
                    user_id=user_id,
                    conversation_point=f"choice_{fragment_key}",
                    emotional_state=emotional_state,
                    memory_content=f"User made vulnerable choice: {choice_made}",
                    emotional_impact=vulnerability,
                    narrative_fragment=fragment_key,
                    is_core_memory=vulnerability > 0.8
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with narrative system: {e}")
            return False
    
    def _analyze_choice_emotion(self, choice_text: str) -> EmotionalState:
        """Simple emotion analysis of choice text"""
        choice_lower = choice_text.lower()
        
        if any(word in choice_lower for word in ["excited", "happy", "great", "amazing"]):
            return EmotionalState.EXCITED
        elif any(word in choice_lower for word in ["curious", "wonder", "explore", "learn"]):
            return EmotionalState.CURIOUS
        elif any(word in choice_lower for word in ["serious", "important", "careful"]):
            return EmotionalState.SERIOUS
        elif any(word in choice_lower for word in ["playful", "fun", "joke", "laugh"]):
            return EmotionalState.PLAYFUL
        else:
            return EmotionalState.NEUTRAL
    
    def _assess_choice_vulnerability(self, choice_text: str) -> float:
        """Assess vulnerability level of a choice"""
        vulnerable_keywords = ["afraid", "scared", "worried", "personal", "secret", "share", "trust", "vulnerable"]
        choice_lower = choice_text.lower()
        
        vulnerability_count = sum(1 for keyword in vulnerable_keywords if keyword in choice_lower)
        return min(vulnerability_count * 0.3, 1.0)
