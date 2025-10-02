# 🎭 ROADMAP: EXPERIENCIA DE USUARIO - PLAN PRAGMÁTICO

## 📊 **RESUMEN EJECUTIVO**

**Objetivo:** Crear experiencia de conversión Free → VIP optimizada para creadora de contenido
**Duración:** 6 semanas de desarrollo
**Filosofía:** Simple, funcional, sin sobreingeniería
**Conversión esperada:** 25-35% en primer mes

---

## 🔪 **DECISIONES DE DISEÑO: QUÉ SE ELIMINÓ**

### ❌ **ELIMINADO (Complejidad sin ROI)**

#### 1. Sistema Sombra/Luz Profundo
- **Propuesto:** Análisis complejo de arquetipos, contenido diferenciado
- **Eliminado:** Sobrecomplica sin ROI proporcional
- **Reemplazado con:** Tracking básico (activo/observador/casual) solo para frecuencia de mensajes

#### 2. Juego de Espejos con NLP
- **Propuesto:** Análisis de texto libre, interpretación profunda
- **Eliminado:** Requiere mucho desarrollo, puede fallar
- **Reemplazado con:** Preguntas de opción múltiple (A/B/C/D)

#### 3. Eventos Lunares Automáticos
- **Propuesto:** Scheduler detecta lunas, crea eventos automáticos
- **Eliminado:** Cool pero innecesario
- **Reemplazado con:** Admin crea evento mensual manual (5 min/mes)

#### 4. Múltiples Puntos de Conversión (5+)
- **Propuesto:** Ofertas día 7, 14, 21, 30 diferenciadas
- **Eliminado:** Satura usuario, complica tracking
- **Reemplazado con:** DOS ofertas potentes (día 7, día 30)

#### 5. Sesiones Individuales Automatizadas
- **Propuesto:** Sistema completo de reserva/pago/entrega/follow-up
- **Eliminado:** Es producto separado, requiere desarrollo enorme
- **Reemplazado con:** Botón "Solicitar Sesión" → Admin coordina manualmente

---

## ✅ **QUÉ SE MANTIENE (ROI Alto)**

### 1. CMS de Contenido ⭐ CRÍTICO
- Admin sube sets de fotos/videos/audios
- Bot los envía a usuarios
- **Esfuerzo:** 1 semana | **ROI:** INFINITO

### 2. Journey Automatizado ⭐ CRÍTICO
- Día 1: Regalo "Primera Mirada" automático
- Día 7: Oferta VIP automática
- Día 30: Oferta final automática
- **Esfuerzo:** 3-4 días | **ROI:** ALTO

### 3. Gift Service ⭐ IMPORTANTE
- Enviar regalos sorpresa
- Manual o por logros
- **Esfuerzo:** 2-3 días | **ROI:** ALTO

### 4. Ofertas Temporales
- Códigos de descuento
- Expiración automática
- Escasez (X usos máximo)
- **Esfuerzo:** 2 días | **ROI:** MEDIO-ALTO

### 5. Subastas Mensuales
- Ya existe, solo usar más
- **Esfuerzo:** 0 | **ROI:** ALTO

### 6. Tienda de Productos
- Ya existe, solo agregar más
- **Esfuerzo:** 0 | **ROI:** MEDIO

---

## 📅 **PLAN DE 6 SEMANAS**

### **SEMANA 1-2: CMS DE CONTENIDO**

**Objetivo:** Admin puede gestionar contenido fácilmente

**Tareas:**
- [ ] Crear modelo `ContentSet` en base de datos
- [ ] Admin panel para subir sets (foto/video/audio)
- [ ] Service para enviar sets a usuarios
- [ ] Tracking de quién recibió qué set
- [ ] Comando `/test_send_set` para pruebas

**Entregables:**
```python
# Admin puede:
1. Subir "Set Primera Mirada" (5 fotos)
2. Categorizar como "free", "vip", "gift"
3. Bot lo envía a usuario con narrativa
4. Sistema trackea entrega
```

**Archivos a crear:**
```
database/models.py          → ContentSet model
services/content_service.py → ContentService
handlers/admin/content_admin.py → Admin handlers
migrations/create_content_sets.py → Migración BD
```

---

### **SEMANA 3: JOURNEY AUTOMATIZADO**

**Objetivo:** Usuarios reciben experiencia consistente días 1-30

**Tareas:**
- [ ] Scheduler diario de milestones
- [ ] Día 1: Envío automático "Primera Mirada"
- [ ] Día 7: Oferta VIP automática
- [ ] Día 30: Mensaje final para no-VIP
- [ ] Tracking de milestones cumplidos

**Entregables:**
```python
# Automático:
DÍA 1  → Usuario recibe Set "Primera Mirada" + mensaje Lucien
DÍA 7  → Usuario recibe oferta VIP código PRIMERA_VEZ
DÍA 30 → Usuario (si no-VIP) recibe última oferta código MESUNO
```

**Archivos a crear:**
```
services/user_journey_service.py → Journey logic
schedulers/milestone_scheduler.py → Scheduler diario
handlers/journey_messages.py → Mensajes del journey
```

---

### **SEMANA 4: GIFT SERVICE**

**Objetivo:** Capacidad de sorprender usuarios estratégicamente

**Tareas:**
- [ ] Service `send_gift()` funcional
- [ ] Admin puede enviar regalos manuales
- [ ] Regalos automáticos por logros
- [ ] Tracking de regalos recibidos
- [ ] Prevenir duplicados

**Entregables:**
```python
# Admin puede:
1. Enviar regalo a usuario específico
2. Enviar regalo a segmento (todos VIP, todos día-15, etc)
3. Sistema automático: "Compró 5 productos → regalo sorpresa"

# Ejemplos:
- Usuario ganó subasta → regalo bonus
- Usuario cumple 60 días → regalo lealtad
- Usuario alcanzó nivel 10 → regalo milestone
```

**Archivos a crear:**
```
services/gift_service.py → Gift logic
handlers/admin/gift_admin.py → Admin panel para gifts
database/models.py → GiftRecord model (tracking)
```

---

### **SEMANA 5: OFERTAS Y CÓDIGOS**

**Objetivo:** Crear urgencia en conversiones

**Tareas:**
- [ ] Modelo `Offer` en BD
- [ ] Admin crea ofertas con código
- [ ] Validación automática al suscribirse
- [ ] Expiración por fecha
- [ ] Límite de usos (escasez)
- [ ] Tracking de uso

**Entregables:**
```python
# Admin crea oferta:
Código: PRIMERA_VEZ
Descuento: 100% (gratis)
Válida hasta: 24hrs después de enviarse
Usos máximos: Ilimitado

Código: MESUNO
Descuento: 50%
Válida hasta: [fecha específica]
Usos máximos: 50

# Usuario usa código al suscribirse VIP
# Sistema valida automáticamente
```

**Archivos a crear:**
```
database/models.py → Offer model
services/offer_service.py → Offer logic
handlers/admin/offer_admin.py → Admin panel
handlers/subscription.py → Integrar códigos en suscripción
```

---

### **SEMANA 6: POLISH Y TESTING**

**Objetivo:** Sistema 100% funcional y documentado

**Tareas:**
- [ ] Testing completo del journey
- [ ] Simular usuario desde día 0 hasta día 30
- [ ] Verificar todos los regalos se envían
- [ ] Verificar ofertas funcionan
- [ ] Ajustar mensajes narrativos (tono Diana/Lucien)
- [ ] Documentar flujos para admin
- [ ] Manual de uso para administrador

**Entregables:**
```
✅ Journey día 1-30 funciona perfecto
✅ Admin sabe cómo subir contenido
✅ Admin sabe cómo crear ofertas
✅ Admin sabe cómo enviar regalos
✅ Documentación completa
✅ Sistema en producción
```

---

## 🎯 **JOURNEY SIMPLIFICADO: LA EXPERIENCIA REAL**

### **DÍA 1: BIENVENIDA AUTOMÁTICA**

```
🎩 LUCIEN (bot automático):
"Bienvenido al umbral. Diana sabe que estás aquí...
pero aún no decide si quiere conocerte.

Demuestra que mereces su atención."

🎁 REGALO AUTOMÁTICO:
→ Set "Primera Mirada" (5 fotos artísticas)
  • Sugerentes, elegantes, NO explícitas
  • Calidad profesional
  • Móvil con funda anime visible (marca personal)

💭 DIANA:
"Esto es lo que muestro al inicio.
Quédate y verás mucho más."
```

**Implementación:**
```python
# services/user_journey_service.py
async def check_day_1_milestone(user):
    if not user.received_day1_gift:
        await ContentService.send_set(user.id, "Primera_Mirada",
            context_message=LUCIEN_WELCOME_MESSAGE)
        await bot.send_message(user.id, DIANA_FIRST_MESSAGE)
        user.received_day1_gift = True
```

---

### **DÍAS 2-6: NUTRICIÓN PASIVA**

```
📱 CANAL GRATUITO (admin publica manual):
- 2-3 posts por semana
- 1 foto teaser por post
- Botones de reacción (sistema ya existe)
- Menciones casuales: "Los de El Diván ya vieron el set completo de esto"

NO hay automatización aquí, admin publica como siempre
```

---

### **DÍA 7: PRIMERA OFERTA VIP (AUTOMÁTICA)**

```
🎩 LUCIEN (bot automático):
"Una semana observando desde afuera.
Diana pregunta: ¿Estás listo para entrar a su mundo real?

🔥 OFERTA ESPECIAL (solo hoy):
✅ Primera semana VIP GRATIS
✅ Sin compromiso, cancela cuando quieras
✅ Acceso inmediato a todo el contenido exclusivo

Código: PRIMERA_VEZ
Válido hasta mañana a las 23:59"

[Botón: 💎 Sí, entrar a El Diván]
[Botón: ⏳ Todavía no]
```

**Si usuario hace clic "Sí":**
```
→ Proceso de suscripción VIP
→ Aplica código PRIMERA_VEZ automáticamente
→ Usuario entra a canal VIP
→ Recibe mensaje de bienvenida VIP
```

**Si usuario hace clic "Todavía no":**
```
💭 DIANA:
"Lo entiendo perfectamente. No todos están listos.
Toma esto mientras decides..."

🎁 REGALO COMPENSATORIO:
→ Set "Paciencia" (3 fotos)

"Nos vemos cuando estés listo."
```

**Implementación:**
```python
# services/user_journey_service.py
async def check_day_7_milestone(user):
    if user.role == "free" and not user.received_vip_offer:
        # Crear oferta personal
        offer = await OfferService.create_offer(
            code=f"PRIMERA_VEZ_{user.id}",
            discount_percent=100,
            valid_hours=24,
            user_specific=user.id
        )

        await bot.send_message(user.id, LUCIEN_VIP_OFFER,
            reply_markup=get_vip_offer_keyboard())
        user.received_vip_offer = True
```

---

### **DÍAS 8-29: DESARROLLO**

**USUARIOS GRATUITOS:**
```
📱 Siguen en canal gratuito
📬 Contenido regular 2x semana (admin publica manual)
🎭 Invitaciones a subastas mensuales (pueden pujar por 1 caja)
💭 Teasers casuales de contenido VIP
```

**USUARIOS VIP:**
```
💎 Canal VIP con contenido diario/semanal abundante
📦 Sets completos (no teasers)
🎁 Behind-the-scenes
🔓 Acceso a todas las cajas en subastas
🛍️ Descuentos en tienda
```

---

### **DÍA 30: ÚLTIMA OFERTA (SOLO FREE, AUTOMÁTICA)**

```
💌 DIANA (bot automático):
"Un mes juntos.
Has visto fragmentos de mi mundo, pero solo eso... fragmentos.

¿No te preguntas cómo es el cuadro completo?

🔥 ÚLTIMA OPORTUNIDAD:
✅ 50% descuento en primer mes VIP
✅ Código: MESUNO
✅ Expira en 48 horas

Después de esto, seguirás siendo bienvenido aquí...
pero te perderás mucho de lo que comparto dentro."

[Botón: 💎 Entrar a El Diván]
[Botón: 💭 Prefiero quedarme aquí]
```

**Si acepta:** Usuario VIP
**Si rechaza:** Queda en nutrición pasiva indefinida

**Implementación:**
```python
# services/user_journey_service.py
async def check_day_30_milestone(user):
    if user.role == "free" and not user.received_final_offer:
        offer = await OfferService.create_offer(
            code=f"MESUNO_{user.id}",
            discount_percent=50,
            valid_hours=48,
            user_specific=user.id
        )

        await bot.send_message(user.id, DIANA_FINAL_OFFER,
            reply_markup=get_final_offer_keyboard())
        user.received_final_offer = True
```

---

## 💰 **CONVERSIÓN ESPERADA**

### **Primer Mes (100 usuarios nuevos):**

```
DÍA 1:  100 usuarios reciben "Primera Mirada"
        → 85-90 permanecen activos

DÍA 7:  ~85 usuarios reciben oferta gratis
        → 15-20 convierten a VIP (17-23%)

DÍA 30: ~65 usuarios free reciben oferta 50%
        → 10-15 convierten adicionales (15-23%)

TOTAL: 25-35 VIPs de 100 iniciales
CONVERSIÓN: 25-35% primer mes
```

### **Retención VIP (Segundo Mes):**

```
De 30 VIPs del primer mes:
→ 21-24 renuevan (70-80%) gracias a contenido de calidad
→ 3-5 compran productos tienda (10-15%)
→ 1-3 solicitan sesión individual (5-10%)
```

### **Lifetime Value:**

```
Usuario PROMEDIO:
- Permanece 3-4 meses VIP
- Gasta $X/mes en suscripción
- Compra 2-3 productos adicionales
- 10% compra sesión individual ($$$)

LTV estimado: [calcular según precios reales]
```

---

## 📊 **MÉTRICAS A TRACKEAR**

### **Dashboard Admin (implementar en semana 6):**

```
📈 CONVERSIÓN:
- Usuarios nuevos hoy/semana/mes
- % conversión día 7
- % conversión día 30
- % conversión total

👥 ENGAGEMENT:
- Usuarios activos diarios
- Reacciones promedio por post
- Usuarios en subastas
- Compras en tienda

💎 RETENCIÓN VIP:
- Renovaciones mes a mes
- Cancelaciones
- Tiempo promedio de permanencia

🎁 CONTENIDO:
- Sets enviados
- Sets más populares
- Regalos enviados
```

---

## 🛠️ **STACK TÉCNICO**

### **Base de Datos:**
```sql
-- Nuevas tablas necesarias:

content_sets (
    id, name, type, tier, file_ids, description, created_at
)

offers (
    code, discount_percent, valid_until, max_uses, current_uses, user_specific
)

gift_records (
    user_id, content_set_id, sent_at, context
)

user_milestones (
    user_id, milestone_day, completed, completed_at
)
```

### **Servicios Nuevos:**
```
services/
  ├── content_service.py      → Gestión de sets
  ├── user_journey_service.py → Lógica de milestones
  ├── gift_service.py         → Envío de regalos
  └── offer_service.py        → Gestión de ofertas

schedulers/
  └── milestone_scheduler.py  → Chequeo diario de milestones

handlers/admin/
  ├── content_admin.py        → Panel de contenido
  ├── gift_admin.py           → Panel de regalos
  └── offer_admin.py          → Panel de ofertas
```

---

## 📋 **CHECKLIST FINAL**

### **Semana 1-2:**
- [ ] Modelo `ContentSet` creado
- [ ] Admin puede subir sets (fotos/videos)
- [ ] Service envía sets a usuarios
- [ ] Tracking funciona
- [ ] Testing: Set "Primera Mirada" se envía correctamente

### **Semana 3:**
- [ ] Scheduler diario funciona
- [ ] Día 1 automático funciona
- [ ] Día 7 automático funciona
- [ ] Día 30 automático funciona
- [ ] Testing: Simular usuario 30 días

### **Semana 4:**
- [ ] Service `send_gift()` funciona
- [ ] Admin puede enviar regalo manual
- [ ] Regalos por logros funcionan
- [ ] Testing: Regalo por compra, regalo por milestone

### **Semana 5:**
- [ ] Modelo `Offer` creado
- [ ] Admin puede crear ofertas
- [ ] Códigos se validan al suscribirse
- [ ] Expiración funciona
- [ ] Testing: Código válido/inválido/expirado

### **Semana 6:**
- [ ] Journey completo testeado
- [ ] Mensajes narrativos ajustados
- [ ] Documentación creada
- [ ] Admin entrenado
- [ ] Sistema en producción

---

## 🚀 **LANZAMIENTO**

### **Pre-Launch:**
```
✅ Contenido preparado (sets fotográficos categorizados)
✅ Sistema testeado con usuarios beta
✅ Admin sabe usar todas las funciones
✅ Mensajes narrativos aprobados
```

### **Launch Day:**
```
1. Anunciar en canal que "el journey comienza"
2. Nuevos usuarios entran al journey automático
3. Monitorear primeros días
4. Ajustar según feedback
```

### **Post-Launch:**
```
📊 Revisar métricas semanalmente
🎨 Agregar contenido constantemente
🎁 Sorprender con regalos inesperados
📈 Optimizar mensajes según conversión
```

---

## ✨ **PRINCIPIOS GUÍA**

1. **SIMPLE > COMPLEJO**
   - Si algo toma más de 1 semana desarrollar, replantear
   - Manual está bien si es esporádico

2. **CONTENIDO > TECNOLOGÍA**
   - La mejor tecnología no compensa mal contenido
   - Fotos de calidad > features complejas

3. **CONVERSIÓN > ENGAGEMENT**
   - Objetivo: llevar a VIP
   - Engagement es medio, no fin

4. **PRAGMÁTICO > PERFECTO**
   - Lanzar y ajustar > esperar perfección
   - MVP funcional > sistema completo teórico

---

## 📞 **CONTACTO Y SOPORTE**

**Documentación adicional:**
- `/docs/MISSION_ADMIN_PANEL_DESIGN.md` - Sistema de misiones
- `/docs/REACCIONES_NATIVAS_IMPLEMENTACION.md` - Reacciones
- `/docs/concepto.md` - Concepto original del bot

**Para debugging:**
```bash
# Ver logs de journey
tail -f logs/bot.log | grep "journey"

# Ver logs de regalos
tail -f logs/bot.log | grep "gift"

# Ver logs de ofertas
tail -f logs/bot.log | grep "offer"
```

---

**VERSIÓN:** 1.0
**FECHA:** 2025-10-02
**STATUS:** 🚀 LISTO PARA IMPLEMENTAR
