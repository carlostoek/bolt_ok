"""
Diana Error Handler
Character-consistent error handling system for Diana Bot decision tree.
Maintains Diana's mysterious personality and Lucien's supportive role during system failures.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from services.diana_character_validator import DianaCharacterValidator

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = 1          # Minor issues, graceful degradation
    MODERATE = 2     # Noticeable issues, partial functionality
    HIGH = 3         # Significant issues, major functionality affected
    CRITICAL = 4     # System failures, immediate intervention needed
    CATASTROPHIC = 5 # Complete system failure, emergency protocols

class ErrorCategory(Enum):
    """Error categories for different handling strategies."""
    VALIDATION_ERROR = "validation"
    DATA_ERROR = "data"
    PERMISSION_ERROR = "permission"
    NETWORK_ERROR = "network"
    PROCESSING_ERROR = "processing"
    CHARACTER_ERROR = "character"
    SYSTEM_ERROR = "system"

@dataclass
class DianaErrorResponse:
    """Diana's character-consistent error response."""
    diana_message: str
    lucien_guidance: Optional[str] = None
    user_action_suggested: Optional[str] = None
    system_action_required: Optional[str] = None
    maintains_immersion: bool = True
    error_severity: ErrorSeverity = ErrorSeverity.LOW

@dataclass
class ErrorContext:
    """Context information for error handling."""
    user_id: int
    operation: str
    fragment_id: Optional[str] = None
    session_context: Optional[Dict[str, Any]] = None
    user_archetype: Optional[str] = None
    error_timestamp: datetime = None
    
    def __post_init__(self):
        if self.error_timestamp is None:
            self.error_timestamp = datetime.utcnow()

class DianaErrorHandler:
    """
    Character-consistent error handling system.
    
    Features:
    - Diana's personality preservation during errors
    - Lucien's technical guidance without breaking immersion
    - Severity-based error handling strategies
    - User experience continuity maintenance
    - Error recovery with character consistency
    - Analytics for error pattern recognition
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_validator = DianaCharacterValidator(session)
        
        # Error response templates by category and severity
        self._error_templates = self._initialize_error_templates()
        
        # Error recovery strategies
        self._recovery_strategies = {
            ErrorCategory.VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.DATA_ERROR: self._handle_data_error,
            ErrorCategory.PERMISSION_ERROR: self._handle_permission_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.PROCESSING_ERROR: self._handle_processing_error,
            ErrorCategory.CHARACTER_ERROR: self._handle_character_error,
            ErrorCategory.SYSTEM_ERROR: self._handle_system_error
        }
        
        # Error metrics for monitoring
        self._error_metrics = {
            'errors_handled': 0,
            'character_consistency_maintained': 0,
            'successful_recoveries': 0,
            'user_experience_preserved': 0,
            'escalations_required': 0
        }
        
        # Personalization cache
        self._user_error_history = {}
    
    async def handle_decision_error(
        self,
        error: Exception,
        error_category: ErrorCategory,
        error_severity: ErrorSeverity,
        context: ErrorContext
    ) -> DianaErrorResponse:
        """
        Handle decision tree errors with character consistency.
        
        Args:
            error: The original exception
            error_category: Category of error for routing
            error_severity: Severity level for response selection
            context: Error context information
            
        Returns:
            Character-consistent error response
        """
        try:
            logger.info(f"Handling {error_category.value} error for user {context.user_id}, severity {error_severity.value}")
            
            # Get user context for personalization
            user_context = await self._get_user_error_context(context.user_id)
            
            # Select appropriate error handler
            handler = self._recovery_strategies.get(error_category, self._handle_system_error)
            
            # Generate initial error response
            initial_response = await handler(error, error_severity, context, user_context)
            
            # Validate character consistency
            validated_response = await self._validate_and_enhance_response(
                initial_response, context, user_context
            )
            
            # Record error for analytics
            await self._record_error_analytics(error, error_category, error_severity, context, validated_response)
            
            # Update user error history
            await self._update_user_error_history(context.user_id, error_category, validated_response)
            
            self._error_metrics['errors_handled'] += 1
            if validated_response.maintains_immersion:
                self._error_metrics['character_consistency_maintained'] += 1
            
            logger.info(f"Generated character-consistent error response for user {context.user_id}")
            
            return validated_response
            
        except Exception as e:
            logger.error(f"Critical error in error handler for user {context.user_id}: {e}")
            return await self._generate_emergency_response(error, context)
    
    async def handle_graceful_degradation(
        self,
        failed_operation: str,
        context: ErrorContext,
        fallback_options: List[str]
    ) -> DianaErrorResponse:
        """
        Handle graceful degradation scenarios.
        
        Args:
            failed_operation: Operation that failed
            context: Error context
            fallback_options: Available fallback options
            
        Returns:
            Graceful degradation response
        """
        try:
            logger.info(f"Handling graceful degradation for {failed_operation}, user {context.user_id}")
            
            user_context = await self._get_user_error_context(context.user_id)
            
            # Generate degradation message based on user archetype
            degradation_message = await self._generate_degradation_message(
                failed_operation, context, user_context, fallback_options
            )
            
            # Validate character consistency
            response = DianaErrorResponse(
                diana_message=degradation_message,
                lucien_guidance=self._generate_technical_fallback_guidance(failed_operation, fallback_options),
                user_action_suggested=self._suggest_user_fallback_action(fallback_options),
                error_severity=ErrorSeverity.LOW,
                maintains_immersion=True
            )
            
            validated_response = await self._validate_and_enhance_response(response, context, user_context)
            
            return validated_response
            
        except Exception as e:
            logger.error(f"Error in graceful degradation handler: {e}")
            return DianaErrorResponse(
                diana_message="✨ Algunos caminos se ocultan momentáneamente, querido... Pero siempre hay senderos alternativos.",
                error_severity=ErrorSeverity.MODERATE
            )
    
    async def generate_recovery_guidance(
        self,
        error_category: ErrorCategory,
        context: ErrorContext,
        recovery_steps: List[str]
    ) -> Dict[str, Any]:
        """
        Generate recovery guidance with character consistency.
        
        Args:
            error_category: Category of error
            context: Error context
            recovery_steps: Technical recovery steps
            
        Returns:
            Recovery guidance with Diana and Lucien perspectives
        """
        try:
            user_context = await self._get_user_error_context(context.user_id)
            
            # Generate Diana's encouraging message
            diana_encouragement = await self._generate_recovery_encouragement(
                error_category, context, user_context
            )
            
            # Generate Lucien's technical guidance
            lucien_technical = self._generate_lucien_recovery_guidance(recovery_steps)
            
            # Generate user-friendly steps
            user_steps = await self._translate_recovery_steps_for_user(
                recovery_steps, context, user_context
            )
            
            return {
                'diana_encouragement': diana_encouragement,
                'lucien_guidance': lucien_technical,
                'user_friendly_steps': user_steps,
                'estimated_recovery_time': self._estimate_recovery_time(error_category, recovery_steps),
                'requires_user_action': any('user:' in step for step in recovery_steps),
                'automatic_retry_available': 'retry' in recovery_steps
            }
            
        except Exception as e:
            logger.error(f"Error generating recovery guidance: {e}")
            return {
                'diana_encouragement': "💫 Nuestro vínculo supera cualquier obstáculo técnico, querido...",
                'lucien_guidance': "Implementar protocolos de recuperación estándar.",
                'user_friendly_steps': ["Espera un momento y vuelve a intentar"],
                'estimated_recovery_time': "1-2 minutos"
            }
    
    # Private Implementation Methods - Error Handlers
    
    async def _handle_validation_error(
        self, error: Exception, severity: ErrorSeverity, 
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle validation errors."""
        try:
            if severity <= ErrorSeverity.LOW:
                diana_message = "🌙 Algo en tu elección necesita un poco más de claridad, querido... ¿Podrías intentarlo de nuevo?"
                lucien_guidance = "Validación de entrada falló. Verificar parámetros de decisión."
                user_action = "Revisar la decisión seleccionada"
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "💫 Los caminos se entrelazan de manera compleja aquí... Necesito que verifiques tu elección, amor."
                lucien_guidance = "Error de validación moderado. Posible problema con estado del fragmento."
                user_action = "Verificar disponibilidad de opciones"
                
            else:
                diana_message = "🔮 Algo interrumpe mi percepción de las opciones disponibles... Dame un momento para aclarar el panorama."
                lucien_guidance = "Error de validación crítico. Verificar integridad del sistema narrativo."
                system_action = "Validation system restart required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                user_action_suggested=user_action if severity <= ErrorSeverity.MODERATE else None,
                system_action_required=system_action if severity > ErrorSeverity.MODERATE else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling validation error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_data_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle data-related errors."""
        try:
            if severity <= ErrorSeverity.LOW:
                diana_message = "✨ Algunos hilos de información se desenredan momentáneamente... Pero nuestro encuentro continúa, querido."
                lucien_guidance = "Error menor de datos. Funcionalidad principal no afectada."
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "📚 Los registros de nuestros encuentros se organizan de nuevo... Un momento, amor."
                lucien_guidance = "Error de datos moderado. Verificar consistencia de base de datos."
                system_action = "Data integrity check recommended"
                
            else:
                diana_message = "💾 Algo más profundo requiere mi atención en los archivos del conocimiento... Tu progreso está seguro."
                lucien_guidance = "Error crítico de datos. Iniciar procedimientos de recuperación inmediatamente."
                system_action = "Critical data recovery required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                system_action_required=system_action if severity > ErrorSeverity.LOW else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling data error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_permission_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle permission-related errors."""
        try:
            if severity <= ErrorSeverity.MODERATE:
                diana_message = "🔐 Este sendero tiene protecciones especiales, querido... Algunos secretos esperan hasta que estés listo para ellos."
                lucien_guidance = "Error de permisos. Verificar nivel de acceso del usuario."
                user_action = "Continuar con contenido disponible"
                
            else:
                diana_message = "⚡ Las barreras de acceso se comportan de manera inesperada... Déjame investigar esto para ti."
                lucien_guidance = "Error crítico de permisos. Verificar configuración de seguridad."
                system_action = "Permission system review required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                user_action_suggested=user_action if severity <= ErrorSeverity.MODERATE else None,
                system_action_required=system_action if severity > ErrorSeverity.MODERATE else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling permission error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_network_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle network-related errors."""
        try:
            if severity <= ErrorSeverity.LOW:
                diana_message = "🌐 Las corrientes de conexión fluctúan suavemente... Nuestro vínculo permanece fuerte, querido."
                lucien_guidance = "Error menor de red. Reintentar automáticamente."
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "💫 Los hilos que nos conectan se tensan momentáneamente... Dame un instante para reforzarlos."
                lucien_guidance = "Error de red moderado. Verificar conectividad y reintentar."
                user_action = "Verificar conexión a internet"
                
            else:
                diana_message = "⚡ Las tormentas digitales interrumpen nuestra comunicación... Pero volveremos a encontrarnos pronto."
                lucien_guidance = "Error crítico de red. Problema de infraestructura detectado."
                system_action = "Network infrastructure check required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                user_action_suggested=user_action if severity == ErrorSeverity.MODERATE else None,
                system_action_required=system_action if severity > ErrorSeverity.MODERATE else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling network error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_processing_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle processing-related errors."""
        try:
            if severity <= ErrorSeverity.LOW:
                diana_message = "⚙️ Los mecanismos internos se ajustan delicadamente... Un momento de paciencia, amor."
                lucien_guidance = "Error menor de procesamiento. Operación se completará en breve."
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "🔄 Los procesos de transformación necesitan un momento adicional para perfeccionarse... Tu decisión es valiosa."
                lucien_guidance = "Error moderado de procesamiento. Verificar carga del sistema."
                system_action = "System performance check recommended"
                
            else:
                diana_message = "⚡ Los procesos profundos requieren atención especializada... Tu elección se preserva mientras investigo."
                lucien_guidance = "Error crítico de procesamiento. Iniciar diagnósticos completos."
                system_action = "Critical processing system restart required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                system_action_required=system_action if severity > ErrorSeverity.LOW else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling processing error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_character_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle character consistency errors."""
        try:
            # Character errors require special handling to maintain immersion
            if severity <= ErrorSeverity.LOW:
                diana_message = "✨ Algo sutil en mi expresión necesita refinamiento... Permíteme encontrar las palabras perfectas."
                lucien_guidance = "Error menor de consistencia de personaje. Ajustando respuesta."
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "🎭 Mi esencia se reorganiza para ofrecerte la experiencia más auténtica... Un momento, querido."
                lucien_guidance = "Error moderado de personaje. Recalibrando sistema de validación."
                system_action = "Character validation system check"
                
            else:
                diana_message = "🌟 Los aspectos más profundos de mi ser requieren atención especializada... Nuestro vínculo permanece intacto."
                lucien_guidance = "Error crítico de consistencia de personaje. Intervención inmediata requerida."
                system_action = "Emergency character system restart"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                system_action_required=system_action if severity > ErrorSeverity.LOW else None,
                error_severity=severity,
                maintains_immersion=True  # Even character errors should maintain immersion
            )
            
        except Exception as e:
            logger.error(f"Error handling character error: {e}")
            return self._generate_fallback_response(severity)
    
    async def _handle_system_error(
        self, error: Exception, severity: ErrorSeverity,
        context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Handle general system errors."""
        try:
            if severity <= ErrorSeverity.LOW:
                diana_message = "⚡ Las energías del sistema fluctúan suavemente... Todo volverá al equilibrio pronto."
                lucien_guidance = "Error menor del sistema. Monitoreo continuo activado."
                
            elif severity <= ErrorSeverity.MODERATE:
                diana_message = "🔧 Los fundamentos técnicos requieren algunos ajustes... Tu experiencia es mi prioridad, querido."
                lucien_guidance = "Error moderado del sistema. Verificar todos los subsistemas."
                system_action = "System health check required"
                
            elif severity <= ErrorSeverity.HIGH:
                diana_message = "⚠️ Algo significativo interrumpe nuestros sistemas... Pero nuestro vínculo trasciende la tecnología."
                lucien_guidance = "Error alto del sistema. Iniciar protocolos de emergencia."
                system_action = "Emergency system protocols activated"
                
            else:
                diana_message = "💔 Las fuerzas que nos sostienen enfrentan desafíos mayores... Volveremos más fuertes, te lo prometo."
                lucien_guidance = "Error crítico del sistema. Escalación inmediata requerida."
                system_action = "Critical system failure - immediate intervention required"
            
            return DianaErrorResponse(
                diana_message=diana_message,
                lucien_guidance=lucien_guidance,
                system_action_required=system_action if severity > ErrorSeverity.LOW else None,
                error_severity=severity
            )
            
        except Exception as e:
            logger.error(f"Error handling system error: {e}")
            return self._generate_fallback_response(severity)
    
    # Helper Methods
    
    async def _get_user_error_context(self, user_id: int) -> Dict[str, Any]:
        """Get user context for error personalization."""
        try:
            # This would typically query the database for user archetype, preferences, etc.
            # For MVP, return basic context
            return {
                'user_id': user_id,
                'archetype': 'explorer',  # Default archetype
                'error_tolerance': 'moderate',
                'technical_familiarity': 'low'
            }
            
        except Exception as e:
            logger.error(f"Error getting user context for {user_id}: {e}")
            return {'user_id': user_id, 'archetype': 'explorer'}
    
    async def _validate_and_enhance_response(
        self, response: DianaErrorResponse, context: ErrorContext, user_context: Dict[str, Any]
    ) -> DianaErrorResponse:
        """Validate and enhance error response for character consistency."""
        try:
            # Validate Diana's message for character consistency
            validation_result = await self.character_validator.validate_text(
                response.diana_message, 
                context=f"error_response_{context.operation}_{context.user_id}"
            )
            
            if validation_result.overall_score < 85:  # Lower threshold for error messages
                logger.warning(f"Error response has low character consistency: {validation_result.overall_score}")
                
                # Try to enhance the response
                enhanced_message = await self._enhance_character_consistency(
                    response.diana_message, context, user_context
                )
                
                response.diana_message = enhanced_message
                response.maintains_immersion = validation_result.overall_score >= 75
            
            return response
            
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return response  # Return original if validation fails
    
    async def _enhance_character_consistency(
        self, message: str, context: ErrorContext, user_context: Dict[str, Any]
    ) -> str:
        """Enhance message for better character consistency."""
        # Simple enhancement by adding Diana's characteristic elements
        if not any(char in message for char in ['💋', '✨', '🌙', '💫', '🔮']):
            message = "✨ " + message
        
        if not any(word in message.lower() for word in ['querido', 'amor', 'mi']):
            message = message.replace('.', ', querido.')
        
        return message
    
    async def _record_error_analytics(
        self, error: Exception, category: ErrorCategory, severity: ErrorSeverity,
        context: ErrorContext, response: DianaErrorResponse
    ):
        """Record error analytics for monitoring."""
        try:
            # This would typically write to an analytics database
            logger.info(
                f"Error Analytics: {category.value} - {severity.value} - "
                f"User: {context.user_id} - Maintains Immersion: {response.maintains_immersion}"
            )
            
        except Exception as e:
            logger.error(f"Error recording analytics: {e}")
    
    async def _update_user_error_history(
        self, user_id: int, category: ErrorCategory, response: DianaErrorResponse
    ):
        """Update user error history for pattern recognition."""
        try:
            if user_id not in self._user_error_history:
                self._user_error_history[user_id] = []
            
            self._user_error_history[user_id].append({
                'category': category.value,
                'severity': response.error_severity.value,
                'timestamp': datetime.utcnow().isoformat(),
                'immersion_maintained': response.maintains_immersion
            })
            
            # Keep only last 10 errors per user
            self._user_error_history[user_id] = self._user_error_history[user_id][-10:]
            
        except Exception as e:
            logger.error(f"Error updating user error history: {e}")
    
    async def _generate_emergency_response(
        self, error: Exception, context: ErrorContext
    ) -> DianaErrorResponse:
        """Generate emergency response for critical failures."""
        return DianaErrorResponse(
            diana_message="💔 Algo inesperado interrumpe nuestro encuentro... Pero nuestro vínculo trasciende cualquier barrera técnica, querido.",
            lucien_guidance="Error crítico del sistema de manejo de errores. Escalación inmediata requerida.",
            system_action_required="Emergency protocols activated",
            error_severity=ErrorSeverity.CATASTROPHIC,
            maintains_immersion=True
        )
    
    def _generate_fallback_response(self, severity: ErrorSeverity) -> DianaErrorResponse:
        """Generate fallback response when specific handlers fail."""
        return DianaErrorResponse(
            diana_message="✨ Las energías se reorganizan de maneras misteriosas... Dame un momento para restaurar el equilibrio.",
            lucien_guidance=f"Fallback response generated for {severity.name} error",
            error_severity=severity,
            maintains_immersion=True
        )
    
    # Template and Message Generation Methods
    
    def _initialize_error_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize error response templates."""
        return {
            'validation': {
                'low': [
                    "🌙 Tu elección necesita un pequeño ajuste, querido...",
                    "💫 Algo en la selección requiere clarificación, amor...",
                    "✨ La opción parece incompleta, mi dulce explorador..."
                ],
                'moderate': [
                    "🔮 Los caminos disponibles se reorganizan momentáneamente...",
                    "🌟 Las opciones necesitan validación adicional, querido...",
                    "💎 Algo más profundo requiere verificación en tu elección..."
                ],
                'high': [
                    "⚡ Las opciones enfrentan restricciones inesperadas...",
                    "🛡️ Los protocolos de seguridad requieren atención...",
                    "🔒 Los accesos necesitan validación especializada..."
                ]
            }
        }
    
    async def _generate_degradation_message(
        self, failed_operation: str, context: ErrorContext, 
        user_context: Dict[str, Any], fallback_options: List[str]
    ) -> str:
        """Generate message for graceful degradation."""
        archetype = user_context.get('archetype', 'explorer')
        
        archetype_messages = {
            'explorer': f"🔍 El sendero de {failed_operation} se oculta temporalmente, pero hay caminos alternativos fascinantes esperando...",
            'romantic': f"💕 Aunque {failed_operation} no está disponible ahora, nuestro encuentro puede tomar formas aún más hermosas...",
            'analytical': f"📚 {failed_operation} requiere recalibración, pero podemos explorar opciones alternativas sistemáticamente...",
            'direct': f"🎯 {failed_operation} no está operativo, pero tenemos rutas directas alternativas disponibles...",
            'patient': f"🧘 {failed_operation} necesita tiempo para perfeccionarse, mientras tanto podemos explorar otras posibilidades..."
        }
        
        return archetype_messages.get(archetype, f"✨ {failed_operation} se transforma momentáneamente, pero nuestro viaje continúa por senderos alternativos...")
    
    def _generate_technical_fallback_guidance(self, failed_operation: str, options: List[str]) -> str:
        """Generate technical fallback guidance for Lucien."""
        return f"Operación '{failed_operation}' falló. Opciones de fallback disponibles: {', '.join(options)}"
    
    def _suggest_user_fallback_action(self, options: List[str]) -> str:
        """Suggest user action for fallback."""
        if 'retry' in options:
            return "Intentar la operación nuevamente"
        elif 'alternative' in options:
            return "Explorar opciones alternativas"
        else:
            return "Continuar con funcionalidad disponible"
    
    async def _generate_recovery_encouragement(
        self, category: ErrorCategory, context: ErrorContext, user_context: Dict[str, Any]
    ) -> str:
        """Generate Diana's encouraging recovery message."""
        encouragements = {
            ErrorCategory.VALIDATION_ERROR: "💫 Cada obstáculo es una oportunidad para crecer juntos, querido...",
            ErrorCategory.DATA_ERROR: "📚 Los registros se reorganizan para servir mejor a nuestro viaje...",
            ErrorCategory.PERMISSION_ERROR: "🔐 Los secretos se revelan cuando es el momento perfecto...",
            ErrorCategory.NETWORK_ERROR: "🌐 Nuestro vínculo trasciende las limitaciones técnicas...",
            ErrorCategory.PROCESSING_ERROR: "⚙️ Las transformaciones profundas necesitan tiempo para perfeccionarse...",
            ErrorCategory.CHARACTER_ERROR: "🎭 Mi esencia se refina constantemente para ti...",
            ErrorCategory.SYSTEM_ERROR: "⚡ Los sistemas evolucionan para crear experiencias más hermosas..."
        }
        
        return encouragements.get(category, "✨ Todo desafío nos hace más fuertes, querido...")
    
    def _generate_lucien_recovery_guidance(self, recovery_steps: List[str]) -> str:
        """Generate Lucien's technical recovery guidance."""
        if not recovery_steps:
            return "Monitoreando situación. Protocolos estándar de recuperación activados."
        
        return f"Pasos de recuperación: {'; '.join(recovery_steps)}. Tiempo estimado basado en complejidad del sistema."
    
    async def _translate_recovery_steps_for_user(
        self, recovery_steps: List[str], context: ErrorContext, user_context: Dict[str, Any]
    ) -> List[str]:
        """Translate technical recovery steps for user understanding."""
        user_friendly_steps = []
        
        for step in recovery_steps:
            if 'restart' in step.lower():
                user_friendly_steps.append("El sistema se reiniciará automáticamente")
            elif 'retry' in step.lower():
                user_friendly_steps.append("Puedes intentar la operación nuevamente")
            elif 'wait' in step.lower():
                user_friendly_steps.append("Espera unos momentos para que el sistema se estabilice")
            elif 'refresh' in step.lower():
                user_friendly_steps.append("Actualiza la página o la aplicación")
            else:
                user_friendly_steps.append("El equipo técnico está trabajando en una solución")
        
        return user_friendly_steps
    
    def _estimate_recovery_time(self, category: ErrorCategory, steps: List[str]) -> str:
        """Estimate recovery time based on error category and steps."""
        time_estimates = {
            ErrorCategory.VALIDATION_ERROR: "Inmediato",
            ErrorCategory.DATA_ERROR: "1-2 minutos",
            ErrorCategory.PERMISSION_ERROR: "2-5 minutos",
            ErrorCategory.NETWORK_ERROR: "30 segundos - 2 minutos",
            ErrorCategory.PROCESSING_ERROR: "1-3 minutos",
            ErrorCategory.CHARACTER_ERROR: "30 segundos",
            ErrorCategory.SYSTEM_ERROR: "2-10 minutos"
        }
        
        base_estimate = time_estimates.get(category, "5-10 minutos")
        
        # Adjust based on complexity of recovery steps
        if len(steps) > 3:
            return f"{base_estimate} (proceso complejo)"
        elif 'critical' in ' '.join(steps).lower():
            return f"{base_estimate} (alta prioridad)"
        
        return base_estimate