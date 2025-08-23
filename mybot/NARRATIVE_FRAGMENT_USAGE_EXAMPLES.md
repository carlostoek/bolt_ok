# Ejemplos de Uso del Sistema de Fragmentos Narrativos Unificados

## 1. Crear un Fragmento de Historia

```
Usuario: /create_fragment
Bot: 📝 Creando un nuevo fragmento narrativo.

     Por favor, envíame el título del fragmento:

Usuario: El Misterio del Castillo
Bot: 📄 Ahora envíame el contenido del fragmento:

Usuario: En una noche oscura de invierno, un misterio ancestral aguardaba ser resuelto en las profundidades del castillo olvidado.

Bot: Tipo de fragmento:
     1. 📖 Historia
     2. ❓ Decisión
     3. ℹ️ Información

     Por favor, responde con el número correspondiente al tipo de fragmento:

Usuario: 1
Bot: 🎁 Ahora puedes agregar triggers (recompensas/efectos).
     Envíame los triggers en formato JSON, o escribe 'ninguno' si no hay triggers:

     Ejemplo:
     {"reward_points": 10, "unlock_lore": "codigo-pista"}

Usuario: {"reward_points": 15, "unlock_lore": "historia-castillo"}
Bot: 🗝️ Finalmente, puedes especificar las pistas requeridas.
     Envíame una lista de códigos de pistas separadas por comas, o escribe 'ninguna' si no hay requisitos:

     Ejemplo:
     pista-1,pista-2,pista-3

Usuario: ninguna
Bot: ✅ Fragmento narrativo creado exitosamente!

     🆔 ID: a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8
     📝 Título: El Misterio del Castillo
     🏷️ Tipo: STORY
```

## 2. Crear un Fragmento de Decisión

```
Usuario: /create_fragment
Bot: 📝 Creando un nuevo fragmento narrativo.

     Por favor, envíame el título del fragmento:

Usuario: El Cruce del Bosque
Bot: 📄 Ahora envíame el contenido del fragmento:

Usuario: Llegas a un cruce en el bosque. A tu izquierda, un sendero cubierto de niebla conduce hacia lo desconocido. A tu derecha, un camino mejor definido parece más seguro.

Bot: Tipo de fragmento:
     1. 📖 Historia
     2. ❓ Decisión
     3. ℹ️ Información

     Por favor, responde con el número correspondiente al tipo de fragmento:

Usuario: 2
Bot: 🔗 Para fragmentos de decisión, puedes agregar opciones.
     Envíame las opciones en formato JSON, o escribe 'ninguna' si no hay opciones:

     Ejemplo:
     [{"text": "Opción 1", "next_fragment_id": "uuid-aqui"}, {"text": "Opción 2", "next_fragment_id": "otro-uuid-aqui"}]

Usuario: [{"text": "Tomar el sendero de la izquierda", "next_fragment_id": "niebla-misteriosa"}, {"text": "Elegir el camino de la derecha", "next_fragment_id": "camino-seguro"}]
Bot: 🎁 Ahora puedes agregar triggers (recompensas/efectos).
     Envíame los triggers en formato JSON, o escribe 'ninguno' si no hay triggers:

     Ejemplo:
     {"reward_points": 10, "unlock_lore": "codigo-pista"}

Usuario: {"reward_points": 5}
Bot: 🗝️ Finalmente, puedes especificar las pistas requeridas.
     Envíame una lista de códigos de pistas separadas por comas, o escribe 'ninguna' si no hay requisitos:

     Ejemplo:
     pista-1,pista-2,pista-3

Usuario: pista-bosque
Bot: ✅ Fragmento narrativo creado exitosamente!

     🆔 ID: b2c3d4e5-f6g7-8901-h2i3-j4k5l6m7n8o9
     📝 Título: El Cruce del Bosque
     🏷️ Tipo: DECISION
```

## 3. Listar Fragmentos

```
Usuario: /list_fragments
Bot: 📖 Fragmentos Narrativos:

     🏷️ Historia:
       • El Misterio del Castillo (a1b2c3d4...)
     
     ❓ Decisión:
       • El Cruce del Bosque (b2c3d4e5...)
     
     ℹ️ Información:
       (No hay fragmentos informativos)
```

## 4. Obtener Detalles de un Fragmento

```
Usuario: /get_fragment
Bot: 🆔 Por favor, envíame el ID del fragmento que deseas obtener:

Usuario: a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8
Bot: 📄 Detalles del Fragmento:

     🆔 ID: a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8
     📝 Título: El Misterio del Castillo
     🏷️ Tipo: STORY
     📅 Creado: 2025-08-23 15:30:45.123456
     🔄 Actualizado: 2025-08-23 15:30:45.123456
     ✅ Activo: Sí

     📄 Contenido:
     En una noche oscura de invierno, un misterio ancestral aguardaba ser resuelto en las profundidades del castillo olvidado.

     🎁 Triggers: {
       "reward_points": 15,
       "unlock_lore": "historia-castillo"
     }

     🗝️ Pistas requeridas:
```