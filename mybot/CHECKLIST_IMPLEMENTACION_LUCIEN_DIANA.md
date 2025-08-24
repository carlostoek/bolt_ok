# Checklist de Implementación: El Mayordomo del Diván

## Fase 1: Preparación y Modelos de Datos (3-4 días)

### Día 1-2: Extensión de Modelos
- [ ] Extender modelo `UserNarrativeState` con campos de Lucien-Diana
  - [ ] Añadir `lucien_trust_level`, `lucien_interaction_count`, `diana_appearances`
  - [ ] Añadir `narrative_level`, `archetype`, `quantum_effects`
- [ ] Extender modelo `NarrativeFragment` con campos adicionales
  - [ ] Añadir `presenter`, `diana_appearance_threshold`
  - [ ] Añadir `is_temporal`, `temporal_weekdays`, `temporal_hours`
  - [ ] Añadir `is_quantum`, `quantum_trigger_type`, `alternative_versions`
- [ ] Crear migraciones de base de datos
  - [ ] Script de migración para nuevos campos
  - [ ] Pruebas de migración con datos de prueba

### Día 3-4: Sistema de Eventos y Acciones
- [ ] Extender `EventBus` con nuevos tipos de eventos
  - [ ] Añadir `LUCIEN_CHALLENGE_ISSUED`, `LUCIEN_CHALLENGE_COMPLETED`
  - [ ] Añadir `LUCIEN_TRUST_INCREASED`, `DIANA_APPEARED` 
  - [ ] Añadir `QUANTUM_FRAGMENT_CHANGED`, `NARRATIVE_LEVEL_ADVANCED`
- [ ] Extender `AccionUsuario` en CoordinadorCentral
  - [ ] Añadir `LUCIEN_CHALLENGE`, `LUCIEN_DIALOGUE`
  - [ ] Añadir `DIANA_APPEARANCE`, `QUANTUM_TRIGGER`
- [ ] Configurar sistema de eventos de prueba
  - [ ] Crear suscriptores de prueba para eventos
  - [ ] Verificar propagación de eventos

## Fase 2: Servicios Core (5-7 días)

### Día 5-6: LucienService
- [ ] Implementar personalidad y respuestas de Lucien
  - [ ] Crear clase `LucienPersonality` con plantillas
  - [ ] Implementar generación formal de respuestas
- [ ] Implementar funciones core
  - [ ] `handle_initial_greeting`: Saludo inicial
  - [ ] `evaluate_user_reaction`: Evaluación de reacciones
  - [ ] `determine_diana_appearance`: Lógica de apariciones

### Día 7-8: ObservationChallengeService
- [ ] Implementar sistema de desafíos
  - [ ] `create_observation_challenge`: Crear desafíos
  - [ ] `evaluate_observation_attempt`: Evaluar respuestas
  - [ ] Niveles y dificultad progresiva
- [ ] Integrar con LucienService
  - [ ] Respuestas formales a intentos
  - [ ] Cambios de confianza por desafíos

### Día 9-10: Servicios Cuánticos y Temporales
- [ ] Implementar QuantumFragmentService
  - [ ] `apply_quantum_trigger`: Aplicar cambios retroactivos
  - [ ] Modificación de fragmentos por decisiones
- [ ] Implementar TemporalMomentService
  - [ ] `get_available_moments`: Momentos disponibles por tiempo
  - [ ] Restricciones por día y hora

### Día 11: DianaAppearanceService
- [ ] Implementar apariciones de Diana
  - [ ] `get_diana_response`: Respuestas según contexto
  - [ ] `register_diana_reaction`: Reacciones a apariciones
  - [ ] Control de frecuencia de apariciones

## Fase 3: Extensión de Servicios Existentes (3-5 días)

### Día 12-13: Extensión de CoordinadorCentral
- [ ] Implementar flujo Lucien-Diana
  - [ ] `_flujo_lucien_diana_dynamic`: Orquestación de interacciones
  - [ ] `_record_diana_appearance`: Registro de apariciones
- [ ] Integrar con eventos
  - [ ] Extender `_emit_workflow_events` para nuevos eventos
  - [ ] Correlación de eventos entre Lucien y Diana

### Día 14-15: Extensión de NotificationService
- [ ] Añadir tipos de notificación para Lucien-Diana
  - [ ] Tipo `lucien_message` para mensajes formales
  - [ ] Tipo `diana_appearance` para apariciones raras
- [ ] Implementar formateo especial
  - [ ] Extender `_build_enhanced_unified_message`
  - [ ] Diferenciación visual entre Lucien y Diana

### Día 16: Integración con DianaMenuSystem
- [ ] Añadir secciones de menú para Lucien
  - [ ] Sección de desafíos activos
  - [ ] Historial de interacciones con Lucien
- [ ] Adaptar sistema de desbloqueo progresivo
  - [ ] Integrar con niveles de confianza

## Fase 4: Handlers y Frontend (5-7 días)

### Día 17-18: Implementación de ChannelHandlers
- [ ] Implementar detección de solicitudes
  - [ ] `handle_join_request`: Manejo de solicitudes de canal
  - [ ] Programación de mensajes retrasados
- [ ] Implementar funciones auxiliares
  - [ ] `send_lucien_welcome`: Mensaje de bienvenida (5 min)
  - [ ] `approve_channel_request`: Aprobación (15 min)

### Día 19-20: Implementación de LucienHandlers
- [ ] Implementar handlers para desafíos
  - [ ] `handle_lucien_challenge`: Interacción con desafíos
  - [ ] Estados FSM para flujo de respuesta
- [ ] Implementar handlers para reacciones
  - [ ] `handle_lucien_reaction`: Reacciones a fragmentos

### Día 21-22: Implementación de DianaHandlers
- [ ] Implementar handlers para apariciones
  - [ ] `handle_diana_reaction`: Reacciones a apariciones
  - [ ] Transiciones Lucien-Diana
- [ ] Implementar momentos temporales
  - [ ] `handle_temporal_moment`: Momentos especiales

### Día 23: Implementación de UI y Teclados
- [ ] Crear teclados para interacciones
  - [ ] Teclados para desafíos de observación
  - [ ] Teclados para reacciones emocionales
  - [ ] Teclados para respuestas a Diana

## Fase 5: Pruebas y Refinamiento (3-4 días)

### Día 24-25: Pruebas Unitarias
- [ ] Implementar pruebas para cada servicio
  - [ ] `test_lucien_service.py`: Pruebas de personalidad y respuestas
  - [ ] `test_observation_challenge_service.py`: Pruebas de desafíos
  - [ ] `test_quantum_fragment_service.py`: Pruebas de efectos cuánticos
  - [ ] `test_temporal_moment_service.py`: Pruebas de momentos temporales
  - [ ] `test_diana_appearance_service.py`: Pruebas de apariciones

### Día 26-27: Pruebas de Integración
- [ ] Implementar pruebas de flujo completo
  - [ ] `test_lucien_diana_full_flow`: Flujo desde solicitud hasta VIP
  - [ ] `test_lucien_challenge_progression`: Progresión de desafíos
  - [ ] `test_diana_appearance_impact`: Impacto de apariciones
- [ ] Pruebas de rendimiento
  - [ ] Verificar impacto en rendimiento de base de datos
  - [ ] Optimizar consultas pesadas

### Día 28: Datos Iniciales y Despliegue
- [ ] Crear datos de semilla
  - [ ] Scripts para desafíos iniciales
  - [ ] Scripts para fragmentos cuánticos
  - [ ] Scripts para momentos temporales
- [ ] Preparar despliegue
  - [ ] Revisión final de dependencias
  - [ ] Plan de rollback en caso necesario

## Hitos de Verificación

### Hito 1: Prueba de Concepto (Día 8)
- [ ] Demo de interacción básica Lucien-Diana
- [ ] Flujo de saludo inicial implementado
- [ ] Desafío básico de observación funcionando

### Hito 2: MVP de Interacción (Día 16)
- [ ] Flujo completo de solicitud de canal
- [ ] Sistema de desafíos con evaluación
- [ ] Apariciones básicas de Diana tras reacciones

### Hito 3: Sistema Completo (Día 23)
- [ ] Todos los flujos implementados
- [ ] Fragmentos cuánticos funcionando
- [ ] Momentos temporales activados
- [ ] Transición a VIP integrada

### Hito 4: Producto Final (Día 28)
- [ ] Todas las pruebas pasando
- [ ] Rendimiento optimizado
- [ ] Documentación actualizada
- [ ] Datos iniciales cargados

## Monitoreo Post-Implementación

### Semana 1 Post-Lanzamiento
- [ ] Verificar métricas de retención D1-D7
- [ ] Monitorear frecuencia de apariciones de Diana
- [ ] Comprobar progresión de confianza con Lucien
- [ ] Verificar tasas de conversión a VIP

### Semana 2 Post-Lanzamiento
- [ ] Ajustes de balance en desafíos
- [ ] Refinamiento de mensajes de Lucien
- [ ] Optimización de frecuencia de apariciones
- [ ] Resolución de bugs reportados

## Notas de Implementación

1. **Priorización**: Implementar primero el flujo central de Lucien para obtener feedback temprano
2. **Iteración**: Añadir apariciones de Diana gradualmente, refinando con feedback de usuarios
3. **Testing**: Enfocarse en probar consistencia narrativa y progresión adecuada
4. **Monitoreo**: Prestar especial atención a la tasa de progresión para evitar avance demasiado rápido o lento

Esta checklist proporciona un marco detallado para la implementación del sistema "El Mayordomo del Diván", con fases claras, tareas específicas y puntos de verificación para asegurar una implementación exitosa y coherente.