from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import LorePiece, UserLorePiece
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

class LorePieceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def code_exists(self, code_name: str) -> bool:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_lore_piece(
        self,
        code_name: str,
        title: str,
        content_type: str,
        content: str,
        *,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool = False,
    ) -> LorePiece:
        piece = LorePiece(
            code_name=code_name,
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            category=category,
            is_main_story=is_main_story,
        )
        self.session.add(piece)
        await self.session.commit()
        await self.session.refresh(piece)
        return piece

    async def get_lore_piece_by_code(self, code_name: str) -> LorePiece | None:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_lore_piece(
        self,
        code_name: str,
        *,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool | None = None,
        content_type: str | None = None,
        content: str | None = None,
    ) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        if title is not None:
            piece.title = title
        if description is not None:
            piece.description = description
        if category is not None:
            piece.category = category
        if is_main_story is not None:
            piece.is_main_story = is_main_story
        if content_type is not None:
            piece.content_type = content_type
        if content is not None:
            piece.content = content
        await self.session.commit()
        return True

    async def delete_lore_piece(self, code_name: str) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        await self.session.delete(piece)
        await self.session.commit()
        return True

    async def toggle_piece_status(self, code_name: str, status: bool) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if piece:
            piece.is_active = status
            await self.session.commit()
            return True
        return False

    async def unlock_lore_piece_for_user(
        self,
        user_id: int,
        lore_piece_code: str,
        context: dict | None = None,
        bot: Bot | None = None
    ) -> bool:
        """
        Canonical function to unlock a lore piece for a user.
        Replaces both desbloquear_pista and desbloquear_pista_narrativa.
        
        Args:
            user_id: The user's ID
            lore_piece_code: The code name of the lore piece to unlock
            context: Optional context data about how the piece was unlocked
            bot: Optional bot instance to send notifications
            
        Returns:
            bool: True if the piece was unlocked, False if it was already owned or not found
        """
        # Find the lore piece
        lore_piece = await self.get_lore_piece_by_code(lore_piece_code)
        if not lore_piece:
            logger.warning(f"Lore piece with code '{lore_piece_code}' not found")
            return False
        
        # Check if user already has this piece
        existing_stmt = select(UserLorePiece).where(
            and_(
                UserLorePiece.user_id == user_id,
                UserLorePiece.lore_piece_id == lore_piece.id
            )
        )
        existing_result = await self.session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            logger.info(f"User {user_id} already has lore piece '{lore_piece_code}'")
            return False
        
        # Create the user lore piece record
        user_lore_piece = UserLorePiece(
            user_id=user_id,
            lore_piece_id=lore_piece.id,
            context=context or {}
        )
        self.session.add(user_lore_piece)
        await self.session.commit()
        
        # Send notification if bot is provided
        if bot:
            await self._send_lore_piece_notification(bot, user_id, lore_piece)
        
        logger.info(f"Successfully unlocked lore piece '{lore_piece_code}' for user {user_id}")
        return True

    async def _send_lore_piece_notification(self, bot: Bot, user_id: int, lore_piece: LorePiece):
        """Send the lore piece content to the user."""
        try:
            if lore_piece.content_type == "image":
                await bot.send_photo(
                    user_id, 
                    lore_piece.content, 
                    caption=f"📖 {lore_piece.title}"
                )
            elif lore_piece.content_type == "video":
                await bot.send_video(
                    user_id, 
                    lore_piece.content, 
                    caption=f"📖 {lore_piece.title}"
                )
            elif lore_piece.content_type == "audio":
                await bot.send_audio(
                    user_id, 
                    lore_piece.content, 
                    caption=f"📖 {lore_piece.title}"
                )
            else:
                await bot.send_message(
                    user_id, 
                    f"📖 {lore_piece.title}\n\n{lore_piece.content}"
                )
        except Exception as e:
            logger.error(f"Error sending lore piece notification to user {user_id}: {e}")
