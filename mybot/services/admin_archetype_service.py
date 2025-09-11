"""
Admin Archetype Service - Administrative interface for user archetype analytics.

Provides comprehensive analytics, reporting, and management capabilities
for the user archetype classification system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from sqlalchemy import desc, asc

try:
    from ..database.models import UserArchetypeData, User
    from .user_archetype_service import UserArchetypeService, UserArchetype
except ImportError:
    from database.models import UserArchetypeData, User
    from services.user_archetype_service import UserArchetypeService, UserArchetype

logger = logging.getLogger(__name__)


class AdminArchetypeService:
    """
    Administrative service for user archetype analytics and management.
    
    Provides detailed analytics, reporting, and administrative controls
    for the archetype classification system.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the admin archetype service."""
        self.session = session
        self.user_archetype_service = UserArchetypeService(session)
    
    async def get_global_archetype_distribution(self) -> Dict[str, Any]:
        """
        Get global distribution of user archetypes.
        
        Returns:
            Dict with archetype distribution statistics
        """
        try:
            # Get all users with archetype data
            stmt = select(UserArchetypeData).where(
                UserArchetypeData.current_archetype != "undefined",
                UserArchetypeData.confidence_score >= 0.5
            )
            result = await self.session.execute(stmt)
            archetype_data = result.scalars().all()
            
            # Count distributions
            distribution = {}
            total_classified = 0
            confidence_sum = 0.0
            
            for data in archetype_data:
                archetype = data.current_archetype
                if archetype not in distribution:
                    distribution[archetype] = {
                        'count': 0,
                        'avg_confidence': 0.0,
                        'total_confidence': 0.0
                    }
                
                distribution[archetype]['count'] += 1
                distribution[archetype]['total_confidence'] += data.confidence_score
                distribution[archetype]['avg_confidence'] = (
                    distribution[archetype]['total_confidence'] / 
                    distribution[archetype]['count']
                )
                
                total_classified += 1
                confidence_sum += data.confidence_score
            
            # Calculate percentages
            for archetype in distribution:
                distribution[archetype]['percentage'] = (
                    distribution[archetype]['count'] / total_classified * 100 
                    if total_classified > 0 else 0
                )
            
            # Get total users for context
            total_users_stmt = select(func.count(User.id))
            total_users_result = await self.session.execute(total_users_stmt)
            total_users = total_users_result.scalar()
            
            return {
                'distribution': distribution,
                'total_classified': total_classified,
                'total_users': total_users,
                'classification_rate': total_classified / total_users * 100 if total_users > 0 else 0,
                'avg_global_confidence': confidence_sum / total_classified if total_classified > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting global archetype distribution: {e}")
            return {}
    
    async def get_archetype_evolution_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get archetype evolution trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with evolution trends and patterns
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get users with archetype history
            stmt = select(UserArchetypeData).where(
                UserArchetypeData.updated_at >= cutoff_date,
                UserArchetypeData.archetype_history.isnot(None)
            )
            result = await self.session.execute(stmt)
            archetype_data = result.scalars().all()
            
            evolution_patterns = {}
            stability_scores = []
            
            for data in archetype_data:
                if not data.archetype_history:
                    continue
                
                user_id = data.user_id
                history = data.archetype_history
                
                # Analyze stability
                if len(history) > 1:
                    changes = len(history)
                    stability = max(0, 1.0 - (changes / 10.0))  # Lower score for more changes
                    stability_scores.append(stability)
                    
                    # Track transition patterns
                    for i in range(len(history) - 1):
                        from_archetype = history[i].get('from_archetype', 'unknown')
                        to_archetype = history[i].get('to_archetype', 'unknown')
                        transition = f"{from_archetype} -> {to_archetype}"
                        
                        if transition not in evolution_patterns:
                            evolution_patterns[transition] = 0
                        evolution_patterns[transition] += 1
            
            # Calculate average stability
            avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0
            
            # Sort transitions by frequency
            sorted_patterns = dict(sorted(evolution_patterns.items(), key=lambda x: x[1], reverse=True))
            
            return {
                'evolution_patterns': sorted_patterns,
                'avg_stability_score': avg_stability,
                'users_with_changes': len(stability_scores),
                'analysis_period_days': days,
                'most_common_transition': max(sorted_patterns.keys(), key=lambda k: sorted_patterns[k]) if sorted_patterns else None
            }
            
        except Exception as e:
            logger.error(f"Error getting archetype evolution trends: {e}")
            return {}
    
    async def get_user_archetype_details(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed archetype information for a specific user.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Comprehensive user archetype details
        """
        try:
            # Get user basic info
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {'error': 'User not found'}
            
            # Get archetype data
            archetype_data = await self.user_archetype_service.get_user_archetype_data(user_id)
            if not archetype_data:
                return {'error': 'No archetype data found'}
            
            # Get current classification
            current_archetype, confidence = await self.user_archetype_service.get_user_archetype(user_id)
            
            # Get analytics
            analytics = await self.user_archetype_service.get_archetype_analytics(user_id)
            
            # Calculate behavioral insights
            behavioral_patterns = archetype_data.behavioral_patterns or {}
            insights = self._generate_behavioral_insights(behavioral_patterns, current_archetype)
            
            return {
                'user_info': {
                    'user_id': user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'points': user.points,
                    'level': user.level
                },
                'archetype_info': {
                    'current_archetype': current_archetype.value if hasattr(current_archetype, 'value') else str(current_archetype),
                    'confidence_score': confidence,
                    'classification_count': archetype_data.classification_count,
                    'last_classification': archetype_data.last_classification,
                    'avg_classification_time': archetype_data.avg_classification_time
                },
                'behavioral_patterns': behavioral_patterns,
                'behavioral_insights': insights,
                'evolution_history': archetype_data.archetype_history or [],
                'all_scores': archetype_data.archetype_scores or {},
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting user archetype details for {user_id}: {e}")
            return {'error': str(e)}
    
    def _generate_behavioral_insights(self, patterns: Dict[str, Any], archetype: UserArchetype) -> List[str]:
        """Generate behavioral insights from patterns."""
        insights = []
        
        try:
            # Response time insights
            avg_response_time = patterns.get('avg_response_time', 0)
            if avg_response_time > 0:
                if avg_response_time < 3:
                    insights.append("Usuario con respuestas muy rápidas - posible Directo Auténtico")
                elif avg_response_time > 10:
                    insights.append("Usuario reflexivo - posible Explorador Profundo o Analítico Empático")
            
            # Exploration patterns
            rereads = patterns.get('rereads_count', 0)
            if rereads > 3:
                insights.append(f"Alta tendencia a releer contenido ({rereads} veces) - patrón de Explorador Profundo")
            
            deep_navigation = patterns.get('deep_navigation_sessions', 0)
            if deep_navigation > 5:
                insights.append(f"Navegación profunda frecuente ({deep_navigation} sesiones) - busca detalles")
            
            # Aesthetic preferences
            aesthetic_choices = patterns.get('aesthetic_choices', 0)
            metaphorical_prefs = patterns.get('metaphorical_preferences', 0)
            if aesthetic_choices > 2 or metaphorical_prefs > 2:
                insights.append("Preferencias estéticas/metafóricas - patrón de Poeta del Deseo")
            
            # Consistency patterns
            consistent_engagement = patterns.get('consistent_engagement', 0)
            if consistent_engagement > 7:
                insights.append(f"Alto engagement consistente ({consistent_engagement}) - patrón de Persistente Paciente")
            
            # Session patterns
            avg_session = patterns.get('session_duration_avg', 0)
            if avg_session > 900:  # 15 minutes
                insights.append(f"Sesiones largas (promedio: {avg_session/60:.1f} min) - usuario dedicado")
            
            # Classification confidence insights
            archetype_name = archetype.value if hasattr(archetype, 'value') else str(archetype)
            if archetype_name != "undefined":
                insights.append(f"Clasificado como {archetype_name.replace('_', ' ').title()}")
            
        except Exception as e:
            logger.error(f"Error generating behavioral insights: {e}")
            insights.append("Error al generar insights de comportamiento")
        
        return insights
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics for archetype classification.
        
        Returns:
            Performance and efficiency metrics
        """
        try:
            # Get classification performance data
            stmt = select(UserArchetypeData).where(
                UserArchetypeData.avg_classification_time > 0
            )
            result = await self.session.execute(stmt)
            archetype_data = result.scalars().all()
            
            if not archetype_data:
                return {'error': 'No performance data available'}
            
            classification_times = [data.avg_classification_time for data in archetype_data]
            confidence_scores = [data.confidence_score for data in archetype_data if data.confidence_score > 0]
            
            # Calculate metrics
            avg_classification_time = sum(classification_times) / len(classification_times)
            max_classification_time = max(classification_times)
            min_classification_time = min(classification_times)
            
            # Performance targets
            target_time = 0.1  # 100ms target
            fast_classifications = len([t for t in classification_times if t <= target_time])
            performance_rate = fast_classifications / len(classification_times) * 100
            
            # Confidence metrics
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            high_confidence_rate = len([c for c in confidence_scores if c >= 0.7]) / len(confidence_scores) * 100 if confidence_scores else 0
            
            return {
                'classification_performance': {
                    'avg_time_seconds': avg_classification_time,
                    'max_time_seconds': max_classification_time,
                    'min_time_seconds': min_classification_time,
                    'target_time_seconds': target_time,
                    'performance_rate_percentage': performance_rate,
                    'total_classifications': len(classification_times)
                },
                'confidence_metrics': {
                    'avg_confidence_score': avg_confidence,
                    'high_confidence_rate_percentage': high_confidence_rate,
                    'total_confident_classifications': len([c for c in confidence_scores if c >= 0.5])
                },
                'system_health': {
                    'meeting_performance_target': performance_rate > 80,
                    'high_accuracy': high_confidence_rate > 70,
                    'status': 'healthy' if performance_rate > 80 and high_confidence_rate > 70 else 'needs_attention'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    async def force_user_reclassification(self, user_id: int) -> Dict[str, Any]:
        """
        Force reclassification of a specific user.
        
        Args:
            user_id: User ID to reclassify
            
        Returns:
            Results of the reclassification
        """
        try:
            old_archetype, old_confidence = await self.user_archetype_service.get_user_archetype(user_id)
            
            new_archetype = await self.user_archetype_service.force_reclassification(user_id)
            
            new_confidence = 0.0
            if new_archetype != UserArchetype.UNDEFINED:
                _, new_confidence = await self.user_archetype_service.get_user_archetype(user_id)
            
            return {
                'success': True,
                'user_id': user_id,
                'old_archetype': old_archetype.value if hasattr(old_archetype, 'value') else str(old_archetype),
                'old_confidence': old_confidence,
                'new_archetype': new_archetype.value if hasattr(new_archetype, 'value') else str(new_archetype),
                'new_confidence': new_confidence,
                'changed': old_archetype != new_archetype,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forcing user reclassification for {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    async def get_archetype_recommendations(self, archetype: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get users with specific archetype for content recommendations.
        
        Args:
            archetype: Target archetype
            limit: Maximum number of users to return
            
        Returns:
            List of users with the specified archetype
        """
        try:
            stmt = (
                select(UserArchetypeData, User)
                .join(User, UserArchetypeData.user_id == User.id)
                .where(
                    UserArchetypeData.current_archetype == archetype,
                    UserArchetypeData.confidence_score >= 0.6
                )
                .order_by(desc(UserArchetypeData.confidence_score))
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            user_data = result.all()
            
            recommendations = []
            for archetype_data, user in user_data:
                recommendations.append({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'confidence_score': archetype_data.confidence_score,
                    'classification_count': archetype_data.classification_count,
                    'points': user.points,
                    'level': user.level
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting archetype recommendations for {archetype}: {e}")
            return []
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive archetype system report.
        
        Returns:
            Complete system analysis report
        """
        try:
            # Get all major metrics
            distribution = await self.get_global_archetype_distribution()
            evolution_trends = await self.get_archetype_evolution_trends()
            performance = await self.get_performance_metrics()
            
            # Generate summary insights
            insights = []
            
            if distribution:
                total_classified = distribution.get('total_classified', 0)
                classification_rate = distribution.get('classification_rate', 0)
                
                if classification_rate > 50:
                    insights.append(f"Buena tasa de clasificación: {classification_rate:.1f}% de usuarios clasificados")
                else:
                    insights.append(f"Oportunidad de mejora: solo {classification_rate:.1f}% de usuarios clasificados")
                
                # Find dominant archetype
                archetypes = distribution.get('distribution', {})
                if archetypes:
                    dominant = max(archetypes.keys(), key=lambda k: archetypes[k]['count'])
                    dominant_percentage = archetypes[dominant]['percentage']
                    insights.append(f"Arquetipo dominante: {dominant.replace('_', ' ').title()} ({dominant_percentage:.1f}%)")
            
            if evolution_trends:
                avg_stability = evolution_trends.get('avg_stability_score', 0)
                if avg_stability > 0.7:
                    insights.append(f"Alta estabilidad de clasificación: {avg_stability:.2f}")
                else:
                    insights.append(f"Clasificaciones inestables: {avg_stability:.2f} - revisar algoritmo")
            
            if performance and 'system_health' in performance:
                system_status = performance['system_health']['status']
                insights.append(f"Estado del sistema: {system_status}")
            
            return {
                'report_timestamp': datetime.utcnow().isoformat(),
                'global_distribution': distribution,
                'evolution_trends': evolution_trends,
                'performance_metrics': performance,
                'key_insights': insights,
                'recommendations': self._generate_system_recommendations(distribution, evolution_trends, performance)
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}
    
    def _generate_system_recommendations(self, distribution: Dict, evolution: Dict, performance: Dict) -> List[str]:
        """Generate system improvement recommendations."""
        recommendations = []
        
        try:
            # Distribution recommendations
            if distribution:
                classification_rate = distribution.get('classification_rate', 0)
                if classification_rate < 30:
                    recommendations.append("Incrementar interacciones para mejorar tasa de clasificación")
                
                avg_confidence = distribution.get('avg_global_confidence', 0)
                if avg_confidence < 0.6:
                    recommendations.append("Ajustar pesos del algoritmo para mejorar confianza")
            
            # Evolution recommendations
            if evolution:
                avg_stability = evolution.get('avg_stability_score', 0)
                if avg_stability < 0.5:
                    recommendations.append("Revisar frecuencia de reclasificación - demasiada inestabilidad")
            
            # Performance recommendations
            if performance and 'classification_performance' in performance:
                perf_rate = performance['classification_performance'].get('performance_rate_percentage', 0)
                if perf_rate < 80:
                    recommendations.append("Optimizar algoritmo de clasificación para mejorar velocidad")
                
                if 'system_health' in performance and performance['system_health']['status'] == 'needs_attention':
                    recommendations.append("Sistema requiere atención - revisar métricas de rendimiento")
            
            if not recommendations:
                recommendations.append("Sistema funcionando dentro de parámetros normales")
                
        except Exception as e:
            logger.error(f"Error generating system recommendations: {e}")
            recommendations.append("Error al generar recomendaciones")
        
        return recommendations