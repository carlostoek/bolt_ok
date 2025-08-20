# Diana Menu System

## Descripción General

El Diana Menu System es un sistema avanzado de menús diseñado para proporcionar una interfaz unificada entre todos los módulos del bot:

- **Administración**: Gestión completa del sistema y configuración
- **Gamificación**: Puntos, misiones, logros y niveles
- **Narrativa**: Storytelling interactivo y contenido VIP

El sistema se integra con el CoordinadorCentral para flujos de trabajo complejos entre módulos y utiliza el EventBus para comunicación asíncrona.

## Arquitectura

El Diana Menu System está compuesto por los siguientes componentes principales:

1. **Sistema Principal** (`diana_menu_system.py`):
   - Clase `DianaMenuSystem` que orquesta la creación de menús y la interacción con módulos especializados

2. **Módulo de Integración** (`diana_menu_integration_impl.py`):
   - Proporciona puntos de conexión entre el Diana Menu System y los handlers existentes
   - Implementa un router dedicado y puentes de compatibilidad

3. **Módulos de Menú Especializados**:
   - `admin_menu.py`: Para administración del sistema
   - `user_menu.py`: Para interfaz general de usuario
   - `narrative_menu.py`: Para storytelling interactivo
   - `gamification_menu.py`: Para características de gamificación

4. **Handler Dedicado** (`diana_handler.py`):
   - Define comandos y callbacks específicos para Diana
   - Implementa estrategias de fallback para integración gradual

## Integración con Sistema Existente

El Diana Menu System se ha integrado con el sistema existente siguiendo estas pautas:

1. **Integración No Intrusiva**:
   - El sistema existente sigue funcionando sin cambios
   - Diana se activa solo cuando se solicita explícitamente o en áreas específicas

2. **Estrategia de Fallback**:
   - Se intenta primero usar Diana para ciertos estados y callbacks
   - Si falla, se recurre al sistema existente

3. **Comandos Dedicados**:
   - `/diana`: Acceso al menú principal de Diana
   - `/diana_admin`: Acceso directo al panel administrativo de Diana

4. **Monitoreo de Salud**:
   - Tarea programada que verifica el estado del sistema Diana
   - Envía alertas si hay problemas

## Uso para Desarrolladores

### Activación del Sistema Diana

El sistema Diana se activa automáticamente durante el arranque del bot si está disponible. No se requiere ninguna configuración adicional.

### Navegación entre Sistemas

La navegación entre el sistema existente y Diana es transparente para el usuario. Los desarrolladores pueden:

1. **Usar el Puente de Compatibilidad**:
   ```python
   from services.diana_menu_integration_impl import get_compatibility_bridge
   
   async def my_handler(callback: CallbackQuery, session: AsyncSession):
       # Intentar con Diana primero
       diana_bridge = get_compatibility_bridge(session)
       handled = await diana_bridge.bridge_user_menu(callback)
       
       # Si Diana no lo manejó, usar sistema existente
       if not handled:
           # Lógica existente aquí
   ```

2. **Verificar Estado de Diana**:
   ```python
   from handlers.diana_handler import report_system_status
   
   async def check_status(message: Message, session: AsyncSession):
       status = await report_system_status(message.bot, session)
       # Usar status para diagnóstico
   ```

### Extendiendo el Sistema Diana

Para añadir nuevas funcionalidades al Diana Menu System:

1. **Añadir Nuevos Estados de Menú**:
   - Crear métodos en los módulos especializados correspondientes
   - Actualizar los handlers de callbacks en `diana_menu_system.py`

2. **Añadir Nuevos Comandos**:
   - Registrar nuevos handlers en `diana_handler.py`

3. **Integración con Eventos**:
   - Suscribir a eventos relevantes en `diana_menu_integration_impl.py`

## Transición Gradual

Se recomienda seguir estos pasos para una transición completa al Diana Menu System:

1. **Fase 1**: Usar comandos específicos de Diana (/diana, /diana_admin)
2. **Fase 2**: Migrar características específicas (ej. panel de misiones, narrativa)
3. **Fase 3**: Integración completa en menús principales
4. **Fase 4**: Refactorización para usar Diana como sistema principal

## Solución de Problemas

Si encuentras problemas con el Diana Menu System:

1. **Verificar Logs**:
   - Los logs de Diana tienen el prefijo "Diana" para fácil identificación

2. **Comprobar Estado**:
   - Usar `report_system_status()` para verificar el estado del sistema

3. **Fallback Manual**:
   - Configurar `DIANA_ENABLED = False` en `menu_factory.py` para desactivar temporalmente

4. **Reiniciar Sistema**:
   - Reiniciar el bot para reinicializar el sistema Diana

## Contribución

Al contribuir al Diana Menu System, asegúrate de:

1. Seguir la arquitectura existente
2. Mantener la estrategia de integración no intrusiva
3. Implementar manejo de errores robusto
4. Mantener la documentación actualizada