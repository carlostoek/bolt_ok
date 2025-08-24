"""
Servicio de narrativa unificada para DianaBot.
Maneja la lógica de fragmentos narrativos unificados, decisiones y progresión de historia.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import User
from database.narrative_models import UserNarrativeState, StoryFragment, NarrativeChoice
from database.narrative_unified import NarrativeFragment as UnifiedNarrativeFragment
from services.narrative_fragment_service import NarrativeFragmentService
from services.point_service import PointService
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedNarrativeService:
    """Servicio principal del sistema narrativo unificado."""
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        self.point_service = PointService(session) if session else None
        self.fragment_service = NarrativeFragmentService(session)
    
    async def get_user_current_fragment(self, user_id: int) -> Optional[UnifiedNarrativeFragment]:
        """Obtiene el fragmento actual del usuario."""
        # Obtener o crear estado narrativo del usuario
        user_state = await self._get_or_create_user_state(user_id)
        
        if not user_state.current_fragment_key:
            # Iniciar narrativa desde el fragmento inicial
            start_fragment = await self._get_unified_fragment_by_id("start")
            if start_fragment:
                user_state.current_fragment_key = start_fragment.id
                await self.session.commit()
                return start_fragment
            else:
                logger.error("No se encontró fragmento inicial 'start'")
                return None
        
        # Obtener fragmento actual
        fragment = await self._get_unified_fragment_by_id(user_state.current_fragment_key)
        return fragment
    
    async def start_narrative(self, user_id: int) -> Optional[UnifiedNarrativeFragment]:
        """Inicia la narrativa para un usuario nuevo."""
        user_state = await self._get_or_create_user_state(user_id)
        
        # Buscar fragmento inicial
        start_fragment = await self._get_unified_fragment_by_id("start")
        if not start_fragment:
            logger.error("No se encontró fragmento inicial 'start'")
            return None
        
        # Verificar condiciones de acceso
        if not await self._check_access_conditions(user_id, start_fragment):
            return None
        
        # Configurar estado inicial
        user_state.current_fragment_key = start_fragment.id
        user_state.choices_made = []
        user_state.narrative_started_at = datetime.utcnow()
        
        # Procesar recompensas del fragmento inicial
        await self._process_fragment_rewards(user_id, start_fragment)
        
        await self.session.commit()
        
        logger.info(f"Narrativa unificada iniciada para usuario {user_id}")
        return start_fragment
    
    async def process_user_decision(
        self, 
        user_id: int, 
        choice_data: Dict[str, Any]
    ) -> Optional[UnifiedNarrativeFragment]:
        """Procesa una decisión del usuario y avanza la narrativa."""
        current_fragment = await self.get_user_current_fragment(user_id)
        if not current_fragment:
            return None
        
        # Verificar que el fragmento sea de tipo DECISION
        if not current_fragment.is_decision:
            logger.warning(f"Fragmento {current_fragment.id} no es de tipo DECISION")
            return None
        
        # Buscar la opción seleccionada en las choices del fragmento
        choice_index = choice_data.get("index")
        if choice_index is None or choice_index < 0 or choice_index >= len(current_fragment.choices):
            logger.warning(f"Índice de decisión inválido: {choice_index} para fragmento {current_fragment.id}")
            return None
        
        selected_choice = current_fragment.choices[choice_index]
        
        # Buscar el fragmento de destino
        next_fragment_id = selected_choice.get("next_fragment_id")
        if not next_fragment_id:
            logger.error(f"Fragmento de destino no especificado en choice: {selected_choice}")
            return None
            
        next_fragment = await self._get_unified_fragment_by_id(next_fragment_id)
        if not next_fragment:
            logger.error(f"Fragmento de destino no encontrado: {next_fragment_id}")
            return None
        
        # Verificar condiciones de acceso
        if not await self._check_access_conditions(user_id, next_fragment):
            logger.info(f"Usuario {user_id} no cumple condiciones para fragmento {next_fragment.id}")
            return None
        
        # Registrar la decisión
        user_state = await self._get_or_create_user_state(user_id)
        if not user_state.choices_made:
            user_state.choices_made = []
        
        user_state.choices_made.append({
            "fragment_id": current_fragment.id,
            "choice_index": choice_index,
            "choice_text": selected_choice.get("text", "Opción desconocida"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Avanzar al siguiente fragmento
        user_state.current_fragment_key = next_fragment.id
        user_state.fragments_visited += 1
        user_state.last_activity_at = datetime.utcnow()
        
        # Procesar triggers del fragmento
        await self._process_fragment_triggers(user_id, next_fragment)
        
        await self.session.commit()
        
        logger.info(f"Usuario {user_id} avanzó de {current_fragment.id} a {next_fragment.id}")
        return next_fragment
    
    async def get_user_narrative_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas narrativas del usuario."""
        user_state = await self._get_or_create_user_state(user_id)
        
        # Obtener fragmento actual
        current_fragment_id = None
        if user_state.current_fragment_key:
            current_fragment = await self._get_unified_fragment_by_id(user_state.current_fragment_key)
            current_fragment_id = current_fragment.id if current_fragment else None
        
        # Calcular progreso aproximado
        total_fragments = await self._count_accessible_fragments(user_id)
        progress_percentage = (user_state.fragments_visited / max(total_fragments, 1)) * 100
        
        return {
            "current_fragment": current_fragment_id,
            "fragments_visited": user_state.fragments_visited,
            "total_accessible": total_fragments,
            "progress_percentage": min(progress_percentage, 100),
            "choices_made": user_state.choices_made or []
        }
    
    async def _get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo del usuario."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_key=None,
                choices_made=[],
                fragments_visited=0
            )
            self.session.add(user_state)
            await self.session.commit()
            await self.session.refresh(user_state)
        
        return user_state
    
    async def _get_unified_fragment_by_id(self, fragment_id: str) -> Optional[UnifiedNarrativeFragment]:
        """Obtiene un fragmento unificado por su ID."""
        return await self.fragment_service.get_fragment(fragment_id)
    
    async def _check_access_conditions(self, user_id: int, fragment: UnifiedNarrativeFragment) -> bool:
        """Verifica si el usuario puede acceder a un fragmento."""
        if not fragment:
            return False
        
        # Verificar pistas requeridas
        if fragment.required_clues:
            # En una implementación completa, verificaríamos si el usuario tiene las pistas
            # Por ahora, solo verificamos que existan
            pass
        
        # Verificar rol requerido (si se implementa en el futuro)
        # Esto sería similar a la implementación en NarrativeEngine
        
        return True
    
    async def _process_fragment_triggers(self, user_id: int, fragment: UnifiedNarrativeFragment):
        """Procesa los triggers de un fragmento."""
        if not fragment.triggers:
            return
            
        # Procesar recompensas de puntos usando el sistema unificado
        reward_points = fragment.triggers.get("reward_points", 0)
        if reward_points > 0:
            try:
                from services.reward_service import RewardSystem
                reward_system = RewardSystem(self.session)
                await reward_system.grant_reward(
                    user_id=user_id,
                    reward_type='points',
                    reward_data={
                        'amount': reward_points,
                        'description': f'Recompensa por fragmento: {fragment.title}'
                    },
                    source='unified_narrative_fragment'
                )
                logger.info(f"Usuario {user_id} recibió {reward_points} puntos del fragmento {fragment.id}")
            except Exception as e:
                logger.error(f"Error al otorgar puntos al usuario {user_id}: {e}")
        
        # Procesar desbloqueo de pistas usando el sistema unificado
        unlock_lore = fragment.triggers.get("unlock_lore")
        if unlock_lore:
            try:
                from services.reward_service import RewardSystem
                reward_system = RewardSystem(self.session)
                await reward_system.grant_reward(
                    user_id=user_id,
                    reward_type='clue',
                    reward_data={
                        'clue_code': unlock_lore,
                        'description': f'Pista desbloqueada por fragmento: {fragment.title}'
                    },
                    source='unified_narrative_fragment'
                )
                logger.info(f"Fragmento {fragment.id} desbloquea pista: {unlock_lore}")
            except Exception as e:
                logger.error(f"Error al desbloquear pista {unlock_lore} para usuario {user_id}: {e}")
    
    async def _count_accessible_fragments(self, user_id: int) -> int:
        """Cuenta los fragmentos accesibles para el usuario."""
        # En una implementación completa, esto filtraría según las condiciones del usuario
        # Por ahora, simplemente contamos todos los fragmentos activos
        stmt = select(UnifiedNarrativeFragment).where(
            UnifiedNarrativeFragment.is_active == True
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())