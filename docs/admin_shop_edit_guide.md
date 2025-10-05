# Guía de Edición de Productos - Panel de Tienda

**Fecha:** 30 de septiembre de 2025
**Mejora:** #2 - Implementar edición de productos existentes
**Estado:** ✅ Completado

---

## 📋 Resumen

Se implementó la funcionalidad completa para editar productos existentes desde el panel de administración, permitiendo modificar todos los campos de un producto sin necesidad de eliminarlo y recrearlo.

---

## 🎯 Funcionalidades Implementadas

### Menú de Edición Principal

**Ruta:** Admin → Tienda → [Producto] → ✏️ Editar

```
✏️ Editar Producto

Producto: 📓 Diario Íntimo

¿Qué deseas editar?

[📝 Nombre]        [📄 Descripción]
[💰 Precio]        [👑 Acceso VIP]
[🔓 Desbloqueo]
[🔙 Volver]
```

**Campos editables:**
1. 📝 **Nombre** - Nombre del producto (con validación de duplicados)
2. 📄 **Descripción** - Descripción detallada
3. 💰 **Precio** - Precio en besitos
4. 👑 **Acceso VIP** - Toggle solo VIP / para todos
5. 🔓 **Desbloqueo** - Configurar qué LorePiece desbloquea

---

## 🔧 Flujos de Edición

### 1. Editar Nombre (`edit_field:name`)

**Paso 1: Solicitar nuevo nombre**
```
✏️ Editar Nombre

Nombre actual: 📓 Diario Íntimo

Ingresa el nuevo nombre del producto (incluye emoji):
Ejemplo: "📓 Diario Íntimo Deluxe"

💡 Tip: Usa emojis relevantes para mejor visualización.
```

**Paso 2: Validación**
- ✅ Verifica que el nombre no exista (excepto el actual)
- ✅ Actualiza el nombre en la base de datos
- ✅ Muestra confirmación con antes/después

**Paso 3: Confirmación**
```
✅ Nombre Actualizado

Antes: 📓 Diario Íntimo
Ahora: 📓 Diario Íntimo Premium

El nombre ha sido actualizado exitosamente.

[✏️ Editar Otro Campo]
[👁️ Ver Producto]
[🔙 Lista de Productos]
```

**Estado FSM:** `AdminShopStates.editing_name`

**Validaciones:**
- Nombre no vacío
- No existe otro producto con el mismo nombre
- Longitud razonable (máx 255 caracteres)

---

### 2. Editar Descripción (`edit_field:description`)

**Paso 1: Solicitar nueva descripción**
```
✏️ Editar Descripción

Descripción actual:
El diario personal más íntimo de Diana...

Ingresa la nueva descripción del producto:
(Explica qué desbloquea y por qué es valioso)
```

**Paso 2: Procesamiento**
- ✅ Acepta texto largo (multiline)
- ✅ Actualiza descripción completa
- ✅ Muestra la nueva descripción

**Paso 3: Confirmación**
```
✅ Descripción Actualizada

Producto: 📓 Diario Íntimo Premium

Nueva descripción:
Accede a los pensamientos más profundos...

La descripción ha sido actualizada exitosamente.
```

**Estado FSM:** `AdminShopStates.editing_description`

**Características:**
- Soporta markdown
- Sin límite de longitud (práctico)
- Puede dejarse vacía

---

### 3. Editar Precio (`edit_field:price`)

**Paso 1: Solicitar nuevo precio**
```
✏️ Editar Precio

Producto: 📓 Diario Íntimo
Precio actual: 30 besitos

Ingresa el nuevo precio en besitos (puntos):

💡 Precios recomendados:
• Básico: 30 besitos
• Intermedio: 50 besitos
• Premium: 100 besitos
• Exclusivo: 150+ besitos
```

**Paso 2: Validación**
- ✅ Debe ser un número entero
- ✅ Debe ser positivo (>= 0)
- ✅ Calcula el cambio porcentual

**Paso 3: Confirmación con análisis**
```
✅ Precio Actualizado

Producto: 📓 Diario Íntimo

Precio anterior: 30 besitos
Precio nuevo: 50 besitos
Cambio: +66.7%

El precio ha sido actualizado exitosamente.
```

**Estado FSM:** `AdminShopStates.editing_price`

**Features especiales:**
- 📊 Cálculo automático de cambio porcentual
- 💡 Sugerencias de precios
- ⚠️ Advertencia si el cambio es muy drástico (opcional)

---

### 4. Editar Acceso VIP (`edit_field:vip`)

**Toggle instantáneo** (sin FSM)

**Antes:** 🆓 Para Todos
**Click en "👑 Acceso VIP"**
**Después:** 👑 Solo VIP

```
✅ Acceso VIP Actualizado

Producto: 📓 Diario Íntimo
Nuevo acceso: 👑 Solo VIP

El estado VIP ha sido actualizado exitosamente.

[✏️ Editar Otro Campo]
[👁️ Ver Producto]
[🔙 Lista de Productos]
```

**Características:**
- ✅ Toggle en un solo click
- ✅ Confirmación visual inmediata
- ✅ Sin pasos adicionales

**Impacto:**
- Si cambias a "Solo VIP", usuarios no-VIP no verán el producto
- Si cambias a "Para Todos", todos podrán verlo

---

### 5. Editar Desbloqueo (`edit_field:unlock`)

**Paso 1: Mostrar opciones de LorePiece**
```
✏️ Editar Desbloqueo

Producto: 📓 Diario Íntimo
Desbloqueo actual: 🔓 Diario Íntimo de Diana (`diario_intimo_diana`)

Selecciona qué contenido narrativo desbloqueará este producto:

[✅ 📜 Diario Íntimo de Diana]
[🗺️ Fragmento del Mapa]
[💭 Memoria Compartida]
[🔮 Secreto Místico]
...
[❌ Sin Desbloqueo]
[🔙 Volver]
```

**Características:**
- ✅ Lista todos los `LorePiece` disponibles
- ✅ Marca con ✅ el actual
- ✅ Categoriza con emojis (fragmentos, memorias, secretos, llaves)
- ✅ Opción para quitar el desbloqueo

**Paso 2: Confirmar cambio**
```
✅ Desbloqueo Actualizado

Producto: 📓 Diario Íntimo

Antes: Diario Íntimo de Diana
Ahora: Memoria Compartida del Pasado (`memoria_compartida_01`)

El desbloqueo ha sido configurado exitosamente.
```

**Callback:** `set_unlock:{item_id}:{lore_id}` o `set_unlock:{item_id}:none`

**Validaciones:**
- Verifica que el LorePiece exista
- Permite quitar completamente el desbloqueo
- Actualiza `ShopItem.unlocks_lore_piece_id`

---

## 🎨 Estados FSM Utilizados

```python
class AdminShopStates(StatesGroup):
    # ... estados de creación ...

    editing_name = State()
    editing_description = State()
    editing_price = State()

    # No se usan estados para VIP y Unlock (interacción directa)
```

**Flujo de estados:**
```
[Menú Edición] → Selecciona campo → Estado FSM activo
                                           ↓
                        Usuario ingresa texto → Procesa y valida
                                           ↓
                        Actualiza BD → Confirmación → Limpia estado
```

---

## 📊 Comparación: Antes vs Después

| Acción | Antes (Sin Edición) | Después (Con Edición) |
|--------|--------------------|-----------------------|
| Cambiar nombre | Eliminar y recrear | Editar → Nombre |
| Cambiar precio | Eliminar y recrear | Editar → Precio |
| Cambiar VIP | Eliminar y recrear | Toggle instantáneo |
| Cambiar desbloqueo | Eliminar y recrear | Selector visual |
| Preservar ventas | ❌ Se pierden | ✅ Se mantienen |
| Tiempo requerido | 5+ pasos | 2-3 pasos |
| Historial | Se pierde | Se mantiene |

---

## 🔗 Integración con Sistema de Ventas

**Importante:** Al editar un producto, se preservan:

✅ **Historial de ventas** (`UserPurchase`)
✅ **Contenido desbloqueado** (`UserLorePiece`)
✅ **Configuración de desbloqueos** (`decision_requirements.json`)

**Ejemplo de caso de uso:**

1. **Producto original:**
   - Nombre: "📓 Diario Íntimo"
   - Precio: 30 besitos
   - Ventas: 25 usuarios

2. **Admin decide subir precio:**
   - Edita → Precio → 50 besitos
   - ✅ Los 25 usuarios que ya compraron mantienen acceso
   - ✅ Los nuevos usuarios pagan 50 besitos
   - ✅ Histórico muestra: 25 ventas × 30 besitos = 750 total

3. **Reportes actualizados:**
   - Total ventas: 27 (25 antiguas + 2 nuevas)
   - Ingresos: 750 + (2 × 50) = 850 besitos

---

## 🛡️ Validaciones y Seguridad

### Validación de Nombre
```python
# Check if name already exists (excluding current item)
existing = await session.execute(
    select(ShopItem).where(ShopItem.name == new_name, ShopItem.id != item_id)
)
if existing.scalar_one_or_none():
    await message.answer("❌ Ya existe un producto con ese nombre")
```

### Validación de Precio
```python
try:
    new_price = int(message.text.strip())
    if new_price < 0:
        return await message.answer("❌ El precio debe ser positivo")
except ValueError:
    return await message.answer("❌ Precio inválido. Ingresa un número")
```

### Validación de Permisos
```python
if not await is_admin(callback.from_user.id, session):
    return await callback.answer("Acceso denegado", show_alert=True)
```

---

## 💡 Casos de Uso

### Caso 1: Ajustar Precio por Demanda

**Escenario:** El producto se vende mucho

1. Admin → Tienda → [Producto] → ✏️ Editar
2. 💰 Precio → 80 (antes 50)
3. ✅ Confirmar

**Resultado:**
- Precio actualizado para nuevos compradores
- Histórico preservado con precio anterior
- Sin afectar a quienes ya compraron

### Caso 2: Mejorar Descripción

**Escenario:** Usuarios no entienden qué desbloquea

1. Admin → Tienda → [Producto] → ✏️ Editar
2. 📄 Descripción → "Desbloquea 15 fragmentos íntimos..."
3. ✅ Confirmar

**Resultado:**
- Descripción más clara en tienda
- Mejor conversión de ventas

### Caso 3: Hacer Producto VIP

**Escenario:** Contenido muy premium

1. Admin → Tienda → [Producto] → ✏️ Editar
2. 👑 Acceso VIP → Click
3. ✅ Confirmado

**Resultado:**
- Solo usuarios VIP ven el producto
- Usuarios free ya no lo ven en tienda
- Quienes ya compraron mantienen acceso

### Caso 4: Cambiar Contenido Desbloqueado

**Escenario:** Error en configuración inicial

1. Admin → Tienda → [Producto] → ✏️ Editar
2. 🔓 Desbloqueo → Seleccionar LorePiece correcto
3. ✅ Confirmar

**Resultado:**
- Nuevas compras desbloquean contenido correcto
- Compras anteriores mantienen lo que tenían
- Puede requerir ajuste manual para usuarios previos

---

## 🐛 Troubleshooting

### Problema: No puedo editar el nombre

**Síntoma:** Mensaje "Ya existe un producto con ese nombre"

**Causa:** Otro producto tiene ese nombre

**Solución:**
1. Verificar lista de productos
2. Elegir un nombre único
3. Agregar variante (ej: "Deluxe", "Premium", "V2")

---

### Problema: El precio no se actualiza en tienda

**Síntoma:** Los usuarios ven el precio antiguo

**Causa:** Caché del frontend o del bot

**Solución:**
1. Verificar que se guardó: Admin → Tienda → [Producto]
2. Usuario debe cerrar y abrir tienda
3. En producción: invalidar caché si existe

---

### Problema: Cambié el desbloqueo pero usuarios ya compraron

**Síntoma:** Usuarios antiguos tienen contenido incorrecto

**Causa:** El cambio solo afecta compras futuras

**Solución:**
1. **Opción A:** Dejar como está (usuarios mantienen lo que pagaron)
2. **Opción B:** Ajuste manual en base de datos:
```sql
-- Actualizar UserLorePiece para usuarios específicos
UPDATE user_lore_pieces
SET lore_piece_id = [nuevo_id]
WHERE user_id IN (
    SELECT user_id FROM user_purchases
    WHERE shop_item_id = [item_id]
) AND lore_piece_id = [viejo_id];
```

---

## 📚 Código Relevante

### Handler Principal
```python
@router.callback_query(F.data.startswith("admin_shop_edit:"))
async def admin_shop_edit_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing a shop item - show edit menu."""
```

**Ubicación:** `handlers/admin/shop_admin.py:528`

### Handlers de Campos
- `edit_field:name` → `admin_shop_edit_name()` (línea 570)
- `edit_field:description` → `admin_shop_edit_description()` (línea 645)
- `edit_field:price` → `admin_shop_edit_price()` (línea 713)
- `edit_field:vip` → `admin_shop_edit_vip_toggle()` (línea 802)
- `edit_field:unlock` → `admin_shop_edit_unlock()` (línea 847)

### Procesadores FSM
- `AdminShopStates.editing_name` → `admin_shop_edit_name_process()` (línea 599)
- `AdminShopStates.editing_description` → `admin_shop_edit_description_process()` (línea 673)
- `AdminShopStates.editing_price` → `admin_shop_edit_price_process()` (línea 746)

---

## ✅ Checklist de Edición

Antes de editar un producto, considera:

- [ ] ¿El producto ya tiene ventas?
- [ ] ¿Cambiar el nombre afectará `decision_requirements.json`?
- [ ] ¿El nuevo precio es justo?
- [ ] ¿La descripción es clara?
- [ ] ¿El cambio de VIP afecta a muchos usuarios?
- [ ] ¿El nuevo desbloqueo es coherente con el precio?

---

## 🚀 Features Adicionales Implementadas

### 1. Cálculo de Cambio Porcentual (Precio)
```python
if old_price > 0:
    change_pct = ((new_price - old_price) / old_price) * 100
    change_text = f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%"
```

**Ejemplo:**
- Precio anterior: 30 besitos
- Precio nuevo: 50 besitos
- Cambio: **+66.7%**

### 2. Indicador Visual de Selección (Desbloqueo)
```python
prefix = "✅ " if item.unlocks_lore_piece_id == lore.id else ""
```

Muestra ✅ en el LorePiece actualmente seleccionado.

### 3. Navegación Consistente
Todos los flujos de edición terminan con opciones:
- ✏️ Editar Otro Campo
- 👁️ Ver Producto
- 🔙 Lista de Productos

### 4. Preservación de Estado
El `item_id` se mantiene en FSM state para contexto completo.

---

## 📖 Referencias

- **Panel Principal:** `handlers/admin/shop_admin.py`
- **Estados FSM:** `utils/admin_state.py:196-210`
- **Guía del Panel:** `docs/admin_shop_panel_guide.md`
- **Migración JSON:** `docs/migracion_decision_requirements.md`

---

**Funcionalidad de edición implementada exitosamente** ✅

Ahora es posible editar todos los aspectos de un producto sin necesidad de eliminarlo, preservando el historial de ventas y la experiencia de usuarios que ya compraron.