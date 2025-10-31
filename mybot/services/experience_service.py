"""
Servicio para gestionar experiencias unificadas que integran narrativa, gamificación y tienda.
Permite configurar experiencias completas en un solo lugar con propagación automática.
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class ExperienceService:
    """Servicio para gestionar experiencias unificadas."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_experience(
        self,
        experience_id: str,
        name: str,
        description: str = "",
        requirements: Dict[str, Any] = None,
        triggers: Dict[str, Any] = None,
        rewards: Dict[str, Any] = None,
        narrative_flow: Dict[str, Any] = None
    ):
        """
        Crea una nueva experiencia unificada.
        
        Args:
            experience_id: ID único de la experiencia
            name: Nombre de la experiencia
            description: Descripción opcional
            requirements: Requisitos compuestos para acceder
            triggers: Qué desencadena la experiencia
            rewards: Recompensas automáticas
            narrative_flow: Flujo narrativo asociado
            
        Returns:
            UnifiedExperience creada
        """
        from database.experience_models import UnifiedExperience
        
        experience = UnifiedExperience(
            id=experience_id,
            name=name,
            description=description,
            requirements=requirements or {},
            triggers=triggers or {},
            rewards=rewards or {},
            narrative_flow=narrative_flow or {}
        )
        
        self.session.add(experience)
        await self.session.commit()
        await self.session.refresh(experience)
        
        logger.info(f"Experiencia unificada creada: {experience_id}")
        return experience
    
    async def get_experience(self, experience_id: str):
        """Obtiene una experiencia por ID."""
        from database.experience_models import UnifiedExperience
        
        result = await self.session.execute(
            select(UnifiedExperience).where(UnifiedExperience.id == experience_id)
        )
        return result.scalar_one_or_none()
    
    async def list_experiences(self, active_only: bool = True) -> List:
        """Lista todas las experiencias."""
        from database.experience_models import UnifiedExperience
        
        query = select(UnifiedExperience)
        if active_only:
            query = query.where(UnifiedExperience.is_active == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_experience(
        self,
        experience_id: str,
        **updates
    ):
        """Actualiza una experiencia existente."""
        experience = await self.get_experience(experience_id)
        if not experience:
            return None
        
        for key, value in updates.items():
            if hasattr(experience, key):
                setattr(experience, key, value)
        
        await self.session.commit()
        await self.session.refresh(experience)
        
        logger.info(f"Experiencia actualizada: {experience_id}")
        return experience
    
    async def delete_experience(self, experience_id: str) -> bool:
        """Elimina una experiencia (soft delete)."""
        experience = await self.get_experience(experience_id)
        if not experience:
            return False
        
        experience.is_active = False
        await self.session.commit()
        
        logger.info(f"Experiencia desactivada: {experience_id}")
        return True
    
    async def get_experience_elements(self, experience_id: str) -> Dict[str, List]:
        """
        Obtiene todos los elementos asociados a una experiencia.
        
        Returns:
            Dict con fragmentos, items de tienda y misiones
        """
        from database.narrative_models import StoryFragment
        from database.models import ShopItem, Mission
        
        experience = await self.get_experience(experience_id)
        if not experience:
            return {}
        
        # Obtener fragmentos narrativos
        fragments_result = await self.session.execute(
            select(StoryFragment).where(StoryFragment.experience_id == experience_id)
        )
        fragments = list(fragments_result.scalars().all())
        
        # Obtener items de tienda
        shop_items_result = await self.session.execute(
            select(ShopItem).where(ShopItem.experience_id == experience_id)
        )
        shop_items = list(shop_items_result.scalars().all())
        
        # Obtener misiones
        missions_result = await self.session.execute(
            select(Mission).where(Mission.experience_id == experience_id)
        )
        missions = list(missions_result.scalars().all())
        
        return {
            "fragments": fragments,
            "shop_items": shop_items,
            "missions": missions
        }
    
    async def add_dependency(
        self,
        experience_id: str,
        dependency_type: str,
        dependency_id: str,
        dependency_name: str
    ):
        """
        Agrega una dependencia a una experiencia.
        
        Args:
            experience_id: ID de la experiencia
            dependency_type: Tipo de dependencia ("fragment", "shop_item", "mission", "achievement")
            dependency_id: ID del elemento dependiente
            dependency_name: Nombre para mostrar
            
        Returns:
            ExperienceDependency creada
        """
        from database.experience_models import ExperienceDependency
        
        dependency = ExperienceDependency(
            experience_id=experience_id,
            dependency_type=dependency_type,
            dependency_id=dependency_id,
            dependency_name=dependency_name
        )
        
        self.session.add(dependency)
        await self.session.commit()
        await self.session.refresh(dependency)
        
        logger.info(f"Dependencia agregada: {dependency_type}:{dependency_id} a {experience_id}")
        return dependency
    
    async def get_dependencies(self, experience_id: str) -> List:
        """Obtiene todas las dependencias de una experiencia."""
        from database.experience_models import ExperienceDependency
        
        result = await self.session.execute(
            select(ExperienceDependency).where(
                ExperienceDependency.experience_id == experience_id
            )
        )
        return list(result.scalars().all())
    
    async def validate_experience_requirements(
        self,
        experience_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Valida si un usuario cumple los requisitos para acceder a una experiencia.
        
        Returns:
            Dict con resultado de validación y detalles
        """
        experience = await self.get_experience(experience_id)
        if not experience:
            return {
                "valid": False,
                "reason": "Experiencia no encontrada",
                "details": {}
            }
        
        requirements = experience.requirements or {}
        validation_result = {
            "valid": True,
            "reason": "",
            "details": {}
        }
        
        # Validar requisitos compuestos
        if "min_level" in requirements:
            from services.user_service import UserService
            user_service = UserService(self.session)
            user = await user_service.get_user(user_id)
            if user and user.level < requirements["min_level"]:
                validation_result["valid"] = False
                validation_result["reason"] = f"Nivel mínimo requerido: {requirements['min_level']}"
                validation_result["details"]["level"] = {
                    "required": requirements["min_level"],
                    "current": user.level
                }
        
        # Validar dependencias de otras experiencias
        dependencies = await self.get_dependencies(experience_id)
        for dependency in dependencies:
            if dependency.dependency_type == "experience":
                # Verificar si la experiencia dependiente está completada
                dep_validation = await self.validate_experience_requirements(
                    dependency.dependency_id, user_id
                )
                if not dep_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["reason"] = f"Experiencia requerida no completada: {dependency.dependency_name}"
                    validation_result["details"]["dependency"] = {
                        "id": dependency.dependency_id,
                        "name": dependency.dependency_name
                    }
                    break
        
        return validation_result
    
    async def get_total_count(self) -> int:
        """Obtiene el número total de experiencias."""
        from database.experience_models import UnifiedExperience
        
        result = await self.session.execute(
            select(UnifiedExperience)
        )
        experiences = result.scalars().all()
        return len(list(experiences))
    
    async def get_active_count(self) -> int:
        """Obtiene el número de experiencias activas."""
        from database.experience_models import UnifiedExperience
        
        result = await self.session.execute(
            select(UnifiedExperience).where(UnifiedExperience.is_active == True)
        )
        experiences = result.scalars().all()
        return len(list(experiences))
    
    async def get_all_experiences(self) -> List:
        """Obtiene todas las experiencias."""
        from database.experience_models import UnifiedExperience
        
        result = await self.session.execute(
            select(UnifiedExperience).order_by(UnifiedExperience.name)
        )
        return list(result.scalars().all())
    
    async def get_fragment_count(self, experience_id: str) -> int:
        """Obtiene el número de fragmentos asociados a una experiencia."""
        from database.narrative_models import StoryFragment
        
        result = await self.session.execute(
            select(StoryFragment).where(StoryFragment.experience_id == experience_id)
        )
        fragments = result.scalars().all()
        return len(list(fragments))
    
    async def get_item_count(self, experience_id: str) -> int:
        """Obtiene el número de items de tienda asociados a una experiencia."""
        from database.models import ShopItem
        
        result = await self.session.execute(
            select(ShopItem).where(ShopItem.experience_id == experience_id)
        )
        items = result.scalars().all()
        return len(list(items))
    
    async def get_mission_count(self, experience_id: str) -> int:
        """Obtiene el número de misiones asociadas a una experiencia."""
        from database.models import Mission
        
        result = await self.session.execute(
            select(Mission).where(Mission.experience_id == experience_id)
        )
        missions = result.scalars().all()
        return len(list(missions))
    
    async def get_total_fragment_count(self) -> int:
        """Obtiene el número total de fragmentos de todas las experiencias."""
        from database.narrative_models import StoryFragment
        
        result = await self.session.execute(
            select(StoryFragment).where(StoryFragment.experience_id.isnot(None))
        )
        fragments = result.scalars().all()
        return len(list(fragments))
    
    async def get_total_item_count(self) -> int:
        """Obtiene el número total de items de tienda de todas las experiencias."""
        from database.models import ShopItem
        
        result = await self.session.execute(
            select(ShopItem).where(ShopItem.experience_id.isnot(None))
        )
        items = result.scalars().all()
        return len(list(items))
    
    async def get_total_mission_count(self) -> int:
        """Obtiene el número total de misiones de todas las experiencias."""
        from database.models import Mission
        
        result = await self.session.execute(
            select(Mission).where(Mission.experience_id.isnot(None))
        )
        missions = result.scalars().all()
        return len(list(missions))
    
    async def update_experience_status(self, experience_id: str, is_active: bool) -> bool:
        """Actualiza el estado activo/inactivo de una experiencia."""
        experience = await self.get_experience(experience_id)
        if not experience:
            return False
        
        experience.is_active = is_active
        await self.session.commit()
        
        logger.info(f"Estado de experiencia {experience_id} actualizado a {'activa' if is_active else 'inactiva'}")
        return True
    
    async def get_experience_by_id(self, experience_id: str):
        """Alias para get_experience para mantener compatibilidad."""
        return await self.get_experience(experience_id)