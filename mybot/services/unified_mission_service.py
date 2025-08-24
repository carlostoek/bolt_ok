"""
Servicio de misiones unificado para DianaBot.
Maneja la lógica de misiones, progreso, y recompensas integradas con el sistema narrativo.
"""

import logging
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.future import select

from database.models import User, LorePiece, UserLorePiece
from database.mission_unified import UnifiedMission, UserMissionProgress
from database.narrative_unified import NarrativeFragment, UserNarrativeState

logger = logging.getLogger(__name__)

class UnifiedMissionService:
    """Servicio principal para el sistema de misiones unificado."""
    
    def __init__(self, session: AsyncSession, bot=None):
        """Inicializa el servicio de misiones unificado.
        
        Args:
            session (AsyncSession): Sesión de base de datos
            bot: Instancia del bot de Telegram (opcional)
        """
        self.session = session
        self.bot = bot
        
    async def get_all_missions(self, 
                         mission_type: str = None,
                         active_only: bool = True,
                         user_id: int = None) -> List[UnifiedMission]:
        """Obtiene todas las misiones disponibles, opcionalmente filtradas por tipo.
        
        Args:
            mission_type (str, optional): Tipo de misión para filtrar
            active_only (bool): Solo misiones activas si es True
            user_id (int, optional): ID del usuario para verificar disponibilidad
            
        Returns:
            List[UnifiedMission]: Lista de misiones que cumplen los criterios
        """
        query = select(UnifiedMission)
        
        if active_only:
            query = query.where(UnifiedMission.is_active == True)
            
        if mission_type:
            query = query.where(UnifiedMission.mission_type == mission_type)
            
        # Ordenar por orden y luego por fecha de creación
        query = query.order_by(UnifiedMission.order, UnifiedMission.created_at)
        
        result = await self.session.execute(query)
        missions = result.scalars().all()
        
        # Si se proporciona un ID de usuario, filtrar misiones por disponibilidad
        if user_id:
            available_missions = []
            for mission in missions:
                is_available = await self._check_mission_availability(user_id, mission)
                if is_available:
                    available_missions.append(mission)
            return available_missions
            
        return missions
    
    async def get_user_available_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene todas las misiones disponibles para un usuario con su progreso.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            List[Dict]: Lista de misiones con información de progreso
        """
        missions = await self.get_all_missions(active_only=True, user_id=user_id)
        result = []
        
        for mission in missions:
            progress = await self.get_mission_progress(user_id, mission.id)
            mission_data = {
                "id": mission.id,
                "title": mission.title,
                "description": mission.description,
                "mission_type": mission.mission_type,
                "objectives": mission.objectives,
                "is_completed": progress.is_completed if progress else False,
                "progress_percentage": progress.get_completion_percentage() if progress else 0,
                "rewards": mission.rewards
            }
            result.append(mission_data)
            
        return result
    
    async def get_mission_by_id(self, mission_id: str) -> Optional[UnifiedMission]:
        """Obtiene una misión por su ID.
        
        Args:
            mission_id (str): ID de la misión
            
        Returns:
            Optional[UnifiedMission]: Misión encontrada o None
        """
        return await self.session.get(UnifiedMission, mission_id)
    
    async def get_mission_progress(self, 
                             user_id: int, 
                             mission_id: str) -> Optional[UserMissionProgress]:
        """Obtiene el progreso de un usuario en una misión específica.
        
        Args:
            user_id (int): ID del usuario
            mission_id (str): ID de la misión
            
        Returns:
            Optional[UserMissionProgress]: Progreso del usuario o None
        """
        query = select(UserMissionProgress).where(
            UserMissionProgress.user_id == user_id,
            UserMissionProgress.mission_id == mission_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_mission(self,
                       title: str,
                       description: str,
                       mission_type: str,
                       objectives: List[Dict[str, Any]],
                       requirements: Dict[str, Any],
                       rewards: Dict[str, Any],
                       is_active: bool = True,
                       is_repeatable: bool = False,
                       duration_days: int = 0,
                       cooldown_hours: int = 0,
                       order: int = 0) -> UnifiedMission:
        """Crea una nueva misión unificada.
        
        Args:
            title (str): Título de la misión
            description (str): Descripción de la misión
            mission_type (str): Tipo de misión (MAIN, SIDE, DAILY, WEEKLY, EVENT)
            objectives (List[Dict]): Lista de objetivos visibles para el usuario
            requirements (Dict): Requisitos para completar la misión
            rewards (Dict): Recompensas por completar la misión
            is_active (bool): Si la misión está activa
            is_repeatable (bool): Si la misión es repetible
            duration_days (int): Duración en días (0 = sin límite)
            cooldown_hours (int): Tiempo de espera para repetir la misión
            order (int): Orden de la misión
            
        Returns:
            UnifiedMission: La misión creada
        """
        # Validar el tipo de misión
        valid_types = ['MAIN', 'SIDE', 'DAILY', 'WEEKLY', 'EVENT']
        if mission_type not in valid_types:
            raise ValueError(f"Tipo de misión inválido. Debe ser uno de: {', '.join(valid_types)}")
        
        # Crear la misión
        mission = UnifiedMission(
            title=title,
            description=description,
            mission_type=mission_type,
            objectives=objectives,
            requirements=requirements,
            rewards=rewards,
            is_active=is_active,
            is_repeatable=is_repeatable,
            duration_days=duration_days,
            cooldown_hours=cooldown_hours,
            order=order
        )
        
        # Si es una misión con duración, establecer la fecha de expiración
        if duration_days > 0:
            mission.expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=duration_days)
            
        self.session.add(mission)
        await self.session.commit()
        await self.session.refresh(mission)
        
        logger.info(f"Misión creada: {mission.id} - {mission.title}")
        return mission
    
    async def update_mission_status(self, mission_id: str, is_active: bool) -> bool:
        """Actualiza el estado de una misión.
        
        Args:
            mission_id (str): ID de la misión
            is_active (bool): Nuevo estado de activación
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        mission = await self.get_mission_by_id(mission_id)
        if not mission:
            return False
            
        mission.is_active = is_active
        mission.updated_at = datetime.datetime.utcnow()
        
        await self.session.commit()
        logger.info(f"Estado de misión {mission_id} actualizado a: {'activa' if is_active else 'inactiva'}")
        return True
    
    async def update_user_progress(self, 
                             user_id: int,
                             action_type: str,
                             action_data: Dict[str, Any]) -> List[Tuple[UnifiedMission, bool]]:
        """Actualiza el progreso del usuario en todas las misiones afectadas por una acción.
        
        Args:
            user_id (int): ID del usuario
            action_type (str): Tipo de acción realizada
            action_data (Dict): Datos adicionales de la acción
            
        Returns:
            List[Tuple[UnifiedMission, bool]]: Lista de tuplas (misión, completada_ahora)
        """
        # Obtener todas las misiones activas
        missions = await self.get_all_missions(active_only=True)
        completed_missions = []
        
        # Verificar cada misión si puede ser afectada por esta acción
        for mission in missions:
            # Obtener o crear progreso del usuario
            progress = await self._get_or_create_progress(user_id, mission.id)
            
            # Si ya está completada y no es repetible, continuar
            if progress.is_completed and not mission.is_repeatable:
                continue
                
            # Si es repetible pero está en cooldown, continuar
            if mission.is_repeatable and progress.is_completed and mission.cooldown_hours > 0:
                if progress.completed_at:
                    cooldown_time = progress.completed_at + datetime.timedelta(hours=mission.cooldown_hours)
                    if datetime.datetime.utcnow() < cooldown_time:
                        continue
            
            # Actualizar progreso según el tipo de acción
            progress_updated = False
            
            if action_type == "narrative_fragment":
                fragment_id = action_data.get("fragment_id")
                if fragment_id and "narrative_fragments" in mission.requirements:
                    if fragment_id in mission.requirements["narrative_fragments"]:
                        # Actualizar progreso
                        if "narrative_fragments" not in progress.progress_data:
                            progress.progress_data["narrative_fragments"] = []
                        if fragment_id not in progress.progress_data["narrative_fragments"]:
                            progress.progress_data["narrative_fragments"].append(fragment_id)
                            progress_updated = True
                            
            elif action_type == "lore_piece":
                piece_code = action_data.get("piece_code")
                if piece_code and "lore_pieces" in mission.requirements:
                    if piece_code in mission.requirements["lore_pieces"]:
                        # Actualizar progreso
                        if "lore_pieces" not in progress.progress_data:
                            progress.progress_data["lore_pieces"] = []
                        if piece_code not in progress.progress_data["lore_pieces"]:
                            progress.progress_data["lore_pieces"].append(piece_code)
                            progress_updated = True
                            
            elif action_type in ["reaction", "checkin", "message", "login"]:
                if "actions" in mission.requirements:
                    for action_req in mission.requirements["actions"]:
                        if action_req.get("type") == action_type:
                            # Actualizar contador de acciones
                            if "actions" not in progress.progress_data:
                                progress.progress_data["actions"] = {}
                            if action_type not in progress.progress_data["actions"]:
                                progress.progress_data["actions"][action_type] = 0
                                
                            # Incrementar contador
                            increment = action_data.get("increment", 1)
                            progress.progress_data["actions"][action_type] += increment
                            progress_updated = True
            
            # Si se actualizó el progreso, verificar si la misión está completada
            if progress_updated:
                progress.updated_at = datetime.datetime.utcnow()
                was_completed = progress.is_completed
                is_completed_now = await self._check_mission_completion(user_id, mission.id, progress)
                
                if is_completed_now and not was_completed:
                    completed_missions.append((mission, True))
                
                await self.session.commit()
                
        return completed_missions
    
    async def complete_mission(self, user_id: int, mission_id: str) -> Tuple[bool, Optional[UnifiedMission]]:
        """Marca una misión como completada manualmente y otorga recompensas.
        
        Args:
            user_id (int): ID del usuario
            mission_id (str): ID de la misión
            
        Returns:
            Tuple[bool, Optional[UnifiedMission]]: (éxito, misión)
        """
        mission = await self.get_mission_by_id(mission_id)
        if not mission or not mission.is_active:
            logger.warning(f"Misión {mission_id} no encontrada o inactiva")
            return False, None
            
        progress = await self._get_or_create_progress(user_id, mission_id)
        
        # Si ya está completada y no es repetible, no hacer nada
        if progress.is_completed and not mission.is_repeatable:
            logger.info(f"Misión {mission_id} ya completada por usuario {user_id}")
            return False, mission
            
        # Si es repetible pero está en cooldown, verificar
        if mission.is_repeatable and progress.is_completed and mission.cooldown_hours > 0:
            if progress.completed_at:
                cooldown_time = progress.completed_at + datetime.timedelta(hours=mission.cooldown_hours)
                if datetime.datetime.utcnow() < cooldown_time:
                    logger.info(f"Misión {mission_id} en cooldown para usuario {user_id}")
                    return False, mission
        
        # Marcar como completada
        progress.is_completed = True
        progress.completed_at = datetime.datetime.utcnow()
        progress.times_completed += 1
        
        # Otorgar recompensas
        await self._grant_mission_rewards(user_id, mission)
        
        await self.session.commit()
        logger.info(f"Misión {mission_id} completada por usuario {user_id}")
        
        # Enviar notificación si hay bot disponible
        if self.bot:
            await self._send_mission_completed_notification(user_id, mission)
            
        return True, mission
    
    async def reset_mission_progress(self, 
                                user_id: int, 
                                mission_id: str) -> bool:
        """Reinicia el progreso de un usuario en una misión.
        
        Args:
            user_id (int): ID del usuario
            mission_id (str): ID de la misión
            
        Returns:
            bool: True si se reinició correctamente, False en caso contrario
        """
        progress = await self.get_mission_progress(user_id, mission_id)
        if not progress:
            return False
            
        # Reiniciar progreso
        progress.progress_data = {}
        progress.is_completed = False
        progress.completed_at = None
        progress.updated_at = datetime.datetime.utcnow()
        
        await self.session.commit()
        logger.info(f"Progreso de misión {mission_id} reiniciado para usuario {user_id}")
        return True
    
    async def reset_daily_missions(self) -> int:
        """Reinicia todas las misiones diarias completadas.
        
        Returns:
            int: Número de misiones reiniciadas
        """
        # Obtener todas las misiones diarias
        daily_missions = await self.get_all_missions(mission_type="DAILY")
        mission_ids = [mission.id for mission in daily_missions]
        
        if not mission_ids:
            return 0
            
        # Obtener todos los progresos completados para estas misiones
        query = select(UserMissionProgress).where(
            UserMissionProgress.mission_id.in_(mission_ids),
            UserMissionProgress.is_completed == True
        )
        result = await self.session.execute(query)
        progress_records = result.scalars().all()
        
        # Reiniciar cada progreso
        count = 0
        for progress in progress_records:
            progress.progress_data = {}
            progress.is_completed = False
            progress.completed_at = None
            progress.last_reset_at = datetime.datetime.utcnow()
            count += 1
            
        await self.session.commit()
        logger.info(f"Reiniciadas {count} misiones diarias")
        return count
    
    async def reset_weekly_missions(self) -> int:
        """Reinicia todas las misiones semanales completadas.
        
        Returns:
            int: Número de misiones reiniciadas
        """
        # Obtener todas las misiones semanales
        weekly_missions = await self.get_all_missions(mission_type="WEEKLY")
        mission_ids = [mission.id for mission in weekly_missions]
        
        if not mission_ids:
            return 0
            
        # Obtener todos los progresos completados para estas misiones
        query = select(UserMissionProgress).where(
            UserMissionProgress.mission_id.in_(mission_ids),
            UserMissionProgress.is_completed == True
        )
        result = await self.session.execute(query)
        progress_records = result.scalars().all()
        
        # Reiniciar cada progreso
        count = 0
        for progress in progress_records:
            progress.progress_data = {}
            progress.is_completed = False
            progress.completed_at = None
            progress.last_reset_at = datetime.datetime.utcnow()
            count += 1
            
        await self.session.commit()
        logger.info(f"Reiniciadas {count} misiones semanales")
        return count
    
    async def _get_or_create_progress(self, 
                                 user_id: int, 
                                 mission_id: str) -> UserMissionProgress:
        """Obtiene o crea un registro de progreso para un usuario y misión.
        
        Args:
            user_id (int): ID del usuario
            mission_id (str): ID de la misión
            
        Returns:
            UserMissionProgress: Registro de progreso
        """
        progress = await self.get_mission_progress(user_id, mission_id)
        
        if not progress:
            progress = UserMissionProgress(
                user_id=user_id,
                mission_id=mission_id,
                progress_data={},
                is_completed=False,
                times_completed=0
            )
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
            
        return progress
    
    async def _check_mission_completion(self, 
                                   user_id: int, 
                                   mission_id: str,
                                   progress: UserMissionProgress = None) -> bool:
        """Verifica si una misión ha sido completada por un usuario.
        
        Args:
            user_id (int): ID del usuario
            mission_id (str): ID de la misión
            progress (UserMissionProgress, optional): Registro de progreso si ya está cargado
            
        Returns:
            bool: True si la misión está completada, False en caso contrario
        """
        if not progress:
            progress = await self.get_mission_progress(user_id, mission_id)
            if not progress:
                return False
                
        mission = await self.get_mission_by_id(mission_id)
        if not mission:
            return False
            
        # Si ya está marcada como completada, retornar directamente
        if progress.is_completed:
            return True
            
        requirements = mission.requirements or {}
        progress_data = progress.progress_data or {}
        
        # Verificar fragmentos narrativos requeridos
        if "narrative_fragments" in requirements:
            req_fragments = requirements["narrative_fragments"]
            prog_fragments = progress_data.get("narrative_fragments", [])
            
            # Verificar que todos los fragmentos requeridos estén en el progreso
            if not all(fragment in prog_fragments for fragment in req_fragments):
                return False
                
        # Verificar pistas de lore requeridas
        if "lore_pieces" in requirements:
            req_pieces = requirements["lore_pieces"]
            prog_pieces = progress_data.get("lore_pieces", [])
            
            # Verificar que todas las pistas requeridas estén en el progreso
            if not all(piece in prog_pieces for piece in req_pieces):
                return False
                
        # Verificar acciones requeridas
        if "actions" in requirements:
            for action_req in requirements["actions"]:
                action_type = action_req.get("type")
                req_count = action_req.get("count", 1)
                
                if not action_type:
                    continue
                    
                prog_actions = progress_data.get("actions", {})
                prog_count = prog_actions.get(action_type, 0)
                
                # Verificar que el contador actual sea al menos el requerido
                if prog_count < req_count:
                    return False
                    
        # Verificar submisiones requeridas
        if "missions" in requirements:
            req_missions = requirements["missions"]
            
            # Verificar que todas las submisiones estén completadas
            for sub_mission_id in req_missions:
                sub_progress = await self.get_mission_progress(user_id, sub_mission_id)
                if not sub_progress or not sub_progress.is_completed:
                    return False
        
        # Si llegamos aquí, todos los requisitos se cumplen
        # Marcar como completada
        progress.is_completed = True
        progress.completed_at = datetime.datetime.utcnow()
        progress.times_completed += 1
        
        # Otorgar recompensas
        await self._grant_mission_rewards(user_id, mission)
        
        # Enviar notificación si hay bot disponible
        if self.bot:
            await self._send_mission_completed_notification(user_id, mission)
            
        return True
    
    async def _check_mission_availability(self, user_id: int, mission: UnifiedMission) -> bool:
        """Verifica si una misión está disponible para un usuario.
        
        Args:
            user_id (int): ID del usuario
            mission (UnifiedMission): Misión a verificar
            
        Returns:
            bool: True si la misión está disponible, False en caso contrario
        """
        # Verificar si la misión está activa
        if not mission.is_active:
            return False
            
        # Verificar fecha de expiración
        if mission.expiration_date and datetime.datetime.utcnow() > mission.expiration_date:
            return False
            
        # Obtener progreso del usuario
        progress = await self.get_mission_progress(user_id, mission.id)
        
        # Si no hay progreso, la misión está disponible
        if not progress:
            return True
            
        # Si la misión ya está completada y no es repetible, no está disponible
        if progress.is_completed and not mission.is_repeatable:
            return False
            
        # Si la misión es repetible pero está en cooldown, verificar
        if progress.is_completed and mission.is_repeatable and mission.cooldown_hours > 0:
            if progress.completed_at:
                cooldown_time = progress.completed_at + datetime.timedelta(hours=mission.cooldown_hours)
                if datetime.datetime.utcnow() < cooldown_time:
                    return False
                    
        return True
    
    async def _grant_mission_rewards(self, user_id: int, mission: UnifiedMission) -> None:
        """Otorga las recompensas de una misión a un usuario.
        
        Args:
            user_id (int): ID del usuario
            mission (UnifiedMission): Misión completada
        """
        rewards = mission.rewards or {}
        
        try:
            # Intentar usar el sistema de recompensas unificado
            from services.reward_service import RewardSystem
            reward_system = RewardSystem(self.session)
            
            # Otorgar puntos
            if "points" in rewards and rewards["points"] > 0:
                await reward_system.grant_reward(
                    user_id=user_id,
                    reward_type="points",
                    reward_data={
                        "amount": rewards["points"],
                        "description": f"Recompensa por misión: {mission.title}"
                    },
                    source="unified_mission"
                )
                logger.info(f"Otorgados {rewards['points']} puntos al usuario {user_id} por misión {mission.id}")
                
            # Otorgar pistas de lore
            if "lore_pieces" in rewards and rewards["lore_pieces"]:
                for piece_code in rewards["lore_pieces"]:
                    await reward_system.grant_reward(
                        user_id=user_id,
                        reward_type="clue",
                        reward_data={
                            "clue_code": piece_code,
                            "description": f"Pista desbloqueada por misión: {mission.title}"
                        },
                        source="unified_mission"
                    )
                    logger.info(f"Desbloqueada pista {piece_code} para usuario {user_id} por misión {mission.id}")
                    
            # Otorgar badges (si se implementa en el futuro)
            if "badges" in rewards and rewards["badges"]:
                for badge_id in rewards["badges"]:
                    await reward_system.grant_reward(
                        user_id=user_id,
                        reward_type="badge",
                        reward_data={
                            "badge_id": badge_id,
                            "description": f"Insignia desbloqueada por misión: {mission.title}"
                        },
                        source="unified_mission"
                    )
                    logger.info(f"Otorgada insignia {badge_id} a usuario {user_id} por misión {mission.id}")
                    
        except ImportError:
            # Fallback a métodos tradicionales si el sistema unificado no está disponible
            logger.warning("Sistema de recompensas unificado no disponible, usando métodos tradicionales")
            
            # Otorgar puntos
            if "points" in rewards and rewards["points"] > 0:
                from services.point_service import PointService
                point_service = PointService(self.session)
                await point_service.add_points(
                    user_id, 
                    rewards["points"], 
                    reason=f"Misión completada: {mission.title}",
                    bot=self.bot
                )
                
            # Otorgar pistas de lore
            if "lore_pieces" in rewards and rewards["lore_pieces"]:
                for piece_code in rewards["lore_pieces"]:
                    # Buscar la pista
                    piece_stmt = select(LorePiece).where(LorePiece.code_name == piece_code)
                    piece_result = await self.session.execute(piece_stmt)
                    piece = piece_result.scalar_one_or_none()
                    
                    if piece:
                        # Verificar si ya está desbloqueada
                        check_stmt = select(UserLorePiece).where(
                            UserLorePiece.user_id == user_id,
                            UserLorePiece.lore_piece_id == piece.id
                        )
                        exists = (await self.session.execute(check_stmt)).scalar_one_or_none()
                        
                        if not exists:
                            # Desbloquear pista
                            self.session.add(UserLorePiece(
                                user_id=user_id,
                                lore_piece_id=piece.id
                            ))
                            
            await self.session.commit()
    
    async def _send_mission_completed_notification(self, user_id: int, mission: UnifiedMission) -> None:
        """Envía una notificación al usuario cuando completa una misión.
        
        Args:
            user_id (int): ID del usuario
            mission (UnifiedMission): Misión completada
        """
        try:
            # Usar servicio de notificaciones unificadas si está disponible
            from services.notification_service import NotificationService, NotificationPriority
            
            notification_service = NotificationService(self.session, self.bot)
            
            # Preparar datos de recompensas para la notificación
            rewards_data = {}
            if "points" in mission.rewards:
                rewards_data["points"] = mission.rewards["points"]
            if "lore_pieces" in mission.rewards:
                rewards_data["lore_pieces"] = len(mission.rewards["lore_pieces"])
            if "badges" in mission.rewards:
                rewards_data["badges"] = len(mission.rewards["badges"])
                
            await notification_service.add_notification(
                user_id,
                "mission_completed",
                {
                    "mission_id": mission.id,
                    "title": mission.title,
                    "description": mission.description,
                    "rewards": rewards_data
                },
                priority=NotificationPriority.MEDIUM
            )
            
            logger.info(f"Enviada notificación unificada de misión completada a usuario {user_id}")
            
        except ImportError:
            # Fallback al método anterior si no está disponible el servicio unificado
            from utils.message_utils import get_mission_completed_message
            from utils.keyboard_utils import get_mission_completed_keyboard
            
            # Adaptar mensaje para misión unificada
            points_text = f"{mission.rewards.get('points', 0)} puntos" if mission.rewards.get("points") else "sin puntos"
            
            # Enviar mensaje directo
            await self.bot.send_message(
                user_id,
                f"🎯 ¡Misión Completada! 🎯\n\n"
                f"*{mission.title}*\n\n"
                f"{mission.description}\n\n"
                f"💰 Recompensa: {points_text}",
                reply_markup=get_mission_completed_keyboard(),
                parse_mode="Markdown"
            )
            
            logger.info(f"Enviada notificación directa de misión completada a usuario {user_id}")