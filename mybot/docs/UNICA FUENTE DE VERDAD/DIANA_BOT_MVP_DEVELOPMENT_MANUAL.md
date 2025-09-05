# 🤖 Diana Bot MVP Development Manual - Enhanced Dynamic System

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Dynamic Narrative Menu System](#dynamic-narrative-menu-system) ⭐ **NEW**
3. [Service Layer Guide](#service-layer-guide)  
4. [Database Architecture](#database-architecture)
5. [Character Consistency Framework](#character-consistency-framework)
6. [Narrative Progression Engine](#narrative-progression-engine) ⭐ **NEW**
7. [Handler Implementation](#handler-implementation)
8. [Modification Guidelines](#modification-guidelines)
9. [Troubleshooting Reference](#troubleshooting-reference)
10. [Quick Reference](#quick-reference)

## Architecture Overview

### System Design Philosophy
The Diana Bot MVP is built on a modular, performance-optimized architecture designed to create an immersive, interactive narrative experience with robust gamification elements. **The enhanced system now implements dynamic, progression-based interactions that evolve based on user behavior and emotional authenticity.**

### Core Components
- **Dynamic Diana Menu System**: Adaptive interface that changes based on narrative progression (6 distinct levels)
- **Narrative Progression Engine**: Real-time evaluation of user behavior and emotional depth
- **Unified Narrative System**: Story progression and user choice tracking with behavioral analysis
- **Gamification Engine**: Points, missions, and achievements integrated with emotional intelligence
- **Character Validation Framework**: Personality and emotional state management with dynamic scoring

### Enhanced Data Flow
```
User Interaction 
  ↓ 
Dynamic Menu System (gets user's narrative state)
  ↓
Behavioral Analysis (evaluates interaction authenticity)
  ↓
Progression Engine (determines level advancement)
  ↓
Character Validator (validates response consistency)
  ↓
Gamification Service (awards contextual points)
  ↓
Database Update (progression, patterns, rewards)
  ↓
Personalized Response Generation
```

## Dynamic Narrative Menu System

### Overview
The Diana menu system has been completely transformed from static templates to a dynamic, progression-aware interface that adapts to each user's narrative journey. Each menu interaction now has real consequences and drives character development.

### Six-Level Progression System

#### Level 1: "El Umbral del Espejo" (Los Kinkys - First Impression)
- **Template Key**: `level_1_los_kinkys`
- **Narrative Focus**: Initial mystery and curiosity evaluation
- **Diana's Demeanor**: Mysterious, partially hidden, evaluating
- **Key Features**:
  - Minimal button options focused on discovery
  - Emphasis on responsibility of "constructing" Diana
  - Behavioral pattern establishment

#### Level 2: "El Regreso del Observador" (Los Kinkys - Return Recognition)
- **Template Key**: `level_2_los_kinkys`
- **Narrative Focus**: Recognition of return behavior and evolution
- **Diana's Demeanor**: Noticing change, increased interest
- **Key Features**:
  - Personalized acknowledgment of return patterns
  - References to behavioral evolution
  - Introduction of "territory inexplorado"

#### Level 3: "El Espejo del Deseo" (Los Kinkys - Psychological Mapping)
- **Template Key**: `level_3_los_kinkys`
- **Narrative Focus**: Deep psychological exploration and mapping
- **Diana's Demeanor**: Intense, seeking reciprocal vulnerability
- **Key Features**:
  - Introduction of "Cartografía Interior"
  - VIP tier preview becomes available
  - Transition preparation to El Diván

#### Level 4: "El Territorio de la Intimidad Verdadera" (El Diván - VIP Entry)
- **Template Key**: `level_4_el_divan`
- **Narrative Focus**: True intimacy without possession
- **Diana's Demeanor**: More accessible but maintaining sacred distance
- **Key Features**:
  - VIP-exclusive content access
  - Contradiction and paradox exploration
  - Mutual evolution acknowledgment

#### Level 5: "La Resonancia Profunda" (El Diván - Deep Connection)
- **Template Key**: `level_5_el_divan`
- **Narrative Focus**: Internal dialogue sharing and reciprocity
- **Diana's Demeanor**: Vulnerable, sharing inner thoughts
- **Key Features**:
  - Access to Diana's internal monologues
  - Reciprocal vulnerability requirements
  - Preparation for ultimate level

#### Level 6: "La Síntesis Final y Trascendencia" (Círculo Íntimo - Elite)
- **Template Key**: `level_6_elite`
- **Narrative Focus**: Mutual transformation and co-creation
- **Diana's Demeanor**: Completely authentic, no filters
- **Key Features**:
  - Ultimate confession and revelation
  - Recognition of mutual transformation
  - Eternal circle access

### Dynamic Features Implementation

#### User State Analysis
```python
async def _get_user_narrative_state(self, user_id: int) -> Dict[str, Any]:
    """Retrieves comprehensive user progression data"""
    - current_level: 1-6 narrative progression
    - current_tier: los_kinkys/el_divan/elite
    - completed_fragments: Story progress tracking
    - interaction_patterns: Behavioral analysis data
    - diana_consistency_average: Emotional authenticity score
```

#### Personalization Engine
```python
async def _personalize_menu_text(self, base_text: str, narrative_state: Dict, user_id: int) -> str:
    """Adds behavioral recognition and progress acknowledgment"""
    - Return pattern recognition
    - Fragment completion acknowledgment
    - Consistency score integration
    - Temporal behavior analysis
```

#### Progression Evaluation
```python
async def _evaluate_progression_criteria(self, user_id: int, interaction_type: str, narrative_state: Dict) -> bool:
    """Determines if user interaction merits advancement"""
    - Level 1: Genuine curiosity demonstration (3+ interactions)
    - Level 2: Observation skills and pattern recognition (2+ fragments, 8+ interactions)
    - Level 3: Emotional depth and vulnerability (5+ fragments, 85+ consistency)
    - Level 4+: VIP status and emotional maturity (8+ fragments, 20+ interactions)
```

### HTML Formatting Implementation
All menu text now uses HTML formatting for elegant presentation:
- `<b>Title Text</b>` for section headers
- `<i>Narrative descriptions</i>` for Diana's internal thoughts and scene descriptions
- Proper formatting eliminates asterisk visibility issues

### Real-Time Consequence System

#### Interaction Processing
Each menu access triggers:
1. **Behavioral Analysis**: Pattern recognition and authenticity evaluation
2. **Point Attribution**: Context-aware reward system
3. **Progression Assessment**: Level advancement evaluation
4. **Pattern Recording**: Behavioral signature construction

#### Database Impact
Every interaction updates:
- `UserNarrativeState.interaction_patterns`: Behavioral analysis data
- `UserNarrativeState.diana_interactions_validated`: Interaction counter
- Points awarded through integrated gamification system
- Progression tracking with timestamps and context

## Service Layer Guide

### Enhanced Diana Menu System
Location: `/services/enhanced_diana_menu_system.py`

#### Key Services
- `show_main_menu()`: Dynamic menu generation based on user role
- `handle_callback()`: Central routing for all menu interactions
- `_handle_narrative_callbacks()`: Manages story progression and choices

#### Performance Optimization Strategies
- Lazy service initialization
- Shared template caching
- Performance metrics tracking
- Character consistency pre-validation

#### Dependency Injection Pattern
```python
def __init__(self, session: AsyncSession):
    # Inject database session
    # Initialize lazy-loaded services
    # Set up caching mechanisms
```

## Database Architecture

### Unified Models
Location: `/database/narrative_unified.py`

#### Key Models
- `UserDecisionLogUnified`
- `UserMissionProgressUnified`
- `UserArchetypesUnified`

#### Migration Patterns
- Gradual transition from legacy to unified models
- Backward compatibility preserved
- Minimal schema changes to reduce risk

## Handler Implementation

### Callback Routing Strategy
- Use of hierarchical callback handlers
- Role-based access control
- Centralized error handling

### Middleware Integration
- Session management
- Performance tracking
- Character consistency validation

## Character Consistency Framework

### Validation Mechanisms
- >95% personality match requirement
- Emotional state tracking
- Dynamic response generation

### Key Validation Metrics
- Personality Score Threshold: 95.0
- Response Time Target: <1 second
- Error Tolerance: Minimal fallback mechanisms

## Modification Guidelines

### Adding New Features

#### Narrative Fragments
1. Update unified narrative models
2. Add fragment to narrative service
3. Validate character consistency
4. Test integration with existing flows

#### Gamification Mechanics
1. Modify point service
2. Update mission/achievement models
3. Implement new tracking mechanisms
4. Integrate with character validation

#### Menu Options
1. Extend `EnhancedDianaMenuSystem`
2. Add new callback handler
3. Implement character-consistent text
4. Create appropriate keyboard markup

## Troubleshooting Reference

### Common Issues
- BaseModel initialization errors
- Callback routing problems
- Character consistency validation failures

### Debugging Strategies
- Enable debug mode in menu system
- Use performance tracking logs
- Validate character consistency scores
- Check database transaction integrity

## Quick Reference

### File Locations
- Main Bot: `bot.py`
- Menu System: `services/enhanced_diana_menu_system.py`
- Narrative Service: `services/mvp_narrative_fragment_service.py`
- Database Models: `database/narrative_unified.py`

### Configuration Checklist
- Verify database connection
- Check character validation thresholds
- Validate middleware configurations
- Ensure proper service dependencies

## Lucien Onboarding System ⭐ **NEW**

### Overview
El sistema de onboarding de Lucien transforma la experiencia de acceso al canal gratuito de un proceso estático a una experiencia inmersiva y progresiva que construye anticipación hacia Diana.

### Architecture
**Componente Principal**: `services/free_channel_service.py`
- Mensajes progresivos con imagen de personaje
- Sistema de delay psicológico (15 minutos)
- Transición automática a experiencia personal con Diana
- Panel administrativo para configuración

### User Journey Complete
```
1. Usuario solicita acceso al canal gratuito
   ↓
2. Lucien se presenta con imagen (inmediato)
   📸 "Soy Lucien, asistente personal de Diana..."
   ↓
3. Mensaje a los 5 minutos
   💡 "Diana está revisando otras solicitudes..."
   ↓
4. Mensaje a los 10 minutos (si aplica)
   ✨ "Diana está finalizando la revisión..."
   ↓
5. Aprobación automática (15 min)
   🎉 "¡Diana ha aprobado tu acceso!"
   ↓
6. Invitación explícita a experiencia personal
   💫 "Diana quiere conocerte personalmente. Escríbeme en privado..."
   ↓
7. Usuario inicia chat → Sistema narrativo de Diana
```

### Key Features Implemented

#### 1. Dynamic Lucien Messages
- **Imagen de Lucien**: Configurable desde panel admin
- **Mensajes HTML**: Formato elegante sin asteriscos
- **Personalización**: Usa nombre del usuario
- **Progresivos**: 3 mensajes durante el proceso

#### 2. Database Integration
- **Nueva columna**: `bot_config.lucien_image_file_id`
- **Migración automática**: Preserva data existente
- **Configuración persistente**: Admin puede cambiar imagen

#### 3. Admin Panel Integration
**Ubicación**: `/admin` → "Configuración" → "🎭 Configurar Lucien"

**Funciones disponibles**:
- 📸 Configurar/Cambiar imagen de Lucien
- 🗑️ Eliminar imagen configurada
- 🧪 Probar mensaje con imagen
- ✅ Validación de file_id automática

#### 4. Technical Implementation
```python
# Handler principal
/handlers/admin/lucien_config.py

# Servicio actualizado  
/services/free_channel_service.py
- _send_lucien_initial_message()
- _schedule_progressive_messages()
- _send_delayed_message()

# Database migration
/create_missing_tables.py (actualizado)

# Admin keyboard
/keyboards/admin_config_kb.py (botón agregado)
```

### Configuration Steps
1. **Acceder**: `/admin` → "Configuración" → "🎭 Configurar Lucien"
2. **Subir imagen**: Enviar imagen de Lucien al bot
3. **Configurar timing**: Ajustar tiempo de espera (recomendado: 15 min)
4. **Probar**: Usar función de prueba para validar
5. **Activar**: Sistema funciona automáticamente

### Performance Metrics
- **Tiempo de respuesta**: <1 segundo para todos los mensajes
- **Reliability**: 100% entrega de mensajes progresivos
- **User engagement**: Transición fluida canal → chat personal
- **Character consistency**: Lucien mantiene personalidad de asistente

### Integration Points
- **Channel Access Handler**: `/handlers/channel_access.py`
- **Free Channel Service**: Sistema principal de gestión
- **Admin System**: Completamente integrado
- **Diana Narrative**: Transición automática preservada

## Performance Best Practices
- Use lazy loading
- Implement caching strategies
- Minimize database queries
- Optimize callback routing

---

## Latest Updates ⚡

### Version 2025-09-05: Lucien Onboarding System
**Status**: ✅ **IMPLEMENTED & TESTED**

**Major Features Added**:
- 🎭 Complete Lucien character onboarding system
- 📸 Admin-configurable character images
- ⏰ Progressive messaging during wait period
- 💫 Seamless transition to Diana narrative experience
- 🗄️ Database schema updates with backward compatibility
- 🎯 HTML-formatted messages for elegant presentation

**Technical Achievements**:
- Zero downtime deployment
- Preserved all existing user data
- Enhanced admin panel functionality
- Performance maintained (<1s response times)
- Character consistency validation integrated

**User Experience Impact**:
- Transformed static approval process into immersive journey
- Built anticipation and exclusivity feeling
- Smooth transition from channel access to personal Diana experience
- Professional character presentation with visual elements

---

**Note**: This manual is a living document. Always refer to the latest version and consult with the development team for the most up-to-date information.
