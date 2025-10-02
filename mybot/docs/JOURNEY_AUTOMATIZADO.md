# ✅ Journey Automatizado - Week 3 Completado

## 📋 Resumen

Se ha implementado completamente el **Sistema de Journey Automatizado** que procesa milestones del usuario de forma automática (Day 1, 7, 30), enviando contenido y ofertas según la progresión temporal.

**Estado:** ✅ Completado y testeado
**Fecha:** 2025-10-02
**Semana:** 3 del roadmap de 6 semanas

---

## 🎯 Objetivos Cumplidos

El journey automatizado cubre los siguientes hitos del usuario:

### **Day 1: Bienvenida** ✅
- Envío automático del content set `day_1_welcome`
- Mensaje narrativo de Lucien
- Tracking de milestone completado

### **Day 7: Oferta VIP** ✅
- Oferta automática con código de descuento `PRIMERA_VEZ` (15% off)
- Mensaje personalizado según arquetipo
- Envío opcional de teaser VIP (`day_7_vip_teaser`)
- Skip automático para usuarios ya VIP

### **Day 30: Celebración / Última Oferta** ✅
- **Para VIP:** Regalo de celebración (`day_30_vip_gift`)
- **Para no-VIP:** Última oferta con código `MESUNO` (20% off)
- Tracking de conversión

---

## 🏗️ Arquitectura Implementada

### **1. User Journey Service** ✅

**Archivo:** `services/user_journey_service.py`

Servicio central que gestiona toda la lógica del journey del usuario.

#### Métodos principales:

```python
class UserJourneyService:
    # Inicialización
    async def initialize_user_milestones(user_id: int)
        """Crea milestones day_1, day_7, day_30 para nuevo usuario"""

    # Queries
    async def get_users_for_milestone(milestone_type: str) -> List[User]
        """Obtiene usuarios que alcanzaron un milestone pendiente"""

    async def is_milestone_completed(user_id: int, milestone_type: str) -> bool
        """Verifica si un milestone está completado"""

    # Procesamiento
    async def process_day_1_milestone(user: User, bot: Bot) -> bool
        """Envía contenido de bienvenida"""

    async def process_day_7_milestone(user: User, bot: Bot) -> bool
        """Envía oferta VIP con cupón"""

    async def process_day_30_milestone(user: User, bot: Bot) -> bool
        """Envía celebración o última oferta"""

    async def process_all_milestones(bot: Bot) -> Dict[str, int]
        """Procesa TODOS los milestones pendientes (scheduler)"""

    # Tracking
    async def mark_milestone_completed(user_id: int, milestone_type: str, data: Dict)
        """Marca milestone como completado"""
```

#### Lógica de procesamiento:

**Day 1:**
```python
# 1. Envía mensaje de Lucien
# 2. Envía content set "day_1_welcome"
# 3. Marca milestone como completado
```

**Day 7:**
```python
# 1. Verifica si usuario es VIP → Skip si es VIP
# 2. Envía mensaje con oferta y código PRIMERA_VEZ
# 3. (Opcional) Envía teaser VIP si existe
# 4. Marca milestone como completado con metadata del código
```

**Day 30:**
```python
# 1. Si es VIP:
#    - Mensaje de celebración
#    - Envía regalo especial (si existe)
# 2. Si es free:
#    - Última oferta con código MESUNO
#    - Mensaje de despedida amistosa
# 3. Marca milestone como completado con metadata
```

---

### **2. Milestone Scheduler** ✅

**Archivo:** `services/scheduler.py`

Scheduler que ejecuta la verificación de milestones automáticamente.

#### Funciones agregadas:

```python
async def run_user_journey_check(bot: Bot, session_factory):
    """Ejecuta procesamiento de milestones una vez"""
    - Llama a UserJourneyService.process_all_milestones()
    - Registra stats en logs

async def user_journey_scheduler(bot: Bot, session_factory):
    """Loop infinito que ejecuta cada hora"""
    - Intervalo: 3600 segundos (1 hora)
    - Ejecuta run_user_journey_check() cada ciclo
    - Maneja errores y cancellations gracefully
```

#### Integración en bot.py:

```python
# Import
from services.scheduler import user_journey_scheduler

# Registro
task_manager.add_task(
    user_journey_scheduler(bot, session_factory),
    "user_journey"
)
```

**El scheduler se ejecuta automáticamente al iniciar el bot.**

---

### **3. Inicialización Automática de Milestones** ✅

**Archivo:** `middlewares/user_middleware.py`

Cuando un nuevo usuario se registra, se inicializan sus milestones automáticamente.

#### Cambios en UserRegistrationMiddleware:

```python
# Después de crear usuario nuevo:
if not user:
    user = await service.create_user(...)

    # Inicializar milestones del journey
    try:
        journey_service = UserJourneyService(session)
        await journey_service.initialize_user_milestones(user.id)
        logger.info(f"Journey milestones initialized for new user {user.id}")
    except Exception as e:
        logger.error(f"Error initializing journey milestones: {e}")
```

**Cada nuevo usuario tiene automáticamente:**
- Milestone `day_1` (pendiente)
- Milestone `day_7` (pendiente)
- Milestone `day_30` (pendiente)

---

### **4. Admin Panel para Journey** ✅

**Archivos:**
- `handlers/admin/journey_admin.py`
- `keyboards/admin_journey_kb.py`

Panel de administración completo para gestionar y monitorear el journey.

#### Funcionalidades:

##### **📊 Estadísticas Journey**
Muestra:
- Total de usuarios registrados
- Milestones completados por tipo (day_1, day_7, day_30)
- Milestones pendientes
- Tasas de conversión (% completado)

##### **▶️ Forzar Procesamiento**
Ejecuta manualmente el procesamiento de todos los milestones pendientes.
Útil para testing o recuperación de errores.

##### **🧪 Test Milestone**
Permite enviar un milestone específico a un usuario:
1. Seleccionar milestone (day_1, day_7, day_30)
2. Ingresar user_id
3. Envío inmediato del contenido

Ideal para testing antes de desplegar a producción.

##### **👤 Ver Usuario**
Consulta el estado del journey de un usuario específico:
- Milestones completados vs pendientes
- Fechas de completación
- Metadata adicional

##### **Acceso:**
```
/admin → Gestión de Contenido → 📦 CMS Journey → 🎯 Journey Management
```

---

## 📊 Flujo del Journey

### **Timeline automático:**

```
DÍA 0 (Registro)
└─> Se crean 3 milestones (day_1, day_7, day_30) con estado "pendiente"

DÍA 1
└─> Scheduler detecta milestone day_1 alcanzado
    └─> Envía mensaje de Lucien + set "day_1_welcome"
    └─> Marca day_1 como completado

DÍA 7
└─> Scheduler detecta milestone day_7 alcanzado
    ├─> Si usuario es VIP → Skip (marca como completado)
    └─> Si usuario es free:
        └─> Envía oferta VIP + código PRIMERA_VEZ
        └─> (Opcional) Envía teaser VIP
        └─> Marca day_7 como completado

DÍA 30
└─> Scheduler detecta milestone day_30 alcanzado
    ├─> Si usuario es VIP:
    │   └─> Envía celebración + regalo especial
    │   └─> Marca day_30 como completado
    └─> Si usuario es free:
        └─> Envía última oferta + código MESUNO
        └─> Marca day_30 como completado
```

---

## 🧪 Testing

**Archivo:** `tests/test_journey.py`

**5 tests implementados:**

1. ✅ `test_initialize_user_milestones` - Verifica creación de milestones
2. ✅ `test_get_users_for_day_1_milestone` - Query de usuarios por milestone
3. ✅ `test_mark_milestone_completed` - Marcado como completado
4. ✅ `test_is_milestone_completed` - Verificación de estado
5. ✅ `test_skip_day_7_for_vip_users` - Skip automático para VIP

**Cómo ejecutar:**
```bash
export BOT_TOKEN=test_token
export PYTHONPATH=/home/azureuser/repos/bolt_ok/mybot
python tests/test_journey.py
```

**Status:** ✅ Todos los tests pasan exitosamente

---

## 📦 Content Sets Requeridos

Para que el journey funcione completamente, deben existir estos content sets en la BD:

### **Obligatorios:**
```python
# Day 1 - OBLIGATORIO
id="day_1_welcome"
type="photo_set"  # o el tipo que prefieras
tier="gift"
category="welcome"
```

### **Opcionales:**
```python
# Day 7 - Teaser VIP (opcional)
id="day_7_vip_teaser"
tier="gift"
category="teaser"

# Day 30 - Regalo VIP (opcional)
id="day_30_vip_gift"
tier="gift"
category="gift"
```

**Si un content set opcional no existe, simplemente no se envía (no genera error).**

---

## 🎨 Mensajes Narrativos

### **Day 1 - Bienvenida**
```
Hola {username} 💫

Soy Lucien, el guardián de este espacio mágico.

Diana me pidió que te diera la bienvenida y te mostrara
un pequeño adelanto de lo que encontrarás aquí...

Prepárate para tu primera mirada. ✨
```

### **Day 7 - Oferta VIP**
```
{username} 💎

Ha pasado una semana desde que nos conocimos, y Diana
ha notado tu interés por este mundo...

Quiere ofrecerte algo especial: acceso exclusivo VIP
con un descuento único para ti.

🎁 Código de descuento: PRIMERA_VEZ
💫 15% de descuento en tu primera suscripción VIP

Este código es solo para ti y expira en 48 horas.

¿Lista para desbloquear todo el contenido exclusivo? 🔥
```

### **Day 30 - VIP (Celebración)**
```
¡{username}! 🎉

¡Ha pasado un mes desde que te uniste a nosotros!

Diana quiere agradecerte por ser parte de nuestra
comunidad VIP. Tu apoyo hace posible todo esto. 💖

Como agradecimiento, te envío algo especial...
```

### **Day 30 - Free (Última Oferta)**
```
{username} ✨

Ha pasado un mes desde que nos conociste, y aunque
te hemos visto por aquí, aún no has dado el paso...

Diana quiere darte una última oportunidad especial:

🎁 Código exclusivo: MESUNO
💎 20% de descuento en cualquier suscripción VIP

Este es nuestro mejor descuento y expira en 72 horas.

Si decides quedarte con el contenido gratuito, está bien,
seguiremos compartiendo sorpresas contigo de vez en cuando. 💫

Pero si quieres ver TODO lo que Diana tiene para ofrecerte,
esta es tu oportunidad. 🔥
```

---

## 🔧 Configuración

### **Intervalos de Scheduler:**

Por defecto, el journey scheduler ejecuta cada **1 hora**.

Para cambiar el intervalo, editar en `services/scheduler.py:260`:
```python
interval = 3600  # segundos (3600 = 1 hora)
```

Intervalos recomendados:
- **Producción:** 3600 (1 hora)
- **Testing:** 60 (1 minuto)
- **Diario:** 86400 (24 horas)

### **Personalización de Días:**

Para cambiar los días de cada milestone, editar en `services/user_journey_service.py:77-81`:
```python
days_map = {
    "day_1": 1,    # Cambiar a 0 para envío inmediato
    "day_7": 7,
    "day_30": 30
}
```

---

## 📁 Archivos Modificados/Creados

### Creados:
- `services/user_journey_service.py` ✅
- `handlers/admin/journey_admin.py` ✅
- `keyboards/admin_journey_kb.py` ✅
- `tests/test_journey.py` ✅

### Modificados:
- `services/scheduler.py` - Agregado user_journey_scheduler ✅
- `middlewares/user_middleware.py` - Auto-inicialización de milestones ✅
- `bot.py` - Registro de router y scheduler ✅
- `keyboards/admin_content_cms_kb.py` - Agregado botón Journey Management ✅

---

## 🔍 Debugging

### **Ver logs del scheduler:**
```bash
tail -f bot.log | grep "Journey milestones processed"
```

Output esperado cada hora:
```
2025-10-02 12:00:00 - INFO - Journey milestones processed - Day 1: 5, Day 7: 2, Day 30: 1, Errors: 0
```

### **Verificar estado de un usuario:**

```sql
-- Ver milestones de usuario
SELECT * FROM user_milestones WHERE user_id = 123;

-- Ver regalos recibidos
SELECT * FROM gift_records WHERE user_id = 123;
```

### **Forzar procesamiento manual:**

Desde el admin panel:
```
/admin → CMS Journey → Journey Management → ▶️ Forzar Procesamiento
```

O ejecutar directamente:
```python
from services.user_journey_service import UserJourneyService
journey_service = UserJourneyService(session)
stats = await journey_service.process_all_milestones(bot)
```

---

## 📈 Métricas Esperadas

Con el journey automatizado, las conversiones esperadas son:

| Milestone | Tasa de Entrega | Conversión a VIP | Notas |
|-----------|----------------|------------------|-------|
| **Day 1** | ~95% | N/A | Bienvenida obligatoria |
| **Day 7** | ~80% | **5-10%** | Primera conversión |
| **Day 30** | ~60% | **10-15%** | Última oportunidad |

**Objetivo total de conversión:** **25-35%** a los 30 días

---

## ✅ Checklist Week 3

- [x] UserJourneyService creado
- [x] Métodos de procesamiento para day_1, day_7, day_30
- [x] Scheduler agregado y registrado
- [x] Auto-inicialización en registro de usuario
- [x] Admin panel completo
- [x] Estadísticas en tiempo real
- [x] Test de milestones individuales
- [x] 5 tests unitarios pasando
- [x] Documentación completa

---

## 🚀 Próximos Pasos (Week 4)

**Gift Service para sorpresas estratégicas:**

1. **Manual Gifts:**
   - Enviar regalos por logros (ganó subasta, compró en tienda)
   - Mensaje narrativo según contexto

2. **Surprise Gifts:**
   - Admin programa sorpresas espontáneas
   - Segmentación básica (VIP vs Free, Luz vs Sombra)

---

**Sistema de journey 100% funcional y automático!** 🎉

Los usuarios ahora reciben una experiencia consistente y personalizada desde el día 1 hasta el día 30, con ofertas estratégicas en momentos clave de conversión.

**Next sprint:** Gift Service y ofertas temporales (Week 4-5)
