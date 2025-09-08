from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.narrative_unified import UserNarrativeState, NarrativeFragment
from database.models import User, LorePiece
from services.interfaces import IUserNarrativeService, IRewardSystem
import logging

logger = logging.getLogger(__name__)


# Simple decorator to replace safe_handler
def safe_handler(func):
    """Simple decorator to handle exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper


class UserNarrativeService(IUserNarrativeService):
    """Servicio para gestionar el estado narrativo unificado de los usuarios."""
    
    def __init__(self, session: AsyncSession, reward_system: IRewardSystem):
        """
        Constructor con inyección de dependencias.
        
        Args:
            session (AsyncSession): Sesión de base de datos
            reward_system (IRewardSystem): Sistema de recompensas
        """
        self.session = session
        self.reward_system = reward_system
        
        # Optional Cinema System Integration
        self.cinema_master = None
        try:
            from .cinema_master_integration import get_cinema_master_integration
            self.cinema_master = get_cinema_master_integration(session)
            logger.info("Cinema Master Integration available for UserNarrativeService")
        except ImportError:
            logger.info("Cinema Master Integration not available for UserNarrativeService")
        except Exception as e:
            logger.warning(f"Failed to initialize Cinema Master Integration: {e}")

    async def get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserNarrativeState: Estado narrativo del usuario
            
        Raises:
            ValueError: Si el usuario no existe
        """
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            # Verificar que el usuario exista
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"Usuario con ID {user_id} no encontrado")
            
            state = UserNarrativeState(
                user_id=user_id,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[]
            )
            self.session.add(state)
            await self.session.commit()
            await self.session.refresh(state)
            
        return state

    async def update_current_fragment(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        """Actualiza el fragmento actual del usuario.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si el fragmento no existe o está inactivo
        """
        state = await self.get_or_create_user_state(user_id)
        
        # Verificar que el fragmento exista
        fragment_stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        fragment_result = await self.session.execute(fragment_stmt)
        fragment = fragment_result.scalar_one_or_none()
        
        if not fragment:
            raise ValueError(f"Fragmento con ID {fragment_id} no encontrado o inactivo")
        
        state.current_fragment_id = fragment_id
        
        # Añadir a fragmentos visitados si no está ya
        if fragment_id not in state.visited_fragments:
            state.visited_fragments.append(fragment_id)
        
        await self.session.commit()
        await self.session.refresh(state)
        
        return state

    async def mark_fragment_completed(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        """Marca un fragmento como completado por el usuario.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si el fragmento no existe o está inactivo
        """
        state = await self.get_or_create_user_state(user_id)
        
        # Verificar que el fragmento exista
        fragment_stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        fragment_result = await self.session.execute(fragment_stmt)
        fragment = fragment_result.scalar_one_or_none()
        
        if not fragment:
            raise ValueError(f"Fragmento con ID {fragment_id} no encontrado o inactivo")
        
        # Añadir a fragmentos completados si no está ya
        if fragment_id not in state.completed_fragments:
            state.completed_fragments.append(fragment_id)
            
            # Procesar triggers del fragmento
            await self._process_fragment_triggers(user_id, fragment)
        
        await self.session.commit()
        await self.session.refresh(state)
        
        return state

    async def unlock_clue(self, user_id: int, clue_code: str) -> UserNarrativeState:
        """Desbloquea una pista para el usuario.
        
        Args:
            user_id (int): ID del usuario
            clue_code (str): Código de la pista a desbloquear
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si la pista no existe o está inactiva
        """
        state = await self.get_or_create_user_state(user_id)
        
        # Verificar que la pista exista
        clue_stmt = select(LorePiece).where(
            LorePiece.code_name == clue_code,
            LorePiece.is_active == True
        )
        clue_result = await self.session.execute(clue_stmt)
        clue = clue_result.scalar_one_or_none()
        
        if not clue:
            raise ValueError(f"Pista con código {clue_code} no encontrada o inactiva")
        
        # Añadir a pistas desbloqueadas si no está ya
        if clue_code not in state.unlocked_clues:
            state.unlocked_clues.append(clue_code)
        
        await self.session.commit()
        await self.session.refresh(state)
        
        return state

    async def check_user_access(self, user_id: int, fragment_id: str) -> bool:
        """Verifica si un usuario tiene acceso a un fragmento.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            bool: True si el usuario tiene acceso, False en caso contrario
        """
        state = await self.get_or_create_user_state(user_id)
        
        # Obtener el fragmento
        fragment_stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        fragment_result = await self.session.execute(fragment_stmt)
        fragment = fragment_result.scalar_one_or_none()
        
        if not fragment:
            return False
            
        # Si no hay pistas requeridas, el usuario tiene acceso
        if not fragment.required_clues:
            return True
            
        # Verificar si el usuario ha desbloqueado todas las pistas requeridas
        return all(clue in state.unlocked_clues for clue in fragment.required_clues)

    async def get_user_progress_percentage(self, user_id: int) -> float:
        """Obtiene el porcentaje de progreso del usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        state = await self.get_or_create_user_state(user_id)
        return state.get_progress_percentage(self.session)

    async def _process_fragment_triggers(self, user_id: int, fragment: NarrativeFragment):
        """Procesa los triggers de un fragmento completado.
        
        Args:
            user_id (int): ID del usuario
            fragment (NarrativeFragment): Fragmento completado
        """
        if not fragment.triggers:
            return
            
        # Procesar recompensas de puntos
        if "reward_points" in fragment.triggers:
            points = fragment.triggers["reward_points"]
            try:
                await self.reward_system.grant_reward(
                    user_id=user_id,
                    reward_type='points',
                    reward_data={
                        'amount': points,
                        'description': f'Recompensa por completar fragmento: {fragment.title}'
                    },
                    source='narrative_fragment'
                )
                logger.info(f"Otorgados {points} puntos al usuario {user_id} por completar fragmento {fragment.id}")
            except Exception as e:
                logger.error(f"Error al otorgar puntos al usuario {user_id}: {e}")
            
        # Procesar desbloqueo de pistas
        if "unlock_lore" in fragment.triggers:
            clue_code = fragment.triggers["unlock_lore"]
            try:
                await self.reward_system.grant_reward(
                    user_id=user_id,
                    reward_type='clue',
                    reward_data={
                        'clue_code': clue_code,
                        'description': f'Pista desbloqueada por completar fragmento: {fragment.title}'
                    },
                    source='narrative_fragment'
                )
                logger.info(f"Desbloqueada pista {clue_code} para usuario {user_id}")
            except Exception as e:
                logger.error(f"Error al desbloquear pista {clue_code} para usuario {user_id}: {e}")

    async def reset_user_progress(self, user_id: int) -> UserNarrativeState:
        """Restablece el progreso narrativo del usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserNarrativeState: Estado narrativo reiniciado del usuario
        """
        state = await self.get_or_create_user_state(user_id)
        
        state.current_fragment_id = None
        state.visited_fragments = []
        state.completed_fragments = []
        state.unlocked_clues = []
        
        await self.session.commit()
        await self.session.refresh(state)
        
        return state

    # ==================== CINEMA ENHANCED METHODS ====================
    
    async def get_user_state_enhanced(self, user_id: int) -> Dict[str, Any]:
        """
        Enhanced user state retrieval with soul signature personalization.
        Falls back to standard functionality if cinema systems unavailable.
        
        Args:
            user_id: User ID
            
        Returns:
            Enhanced user state data with personalization if available
        """
        try:
            # Get standard user state
            standard_state = await self.get_or_create_user_state(user_id)
            
            result = {
                "user_id": user_id,
                "current_fragment_id": standard_state.current_fragment_id,
                "completed_fragments": standard_state.completed_fragments,
                "unlocked_clues": standard_state.unlocked_clues,
                "visited_fragments": standard_state.visited_fragments,
                "enhanced": False
            }
            
            # Try cinema enhancement
            if self.cinema_master and self.cinema_master.is_soul_signature_available():
                try:
                    # Get soul signature personalization
                    soul_signature = getattr(self.cinema_master, 'soul_signature', None)
                    if soul_signature and hasattr(soul_signature, 'get_user_personalization_profile'):
                        personalization = await soul_signature.get_user_personalization_profile(user_id)
                        result.update({
                            "personalization_profile": personalization,
                            "enhanced": True,
                            "enhancement_type": "soul_signature"
                        })
                except Exception as e:
                    logger.warning(f"Soul signature enhancement failed for user {user_id}: {e}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in get_user_state_enhanced for user {user_id}: {e}")
            # Fallback to standard state
            standard_state = await self.get_or_create_user_state(user_id)
            return {
                "user_id": user_id,
                "current_fragment_id": standard_state.current_fragment_id,
                "completed_fragments": standard_state.completed_fragments,
                "unlocked_clues": standard_state.unlocked_clues,
                "visited_fragments": standard_state.visited_fragments,
                "enhanced": False,
                "fallback_used": True,
                "error": str(e)
            }
    
    async def advance_narrative_enhanced(self, user_id: int, fragment_id: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced narrative advancement with cinema integration.
        
        Args:
            user_id: User ID
            fragment_id: Fragment to advance to
            **kwargs: Additional parameters for cinema enhancement
            
        Returns:
            Enhanced advancement result
        """
        try:
            # Execute standard advancement
            standard_result = await self.advance_narrative(user_id, fragment_id)
            
            result = {
                "success": True,
                "user_state": standard_result,
                "enhanced": False
            }
            
            # Try cinema enhancement
            if self.cinema_master and self.cinema_master.cinema_active:
                try:
                    enhanced_result = await self.cinema_master.enhance_fragment_experience(
                        user_id, fragment_id, result
                    )
                    if enhanced_result:
                        result.update(enhanced_result)
                        result["enhanced"] = True
                except Exception as e:
                    logger.warning(f"Cinema enhancement failed for narrative advancement: {e}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in advance_narrative_enhanced for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "enhanced": False,
                "fallback_available": True
            }
    
    async def get_personalized_fragments(self, user_id: int, fragment_type: str = None) -> List[Dict[str, Any]]:
        """
        Get fragments personalized for the user's soul signature.
        
        Args:
            user_id: User ID
            fragment_type: Optional type filter
            
        Returns:
            List of personalized fragments
        """
        try:
            # Get available fragments (standard functionality)
            fragments = await self.get_available_fragments(user_id)
            
            # If no cinema enhancement, return standard fragments
            if not self.cinema_master or not self.cinema_master.is_soul_signature_available():
                return [{"fragment": f, "personalized": False} for f in fragments]
            
            # Apply soul signature personalization
            personalized_fragments = []
            soul_signature = getattr(self.cinema_master, 'soul_signature', None)
            
            for fragment in fragments:
                fragment_data = {"fragment": fragment, "personalized": False}
                
                if soul_signature and hasattr(soul_signature, 'personalize_fragment_preview'):
                    try:
                        personalization = await soul_signature.personalize_fragment_preview(
                            user_id, fragment.id, fragment_type
                        )
                        fragment_data.update({
                            "personalization": personalization,
                            "personalized": True
                        })
                    except Exception as e:
                        logger.warning(f"Fragment personalization failed for fragment {fragment.id}: {e}")
                
                personalized_fragments.append(fragment_data)
            
            return personalized_fragments
            
        except Exception as e:
            logger.exception(f"Error in get_personalized_fragments for user {user_id}: {e}")
            # Fallback to standard fragments
            fragments = await self.get_available_fragments(user_id)
            return [{"fragment": f, "personalized": False, "error": str(e)} for f in fragments]