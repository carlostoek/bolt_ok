"""
Personalized Teaser Content Service
Task 21: Implement personalized teaser content system

This service creates contextually appropriate and personalized teaser content for
item-restricted narrative content. It integrates user archetype analysis,
character voice patterns, and shop item relationships to create compelling
teasers that motivate engagement rather than simply blocking access.
"""
import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# Core services
from database.models import User, ShopItem, UserPurchase
from database.narrative_models import StoryFragment, UserNarrativeState, UserJourneyAnalytics
from database.emotional_models import UserEmotionalProfile, ArchetypeClassification
from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
from services.emotional_service import EmotionalService
from services.shop_service import ShopService

logger = logging.getLogger(__name__)


class PersonalizedTeaserService:
    """
    Creates personalized teaser content that adapts to user archetypes,
    character relationships, and purchase history to create compelling
    motivation for engagement with restricted content.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_voice_service = CharacterVoiceService()
        self.emotional_service = EmotionalService(session)
        self.shop_service = ShopService(session)

    async def generate_personalized_teaser(
        self,
        user_id: int,
        restricted_fragment: StoryFragment,
        restriction_type: str = "besitos",
        restriction_amount: int = 0
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive personalized teaser for restricted content.

        Args:
            user_id: User requesting access
            restricted_fragment: The fragment they cannot access
            restriction_type: Type of restriction (besitos, vip, item)
            restriction_amount: Amount needed (for besitos)

        Returns:
            Complete teaser response with personalized content
        """
        try:
            # Gather user data for personalization
            user_context = await self._gather_user_context(user_id)

            # Determine appropriate character to deliver teaser
            character = self._determine_teaser_character(restricted_fragment, user_context)

            # Get user archetype for personalization
            archetype = user_context.get("archetype", "explorer")

            # Generate archetype-specific teaser content
            base_teaser = await self._generate_archetype_teaser(
                archetype, restricted_fragment, restriction_type, restriction_amount, user_context
            )

            # Determine emotional context for character voice
            emotional_context = self._determine_emotional_context(user_context, restriction_type)

            # Enhance with character voice
            character_enhanced_teaser = self.character_voice_service.enhance_message_with_character_voice(
                base_message=base_teaser["content"],
                character=character,
                emotional_context=emotional_context
            )

            # Add purchase motivation if relevant
            purchase_motivation = await self._generate_purchase_motivation(
                user_id, restriction_type, restriction_amount, archetype, character
            )

            # Track teaser analytics
            await self._track_teaser_analytics(
                user_id, restricted_fragment.key, archetype, character.value, restriction_type
            )

            return {
                "teaser_content": character_enhanced_teaser,
                "purchase_motivation": purchase_motivation,
                "character": character.value,
                "archetype": archetype,
                "restriction_info": {
                    "type": restriction_type,
                    "amount_needed": restriction_amount,
                    "fragment_key": restricted_fragment.key
                },
                "personalization_data": base_teaser.get("personalization_notes", {}),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating personalized teaser for user {user_id}: {e}")
            return await self._generate_fallback_teaser(restricted_fragment, restriction_type, restriction_amount)

    async def _gather_user_context(self, user_id: int) -> Dict[str, Any]:
        """Gather comprehensive user context for personalization."""
        try:
            context = {}

            # Basic user info
            user = await self.session.get(User, user_id)
            if user:
                context.update({
                    "points": user.points,
                    "level": user.level,
                    "role": user.role
                })

            # Emotional profile and archetype
            emotional_profile = await self.session.get(UserEmotionalProfile, user_id)
            if emotional_profile:
                context.update({
                    "archetype": emotional_profile.archetype_classification.value,
                    "archetype_confidence": emotional_profile.archetype_confidence,
                    "vulnerability_level": emotional_profile.vulnerability_level,
                    "authenticity_score": emotional_profile.authenticity_score
                })
            else:
                # Default to explorer archetype if no data available
                context["archetype"] = "explorer"

            # Narrative journey data
            journey = await self._get_user_journey_data(user_id)
            if journey:
                context.update({
                    "engagement_level": journey.engagement_level,
                    "exploration_score": journey.exploration_score or 0,
                    "total_time_spent": journey.total_time_spent or 0,
                    "character_interactions": journey.character_interaction_count or {},
                    "fragments_completed": journey.fragments_completed or 0
                })

            # Purchase history
            purchase_history = await self._get_purchase_context(user_id)
            context.update(purchase_history)

            return context

        except Exception as e:
            logger.error(f"Error gathering user context for {user_id}: {e}")
            return {"archetype": "explorer"}

    async def _generate_archetype_teaser(
        self,
        archetype: str,
        fragment: StoryFragment,
        restriction_type: str,
        restriction_amount: int,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate teaser content specific to user archetype."""

        archetype_strategies = {
            "explorer": self._create_explorer_teaser,
            "direct": self._create_direct_teaser,
            "poet": self._create_poet_teaser,
            "analytic": self._create_analytic_teaser,
            "patient": self._create_patient_teaser
        }

        strategy = archetype_strategies.get(archetype, self._create_explorer_teaser)
        return await strategy(fragment, restriction_type, restriction_amount, user_context)

    async def _create_explorer_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teasers for Explorer archetype - emphasize discovery and mystery."""

        explorer_hooks = [
            f"Un sendero inexplorado se abre ante ti en '{fragment.key}'...",
            "Hay territorios desconocidos esperando ser descubiertos aquí.",
            "Tu espíritu aventurero ha encontrado una puerta hacia lo inexplorado.",
            "Un misterio sin resolver palpita en este espacio vedado.",
            "Los exploradores como tú siempre encuentran lo que otros no ven."
        ]

        mystery_elements = [
            "¿Qué secretos esconde este fragmento?",
            "Solo los verdaderamente curiosos descubren lo que aguarda aquí.",
            "Tu instinto de explorador te dice que algo importante te espera.",
            "Cada paso hacia lo desconocido revela nuevas maravillas."
        ]

        base_content = f"{random.choice(explorer_hooks)}\n\n{random.choice(mystery_elements)}"

        # Add progression motivation
        if user_context.get("exploration_score", 0) > 50:
            base_content += "\n\nTu experiencia explorando otros caminos te ha preparado para esto."

        return {
            "content": base_content,
            "archetype_approach": "discovery_focused",
            "personalization_notes": {
                "emphasizes": "mystery and discovery",
                "motivation_type": "curiosity_driven"
            }
        }

    async def _create_direct_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teasers for Direct archetype - straightforward and action-oriented."""

        direct_approaches = [
            f"Acceso directo a '{fragment.key}' disponible con los recursos adecuados.",
            "Camino bloqueado. Se requiere acción específica para continuar.",
            "Contenido premium esperando. Tu decisión determinará el próximo paso.",
            "Barrera identificada. Solución clara disponible.",
            "Restricción presente. Método de acceso definido."
        ]

        action_calls = [
            "La solución es simple y directa.",
            "No hay rodeos necesarios aquí.",
            "Tu enfoque práctico aprecia la claridad de esta situación.",
            "Una inversión estratégica desbloquea el contenido inmediatamente."
        ]

        base_content = f"{random.choice(direct_approaches)}\n\n{random.choice(action_calls)}"

        # Add efficiency motivation
        if restriction_type == "besitos":
            base_content += f"\n\nInversión requerida: {restriction_amount} besitos. Resultado inmediato garantizado."

        return {
            "content": base_content,
            "archetype_approach": "efficiency_focused",
            "personalization_notes": {
                "emphasizes": "clear action and immediate results",
                "motivation_type": "solution_oriented"
            }
        }

    async def _create_poet_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teasers for Poet archetype - emotional and aesthetic."""

        poetic_imagery = [
            f"En '{fragment.key}' habitan palabras aún no escritas, esperando tu toque para cobrar vida.",
            "Hay una sinfonía silenciosa en este espacio, una melodía que solo tu alma puede escuchar.",
            "Los versos no escritos de esta historia susurran tu nombre desde las sombras.",
            "Un lienzo emocional en blanco aguarda que tu sensibilidad lo pinte de experiencias.",
            "Las emociones más profundas de este relato esperan encontrarse con tu corazón."
        ]

        aesthetic_elements = [
            "La belleza de lo no revelado tiene su propio encanto.",
            "Hay poesía en la anticipación, música en el deseo.",
            "Tu naturaleza artística percibe la promesa de belleza que se esconde aquí.",
            "Los momentos más hermosos nacen del anhelo cultivado con paciencia."
        ]

        base_content = f"{random.choice(poetic_imagery)}\n\n{random.choice(aesthetic_elements)}"

        # Add aesthetic motivation
        character_interactions = user_context.get("character_interactions", {})
        diana_count = character_interactions.get("Diana", 0)

        if diana_count > 5:
            base_content += "\n\nTu conexión creciente con Diana ha afinado tu percepción de estos matices sutiles."

        return {
            "content": base_content,
            "archetype_approach": "aesthetic_focused",
            "personalization_notes": {
                "emphasizes": "beauty and emotional depth",
                "motivation_type": "aesthetic_appreciation"
            }
        }

    async def _create_analytic_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teasers for Analytic archetype - logical and systematic."""

        analytical_frameworks = [
            f"Análisis de '{fragment.key}': Contenido de alta relevancia identificado.",
            "Datos insuficientes para acceso completo. Ampliación de recursos requerida.",
            "Patrón identificado: Contenido premium correlacionado con experiencias mejoradas.",
            "Variable de acceso: Recursos necesarios para completar ecuación narrativa.",
            "Métrica detectada: Inversión estratégica optimiza retorno experiencial."
        ]

        logical_justifications = [
            "El análisis histórico sugiere que el contenido restringido ofrece valor diferenciado.",
            "Tu patrón de exploración sistemática te ha preparado para este nivel de contenido.",
            "La lógica sugiere que la inversión en este punto maximiza la comprensión narrativa.",
            "Los datos de tu progresión indican alta compatibilidad con este material."
        ]

        base_content = f"{random.choice(analytical_frameworks)}\n\n{random.choice(logical_justifications)}"

        # Add analytical motivation with data
        completion_rate = min(100, (user_context.get("fragments_completed", 0) / max(1, user_context.get("fragments_completed", 1))) * 100)

        if completion_rate > 0:
            base_content += f"\n\nTasa de finalización actual: {completion_rate:.1f}%. Acceso optimizaría progresión."

        return {
            "content": base_content,
            "archetype_approach": "logic_focused",
            "personalization_notes": {
                "emphasizes": "data and logical progression",
                "motivation_type": "optimization_driven"
            }
        }

    async def _create_patient_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teasers for Patient archetype - gradual and contemplative."""

        patient_approaches = [
            f"'{fragment.key}' permanece en calma, esperando el momento adecuado para revelarse.",
            "Como todas las cosas valiosas, este contenido aguarda con paciencia infinita.",
            "No hay prisa aquí. Este fragmento comprende el valor del tiempo bien invertido.",
            "La paciencia es una virtud que este espacio narrativo respeta profundamente.",
            "En el ritmo correcto de las cosas, todo encuentra su momento perfecto de revelación."
        ]

        contemplative_elements = [
            "Tu capacidad para la reflexión profunda se alinea perfectamente con lo que aguarda aquí.",
            "Los tesoros más valiosos se revelan solo a quienes saben cultivar la paciencia.",
            "Tu comprensión del timing narrativo te permitirá apreciar plenamente este contenido.",
            "La contemplación previa enriquece exponencialmente la experiencia final."
        ]

        base_content = f"{random.choice(patient_approaches)}\n\n{random.choice(contemplative_elements)}"

        # Add patience-based motivation
        total_time = user_context.get("total_time_spent", 0)
        if total_time > 1800:  # More than 30 minutes total
            base_content += "\n\nTu dedicación temporal demuestra la profundidad de tu compromiso con esta narrativa."

        return {
            "content": base_content,
            "archetype_approach": "patience_focused",
            "personalization_notes": {
                "emphasizes": "timing and contemplation",
                "motivation_type": "patience_rewarded"
            }
        }

    def _determine_teaser_character(
        self, fragment: StoryFragment, user_context: Dict[str, Any]
    ) -> CharacterType:
        """Determine which character should deliver the teaser."""

        # If fragment specifies a character, generally use that character
        fragment_character = fragment.character.lower()

        # Character interaction history influences choice
        character_interactions = user_context.get("character_interactions", {})
        diana_interactions = character_interactions.get("Diana", 0)
        lucien_interactions = character_interactions.get("Lucien", 0)

        # User archetype influences character choice
        archetype = user_context.get("archetype", "explorer")

        # Decision logic
        if fragment_character == "diana":
            # Diana content - usually Diana delivers teaser, but Lucien can if user needs guidance
            if user_context.get("engagement_level") == "new" or diana_interactions < 3:
                return CharacterType.LUCIEN  # Lucien introduces Diana content
            return CharacterType.DIANA

        elif fragment_character == "lucien":
            # Lucien content - Lucien usually delivers
            return CharacterType.LUCIEN

        else:
            # General content - choose based on user patterns
            if archetype in ["analytic", "direct"] or lucien_interactions > diana_interactions:
                return CharacterType.LUCIEN
            return CharacterType.DIANA

    def _determine_emotional_context(
        self, user_context: Dict[str, Any], restriction_type: str
    ) -> EmotionalContext:
        """Determine appropriate emotional context for character voice."""

        engagement_level = user_context.get("engagement_level", "new")
        vulnerability_level = user_context.get("vulnerability_level", 0.3)
        total_interactions = sum(user_context.get("character_interactions", {}).values())

        # New users get welcoming context
        if total_interactions < 5:
            return EmotionalContext.NUEVO_USUARIO

        # Advanced users get different treatment
        elif total_interactions > 50:
            return EmotionalContext.USUARIO_AVANZADO

        # High vulnerability users get gentle approach
        elif vulnerability_level > 0.6:
            return EmotionalContext.VULNERABILIDAD_ALTA

        # High engagement gets encouraging approach
        elif engagement_level == "highly_engaged":
            return EmotionalContext.ENGAGEMENT_ALTO

        # Low engagement needs motivation
        elif engagement_level in ["new", "stalled"]:
            return EmotionalContext.ENGAGEMENT_BAJO

        # Default to reflective pause
        return EmotionalContext.PAUSA_REFLEXIVA

    async def _generate_purchase_motivation(
        self,
        user_id: int,
        restriction_type: str,
        restriction_amount: int,
        archetype: str,
        character: CharacterType
    ) -> Optional[Dict[str, Any]]:
        """Generate purchase motivation based on restriction type and user profile."""

        if restriction_type != "besitos":
            return None

        try:
            # Get user's current points
            user = await self.session.get(User, user_id)
            if not user:
                return None

            current_points = user.points
            points_needed = max(0, restriction_amount - current_points)

            # Find relevant shop items that could help
            relevant_items = await self._find_relevant_shop_items(user_id, points_needed)

            # Generate archetype-specific motivation
            motivation_messages = {
                "explorer": [
                    "Nuevos horizontes esperan ser explorados con los recursos adecuados.",
                    "Tu espíritu aventurero merece acceso a todos los territorios narrativos.",
                    "Los exploradores más exitosos invierten en las herramientas correctas."
                ],
                "direct": [
                    f"Solución directa: {points_needed} besitos adicionales desbloquean acceso inmediato.",
                    "Inversión estratégica con retorno garantizado de contenido premium.",
                    "Método más eficiente: adquisición de recursos específicos."
                ],
                "poet": [
                    "La belleza completa de esta narrativa merece tu inversión emocional.",
                    "Algunas experiencias artísticas requieren compromiso para revelarse plenamente.",
                    "Tu sensibilidad poética encontrará valor en esta inversión creativa."
                ],
                "analytic": [
                    f"Análisis de costo-beneficio: {points_needed} besitos por acceso a contenido diferenciado.",
                    "Optimización de recursos narrativos mediante inversión dirigida.",
                    "Ecuación simple: Inversión estratégica = Experiencia maximizada."
                ],
                "patient": [
                    "Las inversiones más sabias son aquellas hechas con contemplación cuidadosa.",
                    "El momento adecuado para invertir en tu experiencia narrativa ha llegado.",
                    "La paciencia cultivada merece ser recompensada con acceso completo."
                ]
            }

            motivation_text = random.choice(motivation_messages.get(archetype, motivation_messages["explorer"]))

            return {
                "motivation_text": motivation_text,
                "points_needed": points_needed,
                "current_points": current_points,
                "target_amount": restriction_amount,
                "relevant_items": relevant_items,
                "character_voice": character.value
            }

        except Exception as e:
            logger.error(f"Error generating purchase motivation: {e}")
            return None

    async def _find_relevant_shop_items(self, user_id: int, points_needed: int) -> List[Dict[str, Any]]:
        """Find shop items that could help user reach their goal."""
        try:
            # Get user's available items from shop service
            available_items = await self.shop_service.get_available_items(user_id)

            # Focus on items that provide points or besitos
            relevant_items = []

            for item in available_items[:3]:  # Limit to top 3 suggestions
                # Check if user already has this item
                has_item = await self.shop_service.has_item_in_inventory(user_id, item.name)

                if not has_item:
                    relevant_items.append({
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "price": item.price,
                        "relevance_note": f"Acceso a contenido exclusivo que enriquece tu experiencia narrativa"
                    })

            return relevant_items

        except Exception as e:
            logger.error(f"Error finding relevant shop items: {e}")
            return []

    async def _get_user_journey_data(self, user_id: int) -> Optional[UserJourneyAnalytics]:
        """Get user journey analytics data."""
        try:
            stmt = select(UserJourneyAnalytics).where(UserJourneyAnalytics.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user journey data: {e}")
            return None

    async def _get_purchase_context(self, user_id: int) -> Dict[str, Any]:
        """Get user's purchase history context."""
        try:
            stmt = select(func.count(UserPurchase.id), func.coalesce(func.sum(UserPurchase.price_paid), 0)).where(
                UserPurchase.user_id == user_id
            )
            result = await self.session.execute(stmt)
            purchase_count, total_spent = result.first() or (0, 0)

            return {
                "total_purchases": purchase_count,
                "total_spent": total_spent,
                "is_customer": purchase_count > 0,
                "is_frequent_customer": purchase_count >= 3
            }
        except Exception as e:
            logger.error(f"Error getting purchase context: {e}")
            return {"total_purchases": 0, "total_spent": 0, "is_customer": False}

    async def _track_teaser_analytics(
        self,
        user_id: int,
        fragment_key: str,
        archetype: str,
        character: str,
        restriction_type: str
    ) -> None:
        """Track teaser generation for analytics."""
        try:
            # Create or update teaser analytics (this could be expanded into a dedicated table)
            # For now, we'll use existing analytics infrastructure

            # You could extend UserJourneyAnalytics or create a new TeaserAnalytics table
            # This is a placeholder for future analytics expansion

            logger.info(f"Teaser analytics: user={user_id}, fragment={fragment_key}, "
                       f"archetype={archetype}, character={character}, restriction={restriction_type}")

        except Exception as e:
            logger.error(f"Error tracking teaser analytics: {e}")

    async def _generate_fallback_teaser(
        self, fragment: StoryFragment, restriction_type: str, restriction_amount: int
    ) -> Dict[str, Any]:
        """Generate a fallback teaser when personalization fails."""

        fallback_content = f"Un fragmento especial de la historia aguarda en '{fragment.key}'."

        if restriction_type == "besitos" and restriction_amount > 0:
            fallback_content += f"\n\nSe requieren {restriction_amount} besitos para acceder a este contenido exclusivo."
        elif restriction_type == "vip":
            fallback_content += "\n\nEste contenido está disponible para miembros VIP."

        fallback_content += "\n\n*Un misterio te espera, cuando estés listo para descubrirlo...*"

        return {
            "teaser_content": fallback_content,
            "purchase_motivation": None,
            "character": "lucien",
            "archetype": "explorer",
            "restriction_info": {
                "type": restriction_type,
                "amount_needed": restriction_amount,
                "fragment_key": fragment.key
            },
            "personalization_data": {},
            "generated_at": datetime.utcnow().isoformat(),
            "fallback": True
        }

    async def get_teaser_effectiveness_stats(
        self, fragment_key: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics on teaser effectiveness (placeholder for future analytics expansion)."""
        try:
            # This would query teaser analytics tables to provide insights on:
            # - Conversion rates by archetype
            # - Most effective character/archetype combinations
            # - Purchase completion rates after teaser views
            # - A/B testing results for different teaser approaches

            # For now, return placeholder data structure
            return {
                "period_days": days,
                "fragment_key": fragment_key,
                "total_teasers_generated": 0,
                "conversion_rate_by_archetype": {},
                "effective_character_combinations": {},
                "average_time_to_conversion": 0,
                "most_effective_approaches": [],
                "recommendations": []
            }

        except Exception as e:
            logger.error(f"Error getting teaser effectiveness stats: {e}")
            return {}