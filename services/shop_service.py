"""
ShopService - Servicio principal del sistema de tienda
Maneja la lógica de negocio para artículos, compras e inventario.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime

from database.shop_models import ShopItem, UserPurchase, UserInventory, ShopCategory, ShopDiscount
from database.models import User
from services.point_service import PointService
from services.subscription_service import SubscriptionService
from services.lore_piece_service import LorePieceService
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)

class ShopService:
    """Servicio principal para gestión de tienda."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
        self.subscription_service = SubscriptionService(session)
        self.lore_service = LorePieceService(session)
    
    # === GESTIÓN DE ARTÍCULOS ===
    
    async def get_available_items(
        self, 
        user_id: int, 
        category: Optional[str] = None,
        include_vip_only: bool = True
    ) -> List[ShopItem]:
        """
        Obtiene artículos disponibles para un usuario específico.
        Filtra por acceso VIP y nivel del usuario.
        """
        try:
            # Verificar si el usuario es VIP
            is_vip = await self.subscription_service.is_subscription_active(user_id)
            
            # Obtener nivel del usuario
            user = await self.session.get(User, user_id)
            user_level = user.level if user else 1
            
            # Construir query base
            stmt = select(ShopItem).where(
                ShopItem.is_active == True,
                ShopItem.required_level <= user_level
            )
            
            # Filtrar por categoría si se especifica
            if category:
                stmt = stmt.where(ShopItem.category == category)
            
            # Filtrar artículos VIP si el usuario no es VIP
            if not is_vip and not include_vip_only:
                stmt = stmt.where(ShopItem.is_vip_exclusive == False)
            
            # Filtrar artículos sin stock
            stmt = stmt.where(
                (ShopItem.stock_quantity > 0) | (ShopItem.stock_quantity == -1)
            )
            
            stmt = stmt.order_by(ShopItem.category, ShopItem.price)
            
            result = await self.session.execute(stmt)
            items = result.scalars().all()
            
            logger.info(f"Retrieved {len(items)} available items for user {user_id}")
            return items
            
        except Exception as e:
            logger.error(f"Error getting available items for user {user_id}: {e}")
            return []
    
    async def get_item_by_id(self, item_id: int) -> Optional[ShopItem]:
        """Obtiene un artículo específico por ID."""
        return await self.session.get(ShopItem, item_id)
    
    async def create_item(
        self,
        name: str,
        description: str,
        price: int,
        category: Optional[str] = None,
        is_vip_exclusive: bool = False,
        required_level: int = 1,
        unlocks_lore_piece_code: Optional[str] = None,
        image_url: Optional[str] = None,
        stock_quantity: int = -1
    ) -> ShopItem:
        """Crear un nuevo artículo en la tienda (solo admins)."""
        try:
            item = ShopItem(
                name=sanitize_text(name),
                description=sanitize_text(description),
                price=price,
                category=category,
                is_vip_exclusive=is_vip_exclusive,
                required_level=required_level,
                unlocks_lore_piece_code=unlocks_lore_piece_code,
                image_url=image_url,
                stock_quantity=stock_quantity
            )
            
            self.session.add(item)
            await self.session.commit()
            await self.session.refresh(item)
            
            logger.info(f"Created shop item: {name} (ID: {item.id})")
            return item
            
        except Exception as e:
            logger.error(f"Error creating shop item: {e}")
            await self.session.rollback()
            raise
    
    # === GESTIÓN DE COMPRAS ===
    
    async def can_purchase_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
        """
        Verifica si un usuario puede comprar un artículo específico.
        
        Returns:
            Tuple[bool, str]: (puede_comprar, mensaje_error)
        """
        try:
            # Obtener artículo
            item = await self.get_item_by_id(item_id)
            if not item or not item.is_active:
                return False, "Artículo no disponible"
            
            # Verificar stock
            if item.stock_quantity == 0:
                return False, "Artículo agotado"
            
            # Obtener usuario
            user = await self.session.get(User, user_id)
            if not user:
                return False, "Usuario no encontrado"
            
            # Verificar nivel requerido
            if user.level < item.required_level:
                return False, f"Requiere nivel {item.required_level} (tienes nivel {user.level})"
            
            # Verificar acceso VIP
            if item.is_vip_exclusive:
                is_vip = await self.subscription_service.is_subscription_active(user_id)
                if not is_vip:
                    return False, "Este artículo es exclusivo para miembros VIP"
            
            # Verificar si ya fue comprado (para artículos únicos)
            existing_purchase = await self._get_user_purchase(user_id, item_id)
            if existing_purchase:
                return False, "Ya has comprado este artículo"
            
            # Calcular precio final (con descuentos)
            final_price = await self._calculate_final_price(user_id, item)
            
            # Verificar puntos suficientes
            if user.points < final_price:
                return False, f"Puntos insuficientes. Necesitas {final_price}, tienes {int(user.points)}"
            
            return True, "Compra permitida"
            
        except Exception as e:
            logger.error(f"Error checking purchase eligibility for user {user_id}, item {item_id}: {e}")
            return False, "Error verificando elegibilidad de compra"
    
    async def purchase_item(self, user_id: int, item_id: int, bot=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Procesa la compra de un artículo.
        
        Returns:
            Tuple[bool, str, Optional[Dict]]: (éxito, mensaje, datos_adicionales)
        """
        try:
            # Verificar elegibilidad
            can_purchase, error_msg = await self.can_purchase_item(user_id, item_id)
            if not can_purchase:
                return False, error_msg, None
            
            # Obtener datos necesarios
            item = await self.get_item_by_id(item_id)
            user = await self.session.get(User, user_id)
            final_price = await self._calculate_final_price(user_id, item)
            
            # Iniciar transacción atómica
            async with self.session.begin():
                # 1. Descontar puntos
                success = await self.point_service.deduct_points(user_id, final_price)
                if not success:
                    await self.session.rollback()
                    return False, "Error al descontar puntos", None
                
                # 2. Registrar compra
                purchase = UserPurchase(
                    user_id=user_id,
                    item_id=item_id,
                    price_paid=final_price,
                    quantity=1
                )
                self.session.add(purchase)
                
                # 3. Agregar al inventario
                await self._add_to_inventory(user_id, item_id, 1)
                
                # 4. Actualizar stock si es limitado
                if item.stock_quantity > 0:
                    item.stock_quantity -= 1
                
                # 5. Desbloquear pista narrativa si aplica
                lore_unlocked = None
                if item.unlocks_lore_piece_code:
                    lore_unlocked = await self._unlock_narrative_lore(
                        user_id, item.unlocks_lore_piece_code, bot
                    )
                
                await self.session.commit()
            
            # Datos adicionales para respuesta
            purchase_data = {
                "item_name": item.name,
                "price_paid": final_price,
                "lore_unlocked": lore_unlocked,
                "remaining_points": user.points - final_price
            }
            
            logger.info(f"User {user_id} purchased item {item.name} for {final_price} points")
            return True, f"¡Compra exitosa! Has adquirido {item.name}", purchase_data
            
        except Exception as e:
            logger.error(f"Error processing purchase for user {user_id}, item {item_id}: {e}")
            await self.session.rollback()
            return False, "Error procesando la compra", None
    
    # === GESTIÓN DE INVENTARIO ===
    
    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene el inventario completo de un usuario."""
        try:
            stmt = select(UserInventory, ShopItem).join(
                ShopItem, UserInventory.item_id == ShopItem.id
            ).where(UserInventory.user_id == user_id).order_by(ShopItem.category, ShopItem.name)
            
            result = await self.session.execute(stmt)
            inventory_data = result.all()
            
            inventory = []
            for inv_entry, item in inventory_data:
                inventory.append({
                    "item_id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "category": item.category,
                    "quantity": inv_entry.quantity,
                    "acquired_at": inv_entry.acquired_at,
                    "is_used": inv_entry.is_used,
                    "unlocks_lore": bool(item.unlocks_lore_piece_code)
                })
            
            return inventory
            
        except Exception as e:
            logger.error(f"Error getting inventory for user {user_id}: {e}")
            return []
    
    async def use_inventory_item(self, user_id: int, item_id: int) -> Tuple[bool, str]:
        """
        Usar un artículo del inventario (para artículos consumibles).
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Verificar que el usuario tiene el artículo
            stmt = select(UserInventory).where(
                and_(
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id,
                    UserInventory.quantity > 0
                )
            )
            result = await self.session.execute(stmt)
            inventory_entry = result.scalar_one_or_none()
            
            if not inventory_entry:
                return False, "No tienes este artículo en tu inventario"
            
            # Obtener información del artículo
            item = await self.get_item_by_id(item_id)
            if not item:
                return False, "Artículo no encontrado"
            
            # Marcar como usado y actualizar cantidad
            inventory_entry.is_used = True
            inventory_entry.last_used_at = datetime.utcnow()
            inventory_entry.quantity -= 1
            
            # Si la cantidad llega a 0, eliminar del inventario
            if inventory_entry.quantity <= 0:
                await self.session.delete(inventory_entry)
            
            await self.session.commit()
            
            logger.info(f"User {user_id} used item {item.name}")
            return True, f"Has usado {item.name}"
            
        except Exception as e:
            logger.error(f"Error using inventory item for user {user_id}, item {item_id}: {e}")
            await self.session.rollback()
            return False, "Error usando el artículo"
    
    # === GESTIÓN DE CATEGORÍAS ===
    
    async def get_categories(self) -> List[ShopCategory]:
        """Obtiene todas las categorías activas."""
        try:
            stmt = select(ShopCategory).where(
                ShopCategory.is_active == True
            ).order_by(ShopCategory.display_order, ShopCategory.name)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting shop categories: {e}")
            return []
    
    async def create_category(
        self, 
        name: str, 
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        display_order: int = 0
    ) -> ShopCategory:
        """Crear una nueva categoría (solo admins)."""
        try:
            category = ShopCategory(
                name=sanitize_text(name),
                description=sanitize_text(description),
                emoji=emoji,
                display_order=display_order
            )
            
            self.session.add(category)
            await self.session.commit()
            await self.session.refresh(category)
            
            logger.info(f"Created shop category: {name}")
            return category
            
        except Exception as e:
            logger.error(f"Error creating shop category: {e}")
            await self.session.rollback()
            raise
    
    # === GESTIÓN DE DESCUENTOS ===
    
    async def get_applicable_discounts(self, user_id: int, item: ShopItem) -> List[ShopDiscount]:
        """Obtiene descuentos aplicables para un usuario y artículo."""
        try:
            now = datetime.utcnow()
            is_vip = await self.subscription_service.is_subscription_active(user_id)
            
            stmt = select(ShopDiscount).where(
                ShopDiscount.is_active == True,
                ShopDiscount.starts_at <= now,
                (ShopDiscount.expires_at.is_(None)) | (ShopDiscount.expires_at > now)
            )
            
            # Filtros adicionales
            conditions = []
            
            # Descuentos VIP
            if is_vip:
                conditions.append(ShopDiscount.applies_to_vip_only == True)
            
            # Descuentos por categoría
            if item.category:
                conditions.append(ShopDiscount.applies_to_category == item.category)
            
            # Descuentos por artículo específico
            conditions.append(ShopDiscount.applies_to_item_id == item.id)
            
            # Descuentos generales (sin restricciones específicas)
            conditions.append(
                and_(
                    ShopDiscount.applies_to_vip_only == False,
                    ShopDiscount.applies_to_category.is_(None),
                    ShopDiscount.applies_to_item_id.is_(None)
                )
            )
            
            if conditions:
                from sqlalchemy import or_
                stmt = stmt.where(or_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting applicable discounts: {e}")
            return []
    
    # === ESTADÍSTICAS Y REPORTES ===
    
    async def get_shop_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de la tienda."""
        try:
            # Total de artículos
            items_stmt = select(func.count()).select_from(ShopItem).where(ShopItem.is_active == True)
            items_result = await self.session.execute(items_stmt)
            total_items = items_result.scalar() or 0
            
            # Total de compras
            purchases_stmt = select(func.count()).select_from(UserPurchase)
            purchases_result = await self.session.execute(purchases_stmt)
            total_purchases = purchases_result.scalar() or 0
            
            # Ingresos totales
            revenue_stmt = select(func.sum(UserPurchase.price_paid)).select_from(UserPurchase)
            revenue_result = await self.session.execute(revenue_stmt)
            total_revenue = revenue_result.scalar() or 0
            
            # Artículo más popular
            popular_stmt = select(
                ShopItem.name, 
                func.count(UserPurchase.id).label('purchase_count')
            ).join(
                UserPurchase, ShopItem.id == UserPurchase.item_id
            ).group_by(
                ShopItem.id, ShopItem.name
            ).order_by(
                func.count(UserPurchase.id).desc()
            ).limit(1)
            
            popular_result = await self.session.execute(popular_stmt)
            popular_item = popular_result.first()
            
            return {
                "total_items": total_items,
                "total_purchases": total_purchases,
                "total_revenue": total_revenue,
                "most_popular_item": popular_item[0] if popular_item else "N/A",
                "most_popular_purchases": popular_item[1] if popular_item else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting shop statistics: {e}")
            return {}
    
    async def get_user_purchase_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de compras de un usuario."""
        try:
            stmt = select(UserPurchase, ShopItem).join(
                ShopItem, UserPurchase.item_id == ShopItem.id
            ).where(
                UserPurchase.user_id == user_id
            ).order_by(UserPurchase.purchased_at.desc())
            
            result = await self.session.execute(stmt)
            purchase_data = result.all()
            
            history = []
            for purchase, item in purchase_data:
                history.append({
                    "item_name": item.name,
                    "price_paid": purchase.price_paid,
                    "purchased_at": purchase.purchased_at,
                    "category": item.category
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting purchase history for user {user_id}: {e}")
            return []
    
    # === MÉTODOS PRIVADOS ===
    
    async def _get_user_purchase(self, user_id: int, item_id: int) -> Optional[UserPurchase]:
        """Verifica si el usuario ya compró un artículo específico."""
        stmt = select(UserPurchase).where(
            and_(
                UserPurchase.user_id == user_id,
                UserPurchase.item_id == item_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _add_to_inventory(self, user_id: int, item_id: int, quantity: int = 1):
        """Agrega un artículo al inventario del usuario."""
        # Verificar si ya existe en inventario
        stmt = select(UserInventory).where(
            and_(
                UserInventory.user_id == user_id,
                UserInventory.item_id == item_id
            )
        )
        result = await self.session.execute(stmt)
        inventory_entry = result.scalar_one_or_none()
        
        if inventory_entry:
            # Incrementar cantidad existente
            inventory_entry.quantity += quantity
        else:
            # Crear nueva entrada en inventario
            inventory_entry = UserInventory(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity
            )
            self.session.add(inventory_entry)
    
    async def _calculate_final_price(self, user_id: int, item: ShopItem) -> int:
        """Calcula el precio final aplicando descuentos."""
        base_price = item.price
        applicable_discounts = await self.get_applicable_discounts(user_id, item)
        
        if not applicable_discounts:
            return base_price
        
        # Aplicar el mejor descuento disponible
        best_discount = max(applicable_discounts, key=lambda d: d.discount_percentage)
        discount_amount = base_price * best_discount.discount_percentage
        final_price = max(1, int(base_price - discount_amount))  # Mínimo 1 punto
        
        logger.debug(f"Applied discount {best_discount.name}: {base_price} -> {final_price}")
        return final_price
    
    async def _unlock_narrative_lore(
        self, 
        user_id: int, 
        lore_code: str, 
        bot=None
    ) -> Optional[str]:
        """Desbloquea una pista narrativa al comprar un artículo."""
        try:
            # Verificar que la pista existe
            lore_piece = await self.lore_service.get_lore_piece_by_code(lore_code)
            if not lore_piece:
                logger.warning(f"Lore piece {lore_code} not found for unlock")
                return None
            
            # Desbloquear la pista usando el sistema existente
            from backpack import desbloquear_pista_narrativa
            success = await desbloquear_pista_narrativa(
                bot, 
                user_id, 
                lore_code,
                {"source": "shop_purchase", "timestamp": datetime.utcnow().isoformat()}
            )
            
            if success:
                logger.info(f"Unlocked lore piece {lore_code} for user {user_id} via shop purchase")
                return lore_piece.title
            else:
                logger.warning(f"Failed to unlock lore piece {lore_code} for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error unlocking narrative lore {lore_code} for user {user_id}: {e}")
            return None