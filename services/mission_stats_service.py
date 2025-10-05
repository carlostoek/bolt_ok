"""
Servicio de estadísticas de misiones

Proporciona analytics y métricas sobre el desempeño de las misiones.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import Mission, User, UserMissionEntry

logger = logging.getLogger(__name__)


class MissionStatsService:
    """Servicio para obtener estadísticas de misiones"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_mission_stats(self, mission_id: str) -> dict:
        """
        Obtiene estadísticas completas de una misión.

        Returns:
            {
                "total_completions": int,
                "unique_users": int,
                "completion_rate": float,
                "average_time_days": float,
                "top_completers": list,
                "completions_per_day": dict,
                "current_active_users": int,
            }
        """
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return {}

        # Total de completaciones
        total_stmt = select(func.count()).select_from(UserMissionEntry).where(
            and_(
                UserMissionEntry.mission_id == mission_id,
                UserMissionEntry.completed == True,
            )
        )
        total_result = await self.session.execute(total_stmt)
        total_completions = total_result.scalar_one()

        # Usuarios únicos que completaron
        unique_stmt = (
            select(func.count(UserMissionEntry.user_id.distinct()))
            .select_from(UserMissionEntry)
            .where(
                and_(
                    UserMissionEntry.mission_id == mission_id,
                    UserMissionEntry.completed == True,
                )
            )
        )
        unique_result = await self.session.execute(unique_stmt)
        unique_users = unique_result.scalar_one()

        # Usuarios con progreso activo (no completado)
        active_stmt = select(func.count()).select_from(UserMissionEntry).where(
            and_(
                UserMissionEntry.mission_id == mission_id,
                UserMissionEntry.completed == False,
            )
        )
        active_result = await self.session.execute(active_stmt)
        current_active_users = active_result.scalar_one()

        # Calcular tasa de completación
        total_users_stmt = select(func.count()).select_from(User)
        total_users_result = await self.session.execute(total_users_stmt)
        total_users = total_users_result.scalar_one()
        completion_rate = (unique_users / total_users * 100) if total_users > 0 else 0

        # Tiempo promedio para completar (si hay datos)
        avg_time_days = await self._calculate_average_time(mission_id)

        # Top completadores
        top_completers = await self.get_top_completers(mission_id, limit=10)

        # Completaciones por día (últimos 7 días)
        completions_per_day = await self._get_completions_per_day(mission_id, days=7)

        return {
            "mission_id": mission_id,
            "mission_name": mission.name,
            "total_completions": total_completions,
            "unique_users": unique_users,
            "completion_rate": round(completion_rate, 2),
            "average_time_days": round(avg_time_days, 2) if avg_time_days else None,
            "top_completers": top_completers,
            "completions_per_day": completions_per_day,
            "current_active_users": current_active_users,
            "max_completions_global": mission.max_completions_global,
            "current_completions_global": mission.current_completions_global or 0,
        }

    async def get_top_completers(
        self, mission_id: str, limit: int = 10
    ) -> list[dict]:
        """
        Obtiene el top de usuarios que más veces han completado una misión.

        Returns:
            [
                {"user_id": int, "username": str, "completions": int},
                ...
            ]
        """
        # Para misiones repetibles, contar cuántas veces cada usuario la completó
        stmt = (
            select(
                UserMissionEntry.user_id,
                func.count(UserMissionEntry.id).label("completions"),
            )
            .where(
                and_(
                    UserMissionEntry.mission_id == mission_id,
                    UserMissionEntry.completed == True,
                )
            )
            .group_by(UserMissionEntry.user_id)
            .order_by(func.count(UserMissionEntry.id).desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        top_completers = []
        for row in rows:
            user = await self.session.get(User, row.user_id)
            if user:
                top_completers.append(
                    {
                        "user_id": row.user_id,
                        "username": user.username or user.first_name or "Anónimo",
                        "completions": row.completions,
                    }
                )

        return top_completers

    async def _calculate_average_time(self, mission_id: str) -> float:
        """Calcula el tiempo promedio (en días) para completar una misión"""
        stmt = select(UserMissionEntry).where(
            and_(
                UserMissionEntry.mission_id == mission_id,
                UserMissionEntry.completed == True,
                UserMissionEntry.completed_at.isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return 0.0

        mission = await self.session.get(Mission, mission_id)
        if not mission or not mission.created_at:
            return 0.0

        total_days = 0
        count = 0

        for entry in entries:
            if entry.completed_at:
                # Calcular días desde la creación de la misión hasta completación
                delta = entry.completed_at - mission.created_at
                total_days += delta.days
                count += 1

        return total_days / count if count > 0 else 0.0

    async def _get_completions_per_day(
        self, mission_id: str, days: int = 7
    ) -> dict:
        """
        Obtiene el número de completaciones por día en los últimos X días.

        Returns:
            {"2025-10-01": 5, "2025-10-02": 8, ...}
        """
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)

        stmt = select(UserMissionEntry).where(
            and_(
                UserMissionEntry.mission_id == mission_id,
                UserMissionEntry.completed == True,
                UserMissionEntry.completed_at >= start_date,
            )
        )

        result = await self.session.execute(stmt)
        entries = result.scalars().all()

        # Agrupar por día
        completions_by_day = {}
        for entry in entries:
            if entry.completed_at:
                day_key = entry.completed_at.strftime("%Y-%m-%d")
                completions_by_day[day_key] = completions_by_day.get(day_key, 0) + 1

        # Rellenar días sin completaciones
        for i in range(days):
            day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if day not in completions_by_day:
                completions_by_day[day] = 0

        return dict(sorted(completions_by_day.items()))

    async def get_global_stats(self) -> dict:
        """
        Obtiene estadísticas globales de todas las misiones.

        Returns:
            {
                "total_missions": int,
                "active_missions": int,
                "hidden_missions": int,
                "total_completions_all": int,
                "most_popular_mission": dict,
                "most_difficult_mission": dict,
            }
        """
        # Total de misiones
        total_stmt = select(func.count()).select_from(Mission)
        total_result = await self.session.execute(total_stmt)
        total_missions = total_result.scalar_one()

        # Misiones activas
        active_stmt = select(func.count()).select_from(Mission).where(
            Mission.is_active == True
        )
        active_result = await self.session.execute(active_stmt)
        active_missions = active_result.scalar_one()

        # Misiones ocultas
        hidden_stmt = select(func.count()).select_from(Mission).where(
            Mission.is_hidden == True
        )
        hidden_result = await self.session.execute(hidden_stmt)
        hidden_missions = hidden_result.scalar_one()

        # Total de completaciones globales
        total_comp_stmt = select(func.count()).select_from(UserMissionEntry).where(
            UserMissionEntry.completed == True
        )
        total_comp_result = await self.session.execute(total_comp_stmt)
        total_completions_all = total_comp_result.scalar_one()

        # Misión más popular (más completaciones)
        popular_stmt = (
            select(
                UserMissionEntry.mission_id,
                func.count(UserMissionEntry.id).label("completions"),
            )
            .where(UserMissionEntry.completed == True)
            .group_by(UserMissionEntry.mission_id)
            .order_by(func.count(UserMissionEntry.id).desc())
            .limit(1)
        )
        popular_result = await self.session.execute(popular_stmt)
        popular_row = popular_result.first()

        most_popular_mission = None
        if popular_row:
            mission = await self.session.get(Mission, popular_row.mission_id)
            if mission:
                most_popular_mission = {
                    "id": mission.id,
                    "name": mission.name,
                    "completions": popular_row.completions,
                }

        return {
            "total_missions": total_missions,
            "active_missions": active_missions,
            "hidden_missions": hidden_missions,
            "total_completions_all": total_completions_all,
            "most_popular_mission": most_popular_mission,
        }
