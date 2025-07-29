# Sistema de Personalización de Diana

Este documento detalla el sistema de personalización implementado para transformar mensajes estándar como "Diana sonríe... +10 besitos" en respuestas personalizadas basadas en el nivel de intimidad, memoria emocional y contexto de interacción.

## Visión General

El sistema personaliza los mensajes de Diana considerando:

1. **Nivel de intimidad** de la relación con el usuario
2. **Estado emocional** actual basado en interacciones previas
3. **Adaptación de personalidad** específica para cada usuario
4. **Memoria de interacciones** pasadas para referencias contextuales
5. **Tipo de reacción** y contexto específico de la interacción

## Componentes Principales

### 1. Servicio Emocional de Diana (`DianaEmotionalService`)

El corazón del sistema que proporciona:

- Almacenamiento y recuperación de memorias emocionales
- Gestión del estado de la relación con cada usuario
- Adaptación de personalidad basada en interacciones
- Algoritmos de personalización de mensajes

### 2. Coordinador Central (`CoordinadorCentral`)

Orquesta la integración de todos los componentes:

- Conecta el flujo de reacciones con el servicio emocional
- Garantiza la inicialización de perfiles de usuario
- Maneja la recuperación de datos de relación y personalidad
- Aplica la personalización adecuada según el tipo de acción

### 3. Modelos de Datos Emocionales

Estructuras de datos que soportan el sistema:

- `DianaEmotionalMemory`: Almacena recuerdos de interacciones significativas
- `DianaRelationshipState`: Mantiene el estado actual de la relación
- `DianaPersonalityAdaptation`: Configura la adaptación de personalidad para cada usuario

## Niveles de Intimidad y Personalización

El sistema determina el nivel de intimidad (0.0-1.0) basado en:

- Estado de la relación (inicial, conocido, amistoso, cercano, íntimo)
- Nivel de confianza desarrollado
- Rapport y familiaridad
- Historial de interacciones positivas/negativas

### Ejemplo de Progresión de Mensajes

#### Usuario Nuevo (Intimidad Baja)
```
Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.
```

#### Usuario Conocido (Intimidad Media)
```
Diana guiña un ojo con picardía... *+10 besitos* 💋 han sido añadidos a tu cuenta.
```

#### Usuario Amistoso (Intimidad Media-Alta)
```
mi admirador, Diana sonríe con dulzura ✨... *+10 besitos* 💋 han sido añadidos a tu cuenta.
```

#### Usuario Cercano/Íntimo (Intimidad Alta)
```
mi amor, Diana te mira con intensidad recordando tu gesto anterior ✨💖... *+10 besitos* 💋 han sido añadidos a tu cuenta.
```

## Personalización Contextual

El sistema ajusta los mensajes según:

### 1. Tipo de Reacción
- **Positiva**: Sonrisas, aprobación, asentimiento
- **Romántica**: Sonrojos, miradas intensas, gestos íntimos
- **Humorística**: Risas, guiños, expresiones juguetonas
- **Sorpresa**: Arqueo de cejas, ojos abiertos, expresiones de asombro

### 2. Estado Emocional del Usuario
- Adaptación a emociones dominantes del usuario
- Respuestas empáticas cuando se detectan emociones negativas
- Amplificación de respuestas positivas cuando el usuario está feliz

### 3. Preferencias de Comunicación
- Ajuste del nivel de calidez
- Adaptación del uso de emojis
- Modulación del humor y formalidad
- Personalización de términos de cariño según nivel de relación

## Memoria Emocional

El sistema construye memoria contextual:

- Recuerda interacciones significativas
- Referencia momentos compartidos en mensajes
- Desarrolla un sentido de continuidad en la relación
- Evita contradicciones emocionales entre mensajes

## Implementación Técnica

Las funciones clave incluyen:

- `_enhance_reaction_message()`: Personaliza mensajes para reacciones
- `_calculate_intimacy_level()`: Determina el nivel de intimidad actual
- `_get_relationship_endearment()`: Selecciona términos de cariño apropiados
- `_get_personalized_action()`: Genera acciones personalizadas según contexto
- `_get_contextual_memory_reference()`: Incorpora referencias a memorias compartidas

## Ejemplo de Uso

Para usar el sistema, el flujo típico es:

1. El usuario realiza una acción (reacción, decisión narrativa, etc.)
2. El sistema genera un mensaje base con la información funcional
3. El `CoordinadorCentral` invoca `enhance_with_diana()` para personalizar
4. El sistema recupera el estado de la relación y adaptación del usuario
5. Se aplican algoritmos de personalización específicos según el tipo de acción
6. El mensaje personalizado se devuelve para mostrar al usuario

## Pruebas y Ejemplos

En el archivo `examples/personalization_examples.py` se proporcionan ejemplos de:

- Diferentes tipos de usuarios y niveles de relación
- Variedad de reacciones y respuestas personalizadas
- Simulación de progresión de relación a lo largo del tiempo

## Extensión Futura

El sistema puede ampliarse con:

- Más tipos de interacciones personalizables
- Algoritmos más sofisticados de análisis de emociones
- Aprendizaje automático de preferencias de comunicación
- Integración con sistemas de procesamiento de lenguaje natural