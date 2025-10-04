"""
Servicio para tracking de métricas de UX y engagement
STRATEGIC: Sistema de monitoreo para validar mejoras
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class MetricsService:
    """Servicio para tracking y análisis de métricas de usuario"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def record_interaction(self, user_id: int, interaction_type: str, data: Dict = None):
        """Registra una interacción del usuario para análisis"""
        try:
            from database.models import UserInteraction
            
            interaction = UserInteraction(
                user_id=user_id,
                interaction_type=interaction_type,
                timestamp=datetime.utcnow(),
                data=data or {}
            )
            self.session.add(interaction)
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error registrando interacción: {e}")
            await self.session.rollback()
    
    async def get_engagement_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Obtiene métricas de engagement para los últimos N días"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Métricas básicas de engagement
            stmt = select(
                func.count(UserInteraction.id).label("total_interactions"),
                func.count(func.distinct(UserInteraction.user_id)).label("active_users"),
                func.avg(
                    select(func.count(UserInteraction.id))
                    .where(UserInteraction.user_id == UserInteraction.user_id)
                    .scalar_subquery()
                ).label("avg_interactions_per_user")
            ).where(UserInteraction.timestamp >= start_date)
            
            result = await self.session.execute(stmt)
            metrics = result.first()
            
            # Distribución por tipo de interacción
            type_stmt = select(
                UserInteraction.interaction_type,
                func.count(UserInteraction.id).label("count")
            ).where(
                UserInteraction.timestamp >= start_date
            ).group_by(UserInteraction.interaction_type)
            
            type_result = await self.session.execute(type_stmt)
            type_distribution = {row[0]: row[1] for row in type_result}
            
            return {
                "period_days": days,
                "total_interactions": metrics.total_interactions or 0,
                "active_users": metrics.active_users or 0,
                "avg_interactions_per_user": round(float(metrics.avg_interactions_per_user or 0), 2),
                "interaction_types": type_distribution,
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de engagement: {e}")
            return {}
    
    async def get_onboarding_funnel(self) -> Dict[str, Any]:
        """Obtiene métricas del funnel de onboarding"""
        try:
            from database.models import UserMilestone
            
            # Contar usuarios por paso de onboarding completado
            funnel_steps = [
                "onboarding_welcome",
                "onboarding_narrative_intro", 
                "onboarding_missions_intro",
                "onboarding_points_explained",
                "onboarding_first_interaction",
                "onboarding_complete"
            ]
            
            funnel_data = {}
            for step in funnel_steps:
                stmt = select(func.count(UserMilestone.id)).where(
                    UserMilestone.milestone_type == step,
                    UserMilestone.completed == True
                )
                result = await self.session.execute(stmt)
                count = result.scalar() or 0
                funnel_data[step] = count
            
            return {
                "funnel_steps": funnel_data,
                "total_users": await self._get_total_users(),
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo funnel de onboarding: {e}")
            return {}
    
    async def _get_total_users(self) -> int:
        """Obtiene el total de usuarios registrados"""
        from database.models import User
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
