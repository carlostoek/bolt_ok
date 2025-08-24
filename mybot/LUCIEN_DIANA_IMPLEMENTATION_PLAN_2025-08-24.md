# LUCIEN-DIANA IMPLEMENTATION PLAN (Mayordomo del Diván)
*Fecha: 24 de agosto de 2025*

## VISIÓN GENERAL

Este documento detalla el plan de implementación para transformar el bot Diana en "El Mayordomo del Diván", un sistema narrativo donde Lucien actúa como guardián principal y Diana aparece como figura misteriosa en momentos clave. La arquitectura aprovecha los sistemas existentes mientras introduce mecánicas sofisticadas de narrativa evolutiva.

## MODELO CONCEPTUAL

### Dinámica Central
- **Lucien (Primario)**: Guardián formal, evaluador, intermediario con Diana
- **Diana (Secundaria)**: Figura misteriosa que aparece brevemente en momentos significativos
- **Progresión**: Desarrollo de confianza con Lucien que eventualmente permite mayor acceso a Diana

## DISEÑO DE FLUJO DE USUARIO

### Fase 1: Contacto Inicial y Onboarding
```
**Punto de Entrada: Solicitud de Acceso al Canal → Bienvenida de Lucien → Breve Aparición de Diana**

1. Detección de Solicitud de Acceso al Canal
   - Sistema detecta cuando el usuario solicita acceso a "Los Kinkys"
   - Activa temporizador de 15 minutos para aprobación de acceso

2. Introducción de Lucien (5 minutos después de la solicitud)
   - Lucien envía mensaje formal de bienvenida con tono de guardián sofisticado
   - "Permíteme presentarme: Lucien, guardián de los secretos de Diana... y evaluador de quienes desean conocerla."
   - Explica su rol como el "Mayordomo del Diván" que determina quién es digno de la atención de Diana
   - Presenta primer desafío: reacción al contenido del canal como prueba inicial

3. Breve Aparición de Diana (Solo después de la prueba de reacción)
   - Diana aparece momentáneamente con un mensaje sutil e intrigante
   - La interacción es breve y misteriosa, reforzando que el acceso a ella está mediado por Lucien
   - Lucien regresa inmediatamente para explicar lo ocurrido y su significado
   
4. Aprobación de Acceso e Introducción de Mecánicas Centrales
   - Acceso al canal otorgado automáticamente después del retraso de 15 minutos
   - Lucien envía invitación formal a "Los Kinkys" con explicación del viaje por delante
   - Introduce la "Mochila del Viajero" y el sistema de pistas
```

### Fase 2: Bucle Principal de Juego con Dinámica Lucien-Diana
```
**Bucle Principal: Observar → Reaccionar → Ganar Confianza → Vislumbrar a Diana → Progresar**

1. Sistema de Observación de Lucien
   - Lucien presenta desafíos que prueban la atención al detalle del usuario
   - "Misiones de Observación" que requieren encontrar elementos ocultos en el contenido del canal
   - Lucien evalúa respuestas y proporciona retroalimentación formal, al estilo mayordomo

2. Mecánicas de Reacción
   - Cuatro reacciones emocionales (comprendo, duda, asombro, temor) a fragmentos narrativos
   - Lucien reconoce las reacciones primero, explicando lo que revelan sobre el usuario
   - Diana aparece brevemente para reacciones particularmente perspicaces o auténticas

3. Construcción de Confianza con Lucien
   - Lucien gradualmente pasa de guardián formal a facilitador respetuoso
   - Sistema de puntos representado como "Nivel de Confianza con Lucien"
   - En umbrales clave de confianza, Lucien revela más sobre Diana y sobre sí mismo
```

### Fase 3: Apariciones de Diana y Progresión Narrativa
```
**Integración de Diana: Apariciones Raras y Significativas en Momentos Clave**

1. Apariciones Programadas de Diana
   - Diana aparece en hitos narrativos específicos, no aleatoriamente
   - Cada aparición es breve pero impactante, dejando a los usuarios deseando más
   - Lucien siempre contextualiza sus apariciones después

2. Sistema de Fragmentos Cuánticos
   - Decisiones tomadas con Lucien afectan cómo aparece Diana en interacciones posteriores
   - Conversaciones pasadas con Diana pueden cambiar retroactivamente según el nivel de confianza
   - Lucien explica estos cambios como "Diana revelando más de su verdadera esencia"

3. Progresión VIP: Acceso a El Diván
   - Lucien formalmente invita a usuarios dignos a "El Diván" (canal VIP)
   - Lo presenta como un santuario interior donde Diana está más presente
   - El sistema VIP presenta más interacciones directas con Diana, aunque Lucien sigue siendo el guía principal
```

## PLAN DE IMPLEMENTACIÓN

### Fase 1: Marco del Sistema Centrado en Lucien

1. **Servicio de Personaje de Lucien**
   - `/services/lucien_service.py`: Crear servicio central para la personalidad y respuestas de Lucien
   ```python
   class LucienService:
       """Servicio para gestionar las interacciones de Lucien como Mayordomo del Diván."""
       
       def __init__(self, session: AsyncSession, notification_service: Optional[NotificationService] = None):
           self.session = session
           self.notification_service = notification_service
       
       async def handle_initial_greeting(self, user_id: int) -> Dict[str, Any]:
           """Genera el saludo inicial de Lucien después de la solicitud de acceso al canal."""
           # Implementación con bienvenida formal estilo mayordomo
           
       async def evaluate_user_reaction(self, user_id: int, reaction_type: str, context: str) -> Dict[str, Any]:
           """Evalúa la reacción de un usuario al contenido desde la perspectiva de Lucien."""
           # Implementación con diferentes respuestas basadas en tipo de reacción y contexto
           
       async def determine_diana_appearance(self, user_id: int, trigger_type: str) -> bool:
           """Determina si una acción del usuario debería desencadenar una aparición de Diana."""
           # Implementación basada en progreso del usuario, patrones de reacción y posición narrativa
   ```

2. **Extensión del CoordinadorCentral**
   - `/services/coordinador_central.py`: Añadir nuevo método para manejar la dinámica Lucien-Diana
   ```python
   async def _flujo_lucien_diana_dynamic(self, user_id: int, action: str, context: Dict[str, Any] = None, bot=None) -> Dict[str, Any]:
       """
       Flujo para gestionar la dinámica de interacción Lucien-Diana.
       
       Args:
           user_id: ID del usuario
           action: Tipo de acción ("lucien_challenge", "diana_appearance", etc.)
           context: Contexto adicional para la acción
           bot: Instancia del bot para enviar mensajes
           
       Returns:
           Dict con resultados y mensajes
       """
       # Implementación que orquesta el rol primario de Lucien y las apariciones secundarias de Diana
       lucien_service = LucienService(self.session)
       
       if action == "lucien_challenge":
           # Maneja a Lucien presentando un desafío al usuario
           challenge_result = await lucien_service.create_challenge(user_id, context.get("challenge_type"))
           # ...
       
       elif action == "evaluate_reaction":
           # Evalúa la reacción del usuario con la perspectiva de Lucien
           evaluation = await lucien_service.evaluate_user_reaction(
               user_id, context.get("reaction_type"), context.get("reaction_context")
           )
           
           # Determina si esto debería desencadenar una aparición de Diana
           should_diana_appear = await lucien_service.determine_diana_appearance(
               user_id, "reaction_evaluation"
           )
           
           if should_diana_appear:
               # Desencadena una breve aparición de Diana
               diana_response = await self._get_diana_response(user_id, evaluation)
               # ...
       
       # Otras acciones y resultados de retorno
   ```

3. **Modelo de Base de Datos Unificado para Narrativa Lucien-Diana**
   - `/database/narrative_unified.py`: Añadir campos específicos de Lucien a los modelos narrativos
   ```python
   # Añadir al modelo UserNarrativeState
   lucien_trust_level = Column(Float, default=0.0)
   lucien_interaction_count = Column(Integer, default=0)
   diana_appearances = Column(JSON, default=list)  # Lista de timestamps y contextos
   narrative_level = Column(Integer, default=1)  # Corresponde a los Niveles 1-6 en la narrativa
   archetype = Column(String, nullable=True)  # Arquetipo de usuario según identificación del sistema
   
   # Añadir al modelo NarrativeFragment
   presenter = Column(String, default="lucien")  # Quién presenta este fragmento: lucien, diana, o ambos
   diana_appearance_threshold = Column(Float, default=1.0)  # Nivel mínimo de confianza para que Diana aparezca
   narrative_level_required = Column(Integer, default=1)
   ```

### Fase 2: Sistemas de Reacción y Observación

1. **Sistema de Desafío de Observación de Lucien**
   - `/services/observation_challenge_service.py`: Servicio para los desafíos de observación de Lucien
   ```python
   class ObservationChallengeService:
       """Servicio para gestionar los desafíos de observación de Lucien."""
       
       def __init__(self, session: AsyncSession):
           self.session = session
       
       async def create_observation_challenge(self, user_id: int, challenge_level: int = 1) -> Dict[str, Any]:
           """Crea un nuevo desafío de observación apropiado para el nivel del usuario."""
           # Implementación creando desafíos que prueben la atención al detalle
           
       async def evaluate_observation_attempt(self, user_id: int, challenge_id: str, answer: str) -> Dict[str, Any]:
           """Evalúa el intento de un usuario de resolver un desafío de observación."""
           # Implementación con retroalimentación formal de Lucien
           
       async def get_lucien_response(self, success_level: float, user_archetype: str) -> str:
           """Obtiene la respuesta formal de Lucien a un intento de desafío basado en éxito y tipo de usuario."""
           # Implementación con respuestas estilo mayordomo para diferentes niveles de éxito
   ```

2. **Sistema de Reacción Mejorado**
   - `/services/narrative_reaction_service.py`: Servicio para reacciones emocionales con mediación de Lucien
   ```python
   class NarrativeReactionService:
       """Servicio para gestionar reacciones narrativas con interpretación de Lucien."""
       
       def __init__(self, session: AsyncSession, lucien_service: LucienService):
           self.session = session
           self.lucien_service = lucien_service
       
       async def register_reaction(self, user_id: int, fragment_id: str, reaction_type: str) -> Dict[str, Any]:
           """Registra e interpreta la reacción emocional de un usuario con la perspectiva de Lucien."""
           # Implementación con reacciones procesadas a través del filtro de Lucien
           
           # Registra reacción en la base de datos
           reaction = NarrativeReaction(
               user_id=user_id,
               fragment_id=fragment_id,
               reaction_type=reaction_type,
               timestamp=datetime.utcnow()
           )
           self.session.add(reaction)
           await self.session.commit()
           
           # Obtiene la interpretación de Lucien
           lucien_interpretation = await self.lucien_service.interpret_reaction(
               user_id, reaction_type, fragment_id
           )
           
           # Determina si esto debería desencadenar a Diana
           should_diana_appear = await self.lucien_service.determine_diana_appearance(
               user_id, "reaction", reaction_type
           )
           
           return {
               "success": True,
               "lucien_response": lucien_interpretation["response"],
               "trust_change": lucien_interpretation["trust_change"],
               "diana_appears": should_diana_appear,
               "diana_response": lucien_interpretation.get("diana_response") if should_diana_appear else None
           }
   ```

3. **Handlers para Interacciones Lucien-Diana**
   - `/handlers/lucien_handlers.py`: Handlers para las interacciones de Lucien
   ```python
   # Callback para reacciones a fragmentos
   @router.callback_query(F.data.startswith("lucien_reaction_"))
   async def handle_lucien_reaction(callback: CallbackQuery, session: AsyncSession, bot: Bot):
       """Maneja reacciones a fragmentos narrativos presentados por Lucien."""
       # Extrae datos de reacción
       parts = callback.data.split("_")
       fragment_id = parts[2]
       reaction_type = parts[3]
       
       # Procesa la reacción a través de Lucien
       lucien_service = LucienService(session)
       narrative_reaction_service = NarrativeReactionService(session, lucien_service)
       
       result = await narrative_reaction_service.register_reaction(
           user_id=callback.from_user.id,
           fragment_id=fragment_id,
           reaction_type=reaction_type
       )
       
       # Primero, Lucien responde
       await callback.message.reply(
           result["lucien_response"],
           parse_mode="HTML"
       )
       
       # Si Diana aparece, envía un mensaje separado
       if result["diana_appears"]:
           # Ligero retraso para crear separación entre Lucien y Diana
           await asyncio.sleep(1.5)
           await bot.send_message(
               callback.from_user.id,
               f"<i>{result['diana_response']}</i>",
               parse_mode="HTML"
           )
           
           # Lucien regresa para explicar la aparición de Diana
           await asyncio.sleep(2)
           await bot.send_message(
               callback.from_user.id,
               "Diana se ha ido tan rápido como apareció. Fascinante cómo tu reacción captó su atención por un momento...",
               parse_mode="HTML"
           )
   ```

### Fase 3: Sistema de Fragmentos Cuánticos

1. **Servicio de Estado Cuántico**
   - `/services/quantum_fragment_service.py`: Servicio para fragmentos que cambian según el progreso narrativo
   ```python
   class QuantumFragmentService:
       """Servicio para gestionar fragmentos narrativos que cambian retroactivamente con explicación de Lucien."""
       
       def __init__(self, session: AsyncSession, lucien_service: LucienService):
           self.session = session
           self.lucien_service = lucien_service
       
       async def apply_quantum_trigger(self, user_id: int, trigger_fragment_id: str, decision: str) -> Dict:
           """Aplica un disparador que puede modificar fragmentos visitados previamente."""
           # Implementación que cambia fragmentos pasados
           
           # Primero, aplica cambios de estado cuántico
           state = await self.get_user_narrative_state(user_id)
           
           # Crea efecto de estado cuántico basado en la decisión
           quantum_effect = {
               "triggered_by": trigger_fragment_id,
               "decision": decision,
               "timestamp": datetime.utcnow().isoformat(),
               "affected_fragments": []  # Se poblará con fragmentos cambiados
           }
           
           # Determina qué fragmentos pasados deberían cambiar
           affected_fragments = await self._find_affected_fragments(user_id, decision)
           
           # Aplica cambios a cada fragmento
           for fragment_id in affected_fragments:
               await self._modify_fragment_perception(user_id, fragment_id, decision)
               quantum_effect["affected_fragments"].append(fragment_id)
           
           # Almacena efecto cuántico en estado de usuario
           if "quantum_effects" not in state.additional_data:
               state.additional_data["quantum_effects"] = []
           
           state.additional_data["quantum_effects"].append(quantum_effect)
           await self.session.commit()
           
           # Obtiene explicación de Lucien sobre lo ocurrido
           lucien_explanation = await self.lucien_service.explain_quantum_change(
               user_id, len(affected_fragments), decision
           )
           
           return {
               "success": True,
               "affected_fragments": len(affected_fragments),
               "lucien_explanation": lucien_explanation,
               "should_review_past": len(affected_fragments) > 0
           }
   ```

2. **Sistema de Momento Temporal**
   - `/services/temporal_moment_service.py`: Servicio para momentos narrativos restringidos por tiempo
   ```python
   class TemporalMomentService:
       """Servicio para gestionar momentos narrativos restringidos por tiempo."""
       
       def __init__(self, session: AsyncSession, lucien_service: LucienService):
           self.session = session
           self.lucien_service = lucien_service
       
       async def get_available_moments(self, user_id: int) -> List[Dict]:
           """Obtiene momentos temporales actualmente disponibles para el usuario."""
           # Implementación verificando restricciones de tiempo y progreso del usuario
           
           now = datetime.utcnow()
           current_weekday = now.weekday()
           current_hour = now.hour
           
           # Obtiene estado narrativo del usuario para verificar elegibilidad
           state = await self.get_user_narrative_state(user_id)
           
           # Consulta para fragmentos temporales disponibles
           stmt = select(NarrativeFragment).where(
               and_(
                   NarrativeFragment.is_active == True,
                   NarrativeFragment.is_temporal == True,
                   NarrativeFragment.narrative_level_required <= state.narrative_level,
                   or_(
                       NarrativeFragment.temporal_weekdays == None,
                       func.json_contains(NarrativeFragment.temporal_weekdays, current_weekday)
                   ),
                   or_(
                       NarrativeFragment.temporal_hours == None,
                       func.json_contains(NarrativeFragment.temporal_hours, current_hour)
                   )
               )
           )
           
           result = await self.session.execute(stmt)
           available_fragments = result.scalars().all()
           
           # Formatea resultados con introducción de Lucien para cada uno
           formatted_moments = []
           for fragment in available_fragments:
               lucien_intro = await self.lucien_service.get_temporal_moment_introduction(
                   user_id, fragment.id
               )
               
               formatted_moments.append({
                   "id": fragment.id,
                   "title": fragment.title,
                   "lucien_introduction": lucien_intro,
                   "presenter": fragment.presenter,
                   "expires_in_minutes": self._calculate_expiration_minutes(fragment)
               })
           
           return formatted_moments
   ```

3. **Sistema de Aparición de Diana**
   - `/services/diana_appearance_service.py`: Servicio para gestionar las apariciones raras de Diana
   ```python
   class DianaAppearanceService:
       """Servicio para gestionar las apariciones y respuestas de Diana."""
       
       def __init__(self, session: AsyncSession):
           self.session = session
       
       async def get_diana_response(self, user_id: int, context: Dict[str, Any]) -> str:
           """Obtiene una respuesta de Diana basada en el usuario y contexto."""
           # Implementación de las respuestas raras pero impactantes de Diana
           
           # Obtiene estado del usuario para determinar tono apropiado de Diana
           state = await self.get_user_narrative_state(user_id)
           
           # Obtiene arquetipo de usuario si se conoce
           archetype = state.archetype or "unknown"
           
           # Obtiene respuestas específicas de contexto
           if context.get("type") == "reaction":
               reaction_type = context.get("reaction_type", "")
               responses = await self._get_diana_reaction_responses(
                   reaction_type, state.narrative_level, archetype
               )
               
           elif context.get("type") == "milestone":
               milestone_type = context.get("milestone_type", "")
               responses = await self._get_diana_milestone_responses(
                   milestone_type, state.narrative_level, archetype
               )
           
           else:
               # Respuestas predeterminadas
               responses = await self._get_diana_default_responses(
                   state.narrative_level, archetype
               )
           
           # Elige respuesta basada en historial del usuario para evitar repetición
           chosen_response = await self._select_non_repetitive_response(user_id, responses)
           
           # Registra esta aparición
           await self._record_diana_appearance(
               user_id, context.get("type"), chosen_response
           )
           
           return chosen_response
   ```

### Fase 4: Notificación e Integración

1. **Integración del Servicio de Notificación Mejorado**
   - `/services/notification_service.py`: Extender para dinámica Lucien-Diana
   ```python
   # Añadir al método _build_enhanced_unified_message
   async def _build_enhanced_unified_message(self, grouped: Dict[str, List[Dict[str, Any]]]) -> str:
       # ...código existente...
       
       # === SECCIÓN DE LUCIEN Y DIANA ===
       if "lucien_message" in grouped:
           lucien_messages = grouped["lucien_message"]
           latest_message = lucien_messages[-1]
           
           # Añadir sección de Lucien con tono propio de mayordomo
           sections.append("🎩 *Mensaje de Lucien:*")
           sections.append(f"_{latest_message.get('message', 'Lucien observa tu progreso...')}_")
       
       if "diana_appearance" in grouped:
           diana_appearances = grouped["diana_appearance"]
           # Las apariciones de Diana son raras y especiales, así que destacarlas
           sections.append("━━━━━━━━━━━━━━━")
           sections.append("🌸 *Diana apareció brevemente...*")
           
           for appearance in diana_appearances[:1]:  # Solo mostrar la más reciente
               sections.append(f"_{appearance.get('message', 'Sus ojos te observaron por un instante...')}_")
           
           # Añadir comentario de Lucien sobre la aparición de Diana
           sections.append("🎩 *Lucien comenta:*")
           sections.append("_\"Fascinante... Diana no suele mostrar interés tan directamente. Parece que algo en ti captó su atención.\"_")
       
       # ...resto del código existente...
   ```

2. **Extensiones de EventBus**
   - `/services/event_bus.py`: Añadir nuevos tipos de eventos para dinámica Lucien-Diana
   ```python
   # Añadir a la clase EventType
   class EventType(Enum):
       # ...eventos existentes...
       
       # Eventos de dinámica Lucien-Diana
       LUCIEN_CHALLENGE_ISSUED = "lucien_challenge_issued"
       LUCIEN_CHALLENGE_COMPLETED = "lucien_challenge_completed"
       LUCIEN_TRUST_INCREASED = "lucien_trust_increased"
       DIANA_APPEARED = "diana_appeared"
       QUANTUM_FRAGMENT_CHANGED = "quantum_fragment_changed"
       NARRATIVE_LEVEL_ADVANCED = "narrative_level_advanced"
   ```

3. **Integración de Eventos en CoordinadorCentral**
   - `/services/coordinador_central.py`: Añadir publicación de eventos para dinámica Lucien-Diana
   ```python
   # Añadir al método _emit_workflow_events
   async def _emit_workflow_events(self, user_id: int, accion: AccionUsuario, 
                                  result: Dict[str, Any], correlation_id: str) -> None:
       # ...código existente...
       
       # Manejar eventos específicos de Lucien-Diana
       if accion == AccionUsuario.LUCIEN_CHALLENGE:
           await self.event_bus.publish(
               EventType.LUCIEN_CHALLENGE_ISSUED if result.get("challenge_issued") else EventType.LUCIEN_CHALLENGE_COMPLETED,
               user_id,
               {
                   "challenge_type": result.get("challenge_type"),
                   "success_level": result.get("success_level"),
                   "trust_change": result.get("trust_change"),
                   "diana_appeared": result.get("diana_appeared", False)
               },
               source="coordinador_central",
               correlation_id=correlation_id
           )
           
           if result.get("diana_appeared"):
               await self.event_bus.publish(
                   EventType.DIANA_APPEARED,
                   user_id,
                   {
                       "context": "lucien_challenge",
                       "challenge_type": result.get("challenge_type"),
                       "response": result.get("diana_response")
                   },
                   source="coordinador_central",
                   correlation_id=correlation_id
               )
       
       # ...resto del código existente...
   ```

### Fase 5: Handlers de Frontend

1. **Handler de Solicitud de Canal**
   - `/handlers/channel_handlers.py`: Handler para acceso inicial al canal
   ```python
   @router.chat_join_request(ChatJoinRequestFilter())
   async def handle_join_request(join_request: ChatJoinRequest, bot: Bot, session: AsyncSession):
       """Maneja una solicitud de usuario para unirse al canal."""
       try:
           user_id = join_request.from_user.id
           chat_id = join_request.chat.id
           
           # Registra la solicitud de unión
           logger.info(f"Solicitud de unión del usuario {user_id} para chat {chat_id}")
           
           # Crea usuario si no existe
           user = await get_or_create_user(session, join_request.from_user)
           
           # Programa mensaje de bienvenida de Lucien (5 minutos después de la solicitud)
           scheduler.add_job(
               send_lucien_welcome,
               'date',
               run_date=datetime.datetime.now() + datetime.timedelta(minutes=5),
               args=[bot, user_id, join_request.chat.id]
           )
           
           # Programa aprobación del canal (15 minutos después de la solicitud)
           scheduler.add_job(
               approve_channel_request,
               'date',
               run_date=datetime.datetime.now() + datetime.timedelta(minutes=15),
               args=[bot, user_id, join_request.chat.id]
           )
           
           logger.info(f"Programada bienvenida y aprobación para usuario {user_id}")
           
       except Exception as e:
           logger.exception(f"Error al manejar solicitud de unión: {e}")
   ```

2. **Handlers de Desafío de Lucien**
   - `/handlers/lucien_challenge_handlers.py`: Handlers para los desafíos de Lucien
   ```python
   @router.callback_query(F.data.startswith("lucien_challenge_"))
   async def handle_lucien_challenge(callback: CallbackQuery, session: AsyncSession, bot: Bot):
       """Maneja la interacción del usuario con los desafíos de Lucien."""
       # Extrae datos del desafío
       parts = callback.data.split("_")
       challenge_id = parts[2]
       action = parts[3] if len(parts) > 3 else "view"
       
       # Obtiene el servicio de desafío
       lucien_service = LucienService(session)
       observation_service = ObservationChallengeService(session)
       
       if action == "view":
           # Muestra detalles del desafío
           challenge = await observation_service.get_challenge(challenge_id)
           
           # Formatea presentación del desafío de Lucien
           challenge_text = await lucien_service.format_challenge_presentation(
               callback.from_user.id, challenge
           )
           
           # Crea teclado inline para respuesta
           keyboard = InlineKeyboardMarkup(inline_keyboard=[
               [
                   InlineKeyboardButton(
                       text="Aceptar desafío",
                       callback_data=f"lucien_challenge_{challenge_id}_accept"
                   )
               ]
           ])
           
           await callback.message.edit_text(
               challenge_text,
               reply_markup=keyboard,
               parse_mode="HTML"
           )
           
       elif action == "accept":
           # Usuario acepta el desafío
           await callback.answer("Lucien asiente con aprobación.")
           
           # Actualiza estado del desafío y obtiene instrucciones
           instructions = await observation_service.start_challenge(
               callback.from_user.id, challenge_id
           )
           
           # Formatea instrucciones de Lucien
           instructions_text = await lucien_service.format_challenge_instructions(
               callback.from_user.id, instructions
           )
           
           await callback.message.edit_text(
               instructions_text,
               parse_mode="HTML"
           )
           
       elif action == "submit":
           # Usuario está enviando una respuesta - manejar en estado FSM en su lugar
           await callback.answer("Por favor, envía tu respuesta como mensaje.")
   ```

3. **Handler de Aparición de Diana**
   - `/handlers/diana_handlers.py`: Handler para las apariciones raras de Diana
   ```python
   @router.callback_query(F.data.startswith("diana_reaction_"))
   async def handle_diana_reaction(callback: CallbackQuery, session: AsyncSession, bot: Bot, state: FSMContext):
       """Maneja reacciones del usuario a las raras apariciones de Diana."""
       # Extrae datos de reacción
       parts = callback.data.split("_")
       appearance_id = parts[2]
       reaction = parts[3]
       
       # Obtiene servicios
       diana_service = DianaAppearanceService(session)
       lucien_service = LucienService(session)
       
       # Registra la reacción del usuario a Diana
       result = await diana_service.register_diana_reaction(
           callback.from_user.id, appearance_id, reaction
       )
       
       # Primero Diana responde brevemente
       await callback.message.edit_text(
           f"<i>{result['diana_response']}</i>",
           parse_mode="HTML"
       )
       
       # Luego Diana desaparece y Lucien regresa para explicar
       await asyncio.sleep(2)
       
       lucien_explanation = await lucien_service.explain_diana_reaction(
           callback.from_user.id, reaction, result
       )
       
       await bot.send_message(
           callback.from_user.id,
           lucien_explanation,
           parse_mode="HTML"
       )
       
       # Si esto desbloqueó algo especial, Lucien lo menciona
       if result.get("unlocked_content"):
           await asyncio.sleep(1)
           
           unlock_message = await lucien_service.explain_content_unlock(
               callback.from_user.id, result["unlocked_content"]
           )
           
           await bot.send_message(
               callback.from_user.id,
               unlock_message,
               parse_mode="HTML"
           )
   ```

## MITIGACIÓN DE RIESGOS

- **Riesgo de Consistencia Narrativa**: Implementar capa de validación para asegurar que las respuestas de Lucien y Diana permanezcan dentro del personaje
- **Riesgo de Equilibrio de Progresión**: Crear herramientas de monitoreo para seguir las tasas de progreso del usuario a través de los niveles narrativos
- **Riesgo de Aparición de Diana**: Establecer límites estrictos de tasa de aparición para mantener la rareza e impacto de las interacciones con Diana

## PRUEBAS DE INTEGRACIÓN

1. `test_lucien_diana_full_flow`: Probar viaje completo desde solicitud de canal a través de múltiples niveles narrativos
2. `test_lucien_challenge_progression`: Verificar que los desafíos aumentan en sofisticación con el progreso del usuario
3. `test_diana_appearance_impact`: Probar apariciones de Diana y su impacto psicológico/narrativo

## CONCLUSIÓN

Este diseño crea una experiencia narrativa sofisticada centrada en Lucien como guardián principal e intérprete del mundo de Diana, con Diana apareciendo raramente pero de manera impactante. La implementación aprovecha la arquitectura del sistema existente mientras introduce nuevas mecánicas como fragmentos cuánticos, reacciones emocionales y momentos temporales que se enmarcan a través de la perspectiva formal y mayordómica de Lucien.