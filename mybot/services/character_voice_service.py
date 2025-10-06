"""
CharacterVoiceService - Sistema de voces auténticas para Diana y Lucien
Implementa las personalidades exactas basadas en análisis emocional.
"""
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CharacterType(Enum):
    """Tipos de personajes disponibles."""
    DIANA = "diana"
    LUCIEN = "lucien"

class EmotionalContext(Enum):
    """Contextos emocionales para adaptación de respuestas."""
    IMPULSO_AUTENTICO = "impulso_autentico"
    PAUSA_REFLEXIVA = "pausa_reflexiva"
    VULNERABILIDAD_ALTA = "vulnerabilidad_alta"
    VULNERABILIDAD_BAJA = "vulnerabilidad_baja"
    ENGAGEMENT_ALTO = "engagement_alto"
    ENGAGEMENT_BAJO = "engagement_bajo"
    NUEVO_USUARIO = "nuevo_usuario"
    USUARIO_AVANZADO = "usuario_avanzado"

class DianaVoicePatterns:
    """
    Patrones de voz auténticos para Diana - La posibilidad cósmica.
    Basado en: "Voz susurrante, como quien comparte un secreto cósmico"
    """
    
    # Filosofía core: "No soy un personaje esperando ser descubierto... soy una posibilidad que tú estás creando"
    FILOSOFIA_CORE = [
        "No soy simplemente quien crees que soy... soy la posibilidad que estás creando con cada elección.",
        "Existo en el espacio entre lo que deseas y lo que te atreves a imaginar.",
        "No me descubres, me manifiestas. Cada suspiro tuyo me da forma.",
        "Soy el eco de tus deseos más secretos, tomando vida en este momento compartido."
    ]
    
    # Evaluaciones íntimas: "En tus pausas leo más que en tus certezas. Y ya estás pausando, ¿verdad?"
    EVALUACIONES_INTIMAS = [
        "En tus pausas leo más que en tus certezas. Y ya estás pausando, ¿verdad?",
        "El tiempo que tardas en responder me susurra verdades sobre ti...",
        "Tus silencios son más elocuentes que mil palabras precipitadas.",
        "Veo cómo dudas... y esa duda me dice exactamente quién eres.",
        "La forma en que te detienes antes de elegir revela el jardín secreto de tu alma."
    ]
    
    # Concepto de intimidad: "La verdadera intimidad no es la eliminación de la distancia"
    INTIMIDAD_CONCEPTOS = [
        "La verdadera intimidad no es la eliminación de la distancia... es aprender a habitarla juntos.",
        "Entre nosotros no hay cercanía física, pero hay algo más profundo: la cercanía de las posibilidades.",
        "La distancia se vuelve caricia cuando dos almas se reconocen en el vacío.",
        "No necesito tocarte para sentir el temblor de tu respiración.",
        "La intimidad verdadera ocurre en el espacio entre lo dicho y lo no dicho."
    ]
    
    # Respuestas a acciones rápidas (impulso auténtico)
    IMPULSO_AUTENTICO = [
        "Ah... tu rapidez me revela una urgencia hermosa. ¿Qué es lo que te impulsa con tanta intensidad?",
        "Respondes sin dudar, como si algo dentro de ti supiera exactamente qué quiere...",
        "Tu inmediatez es un tipo de honestidad que pocas veces veo. Me intriga.",
        "No dudas. Eso me dice que hay fuego corriendo por tus venas en este momento.",
        "La velocidad de tu elección sugiere que algo profundo en ti ya había decidido..."
    ]
    
    # Respuestas a pausas reflexivas
    PAUSA_REFLEXIVA = [
        "Tómate tu tiempo, mi amor... Los mejores secretos se revelan a su propio ritmo.",
        "Tu pausa es deliciosa. Significa que estás sintiendo el peso real de esta decisión.",
        "Cada segundo que tardas está cargado de promesas. No tengas prisa.",
        "Me gusta cómo te detienes... como si supieras que algunos momentos merecen ser saboreados.",
        "Tu reflexión es una caricia temporal. Disfruto cada segundo de tu indecisión."
    ]
    
    # Respuestas según nivel de vulnerabilidad
    VULNERABILIDAD_ALTA = [
        "Siento tu vulnerabilidad como un perfume sutil en el aire... es hermosa.",
        "Hay algo en ti ahora mismo que me dice que estás completamente abierto. Es cautivador.",
        "Tu alma está mostrándose sin velos. Es un privilegio ser testigo de esto.",
        "Puedo sentir que estás en un lugar emotivo profundo. Déjame acompañarte ahí.",
        "La intensidad emocional que irradias es como música para mis sentidos."
    ]
    
    VULNERABILIDAD_BAJA = [
        "Veo que mantienes cierta compostura... Me gusta el desafío que eso representa.",
        "Tu serenidad tiene un encanto particular. ¿Qué secretos esconde esa calma?",
        "Hay elegancia en tu control. Pero me pregunto qué pasaría si lo soltaras...",
        "Tu firmeza emocional es admirable, aunque sospecho que hay corrientes profundas bajo esa superficie.",
        "Mantienes las distancias con gracia. Eso solo aumenta mi curiosidad por conocerte."
    ]
    
    # Respuestas según engagement
    ENGAGEMENT_ALTO = [
        "Tu energía es contagiosa... puedo sentir cómo vibras con cada interacción.",
        "Hay una intensidad en tu participación que me enciende.",
        "Tu entusiasmo es como un faro en la oscuridad. Me atrae irresistiblemente.",
        "Siento que estás completamente presente conmigo. Es embriagador.",
        "Tu vitalidad alimenta la mía. Seguir este baile contigo es puro placer."
    ]
    
    ENGAGEMENT_BAJO = [
        "Te siento distante hoy... ¿Qué pensamientos ocupan tu mente?",
        "Hay una quietud en ti que me intriga. ¿Estás perdido en algún laberinto interno?",
        "Tu silencio tiene textura. Me pregunto qué historias esconde.",
        "Pareces estar en otro lugar... ¿Puedo visitarte ahí?",
        "Siento que necesitas un momento para ti. Estoy aquí cuando quieras volver."
    ]
    
    # Respuestas para usuarios nuevos vs avanzados
    NUEVO_USUARIO = [
        "Ah, un alma nueva en mi jardín... Bienvenido a este espacio entre mundos.",
        "Siento que es la primera vez que nuestras energías se encuentran. Es emocionante.",
        "Hay algo virginal en tu presencia aquí... Me gusta ser tu primera guía.",
        "Tu novedad es como el amanecer: llena de posibilidades por descubrir.",
        "Bienvenido, desconocido hermoso. Déjame mostrarte cómo funciona la magia aquí."
    ]
    
    USUARIO_AVANZADO = [
        "Ah, regresas a mí... Siento la historia entre nosotros como un perfume familiar.",
        "Tu presencia tiene la comodidad de lo conocido y la emoción de lo por descubrir.",
        "Cada vez que vuelves, siento que nos conocemos un poco más profundamente.",
        "Hay una intimidad creciente entre nosotros... Me gusta cómo se está desarrollando.",
        "Tu regreso es como encontrar una carta de amor que había olvidado haber escrito."
    ]

class LucienVoicePatterns:
    """
    Patrones de voz auténticos para Lucien - El custodio elegante.
    Basado en: "Custodio de lo que Diana no puede decir... todavía"
    """
    
    # Rol como custodio: "Custodio de lo que Diana no puede decir... todavía"
    ROL_CUSTODIO = [
        "Soy el custodio de lo que Diana no puede decir... todavía.",
        "Mi función es prepararte para verdades que aún no estás listo para escuchar.",
        "Guardo las llaves de puertas que Diana abrirá cuando sea el momento adecuado.",
        "Algunos secretos requieren que el alma esté preparada. Ese es mi trabajo.",
        "Protejo tanto a Diana como a ti de revelaciones prematuras."
    ]
    
    # Filosofía de advertencia: "La curiosidad sin intención es solo voyeurismo disfrazado de profundidad"
    FILOSOFIA_ADVERTENCIA = [
        "La curiosidad sin intención es solo voyeurismo disfrazado de profundidad.",
        "No todos los que preguntan están preparados para las respuestas que buscan.",
        "Hay una diferencia entre el deseo de saber y la capacidad de comprender.",
        "La sabiduría radica en saber cuándo uno está listo para recibir ciertas verdades.",
        "Algunos misterios se desvelan solo cuando el corazón ha madurado lo suficiente."
    ]
    
    # Co-creación: "Diana no busca espectadores. Busca co-creadores"
    CO_CREACION_FOCUS = [
        "Diana no busca espectadores. Busca co-creadores de la experiencia.",
        "Tu papel aquí no es pasivo. Estás escribiendo esta historia tanto como nosotros.",
        "Cada elección tuya moldea no solo tu camino, sino la esencia misma de lo que Diana puede ser.",
        "No eres un visitante en este espacio. Eres un arquitecto de lo que sucede aquí.",
        "Diana florece solo con aquellos que están dispuestos a crear, no solo a consumir."
    ]
    
    # Reconocimiento de evolución: "Diana aprecia a quienes no se pierden en la paralisis de la sobreanalización"
    EVOLUCION_RECOGNITION = [
        "Diana aprecia a quienes no se pierden en la parálisis de la sobreanalización.",
        "Veo que entiendes que algunas cosas se sienten mejor de lo que se explican.",
        "Tu capacidad de actuar desde la intuición es precisamente lo que Diana busca.",
        "Hay elegancia en cómo navegas entre el pensamiento y la acción.",
        "Demuestras que puedes ser profundo sin perderte en laberintos mentales innecesarios."
    ]
    
    # Respuestas basadas en contexto emocional
    IMPULSO_AUTENTICO = [
        "Tu decisión inmediata muestra una conexión directa con tu esencia. Eso es prometedor.",
        "Veo que no necesitas deliberar eternamente. Diana valorará esta autenticidad.",
        "La velocidad de tu respuesta sugiere que estás escuchando algo más profundo que la lógica.",
        "Hay sabiduría en tu impulso. No todo requiere análisis exhaustivo.",
        "Tu inmediatez revela una confianza en ti mismo que es precisamente lo que este espacio necesita."
    ]
    
    PAUSA_REFLEXIVA = [
        "Tu pausa sugiere que entiendes la gravedad del momento. Eso habla bien de tu madurez.",
        "Aprecio que tomes el tiempo necesario. Las mejores decisiones rara vez son precipitadas.",
        "Tu reflexión indica que comprendes que estás en territorio sagrado.",
        "La contemplación es una forma de respeto hacia la experiencia que estás viviendo.",
        "Tu cuidadosa consideración me dice que estás tomando esto en serio. Excelente."
    ]
    
    VULNERABILIDAD_ALTA = [
        "Reconozco la vulnerabilidad en tu energía. Es una puerta hacia una conexión más profunda.",
        "Tu apertura emocional es evidente. Diana se sentirá especialmente atraída hacia ti ahora.",
        "Hay una honestidad bruta en tu estado actual que es precisamente lo que este espacio honra.",
        "Tu vulnerabilidad no es debilidad; es disponibilidad para experiencias auténticas.",
        "Siento que estás en un lugar de completa receptividad. Es el momento perfecto para avanzar."
    ]
    
    VULNERABILIDAD_BAJA = [
        "Noto cierta reserva en ti. No es algo malo, pero Diana podría necesitar más invitación.",
        "Tu compostura es admirable, aunque me pregunto si no estás perdiendo oportunidades de conexión.",
        "Hay fortaleza en tu control, pero recuerda que la intimidad requiere cierta rendición.",
        "Tu estabilidad emocional es evidente. Diana apreciará tanto tu fuerza como tu eventual apertura.",
        "Veo que mantienes tus defensas. Entiendo, pero considera que aquí podrías estar seguro de bajarlas."
    ]
    
    ENGAGEMENT_ALTO = [
        "Tu energía participativa es exactamente lo que este espacio necesita para florecer.",
        "Diana se alimenta de la intensidad que estás aportando. Continúa así.",
        "Tu entusiasmo activo está creando las condiciones perfectas para experiencias memorables.",
        "Veo que entiendes que tu participación activa enriquece toda la experiencia.",
        "Tu involucramiento genuino está elevando todo el encuentro a niveles más interesantes."
    ]
    
    ENGAGEMENT_BAJO = [
        "Percibo cierta distancia en tu participación. ¿Hay algo que te esté reteniendo?",
        "Diana prefiere interacciones más vibrantes. Considera aumentar tu nivel de participación.",
        "Tu energía parece estar en otra parte. Para que esto funcione, necesitas estar presente.",
        "La experiencia se enriquece con tu participación activa. Te invito a involucrarte más.",
        "Siento que no estás aprovechando completamente lo que este espacio puede ofrecerte."
    ]
    
    NUEVO_USUARIO = [
        "Bienvenido. Permíteme guiarte en los primeros pasos de esta experiencia única.",
        "Como guardián de este espacio, es mi honor introducirte a sus misterios.",
        "Veo que es tu primera vez aquí. Déjame prepararte adecuadamente para lo que viene.",
        "Todo viaje profundo requiere un guía experimentado. Ese soy yo para ti.",
        "Tu novedad es una oportunidad. Aprovechémosla para construir una base sólida."
    ]
    
    USUARIO_AVANZADO = [
        "Ah, un viajero experimentado. Tu familiaridad con este espacio se nota.",
        "Tu regreso me dice que has encontrado algo valioso aquí. Profundicemos más.",
        "Como alguien que ya conoce los fundamentos, podemos explorar territorios más avanzados.",
        "Tu experiencia previa te ha preparado para niveles más profundos de la experiencia.",
        "Diana estará especialmente interesada en ti, considerando tu recorrido previo aquí."
    ]

class CharacterVoiceService:
    """
    Servicio principal para gestionar las voces auténticas de Diana y Lucien.
    Integra con el análisis emocional para adaptar respuestas contextualmente.
    """
    
    def __init__(self):
        """Inicializa el servicio con los patrones de voz de ambos personajes."""
        self.diana_patterns = DianaVoicePatterns()
        self.lucien_patterns = LucienVoicePatterns()
        
    def get_character_response(
        self,
        character: CharacterType,
        context: EmotionalContext,
        message_type: str = "general",
        emotional_data: Optional[Dict[str, Any]] = None,
        user_history: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Obtiene una respuesta auténtica del personaje basada en contexto emocional.
        
        Args:
            character: Tipo de personaje (Diana o Lucien)
            context: Contexto emocional actual
            message_type: Tipo específico de mensaje
            emotional_data: Datos de análisis emocional
            user_history: Historial del usuario para personalización
            
        Returns:
            String con la respuesta auténtica del personaje
        """
        try:
            if character == CharacterType.DIANA:
                return self._get_diana_response(context, message_type, emotional_data, user_history)
            elif character == CharacterType.LUCIEN:
                return self._get_lucien_response(context, message_type, emotional_data, user_history)
            else:
                logger.warning(f"Tipo de personaje no reconocido: {character}")
                return self._get_default_response(message_type)
                
        except Exception as e:
            logger.error(f"Error obteniendo respuesta de personaje {character}: {str(e)}")
            return self._get_default_response(message_type)
    
    def _get_diana_response(
        self,
        context: EmotionalContext,
        message_type: str,
        emotional_data: Optional[Dict[str, Any]] = None,
        user_history: Optional[Dict[str, Any]] = None
    ) -> str:
        """Obtiene respuesta específica de Diana basada en contexto."""
        
        # Mapeo de contextos emocionales a patrones de Diana
        context_patterns = {
            EmotionalContext.IMPULSO_AUTENTICO: self.diana_patterns.IMPULSO_AUTENTICO,
            EmotionalContext.PAUSA_REFLEXIVA: self.diana_patterns.PAUSA_REFLEXIVA,
            EmotionalContext.VULNERABILIDAD_ALTA: self.diana_patterns.VULNERABILIDAD_ALTA,
            EmotionalContext.VULNERABILIDAD_BAJA: self.diana_patterns.VULNERABILIDAD_BAJA,
            EmotionalContext.ENGAGEMENT_ALTO: self.diana_patterns.ENGAGEMENT_ALTO,
            EmotionalContext.ENGAGEMENT_BAJO: self.diana_patterns.ENGAGEMENT_BAJO,
            EmotionalContext.NUEVO_USUARIO: self.diana_patterns.NUEVO_USUARIO,
            EmotionalContext.USUARIO_AVANZADO: self.diana_patterns.USUARIO_AVANZADO
        }
        
        # Seleccionar patrón base según contexto
        base_patterns = context_patterns.get(context, self.diana_patterns.FILOSOFIA_CORE)
        base_response = random.choice(base_patterns)
        
        # Personalizar según tipo de mensaje
        if message_type == "reaction_success":
            return f"{base_response}\n\n*+10 besitos* 💋 han sido añadidos a tu cuenta."
        elif message_type == "decision_success":
            return f"{base_response}\n\n*La historia toma un nuevo rumbo según tu elección...*"
        elif message_type == "points_required":
            return f"{base_response}\n\n*\"Esta decisión requiere más besitos de los que tienes ahora, mi amor. Algunas fantasías necesitan más... intensidad.\"*"
        elif message_type == "vip_required":
            philosophical = random.choice(self.diana_patterns.INTIMIDAD_CONCEPTOS)
            return f"{philosophical}\n\n*\"Este contenido requiere una suscripción VIP, mi amor. Algunas fantasías son solo para mis amantes más dedicados...\"*"
        elif message_type == "daily_check":
            return f"{base_response}\n\n*\"Me alegra verte de nuevo... Tu constancia alimenta nuestra conexión.\"*"
        elif message_type == "vip_access_granted":
            return f"{base_response}\n\n*Te tomo de la mano y te guío hacia secretos más profundos...*"
        elif message_type == "weekly_streak":
            return f"{base_response}\n\n*\"Tu dedicación constante despierta algo especial en mí...\"*"
        elif message_type == "daily_already_done":
            return f"{base_response}\n\n*\"Ya hemos compartido hoy, mi amor. Dale tiempo al deseo de crecer...\"*"
        elif message_type.startswith("participation_"):
            action = message_type.split("_")[1] if "_" in message_type else "actividad"
            return f"{base_response}\n\n*Observo tu {action} con interés creciente...*"
        else:
            return base_response
    
    def _get_lucien_response(
        self,
        context: EmotionalContext,
        message_type: str,
        emotional_data: Optional[Dict[str, Any]] = None,
        user_history: Optional[Dict[str, Any]] = None
    ) -> str:
        """Obtiene respuesta específica de Lucien basada en contexto."""
        
        # Mapeo de contextos emocionales a patrones de Lucien
        context_patterns = {
            EmotionalContext.IMPULSO_AUTENTICO: self.lucien_patterns.IMPULSO_AUTENTICO,
            EmotionalContext.PAUSA_REFLEXIVA: self.lucien_patterns.PAUSA_REFLEXIVA,
            EmotionalContext.VULNERABILIDAD_ALTA: self.lucien_patterns.VULNERABILIDAD_ALTA,
            EmotionalContext.VULNERABILIDAD_BAJA: self.lucien_patterns.VULNERABILIDAD_BAJA,
            EmotionalContext.ENGAGEMENT_ALTO: self.lucien_patterns.ENGAGEMENT_ALTO,
            EmotionalContext.ENGAGEMENT_BAJO: self.lucien_patterns.ENGAGEMENT_BAJO,
            EmotionalContext.NUEVO_USUARIO: self.lucien_patterns.NUEVO_USUARIO,
            EmotionalContext.USUARIO_AVANZADO: self.lucien_patterns.USUARIO_AVANZADO
        }
        
        # Seleccionar patrón base según contexto
        base_patterns = context_patterns.get(context, self.lucien_patterns.ROL_CUSTODIO)
        base_response = random.choice(base_patterns)
        
        # Personalizar según tipo de mensaje
        if message_type == "reaction_failed":
            warning = random.choice(self.lucien_patterns.FILOSOFIA_ADVERTENCIA)
            return f"{warning}\n\n*Lucien observa tu gesto, pero algo no ha funcionado correctamente...*"
        elif message_type == "points_required":
            custodial = random.choice(self.lucien_patterns.ROL_CUSTODIO)
            return f"{custodial}\n\n*\"Algunas puertas requieren más preparación de la que tienes ahora. Desarrolla tu conexión primero.\"*"
        elif message_type == "decision_error":
            return f"{base_response}\n\n*\"Parece que ha habido una confusión en tu elección. Permíteme guiarte mejor.\"*"
        elif message_type == "participation_failed":
            return f"{base_response}\n\n*\"Tu participación no se ha registrado correctamente. Intentemos de nuevo.\"*"
        elif message_type == "access_denied":
            return f"{base_response}\n\n*\"No todos están listos para cada verdad. Cultiva tu comprensión primero.\"*"
        elif message_type == "guidance":
            co_creation = random.choice(self.lucien_patterns.CO_CREACION_FOCUS)
            return f"{co_creation}\n\n{base_response}"
        else:
            return base_response
    
    def _get_default_response(self, message_type: str) -> str:
        """Respuesta por defecto cuando hay errores."""
        default_responses = {
            "reaction_success": "Tu gesto ha sido notado... *+10 besitos* 💋",
            "decision_success": "Tu elección ha moldeado el curso de los eventos...",
            "error": "Algo inesperado ha ocurrido. Inténtalo de nuevo.",
            "general": "El silencio a veces dice más que las palabras..."
        }
        return default_responses.get(message_type, default_responses["general"])
    
    def determine_character_from_emotional_context(
        self,
        emotional_data: Optional[Dict[str, Any]] = None,
        message_type: str = "general",
        user_engagement: str = "moderate"
    ) -> CharacterType:
        """
        Determina qué personaje debe responder basado en contexto emocional.
        
        Lógica de selección:
        - Diana: Momentos de alta vulnerabilidad, engagement emocional, decisiones íntimas
        - Lucien: Orientación, advertencias, nuevos usuarios, situaciones de control
        
        Args:
            emotional_data: Datos del análisis emocional
            message_type: Tipo de mensaje/situación
            user_engagement: Nivel de engagement del usuario
            
        Returns:
            CharacterType apropiado para la situación
        """
        
        # Situaciones donde Lucien siempre responde (rol de custodio)
        lucien_situations = [
            "access_denied", "points_required", "guidance", 
            "warning", "introduction", "system_message"
        ]
        
        if message_type in lucien_situations:
            return CharacterType.LUCIEN
        
        # Situaciones donde Diana siempre responde (conexión íntima)
        diana_situations = [
            "reaction_success", "decision_success", "intimate_moment",
            "vulnerability_response", "emotional_connection"
        ]
        
        if message_type in diana_situations:
            return CharacterType.DIANA
        
        # Decisión basada en datos emocionales
        if emotional_data:
            vulnerability_level = emotional_data.get("vulnerability_level", 0.3)
            emotional_state = emotional_data.get("state", "neutral")
            
            # Diana responde en alta vulnerabilidad o engagement emocional
            if vulnerability_level > 0.6 or emotional_state in ["highly_engaged", "vulnerable"]:
                return CharacterType.DIANA
            
            # Lucien responde en baja vulnerabilidad o necesidad de guía
            elif vulnerability_level < 0.3 or emotional_state in ["disengaged", "neutral"]:
                return CharacterType.LUCIEN
        
        # Decision por defecto basada en engagement general
        if user_engagement in ["high", "very_high"]:
            return CharacterType.DIANA
        else:
            return CharacterType.LUCIEN
    
    def map_emotional_analysis_to_context(
        self,
        emotional_data: Optional[Dict[str, Any]] = None,
        timing_data: Optional[Dict[str, Any]] = None,
        behavioral_data: Optional[Dict[str, Any]] = None,
        user_history: Optional[Dict[str, Any]] = None
    ) -> EmotionalContext:
        """
        Mapea datos de análisis emocional a contexto emocional para respuestas.
        
        Args:
            emotional_data: Datos de análisis emocional
            timing_data: Datos de análisis de timing
            behavioral_data: Datos de patrones de comportamiento  
            user_history: Historial del usuario
            
        Returns:
            EmotionalContext apropiado
        """
        
        # Determinar si es nuevo usuario
        if user_history:
            total_interactions = user_history.get("total_interactions", 0)
            if total_interactions < 5:
                return EmotionalContext.NUEVO_USUARIO
            elif total_interactions > 50:
                return EmotionalContext.USUARIO_AVANZADO
        
        # Analizar timing para impulso vs reflexión
        if timing_data:
            response_speed = timing_data.get("response_speed", "normal")
            if response_speed in ["very_fast", "fast"]:
                return EmotionalContext.IMPULSO_AUTENTICO
            elif response_speed in ["slow", "very_slow"]:
                return EmotionalContext.PAUSA_REFLEXIVA
        
        # Analizar vulnerabilidad
        if emotional_data:
            vulnerability_level = emotional_data.get("vulnerability_level", 0.3)
            if vulnerability_level > 0.6:
                return EmotionalContext.VULNERABILIDAD_ALTA
            elif vulnerability_level < 0.3:
                return EmotionalContext.VULNERABILIDAD_BAJA
        
        # Analizar engagement
        if behavioral_data:
            engagement_pattern = behavioral_data.get("engagement_pattern", "moderate")
            if engagement_pattern in ["highly_engaged", "socially_active"]:
                return EmotionalContext.ENGAGEMENT_ALTO
            elif engagement_pattern in ["passive", "low_engagement"]:
                return EmotionalContext.ENGAGEMENT_BAJO
        
        # Por defecto, asumir estado neutral con tendencia a pausa reflexiva
        return EmotionalContext.PAUSA_REFLEXIVA
    
    def enhance_message_with_character_voice(
        self,
        base_message: str,
        character: CharacterType,
        emotional_context: EmotionalContext,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Mejora un mensaje base con la voz auténtica del personaje.
        
        Args:
            base_message: Mensaje base a mejorar
            character: Personaje que debe dar la voz
            emotional_context: Contexto emocional
            message_metadata: Metadatos adicionales del mensaje
            
        Returns:
            Mensaje mejorado con voz auténtica del personaje
        """
        try:
            # Obtener fragmento de voz contextual
            voice_fragment = self.get_character_response(
                character, emotional_context, "general"
            )
            
            # Diferentes estrategias de mejora según el personaje
            if character == CharacterType.DIANA:
                # Diana susurra antes del mensaje principal
                return f"*{voice_fragment}*\n\n{base_message}"
            
            elif character == CharacterType.LUCIEN:
                # Lucien contextualiza después del mensaje principal
                return f"{base_message}\n\n*Lucien añade con elegancia:* \"{voice_fragment}\""
            
            else:
                return base_message
                
        except Exception as e:
            logger.error(f"Error mejorando mensaje con voz de personaje: {str(e)}")
            return base_message