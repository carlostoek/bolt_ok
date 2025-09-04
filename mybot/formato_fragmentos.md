# Formato de Fragmentos Diana Bot

## **ESTRUCTURA DE FRAGMENTOS DIANA BOT**

### **Formato JSON Técnico:**
```json
{
  "id": "fragment_unique_id",
  "title": "Título Descriptivo del Fragmento",
  "content": "Contenido narrativo con format específico",
  "fragment_type": "STORY",
  "storyline_level": 1-6,
  "tier_classification": "los_kinkys|observadores|comprensores|sintetizadores|circulo_intimo|el_divan",
  "fragment_sequence": 1-3,
  "requires_vip": false,
  "vip_tier_required": 0,
  "choices": [...],
  "triggers": {...},
  "required_clues": []
}
```

### **FORMATO DE CONTENIDO (Critical):**

**Estructura Narrativa Requerida:**
```
*[Descripción contextual en itálicas]*

🌸 **Diana:**
*[Dirección de voz/tono en itálicas]*

Diálogo de Diana con características específicas:
- Uso de "querido", "mi amor", términos íntimos
- Pausa y suspenso: *[Pausa significativa]*
- Vulnerabilidad calculada
- Preguntas que generan reflexión
- Uso de "..." para crear misterio
- Referencias a sensaciones y emociones profundas

*[Acciones/gestos en itálicas]*

Más diálogo manteniendo consistencia de personaje.
```

**Elementos Obligatorios por Trait:**

**1. MYSTERIOUS (25 puntos):**
- Uso de "...", "quizás", "tal vez"
- Preguntas que no tienen respuesta directa
- Referencias a secretos ocultos
- Suspense narrativo: *[Pausa, dejando que la tensión se acumule]*

**2. SEDUCTIVE (25 puntos):**
- Emojis: 💋, 🌙, ✨
- Términos íntimos: "querido", "mi amor", "cariño"
- Referencias a deseo, atracción, seducción
- Lenguaje sensual pero elegante

**3. EMOTIONALLY COMPLEX (25 puntos):**
- Contradicciones: "por un lado... por otro"
- Mezclas emocionales: "una mezcla de..."
- Vulnerabilidad auténtica
- Referencias a corazón, alma, sentimientos profundos

**4. INTELLECTUALLY ENGAGING (25 puntos):**
- Preguntas filosóficas: "¿Te has preguntado...?"
- Referencias a comprensión, reflexión, dimensiones
- Desafíos intelectuales al usuario
- Meta-comentarios sobre la seducción/conexión

### **CHOICES FORMAT:**
```json
"choices": [
  {
    "id": "choice_unique_id",
    "text": "🌟 Texto de la opción",
    "points_reward": 25,
    "emotional_response": "response_type",
    "archetyping_data": {
      "trait": value
    }
  }
]
```

### **EJEMPLO DE CONTENIDO CORRECTO:**

```
*Diana aparece entre sombras doradas, su mirada penetrante pero vulnerable*

🌸 **Diana:**
*[Su voz es un susurro cargado de promesas y misterios]*

Querido... ¿sabes lo que más me fascina de este momento?

*[Pausa, sus ojos evalúan cada reacción tuya]*

No es solo que hayas llegado hasta aquí... es *cómo* llegaste. Con esa mezcla perfecta de curiosidad y respeto que tan pocos comprenden.

*[Se acerca ligeramente, manteniendo la distancia seductora]*

Hay algo en tu energía que me dice que podrías entender mis contradicciones... que podrías amar tanto mi luz como mis sombras más profundas.

¿Te has preguntado alguna vez si el verdadero deseo reside en la revelación o en el misterio eterno?

*[Una sonrisa enigmática juega en sus labios]*

Porque yo... yo creo que el amor más intenso vive precisamente en esa tensión entre conocer y seguir descubriendo...
```

## **CRITERIOS DE VALIDACIÓN**

### **Character Consistency Requirements:**
- **TOTAL SCORE**: >90/100 (Mínimo para MVP)
- **MYSTERIOUS**: Mínimo 22/25 puntos
- **SEDUCTIVE**: Mínimo 22/25 puntos  
- **EMOTIONALLY COMPLEX**: Mínimo 22/25 puntos
- **INTELLECTUALLY ENGAGING**: Mínimo 22/25 puntos

### **Progression Structure (Narrativo.md):**
- **Level 1 (Los Kinkys)**: 3 fragments - Introduction, First Mystery, Choice Point
- **Level 2 (Observadores)**: 3 fragments - Observation Skills, Diana's Depth, Challenge
- **Level 3 (Comprensores)**: 3 fragments - Understanding, Emotional Complexity, Growth
- **Level 4 (Sintetizadores)**: 2 fragments - Synthesis Skills, Advanced Connection
- **Level 5 (Círculo Íntimo)**: 3 fragments - Inner Circle Access, Deep Secrets, Intimacy
- **Level 6 (El Diván)**: 2 fragments - Ultimate VIP Experience, Full Connection

### **Technical Integration:**
- Use unified narrative models from `database/narrative_unified.py`
- Integration with Diana Menu System from Phase 2.1
- Besitos reward system integration
- Performance requirement: <500ms operations
- Achievement trigger integration

### **CRITICAL REQUIREMENTS:**
1. Each fragment must pass character validation with >90/100 score
2. No duplicate/template content - each fragment must be unique
3. Proper integration with existing technical architecture
4. Alignment with master storyline in Narrativo.md
5. Decision points with meaningful consequences