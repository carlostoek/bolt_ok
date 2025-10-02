# 🎯 Panel de Administración de Misiones - Diseño Completo

## 📋 Objetivo

Crear un panel de administración robusto que permita configurar **todos** los tipos de misiones sin necesidad de modificar código.

---

## 🏗️ Arquitectura Propuesta

### 1. **Modelo de Datos Extendido**

```python
class Mission(Base):
    # Campos existentes
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    reward_points = Column(Integer, default=0)
    type = Column(String, default="one_time")  # Tipos: one_time, daily, weekly, reaction, custom
    target_value = Column(Integer, default=1)
    duration_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False)
    action_data = Column(JSON, nullable=True)
    unlocks_lore_piece_code = Column(String, ForeignKey('lore_pieces.code_name'), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # NUEVOS CAMPOS PROPUESTOS
    mission_category = Column(String, nullable=True)  # narrative, social, competitive, secret
    is_hidden = Column(Boolean, default=False)  # Misiones secretas
    prerequisite_mission_id = Column(String, ForeignKey('missions.id'), nullable=True)  # Misión requerida
    unlocks_mission_id = Column(String, ForeignKey('missions.id'), nullable=True)  # Misión que se desbloquea
    time_limit_minutes = Column(Integer, nullable=True)  # Timer para urgencia
    bonus_points_if_fast = Column(Integer, nullable=True)  # Bonus por rapidez
    min_ranking_position = Column(Integer, nullable=True)  # Para misiones competitivas
    max_completions_global = Column(Integer, nullable=True)  # Límite global (escasez)
    current_completions_global = Column(Integer, default=0)  # Contador
    repeatable = Column(Boolean, default=False)  # Si puede repetirse
    reset_period = Column(String, nullable=True)  # daily, weekly, monthly
    icon_emoji = Column(String, nullable=True)  # Emoji visual
    difficulty_level = Column(Integer, default=1)  # 1-5 estrellas
    xp_reward = Column(Integer, default=0)  # XP adicional además de puntos
    tags = Column(JSON, default=[])  # Tags para filtrar ["vip", "beginner", etc]
```

### 2. **action_data JSON Schema**

El campo `action_data` contendrá configuraciones específicas por tipo de misión:

```json
{
  // Para misiones de reacción
  "action_type": "reaction_count",
  "required_emoji": "💋",
  "target_message_ids": [123, 456],
  "unlocks_lore_piece_code": "garden_secret",

  // Para misiones con timer
  "time_limit_minutes": 5,
  "bonus_points_if_fast": 100,

  // Para misiones competitivas
  "ranking_metric": "weekly_reactions",  // weekly_reactions, total_points, mission_count
  "ranking_position": 10,  // Top 10

  // Para misiones colaborativas (futuro)
  "is_community_mission": true,
  "global_target_value": 10000,
  "reward_type": "all_participants",  // all_participants, top_contributors

  // Para misiones con elección
  "is_choice_mission": true,
  "options": [
    {
      "id": "option_a",
      "name": "Ayudar a Lucien",
      "reward_points": 100,
      "unlocks_lore_piece_code": "lucien_trust"
    },
    {
      "id": "option_b",
      "name": "Explorar solo",
      "reward_points": 150,
      "unlocks_lore_piece_code": "independence"
    }
  ],
  "mutually_exclusive": true,

  // Para misiones narrativas
  "narrative_context": "Lucien te observa con curiosidad...",
  "completion_message": "¡Has ganado la confianza de Lucien!",

  // Para validación personalizada
  "validation_rules": {
    "min_level": 5,
    "requires_vip": false,
    "requires_badge": "first_steps",
    "cooldown_hours": 24
  }
}
```

---

## 📱 Flujo de Creación de Misión en Admin Panel

### **Paso 1: Tipo de Misión**
```
Admin selecciona:
├── 📖 Narrativa Simple (one_time)
├── 🔁 Diaria (daily)
├── 📅 Semanal (weekly)
├── 💬 Por Reacción (reaction)
├── 🏆 Competitiva (competitive)
├── ⏰ Con Timer (timed)
├── 🔗 En Cadena (chain)
├── 🤫 Secreta (hidden)
├── 🌍 Colaborativa (community)
└── ⚙️ Personalizada (custom)
```

### **Paso 2: Información Básica**
```
- Nombre: "🌹 Descubre el Jardín Secreto"
- Descripción: "Reacciona con 💋 a 3 publicaciones de Diana"
- Emoji: 🌹
- Categoría: narrative | social | competitive | secret
- Dificultad: ⭐⭐⭐ (1-5)
```

### **Paso 3: Configuración por Tipo**

#### **Si es NARRATIVA:**
```
- ¿Desbloquea pista de lore? → Seleccionar de lista
- ¿Requiere misión previa? → Seleccionar de lista
- ¿Desbloquea nueva misión? → Seleccionar de lista
- Contexto narrativo: "Lucien te observa..."
- Mensaje al completar: "¡Has ganado la confianza de Lucien!"
```

#### **Si es COMPETITIVA:**
```
- Métrica: [Reacciones semanales | Puntos totales | Misiones completadas]
- Posición requerida: Top [10]
- Recompensa por posición:
  - 1er lugar: [500] puntos
  - 2do-5to: [300] puntos
  - 6to-10mo: [100] puntos
```

#### **Si es CON TIMER:**
```
- Tiempo límite: [5] minutos
- Bonus por rapidez: [100] puntos
- ¿Penalización por fallo?: [Sí/No]
- Puntos de penalización: [20]
```

#### **Si es SECRETA:**
```
- Condición de descubrimiento:
  ├── Reaccionar con emoji específico: [🔮]
  ├── Alcanzar nivel: [10]
  ├── Completar misión: [Seleccionar]
  └── Encontrar código secreto en mensaje
```

#### **Si es COLABORATIVA:**
```
- Objetivo global: [10,000] reacciones
- Contribución individual mínima: [50]
- Duración del evento: [7] días
- Tipo de recompensa:
  ├── Todos los participantes
  ├── Solo top contribuidores (Top [100])
  └── Escalada (más contribuyes, más ganas)
```

### **Paso 4: Recompensas**
```
- Puntos base: [150]
- XP: [50]
- Desbloquea pista: [Seleccionar de lista]
- Badge adicional: [Seleccionar de lista]
- Item de tienda: [Seleccionar de lista]
```

### **Paso 5: Restricciones**
```
- ¿Requiere VIP?: [Sí/No]
- Nivel mínimo: [5]
- Badge requerido: [Seleccionar]
- Máximo de completaciones globales: [100] (escasez)
- Cooldown entre repeticiones: [24] horas
```

### **Paso 6: Visibilidad y Activación**
```
- Estado inicial: [Activa / Inactiva]
- ¿Es visible?: [Sí / No (secreta)]
- Fecha de inicio: [Inmediato / Programar]
- Fecha de fin: [Permanente / [Fecha]]
```

---

## 🖥️ Interfaz de Admin - Wireframe

```
╔══════════════════════════════════════════════════════╗
║  📌 GESTIÓN DE MISIONES                              ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  [➕ Crear Nueva Misión]  [📊 Ver Todas]            ║
║  [🔍 Buscar]  [🏷️ Filtrar por Categoría]            ║
║                                                      ║
║  ┌────────────────────────────────────────────────┐ ║
║  │ 🌹 Descubre el Jardín Secreto                  │ ║
║  │ Tipo: Narrativa | Dificultad: ⭐⭐⭐            │ ║
║  │ Estado: ✅ Activa | Completadas: 45/100        │ ║
║  │ Recompensa: 150 pts + Pista "garden_entrance"  │ ║
║  │                                                 │ ║
║  │ [✏️ Editar] [📊 Stats] [❌ Desactivar] [🗑️]    │ ║
║  └────────────────────────────────────────────────┘ ║
║                                                      ║
║  ┌────────────────────────────────────────────────┐ ║
║  │ 🏆 Top Reaccionador de la Semana               │ ║
║  │ Tipo: Competitiva | Dificultad: ⭐⭐⭐⭐        │ ║
║  │ Estado: ✅ Activa | Ranking actual: Ver        │ ║
║  │ Recompensa: 500 pts (1er lugar)                │ ║
║  │                                                 │ ║
║  │ [✏️ Editar] [📊 Stats] [❌ Desactivar] [🗑️]    │ ║
║  └────────────────────────────────────────────────┘ ║
║                                                      ║
║  [⬅️ Volver al Panel de Admin]                     ║
╚══════════════════════════════════════════════════════╝
```

---

## 📊 Vista de Estadísticas de Misión

```
╔══════════════════════════════════════════════════════╗
║  📊 Estadísticas: "Descubre el Jardín Secreto"      ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Total completadas: 45 / 100 (45%)                  ║
║  Tasa de completación: 72%                          ║
║  Tiempo promedio: 3.5 días                          ║
║  Usuarios activos: 23                               ║
║                                                      ║
║  Top Completadores:                                 ║
║  1. @usuario1 - 15 veces                            ║
║  2. @usuario2 - 12 veces                            ║
║  3. @usuario3 - 8 veces                             ║
║                                                      ║
║  Gráfico de completaciones por día:                 ║
║  ▁▃▄▆█▇▅▃▂ (últimos 9 días)                         ║
║                                                      ║
║  [🔙 Volver]                                        ║
╚══════════════════════════════════════════════════════╝
```

---

## 🔧 Implementación Técnica

### **Nuevos Servicios Necesarios**

```python
# services/mission_template_service.py
class MissionTemplateService:
    """Servicio para crear misiones desde templates predefinidos"""

    async def create_from_template(self, template_name: str, **kwargs) -> Mission:
        """Crea una misión desde un template"""
        pass

    async def list_templates(self) -> list[dict]:
        """Lista todos los templates disponibles"""
        pass

# services/mission_validator_service.py
class MissionValidatorService:
    """Valida si un usuario puede completar una misión"""

    async def can_complete(self, user_id: int, mission_id: str) -> tuple[bool, str]:
        """Verifica requisitos, cooldowns, límites, etc."""
        pass

    async def validate_action(self, user_id: int, mission_id: str, action_data: dict) -> bool:
        """Valida que la acción cumple con los requisitos de la misión"""
        pass

# services/mission_stats_service.py
class MissionStatsService:
    """Estadísticas de misiones"""

    async def get_mission_stats(self, mission_id: str) -> dict:
        """Obtiene estadísticas completas de una misión"""
        pass

    async def get_top_completers(self, mission_id: str, limit: int = 10) -> list:
        """Top usuarios que han completado la misión"""
        pass
```

### **Nuevos Estados FSM para Admin**

```python
class AdminMissionStatesV2(StatesGroup):
    # Flujo básico
    selecting_mission_type = State()
    entering_basic_info = State()

    # Flujo por tipo
    configuring_narrative = State()
    configuring_competitive = State()
    configuring_timed = State()
    configuring_secret = State()
    configuring_community = State()
    configuring_chain = State()

    # Configuración de recompensas
    setting_rewards = State()
    selecting_lore_unlock = State()
    selecting_badge_reward = State()

    # Restricciones
    setting_restrictions = State()
    setting_visibility = State()

    # Confirmación
    confirming_creation = State()
    editing_mission = State()
```

---

## 📦 Templates de Misiones Predefinidos

```json
{
  "templates": [
    {
      "id": "narrative_simple",
      "name": "Misión Narrativa Simple",
      "description": "Una misión que avanza la historia",
      "default_config": {
        "type": "one_time",
        "category": "narrative",
        "requires_action": false,
        "action_data": {}
      }
    },
    {
      "id": "reaction_collector",
      "name": "Colector de Reacciones",
      "description": "Reaccionar X veces con emoji específico",
      "default_config": {
        "type": "weekly",
        "category": "social",
        "requires_action": true,
        "action_data": {
          "action_type": "reaction_count",
          "required_emoji": "❤️"
        }
      }
    },
    {
      "id": "ranking_challenge",
      "name": "Desafío de Ranking",
      "description": "Estar en el top X de una métrica",
      "default_config": {
        "type": "weekly",
        "category": "competitive",
        "requires_action": true,
        "action_data": {
          "action_type": "ranking",
          "ranking_metric": "weekly_reactions"
        }
      }
    },
    {
      "id": "speed_mission",
      "name": "Misión Contra Reloj",
      "description": "Completar en tiempo límite",
      "default_config": {
        "type": "one_time",
        "category": "timed",
        "requires_action": true,
        "action_data": {
          "time_limit_minutes": 5
        }
      }
    }
  ]
}
```

---

## 🎯 Roadmap de Implementación

### **Fase 1: Estructura Base (2-3 días)**
- [ ] Migración de base de datos (nuevos campos)
- [ ] Servicios básicos (MissionValidatorService, MissionStatsService)
- [ ] Estados FSM extendidos

### **Fase 2: Panel Admin Básico (3-4 días)**
- [ ] UI de selección de tipo de misión
- [ ] Formularios dinámicos por tipo
- [ ] Preview antes de crear
- [ ] Edición de misiones existentes

### **Fase 3: Templates y Validación (2-3 días)**
- [ ] Sistema de templates
- [ ] Validación avanzada
- [ ] Vista de estadísticas

### **Fase 4: Funcionalidades Avanzadas (5-7 días)**
- [ ] Misiones en cadena
- [ ] Misiones competitivas
- [ ] Misiones con timer
- [ ] Misiones secretas

### **Fase 5: Polish y Testing (2-3 días)**
- [ ] Testing completo
- [ ] Documentación
- [ ] Optimización

---

## 💡 Notas de Implementación

1. **Backwards Compatibility**: El sistema debe ser compatible con misiones existentes
2. **Validación del lado del servidor**: NUNCA confiar en el cliente
3. **Logs**: Registrar todas las acciones de admin para auditoría
4. **Performance**: Cachear queries frecuentes
5. **UX**: Tooltips y ayuda contextual en cada paso del wizard
6. **Testing**: Tests unitarios para cada tipo de misión

---

## 🚀 Beneficios

✅ **Sin tocar código**: Todo configurable desde el panel
✅ **Flexibilidad total**: Soporta todos los tipos de misiones propuestos
✅ **Escalable**: Fácil agregar nuevos tipos de misiones
✅ **User-friendly**: Wizard paso a paso
✅ **Auditable**: Logs de todas las operaciones
✅ **Performante**: Validación eficiente
