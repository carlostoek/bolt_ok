"""
Servicio unificado para el sistema de narrativa inmersiva.
Maneja la lógica de fragmentos, decisiones y progresión de historia.
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import User, Achievement
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
from services.point_service import PointService
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrativeService:
    """Servicio principal del sistema narrativo unificado."""
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        self.point_service = PointService(session) if session else None

    async def get_user_current_fragment(self, user_id: int) -> Optional[StoryFragment]:
        """Obtiene el fragmento actual del usuario o inicia la narrativa."""
        user_state = await self._get_or_create_user_state(user_id)
        
        if not user_state.current_fragment_key:
            start_fragment = await self._get_fragment_by_key("start")
            if start_fragment:
                user_state.current_fragment_key = start_fragment.key
                await self.session.commit()
                return start_fragment
            else:
                logger.error("No se encontró fragmento inicial 'start'")
                return None
        
        return await self._get_fragment_by_key(user_state.current_fragment_key)

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

        source_fragment_key = (await self.get_user_current_fragment(user_id)).key

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
        
        user_state.choices_made.append({
            "source_fragment_key": source_fragment_key,
            "destination_fragment_key": next_fragment.key,
            "choice_text": decision.text,
            "timestamp": datetime.utcnow().isoformat()
        })

        user_state.current_fragment_key = next_fragment.key
        user_state.fragments_visited = (user_state.fragments_visited or 0) + 1
        user_state.last_activity_at = datetime.utcnow()
        
        await self._process_fragment_rewards(user_id, next_fragment)
        
        await self.session.commit()
        
        logger.info(f"Usuario {user_id} avanzó de {source_fragment_key} a {next_fragment.key}")
        return next_fragment

    async def go_back_to_previous_fragment(self, user_id: int) -> Optional[StoryFragment]:
        """Navega al fragmento anterior en el historial del usuario."""
        user_state = await self._get_or_create_user_state(user_id)

        if not user_state.choices_made or len(user_state.choices_made) == 0:
            logger.warning(f"Usuario {user_id} no tiene historial para retroceder")
            return None

        # Obtener el último elemento del historial
        last_choice = user_state.choices_made[-1]
        previous_fragment_key = last_choice.get("source_fragment_key")

        if not previous_fragment_key:
            logger.warning(f"No se encontró fragmento anterior en el historial para usuario {user_id}")
            return None

        # Obtener el fragmento anterior
        previous_fragment = await self._get_fragment_by_key(previous_fragment_key)
        if not previous_fragment:
            logger.error(f"Fragmento anterior no encontrado: {previous_fragment_key}")
            return None

        # Actualizar estado: remover última decisión y regresar al fragmento anterior
        user_state.choices_made.pop()
        user_state.current_fragment_key = previous_fragment_key
        user_state.last_activity_at = datetime.utcnow()

        await self.session.commit()

        logger.info(f"Usuario {user_id} retrocedió a fragmento {previous_fragment_key}")
        return previous_fragment

    async def can_go_back(self, user_id: int) -> bool:
        """Verifica si el usuario puede retroceder en la narrativa."""
        user_state = await self._get_or_create_user_state(user_id)
        return bool(user_state.choices_made and len(user_state.choices_made) > 0)

    async def get_user_narrative_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas narrativas del usuario."""
        user_state = await self._get_or_create_user_state(user_id)

        total_fragments = await self._count_accessible_fragments(user_id)
        progress_percentage = ((user_state.fragments_visited or 0) / max(total_fragments, 1)) * 100

        return {
            "current_fragment": user_state.current_fragment_key,
            "fragments_visited": user_state.fragments_visited or 0,
            "total_accessible": total_fragments,
            "progress_percentage": min(progress_percentage, 100),
            "choices_made": user_state.choices_made or [],
            "can_go_back": await self.can_go_back(user_id)
        }

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
