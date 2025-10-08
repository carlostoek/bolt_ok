from aiogram import Bot
from services.lore_piece_service import LorePieceService
from database.setup import get_session_factory

async def desbloquear_pista(bot: Bot, user_id: int, pista_code: str):
    """Legacy function - now uses the canonical service method."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = LorePieceService(session)
        await service.unlock_lore_piece_for_user(
            user_id=user_id,
            lore_piece_code=pista_code,
            context={"source": "legacy_desbloquear_pista"},
            bot=bot
        )
