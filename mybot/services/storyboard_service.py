"""
Servicio para visualización y análisis de la estructura narrativa en forma de storyboard.
Permite representar gráficamente la estructura narrativa, analizar conexiones y generar mapas.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.narrative_unified import NarrativeFragment, UserNarrativeState

from services.narrative_admin_service import NarrativeAdminService

logger = logging.getLogger(__name__)

class StoryboardService:
    """
    Servicio para la visualización y análisis de la estructura narrativa.
    Genera representaciones visuales y analíticas del storyboard narrativo.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con la sesión de base de datos.
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.narrative_admin_service = NarrativeAdminService(session)
    
    async def generate_visualization_data(self, 
                                         root_fragment_id: Optional[str] = None, 
                                         max_depth: int = 3, 
                                         view_type: str = "tree") -> Dict[str, Any]:
        """
        Genera datos para visualización del storyboard.
        
        Args:
            root_fragment_id: ID del fragmento raíz (opcional, se busca uno si no se proporciona)
            max_depth: Profundidad máxima del árbol a generar
            view_type: Tipo de visualización ("tree", "flow" o "map")
            
        Returns:
            Dict con datos para la visualización
        """
        try:
            # Si no se proporciona ID de fragmento raíz, buscar uno
            if not root_fragment_id:
                # Intentar encontrar el fragmento con menos conexiones entrantes (probablemente es el inicio)
                start_fragments = await self._find_potential_start_fragments()
                if start_fragments:
                    root_fragment_id = start_fragments[0].get("id")
                else:
                    # Si no se encuentra, obtener cualquier fragmento activo
                    query = select(NarrativeFragment).where(
                        NarrativeFragment.is_active == True
                    ).limit(1)
                    result = await self.session.execute(query)
                    fragment = result.scalar_one_or_none()
                    
                    if fragment:
                        root_fragment_id = fragment.id
                    else:
                        return {"error": "No se encontraron fragmentos activos"}
            
            # Obtener fragmento raíz
            root_query = select(NarrativeFragment).where(NarrativeFragment.id == root_fragment_id)
            root_result = await self.session.execute(root_query)
            root_fragment = root_result.scalar_one_or_none()
            
            if not root_fragment:
                return {"error": f"Fragmento raíz con ID {root_fragment_id} no encontrado"}
            
            # Generar visualización según el tipo
            if view_type == "tree":
                return await self._generate_tree_visualization(root_fragment, max_depth)
            elif view_type == "flow":
                return await self._generate_flow_visualization(root_fragment, max_depth)
            elif view_type == "map":
                return await self._generate_map_visualization(root_fragment, max_depth)
            else:
                return {"error": f"Tipo de visualización '{view_type}' no soportado"}
            
        except Exception as e:
            logger.error(f"Error generando datos de visualización: {e}")
            return {"error": str(e)}
    
    async def get_fragment_tree(self, 
                               fragment_id: str, 
                               direction: str = "forward", 
                               depth: int = 2) -> Dict[str, Any]:
        """
        Obtiene el árbol de fragmentos en una dirección específica.
        
        Args:
            fragment_id: ID del fragmento central
            direction: Dirección del árbol ("forward", "backward" o "both")
            depth: Profundidad máxima del árbol
            
        Returns:
            Dict con árbol de fragmentos en la dirección especificada
        """
        try:
            # Obtener fragmento central
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                return {"error": f"Fragmento con ID {fragment_id} no encontrado"}
            
            # Inicializar resultado
            tree_data = {
                "fragment_id": fragment_id,
                "fragment_title": fragment.title,
                "fragment_type": fragment.fragment_type,
            }
            
            # Obtener árbol en direcciones solicitadas
            if direction in ["forward", "both"]:
                forward_tree = await self._get_forward_tree(fragment_id, depth)
                tree_data["forward_tree"] = forward_tree
            
            if direction in ["backward", "both"]:
                backward_tree = await self._get_backward_tree(fragment_id, depth)
                tree_data["backward_tree"] = backward_tree
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Error obteniendo árbol de fragmentos: {e}")
            return {"error": str(e)}
    
    async def generate_node_representation(self, fragment: NarrativeFragment) -> Dict[str, Any]:
        """
        Genera representación visual de un nodo de fragmento.
        
        Args:
            fragment: Objeto de fragmento narrativo
            
        Returns:
            Dict con representación visual del nodo
        """
        try:
            # Obtener estadísticas de usuario para este fragmento
            active_query = select(func.count()).select_from(UserNarrativeState).where(
                UserNarrativeState.current_fragment_id == fragment.id
            )
            active_result = await self.session.execute(active_query)
            active_users = active_result.scalar() or 0
            
            # Determinar estilo según tipo y estadísticas
            node_style = {
                "STORY": {"bgcolor": "#e6f7ff", "shape": "box", "border": "#1890ff"},
                "DECISION": {"bgcolor": "#fff7e6", "shape": "diamond", "border": "#fa8c16"},
                "INFO": {"bgcolor": "#f6ffed", "shape": "ellipse", "border": "#52c41a"}
            }.get(fragment.fragment_type, {"bgcolor": "#f0f0f0", "shape": "box", "border": "#d9d9d9"})
            
            # Aumentar importancia visual si hay usuarios activos
            if active_users > 0:
                node_style["border_width"] = 2
                node_style["highlight"] = True
            
            # Marcar inactivos con estilo específico
            if not fragment.is_active:
                node_style["opacity"] = 0.5
                node_style["dashed"] = True
            
            # Preparar representación
            node = {
                "id": fragment.id,
                "label": fragment.title,
                "type": fragment.fragment_type,
                "is_active": fragment.is_active,
                "style": node_style,
                "has_choices": bool(fragment.choices),
                "has_triggers": bool(fragment.triggers),
                "has_requirements": bool(fragment.required_clues),
                "active_users": active_users
            }
            
            return node
            
        except Exception as e:
            logger.error(f"Error generando representación de nodo: {e}")
            return {
                "id": fragment.id,
                "label": fragment.title,
                "type": fragment.fragment_type,
                "is_active": fragment.is_active,
                "style": {"bgcolor": "#f0f0f0", "shape": "box", "border": "#d9d9d9"},
                "error": str(e)
            }
    
    async def get_connection_statistics(self, fragment_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conexiones de un fragmento.
        
        Args:
            fragment_id: ID del fragmento
            
        Returns:
            Dict con estadísticas de conexiones del fragmento
            
        Raises:
            ValueError: Si el fragmento no existe
        """
        try:
            # Obtener conexiones del fragmento
            connections_data = await self.narrative_admin_service.get_fragment_connections(fragment_id)
            
            # Obtener detalles del fragmento
            fragment_details = await self.narrative_admin_service.get_fragment_details(fragment_id)
            
            # Inicializar estadísticas
            stats = {
                "fragment_id": fragment_id,
                "fragment_title": fragment_details["title"],
                "fragment_type": fragment_details["type"],
                "outgoing_count": len(connections_data.get("outgoing_connections", [])),
                "incoming_count": len(connections_data.get("incoming_connections", [])),
                "is_start": len(connections_data.get("incoming_connections", [])) == 0,
                "is_end": len(connections_data.get("outgoing_connections", [])) == 0,
                "connections": []
            }
            
            # Procesar cada conexión de salida
            for connection in connections_data.get("outgoing_connections", []):
                target_id = connection.get("id")
                
                # Para estadísticas reales, se necesitaría seguimiento de elecciones
                # Este es un placeholder que podría completarse después
                connection_stats = {
                    "target_id": target_id,
                    "target_title": connection.get("title"),
                    "choice_text": connection.get("choice_text"),
                    "is_active": connection.get("is_active", True),
                    "users_chosen": 0,  # Placeholder
                    "percentage": 0  # Placeholder
                }
                
                stats["connections"].append(connection_stats)
            
            return stats
            
        except ValueError as e:
            logger.error(f"Error de validación obteniendo estadísticas: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de conexiones: {e}")
            raise
    
    async def _find_potential_start_fragments(self) -> List[Dict[str, Any]]:
        """
        Encuentra fragmentos que podrían ser puntos de inicio de la narrativa.
        Busca fragmentos con pocas o ninguna conexión entrante.
        
        Returns:
            Lista de fragmentos potenciales de inicio
        """
        try:
            # Obtener todos los fragmentos activos
            fragment_query = select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            fragment_result = await self.session.execute(fragment_query)
            fragments = fragment_result.scalars().all()
            
            # Mapear IDs para búsqueda rápida
            fragment_map = {fragment.id: fragment for fragment in fragments}
            
            # Contabilizar conexiones entrantes para cada fragmento
            incoming_connections = {}
            for fragment in fragments:
                # Inicializar contador para cada fragmento
                if fragment.id not in incoming_connections:
                    incoming_connections[fragment.id] = 0
                
                # Contar conexiones salientes a otros fragmentos
                for choice in fragment.choices:
                    if "next_fragment" in choice:
                        target_id = choice["next_fragment"]
                        if target_id in incoming_connections:
                            incoming_connections[target_id] += 1
                        else:
                            incoming_connections[target_id] = 1
            
            # Ordenar fragmentos por número de conexiones entrantes
            sorted_fragments = sorted(
                [(fid, count) for fid, count in incoming_connections.items()],
                key=lambda x: x[1]
            )
            
            # Convertir a formato de respuesta
            result = []
            for fragment_id, count in sorted_fragments:
                if fragment_id in fragment_map:
                    fragment = fragment_map[fragment_id]
                    result.append({
                        "id": fragment.id,
                        "title": fragment.title,
                        "type": fragment.fragment_type,
                        "incoming_connections": count,
                        "is_active": fragment.is_active
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error encontrando fragmentos de inicio: {e}")
            return []
    
    async def _generate_tree_visualization(self, 
                                          root_fragment: NarrativeFragment, 
                                          max_depth: int) -> Dict[str, Any]:
        """
        Genera visualización en árbol del storyboard.
        
        Args:
            root_fragment: Fragmento raíz
            max_depth: Profundidad máxima
            
        Returns:
            Dict con datos para visualización en árbol
        """
        try:
            # Inicializar conjuntos para seguimiento
            processed_nodes = set()
            nodes = []
            edges = []
            
            # Procesar nodo raíz
            root_node = await self.generate_node_representation(root_fragment)
            nodes.append(root_node)
            processed_nodes.add(root_fragment.id)
            
            # Procesar árbol recursivamente
            await self._process_tree_node(root_fragment.id, nodes, edges, processed_nodes, 1, max_depth)
            
            return {
                "type": "tree",
                "root_id": root_fragment.id,
                "root_title": root_fragment.title,
                "nodes": nodes,
                "edges": edges,
                "max_depth": max_depth,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error generando visualización en árbol: {e}")
            return {"error": str(e)}
    
    async def _process_tree_node(self, 
                                node_id: str, 
                                nodes: List[Dict[str, Any]], 
                                edges: List[Dict[str, Any]], 
                                processed_nodes: Set[str], 
                                current_depth: int, 
                                max_depth: int) -> None:
        """
        Procesa un nodo del árbol recursivamente.
        
        Args:
            node_id: ID del nodo a procesar
            nodes: Lista de nodos procesados
            edges: Lista de conexiones procesadas
            processed_nodes: Conjunto de IDs de nodos ya procesados
            current_depth: Profundidad actual en el árbol
            max_depth: Profundidad máxima a procesar
        """
        # Detener si se alcanza la profundidad máxima
        if current_depth >= max_depth:
            return
        
        try:
            # Obtener fragmento
            query = select(NarrativeFragment).where(NarrativeFragment.id == node_id)
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                return
            
            # Procesar conexiones salientes
            for choice in fragment.choices:
                if "next_fragment" in choice:
                    target_id = choice["next_fragment"]
                    
                    # Añadir borde
                    edge = {
                        "id": f"{node_id}-{target_id}",
                        "from": node_id,
                        "to": target_id,
                        "label": choice.get("text", ""),
                        "has_requirements": bool(choice.get("requirements"))
                    }
                    edges.append(edge)
                    
                    # Procesar nodo destino si no se ha procesado ya
                    if target_id not in processed_nodes:
                        # Obtener fragmento destino
                        target_query = select(NarrativeFragment).where(NarrativeFragment.id == target_id)
                        target_result = await self.session.execute(target_query)
                        target_fragment = target_result.scalar_one_or_none()
                        
                        if target_fragment:
                            # Añadir nodo
                            target_node = await self.generate_node_representation(target_fragment)
                            nodes.append(target_node)
                            processed_nodes.add(target_id)
                            
                            # Procesar recursivamente
                            await self._process_tree_node(
                                target_id, nodes, edges, processed_nodes, 
                                current_depth + 1, max_depth
                            )
                        
        except Exception as e:
            logger.error(f"Error procesando nodo del árbol {node_id}: {e}")
    
    async def _generate_flow_visualization(self, 
                                          root_fragment: NarrativeFragment, 
                                          max_depth: int) -> Dict[str, Any]:
        """
        Genera visualización de flujo del storyboard.
        
        Args:
            root_fragment: Fragmento raíz
            max_depth: Profundidad máxima
            
        Returns:
            Dict con datos para visualización de flujo
        """
        try:
            # Para la visualización de flujo, usamos el mismo algoritmo que el árbol
            # pero con un diseño de jerarquía horizontal en lugar de vertical
            tree_data = await self._generate_tree_visualization(root_fragment, max_depth)
            
            # Modificar tipo
            tree_data["type"] = "flow"
            
            # Añadir metadatos específicos de flujo
            tree_data["direction"] = "LR"  # Izquierda a derecha
            tree_data["alignment"] = "hierarchical"
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Error generando visualización de flujo: {e}")
            return {"error": str(e)}
    
    async def _generate_map_visualization(self, 
                                         root_fragment: NarrativeFragment, 
                                         max_depth: int) -> Dict[str, Any]:
        """
        Genera visualización de mapa del storyboard.
        
        Args:
            root_fragment: Fragmento raíz
            max_depth: Profundidad máxima
            
        Returns:
            Dict con datos para visualización de mapa
        """
        try:
            # El mapa es similar al árbol, pero con un diseño en red no dirigida
            tree_data = await self._generate_tree_visualization(root_fragment, max_depth)
            
            # Modificar tipo
            tree_data["type"] = "map"
            
            # Añadir metadatos específicos de mapa
            tree_data["layout"] = "force"
            tree_data["physics"] = True
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Error generando visualización de mapa: {e}")
            return {"error": str(e)}
    
    async def _get_forward_tree(self, fragment_id: str, depth: int) -> Dict[str, Any]:
        """
        Obtiene árbol de fragmentos en dirección hacia adelante.
        
        Args:
            fragment_id: ID del fragmento inicial
            depth: Profundidad máxima
            
        Returns:
            Dict con árbol de fragmentos hacia adelante
        """
        # Usar el algoritmo de visualización de árbol pero limitando profundidad
        query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        result = await self.session.execute(query)
        fragment = result.scalar_one_or_none()
        
        if not fragment:
            return {"error": f"Fragmento con ID {fragment_id} no encontrado"}
        
        return await self._generate_tree_visualization(fragment, depth)
    
    async def _get_backward_tree(self, fragment_id: str, depth: int) -> Dict[str, Any]:
        """
        Obtiene árbol de fragmentos en dirección hacia atrás.
        
        Args:
            fragment_id: ID del fragmento final
            depth: Profundidad máxima
            
        Returns:
            Dict con árbol de fragmentos hacia atrás
        """
        try:
            # Inicializar conjuntos para seguimiento
            processed_nodes = set()
            nodes = []
            edges = []
            
            # Obtener fragmento central
            query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            result = await self.session.execute(query)
            target_fragment = result.scalar_one_or_none()
            
            if not target_fragment:
                return {"error": f"Fragmento con ID {fragment_id} no encontrado"}
            
            # Procesar nodo objetivo
            target_node = await self.generate_node_representation(target_fragment)
            nodes.append(target_node)
            processed_nodes.add(target_fragment.id)
            
            # Iniciar búsqueda inversa
            await self._process_backward_tree(fragment_id, nodes, edges, processed_nodes, 1, depth)
            
            return {
                "type": "backward_tree",
                "target_id": fragment_id,
                "target_title": target_fragment.title,
                "nodes": nodes,
                "edges": edges,
                "max_depth": depth,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error generando árbol hacia atrás: {e}")
            return {"error": str(e)}
    
    async def _process_backward_tree(self, 
                                    target_id: str, 
                                    nodes: List[Dict[str, Any]], 
                                    edges: List[Dict[str, Any]], 
                                    processed_nodes: Set[str], 
                                    current_depth: int, 
                                    max_depth: int) -> None:
        """
        Procesa un nodo del árbol inverso recursivamente.
        
        Args:
            target_id: ID del nodo objetivo
            nodes: Lista de nodos procesados
            edges: Lista de conexiones procesadas
            processed_nodes: Conjunto de IDs de nodos ya procesados
            current_depth: Profundidad actual en el árbol
            max_depth: Profundidad máxima a procesar
        """
        # Detener si se alcanza la profundidad máxima
        if current_depth >= max_depth:
            return
        
        try:
            # Obtener todos los fragmentos que apuntan al objetivo
            # Esto es ineficiente pero necesario dada la estructura actual
            query = select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            result = await self.session.execute(query)
            all_fragments = result.scalars().all()
            
            # Encontrar fragmentos que apuntan al objetivo
            for fragment in all_fragments:
                for choice in fragment.choices:
                    if "next_fragment" in choice and choice["next_fragment"] == target_id:
                        # Añadir borde
                        edge = {
                            "id": f"{fragment.id}-{target_id}",
                            "from": fragment.id,
                            "to": target_id,
                            "label": choice.get("text", ""),
                            "has_requirements": bool(choice.get("requirements"))
                        }
                        edges.append(edge)
                        
                        # Procesar nodo fuente si no se ha procesado ya
                        if fragment.id not in processed_nodes:
                            # Añadir nodo
                            source_node = await self.generate_node_representation(fragment)
                            nodes.append(source_node)
                            processed_nodes.add(fragment.id)
                            
                            # Procesar recursivamente
                            await self._process_backward_tree(
                                fragment.id, nodes, edges, processed_nodes, 
                                current_depth + 1, max_depth
                            )
                        
        except Exception as e:
            logger.error(f"Error procesando nodo del árbol inverso {target_id}: {e}")
    
    # ==================== MÉTODOS DE ANÁLISIS ====================
    
    async def analyze_story_structure(self) -> Dict[str, Any]:
        """
        Analiza la estructura global de la historia.
        
        Returns:
            Dict con análisis de la estructura de la historia
        """
        try:
            # Obtener todos los fragmentos activos
            query = select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            result = await self.session.execute(query)
            fragments = result.scalars().all()
            
            # Inicializar contadores
            total_fragments = len(fragments)
            fragment_types = {"STORY": 0, "DECISION": 0, "INFO": 0}
            total_choices = 0
            total_requirements = 0
            total_triggers = 0
            
            # Estructuras para análisis de conectividad
            fragment_ids = set()
            connections = {}
            incoming = {}
            outgoing = {}
            
            # Procesar cada fragmento
            for fragment in fragments:
                # Contabilizar por tipo
                if fragment.fragment_type in fragment_types:
                    fragment_types[fragment.fragment_type] += 1
                
                # Recopilar ID para análisis de conectividad
                fragment_ids.add(fragment.id)
                
                # Contar requisitos y triggers
                if fragment.required_clues:
                    total_requirements += len(fragment.required_clues)
                    
                if fragment.triggers and any(fragment.triggers.values()):
                    total_triggers += 1
                
                # Contabilizar conexiones salientes
                outgoing_count = len(fragment.choices)
                total_choices += outgoing_count
                outgoing[fragment.id] = outgoing_count
                
                # Registrar conexiones para análisis
                connections[fragment.id] = []
                if fragment.id not in incoming:
                    incoming[fragment.id] = 0
                
                # Procesar cada elección
                for choice in fragment.choices:
                    if "next_fragment" in choice:
                        target_id = choice["next_fragment"]
                        connections[fragment.id].append(target_id)
                        
                        # Incrementar contador de conexiones entrantes
                        if target_id in incoming:
                            incoming[target_id] += 1
                        else:
                            incoming[target_id] = 1
            
            # Identificar puntos de inicio y fin
            start_points = [fid for fid in fragment_ids if fid not in incoming or incoming[fid] == 0]
            end_points = [fid for fid in fragment_ids if fid not in outgoing or outgoing[fid] == 0]
            
            # Identificar caminos muertos (fragmentos sin salida)
            dead_ends = [fid for fid in fragment_ids if fid not in outgoing or outgoing[fid] == 0 and incoming[fid] > 0]
            
            # Identificar fragmentos desconectados
            disconnected = [fid for fid in fragment_ids if (fid not in incoming or incoming[fid] == 0) and (fid not in outgoing or outgoing[fid] == 0)]
            
            # Métricas de estructura
            avg_choices_per_decision = 0
            if fragment_types["DECISION"] > 0:
                avg_choices_per_decision = total_choices / fragment_types["DECISION"]
            
            # Calcular relación historia/decisión
            story_decision_ratio = 0
            if fragment_types["DECISION"] > 0:
                story_decision_ratio = fragment_types["STORY"] / fragment_types["DECISION"]
            
            return {
                "total_fragments": total_fragments,
                "fragment_types": fragment_types,
                "total_choices": total_choices,
                "total_requirements": total_requirements,
                "total_triggers": total_triggers,
                "connectivity": {
                    "start_points": len(start_points),
                    "end_points": len(end_points),
                    "dead_ends": len(dead_ends),
                    "disconnected": len(disconnected)
                },
                "metrics": {
                    "avg_choices_per_decision": avg_choices_per_decision,
                    "story_decision_ratio": story_decision_ratio,
                    "complexity_score": total_choices * total_requirements / (total_fragments if total_fragments > 0 else 1)
                },
                "potential_issues": {
                    "no_start_points": len(start_points) == 0,
                    "no_end_points": len(end_points) == 0,
                    "too_many_dead_ends": len(dead_ends) > total_fragments * 0.2,
                    "disconnected_fragments": len(disconnected) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analizando estructura de historia: {e}")
            return {"error": str(e)}
    
    async def find_optimal_path(self, start_id: str, end_id: str) -> Dict[str, Any]:
        """
        Encuentra el camino óptimo entre dos fragmentos.
        
        Args:
            start_id: ID del fragmento inicial
            end_id: ID del fragmento final
            
        Returns:
            Dict con camino óptimo entre los fragmentos
            
        Raises:
            ValueError: Si alguno de los fragmentos no existe
        """
        try:
            # Verificar que ambos fragmentos existen
            for fragment_id in [start_id, end_id]:
                query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
                result = await self.session.execute(query)
                if not result.scalar_one_or_none():
                    raise ValueError(f"Fragmento con ID {fragment_id} no encontrado")
            
            # Obtener todos los fragmentos activos
            query = select(NarrativeFragment).where(NarrativeFragment.is_active == True)
            result = await self.session.execute(query)
            fragments = result.scalars().all()
            
            # Construir grafo
            graph = {}
            for fragment in fragments:
                graph[fragment.id] = []
                for choice in fragment.choices:
                    if "next_fragment" in choice:
                        graph[fragment.id].append(choice["next_fragment"])
            
            # Buscar camino con BFS
            path = await self._bfs_shortest_path(graph, start_id, end_id)
            
            if not path:
                return {
                    "found": False,
                    "message": "No hay camino entre los fragmentos especificados"
                }
            
            # Obtener detalles de cada fragmento en el camino
            path_details = []
            for fragment_id in path:
                query = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
                result = await self.session.execute(query)
                fragment = result.scalar_one_or_none()
                
                if fragment:
                    path_details.append({
                        "id": fragment.id,
                        "title": fragment.title,
                        "type": fragment.fragment_type
                    })
            
            return {
                "found": True,
                "path_length": len(path) - 1,  # Número de pasos (aristas)
                "path": path,
                "path_details": path_details
            }
            
        except ValueError as e:
            logger.error(f"Error de validación en búsqueda de camino: {e}")
            raise
        except Exception as e:
            logger.error(f"Error encontrando camino óptimo: {e}")
            return {"error": str(e)}
    
    async def _bfs_shortest_path(self, 
                                graph: Dict[str, List[str]], 
                                start: str, 
                                end: str) -> List[str]:
        """
        Encuentra el camino más corto entre dos nodos usando BFS.
        
        Args:
            graph: Diccionario con el grafo de conexiones
            start: ID del nodo inicial
            end: ID del nodo final
            
        Returns:
            Lista con los IDs de los nodos en el camino más corto
        """
        # Verificar casos especiales
        if start == end:
            return [start]
            
        if start not in graph or end not in graph:
            return []
        
        # Inicializar BFS
        visited = {start}
        queue = [(start, [start])]
        
        while queue:
            (vertex, path) = queue.pop(0)
            
            # Procesar vecinos no visitados
            for next_vertex in graph.get(vertex, []):
                if next_vertex == end:
                    return path + [next_vertex]
                    
                if next_vertex not in visited:
                    visited.add(next_vertex)
                    queue.append((next_vertex, path + [next_vertex]))
        
        # No se encontró camino
        return []