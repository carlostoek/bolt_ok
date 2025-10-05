# examples/emotional_integration_example.py
"""
Example Integration: Emotional Tracking with Existing Services
Demonstrates how to add emotional intelligence without breaking existing functionality.
All emotional tracking is optional and enhances existing features.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UserStats
from database.emotional_models import (
    UserEmotionalProfile, EmotionalInteraction, ConversationMemory,
    ArchetypeClassification, EmotionalState, InteractionType
)
from services.emotional_service import EmotionalService
import asyncio
import logging

logger = logging.getLogger(__name__)


class EnhancedPointService:
    """
    Example of how to enhance existing PointService with emotional intelligence.
    Maintains full backward compatibility while adding emotional context.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.emotional_service = EmotionalService(session)
    
    async def add_points_with_emotion(
        self, 
        user_id: int, 
        points: float, 
        source: str = "general",
        emotional_context: str = None
    ) -> bool:
        """
        Enhanced version of add_points that includes emotional tracking.
        Falls back gracefully if emotional service fails.
        """
        try:
            # EXISTING FUNCTIONALITY (unchanged)
            user = await self.session.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return False
            
            # Award points (existing logic)
            user.points += points
            await self.session.commit()
            
            # NEW: Add emotional context (optional enhancement)
            try:
                # Determine emotional state from context
                emotional_state = self._analyze_point_context(source, points)
                
                # Record the emotional interaction
                await self.emotional_service.record_interaction(
                    user_id=user_id,
                    interaction_type=InteractionType.ACHIEVEMENT_RESPONSE,
                    emotional_state=emotional_state,
                    authenticity_score=0.8,  # Points usually indicate genuine achievement
                    context_data={
                        "points_awarded": points,
                        "source": source,
                        "context": emotional_context
                    }
                )
                
                logger.debug(f"Recorded emotional context for point award: {emotional_state}")
                
            except Exception as e:
                # Emotional tracking failure doesn't break point awarding
                logger.warning(f"Emotional tracking failed for user {user_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding points to user {user_id}: {e}")
            await self.session.rollback()
            return False
    
    def _analyze_point_context(self, source: str, points: float) -> EmotionalState:
        """Analyze point award context to determine likely emotional state"""
        
        if points >= 100:
            return EmotionalState.EXCITED
        elif "achievement" in source.lower():
            return EmotionalState.CONFIDENT
        elif "daily" in source.lower() or "routine" in source.lower():
            return EmotionalState.NEUTRAL
        elif points <= 1:
            return EmotionalState.CURIOUS
        else:
            return EmotionalState.NEUTRAL


class EnhancedNarrativeService:
    """
    Example of how to enhance narrative choices with emotional intelligence.
    Maintains existing narrative functionality while adding emotional context.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.emotional_service = EmotionalService(session)
    
    async def record_narrative_choice_with_emotion(
        self,
        user_id: int,
        fragment_key: str, 
        choice_text: str,
        response_time_seconds: float = None
    ) -> bool:
        """
        Enhanced narrative choice recording with emotional intelligence.
        Existing narrative system continues working even if emotional tracking fails.
        """
        try:
            # EXISTING NARRATIVE LOGIC (unchanged)
            # ... existing choice recording logic would go here ...
            
            # NEW: Add emotional intelligence (optional enhancement)
            try:
                # Analyze the emotional content of the choice
                emotional_state = self._analyze_choice_emotion(choice_text)
                vulnerability_level = self._assess_choice_vulnerability(choice_text)
                
                # Record the emotional interaction
                await self.emotional_service.record_interaction(
                    user_id=user_id,
                    interaction_type=InteractionType.CHOICE_SELECTION,
                    emotional_state=emotional_state,
                    response_timing=response_time_seconds,
                    vulnerability_level=vulnerability_level,
                    context_data={
                        "fragment_key": fragment_key,
                        "choice_text": choice_text
                    }
                )
                
                # Create memory for significant emotional moments
                if vulnerability_level > 0.6:
                    await self.emotional_service.create_memory(
                        user_id=user_id,
                        conversation_point=f"vulnerable_choice_{fragment_key}",
                        emotional_state=emotional_state,
                        memory_content=f"User made vulnerable choice: {choice_text}",
                        emotional_impact=vulnerability_level,
                        narrative_fragment=fragment_key,
                        is_core_memory=vulnerability_level > 0.8
                    )
                
                logger.debug(f"Recorded emotional context for narrative choice: {emotional_state}")
                
            except Exception as e:
                # Emotional tracking failure doesn't break narrative system
                logger.warning(f"Emotional analysis failed for choice by user {user_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording narrative choice for user {user_id}: {e}")
            return False
    
    async def get_personalized_narrative_suggestions(self, user_id: int) -> dict:
        """
        Use emotional intelligence to personalize narrative experience.
        Falls back to standard suggestions if emotional data unavailable.
        """
        try:
            # Get emotional analysis
            analysis = await self.emotional_service.analyze_user_emotional_patterns(user_id)
            
            if analysis.get("status") == "success":
                # Use emotional insights for personalization
                suggestions = {
                    "tone": analysis["narrative_recommendations"]["tone_preference"],
                    "depth": analysis["narrative_recommendations"]["narrative_depth"], 
                    "interaction_style": analysis["narrative_recommendations"]["interaction_style"],
                    "avoid_triggers": await self._get_triggers_to_avoid(user_id),
                    "leverage_memories": await self._get_memories_to_reference(user_id)
                }
                
                logger.info(f"Generated personalized suggestions for user {user_id}")
                return suggestions
            
            else:
                # Fallback to standard suggestions
                return {
                    "tone": "neutral",
                    "depth": "medium", 
                    "interaction_style": "standard",
                    "avoid_triggers": [],
                    "leverage_memories": []
                }
                
        except Exception as e:
            logger.error(f"Error generating personalized suggestions for user {user_id}: {e}")
            return {"tone": "neutral", "depth": "medium", "interaction_style": "standard"}
    
    async def _get_triggers_to_avoid(self, user_id: int) -> list:
        """Get emotional triggers that should be handled carefully"""
        triggers = await self.emotional_service.get_emotional_triggers(user_id)
        return [
            trigger.trigger_keyword 
            for trigger in triggers 
            if trigger.requires_careful_handling
        ]
    
    async def _get_memories_to_reference(self, user_id: int) -> list:
        """Get positive memories that can be referenced in narrative"""
        memories = await self.emotional_service.get_user_memories_for_narrative(user_id, limit=5)
        return [
            {
                "reference": memory.memory_reference,
                "emotional_impact": memory.emotional_impact,
                "fragment": memory.narrative_fragment_key
            }
            for memory in memories
            if memory.emotional_impact > 0.5 and not memory.requires_sensitivity
        ]
    
    def _analyze_choice_emotion(self, choice_text: str) -> EmotionalState:
        """Simple emotion analysis of choice text"""
        choice_lower = choice_text.lower()
        
        # Emotional keywords mapping
        emotion_keywords = {
            EmotionalState.EXCITED: ["excited", "amazing", "fantastic", "wonderful", "thrilled"],
            EmotionalState.CURIOUS: ["curious", "wonder", "explore", "discover", "learn"],
            EmotionalState.SERIOUS: ["serious", "important", "careful", "responsible", "duty"],
            EmotionalState.PLAYFUL: ["playful", "fun", "joke", "laugh", "silly"],
            EmotionalState.VULNERABLE: ["scared", "worried", "afraid", "nervous", "uncertain"],
            EmotionalState.CONFIDENT: ["confident", "sure", "certain", "strong", "capable"],
            EmotionalState.NOSTALGIC: ["remember", "past", "used to", "before", "memories"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in choice_lower for keyword in keywords):
                return emotion
        
        return EmotionalState.NEUTRAL
    
    def _assess_choice_vulnerability(self, choice_text: str) -> float:
        """Assess vulnerability level of a choice (0.0 to 1.0)"""
        vulnerable_indicators = {
            "high": ["afraid", "terrified", "secret", "ashamed", "embarrassed"],
            "medium": ["worried", "concerned", "nervous", "unsure", "personal"],
            "low": ["slightly concerned", "a bit worried", "wondering"]
        }
        
        choice_lower = choice_text.lower()
        
        for level, keywords in vulnerable_indicators.items():
            for keyword in keywords:
                if keyword in choice_lower:
                    if level == "high":
                        return 0.9
                    elif level == "medium": 
                        return 0.6
                    elif level == "low":
                        return 0.3
        
        return 0.0


class EmotionalDashboard:
    """
    Example dashboard that combines existing user stats with emotional intelligence.
    Shows how to present enhanced user information.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.emotional_service = EmotionalService(session)
    
    async def get_enhanced_user_overview(self, user_id: int) -> dict:
        """
        Get comprehensive user overview combining existing stats with emotional intelligence.
        Gracefully handles missing emotional data.
        """
        try:
            # Get existing user data (always available)
            user = await self.session.get(User, user_id)
            user_stats = await self.session.get(UserStats, user_id)
            
            if not user:
                return {"error": "User not found"}
            
            # Build basic overview from existing data
            overview = {
                "user_id": user_id,
                "username": user.username or f"User{user_id}",
                "level": user.level,
                "points": user.points,
                "role": user.role,
                "achievements_count": len(user.achievements) if user.achievements else 0,
                "messages_sent": user_stats.messages_sent if user_stats else 0,
                "last_activity": user_stats.last_activity_at.isoformat() if user_stats and user_stats.last_activity_at else None
            }
            
            # Try to add emotional intelligence (optional)
            try:
                emotional_profile = await self.session.get(UserEmotionalProfile, user_id)
                if emotional_profile:
                    overview["emotional_intelligence"] = {
                        "archetype": emotional_profile.archetype_classification.value,
                        "confidence": emotional_profile.archetype_confidence,
                        "dominant_emotion": emotional_profile.dominant_emotion.value if emotional_profile.dominant_emotion else "neutral",
                        "vulnerability_level": emotional_profile.vulnerability_level,
                        "authenticity_score": emotional_profile.authenticity_score,
                        "total_interactions": emotional_profile.total_interactions_analyzed
                    }
                    
                    # Get recent emotional patterns
                    analysis = await self.emotional_service.analyze_user_emotional_patterns(user_id)
                    if analysis.get("status") == "success":
                        overview["emotional_patterns"] = {
                            "recent_emotions": analysis.get("emotional_distribution", {}),
                            "consistency": analysis.get("emotional_consistency", 0.0),
                            "narrative_recommendations": analysis.get("narrative_recommendations", {})
                        }
                
                else:
                    overview["emotional_intelligence"] = {
                        "status": "not_initialized",
                        "message": "Emotional profiling will begin as user interacts more"
                    }
                
            except Exception as e:
                logger.warning(f"Could not load emotional data for user {user_id}: {e}")
                overview["emotional_intelligence"] = {
                    "status": "unavailable",
                    "message": "Emotional tracking temporarily unavailable"
                }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting user overview for {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_emotional_insights_summary(self, user_id: int) -> dict:
        """Get summary of emotional insights for admin/analysis purposes"""
        try:
            analysis = await self.emotional_service.analyze_user_emotional_patterns(user_id)
            memories = await self.emotional_service.get_user_memories_for_narrative(user_id, limit=3)
            triggers = await self.emotional_service.get_emotional_triggers(user_id)
            
            return {
                "analysis": analysis,
                "key_memories": [
                    {
                        "point": memory.conversation_point,
                        "emotion": memory.emotional_state.value,
                        "impact": memory.emotional_impact
                    }
                    for memory in memories
                ],
                "triggers_count": len(triggers),
                "high_impact_triggers": len([t for t in triggers if t.requires_careful_handling])
            }
            
        except Exception as e:
            logger.error(f"Error getting emotional insights for user {user_id}: {e}")
            return {"error": str(e)}


async def demonstration_example():
    """
    Demonstration of how the emotional tracking integrates with existing functionality.
    Shows the complete workflow from basic operations to emotional intelligence.
    """
    # This would normally be provided by your existing database setup
    session = None  # AsyncSession would be injected here
    
    if not session:
        print("Note: This is a demonstration - actual session would be provided by your app")
        return
    
    try:
        user_id = 12345  # Example user ID
        
        # 1. Enhanced Point Service
        print("=== Enhanced Point Service Example ===")
        point_service = EnhancedPointService(session)
        
        # Award points with emotional context
        success = await point_service.add_points_with_emotion(
            user_id=user_id,
            points=50,
            source="achievement_unlocked",
            emotional_context="User completed difficult challenge"
        )
        print(f"Points awarded with emotional context: {success}")
        
        # 2. Enhanced Narrative Service
        print("\n=== Enhanced Narrative Service Example ===")
        narrative_service = EnhancedNarrativeService(session)
        
        # Record narrative choice with emotional analysis
        choice_success = await narrative_service.record_narrative_choice_with_emotion(
            user_id=user_id,
            fragment_key="intro_choice_1",
            choice_text="I'm really excited to explore this mysterious place!",
            response_time_seconds=12.5
        )
        print(f"Narrative choice recorded with emotion: {choice_success}")
        
        # Get personalized suggestions
        suggestions = await narrative_service.get_personalized_narrative_suggestions(user_id)
        print(f"Personalized narrative suggestions: {suggestions}")
        
        # 3. Emotional Dashboard
        print("\n=== Emotional Dashboard Example ===")
        dashboard = EmotionalDashboard(session)
        
        # Get enhanced user overview
        overview = await dashboard.get_enhanced_user_overview(user_id)
        print(f"Enhanced user overview: {overview}")
        
        # Get emotional insights
        insights = await dashboard.get_emotional_insights_summary(user_id)
        print(f"Emotional insights summary: {insights}")
        
        print("\n=== Integration Complete ===")
        print("Emotional tracking successfully integrated with existing services!")
        print("- Point awards now include emotional context")
        print("- Narrative choices are analyzed for emotional content")
        print("- User overviews include emotional intelligence data")
        print("- All existing functionality remains unchanged")
        
    except Exception as e:
        print(f"Demonstration error: {e}")
        print("In production, errors would be logged and handled gracefully")


if __name__ == "__main__":
    print("Emotional Integration Example")
    print("This demonstrates how emotional tracking extends existing functionality")
    print("without breaking current features.\n")
    
    # Run demonstration
    asyncio.run(demonstration_example())