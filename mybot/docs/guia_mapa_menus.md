# Guía Rápida de Archivos de Menús (Administrador)

Este documento resume los archivos clave que generan los menús de administración.

## 1. Panel Principal de Administrador

- **Descripción**: Es el primer menú que ve un administrador al usar `/start`.
- **Archivo del Teclado**: `keyboards/admin_main_kb.py`
- **Función Clave**: `get_admin_main_kb()`
- **Activación**: Se dispara desde `handlers/start.py`, que a su vez utiliza `utils/menu_factory.py` para decidir qué menú mostrar.
- **Patrón**: `Handler -> Factory -> Builder` (Consistente).

## 2. Submenú "Canal VIP"

- **Descripción**: Menú para gestionar las opciones del canal de pago.
- **Archivo del Teclado**: `keyboards/admin_vip_channel_kb.py`
- **Función Clave**: `get_admin_vip_channel_kb()`
- **Activación**: Se dispara desde `handlers/admin/vip_menu.py` en respuesta al callback `admin_vip`.
- **Patrón**: `Handler -> Factory -> Builder` (Consistente).

## 3. Submenú "Canal Free"

- **Descripción**: Menú para gestionar las opciones del canal gratuito.
- **Archivo del Teclado**: `keyboards/free_channel_admin_kb.py`
- **Función Clave**: `get_free_channel_admin_kb()`
- **Activación**: Se dispara desde `handlers/admin/free_menu.py` en respuesta al callback `admin_free`.
- **Patrón**: `Handler -> Factory -> Builder` (Consistente).

## 4. Submenú "Gestión de Gamificación"

- **Descripción**: Panel para administrar las funciones de gamificación (misiones, insignias, etc.). Accedido a través del botón "Juego Kinky" en el menú principal de admin.
- **Archivos de Teclado Recientes**: 
  - `keyboards/admin_manage_content_kb.py`
  - `keyboards/admin_content_missions_kb.py`
  - `keyboards/admin_content_badges_kb.py`
  - `keyboards/admin_content_levels_kb.py`
- **Funciones Clave**: `get_admin_manage_content_keyboard()`, etc.
- **Activación**: Se dispara desde `handlers/admin/game_admin.py` y `handlers/admin/admin_menu.py`.
- **Patrón**: `Handler -> Builder` (Inconsistente). Este es uno de los sistemas de menús que necesita ser refactorizado para usar `MenuFactory` y centralizar la lógica, como se detalla en `docs/refactoring_report.md`.