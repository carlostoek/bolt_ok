"""
Servicio unificado para el sistema de narrativa inmersiva.
Maneja la lógica de fragmentos, decisiones y progresión de historia.
"""
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from database.models import User, Achievement
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState, FragmentAnalytics, UserJourneyAnalytics
from services.point_service import PointService
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class NarrativeService:
    """Servicio principal del sistema narrativo unificado con analíticas integradas."""

    def __init__(self, session: AsyncSession, bot=None, analytics_enabled: bool = True):
        self.session = session
        self.bot = bot
        self.point_service = PointService(session) if session else None
        self.analytics_enabled = analytics_enabled
        self._session_start_times = {}  # Track session start times for analytics

    async def get_user_current_fragment(self, user_id: int) -> Optional[StoryFragment]:
        """Obtiene el fragmento actual del usuario o inicia la narrativa."""
        user_state = await self._get_or_create_user_state(user_id)

        if not user_state.current_fragment_key:
            start_fragment = await self._get_fragment_by_key("start")
            if start_fragment:
                user_state.current_fragment_key = start_fragment.key

                # Analytics tracking for auto-start
                if self.analytics_enabled:
                    await self._track_narrative_start(user_id, start_fragment)
                    self._session_start_times[user_id] = time.time()

                await self.session.commit()
                return start_fragment
            else:
                logger.error("No se encontró fragmento inicial 'start'")
                return None

        fragment = await self._get_fragment_by_key(user_state.current_fragment_key)

        # Track fragment view for analytics
        if self.analytics_enabled and fragment:
            await self._track_fragment_view(user_id, fragment)

        return fragment

    async def start_narrative(self, user_id: int) -> Optional[StoryFragment]:
        """Inicia la narrativa para un usuario nuevo."""
        user_state = await self._get_or_create_user_state(user_id)

        start_fragment = await self._get_fragment_by_key("start")
        if not start_fragment:
            logger.error("No se encontró fragmento inicial 'start'")
            return None

        if not await self._check_access_conditions(user_id, start_fragment):
            return None

        user_state.current_fragment_key = start_fragment.key
        user_state.choices_made = []
        user_state.narrative_started_at = datetime.utcnow()

        # Analytics tracking for narrative start
        if self.analytics_enabled:
            await self._track_narrative_start(user_id, start_fragment)
            self._session_start_times[user_id] = time.time()

        await self._process_fragment_rewards(user_id, start_fragment)

        await self.session.commit()

        logger.info(f"Narrativa iniciada para usuario {user_id}")
        return start_fragment

    async def process_user_decision(self, user_id: int, choice_index: int) -> Optional[StoryFragment]:
        """Procesa una decisión del usuario (basada en índice) y avanza la narrativa."""
        current_fragment = await self.get_user_current_fragment(user_id)
        if not current_fragment:
            return None
        
        choices = await self._get_fragment_choices(current_fragment.id)
        
        if not (0 <= choice_index < len(choices)):
            logger.warning(f"Índice de decisión inválido: {choice_index} para fragmento {current_fragment.key}")
            return None
            
        selected_choice = choices[choice_index]
        
        # Reutiliza la lógica de procesar por ID para mantener consistencia
        return await self._process_decision_by_id(user_id, selected_choice.id)

    async def process_user_decision_by_id(self, user_id: int, decision_id: int) -> Optional[StoryFragment]:
        """Procesa una decisión por su ID, verifica condiciones y avanza la historia."""
        decision = await self.session.get(NarrativeChoice, decision_id)
        if not decision:
            logger.warning(f"Decisión con ID {decision_id} no encontrada.")
            return None

        return await self._process_decision_by_id(user_id, decision.id)

    async def _process_decision_by_id(self, user_id: int, decision_id: int) -> Optional[StoryFragment]:
        """Lógica central para procesar una decisión y avanzar el estado."""
        decision = await self.session.get(NarrativeChoice, decision_id)
        if not decision:
            return None

        current_fragment = await self.get_user_current_fragment(user_id)
        source_fragment_key = current_fragment.key if current_fragment else None

        next_fragment = await self._get_fragment_by_key(decision.destination_fragment_key)
        if not next_fragment:
            logger.error(f"Fragmento de destino no encontrado: {decision.destination_fragment_key}")
            return None

        if not await self._check_access_conditions(user_id, next_fragment):
            logger.info(f"Usuario {user_id} no cumple condiciones para fragmento {next_fragment.key}")
            return None

        user_state = await self._get_or_create_user_state(user_id)
        if not user_state.choices_made:
            user_state.choices_made = []

        choice_data = {
            "fragment_key": source_fragment_key,
            "choice_id": decision.id,
            "choice_text": decision.text,
            "timestamp": datetime.utcnow().isoformat()
        }

        user_state.choices_made.append(choice_data)
        user_state.current_fragment_key = next_fragment.key
        user_state.fragments_visited = (user_state.fragments_visited or 0) + 1
        user_state.last_activity_at = datetime.utcnow()

        # Analytics tracking for choice made and fragment transition
        if self.analytics_enabled:
            session_time = self._get_session_time(user_id)
            await self._track_choice_made(user_id, current_fragment, decision, session_time)
            await self._track_fragment_progression(user_id, source_fragment_key, next_fragment.key)
            await self._update_user_journey_analytics(user_id, choice_data, next_fragment)

        await self._process_fragment_rewards(user_id, next_fragment)

        await self.session.commit()

        logger.info(f"Usuario {user_id} avanzó de {source_fragment_key} a {next_fragment.key}")
        return next_fragment

    async def get_user_narrative_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas narrativas del usuario con análisis enriquecido."""
        user_state = await self._get_or_create_user_state(user_id)

        total_fragments = await self._count_accessible_fragments(user_id)
        progress_percentage = ((user_state.fragments_visited or 0) / max(total_fragments, 1)) * 100

        # Get enhanced analytics if enabled
        analytics_data = {}
        if self.analytics_enabled:
            analytics_data = await self._get_user_analytics_summary(user_id)

        stats = {
            "current_fragment": user_state.current_fragment_key,
            "fragments_visited": user_state.fragments_visited or 0,
            "total_accessible": total_fragments,
            "progress_percentage": min(progress_percentage, 100),
            "choices_made": user_state.choices_made or [],
            "narrative_started_at": user_state.narrative_started_at.isoformat() if user_state.narrative_started_at else None,
            "last_activity_at": user_state.last_activity_at.isoformat() if user_state.last_activity_at else None
        }

        # Add analytics data if available
        if analytics_data:
            stats.update(analytics_data)

        return stats

    async def _get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo del usuario."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            user_state = UserNarrativeState(user_id=user_id)
            self.session.add(user_state)
            await self.session.flush()
            await self.session.refresh(user_state)
        
        return user_state

    async def _get_fragment_by_key(self, key: str) -> Optional[StoryFragment]:
        """Obtiene un fragmento por su clave única."""
        stmt = select(StoryFragment).where(StoryFragment.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_fragment_choices(self, fragment_id: int) -> List[NarrativeChoice]:
        """Obtiene las opciones de decisión para un fragmento."""
        stmt = select(NarrativeChoice).where(
            NarrativeChoice.source_fragment_id == fragment_id
        ).order_by(NarrativeChoice.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _check_access_conditions(self, user_id: int, fragment: StoryFragment) -> bool:
        """Verifica si el usuario puede acceder a un fragmento."""
        if not fragment:
            return False
        
        user = await self.session.get(User, user_id)
        if not user:
            return False

        if fragment.min_besitos > 0 and user.points < fragment.min_besitos:
            return False
        
        if fragment.required_role and self.bot:
            from utils.user_roles import get_user_role
            user_role = await get_user_role(self.bot, user_id, session=self.session)
            if user_role not in (fragment.required_role, "admin"):
                return False
        
        return True

    async def _process_fragment_rewards(self, user_id: int, fragment: StoryFragment):
        """Procesa las recompensas de un fragmento."""
        if fragment.reward_besitos > 0 and self.point_service and self.bot:
            await self.point_service.add_points(
                user_id, 
                fragment.reward_besitos, 
                bot=self.bot
            )
            logger.info(f"Usuario {user_id} recibió {fragment.reward_besitos} besitos del fragmento {fragment.key}")
        
        if fragment.unlocks_achievement_id:
            from services.achievement_service import AchievementService
            ach_service = AchievementService(self.session)
            achievement = await self.session.get(Achievement, fragment.unlocks_achievement_id)
            if achievement:
                await ach_service._grant(user_id, achievement, bot=self.bot)

    async def _count_accessible_fragments(self, user_id: int) -> int:
        """Cuenta los fragmentos accesibles para el usuario."""
        # This is a simplified count. A more accurate one would traverse the graph.
        stmt = select(func.count(StoryFragment.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_contextual_narrative_response(self, user_id: int, fragment: StoryFragment) -> Dict[str, Any]:
        """Genera respuesta narrativa contextualizada basada en historial del usuario."""
        if not self.analytics_enabled or not fragment:
            return {"fragment": fragment, "context": {}, "personalization": {}}

        user_state = await self._get_or_create_user_state(user_id)
        user_journey = await self._get_user_journey_analytics(user_id)

        context = {
            "is_returning_visitor": len(user_state.choices_made or []) > 0,
            "fragment_revisit": await self._is_fragment_revisit(user_id, fragment.key),
            "progression_path": [choice.get("fragment_key") for choice in (user_state.choices_made or [])][-5:],  # Last 5
            "character_familiarity": await self._get_character_familiarity(user_id, fragment.character)
        }

        personalization = {
            "suggested_tone": await self._suggest_narrative_tone(user_id, user_journey),
            "reference_previous_choices": await self._get_relevant_previous_choices(user_id, fragment),
            "teaser_content": await self._get_contextual_teasers(user_id, fragment)
        }

        return {
            "fragment": fragment,
            "context": context,
            "personalization": personalization,
            "analytics_timestamp": datetime.utcnow().isoformat()
        }

    async def unlock_lore_piece(self, user_id: int, lore_piece_id: int) -> bool:
        """
        Unlock a lore piece for the user.
        """
        from database.models import UserLorePiece
        # Check if already unlocked
        result = await self.session.execute(
            select(UserLorePiece).where(
                UserLorePiece.user_id == user_id,
                UserLorePiece.lore_piece_id == lore_piece_id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            # Add to user's unlocked lore pieces
            user_lore_piece = UserLorePiece(
                user_id=user_id,
                lore_piece_id=lore_piece_id
            )
            self.session.add(user_lore_piece)
            await self.session.commit()
            return True
        return False

    # ============================================================================
    # ANALYTICS INTEGRATION METHODS - Task 20 Implementation
    # ============================================================================

    def _get_session_time(self, user_id: int) -> float:
        """Calculate session time for current user session."""
        start_time = self._session_start_times.get(user_id)
        if start_time:
            return time.time() - start_time
        return 0.0

    async def _track_narrative_start(self, user_id: int, fragment: StoryFragment) -> None:
        """Track narrative start for analytics."""
        try:
            # Update or create user journey analytics
            journey = await self._get_or_create_user_journey_analytics(user_id)
            journey.journey_started_at = datetime.utcnow()
            journey.last_activity_at = datetime.utcnow()
            journey.session_count = (journey.session_count or 0) + 1
            journey.engagement_level = "new"

            # Track fragment view
            await self._increment_fragment_analytics(fragment.key, "view_count")

            logger.debug(f"Tracked narrative start for user {user_id} at fragment {fragment.key}")
        except Exception as e:
            logger.error(f"Error tracking narrative start: {e}")

    async def _track_fragment_view(self, user_id: int, fragment: StoryFragment) -> None:
        """Track fragment view for analytics."""
        try:
            # Update user journey
            journey = await self._get_or_create_user_journey_analytics(user_id)
            journey.last_activity_at = datetime.utcnow()

            # Add to visited fragments if not already there
            fragments_visited = journey.fragments_visited or []
            fragment_entry = {
                "fragment_key": fragment.key,
                "timestamp": datetime.utcnow().isoformat(),
                "character": fragment.character
            }
            fragments_visited.append(fragment_entry)
            journey.fragments_visited = fragments_visited

            # Track character interaction
            char_interactions = journey.character_interaction_count or {}
            char_interactions[fragment.character] = char_interactions.get(fragment.character, 0) + 1
            journey.character_interaction_count = char_interactions

            # Update fragment analytics
            await self._increment_fragment_analytics(fragment.key, "view_count")

            logger.debug(f"Tracked fragment view for user {user_id} at fragment {fragment.key}")
        except Exception as e:
            logger.error(f"Error tracking fragment view: {e}")

    async def _track_choice_made(self, user_id: int, fragment: StoryFragment, choice: NarrativeChoice, session_time: float) -> None:
        """Track user choice for comprehensive analytics."""
        try:
            # Update fragment analytics with choice distribution
            fragment_analytics = await self._get_or_create_fragment_analytics(fragment.key)
            choice_dist = fragment_analytics.choice_distribution or {}
            choice_dist[str(choice.id)] = choice_dist.get(str(choice.id), 0) + 1
            fragment_analytics.choice_distribution = choice_dist

            # Update most popular choice
            most_popular = max(choice_dist.items(), key=lambda x: x[1])
            fragment_analytics.most_popular_choice_id = int(most_popular[0])

            # Update timing analytics
            if session_time > 0:
                current_avg = fragment_analytics.average_time_spent or 0
                view_count = fragment_analytics.view_count or 1
                new_avg = ((current_avg * (view_count - 1)) + session_time) / view_count
                fragment_analytics.average_time_spent = int(new_avg)

            # Update user journey analytics
            journey = await self._get_or_create_user_journey_analytics(user_id)
            choices_made = journey.choices_made or []
            choice_entry = {
                "choice_id": choice.id,
                "fragment_key": fragment.key,
                "choice_text": choice.text,
                "timestamp": datetime.utcnow().isoformat(),
                "session_time": session_time
            }
            choices_made.append(choice_entry)
            journey.choices_made = choices_made
            journey.total_time_spent = (journey.total_time_spent or 0) + int(session_time)

            logger.debug(f"Tracked choice made for user {user_id}: choice {choice.id} in fragment {fragment.key}")
        except Exception as e:
            logger.error(f"Error tracking choice made: {e}")

    async def _track_fragment_progression(self, user_id: int, from_fragment: str, to_fragment: str) -> None:
        """Track progression between fragments."""
        try:
            # Update fragment analytics
            if from_fragment:
                from_analytics = await self._get_or_create_fragment_analytics(from_fragment)
                from_analytics.users_progressed_from = (from_analytics.users_progressed_from or 0) + 1
                from_analytics.completion_count = (from_analytics.completion_count or 0) + 1

            to_analytics = await self._get_or_create_fragment_analytics(to_fragment)
            to_analytics.users_returned_to = (to_analytics.users_returned_to or 0) + 1

            # Update user journey progression path
            journey = await self._get_or_create_user_journey_analytics(user_id)
            progression_path = journey.progression_path or []
            progression_path.append(to_fragment)
            journey.progression_path = progression_path
            journey.fragments_completed = (journey.fragments_completed or 0) + 1

            logger.debug(f"Tracked fragment progression for user {user_id}: {from_fragment} -> {to_fragment}")
        except Exception as e:
            logger.error(f"Error tracking fragment progression: {e}")

    async def _update_user_journey_analytics(self, user_id: int, choice_data: Dict, next_fragment: StoryFragment) -> None:
        """Update comprehensive user journey analytics."""
        try:
            journey = await self._get_or_create_user_journey_analytics(user_id)

            # Update engagement level based on activity
            fragments_completed = journey.fragments_completed or 0
            if fragments_completed >= 10:
                journey.engagement_level = "highly_engaged"
            elif fragments_completed >= 3:
                journey.engagement_level = "engaged"
            elif fragments_completed >= 1:
                journey.engagement_level = "active"

            # Calculate exploration score based on choice diversity
            choices_made = journey.choices_made or []
            unique_choices = len(set(c.get("choice_id") for c in choices_made))
            total_choices = len(choices_made)
            if total_choices > 0:
                journey.exploration_score = min(100, int((unique_choices / total_choices) * 100))

            # Update last fragment
            journey.last_fragment_key = next_fragment.key
            journey.last_activity_at = datetime.utcnow()

            # Reset session timer for next interaction
            self._session_start_times[user_id] = time.time()

            logger.debug(f"Updated user journey analytics for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating user journey analytics: {e}")

    async def _get_or_create_fragment_analytics(self, fragment_key: str) -> FragmentAnalytics:
        """Get or create fragment analytics record."""
        stmt = select(FragmentAnalytics).where(FragmentAnalytics.fragment_key == fragment_key)
        result = await self.session.execute(stmt)
        analytics = result.scalar_one_or_none()

        if not analytics:
            analytics = FragmentAnalytics(fragment_key=fragment_key)
            self.session.add(analytics)
            await self.session.flush()

        return analytics

    async def _get_or_create_user_journey_analytics(self, user_id: int) -> UserJourneyAnalytics:
        """Get or create user journey analytics record."""
        stmt = select(UserJourneyAnalytics).where(UserJourneyAnalytics.user_id == user_id)
        result = await self.session.execute(stmt)
        journey = result.scalar_one_or_none()

        if not journey:
            journey = UserJourneyAnalytics(user_id=user_id)
            self.session.add(journey)
            await self.session.flush()

        return journey

    async def _increment_fragment_analytics(self, fragment_key: str, metric: str) -> None:
        """Increment a specific metric in fragment analytics."""
        analytics = await self._get_or_create_fragment_analytics(fragment_key)
        current_value = getattr(analytics, metric, 0) or 0
        setattr(analytics, metric, current_value + 1)
        analytics.last_analyzed_at = datetime.utcnow()

    async def _get_user_analytics_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics summary for a user."""
        try:
            journey = await self._get_user_journey_analytics(user_id)
            if not journey:
                return {}

            return {
                "analytics": {
                    "engagement_level": journey.engagement_level,
                    "exploration_score": journey.exploration_score or 0,
                    "total_time_spent": journey.total_time_spent or 0,
                    "session_count": journey.session_count or 0,
                    "backtrack_count": journey.backtrack_count or 0,
                    "narrative_completion_percentage": journey.narrative_completion_percentage or 0,
                    "character_interactions": journey.character_interaction_count or {}
                }
            }
        except Exception as e:
            logger.error(f"Error getting user analytics summary: {e}")
            return {}

    async def _get_user_journey_analytics(self, user_id: int) -> Optional[UserJourneyAnalytics]:
        """Get user journey analytics record."""
        stmt = select(UserJourneyAnalytics).where(UserJourneyAnalytics.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================================
    # CONTEXT-AWARE NARRATIVE ENHANCEMENT METHODS - Task 20 Implementation
    # ============================================================================

    async def _is_fragment_revisit(self, user_id: int, fragment_key: str) -> bool:
        """Check if user has visited this fragment before."""
        try:
            journey = await self._get_user_journey_analytics(user_id)
            if not journey or not journey.fragments_visited:
                return False

            visited_fragments = [f.get("fragment_key") for f in journey.fragments_visited]
            return visited_fragments.count(fragment_key) > 1
        except Exception as e:
            logger.error(f"Error checking fragment revisit: {e}")
            return False

    async def _get_character_familiarity(self, user_id: int, character_name: str) -> Dict[str, Any]:
        """Get user's familiarity level with a character."""
        try:
            journey = await self._get_user_journey_analytics(user_id)
            if not journey or not journey.character_interaction_count:
                return {"level": "new", "interactions": 0}

            interactions = journey.character_interaction_count.get(character_name, 0)

            if interactions >= 20:
                level = "intimate"
            elif interactions >= 10:
                level = "familiar"
            elif interactions >= 5:
                level = "acquainted"
            else:
                level = "new"

            return {"level": level, "interactions": interactions}
        except Exception as e:
            logger.error(f"Error getting character familiarity: {e}")
            return {"level": "new", "interactions": 0}

    async def _suggest_narrative_tone(self, user_id: int, journey: Optional[UserJourneyAnalytics]) -> str:
        """Suggest narrative tone based on user behavior patterns."""
        try:
            if not journey:
                return "welcoming"

            engagement_level = journey.engagement_level or "new"
            exploration_score = journey.exploration_score or 0

            if engagement_level == "highly_engaged" and exploration_score > 70:
                return "adventurous"
            elif engagement_level == "engaged":
                return "encouraging"
            elif exploration_score < 30:
                return "guiding"
            else:
                return "balanced"
        except Exception as e:
            logger.error(f"Error suggesting narrative tone: {e}")
            return "neutral"

    async def _get_relevant_previous_choices(self, user_id: int, current_fragment: StoryFragment) -> List[Dict[str, Any]]:
        """Get previous choices relevant to current context."""
        try:
            user_state = await self._get_or_create_user_state(user_id)
            choices_made = user_state.choices_made or []

            # Get last 3 choices for context
            relevant_choices = choices_made[-3:] if len(choices_made) > 0 else []

            return [
                {
                    "fragment": choice.get("fragment_key"),
                    "choice_text": choice.get("choice_text"),
                    "timestamp": choice.get("timestamp"),
                    "relative_time": self._format_relative_time(choice.get("timestamp"))
                }
                for choice in relevant_choices
                if choice.get("fragment_key") != current_fragment.key  # Exclude current fragment
            ]
        except Exception as e:
            logger.error(f"Error getting relevant previous choices: {e}")
            return []

    async def _get_contextual_teasers(self, user_id: int, current_fragment: StoryFragment) -> Dict[str, Any]:
        """Generate contextual teasers based on user progress and items using personalized teaser service."""
        try:
            # Import here to avoid circular imports
            from services.personalized_teaser_service import PersonalizedTeaserService

            user = await self.session.get(User, user_id)
            if not user:
                return {}

            teasers = {
                "item_restricted_content": [],
                "progression_hints": [],
                "character_insights": [],
                "personalized_teasers": []
            }

            # Generate personalized teasers for access restrictions
            personalized_teaser_service = PersonalizedTeaserService(self.session)

            # Check for item-restricted content teasers
            if current_fragment.min_besitos > user.points:
                # Generate personalized teaser for besitos restriction
                personalized_teaser = await personalized_teaser_service.generate_personalized_teaser(
                    user_id=user_id,
                    restricted_fragment=current_fragment,
                    restriction_type="besitos",
                    restriction_amount=current_fragment.min_besitos
                )

                teasers["personalized_teasers"].append(personalized_teaser)

                # Also keep the basic teaser for backward compatibility
                teasers["item_restricted_content"].append({
                    "type": "besitos_required",
                    "requirement": current_fragment.min_besitos,
                    "current": user.points,
                    "message": f"Need {current_fragment.min_besitos - user.points} more besitos to unlock this content"
                })

            # Check for VIP restrictions
            if current_fragment.required_role and current_fragment.required_role.lower() == "vip":
                # Generate personalized teaser for VIP restriction
                personalized_vip_teaser = await personalized_teaser_service.generate_personalized_teaser(
                    user_id=user_id,
                    restricted_fragment=current_fragment,
                    restriction_type="vip",
                    restriction_amount=0
                )

                teasers["personalized_teasers"].append(personalized_vip_teaser)

            # Add progression hints based on character familiarity
            char_familiarity = await self._get_character_familiarity(user_id, current_fragment.character)
            if char_familiarity["level"] == "intimate":
                teasers["character_insights"].append({
                    "type": "deep_knowledge",
                    "character": current_fragment.character,
                    "message": f"Your deep connection with {current_fragment.character} reveals new perspectives"
                })

            return teasers
        except Exception as e:
            logger.error(f"Error generating contextual teasers: {e}")
            return {}

    def _format_relative_time(self, timestamp_str: str) -> str:
        """Format timestamp as relative time."""
        try:
            if not timestamp_str:
                return "unknown"

            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.utcnow()
            diff = now - timestamp

            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "just now"
        except Exception as e:
            logger.error(f"Error formatting relative time: {e}")
            return "unknown"
