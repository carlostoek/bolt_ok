# 🚀 Journey System - Quick Start

## ⚡ Setup Rápido (5 minutos)

### **1. Crear los Content Sets Base**

Ejecuta este comando UNA SOLA VEZ:

```bash
python scripts/create_default_journey_content.py
```

Esto crea 3 content sets vacíos:
- ✅ `day_1_welcome` (obligatorio)
- ⚙️ `day_7_vip_teaser` (opcional)
- ⚙️ `day_30_vip_gift` (opcional)

**IMPORTANTE:** Los sets están vacíos (sin fotos/videos). El sistema funcionará igual, **solo enviará los mensajes narrativos**.

---

### **2. Subir Contenido (Desde el Bot)**

Para agregar fotos/videos a los sets:

1. `/admin`
2. Gestión de Contenido
3. 📦 CMS Journey
4. 📋 Ver Sets
5. Seleccionar el set (ej: `day_1_welcome`)
6. Presionar "✏️ Editar"
7. Subir archivos nuevos

**O simplemente crear uno nuevo:**

1. 📦 CMS Journey
2. 📤 Subir Nuevo Set
3. ID: `day_1_welcome` (reemplazar el vacío)
4. Subir tus fotos/videos

---

### **3. Probar el Journey**

**Test Manual:**

1. `/admin`
2. Gestión de Contenido
3. 📦 CMS Journey
4. 🎯 Journey Management
5. 🧪 Test Milestone
6. Seleccionar Day 1/7/30
7. Ingresar tu user_id (o el de un usuario de prueba)

**¡Listo!** Deberías recibir el milestone inmediatamente.

---

## ❓ FAQ - Problemas Comunes

### **"Error: Content set no encontrado: day_1_welcome"**

**Solución:** Ejecuta el script de creación:
```bash
python scripts/create_default_journey_content.py
```

---

### **"Recibo el mensaje pero sin fotos/videos"**

**Es normal!** El sistema es tolerante a errores:
- Si el content set no tiene archivos → Envía solo el mensaje
- Si el content set no existe → Envía solo el mensaje
- El milestone se marca como completado de todas formas

Para agregar contenido: Sigue el paso 2 (Subir Contenido)

---

### **"¿Cómo sé si el journey está funcionando?"**

Verifica los logs:
```bash
tail -f bot.log | grep "milestone"
```

Deberías ver cada hora:
```
Journey milestones processed - Day 1: X, Day 7: Y, Day 30: Z
```

O revisa las estadísticas:
```
/admin → CMS Journey → Journey Management → 📊 Estadísticas
```

---

### **"¿Puedo cambiar los mensajes narrativos?"**

Sí! Edita directamente en:
```
services/user_journey_service.py
```

Busca las secciones:
- `process_day_1_milestone` → Mensaje Day 1
- `process_day_7_milestone` → Mensaje Day 7
- `process_day_30_milestone` → Mensajes Day 30

---

### **"¿Cuándo se envían los milestones?"**

**Automáticamente** cada hora, el scheduler verifica:
- Usuarios registrados hace 1+ día → Day 1
- Usuarios registrados hace 7+ días → Day 7
- Usuarios registrados hace 30+ días → Day 30

**Manual:** Usa el Test Milestone desde el admin panel.

---

## 🎯 Content Sets Recomendados

### **Day 1 (Obligatorio):**
- **Tipo:** Set de fotos (3-5 fotos)
- **Contenido:** Teasers suaves, primera impresión
- **Objetivo:** Hook inicial, mantener interés

### **Day 7 (Opcional):**
- **Tipo:** Set de fotos (2-3 fotos)
- **Contenido:** Preview de contenido VIP
- **Objetivo:** Generar FOMO, impulsar conversión

### **Day 30 (Opcional - VIP only):**
- **Tipo:** Set de fotos/video (1-3 archivos)
- **Contenido:** Regalo especial para agradecer
- **Objetivo:** Retención de VIPs

---

## 🔥 Pro Tips

### **Tip 1: Testea antes de lanzar**
```
1. Crea los content sets con TU contenido real
2. Usa Test Milestone con TU user_id
3. Verifica que todo se vea bien
4. Ahora sí, deja que el scheduler trabaje automáticamente
```

### **Tip 2: Empieza simple**
No necesitas los 3 content sets desde el día 1:
- **Mínimo viable:** Solo `day_1_welcome` con mensaje
- **Siguiente paso:** Agregar fotos a day_1
- **Optimización:** Agregar day_7 teaser cuando tengas métricas

### **Tip 3: Monitorea conversiones**
Revisa las estadísticas semanalmente:
```
/admin → Journey Management → 📊 Estadísticas

Pregunta clave:
¿Cuántos usuarios completaron Day 7 vs cuántos se convirtieron a VIP?
```

---

## ✅ Checklist Post-Setup

Después de ejecutar el script:

- [ ] Los 3 content sets existen en la BD
- [ ] El bot se reinició correctamente
- [ ] Test manual de Day 1 funciona (con o sin fotos)
- [ ] Los logs muestran "Journey milestones processed" cada hora
- [ ] (Opcional) Subiste contenido real a `day_1_welcome`

**¡Ya está todo listo!** El journey funcionará automáticamente. 🎉

---

## 📞 Soporte

Si algo no funciona:

1. **Revisa los logs:**
   ```bash
   tail -f bot.log | grep -E "(milestone|journey)"
   ```

2. **Fuerza el procesamiento:**
   ```
   /admin → Journey Management → ▶️ Forzar Procesamiento
   ```

3. **Verifica la BD:**
   ```bash
   sqlite3 bot.db
   > SELECT * FROM content_sets;
   > SELECT * FROM user_milestones LIMIT 10;
   ```

Si nada funciona, el sistema seguirá enviando los mensajes narrativos (sin contenido multimedia). Los usuarios no se quedarán sin respuesta. ✅
