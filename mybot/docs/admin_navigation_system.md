# Sistema de Navegación de Menús de Administrador

**Fecha:** 30 de septiembre de 2025

Este documento explica el sistema de navegación "limpia" implementado para los menús de administrador, donde todos los menús se mantienen en un solo mensaje que se edita en lugar de enviar mensajes nuevos.

## Objetivo

Mantener el chat limpio editando el mismo mensaje del menú en lugar de enviar nuevos mensajes cada vez que el administrador navega entre opciones. Esto proporciona una experiencia de usuario más profesional y ordenada.

## Componentes Principales

### 1. `utils/menu_utils.py`

Contiene las funciones centrales para la navegación:

- **`update_menu(callback, text, reply_markup, session, state)`**: Función principal que edita el mensaje del menú existente. Mantiene un caché del mensaje actual para cada usuario.
- **`send_menu(message, text, reply_markup, session, state)`**: Envía o actualiza un menú desde un comando (no callback).
- **`MENU_CACHE`**: Diccionario que almacena el mensaje actual del menú para cada usuario `{user_id: (chat_id, message_id)}`.

### 2. `utils/menu_factory.py`

El `MenuFactory` centraliza la creación de menús basados en el estado y rol del usuario. Todos los menús de admin están diseñados para ser editados in-place.

**Métodos clave:**
- `create_menu(menu_state, user_id, session, bot)`: Retorna tupla `(text, keyboard)` para el estado solicitado.

### 3. Handlers de Admin

Todos los callbacks de admin deben usar `update_menu()` para mantener la navegación limpia.

**Ejemplo correcto:**
```python
@router.callback_query(F.data == "admin_vip")
async def vip_menu(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    text, keyboard = await menu_factory.create_menu(
        "admin_vip", callback.from_user.id, session, bot
    )
    await update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_vip",
    )
    await callback.answer()
```

## Flujo de Navegación

1. **Usuario hace clic en un botón del menú** → Genera un `CallbackQuery`
2. **Handler recibe el callback** → Obtiene el texto y teclado del `MenuFactory`
3. **Llama a `update_menu()`** → Edita el mensaje existente con el nuevo contenido
4. **Actualiza el caché** → Guarda la referencia al mensaje editado
5. **Usuario ve el menú actualizado** → Sin mensajes nuevos en el chat

## Casos Especiales

### Estados FSM (Formularios)

Cuando se solicita input del usuario (FSM states), también se debe usar `update_menu()`:

```python
@router.callback_query(F.data.startswith("admin_user_add_"))
async def admin_user_add(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await update_menu(
        callback,
        f"Ingresa la cantidad de puntos a sumar:",
        get_back_kb("admin_manage_users"),
        session,
        "admin_user_add_points"
    )
    await state.set_state(AdminUserStates.assigning_points_amount)
```

### Mensajes de Información Adicional

Algunos casos requieren enviar mensajes adicionales (ej. mostrar perfil de usuario completo). Estos están permitidos usando `callback.message.answer()` pero solo para información complementaria, **nunca para navegación de menús**.

## Beneficios

1. **Chat limpio**: El administrador no ve un historial lleno de menús antiguos.
2. **Mejor UX**: Navegación fluida similar a una aplicación nativa.
3. **Fácil de encontrar**: El menú actual siempre está en el último mensaje del bot.
4. **Menos spam**: No se crean docenas de mensajes al navegar.

## Convenciones

- ✅ **USAR** `update_menu()` para navegación entre menús
- ✅ **USAR** `update_menu()` para prompts de input (FSM)
- ❌ **NO USAR** `callback.message.answer()` para navegación
- ✅ **PERMITIDO** `callback.message.answer()` solo para información adicional específica

## Mantenimiento

Al agregar nuevos menús o callbacks de admin:

1. Importar `update_menu` desde `utils.menu_utils`
2. Usar `menu_factory.create_menu()` para obtener contenido
3. Llamar a `update_menu()` en lugar de `edit_text()` o `answer()`
4. Asegurarse de que el callback incluya el parámetro `session: AsyncSession`

## Ejemplo Completo

```python
from utils.menu_utils import update_menu
from utils.menu_factory import menu_factory

@router.callback_query(F.data == "admin_custom_menu")
async def custom_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text, keyboard = await menu_factory.create_menu(
        "admin_custom_menu",
        callback.from_user.id,
        session,
        callback.bot
    )

    await update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_custom_menu"
    )
    await callback.answer()
```

## Archivos Relacionados

- `utils/menu_utils.py` - Funciones de navegación
- `utils/menu_factory.py` - Creador centralizado de menús
- `handlers/admin/admin_menu.py` - Menú principal de admin
- `handlers/admin/vip_menu.py` - Gestión de canal VIP
- `handlers/admin/free_menu.py` - Gestión de canal gratuito
- `handlers/admin/game_admin.py` - Gestión de gamificación