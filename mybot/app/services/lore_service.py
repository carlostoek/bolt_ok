"""
Servicio para gestión de piezas de lore.
Incluye lógica de negocio para lore y su desbloqueo.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.models.lore import LorePiece
from app.schemas.lore import LoreCreate, LoreUpdate, LoreFilterParams
from app.core.exceptions import NotFoundException, ValidationException


class LoreService:
    """Servicio para operaciones relacionadas con piezas de lore."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lore_piece(self, lore_id: str) -> Optional[LorePiece]:
        """Obtiene una pieza de lore por su ID de negocio."""
        result = await self.db.execute(
            select(LorePiece).where(LorePiece.lore_id == lore_id)
        )
        return result.scalar_one_or_none()

    async def get_lore_piece_by_id(self, id: int) -> Optional[LorePiece]:
        """Obtiene una pieza de lore por su ID numérico."""
        result = await self.db.execute(
            select(LorePiece).where(LorePiece.id == id)
        )
        return result.scalar_one_or_none()

    async def list_lore_pieces(
        self, 
        filters: LoreFilterParams,
        page: int = 1, 
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Lista piezas de lore con filtros y paginación."""
        query = select(LorePiece)

        # Aplicar filtros
        if filters.is_unlocked_by_default is not None:
            query = query.where(LorePiece.is_unlocked_by_default == filters.is_unlocked_by_default)
        if filters.required_role:
            query = query.where(LorePiece.required_role == filters.required_role)
        if filters.created_after:
            query = query.where(LorePiece.created_at >= filters.created_after)
        if filters.created_before:
            query = query.where(LorePiece.created_at <= filters.created_before)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    LorePiece.lore_id.ilike(search_term),
                    LorePiece.title.ilike(search_term),
                    LorePiece.content.ilike(search_term)
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
        lore_pieces = result.scalars().all()

        return {
            "data": lore_pieces,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }

    async def create_lore_piece(self, lore_data: LoreCreate) -> LorePiece:
        """Crea una nueva pieza de lore."""
        # Verificar si el lore_id ya existe
        existing_lore = await self.get_lore_piece(lore_data.lore_id)
        if existing_lore:
            raise ValidationException(f"La pieza de lore con ID '{lore_data.lore_id}' ya existe")

        # Crear pieza de lore
        lore_piece = LorePiece(**lore_data.model_dump())
        self.db.add(lore_piece)

        await self.db.commit()
        await self.db.refresh(lore_piece)
        return lore_piece

    async def update_lore_piece(self, lore_id: str, lore_data: LoreUpdate) -> LorePiece:
        """Actualiza una pieza de lore existente."""
        lore_piece = await self.get_lore_piece(lore_id)
        if not lore_piece:
            raise NotFoundException(f"Pieza de lore con ID '{lore_id}' no encontrada")

        # Actualizar campos
        update_data = lore_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lore_piece, field, value)

        await self.db.commit()
        await self.db.refresh(lore_piece)
        return lore_piece

    async def delete_lore_piece(self, lore_id: str) -> bool:
        """Elimina una pieza de lore."""
        lore_piece = await self.get_lore_piece(lore_id)
        if not lore_piece:
            raise NotFoundException(f"Pieza de lore con ID '{lore_id}' no encontrada")

        await self.db.delete(lore_piece)
        await self.db.commit()
        return True

    async def bulk_create_lore_pieces(self, lore_pieces_data: List[LoreCreate]) -> List[LorePiece]:
        """Crea múltiples piezas de lore en lote."""
        created_pieces = []
        
        for lore_data in lore_pieces_data:
            # Verificar si el lore_id ya existe
            existing_lore = await self.get_lore_piece(lore_data.lore_id)
            if existing_lore:
                raise ValidationException(f"La pieza de lore con ID '{lore_data.lore_id}' ya existe")

            lore_piece = LorePiece(**lore_data.model_dump())
            self.db.add(lore_piece)
            created_pieces.append(lore_piece)

        await self.db.commit()
        
        # Refrescar los objetos para obtener los IDs
        for piece in created_pieces:
            await self.db.refresh(piece)
        
        return created_pieces

    async def search_lore_pieces(self, query: str, limit: int = 10) -> List[LorePiece]:
        """Busca piezas de lore por texto."""
        search_term = f"%{query}%"
        
        result = await self.db.execute(
            select(LorePiece)
            .where(
                or_(
                    LorePiece.lore_id.ilike(search_term),
                    LorePiece.title.ilike(search_term),
                    LorePiece.content.ilike(search_term)
                )
            )
            .limit(limit)
        )
        
        return result.scalars().all()

    async def get_lore_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre las piezas de lore."""
        # Total de piezas de lore
        total_result = await self.db.execute(select(func.count(LorePiece.id)))
        total = total_result.scalar_one()

        # Piezas desbloqueadas por defecto
        unlocked_result = await self.db.execute(
            select(func.count(LorePiece.id)).where(LorePiece.is_unlocked_by_default == True)
        )
        unlocked_by_default = unlocked_result.scalar_one()

        # Piezas por rol requerido
        roles_result = await self.db.execute(
            select(LorePiece.required_role, func.count(LorePiece.id))
            .group_by(LorePiece.required_role)
        )
        roles_distribution = dict(roles_result.all())

        return {
            "total_lore_pieces": total,
            "unlocked_by_default": unlocked_by_default,
            "locked_pieces": total - unlocked_by_default,
            "roles_distribution": roles_distribution
        }