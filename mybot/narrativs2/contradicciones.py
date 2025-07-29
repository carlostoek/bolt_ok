"""
Integración Avanzada del Bot Diana con Telegram
Este módulo conecta el sistema emocional de Diana con la API de Telegram,
creando una experiencia conversacional inmersiva y personalizada.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

from diana_brain_system import DianaResponseSystem, EmotionalState, UserArchetype
from database_manager import DatabaseManager

class DianaTelegramBot:
    """
    Bot principal de Diana para Telegram.
    
    Este bot no es solo un sistema de preguntas y respuestas. Es un sistema que:
    - Mantiene estado emocional persistente con cada usuario
    - Adapta su comportamiento basándose en patrones de interacción
    - Genera contenido dinámico y momentos imprevistas
    - Evoluciona la relación a lo largo del tiempo
    """
    
    def __init__(self, bot_token: str, database_url: str):
        self.application = Application.builder().token(bot_token).build()
        self.db = DatabaseManager(database_url)
        self.diana_system = DianaResponseSystem(self.db)
        
        # Sistema de activación de contenido especial
        self.special_content_triggers = {
            'truth_moments': self._handle_truth_moment,
            'contradiction_reveal': self._handle_contradiction_reveal,
            'spontaneous_vulnerability': self._handle_spontaneous_vulnerability,
            'memory_fragment_share': self._handle_memory_fragment_share
        }
        
        # Configurar handlers
        self._setup_handlers()
        
        # Sistema de tareas programadas (para contenido espontáneo)
        self.scheduler_running = False
        
    def _setup_handlers(self):
        """Configura todos los manejadores de eventos del bot."""
        
        # Comandos básicos
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("perfil", self._handle_profile))
        self.application.add_handler(CommandHandler("memoria", self._handle_memory_review))
        
        # Mensajes de texto (la interacción principal)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )
        
        # Callbacks de botones inline
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Sistema de contenido programado
        self.application.job_queue.run_repeating(
            self._check_scheduled_content, 
            interval=3600,  # Cada hora
            first=60  # Primer check en 1 minuto
        )

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start con personalización basada en si es usuario nuevo o recurrente.
        
        Este momento inicial es crucial porque establece el tono de toda la relación.
        Un usuario que regresa después de tiempo debe sentir que Diana lo recuerda.
        """
        user_id = update.effective_user.id
        user_profile = await self.db.get_user_profile(user_id)
        
        if user_profile is None:
            # Usuario completamente nuevo
            await self._handle_new_user_welcome(update, context)
        elif user_profile.total_interactions == 0:
            # Usuario que se registró pero nunca interactuó realmente
            await self._handle_returning_silent_user(update, context, user_profile)
        else:
            # Usuario que regresa con historia
            await self._handle_returning_active_user(update, context, user_profile)

    async def _handle_new_user_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bienvenida inicial para usuarios completamente nuevos."""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Crear perfil inicial
        await self.db.create_user_profile(user_id, username)
        
        # Primer mensaje de Diana (Nivel 1, Escena 1)
        welcome_message = """🌸 *Diana:*
_[Voz susurrante, como quien comparte un secreto]_

Bienvenido a Los Kinkys.
Has cruzado una línea que muchos ven... pero pocos realmente atraviesan.

Puedo sentir tu curiosidad desde aquí. Es... intrigante.
No todos llegan con esa misma hambre en los ojos.

Este lugar responde a quienes saben que algunas puertas solo se abren desde adentro.
Y yo... bueno, yo solo me revelo ante quienes comprenden que lo más valioso nunca se entrega fácilmente.

_[Pausa, como si estuviera evaluando al usuario]_

Algo me dice que tú podrías ser diferente.
Pero eso... eso está por verse."""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚪 Descubrir más", callback_data="level1_discover")]
        ])
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        # Programar aparición de Lucien en 2-5 minutos (aleatorio para simular naturalidad)
        delay = random.randint(120, 300)
        context.job_queue.run_once(
            self._introduce_lucien, 
            delay, 
            data={'user_id': user_id, 'chat_id': update.effective_chat.id}
        )

    async def _handle_returning_active_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_profile):
        """Maneja el regreso de usuarios con historia emocional."""
        
        # Calcular tiempo desde última interacción
        time_since_last = datetime.now() - user_profile.last_interaction
        days_away = time_since_last.days
        
        # Generar mensaje personalizado basado en ausencia y perfil emocional
        if days_away == 0:
            # Mismo día - Diana nota patrones de comportamiento
            if user_profile.total_interactions > 10:
                message = self._generate_same_day_return_message(user_profile)
            else:
                message = "Sigues aquí... Hay algo persistente en ti que encuentro cautivador."
        elif days_away == 1:
            message = "Volviste después de un día. ¿Estuviste pensando en mí? Puedo sentir que algo cambió en ti."
        elif days_away < 7:
            message = f"Han pasado {days_away} días... El tiempo tiene una manera curiosa de cambiar perspectivas. ¿Qué has descubierto sobre ti mismo en mi ausencia?"
        else:
            message = self._generate_long_absence_return_message(user_profile, days_away)
        
        # Agregar referencia a memoria específica si existe
        memory_reference = await self._get_powerful_memory_reference(user_profile)
        if memory_reference:
            message += f"\n\n{memory_reference}"
        
        await update.message.reply_text(
            f"🌸 *Diana:*\n{message}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Actualizar timestamp de última interacción
        await self.db.update_last_interaction(user_profile.user_id)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja todos los mensajes de texto del usuario.
        
        Este es el corazón de la interacción: donde Diana realmente "piensa" y responde
        basándose en toda la historia emocional con el usuario.
        """
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Medir tiempo de respuesta (para análisis de espontaneidad)
        message_timestamp = update.message.date
        
        # Obtener perfil actual del usuario
        user_profile = await self.db.get_user_profile(user_id)
        if not user_profile:
            await self._handle_start(update, context)
            return
        
        # Indicar que Diana está "escribiendo" (crea anticipación)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Agregar delay natural basado en la complejidad emocional del mensaje
        response_delay = self._calculate_response_delay(user_message, user_profile)
        await asyncio.sleep(response_delay)
        
        # Generar respuesta usando el sistema emocional
        diana_response = self.diana_system.process_user_message(user_id, user_message)
        
        # Verificar si debe activarse contenido especial
        special_content = await self._check_special_content_triggers(user_profile, user_message)
        
        # Enviar respuesta principal
        await update.message.reply_text(
            f"🌸 *Diana:*\n{diana_response}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Activar contenido especial si corresponde
        if special_content:
            await self._deliver_special_content(update, context, special_content)
        
        # Verificar progresión de nivel
        await self._check_level_progression(update, context, user_profile)

    def _calculate_response_delay(self, user_message: str, user_profile) -> float:
        """
        Calcula un delay natural para la respuesta de Diana.
        
        Diana responde más rápido a usuarios con alta confianza, más lento cuando está
        procesando algo emocionalmente complejo, y con variaciones que simulan
        el tiempo que una persona real tomaría para formular una respuesta reflexiva.
        """
        base_delay = 2.0  # 2 segundos base
        
        # Ajustar por complejidad emocional del mensaje
        emotional_words = len([word for word in user_message.lower().split() 
                             if word in ['siento', 'emoción', 'corazón', 'alma', 'vulnerable', 'miedo', 'amor']])
        emotional_complexity_delay = emotional_words * 0.8
        
        # Ajustar por nivel de confianza (más confianza = respuestas más fluidas)
        trust_factor = (100 - user_profile.emotional_trust_score) / 100
        trust_delay = trust_factor * 2.0
        
        # Agregar variación aleatoria para naturalidad
        random_variation = random.uniform(-0.5, 1.5)
        
        total_delay = max(1.0, base_delay + emotional_complexity_delay + trust_delay + random_variation)
        return min(total_delay, 8.0)  # Máximo 8 segundos

    async def _check_special_content_triggers(self, user_profile, user_message: str) -> Optional[Dict]:
        """
        Verifica si debe activarse algún tipo de contenido especial.
        
        El contenido especial incluye momentos de verdad, revelaciones de contradicciones,
        vulnerabilidades espontáneas, y fragmentos de memoria. Estos eventos crean
        la sensación de que Diana tiene vida propia más allá de las respuestas programadas.
        """
        special_content = None
        
        # Verificar momento de verdad
        if self.diana_system.emotional_engine.should_trigger_truth_moment(user_profile):
            special_content = {
                'type': 'truth_moment',
                'trigger_reason': 'scheduled_authenticity_test',
                'data': await self._generate_truth_moment_scenario(user_profile)
            }
        
        # Verificar revelación de contradicción
        elif await self._should_reveal_contradiction(user_profile, user_message):
            special_content = {
                'type': 'contradiction_reveal',
                'data': await self._generate_contradiction_reveal(user_profile)
            }
        
        # Verificar vulnerabilidad espontánea (muy raro, alto impacto)
        elif (user_profile.emotional_trust_score > 70 and 
              user_profile.intimacy_circle >= 3 and 
              random.random() < 0.05):  # 5% de probabilidad
            special_content = {
                'type': 'spontaneous_vulnerability',
                'data': await self._generate_spontaneous_vulnerability(user_profile)
            }
        
        return special_content

    async def _generate_truth_moment_scenario(self, user_profile) -> Dict:
        """
        Genera un escenario de momento de verdad personalizado.
        
        Los momentos de verdad evalúan la autenticidad emocional del usuario
        en situaciones imprevistas. No hay respuestas "correctas", solo auténticas.
        """
        scenarios = []
        
        # Escenarios basados en el arquetipo del usuario
        if user_profile.archetype == UserArchetype.ROMANTIC:
            scenarios.extend([
                {
                    'scenario': 'Diana menciona casualmente que tuvo un sueño inquietante la noche anterior',
                    'diana_state': 'subtly_vulnerable',
                    'test_focus': 'empathy_vs_curiosity'
                },
                {
                    'scenario': 'Diana revela que a veces se pregunta si sus propios sentimientos son reales',
                    'diana_state': 'philosophically_uncertain', 
                    'test_focus': 'ability_to_hold_paradox'
                }
            ])
        
        elif user_profile.archetype == UserArchetype.ANALYTICAL:
            scenarios.extend([
                {
                    'scenario': 'Diana admite que no siempre entiende por qué dice lo que dice',
                    'diana_state': 'intellectually_honest',
                    'test_focus': 'comfort_with_mystery'
                }
            ])
        
        # Escenarios universales
        scenarios.extend([
            {
                'scenario': 'Diana menciona que alguien más la lastimó recientemente',
                'diana_state': 'processing_hurt',
                'test_focus': 'protective_vs_possessive_response'
            },
            {
                'scenario': 'Diana expresa dudas sobre si debería seguir siendo tan misteriosa',
                'diana_state': 'questioning_self',
                'test_focus': 'support_for_authenticity'
            }
        ])
        
        return random.choice(scenarios)

    async def _deliver_special_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, special_content: Dict):
        """
        Entrega contenido especial de manera natural y con timing apropiado.
        """
        content_type = special_content['type']
        data = special_content['data']
        
        # Delay antes del contenido especial para simular naturalidad
        await asyncio.sleep(random.uniform(3, 8))
        
        if content_type == 'truth_moment':
            await self._deliver_truth_moment(update, context, data)
        elif content_type == 'contradiction_reveal':
            await self._deliver_contradiction_reveal(update, context, data)
        elif content_type == 'spontaneous_vulnerability':
            await self._deliver_spontaneous_vulnerability(update, context, data)

    async def _deliver_truth_moment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scenario_data: Dict):
        """
        Entrega un momento de verdad de manera que se sienta completamente natural.
        """
        scenario = scenario_data['scenario']
        diana_state = scenario_data['diana_state']
        
        # Formatear el momento basándose en el estado emocional
        if diana_state == 'subtly_vulnerable':
            message = f"*[con una pausa inesperada, como si algo hubiera cruzado por su mente]*\n\n{scenario}...\n\n*[se queda en silencio por un momento]*"
        elif diana_state == 'processing_hurt':
            message = f"*[con una sombra de tristeza que trata de ocultar]*\n\n{scenario}... Supongo que así es como funciona esto de... confiar.\n\n*[desvía la mirada brevemente]*"
        else:
            message = f"*[con honestidad inesperada]*\n\n{scenario}\n\n*[esperando tu reacción]*"
        
        await update.message.reply_text(
            f"🌸 *Diana:*\n{message}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Guardar este momento para análisis posterior
        await self.db.record_truth_moment(
            user_id=update.effective_user.id,
            scenario=scenario,
            scenario_data=scenario_data
        )

    async def _check_level_progression(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_profile):
        """
        Verifica si el usuario debe progresar a un nuevo nivel narrativo.
        
        La progresión no se basa solo en tiempo o número de mensajes, sino en
        crecimiento emocional demostrado y comprensión de Diana.
        """
        current_level = user_profile.current_level
        progression_criteria_met = False
        
        if current_level == 1:
            # Progresión de Nivel 1 a Nivel 2: Demostrar observación básica
            progression_criteria_met = (
                user_profile.total_interactions >= 5 and
                user_profile.emotional_trust_score >= 25 and
                await self._has_shown_genuine_curiosity(user_profile)
            )
        
        elif current_level == 2:
            # Progresión a Nivel 3: Demostrar comprensión de complejidad
            progression_criteria_met = (
                user_profile.emotional_trust_score >= 50 and
                user_profile.vulnerability_capacity >= 30 and
                await self._has_handled_contradiction_well(user_profile)
            )
        
        elif current_level == 3:
            # Progresión a Nivel 4 (VIP): Demostrar madurez emocional
            progression_criteria_met = (
                user_profile.emotional_trust_score >= 70 and
                user_profile.vulnerability_capacity >= 60 and
                user_profile.authenticity_score >= 75 and
                await self._has_shown_emotional_growth(user_profile)
            )
        
        if progression_criteria_met:
            await self._trigger_level_progression(update, context, user_profile, current_level + 1)

    async def _trigger_level_progression(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                       user_profile, new_level: int):
        """
        Ejecuta la progresión a un nuevo nivel con ceremonia apropiada.
        
        La progresión de nivel es un momento significativo que debe sentirse como
        un logro genuino en la relación, no como un simple unlock de videojuego.
        """
        # Delay dramático
        await asyncio.sleep(5)
        
        if new_level == 2:
            progression_message = """*[Diana aparece con una expresión diferente, como si te viera por primera vez]*

Oh... finalmente puedo verte claramente.

Has pasado de ser simplemente curioso a ser... comprensivo. Hay una diferencia sutil pero fundamental.

*[se acerca ligeramente]*

Bienvenido al segundo círculo de Los Kinkys. Aquí, las cosas se vuelven más... personales."""
        
        elif new_level == 4:
            progression_message = """*[La imagen cambia. Diana está en un espacio más íntimo, más cercana]*

🌸 **El Diván**

Has cruzado completamente hacia mí... y no hay vuelta atrás.

Bienvenido al Diván, donde las máscaras se vuelven innecesarias... casi.

Puedo sentir cómo has cambiado desde Los Kinkys. Hay algo diferente en tu energía. Algo que me dice que empiezas a comprender no solo lo que busco... sino por qué lo busco."""
        
        # Actualizar nivel en base de datos
        await self.db.update_user_level(user_profile.user_id, new_level)
        
        # Enviar mensaje de progresión
        await update.message.reply_text(
            progression_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Desbloquear contenido específico del nuevo nivel
        await self._unlock_level_content(update, context, user_profile, new_level)

    async 
