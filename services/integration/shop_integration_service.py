"""
ShopIntegrationService - Integración del módulo de tienda con CoordinadorCentral
Conecta la tienda con gamificación, narrativa y administración de canales.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..shop_service import ShopService
    from ..point_service import PointService
    from ..achievement_service import AchievementService
    from ..subscription_service import SubscriptionService
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.shop_service import ShopService
    from services.point_service import PointService
    from services.achievement_service import AchievementService
    from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class ShopIntegrationService:
    """
    Servicio de integración para conectar la tienda con otros módulos del sistema.
    Maneja la orquestación de compras y sus efectos en gamificación y narrativa.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.shop_service = ShopService(session)
        self.point_service = PointService(session)
        self.achievement_service = AchievementService(session)
        self.subscription_service = SubscriptionService(session)
    
    async def process_item_purchase(
        self, 
        user_id: int, 
        item_id: int, 
        bot=None
    ) -> Dict[str, Any]:
        """
        Procesa una compra completa integrando todos los módulos del sistema.
        
        Args:
            user_id: ID del usuario comprando
            item_id: ID del artículo a comprar
            bot: Instancia del bot para notificaciones
            
        Returns:
            Dict con resultado de la compra y efectos en otros módulos
        """
        try:
            # 1. Verificar elegibilidad de compra
            can_purchase, error_msg = await self.shop_service.can_purchase_item(user_id, item_id)
            if not can_purchase:
                return {
                    "success": False,
                    "message": error_msg,
                    "action": "purchase_denied",
                    "reason": error_msg
                }
            
            # 2. Procesar la compra
            purchase_success, purchase_msg, purchase_data = await self.shop_service.purchase_item(
                user_id, item_id, bot
            )
            
            if not purchase_success:
                return {
                    "success": False,
                    "message": purchase_msg,
                    "action": "purchase_failed"
                }
            
            # 3. Procesar efectos secundarios de la compra
            side_effects = await self._process_purchase_side_effects(
                user_id, item_id, purchase_data, bot
            )
            
            # 4. Generar mensaje de éxito con efectos
            success_message = await self._generate_purchase_success_message(
                purchase_data, side_effects
            )
            
            return {
                "success": True,
                "message": success_message,
                "action": "purchase_completed",
                "purchase_data": purchase_data,
                "side_effects": side_effects
            }
            
        except Exception as e:
            logger.error(f"Error in integrated purchase process for user {user_id}, item {item_id}: {e}")
            return {
                "success": False,
                "message": "Error inesperado durante la compra",
                "action": "purchase_error",
                "error": str(e)
            }
    
    async def get_personalized_shop_catalog(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene el catálogo de tienda personalizado para un usuario.
        Incluye verificación VIP, descuentos aplicables y recomendaciones.
        """
        try:
            # Obtener información del usuario
            from database.models import User
            user = await self.session.get(User, user_id)
            if not user:
                return {
                    "success": False,
                    "message": "Usuario no encontrado"
                }
            
            # Verificar estatus VIP
            is_vip = await self.subscription_service.is_subscription_active(user_id)
            
            # Obtener artículos disponibles
            available_items = await self.shop_service.get_available_items(
                user_id, include_vip_only=is_vip
            )
            
            # Obtener categorías
            categories = await self.shop_service.get_categories()
            
            # Organizar artículos por categoría
            items_by_category = {}
            for item in available_items:
                category = item.category or "general"
                if category not in items_by_category:
                    items_by_category[category] = []
                
                # Calcular precio con descuentos
                final_price = await self.shop_service._calculate_final_price(user_id, item)
                discount_applied = final_price < item.price
                
                item_data = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "original_price": item.price,
                    "final_price": final_price,
                    "discount_applied": discount_applied,
                    "is_vip_exclusive": item.is_vip_exclusive,
                    "unlocks_lore": bool(item.unlocks_lore_piece_code),
                    "can_afford": user.points >= final_price,
                    "stock_available": item.stock_quantity != 0
                }
                items_by_category[category].append(item_data)
            
            return {
                "success": True,
                "user_points": int(user.points),
                "is_vip": is_vip,
                "categories": [{"name": cat.name, "emoji": cat.emoji} for cat in categories],
                "items_by_category": items_by_category,
                "total_items": len(available_items)
            }
            
        except Exception as e:
            logger.error(f"Error getting personalized shop catalog for user {user_id}: {e}")
            return {
                "success": False,
                "message": "Error cargando el catálogo de tienda"
            }
    
    async def get_user_shop_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado del usuario en la tienda.
        Incluye inventario, historial de compras y recomendaciones.
        """
        try:
            # Obtener inventario
            inventory = await self.shop_service.get_user_inventory(user_id)
            
            # Obtener historial de compras
            purchase_history = await self.shop_service.get_user_purchase_history(user_id)
            
            # Calcular estadísticas del usuario
            total_spent = sum(purchase["price_paid"] for purchase in purchase_history)
            total_items_owned = len(inventory)
            
            # Obtener recomendaciones basadas en compras previas
            recommendations = await self._get_purchase_recommendations(user_id, purchase_history)
            
            return {
                "success": True,
                "inventory_count": total_items_owned,
                "total_spent": total_spent,
                "total_purchases": len(purchase_history),
                "recent_purchases": purchase_history[:5],  # Últimas 5 compras
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting shop summary for user {user_id}: {e}")
            return {
                "success": False,
                "message": "Error cargando resumen de tienda"
            }
    
    # === MÉTODOS PRIVADOS ===
    
    async def _process_purchase_side_effects(
        self, 
        user_id: int, 
        item_id: int, 
        purchase_data: Dict[str, Any],
        bot=None
    ) -> Dict[str, Any]:
        """Procesa efectos secundarios de una compra (logros, misiones, etc.)."""
        side_effects = {
            "achievements_unlocked": [],
            "missions_completed": [],
            "level_up": False,
            "special_effects": []
        }
        
        try:
            # Verificar logros relacionados con compras
            await self._check_purchase_achievements(user_id, purchase_data, side_effects, bot)
            
            # Verificar si la compra completa alguna misión
            await self._check_purchase_missions(user_id, item_id, side_effects, bot)
            
            # Verificar subida de nivel (por puntos gastados)
            await self._check_level_progression(user_id, side_effects, bot)
            
            return side_effects
            
        except Exception as e:
            logger.error(f"Error processing purchase side effects: {e}")
            return side_effects
    
    async def _check_purchase_achievements(
        self, 
        user_id: int, 
        purchase_data: Dict[str, Any],
        side_effects: Dict[str, Any],
        bot=None
    ):
        """Verifica y otorga logros relacionados con compras."""
        try:
            # Logro de primera compra
            purchase_history = await self.shop_service.get_user_purchase_history(user_id)
            if len(purchase_history) == 1:  # Primera compra
                # Aquí se integraría con AchievementService para otorgar logro
                side_effects["achievements_unlocked"].append("first_purchase")
                
                if bot:
                    await bot.send_message(
                        user_id,
                        "🏆 ¡Logro desbloqueado: Primera Compra!\n"
                        "Has realizado tu primera compra en la tienda."
                    )
            
            # Logro de gran comprador (ejemplo: 10 compras)
            if len(purchase_history) == 10:
                side_effects["achievements_unlocked"].append("big_spender")
                
                if bot:
                    await bot.send_message(
                        user_id,
                        "🏆 ¡Logro desbloqueado: Gran Comprador!\n"
                        "Has realizado 10 compras en la tienda."
                    )
                    
        except Exception as e:
            logger.error(f"Error checking purchase achievements: {e}")
    
    async def _check_purchase_missions(
        self, 
        user_id: int, 
        item_id: int,
        side_effects: Dict[str, Any],
        bot=None
    ):
        """Verifica si la compra completa alguna misión activa."""
        try:
            from services.mission_service import MissionService
            mission_service = MissionService(self.session)
            
            # Actualizar progreso de misiones relacionadas con compras
            await mission_service.update_progress(
                user_id, 
                "shop_purchase", 
                increment=1, 
                bot=bot
            )
            
            side_effects["missions_completed"].append("shop_purchase_progress")
            
        except Exception as e:
            logger.error(f"Error checking purchase missions: {e}")
    
    async def _check_level_progression(
        self, 
        user_id: int,
        side_effects: Dict[str, Any],
        bot=None
    ):
        """Verifica si el usuario subió de nivel después de la compra."""
        try:
            from database.models import User
            from services.level_service import LevelService
            
            user = await self.session.get(User, user_id)
            if user:
                level_service = LevelService(self.session)
                level_up = await level_service.check_for_level_up(user, bot=bot)
                side_effects["level_up"] = level_up
                
        except Exception as e:
            logger.error(f"Error checking level progression: {e}")
    
    async def _get_purchase_recommendations(
        self, 
        user_id: int, 
        purchase_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Genera recomendaciones de compra basadas en historial."""
        try:
            recommendations = []
            
            # Analizar categorías compradas frecuentemente
            category_counts = {}
            for purchase in purchase_history:
                category = purchase.get("category", "general")
                category_counts[category] = category_counts.get(category, 0) + 1
            
            if category_counts:
                # Recomendar artículos de la categoría más comprada
                favorite_category = max(category_counts, key=category_counts.get)
                
                # Obtener artículos no comprados de esa categoría
                available_items = await self.shop_service.get_available_items(
                    user_id, category=favorite_category
                )
                
                # Filtrar artículos ya comprados
                purchased_item_ids = {
                    purchase.get("item_id") for purchase in purchase_history
                }
                
                for item in available_items[:3]:  # Top 3 recomendaciones
                    if item.id not in purchased_item_ids:
                        recommendations.append({
                            "item_id": item.id,
                            "name": item.name,
                            "price": item.price,
                            "reason": f"Te gusta la categoría {favorite_category}"
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating purchase recommendations: {e}")
            return []
    
    async def _generate_purchase_success_message(
        self, 
        purchase_data: Dict[str, Any],
        side_effects: Dict[str, Any]
    ) -> str:
        """Genera mensaje de éxito personalizado con efectos secundarios."""
        base_message = f"✅ **Compra Exitosa**\n\n"
        base_message += f"🛒 **Artículo**: {purchase_data['item_name']}\n"
        base_message += f"💰 **Precio**: {purchase_data['price_paid']} besitos\n"
        base_message += f"💎 **Puntos restantes**: {purchase_data['remaining_points']}\n"
        
        # Agregar efectos especiales
        if purchase_data.get("lore_unlocked"):
            base_message += f"\n🗝️ **Pista desbloqueada**: {purchase_data['lore_unlocked']}"
        
        if side_effects.get("achievements_unlocked"):
            base_message += f"\n🏆 **Logros desbloqueados**: {len(side_effects['achievements_unlocked'])}"
        
        if side_effects.get("level_up"):
            base_message += f"\n🎉 **¡Has subido de nivel!**"
        
        base_message += f"\n\n📦 El artículo ha sido agregado a tu inventario."
        
        return base_message
    
    async def get_shop_access_level(self, user_id: int) -> Dict[str, Any]:
        """
        Determina el nivel de acceso del usuario a la tienda.
        
        Returns:
            Dict con información de acceso y permisos
        """
        try:
            from database.models import User
            user = await self.session.get(User, user_id)
            if not user:
                return {
                    "access_level": "none",
                    "can_purchase": False,
                    "message": "Usuario no encontrado"
                }
            
            # Verificar estatus VIP
            is_vip = await self.subscription_service.is_subscription_active(user_id)
            
            # Determinar nivel de acceso
            if is_vip:
                access_level = "vip"
                access_message = "Acceso completo a todos los artículos VIP"
            else:
                access_level = "free"
                access_message = "Acceso a artículos gratuitos. Suscríbete para ver artículos VIP"
            
            return {
                "access_level": access_level,
                "is_vip": is_vip,
                "user_level": user.level,
                "user_points": int(user.points),
                "can_purchase": user.points > 0,
                "message": access_message
            }
            
        except Exception as e:
            logger.error(f"Error determining shop access for user {user_id}: {e}")
            return {
                "access_level": "error",
                "can_purchase": False,
                "message": "Error verificando acceso a la tienda"
            }
    
    async def process_vip_exclusive_access(self, user_id: int, item_id: int) -> Dict[str, Any]:
        """
        Procesa intento de acceso a artículo VIP exclusivo.
        Integra con el sistema de suscripciones.
        """
        try:
            # Obtener artículo
            item = await self.shop_service.get_item_by_id(item_id)
            if not item:
                return {
                    "access_granted": False,
                    "message": "Artículo no encontrado"
                }
            
            # Verificar si es VIP exclusivo
            if not item.is_vip_exclusive:
                return {
                    "access_granted": True,
                    "message": "Artículo disponible para todos los usuarios"
                }
            
            # Verificar suscripción VIP
            is_vip = await self.subscription_service.is_subscription_active(user_id)
            if not is_vip:
                return {
                    "access_granted": False,
                    "message": "Este artículo es exclusivo para miembros VIP",
                    "action_required": "vip_subscription",
                    "item_name": item.name
                }
            
            return {
                "access_granted": True,
                "message": f"Acceso VIP confirmado para {item.name}",
                "vip_discount_available": True
            }
            
        except Exception as e:
            logger.error(f"Error processing VIP access for user {user_id}, item {item_id}: {e}")
            return {
                "access_granted": False,
                "message": "Error verificando acceso VIP"
            }