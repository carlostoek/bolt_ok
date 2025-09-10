# Diana Bot - Hoja de Ruta de Implementación
*Plan Modular para Desarrollo por Sesiones*

## 🎯 Estrategia: Construcción Incremental

**Principios del plan:**
- ✅ Cada sesión implementa una funcionalidad **COMPLETA** y **funcional**
- ✅ Nuevas funcionalidades se basan en lo **YA IMPLEMENTADO**
- ✅ No hay dependencias de funcionalidades futuras
- ✅ Cada implementación mejora inmediatamente la experiencia del usuario
- ✅ Testing y validación en cada sesión

---

## 📋 ESTADO BASE ACTUAL

### ✅ **Infraestructura Disponible:**
- `CoordinadorCentral` - Orquestación entre módulos
- `Enhanced Diana Menu System` - Interface unificada
- `MVPNarrativeFragmentService` - Motor narrativo (8 fragmentos)
- `Point Service` - Sistema de besitos funcional
- `Event Bus` - Comunicación inter-módulo
- `Database Layer` - SQLAlchemy con tablas unificadas
- `Session Management` - Middleware robusto

### ✅ **Lo que funciona para usuarios:**
- Navegación narrativa con decisiones dinámicas
- Otorgamiento automático de besitos por progreso
- Progresión de niveles (1→2→3)
- Menu principal accesible con `/diana`

---

## 🚀 FASES DE IMPLEMENTACIÓN

# FASE 1: EXPERIENCIA DE USUARIO BÁSICA
*Objetivo: Hacer tangibles las recompensas para el usuario*

## Sesión 1: Sistema de Recompensas Diarias 🎁
**Duración estimada: 2-3 horas**

### ¿Por qué empezar aquí?
- ✅ No depende de ninguna funcionalidad futura
- ✅ Usa la infraestructura de puntos ya existente
- ✅ Mejora inmediatamente el engagement diario
- ✅ Fácil de testear y validar

### Implementación:
```
services/daily_reward_service.py
├── DailyRewardService
├── claim_daily_reward(user_id)
├── get_reward_status(user_id)
└── reset_daily_rewards() [background task]

database/models.py
└── user_daily_claims table

handlers/user/daily_rewards.py
├── /regalo handler
├── /estado_regalo handler
└── Callback handlers para UI

enhanced_diana_menu_system.py
└── Daily rewards menu integration
```

### Funcionalidad completa:
- Usuario puede reclamar besitos diarios con `/regalo`
- Cooldown de 24 horas automático
- Visualización de tiempo restante
- Integración en el menú principal de Diana
- Notificaciones de reward disponible

### Testing:
- Verificar que se otorgan besitos correctamente
- Validar cooldown de 24 horas
- Confirmar integración con el menú principal

---

## Sesión 2: Sistema de Inventario/Mochila 🎒
**Duración estimada: 3-4 horas**

### ¿Por qué ahora?
- ✅ Construye sobre el sistema de puntos existente
- ✅ Prepara la base para futuros sistemas (tienda, objetos)
- ✅ Hace visible el progreso del usuario

### Implementación:
```
services/inventory_service.py
├── InventoryService
├── add_item_to_inventory(user_id, item_type, item_data)
├── get_user_inventory(user_id)
├── get_item_count(user_id, item_type)
└── use_item(user_id, item_id) [para futuro]

database/models.py
└── user_inventory table
    ├── user_id, item_type, item_name, item_data
    ├── quantity, acquired_date
    └── is_used, used_date

handlers/user/inventory.py
├── /mochila handler
└── Paginación para inventarios grandes

enhanced_diana_menu_system.py
└── Inventory menu integration
```

### Funcionalidad completa:
- Usuario ve su inventario con `/mochila`
- Items se categorizan (besitos, logros, pistas_futuras)
- Interface paginada para inventarios grandes
- Integración en menú principal
- Contadores de items por tipo

### Testing:
- Agregar items de prueba al inventario
- Verificar visualización correcta
- Validar paginación

---

## Sesión 3: Sistema de Logros/Badges 🏆
**Duración estimada: 3-4 horas**

### ¿Por qué ahora?
- ✅ Se basa en los sistemas existentes (puntos, inventario)
- ✅ Reconoce el progreso ya realizado por usuarios
- ✅ Añade gamificación sin requerir nuevas mecánicas

### Implementación:
```
services/achievement_service.py
├── AchievementService (mejorar el existente)
├── check_and_unlock_achievements(user_id, event_data)
├── get_user_achievements(user_id)
└── get_achievement_progress(user_id, achievement_id)

database/models.py
├── achievements table (definitions)
├── user_achievements table (unlocked)
└── achievement_progress table (tracking)

Achievement definitions:
├── "Primer Paso" - Completar Level 1
├── "Coleccionista" - Acumular 100 besitos
├── "Explorador" - Completar Level 2
├── "Veterano" - Acumular 500 besitos
└── "Maestro" - Completar Level 3

event_bus.py integration
└── Listen for POINTS_AWARDED, LEVEL_UP events
```

### Funcionalidad completa:
- Achievements se desbloquean automáticamente
- Usuario ve sus logros con `/logros`
- Progreso hacia achievements no desbloqueados
- Rewards adicionales por logros (besitos bonus)
- Integración con Event Bus para auto-detection

### Testing:
- Verificar que achievements se desbloquean correctamente
- Validar rewards por achievements
- Confirmar visualización de progreso

---

# FASE 2: MECÁNICAS DE INTERCAMBIO
*Objetivo: Crear un ciclo económico básico*

## Sesión 4: Tienda Virtual Básica 🛒
**Duración estimada: 4-5 horas**

### ¿Por qué ahora?
- ✅ Los usuarios ya tienen besitos que gastar
- ✅ Existe inventario donde almacenar compras
- ✅ Crea un sink económico para los besitos

### Implementación:
```
services/shop_service.py
├── ShopService
├── get_shop_items(category=None)
├── purchase_item(user_id, item_id)
├── can_afford_item(user_id, item_id)
└── get_purchase_history(user_id)

database/models.py
├── shop_items table
│   ├── item_id, name, description, price
│   ├── category, is_available, stock
│   └── item_data (JSON for special properties)
└── user_purchases table

Static shop items:
├── "Pista Misteriosa" - 50 besitos
├── "Amuleto de Suerte" - 100 besitos  
├── "Carta de Diana" - 200 besitos
├── "Llave Dorada" - 500 besitos
└── "Secreto Ancestral" - 1000 besitos

handlers/user/shop.py
├── /tienda handler with categories
├── /comprar callback handlers
└── Purchase confirmation system
```

### Funcionalidad completa:
- Tienda con items categorizados
- Sistema de compra con confirmación
- Validación de saldo suficiente
- Items se almacenan en inventario automáticamente
- Historial de compras del usuario

### Testing:
- Verificar que las compras consumen besitos correctamente
- Validar que items aparecen en inventario
- Confirmar prevención de compras sin saldo

---

## Sesión 5: Sistema de Trivias 🧠
**Duración estimada: 3-4 horas**

### ¿Por qué ahora?
- ✅ Otra forma de ganar besitos (diversifica las fuentes)
- ✅ Contenido que no depende de desarrollo narrativo complejo
- ✅ Mecánica autónoma y reutilizable

### Implementación:
```
services/trivia_service.py
├── TriviaService
├── get_daily_trivia(user_id)
├── submit_answer(user_id, trivia_id, answer)
├── get_trivia_history(user_id)
└── create_trivia_question(question, options, correct, reward)

database/models.py
├── trivia_questions table
├── user_trivia_attempts table
└── trivia_rewards table

Static questions:
├── "¿Cuál es la moneda de Diana Bot?" → "Besitos"
├── "¿Quién es el mayordomo?" → "Lucien"  
├── "¿Cuántos niveles tiene el canal gratuito?" → "3"
└── [10-15 preguntas iniciales]

handlers/user/trivia.py
├── /trivia handler
├── Answer callback handlers
└── Results and rewards display
```

### Funcionalidad completa:
- Trivia diaria para cada usuario
- Recompensas por respuestas correctas
- Historial de participación
- Preguntas con 3-4 opciones múltiples
- Cooldown para evitar spam

### Testing:
- Verificar recompensas por respuestas correctas
- Validar cooldown entre trivias
- Confirmar que se registra el historial

---

# FASE 3: INTERACCIÓN SOCIAL
*Objetivo: Conectar usuarios con contenido de canales*

## Sesión 6: Tracking de Reacciones en Canales 👍
**Duración estimada: 4-5 horas**

### ¿Por qué ahora?
- ✅ Conecta el bot con la actividad real en canales
- ✅ Crea incentivos para engagement
- ✅ Usa infraestructura de Event Bus existente

### Implementación:
```
services/reaction_tracking_service.py
├── ReactionTrackingService
├── register_reaction(user_id, message_id, reaction_type)
├── get_user_reaction_stats(user_id)
├── check_reaction_rewards(user_id)
└── get_eligible_messages()

database/models.py
├── tracked_messages table (admin-defined)
├── user_reactions table (user activity)
└── reaction_rewards table (rewards given)

middlewares/reaction_middleware.py
└── Monitor specific channel messages for reactions

handlers/admin/reaction_admin.py
├── /admin_reactions - Manage tracked messages
└── Configure reward amounts per reaction type

handlers/user/reaction_status.py
└── /mis_reacciones - User reaction history
```

### Funcionalidad completa:
- Admin puede marcar mensajes para tracking
- Usuarios ganan besitos por reaccionar a mensajes marcados
- Visualización de estadísticas de reacciones
- Prevención de spam (una reacción por usuario por mensaje)
- Sistema de rewards escalables por tipo de reacción

### Testing:
- Verificar que se detectan reacciones correctamente
- Validar otorgamiento de besitos por reacciones
- Confirmar prevención de duplicados

---

## Sesión 7: Personajes - Lucien y Diana 🎭
**Duración estimada: 5-6 horas**

### ¿Por qué ahora?
- ✅ Todo el sistema base ya existe
- ✅ Puede integrarse en interacciones existentes
- ✅ No requiere nuevas mecánicas, solo personalidad

### Implementación:
```
services/character_service.py
├── CharacterService
├── get_lucien_response(context, user_data)
├── get_diana_response(context, user_data)
├── generate_contextual_dialogue(character, situation)
└── validate_character_consistency()

data/characters/
├── lucien_dialogues.json
│   ├── greetings, narrative_transitions
│   ├── shop_interactions, reward_celebrations
│   └── encouraging_messages, witty_remarks
└── diana_dialogues.json
    ├── mysterious_responses, seductive_hints
    └── level_progression_messages

enhanced_diana_menu_system.py
├── Integrate Lucien responses in menus
├── Add Diana messages for special moments
└── Context-aware character responses

handlers/user/characters.py
├── /lucien - Direct interaction
└── /diana - Special Diana moments
```

### Funcionalidad completa:
- Lucien aparece en interacciones del menú con personalidad propia
- Diana da mensajes especiales en momentos clave (level up, achievements)
- Respuestas contextuales basadas en progreso del usuario
- Personalidades distintivas y consistentes
- Sistema extensible para más diálogos

### Testing:
- Verificar que las personalidades son distintivas
- Validar que los contextos generan respuestas apropiadas
- Confirmar consistencia con Diana Character Validator

---

# FASE 4: CONTENIDO AVANZADO
*Objetivo: Expandir la experiencia narrativa*

## Sesión 8: Sistema de Pistas (LorePieces) 🔍
**Duración estimada: 4-5 horas**

### ¿Por qué ahora?
- ✅ Tienda ya existe para vender pistas
- ✅ Inventario ya puede almacenar pistas
- ✅ Personajes pueden dar contexto a las pistas

### Implementación:
```
services/lore_service.py
├── LoreService
├── get_available_lore_pieces(user_id)
├── unlock_lore_piece(user_id, lore_id)
├── get_user_lore_collection(user_id)
└── combine_lore_pieces(user_id, piece_ids)

database/models.py
├── lore_pieces table (definitions)
├── user_lore_pieces table (unlocked)
└── lore_combinations table (special unlocks)

Initial lore pieces:
├── "El Origen de Diana" - Comprable en tienda
├── "Los Secretos de Lucien" - Reward por achievement
├── "El Primer Encuentro" - Unlock por Level 2
└── "La Promesa Dorada" - Combinación especial

enhanced_diana_menu_system.py
└── Lore collection viewer

handlers/user/lore.py
├── /pistas - View collection
└── /combinar - Combine pieces interface
```

### Funcionalidad completa:
- Pistas se desbloquean por múltiples medios (compra, achievements, progreso)
- Usuario puede ver su colección de pistas
- Sistema de combinación para unlocks especiales
- Pistas añaden contexto narrativo sin afectar progreso principal
- Integración con personajes para dar contexto

### Testing:
- Verificar que pistas se desbloquean correctamente
- Validar sistema de combinación
- Confirmar que se almacenan en inventario

---

## Sesión 9: Contenido VIP Narrativo 👑
**Duración estimada: 5-6 horas**

### ¿Por qué ahora?
- ✅ Sistema narrativo base está sólido
- ✅ Validación VIP ya existe
- ✅ Puede monetizar el contenido desarrollado

### Implementación:
```
services/vip_narrative_service.py
├── VIPNarrativeService  
├── get_vip_fragments(user_id)
├── validate_vip_access(user_id)
└── unlock_vip_level(user_id, level)

database/narrative_fragments_unified.py
└── Add VIP fragments (Levels 4-6)

New VIP fragments:
├── Level 4: "Despertar Profundo"
├── Level 5: "Encuentro Íntimo"  
├── Level 6: "Revelación Final"
└── Special VIP endings

enhanced_diana_menu_system.py
├── VIP content gates
└── Upgrade prompts for non-VIP users

handlers/vip/vip_narrative.py
├── VIP-only narrative handlers
└── Subscription validation
```

### Funcionalidad completa:
- 3 niveles narrativos exclusivos para VIP
- Validación automática de suscripción
- Contenido premium con mayor profundidad
- Prompts de upgrade para usuarios free
- Continuidad narrativa desde Level 3

### Testing:
- Verificar que solo VIP accede al contenido
- Validar continuidad narrativa
- Confirmar prompts de upgrade para free users

---

## Sesión 10: Sistema de Subastas VIP 💎
**Duración estimada: 6-7 horas**

### ¿Por qué ahora?
- ✅ Usuarios VIP ya tienen acceso premium
- ✅ Sistema de besitos maduro para pujas
- ✅ Inventario puede almacenar items ganados

### Implementación:
```
services/auction_service.py
├── AuctionService
├── create_auction(item_data, starting_bid, duration)
├── place_bid(user_id, auction_id, amount)
├── get_active_auctions()
├── get_auction_history(user_id)
└── finalize_auction(auction_id)

database/models.py
├── auctions table
├── auction_bids table
└── auction_winners table

Background tasks:
└── Auction monitor and auto-finalization

handlers/vip/auctions.py
├── /subastas - View active auctions
├── /pujar - Place bid interface
└── /historial_subastas - Auction history

Auction items:
├── "Mensaje Exclusivo de Diana"
├── "Acceso a Fragmento Secreto"
└── "Consulta Privada con Lucien"
```

### Funcionalidad completa:
- Subastas en tiempo real solo para VIP
- Sistema de pujas con validación de saldo
- Auto-finalización al vencer tiempo
- Notificaciones a ganadores
- Items exclusivos que no se pueden obtener de otra forma

### Testing:
- Verificar que solo VIP puede participar
- Validar mecánica de pujas en tiempo real
- Confirmar entrega automática a ganadores

---

# FASE 5: ADMINISTRACIÓN AVANZADA
*Objetivo: Herramientas admin para gestión de contenido*

## Sesión 11: Panel de Publicaciones Programadas 📅
**Duración estimada: 4-5 horas**

### Implementación:
```
services/publication_service.py
├── PublicationService
├── schedule_publication(channel, content, datetime)
├── get_scheduled_publications()
└── cancel_publication(pub_id)

Background tasks:
└── Publication scheduler

handlers/admin/publications.py
├── /admin_publicar - Schedule interface
├── /admin_calendario - View scheduled
└── Content creation tools
```

---

## Sesión 12: Contenido Interactivo en Canales 🎯
**Duración estimada: 5-6 horas**

### Implementación:
```
services/interactive_content_service.py
├── InteractiveContentService
├── create_decision_post(content, options)
├── process_inline_responses()
└── track_engagement_metrics()

Integration:
└── Narrative decisions in channel posts
```

---

## 📊 RESUMEN DE LA HOJA DE RUTA

### Cronograma Estimado:
- **Fase 1** (Sesiones 1-3): 8-11 horas → **Experiencia usuario básica**
- **Fase 2** (Sesiones 4-5): 7-9 horas → **Economía funcional**
- **Fase 3** (Sesiones 6-7): 9-11 horas → **Interacción social**  
- **Fase 4** (Sesiones 8-10): 15-18 horas → **Contenido avanzado**
- **Fase 5** (Sesiones 11-12): 9-11 horas → **Admin tools**

### **Total estimado: 48-60 horas de desarrollo**

### Milestone Goals:
- **Después Fase 1**: Usuario ve recompensas tangibles
- **Después Fase 2**: Ciclo económico básico funcional
- **Después Fase 3**: Engagement con canales conectado
- **Después Fase 4**: Experiencia narrativa completa
- **Después Fase 5**: Sistema completamente autónomo

### **Cada sesión produce una mejora inmediatamente visible para los usuarios** ✅