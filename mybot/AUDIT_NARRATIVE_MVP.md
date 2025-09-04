# Auditoría Narrativa para MVP

Este documento valida el alcance del MVP desde una perspectiva narrativa y establece las directrices obligatorias para la migración y creación de contenido dentro del Sistema Narrativo Unificado.

## 1. Validación Narrativa del Alcance del MVP

El alcance propuesto es **aprobado** con las siguientes consideraciones narrativas:

*   **Ciclo Emocional:** El ciclo "Interactuar -> Ganar Puntos -> Ver Saldo" es funcional. Debe enmarcarse como un ciclo emocional: "Atraer a Diana -> Ganar su Interés (Puntos) -> Ver un Reflejo de su Interés (Billetera)".
*   **La Billetera ("Wallet"):** No debe ser un simple balance. Su presentación debe tener un envoltorio narrativo. Por ejemplo, el texto podría ser: `Diana observa tu dedicación. Tu influencia sobre ella ha alcanzado [X] puntos.`
*   **Prioridad:** La migración del contenido narrativo existente al nuevo sistema es la prioridad absoluta. Un MVP sin una historia coherente y funcional es un fracaso, sin importar la calidad técnica.

## 2. Guía de Migración Narrativa

Para asegurar que no se pierda contexto emocional durante la migración técnica, se deben seguir estas reglas:

1.  **Mapeo de Intenciones:** Cada `StoryFragment` o `NarrativeFragment` antiguo debe ser analizado no solo por su texto, sino por su **intención emocional**. ¿Era un momento de vulnerabilidad? ¿Un desafío? Esta intención debe ser preservada.
2.  **Las Elecciones son Carácter:** Las antiguas `NarrativeChoice` deben ser convertidas al campo JSON `choices`. Es crucial que el texto de la elección refleje la personalidad de Diana. Evitar opciones directas; favorecer la ambigüedad y la seducción.
3.  **Las Recompensas son Inversión:** Los antiguos `reward_besitos` deben ser mapeados al campo `triggers`. La cantidad de puntos debe ser proporcional a la **inversión emocional** que el usuario ha hecho para llegar a ese punto, no a la dificultad.

## 3. Guía de Voz de Personaje para el Modelo Unificado

El modelo `NarrativeFragment` unificado debe ser utilizado siguiendo estos patrones para mantener la coherencia de los personajes. **Estos no son sugerencias, son reglas.**

### Patrón: Vulnerabilidad Calculada de Diana
Un momento en que Diana comparte algo aparentemente personal. Siempre debe ser una recompensa a la lealtad del usuario.

```json
// NarrativeFragment - ID: "diana_confession_1"
{
  "title": "Un destello en la oscuridad",
  "content": "A veces... incluso la luz de las estrellas se siente solitaria. Pero tu presencia... es una interrupción interesante.",
  "fragment_type": "STORY",
  "required_clues": ["USER_LOYALTY_LVL2"],
  "triggers": {
    "unlock_clue": "DIANA_TRUSTS_YOU_LVL1",
    "points": 50
  }
}
```

### Patrón: Desafío Intelectual de Diana
Diana no da respuestas, hace preguntas que fuerzan al usuario a pensar.

```json
// NarrativeFragment - ID: "diana_riddle_of_self"
{
  "title": "El espejo",
  "content": "Me preguntas qué es lo que quiero. Curioso... ¿alguna vez te has preguntado qué quieres tú realmente, o solo deseas lo que crees que deberías desear?",
  "fragment_type": "DECISION",
  "choices": [
    {"text": "Busco entenderte a ti.", "next_id": "diana_deflection_1"},
    {"text": "Busco entenderme a mí mismo.", "next_id": "diana_approval_1"}
  ]
}
```

### Patrón: Guía Práctica de Lucien
Lucien explica la mecánica del sistema, pero siempre la enmarca en el contexto de Diana.

```json
// NarrativeFragment - ID: "lucien_explains_wallet"
{
  "title": "El interés de Diana",
  "content": "He notado que la atención de Diana hacia ti ha aumentado. Si deseas ver una medida de tu influencia, puedes consultarlo en tu 'Billetera'. Es... un sistema que ella diseñó.",
  "fragment_type": "INFO"
}
```

## 4. User Stories Enriquecidas

Se añaden requisitos narrativos a las User Stories existentes.

### US-02: Progresar en la Narrativa Unificada
*   **Requisito Narrativo:** Las respuestas y elecciones de Diana deben seguir los patrones de voz definidos (misterio, vulnerabilidad calculada, etc.).
*   **Criterio de Aceptación Adicional:** El flujo de la conversación se siente natural y coherente con la personalidad de Diana.

### US-04: Consultar Saldo de Puntos
*   **Requisito Narrativo:** La presentación del saldo de puntos debe estar enmarcada en la narrativa del bot, como se describe en la sección 1.
*   **Criterio de Aceptación Adicional:** El texto que acompaña al saldo de puntos refuerza la idea de que los puntos representan el "interés" o "influencia" sobre Diana.
