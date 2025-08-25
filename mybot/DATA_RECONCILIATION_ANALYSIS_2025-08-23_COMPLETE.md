# SEMANA 2: Análisis de Reconciliación de Datos

```yaml
---
name: data_reconciliation_analyst
description: Mapea y reconcilia flujos de datos entre modelos duplicados del sistema Diana
color: orange
---
```

## 1. DATABASE SCHEMA ANALYSIS

### 1.1 Modelos de Datos Principales

#### 1.1.1 Sistema de Narrativa y Pistas

**LorePiece & UserLorePiece (database/models.py)**
- `LorePiece`: Almacena fragmentos de narrativa/pistas
  - Atributos: id, code_name, title, description, content_type, content, category, is_main_story, etc.
- `UserLorePiece`: Mapea qué pistas ha desbloqueado cada usuario
  - Atributos: user_id, lore_piece_id, unlocked_at, context

**StoryFragment & NarrativeChoice (database/narrative_models.py)**
- `StoryFragment`: Fragmentos de historia interactiva básica
  - Atributos: id, key, text, character, level, min_besitos, required_role, etc.
- `NarrativeChoice`: Decisiones dentro de los fragmentos de historia
  - Atributos: id, source_fragment_id, destination_fragment_key, text, required_besitos, required_role

**NarrativeFragment & NarrativeDecision (database/narrative_models.py)**
- `NarrativeFragment`: Fragmentos de narrativa mejorados (versión extendida)
  - Atributos: id, key, title, content, completion_points, is_completion_point, requires_engagement, etc.
- `NarrativeDecision`: Decisiones mejoradas en narrativa
  - Atributos: id, fragment_key, text, next_fragment_key, points_reward, karma_modifier, etc.

**UserNarrativeState (database/narrative_models.py)**
- Estado de progreso del usuario en la narrativa
  - Atributos: user_id, current_fragment_key, choices_made, fragments_visited, fragments_completed, etc.

#### 1.1.2 Sistema de Transacciones

**PointTransaction & VipTransaction (database/transaction_models.py)**
- `PointTransaction`: Auditoría completa de operaciones de puntos
  - Atributos: id, user_id, amount, balance_after, source, description, created_at
- `VipTransaction`: Auditoría completa de estado VIP
  - Atributos: id, user_id, action, source, source_id, duration_days, expires_at, is_active, created_at, notes

#### 1.1.3 Sistema de Usuarios y Recompensas

**User (database/models.py)**
- Información principal del usuario
  - Atributos: id, username, first_name, last_name, points, level, achievements, etc.

**UserReward, UserAchievement, UserMissionEntry, UserBadge (database/models.py)**
- Modelos para tracking de recompensas, logros, misiones y badges del usuario

## 2. DATA FLOW MAPPING

### 2.1 Flujos de Narrativa

1. **Desbloqueo de Pistas (LorePiece)**
   - Trigger: Completar misiones, alcanzar niveles, decisiones narrativas
   - Flujo: services/narrative_service.py → database/models.py (LorePiece/UserLorePiece) → bot interactions
   - Archivos clave: narrativa.py, mochila.py, backpack.py, combinar_pistas.py

2. **Progresión Narrativa (StoryFragment/NarrativeFragment)**
   - Trigger: Interacciones del usuario con la narrativa
   - Flujo: services/narrative_engine.py → database/narrative_models.py → services/narrative_service.py
   - Archivos clave: services/narrative_engine.py, services/narrative_service.py, services/narrative_loader.py

3. **Estado de Usuario (UserNarrativeState)**
   - Actualización: Cada interacción narrativa
   - Flujo: services/narrative_engine.py → database/narrative_models.py (UserNarrativeState)

### 2.2 Flujos de Transacciones

1. **Transacciones de Puntos (PointTransaction)**
   - Trigger: Actividades del usuario (mensajes, reacciones, checkins)
   - Flujo: services/point_service.py → database/transaction_models.py (PointTransaction)
   - Archivos clave: services/point_service.py, database/transaction_models.py

2. **Transacciones VIP (VipTransaction)**
   - Trigger: Suscripciones, badges VIP, promociones
   - Flujo: services/subscription_service.py, services/token_service.py → database/transaction_models.py (VipTransaction)
   - Archivos clave: services/subscription_service.py, services/token_service.py

## 3. DATA DUPLICATION REPORT

### 3.1 Modelos Duplicados Identificados

1. **Sistema de Narrativa**
   - **Duplicación**: StoryFragment vs NarrativeFragment
     - `StoryFragment`: Modelo básico para narrativa interactiva
     - `NarrativeFragment`: Modelo extendido con características adicionales
     - **Impacto**: Confusión en el desarrollo, posibles inconsistencias en tracking de progreso

2. **Sistema de Progresión de Usuario**
   - **Duplicación**: User.points vs UserNarrativeState (antes tenía total_besitos_earned)
     - `User.points`: Almacena puntos totales del usuario
     - `UserNarrativeState`: Antes tenía campo redundante total_besitos_earned (ya removido)
     - **Impacto**: Redundancia eliminada, pero requiere verificación de consistencia

### 3.2 Campos Duplicados o Redundantes

1. **En User Model**
   - `points`: Puntos totales del usuario
   - `achievements`: Logros desbloqueados (JSON)
   - `missions_completed`: Misiones completadas (JSON)
   
2. **En UserNarrativeState**
   - `fragments_visited`: Contador de fragmentos visitados
   - `fragments_completed`: Contador de fragmentos completados

## 4. INCONSISTENCY CATALOG

### 4.1 Inconsistencias Estructurales

1. **Duplicación de Modelos Narrativos**
   - `StoryFragment` y `NarrativeFragment` tienen propósitos similares pero estructuras diferentes
   - Falta documentación clara sobre cuándo usar cada uno

2. **Redundancia en Tracking de Progreso**
   - Aunque se eliminó `total_besitos_earned` de `UserNarrativeState`, se debe verificar que todos los servicios usen `User.points` consistentemente

### 4.2 Inconsistencias de Flujo

1. **Desbloqueo de Pistas**
   - Algunas pistas se desbloquean a través de `LorePiece` directamente
   - Otras se desbloquean como resultado de decisiones narrativas
   - No hay unificación en el mecanismo de desbloqueo

2. **Sistema de Recompensas**
   - Recompensas pueden venir de misiones, niveles, trivias o decisiones narrativas
   - Diferentes modelos y flujos manejan estas recompensas sin un sistema unificado

## 5. MIGRATION ROADMAP

### 5.1 Fase 1: Unificación de Modelos Narrativos

**Objetivo**: Consolidar StoryFragment y NarrativeFragment en un único modelo

1. **Análisis de Impacto**
   - Identificar todas las dependencias de ambos modelos
   - Mapear funcionalidades únicas de cada modelo

2. **Diseño del Modelo Unificado**
   - Crear nuevo modelo StoryFragment con todas las funcionalidades
   - Mantener compatibilidad con versiones existentes

3. **Migración de Datos**
   - Script para migrar datos de NarrativeFragment a StoryFragment
   - Verificación de integridad post-migración

4. **Actualización de Servicios**
   - Refactorizar servicios que usan NarrativeFragment
   - Eliminar referencias a NarrativeFragment

### 5.2 Fase 2: Unificación de Sistemas de Recompensas

**Objetivo**: Crear un sistema unificado de recompensas narrativas

1. **Análisis de Recompensas Actuales**
   - Mapear todas las fuentes de recompensas (misiones, niveles, trivias, narrativa)
   - Identificar tipos de recompensas y su valoración

2. **Diseño del Sistema Unificado**
   - Crear modelo unificado de recompensas narrativas
   - Definir API común para otorgar recompensas

3. **Migración e Integración**
   - Adaptar servicios existentes al nuevo sistema
   - Implementar mecanismos de retrocompatibilidad

### 5.3 Fase 3: Verificación y Optimización

**Objetivo**: Asegurar consistencia y performance post-migración

1. **Pruebas Integrales**
   - Verificar que todos los flujos narrativos funcionen correctamente
   - Validar que las transacciones de puntos y VIP sean consistentes

2. **Optimización de Queries**
   - Revisar y optimizar consultas a la base de datos
   - Implementar índices necesarios

3. **Documentación y Capacitación**
   - Actualizar documentación técnica
   - Preparar guía de migración para desarrolladores

## 6. RECOMMENDATIONS

1. **Priorizar la unificación de modelos narrativos** para reducir complejidad
2. **Implementar un sistema de recompensas unificado** para mejorar la mantenibilidad
3. **Mantener auditoría completa** con PointTransaction y VipTransaction
4. **Documentar claramente** cuándo usar cada modelo y cómo migrar entre ellos
5. **Establecer protocolos de verificación** para mantener consistencia de datos post-migración