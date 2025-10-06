"""
Handler para métricas de admin
STRATEGIC: Sistema de monitoreo para validar mejoras
"""
import logging
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from services.metrics_service import MetricsService
from utils.admin_check import is_admin

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("metrics"))
async def metrics_command(message: types.Message, session: AsyncSession):
    """Muestra métricas del sistema para admins"""
    try:
        # Verificar permisos de admin
        if not await is_admin(message.from_user.id, session):
            await message.answer("❌ Solo los administradores pueden ver las métricas.")
            return
        
        metrics_service = MetricsService(session)
        
        # Obtener métricas
        engagement_metrics = await metrics_service.get_engagement_metrics(days=7)
        onboarding_funnel = await metrics_service.get_onboarding_funnel()
        
        # Formatear respuesta
        response = "📊 **Métricas del Sistema**\n\n"
        
        response += "🔥 **Engagement (7 días)**\n"
        response += f"• Interacciones totales: {engagement_metrics.get('total_interactions', 0):,}\n"
        response += f"• Usuarios activos: {engagement_metrics.get('active_users', 0):,}\n"
        response += f"• Avg interacciones/usuario: {engagement_metrics.get('avg_interactions_per_user', 0):.1f}\n\n"
        
        response += "🚀 **Funnel de Onboarding**\n"
        funnel_data = onboarding_funnel.get('funnel_steps', {})
        total_users = onboarding_funnel.get('total_users', 0)
        
        if total_users > 0:
            response += f"• Bienvenida: {funnel_data.get('onboarding_welcome', 0)} ({funnel_data.get('onboarding_welcome', 0)/total_users*100:.1f}%)\n"
            response += f"• Narrativa: {funnel_data.get('onboarding_narrative_intro', 0)} ({funnel_data.get('onboarding_narrative_intro', 0)/total_users*100:.1f}%)\n"
            response += f"• Misiones: {funnel_data.get('onboarding_missions_intro', 0)} ({funnel_data.get('onboarding_missions_intro', 0)/total_users*100:.1f}%)\n"
            response += f"• Onboarding completo: {funnel_data.get('onboarding_complete', 0)} ({funnel_data.get('onboarding_complete', 0)/total_users*100:.1f}%)\n"
        
        response += f"\n📈 Total usuarios: {total_users:,}"
        response += f"\n🕐 Calculado: {engagement_metrics.get('calculated_at', 'N/A')}"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error en comando de métricas: {e}")
        await message.answer("❌ Error obteniendo métricas. Revisa los logs.")
