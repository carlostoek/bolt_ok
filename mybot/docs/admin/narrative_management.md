# Narrative Administration Guide

**Fecha:** 16 de Septiembre, 2025
**Proyecto:** Bot Diana - Sistema de Narrativa Interactiva
**Versión:** 2.0

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso al Panel Administrativo](#acceso-al-panel-administrativo)
3. [Gestión de Fragmentos Narrativos](#gestión-de-fragmentos-narrativos)
4. [Gestión de Piezas de Lore](#gestión-de-piezas-de-lore)
5. [Integración con la Tienda](#integración-con-la-tienda)
6. [Análisis y Métricas](#análisis-y-métricas)
7. [Validación y Consistencia Narrativa](#validación-y-consistencia-narrativa)
8. [Mejores Prácticas](#mejores-prácticas)
9. [Troubleshooting](#troubleshooting)
10. [Casos de Uso Avanzados](#casos-de-uso-avanzados)

---

## 📖 Introducción

El sistema de administración narrativa de DianaBot proporciona una interfaz completa para crear, gestionar y analizar contenido narrativo interactivo. Este sistema permite a los administradores mantener la calidad narrativa, expandir el contenido de manera coherente, y optimizar la experiencia del usuario basándose en métricas detalladas.

### Características Principales

- **Gestión integral de fragmentos**: Creación, edición y organización de contenido narrativo
- **Sistema de lore avanzado**: Gestión de contenido desbloqueable vinculado a items de la tienda
- **Validación automática**: Verificación de consistencia narrativa y flujo de historia
- **Análisis detallado**: Métricas de engagement, patrones de elección y rutas de usuario
- **Integración con tienda**: Vinculación directa con el sistema de items y compras
- **Personalización por arquetipo**: Adaptación de contenido según perfil de usuario

---

## 🔐 Acceso al Panel Administrativo

### Requisitos de Acceso

Para acceder al panel administrativo de narrativa necesitas:

1. **Permisos de Administrador**: Tu cuenta debe tener rol de administrador
2. **Acceso al Bot**: Conexión activa con el bot DianaBot
3. **Sesión Válida**: Autenticación reciente en el sistema

### Navegación Inicial

```
/admin → Panel Principal → 📖 Gestión Narrativa
```

**Comandos de acceso:**
- `/admin` - Panel principal de administración
- Botón "📖 Gestión Narrativa" - Acceso directo al módulo narrativo

### Estructura del Panel Narrativo

```
📖 Panel de Gestión Narrativa
├── 📝 Fragmentos de Historia
├── 📚 Gestión de Lore
├── 🔗 Integración con Tienda
├── 📊 Análisis y Métricas
├── ✅ Validación Narrativa
└── ⚙️ Configuración Avanzada
```

---

## 📝 Gestión de Fragmentos Narrativos

### Creación de Fragmentos

#### Formulario de Creación

**Campos obligatorios:**
- **Key del Fragmento**: Identificador único (ej: `diana_level2_intro`)
- **Contenido**: Texto narrativo con formato Markdown
- **Personaje**: Diana, Lucien, Sistema
- **Nivel Narrativo**: 1-5 (nivel de intimidad/complejidad)

**Campos opcionales:**
- **Tipo de Contenido**: text, choice, teaser, exclusive
- **Tono Emocional**: friendly, intimate, mysterious, vulnerable
- **Besitos Requeridos**: Costo para acceder al fragmento
- **Besitos de Recompensa**: Puntos otorgados por completar
- **Metadata Analytics**: JSON con datos para seguimiento

#### Ejemplo de Fragmento

```markdown
**Key:** diana_diary_intro
**Contenido:**
🌸 **Diana:** *Sus ojos brillan con una mezcla de nerviosismo y confianza*

Hay algo especial que quiero compartir contigo... algo que pocos han visto.

*Saca cuidadosamente un pequeño diario de tapas rosadas*

Este es mi diario personal. Aquí escribo mis pensamientos más íntimos, mis sueños... y últimamente, mis sentimientos sobre ti.

**Personaje:** Diana
**Nivel:** 2
**Tono Emocional:** intimate
**Besitos Requeridos:** 0
**Besitos de Recompensa:** 15
```

### Edición de Fragmentos Existentes

#### Proceso de Edición Segura

1. **Seleccionar Fragmento**: Buscar por key o navegar por niveles
2. **Verificar Dependencias**: El sistema mostrará qué fragmentos enlazan a este
3. **Modo de Edición**: Editar contenido manteniendo integridad narrativa
4. **Preview**: Vista previa del fragmento renderizado
5. **Validación**: Verificación automática de consistencia
6. **Guardar**: Confirmación con log de cambios

#### Alertas de Integridad

El sistema alertará sobre:
- **Fragmentos Huérfanos**: Sin enlaces entrantes
- **Enlaces Rotos**: Referencias a fragmentos inexistentes
- **Cambios Críticos**: Modificaciones que afectan rutas principales
- **Inconsistencias de Nivel**: Saltos abruptos en intimidad narrativa

### Organización Jerárquica

#### Estructura de Niveles

```
Nivel 1: Introducción y Establecimiento
├── diana_intro_salon
├── diana_first_conversation
└── diana_basic_interaction

Nivel 2: Desarrollo de Confianza
├── diana_personal_share
├── diana_diary_tease
└── diana_friendship_deepen

Nivel 3: Intimidad Emocional
├── diana_diary_intimate
├── diana_vulnerable_moment
└── diana_deep_connection

Nivel 4: Máxima Intimidad
├── diana_ultimate_trust
├── diana_secret_revelation
└── diana_complete_openness

Nivel 5: Contenido Exclusivo Premium
├── diana_premium_experience
├── diana_special_event
└── diana_collector_content
```

#### Convenciones de Naming

```python
# Formato estándar para keys
"{personaje}_{categoria}_{descriptor}"

# Ejemplos:
"diana_diary_intro"        # Diana, categoría diario, introducción
"lucien_mystery_reveal"    # Lucien, categoría misterio, revelación
"diana_level3_intimate"    # Diana, nivel específico, tipo de contenido
"teaser_diary_access"      # Teaser para acceso restringido
```

### Gestión de Decisiones

#### Creación de Opciones de Elección

**Estructura de una decisión:**
```json
{
  "text": "💭 Preguntarle sobre su diario íntimo",
  "next_fragment": "diana_diary_intimate",
  "required_item": "📓 Diario Íntimo",
  "conditions": {
    "user_level": 2,
    "relationship_points": 50,
    "previous_choices": ["diana_trust_building"]
  },
  "archetype_adaptations": {
    "Explorer": "🔍 Investigar el contenido de su diario",
    "Direct": "📝 Pedirle que lea su diario",
    "Poet": "✨ Invitarla a compartir sus pensamientos",
    "Analytic": "📊 Preguntarle sobre el propósito del diario",
    "Patient": "⏳ Esperar a que ella decida compartir"
  }
}
```

#### Lógica Condicional Avanzada

**Tipos de condiciones:**
- **Item Ownership**: Verificación de items específicos en inventario
- **User Stats**: Nivel, besitos, relationship points
- **Previous Choices**: Historial de decisiones tomadas
- **Time-Based**: Condiciones temporales y de frecuencia
- **Archetype-Based**: Adaptación según personalidad del usuario

---

## 📚 Gestión de Piezas de Lore

### Creación de Lore Pieces

#### Tipos de Contenido Soportados

1. **Texto Enriquecido**: Markdown con imágenes y formato
2. **Contenido Multimedia**: Soporte para imágenes y videos
3. **Contenido Interactivo**: Mini-juegos y experiencias especiales
4. **Colecciones**: Grupos de lore pieces relacionados

#### Formulario de Creación de Lore

**Campos principales:**
```
Título: "Diario Íntimo de Diana - Entrada 1"
Code Name: "diana_diary_entry_1"
Categoría: "Personal Diary"
Tags: ["diana", "intimate", "diary", "level3"]
Descripción: "Primera entrada íntima del diario personal de Diana"
```

**Contenido:**
```markdown
# 📓 Entrada del Diario - Día 127

*Letra elegante en tinta rosa*

Querido diario,

Hoy he sentido algo diferente... hay alguien especial que ha comenzado a ocupar mis pensamientos de manera más frecuente.

*[CONTENIDO ÍNTIMO ADICIONAL AQUÍ]*

Su forma de hablar conmigo, de escucharme realmente... es como si pudiera ver a través de todas mis máscaras sociales y llegar al verdadero yo que guardo dentro.

¿Será posible que alguien me pueda amar tal como soy realmente?

*~ Diana ♥*
```

**Metadata avanzada:**
```json
{
  "unlock_conditions": {
    "required_items": ["📓 Diario Íntimo"],
    "min_relationship_level": 3,
    "required_previous_lore": ["diana_diary_entry_0"]
  },
  "analytics_tracking": {
    "track_reading_time": true,
    "track_return_visits": true,
    "emotional_response_tracking": true
  },
  "personalization": {
    "archetype_variations": {
      "Explorer": "Incluye pistas adicionales sobre secretos",
      "Poet": "Lenguaje más metafórico y emotivo",
      "Analytic": "Detalles sobre la psicología de Diana"
    }
  }
}
```

### Organización y Categorización

#### Sistema de Categorías

```
📚 Lore Categories
├── 💝 Personal Diaries
│   ├── Diana's Intimate Journal
│   ├── Lucien's Mystery Notes
│   └── Shared Memory Collection
├── 🏛️ World Building
│   ├── Academy History
│   ├── Character Backgrounds
│   └── Cultural Context
├── 🎭 Character Development
│   ├── Personality Evolution
│   ├── Relationship Milestones
│   └── Growth Moments
└── 🎁 Exclusive Content
    ├── Premium Experiences
    ├── Collector's Items
    └── Limited Time Content
```

#### Sistema de Tags

**Tags de Personaje:**
- `diana`, `lucien`, `academy_characters`

**Tags de Contenido:**
- `intimate`, `mystery`, `romance`, `friendship`, `humor`

**Tags de Nivel:**
- `level1`, `level2`, `level3`, `level4`, `level5`

**Tags de Tipo:**
- `diary`, `letter`, `memory`, `secret`, `revelation`

**Tags de Acceso:**
- `premium`, `vip_only`, `time_limited`, `achievement_based`

### Gestión de Relaciones entre Lore

#### Enlaces de Contenido

**Tipos de relaciones:**
- **Secuencial**: Contenido que debe leerse en orden
- **Temática**: Contenido relacionado por tema
- **Personaje**: Contenido del mismo personaje
- **Alternativa**: Contenido que varía según decisiones

**Configuración de enlaces:**
```json
{
  "lore_piece_id": "diana_diary_entry_1",
  "relationships": {
    "prerequisite": ["diana_diary_entry_0"],
    "next_in_sequence": ["diana_diary_entry_2"],
    "related_content": ["diana_vulnerable_moment", "diana_trust_confession"],
    "alternative_versions": {
      "explorer_variant": "diana_diary_entry_1_explorer",
      "poet_variant": "diana_diary_entry_1_poet"
    }
  }
}
```

---

## 🔗 Integración con la Tienda

### Vinculación de Items con Contenido

#### Proceso de Vinculación

1. **Seleccionar Lore Piece**: Elegir contenido a vincular
2. **Crear/Seleccionar Shop Item**: Definir item desbloqueador
3. **Configurar Condiciones**: Establecer lógica de unlock
4. **Configurar Teaser**: Mensaje para usuarios sin acceso
5. **Validar Integración**: Probar flujo completo

#### Configuración de Shop Items

**Ejemplo de item vinculado:**
```json
{
  "shop_item": {
    "name": "📓 Diario Íntimo",
    "description": "Desbloquea el acceso completo al diario personal de Diana",
    "price": 30,
    "is_vip_only": false,
    "category": "narrative_unlock",
    "unlocks_lore_piece_id": "diana_diary_complete_collection"
  },
  "unlock_configuration": {
    "immediate_access": true,
    "unlock_all_related": true,
    "grant_special_choices": true,
    "unlock_conditions": {
      "and": [
        {"item_owned": "📓 Diario Íntimo"},
        {"relationship_level": ">=", "value": 2}
      ]
    }
  }
}
```

### Gestión de Contenido Restringido

#### Tipos de Restricciones

1. **Item-Based**: Requiere items específicos
2. **Level-Based**: Requiere nivel mínimo de relación
3. **Achievement-Based**: Requiere logros específicos
4. **Time-Based**: Disponible en horarios específicos
5. **Combination-Based**: Múltiples condiciones simultáneas

#### Configuración de Teasers

**Teaser para contenido restringido:**
```markdown
🌸 **Diana:** *Sus mejillas se tiñen de un suave rosa*

Eso es... muy personal para mí. Mi diario contiene mis pensamientos más íntimos, mis secretos más profundos...

*Mira hacia abajo, jugando nerviosamente con las páginas*

Tal vez... si me demuestras que realmente te importo comprando algo especial que represente tu interés en conocer mi mundo interior... podría considerarlo.

*Te mira con una sonrisa tímida*

**Opciones:**
🛒 Ir a la tienda
🔄 Volver al salón
```

#### Lógica de Promoción de Items

**Estrategias de promoción:**
- **Contextual**: Mencionar items relevantes en el momento narrativo apropiado
- **Progresiva**: Introducir items más valiosos a medida que avanza la relación
- **Temática**: Agrupar items relacionados con eventos narrativos específicos
- **Exclusiva**: Items de tiempo limitado vinculados a eventos especiales

### Analytics de Conversión

#### Métricas de Shop Integration

**Tracking de conversión:**
- **Teaser Views**: Cuántas veces se muestra contenido restringido
- **Shop Clicks**: Clicks desde teasers hacia la tienda
- **Purchase Conversion**: Porcentaje de usuarios que compran después del teaser
- **Content Engagement**: Engagement con contenido desbloqueado
- **Return Purchase Rate**: Usuarios que compran múltiples items narrativos

---

## 📊 Análisis y Métricas

### Dashboard de Analytics

#### Vista General del Sistema

**Métricas principales:**
```
📈 Resumen Narrativo (Últimos 30 días)
├── Total Fragmentos Activos: 127
├── Usuarios Únicos: 1,847
├── Sesiones Narrativas: 5,621
├── Tasa de Completación: 78.5%
├── Tiempo Promedio por Sesión: 8.3 min
└── Fragmentos Más Populares: diana_diary_intro (67% engagement)
```

#### Métricas por Fragmento

**Información detallada por fragmento:**
- **View Count**: Número total de visualizaciones
- **Completion Rate**: Porcentaje de usuarios que completan el fragmento
- **Choice Distribution**: Distribución de decisiones tomadas
- **Average Time Spent**: Tiempo promedio de lectura
- **Return Rate**: Usuarios que regresan al fragmento
- **Next Fragment Success**: Éxito en la transición al siguiente fragmento

### Análisis de Patrones de Usuario

#### Segmentación de Usuarios

**Por Arquetipo:**
```
🔍 Explorer (23%): Prefieren fragmentos de descubrimiento y misterio
📝 Direct (19%): Elecciones directas y progresión rápida
✨ Poet (18%): Contenido emotivo y descriptivo
📊 Analytic (21%): Información detallada y opciones lógicas
⏳ Patient (19%): Progresión gradual y desarrollo de relaciones
```

**Por Nivel de Engagement:**
- **Highly Engaged (15%)**: >20 sesiones, compras múltiples
- **Moderately Engaged (45%)**: 5-20 sesiones, algunas compras
- **Casually Engaged (35%)**: 1-5 sesiones, compras ocasionales
- **Low Engagement (5%)**: <1 sesión completa, sin compras

#### Journey Mapping

**Rutas comunes de usuario:**
```
Ruta Estándar (67% usuarios):
intro_salon → diana_first_talk → friendship_building →
diary_tease → shop_visit → diary_purchase → intimate_content

Ruta Explorador (15% usuarios):
intro_salon → mystery_investigation → lucien_encounter →
advanced_mystery → premium_content

Ruta Premium (12% usuarios):
intro_salon → fast_progression → multiple_purchases →
exclusive_content → collector_items

Ruta Abandonada (6% usuarios):
intro_salon → basic_interaction → [abandono en decisión compleja]
```

### Reports y Exportación

#### Tipos de Reports Disponibles

1. **Engagement Report**: Métricas de interacción y tiempo
2. **Conversion Report**: Análisis de shop integration y compras
3. **Content Performance**: Efectividad de fragmentos individuales
4. **User Journey Report**: Patrones de navegación y progresión
5. **A/B Testing Report**: Comparación de versiones de contenido
6. **Cohort Analysis**: Comportamiento de usuarios por cohortes

#### Formatos de Exportación

- **PDF**: Reports completos con gráficos
- **Excel**: Datos tabulares para análisis adicional
- **JSON**: Datos estructurados para integración
- **CSV**: Datos simples para análisis externo

**Ejemplo de configuración de export:**
```json
{
  "report_type": "engagement_report",
  "date_range": {
    "start": "2025-08-01",
    "end": "2025-09-15"
  },
  "filters": {
    "fragments": ["diana_diary_*", "lucien_mystery_*"],
    "user_segments": ["highly_engaged", "moderately_engaged"],
    "include_shop_data": true
  },
  "format": "pdf",
  "include_graphs": true,
  "email_recipients": ["admin@dianabot.com"]
}
```

---

## ✅ Validación y Consistencia Narrativa

### Sistema de Validación Automática

#### Tipos de Validación

1. **Validación Estructural**: Verificación de formato y campos requeridos
2. **Validación de Enlaces**: Verificación de referencias entre fragmentos
3. **Validación de Flujo**: Verificación de rutas narrativas completas
4. **Validación de Consistencia**: Verificación de coherencia de personajes
5. **Validación de Performance**: Verificación de tiempos de carga

#### Reglas de Validación

**Validaciones críticas (bloquean guardado):**
- Referencias a fragmentos inexistentes
- Fragmentos sin salida (dead ends no intencionales)
- Inconsistencias graves de nivel narrativo
- Campos obligatorios faltantes
- Formato JSON inválido en metadata

**Validaciones de advertencia (permiten guardado con alerta):**
- Fragmentos huérfanos (sin enlaces entrantes)
- Saltos de nivel narrativo abruptos
- Inconsistencias menores de personaje
- Contenido potencialmente repetitivo
- Falta de diversidad en opciones de elección

### Herramientas de Visualización

#### Narrative Graph Visualization

El sistema proporciona una visualización interactiva del grafo narrativo:

```
[diana_intro] → [diana_first_talk] → [diana_friendship]
     ↓                ↓                    ↓
[teaser_diary] → [shop_redirect] → [diary_purchase] → [intimate_content]
     ↓                                        ↓
[alternative_path] ← ← ← ← ← ← ← ← ← ← ← [premium_route]
```

**Características de la visualización:**
- **Nodos coloreados por nivel**: Azul (Nivel 1), Verde (Nivel 2), Amarillo (Nivel 3), Naranja (Nivel 4), Rojo (Nivel 5)
- **Conexiones por tipo**: Líneas sólidas (flujo normal), líneas punteadas (condicionado por item)
- **Indicadores de estado**: Verde (validado), Amarillo (advertencias), Rojo (errores)
- **Filtros interactivos**: Por personaje, nivel, tipo de contenido

#### Herramientas de Debugging

**Fragment Inspector:**
- Vista detallada de cualquier fragmento
- Lista de fragmentos que enlazan a este
- Lista de fragmentos a los que enlaza
- Historial de cambios y versiones
- Estadísticas de uso y engagement

**Consistency Checker:**
- Verificación de voz de personaje
- Verificación de progresión emocional
- Verificación de references temporales
- Verificación de continuidad narrativa

---

## 🎯 Mejores Prácticas

### Creación de Contenido

#### Guías de Voz de Personaje

**Diana - Personalidad Base:**
- Dulce pero con profundidad emocional
- Vulnerable en momentos íntimos
- Juguetona y coqueta en interacciones casuales
- Madura y reflexiva en momentos serios
- Usa emojis florales y de corazón: 🌸 💝 ✨

**Ejemplo de voz consistente:**
```markdown
🌸 **Diana:** *Sus ojos brillan con una mezcla de nerviosismo y emoción*

Sabes... hay algo mágico en estos momentos que compartimos.

*Se acerca un poco más, su voz se vuelve más suave*

Cada vez que eliges quedarte conmigo, cada vez que decides conocerme un poco más profundamente... mi corazón se llena de una calidez que nunca había sentido antes.

*Sonríe con ternura*

Gracias por ser tan paciente conmigo, por permitirme abrirme a mi propio ritmo. ¿Sabes cuánto significa eso para mí?
```

**Lucien - Personalidad Base:**
- Misterioso pero accesible
- Intelectual y observador
- Cálido bajo su exterior reservado
- Protector de quienes ama
- Uso elegante del lenguaje, emojis sutiles: 🌙 📚 ⚡

#### Progresión Emocional

**Escalada de Intimidad:**
```
Nivel 1: Presentación y cortesía social
Nivel 2: Amistad genuina y confianza básica
Nivel 3: Intimidad emocional y vulnerabilidad
Nivel 4: Conexión profunda y secretos personales
Nivel 5: Máxima intimidad y contenido exclusivo
```

**Transiciones suaves entre niveles:**
- Evitar saltos abruptos en intimidad
- Proporcionar razones narrativas para la progresión
- Respetar el ritmo natural de desarrollo de relaciones
- Incluir opciones para usuarios que prefieren progresión más lenta

### Gestión de Contenido Restringido

#### Estrategias de Monetización Ética

**Principios fundamentales:**
1. **Valor Real**: Cada item debe desbloquear contenido genuinamente valioso
2. **Transparencia**: Los usuarios deben saber exactamente qué obtienen
3. **Alternativas**: Proporcionar rutas narrativas para todos los niveles de inversión
4. **Respeto**: No explotar vulnerabilidades emocionales para forzar compras

**Ejemplo de implementación ética:**
```markdown
🌸 **Diana:** *Mira su diario con cariño*

Este diario contiene mis pensamientos más profundos sobre nosotros, sobre cómo me haces sentir, sobre los sueños que tengo cuando pienso en nuestro futuro...

*Pausa, considerando*

Es algo muy personal para mí. Si decides que quieres acompañarme en este nivel de intimidad, hay una manera especial de demostrar ese compromiso...

**Pero por favor, no sientas que tienes que hacerlo. Nuestra amistad es preciosa para mí exactamente como es.**

*Sonríe con sinceridad*

Opciones:
💝 Me interesa conocer esa manera especial
🌸 Nuestra amistad actual es perfecta
🔄 Hablemos de otra cosa
```

### Optimización de Performance

#### Mejores Prácticas Técnicas

**Estructura de fragmentos:**
- Mantener fragmentos entre 100-500 palabras para óptima legibilidad
- Usar imágenes optimizadas (máximo 500KB por imagen)
- Evitar anidación excesiva en decision trees
- Implementar lazy loading para contenido multimedia

**Gestión de base de datos:**
- Indexar campos frecuentemente consultados
- Usar paginación en listas largas de fragmentos
- Implementar caching para fragmentos populares
- Hacer cleanup regular de analytics data antiguo

---

## 🔧 Troubleshooting

### Problemas Comunes

#### Error: "Fragmento no encontrado"

**Causas comunes:**
- Key de fragmento incorrecta o cambiada
- Fragmento eliminado sin actualizar referencias
- Error de tipeo en navigation logic

**Solución:**
1. Verificar que el fragmento existe en la base de datos
2. Revisar todas las referencias al fragmento en el sistema
3. Usar la herramienta de "Fragment Inspector" para diagnóstico
4. Actualizar o crear el fragmento faltante

#### Error: "Validación de consistencia fallida"

**Causas comunes:**
- Cambios en voz de personaje inconsistentes
- Progresión de nivel narrativo inválida
- Referencias circulares en decision trees

**Solución:**
1. Usar el Consistency Checker para identificar problemas específicos
2. Revisar cambios recientes en fragmentos relacionados
3. Verificar que la progresión emocional sea lógica
4. Corregir inconsistencias identificadas

#### Problema: Baja tasa de conversión en shop

**Causas comunes:**
- Teasers no suficientemente atractivos
- Precio demasiado alto para el valor percibido
- Timing incorrecto en la presentación del item
- Falta de contexto emocional adecuado

**Solución:**
1. Revisar analytics de la ruta de conversión
2. A/B testing con diferentes versiones de teaser
3. Ajustar pricing basado en engagement metrics
4. Mejorar el contexto narrativo previo a la presentación del item

### Herramientas de Diagnóstico

#### Content Health Check

Utilidad para verificar la salud general del contenido:

```
🔍 Content Health Report
├── ✅ Fragmentos Válidos: 124/127 (97.6%)
├── ⚠️ Advertencias: 8 fragmentos con enlaces débiles
├── ❌ Errores Críticos: 3 referencias rotas
├── 📊 Performance: Tiempo promedio de carga 1.2s
└── 🔗 Integración Shop: 23/25 items correctamente vinculados
```

#### Analytics Troubleshooting

**Problemas de tracking:**
- Verificar que los event triggers estén configurados
- Confirmar que la metadata de analytics esté presente
- Validar que las métricas se estén registrando correctamente
- Revisar logs de errores en el sistema de analytics

---

## 🚀 Casos de Uso Avanzados

### Campañas de Contenido Especial

#### Eventos Temáticos

**Ejemplo: "Semana de San Valentín"**

**Configuración:**
```json
{
  "event_name": "valentine_week_2025",
  "duration": {
    "start": "2025-02-10",
    "end": "2025-02-17"
  },
  "special_content": {
    "fragments": [
      "diana_valentine_confession",
      "lucien_valentine_mystery",
      "valentine_exclusive_diary"
    ],
    "items": [
      {
        "name": "💝 Carta de Amor Especial",
        "price": 25,
        "temporary": true,
        "unlocks": "valentine_exclusive_content"
      }
    ]
  },
  "modifications": {
    "existing_fragments": {
      "diana_daily_greeting": "valentine_greeting_variant",
      "main_salon": "valentine_decorated_salon"
    }
  }
}
```

#### Contenido Dinámico

**Personalización por historial:**
- Adaptar diálogos según choices previas del usuario
- Referencias a eventos pasados en nuevas conversaciones
- Progresión de relationship que se refleja en nuevos fragmentos
- Contenido que evoluciona basado en items poseídos

### A/B Testing de Contenido

#### Configuración de Tests

**Ejemplo de test de conversión:**
```json
{
  "test_name": "diary_teaser_optimization",
  "variants": {
    "control": {
      "fragment_key": "diana_diary_tease_original",
      "description": "Teaser original directo"
    },
    "emotional": {
      "fragment_key": "diana_diary_tease_emotional",
      "description": "Teaser con más carga emocional"
    },
    "playful": {
      "fragment_key": "diana_diary_tease_playful",
      "description": "Teaser más juguetón y coqueto"
    }
  },
  "traffic_split": {
    "control": 34,
    "emotional": 33,
    "playful": 33
  },
  "success_metrics": [
    "shop_click_rate",
    "purchase_conversion",
    "user_satisfaction"
  ],
  "duration_days": 14
}
```

### Integración con Sistemas Externos

#### API de Contenido

**Endpoints para integración:**
```
GET /api/narrative/fragment/{key}
POST /api/narrative/fragment
PUT /api/narrative/fragment/{key}
DELETE /api/narrative/fragment/{key}

GET /api/lore/piece/{id}
POST /api/lore/piece
PUT /api/lore/piece/{id}

GET /api/analytics/engagement/{timeframe}
GET /api/analytics/conversion/{item_id}
```

#### Webhook Integration

**Notificaciones automáticas:**
- Nuevos fragmentos creados
- Cambios críticos en contenido
- Alertas de consistencia narrativa
- Métricas de performance que cruzan umbrales

---

## 📝 Conclusión

El sistema de administración narrativa de DianaBot proporciona una plataforma completa para crear, gestionar y optimizar experiencias narrativas interactivas. Con herramientas para validación automática, análisis detallado, y integración perfecta con el sistema de tienda, los administradores pueden mantener la calidad narrativa mientras escalan el contenido de manera efectiva.

### Recursos Adicionales

- **Documentación Técnica**: `/docs/technical/narrative_api.md`
- **Guías de Character Voice**: `/docs/character_guides/`
- **Best Practices**: `/docs/content_creation_guidelines.md`
- **Troubleshooting Database**: `/docs/troubleshooting/narrative_issues.md`

### Soporte

Para asistencia adicional:
- **Technical Support**: Revisar logs en el panel de admin
- **Content Guidelines**: Consultar la Biblia Psicológica del proyecto
- **Performance Issues**: Usar herramientas de monitoring integradas

---

**Documento actualizado:** 16 de Septiembre, 2025
**Próxima revisión:** 16 de Octubre, 2025
**Versión del sistema:** 2.0 - Enhanced Narrative Management