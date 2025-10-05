# Flujo de Onboarding - Usuario Gratuito

## Descripción General

El flujo de onboarding para usuarios gratuitos está diseñado para convertir la espera de aprobación en una oportunidad de engagement, usando la voz de **Lucien** (el mayordomo) y **Diana** para guiar al usuario.

---

## Flujo Completo

### 1. Solicitud de Ingreso al Canal

**Trigger**: Usuario solicita unirse al canal gratuito (link público)

**Acción**: El bot registra la solicitud y envía el primer mensaje

**Mensaje (narrado por Lucien)**:
```
🎩 Bienvenido al Diván de Diana

Permítame presentarme. Soy Lucien, el mayordomo de este distinguido establecimiento.

Su solicitud para acceder al canal gratuito ha sido registrada exitosamente.

⏰ Tiempo de espera estimado: 15 minutos

Mientras tanto, permítame sugerirle algo que podría acelerar considerablemente su entrada...

💫 Diana tiene presencia en otras plataformas donde comparte contenido exclusivo.
Seguirla en sus redes sociales no solo le permitirá conocerla mejor, sino que también
demostrará su genuino interés.

Los usuarios que siguen a Diana suelen recibir una bienvenida más... personalizada.
```

**Botones**:
- 📸 Instagram → Link directo
- 🎵 TikTok → Link directo
- 🐦 Twitter/X → Link directo (opcional)
- 🔞 OnlyFans → Link directo (opcional)
- 🔄 Ver Estado → Callback para ver tiempo restante

**Objetivo**: Convertir el tiempo de espera en engagement con las redes sociales

---

### 2. Verificación de Estado (Opcional)

**Trigger**: Usuario presiona "🔄 Ver Estado"

**Acción**: El bot calcula el tiempo restante y actualiza el mensaje

**Mensajes según tiempo restante**:

**Si faltan más de 5 minutos**:
```
⏰ Estado de tu Solicitud

Tiempo transcurrido: X minutos
Tiempo restante: Y minutos

Recuerda: seguir a Diana en sus redes sociales demuestra tu interés genuino.

¿Ya la sigues en todas sus plataformas?
```

**Si faltan menos de 5 minutos**:
```
⏰ ¡Casi listo!

Tiempo restante: aproximadamente Y minutos.

Prepárate para la bienvenida de Diana...
```

**Si ya es hora de aprobación**:
```
⏰ Tu solicitud está siendo procesada. Serás aprobado en cualquier momento.
```

**Botones**:
- 📸 Instagram
- 🎵 TikTok
- 🔄 Actualizar Estado

---

### 3. Aprobación y Bienvenida

**Trigger**: Han transcurrido los minutos configurados (default: 15)

**Acción**:
1. El bot aprueba automáticamente la solicitud en Telegram
2. Envía mensaje de bienvenida dual (Lucien + Diana)

**Mensaje de bienvenida**:
```
🎉 ¡Excelente noticia!

[Nombre del usuario], su solicitud ha sido aprobada.

Ya tiene acceso completo al canal gratuito del Diván de Diana.

Ahora, permítame presentarle formalmente a la dueña de este establecimiento...

---

🌸 Diana te da la bienvenida

Hola, mi kinky. Qué emoción que estés aquí.

Este es mi espacio, donde lo especial sucede. Aquí encontrarás contenido gratuito,
pero también... mucho más.

Si quieres conocerme de verdad, tienes dos opciones:

💎 Modo VIP: Acceso completo a todo mi contenido sin censura, videos explícitos,
historias diarias y descuentos especiales.

📖 La Historia: Una experiencia narrativa única donde tus decisiones importan.
Gana besitos, desbloquea contenido y descubre secretos.

---

🎩 Lucien nuevamente

¿Por dónde desea comenzar su experiencia en el Diván?

Use el menú principal del bot para explorar todas las opciones disponibles.
```

**Botones**:
- 📖 Comenzar la Historia
- 💎 Ver Membresía VIP
- 🎁 Contenido Gratuito

---

## Configuración

### Enlaces de Redes Sociales

Los enlaces se configuran en `/utils/onboarding_messages.py`:

```python
DEFAULT_SOCIAL_LINKS = {
    'instagram': 'https://instagram.com/dianakinky',
    'tiktok': 'https://tiktok.com/@dianakinky',
    'twitter': 'https://twitter.com/dianakinky',
    'onlyfans': 'https://onlyfans.com/dianakinky'
}
```

### Tiempo de Espera

Se configura desde el panel de administrador:

1. Admin → Gestionar Canal Gratuito
2. Configurar Tiempo de Espera
3. Ingresar minutos (default: 15)

---

## Arquitectura Técnica

### Archivos Involucrados

1. **`utils/onboarding_messages.py`**
   - Contiene todos los mensajes del flujo
   - Funciones para generar mensajes dinámicos
   - Configuración de enlaces sociales

2. **`services/free_channel_service.py`**
   - Lógica de negocio para solicitudes de canal
   - Procesa aprobaciones automáticas
   - Envía mensajes de onboarding

3. **`handlers/channel_access.py`**
   - Handler para solicitudes de ingreso (`@router.chat_join_request()`)
   - Handler para botón "Ver Estado" (`check_join_status`)

4. **`database/models.py`**
   - `PendingChannelRequest`: Almacena solicitudes pendientes
   - `BotConfig`: Guarda tiempo de espera configurado

### Base de Datos

**Tabla**: `pending_channel_requests`
```sql
- user_id: BigInteger (FK)
- chat_id: BigInteger (ID del canal)
- request_timestamp: DateTime (momento de la solicitud)
- approved: Boolean (False = pendiente, True = aprobado)
```

**Tabla**: `bot_config`
```sql
- id: Integer (PK)
- free_channel_wait_time_minutes: Integer (tiempo de espera)
```

---

## Scheduler de Procesamiento

Un scheduler corre cada 2 minutos revisando solicitudes pendientes:

```python
# En services/scheduler.py
async def free_channel_cleanup_scheduler(bot, session_factory):
    while True:
        await asyncio.sleep(120)  # Cada 2 minutos
        # Procesa solicitudes que cumplieron el tiempo de espera
        await free_channel_service.process_pending_requests()
```

---

## Personalización Futura

### Ideas para Mejorar el Onboarding

1. **Verificación de Follow**:
   - Integrar APIs de Instagram/TikTok
   - Reducir tiempo de espera si el usuario siguió en redes

2. **Mini-juego Durante la Espera**:
   - Quiz sobre Diana
   - Gana besitos extra antes de entrar

3. **Contenido Teaser**:
   - Enviar imágenes/videos de muestra durante la espera
   - Aumentar anticipación

4. **Segmentación**:
   - Diferentes mensajes según origen del usuario
   - Personalizar según idioma/región

---

## Testing

Para probar el flujo completo:

1. **Reducir tiempo de espera a 1 minuto** (para pruebas rápidas)
   ```bash
   # En el panel de admin
   Admin → Canal Gratuito → Configurar: 1 minuto
   ```

2. **Crear cuenta de prueba**
   - Usar otro número de teléfono
   - Solicitar unirse al canal gratuito

3. **Verificar mensajes**:
   - ✅ Mensaje inicial con enlaces sociales
   - ✅ Botón "Ver Estado" funciona
   - ✅ Aprobación automática después de 1 minuto
   - ✅ Mensaje de bienvenida dual (Lucien + Diana)

4. **Restaurar tiempo real**
   ```bash
   Admin → Canal Gratuito → Configurar: 15 minutos
   ```

---

## Métricas a Trackear

- **Conversion Rate**: % de usuarios que siguen en redes sociales
- **Time to First Action**: Tiempo desde aprobación hasta primera acción en el bot
- **Drop-off Rate**: % de usuarios que se van durante la espera
- **Engagement Score**: Interacciones con botones de estado

---

## Soporte

Para modificar los mensajes o personalizar el flujo, contacta al desarrollador o consulta la documentación técnica en `/docs`.
