"""
Servicio de administración narrativa para la gestión de fragmentos narrativos.
Permite a los administradores gestionar, visualizar y analizar el contenido narrativo.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.notification_service import NotificationService
from services.event_bus import get_event_bus, EventType

logger = logging.getLogger(__name__)

VALID_FRAGMENT_TYPES = ["STORY", "DECISION", "INFO"]

class NarrativeAdminService:
    """
    Servicio para administración de contenido narrativo.
    Permite gestionar fragmentos, visualizar estructura y analizar engagement.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con la sesión de base de datos.
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.event_bus = get_event_bus()
        
    async def get_narrative_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales del sistema narrativo.
        
        Returns:
            Dict con estadísticas de fragmentos, usuarios y engagement
        """
        try:
            # Total de fragmentos
            total_query = select(func.count(NarrativeFragment.id))
            total_result = await self.session.execute(total_query)
            total_fragments = total_result.scalar() or 0
            
            # Fragmentos por tipo
            by_type_query = select(NarrativeFragment.fragment_type, func.count(NarrativeFragment.id))\
                .group_by(NarrativeFragment.fragment_type)
            fragments_by_type_result = await self.session.execute(by_type_query)
            fragments_by_type = dict(fragments_by_type_result.all())
            
            # Fragmentos activos
            active_query = select(func.count(NarrativeFragment.id))\
                .where(NarrativeFragment.is_active == True)
            active_result = await self.session.execute(active_query)
            active_fragments = active_result.scalar() or 0
            
            # Fragmentos con conexiones
            connections_query = select(func.count(NarrativeFragment.id))\
                .where(NarrativeFragment.choices.cast(str) != '[]')
            connections_result = await self.session.execute(connections_query)
            fragments_with_connections = connections_result.scalar() or 0
            
            # Usuarios en narrativa
            users_query = select(func.count(UserNarrativeState.user_id))
            users_result = await self.session.execute(users_query)
            users_in_narrative = users_result.scalar() or 0
            
            # Promedio de fragmentos completados por usuario
            avg_completed_query = select(func.avg(func.array_length(UserNarrativeState.completed_fragments, 1)))\
                .where(func.array_length(UserNarrativeState.completed_fragments, 1) > 0)
            avg_completed_result = await self.session.execute(avg_completed_query)
            avg_fragments_completed = avg_completed_result.scalar() or 0
            
            # Construir diccionario de estadísticas
            stats = {
                "total_fragments": total_fragments,
                "active_fragments": active_fragments,
                "inactive_fragments": total_fragments - active_fragments,
                "fragments_by_type": fragments_by_type,
                "fragments_with_connections": fragments_with_connections,
                "users_in_narrative": users_in_narrative,
                "avg_fragments_completed": avg_fragments_completed
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas narrativas: {e}")
            return {
                "total_fragments": 0,
                "active_fragments": 0,
                "inactive_fragments": 0,
                "fragments_by_type": {"STORY": 0, "DECISION": 0, "INFO": 0},
                "fragments_with_connections": 0,
                "users_in_narrative": 0,
                "avg_fragments_completed": 0
            }
            
    async def get_fragment_details(self, fragment_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles completos de un fragmento incluyendo estadísticas de uso.
        
        Args:
            fragment_id: ID del fragmento
            
        Returns:
            Dict con detalles del fragmento y estadísticas
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener el fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID '{fragment_id}' no encontrado")
            
            # Obtener estadísticas de uso
            # Usuarios que tienen este fragmento como actual
            active_users_query = select(func.count(UserNarrativeState.user_id))\
                .where(UserNarrativeState.current_fragment_id == fragment_id)
            active_users_result = await self.session.execute(active_users_query)
            active_users = active_users_result.scalar() or 0
            
            # Usuarios que han visitado este fragmento
            visited_users_query = select(func.count(UserNarrativeState.user_id))\
                .where(UserNarrativeState.visited_fragments.contains([fragment_id]))
            visited_users_result = await self.session.execute(visited_users_query)
            visited_users = visited_users_result.scalar() or 0
            
            # Usuarios que han completado este fragmento
            completed_users_query = select(func.count(UserNarrativeState.user_id))\
                .where(UserNarrativeState.completed_fragments.contains([fragment_id]))
            completed_users_result = await self.session.execute(completed_users_query)
            completed_users = completed_users_result.scalar() or 0
            
            # Calcular tasa de finalización
            completion_rate = (completed_users / visited_users * 100) if visited_users > 0 else 0
            
            # Construir diccionario de detalles
            fragment_details = {
                "id": fragment.id,
                "title": fragment.title,
                "content": fragment.content,
                "type": fragment.fragment_type,
                "created_at": str(fragment.created_at) if fragment.created_at else None,
                "updated_at": str(fragment.updated_at) if fragment.updated_at else None,
                "is_active": fragment.is_active,
                "choices": fragment.choices or [],
                "triggers": fragment.triggers or {},
                "required_clues": fragment.required_clues or [],
                "statistics": {
                    "active_users": active_users,
                    "visited_users": visited_users,
                    "completed_users": completed_users,
                    "completion_rate": round(completion_rate, 1)
                }
            }
            
            return fragment_details
            
        except ValueError as ve:
            # Re-lanzar ValueError para que el handler pueda manejarlo
            raise ve
        except Exception as e:
            logger.error(f"Error obteniendo detalles del fragmento '{fragment_id}': {e}")
            raise ValueError(f"Error al obtener detalles del fragmento: {e}")

    
    async def get_all_fragments(self, 
                               page: int = 1, 
                               limit: int = 10, 
                               filter_type: Optional[str] = None,
                               search_query: Optional[str] = None,
                               include_inactive: bool = False) -> Dict[str, Any]:
        """
        Obtiene fragmentos narrativos con paginación y filtrado opcional.
        
        Args:
            page: Número de página (comienza en 1)
            limit: Cantidad de resultados por página
            filter_type: Tipo de fragmento para filtrar (STORY, DECISION, INFO)
            search_query: Término de búsqueda para título o contenido
            include_inactive: Si es True, incluye fragmentos inactivos
            
        Returns:
            Dict con fragmentos paginados y metadatos
        """
        try:
            # Calcular offset para paginación
            offset = (page - 1) * limit
            
            # Construir consulta base
            base_query = select(NarrativeFragment)
            
            # Aplicar filtros
            if not include_inactive:
                base_query = base_query.where(NarrativeFragment.is_active == True)
                
            if filter_type:
                base_query = base_query.where(NarrativeFragment.fragment_type == filter_type)
                
            if search_query:
                search_pattern = f"%{search_query}%"
                base_query = base_query.where(
                    or_(
                        NarrativeFragment.title.ilike(search_pattern),
                        NarrativeFragment.content.ilike(search_pattern)
                    )
                )
            
            # Contar total de resultados para metadatos de paginación
            count_query = select(func.count()).select_from(base_query.subquery())
            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Aplicar paginación y ordenar por fecha de actualización
            query = base_query.order_by(desc(NarrativeFragment.updated_at)).offset(offset).limit(limit)
            
            # Ejecutar consulta paginada
            result = await self.session.execute(query)
            fragments = result.scalars().all()
            
            # Formatear fragmentos para la respuesta
            fragment_list = []
            for fragment in fragments:
                fragment_data = {
                    "id": fragment.id,
                    "title": fragment.title,
                    "type": fragment.fragment_type,
                    "created_at": fragment.created_at.isoformat() if fragment.created_at else None,
                    "updated_at": fragment.updated_at.isoformat() if fragment.updated_at else None,
                    "is_active": fragment.is_active,
                    "has_choices": bool(fragment.choices),
                    "has_triggers": bool(fragment.triggers),
                    "has_requirements": bool(fragment.required_clues)
                }
                fragment_list.append(fragment_data)
            
            # Preparar metadatos de paginación
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            
            return {
                "items": fragment_list,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "filter_type": filter_type,
                "search_query": search_query
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo fragmentos narrativos: {e}")
            raise
    
    async def get_fragment_details(self, fragment_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles completos de un fragmento incluyendo estadísticas de uso.
        
        Args:
            fragment_id: ID único del fragmento
            
        Returns:
            Dict con detalles completos del fragmento y estadísticas
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Obtener número de usuarios que tienen este fragmento como actual
            users_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.current_fragment_id == fragment_id
            )
            users_result = await self.session.execute(users_query)
            active_users = users_result.scalar() or 0
            
            # Obtener número de usuarios que han visitado este fragmento
            visited_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.visited_fragments.contains([fragment_id])
            )
            visited_result = await self.session.execute(visited_query)
            visited_users = visited_result.scalar() or 0
            
            # Obtener número de usuarios que han completado este fragmento
            completed_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.completed_fragments.contains([fragment_id])
            )
            completed_result = await self.session.execute(completed_query)
            completed_users = completed_result.scalar() or 0
            
            # Formatear datos para la respuesta
            response = {
                "id": fragment.id,
                "title": fragment.title,
                "content": fragment.content,
                "type": fragment.fragment_type,
                "created_at": fragment.created_at.isoformat() if fragment.created_at else None,
                "updated_at": fragment.updated_at.isoformat() if fragment.updated_at else None,
                "is_active": fragment.is_active,
                "choices": fragment.choices,
                "triggers": fragment.triggers,
                "required_clues": fragment.required_clues,
                "statistics": {
                    "active_users": active_users,
                    "visited_users": visited_users,
                    "completed_users": completed_users,
                    "completion_rate": (completed_users / visited_users * 100) if visited_users > 0 else 0
                }
            }
            
            return response
            
        except ValueError as e:
            logger.error(f"Error de validación al obtener detalles de fragmento: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo detalles de fragmento: {e}")
            raise
    
    async def create_fragment(self, fragment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo fragmento narrativo.
        
        Args:
            fragment_data: Datos del fragmento a crear
            
        Returns:
            Dict con datos del fragmento creado
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        try:
            # Validar datos requeridos
            required_fields = ["title", "content", "fragment_type"]
            for field in required_fields:
                if field not in fragment_data or not fragment_data[field]:
                    raise ValueError(f"Campo requerido '{field}' faltante o vacío")
            
            # Validar tipo de fragmento
            valid_types = ["STORY", "DECISION", "INFO"]
            if fragment_data["fragment_type"] not in valid_types:
                raise ValueError(f"Tipo de fragmento inválido. Debe ser uno de: {', '.join(valid_types)}")
            
            # Crear objeto de fragmento
            fragment = NarrativeFragment(
                title=fragment_data["title"],
                content=fragment_data["content"],
                fragment_type=fragment_data["fragment_type"],
                choices=fragment_data.get("choices", []),
                triggers=fragment_data.get("triggers", {}),
                required_clues=fragment_data.get("required_clues", []),
                is_active=fragment_data.get("is_active", True)
            )
            
            # Guardar en la base de datos
            self.session.add(fragment)
            await self.session.commit()
            await self.session.refresh(fragment)
            
            # Emitir evento de creación
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # ID del sistema
                {
                    "action": "fragment_created",
                    "fragment_id": fragment.id,
                    "fragment_type": fragment.fragment_type
                },
                source="narrative_admin_service"
            )
            
            # Devolver datos del fragmento creado
            return {
                "id": fragment.id,
                "title": fragment.title,
                "content": fragment.content,
                "type": fragment.fragment_type,
                "created_at": fragment.created_at.isoformat() if fragment.created_at else None,
                "updated_at": fragment.updated_at.isoformat() if fragment.updated_at else None,
                "is_active": fragment.is_active,
                "choices": fragment.choices,
                "triggers": fragment.triggers,
                "required_clues": fragment.required_clues
            }
            
        except ValueError as e:
            logger.error(f"Error de validación al crear fragmento: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creando fragmento narrativo: {e}")
            await self.session.rollback()
            raise
    
    async def update_fragment(self, fragment_id: str, fragment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un fragmento existente.
        
        Args:
            fragment_id: ID único del fragmento a actualizar
            fragment_data: Datos actualizados del fragmento
            
        Returns:
            Dict con datos del fragmento actualizado
            
        Raises:
            ValueError: Si el fragmento no existe o los datos son inválidos
        """
        try:
            # Obtener fragmento existente
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Actualizar campos
            if "title" in fragment_data and fragment_data["title"]:
                fragment.title = fragment_data["title"]
                
            if "content" in fragment_data and fragment_data["content"]:
                fragment.content = fragment_data["content"]
                
            if "fragment_type" in fragment_data and fragment_data["fragment_type"]:
                valid_types = ["STORY", "DECISION", "INFO"]
                if fragment_data["fragment_type"] not in valid_types:
                    raise ValueError(f"Tipo de fragmento inválido. Debe ser uno de: {', '.join(valid_types)}")
                fragment.fragment_type = fragment_data["fragment_type"]
                
            if "choices" in fragment_data:
                fragment.choices = fragment_data["choices"]
                
            if "triggers" in fragment_data:
                fragment.triggers = fragment_data["triggers"]
                
            if "required_clues" in fragment_data:
                fragment.required_clues = fragment_data["required_clues"]
                
            if "is_active" in fragment_data:
                fragment.is_active = bool(fragment_data["is_active"])
            
            # Guardar cambios
            await self.session.commit()
            await self.session.refresh(fragment)
            
            # Emitir evento de actualización
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # ID del sistema
                {
                    "action": "fragment_updated",
                    "fragment_id": fragment.id,
                    "fragment_type": fragment.fragment_type
                },
                source="narrative_admin_service"
            )
            
            # Devolver datos actualizados
            return {
                "id": fragment.id,
                "title": fragment.title,
                "content": fragment.content,
                "type": fragment.fragment_type,
                "created_at": fragment.created_at.isoformat() if fragment.created_at else None,
                "updated_at": fragment.updated_at.isoformat() if fragment.updated_at else None,
                "is_active": fragment.is_active,
                "choices": fragment.choices,
                "triggers": fragment.triggers,
                "required_clues": fragment.required_clues
            }
            
        except ValueError as e:
            logger.error(f"Error de validación al actualizar fragmento: {e}")
            raise
        except Exception as e:
            logger.error(f"Error actualizando fragmento narrativo: {e}")
            await self.session.rollback()
            raise
    
    async def delete_fragment(self, fragment_id: str) -> bool:
        """
        Marca un fragmento como inactivo (borrado lógico).
        
        Args:
            fragment_id: ID único del fragmento a marcar como inactivo
            
        Returns:
            bool: True si el fragmento fue marcado como inactivo correctamente
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener fragmento existente
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Marcar como inactivo (borrado lógico)
            fragment.is_active = False
            
            # Guardar cambios
            await self.session.commit()
            
            # Emitir evento de borrado
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # ID del sistema
                {
                    "action": "fragment_deleted",
                    "fragment_id": fragment_id
                },
                source="narrative_admin_service"
            )
            
            return True
            
        except ValueError as e:
            logger.error(f"Error de validación al eliminar fragmento: {e}")
            raise
        except Exception as e:
            logger.error(f"Error eliminando fragmento narrativo: {e}")
            await self.session.rollback()
            raise
    
    async def get_fragment_connections(self, fragment_id: str) -> Dict[str, Any]:
        """
        Obtiene fragmentos conectados (entrada/salida) a un fragmento específico.
        
        Args:
            fragment_id: ID único del fragmento
            
        Returns:
            Dict con fragmentos conectados, tanto de entrada como de salida
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Encontrar conexiones de salida (fragmentos a los que este fragmento puede llevar)
            outgoing_connections = []
            for choice in fragment.choices:
                if "next_fragment" in choice:
                    target_id = choice["next_fragment"]
                    
                    # Obtener fragmento destino
                    target_query = select(NarrativeFragment).where(NarrativeFragment.id == target_id)
                    target_result = await self.session.execute(target_query)
                    target_fragment = target_result.scalar_one_or_none()
                    
                    if target_fragment:
                        outgoing_connections.append({
                            "id": target_fragment.id,
                            "title": target_fragment.title,
                            "type": target_fragment.fragment_type,
                            "is_active": target_fragment.is_active,
                            "choice_text": choice.get("text", "")
                        })
            
            # Encontrar conexiones de entrada (fragmentos que pueden llevar a este fragmento)
            incoming_query = select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            incoming_result = await self.session.execute(incoming_query)
            all_fragments = incoming_result.scalars().all()
            
            incoming_connections = []
            for potential_source in all_fragments:
                for choice in potential_source.choices:
                    if "next_fragment" in choice and choice["next_fragment"] == fragment_id:
                        incoming_connections.append({
                            "id": potential_source.id,
                            "title": potential_source.title,
                            "type": potential_source.fragment_type,
                            "is_active": potential_source.is_active,
                            "choice_text": choice.get("text", "")
                        })
            
            return {
                "fragment_id": fragment_id,
                "fragment_title": fragment.title,
                "fragment_type": fragment.fragment_type,
                "outgoing_connections": outgoing_connections,
                "incoming_connections": incoming_connections
            }
            
        except ValueError as e:
            logger.error(f"Error de validación al obtener conexiones: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo conexiones de fragmento: {e}")
            raise
    
    async def update_fragment_connections(self, fragment_id: str, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Actualiza las conexiones de un fragmento.
        
        Args:
            fragment_id: ID único del fragmento
            connections: Lista de conexiones a actualizar
            
        Returns:
            Dict con fragmentos conectados actualizados
            
        Raises:
            ValueError: Si el fragmento no existe o datos inválidos
        """
        try:
            # Obtener fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Validar datos de conexiones
            if not isinstance(connections, list):
                raise ValueError("Las conexiones deben ser una lista")
            
            # Actualizar las opciones de elección (choices)
            new_choices = []
            for connection in connections:
                if not isinstance(connection, dict):
                    raise ValueError("Cada conexión debe ser un objeto")
                
                if "text" not in connection or not connection["text"]:
                    raise ValueError("Cada conexión debe tener un texto")
                
                if "next_fragment" not in connection or not connection["next_fragment"]:
                    raise ValueError("Cada conexión debe tener un fragmento destino")
                
                # Verificar que el fragmento destino existe
                target_query = select(NarrativeFragment).where(NarrativeFragment.id == connection["next_fragment"])
                target_result = await self.session.execute(target_query)
                if not target_result.scalar_one_or_none():
                    raise ValueError(f"Fragmento destino con ID {connection['next_fragment']} no encontrado")
                
                # Añadir conexión a la lista
                new_choices.append({
                    "text": connection["text"],
                    "next_fragment": connection["next_fragment"],
                    "requirements": connection.get("requirements", {})
                })
            
            # Actualizar choices del fragmento
            fragment.choices = new_choices
            
            # Guardar cambios
            await self.session.commit()
            await self.session.refresh(fragment)
            
            # Emitir evento de actualización
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # ID del sistema
                {
                    "action": "fragment_connections_updated",
                    "fragment_id": fragment_id,
                    "connections_count": len(new_choices)
                },
                source="narrative_admin_service"
            )
            
            # Obtener conexiones actualizadas
            return await self.get_fragment_connections(fragment_id)
            
        except ValueError as e:
            logger.error(f"Error de validación al actualizar conexiones: {e}")
            raise
        except Exception as e:
            logger.error(f"Error actualizando conexiones de fragmento: {e}")
            await self.session.rollback()
            raise
    
    async def get_narrative_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales del sistema narrativo.
        
        Returns:
            Dict con estadísticas globales
        """
        try:
            # Total de fragmentos
            total_fragments_query = select(func.count()).select_from(NarrativeFragment)
            total_fragments_result = await self.session.execute(total_fragments_query)
            total_fragments = total_fragments_result.scalar() or 0
            
            # Fragmentos por tipo
            fragments_by_type_query = select(
                NarrativeFragment.fragment_type, 
                func.count()
            ).group_by(NarrativeFragment.fragment_type)
            fragments_by_type_result = await self.session.execute(fragments_by_type_query)
            fragments_by_type = dict(fragments_by_type_result.all())
            
            # Fragmentos activos vs inactivos
            active_fragments_query = select(func.count()).select_from(NarrativeFragment).where(
                NarrativeFragment.is_active == True
            )
            active_fragments_result = await self.session.execute(active_fragments_query)
            active_fragments = active_fragments_result.scalar() or 0
            
            # Fragmentos con conexiones
            fragments_with_connections_query = select(func.count()).select_from(NarrativeFragment).where(
                NarrativeFragment.choices != []
            )
            fragments_with_connections_result = await self.session.execute(fragments_with_connections_query)
            fragments_with_connections = fragments_with_connections_result.scalar() or 0
            
            # Usuarios activos en la narrativa
            users_in_narrative_query = select(func.count()).select_from(UserNarrativeState)
            users_in_narrative_result = await self.session.execute(users_in_narrative_query)
            users_in_narrative = users_in_narrative_result.scalar() or 0
            
            # Tasa de engagement promedio - compatible con SQLite
            try:
                # Intentar obtener todos los estados de usuario
                user_states_query = select(UserNarrativeState)
                user_states_result = await self.session.execute(user_states_query)
                user_states = user_states_result.scalars().all()
                
                # Calcular manualmente el promedio de fragmentos completados
                if user_states:
                    total_completed = sum(len(state.completed_fragments) for state in user_states)
                    avg_completion = total_completed / len(user_states)
                else:
                    avg_completion = 0
            except Exception as e:
                logger.warning(f"Error calculando promedio de fragmentos completados: {e}")
                avg_completion = 0
            
            return {
                "total_fragments": total_fragments,
                "active_fragments": active_fragments,
                "inactive_fragments": total_fragments - active_fragments,
                "fragments_by_type": fragments_by_type,
                "fragments_with_connections": fragments_with_connections,
                "users_in_narrative": users_in_narrative,
                "avg_fragments_completed": float(avg_completion),
                "timestamp": func.now()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas narrativas: {e}")
            return {
                "error": str(e),
                "total_fragments": 0,
                "active_fragments": 0,
                "users_in_narrative": 0
            }
    
    async def get_user_narrative_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene el progreso narrativo detallado de un usuario específico.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con progreso narrativo detallado
            
        Raises:
            ValueError: Si el usuario no tiene progreso narrativo
        """
        try:
            # Obtener estado narrativo del usuario
            query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(query)
            user_state = result.scalar_one_or_none()
            
            if not user_state:
                raise ValueError(f"Usuario con ID {user_id} no tiene progreso narrativo")
            
            # Obtener fragmento actual
            current_fragment = None
            if user_state.current_fragment_id:
                current_fragment_query = select(NarrativeFragment).where(
                    NarrativeFragment.id == user_state.current_fragment_id
                )
                current_fragment_result = await self.session.execute(current_fragment_query)
                current_fragment = current_fragment_result.scalar_one_or_none()
            
            # Contar fragmentos visitados y completados
            visited_count = len(user_state.visited_fragments)
            completed_count = len(user_state.completed_fragments)
            
            # Calcular porcentaje de progreso
            progress_percentage = await user_state.get_progress_percentage(self.session)
            
            # Obtener pistas desbloqueadas
            unlocked_clues = user_state.unlocked_clues
            
            current_fragment_data = None
            if current_fragment:
                current_fragment_data = {
                    "id": current_fragment.id,
                    "title": current_fragment.title,
                    "type": current_fragment.fragment_type
                }
            
            return {
                "user_id": user_id,
                "current_fragment": current_fragment_data,
                "visited_fragments_count": visited_count,
                "completed_fragments_count": completed_count,
                "progress_percentage": progress_percentage,
                "unlocked_clues": unlocked_clues,
                "visited_fragments": user_state.visited_fragments,
                "completed_fragments": user_state.completed_fragments
            }
            
        except ValueError as e:
            logger.error(f"Error de validación al obtener progreso: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo progreso narrativo del usuario: {e}")
            raise
    
    async def get_fragment_engagement(self, fragment_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de engagement para un fragmento específico.
        
        Args:
            fragment_id: ID único del fragmento
            
        Returns:
            Dict con estadísticas de engagement
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Usuarios que tienen este fragmento como actual
            active_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.current_fragment_id == fragment_id
            )
            active_result = await self.session.execute(active_query)
            active_users = active_result.scalar() or 0
            
            # Usuarios que han visitado este fragmento
            visited_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.visited_fragments.contains([fragment_id])
            )
            visited_result = await self.session.execute(visited_query)
            visited_users = visited_result.scalar() or 0
            
            # Usuarios que han completado este fragmento
            completed_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.completed_fragments.contains([fragment_id])
            )
            completed_result = await self.session.execute(completed_query)
            completed_users = completed_result.scalar() or 0
            
            # Tasa de finalización
            completion_rate = (completed_users / visited_users * 100) if visited_users > 0 else 0
            
            # Recopilación de datos sobre elecciones (si es fragmento de decisión)
            choice_stats = []
            if fragment.fragment_type == "DECISION" and fragment.choices:
                for i, choice in enumerate(fragment.choices):
                    # Para una estadística real, se debería implementar un sistema de seguimiento de elecciones
                    # Aquí es un placeholder que podrías completar más adelante
                    choice_stats.append({
                        "choice_index": i,
                        "choice_text": choice.get("text", f"Opción {i+1}"),
                        "target_fragment": choice.get("next_fragment"),
                        "times_chosen": 0,  # Placeholder
                        "percentage": 0  # Placeholder
                    })
            
            return {
                "fragment_id": fragment_id,
                "fragment_title": fragment.title,
                "fragment_type": fragment.fragment_type,
                "active_users": active_users,
                "visited_users": visited_users,
                "completed_users": completed_users,
                "completion_rate": completion_rate,
                "choice_stats": choice_stats
            }
            
        except ValueError as e:
            logger.error(f"Error de validación al obtener engagement: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de engagement: {e}")
            raise
    
    async def reset_user_narrative(self, user_id: int) -> bool:
        """
        Reinicia el progreso narrativo de un usuario específico.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si el progreso fue reiniciado correctamente
            
        Raises:
            ValueError: Si el usuario no tiene progreso narrativo
        """
        try:
            # Obtener estado narrativo del usuario
            query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(query)
            user_state = result.scalar_one_or_none()
            
            if not user_state:
                raise ValueError(f"Usuario con ID {user_id} no tiene progreso narrativo")
            
            # Borrar el estado actual
            await self.session.delete(user_state)
            
            # Crear nuevo estado vacío
            new_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[]
            )
            
            self.session.add(new_state)
            await self.session.commit()
            
            # Emitir evento de reinicio
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                user_id,
                {
                    "action": "user_narrative_reset",
                    "user_id": user_id
                },
                source="narrative_admin_service"
            )
            
            return True
            
        except ValueError as e:
            logger.error(f"Error de validación al reiniciar progreso: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reiniciando progreso narrativo: {e}")
            await self.session.rollback()
            raise