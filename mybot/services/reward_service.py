from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, LorePiece, UserLorePiece
from database.transaction_models import RewardLog
from services.point_service import PointService
import logging

logger = logging.getLogger(__name__)


class RewardSystem:
    """
    Sistema centralizado para manejar todas las recompensas
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def grant_reward(self, user_id: int, reward_type: str, reward_data: dict, source: str = None):
        """
        Otorga recompensas de manera unificada
        
        Args:
            user_id (int): ID del usuario
            reward_type (str): Tipo de recompensa ('points', 'clue', 'achievement')
            reward_data (dict): Datos específicos de la recompensa
            source (str): Origen de la recompensa (opcional)
        """
        try:
            # Verificar que el usuario exista
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"Usuario con ID {user_id} no encontrado")
            
            if reward_type == 'points':
                await self._grant_points_reward(user, reward_data, source)
                
            elif reward_type == 'clue':
                await self._grant_clue_reward(user, reward_data, source)
                
            elif reward_type == 'achievement':
                await self._grant_achievement_reward(user, reward_data, source)
            
            # Registrar en log de recompensas
            reward_log = RewardLog(
                user_id=user_id,
                reward_type=reward_type,
                reward_data=reward_data,
                source=source or 'system'
            )
            self.session.add(reward_log)
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error al otorgar recompensa: {e}")
            raise

    async def _grant_points_reward(self, user: User, reward_data: dict, source: str = None):
        """
        Otorga recompensa de puntos
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str): Origen de la recompensa
        """
        amount = reward_data.get('amount', 0)
        if amount > 0:
            point_service = PointService(self.session)
            await point_service.add_points(
                user_id=user.id,
                points=amount,
                source=source or 'reward',
                description=reward_data.get('description', 'Recompensa otorgada')
            )

    async def _grant_clue_reward(self, user: User, reward_data: dict, source: str = None):
        """
        Otorga recompensa de pista
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str): Origen de la recompensa
        """
        clue_code = reward_data.get('clue_code') or reward_data.get('code_name')
        if clue_code:
            # Buscar la pista por su código
            clue_stmt = select(LorePiece).where(
                LorePiece.code_name == clue_code,
                LorePiece.is_active == True
            )
            clue_result = await self.session.execute(clue_stmt)
            clue = clue_result.scalar_one_or_none()
            
            if clue:
                # Verificar si el usuario ya tiene desbloqueada esta pista
                user_clue_stmt = select(UserLorePiece).where(
                    UserLorePiece.user_id == user.id,
                    UserLorePiece.lore_piece_id == clue.id
                )
                user_clue_result = await self.session.execute(user_clue_stmt)
                user_clue = user_clue_result.scalar_one_or_none()
                
                # Si no la tiene, añadirla
                if not user_clue:
                    user_lore_piece = UserLorePiece(
                        user_id=user.id,
                        lore_piece_id=clue.id
                    )
                    self.session.add(user_lore_piece)
                    await self.session.commit()
            else:
                logger.warning(f"Pista con código {clue_code} no encontrada o inactiva")

    async def _grant_achievement_reward(self, user: User, reward_data: dict, source: str = None):
        """
        Otorga recompensa de logro
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str): Origen de la recompensa
        """
        achievement_id = reward_data.get('achievement_id')
        if achievement_id:
            # Asegurarse de que achievements sea un dict
            if not isinstance(user.achievements, dict):
                user.achievements = {}
            
            # Añadir el logro si no lo tiene
            if achievement_id not in user.achievements:
                user.achievements[achievement_id] = {
                    "unlocked_at": reward_data.get('unlocked_at', ''),
                    "context": reward_data.get('context', {})
                }
                await self.session.commit()