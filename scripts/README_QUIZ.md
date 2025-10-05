# 💘 Guía para Crear Quizzes de Compatibilidad

## 🚀 Inicio Rápido

### Crear el Quiz Inicial (Ya incluido)

Desde el directorio raíz del proyecto:

```bash
# Opción 1 - Usar el wrapper (más fácil)
./crear_quiz.sh

# Opción 2 - Directamente con Python
python scripts/create_initial_quiz.py
```

## 🎨 Crear un Quiz Personalizado

### Paso 1: Duplicar el Script

```bash
cp scripts/create_initial_quiz.py scripts/mi_nuevo_quiz.py
```

### Paso 2: Editar `QUIZ_DATA`

Abre `scripts/mi_nuevo_quiz.py` y modifica el diccionario `QUIZ_DATA`:

```python
QUIZ_DATA = {
    "title": "Título de tu quiz",
    "description": "Descripción que verán los usuarios",
    "besitos_reward": 100,  # Besitos que ganan al completarlo
    "questions": [
        {
            "number": 1,
            "category": "personality",  # o "interests", "values"
            "text": "¿Tu pregunta aquí?",
            "options": [
                {
                    "text": "Opción 1",
                    "score": 85,  # Puntuación de compatibilidad (0-100)
                    "response": "Respuesta personalizada de Diana"
                },
                {
                    "text": "Opción 2",
                    "score": 95,
                    "response": "Otra respuesta de Diana"
                },
                # ... más opciones (3-5 recomendado)
            ]
        },
        # ... más preguntas
    ]
}
```

### Paso 3: Ejecutar tu Quiz

```bash
python scripts/mi_nuevo_quiz.py
```

## 📊 Estructura de un Quiz

### Categorías Disponibles
- `personality` - Preguntas sobre personalidad
- `interests` - Preguntas sobre gustos e intereses
- `values` - Preguntas sobre valores y prioridades

### Puntuación de Compatibilidad
- `0-50`: Baja compatibilidad
- `51-70`: Compatibilidad moderada
- `71-85`: Buena compatibilidad
- `86-95`: Muy compatible
- `96-100`: Compatibilidad perfecta

### Niveles de Compatibilidad (calculados automáticamente)
- **90-100%**: "💘 Alma Gemela"
- **80-89%**: "💖 Conexión Especial"
- **70-79%**: "💕 Muy Compatible"
- **60-69%**: "💗 Buena Química"
- **50-59%**: "💓 Compatible"
- **0-49%**: "💝 Por Conocerse"

## 💡 Tips para Buenos Quizzes

### ✅ Hacer
- Preguntas que revelen personalidad genuina
- Opciones balanceadas (sin respuestas "obviamente correctas")
- Respuestas de Diana auténticas y personales
- 8-12 preguntas en total (ni muy corto ni muy largo)
- Mezclar categorías para análisis completo
- Dar puntuaciones honestas que reflejen compatibilidad real

### ❌ Evitar
- Preguntas con respuesta "correcta" obvia
- Muy pocas opciones (mínimo 3 por pregunta)
- Respuestas genéricas de Diana
- Quizzes muy largos (>15 preguntas)
- Puntuaciones todas altas o todas bajas

## 🎯 Ejemplo Completo de Pregunta

```python
{
    "number": 1,
    "category": "personality",
    "text": "¿Cómo manejas el estrés?",
    "options": [
        {
            "text": "Hablo con alguien de confianza",
            "score": 95,
            "response": "Me encanta que busques conexión en momentos difíciles."
        },
        {
            "text": "Hago ejercicio o actividades físicas",
            "score": 85,
            "response": "Cuidar tu cuerpo para cuidar tu mente. Muy sabio."
        },
        {
            "text": "Me tomo un tiempo a solas",
            "score": 90,
            "response": "La introspección es poderosa. Yo también lo hago."
        },
        {
            "text": "Lo ignoro hasta que desaparece",
            "score": 50,
            "response": "A veces enfrentar ayuda más que evitar. ¿Has probado?"
        }
    ]
}
```

## 🔧 Gestión de Quizzes

### Ver Quizzes Activos
Desde el panel admin en el bot:
`💎 Mi Diván → 💘 Gestionar Quizzes`

### Activar/Pausar Quiz
En el panel de gestión, usa los botones:
- `▶️ Activar` - Hacer visible el quiz
- `⏸️ Pausar` - Ocultar temporalmente

### Ver Estadísticas
`💎 Mi Diván → 📈 Estadísticas de Quizzes`

Muestra:
- Total de intentos
- Tasa de completado
- Puntuación promedio
- Distribución de niveles de compatibilidad
- Intentos de hoy

## 🚨 Notas Importantes

1. **Un Quiz Activo**: Solo puede haber un quiz activo a la vez. Si creas uno nuevo, pausa el anterior primero.

2. **No Borrar Quizzes**: Los quizzes con intentos completados no deben borrarse de la base de datos (afectaría las estadísticas de usuarios).

3. **Testing**: Después de crear un quiz, pruébalo como usuario VIP antes de activarlo para todos.

4. **Backups**: Haz backup de `bot.db` antes de crear quizzes en producción.

## 📚 Archivos Relacionados

- `scripts/create_initial_quiz.py` - Template del quiz inicial
- `database/midivan_models.py` - Modelos de base de datos
- `services/midivan_service.py` - Lógica del quiz
- `handlers/quiz_handler.py` - Interfaz de usuario del quiz
- `handlers/admin/midivan_admin.py` - Panel de gestión admin

## 🆘 Solución de Problemas

### Error: "No module named 'database'"
**Solución**: Ejecuta desde el directorio raíz del proyecto o usa `./crear_quiz.sh`

### Quiz no aparece para usuarios
**Solución**: Verifica que el quiz esté marcado como `is_active=True` en el panel admin

### Error al crear quiz
**Solución**: Revisa que:
- Todas las preguntas tengan `number` único
- Todas las opciones tengan `score` entre 0-100
- No haya caracteres especiales mal escapados en textos

## 💬 Soporte

Para dudas o problemas:
1. Revisa los logs del bot
2. Verifica el panel admin Mi Diván
3. Consulta este README
