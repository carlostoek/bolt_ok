"""
Servicio para propagar automáticamente elementos de experiencias unificadas
a los sistemas de narrativa, tienda y misiones.
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class ExperiencePropagator:
    """Propagador automático de elementos de experiencias."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def propagate_experience_elements(
        self,
        experience_id: str,
        narrative_config: Dict[str, Any] = None,
        shop_config: Dict[str, Any] = None,
        mission_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Propaga los elementos de una experiencia a los sistemas correspondientes.
        
        Args:
            experience_id: ID de la experiencia
            narrative_config: Configuración de fragmentos narrativos
            shop_config: Configuración de items de tienda
            mission_config: Configuración de misiones
            
        Returns:
            Dict con resultados de la propagación
        """
        results = {
            "fragments_created": [],
            "shop_items_created": [],
            "missions_created": [],
            "errors": []
        }
        
        # Propagar fragmentos narrativos
        if narrative_config:
            try:
                fragments = await self._propagate_narrative_elements(
                    experience_id, narrative_config
                )
                results["fragments_created"] = fragments
            except Exception as e:
                logger.error(f"Error propagando fragmentos para {experience_id}: {e}")
                results["errors"].append(f"Narrative: {str(e)}")
        
        # Propagar items de tienda
        if shop_config:
            try:
                shop_items = await self._propagate_shop_elements(
                    experience_id, shop_config
                )
                results["shop_items_created"] = shop_items
            except Exception as e:
                logger.error(f"Error propagando items de tienda para {experience_id}: {e}")
                results["errors"].append(f"Shop: {str(e)}")
        
        # Propagar misiones
        if mission_config:
            try:
                missions = await self._propagate_mission_elements(
                    experience_id, mission_config
                )
                results["missions_created"] = missions
            except Exception as e:
                logger.error(f"Error propagando misiones para {experience_id}: {e}")
                results["errors"].append(f"Mission: {str(e)}")
        
        logger.info(f"Propagación completada para experiencia {experience_id}")
        return results
    
    async def _propagate_narrative_elements(
        self,
        experience_id: str,
        narrative_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Propaga fragmentos narrativos."""
        from database.narrative_models import StoryFragment, NarrativeChoice
        
        created_fragments = []
        
        for fragment_data in narrative_config.get("fragments", []):
            # Crear fragmento
            fragment = StoryFragment(
                key=fragment_data["key"],
                text=fragment_data["text"],
                character=fragment_data.get("character", "Lucien"),
                level=fragment_data.get("level", 1),
                min_besitos=fragment_data.get("min_besitos", 0),
                reward_besitos=fragment_data.get("reward_besitos", 0),
                experience_id=experience_id
            )
            
            self.session.add(fragment)
            await self.session.flush()  # Para obtener el ID
            
            # Crear decisiones si existen
            for choice_data in fragment_data.get("choices", []):
                choice = NarrativeChoice(
                    source_fragment_id=fragment.id,
                    destination_fragment_key=choice_data["destination"],
                    text=choice_data["text"],
                    required_besitos=choice_data.get("required_besitos", 0),
                    required_role=choice_data.get("required_role")
                )
                self.session.add(choice)
            
            created_fragments.append({
                "id": fragment.id,
                "key": fragment.key,
                "text": fragment.text[:50] + "..." if len(fragment.text) > 50 else fragment.text
            })
        
        await self.session.commit()
        return created_fragments
    
    async def _propagate_shop_elements(
        self,
        experience_id: str,
        shop_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Propaga items de tienda."""
        from database.models import ShopItem
        
        created_items = []
        
        for item_data in shop_config.get("items", []):
            item = ShopItem(
                name=item_data["name"],
                description=item_data["description"],
                price=item_data["price"],
                is_vip_only=item_data.get("is_vip_only", False),
                unlocks_fragment_key=item_data.get("unlocks_fragment_key"),
                stock_limit=item_data.get("stock_limit"),
                max_purchases_per_user=item_data.get("max_purchases_per_user", 1),
                unlock_requirements=item_data.get("unlock_requirements"),
                experience_id=experience_id
            )
            
            self.session.add(item)
            await self.session.flush()
            
            created_items.append({
                "id": item.id,
                "name": item.name,
                "price": item.price
            })
        
        await self.session.commit()
        return created_items
    
    async def _propagate_mission_elements(
        self,
        experience_id: str,
        mission_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Propaga misiones."""
        from database.models import Mission
        
        created_missions = []
        
        for mission_data in mission_config.get("missions", []):
            mission = Mission(
                id=mission_data["id"],
                name=mission_data["name"],
                description=mission_data["description"],
                reward_points=mission_data.get("reward_points", 0),
                type=mission_data.get("type", "one_time"),
                target_value=mission_data.get("target_value", 1),
                duration_days=mission_data.get("duration_days", 0),
                requires_action=mission_data.get("requires_action", False),
                action_data=mission_data.get("action_data"),
                unlocks_lore_piece_code=mission_data.get("unlocks_lore_piece_code"),
                experience_id=experience_id
            )
            
            self.session.add(mission)
            
            created_missions.append({
                "id": mission.id,
                "name": mission.name,
                "reward_points": mission.reward_points
            })
        
        await self.session.commit()
        return created_missions
    
    async def create_complete_experience(
        self,
        experience_id: str,
        name: str,
        description: str = "",
        narrative_flow: Dict[str, Any] = None,
        shop_items: List[Dict[str, Any]] = None,
        missions: List[Dict[str, Any]] = None,
        requirements: Dict[str, Any] = None,
        rewards: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Crea una experiencia completa con todos sus elementos.
        
        Args:
            experience_id: ID único de la experiencia
            name: Nombre de la experiencia
            description: Descripción opcional
            narrative_flow: Flujo narrativo con fragmentos y decisiones
            shop_items: Items de tienda relacionados
            missions: Misiones relacionadas
            requirements: Requisitos para acceder
            rewards: Recompensas automáticas
            
        Returns:
            Dict con resultados de la creación
        """
        from services.experience_service import ExperienceService
        
        experience_service = ExperienceService(self.session)
        
        # Crear la experiencia base
        experience = await experience_service.create_experience(
            experience_id=experience_id,
            name=name,
            description=description,
            requirements=requirements or {},
            rewards=rewards or {},
            narrative_flow=narrative_flow or {}
        )
        
        # Propagar elementos
        propagation_results = await self.propagate_experience_elements(
            experience_id=experience_id,
            narrative_config=narrative_flow,
            shop_config={"items": shop_items or []},
            mission_config={"missions": missions or []}
        )
        
        # Agregar dependencias
        for fragment in propagation_results["fragments_created"]:
            await experience_service.add_dependency(
                experience_id=experience_id,
                dependency_type="fragment",
                dependency_id=fragment["key"],
                dependency_name=fragment["key"]
            )
        
        for shop_item in propagation_results["shop_items_created"]:
            await experience_service.add_dependency(
                experience_id=experience_id,
                dependency_type="shop_item",
                dependency_id=str(shop_item["id"]),
                dependency_name=shop_item["name"]
            )
        
        for mission in propagation_results["missions_created"]:
            await experience_service.add_dependency(
                experience_id=experience_id,
                dependency_type="mission",
                dependency_id=mission["id"],
                dependency_name=mission["name"]
            )
        
        return {
            "experience": {
                "id": experience.id,
                "name": experience.name
            },
            "propagation": propagation_results
        }
    
    async def update_experience_elements(
        self,
        experience_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza elementos de una experiencia existente.
        
        Args:
            experience_id: ID de la experiencia
            updates: Actualizaciones a aplicar
            
        Returns:
            Dict con resultados de la actualización
        """
        results = {
            "updated": [],
            "errors": []
        }
        
        # Actualizar fragmentos narrativos
        if "narrative" in updates:
            try:
                await self._update_narrative_elements(experience_id, updates["narrative"])
                results["updated"].append("narrative")
            except Exception as e:
                logger.error(f"Error actualizando narrativa para {experience_id}: {e}")
                results["errors"].append(f"Narrative: {str(e)}")
        
        # Actualizar items de tienda
        if "shop" in updates:
            try:
                await self._update_shop_elements(experience_id, updates["shop"])
                results["updated"].append("shop")
            except Exception as e:
                logger.error(f"Error actualizando tienda para {experience_id}: {e}")
                results["errors"].append(f"Shop: {str(e)}")
        
        # Actualizar misiones
        if "missions" in updates:
            try:
                await self._update_mission_elements(experience_id, updates["missions"])
                results["updated"].append("missions")
            except Exception as e:
                logger.error(f"Error actualizando misiones para {experience_id}: {e}")
                results["errors"].append(f"Missions: {str(e)}")
        
        return results
    
    async def _update_narrative_elements(
        self,
        experience_id: str,
        narrative_updates: Dict[str, Any]
    ):
        """Actualiza fragmentos narrativos."""
        from database.narrative_models import StoryFragment
        from sqlalchemy import select
        
        # Obtener fragmentos existentes
        result = await self.session.execute(
            select(StoryFragment).where(StoryFragment.experience_id == experience_id)
        )
        existing_fragments = result.scalars().all()
        
        # Actualizar fragmentos (implementación básica)
        for fragment in existing_fragments:
            if fragment.key in narrative_updates.get("fragments", {}):
                update_data = narrative_updates["fragments"][fragment.key]
                for key, value in update_data.items():
                    if hasattr(fragment, key):
                        setattr(fragment, key, value)
        
        await self.session.commit()
    
    async def _update_shop_elements(
        self,
        experience_id: str,
        shop_updates: Dict[str, Any]
    ):
        """Actualiza items de tienda."""
        from database.models import ShopItem
        from sqlalchemy import select
        
        # Obtener items existentes
        result = await self.session.execute(
            select(ShopItem).where(ShopItem.experience_id == experience_id)
        )
        existing_items = result.scalars().all()
        
        # Actualizar items (implementación básica)
        for item in existing_items:
            if str(item.id) in shop_updates.get("items", {}):
                update_data = shop_updates["items"][str(item.id)]
                for key, value in update_data.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
        
        await self.session.commit()
    
    async def _update_mission_elements(
        self,
        experience_id: str,
        mission_updates: Dict[str, Any]
    ):
        """Actualiza misiones."""
        from database.models import Mission
        from sqlalchemy import select
        
        # Obtener misiones existentes
        result = await self.session.execute(
            select(Mission).where(Mission.experience_id == experience_id)
        )
        existing_missions = result.scalars().all()
        
        # Actualizar misiones (implementación básica)
        for mission in existing_missions:
            if mission.id in mission_updates.get("missions", {}):
                update_data = mission_updates["missions"][mission.id]
                for key, value in update_data.items():
                    if hasattr(mission, key):
                        setattr(mission, key, value)
        
        await self.session.commit()