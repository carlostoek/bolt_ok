"""
Content Service - Gestión de sets de contenido multimedia

Maneja la creación, envío y tracking de sets de fotos/videos/audios
para el journey del usuario.
"""
import logging
import json
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, InputMediaAudio

from database.models import ContentSet, GiftRecord, User

logger = logging.getLogger(__name__)


class ContentService:
    """Servicio para gestionar sets de contenido"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_content_set(
        self,
        id: str,
        name: str,
        type: str,
        tier: str,
        file_ids: list,
        description: str = None,
        category: str = None,
        for_archetype: str = "all"
    ) -> ContentSet:
        """
        Crea un nuevo content set

        Args:
            id: ID único (ej: "primera_mirada")
            name: Nombre display (ej: "Primera Mirada")
            type: "photo_set", "video", "audio", "mixed"
            tier: "free", "vip", "gift", "premium"
            file_ids: Lista de Telegram file_ids
            description: Descripción interna
            category: "teaser", "welcome", "milestone", "surprise"
            for_archetype: "luz", "sombra", "all"
        """
        content_set = ContentSet(
            id=id,
            name=name,
            type=type,
            tier=tier,
            file_ids=file_ids,
            description=description,
            category=category,
            for_archetype=for_archetype,
            is_active=True
        )

        self.session.add(content_set)
        await self.session.commit()
        await self.session.refresh(content_set)

        logger.info(f"Content set creado: {id} ({name})")
        return content_set

    async def get_content_set(self, set_id: str) -> Optional[ContentSet]:
        """Obtiene un content set por ID"""
        stmt = select(ContentSet).where(ContentSet.id == set_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_content_sets(
        self,
        tier: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[ContentSet]:
        """
        Lista content sets con filtros opcionales

        Args:
            tier: Filtrar por tier (free, vip, gift, premium)
            category: Filtrar por categoría
            active_only: Solo sets activos
        """
        stmt = select(ContentSet)

        if tier:
            stmt = stmt.where(ContentSet.tier == tier)
        if category:
            stmt = stmt.where(ContentSet.category == category)
        if active_only:
            stmt = stmt.where(ContentSet.is_active == True)

        stmt = stmt.order_by(ContentSet.created_at.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def send_content_set(
        self,
        user_id: int,
        set_id: str,
        context_message: str = "",
        bot: Bot = None,
        trigger_type: str = "manual",
        sent_by_admin: bool = False
    ) -> bool:
        """
        Envía un content set a un usuario

        Args:
            user_id: ID del usuario
            set_id: ID del content set
            context_message: Mensaje narrativo ANTES del contenido
            bot: Instancia del bot
            trigger_type: "manual", "automatic", "milestone", "achievement"
            sent_by_admin: Si fue enviado manualmente por admin

        Returns:
            True si se envió correctamente, False si hubo error
        """
        if not bot:
            logger.error("Bot instance requerida para enviar contenido")
            return False

        # Obtener content set
        content_set = await self.get_content_set(set_id)
        if not content_set:
            logger.error(f"Content set no encontrado: {set_id}")
            return False

        if not content_set.is_active:
            logger.warning(f"Content set inactivo: {set_id}")
            return False

        try:
            # Enviar mensaje de contexto primero
            if context_message:
                await bot.send_message(user_id, context_message)

            # Obtener file_ids
            file_ids = content_set.file_ids
            if isinstance(file_ids, str):
                file_ids = json.loads(file_ids)

            if not file_ids:
                logger.warning(f"Content set {set_id} no tiene archivos")
                return False

            # Enviar contenido según tipo
            if content_set.type == "photo_set":
                # Enviar fotos
                for file_id in file_ids:
                    await bot.send_photo(user_id, file_id)

            elif content_set.type == "video":
                # Enviar video
                await bot.send_video(user_id, file_ids[0])

            elif content_set.type == "audio":
                # Enviar audio
                await bot.send_audio(user_id, file_ids[0])

            elif content_set.type == "mixed":
                # Enviar todos en orden (asumiendo formato específico)
                for file_id in file_ids:
                    # Intentar detectar tipo por file_id (esto es simplificado)
                    # En producción, guardar metadata de cada archivo
                    try:
                        await bot.send_photo(user_id, file_id)
                    except:
                        try:
                            await bot.send_video(user_id, file_id)
                        except:
                            await bot.send_document(user_id, file_id)

            # Registrar gift en BD
            gift_record = GiftRecord(
                user_id=user_id,
                content_set_id=set_id,
                context=f"{trigger_type}",
                trigger_type=trigger_type,
                sent_by_admin=sent_by_admin
            )
            self.session.add(gift_record)
            await self.session.commit()

            logger.info(f"Content set {set_id} enviado a usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error enviando content set {set_id} a usuario {user_id}: {e}")
            return False

    async def update_content_set(self, set_id: str, **kwargs) -> bool:
        """
        Actualiza un content set

        Args:
            set_id: ID del set
            **kwargs: Campos a actualizar (name, description, file_ids, etc)
        """
        stmt = (
            update(ContentSet)
            .where(ContentSet.id == set_id)
            .values(**kwargs)
        )

        await self.session.execute(stmt)
        await self.session.commit()

        logger.info(f"Content set actualizado: {set_id}")
        return True

    async def delete_content_set(self, set_id: str, soft_delete: bool = True) -> bool:
        """
        Elimina un content set

        Args:
            set_id: ID del set
            soft_delete: Si True, marca como inactivo. Si False, borra de BD
        """
        if soft_delete:
            await self.update_content_set(set_id, is_active=False)
            logger.info(f"Content set desactivado: {set_id}")
        else:
            stmt = delete(ContentSet).where(ContentSet.id == set_id)
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info(f"Content set eliminado: {set_id}")

        return True

    async def get_user_received_gifts(self, user_id: int) -> List[GiftRecord]:
        """Obtiene todos los regalos recibidos por un usuario"""
        stmt = (
            select(GiftRecord)
            .where(GiftRecord.user_id == user_id)
            .order_by(GiftRecord.sent_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def has_received_set(self, user_id: int, set_id: str) -> bool:
        """Verifica si un usuario ya recibió un set específico"""
        stmt = select(GiftRecord).where(
            GiftRecord.user_id == user_id,
            GiftRecord.content_set_id == set_id
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
