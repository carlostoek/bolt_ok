# 📖 Formato de Fragmentos Narrativos - DianaBot

## Tabla de Contenidos
- [Estructura Básica](#estructura-básica)
- [Campos Disponibles](#campos-disponibles)
- [Ejemplos Completos](#ejemplos-completos)
- [Sistema de Arquetipos](#sistema-de-arquetipos)
- [Naming Convention](#naming-convention)
- [Cómo Cargar Fragmentos](#cómo-cargar-fragmentos)
- [Notas Importantes](#notas-importantes)

---

## Estructura Básica

```json
{
  "fragments": [
    {
      "fragment_id": "nombre_unico_del_fragmento",
      "content": "Texto del fragmento con markdown",
      "character": "Lucien" o "Diana",
      "level": 1-5,
      "required_besitos": 0,
      "reward_besitos": 5,
      "decisions": [
        {
          "text": "Texto de la opción",
          "next_fragment": "id_del_siguiente_fragmento"
        }
      ]
    }
  ]
}
```

---

## Campos Disponibles

### **Obligatorios:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `fragment_id` | string | Identificador único del fragmento |
| `content` | string | Texto que se mostrará (soporta Markdown) |
| `character` | string | "Lucien" o "Diana" |

### **Opcionales:**

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `level` | integer | 1 | Nivel narrativo 1-5 |
| `required_besitos` | integer | 0 | Besitos necesarios para ver este fragmento |
| `required_role` | string | null | "vip" si requiere ser VIP |
| `reward_besitos` | integer | 0 | Besitos que otorga al visitarlo |
| `image_url` | string | null | URL de imagen opcional |
| `unlocks_achievement_id` | string | null | ID de logro que desbloquea |
| `auto_next_fragment_key` | string | null | Fragmento siguiente automático (sin decisiones) |
| `archetype_variant` | string | null | Variante por arquetipo (ver tabla abajo) |
| `comment` | string | - | Comentarios para organización (se ignora al cargar) |

### **Decisiones (decisions):**

Array de objetos con:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `text` | string | Texto del botón de decisión |
| `next_fragment` | string | ID del fragmento destino |
| `required_besitos` | integer | Besitos necesarios para esta decisión (opcional) |
| `required_role` | string | "vip" si la decisión requiere VIP (opcional) |

---

## Ejemplos Completos

### 1. Fragmento Simple (sin decisiones, auto-avanza)

```json
{
  "fragment_id": "diana_final",
  "content": "🌸 **Diana:** Gracias por acompañarme en este viaje.\n\nHas llegado al final de esta historia... pero esto es solo el comienzo de algo más profundo.",
  "character": "Diana",
  "level": 5,
  "reward_besitos": 50,
  "auto_next_fragment_key": null
}
```

### 2. Fragmento con Decisiones

```json
{
  "fragment_id": "start",
  "content": "🎩 **Lucien:** Bienvenido. Esta casa no se abre para cualquiera. Si estás aquí, es porque ella te ha visto. Diana no elige al azar.",
  "character": "Lucien",
  "level": 1,
  "required_besitos": 0,
  "reward_besitos": 5,
  "decisions": [
    {
      "text": "¿Dónde está Diana?",
      "next_fragment": "diana_echo"
    },
    {
      "text": "¿Por qué fui elegido?",
      "next_fragment": "lucien_selection"
    },
    {
      "text": "Estoy listo para entrar",
      "next_fragment": "threshold_entry"
    }
  ]
}
```

### 3. Fragmento VIP con Requisitos

```json
{
  "fragment_id": "vip_chamber",
  "content": "🌸 **Diana:** *Te abre la puerta privada*\n\nAquí no hay narrativa, solo piel. Pero para quedarte, debes haber dejado algo atrás.",
  "character": "Diana",
  "level": 4,
  "required_besitos": 50,
  "required_role": "vip",
  "reward_besitos": 35,
  "decisions": [
    {
      "text": "Estoy listo",
      "next_fragment": "vip_ritual",
      "required_role": "vip"
    },
    {
      "text": "Aún no",
      "next_fragment": "diana_closure"
    }
  ]
}
```

### 4. Fragmento con Variante por Arquetipo

```json
{
  "fragment_id": "diana_direct_adventurer",
  "content": "🌸 **Diana:** *Te mira directamente a los ojos*\n\nSin juegos. Sin máscaras. Veo que no eres de los que pierden tiempo con rodeos. Me gusta.\n\nNo necesitas preguntas románticas ni metáforas. Quieres saber qué hay aquí, y yo te lo voy a mostrar... tal como es.",
  "character": "Diana",
  "level": 3,
  "required_besitos": 15,
  "reward_besitos": 20,
  "archetype_variant": "adventurer",
  "decisions": [
    {
      "text": "Muéstrame todo",
      "next_fragment": "vip_fast_track_adventurer"
    },
    {
      "text": "¿Qué esperas de mí?",
      "next_fragment": "diana_expectations_adventurer"
    }
  ]
}
```

### 5. Fragmento con Imagen y Logro

```json
{
  "fragment_id": "diana_revelation",
  "content": "🌸 **Diana:** *Comparte una foto íntima contigo*\n\nEsta soy yo. Sin filtros. Sin ediciones. Solo yo.",
  "character": "Diana",
  "level": 3,
  "required_besitos": 25,
  "reward_besitos": 15,
  "image_url": "https://example.com/diana_photo.jpg",
  "unlocks_achievement_id": "first_intimacy",
  "decisions": [
    {
      "text": "Eres hermosa",
      "next_fragment": "diana_grateful"
    },
    {
      "text": "Quiero ver más",
      "next_fragment": "diana_deeper",
      "required_besitos": 10
    }
  ]
}
```

---

## Sistema de Arquetipos

El bot clasifica automáticamente a los usuarios en arquetipos después de **3 decisiones narrativas**. Esto permite personalizar la experiencia narrativa según el estilo de cada usuario.

### 🎭 Arquetipos Disponibles

| Arquetipo | Emoji | Código | Características | Personalización |
|-----------|-------|--------|-----------------|-----------------|
| **Aventurero** | 🔥 | `adventurer` | Directo, rápido, transparente | Contenido sin rodeos, intenso |
| **Romántico** | 💭 | `romantic` | Analítico, lento, reservado | Narrativa emocional, pausada |
| **Explorador** | 🎭 | `explorer` | Curioso, variable, experimental | Múltiples caminos, opciones variadas |
| **Equilibrado** | ⚖️ | `balanced` | Mixto, moderado, selectivo | Balance entre todos (usa genéricos) |
| **Indeterminado** | ❓ | `undetermined` | Menos de 3 decisiones | Aún en clasificación |

### Clasificación Automática

El sistema analiza las decisiones del usuario y cuenta tags:

```python
# Ejemplo de clasificación:
Usuario hace 3 decisiones:
1. "Estoy listo para entrar" → tags: direct, fast
2. "Acepto ese reflejo" → tags: direct, transparent
3. "Te busco a ti" → tags: direct, transparent

Conteo final:
  direct: 3
  fast: 1
  transparent: 2

→ Resultado: "adventurer" 🔥
```

### Tags de Decisiones

Las decisiones se clasifican en 3 categorías:

**1. Approach (Aproximación):**
- `direct` - Va directo al grano
- `curious` - Hace preguntas, explora
- `analytical` - Analiza antes de actuar
- `cautious` - Procede con cuidado

**2. Speed (Velocidad):**
- `fast` - Avanza rápido
- `moderate` - Ritmo normal
- `slow` - Se toma su tiempo

**3. Depth (Profundidad emocional):**
- `transparent` - Abierto, vulnerable
- `reserved` - Reservado, privado
- `selective` - Selectivo en qué comparte

---

## Naming Convention

### Para Fragmentos con Variantes por Arquetipo

El sistema busca automáticamente variantes siguiendo este patrón:

```
Fragmento base:      diana_encounter
Aventurero:          diana_encounter_adventurer
Romántico:           diana_encounter_romantic
Explorador:          diana_encounter_explorer
Equilibrado:         diana_encounter (usa el base)
```

**Ejemplo de ramificación:**

```json
// Fragmento genérico (fallback)
{
  "fragment_id": "hall_of_mirrors",
  "content": "🌸 **Diana:** Ya estás aquí... ¿Me buscas a mí o huyes de ti?",
  "character": "Diana",
  "level": 3,
  "decisions": [...]
}

// Variante para Aventureros
{
  "fragment_id": "hall_of_mirrors_adventurer",
  "content": "🌸 **Diana:** *Directa* Sin juegos. Veo que vas directo al punto.",
  "character": "Diana",
  "level": 3,
  "archetype_variant": "adventurer",
  "decisions": [...]
}

// Variante para Románticos
{
  "fragment_id": "hall_of_mirrors_romantic",
  "content": "🌸 **Diana:** *Suave* Tómate tu tiempo... aprecio que no tengas prisa.",
  "character": "Diana",
  "level": 3,
  "archetype_variant": "romantic",
  "decisions": [...]
}
```

### Lógica de Selección

1. Sistema detecta arquetipo del usuario (ej: `adventurer`)
2. Busca fragmento: `hall_of_mirrors_adventurer`
3. Si existe → lo muestra
4. Si NO existe → muestra `hall_of_mirrors` (genérico)

**Logs generados:**
```
[ARCHETYPE] User 123456 classified as 'adventurer' after 5 decisions
[ARCHETYPE_ROUTING] User 123456 (adventurer) → variant fragment: hall_of_mirrors_adventurer
```

---

## Cómo Cargar Fragmentos

### 1. Cargar un archivo específico

```bash
cd /home/azureuser/repos/bolt_ok/mybot
python scripts/load_narrative_fragments.py narrative_fragments/mi_historia.json
```

### 2. Cargar fragmentos con variantes de arquetipos

```bash
python scripts/load_archetype_fragments.py
```

Esto carga automáticamente: `narrative_fragments/archetype_variants.json`

### 3. Cargar todos los fragmentos del directorio

```bash
# Cargar todos los .json en narrative_fragments/
python -c "
from services.narrative_loader import NarrativeLoader
from database.setup import init_db, get_session_factory
import asyncio

async def load_all():
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        loader = NarrativeLoader(session)
        await loader.load_fragments_from_directory('narrative_fragments')

asyncio.run(load_all())
"
```

### Verificar fragmentos cargados

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('./bot.db')
cursor = conn.cursor()
cursor.execute('SELECT key, character, level, archetype_variant FROM story_fragments')
for row in cursor.fetchall():
    print(f'{row[0]:30} | {row[1]:10} | Lvl {row[2]} | {row[3] or \"generic\"} ')
conn.close()
"
```

---

## Notas Importantes

### ✅ Permitido

- **Markdown soportado**: `**negrita**`, `*cursiva*`, emojis
- **Saltos de línea**: Usa `\n\n` para párrafos
- **Múltiples decisiones**: Hasta 5-6 opciones por fragmento
- **IDs descriptivos**: Usa nombres claros como `diana_first_kiss` en vez de `frag_012`

### ⚠️ Restricciones

- **IDs únicos**: Cada `fragment_id` debe ser único en toda la DB
- **Referencias válidas**: `next_fragment` debe apuntar a fragmentos existentes
- **Sin auto-next + decisions**: Usa uno u otro, no ambos
- **required_role**: Solo "vip" o null, no otros valores
- **Caracteres especiales**: Escapar `_`, `*`, `` ` ``, `[`, `]` si no quieres formateo

### 🔍 Debugging

Si un fragmento no se carga:

1. Verificar JSON válido: `python -m json.tool archivo.json`
2. Revisar logs: `[narrative_loader]` en consola
3. Verificar DB: `SELECT * FROM story_fragments WHERE key = 'nombre'`
4. Logs de arquetipo: Buscar `[ARCHETYPE_ROUTING]` en logs del bot

### 📊 Estadísticas del Sistema

Fragmentos actuales en el sistema:
- **Genéricos**: ~37 fragmentos (historia base)
- **Variantes Aventurero**: 5 fragmentos específicos
- **Variantes Romántico**: 7 fragmentos específicos
- **Variantes Explorador**: 7 fragmentos específicos
- **Total**: ~56 fragmentos únicos

---

## Ejemplos de Ramificación Completa

### Punto de Ramificación: Encuentro con Diana

```json
{
  "fragments": [
    {
      "comment": "Decisión que lleva a ramificación",
      "fragment_id": "lucien_final_question",
      "content": "🎩 **Lucien:** Diana está esperando. ¿Estás listo?",
      "character": "Lucien",
      "level": 2,
      "decisions": [
        {
          "text": "Sí, estoy listo",
          "next_fragment": "diana_encounter"
        }
      ]
    },
    {
      "comment": "Fragmento genérico (si usuario no tiene arquetipo o es balanced)",
      "fragment_id": "diana_encounter",
      "content": "🌸 **Diana:** Hola... finalmente nos conocemos.",
      "character": "Diana",
      "level": 3,
      "decisions": [
        {
          "text": "Hola Diana",
          "next_fragment": "diana_response"
        }
      ]
    },
    {
      "comment": "Variante para Aventureros 🔥",
      "fragment_id": "diana_encounter_adventurer",
      "content": "🌸 **Diana:** *Sin rodeos* Hola. Veo que no pierdes tiempo.",
      "character": "Diana",
      "level": 3,
      "archetype_variant": "adventurer",
      "decisions": [
        {
          "text": "No me gusta perder tiempo",
          "next_fragment": "diana_direct_path"
        }
      ]
    },
    {
      "comment": "Variante para Románticos 💭",
      "fragment_id": "diana_encounter_romantic",
      "content": "🌸 **Diana:** *Susurrando* Hola... tómate tu tiempo. No hay prisa.",
      "character": "Diana",
      "level": 3,
      "archetype_variant": "romantic",
      "decisions": [
        {
          "text": "Quiero conocerte bien",
          "next_fragment": "diana_slow_path"
        }
      ]
    },
    {
      "comment": "Variante para Exploradores 🎭",
      "fragment_id": "diana_encounter_explorer",
      "content": "🌸 **Diana:** *Curiosa* Hola explorador. ¿Qué camino elegirás?",
      "character": "Diana",
      "level": 3,
      "archetype_variant": "explorer",
      "decisions": [
        {
          "text": "Quiero explorar todos los caminos",
          "next_fragment": "diana_multi_path"
        },
        {
          "text": "Muéstrame el camino secreto",
          "next_fragment": "diana_hidden_path"
        }
      ]
    }
  ]
}
```

---

## Soporte y Contribuciones

- **Documentación adicional**: `/docs/`
- **Ejemplos**: `/narrative_fragments/`
- **Scripts de carga**: `/scripts/load_*_fragments.py`

Para agregar nuevos arquetipos o modificar la lógica de clasificación, ver:
- `utils/archetype_analyzer.py` - Sistema de clasificación
- `services/narrative_service.py` - Lógica de selección de fragmentos

---

**Última actualización**: 2025-10-04
**Versión del sistema**: 2.0 (con arquetipos)
