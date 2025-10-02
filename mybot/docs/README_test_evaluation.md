# Sistema de Test de Evaluación Emocional

## Descripción

Sistema completamente aislado para DianaBot que permite probar la evaluación emocional de usuarios basada en el timing de sus respuestas. Integrado seamlessly con el CoordinadorCentral y EmotionalAnalysisService existente.

## Características

- **Comando:** `/test_evaluacion`
- **UI:** Menú interactivo con 4 botones de prueba
- **Análisis:** Medición precisa del timing de respuesta
- **Integración:** Utiliza CoordinadorCentral y EmotionalAnalysisService
- **Feedback:** Clasificación automática del tipo de usuario

## Clasificaciones de Usuario

| Tiempo de Respuesta | Tipo | Descripción |
|---------------------|------|-------------|
| < 3 segundos | 🔥 Impulso Auténtico | Respuestas espontáneas desde el corazón |
| 3-15 segundos | 💭 Pausa Reflexiva | Decisiones conscientes y profundas |
| 15-60 segundos | 🌙 Contemplación | Análisis profundo antes de actuar |
| > 60 segundos | 🌊 Abandono | Tendencia a alejarse bajo presión |

## Archivos Implementados

### Nuevos Archivos
- `handlers/test_evaluation_handler.py` - Handler completamente aislado
- `keyboards/test_evaluation_kb.py` - Teclados para el test
- `demo_test_evaluation.py` - Demo del funcionamiento

### Archivos Modificados
- `services/coordinador_central.py` - Agregado enum y flujo del test
- `bot.py` - Registrado el nuevo handler

## Flujo de Usuario

1. **Inicio:** Usuario ejecuta `/test_evaluacion`
2. **Confirmación:** Sistema muestra explicación y botón de confirmación
3. **Test Activo:** Menú con opciones A, B, C, y "Ver mi perfil"
4. **Análisis:** Sistema mide timing y analiza patrones emocionales
5. **Resultados:** Diana proporciona perfil personalizado
6. **Opciones:** Usuario puede repetir test o finalizar

## Integración con Sistema Existente

### CoordinadorCentral
- Nuevo enum: `AccionUsuario.TEST_EVALUACION_EMOCIONAL`
- Nuevo flujo: `_flujo_test_evaluacion_emocional()`
- Integración con EmotionalAnalysisService y CharacterVoiceService

### Análisis Emocional Real
- `analyze_response_timing()` - Análisis de patrones temporales
- `assess_vulnerability_level()` - Evaluación de vulnerabilidad
- `detect_behavioral_patterns()` - Detección de comportamientos

### Respuestas Auténticas
- CharacterVoiceService genera respuestas de Diana
- Contexto emocional determinado por timing
- Mensajes personalizados según perfil detectado

## Características Técnicas

### Aislamiento Completo
- ✅ No modifica handlers existentes
- ✅ No modifica servicios existentes
- ✅ Solo adiciones a CoordinadorCentral
- ✅ Graceful degradation en caso de errores

### Gestión de Estado
- Cache temporal para sesiones de test
- Auto-cleanup de sesiones expiradas
- Manejo de errores robusto
- Logging detallado para monitoring

### Rendimiento
- Análisis en tiempo real del timing
- Cache de análisis emocional (5 min)
- Procesamiento asíncrono
- Cleanup automático de memoria

## Uso

```python
# El usuario ejecuta en Telegram:
/test_evaluacion

# Sistema responde con:
# 1. Mensaje de bienvenida y explicación
# 2. Botón "Comenzar Test"
# 3. Menú con opciones A, B, C, "Ver perfil"
# 4. Análisis automático del timing
# 5. Perfil personalizado con recomendaciones
```

## Ejemplo de Respuesta

```
🔥 IMPULSO AUTÉNTICO

Respondes desde el corazón, sin filtros. Tu naturaleza espontánea 
te lleva a conectar de manera genuina y directa. Eres de quienes 
viven el momento con intensidad.

💡 Tu patrón de respuesta indica alta energía emocional.

✨ Tu estabilidad emocional te permite explorar con confianza.
```

## Monitoreo

El sistema incluye logging detallado:
- Inicio/finalización de tests
- Timing de respuestas de usuarios
- Tipos de perfil detectados
- Errores de análisis emocional
- Limpieza de sesiones

## Seguridad

- Validación de entrada en callbacks
- Manejo seguro de excepciones
- Timeout automático de sesiones
- No persistencia de datos sensibles

---

**Estado:** ✅ Implementado y listo para uso
**Fecha:** 2025-09-12
**Versión:** 1.0.0