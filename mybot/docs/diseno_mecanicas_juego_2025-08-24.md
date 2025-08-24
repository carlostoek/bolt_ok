# ANÁLISIS Y DISEÑO DE MECÁNICAS DE JUEGO - DIANA BOT
*Fecha: 24 de agosto de 2025*

## ANÁLISIS DE GAME DESIGN

### CONTEXTO PSICOLÓGICO
- **Audiencia**: Usuarios de Telegram interesados en experiencias narrativas interactivas con toques de misterio y seducción. Combinación de motivaciones sociales y de progresión.
- **Motivaciones primarias**: Descubrimiento narrativo, acumulación de status social, desarrollo de personaje, y competencia amistosa.
- **Pain points actuales**: Posible fatiga por interacciones repetitivas, falta de sentido de comunidad, progresión potencialmente lineal, limitadas interacciones sociales significativas.
- **Oportunidades emocionales**: Aumentar sorpresa y descubrimiento, profundizar conexión emocional con Diana, crear momentos memorables compartibles, elevar tensión narrativa.

### BENCHMARKING COMPETITIVO
- **Qué están haciendo otros**: Sistemas básicos de puntos, badges simples, narrativas lineales, reacciones estándar de Telegram.
- **Gaps identificados**: Falta de emergent gameplay, limitada personalización, ausencia de mecánicas temporales/FOMO, pocas oportunidades para co-creación.
- **Ventajas de Telegram**: Capacidad para mensajes multimedia, interacción por comandos, soporte para bots avanzados, funcionalidad de canales y grupos integrada.

### OPORTUNIDADES DE INNOVACIÓN
- **Disruptiva**: Sistema de "Momentos Congelados" - fragmentos narrativos especiales que solo aparecen en momentos específicos del día real
- **Engagement**: Construcción de "Conspiración Colectiva" - misiones narrativas que requieren colaboración entre usuarios
- **Creative**: Uso de "Reacciones Evolutivas" que cambian en función del contexto narrativo y desbloquean contenido
- **Memorable**: "Momentos Diana" personalizados basados en el historial de decisiones del usuario

### PROPUESTA DE VALOR ÚNICA
- **Para el usuario**: Una experiencia narrativa que evoluciona orgánicamente basada en acciones colectivas e individuales, con profundidad psicológica y recompensas inesperadas
- **Diferenciación**: Sistema de intriga social donde tus decisiones afectan a otros usuarios, creando una experiencia de comunidad inmersiva que se siente viva

## SISTEMA DE JUEGO: ECOSISTEMA NARRATIVO EVOLUTIVO

### VISIÓN Y FILOSOFÍA
- **Experiencia emocional**: Intriga, anticipación, sorpresa y satisfacción por descubrimiento
- **Transformación personal**: De consumidor pasivo a co-creador activo de la narrativa
- **Historia emergente**: Cada usuario experimenta una versión ligeramente diferente de Diana basada en sus elecciones y las de la comunidad

### ARQUITECTURA DE ENGAGEMENT
- **Onboarding hook**: Mensaje inicial misterioso de Diana con una decisión inmediata que afecta su personalidad inicial
- **Core gameplay loop**: Descubrir → Decidir → Desbloquear → Compartir → Descubrir
- **Meta-progression**: Historia personal con Diana + Conspiración colectiva comunitaria
- **Social dynamics**: Fragmentos compartibles, decisiones de impacto comunitario, teorización grupal
- **Mastery path**: De novato intrigado a conspirador informado a confidente íntimo

### ECONOMÍA DE JUEGO
- **Recursos principales**: Besitos (puntos), Secretos (pistas), Momentos (fragmentos especiales), Confianza (nivel de relación)
- **Fuentes de valor**: Participación consistente, decisiones narrativas, descubrimiento de secretos, compartir teorías
- **Sinks de valor**: Desbloqueo de fragmentos VIP, acceso a decisiones especiales, personalización de experiencia
- **Balance dinámico**: Diferentes paths narrativos ofrecen balance de recompensas variadas según estilo de juego
- **Emergent strategies**: Especialización en tipos de narrativa, colaboración para teorías, experimentación con decisiones

### EVOLUCIÓN TEMPORAL
- **Semana 1**: Introducción a Diana y mecánicas básicas, primeras decisiones narrativas importantes
- **Mes 1**: Desarrollo de relación personalizada, participación en primer evento comunitario
- **Mes 6**: Acceso a secretos profundos, rol activo en conspiración comunitaria, identidad establecida
- **Año 1+**: Estatus de "Confidente", co-creación de momentos narrativos, influencia significativa en comunidad

### MECÁNICAS INNOVADORAS ESPECÍFICAS

#### Fragmentos Quánticos
- **Descripción**: Decisiones narrativas que cambian retroactivamente partes anteriores de la historia
- **Innovación**: Recontextualiza experiencias pasadas creando aha-moments sorprendentes
- **Implementación**: Sistema de estado narrativo que puede modificar fragmentos ya visitados
- **Impacto**: Crea momentos "mind-blown" altamente compartibles y fomenta múltiples recorridos

#### Sistema de Confianza Diana
- **Descripción**: Nivel de intimidad variable con Diana basado en consistencia y elecciones
- **Innovación**: Personalidad de Diana evoluciona basada en patrones de interacción, no solo decisiones puntuales
- **Implementación**: Modelo de personalidad con variables influenciadas por comportamiento de usuario
- **Impacto**: Relación única para cada usuario que evoluciona naturalmente, creando apego emocional genuino

#### Teorías Colectivas
- **Descripción**: Sistema donde usuarios proponen teorías sobre la narrativa que afectan la historia
- **Innovación**: Mecanismo de co-creación narrativa donde las teorías populares se incorporan sutilmente al canon
- **Implementación**: Panel de teorías votable con influencia algorítmica en nuevos fragmentos narrativos
- **Impacto**: Sentido de agencia colectiva y comunidad intelectualmente comprometida

### ELEMENTOS VIRALES Y SOCIALES
- **Shareable moments**: "Confesiones de Diana" - fragmentos narrativos personalizados diseñados para ser compartidos
- **Social proof**: Tablero de "Conexiones Profundas" mostrando decisiones significativas de amigos
- **Collaboration**: "Misterios Colectivos" que requieren descifrar pistas entre múltiples usuarios
- **Competition**: "Círculo Íntimo" - acceso especial temporal basado en engagement reciente

### MONETIZACIÓN ÉTICA
- **Value proposition**: Contenido VIP como ventana a dimensiones narrativas alternativas, no como continuación obligatoria
- **Fairness**: Experiencia completa y satisfactoria para usuarios free, VIP como enriquecimiento no esencial
- **Whale management**: Beneficios de status social y personalización profunda vs. ventajas competitivas
- **Free user value**: Acceso a narrativa principal completa y todas las mecánicas sociales fundamentales

## MECÁNICAS ESPECÍFICAS

### MECÁNICA: RESONANCIA NARRATIVA

#### CORE LOOP
- **Trigger**: Recibir fragmento narrativo con elementos ambiguos
- **Action**: Interpretar significado y tomar decisión
- **Variable Reward**: Reacción personalizada de Diana + desbloqueo impredecible
- **Investment**: Compartir interpretación con comunidad
- **Social**: Ver otras interpretaciones y discutir implicaciones

#### PSICOLOGÍA SUBYACENTE
- **Motivación atacada**: Necesidad de significado y cohesión narrativa (intrínseca)
- **Principio psicológico**: Efecto Zeigarnik (tensión por narrativas incompletas) + Sesgo de Ikea (valoramos más lo que ayudamos a crear)
- **Elemento sorpresa**: Interpretaciones comunitarias populares sutilmente influencian futuras respuestas de Diana

#### IMPLEMENTACIÓN PROGRESIVA
- **Versión MVP**: Fragmentos con interpretación abierta + foro simple de teorías
- **Versión v2**: Sistema de votación de teorías + influencia ligera en narrativa
- **Versión avanzada**: Motor narrativo adaptativo que evoluciona basado en interpretaciones colectivas

#### MÉTRICAS DE ÉXITO
- **Engagement**: Tiempo dedicado a analizar fragmentos + participación en discusiones
- **Behavioral**: Incremento en compartir teorías y debate comunitario constructivo
- **Emocional**: Reportes de "aha moments" y conexión profunda con la narrativa

#### ELEMENTOS ÚNICOS E INNOVADORES
- **Nunca visto**: Narrativa que evoluciona orgánicamente basada en interpretación colectiva
- **Telegram-native**: Usa grupos y canales para crear espacios dedicados a interpretación comunitaria
- **Creative twist**: "Fragmentos Espejo" que reflejan sutilmente comportamientos previos del usuario

### MECÁNICA: CONSPIRACIÓN COLECTIVA

#### CORE LOOP
- **Trigger**: Descubrir pista fragmentada que sugiere evento mayor
- **Action**: Colaborar con otros usuarios para completar el puzzle
- **Variable Reward**: Desbloqueo colectivo de revelación narrativa + recompensa individual basada en contribución
- **Investment**: Teorizar sobre implicaciones y próximas pistas
- **Social**: Compartir descubrimientos y coordinar búsqueda

#### PSICOLOGÍA SUBYACENTE
- **Motivación atacada**: Pertenencia social + competencia colaborativa
- **Principio psicológico**: Scarcity (pistas limitadas) + IKEA effect (valoramos lo que ayudamos a construir)
- **Elemento sorpresa**: Pistas que parecen desconectadas cobran sentido sorprendente cuando se combinan

#### IMPLEMENTACIÓN PROGRESIVA
- **Versión MVP**: Fragmentos de pistas distribuidos aleatoriamente que deben compartirse
- **Versión v2**: Sistema de "teorías colectivas" votables que desbloquean contenido
- **Versión avanzada**: Narrativas ramificadas basadas en consensos comunitarios sobre pistas

#### MÉTRICAS DE ÉXITO
- **Engagement**: Tasa de participación en eventos conspirativos
- **Behavioral**: Incremento en interacciones sociales entre usuarios
- **Emocional**: Momentos "eureka" colectivos y satisfacción por descubrimiento grupal

#### ELEMENTOS ÚNICOS E INNOVADORES
- **Nunca visto**: Sistema de narrativa emergente basada en consenso de interpretación
- **Telegram-native**: Aprovecha estructura de canales para distribuir pistas en forma no obvia
- **Creative twist**: Las pistas cambian sutilmente dependiendo de cuántos usuarios las han visto

### MECÁNICA: MOMENTOS CONGELADOS

#### CORE LOOP
- **Trigger**: Notificación de ventana temporal específica para contenido especial
- **Action**: Acceder a fragmento narrativo temporal exclusivo
- **Variable Reward**: Revelación narrativa única + recompensas contextuales
- **Investment**: Teorizar y discutir con comunidad
- **Social**: Coordinación para asegurar que amigos no pierdan el momento

#### PSICOLOGÍA SUBYACENTE
- **Motivación atacada**: FOMO (miedo a perderse algo) + exclusividad temporal
- **Principio psicológico**: Escasez temporal + rituales comunitarios
- **Elemento sorpresa**: Contenido que solo existe durante ventanas específicas y nunca se repite exactamente igual

#### IMPLEMENTACIÓN PROGRESIVA
- **Versión MVP**: Fragmentos narrativos disponibles solo en horarios específicos
- **Versión v2**: Fragmentos que cambian según cantidad de usuarios simultáneos
- **Versión avanzada**: Eventos narrativos en tiempo real con decisiones colectivas de tiempo limitado

#### MÉTRICAS DE ÉXITO
- **Engagement**: Porcentaje de usuarios que participan en momentos temporales
- **Behavioral**: Formación de hábitos de check-in en horarios específicos
- **Emocional**: Sensación de evento especial y experiencia compartida

#### ELEMENTOS ÚNICOS E INNOVADORES
- **Nunca visto**: Narrativa que existe solo en momentos específicos, creando "realidad compartida"
- **Telegram-native**: Aprovecha notificaciones y presencia online para crear eventos temporales
- **Creative twist**: El contenido varía sutilmente según fase lunar, día de semana, o eventos reales

### MECÁNICA: REACCIONES NARRATIVAS EVOLUTIVAS

#### CORE LOOP
- **Trigger**: Recibir fragmento narrativo con sistema de reacciones contextual
- **Action**: Elegir reacción que refleja interpretación personal
- **Variable Reward**: Respuesta personalizada de Diana + desbloqueo potencial
- **Investment**: Ver reacciones colectivas y su impacto
- **Social**: Discutir diferencias de interpretación basadas en reacciones

#### PSICOLOGÍA SUBYACENTE
- **Motivación atacada**: Expresión personal + curiosidad por caminos alternativos
- **Principio psicológico**: Self-expression + meaningful choices
- **Elemento sorpresa**: Cada reacción desbloquea respuesta única de Diana, a veces inesperada

#### IMPLEMENTACIÓN PROGRESIVA
- **Versión MVP**: Set básico de reacciones narrativas con respuestas predefinidas
- **Versión v2**: Reacciones desbloqueables que reflejan comprensión narrativa profunda
- **Versión avanzada**: Sistema predictivo que personaliza opciones de reacción según historial

#### MÉTRICAS DE ÉXITO
- **Engagement**: Diversidad de reacciones utilizadas por usuario
- **Behavioral**: Experimentación con diferentes reacciones para ver respuestas
- **Emocional**: Satisfacción al descubrir reacciones "perfectas" para momentos específicos

#### ELEMENTOS ÚNICOS E INNOVADORES
- **Nunca visto**: Reacciones como mecánica narrativa profunda, no solo expresión social
- **Telegram-native**: Extiende sistema nativo de reacciones con capa narrativa significativa
- **Creative twist**: Reacciones "prohibidas" o "tabú" que desbloquean rutas narrativas ocultas

## RECOMENDACIONES DE IMPLEMENTACIÓN

### FASE 1: FUNDAMENTOS (1-2 meses)

#### Estructura de Datos Mejorada

```python
# Extensión al modelo NarrativeFragment
class NarrativeFragment(Base):
    # Campos existentes...
    
    # Nuevos campos
    context_variables = Column(JSON, default=dict)  # Variables que cambian según usuario/comunidad
    alt_content_versions = Column(JSON, default=dict)  # Versiones alternativas de contenido
    temporal_availability = Column(JSON, default=dict)  # Restricciones temporales
    community_influence_level = Column(Float, default=0.0)  # Cuánto puede cambiar por consenso
    interpretation_data = Column(JSON, default=dict)  # Datos sobre interpretaciones de usuarios
    resonance_score = Column(Float, default=0.0)  # Impacto emocional medido
```

```python
# Nuevo modelo para Teorías Colectivas
class NarrativeTheory(Base):
    __tablename__ = 'narrative_theories'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    status = Column(String, default="proposed")  # proposed, popular, canonical, debunked
    related_fragments = Column(JSON, default=list)  # Fragmentos relacionados
    community_consensus = Column(Float, default=0.0)  # Nivel de acuerdo (-1.0 a 1.0)
    
    # Relaciones
    responses = relationship("NarrativeTheoryResponse", back_populates="theory")
```

```python
# Nuevo modelo para Reacciones Narrativas
class NarrativeReaction(Base):
    __tablename__ = 'narrative_reactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    fragment_id = Column(String, ForeignKey("narrative_fragments_unified.id"), nullable=False)
    reaction_type = Column(String, nullable=False)
    context_data = Column(JSON, default=dict)  # Datos contextuales
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "fragment_id", name="uix_user_fragment_reaction"),
    )
```

#### Servicios Esenciales

```python
class TheoryService:
    """Servicio para gestionar teorías narrativas colectivas."""
    
    def __init__(self, session: AsyncSession, notification_service: Optional[INotificationService] = None):
        self.session = session
        self.notification_service = notification_service
    
    async def propose_theory(self, user_id: int, title: str, content: str, related_fragments: List[str]) -> NarrativeTheory:
        """Propone una nueva teoría narrativa."""
        # Implementación...
        
    async def vote_theory(self, user_id: int, theory_id: str, vote_type: str) -> NarrativeTheory:
        """Vota una teoría (upvote/downvote)."""
        # Implementación...
        
    async def get_popular_theories(self, limit: int = 10) -> List[NarrativeTheory]:
        """Obtiene las teorías más populares."""
        # Implementación...
        
    async def update_theory_status(self, theory_id: str, new_status: str) -> NarrativeTheory:
        """Actualiza el estado de una teoría."""
        # Implementación...
        
    async def apply_community_consensus(self, threshold: float = 0.75) -> List[NarrativeTheory]:
        """Aplica consenso comunitario a teorías que superan umbral."""
        # Implementación...
```

```python
class EvolutiveNarrativeService:
    """Servicio para gestionar la narrativa evolutiva."""
    
    def __init__(self, 
                 session: AsyncSession, 
                 user_narrative_service: UserNarrativeService,
                 theory_service: TheoryService,
                 notification_service: Optional[INotificationService] = None):
        self.session = session
        self.user_narrative_service = user_narrative_service
        self.theory_service = theory_service
        self.notification_service = notification_service
    
    async def get_fragment_with_context(self, user_id: int, fragment_id: str) -> Dict:
        """Obtiene un fragmento con contexto personalizado."""
        # Implementación...
        
    async def register_narrative_reaction(self, user_id: int, fragment_id: str, reaction_type: str) -> Dict:
        """Registra una reacción narrativa y retorna respuesta personalizada."""
        # Implementación...
        
    async def check_temporal_fragments(self) -> List[Dict]:
        """Verifica fragmentos con disponibilidad temporal específica."""
        # Implementación...
        
    async def update_fragment_resonance(self, fragment_id: str) -> float:
        """Actualiza el score de resonancia de un fragmento basado en reacciones."""
        # Implementación...
```

### FASE 2: MECÁNICAS CLAVE (2-4 meses)

#### Resonancia Narrativa

```python
# Handler para interpretación narrativa
@router.message(F.text, UserMenuState(state="interpreting_fragment"))
async def handle_narrative_interpretation(
    message: Message, session: AsyncSession, state: FSMContext
):
    # Obtener datos del estado
    data = await state.get_data()
    fragment_id = data.get("current_fragment_id")
    
    # Procesar interpretación del usuario
    evolutive_service = EvolutiveNarrativeService(session)
    interpretation_result = await evolutive_service.register_interpretation(
        user_id=message.from_user.id,
        fragment_id=fragment_id,
        interpretation_text=message.text
    )
    
    # Enviar respuesta personalizada de Diana
    await message.answer(
        interpretation_result["diana_response"],
        reply_markup=interpretation_result["reply_markup"]
    )
    
    # Actualizar estado
    await state.set_state(UserMenuState.browsing_theories)
```

#### Conspiración Colectiva

```python
# Comando para ver teorías actuales
@router.message(Command("teorias"))
async def cmd_theories(message: Message, session: AsyncSession):
    theory_service = TheoryService(session)
    popular_theories = await theory_service.get_popular_theories(limit=5)
    
    response_text = "🔍 <b>Teorías Populares:</b>\n\n"
    for idx, theory in enumerate(popular_theories, 1):
        consensus = int(theory.community_consensus * 100)
        response_text += f"{idx}. <b>{theory.title}</b> · {consensus}% consenso\n"
        response_text += f"<i>{theory.content[:100]}...</i>\n\n"
    
    response_text += "\nUsa /teoria <número> para ver detalles o /proponer para crear nueva teoría."
    
    await message.answer(response_text, parse_mode="HTML")
```

```python
# Comando para crear nueva teoría
@router.message(Command("proponer"))
async def cmd_propose_theory(message: Message, state: FSMContext):
    await message.answer(
        "🔍 <b>Nueva Teoría Narrativa</b>\n\n"
        "Estás a punto de proponer una teoría sobre la historia de Diana.\n"
        "Primero, envíame un título breve y descriptivo para tu teoría.",
        parse_mode="HTML"
    )
    await state.set_state(UserMenuState.creating_theory_title)
```

#### Momentos Congelados

```python
# Tarea programada para activar fragmentos temporales
async def check_temporal_fragments_task(bot: Bot, session_pool):
    """Tarea programada que ejecuta cada 15 minutos para activar fragmentos temporales."""
    async with session_pool() as session:
        evolutive_service = EvolutiveNarrativeService(session)
        active_temporal_fragments = await evolutive_service.check_temporal_fragments()
        
        # Notificar a usuarios elegibles sobre fragmentos temporales
        for fragment_data in active_temporal_fragments:
            for user_id in fragment_data["eligible_users"]:
                try:
                    await bot.send_message(
                        user_id,
                        f"⏱️ <b>Momento Congelado Disponible</b>\n\n"
                        f"Un fragmento especial de la historia ha aparecido:\n"
                        f"<i>{fragment_data['title']}</i>\n\n"
                        f"⚠️ Solo estará disponible por {fragment_data['duration_minutes']} minutos.\n"
                        f"Usa /momento_{fragment_data['id']} para acceder ahora.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Error notifying user {user_id} about temporal fragment: {e}")
```

#### Reacciones Narrativas Evolutivas

```python
# Callback para reacción narrativa
@router.callback_query(F.data.startswith("nreact_"))
async def handle_narrative_reaction(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    # Parsear datos del callback
    parts = callback.data.split("_")
    fragment_id = parts[1]
    reaction_type = parts[2]
    
    # Registrar reacción
    evolutive_service = EvolutiveNarrativeService(session)
    reaction_result = await evolutive_service.register_narrative_reaction(
        user_id=callback.from_user.id,
        fragment_id=fragment_id,
        reaction_type=reaction_type
    )
    
    # Enviar respuesta personalizada
    await callback.message.edit_text(
        reaction_result["updated_content"],
        reply_markup=reaction_result["updated_markup"],
        parse_mode="HTML"
    )
    
    # Enviar respuesta de Diana como mensaje separado si existe
    if reaction_result.get("diana_response"):
        await bot.send_message(
            callback.from_user.id,
            reaction_result["diana_response"],
            parse_mode="HTML"
        )
```

### FASE 3: INTEGRACIÓN SOCIAL (3-6 meses)

#### Coordinador Central Mejorado

```python
class CoordinadorCentral:
    # Métodos existentes...
    
    async def register_narrative_reaction(self, user_id: int, fragment_id: str, reaction_type: str, bot: Bot) -> Dict:
        """Coordina el registro de una reacción narrativa con efectos en múltiples sistemas."""
        async with self.session_factory() as session:
            # Servicios necesarios
            evolutive_service = EvolutiveNarrativeService(session)
            point_service = PointService(session)
            mission_service = MissionService(session)
            
            # Registrar reacción y obtener resultado
            reaction_result = await evolutive_service.register_narrative_reaction(
                user_id=user_id,
                fragment_id=fragment_id,
                reaction_type=reaction_type
            )
            
            # Otorgar puntos según tipo y contexto de reacción
            points = reaction_result.get("points_earned", 1.0)
            await point_service.add_points(
                user_id, 
                points, 
                bot=bot,
                source=f"narrative_reaction_{reaction_type}"
            )
            
            # Actualizar progreso de misiones relacionadas
            await mission_service.update_progress(
                user_id,
                "narrative_reaction",
                bot=bot,
                fragment_id=fragment_id,
                reaction_type=reaction_type
            )
            
            # Publicar evento para otros sistemas
            await self.event_bus.publish(
                "narrative_reaction",
                {
                    "user_id": user_id,
                    "fragment_id": fragment_id,
                    "reaction_type": reaction_type,
                    "context": reaction_result.get("context", {}),
                    "resonance_score": reaction_result.get("resonance_score", 0.0)
                }
            )
            
            return reaction_result
```

#### Sistemas de Comunidad

```python
# Nuevo modelo para Círculo Íntimo
class InnerCircle(Base):
    __tablename__ = 'inner_circle'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    valid_until = Column(DateTime, nullable=False)
    reason = Column(String, nullable=False)
    resonance_level = Column(Float, default=0.0)
    special_permissions = Column(JSON, default=list)
    
    __table_args__ = (
        Index('ix_inner_circle_valid', 'valid_until'),
    )
```

```python
class CommunityService:
    """Servicio para gestionar aspectos sociales y comunitarios."""
    
    def __init__(self, session: AsyncSession, notification_service: Optional[INotificationService] = None):
        self.session = session
        self.notification_service = notification_service
    
    async def update_inner_circle(self) -> List[Dict]:
        """Actualiza el Círculo Íntimo basado en engagement reciente."""
        # Implementación...
        
    async def get_community_insights(self, fragment_id: str) -> Dict:
        """Obtiene insights comunitarios sobre un fragmento específico."""
        # Implementación...
        
    async def register_shared_moment(self, user_id: int, fragment_id: str, platform: str) -> Dict:
        """Registra cuando un usuario comparte un momento y otorga beneficios."""
        # Implementación...
```

### IMPLEMENTACIÓN TÉCNICA DETALLADA: SISTEMA DE FRAGMENTOS QUÁNTICOS

Este sistema permite que decisiones narrativas actuales modifiquen retroactivamente fragmentos ya visitados, creando una experiencia narrativa no lineal donde el pasado puede "cambiar" basado en decisiones presentes.

#### Modelo de Datos

```python
# Extensión a NarrativeFragment
class NarrativeFragment(Base):
    # Campos existentes...
    
    # Quantum Fragments
    quantum_state = Column(Boolean, default=False)  # Indica si es un fragmento cuántico
    quantum_versions = Column(JSON, default=dict)  # Versiones alternativas según estados cuánticos
    quantum_triggers = Column(JSON, default=dict)  # Decisiones que afectan este fragmento
```

```python
# Nuevo modelo para Estados Cuánticos
class QuantumState(Base):
    __tablename__ = 'quantum_states'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    affected_fragments = Column(JSON, default=list)  # IDs de fragmentos afectados
    trigger_fragments = Column(JSON, default=list)  # IDs de fragmentos que lo activan
    narrative_implications = Column(Text, nullable=True)  # Descripción de implicaciones
    is_active = Column(Boolean, default=True)
```

```python
# Extensión a UserNarrativeState
class UserNarrativeState(Base):
    # Campos existentes...
    
    # Quantum States
    active_quantum_states = Column(JSON, default=list)  # Estados cuánticos activos
    quantum_history = Column(JSON, default=list)  # Historial de cambios cuánticos
```

#### Servicio de Fragmentos Quánticos

```python
class QuantumFragmentService:
    """Servicio para gestionar fragmentos cuánticos que cambian según decisiones narrativas."""
    
    def __init__(self, session: AsyncSession, user_narrative_service: UserNarrativeService):
        self.session = session
        self.user_narrative_service = user_narrative_service
    
    async def apply_quantum_trigger(self, user_id: int, trigger_fragment_id: str, decision: str) -> Dict:
        """Aplica un trigger cuántico que puede modificar fragmentos ya visitados."""
        # Obtener el fragmento trigger
        fragment_stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == trigger_fragment_id,
            NarrativeFragment.is_active == True
        )
        fragment_result = await self.session.execute(fragment_stmt)
        fragment = fragment_result.scalar_one_or_none()
        
        if not fragment or not fragment.quantum_triggers:
            return {"success": False, "message": "No quantum triggers found"}
        
        # Verificar si la decisión activa un trigger cuántico
        quantum_trigger = fragment.quantum_triggers.get(decision)
        if not quantum_trigger:
            return {"success": False, "message": "Decision does not trigger quantum change"}
        
        # Obtener estado del usuario
        state = await self.user_narrative_service.get_or_create_user_state(user_id)
        
        # Activar estados cuánticos correspondientes
        activated_states = []
        for state_id in quantum_trigger.get("activate_states", []):
            # Añadir estado cuántico si no está ya activo
            if state_id not in state.active_quantum_states:
                state.active_quantum_states.append(state_id)
                activated_states.append(state_id)
            
            # Registrar en historial cuántico
            state.quantum_history.append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "state_id": state_id,
                "trigger_fragment": trigger_fragment_id,
                "decision": decision,
                "action": "activated"
            })
        
        # Desactivar estados cuánticos si es necesario
        deactivated_states = []
        for state_id in quantum_trigger.get("deactivate_states", []):
            if state_id in state.active_quantum_states:
                state.active_quantum_states.remove(state_id)
                deactivated_states.append(state_id)
                
                # Registrar en historial cuántico
                state.quantum_history.append({
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "state_id": state_id,
                    "trigger_fragment": trigger_fragment_id,
                    "decision": decision,
                    "action": "deactivated"
                })
        
        await self.session.commit()
        
        return {
            "success": True,
            "activated_states": activated_states,
            "deactivated_states": deactivated_states,
            "message": "Quantum states updated successfully"
        }
    
    async def get_quantum_fragment_version(self, user_id: int, fragment_id: str) -> Dict:
        """Obtiene la versión correcta de un fragmento según estados cuánticos del usuario."""
        # Obtener el fragmento base
        fragment_stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        fragment_result = await self.session.execute(fragment_stmt)
        fragment = fragment_result.scalar_one_or_none()
        
        if not fragment:
            return {"success": False, "message": "Fragment not found"}
        
        # Si no es cuántico, retornar versión original
        if not fragment.quantum_state:
            return {
                "success": True,
                "is_quantum": False,
                "fragment": fragment,
                "content": fragment.content,
                "title": fragment.title,
                "choices": fragment.choices
            }
        
        # Obtener estados cuánticos activos del usuario
        state = await self.user_narrative_service.get_or_create_user_state(user_id)
        active_states = state.active_quantum_states
        
        # Determinar la versión del fragmento a mostrar
        for state_id in active_states:
            if state_id in fragment.quantum_versions:
                version_data = fragment.quantum_versions[state_id]
                
                return {
                    "success": True,
                    "is_quantum": True,
                    "quantum_state": state_id,
                    "fragment": fragment,
                    "content": version_data.get("content", fragment.content),
                    "title": version_data.get("title", fragment.title),
                    "choices": version_data.get("choices", fragment.choices),
                    "was_rewritten": True
                }
        
        # Si no hay versión específica, retornar original
        return {
            "success": True,
            "is_quantum": True,
            "active_states": active_states,
            "fragment": fragment,
            "content": fragment.content,
            "title": fragment.title,
            "choices": fragment.choices,
            "was_rewritten": False
        }
    
    async def get_affected_fragments(self, user_id: int) -> List[Dict]:
        """Obtiene lista de fragmentos que han sido afectados por cambios cuánticos."""
        # Obtener estados cuánticos activos del usuario
        state = await self.user_narrative_service.get_or_create_user_state(user_id)
        active_states = state.active_quantum_states
        
        if not active_states:
            return []
        
        # Obtener estados cuánticos
        states_stmt = select(QuantumState).where(
            QuantumState.id.in_(active_states),
            QuantumState.is_active == True
        )
        states_result = await self.session.execute(states_stmt)
        quantum_states = states_result.scalars().all()
        
        # Recopilar fragmentos afectados
        affected_fragments = []
        visited_fragments = set(state.visited_fragments)
        
        for qstate in quantum_states:
            for fragment_id in qstate.affected_fragments:
                # Solo incluir si el usuario ya visitó el fragmento
                if fragment_id in visited_fragments:
                    affected_fragments.append({
                        "fragment_id": fragment_id,
                        "quantum_state": qstate.id,
                        "quantum_name": qstate.name
                    })
        
        return affected_fragments
```

#### Handler de Implementación

```python
# Handler para fragmentos cuánticos
@router.callback_query(F.data.startswith("quantum_decision_"))
async def handle_quantum_decision(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    # Parsear datos del callback
    parts = callback.data.split("_")
    fragment_id = parts[2]
    decision = parts[3]
    
    # Aplicar trigger cuántico
    quantum_service = QuantumFragmentService(session, UserNarrativeService(session))
    result = await quantum_service.apply_quantum_trigger(
        user_id=callback.from_user.id,
        trigger_fragment_id=fragment_id,
        decision=decision
    )
    
    if result["success"]:
        # Notificar al usuario sobre el cambio cuántico
        await callback.answer("Tu decisión ha alterado tu percepción de eventos pasados...", show_alert=True)
        
        # Si hay fragmentos afectados, ofrecer revisitarlos
        affected_fragments = await quantum_service.get_affected_fragments(callback.from_user.id)
        
        if affected_fragments:
            # Crear mensaje sobre fragmentos afectados
            message_text = (
                "🌀 <b>Alteración en la Realidad</b>\n\n"
                "Tu decisión ha creado ondas que alteran tu percepción de eventos pasados.\n"
                "Algunos recuerdos parecen... diferentes ahora.\n\n"
                "<i>Fragmentos afectados:</i>\n"
            )
            
            for idx, fragment in enumerate(affected_fragments[:3], 1):
                message_text += f"{idx}. <b>Recuerdo alterado</b> · /revisar_{fragment['fragment_id']}\n"
            
            if len(affected_fragments) > 3:
                message_text += f"\n<i>...y {len(affected_fragments) - 3} más.</i>"
                
            message_text += "\n\nPuedes revisar estos recuerdos alterados o continuar tu camino."
            
            await callback.message.answer(message_text, parse_mode="HTML")
    
    # Continuar con la narrativa normal
    # ...
```

## IMPLEMENTACIÓN RÁPIDA: PRIMEROS PASOS

Para integrar estas mecánicas avanzadas de manera gradual, recomiendo comenzar con estos tres elementos de alto impacto y baja complejidad técnica:

### 1. REACCIONES NARRATIVAS (2-3 semanas)

#### Mejoras a los modelos existentes

```python
# En database/models.py - Añadir modelo para reacciones narrativas
class NarrativeReaction(Base):
    __tablename__ = "narrative_reactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    fragment_id = Column(String, ForeignKey("narrative_fragments_unified.id"), nullable=False)
    reaction_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "fragment_id", "reaction_type", name="uix_user_fragment_reaction"),
    )
```

#### Funciones en el servicio narrativo

```python
# En services/user_narrative_service.py - Añadir método
async def register_narrative_reaction(self, user_id: int, fragment_id: str, reaction_type: str) -> Dict:
    """Registra una reacción narrativa a un fragmento.
    
    Args:
        user_id (int): ID del usuario
        fragment_id (str): ID del fragmento
        reaction_type (str): Tipo de reacción ('comprendo', 'duda', 'asombro', 'temor', etc.)
        
    Returns:
        Dict: Resultado de la operación con respuesta personalizada
    """
    # Verificar fragmento
    fragment_stmt = select(NarrativeFragment).where(
        NarrativeFragment.id == fragment_id,
        NarrativeFragment.is_active == True
    )
    fragment_result = await self.session.execute(fragment_stmt)
    fragment = fragment_result.scalar_one_or_none()
    
    if not fragment:
        return {"success": False, "message": "Fragmento no encontrado"}
    
    # Crear o actualizar reacción
    reaction_stmt = select(NarrativeReaction).where(
        NarrativeReaction.user_id == user_id,
        NarrativeReaction.fragment_id == fragment_id,
        NarrativeReaction.reaction_type == reaction_type
    )
    reaction_result = await self.session.execute(reaction_stmt)
    reaction = reaction_result.scalar_one_or_none()
    
    is_new = reaction is None
    
    if is_new:
        reaction = NarrativeReaction(
            user_id=user_id,
            fragment_id=fragment_id,
            reaction_type=reaction_type
        )
        self.session.add(reaction)
    
    await self.session.commit()
    
    # Generar respuesta personalizada basada en el tipo de reacción
    responses = {
        "comprendo": [
            "Me alegra que lo entiendas... hay mucho más por descubrir.",
            "Tu intuición es buena, ¿qué más puedes deducir?",
            "Veo que me sigues perfectamente, cariño."
        ],
        "duda": [
            "Es normal tener preguntas... algunas se responderán con el tiempo.",
            "La duda es el principio de la sabiduría, ¿no crees?",
            "Entiendo tu confusión. Todo tendrá sentido eventualmente."
        ],
        "asombro": [
            "¿Te sorprende? Imagina cómo me sentí yo...",
            "Las sorpresas apenas comienzan, te lo aseguro.",
            "Tu asombro alimenta mi curiosidad por ti."
        ],
        "temor": [
            "No temas, estoy aquí contigo en este camino.",
            "El miedo puede ser... instructivo, ¿no crees?",
            "Algunas verdades son aterradoras, pero necesarias."
        ]
    }
    
    default_responses = ["Interesante reacción...", "Mmm, anotado.", "Aprecio tu sinceridad."]
    possible_responses = responses.get(reaction_type, default_responses)
    
    # Añadir puntos según tipo de reacción (implementación simple)
    points = 1.0
    if reaction_type in ["asombro", "temor"]:
        points = 2.0  # Reacciones emocionales fuertes valen más
    
    # Recompensar con puntos a través del sistema de recompensas
    try:
        await self.reward_system.grant_reward(
            user_id=user_id,
            reward_type='points',
            reward_data={
                'amount': points,
                'description': f'Reacción narrativa: {reaction_type}'
            },
            source='narrative_reaction'
        )
    except Exception as e:
        logger.error(f"Error al otorgar puntos por reacción: {e}")
    
    # Retornar resultado con respuesta personalizada
    import random
    return {
        "success": True,
        "is_new": is_new,
        "points_earned": points,
        "response": random.choice(possible_responses)
    }
```

#### Modificación al handler de fragmentos narrativos

```python
# En handlers/narrative_handlers.py - Modificar el handler existente
@router.callback_query(F.data.startswith("fragment_"))
async def handle_narrative_fragment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    # Código existente para mostrar el fragmento...
    
    # Añadir botones de reacción narrativa
    reactions_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💡 Comprendo",
                callback_data=f"nreact_{fragment.id}_comprendo"
            ),
            InlineKeyboardButton(
                text="❓ Tengo dudas",
                callback_data=f"nreact_{fragment.id}_duda"
            )
        ],
        [
            InlineKeyboardButton(
                text="😮 ¡Increíble!",
                callback_data=f"nreact_{fragment.id}_asombro"
            ),
            InlineKeyboardButton(
                text="😨 Inquietante",
                callback_data=f"nreact_{fragment.id}_temor"
            )
        ],
        # Botones de navegación existentes...
    ])
    
    # Enviar mensaje con botones de reacción
    await callback.message.edit_reply_markup(reply_markup=reactions_keyboard)
```

#### Nuevo handler para reacciones narrativas

```python
# En handlers/narrative_handlers.py - Añadir nuevo handler
@router.callback_query(F.data.startswith("nreact_"))
async def handle_narrative_reaction(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    # Parsear datos del callback
    parts = callback.data.split("_")
    if len(parts) < 3:
        return await callback.answer("Datos de reacción inválidos")
    
    fragment_id = parts[1]
    reaction_type = parts[2]
    
    # Registrar reacción
    narrative_service = UserNarrativeService(session, reward_system=RewardSystem(session))
    result = await narrative_service.register_narrative_reaction(
        user_id=callback.from_user.id,
        fragment_id=fragment_id,
        reaction_type=reaction_type
    )
    
    if result["success"]:
        # Confirmar recepción
        await callback.answer(f"Reacción registrada", show_alert=False)
        
        # Enviar respuesta de Diana como mensaje separado
        await bot.send_message(
            callback.from_user.id,
            f"<i>{result['response']}</i>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("No se pudo registrar tu reacción", show_alert=True)
```

### 2. TEORÍAS NARRATIVAS SIMPLES (4-5 semanas)

#### Modelo de datos básico

```python
# En database/models.py - Añadir modelo para teorías
class UserTheory(Base):
    __tablename__ = "user_theories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_approved = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)
    related_fragments = Column(JSON, default=list)
```

#### Servicio simple de teorías

```python
# En services/theory_service.py - Nuevo servicio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import UserTheory, User
import logging

logger = logging.getLogger(__name__)

class TheoryService:
    """Servicio simple para gestionar teorías de usuarios."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_theory(self, user_id: int, title: str, content: str, related_fragments: List[str] = None) -> UserTheory:
        """Crea una nueva teoría de usuario."""
        theory = UserTheory(
            user_id=user_id,
            title=title,
            content=content,
            related_fragments=related_fragments or []
        )
        self.session.add(theory)
        await self.session.commit()
        await self.session.refresh(theory)
        return theory
    
    async def get_user_theories(self, user_id: int) -> List[UserTheory]:
        """Obtiene las teorías creadas por un usuario."""
        stmt = select(UserTheory).where(
            UserTheory.user_id == user_id
        ).order_by(UserTheory.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_popular_theories(self, limit: int = 10) -> List[Dict]:
        """Obtiene las teorías más populares con información del autor."""
        # Consulta para obtener teorías con información de usuario
        stmt = select(
            UserTheory,
            User.username,
            User.first_name
        ).join(
            User,
            UserTheory.user_id == User.id
        ).where(
            UserTheory.is_approved == True
        ).order_by(
            UserTheory.upvotes.desc()
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        theories_with_users = result.all()
        
        # Formatear resultados
        return [
            {
                "id": theory.id,
                "title": theory.title,
                "content": theory.content,
                "created_at": theory.created_at,
                "upvotes": theory.upvotes,
                "author": username or first_name or f"Usuario {theory.user_id}"
            }
            for theory, username, first_name in theories_with_users
        ]
    
    async def upvote_theory(self, theory_id: int) -> UserTheory:
        """Incrementa los votos positivos de una teoría."""
        theory = await self.session.get(UserTheory, theory_id)
        if theory:
            theory.upvotes += 1
            await self.session.commit()
            await self.session.refresh(theory)
        return theory
    
    async def approve_theory(self, theory_id: int) -> UserTheory:
        """Aprueba una teoría para hacerla visible a todos los usuarios."""
        theory = await self.session.get(UserTheory, theory_id)
        if theory:
            theory.is_approved = True
            await self.session.commit()
            await self.session.refresh(theory)
        return theory
```

#### Handlers básicos para teorías

```python
# En handlers/theory_handlers.py - Nuevos handlers
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from services.theory_service import TheoryService
from utils.user_roles import is_admin

router = Router()

# Estados FSM para creación de teorías
class TheoryStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()

# Comando para ver teorías populares
@router.message(Command("teorias"))
async def cmd_view_theories(message: Message, session: AsyncSession):
    theory_service = TheoryService(session)
    popular_theories = await theory_service.get_popular_theories(limit=5)
    
    if not popular_theories:
        await message.answer(
            "🔍 <b>Teorías de la Comunidad</b>\n\n"
            "Aún no hay teorías publicadas. ¡Sé el primero en proponer una!\n\n"
            "Usa /proponer_teoria para crear tu propia teoría sobre la historia de Diana.",
            parse_mode="HTML"
        )
        return
    
    # Crear mensaje con teorías populares
    text = "🔍 <b>Teorías Populares de la Comunidad</b>\n\n"
    
    for idx, theory in enumerate(popular_theories, 1):
        text += f"{idx}. <b>{theory['title']}</b> · {theory['upvotes']} votos\n"
        text += f"<i>Por {theory['author']}</i>\n"
        
        # Truncar contenido si es muy largo
        content = theory['content']
        if len(content) > 100:
            content = content[:97] + "..."
        
        text += f"{content}\n\n"
    
    text += "Usa /proponer_teoria para crear tu propia teoría."
    
    await message.answer(text, parse_mode="HTML")

# Comando para proponer nueva teoría
@router.message(Command("proponer_teoria"))
async def cmd_propose_theory(message: Message, state: FSMContext):
    await message.answer(
        "🔍 <b>Nueva Teoría Narrativa</b>\n\n"
        "Estás a punto de proponer una teoría sobre la historia de Diana.\n"
        "Primero, envíame un título breve y descriptivo para tu teoría.",
        parse_mode="HTML"
    )
    await state.set_state(TheoryStates.waiting_for_title)

# Handler para recibir título de teoría
@router.message(TheoryStates.waiting_for_title)
async def process_theory_title(message: Message, state: FSMContext):
    # Guardar título
    await state.update_data(title=message.text)
    
    await message.answer(
        "Buen título. Ahora escribe el contenido detallado de tu teoría.\n"
        "Explica tu interpretación, evidencias y conclusiones."
    )
    await state.set_state(TheoryStates.waiting_for_content)

# Handler para recibir contenido de teoría
@router.message(TheoryStates.waiting_for_content)
async def process_theory_content(message: Message, state: FSMContext, session: AsyncSession):
    # Obtener datos guardados
    data = await state.get_data()
    title = data.get("title", "Sin título")
    
    # Guardar teoría
    theory_service = TheoryService(session)
    theory = await theory_service.create_theory(
        user_id=message.from_user.id,
        title=title,
        content=message.text
    )
    
    # Verificar si el usuario es admin para auto-aprobar
    if await is_admin(session, message.from_user.id):
        await theory_service.approve_theory(theory.id)
        await message.answer(
            "✅ <b>Teoría Publicada</b>\n\n"
            f"Tu teoría <b>\"{title}\"</b> ha sido creada y publicada automáticamente "
            f"porque eres administrador.\n\n"
            f"Los usuarios pueden verla usando /teorias.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "✅ <b>Teoría Enviada</b>\n\n"
            f"Tu teoría <b>\"{title}\"</b> ha sido enviada correctamente.\n\n"
            f"Un administrador la revisará pronto y, si es aprobada, "
            f"aparecerá en el listado de teorías de la comunidad.",
            parse_mode="HTML"
        )
    
    # Limpiar estado
    await state.clear()

# Comando de administrador para aprobar teorías
@router.message(Command("aprobar_teoria"))
async def cmd_approve_theory(message: Message, session: AsyncSession):
    # Verificar si es administrador
    if not await is_admin(session, message.from_user.id):
        return
    
    # Obtener parámetros
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Uso: /aprobar_teoria <id_teoria>"
        )
        return
    
    try:
        theory_id = int(parts[1])
    except ValueError:
        await message.answer("ID de teoría inválido")
        return
    
    # Aprobar teoría
    theory_service = TheoryService(session)
    theory = await theory_service.approve_theory(theory_id)
    
    if theory:
        await message.answer(
            f"✅ Teoría ID {theory_id} aprobada correctamente"
        )
    else:
        await message.answer(
            f"❌ No se encontró la teoría con ID {theory_id}"
        )
```

### 3. MOMENTOS ESPECIALES TEMPORALES (3-4 semanas)

#### Extensión de modelo de fragmentos

```python
# En database/narrative_unified.py - Extender NarrativeFragment
class NarrativeFragment(Base):
    # Campos existentes...
    
    # Nuevos campos para momentos temporales
    is_temporal = Column(Boolean, default=False)
    temporal_start = Column(DateTime, nullable=True)
    temporal_end = Column(DateTime, nullable=True)
    temporal_weekdays = Column(JSON, default=list)  # [0-6] para días de semana
    temporal_hours = Column(JSON, default=list)  # [0-23] para horas del día
```

#### Servicio para fragmentos temporales

```python
# En services/temporal_fragments_service.py - Nuevo servicio
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.narrative_unified import NarrativeFragment
from database.models import User
import datetime
import logging

logger = logging.getLogger(__name__)

class TemporalFragmentsService:
    """Servicio para gestionar fragmentos narrativos con disponibilidad temporal."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_available_temporal_fragments(self) -> List[NarrativeFragment]:
        """Obtiene fragmentos temporales actualmente disponibles."""
        now = datetime.datetime.utcnow()
        current_weekday = now.weekday()  # 0-6, 0 es lunes
        current_hour = now.hour  # 0-23
        
        # Consulta para obtener fragmentos temporales activos actualmente
        stmt = select(NarrativeFragment).where(
            and_(
                NarrativeFragment.is_active == True,
                NarrativeFragment.is_temporal == True,
                or_(
                    NarrativeFragment.temporal_start == None,
                    NarrativeFragment.temporal_start <= now
                ),
                or_(
                    NarrativeFragment.temporal_end == None,
                    NarrativeFragment.temporal_end >= now
                )
            )
        )
        
        result = await self.session.execute(stmt)
        all_temporal_fragments = result.scalars().all()
        
        # Filtrar por día de semana y hora si está especificado
        available_fragments = []
        for fragment in all_temporal_fragments:
            weekday_match = (
                not fragment.temporal_weekdays or  # Si está vacío, coincide con cualquier día
                current_weekday in fragment.temporal_weekdays
            )
            
            hour_match = (
                not fragment.temporal_hours or  # Si está vacío, coincide con cualquier hora
                current_hour in fragment.temporal_hours
            )
            
            if weekday_match and hour_match:
                available_fragments.append(fragment)
        
        return available_fragments
    
    async def get_eligible_users_for_fragment(self, fragment_id: str, limit: int = 100) -> List[int]:
        """Obtiene usuarios elegibles para recibir notificación sobre un fragmento temporal."""
        # Aquí podrías implementar lógica más compleja para determinar elegibilidad
        # Por ejemplo, basada en progreso narrativo, nivel, etc.
        
        # Implementación simple: obtener usuarios activos recientemente
        one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        
        stmt = select(User.id).where(
            User.updated_at >= one_day_ago
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return [row[0] for row in result]
    
    async def format_temporal_notification(self, fragment: NarrativeFragment) -> Dict:
        """Formatea información de notificación para un fragmento temporal."""
        # Calcular tiempo restante
        end_time = fragment.temporal_end
        now = datetime.datetime.utcnow()
        
        if end_time:
            time_left = end_time - now
            minutes_left = max(1, int(time_left.total_seconds() / 60))
        else:
            minutes_left = 60  # Valor predeterminado si no hay fin definido
        
        return {
            "id": fragment.id,
            "title": fragment.title,
            "duration_minutes": minutes_left,
            "message": (
                f"⏱️ <b>Momento Especial Disponible</b>\n\n"
                f"Un fragmento temporal de la historia ha aparecido:\n"
                f"<i>{fragment.title}</i>\n\n"
                f"⚠️ Solo estará disponible por {minutes_left} minutos.\n"
                f"Usa /momento_{fragment.id} para acceder ahora."
            )
        }
```

#### Tarea programada para notificaciones

```python
# En bot.py - Añadir tarea programada
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.temporal_fragments_service import TemporalFragmentsService

# Crear scheduler
scheduler = AsyncIOScheduler()

# Tarea para verificar fragmentos temporales (ejecutar cada 15 minutos)
async def check_temporal_fragments_task(bot):
    """Verifica fragmentos temporales disponibles y notifica a usuarios."""
    logger.info("Ejecutando verificación de fragmentos temporales")
    
    async with db_session() as session:
        temporal_service = TemporalFragmentsService(session)
        available_fragments = await temporal_service.get_available_temporal_fragments()
        
        for fragment in available_fragments:
            # Obtener usuarios elegibles
            eligible_users = await temporal_service.get_eligible_users_for_fragment(fragment.id)
            
            if not eligible_users:
                continue
                
            # Formatear notificación
            notification = await temporal_service.format_temporal_notification(fragment)
            
            # Enviar notificaciones (limitar a 20 usuarios por iteración para evitar flood)
            for user_id in eligible_users[:20]:
                try:
                    await bot.send_message(
                        user_id,
                        notification["message"],
                        parse_mode="HTML"
                    )
                    logger.info(f"Notificación de fragmento temporal enviada a usuario {user_id}")
                except Exception as e:
                    logger.error(f"Error enviando notificación a usuario {user_id}: {e}")

# Registrar tarea programada
def setup_scheduler(bot):
    scheduler.add_job(
        check_temporal_fragments_task,
        'interval',
        minutes=15,
        args=[bot]
    )
    scheduler.start()
```

#### Handler para acceder a momentos temporales

```python
# En handlers/narrative_handlers.py - Añadir handler
from aiogram.filters import Command, CommandStart
import re

# Patrón para comandos de momento temporal
MOMENTO_PATTERN = re.compile(r'^\/momento_([a-zA-Z0-9-]+)$')

# Handler para comando de momento temporal
@router.message(lambda message: bool(MOMENTO_PATTERN.match(message.text)))
async def handle_temporal_moment(message: Message, session: AsyncSession, bot: Bot):
    # Extraer ID del fragmento
    match = MOMENTO_PATTERN.match(message.text)
    fragment_id = match.group(1)
    
    # Verificar si el fragmento existe y está disponible temporalmente
    now = datetime.datetime.utcnow()
    current_weekday = now.weekday()
    current_hour = now.hour
    
    fragment_stmt = select(NarrativeFragment).where(
        and_(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True,
            NarrativeFragment.is_temporal == True,
            or_(
                NarrativeFragment.temporal_start == None,
                NarrativeFragment.temporal_start <= now
            ),
            or_(
                NarrativeFragment.temporal_end == None,
                NarrativeFragment.temporal_end >= now
            )
        )
    )
    
    fragment_result = await session.execute(fragment_stmt)
    fragment = fragment_result.scalar_one_or_none()
    
    if not fragment:
        await message.answer(
            "⏱️ <b>Momento No Disponible</b>\n\n"
            "Este momento especial ya no está disponible o nunca existió.\n"
            "Los momentos especiales son temporales y solo aparecen en ciertos momentos.",
            parse_mode="HTML"
        )
        return
    
    # Verificar día y hora si están especificados
    weekday_match = (
        not fragment.temporal_weekdays or
        current_weekday in fragment.temporal_weekdays
    )
    
    hour_match = (
        not fragment.temporal_hours or
        current_hour in fragment.temporal_hours
    )
    
    if not (weekday_match and hour_match):
        await message.answer(
            "⏱️ <b>Fuera de Tiempo</b>\n\n"
            "Este momento especial no está disponible ahora mismo.\n"
            "Regresa en otro momento para experimentarlo.",
            parse_mode="HTML"
        )
        return
    
    # Marcar como visitado en el progreso del usuario
    narrative_service = UserNarrativeService(session, reward_system=RewardSystem(session))
    await narrative_service.update_current_fragment(message.from_user.id, fragment.id)
    
    # Generar mensaje especial para momento temporal
    content = fragment.content
    
    # Añadir indicador visual de momento temporal
    message_text = (
        f"⏱️ <b>MOMENTO ESPECIAL</b> ⏱️\n\n"
        f"<b>{fragment.title}</b>\n\n"
        f"{content}"
    )
    
    # Enviar fragmento
    await message.answer(message_text, parse_mode="HTML")
    
    # Otorgar recompensa especial por experimentar momento temporal
    try:
        reward_system = RewardSystem(session)
        await reward_system.grant_reward(
            user_id=message.from_user.id,
            reward_type='points',
            reward_data={
                'amount': 5.0,  # Recompensa especial por momento temporal
                'description': f'Momento Especial: {fragment.title}'
            },
            source='temporal_fragment'
        )
        
        # Enviar notificación de recompensa
        await message.answer(
            "🎁 <b>Recompensa Especial</b>\n\n"
            "Has recibido 5 besitos extra por experimentar este momento único.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error otorgando recompensa por momento temporal: {e}")
```

## CONCLUSIONES Y SIGUIENTES PASOS

Estas tres implementaciones iniciales crearán una base sólida para la evolución del ecosistema gamificado completo:

1. **Reacciones Narrativas**: Establecen el ciclo de retroalimentación emocional y personalización narrativa

2. **Teorías Narrativas**: Construyen la infraestructura social para co-creación comunitaria 

3. **Momentos Temporales**: Introducen el concepto de exclusividad temporal y experiencias compartidas

Tras implementar estas funcionalidades, se recomienda:

1. **Medir Engagement**: Analizar qué reacciones generan más respuesta emocional

2. **Evaluar Participación Comunitaria**: Monitorear creación y discusión de teorías

3. **Ajustar Frecuencia Temporal**: Optimizar los momentos temporales según patrones de uso

Este enfoque incremental permitirá evolucionar hacia el sistema narrativo evolutivo completo, integrando gradualmente los fragmentos cuánticos, la conspiración colectiva y los demás elementos diseñados, manteniendo a los usuarios comprometidos durante todo el proceso de desarrollo.