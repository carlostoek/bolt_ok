"""
Admin panel for shop management - products, inventory, and narrative unlocks.
Implements the clean navigation pattern with update_menu().
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from utils.admin_state import AdminShopStates
from keyboards.common import get_back_kb
from database.models import ShopItem, LorePiece, UserPurchase
from services.shop_service import ShopService

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_shop")
async def admin_shop_main(callback: CallbackQuery, session: AsyncSession):
    """Main shop administration menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Get shop statistics
    total_items = await session.execute(select(func.count(ShopItem.id)))
    total_count = total_items.scalar()

    active_items = await session.execute(
        select(func.count(ShopItem.id)).where(ShopItem.is_active == True)
    )
    active_count = active_items.scalar()

    total_sales = await session.execute(select(func.count(UserPurchase.id)))
    sales_count = total_sales.scalar()

    text = f"""🛒 **Administración de Tienda**

📊 **Estadísticas:**
• Total de productos: {total_count}
• Productos activos: {active_count}
• Ventas totales: {sales_count}

**Gestiona tu tienda:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Ver Productos", callback_data="admin_shop_list")
    builder.button(text="➕ Crear Producto", callback_data="admin_shop_create")
    builder.button(text="🔗 Gestionar Desbloqueos", callback_data="admin_shop_unlocks")
    builder.button(text="📊 Reportes de Ventas", callback_data="admin_shop_reports")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_shop_main"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_shop_list")
async def admin_shop_list(callback: CallbackQuery, session: AsyncSession):
    """List all shop items."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    result = await session.execute(select(ShopItem).order_by(ShopItem.created_at.desc()))
    items = result.scalars().all()

    if not items:
        text = """📦 **Lista de Productos**

No hay productos en la tienda.

➕ Crea tu primer producto para empezar."""
    else:
        lines = ["📦 **Lista de Productos**\n"]
        for item in items:
            status = "✅" if item.is_active else "❌"
            vip = "👑" if item.is_vip_only else "🆓"
            unlock = "🔓" if item.unlocks_lore_piece_id else "📦"
            lines.append(
                f"{status} {vip} {unlock} **{item.name}**\n"
                f"   💰 {item.price} besitos"
            )
        text = "\n".join(lines)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for item in items:
        builder.button(
            text=f"{'✅' if item.is_active else '❌'} {item.name}",
            callback_data=f"admin_shop_view:{item.id}"
        )

    builder.button(text="➕ Crear Producto", callback_data="admin_shop_create")
    builder.button(text="🔙 Volver", callback_data="admin_shop")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_shop_list"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_shop_view:"))
async def admin_shop_view_item(callback: CallbackQuery, session: AsyncSession):
    """View and manage a specific shop item."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Get sales count
    sales_result = await session.execute(
        select(func.count(UserPurchase.id)).where(UserPurchase.shop_item_id == item_id)
    )
    sales_count = sales_result.scalar()

    # Get unlocked content info
    unlock_info = "No desbloquea contenido"
    if item.unlocks_lore_piece_id:
        lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
        if lore_piece:
            unlock_info = f"🔓 Desbloquea: **{lore_piece.title}**\n   📜 `{lore_piece.code_name}`"

    text = f"""📦 **{item.name}**

**Descripción:**
{item.description or 'Sin descripción'}

**Configuración:**
• 💰 Precio: {item.price} besitos
• 👑 Solo VIP: {'Sí' if item.is_vip_only else 'No'}
• ✅ Estado: {'Activo' if item.is_active else 'Inactivo'}
• 📊 Ventas: {sales_count}

**Desbloqueo:**
{unlock_info}

**Acciones:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(
        text="❌ Desactivar" if item.is_active else "✅ Activar",
        callback_data=f"admin_shop_toggle:{item_id}"
    )
    builder.button(text="🔓 Config. Desbloqueo", callback_data=f"admin_shop_unlock:{item_id}")
    builder.button(text="🗑️ Eliminar", callback_data=f"admin_shop_delete_confirm:{item_id}")
    builder.button(text="🔙 Volver", callback_data="admin_shop_list")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_view_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_shop_toggle:"))
async def admin_shop_toggle(callback: CallbackQuery, session: AsyncSession):
    """Toggle active status of a shop item."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.is_active = not item.is_active
    await session.commit()

    status_text = "activado" if item.is_active else "desactivado"
    await callback.answer(f"✅ Producto {status_text}", show_alert=True)

    # Refresh the view
    await admin_shop_view_item(callback, session)


@router.callback_query(F.data == "admin_shop_create")
async def admin_shop_create_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start creating a new shop item."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Crear Producto**

📝 **Paso 1: Nombre del Producto**

Ingresa el nombre del producto (incluye emoji):
Ejemplo: "📓 Diario Íntimo"

💡 Tip: Usa emojis relevantes para mejor visualización."""

    await update_menu(
        callback,
        text,
        get_back_kb("admin_shop"),
        session,
        "admin_shop_create_name"
    )
    await state.set_state(AdminShopStates.creating_name)
    await callback.answer()


@router.message(AdminShopStates.creating_name)
async def admin_shop_create_name(message: Message, state: FSMContext, session: AsyncSession):
    """Process product name."""
    if not await is_admin(message.from_user.id, session):
        return

    name = message.text.strip()

    # Check if name already exists
    existing = await session.execute(
        select(ShopItem).where(ShopItem.name == name)
    )
    if existing.scalar_one_or_none():
        await message.answer("❌ Ya existe un producto con ese nombre. Intenta otro:")
        return

    await state.update_data(name=name)

    text = f"""➕ **Crear Producto**

✅ Nombre: **{name}**

📝 **Paso 2: Descripción**

Ingresa una descripción atractiva del producto:
(Explica qué desbloquea y por qué es valioso)"""

    await message.answer(text)
    await state.set_state(AdminShopStates.creating_description)


@router.message(AdminShopStates.creating_description)
async def admin_shop_create_description(message: Message, state: FSMContext, session: AsyncSession):
    """Process product description."""
    if not await is_admin(message.from_user.id, session):
        return

    description = message.text.strip()
    await state.update_data(description=description)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Descripción: {description[:100]}...

💰 **Paso 3: Precio**

Ingresa el precio en besitos (puntos):
Ejemplo: 30, 50, 100

💡 Precios recomendados:
• Básico: 30 besitos
• Intermedio: 50 besitos
• Premium: 100 besitos
• Exclusivo: 150+ besitos"""

    await message.answer(text)
    await state.set_state(AdminShopStates.creating_price)


@router.message(AdminShopStates.creating_price)
async def admin_shop_create_price(message: Message, state: FSMContext, session: AsyncSession):
    """Process product price."""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        price = int(message.text.strip())
        if price < 0:
            await message.answer("❌ El precio debe ser positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Precio inválido. Ingresa un número entero:")
        return

    await state.update_data(price=price)
    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {price} besitos

👑 **Paso 4: Acceso VIP**

¿Este producto es exclusivo para usuarios VIP?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Solo VIP", callback_data="shop_create_vip_yes")
    builder.button(text="🆓 Para Todos", callback_data="shop_create_vip_no")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.creating_vip_only)


@router.callback_query(AdminShopStates.creating_vip_only, F.data.startswith("shop_create_vip_"))
async def admin_shop_create_vip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process VIP-only setting."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    is_vip_only = callback.data == "shop_create_vip_yes"
    await state.update_data(is_vip_only=is_vip_only)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Acceso: {'👑 Solo VIP' if is_vip_only else '🆓 Para Todos'}

🔓 **Paso 5: Desbloqueo de Contenido**

¿Este producto desbloquea contenido narrativo?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Sí, desbloquea contenido", callback_data="shop_create_unlock_yes")
    builder.button(text="❌ No desbloquea nada", callback_data="shop_create_unlock_no")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.selecting_unlock)
    await callback.answer()


@router.callback_query(AdminShopStates.selecting_unlock, F.data == "shop_create_unlock_no")
async def admin_shop_create_no_unlock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Create product without unlock."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    data = await state.get_data()

    # Create the shop item
    shop_item = ShopItem(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        is_vip_only=data['is_vip_only'],
        is_active=True,
        unlocks_lore_piece_id=None
    )
    session.add(shop_item)
    await session.commit()

    text = f"""✅ **Producto Creado**

**{shop_item.name}** ha sido agregado a la tienda.

• 💰 Precio: {shop_item.price} besitos
• {'👑 Solo VIP' if shop_item.is_active else '🆓 Para Todos'}
• 📦 Sin desbloqueo de contenido
• ✅ Activo"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{shop_item.id}")
    builder.button(text="➕ Crear Otro", callback_data="admin_shop_create")
    builder.button(text="🔙 Volver", callback_data="admin_shop")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.clear()
    await callback.answer()


@router.callback_query(AdminShopStates.selecting_unlock, F.data == "shop_create_unlock_yes")
async def admin_shop_select_lore_piece(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show lore pieces to select for unlock."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Get all lore pieces
    result = await session.execute(select(LorePiece).order_by(LorePiece.title))
    lore_pieces = result.scalars().all()

    if not lore_pieces:
        text = """❌ **No hay contenido narrativo**

Primero debes crear piezas narrativas (LorePieces) desde el panel de gamificación.

Ve a: Admin → Juego Kinky → Pistas Narrativas"""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Sin desbloqueo", callback_data="shop_create_unlock_no")
        builder.button(text="❌ Cancelar", callback_data="admin_shop")
        builder.adjust(1)

        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    text = """🔓 **Selecciona Contenido a Desbloquear**

Elige qué pieza narrativa se desbloqueará al comprar este producto:

📜 **Pistas Disponibles:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for lore in lore_pieces[:15]:  # Limit to 15 for keyboard size
        category_emoji = {
            'fragmentos': '🗺️',
            'memorias': '💭',
            'secretos': '🔮',
            'llaves': '🗝️'
        }.get(lore.category, '📜')

        builder.button(
            text=f"{category_emoji} {lore.title[:30]}",
            callback_data=f"shop_select_lore:{lore.id}"
        )

    builder.button(text="📝 Sin desbloqueo", callback_data="shop_create_unlock_no")
    builder.button(text="❌ Cancelar", callback_data="admin_shop")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.confirming_creation)
    await callback.answer()


@router.callback_query(AdminShopStates.confirming_creation, F.data.startswith("shop_select_lore:"))
async def admin_shop_create_with_unlock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Create product with lore piece unlock."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    lore_piece_id = int(callback.data.split(":")[1])
    lore_piece = await session.get(LorePiece, lore_piece_id)

    if not lore_piece:
        await callback.answer("Contenido no encontrado", show_alert=True)
        return

    data = await state.get_data()

    # Create the shop item
    shop_item = ShopItem(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        is_vip_only=data['is_vip_only'],
        is_active=True,
        unlocks_lore_piece_id=lore_piece_id
    )
    session.add(shop_item)
    await session.commit()

    text = f"""✅ **Producto Creado con Éxito**

**{shop_item.name}** ha sido agregado a la tienda.

**Configuración:**
• 💰 Precio: {shop_item.price} besitos
• {'👑 Solo VIP' if shop_item.is_vip_only else '🆓 Para Todos'}
• ✅ Estado: Activo

**Desbloqueo:**
🔓 Al comprar, desbloquea:
**{lore_piece.title}**
`{lore_piece.code_name}`

⚠️ **Importante:** Para que el desbloqueo funcione en decisiones narrativas, debes configurar el `decision_requirements` en el Coordinador Central.

📖 Ver documentación en: `docs/guia-fragmentos-condicionados-items-2025-09-15.md`"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{shop_item.id}")
    builder.button(text="🔗 Config. Desbloqueos", callback_data="admin_shop_unlocks")
    builder.button(text="➕ Crear Otro", callback_data="admin_shop_create")
    builder.button(text="🔙 Volver", callback_data="admin_shop")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.clear()
    logger.info(f"Admin {callback.from_user.id} created shop item: {shop_item.name}")
    await callback.answer()


# Import unlock configuration router
from . import shop_unlock_config
router.include_router(shop_unlock_config.router)


# ========== EDIT PRODUCT HANDLERS ==========

@router.callback_query(F.data.startswith("admin_shop_edit:"))
async def admin_shop_edit_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing a shop item - show edit menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Store item_id in state
    await state.update_data(editing_item_id=item_id)

    text = f"""✏️ **Editar Producto**

**Producto:** {item.name}

**¿Qué deseas editar?**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Nombre", callback_data=f"edit_field:name:{item_id}")
    builder.button(text="📄 Descripción", callback_data=f"edit_field:description:{item_id}")
    builder.button(text="💰 Precio", callback_data=f"edit_field:price:{item_id}")
    builder.button(text="👑 Acceso VIP", callback_data=f"edit_field:vip:{item_id}")
    builder.button(text="🔓 Desbloqueo", callback_data=f"edit_field:unlock:{item_id}")
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(2, 2, 1, 1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:name:"))
async def admin_shop_edit_name(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Edit product name."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(editing_item_id=item_id, editing_field="name")

    text = f"""✏️ **Editar Nombre**

**Nombre actual:** {item.name}

Ingresa el nuevo nombre del producto (incluye emoji):
Ejemplo: "📓 Diario Íntimo Deluxe"

💡 Tip: Usa emojis relevantes para mejor visualización."""

    await callback.message.answer(text)
    await state.set_state(AdminShopStates.editing_name)
    await callback.answer()


@router.message(AdminShopStates.editing_name)
async def admin_shop_edit_name_process(message: Message, state: FSMContext, session: AsyncSession):
    """Process new product name."""
    if not await is_admin(message.from_user.id, session):
        return

    new_name = message.text.strip()
    data = await state.get_data()
    item_id = data.get("editing_item_id")

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    # Check if name already exists (excluding current item)
    existing = await session.execute(
        select(ShopItem).where(ShopItem.name == new_name, ShopItem.id != item_id)
    )
    if existing.scalar_one_or_none():
        await message.answer("❌ Ya existe un producto con ese nombre. Intenta otro:")
        return

    old_name = item.name
    item.name = new_name
    await session.commit()

    text = f"""✅ **Nombre Actualizado**

**Antes:** {old_name}
**Ahora:** {new_name}

El nombre ha sido actualizado exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:description:"))
async def admin_shop_edit_description(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Edit product description."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(editing_item_id=item_id, editing_field="description")

    text = f"""✏️ **Editar Descripción**

**Descripción actual:**
{item.description or '_Sin descripción_'}

Ingresa la nueva descripción del producto:
(Explica qué desbloquea y por qué es valioso)"""

    await callback.message.answer(text)
    await state.set_state(AdminShopStates.editing_description)
    await callback.answer()


@router.message(AdminShopStates.editing_description)
async def admin_shop_edit_description_process(message: Message, state: FSMContext, session: AsyncSession):
    """Process new product description."""
    if not await is_admin(message.from_user.id, session):
        return

    new_description = message.text.strip()
    data = await state.get_data()
    item_id = data.get("editing_item_id")

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    old_description = item.description or "Sin descripción"
    item.description = new_description
    await session.commit()

    text = f"""✅ **Descripción Actualizada**

**Producto:** {item.name}

**Nueva descripción:**
{new_description}

La descripción ha sido actualizada exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:price:"))
async def admin_shop_edit_price(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Edit product price."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(editing_item_id=item_id, editing_field="price")

    text = f"""✏️ **Editar Precio**

**Producto:** {item.name}
**Precio actual:** {item.price} besitos

Ingresa el nuevo precio en besitos (puntos):

💡 Precios recomendados:
• Básico: 30 besitos
• Intermedio: 50 besitos
• Premium: 100 besitos
• Exclusivo: 150+ besitos"""

    await callback.message.answer(text)
    await state.set_state(AdminShopStates.editing_price)
    await callback.answer()


@router.message(AdminShopStates.editing_price)
async def admin_shop_edit_price_process(message: Message, state: FSMContext, session: AsyncSession):
    """Process new product price."""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        new_price = int(message.text.strip())
        if new_price < 0:
            await message.answer("❌ El precio debe ser positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Precio inválido. Ingresa un número entero:")
        return

    data = await state.get_data()
    item_id = data.get("editing_item_id")

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    old_price = item.price
    item.price = new_price
    await session.commit()

    # Calculate price change percentage
    if old_price > 0:
        change_pct = ((new_price - old_price) / old_price) * 100
        change_text = f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%"
    else:
        change_text = "N/A"

    text = f"""✅ **Precio Actualizado**

**Producto:** {item.name}

**Precio anterior:** {old_price} besitos
**Precio nuevo:** {new_price} besitos
**Cambio:** {change_text}

El precio ha sido actualizado exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:vip:"))
async def admin_shop_edit_vip_toggle(callback: CallbackQuery, session: AsyncSession):
    """Toggle VIP-only status."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.is_vip_only = not item.is_vip_only
    await session.commit()

    status_text = "👑 Solo VIP" if item.is_vip_only else "🆓 Para Todos"
    await callback.answer(f"✅ Cambiado a {status_text}", show_alert=True)

    # Return to edit menu
    from aiogram.fsm.context import FSMContext
    # We need to pass state but we don't have it, so call the view directly
    text = f"""✅ **Acceso VIP Actualizado**

**Producto:** {item.name}
**Nuevo acceso:** {status_text}

El estado VIP ha sido actualizado exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_vip_updated_{item_id}"
    )


@router.callback_query(F.data.startswith("edit_field:unlock:"))
async def admin_shop_edit_unlock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Edit unlock configuration - show lore pieces."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(editing_item_id=item_id)

    # Get current unlock
    current_unlock = "No desbloquea contenido"
    if item.unlocks_lore_piece_id:
        lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
        if lore_piece:
            current_unlock = f"🔓 {lore_piece.title} (`{lore_piece.code_name}`)"

    # Get all lore pieces
    result = await session.execute(select(LorePiece).order_by(LorePiece.title))
    lore_pieces = result.scalars().all()

    text = f"""✏️ **Editar Desbloqueo**

**Producto:** {item.name}
**Desbloqueo actual:** {current_unlock}

Selecciona qué contenido narrativo desbloqueará este producto:"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for lore in lore_pieces[:15]:
        category_emoji = {
            'fragmentos': '🗺️',
            'memorias': '💭',
            'secretos': '🔮',
            'llaves': '🗝️'
        }.get(lore.category, '📜')

        # Mark currently selected
        prefix = "✅ " if item.unlocks_lore_piece_id == lore.id else ""
        builder.button(
            text=f"{prefix}{category_emoji} {lore.title[:25]}",
            callback_data=f"set_unlock:{item_id}:{lore.id}"
        )

    builder.button(text="❌ Sin Desbloqueo", callback_data=f"set_unlock:{item_id}:none")
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_unlock_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_unlock:"))
async def admin_shop_set_unlock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set new unlock for product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    parts = callback.data.split(":")
    item_id = int(parts[1])
    lore_id_str = parts[2]

    item = await session.get(ShopItem, item_id)
    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    old_unlock_text = "Sin desbloqueo"
    if item.unlocks_lore_piece_id:
        old_lore = await session.get(LorePiece, item.unlocks_lore_piece_id)
        if old_lore:
            old_unlock_text = old_lore.title

    if lore_id_str == "none":
        item.unlocks_lore_piece_id = None
        new_unlock_text = "Sin desbloqueo"
    else:
        lore_id = int(lore_id_str)
        lore_piece = await session.get(LorePiece, lore_id)
        if not lore_piece:
            await callback.answer("Contenido no encontrado", show_alert=True)
            return

        item.unlocks_lore_piece_id = lore_id
        new_unlock_text = f"{lore_piece.title} (`{lore_piece.code_name}`)"

    await session.commit()

    text = f"""✅ **Desbloqueo Actualizado**

**Producto:** {item.name}

**Antes:** {old_unlock_text}
**Ahora:** {new_unlock_text}

El desbloqueo ha sido configurado exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_unlock_updated_{item_id}"
    )
    await state.clear()
    await callback.answer()


# Additional handlers for edit and delete
@router.callback_query(F.data.startswith("admin_shop_delete_confirm:"))
async def admin_shop_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    """Confirm deletion of a shop item."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    text = f"""🗑️ **Confirmar Eliminación**

¿Estás seguro de que deseas eliminar este producto?

**{item.name}**
💰 {item.price} besitos

⚠️ **Advertencia:**
• Los usuarios que ya lo compraron mantendrán el acceso
• El producto desaparecerá de la tienda
• Esta acción NO se puede deshacer"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Sí, Eliminar", callback_data=f"admin_shop_delete_exec:{item_id}")
    builder.button(text="❌ Cancelar", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_delete_confirm_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_shop_delete_exec:"))
async def admin_shop_delete_execute(callback: CallbackQuery, session: AsyncSession):
    """Execute deletion of a shop item."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item_name = item.name
    await session.delete(item)
    await session.commit()

    logger.info(f"Admin {callback.from_user.id} deleted shop item: {item_name}")
    await callback.answer(f"✅ {item_name} eliminado", show_alert=True)

    # Return to shop list
    await admin_shop_list(callback, session)


@router.callback_query(F.data == "admin_shop_reports")
async def admin_shop_reports(callback: CallbackQuery, session: AsyncSession):
    """Show shop sales reports."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Get total sales
    from database.models import UserPurchase, User
    total_sales_result = await session.execute(select(func.count(UserPurchase.id)))
    total_sales = total_sales_result.scalar()

    # Get total revenue
    revenue_result = await session.execute(select(func.sum(UserPurchase.price_paid)))
    total_revenue = revenue_result.scalar() or 0

    # Get top selling items
    from sqlalchemy import desc
    top_items_result = await session.execute(
        select(
            ShopItem.name,
            ShopItem.price,
            func.count(UserPurchase.id).label("sales_count"),
            func.sum(UserPurchase.price_paid).label("revenue")
        )
        .join(UserPurchase, ShopItem.id == UserPurchase.shop_item_id)
        .group_by(ShopItem.id, ShopItem.name, ShopItem.price)
        .order_by(desc("sales_count"))
        .limit(5)
    )
    top_items = top_items_result.all()

    text = f"""📊 **Reportes de Ventas**

**Resumen General:**
• 🛒 Total de ventas: {total_sales}
• 💰 Ingresos totales: {total_revenue} besitos

**Top 5 Productos Más Vendidos:**"""

    if top_items:
        text += "\n"
        for idx, (name, price, sales, revenue) in enumerate(top_items, 1):
            text += f"\n{idx}. **{name}**"
            text += f"\n   💰 {price} besitos × {sales} ventas = {revenue} total\n"
    else:
        text += "\n\n_No hay ventas registradas_"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_shop")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        "admin_shop_reports"
    )
    await callback.answer()
