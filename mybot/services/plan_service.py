from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# El modelo SubscriptionPlan ha sido eliminado
# Este servicio se mantiene por compatibilidad pero no tiene funcionalidad

class SubscriptionPlanService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(self, created_by: int, name: str, price: int, duration_days: int):
        """Método deshabilitado - el sistema de planes ha sido reemplazado"""
        raise NotImplementedError("El sistema de planes ha sido reemplazado por el nuevo sistema de transacciones VIP")

    async def get_plan_by_id(self, plan_id: int):
        """Método deshabilitado - el sistema de planes ha sido reemplazado"""
        raise NotImplementedError("El sistema de planes ha sido reemplazado por el nuevo sistema de transacciones VIP")

    async def list_plans(self):
        """Método deshabilitado - el sistema de planes ha sido reemplazado"""
        raise NotImplementedError("El sistema de planes ha sido reemplazado por el nuevo sistema de transacciones VIP")