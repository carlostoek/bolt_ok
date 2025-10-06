# Guía de Imágenes en Productos - Mejora #3

**Fecha:** 30 de septiembre de 2025
**Mejora:** #3 - Agregar campo de imagen opcional para productos
**Estado:** ✅ Completado

---

## 📋 Resumen

Se implementó soporte completo para imágenes opcionales en productos de la tienda. Los productos pueden tener imágenes asociadas, pero funcionan perfectamente sin ellas (productos conceptuales).

---

## 🎯 Características Implementadas

### 1. **Campo de Imagen en Base de Datos**

**Modelo actualizado:** `database/models.py:481`

```python
class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    is_vip_only = Column(Boolean, default=False)
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    image_file_id = Column(String(255), nullable=True)  # 🆕 Nuevo campo opcional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
```

**Características:**
- ✅ Campo completamente **opcional** (nullable=True)
- ✅ Almacena el `file_id` de Telegram
- ✅ Productos funcionan sin imagen
- ✅ Compatible con SQLite

---

## 🔧 Flujo de Creación de Producto con Imagen

### Paso 5: Imagen del Producto (Opcional)

**Después de configurar VIP**, el admin ve:

```
➕ Crear Producto

✅ Nombre: 📓 Diario Íntimo
✅ Precio: 30 besitos
✅ Acceso: 🆓 Para Todos

🖼️ Paso 5: Imagen del Producto (Opcional)

¿Deseas agregar una imagen para este producto?
(Los productos pueden funcionar sin imagen)

[📸 Sí, agregar imagen]
[⏭️ Omitir (sin imagen)]
```

### Opción A: Agregar Imagen

**1. Admin elige "📸 Sí, agregar imagen"**

```
➕ Crear Producto

🖼️ Enviar Imagen del Producto

Por favor, envía una imagen para este producto.

💡 Tips:
• Formatos soportados: JPG, PNG, GIF
• Tamaño recomendado: máximo 5MB
• La imagen se mostrará en la tienda

⚠️ Envía la imagen como foto (no como archivo)

[❌ Cancelar]
```

**2. Admin envía foto**

Bot captura el `file_id` automáticamente y continúa:

```
➕ Crear Producto

✅ Nombre: 📓 Diario Íntimo
✅ Precio: 30 besitos
✅ Acceso: 🆓 Para Todos
✅ Imagen: Recibida ✓

🔓 Paso 6: Desbloqueo de Contenido

¿Este producto desbloquea contenido narrativo?
```

### Opción B: Omitir Imagen

**Admin elige "⏭️ Omitir (sin imagen)"**

```
➕ Crear Producto

✅ Nombre: 📓 Diario Íntimo
✅ Precio: 30 besitos
✅ Acceso: 🆓 Para Todos
✅ Imagen: Sin imagen

🔓 Paso 6: Desbloqueo de Contenido

¿Este producto desbloquea contenido narrativo?
```

---

## ✏️ Edición de Imágenes

### Menú de Edición Actualizado

**Ruta:** Admin → Tienda → [Producto] → ✏️ Editar

```
✏️ Editar Producto

Producto: 📓 Diario Íntimo

¿Qué deseas editar?

[📝 Nombre]        [📄 Descripción]
[💰 Precio]        [👑 Acceso VIP]
[🖼️ Imagen]        [🔓 Desbloqueo]      🆕 Nueva opción
[🔙 Volver]
```

### Gestión de Imágenes

**1. Producto SIN imagen:**

```
✏️ Editar Imagen

Producto: 📓 Diario Íntimo
Estado actual: ❌ Sin imagen

Opciones:

[➕ Agregar Imagen]
[🔙 Volver]
```

**2. Producto CON imagen:**

```
✏️ Editar Imagen

Producto: 📓 Diario Íntimo
Estado actual: ✅ Tiene imagen

Opciones:

[👁️ Ver Imagen Actual]
[🔄 Cambiar Imagen]
[🗑️ Eliminar Imagen]
[🔙 Volver]
```

### Acciones Disponibles

#### Ver Imagen Actual
- Envía la imagen al chat del admin
- Útil para verificar qué imagen está configurada

#### Cambiar Imagen
- Solicita una nueva foto
- Reemplaza la imagen anterior
- El `file_id` viejo se pierde (Telegram maneja esto)

#### Eliminar Imagen
- Quita la imagen del producto
- Producto vuelve a ser "conceptual"
- Confirmación inmediata

#### Agregar Imagen
- Disponible solo si no hay imagen
- Mismo flujo que en creación

---

## 🛒 Visualización en Tienda

### Para Usuarios

Cuando un usuario accede a la tienda (`/shop` o botón), el bot:

**1. Envía galería de imágenes** (si existen productos con imagen)

```
[Galería de fotos]
📓 Diario Íntimo - 30 besitos
🔮 Cristal Místico - 50 besitos
```

**2. Luego muestra el menú de compra**

```
🛒 Tienda - Elige un artículo:

[📓 Diario Íntimo - 30 besitos]
[🔮 Cristal Místico - 50 besitos]
[📖 Diario Secreto - 25 besitos]  ← Sin imagen
[🔙 Volver]
```

**Características:**
- ✅ Productos sin imagen aparecen en el menú normalmente
- ✅ Máximo 10 imágenes en galería (límite de Telegram)
- ✅ Galería solo se envía si hay al menos 1 producto con imagen

---

## 🔄 Migración de Base de Datos

### Migración Automática

**Al iniciar el bot**, SQLAlchemy detecta el nuevo campo y:
- ✅ Agrega la columna `image_file_id` automáticamente
- ✅ Los productos existentes quedan con `NULL` (sin imagen)
- ✅ No se requiere intervención manual

### Migración Manual (Opcional)

Si prefieres ejecutar la migración manualmente:

```bash
cd /home/azureuser/repos/bolt_ok/mybot
export BOT_TOKEN="tu_token_aqui"
python migrations/add_image_to_shop_items.py
```

**Salida esperada:**

```
============================================================
Starting migration: Add image_file_id to shop_items
============================================================
Adding 'image_file_id' column to 'shop_items' table...
✅ Successfully added 'image_file_id' column to 'shop_items' table
✅ Migration verified successfully
============================================================
✅ Migration completed successfully!
============================================================

Next steps:
  1. Restart the bot
  2. Products can now have optional images
  3. Use Admin → Tienda → Create/Edit to manage images
```

---

## 📊 Casos de Uso

### Caso 1: Producto Visual (con imagen)

**Ejemplo:** Artwork, foto de recompensa física

```
Producto: 🎨 Artwork Exclusivo de Diana
Precio: 100 besitos
Imagen: ✅ Sí (preview del artwork)
```

**Beneficio:** Usuarios ven exactamente qué están comprando

### Caso 2: Producto Conceptual (sin imagen)

**Ejemplo:** Contenido narrativo, acceso especial

```
Producto: 📓 Diario Íntimo
Precio: 30 besitos
Imagen: ❌ No (es un concepto narrativo)
```

**Beneficio:** No requiere crear imágenes innecesarias

### Caso 3: Producto Mixto

**Escenario:** Inicialmente sin imagen, luego se agrega

1. **Creación inicial:**
   - Admin crea producto sin imagen
   - Producto funciona normalmente

2. **Después de un tiempo:**
   - Admin crea artwork para el producto
   - Admin → Tienda → [Producto] → ✏️ Editar → 🖼️ Imagen → ➕ Agregar
   - Usuarios ahora ven imagen en tienda

---

## 🔍 Detalles Técnicos

### Almacenamiento de Imágenes

**Telegram File ID:**
- No se sube la imagen al servidor
- Solo se guarda el `file_id` de Telegram
- Telegram almacena la imagen en sus servidores
- `file_id` es un string único (ej: `AgACAgIAAxkBAAI...`)

**Ventajas:**
- ✅ Cero espacio en disco local
- ✅ Telegram maneja la compresión
- ✅ Acceso rápido (CDN de Telegram)
- ✅ Backups automáticos

**Consideraciones:**
- ⚠️ `file_id` es único por bot
- ⚠️ Si cambias de bot, necesitas resubir imágenes
- ⚠️ Telegram puede invalidar `file_id` muy antiguos (raro)

### Validación de Imágenes

**En creación/edición:**
- ✅ Solo acepta fotos (`F.photo` filter)
- ✅ Rechaza documentos/archivos
- ✅ Captura el tamaño más grande automáticamente
- ✅ Sin límite de dimensiones (Telegram lo maneja)

**Formatos soportados:**
- JPG/JPEG
- PNG
- GIF (estático o animado)

### Estructura de Datos

**En CoordinadorCentral:**

```python
items_data.append({
    'id': item.id,
    'name': item.name,
    'price': item.price,
    'is_vip_only': item.is_vip_only,
    'image_file_id': item.image_file_id  # 🆕 Incluido en respuesta
})
```

**En shop_handlers.py:**

```python
# Filtrar productos con imagen
items_with_images = [item for item in items if item.get('image_file_id')]

# Crear galería
if items_with_images:
    media_group = [
        InputMediaPhoto(
            media=item['image_file_id'],
            caption=f"{item['name']} - {item['price']} besitos"
        )
        for item in items_with_images[:10]
    ]
    await callback.message.answer_media_group(media=media_group)
```

---

## 🐛 Troubleshooting

### Problema: La imagen no se muestra en tienda

**Síntomas:**
- Imagen subida exitosamente en admin
- No aparece en tienda para usuarios

**Diagnóstico:**

1. Verificar que el producto está activo:
   ```
   Admin → Tienda → [Producto] → Ver detalles
   Estado: ✅ Activo
   ```

2. Verificar que tiene `file_id`:
   ```python
   # En base de datos
   SELECT name, image_file_id FROM shop_items WHERE id = X;
   ```

3. Verificar logs:
   ```bash
   tail -f logs/bot.log | grep "Shop access"
   ```

**Soluciones:**
- Si `file_id` es NULL → Editar → Agregar imagen nuevamente
- Si producto inactivo → Activar desde admin panel
- Si error en logs → Verificar permisos del bot

---

### Problema: "Invalid file_id" en tienda

**Síntomas:**
- Error al mostrar imagen
- Telegram responde "File not found"

**Causas:**
- `file_id` muy antiguo (meses/años)
- Imagen subida con otro bot
- Telegram invalidó el archivo

**Solución:**
```
Admin → Tienda → [Producto] → ✏️ Editar → 🖼️ Imagen → 🔄 Cambiar Imagen
```

Subir la imagen nuevamente.

---

### Problema: Imagen incorrecta

**Síntoma:** Producto muestra imagen de otro producto

**Causa:** Probablemente error al copiar/pegar `file_id`

**Solución:**
```
Admin → Tienda → [Producto] → ✏️ Editar → 🖼️ Imagen → 🔄 Cambiar Imagen
```

---

## ✅ Checklist de Implementación

Funcionalidades completadas:

- [x] Agregar campo `image_file_id` a modelo ShopItem
- [x] Crear estado FSM `uploading_image` para creación
- [x] Crear estado FSM `editing_image` para edición
- [x] Implementar paso opcional de imagen en creación
- [x] Implementar opción "Omitir imagen"
- [x] Implementar menú de edición de imagen
- [x] Implementar "Ver imagen actual"
- [x] Implementar "Cambiar imagen"
- [x] Implementar "Eliminar imagen"
- [x] Implementar "Agregar imagen" (cuando no tiene)
- [x] Actualizar CoordinadorCentral para incluir `image_file_id`
- [x] Actualizar shop_handlers para mostrar galería
- [x] Crear script de migración
- [x] Documentar funcionalidad completa
- [x] Verificar que productos sin imagen funcionan
- [x] Verificar límite de 10 imágenes en galería

---

## 📚 Referencias de Código

### Archivos Modificados

1. **`database/models.py:481`**
   - Agregado: `image_file_id = Column(String(255), nullable=True)`

2. **`utils/admin_state.py:202-209`**
   - Agregado: `uploading_image = State()`
   - Agregado: `editing_image = State()`

3. **`handlers/admin/shop_admin.py`**
   - Modificado: `admin_shop_create_vip()` - Ahora pregunta por imagen
   - Agregado: `admin_shop_create_skip_image()` - Omitir imagen
   - Agregado: `admin_shop_create_request_image()` - Solicitar imagen
   - Agregado: `admin_shop_create_receive_image()` - Recibir foto
   - Modificado: Ambos handlers de creación incluyen `image_file_id`
   - Modificado: `admin_shop_edit_start()` - Incluye botón de imagen
   - Agregado: `admin_shop_edit_image_start()` - Menú edición imagen
   - Agregado: `admin_shop_view_image()` - Ver imagen actual
   - Agregado: `admin_shop_add_image()` - Agregar imagen
   - Agregado: `admin_shop_change_image()` - Cambiar imagen
   - Agregado: `admin_shop_remove_image()` - Eliminar imagen
   - Agregado: `admin_shop_edit_image_receive()` - Recibir nueva imagen

4. **`services/coordinador_central.py:727`**
   - Modificado: `_flujo_acceder_tienda()` - Incluye `image_file_id` en items_data

5. **`handlers/shop_handlers.py:30-51`**
   - Modificado: `show_shop()` - Envía galería de imágenes si existen

### Archivos Nuevos

1. **`migrations/add_image_to_shop_items.py`**
   - Script de migración para agregar columna

2. **`docs/admin_shop_image_feature.md`** (este archivo)
   - Documentación completa de la funcionalidad

---

## 🚀 Próximas Mejoras Posibles

### Mejora Futura 1: Múltiples Imágenes por Producto
```python
# En lugar de image_file_id (string)
image_file_ids = Column(JSON, default=[])  # Lista de file_ids
```

### Mejora Futura 2: Categorías de Productos con Imágenes
```python
category_image = Column(String(255), nullable=True)
```

### Mejora Futura 3: Preview en Admin Panel
```python
# Al ver producto en admin, mostrar la imagen
if item.image_file_id:
    await bot.send_photo(...)
```

---

**Funcionalidad de imágenes implementada exitosamente** ✅

Los productos ahora soportan imágenes opcionales sin afectar el funcionamiento de productos conceptuales.
