"""
Servicio para gestión de usuarios.
Incluye lógica de negocio para usuarios, roles, VIP y puntos.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.user import User, UserNarrativeState, InventoryItem, UserRole
from app.models.shop import ShopItem
from app.schemas.user import UserCreate, UserUpdate, UserFilterParams
from app.core.exceptions import NotFoundException, ValidationException


class UserService:
    """Servicio para operaciones relacionadas con usuarios."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_with_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario con su perfil completo."""
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.narrative_state),
                selectinload(User.inventory_items).selectinload(InventoryItem.product)
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None

        # Calcular progreso narrativo
        narrative_progress = {
            "current_fragment_key": user.narrative_state.current_fragment_key if user.narrative_state else None,
            "fragments_viewed": user.narrative_state.fragments_viewed if user.narrative_state else 0,
            "choices_made": user.narrative_state.choices_made if user.narrative_state else 0,
            "unlocked_fragments": user.narrative_state.unlocked_fragments if user.narrative_state else [],
            "completion_percentage": 0.0  # TODO: Calcular basado en fragmentos totales
        }

        # Preparar inventario
        inventory = [
            {
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Producto desconocido",
                "acquired_at": item.acquired_at,
                "quantity": item.quantity
            }
            for item in user.inventory_items
        ]

        return {
            "user": user,
            "narrative_progress": narrative_progress,
            "inventory": inventory,
            "missions_completed": 0,  # TODO: Integrar con módulo de misiones
            "achievements_unlocked": 0  # TODO: Integrar con módulo de logros
        }

    async def list_users(
        self, 
        filters: UserFilterParams,
        page: int = 1, 
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Lista usuarios con filtros y paginación."""
        query = select(User)

        # Aplicar filtros
        if filters.role:
            query = query.where(User.role == filters.role)
        if filters.is_banned is not None:
            query = query.where(User.is_banned == filters.is_banned)
        if filters.is_vip is not None:
            query = query.where(User.is_vip == filters.is_vip)
        if filters.min_points is not None:
            query = query.where(User.points >= filters.min_points)
        if filters.max_points is not None:
            query = query.where(User.points <= filters.max_points)
        if filters.registered_after:
            query = query.where(User.created_at >= filters.registered_after)
        if filters.registered_before:
            query = query.where(User.created_at <= filters.registered_before)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    User.username.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Aplicar paginación
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Ejecutar consulta
        result = await self.db.execute(query)
        users = result.scalars().all()

        return {
            "data": users,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }

    async def create_user(self, user_data: UserCreate) -> User:
        """Crea un nuevo usuario."""
        # Verificar si el usuario ya existe
        existing_user = await self.get_user(user_data.id)
        if existing_user:
            raise ValidationException(f"El usuario con ID {user_data.id} ya existe")

        # Crear usuario
        user = User(**user_data.dict())
        self.db.add(user)

        # Crear estado narrativo por defecto
        narrative_state = UserNarrativeState(user_id=user.id)
        self.db.add(narrative_state)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Actualiza un usuario existente."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        # Actualizar campos
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def grant_vip(self, user_id: int, days: int) -> User:
        """Concede VIP a un usuario por una cantidad de días."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        # Calcular fecha de expiración
        expires_at = datetime.now() + timedelta(days=days)
        
        user.is_vip = True
        user.vip_expires_at = datetime.utcnow() + timedelta(days=days)
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def add_points(self, user_id: int, amount: int) -> User:
        """Añade puntos a un usuario."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        user.points += amount
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def remove_points(self, user_id: int, amount: int) -> User:
        """Resta puntos a un usuario."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        if user.points < amount:
            raise ValidationException("El usuario no tiene suficientes puntos")

        user.points -= amount
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def ban_user(self, user_id: int) -> User:
        """Banea a un usuario."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        user.is_banned = True
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def unban_user(self, user_id: int) -> User:
        """Desbanea a un usuario."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        user.is_banned = False
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_user_role(self, user_id: int, role: UserRole) -> User:
        """Cambia el rol de un usuario."""
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        user.role = role
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def add_to_inventory(self, user_id: int, product_id: int) -> InventoryItem:
        """Añade un producto al inventario del usuario."""
        # Verificar que el usuario existe
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        # Verificar que el producto existe
        result = await self.db.execute(
            select(ShopItem).where(ShopItem.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Producto con ID {product_id} no encontrado")

        # Verificar si ya tiene el producto
        result = await self.db.execute(
            select(InventoryItem).where(
                and_(
                    InventoryItem.user_id == user_id,
                    InventoryItem.product_id == product_id
                )
            )
        )
        existing_item = result.scalar_one_or_none()

        if existing_item:
            # Incrementar cantidad
            existing_item.quantity += 1
            item = existing_item
        else:
            # Crear nuevo ítem
            item = InventoryItem(
                user_id=user_id,
                product_id=product_id,
                quantity=1
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def set_current_fragment(self, user_id: int, fragment_key: str) -> UserNarrativeState:
        """Establece el fragmento actual de un usuario."""
        # Verificar que el usuario existe
        user = await self.get_user(user_id)
        if not user:
            raise NotFoundException(f"Usuario con ID {user_id} no encontrado")

        # Obtener o crear estado narrativo
        result = await self.db.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        narrative_state = result.scalar_one_or_none()

        if not narrative_state:
            narrative_state = UserNarrativeState(user_id=user_id)
            self.db.add(narrative_state)

        narrative_state.current_fragment_key = fragment_key
        narrative_state.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(narrative_state)
        return narrative_state