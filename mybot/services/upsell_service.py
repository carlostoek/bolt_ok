"""
Upsell Service - Lógica de venta inteligente post-compra

Determina qué ofrecer al usuario después de una compra exitosa,
basándose en:
- Tipo de item comprado
- Rol del usuario (VIP/Free)
- Comportamiento reciente
- Días de actividad
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, UserPurchase, ShopItem

logger = logging.getLogger(__name__)


class UpsellService:
    """Servicio para determinar upsells inteligentes post-compra"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_smart_upsell(
        self,
        user_id: int,
        purchased_item: ShopItem
    ) -> Dict[str, any]:
        """
        Determina el mejor upsell para mostrar después de una compra

        Args:
            user_id: ID del usuario
            purchased_item: Item que acaba de comprar

        Returns:
            Dict con:
            - type: Tipo de upsell ("premium_pack", "vip_upgrade", "session_offer", "besitos_reload", None)
            - message_key: Key del mensaje en BOT_MESSAGES
            - data: Datos adicionales para el mensaje
            - keyboard_type: Tipo de keyboard a usar
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return self._get_default_upsell()

            # CASO 1: VIP que compró item narrativo → Ofrecer pack premium
            if user.role == "vip" and purchased_item.item_type == "narrative":
                return await self._upsell_premium_pack(user)

            # CASO 2: VIP activo >30 días → Ofrecer sesión individual
            if user.role == "vip":
                days_vip = await self._get_days_as_vip(user)
                if days_vip >= 30:
                    return await self._upsell_session_loyal_vip(user, days_vip)

            # CASO 3: FREE con >500 besitos → Oferta VIP
            if user.role == "free" and user.points >= 500:
                return await self._upsell_vip_upgrade(user)

            # CASO 4: Usuario muy activo (3+ compras hoy) → Recarga con bonus
            recent_purchases = await self._count_recent_purchases(user_id, hours=24)
            if recent_purchases >= 3:
                return await self._upsell_besitos_reload(user, recent_purchases)

            # CASO DEFAULT: Opciones estándar sin upsell específico
            return self._get_default_upsell()

        except Exception as e:
            logger.error(f"Error getting smart upsell for user {user_id}: {e}")
            return self._get_default_upsell()

    async def _upsell_premium_pack(self, user: User) -> Dict:
        """VIP que compró item narrativo → Pack premium fotográfico"""
        return {
            "type": "premium_pack",
            "message_key": "upsell_premium_pack_vip",
            "data": {"pack_id": 2},  # Pack Sensualidad Revelada
            "keyboard_type": "premium_pack",
            "keyboard_data": {"pack_id": 2}
        }

    async def _upsell_session_loyal_vip(self, user: User, days_vip: int) -> Dict:
        """VIP leal (30+ días) → Sesión individual con descuento"""
        return {
            "type": "session_offer",
            "message_key": "upsell_session_loyal_vip",
            "data": {
                "username": user.username or user.first_name,
                "days_vip": days_vip
            },
            "keyboard_type": "session_offer",
            "keyboard_data": {"session_type": "vip_special"}
        }

    async def _upsell_vip_upgrade(self, user: User) -> Dict:
        """FREE con muchos besitos → Upgrade a VIP"""
        return {
            "type": "vip_upgrade",
            "message_key": "upsell_vip_upgrade_free",
            "data": {"points": int(user.points)},
            "keyboard_type": "vip_upgrade",
            "keyboard_data": {}
        }

    async def _upsell_besitos_reload(self, user: User, purchases_count: int) -> Dict:
        """Usuario muy activo → Recarga con bonus"""
        return {
            "type": "besitos_reload",
            "message_key": "upsell_besitos_reload_active",
            "data": {"purchases_count": purchases_count},
            "keyboard_type": "besitos_reload",
            "keyboard_data": {}
        }

    def _get_default_upsell(self) -> Dict:
        """Upsell por defecto: continuar narrativa o tienda"""
        return {
            "type": None,
            "message_key": None,
            "data": {},
            "keyboard_type": "default",
            "keyboard_data": {}
        }

    async def _get_days_as_vip(self, user: User) -> int:
        """Calcula días que el usuario ha sido VIP"""
        if not user.vip_since:
            return 0
        return (datetime.utcnow() - user.vip_since).days

    async def _count_recent_purchases(self, user_id: int, hours: int = 24) -> int:
        """Cuenta compras recientes del usuario"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            stmt = select(func.count(UserPurchase.id)).where(
                UserPurchase.user_id == user_id,
                UserPurchase.purchased_at >= cutoff
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting recent purchases: {e}")
            return 0

    async def should_show_session_upsell(self, user_id: int) -> bool:
        """
        Verifica si es momento apropiado para ofrecer sesión individual

        Condiciones:
        - Usuario es VIP
        - No se le ofreció sesión en últimos 7 días
        - Ha sido activo recientemente
        """
        try:
            user = await self.session.get(User, user_id)
            if not user or user.role != "vip":
                return False

            # Verificar cooldown (7 días desde última oferta)
            if hasattr(user, 'last_session_offer_at') and user.last_session_offer_at:
                days_since_offer = (datetime.utcnow() - user.last_session_offer_at).days
                if days_since_offer < 7:
                    return False

            # Verificar que sea VIP activo por al menos 30 días
            days_vip = await self._get_days_as_vip(user)
            if days_vip < 30:
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking session upsell eligibility: {e}")
            return False
