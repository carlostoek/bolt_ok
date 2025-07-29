"""
Diana Emotional Service

This service provides the core functionality for Diana's emotional memory system.
It handles the storage, retrieval, and management of emotional interactions,
relationship states, contradictions, and personality adaptations.

The service is optimized for fast queries (<100ms) and provides
natural emotional memory decay and contextual relevance.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, desc, and_, or_
from database.diana_models import (
    DianaEmotionalMemory,
    DianaRelationshipState,
    DianaContradiction,
    DianaPersonalityAdaptation,
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)

logger = logging.getLogger(__name__)


class DianaEmotionalService:
    """
    Service for managing Diana's emotional memory and relationship system.
    
    This service provides methods for:
    - Storing emotional memories
    - Retrieving relevant emotional context
    - Managing relationship states
    - Detecting and resolving contradictions
    - Adapting Diana's personality to users
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
    
    # --- Emotional Memory Methods ---
    
    async def store_emotional_memory(
        self,
        user_id: int,
        interaction_type: EmotionalInteractionType,
        summary: str,
        content: str,
        primary_emotion: EmotionCategory,
        secondary_emotion: Optional[EmotionCategory] = None,
        intensity: EmotionalIntensity = EmotionalIntensity.MODERATE,
        context_data: Dict[str, Any] = None,
        related_achievements: List[str] = None,
        related_narrative_keys: List[str] = None,
        importance_score: float = 1.0,
        decay_rate: float = 0.1,
        tags: List[str] = None,
        is_sensitive: bool = False,
        parent_memory_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store a new emotional memory for a user interaction.
        
        Returns a dict with success status and memory ID.
        """
        try:
            # Create new memory
            memory = DianaEmotionalMemory(
                user_id=user_id,
                interaction_type=interaction_type,
                summary=summary,
                content=content,
                primary_emotion=primary_emotion,
                secondary_emotion=secondary_emotion,
                intensity=intensity,
                context_data=context_data or {},
                related_achievements=related_achievements or [],
                related_narrative_keys=related_narrative_keys or [],
                importance_score=importance_score,
                decay_rate=decay_rate,
                tags=tags or [],
                is_sensitive=is_sensitive,
                parent_memory_id=parent_memory_id
            )
            
            self.session.add(memory)
            await self.session.flush()
            
            # Update relationship state with this new interaction
            await self._update_relationship_state_after_interaction(
                user_id, 
                interaction_type, 
                primary_emotion,
                intensity
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": "Emotional memory stored successfully"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error storing emotional memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recent_memories(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve the most recent emotional memories for a user.
        
        Returns a dict with success status and list of memories.
        """
        try:
            stmt = (
                select(DianaEmotionalMemory)
                .where(
                    and_(
                        DianaEmotionalMemory.user_id == user_id,
                        DianaEmotionalMemory.is_forgotten == False
                    )
                )
                .order_by(DianaEmotionalMemory.timestamp.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            memories = result.scalars().all()
            
            # Update recall metadata for these memories
            memory_ids = [memory.id for memory in memories]
            await self._update_memory_recall_metadata(memory_ids)
            
            return {
                "success": True,
                "memories": [self._serialize_memory(memory) for memory in memories]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving recent memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_memories_by_emotion(
        self,
        user_id: int,
        emotion: EmotionCategory,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve memories associated with a specific emotion.
        
        Returns a dict with success status and list of memories.
        """
        try:
            stmt = (
                select(DianaEmotionalMemory)
                .where(
                    and_(
                        DianaEmotionalMemory.user_id == user_id,
                        DianaEmotionalMemory.is_forgotten == False,
                        or_(
                            DianaEmotionalMemory.primary_emotion == emotion,
                            DianaEmotionalMemory.secondary_emotion == emotion
                        )
                    )
                )
                .order_by(DianaEmotionalMemory.timestamp.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            memories = result.scalars().all()
            
            # Update recall metadata for these memories
            memory_ids = [memory.id for memory in memories]
            await self._update_memory_recall_metadata(memory_ids)
            
            return {
                "success": True,
                "memories": [self._serialize_memory(memory) for memory in memories]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving memories by emotion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_important_memories(
        self,
        user_id: int,
        min_importance: float = 1.5,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve the most important memories for a user.
        
        Returns a dict with success status and list of memories.
        """
        try:
            stmt = (
                select(DianaEmotionalMemory)
                .where(
                    and_(
                        DianaEmotionalMemory.user_id == user_id,
                        DianaEmotionalMemory.is_forgotten == False,
                        DianaEmotionalMemory.importance_score >= min_importance
                    )
                )
                .order_by(DianaEmotionalMemory.importance_score.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            memories = result.scalars().all()
            
            # Update recall metadata for these memories
            memory_ids = [memory.id for memory in memories]
            await self._update_memory_recall_metadata(memory_ids)
            
            return {
                "success": True,
                "memories": [self._serialize_memory(memory) for memory in memories]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving important memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_contextual_memories(
        self,
        user_id: int,
        tags: List[str],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve memories based on contextual tags.
        
        Returns a dict with success status and list of memories.
        """
        try:
            # This is a simplistic approach for SQL dialect compatibility
            # For more complex queries, consider using a full-text search extension
            memories = []
            
            for tag in tags:
                stmt = (
                    select(DianaEmotionalMemory)
                    .where(
                        and_(
                            DianaEmotionalMemory.user_id == user_id,
                            DianaEmotionalMemory.is_forgotten == False,
                            DianaEmotionalMemory.tags.contains([tag])
                        )
                    )
                    .order_by(DianaEmotionalMemory.timestamp.desc())
                    .limit(limit)
                )
                
                result = await self.session.execute(stmt)
                tag_memories = result.scalars().all()
                
                # Add unique memories to the result
                for memory in tag_memories:
                    if memory not in memories:
                        memories.append(memory)
                        
                        # Limit total memories returned
                        if len(memories) >= limit:
                            break
                
                if len(memories) >= limit:
                    break
            
            # Update recall metadata for these memories
            memory_ids = [memory.id for memory in memories]
            await self._update_memory_recall_metadata(memory_ids)
            
            return {
                "success": True,
                "memories": [self._serialize_memory(memory) for memory in memories]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving contextual memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def forget_memory(self, memory_id: int) -> Dict[str, Any]:
        """
        Mark a memory as forgotten (GDPR compliance).
        
        Returns a dict with success status.
        """
        try:
            stmt = (
                update(DianaEmotionalMemory)
                .where(DianaEmotionalMemory.id == memory_id)
                .values(is_forgotten=True)
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            return {
                "success": True,
                "message": "Memory marked as forgotten"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error forgetting memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def forget_all_user_memories(self, user_id: int) -> Dict[str, Any]:
        """
        Mark all memories for a user as forgotten (GDPR compliance).
        
        Returns a dict with success status and count of forgotten memories.
        """
        try:
            stmt = (
                update(DianaEmotionalMemory)
                .where(
                    and_(
                        DianaEmotionalMemory.user_id == user_id,
                        DianaEmotionalMemory.is_forgotten == False
                    )
                )
                .values(is_forgotten=True)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return {
                "success": True,
                "count": result.rowcount,
                "message": f"{result.rowcount} memories marked as forgotten"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error forgetting all user memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # --- Relationship State Methods ---
    
    async def get_relationship_state(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve the current relationship state for a user.
        
        Returns a dict with success status and relationship state data.
        """
        try:
            stmt = select(DianaRelationshipState).where(DianaRelationshipState.user_id == user_id)
            result = await self.session.execute(stmt)
            relationship = result.scalar_one_or_none()
            
            if not relationship:
                # Create a new default relationship state if none exists
                relationship = await self._create_default_relationship_state(user_id)
            
            return {
                "success": True,
                "relationship": self._serialize_relationship(relationship)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving relationship state: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_relationship_status(
        self,
        user_id: int,
        status: RelationshipStatus,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Update the relationship status for a user.
        
        Returns a dict with success status and updated relationship data.
        """
        try:
            # Get current relationship state or create new one
            relationship = await self._get_or_create_relationship_state(user_id)
            
            # Update status
            relationship.status = status
            relationship.updated_at = datetime.now()
            
            # Add milestone if status change is significant
            if status in [
                RelationshipStatus.CLOSE, 
                RelationshipStatus.INTIMATE,
                RelationshipStatus.STRAINED,
                RelationshipStatus.REPAIRED
            ]:
                # Update milestone data
                milestone_data = relationship.milestone_data or {}
                status_milestones = milestone_data.get("status_changes", [])
                status_milestones.append({
                    "timestamp": datetime.now().isoformat(),
                    "old_status": relationship.status.value,
                    "new_status": status.value,
                    "reason": reason
                })
                
                milestone_data["status_changes"] = status_milestones
                relationship.milestone_data = milestone_data
                relationship.milestone_count += 1
            
            await self.session.commit()
            
            return {
                "success": True,
                "relationship": self._serialize_relationship(relationship),
                "message": f"Relationship status updated to {status.value}"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating relationship status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def record_interaction(
        self,
        user_id: int,
        interaction_length: int = None,
        response_time_seconds: int = None
    ) -> Dict[str, Any]:
        """
        Record a general interaction with the user to update metrics.
        
        Returns a dict with success status and updated metrics.
        """
        try:
            # Get current relationship state or create new one
            relationship = await self._get_or_create_relationship_state(user_id)
            
            # Update interaction metrics
            relationship.interaction_count += 1
            relationship.last_interaction_at = datetime.now()
            
            # Update communication metrics if provided
            if interaction_length is not None:
                current_avg = relationship.typical_interaction_length or 0
                total = current_avg * (relationship.interaction_count - 1)
                relationship.typical_interaction_length = (total + interaction_length) / relationship.interaction_count
            
            if response_time_seconds is not None:
                current_avg = relationship.typical_response_time_seconds or 0
                total = current_avg * (relationship.interaction_count - 1)
                relationship.typical_response_time_seconds = (total + response_time_seconds) / relationship.interaction_count
            
            # Calculate communication frequency (interactions per day)
            days_since_start = (datetime.now() - relationship.relationship_started_at).days or 1
            relationship.communication_frequency = relationship.interaction_count / days_since_start
            
            # Calculate absence if applicable
            if relationship.last_interaction_at:
                days_absent = (datetime.now() - relationship.last_interaction_at).days
                relationship.longest_absence_days = max(relationship.longest_absence_days or 0, days_absent)
            
            await self.session.commit()
            
            return {
                "success": True,
                "interaction_count": relationship.interaction_count,
                "message": "Interaction recorded successfully"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error recording interaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # --- Contradiction Management Methods ---
    
    async def record_contradiction(
        self,
        user_id: int,
        contradiction_type: str,
        original_statement: str,
        contradicting_statement: str,
        context_data: Dict[str, Any] = None,
        related_memory_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Record a contradiction in user information.
        
        Returns a dict with success status and contradiction ID.
        """
        try:
            contradiction = DianaContradiction(
                user_id=user_id,
                contradiction_type=contradiction_type,
                original_statement=original_statement,
                contradicting_statement=contradicting_statement,
                context_data=context_data or {},
                related_memory_ids=related_memory_ids or []
            )
            
            self.session.add(contradiction)
            await self.session.commit()
            
            return {
                "success": True,
                "contradiction_id": contradiction.id,
                "message": "Contradiction recorded successfully"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error recording contradiction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def resolve_contradiction(
        self,
        contradiction_id: int,
        resolution: str
    ) -> Dict[str, Any]:
        """
        Resolve a previously recorded contradiction.
        
        Returns a dict with success status.
        """
        try:
            stmt = (
                update(DianaContradiction)
                .where(DianaContradiction.id == contradiction_id)
                .values(
                    resolution=resolution,
                    is_resolved=True,
                    resolved_at=datetime.now()
                )
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            return {
                "success": True,
                "message": "Contradiction resolved successfully"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error resolving contradiction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_unresolved_contradictions(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get all unresolved contradictions for a user.
        
        Returns a dict with success status and list of contradictions.
        """
        try:
            stmt = (
                select(DianaContradiction)
                .where(
                    and_(
                        DianaContradiction.user_id == user_id,
                        DianaContradiction.is_resolved == False
                    )
                )
                .order_by(DianaContradiction.detected_at.desc())
            )
            
            result = await self.session.execute(stmt)
            contradictions = result.scalars().all()
            
            return {
                "success": True,
                "contradictions": [self._serialize_contradiction(c) for c in contradictions]
            }
            
        except Exception as e:
            logger.error(f"Error retrieving unresolved contradictions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # --- Personality Adaptation Methods ---
    
    async def get_personality_adaptation(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get the personality adaptation for a user.
        
        Returns a dict with success status and adaptation data.
        """
        try:
            stmt = select(DianaPersonalityAdaptation).where(DianaPersonalityAdaptation.user_id == user_id)
            result = await self.session.execute(stmt)
            adaptation = result.scalar_one_or_none()
            
            if not adaptation:
                # Create a new default adaptation if none exists
                adaptation = await self._create_default_personality_adaptation(user_id)
            
            return {
                "success": True,
                "adaptation": self._serialize_adaptation(adaptation)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving personality adaptation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enhance_interaction(
        self,
        user_id: int, 
        accion, 
        resultado_original: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhance a user interaction based on Diana's emotional understanding and personal context.
        
        This method records the interaction, stores emotional memory if appropriate, and personalizes
        the response based on the user's relationship state, interaction history, and personality preferences.
        
        Args:
            user_id: ID of the user
            accion: Type of action performed (from AccionUsuario enum)
            resultado_original: Original result from the action 
            **kwargs: Additional parameters specific to the action (reaction_type, etc.)
            
        Returns:
            Dict with enhanced results incorporating relationship context, or original results if enhancement not possible
        """
        try:
            # 1. Get the current relationship state and personality adaptation
            relationship_result = await self.get_relationship_state(user_id)
            if not relationship_result["success"]:
                return resultado_original
                
            relationship = relationship_result["relationship"]
            
            adaptation_result = await self.get_personality_adaptation(user_id)
            if not adaptation_result["success"]:
                return resultado_original
                
            adaptation = adaptation_result["adaptation"]
            
            # 2. Record the interaction to update relationship metrics
            await self.record_interaction(user_id)
            
            # 3. Store emotional memory for significant interactions
            if resultado_original.get("success", False):
                await self._store_interaction_memory(user_id, accion, resultado_original, **kwargs)
            
            # 4. Check if Diana service is active for enhancement
            if not self.is_active():
                return resultado_original
                
            # 5. If active, try to enhance the interaction based on action type
            enhanced_result = await self._enhance_by_action_type(
                user_id, accion, resultado_original, relationship, adaptation, **kwargs
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error enhancing interaction: {e}")
            # Return original result in case of any error
            return resultado_original
    
    async def _store_interaction_memory(self, user_id: int, accion, resultado: Dict[str, Any], **kwargs) -> None:
        """
        Store an emotional memory for this interaction if it's significant.
        
        This creates a persistent record of meaningful interactions that can be referenced
        in future personalizations, building a sense of shared history.
        
        Args:
            user_id: ID of the user
            accion: Type of action performed
            resultado: Result data from the action
            **kwargs: Additional parameters specific to the action
        """
        try:
            # Map action types to appropriate emotional interaction types
            action_name = getattr(accion, "value", str(accion))
            
            # Default values
            summary = "Interacción con Diana"
            content = ""
            primary_emotion = EmotionCategory.NEUTRAL
            secondary_emotion = None
            interaction_type = EmotionalInteractionType.GREETING
            importance_score = 1.0
            context_data = {}
            
            # Populate based on action type
            if action_name == "reaccionar_publicacion":
                reaction_type = kwargs.get("reaction_type", "")
                reaction_category = self._categorize_reaction(reaction_type)
                
                # Set interaction type
                interaction_type = EmotionalInteractionType.FEEDBACK
                
                # Set emotion based on reaction category
                emotion_map = {
                    "positive": EmotionCategory.JOY,
                    "romantic": EmotionCategory.TRUST,
                    "humorous": EmotionCategory.JOY,
                    "surprised": EmotionCategory.SURPRISE,
                    "neutral": EmotionCategory.NEUTRAL
                }
                primary_emotion = emotion_map.get(reaction_category, EmotionCategory.NEUTRAL)
                
                # Create descriptive summary and content
                summary = f"Reacción {reaction_type} a publicación"
                content = f"El usuario reaccionó con {reaction_type} a una publicación de Diana"
                
                # Add context data
                context_data = {
                    "reaction_type": reaction_type,
                    "reaction_category": reaction_category,
                    "points_awarded": resultado.get("points_awarded", 0),
                    "message_id": kwargs.get("message_id", 0)
                }
                
                # Higher importance for romantic reactions
                if reaction_category == "romantic":
                    importance_score = 1.5
                    secondary_emotion = EmotionCategory.ANTICIPATION
                
            # Add more action types as needed
            elif action_name == "tomar_decision":
                decision_id = kwargs.get("decision_id", 0)
                
                interaction_type = EmotionalInteractionType.PERSONAL_SHARE
                primary_emotion = EmotionCategory.ANTICIPATION
                
                summary = f"Decisión narrativa {decision_id}"
                content = f"El usuario eligió la decisión {decision_id} en la narrativa"
                
                context_data = {
                    "decision_id": decision_id,
                    "fragment": resultado.get("fragment", {})
                }
                
                importance_score = 1.8  # Narrative decisions are significant
            
            # Only store memories for significant interactions
            if importance_score >= 1.0:
                await self.store_emotional_memory(
                    user_id=user_id,
                    interaction_type=interaction_type,
                    summary=summary,
                    content=content,
                    primary_emotion=primary_emotion,
                    secondary_emotion=secondary_emotion,
                    context_data=context_data,
                    importance_score=importance_score
                )
                
        except Exception as e:
            # Log but don't fail the whole flow
            logger.error(f"Error storing interaction memory: {e}")
            pass
    
    def is_active(self) -> bool:
        """
        Check if Diana's emotional service is active.
        
        This is a placeholder for any activation logic. This could check a setting in
        a configuration table, a feature flag, or any other mechanism to determine
        if Diana should enhance interactions.
        
        Returns:
            bool: True if Diana is active, False otherwise
        """
        # This should be replaced with actual logic to check if Diana is active
        # For now, we'll return True for testing purposes
        return True
    
    async def _enhance_by_action_type(
        self,
        user_id: int,
        accion,
        resultado_original: Dict[str, Any],
        relationship: Dict[str, Any],
        adaptation: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply enhancements based on the specific action type.
        
        Args:
            user_id: ID of the user
            accion: Type of action performed
            resultado_original: Original result from the action
            relationship: Current relationship state
            adaptation: Current personality adaptation
            **kwargs: Additional parameters specific to the action
            
        Returns:
            Dict with enhanced results
        """
        # Clone the original result to avoid modifying it directly
        resultado = dict(resultado_original)
        
        # Check the action type and apply appropriate enhancements
        action_name = getattr(accion, "value", str(accion))
        
        if action_name == "reaccionar_publicacion":
            resultado = await self._enhance_reaction_message(
                user_id, resultado, relationship, adaptation, **kwargs
            )
        
        # Add more action types as needed
        
        return resultado
    
    async def _enhance_reaction_message(
        self,
        user_id: int,
        resultado: Dict[str, Any],
        relationship: Dict[str, Any],
        adaptation: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhance reaction messages based on relationship state, emotional memories,
        and personality adaptation for truly personalized interactions.
        
        Args:
            user_id: ID of the user
            resultado: Original result to enhance
            relationship: Current relationship state
            adaptation: Current personality adaptation
            **kwargs: Additional parameters including reaction_type
            
        Returns:
            Dict with enhanced message incorporating intimacy level, memories, and context
        """
        if not resultado.get("success", False):
            return resultado
            
        # Get base message and check for hint unlocked scenario
        original_message = resultado.get("message", "")
        hint_unlocked = resultado.get("hint_unlocked")
        
        # If hint is unlocked, we'll preserve the hint part but personalize the greeting
        if hint_unlocked and "Nueva pista desbloqueada" in original_message:
            base_part, hint_part = original_message.split("\n\n", 1)
            # We'll only personalize the base part and keep the hint intact
            is_hint_message = True
        else:
            base_part = original_message
            hint_part = ""
            is_hint_message = False
        
        # Extract core parameters from relationship and adaptation
        status = relationship.get("status", "initial")
        intimacy_level = self._calculate_intimacy_level(relationship)
        
        # Get adaptation parameters with defaults
        warmth = adaptation.get("warmth", 0.5)
        formality = adaptation.get("formality", 0.5)
        humor = adaptation.get("humor", 0.5)
        emoji_usage = adaptation.get("emoji_usage", 0.5)
        directness = adaptation.get("directness", 0.5)
        emotional_expressiveness = adaptation.get("emotional_expressiveness", 0.5)
        
        # Get user's current emotional state based on recent memories
        emotion_result = await self._get_user_emotional_context(user_id)
        primary_emotion = emotion_result.get("primary_emotion", "neutral")
        emotional_context = emotion_result.get("context", {})
        
        # Get reaction type if available and determine what kind of reaction it was
        reaction_type = kwargs.get("reaction_type", "")
        reaction_category = self._categorize_reaction(reaction_type)
        
        # Select appropriate endearment term based on relationship status and warmth
        endearment = self._get_relationship_endearment(status, warmth, intimacy_level)
        
        # Get personalized action verb and description based on all factors
        action_verb, action_description = self._get_personalized_action(
            reaction_category, 
            primary_emotion,
            intimacy_level,
            status,
            warmth,
            humor,
            emotional_expressiveness
        )
        
        # Build the response based on all contextual factors
        if endearment:
            if directness > 0.7:
                # More direct style addresses the user explicitly
                greeting_phrase = f"{endearment}, "
            else:
                greeting_phrase = ""
        else:
            greeting_phrase = ""
            
        # Get reference to past interactions if appropriate
        memory_reference = await self._get_contextual_memory_reference(
            user_id, 
            reaction_category,
            intimacy_level
        )
        
        # Calculate response with proper level of emotional expression
        emotional_intensity = "" if emotional_expressiveness < 0.3 else \
                            "con una chispa en sus ojos" if emotional_expressiveness < 0.6 else \
                            action_description
                            
        # Format the emoji usage based on user preference
        emoji = self._select_appropriate_emoji(reaction_category, emoji_usage)
        
        # Construct the personalized core message
        if intimacy_level > 0.7:
            # High intimacy - more personal, emotional, specific
            core_message = f"Diana {action_verb} {emotional_intensity}{emoji} {memory_reference}"
        elif intimacy_level > 0.4:
            # Medium intimacy - warm but more reserved
            core_message = f"Diana {action_verb}{emoji} {memory_reference}"
        else:
            # Low intimacy - more formal, less emotional
            core_message = f"Diana {action_verb}{emoji}"
            
        # Add the points award part
        points_message = f"*+10 besitos* 💋 han sido añadidos a tu cuenta."
        
        # Combine everything into the enhanced message
        if greeting_phrase:
            enhanced_message = f"{greeting_phrase}{core_message}... {points_message}"
        else:
            enhanced_message = f"{core_message}... {points_message}"
            
        # If there was a hint, add it back
        if is_hint_message:
            enhanced_message = f"{enhanced_message}\n\n{hint_part}"
        
        # Update the result with the enhanced message
        resultado["message"] = enhanced_message
        
        return resultado
        
    def _calculate_intimacy_level(self, relationship: Dict[str, Any]) -> float:
        """
        Calculate an intimacy level score (0.0-1.0) based on relationship metrics.
        
        Args:
            relationship: Relationship state dictionary
            
        Returns:
            Float intimacy score from 0.0 (distant) to 1.0 (very intimate)
        """
        # Base intimacy on status
        status_weights = {
            "initial": 0.1,
            "acquaintance": 0.3,
            "friendly": 0.5,
            "close": 0.8,
            "intimate": 1.0,
            "strained": 0.4,
            "repaired": 0.6,
            "distant": 0.2,
            "complex": 0.5
        }
        
        status = relationship.get("status", "initial")
        base_intimacy = status_weights.get(status, 0.1)
        
        # Factor in trust and rapport
        trust_level = relationship.get("trust_level", 0.1)
        rapport = relationship.get("rapport", 0.1)
        
        # Consider interaction history
        interaction_count = relationship.get("interaction_count", 0)
        interaction_factor = min(1.0, interaction_count / 100.0) * 0.2
        
        # Calculate final intimacy score with weighted components
        intimacy_score = (base_intimacy * 0.4) + (trust_level * 0.3) + (rapport * 0.2) + interaction_factor
        
        # Ensure it's in valid range
        return max(0.0, min(1.0, intimacy_score))
    
    def _categorize_reaction(self, reaction_type: str) -> str:
        """
        Categorize the reaction type into a general emotional category.
        
        Args:
            reaction_type: Specific reaction emoji or code
            
        Returns:
            Category string: 'positive', 'romantic', 'humorous', 'surprised', or 'neutral'
        """
        positive_reactions = ["👍", "👌", "🔥", "✨", "⭐", "🙌", "like"]
        romantic_reactions = ["❤️", "😍", "😘", "💕", "💖", "love", "heart"]
        humorous_reactions = ["😂", "🤣", "😆", "😜", "🤪", "haha", "funny"]
        surprised_reactions = ["😮", "😲", "🤯", "😱", "wow", "omg"]
        
        if any(r in reaction_type for r in positive_reactions):
            return "positive"
        elif any(r in reaction_type for r in romantic_reactions):
            return "romantic"
        elif any(r in reaction_type for r in humorous_reactions):
            return "humorous"
        elif any(r in reaction_type for r in surprised_reactions):
            return "surprised"
        else:
            return "neutral"
    
    def _get_relationship_endearment(self, status: str, warmth: float, intimacy_level: float) -> str:
        """
        Get an appropriate endearment term based on relationship factors.
        
        Args:
            status: Relationship status string
            warmth: Warmth adaptation value (0.0-1.0)
            intimacy_level: Calculated intimacy level (0.0-1.0)
            
        Returns:
            String with appropriate endearment term or empty string
        """
        # High intimacy endearments
        if status in ["intimate", "close"]:
            if warmth > 0.8 and intimacy_level > 0.8:
                options = ["mi amor más preciado", "mi tesoro", "mi vida", "mi adoración"]
            elif warmth > 0.6:
                options = ["mi dulce amor", "mi cielo", "mi corazón", "cariño mío"]
            else:
                options = ["mi amor", "cielo", "cariño"]
                
        # Medium intimacy endearments
        elif status == "friendly":
            if warmth > 0.7:
                options = ["mi querido admirador", "mi dulce compañero", "querido"]
            elif warmth > 0.5:
                options = ["mi dulce admirador", "encanto", "querido"]
            else:
                options = ["mi admirador", "querido"]
                
        # Lower intimacy or beginning relationship
        elif status == "acquaintance":
            if warmth > 0.7:
                options = ["mi nuevo admirador", "dulzura"]
            elif warmth > 0.5:
                options = ["mi admirador"]
            else:
                options = ["admirador"]
                
        # Initial or strained relationships
        else:
            if intimacy_level > 0.3:
                options = ["querido"]
            else:
                return ""
                
        # Select randomly but deterministically based on user_id to maintain consistency
        import hashlib
        index = int(hashlib.md5(f"{status}_{warmth:.1f}".encode()).hexdigest(), 16) % len(options)
        return options[index]
        
    def _get_personalized_action(self, 
                               reaction_category: str,
                               primary_emotion: str,
                               intimacy_level: float,
                               status: str,
                               warmth: float,
                               humor: float,
                               emotional_expressiveness: float) -> Tuple[str, str]:
        """
        Get a personalized action verb and description based on all contextual factors.
        
        Args:
            reaction_category: Category of the reaction
            primary_emotion: User's primary emotional state
            intimacy_level: Calculated intimacy level
            status: Relationship status
            warmth: Warmth adaptation value
            humor: Humor adaptation value
            emotional_expressiveness: Emotional expressiveness value
            
        Returns:
            Tuple of (action_verb, description)
        """
        # Base actions by reaction category
        actions_by_reaction = {
            "positive": [
                ("sonríe", "con aprobación"),
                ("asiente", "complacida"),
                ("responde", "con una sonrisa sincera"),
                ("nota tu reacción", "y sus ojos brillan"),
            ],
            "romantic": [
                ("se sonroja", "ligeramente al ver tu reacción"),
                ("muerde su labio", "mientras te mira fijamente"),
                ("sonríe", "con un brillo especial en sus ojos"),
                ("reacciona", "con una mirada intensa y cómplice"),
            ],
            "humorous": [
                ("ríe", "divertida por tu reacción"),
                ("sonríe ampliamente", "compartiendo tu sentido del humor"),
                ("guiña un ojo", "con complicidad"),
                ("juguetea con su pelo", "mientras ríe contigo"),
            ],
            "surprised": [
                ("arquea una ceja", "sorprendida por tu reacción"),
                ("abre los ojos", "gratamente sorprendida"),
                ("reacciona", "con una expresión de asombro divertido"),
                ("se detiene", "observando tu reacción con curiosidad"),
            ],
            "neutral": [
                ("sonríe", "al notar tu reacción"),
                ("te observa", "con atención"),
                ("nota tu gesto", "con interés"),
                ("registra tu reacción", "con una sonrisa sutil"),
            ]
        }
        
        # Get base options from reaction category
        action_options = actions_by_reaction.get(reaction_category, actions_by_reaction["neutral"])
        
        # Filter or enhance based on intimacy and status
        if intimacy_level > 0.7 and status in ["intimate", "close"]:
            if reaction_category == "romantic":
                # Add more intimate options for romantic reactions in close relationships
                action_options.extend([
                    ("se acerca", "rozando ligeramente tu mano"),
                    ("suspira", "con anhelo mientras te mira"),
                    ("te dedica", "una mirada llena de complicidad y deseo"),
                ])
        
        # Adjust based on user's current emotional state
        if primary_emotion == "joy" and reaction_category in ["positive", "romantic", "humorous"]:
            # Amplify positive responses to positive emotions
            emotional_modifier = 0.2
        elif primary_emotion in ["sadness", "fear"] and emotional_expressiveness > 0.6:
            # More empathetic responses to negative emotions
            action_options = [
                ("responde", "con calidez para animarte"),
                ("sonríe", "con ternura comprensiva"),
                ("te observa", "con ojos compasivos"),
            ]
            emotional_modifier = -0.1
        else:
            emotional_modifier = 0.0
            
        # Apply humor if appropriate
        effective_humor = humor + emotional_modifier
        if effective_humor > 0.7 and reaction_category in ["humorous", "positive"]:
            action_options.extend([
                ("hace un guiño", "con picardía"),
                ("responde", "con una expresión traviesa"),
            ])
            
        # Select an appropriate action based on all factors
        effective_warmth = warmth + emotional_modifier
        
        # Choose more expressive actions for higher emotional expressiveness
        if emotional_expressiveness > 0.7:
            weight_descriptive = 0.8  # Prefer actions with descriptions
        elif emotional_expressiveness > 0.4:
            weight_descriptive = 0.5  # Balance between simple and descriptive
        else:
            weight_descriptive = 0.2  # Prefer simpler actions
            
        # Final selection logic
        import random
        # Seed with consistent factors to maintain personality consistency
        random.seed(f"{reaction_category}_{effective_warmth:.1f}_{effective_humor:.1f}")
        
        if random.random() < weight_descriptive:
            # Select action with description
            action, description = random.choice(action_options)
            return action, description
        else:
            # Select just the action verb
            action, _ = random.choice(action_options)
            return action, ""
    
    def _select_appropriate_emoji(self, reaction_category: str, emoji_usage: float) -> str:
        """
        Select appropriate emojis based on reaction category and emoji usage preference.
        
        Args:
            reaction_category: Category of the reaction
            emoji_usage: User's emoji usage preference (0.0-1.0)
            
        Returns:
            String with appropriate emoji(s) or empty string
        """
        if emoji_usage < 0.3:
            return ""  # No emojis for low preference
            
        # Emoji sets by category and intensity
        emoji_sets = {
            "positive": ["✨", "✨✨", "✨🌟✨"],
            "romantic": ["💕", "💕💖", "💕💖💋"],
            "humorous": ["😊", "😊😉", "😊😉😆"],
            "surprised": ["👀", "👀✨", "👀✨🔥"],
            "neutral": ["✨", "💫", "💫✨"]
        }
        
        # Select intensity based on preference
        if emoji_usage > 0.7:
            intensity_index = 2  # High emoji usage
        elif emoji_usage > 0.5:
            intensity_index = 1  # Medium emoji usage
        else:
            intensity_index = 0  # Low but non-zero emoji usage
            
        # Get emoji set for this category
        emoji_options = emoji_sets.get(reaction_category, emoji_sets["neutral"])
        
        # Return appropriate emoji based on intensity
        return emoji_options[intensity_index]
        
    async def _get_user_emotional_context(self, user_id: int) -> Dict[str, Any]:
        """
        Get the user's current emotional context based on recent memories.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with primary_emotion and context data
        """
        try:
            # Get recent emotional memories
            memories_result = await self.get_recent_memories(user_id, limit=5)
            
            if not memories_result.get("success", False) or not memories_result.get("memories"):
                return {
                    "primary_emotion": "neutral",
                    "context": {}
                }
                
            # Count emotions to determine primary
            emotion_counts = {}
            context_data = {}
            for memory in memories_result["memories"]:
                # Track emotion counts
                primary = memory.get("primary_emotion")
                if primary:
                    emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
                    
                # Collect context data
                if memory.get("context_data"):
                    context_data.update(memory["context_data"])
            
            # Determine primary emotion
            if emotion_counts:
                primary_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            else:
                primary_emotion = "neutral"
                
            return {
                "primary_emotion": primary_emotion,
                "context": context_data
            }
            
        except Exception as e:
            logger.error(f"Error getting user emotional context: {e}")
            return {
                "primary_emotion": "neutral",
                "context": {}
            }
    
    async def _get_contextual_memory_reference(self, user_id: int, reaction_category: str, intimacy_level: float) -> str:
        """
        Get a personalized reference to past interactions if appropriate for intimacy level.
        
        Args:
            user_id: User ID
            reaction_category: Category of the reaction
            intimacy_level: Calculated intimacy level
            
        Returns:
            String with memory reference or empty string
        """
        # Only include memory references for higher intimacy levels
        if intimacy_level < 0.4:
            return ""
            
        try:
            # Get appropriate emotional memory
            relevant_emotions = {"positive": "joy", "romantic": "trust", "humorous": "joy", "surprised": "surprise"}
            emotion = relevant_emotions.get(reaction_category, None)
            
            if emotion:
                # Try to get memories associated with this emotion
                memories_result = await self.get_memories_by_emotion(user_id, EmotionCategory(emotion), limit=3)
                
                if memories_result.get("success", False) and memories_result.get("memories"):
                    # Choose a memory that's important enough to reference
                    significant_memories = [m for m in memories_result["memories"] 
                                         if m.get("importance_score", 0) > 1.2]  
                    
                    if significant_memories and len(significant_memories) > 0 and intimacy_level > 0.5:
                        memory = significant_memories[0]
                        # Create a subtle reference to the memory
                        reference = f"recordando {memory.get('summary', 'tu gesto anterior')}"
                        return reference
            
            # If we've gotten here, no specific memory to reference
            if intimacy_level > 0.7 and reaction_category in ["positive", "romantic"]:
                # Generic positive memory reference for high intimacy
                return "como tantas otras veces que hemos compartido"
                
            return ""
            
        except Exception as e:
            logger.error(f"Error getting contextual memory reference: {e}")
            return ""

    async def update_personality_adaptation(
        self,
        user_id: int,
        adaptation_data: Dict[str, Any],
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Update the personality adaptation for a user.
        
        Returns a dict with success status and updated adaptation data.
        """
        try:
            # Get current adaptation or create new one
            adaptation = await self._get_or_create_personality_adaptation(user_id)
            
            # Update provided fields
            for key, value in adaptation_data.items():
                if hasattr(adaptation, key):
                    setattr(adaptation, key, value)
            
            # Update metadata
            adaptation.updated_at = datetime.now()
            adaptation.last_significant_change = datetime.now()
            adaptation.adaptation_reason = reason or adaptation.adaptation_reason
            
            # Increase confidence slightly with each update
            adaptation.confidence_score = min(1.0, adaptation.confidence_score + 0.05)
            
            await self.session.commit()
            
            return {
                "success": True,
                "adaptation": self._serialize_adaptation(adaptation),
                "message": "Personality adaptation updated successfully"
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating personality adaptation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # --- Helper Methods ---
    
    async def _update_memory_recall_metadata(self, memory_ids: List[int]):
        """Update recall metadata for accessed memories."""
        if not memory_ids:
            return
            
        try:
            now = datetime.now()
            
            for memory_id in memory_ids:
                stmt = (
                    update(DianaEmotionalMemory)
                    .where(DianaEmotionalMemory.id == memory_id)
                    .values(
                        last_recalled_at=now,
                        recall_count=DianaEmotionalMemory.recall_count + 1
                    )
                )
                
                await self.session.execute(stmt)
                
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating memory recall metadata: {e}")
    
    async def _update_relationship_state_after_interaction(
        self,
        user_id: int,
        interaction_type: EmotionalInteractionType,
        emotion: EmotionCategory,
        intensity: EmotionalIntensity
    ):
        """Update relationship state based on a new emotional interaction."""
        try:
            # Get current relationship state or create new one
            relationship = await self._get_or_create_relationship_state(user_id)
            
            # Update interaction count and timestamp
            relationship.interaction_count += 1
            relationship.last_interaction_at = datetime.now()
            
            # Update emotional statistics
            intensity_value = intensity.value  # Convert enum to numeric value
            
            # Categorize positive vs negative interactions
            positive_emotions = [
                EmotionCategory.JOY, 
                EmotionCategory.TRUST,
                EmotionCategory.ANTICIPATION
            ]
            
            negative_emotions = [
                EmotionCategory.SADNESS,
                EmotionCategory.ANGER,
                EmotionCategory.FEAR,
                EmotionCategory.DISGUST
            ]
            
            if emotion in positive_emotions:
                relationship.positive_interactions += 1
            elif emotion in negative_emotions:
                relationship.negative_interactions += 1
                
            # Update dominant emotion (simple majority tracking)
            emotion_counts = relationship.personality_adaptations.get("emotion_counts", {})
            emotion_counts[emotion.value] = emotion_counts.get(emotion.value, 0) + 1
            
            # Find the most common emotion
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            relationship.dominant_emotion = EmotionCategory(dominant_emotion)
            
            # Store updated emotion counts
            adaptations = relationship.personality_adaptations or {}
            adaptations["emotion_counts"] = emotion_counts
            relationship.personality_adaptations = adaptations
            
            # Update emotional volatility (standard deviation approximation)
            emotions_list = []
            for emotion_name, count in emotion_counts.items():
                emotions_list.extend([emotion_name] * count)
                
            if len(emotions_list) > 1:
                # Simple volatility approximation: count of emotion changes / total
                changes = sum(1 for i in range(1, len(emotions_list)) if emotions_list[i] != emotions_list[i-1])
                relationship.emotional_volatility = changes / (len(emotions_list) - 1)
            
            # Update relationship trust based on interaction type
            trust_modifiers = {
                EmotionalInteractionType.PERSONAL_SHARE: 0.05,
                EmotionalInteractionType.CONFESSION: 0.1,
                EmotionalInteractionType.CONFLICT: -0.03,
                EmotionalInteractionType.RESOLUTION: 0.07,
                EmotionalInteractionType.PRAISE: 0.03,
                EmotionalInteractionType.CRITICISM: -0.02
            }
            
            trust_modifier = trust_modifiers.get(interaction_type, 0.01)
            relationship.trust_level = max(0.0, min(1.0, relationship.trust_level + trust_modifier))
            
            # Update familiarity (grows with interactions but slower over time)
            familiarity_gain = 0.01 / (relationship.familiarity + 0.1)
            relationship.familiarity = min(1.0, relationship.familiarity + familiarity_gain)
            
            # Update rapport based on emotional alignment
            if emotion in positive_emotions:
                rapport_change = 0.02 * intensity_value / 5.0
                relationship.rapport = min(1.0, relationship.rapport + rapport_change)
            elif emotion in negative_emotions:
                rapport_change = -0.01 * intensity_value / 5.0
                relationship.rapport = max(0.0, relationship.rapport + rapport_change)
            
            # Check for relationship status transitions based on metrics
            self._check_relationship_status_transitions(relationship)
            
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating relationship state: {e}")
            # Don't raise, let the parent function handle transaction
    
    def _check_relationship_status_transitions(self, relationship: DianaRelationshipState):
        """Check if relationship metrics trigger a status transition."""
        
        # Define thresholds for status transitions
        thresholds = {
            RelationshipStatus.INITIAL: {
                "next": RelationshipStatus.ACQUAINTANCE,
                "requirements": {
                    "interaction_count": 5,
                }
            },
            RelationshipStatus.ACQUAINTANCE: {
                "next": RelationshipStatus.FRIENDLY,
                "requirements": {
                    "familiarity": 0.3,
                    "trust_level": 0.2,
                }
            },
            RelationshipStatus.FRIENDLY: {
                "next": RelationshipStatus.CLOSE,
                "requirements": {
                    "trust_level": 0.6,
                    "rapport": 0.5,
                    "interaction_count": 20,
                }
            },
            RelationshipStatus.CLOSE: {
                "next": RelationshipStatus.INTIMATE,
                "requirements": {
                    "trust_level": 0.8,
                    "rapport": 0.7,
                    "interaction_count": 50,
                }
            },
        }
        
        # Check for negative transitions
        if relationship.negative_interactions > relationship.positive_interactions and \
           relationship.interaction_count > 10 and \
           relationship.status not in [RelationshipStatus.STRAINED, RelationshipStatus.DISTANT]:
            relationship.status = RelationshipStatus.STRAINED
            return
        
        # Check for positive transitions
        current_status = relationship.status
        if current_status in thresholds:
            transition = thresholds[current_status]
            meets_requirements = True
            
            for attr, value in transition["requirements"].items():
                if getattr(relationship, attr, 0) < value:
                    meets_requirements = False
                    break
                    
            if meets_requirements:
                relationship.status = transition["next"]
                
                # Add milestone
                milestone_data = relationship.milestone_data or {}
                status_milestones = milestone_data.get("status_changes", [])
                status_milestones.append({
                    "timestamp": datetime.now().isoformat(),
                    "old_status": current_status.value,
                    "new_status": transition["next"].value,
                    "reason": "Natural progression"
                })
                
                milestone_data["status_changes"] = status_milestones
                relationship.milestone_data = milestone_data
                relationship.milestone_count += 1
    
    async def _get_or_create_relationship_state(self, user_id: int) -> DianaRelationshipState:
        """Get existing relationship state or create a new one."""
        stmt = select(DianaRelationshipState).where(DianaRelationshipState.user_id == user_id)
        result = await self.session.execute(stmt)
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            relationship = await self._create_default_relationship_state(user_id)
            
        return relationship
    
    async def _create_default_relationship_state(self, user_id: int) -> DianaRelationshipState:
        """Create a default relationship state for a new user."""
        relationship = DianaRelationshipState(
            user_id=user_id,
            status=RelationshipStatus.INITIAL,
            trust_level=0.1,
            familiarity=0.0,
            rapport=0.1,
            dominant_emotion=EmotionCategory.NEUTRAL,
            emotional_volatility=0.0,
            positive_interactions=0,
            negative_interactions=0,
            interaction_count=0,
            milestone_count=0,
            milestone_data={
                "status_changes": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "old_status": None,
                        "new_status": RelationshipStatus.INITIAL.value,
                        "reason": "First interaction"
                    }
                ]
            },
            personality_adaptations={
                "emotion_counts": {}
            }
        )
        
        self.session.add(relationship)
        await self.session.commit()
        
        return relationship
    
    async def _get_or_create_personality_adaptation(self, user_id: int) -> DianaPersonalityAdaptation:
        """Get existing personality adaptation or create a new one."""
        stmt = select(DianaPersonalityAdaptation).where(DianaPersonalityAdaptation.user_id == user_id)
        result = await self.session.execute(stmt)
        adaptation = result.scalar_one_or_none()
        
        if not adaptation:
            adaptation = await self._create_default_personality_adaptation(user_id)
            
        return adaptation
    
    async def _create_default_personality_adaptation(self, user_id: int) -> DianaPersonalityAdaptation:
        """Create a default personality adaptation for a new user."""
        adaptation = DianaPersonalityAdaptation(
            user_id=user_id,
            # Default to neutral middle values
            warmth=0.5,
            formality=0.5,
            humor=0.5,
            directness=0.5,
            assertiveness=0.5,
            curiosity=0.5,
            emotional_expressiveness=0.5,
            message_length_preference=100,
            complexity_level=0.5,
            emoji_usage=0.5,
            adaptation_reason="Initial default settings"
        )
        
        self.session.add(adaptation)
        await self.session.commit()
        
        return adaptation
    
    def _serialize_memory(self, memory: DianaEmotionalMemory) -> Dict[str, Any]:
        """Convert a memory object to a serializable dictionary."""
        return {
            "id": memory.id,
            "user_id": memory.user_id,
            "interaction_type": memory.interaction_type.value,
            "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
            "summary": memory.summary,
            "content": memory.content,
            "primary_emotion": memory.primary_emotion.value,
            "secondary_emotion": memory.secondary_emotion.value if memory.secondary_emotion else None,
            "intensity": memory.intensity.value,
            "context_data": memory.context_data,
            "related_achievements": memory.related_achievements,
            "related_narrative_keys": memory.related_narrative_keys,
            "importance_score": memory.importance_score,
            "decay_rate": memory.decay_rate,
            "last_recalled_at": memory.last_recalled_at.isoformat() if memory.last_recalled_at else None,
            "recall_count": memory.recall_count,
            "tags": memory.tags,
            "is_sensitive": memory.is_sensitive,
            "is_forgotten": memory.is_forgotten,
            "parent_memory_id": memory.parent_memory_id
        }
    
    def _serialize_relationship(self, relationship: DianaRelationshipState) -> Dict[str, Any]:
        """Convert a relationship object to a serializable dictionary."""
        return {
            "user_id": relationship.user_id,
            "status": relationship.status.value,
            "trust_level": relationship.trust_level,
            "familiarity": relationship.familiarity,
            "rapport": relationship.rapport,
            "dominant_emotion": relationship.dominant_emotion.value,
            "emotional_volatility": relationship.emotional_volatility,
            "positive_interactions": relationship.positive_interactions,
            "negative_interactions": relationship.negative_interactions,
            "relationship_started_at": relationship.relationship_started_at.isoformat() if relationship.relationship_started_at else None,
            "last_interaction_at": relationship.last_interaction_at.isoformat() if relationship.last_interaction_at else None,
            "longest_absence_days": relationship.longest_absence_days,
            "typical_response_time_seconds": relationship.typical_response_time_seconds,
            "typical_interaction_length": relationship.typical_interaction_length,
            "communication_frequency": relationship.communication_frequency,
            "interaction_count": relationship.interaction_count,
            "milestone_count": relationship.milestone_count,
            "milestone_data": relationship.milestone_data,
            "boundary_settings": relationship.boundary_settings,
            "communication_preferences": relationship.communication_preferences,
            "topic_interests": relationship.topic_interests,
            "personality_adaptations": relationship.personality_adaptations,
            "linguistic_adaptations": relationship.linguistic_adaptations,
            "created_at": relationship.created_at.isoformat() if relationship.created_at else None,
            "updated_at": relationship.updated_at.isoformat() if relationship.updated_at else None
        }
    
    def _serialize_contradiction(self, contradiction: DianaContradiction) -> Dict[str, Any]:
        """Convert a contradiction object to a serializable dictionary."""
        return {
            "id": contradiction.id,
            "user_id": contradiction.user_id,
            "contradiction_type": contradiction.contradiction_type,
            "original_statement": contradiction.original_statement,
            "contradicting_statement": contradiction.contradicting_statement,
            "resolution": contradiction.resolution,
            "detected_at": contradiction.detected_at.isoformat() if contradiction.detected_at else None,
            "context_data": contradiction.context_data,
            "is_resolved": contradiction.is_resolved,
            "resolved_at": contradiction.resolved_at.isoformat() if contradiction.resolved_at else None,
            "related_memory_ids": contradiction.related_memory_ids
        }
    
    def _serialize_adaptation(self, adaptation: DianaPersonalityAdaptation) -> Dict[str, Any]:
        """Convert a personality adaptation object to a serializable dictionary."""
        return {
            "id": adaptation.id,
            "user_id": adaptation.user_id,
            "warmth": adaptation.warmth,
            "formality": adaptation.formality,
            "humor": adaptation.humor,
            "directness": adaptation.directness,
            "assertiveness": adaptation.assertiveness,
            "curiosity": adaptation.curiosity,
            "emotional_expressiveness": adaptation.emotional_expressiveness,
            "message_length_preference": adaptation.message_length_preference,
            "complexity_level": adaptation.complexity_level,
            "emoji_usage": adaptation.emoji_usage,
            "response_delay": adaptation.response_delay,
            "topic_preferences": adaptation.topic_preferences,
            "taboo_topics": adaptation.taboo_topics,
            "memory_reference_frequency": adaptation.memory_reference_frequency,
            "adaptation_reason": adaptation.adaptation_reason,
            "last_significant_change": adaptation.last_significant_change.isoformat() if adaptation.last_significant_change else None,
            "confidence_score": adaptation.confidence_score,
            "created_at": adaptation.created_at.isoformat() if adaptation.created_at else None,
            "updated_at": adaptation.updated_at.isoformat() if adaptation.updated_at else None
        }