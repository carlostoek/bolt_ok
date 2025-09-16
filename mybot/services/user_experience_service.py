import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_models import UserNarrativeState, StoryFragment
from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext

# Placeholder types for return values
ChoicePatterns = Dict[str, Any]
AdaptedFragment = Dict[str, Any]
TeaserContent = str
UserInsights = Dict[str, Any]
EngagementPrediction = Dict[str, Any]
ContentRecommendations = List[Dict[str, Any]]

logger = logging.getLogger(__name__)

class UserExperienceService:
    """
    Service for enhancing the user's narrative experience through personalization.
    """

    def __init__(self, session: AsyncSession, character_voice_service: CharacterVoiceService):
        self.session = session
        self.character_voice_service = character_voice_service

    async def track_user_choice_patterns(self, user_id: int) -> ChoicePatterns:
        """
        Analyzes and tracks the user's choice patterns over time.
        """
        # TODO: Implement choice pattern tracking
        logger.info(f"Tracking choice patterns for user {user_id}")
        return {"status": "not_implemented"}

    async def adapt_narrative_to_user_archetype(self, user_id: int, fragment_id: str) -> AdaptedFragment:
        """
        Adapts a narrative fragment based on the user's archetype.
        """
        # TODO: Implement narrative adaptation logic
        logger.info(f"Adapting fragment {fragment_id} for user {user_id}")
        return {"original_fragment": fragment_id, "adapted_text": "not_implemented"}

    async def generate_personalized_teaser_content(self, user_id: int, restricted_content_key: str) -> TeaserContent:
        """
        Generates personalized teaser content for restricted narrative paths.
        This is more engaging than a simple "access denied" message.
        Now uses the comprehensive PersonalizedTeaserService for enhanced personalization.
        """
        logger.info(f"Generating personalized teaser for content '{restricted_content_key}' for user {user_id}")

        try:
            # Import PersonalizedTeaserService
            from services.personalized_teaser_service import PersonalizedTeaserService

            # Get the restricted fragment
            fragment_stmt = select(StoryFragment).where(StoryFragment.key == restricted_content_key)
            fragment_res = await self.session.execute(fragment_stmt)
            fragment = fragment_res.scalar_one_or_none()

            if not fragment:
                return "Un misterio se esconde aquí, pero su forma aún no está clara..."

            # Determine restriction type and amount
            restriction_type = "besitos"
            restriction_amount = fragment.min_besitos

            if fragment.required_role and fragment.required_role.lower() == "vip":
                restriction_type = "vip"
                restriction_amount = 0

            # Use PersonalizedTeaserService for comprehensive teaser generation
            teaser_service = PersonalizedTeaserService(self.session)
            teaser_result = await teaser_service.generate_personalized_teaser(
                user_id=user_id,
                restricted_fragment=fragment,
                restriction_type=restriction_type,
                restriction_amount=restriction_amount
            )

            # Return the personalized teaser content
            teaser_content = teaser_result.get("teaser_content", "")

            # Add purchase motivation if available
            purchase_motivation = teaser_result.get("purchase_motivation")
            if purchase_motivation and purchase_motivation.get("motivation_text"):
                teaser_content += f"\n\n*{purchase_motivation['motivation_text']}*"

                # Add relevant items suggestion if available
                relevant_items = purchase_motivation.get("relevant_items", [])
                if relevant_items:
                    teaser_content += "\n\n📦 *Objetos que podrían ayudarte:*"
                    for item in relevant_items[:2]:  # Show top 2 items
                        teaser_content += f"\n• {item['name']} ({item['price']} besitos)"

            return teaser_content

        except Exception as e:
            logger.error(f"Error generating personalized teaser using PersonalizedTeaserService: {e}")

            # Fallback to simpler teaser generation
            return await self._generate_fallback_teaser(user_id, restricted_content_key)

    async def _generate_fallback_teaser(self, user_id: int, restricted_content_key: str) -> str:
        """Fallback teaser generation if PersonalizedTeaserService fails."""
        try:
            user_state_stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            user_state_res = await self.session.execute(user_state_stmt)
            user_state = user_state_res.scalar_one_or_none()

            fragment_stmt = select(StoryFragment).where(StoryFragment.key == restricted_content_key)
            fragment_res = await self.session.execute(fragment_stmt)
            fragment = fragment_res.scalar_one_or_none()

            if not fragment:
                return "Un misterio se esconde aquí, pero su forma aún no está clara..."

            # Determine character and context for the teaser
            character = CharacterType.DIANA if fragment.character.lower() == 'diana' else CharacterType.LUCIEN

            # Base teaser message
            teaser_message = f"Sientes una presencia, una historia que anhela ser contada en '{fragment.key}'..."

            # Basic archetype personalization if available
            archetype = user_state.archetype_classification.get("archetype") if user_state and user_state.archetype_classification else None

            if archetype == "explorer":
                teaser_message += "\nTu espíritu curioso te ha traído hasta aquí. ¿Qué secretos crees que aguardan?"
            elif archetype == "poet":
                teaser_message += "\nLas palabras no dichas de este momento resuenan con tu alma. ¿Puedes oír su eco?"
            elif archetype == "direct":
                teaser_message += "\nHay un camino directo hacia este secreto, pero requiere una llave que aún no posees."

            # Use CharacterVoiceService to wrap the message in the character's voice
            emotional_context = EmotionalContext.PAUSA_REFLEXIVA

            enhanced_teaser = self.character_voice_service.enhance_message_with_character_voice(
                base_message=teaser_message,
                character=character,
                emotional_context=emotional_context
            )

            # Add a hint about how to unlock, if possible
            unlock_hint = ""
            if fragment.min_besitos > 0:
                unlock_hint = f"Parece que un gesto de mayor devoción ({fragment.min_besitos} besitos) podría desvelar este camino."
            elif fragment.required_role:
                unlock_hint = f"Solo aquellos con el estatus de '{fragment.required_role}' pueden transitar por aquí."

            final_teaser = enhanced_teaser
            if unlock_hint:
                final_teaser += f"\n\n*{unlock_hint}*"

            return final_teaser

        except Exception as e:
            logger.error(f"Error in fallback teaser generation: {e}")
            return "Un misterio te espera aquí, cuando estés listo para descubrirlo..."

    async def get_user_narrative_insights(self, user_id: int) -> UserInsights:
        """
        Provides deep insights into the user's narrative journey and preferences.
        """
        # TODO: Implement insight generation
        logger.info(f"Getting narrative insights for user {user_id}")
        return {"status": "not_implemented"}

    async def predict_user_engagement_path(self, user_id: int) -> EngagementPrediction:
        """
        Predicts the user's likely future engagement path based on their history.
        """
        # TODO: Implement engagement prediction
        logger.info(f"Predicting engagement path for user {user_id}")
        return {"status": "not_implemented"}

    async def generate_content_recommendations(self, user_id: int) -> ContentRecommendations:
        """
        Recommends narrative branches or items based on user preferences.
        """
        # TODO: Implement content recommendation logic
        logger.info(f"Generating content recommendations for user {user_id}")
        return []
