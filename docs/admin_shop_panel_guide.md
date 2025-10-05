# Guía del Panel de Administración de Tienda

**Fecha:** 30 de septiembre de 2025
**Autor:** Sistema de Admin
**Módulo:** `handlers/admin/shop_admin.py` y `handlers/admin/shop_unlock_config.py`

---

## 📋 Descripción General

El Panel de Administración de Tienda permite gestionar completamente la tienda del bot desde una interfaz visual, sin necesidad de modificar código. Incluye:

✅ **CRUD completo de productos**
✅ **Gestión de desbloqueos narrativos**
✅ **Reportes de ventas**
✅ **Navegación limpia (single-message pattern)**

---

## 🎯 Acceso al Panel

**Ruta:** Admin Principal → 🛒 Tienda

```
/start (como admin) → 🛒 Tienda
```

---

## 🛒 Funcionalidades Principales

### 1. **Ver Productos** (`admin_shop_list`)

Muestra todos los productos de la tienda con indicadores visuales:

- ✅ **Activo** / ❌ **Inactivo**
- 👑 **VIP-only** / 🆓 **Para Todos**
- 🔓 **Desbloquea contenido** / 📦 **Sin desbloqueo**

**Vista de cada producto:**
```
✅ 👑 🔓 📓 Diario Íntimo
   💰 30 besitos
```

### 2. **Crear Producto** (`admin_shop_create`)

Flujo paso a paso usando FSM (Finite State Machine):

#### **Paso 1: Nombre**
```
➕ Crear Producto

📝 Paso 1: Nombre del Producto

Ingresa el nombre del producto (incluye emoji):
Ejemplo: "📓 Diario Íntimo"
```

- Valida que no exista un producto con el mismo nombre
- Permite emojis para mejor visualización

#### **Paso 2: Descripción**
```
📝 Paso 2: Descripción

Ingresa una descripción atractiva del producto:
(Explica qué desbloquea y por qué es valioso)
```

#### **Paso 3: Precio**
```
💰 Paso 3: Precio

Ingresa el precio en besitos (puntos):

💡 Precios recomendados:
• Básico: 30 besitos
• Intermedio: 50 besitos
• Premium: 100 besitos
• Exclusivo: 150+ besitos
```

- Valida que sea un número entero positivo

#### **Paso 4: Acceso VIP**
```
👑 Paso 4: Acceso VIP

¿Este producto es exclusivo para usuarios VIP?

[👑 Solo VIP] [🆓 Para Todos]
```

#### **Paso 5: Desbloqueo de Contenido**
```
🔓 Paso 5: Desbloqueo de Contenido

¿Este producto desbloquea contenido narrativo?

[✅ Sí, desbloquea contenido] [❌ No desbloquea nada]
```

Si elige "Sí":
- Muestra lista de `LorePiece` disponibles
- Permite seleccionar cuál se desbloquea al comprar
- Categoriza por tipo (🗺️ Fragmentos, 💭 Memorias, 🔮 Secretos, 🗝️ Llaves)

#### **Confirmación Final**
```
✅ Producto Creado con Éxito

📓 Diario Íntimo ha sido agregado a la tienda.

Configuración:
• 💰 Precio: 30 besitos
• 🆓 Para Todos
• ✅ Estado: Activo

Desbloqueo:
🔓 Al comprar, desbloquea:
Diario Íntimo de Diana
`diario_intimo_diana`

⚠️ Importante: Para que el desbloqueo funcione en decisiones narrativas,
debes configurar el decision_requirements en el Coordinador Central.
```

### 3. **Ver Detalle de Producto** (`admin_shop_view_item`)

Al hacer clic en un producto desde la lista:

```
📦 📓 Diario Íntimo

Descripción:
El diario personal más íntimo de Diana. Desbloquea contenido narrativo especial y exclusivo.

Configuración:
• 💰 Precio: 30 besitos
• 👑 Solo VIP: No
• ✅ Estado: Activo
• 📊 Ventas: 15

Desbloqueo:
🔓 Desbloquea: Diario Íntimo de Diana
   📜 `diario_intimo_diana`

Acciones:
[✏️ Editar] [❌ Desactivar]
[🔓 Config. Desbloqueo] [🗑️ Eliminar]
[🔙 Volver]
```

**Acciones disponibles:**
- ✏️ **Editar**: Modificar nombre, descripción, precio
- ❌ **Activar/Desactivar**: Toggle rápido del estado
- 🔓 **Config. Desbloqueo**: Ir a gestión de decision_requirements
- 🗑️ **Eliminar**: Eliminar el producto (con confirmación)

### 4. **Activar/Desactivar** (`admin_shop_toggle`)

Toggle instantáneo del estado `is_active`:

```
✅ Producto activado
```

- Los productos inactivos no aparecen en la tienda de usuarios
- Los usuarios que ya lo compraron mantienen el acceso

### 5. **Eliminar Producto** (`admin_shop_delete_confirm`)

Confirmación de seguridad antes de eliminar:

```
🗑️ Confirmar Eliminación

¿Estás seguro de que deseas eliminar este producto?

📓 Diario Íntimo
💰 30 besitos

⚠️ Advertencia:
• Los usuarios que ya lo compraron mantendrán el acceso
• El producto desaparecerá de la tienda
• Esta acción NO se puede deshacer

[✅ Sí, Eliminar] [❌ Cancelar]
```

---

## 🔗 Gestión de Desbloqueos Narrativos

**Ruta:** Admin → Tienda → 🔗 Gestionar Desbloqueos

### ¿Qué son los Desbloqueos?

El sistema permite **condicionar decisiones narrativas** a la posesión de items de tienda.

**Flujo:**
```
Usuario toma decisión → Sistema verifica item →
   ├─ SIN item: Muestra "teaser" + link a tienda
   └─ CON item: Acceso a contenido exclusivo
```

### Panel de Desbloqueos (`admin_shop_unlocks`)

```
🔗 Gestión de Desbloqueos Narrativos

Este panel gestiona el mapeo entre decision_id (decisiones narrativas) e items de tienda.

¿Cómo funciona?
1. Usuario encuentra una decisión narrativa con un decision_id
2. El sistema verifica si tiene el item requerido
3. Si NO lo tiene → Muestra fragmento "teaser"
4. Si SÍ lo tiene → Permite acceder al contenido exclusivo

Configuración Actual:

• Decision `1` → 📖 Diario Secreto
• Decision `15` → 📓 Diario Íntimo

Acciones:
[➕ Agregar Desbloqueo]
[✏️ Editar Desbloqueo]
[🗑️ Eliminar Desbloqueo]
[📖 Ver Documentación]
```

### Agregar Desbloqueo (`admin_unlock_add`)

**Paso 1: Seleccionar Producto**

```
➕ Agregar Desbloqueo

Paso 1: Selecciona el Producto

Elige qué producto de tienda quieres vincular a una decisión narrativa:

[🆓 📓 Diario Íntimo (30💋)]
[👑 📖 Diario Secreto (50💋)]
...
```

**Paso 2: Ingresar decision_id**

```
✅ Producto seleccionado: 📓 Diario Íntimo

Paso 2: Decision ID

Ingresa el decision_id de la decisión narrativa que requerirá este producto.

📖 ¿Dónde encuentro el decision_id?
Los decision IDs están definidos en tus fragmentos narrativos y en la base de datos de decisiones.

Ejemplo: El "Diario Íntimo" usa decision_id = 15

Formato: Solo números (ej: 15, 25, 30)
```

**Confirmación:**

```
✅ Desbloqueo Configurado

Decision ID: `15`
Item Requerido: 📓 Diario Íntimo

¿Qué sucede ahora?
1. Cuando un usuario intente tomar la decisión 15
2. El sistema verificará si tiene 📓 Diario Íntimo en su inventario
3. Si NO lo tiene → Será redirigido al fragmento "teaser"
4. Si SÍ lo tiene → Podrá acceder al contenido exclusivo

⚠️ Importante: Asegúrate de que:
• Existe un fragmento "teaser" configurado en coordinador_central.py
• Existe el fragmento exclusivo para cuando tenga el item
• El handler detecta esta decisión especial

📖 Consulta: docs/guia-fragmentos-condicionados-items-2025-09-15.md
```

### Manejo de Conflictos

Si el `decision_id` ya está asignado:

```
⚠️ Conflicto Detectado

El decision_id = 15 ya está asignado a:
📖 Diario Secreto

¿Deseas reemplazarlo con 📓 Diario Íntimo?

[✅ Reemplazar] [❌ Cancelar]
```

### Documentación Integrada (`admin_unlock_docs`)

```
📖 Documentación: Sistema de Desbloqueos

Flujo Completo:

1️⃣ Usuario intenta tomar una decisión
   → Handler detecta decision_id especial

2️⃣ Sistema verifica inventario
   → ShopService.has_item_in_inventory(user_id, item_name)

3️⃣ Sin el item:
   → Redirige a fragmento "teaser"
   → Muestra mensaje motivacional + link a tienda

4️⃣ Con el item:
   → Permite acceso al fragmento exclusivo
   → Recompensa al usuario

Archivos Involucrados:
• services/coordinador_central.py - Lógica de verificación
• handlers/narrative_handler.py - Detecta decisiones especiales
• config/decision_requirements.json - Configuración (este panel)

Caso de Éxito: Diario Íntimo
• Decision ID: 15
• Item: "📓 Diario Íntimo" (30 besitos)
• Teaser: diana_diary_tease
• Exclusivo: diana_diary_intimate
```

---

## 📊 Reportes de Ventas (`admin_shop_reports`)

```
📊 Reportes de Ventas

Resumen General:
• 🛒 Total de ventas: 42
• 💰 Ingresos totales: 1260 besitos

Top 5 Productos Más Vendidos:

1. 📓 Diario Íntimo
   💰 30 besitos × 25 ventas = 750 total

2. 📖 Diario Secreto
   💰 50 besitos × 10 ventas = 500 total

3. 🔮 Cristal Místico
   💰 100 besitos × 5 ventas = 500 total

4. 🗝️ Llave Maestra
   💰 80 besitos × 2 ventas = 160 total
```

**Métricas incluidas:**
- Total de ventas (transacciones)
- Ingresos totales (besitos)
- Top 5 productos por volumen de ventas
- Ingresos por producto

---

## 🗂️ Archivos de Configuración

### `config/decision_requirements.json`

Este archivo JSON almacena el mapeo entre `decision_id` y `item_name`:

```json
{
  "1": "📖 Diario Secreto",
  "15": "📓 Diario Íntimo",
  "25": "🔮 Cristal Místico"
}
```

**Ubicación:** `/home/azureuser/repos/bolt_ok/mybot/config/decision_requirements.json`

**Creación automática:** El panel crea este archivo automáticamente si no existe.

**Formato:**
- **Clave**: `decision_id` (string)
- **Valor**: Nombre exacto del `ShopItem` (string)

⚠️ **Importante:** El nombre del item debe coincidir EXACTAMENTE con `ShopItem.name`.

---

## 🔄 Integración con el Sistema Existente

### Coordinador Central

El `CoordinadorCentral` lee este archivo en `_flujo_tomar_decision()`:

```python
# services/coordinador_central.py:334
decision_requirements = {
    1: "📖 Diario Secreto",
    15: "📓 Diario Íntimo",
}
```

**Migración:** El sistema actual usa un diccionario hardcodeado. En el futuro, se puede modificar para leer directamente desde `decision_requirements.json`.

### Shop Service

El `ShopService` maneja:
- `get_available_items(user_id)` - Filtra productos por VIP
- `purchase_item(user_id, item_id)` - Procesa compra
- `has_item_in_inventory(user_id, item_name)` - Verifica posesión
- `_add_to_backpack(user_id, item_id, shop_item)` - Desbloquea LorePiece

### Flujo de Compra

```
Usuario → [buy_item:15] → ShopHandler → CoordinadorCentral → ShopService
                                                                    ↓
                                                          purchase_item()
                                                                    ↓
                                                          Valida puntos/VIP
                                                                    ↓
                                                          Deduce besitos
                                                                    ↓
                                                          Registra UserPurchase
                                                                    ↓
                                                          _add_to_backpack()
                                                                    ↓
                                                          Crea UserLorePiece
                                                                    ↓
                                                          Notifica al usuario ✅
```

---

## 🎨 Patrones de Diseño

### Single-Message Navigation

Todos los menús admin usan el patrón de navegación limpia:

```python
await update_menu(
    callback,
    text,
    keyboard,
    session,
    "admin_shop_main"
)
```

**Beneficios:**
- Un solo mensaje que se edita
- Chat limpio sin historial de menús
- Mejor UX para administradores

### FSM States

El flujo de creación usa estados finitos:

```python
class AdminShopStates(StatesGroup):
    creating_name = State()
    creating_description = State()
    creating_price = State()
    creating_vip_only = State()
    selecting_unlock = State()
    confirming_creation = State()
```

**Ventajas:**
- Flujo guiado paso a paso
- Validación en cada etapa
- Cancelación en cualquier momento

---

## 🚀 Casos de Uso

### Caso 1: Crear Producto Simple

**Objetivo:** Crear un producto decorativo sin desbloqueo

1. Admin → Tienda → ➕ Crear Producto
2. Nombre: "🎁 Regalo Especial"
3. Descripción: "Un regalo personalizado de Diana"
4. Precio: 20
5. Acceso: 🆓 Para Todos
6. Desbloqueo: ❌ No desbloquea nada
7. ✅ Producto creado

**Resultado:** Producto disponible en tienda, sin funcionalidad de desbloqueo.

### Caso 2: Crear Producto con Desbloqueo Narrativo

**Objetivo:** Crear producto que desbloquea contenido exclusivo

1. **Preparación** (antes del panel):
   - Crear `LorePiece` con el contenido exclusivo
   - Crear fragmento "teaser" en narrative_loader
   - Crear fragmento "exclusivo" en narrative_loader

2. **En el panel:**
   - Admin → Tienda → ➕ Crear Producto
   - Nombre: "📓 Diario Íntimo"
   - Descripción: "Accede a los secretos más profundos"
   - Precio: 30
   - Acceso: 🆓 Para Todos
   - Desbloqueo: ✅ Sí → Seleccionar LorePiece

3. **Configurar desbloqueo:**
   - Admin → Tienda → 🔗 Gestionar Desbloqueos
   - ➕ Agregar Desbloqueo
   - Seleccionar: 📓 Diario Íntimo
   - Decision ID: 15

4. **Validación:**
   - Verificar en coordinador_central.py que decision_id 15 tiene lógica teaser
   - Verificar en narrative_handler.py que detecta decisión especial

**Resultado:** Sistema completo de desbloqueo funcional.

### Caso 3: Producto VIP-only

**Objetivo:** Crear producto exclusivo para suscriptores VIP

1. Admin → Tienda → ➕ Crear Producto
2. Nombre: "👑 Corona de Diana"
3. Descripción: "Acceso exclusivo VIP al contenido premium"
4. Precio: 100
5. Acceso: 👑 Solo VIP ← **IMPORTANTE**
6. Desbloqueo: (configurar según necesidad)

**Resultado:** Solo usuarios VIP pueden ver y comprar este producto.

---

## 🔧 Troubleshooting

### Problema: Producto no aparece en tienda

**Verificar:**
1. ✅ `is_active = True`
2. ✅ Si es VIP-only, el usuario debe ser VIP
3. ✅ Verificar en `shop_handlers.py` que llama a `get_available_items()`

**Solución:**
```python
# En admin panel:
Admin → Tienda → Ver Productos → [Producto] → ✅ Activar
```

### Problema: Desbloqueo no funciona

**Verificar:**
1. ✅ `decision_requirements.json` tiene el mapeo correcto
2. ✅ `decision_id` coincide con el del fragmento narrativo
3. ✅ `item_name` coincide EXACTAMENTE con `ShopItem.name`
4. ✅ Fragmento "teaser" existe en coordinador_central
5. ✅ Handler detecta la decisión especial

**Diagnóstico:**
```python
# Ver configuración actual:
Admin → Tienda → 🔗 Gestionar Desbloqueos

# Ver logs:
logger.info(f"Decision {decision_id} requires {required_item}")
```

### Problema: Usuario compró pero no desbloquea

**Verificar:**
1. ✅ `UserPurchase` existe en la base de datos
2. ✅ `UserLorePiece` fue creado en `_add_to_backpack()`
3. ✅ `unlocks_lore_piece_id` está configurado en el producto

**Query de verificación:**
```sql
SELECT * FROM user_purchases WHERE user_id = ? AND shop_item_id = ?;
SELECT * FROM user_lore_pieces WHERE user_id = ? AND lore_piece_id = ?;
```

---

## 📚 Referencias

- **Guía de Fragmentos Condicionados:** `docs/guia-fragmentos-condicionados-items-2025-09-15.md`
- **Análisis Completo:** `docs/analisis_tienda_y_contenido_narrativo.md`
- **Sistema de Navegación Admin:** `docs/admin_navigation_system.md`
- **Coordinador Central:** `services/coordinador_central.py`
- **Shop Service:** `services/shop_service.py`
- **Shop Handlers:** `handlers/shop_handlers.py`

---

## ✅ Checklist de Implementación

### Para Producto Simple
- [ ] Crear producto desde panel
- [ ] Configurar nombre, descripción, precio
- [ ] Configurar acceso (VIP o todos)
- [ ] Activar producto
- [ ] Verificar en tienda de usuario

### Para Producto con Desbloqueo
- [ ] Crear LorePiece (contenido exclusivo)
- [ ] Crear fragmento teaser
- [ ] Crear fragmento exclusivo
- [ ] Crear producto desde panel
- [ ] Vincular producto con LorePiece
- [ ] Configurar decision_requirements (panel)
- [ ] Verificar lógica en coordinador_central
- [ ] Verificar detección en narrative_handler
- [ ] Probar flujo completo: sin item → compra → con item

---

**Desarrollado por:** Sistema de Admin
**Última actualización:** 30 de septiembre de 2025
**Estado:** ✅ Completamente funcional