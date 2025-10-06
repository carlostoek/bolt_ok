"""
Shop unlock configuration - Manage decision_requirements mapping.
This module handles the configuration of which shop items unlock which narrative decisions.
"""
import logging
import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from utils.admin_state import AdminShopStates
from keyboards.common import get_back_kb
from database.models import ShopItem

logger = logging.getLogger(__name__)
router = Router()

# Path to the decision requirements configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "decision_requirements.json"


def load_decision_requirements() -> dict:
    """Load decision requirements from JSON file."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Initialize with existing requirements from coordinador_central.py
        default_config = {
            "1": "📖 Diario Secreto",
            "15": "📓 Diario Íntimo"
        }
        save_decision_requirements(default_config)
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading decision requirements: {e}")
        return {}


def save_decision_requirements(requirements: dict) -> bool:
    """Save decision requirements to JSON file."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(requirements, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving decision requirements: {e}")
        return False


@router.callback_query(F.data == "admin_shop_unlocks")
async def admin_shop_unlocks_menu(callback: CallbackQuery, session: AsyncSession):
    """Main menu for managing decision unlocks."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    requirements = load_decision_requirements()

    text = """🔗 **Gestión de Desbloqueos Narrativos**

Este panel gestiona el mapeo entre **decision_id** (decisiones narrativas) e **items de tienda**.

**¿Cómo funciona?**
1. Usuario encuentra una decisión narrativa con un `decision_id`
2. El sistema verifica si tiene el item requerido
3. Si NO lo tiene → Muestra fragmento "teaser"
4. Si SÍ lo tiene → Permite acceder al contenido exclusivo

**Configuración Actual:**"""

    if requirements:
        text += "\n"
        for decision_id, item_name in sorted(requirements.items(), key=lambda x: int(x[0])):
            text += f"\n• Decision `{decision_id}` → **{item_name}**"
    else:
        text += "\n\n_No hay desbloqueos configurados_"

    text += "\n\n**Acciones:**"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Agregar Desbloqueo", callback_data="admin_unlock_add")
    builder.button(text="✏️ Editar Desbloqueo", callback_data="admin_unlock_edit")
    builder.button(text="🗑️ Eliminar Desbloqueo", callback_data="admin_unlock_delete")
    builder.button(text="📖 Ver Documentación", callback_data="admin_unlock_docs")
    builder.button(text="🔙 Volver", callback_data="admin_shop")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_shop_unlocks"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_unlock_add")
async def admin_unlock_add_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start adding a new decision unlock."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Agregar Desbloqueo**

**Paso 1: Selecciona el Producto**

Elige qué producto de tienda quieres vincular a una decisión narrativa:"""

    # Get all shop items
    result = await session.execute(select(ShopItem).where(ShopItem.is_active == True))
    items = result.scalars().all()

    if not items:
        text = """❌ **No hay productos activos**

Primero debes crear productos en la tienda.

📦 Admin → Tienda → Crear Producto"""

        await update_menu(
            callback,
            text,
            get_back_kb("admin_shop_unlocks"),
            session,
            "admin_unlock_add_no_items"
        )
        await callback.answer()
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for item in items:
        vip = "👑" if item.is_vip_only else "🆓"
        builder.button(
            text=f"{vip} {item.name} ({item.price}💋)",
            callback_data=f"unlock_select_item:{item.id}"
        )

    builder.button(text="❌ Cancelar", callback_data="admin_shop_unlocks")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_unlock_add_select"
    )
    await state.set_state(AdminShopStates.configuring_decision_id)
    await callback.answer()


@router.callback_query(AdminShopStates.configuring_decision_id, F.data.startswith("unlock_select_item:"))
async def admin_unlock_select_item(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Item selected, now ask for decision_id."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(selected_item=item.name, selected_item_id=item_id)

    text = f"""➕ **Agregar Desbloqueo**

✅ Producto seleccionado: **{item.name}**

**Paso 2: Decision ID**

Ingresa el `decision_id` de la decisión narrativa que requerirá este producto.

📖 **¿Dónde encuentro el decision_id?**
Los decision IDs están definidos en tus fragmentos narrativos y en la base de datos de decisiones.

**Ejemplo:** El "Diario Íntimo" usa `decision_id = 15`

**Formato:** Solo números (ej: 15, 25, 30)"""

    await callback.message.answer(text)
    await state.set_state(AdminShopStates.configuring_teaser_fragment)
    await callback.answer()


@router.message(AdminShopStates.configuring_teaser_fragment)
async def admin_unlock_set_decision_id(message: Message, state: FSMContext, session: AsyncSession):
    """Process decision_id and save the mapping."""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        decision_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Decision ID inválido. Debe ser un número entero.")
        return

    data = await state.get_data()
    item_name = data.get("selected_item")

    # Load current requirements
    requirements = load_decision_requirements()

    # Check if decision_id already exists
    if str(decision_id) in requirements:
        existing_item = requirements[str(decision_id)]
        text = f"""⚠️ **Conflicto Detectado**

El `decision_id = {decision_id}` ya está asignado a:
**{existing_item}**

¿Deseas reemplazarlo con **{item_name}**?"""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Reemplazar", callback_data=f"unlock_replace:{decision_id}")
        builder.button(text="❌ Cancelar", callback_data="admin_shop_unlocks")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
        await state.update_data(decision_id=decision_id)
        return

    # Save the mapping
    requirements[str(decision_id)] = item_name
    if save_decision_requirements(requirements):
        text = f"""✅ **Desbloqueo Configurado**

**Decision ID:** `{decision_id}`
**Item Requerido:** **{item_name}**

**¿Qué sucede ahora?**
1. Cuando un usuario intente tomar la decisión `{decision_id}`
2. El sistema verificará si tiene **{item_name}** en su inventario
3. Si NO lo tiene → Será redirigido al fragmento "teaser"
4. Si SÍ lo tiene → Podrá acceder al contenido exclusivo

⚠️ **Importante:** Asegúrate de que:
• Existe un fragmento "teaser" configurado en `coordinador_central.py`
• Existe el fragmento exclusivo para cuando tenga el item
• El handler detecta esta decisión especial

📖 Consulta: `docs/guia-fragmentos-condicionados-items-2025-09-15.md`"""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Agregar Otro", callback_data="admin_unlock_add")
        builder.button(text="🔙 Volver", callback_data="admin_shop_unlocks")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
    else:
        await message.answer("❌ Error al guardar la configuración. Revisa los logs.")

    await state.clear()


@router.callback_query(F.data.startswith("unlock_replace:"))
async def admin_unlock_replace_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm replacement of existing decision requirement."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()
    decision_id = data.get("decision_id")
    item_name = data.get("selected_item")

    requirements = load_decision_requirements()
    requirements[str(decision_id)] = item_name

    if save_decision_requirements(requirements):
        await callback.answer("✅ Desbloqueo actualizado", show_alert=True)
        await admin_shop_unlocks_menu(callback, session)
    else:
        await callback.answer("❌ Error al guardar", show_alert=True)

    await state.clear()


@router.callback_query(F.data == "admin_unlock_docs")
async def admin_unlock_show_docs(callback: CallbackQuery, session: AsyncSession):
    """Show documentation about the unlock system."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """📖 **Documentación: Sistema de Desbloqueos**

**Flujo Completo:**

1️⃣ **Usuario intenta tomar una decisión**
   → Handler detecta decision_id especial

2️⃣ **Sistema verifica inventario**
   → `ShopService.has_item_in_inventory(user_id, item_name)`

3️⃣ **Sin el item:**
   → Redirige a fragmento "teaser"
   → Muestra mensaje motivacional + link a tienda

4️⃣ **Con el item:**
   → Permite acceso al fragmento exclusivo
   → Recompensa al usuario

**Archivos Involucrados:**
• `services/coordinador_central.py` - Lógica de verificación
• `handlers/narrative_handler.py` - Detecta decisiones especiales
• `config/decision_requirements.json` - Configuración (este panel)

**Caso de Éxito: Diario Íntimo**
• Decision ID: `15`
• Item: "📓 Diario Íntimo" (30 besitos)
• Teaser: `diana_diary_tease`
• Exclusivo: `diana_diary_intimate`

📄 **Guía Completa:**
`docs/guia-fragmentos-condicionados-items-2025-09-15.md`

💡 **Tips:**
• Usa decision_ids únicos y consecutivos
• Crea teasers atractivos que motiven la compra
• El contenido exclusivo debe valer el precio
• Prueba el flujo completo antes de publicar"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_shop_unlocks")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_unlock_docs"
    )
    await callback.answer()