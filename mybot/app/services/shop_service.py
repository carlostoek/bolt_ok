"""
Servicio de lógica de negocio para el sistema de tienda.
Implementa el patrón Atomic Nested Creation validado en la POC.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func

from app.models.shop import ShopItem
from app.models.narrative import StoryFragment
from app.schemas.shop import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductCreateResponse
)
from app.schemas.narrative import FragmentCreateNested
from app.core.exceptions import (
    DatabaseException,
    DuplicateKeyException,
    ProductNotFoundException,
    NestedCreationException
)

logger = logging.getLogger(__name__)


class ShopService:
    """
    Servicio para gestionar productos de tienda.

    Implementa el patrón de creación anidada atómica que permite
    crear productos con fragmentos de desbloqueo en una sola transacción.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db

    async def create_product_with_nested(
        self,
        data: ProductCreate
    ) -> Dict[str, Any]:
        """
        Crea un producto de tienda con su fragmento de desbloqueo anidado.

        PATRÓN ATOMIC NESTED CREATION:
        1. Crear fragmento nested (si existe) → flush() → obtener key
        2. Crear producto principal → flush() → obtener ID
        3. Vincular fragmento al producto (actualizar unlocks_fragment_key)
        4. Commit único y atómico

        Args:
            data: Esquema de creación con soporte de nested entities

        Returns:
            Dict con el producto creado y resumen de entidades anidadas

        Raises:
            DuplicateKeyException: Si la key del fragmento ya existe
            NestedCreationException: Si falla la creación de entidades anidadas
            DatabaseException: Si falla el commit de la transacción
        """
        try:
            logger.info(f"→ Iniciando creación de producto: '{data.name}'")

            # Variables para tracking
            created_fragment: Optional[StoryFragment] = None
            unlocks_fragment_key = data.unlocks_fragment_key

            # ================================================================
            # PASO 1: CREAR FRAGMENTO NESTED (si existe)
            # ================================================================
            if data.unlocks_fragment:
                logger.info(f"  → Creando fragmento nested: '{data.unlocks_fragment.key}'")

                try:
                    # Verificar si el fragmento ya existe
                    existing_fragment_stmt = select(StoryFragment).where(
                        StoryFragment.key == data.unlocks_fragment.key
                    )
                    existing_fragment_result = await self.db.execute(existing_fragment_stmt)
                    existing_fragment = existing_fragment_result.scalar_one_or_none()

                    if existing_fragment:
                        raise DuplicateKeyException(data.unlocks_fragment.key)

                    # Crear fragmento nested
                    created_fragment = StoryFragment(
                        key=data.unlocks_fragment.key,
                        text=data.unlocks_fragment.text,
                        image_url=data.unlocks_fragment.image_url,
                        min_besitos=data.unlocks_fragment.min_besitos,
                        required_role=data.unlocks_fragment.required_role,
                        reward_besitos=data.unlocks_fragment.reward_besitos,
                        auto_next_fragment_key=data.unlocks_fragment.auto_next_fragment_key
                    )

                    self.db.add(created_fragment)
                    await self.db.flush()  # ← CRÍTICO: Obtener key sin commit

                    unlocks_fragment_key = created_fragment.key
                    logger.info(f"    ✓ Fragmento creado con key: {unlocks_fragment_key}")

                except IntegrityError as e:
                    if "unique constraint" in str(e).lower():
                        raise DuplicateKeyException(data.unlocks_fragment.key)
                    raise NestedCreationException(
                        str(e),
                        nested_entity="fragmento"
                    )
                except Exception as e:
                    raise NestedCreationException(
                        str(e),
                        nested_entity="fragmento"
                    )

            # ================================================================
            # PASO 2: CREAR PRODUCTO PRINCIPAL
            # ================================================================
            logger.info(f"  → Creando producto principal: '{data.name}'")

            try:
                product = ShopItem(
                    name=data.name,
                    description=data.description,
                    price=data.price,
                    is_vip_only=data.is_vip_only,
                    stock_limit=data.stock_limit,
                    max_purchases_per_user=data.max_purchases_per_user,
                    unlocks_fragment_key=unlocks_fragment_key
                )

                self.db.add(product)
                await self.db.flush()  # ← CRÍTICO: Obtener ID sin commit

                logger.info(f"    ✓ Producto creado con ID: {product.id}")

            except IntegrityError as e:
                raise DatabaseException(f"Error de integridad al crear producto: {str(e)}")

            # ================================================================
            # PASO 3: COMMIT ÚNICO Y ATÓMICO
            # ================================================================
            logger.info("  → Ejecutando commit atómico...")
            await self.db.commit()
            logger.info("    ✅ COMMIT EXITOSO - Todas las entidades creadas")

            # ================================================================
            # PASO 4: REFRESH PARA CARGAR RELACIONES
            # ================================================================
            await self.db.refresh(product)

            # ================================================================
            # CONSTRUIR RESPUESTA CON RESUMEN
            # ================================================================
            return {
                "success": True,
                "product": ProductResponse.model_validate(product),
                "created_fragment": {
                    "key": created_fragment.key,
                    "text": created_fragment.text,
                    "reward_besitos": created_fragment.reward_besitos
                } if created_fragment else None,
                "summary": {
                    "product_created": True,
                    "fragment_created": created_fragment is not None,
                    "total_entities": 1 + (1 if created_fragment else 0)
                }
            }

        except (DuplicateKeyException, NestedCreationException, DatabaseException):
            # Re-raise las excepciones específicas
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error inesperado al crear producto: {str(e)}")
            raise DatabaseException(f"Error inesperado: {str(e)}")

    async def get_product(self, product_id: int) -> Optional[ProductResponse]:
        """
        Obtiene un producto por su ID.

        Args:
            product_id: ID del producto

        Returns:
            ProductResponse si existe, None si no
        """
        try:
            stmt = select(ShopItem).where(ShopItem.id == product_id)
            result = await self.db.execute(stmt)
            product = result.scalar_one_or_none()

            if product:
                return ProductResponse.model_validate(product)
            return None

        except Exception as e:
            logger.error(f"Error obteniendo producto {product_id}: {str(e)}")
            raise DatabaseException(f"Error obteniendo producto: {str(e)}")

    async def get_all_products(
        self,
        is_vip_only: Optional[bool] = None,
        in_stock: Optional[bool] = None
    ) -> list[ProductResponse]:
        """
        Obtiene todos los productos con filtros opcionales.

        Args:
            is_vip_only: Filtrar por productos VIP
            in_stock: Filtrar por productos en stock

        Returns:
            Lista de ProductResponse
        """
        try:
            stmt = select(ShopItem)

            # Aplicar filtros
            if is_vip_only is not None:
                stmt = stmt.where(ShopItem.is_vip_only == is_vip_only)

            # TODO: Implementar filtro de stock cuando se agregue la lógica
            # if in_stock is not None:
            #     stmt = stmt.where(...)

            result = await self.db.execute(stmt)
            products = result.scalars().all()

            return [ProductResponse.model_validate(product) for product in products]

        except Exception as e:
            logger.error(f"Error obteniendo productos: {str(e)}")
            raise DatabaseException(f"Error obteniendo productos: {str(e)}")

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate
    ) -> Optional[ProductResponse]:
        """
        Actualiza un producto existente.

        Args:
            product_id: ID del producto
            data: Datos de actualización

        Returns:
            ProductResponse actualizado, None si no existe
        """
        try:
            stmt = select(ShopItem).where(ShopItem.id == product_id)
            result = await self.db.execute(stmt)
            product = result.scalar_one_or_none()

            if not product:
                return None

            # Actualizar campos
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)

            await self.db.commit()
            await self.db.refresh(product)

            return ProductResponse.model_validate(product)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error actualizando producto {product_id}: {str(e)}")
            raise DatabaseException(f"Error actualizando producto: {str(e)}")

    async def delete_product(self, product_id: int) -> bool:
        """
        Elimina un producto.

        Args:
            product_id: ID del producto

        Returns:
            True si se eliminó, False si no existe
        """
        try:
            stmt = select(ShopItem).where(ShopItem.id == product_id)
            result = await self.db.execute(stmt)
            product = result.scalar_one_or_none()

            if not product:
                return False

            await self.db.delete(product)
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error eliminando producto {product_id}: {str(e)}")
            raise DatabaseException(f"Error eliminando producto: {str(e)}")

    async def get_user_points(self, user_id: int) -> int:
        from database.models import User
        user = await self.db.get(User, user_id)
        return user.points if user else 0

    async def get_available_items(self, user_id: int) -> list[ShopItem]:
        from database.models import User
        user = await self.db.get(User, user_id)
        # This is a simplified version. A real implementation would check roles, etc.
        stmt = select(ShopItem).where(ShopItem.is_active == True)
        if not user or not user.is_vip:
            stmt = stmt.where(ShopItem.is_vip_only == False)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_item(self, item_id: int) -> Optional[ShopItem]:
        return await self.db.get(ShopItem, item_id)

    async def has_user_purchased_item(self, user_id: int, item_id: int) -> tuple[bool, int]:
        from database.models import UserPurchase
        stmt = select(func.count(UserPurchase.id)).where(
            UserPurchase.user_id == user_id,
            UserPurchase.shop_item_id == item_id
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return count > 0, count

    async def purchase_item(self, user_id: int, item_id: int) -> Dict[str, Any]:
        from database.models import User
        from database.models import UserPurchase

        user = await self.db.get(User, user_id)
        item = await self.db.get(ShopItem, item_id)

        if not user or not item:
            return {"success": False, "message": "Usuario o item no encontrado."}

        if user.points < item.price:
            return {"success": False, "message": "No tienes suficientes besitos."}

        user.points -= item.price
        purchase = UserPurchase(user_id=user_id, shop_item_id=item_id, price_paid=item.price)
        self.db.add(purchase)
        
        try:
            await self.db.commit()
            return {"success": True}
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error en la compra: {e}")
            return {"success": False, "message": "Error al procesar la compra."}