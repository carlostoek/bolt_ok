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
            temporal = "⏰" if (item.available_from or item.available_until) else ""
            locked = "🔐" if item.unlock_requirements else ""
            lines.append(
                f"{status} {vip} {unlock} {temporal} {locked} **{item.name}**\n"
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
    if item.unlocks_fragment_key:
        from database.narrative_models import StoryFragment
        stmt = select(StoryFragment).where(StoryFragment.key == item.unlocks_fragment_key)
        fragment_result = await session.execute(stmt)
        fragment = fragment_result.scalar_one_or_none()
        if fragment:
            if unlock_info == "No desbloquea contenido":
                unlock_info = f"📖 Desbloquea fragmento: **{item.unlocks_fragment_key}**"
            else:
                unlock_info += f"\n📖 Desbloquea fragmento: **{item.unlocks_fragment_key}**"

    # Build availability info
    avail_info = "♾️ Siempre disponible"
    if item.available_from or item.available_until:
        avail_info = "⏰ Temporal"
        if item.available_from and item.available_until:
            avail_info += f" ({item.available_from.strftime('%d/%m/%Y')} - {item.available_until.strftime('%d/%m/%Y')})"
        elif item.available_from:
            avail_info += f" (desde {item.available_from.strftime('%d/%m/%Y')})"
        elif item.available_until:
            avail_info += f" (hasta {item.available_until.strftime('%d/%m/%Y')})"

    # Build stock info
    stock_info = "♾️ Ilimitado"
    if item.stock_limit is not None:
        purchases_result = await session.execute(
            select(func.count(UserPurchase.id)).where(UserPurchase.shop_item_id == item_id)
        )
        total_purchases = purchases_result.scalar() or 0
        remaining = item.stock_limit - total_purchases
        stock_info = f"📦 {item.stock_limit} unidades ({remaining} restantes)"

    # Build max purchases info
    max_purch = item.max_purchases_per_user
    max_purch_info = '♾️ Sin límite' if max_purch == 0 else f"{max_purch} {'vez' if max_purch == 1 else 'veces'}"

    # Build requirements info
    if item.unlock_requirements:
        from services.condition_checker import ConditionChecker
        checker = ConditionChecker(session)
        req_info = await checker.get_requirements_summary(item.unlock_requirements)
        requirements_text = f"🔐 **Requisitos:**\n{req_info}\n\n"
    else:
        requirements_text = ""

    text = f"""📦 **{item.name}**

**Descripción:**
{item.description or 'Sin descripción'}

**Configuración:**
• 💰 Precio: {item.price} besitos
• 👑 Solo VIP: {'Sí' if item.is_vip_only else 'No'}
• ✅ Estado: {'Activo' if item.is_active else 'Inactivo'}
• 📊 Ventas: {sales_count}
• 📦 Stock: {stock_info}
• 🔢 Límite/usuario: {max_purch_info}
• 📅 Disponibilidad: {avail_info}

{requirements_text}**Desbloqueo:**
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
    """Process VIP-only setting and ask about image."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    is_vip_only = callback.data == "shop_create_vip_yes"
    await state.update_data(is_vip_only=is_vip_only)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Acceso: {'👑 Solo VIP' if is_vip_only else '🆓 Para Todos'}

🖼️ **Paso 5: Imagen del Producto** (Opcional)

¿Deseas agregar una imagen para este producto?
(Los productos pueden funcionar sin imagen)"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Sí, agregar imagen", callback_data="shop_create_image_yes")
    builder.button(text="⏭️ Omitir (sin imagen)", callback_data="shop_create_image_skip")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.uploading_image)
    await callback.answer()


@router.callback_query(AdminShopStates.uploading_image, F.data == "shop_create_image_skip")
async def admin_shop_create_skip_image(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip image upload and proceed to unlock configuration."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Store null for image
    await state.update_data(image_file_id=None)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Acceso: {'👑 Solo VIP' if data['is_vip_only'] else '🆓 Para Todos'}
✅ Imagen: Sin imagen

📦 **Paso 6: Stock del Producto** (Opcional)

¿Este producto tiene stock limitado?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Sí, tiene stock limitado", callback_data="shop_create_stock_yes")
    builder.button(text="♾️ Stock ilimitado", callback_data="shop_create_stock_unlimited")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_stock)
    await callback.answer()


@router.callback_query(AdminShopStates.uploading_image, F.data == "shop_create_image_yes")
async def admin_shop_create_request_image(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request image upload from admin."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Crear Producto**

🖼️ **Enviar Imagen del Producto**

Por favor, envía una imagen para este producto.

💡 Tips:
• Formatos soportados: JPG, PNG, GIF
• Tamaño recomendado: máximo 5MB
• La imagen se mostrará en la tienda

⚠️ Envía la imagen como foto (no como archivo)"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="shop_create_image_skip")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    # Stay in uploading_image state to receive the photo
    await callback.answer()


@router.message(AdminShopStates.uploading_image, F.photo)
async def admin_shop_create_receive_image(message: Message, state: FSMContext, session: AsyncSession):
    """Receive and store the product image."""
    if not await is_admin(message.from_user.id, session):
        return

    # Get the largest photo size
    photo = message.photo[-1]
    file_id = photo.file_id

    # Store the file_id
    await state.update_data(image_file_id=file_id)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Acceso: {'👑 Solo VIP' if data['is_vip_only'] else '🆓 Para Todos'}
✅ Imagen: Recibida ✓

📦 **Paso 6: Stock del Producto** (Opcional)

¿Este producto tiene stock limitado?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Sí, tiene stock limitado", callback_data="shop_create_stock_yes")
    builder.button(text="♾️ Stock ilimitado", callback_data="shop_create_stock_unlimited")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_stock)


@router.callback_query(AdminShopStates.configuring_stock, F.data == "shop_create_stock_unlimited")
async def admin_shop_create_stock_unlimited(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set stock to unlimited and proceed to max purchases."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Store unlimited stock (NULL)
    await state.update_data(stock_limit=None)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: ♾️ Ilimitado

🔢 **Paso 7: Límite por Usuario**

¿Cuántas veces puede comprar este producto cada usuario?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ Una vez (único)", callback_data="shop_create_maxpurch_1")
    builder.button(text="♾️ Sin límite", callback_data="shop_create_maxpurch_unlimited")
    builder.button(text="✏️ Otro número", callback_data="shop_create_maxpurch_custom")
    builder.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_max_purchases)
    await callback.answer()


@router.callback_query(AdminShopStates.configuring_stock, F.data == "shop_create_stock_yes")
async def admin_shop_create_stock_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request stock amount."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Crear Producto**

📦 **Configurar Stock Limitado**

Ingresa el número de unidades disponibles:

💡 Ejemplos:
• 10 - Para productos exclusivos
• 50 - Para ediciones limitadas
• 100 - Para stock moderado

⚠️ Una vez agotado, el producto dejará de aparecer en tienda."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="shop_create_stock_unlimited")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    # Stay in configuring_stock state to receive the number
    await callback.answer()


@router.message(AdminShopStates.configuring_stock)
async def admin_shop_create_stock_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive stock number."""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        stock_limit = int(message.text.strip())
        if stock_limit <= 0:
            await message.answer("❌ El stock debe ser un número positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido:")
        return

    # Store stock limit
    await state.update_data(stock_limit=stock_limit)

    data = await state.get_data()

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: 📦 {stock_limit} unidades

🔢 **Paso 7: Límite por Usuario**

¿Cuántas veces puede comprar este producto cada usuario?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ Una vez (único)", callback_data="shop_create_maxpurch_1")
    builder.button(text="♾️ Sin límite", callback_data="shop_create_maxpurch_unlimited")
    builder.button(text="✏️ Otro número", callback_data="shop_create_maxpurch_custom")
    builder.adjust(2, 1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_max_purchases)


@router.callback_query(AdminShopStates.configuring_max_purchases, F.data == "shop_create_maxpurch_1")
async def admin_shop_create_maxpurch_one(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set max purchases to 1."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(max_purchases_per_user=1)
    await proceed_to_availability_config(callback, state, session)


@router.callback_query(AdminShopStates.configuring_max_purchases, F.data == "shop_create_maxpurch_unlimited")
async def admin_shop_create_maxpurch_unlimited(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set max purchases to unlimited (0)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(max_purchases_per_user=0)
    await proceed_to_availability_config(callback, state, session)


@router.callback_query(AdminShopStates.configuring_max_purchases, F.data == "shop_create_maxpurch_custom")
async def admin_shop_create_maxpurch_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request custom max purchases number."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Crear Producto**

🔢 **Configurar Límite por Usuario**

Ingresa el número máximo de veces que cada usuario puede comprar este producto:

💡 Ejemplos:
• 1 - Solo pueden comprar una vez
• 3 - Hasta 3 compras por usuario
• 5 - Hasta 5 compras por usuario"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="shop_create_maxpurch_unlimited")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    # Stay in configuring_max_purchases state to receive the number
    await callback.answer()


@router.message(AdminShopStates.configuring_max_purchases)
async def admin_shop_create_maxpurch_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive max purchases number."""
    if not await is_admin(message.from_user.id, session):
        return

    try:
        max_purchases = int(message.text.strip())
        if max_purchases <= 0:
            await message.answer("❌ El límite debe ser un número positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido:")
        return

    await state.update_data(max_purchases_per_user=max_purchases)

    data = await state.get_data()

    stock_text = '♾️ Ilimitado' if data.get('stock_limit') is None else f"📦 {data['stock_limit']} unidades"

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: {stock_text}
✅ Límite por usuario: {max_purchases} compras

📅 **Paso 8: Disponibilidad Temporal** (Opcional)

¿Este producto estará disponible solo por tiempo limitado?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⏰ Sí, es temporal", callback_data="shop_create_availability_yes")
    builder.button(text="♾️ Siempre disponible", callback_data="shop_create_availability_no")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_availability)


@router.callback_query(AdminShopStates.configuring_availability, F.data == "shop_create_availability_no")
async def admin_shop_create_availability_none(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set no availability limits (always available)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    # Store null for both dates
    await state.update_data(available_from=None, available_until=None)
    await proceed_to_unlock_config(callback, state, session)


@router.callback_query(AdminShopStates.configuring_availability, F.data == "shop_create_availability_yes")
async def admin_shop_create_availability_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request availability dates."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    text = """➕ **Crear Producto**

📅 **Configurar Disponibilidad Temporal**

Este producto estará disponible solo en un período específico.

**¿Desde cuándo estará disponible?**

Ingresa la fecha de inicio (formato: DD/MM/AAAA)
Ejemplo: 01/12/2025

💡 Deja vacío si quieres que esté disponible desde ahora.
Escribe "ahora" para disponibilidad inmediata."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Desde ahora", callback_data="shop_avail_from_now")
    builder.button(text="❌ Cancelar", callback_data="shop_create_availability_no")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.entering_available_from)
    await callback.answer()


@router.callback_query(AdminShopStates.entering_available_from, F.data == "shop_avail_from_now")
async def admin_shop_avail_from_now(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set available_from to None (immediate availability)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.update_data(available_from=None)

    text = """➕ **Crear Producto**

📅 **Configurar Disponibilidad Temporal**

✅ Disponible desde: **Ahora**

**¿Hasta cuándo estará disponible?**

Ingresa la fecha de finalización (formato: DD/MM/AAAA)
Ejemplo: 31/12/2025

⚠️ Después de esta fecha, el producto dejará de aparecer en la tienda."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="shop_create_availability_no")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.entering_available_until)
    await callback.answer()


@router.message(AdminShopStates.entering_available_from)
async def admin_shop_avail_from_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive available_from date."""
    if not await is_admin(message.from_user.id, session):
        return

    from datetime import datetime

    date_str = message.text.strip().lower()

    if date_str == "ahora":
        await state.update_data(available_from=None)
    else:
        try:
            # Parse date DD/MM/YYYY
            available_from = datetime.strptime(date_str, "%d/%m/%Y")
            await state.update_data(available_from=available_from)
        except ValueError:
            await message.answer("❌ Formato de fecha inválido. Usa DD/MM/AAAA (ej: 01/12/2025):")
            return

    data = await state.get_data()
    avail_from = data.get('available_from')
    from_text = "Ahora" if avail_from is None else avail_from.strftime('%d/%m/%Y')

    text = f"""➕ **Crear Producto**

📅 **Configurar Disponibilidad Temporal**

✅ Disponible desde: **{from_text}**

**¿Hasta cuándo estará disponible?**

Ingresa la fecha de finalización (formato: DD/MM/AAAA)
Ejemplo: 31/12/2025

⚠️ Después de esta fecha, el producto dejará de aparecer en la tienda."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data="shop_create_availability_no")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.entering_available_until)


@router.message(AdminShopStates.entering_available_until)
async def admin_shop_avail_until_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive available_until date."""
    if not await is_admin(message.from_user.id, session):
        return

    from datetime import datetime

    date_str = message.text.strip()

    try:
        # Parse date DD/MM/YYYY
        available_until = datetime.strptime(date_str, "%d/%m/%Y")

        # Validate that until is after from (if from exists)
        data = await state.get_data()
        avail_from = data.get('available_from')

        if avail_from and available_until < avail_from:
            await message.answer("❌ La fecha de finalización debe ser posterior a la fecha de inicio. Intenta de nuevo:")
            return

        await state.update_data(available_until=available_until)

        # Show summary and proceed to unlock config
        avail_from_text = "Ahora" if avail_from is None else avail_from.strftime('%d/%m/%Y')
        avail_until_text = available_until.strftime('%d/%m/%Y')

        data = await state.get_data()
        stock_text = '♾️ Ilimitado' if data.get('stock_limit') is None else f"📦 {data['stock_limit']} unidades"
        max_purch = data.get('max_purchases_per_user', 1)
        max_purch_text = '♾️ Sin límite' if max_purch == 0 else f"{max_purch} {'vez' if max_purch == 1 else 'veces'}"

        text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: {stock_text}
✅ Límite por usuario: {max_purch_text}
✅ Disponible: ⏰ {avail_from_text} - {avail_until_text}

🔓 **Paso 9: Desbloqueo de Contenido**

¿Este producto desbloquea contenido narrativo?"""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Sí, desbloquea contenido", callback_data="shop_create_unlock_yes")
        builder.button(text="❌ No desbloquea nada", callback_data="shop_create_unlock_no")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
        await state.set_state(AdminShopStates.selecting_unlock)

    except ValueError:
        await message.answer("❌ Formato de fecha inválido. Usa DD/MM/AAAA (ej: 31/12/2025):")
        return


async def proceed_to_availability_config(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Helper function to proceed to availability configuration."""
    data = await state.get_data()

    stock_text = '♾️ Ilimitado' if data.get('stock_limit') is None else f"📦 {data['stock_limit']} unidades"
    max_purch = data.get('max_purchases_per_user', 1)
    max_purch_text = '♾️ Sin límite' if max_purch == 0 else f"{max_purch} {'vez' if max_purch == 1 else 'veces'}"

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: {stock_text}
✅ Límite por usuario: {max_purch_text}

📅 **Paso 8: Disponibilidad Temporal** (Opcional)

¿Este producto estará disponible solo por tiempo limitado?"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⏰ Sí, es temporal", callback_data="shop_create_availability_yes")
    builder.button(text="♾️ Siempre disponible", callback_data="shop_create_availability_no")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminShopStates.configuring_availability)
    await callback.answer()


async def proceed_to_unlock_config(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Helper function to proceed to unlock configuration."""
    data = await state.get_data()

    stock_text = '♾️ Ilimitado' if data.get('stock_limit') is None else f"📦 {data['stock_limit']} unidades"
    max_purch = data.get('max_purchases_per_user', 1)
    max_purch_text = '♾️ Sin límite' if max_purch == 0 else f"{max_purch} {'vez' if max_purch == 1 else 'veces'}"

    # Availability text
    avail_from = data.get('available_from')
    avail_until = data.get('available_until')
    if avail_from or avail_until:
        avail_text = "⏰ Temporal"
        if avail_from and avail_until:
            avail_text += f" ({avail_from.strftime('%d/%m/%Y')} - {avail_until.strftime('%d/%m/%Y')})"
        elif avail_from:
            avail_text += f" (desde {avail_from.strftime('%d/%m/%Y')})"
        elif avail_until:
            avail_text += f" (hasta {avail_until.strftime('%d/%m/%Y')})"
    else:
        avail_text = "♾️ Siempre"

    text = f"""➕ **Crear Producto**

✅ Nombre: **{data['name']}**
✅ Precio: {data['price']} besitos
✅ Stock: {stock_text}
✅ Límite por usuario: {max_purch_text}
✅ Disponibilidad: {avail_text}

🔓 **Paso 9: Desbloqueo de Contenido**

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
        image_file_id=data.get('image_file_id'),
        stock_limit=data.get('stock_limit'),
        max_purchases_per_user=data.get('max_purchases_per_user', 1),
        available_from=data.get('available_from'),
        available_until=data.get('available_until'),
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
        image_file_id=data.get('image_file_id'),
        stock_limit=data.get('stock_limit'),
        max_purchases_per_user=data.get('max_purchases_per_user', 1),
        available_from=data.get('available_from'),
        available_until=data.get('available_until'),
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
    builder.button(text="🖼️ Imagen", callback_data=f"edit_field:image:{item_id}")
    builder.button(text="📦 Stock", callback_data=f"edit_field:stock:{item_id}")
    builder.button(text="🔢 Límite Usuario", callback_data=f"edit_field:maxpurch:{item_id}")
    builder.button(text="📅 Disponibilidad", callback_data=f"edit_field:availability:{item_id}")
    builder.button(text="🔐 Requisitos", callback_data=f"edit_field:requirements:{item_id}")
    builder.button(text="🔓 Desbloqueo", callback_data=f"edit_field:unlock:{item_id}")
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(2, 2, 2, 2, 2, 1, 1)

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


@router.callback_query(F.data.startswith("edit_field:image:"))
async def admin_shop_edit_image_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing product image."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Store item_id in state
    await state.update_data(editing_item_id=item_id)

    image_status = "✅ Tiene imagen" if item.image_file_id else "❌ Sin imagen"

    text = f"""✏️ **Editar Imagen**

**Producto:** {item.name}
**Estado actual:** {image_status}

**Opciones:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    if item.image_file_id:
        builder.button(text="👁️ Ver Imagen Actual", callback_data=f"view_image:{item_id}")
        builder.button(text="🔄 Cambiar Imagen", callback_data=f"change_image:{item_id}")
        builder.button(text="🗑️ Eliminar Imagen", callback_data=f"remove_image:{item_id}")
    else:
        builder.button(text="➕ Agregar Imagen", callback_data=f"add_image:{item_id}")

    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_image_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_image:"))
async def admin_shop_view_image(callback: CallbackQuery, session: AsyncSession):
    """Show the current product image."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item or not item.image_file_id:
        await callback.answer("Imagen no encontrada", show_alert=True)
        return

    # Send the image
    from aiogram import Bot
    bot: Bot = callback.bot

    await bot.send_photo(
        chat_id=callback.from_user.id,
        photo=item.image_file_id,
        caption=f"🖼️ Imagen de: **{item.name}**"
    )

    await callback.answer("✅ Imagen enviada")


@router.callback_query(F.data.startswith("add_image:"))
async def admin_shop_add_image(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request image upload for product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_item_id=item_id)

    text = """✏️ **Agregar Imagen**

🖼️ **Enviar Imagen del Producto**

Por favor, envía una imagen para este producto.

💡 Tips:
• Formatos soportados: JPG, PNG, GIF
• Tamaño recomendado: máximo 5MB
• La imagen se mostrará en la tienda

⚠️ Envía la imagen como foto (no como archivo)"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:image:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_add_image_{item_id}"
    )
    await state.set_state(AdminShopStates.editing_image)
    await callback.answer()


@router.callback_query(F.data.startswith("change_image:"))
async def admin_shop_change_image(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request new image upload for product."""
    # Same as add_image
    await admin_shop_add_image(callback, state, session)


@router.callback_query(F.data.startswith("remove_image:"))
async def admin_shop_remove_image(callback: CallbackQuery, session: AsyncSession):
    """Remove product image."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.image_file_id = None
    await session.commit()

    text = f"""✅ **Imagen Eliminada**

**Producto:** {item.name}

La imagen ha sido eliminada exitosamente.
El producto ahora se mostrará sin imagen."""

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
        f"admin_shop_image_removed_{item_id}"
    )
    await callback.answer("✅ Imagen eliminada")


@router.message(AdminShopStates.editing_image, F.photo)
async def admin_shop_edit_image_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive new image for product."""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    item_id = data.get('editing_item_id')

    if not item_id:
        await message.answer("❌ Error: sesión expirada")
        await state.clear()
        return

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    # Get the largest photo size
    photo = message.photo[-1]
    file_id = photo.file_id

    # Update the image
    item.image_file_id = file_id
    await session.commit()

    text = f"""✅ **Imagen Actualizada**

**Producto:** {item.name}

La imagen ha sido actualizada exitosamente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:stock:"))
async def admin_shop_edit_stock_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing product stock."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Store item_id in state
    await state.update_data(editing_item_id=item_id)

    stock_status = f"♾️ Ilimitado" if item.stock_limit is None else f"📦 {item.stock_limit} unidades"

    text = f"""✏️ **Editar Stock**

**Producto:** {item.name}
**Stock actual:** {stock_status}

**Opciones:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    if item.stock_limit is not None:
        builder.button(text="📦 Cambiar Cantidad", callback_data=f"change_stock:{item_id}")
        builder.button(text="♾️ Hacer Ilimitado", callback_data=f"unlimited_stock:{item_id}")
    else:
        builder.button(text="📦 Establecer Límite", callback_data=f"set_stock:{item_id}")

    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_stock_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith(("set_stock:", "change_stock:")))
async def admin_shop_request_stock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request stock amount."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_item_id=item_id)

    text = """✏️ **Configurar Stock**

📦 Ingresa el número de unidades disponibles:

💡 Ejemplos:
• 10 - Para productos exclusivos
• 50 - Para ediciones limitadas
• 100 - Para stock moderado

⚠️ Una vez agotado, el producto dejará de aparecer en tienda."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:stock:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_request_stock_{item_id}"
    )
    await state.set_state(AdminShopStates.editing_stock)
    await callback.answer()


@router.callback_query(F.data.startswith("unlimited_stock:"))
async def admin_shop_unlimited_stock(callback: CallbackQuery, session: AsyncSession):
    """Set stock to unlimited."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.stock_limit = None
    await session.commit()

    text = f"""✅ **Stock Actualizado**

**Producto:** {item.name}

El stock ahora es **♾️ Ilimitado**.
El producto siempre estará disponible en la tienda."""

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
        f"admin_shop_stock_unlimited_{item_id}"
    )
    await callback.answer("✅ Stock ilimitado")


@router.message(AdminShopStates.editing_stock)
async def admin_shop_edit_stock_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive new stock amount."""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    item_id = data.get('editing_item_id')

    if not item_id:
        await message.answer("❌ Error: sesión expirada")
        await state.clear()
        return

    try:
        stock_limit = int(message.text.strip())
        if stock_limit <= 0:
            await message.answer("❌ El stock debe ser un número positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido:")
        return

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    # Update stock
    item.stock_limit = stock_limit
    await session.commit()

    text = f"""✅ **Stock Actualizado**

**Producto:** {item.name}

Stock configurado a: **📦 {stock_limit} unidades**

El producto dejará de aparecer en tienda cuando se agoten las {stock_limit} unidades."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:maxpurch:"))
async def admin_shop_edit_maxpurch_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing max purchases per user."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Store item_id in state
    await state.update_data(editing_item_id=item_id)

    max_purch = item.max_purchases_per_user
    max_purch_text = '♾️ Sin límite' if max_purch == 0 else f"{max_purch} {'vez' if max_purch == 1 else 'veces'}"

    text = f"""✏️ **Editar Límite por Usuario**

**Producto:** {item.name}
**Límite actual:** {max_purch_text}

**Opciones:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ Una vez (único)", callback_data=f"set_maxpurch:1:{item_id}")
    builder.button(text="♾️ Sin límite", callback_data=f"set_maxpurch:0:{item_id}")
    builder.button(text="✏️ Otro número", callback_data=f"custom_maxpurch:{item_id}")
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(2, 1, 1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_maxpurch_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_maxpurch:"))
async def admin_shop_set_maxpurch(callback: CallbackQuery, session: AsyncSession):
    """Set max purchases directly."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    parts = callback.data.split(":")
    max_purchases = int(parts[1])
    item_id = int(parts[2])

    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.max_purchases_per_user = max_purchases
    await session.commit()

    max_purch_text = '♾️ Sin límite' if max_purchases == 0 else f"{max_purchases} {'vez' if max_purchases == 1 else 'veces'}"

    text = f"""✅ **Límite por Usuario Actualizado**

**Producto:** {item.name}

Límite configurado a: **{max_purch_text}**

Cada usuario podrá comprar este producto {'sin límite' if max_purchases == 0 else max_purch_text}."""

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
        f"admin_shop_maxpurch_updated_{item_id}"
    )
    await callback.answer("✅ Límite actualizado")


@router.callback_query(F.data.startswith("custom_maxpurch:"))
async def admin_shop_request_maxpurch(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request custom max purchases number."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_item_id=item_id)

    text = """✏️ **Configurar Límite por Usuario**

🔢 Ingresa el número máximo de veces que cada usuario puede comprar este producto:

💡 Ejemplos:
• 1 - Solo pueden comprar una vez
• 3 - Hasta 3 compras por usuario
• 5 - Hasta 5 compras por usuario"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:maxpurch:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_request_maxpurch_{item_id}"
    )
    await state.set_state(AdminShopStates.editing_max_purchases)
    await callback.answer()


@router.message(AdminShopStates.editing_max_purchases)
async def admin_shop_edit_maxpurch_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive new max purchases number."""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    item_id = data.get('editing_item_id')

    if not item_id:
        await message.answer("❌ Error: sesión expirada")
        await state.clear()
        return

    try:
        max_purchases = int(message.text.strip())
        if max_purchases <= 0:
            await message.answer("❌ El límite debe ser un número positivo. Intenta de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido:")
        return

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    # Update max purchases
    item.max_purchases_per_user = max_purchases
    await session.commit()

    text = f"""✅ **Límite por Usuario Actualizado**

**Producto:** {item.name}

Límite configurado a: **{max_purchases} {'vez' if max_purchases == 1 else 'veces'}**

Cada usuario podrá comprar este producto hasta {max_purchases} {'vez' if max_purchases == 1 else 'veces'}."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
    builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
    builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("edit_field:availability:"))
async def admin_shop_edit_availability_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing product availability dates."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Store item_id in state
    await state.update_data(editing_item_id=item_id)

    # Get current availability
    avail_from = item.available_from
    avail_until = item.available_until

    if avail_from or avail_until:
        avail_text = "⏰ Temporal"
        if avail_from and avail_until:
            avail_text += f" ({avail_from.strftime('%d/%m/%Y')} - {avail_until.strftime('%d/%m/%Y')})"
        elif avail_from:
            avail_text += f" (desde {avail_from.strftime('%d/%m/%Y')})"
        elif avail_until:
            avail_text += f" (hasta {avail_until.strftime('%d/%m/%Y')})"
    else:
        avail_text = "♾️ Siempre disponible"

    text = f"""✏️ **Editar Disponibilidad**

**Producto:** {item.name}
**Disponibilidad actual:** {avail_text}

**Opciones:**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    if avail_from or avail_until:
        builder.button(text="📅 Cambiar Fechas", callback_data=f"change_availability:{item_id}")
        builder.button(text="♾️ Hacer Permanente", callback_data=f"permanent_availability:{item_id}")
    else:
        builder.button(text="⏰ Establecer Período", callback_data=f"set_availability:{item_id}")

    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_availability_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("permanent_availability:"))
async def admin_shop_permanent_availability(callback: CallbackQuery, session: AsyncSession):
    """Set availability to permanent (always available)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.available_from = None
    item.available_until = None
    await session.commit()

    text = f"""✅ **Disponibilidad Actualizada**

**Producto:** {item.name}

El producto ahora está **♾️ Siempre Disponible**.
Aparecerá en la tienda sin restricciones temporales."""

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
        f"admin_shop_availability_permanent_{item_id}"
    )
    await callback.answer("✅ Disponibilidad permanente")


@router.callback_query(F.data.startswith(("set_availability:", "change_availability:")))
async def admin_shop_request_availability(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request availability dates for editing."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_item_id=item_id)

    text = """✏️ **Configurar Disponibilidad Temporal**

Este producto estará disponible solo en un período específico.

**¿Desde cuándo estará disponible?**

Ingresa la fecha de inicio (formato: DD/MM/AAAA)
Ejemplo: 01/12/2025

💡 Deja vacío si quieres que esté disponible desde ahora.
Escribe "ahora" para disponibilidad inmediata."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Desde ahora", callback_data=f"edit_avail_from_now:{item_id}")
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:availability:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_request_availability_{item_id}"
    )
    await state.set_state(AdminShopStates.editing_availability)
    await callback.answer()


@router.callback_query(AdminShopStates.editing_availability, F.data.startswith("edit_avail_from_now:"))
async def admin_shop_edit_avail_from_now(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set available_from to None (immediate) when editing."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_avail_from=None)

    text = """✏️ **Configurar Disponibilidad Temporal**

✅ Disponible desde: **Ahora**

**¿Hasta cuándo estará disponible?**

Ingresa la fecha de finalización (formato: DD/MM/AAAA)
Ejemplo: 31/12/2025

⚠️ Después de esta fecha, el producto dejará de aparecer en la tienda."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:availability:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_avail_until_{item_id}"
    )
    # Stay in editing_availability state to receive the until date
    await callback.answer()


@router.message(AdminShopStates.editing_availability)
async def admin_shop_edit_availability_receive(message: Message, state: FSMContext, session: AsyncSession):
    """Receive availability dates when editing."""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    item_id = data.get('editing_item_id')

    if not item_id:
        await message.answer("❌ Error: sesión expirada")
        await state.clear()
        return

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    from datetime import datetime

    date_str = message.text.strip().lower()

    # Check if we're setting the "from" date or "until" date
    if 'editing_avail_from' not in data:
        # Setting the "from" date
        if date_str == "ahora":
            await state.update_data(editing_avail_from=None)
            from_text = "Ahora"
        else:
            try:
                available_from = datetime.strptime(date_str, "%d/%m/%Y")
                await state.update_data(editing_avail_from=available_from)
                from_text = available_from.strftime('%d/%m/%Y')
            except ValueError:
                await message.answer("❌ Formato de fecha inválido. Usa DD/MM/AAAA (ej: 01/12/2025):")
                return

        text = f"""✏️ **Configurar Disponibilidad Temporal**

✅ Disponible desde: **{from_text}**

**¿Hasta cuándo estará disponible?**

Ingresa la fecha de finalización (formato: DD/MM/AAAA)
Ejemplo: 31/12/2025

⚠️ Después de esta fecha, el producto dejará de aparecer en la tienda."""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancelar", callback_data=f"edit_field:availability:{item_id}")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
        # Stay in editing_availability state to receive the until date
    else:
        # Setting the "until" date
        try:
            available_until = datetime.strptime(date_str, "%d/%m/%Y")

            # Validate that until is after from (if from exists)
            avail_from = data.get('editing_avail_from')

            if avail_from and available_until < avail_from:
                await message.answer("❌ La fecha de finalización debe ser posterior a la fecha de inicio. Intenta de nuevo:")
                return

            # Update the item
            item.available_from = avail_from
            item.available_until = available_until
            await session.commit()

            # Build success message
            from_text = "Ahora" if avail_from is None else avail_from.strftime('%d/%m/%Y')
            until_text = available_until.strftime('%d/%m/%Y')

            text = f"""✅ **Disponibilidad Actualizada**

**Producto:** {item.name}

Disponibilidad configurada:
⏰ **{from_text} - {until_text}**

El producto solo aparecerá en la tienda durante este período."""

            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
            builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
            builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
            builder.adjust(1)

            await message.answer(text, reply_markup=builder.as_markup())
            await state.clear()

        except ValueError:
            await message.answer("❌ Formato de fecha inválido. Usa DD/MM/AAAA (ej: 31/12/2025):")
            return


@router.callback_query(F.data.startswith("edit_field:requirements:"))
async def admin_shop_edit_requirements_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing unlock requirements for a product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    item = await session.get(ShopItem, item_id)

    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    await state.update_data(editing_item_id=item_id)

    # Get current requirements summary
    from services.condition_checker import ConditionChecker
    checker = ConditionChecker(session)
    req_summary = await checker.get_requirements_summary(item.unlock_requirements)

    text = f"""🔐 **Editar Requisitos de Desbloqueo**

**Producto:** {item.name}

**Requisitos actuales:**
{req_summary}

**Plantillas Rápidas:**
Selecciona una plantilla o configura manualmente."""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Quick templates
    builder.button(text="👑 Solo VIP", callback_data=f"req_template:vip:{item_id}")
    builder.button(text="⭐ Nivel 5+", callback_data=f"req_template:level5:{item_id}")
    builder.button(text="💎 VIP + Nivel 10", callback_data=f"req_template:vip_level10:{item_id}")
    builder.button(text="❌ Sin Requisitos", callback_data=f"req_template:none:{item_id}")
    builder.button(text="⚙️ Manual (JSON)", callback_data=f"req_manual:{item_id}")
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_edit:{item_id}")
    builder.adjust(2, 2, 1, 1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_edit_requirements_{item_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("req_template:"))
async def admin_shop_apply_requirement_template(callback: CallbackQuery, session: AsyncSession):
    """Apply a requirement template to a product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    parts = callback.data.split(":")
    template = parts[1]
    item_id = int(parts[2])

    item = await session.get(ShopItem, item_id)
    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Apply template
    if template == "none":
        item.unlock_requirements = None
        template_name = "Sin requisitos"
    elif template == "vip":
        item.unlock_requirements = {
            "operator": "AND",
            "conditions": [
                {"type": "vip_status", "value": True}
            ]
        }
        template_name = "👑 Solo VIP"
    elif template == "level5":
        item.unlock_requirements = {
            "operator": "AND",
            "conditions": [
                {"type": "level", "value": 5, "comparison": ">="}
            ]
        }
        template_name = "⭐ Nivel 5+"
    elif template == "vip_level10":
        item.unlock_requirements = {
            "operator": "AND",
            "conditions": [
                {"type": "vip_status", "value": True},
                {"type": "level", "value": 10, "comparison": ">="}
            ]
        }
        template_name = "💎 VIP + Nivel 10"
    else:
        await callback.answer("Plantilla no válida", show_alert=True)
        return

    await session.commit()

    text = f"""✅ **Requisitos Actualizados**

**Producto:** {item.name}

**Plantilla aplicada:** {template_name}

Los usuarios ahora deben cumplir estos requisitos para ver este producto en la tienda."""

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
        f"admin_shop_requirements_updated_{item_id}"
    )
    await callback.answer("✅ Requisitos aplicados")


@router.callback_query(F.data.startswith("req_manual:"))
async def admin_shop_manual_requirements(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Request manual JSON requirements configuration."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_item_id=item_id)

    text = """🔐 **Configuración Manual de Requisitos**

Envía un JSON con la estructura de requisitos.

**Ejemplo - Solo VIP:**
```json
{
  "operator": "AND",
  "conditions": [
    {"type": "vip_status", "value": true}
  ]
}
```

**Ejemplo - Nivel 5 + 100 puntos:**
```json
{
  "operator": "AND",
  "conditions": [
    {"type": "level", "value": 5, "comparison": ">="},
    {"type": "points", "value": 100, "comparison": ">="}
  ]
}
```

**Tipos soportados:**
• `level` - Nivel del usuario
• `vip_status` - Estado VIP (true/false)
• `owns_item` - Posee item (ID o nombre)
• `points` - Cantidad de puntos
• `owns_lore_piece` - Desbloque narrativo
• `completed_mission` - Misión completada

**Operadores:** `AND`, `OR`
**Comparaciones:** `>=`, `>`, `==`, `<`, `<=`"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancelar", callback_data=f"edit_field:requirements:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"admin_shop_manual_requirements_{item_id}"
    )
    await state.set_state(AdminShopStates.editing_requirements)
    await callback.answer()


@router.message(AdminShopStates.editing_requirements)
async def admin_shop_receive_manual_requirements(message: Message, state: FSMContext, session: AsyncSession):
    """Receive and validate manual JSON requirements."""
    if not await is_admin(message.from_user.id, session):
        return

    data = await state.get_data()
    item_id = data.get('editing_item_id')

    if not item_id:
        await message.answer("❌ Error: sesión expirada")
        await state.clear()
        return

    item = await session.get(ShopItem, item_id)
    if not item:
        await message.answer("❌ Producto no encontrado")
        await state.clear()
        return

    import json

    try:
        # Parse JSON
        requirements = json.loads(message.text)

        # Basic validation
        if not isinstance(requirements, dict):
            await message.answer("❌ El JSON debe ser un objeto ({})")
            return

        if "operator" not in requirements or "conditions" not in requirements:
            await message.answer("❌ El JSON debe tener 'operator' y 'conditions'")
            return

        if requirements["operator"] not in ["AND", "OR"]:
            await message.answer("❌ El operador debe ser 'AND' o 'OR'")
            return

        if not isinstance(requirements["conditions"], list):
            await message.answer("❌ 'conditions' debe ser una lista")
            return

        # Update item
        item.unlock_requirements = requirements
        await session.commit()

        # Get summary
        from services.condition_checker import ConditionChecker
        checker = ConditionChecker(session)
        summary = await checker.get_requirements_summary(requirements)

        text = f"""✅ **Requisitos Actualizados**

**Producto:** {item.name}

**Requisitos configurados:**
{summary}

Los requisitos han sido aplicados exitosamente."""

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Editar Otro Campo", callback_data=f"admin_shop_edit:{item_id}")
        builder.button(text="👁️ Ver Producto", callback_data=f"admin_shop_view:{item_id}")
        builder.button(text="🔙 Lista de Productos", callback_data="admin_shop_list")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
        await state.clear()

    except json.JSONDecodeError as e:
        await message.answer(f"❌ JSON inválido: {str(e)}\n\nAsegúrate de usar comillas dobles (\") y formato JSON válido.")
    except Exception as e:
        logger.error(f"Error setting requirements: {e}")
        await message.answer(f"❌ Error: {str(e)}")


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
            current_unlock = f"🔓 Pista: {lore_piece.title} (`{lore_piece.code_name}`)"
    if item.unlocks_fragment_key:
        if current_unlock == "No desbloquea contenido":
            current_unlock = f"📖 Fragmento: `{item.unlocks_fragment_key}`"
        else:
            current_unlock += f"\n📖 Fragmento: `{item.unlocks_fragment_key}`"

    # Get all lore pieces
    result = await session.execute(select(LorePiece).order_by(LorePiece.title))
    lore_pieces = result.scalars().all()

    # Get all story fragments
    from database.narrative_models import StoryFragment
    fragments_result = await session.execute(select(StoryFragment).order_by(StoryFragment.key))
    fragments = fragments_result.scalars().all()

    text = f"""✏️ **Editar Desbloqueo**

**Producto:** {item.name}
**Desbloqueo actual:** {current_unlock}

Selecciona qué contenido desbloqueará este producto:

**Pistas Narrativas (LorePieces):**"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for lore in lore_pieces[:10]:
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
            callback_data=f"set_unlock_lore:{item_id}:{lore.id}"
        )

    # Add separator
    builder.button(text="━━━ Fragmentos de Historia ━━━", callback_data="noop")

    # Add story fragments
    for fragment in fragments[:10]:
        prefix = "✅ " if item.unlocks_fragment_key == fragment.key else ""
        builder.button(
            text=f"{prefix}📖 {fragment.key}",
            callback_data=f"set_unlock_fragment:{item_id}:{fragment.key}"
        )

    builder.button(text="❌ Sin Desbloqueo", callback_data=f"set_unlock_none:{item_id}")
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


@router.callback_query(F.data.startswith("set_unlock_lore:"))
async def admin_shop_set_unlock_lore(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set lore piece unlock for product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    parts = callback.data.split(":")
    item_id = int(parts[1])
    lore_id = int(parts[2])

    item = await session.get(ShopItem, item_id)
    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    lore_piece = await session.get(LorePiece, lore_id)
    if not lore_piece:
        await callback.answer("Contenido no encontrado", show_alert=True)
        return

    item.unlocks_lore_piece_id = lore_id
    await session.commit()

    text = f"""✅ **Desbloqueo Actualizado**

**Producto:** {item.name}
**Desbloquea:** 🔓 Pista: {lore_piece.title}

El producto ahora desbloqueará esta pista narrativa al comprarlo."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"shop_unlock_set_{item_id}"
    )
    await callback.answer("✅ Desbloqueo actualizado", show_alert=False)


@router.callback_query(F.data.startswith("set_unlock_fragment:"))
async def admin_shop_set_unlock_fragment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set story fragment unlock for product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    parts = callback.data.split(":")
    item_id = int(parts[1])
    fragment_key = parts[2]

    item = await session.get(ShopItem, item_id)
    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    # Verify fragment exists
    from database.narrative_models import StoryFragment
    stmt = select(StoryFragment).where(StoryFragment.key == fragment_key)
    fragment_result = await session.execute(stmt)
    fragment = fragment_result.scalar_one_or_none()

    if not fragment:
        await callback.answer("Fragmento no encontrado", show_alert=True)
        return

    item.unlocks_fragment_key = fragment_key
    await session.commit()

    text = f"""✅ **Desbloqueo Actualizado**

**Producto:** {item.name}
**Desbloquea:** 📖 Fragmento: `{fragment_key}`

El producto ahora llevará al usuario directamente a este fragmento de historia al comprarlo."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"shop_unlock_set_{item_id}"
    )
    await callback.answer("✅ Desbloqueo actualizado", show_alert=False)


@router.callback_query(F.data.startswith("set_unlock_none:"))
async def admin_shop_set_unlock_none(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Remove all unlocks from product."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    item_id = int(callback.data.split(":")[-1])

    item = await session.get(ShopItem, item_id)
    if not item:
        await callback.answer("Producto no encontrado", show_alert=True)
        return

    item.unlocks_lore_piece_id = None
    item.unlocks_fragment_key = None
    await session.commit()

    text = f"""✅ **Desbloqueo Eliminado**

**Producto:** {item.name}
**Desbloquea:** Nada

El producto ya no desbloqueará ningún contenido al comprarlo."""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=f"admin_shop_view:{item_id}")
    builder.adjust(1)

    await update_menu(
        callback,
        text,
        builder.as_markup(),
        session,
        f"shop_unlock_removed_{item_id}"
    )
    await callback.answer("✅ Desbloqueo eliminado", show_alert=False)


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
