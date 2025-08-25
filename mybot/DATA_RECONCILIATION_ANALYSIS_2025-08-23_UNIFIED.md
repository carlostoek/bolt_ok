# SEMANA 2: Análisis de Reconciliación de Datos (Modelos Unificados)

```yaml
---
name: data_reconciliation_analyst
description: Mapea y reconcilia flujos de datos entre modelos duplicados del sistema Diana
color: orange
---
```

## 1. DATABASE SCHEMA ANALYSIS

### 1.1 Modelos de Datos Principales (Unificados)

#### 1.1.1 Sistema de Narrativa Unificada

**NarrativeFragment & UserNarrativeState (database/narrative_unified.py)**
- `NarrativeFragment`: Modelo unificado para fragmentos narrativos con soporte para historia, decisiones e información
  - Atributos: id (UUID), title, content, fragment_type, choices (JSON), triggers (JSON), required_clues (JSON), timestamps, is_active
  - Tipos de fragmentos: STORY, DECISION, INFO
- `UserNarrativeState`: Estado narrativo unificado del usuario
  - Atributos: user_id, current_fragment_id, visited_fragments (JSON), completed_fragments (JSON), unlocked_clues (JSON)

#### 1.1.2 Sistema de Misiones Unificadas

**UnifiedMission & UserMissionProgress (database/mission_unified.py)**
- `UnifiedMission`: Modelo unificado para misiones con integración completa de narrativa y recompensas
  - Atributos: id (UUID), title, description, mission_type, requirements (JSON), objectives (JSON), rewards (JSON), duration_days, expiration_date, is_active, is_repeatable, cooldown_hours, order, timestamps
  - Tipos de misiones: MAIN, SIDE, DAILY, WEEKLY, EVENT
- `UserMissionProgress`: Progreso del usuario en misiones unificadas
  - Atributos: id, user_id, mission_id, progress_data (JSON), is_completed, completed_at, times_completed, last_reset_at, timestamps

#### 1.1.3 Sistema de Transacciones (Sin Cambios)

**PointTransaction & VipTransaction (database/transaction_models.py)**
- `PointTransaction`: Auditoría completa de operaciones de puntos
  - Atributos: id, user_id, amount, balance_after, source, description, created_at
- `VipTransaction`: Auditoría completa de estado VIP
  - Atributos: id, user_id, action, source, source_id, duration_days, expires_at, is_active, created_at, notes

#### 1.1.4 Sistema de Usuarios (Sin Cambios)

**User (database/models.py)**
- Información principal del usuario
  - Atributos: id, username, first_name, last_name, points, level, achievements, etc.

## 2. DATA FLOW MAPPING

### 2.1 Flujos de Narrativa Unificada

1. **Progresión Narrativa (NarrativeFragment)**
   - Trigger: Comandos de usuario, decisiones narrativas
   - Flujo: handlers/unified_narrative_handler.py → services/unified_narrative_service.py → database/narrative_unified.py
   - Archivos clave: handlers/unified_narrative_handler.py, services/unified_narrative_service.py

2. **Estado de Usuario (UserNarrativeState)**
   - Actualización: Cada interacción narrativa
   - Flujo: services/unified_narrative_service.py → database/narrative_unified.py

### 2.2 Flujos de Misiones Unificadas

1. **Gestión de Misiones (UnifiedMission)**
   - Trigger: Comandos de usuario, progreso narrativo, acciones del usuario
   - Flujo: handlers/unified_mission_handler.py → services/unified_mission_service.py → database/mission_unified.py
   - Archivos clave: handlers/unified_mission_handler.py, services/unified_mission_service.py

2. **Progreso de Misiones (UserMissionProgress)**
   - Actualización: Cada acción del usuario que afecta una misión
   - Flujo: services/unified_mission_service.py → database/mission_unified.py

### 2.3 Flujos de Transacciones (Sin Cambios)

1. **Transacciones de Puntos (PointTransaction)**
   - Trigger: Actividades del usuario (mensajes, reacciones, checkins, recompensas de misiones/narrativa)
   - Flujo: services/point_service.py → database/transaction_models.py (PointTransaction)

2. **Transacciones VIP (VipTransaction)**
   - Trigger: Suscripciones, badges VIP, promociones
   - Flujo: services/subscription_service.py → database/transaction_models.py (VipTransaction)

## 3. DATA DUPLICATION REPORT

### 3.1 Modelos Duplicados Eliminados

1. **Sistema de Narrativa**
   - **Eliminados**: StoryFragment, NarrativeChoice, NarrativeFragment (modelo antiguo), NarrativeDecision (modelos antiguos)
   - **Unificado en**: NarrativeFragment (nuevo modelo unificado en database/narrative_unified.py)
   - **Impacto**: Reducción de complejidad, eliminación de inconsistencias en tracking de progreso

2. **Sistema de Progresión de Usuario**
   - **Eliminados**: Redundancia entre User.points y UserNarrativeState.total_besitos_earned
   - **Unificado en**: User (para puntos totales) y UserNarrativeState (para progreso narrativo específico)
   - **Impacto**: Claridad en el propósito de cada modelo, eliminación de campos redundantes

### 3.2 Campos Duplicados o Redundantes Eliminados

1. **En UserNarrativeState (Antiguo)**
   - `total_besitos_earned`: Eliminado en favor de User.points para puntos totales

2. **En Modelos de Narrativa Antiguos**
   - `StoryFragment` y `NarrativeFragment`: Reemplazados por `NarrativeFragment` unificado
   - `NarrativeChoice`: Integrado como campo JSON en `NarrativeFragment` unificado

## 4. INCONSISTENCY CATALOG

### 4.1 Inconsistencias Estructurales Resueltas

1. **Duplicación de Modelos Narrativos**
   - **Resuelto**: StoryFragment y NarrativeFragment han sido unificados en un único modelo NarrativeFragment
   - **Beneficio**: Claridad en el desarrollo, consistencia en tracking de progreso

2. **Redundancia en Tracking de Progreso**
   - **Resuelto**: Campo redundante total_besitos_earned eliminado de UserNarrativeState
   - **Beneficio**: Puntos totales en User.points, progreso narrativo específico en UserNarrativeState

### 4.2 Inconsistencias de Flujo Resueltas

1. **Desbloqueo de Pistas**
   - **Resuelto**: Sistema unificado de triggers en NarrativeFragment para desbloqueo de pistas
   - **Beneficio**: Mecanismo unificado para todas las formas de desbloqueo de contenido

2. **Sistema de Recompensas**
   - **Resuelto**: Integración completa de recompensas en misiones y fragmentos narrativos
   - **Beneficio**: Sistema unificado de recompensas con múltiples tipos (puntos, pistas, insignias)

## 5. MIGRATION ROADMAP

### 5.1 Fase 1: Implementación de Modelos Unificados

**Objetivo**: Implementar modelos unificados y servicios asociados

1. **Modelos Unificados**
   - ✅ Implementados: NarrativeFragment, UserNarrativeState (unificados)
   - ✅ Implementados: UnifiedMission, UserMissionProgress

2. **Servicios Unificados**
   - ✅ Implementados: UnifiedNarrativeService, UnifiedMissionService

3. **Handlers Unificados**
   - ✅ Implementados: unified_narrative_handler, unified_mission_handler

### 5.2 Fase 2: Integración con Sistemas Existentes

**Objetivo**: Integrar modelos unificados con sistemas existentes de transacciones y usuarios

1. **Integración de Recompensas**
   - ✅ Integrados: Sistemas de recompensas unificados en triggers y misiones
   - ✅ Uso de RewardSystem para otorgar recompensas consistentemente

2. **Integración de Transacciones**
   - ✅ Mantenidos: PointTransaction y VipTransaction para auditoría completa
   - ✅ Integración con servicios existentes de puntos y suscripciones

### 5.3 Fase 3: Verificación y Optimización

**Objetivo**: Asegurar consistencia y performance post-migración

1. **Pruebas Integrales**
   - ⏳ En proceso: Verificación de flujos narrativos y de misiones
   - ⏳ En proceso: Validación de transacciones de puntos y VIP

2. **Optimización de Queries**
   - ⏳ Pendiente: Revisar y optimizar consultas a la base de datos
   - ⏳ Pendiente: Implementar índices necesarios

3. **Documentación y Capacitación**
   - ⏳ Pendiente: Actualizar documentación técnica
   - ⏳ Pendiente: Preparar guía de uso para desarrolladores

## 6. RECOMMENDATIONS

1. **✅ Completar pruebas integrales** para verificar que todos los flujos narrativos y de misiones funcionen correctamente
2. **✅ Verificar consistencia de transacciones** para validar que las transacciones de puntos y VIP sean consistentes
3. **✅ Mantener auditoría completa** con PointTransaction y VipTransaction
4. **✅ Documentar claramente** el nuevo sistema unificado y cómo interactúa con los sistemas existentes
5. **✅ Establecer protocolos de monitoreo** para mantener consistencia de datos en producción