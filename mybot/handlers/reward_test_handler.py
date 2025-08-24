from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from services.reward_service import RewardSystem
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "/test_reward_points")
async def test_reward_points(message: Message, session: AsyncSession):
    """Comando de prueba para otorgar recompensa de puntos."""
    user_id = message.from_user.id
    
    try:
        reward_system = RewardSystem(session)
        await reward_system.grant_reward(
            user_id=user_id,
            reward_type='points',
            reward_data={
                'amount': 100,
                'description': 'Recompensa de prueba'
            },
            source='test_command'
        )
        
        await message.answer("✅ Se han otorgado 100 puntos como recompensa de prueba.")
        
    except Exception as e:
        logger.error(f"Error al otorgar recompensa de puntos: {e}")
        await message.answer("❌ Ocurrió un error al otorgar la recompensa de puntos.")


@router.message(F.text == "/test_reward_clue")
async def test_reward_clue(message: Message, session: AsyncSession):
    """Comando de prueba para otorgar recompensa de pista."""
    user_id = message.from_user.id
    
    try:
        reward_system = RewardSystem(session)
        await reward_system.grant_reward(
            user_id=user_id,
            reward_type='clue',
            reward_data={
                'clue_code': 'CLUE-001',  # Código de una pista existente para prueba
                'description': 'Pista de prueba'
            },
            source='test_command'
        )
        
        await message.answer("✅ Se ha otorgado una pista como recompensa de prueba.")
        
    except Exception as e:
        logger.error(f"Error al otorgar recompensa de pista: {e}")
        await message.answer("❌ Ocurrió un error al otorgar la recompensa de pista.")


@router.message(F.text == "/test_reward_achievement")
async def test_reward_achievement(message: Message, session: AsyncSession):
    """Comando de prueba para otorgar recompensa de logro."""
    user_id = message.from_user.id
    
    try:
        reward_system = RewardSystem(session)
        await reward_system.grant_reward(
            user_id=user_id,
            reward_type='achievement',
            reward_data={
                'achievement_id': 'ACHIEVEMENT-001',
                'description': 'Logro de prueba'
            },
            source='test_command'
        )
        
        await message.answer("✅ Se ha otorgado un logro como recompensa de prueba.")
        
    except Exception as e:
        logger.error(f"Error al otorgar recompensa de logro: {e}")
        await message.answer("❌ Ocurrió un error al otorgar la recompensa de logro.")