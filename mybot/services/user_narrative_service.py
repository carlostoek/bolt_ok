from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.narrative_unified import UserNarrativeState, NarrativeFragment
from database.models import User, LorePiece
from services.reward_service import RewardSystem
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


class UserNarrativeService:
    """Servicio para gestionar el estado narrativo unificado de los usuarios."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.reward_system = RewardSystem(session)

    async def get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserNarrativeState: Estado narrativo del usuario
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