# services/archetype_integration_service.py
"""
Servicio de Integración de Arquetipos para el Sistema Narrativo Ramificado Diana

Este servicio actúa como puente entre el ArchetypeAnalyzer y los sistemas existentes,
coordinando la activación del sistema ramificado y proporcionando fallbacks graceful.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from dataclasses import dataclass

try:
    from .archetype_analyzer import ArchetypeAnalyzer
    from .emotional_analysis_service import EmotionalAnalysisService
    from ..database.emotional_models import ArchetypeClassification
except ImportError:
    # Fallback para imports absolutos
    from services.archetype_analyzer import ArchetypeAnalyzer
    from services.emotional_analysis_service import EmotionalAnalysisService
    from database.emotional_models import ArchetypeClassification

logger = logging.getLogger(__name__)


@dataclass
class ArchetypeBranchingDecision:
    """
    Estructura para decisiones del sistema ramificado.

    Contiene información sobre si activar características específicas del
    sistema ramificado basado en la clasificación del usuario.
    """
    activate_ramificado: bool = False
    primary_archetype: Optional[str] = None
    confidence_score: float = 0.0
    recommended_narrative_branch: Optional[str] = None
    fallback_to_standard: bool = True
    detection_metadata: Dict[str, Any] = None


class ArchetypeIntegrationService:
    """
    Servicio que coordina la integración del sistema de arquetipos expandido
    con la infraestructura narrativa existente.

    Este servicio evalúa si un usuario debe activar el sistema ramificado
    basado en su clasificación de arquetipo, y proporciona fallbacks
    graceful al sistema de 5 arquetipos existente cuando es necesario.

    Responsabilidades:
    - Evaluar condiciones para activación del sistema ramificado
    - Proporcionar fallbacks al sistema existente
    - Coordinar integración entre ArchetypeAnalyzer y sistemas narrativos
    - Mantener compatibilidad hacia atrás con infraestructura existente
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de integración de arquetipos.

        Args:
            session: Sesión de base de datos SQLAlchemy asíncrona
        """
        self.session = session
        self.archetype_analyzer = ArchetypeAnalyzer(session)
        self.emotional_service = EmotionalAnalysisService(session)

        # Umbrales de confianza para activación del sistema ramificado
        self.confidence_thresholds = {
            'ramificado_activation': 0.8,  # Activar sistema completo
            'valid_classification': 0.7,   # Clasificación válida pero uso estándar
            'minimum_data': 0.5             # Datos mínimos para análisis
        }

    async def evaluate_ramificado_activation(self, user_id: int) -> ArchetypeBranchingDecision:
        """
        Evalúa si un usuario debe activar el sistema narrativo ramificado.

        Analiza la clasificación de arquetipo del usuario y determina si
        cumple los criterios para activar características avanzadas del
        sistema ramificado o si debe usar el sistema estándar.

        Args:
            user_id: ID único del usuario a evaluar

        Returns:
            ArchetypeBranchingDecision con recomendación de activación
        """
        try:
            # Obtener clasificación existente del usuario
            user_classification = await self.archetype_analyzer.get_user_classification(user_id)

            if not user_classification:
                logger.info(f"Usuario {user_id} sin clasificación de arquetipo, usando sistema estándar")
                return ArchetypeBranchingDecision(
                    activate_ramificado=False,
                    fallback_to_standard=True,
                    detection_metadata={'reason': 'no_classification'}
                )

            # Extraer datos de clasificación
            confidence_score = user_classification.get('archetype_confidence', 0.0)
            primary_archetype = user_classification.get('primary_archetype')
            archetype_stability = user_classification.get('archetype_stability', 0.5)

            # Evaluar condiciones para activación
            activation_decision = await self._evaluate_activation_criteria(
                user_id, user_classification, confidence_score, archetype_stability
            )

            # Determinar rama narrativa recomendada
            if activation_decision.activate_ramificado:
                recommended_branch = await self._determine_narrative_branch(user_classification)
                activation_decision.recommended_narrative_branch = recommended_branch

            logger.info(f"Evaluación de ramificado para usuario {user_id}: "
                       f"activar={activation_decision.activate_ramificado}, "
                       f"confianza={confidence_score:.2f}")

            return activation_decision

        except Exception as e:
            logger.error(f"Error evaluando activación de ramificado para usuario {user_id}: {e}")

            # Fallback seguro en caso de error
            return ArchetypeBranchingDecision(
                activate_ramificado=False,
                fallback_to_standard=True,
                detection_metadata={'reason': 'evaluation_error', 'error': str(e)}
            )

    async def check_classification_confidence(self, user_id: int) -> Dict[str, Any]:
        """
        Verifica el nivel de confianza en la clasificación de arquetipo del usuario.

        Proporciona métricas detalladas sobre la calidad y confiabilidad
        de la clasificación para toma de decisiones del sistema.

        Args:
            user_id: ID único del usuario

        Returns:
            Diccionario con métricas de confianza:
            - confidence_level: Nivel general de confianza (alto/medio/bajo)
            - confidence_score: Puntuación numérica (0.0-1.0)
            - classification_quality: Calidad de la clasificación
            - recommendations: Recomendaciones para el sistema
        """
        try:
            user_classification = await self.archetype_analyzer.get_user_classification(user_id)

            if not user_classification:
                return {
                    'confidence_level': 'none',
                    'confidence_score': 0.0,
                    'classification_quality': 'no_classification',
                    'recommendations': ['perform_l1f1_analysis'],
                    'can_use_ramificado': False
                }

            confidence_score = user_classification.get('archetype_confidence', 0.0)
            archetype_stability = user_classification.get('archetype_stability', 0.5)
            temporal_pattern = user_classification.get('temporal_pattern', 'unknown')

            # Determinar nivel de confianza
            if confidence_score >= self.confidence_thresholds['ramificado_activation']:
                confidence_level = 'high'
                quality = 'excellent'
                can_use_ramificado = True
                recommendations = ['activate_ramificado_system']
            elif confidence_score >= self.confidence_thresholds['valid_classification']:
                confidence_level = 'medium'
                quality = 'good'
                can_use_ramificado = False
                recommendations = ['use_enhanced_standard_system']
            elif confidence_score >= self.confidence_thresholds['minimum_data']:
                confidence_level = 'low'
                quality = 'basic'
                can_use_ramificado = False
                recommendations = ['gather_more_data', 'use_standard_system']
            else:
                confidence_level = 'insufficient'
                quality = 'poor'
                can_use_ramificado = False
                recommendations = ['retake_l1f1_assessment']

            return {
                'confidence_level': confidence_level,
                'confidence_score': confidence_score,
                'classification_quality': quality,
                'archetype_stability': archetype_stability,
                'temporal_pattern': temporal_pattern,
                'can_use_ramificado': can_use_ramificado,
                'recommendations': recommendations,
                'primary_archetype': user_classification.get('primary_archetype'),
                'last_updated': user_classification.get('updated_at')
            }

        except Exception as e:
            logger.error(f"Error verificando confianza de clasificación para usuario {user_id}: {e}")
            return {
                'confidence_level': 'error',
                'confidence_score': 0.0,
                'classification_quality': 'error',
                'can_use_ramificado': False,
                'recommendations': ['retry_analysis'],
                'error': str(e)
            }

    async def get_fallback_archetype(self, user_id: int) -> str:
        """
        Proporciona un arquetipo de fallback del sistema de 5 arquetipos existente.

        Cuando el sistema ramificado no puede activarse, mapea la clasificación
        expandida a uno de los 5 arquetipos originales para mantener compatibilidad.

        Args:
            user_id: ID único del usuario

        Returns:
            Nombre del arquetipo de fallback ('explorer', 'achiever', etc.)
        """
        try:
            user_classification = await self.archetype_analyzer.get_user_classification(user_id)

            if not user_classification:
                # Usar arquetipo por defecto si no hay clasificación
                return 'explorer'

            primary_archetype = user_classification.get('primary_archetype', 'intellectual')

            # Mapeo de arquetipos expandidos a sistema de 5 arquetipos
            archetype_mapping = {
                'intellectual': 'achiever',
                'emotional': 'socializer',
                'exploratory': 'explorer',
                'vulnerable': 'socializer',
                'philosophical': 'achiever',
                'direct': 'challenger',
                'patient': 'creator',
                'reciprocal': 'socializer'
            }

            fallback_archetype = archetype_mapping.get(primary_archetype, 'explorer')

            logger.info(f"Fallback archetype para usuario {user_id}: "
                       f"{primary_archetype} -> {fallback_archetype}")

            return fallback_archetype

        except Exception as e:
            logger.error(f"Error obteniendo fallback archetype para usuario {user_id}: {e}")
            return 'explorer'  # Fallback más seguro

    async def integrate_with_emotional_system(self, user_id: int) -> Dict[str, Any]:
        """
        Integra la clasificación de arquetipos con el sistema emocional existente.

        Coordina entre el ArchetypeAnalyzer y el EmotionalAnalysisService
        para proporcionar una vista unificada del perfil psicológico del usuario.

        Args:
            user_id: ID único del usuario

        Returns:
            Diccionario con perfil psicológico integrado
        """
        try:
            # Obtener datos de ambos sistemas
            archetype_data = await self.archetype_analyzer.get_user_classification(user_id)
            emotional_profile = await self.emotional_service.get_user_emotional_profile(user_id)

            if not archetype_data and not emotional_profile:
                return {
                    'integration_status': 'no_data',
                    'recommendation': 'perform_initial_assessment'
                }

            # Integrar datos disponibles
            integrated_profile = {
                'integration_status': 'success',
                'archetype_classification': archetype_data,
                'emotional_profile': emotional_profile,
                'unified_recommendations': []
            }

            # Agregar recomendaciones basadas en ambos perfiles
            if archetype_data:
                primary_archetype = archetype_data.get('primary_archetype')
                confidence = archetype_data.get('archetype_confidence', 0.0)

                if confidence >= 0.8:
                    integrated_profile['unified_recommendations'].append(
                        f'activate_enhanced_narrative_for_{primary_archetype}'
                    )

            if emotional_profile:
                vulnerability_level = emotional_profile.get('vulnerability_level', 0.0)
                if vulnerability_level > 0.7:
                    integrated_profile['unified_recommendations'].append(
                        'enable_sensitive_content_handling'
                    )

            return integrated_profile

        except Exception as e:
            logger.error(f"Error integrando sistemas para usuario {user_id}: {e}")
            return {
                'integration_status': 'error',
                'error': str(e),
                'recommendation': 'use_fallback_systems'
            }

    async def _evaluate_activation_criteria(
        self,
        user_id: int,
        classification: Dict[str, Any],
        confidence_score: float,
        stability_score: float
    ) -> ArchetypeBranchingDecision:
        """
        Evalúa criterios específicos para activación del sistema ramificado.

        Args:
            user_id: ID del usuario
            classification: Datos de clasificación completos
            confidence_score: Puntuación de confianza
            stability_score: Puntuación de estabilidad

        Returns:
            ArchetypeBranchingDecision con evaluación detallada
        """
        decision = ArchetypeBranchingDecision(
            primary_archetype=classification.get('primary_archetype'),
            confidence_score=confidence_score
        )

        # Criterio 1: Confianza mínima
        if confidence_score < self.confidence_thresholds['ramificado_activation']:
            decision.activate_ramificado = False
            decision.fallback_to_standard = True
            decision.detection_metadata = {
                'reason': 'insufficient_confidence',
                'required': self.confidence_thresholds['ramificado_activation'],
                'actual': confidence_score
            }
            return decision

        # Criterio 2: Estabilidad de clasificación
        if stability_score < 0.6:
            decision.activate_ramificado = False
            decision.fallback_to_standard = True
            decision.detection_metadata = {
                'reason': 'unstable_classification',
                'stability_score': stability_score
            }
            return decision

        # Criterio 3: Datos suficientes en sub-arquetipos
        sub_scores = classification.get('sub_scores', {})
        if not sub_scores or max(sub_scores.values()) < 1.0:
            decision.activate_ramificado = False
            decision.fallback_to_standard = True
            decision.detection_metadata = {
                'reason': 'insufficient_sub_archetype_data',
                'max_sub_score': max(sub_scores.values()) if sub_scores else 0.0
            }
            return decision

        # Todos los criterios cumplidos
        decision.activate_ramificado = True
        decision.fallback_to_standard = False
        decision.detection_metadata = {
            'reason': 'all_criteria_met',
            'confidence': confidence_score,
            'stability': stability_score,
            'sub_archetype_strength': max(sub_scores.values())
        }

        return decision

    async def _determine_narrative_branch(self, classification: Dict[str, Any]) -> str:
        """
        Determina la rama narrativa específica basada en la clasificación.

        Args:
            classification: Datos completos de clasificación del usuario

        Returns:
            Nombre de la rama narrativa recomendada
        """
        primary_archetype = classification.get('primary_archetype', 'intellectual')
        sub_scores = classification.get('sub_scores', {})

        # Encontrar sub-arquetipo dominante
        if sub_scores:
            dominant_sub = max(sub_scores.items(), key=lambda x: x[1])
            sub_archetype_name = dominant_sub[0]

            # Mapear a ramas narrativas específicas
            narrative_branches = {
                'romantic_intellectual': 'intimate_intellectual_branch',
                'skeptical_thinker': 'analytical_challenge_branch',
                'hedonist_philosopher': 'sensual_wisdom_branch',
                'pure_theorist': 'abstract_exploration_branch',
                'empathetic_emotional': 'deep_connection_branch',
                'passionate_emotional': 'intense_experience_branch',
                'wounded_healer': 'healing_journey_branch',
                'adventure_seeker': 'dynamic_adventure_branch',
                'collector_explorer': 'methodical_discovery_branch',
                'freedom_lover': 'liberation_narrative_branch'
            }

            return narrative_branches.get(sub_archetype_name, f'{primary_archetype}_enhanced_branch')

        # Fallback a rama basada en arquetipo primario
        return f'{primary_archetype}_standard_branch'

    async def activate_archetype_branching(self, user_id: int) -> bool:
        """
        Activa el sistema de ramificación narrativa basado en arquetipos para un usuario.

        Verifica que el usuario tenga una clasificación de arquetipo con suficiente
        confianza (>0.8) y actualiza las marcas en la base de datos para habilitar
        la experiencia ramificada personalizada.

        Args:
            user_id: ID único del usuario

        Returns:
            bool: True si la activación fue exitosa, False en caso contrario
        """
        try:
            # Verificar confianza de clasificación
            confidence_check = await self.check_classification_confidence(user_id)

            if not confidence_check.get('can_use_ramificado', False):
                logger.info(f"Usuario {user_id} no cumple criterios para ramificación: "
                           f"confianza={confidence_check.get('confidence_score', 0.0):.2f}")
                return False

            # Obtener clasificación actual
            user_classification = await self.archetype_analyzer.get_user_classification(user_id)

            if not user_classification:
                logger.error(f"No se encontró clasificación para usuario {user_id}")
                return False

            confidence_score = user_classification.get('archetype_confidence', 0.0)

            # Verificar umbral de confianza
            if confidence_score < self.confidence_thresholds['ramificado_activation']:
                logger.warning(f"Usuario {user_id} no alcanza umbral de confianza para activación: "
                              f"{confidence_score:.2f} < {self.confidence_thresholds['ramificado_activation']}")
                return False

            # Actualizar flags de ramificación en la base de datos
            from sqlalchemy import update
            from ..database.emotional_models import ArchetypeClassification

            # Actualizar registro existente con flag de activación
            stmt = update(ArchetypeClassification).where(
                ArchetypeClassification.user_id == user_id
            ).values(
                ramificado_enabled=True,
                activation_timestamp=func.now()
            )

            await self.session.execute(stmt)
            await self.session.commit()

            logger.info(f"Sistema ramificado activado exitosamente para usuario {user_id} "
                       f"con confianza {confidence_score:.2f}")

            return True

        except Exception as e:
            logger.error(f"Error activando ramificación para usuario {user_id}: {e}")
            await self.session.rollback()
            return False

    async def get_archetype_confidence(self, user_id: int) -> Optional[float]:
        """
        Obtiene la puntuación de confianza actual del arquetipo del usuario.

        Proporciona acceso directo a la métrica de confianza de la clasificación
        del arquetipo sin la sobrecarga de análisis completos adicionales.

        Args:
            user_id: ID único del usuario

        Returns:
            float: Puntuación de confianza (0.0-1.0) o None si no existe clasificación
        """
        try:
            # Obtener clasificación del usuario
            user_classification = await self.archetype_analyzer.get_user_classification(user_id)

            if not user_classification:
                logger.debug(f"No se encontró clasificación de arquetipo para usuario {user_id}")
                return None

            confidence_score = user_classification.get('archetype_confidence')

            if confidence_score is None:
                logger.warning(f"Clasificación sin puntuación de confianza para usuario {user_id}")
                return None

            # Validar rango de confianza
            if not isinstance(confidence_score, (int, float)):
                logger.warning(f"Puntuación de confianza inválida para usuario {user_id}: {confidence_score}")
                return None

            # Normalizar a rango válido
            confidence_score = max(0.0, min(1.0, float(confidence_score)))

            logger.debug(f"Confianza de arquetipo para usuario {user_id}: {confidence_score:.3f}")

            return confidence_score

        except Exception as e:
            logger.error(f"Error obteniendo confianza de arquetipo para usuario {user_id}: {e}")
            return None