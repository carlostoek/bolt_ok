from .interfaces.content_delivery_interface import IContentDeliveryService, ContentPackage, ContentType
from typing import Dict, Any, Tuple, List
from aiogram.types import InlineKeyboardMarkup
from utils.message_safety import safe_edit
from aiogram import Bot

class ContentDeliveryService(IContentDeliveryService):
    async def prepare_content(self, content_id: str, context: Dict[str, Any]) -> ContentPackage:
        # Esta es una implementación básica. En el futuro, aquí se buscaría el contenido
        # en la base de datos o en algún otro sistema de almacenamiento.
        return ContentPackage(
            content_id=content_id,
            content_type=ContentType.TEXT,
            payload=context.get("text", f"Contenido para {content_id}"),
            metadata={"reply_markup": context.get("reply_markup")},
            delivery_options={}
        )

    async def deliver_content(self, package: ContentPackage, context: Dict[str, Any]) -> bool:
        bot: Bot = context.get("bot")
        if not bot:
            return False

        if package.content_type == ContentType.TEXT:
            await safe_edit(
                message=context.get("message"),
                text=package.payload,
                reply_markup=package.metadata.get("reply_markup")
            )
            return True
        return False

    async def personalize_content(self, content: str, context: Dict[str, Any]) -> str:
        # Lógica de personalización simple.
        for key, value in context.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content

    async def validate_delivery_constraints(self, package: ContentPackage, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        # Por ahora, no hay restricciones.
        return True, []
