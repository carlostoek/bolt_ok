# Shop Product Availability Scheduling

## Overview

The **Availability Scheduling** feature (Mejora #5) enables temporal control over shop products, allowing administrators to create time-limited offerings, event-based items, pre-orders, and seasonal content.

**Date Added**: 2025-09-30
**Feature ID**: SHOP-AVAILABILITY-001
**Dependencies**: Mejora #4 (Stock and Purchase Limits)

## Key Features

### 1. Temporal Product Availability
Products can be configured to appear in the shop only during specific time periods:
- **Always Available** (default): No date restrictions
- **Available From**: Product appears starting from a specific date
- **Available Until**: Product disappears after a specific date
- **Time Window**: Both start and end dates (event-based items)

### 2. Date Format
- Input format: **DD/MM/YYYY** (user-friendly Spanish format)
- Example: `01/12/2025` for December 1st, 2025
- Shortcut: Type `"ahora"` for immediate availability

### 3. NULL Semantics
- `available_from = NULL`: Available immediately (no start restriction)
- `available_until = NULL`: Available forever (no end restriction)
- Both NULL: Always available (default behavior)

## Database Schema

### New Fields in `shop_items` Table

```sql
ALTER TABLE shop_items
ADD COLUMN available_from DATETIME;

ALTER TABLE shop_items
ADD COLUMN available_until DATETIME;
```

**Field Details:**
- `available_from`: DateTime, nullable - Product becomes visible in shop after this date
- `available_until`: DateTime, nullable - Product becomes hidden from shop after this date

## Admin Interface

### Product Creation Flow

The availability configuration is **Step 8** in the product creation wizard:

**Step 8: Disponibilidad Temporal**

Options:
1. **⏰ Sí, es temporal** - Configure start and end dates
2. **♾️ Siempre disponible** - No time restrictions (skip to Step 9)

When selecting "Sí, es temporal":

**Substep 8a: Fecha de Inicio (Start Date)**
- Prompt: "¿Desde cuándo estará disponible?"
- Input: DD/MM/YYYY or "ahora"
- Button: "⏭️ Desde ahora" (sets `available_from = NULL`)

**Substep 8b: Fecha de Finalización (End Date)**
- Prompt: "¿Hasta cuándo estará disponible?"
- Input: DD/MM/YYYY
- Validation: End date must be after start date

### Product Editing

Access via: Admin → Tienda → [Select Product] → Editar → 📅 Disponibilidad

**Edit Menu Options:**

For products with temporal availability:
- **📅 Cambiar Fechas** - Modify existing dates
- **♾️ Hacer Permanente** - Remove date restrictions

For always-available products:
- **⏰ Establecer Período** - Add date restrictions

## User Experience

### Shop Filtering

Products are automatically filtered based on current date:

```python
now = datetime.now()

# Hide if not yet available
if item.available_from and now < item.available_from:
    continue  # Don't show

# Hide if no longer available
if item.available_until and now > item.available_until:
    continue  # Don't show
```

### Purchase Validation

The shop service validates availability at purchase time:

```python
# Check if product is available now
now = datetime.now()

if item.available_from and now < item.available_from:
    return {
        "success": False,
        "message": f"❌ {item.name} aún no está disponible.
                     Estará disponible desde {item.available_from.strftime('%d/%m/%Y')}."
    }

if item.available_until and now > item.available_until:
    return {
        "success": False,
        "message": f"❌ {item.name} ya no está disponible.
                     Estuvo disponible hasta {item.available_until.strftime('%d/%m/%Y')}."
    }
```

### Visual Indicators

**Admin Product List:**
```
✅ 👑 🔓 ⏰ **📓 Diario Especial Navidad**
   💰 50 besitos
```
- ⏰ emoji indicates temporal availability

**Admin Product View:**
```
• 📅 Disponibilidad: ⏰ Temporal (01/12/2025 - 31/12/2025)
```
Shows the full date range

## Use Cases

### 1. Event-Based Items
**Scenario**: Christmas special diary entry

```
Name: "📓 Diario Especial Navidad"
Price: 50 besitos
Available From: 01/12/2025
Available Until: 31/12/2025
```

**Behavior**:
- Appears in shop on December 1st, 2025
- Disappears from shop on January 1st, 2026
- Users can still access purchased content after expiration

### 2. Pre-Order / Coming Soon
**Scenario**: New content preview

```
Name: "🎬 Próximo Capítulo - Avance"
Price: 30 besitos
Available From: 15/01/2026
Available Until: NULL (forever)
```

**Behavior**:
- Hidden from shop until January 15th, 2026
- Becomes permanently available after that date
- Creates anticipation for new content

### 3. Limited Time Offer
**Scenario**: Flash sale

```
Name: "💎 Pack Premium - Oferta Limitada"
Price: 80 besitos (discounted)
Available From: NULL (now)
Available Until: 28/02/2026
```

**Behavior**:
- Available immediately
- Disappears after February 28th, 2026
- Creates urgency for users to purchase

### 4. Seasonal Content
**Scenario**: Summer exclusive

```
Name: "🏖️ Memorias de Verano"
Price: 40 besitos
Available From: 21/06/2025
Available Until: 23/09/2025
```

**Behavior**:
- Available only during summer months
- Automatically hidden in other seasons
- Can be reused annually by updating dates

## Technical Implementation

### Files Modified

1. **`database/models.py`** (lines 484-485)
   - Added `available_from` and `available_until` DateTime columns

2. **`utils/admin_state.py`** (lines 205-207)
   - Added FSM states: `configuring_availability`, `entering_available_from`, `entering_available_until`
   - Added edit state: `editing_availability`

3. **`handlers/admin/shop_admin.py`**
   - Lines 654-831: Creation flow handlers
   - Lines 917, 1028: Updated `ShopItem` creation to include date fields
   - Lines 1961-2236: Edit handlers for availability
   - Lines 145-168: Updated product view to show availability info
   - Lines 86-95: Updated product list to show ⏰ indicator

4. **`services/shop_service.py`**
   - Lines 43-57: Added date filtering in `get_available_items()`
   - Lines 207-219: Added date validation in `purchase_item()`

### Key Functions

**Creation Flow:**
```python
async def proceed_to_availability_config(callback, state, session)
async def admin_shop_create_availability_none(callback, state, session)
async def admin_shop_create_availability_request(callback, state, session)
async def admin_shop_avail_from_now(callback, state, session)
async def admin_shop_avail_from_receive(message, state, session)
async def admin_shop_avail_until_receive(message, state, session)
```

**Edit Flow:**
```python
async def admin_shop_edit_availability_start(callback, state, session)
async def admin_shop_permanent_availability(callback, session)
async def admin_shop_request_availability(callback, state, session)
async def admin_shop_edit_avail_from_now(callback, state, session)
async def admin_shop_edit_availability_receive(message, state, session)
```

## Migration

### Running the Migration

```bash
cd /home/azureuser/repos/bolt_ok/mybot
python migrations/add_availability_fields_to_shop_items.py
```

### Migration Script
- Location: `migrations/add_availability_fields_to_shop_items.py`
- Adds two nullable DateTime columns
- Checks if columns already exist (idempotent)
- Verifies successful migration

### Post-Migration Steps
1. Restart the bot
2. All existing products default to "always available" (both fields NULL)
3. Create new products with availability or edit existing ones

## Best Practices

### 1. Planning Time-Limited Content
- **Advance Notice**: Create products at least 1 week before `available_from` date
- **Testing**: Test with near-future dates first (e.g., tomorrow)
- **Communication**: Announce limited-time items to users in advance

### 2. Combining with Stock Limits
```
Name: "🎁 Black Friday Bundle"
Price: 100 besitos
Stock: 50 units
Available From: 29/11/2025
Available Until: 30/11/2025
Max Purchases/User: 1
```
Creates a time-limited, stock-limited, single-purchase exclusive item.

### 3. Recurring Events
For annual events, update the dates each year:
- Keep the same product ID
- Update `available_from` and `available_until` to next year's dates
- Previous purchases remain valid

### 4. Timezone Considerations
- All dates use server timezone
- DateTime comparisons use `datetime.now()` (server local time)
- **Future Enhancement**: Could add timezone configuration

## Troubleshooting

### Problem: Product not appearing in shop

**Checklist:**
1. Is `is_active = True`?
2. Check `available_from` - is it in the future?
3. Check `available_until` - has it passed?
4. Is user VIP (if product is VIP-only)?
5. Has user reached purchase limit?
6. Is product sold out (stock limit)?

**Debug Query:**
```sql
SELECT name, is_active, available_from, available_until,
       datetime('now') as current_time
FROM shop_items
WHERE id = ?;
```

### Problem: Product appeared too early/late

**Solution:**
- Verify server timezone: `date` command
- Check date parsing - ensure DD/MM/YYYY format
- Review `available_from` value in database

**Query to check:**
```sql
SELECT name, available_from,
       julianday(available_from) - julianday('now') as days_until_available
FROM shop_items
WHERE available_from IS NOT NULL;
```

### Problem: Users can't purchase but product is visible

**Diagnosis:**
Product might be visible due to past purchases (inventory view) but no longer available for new purchases.

**Solution:**
Check both:
1. `shop_items.available_until` - purchase restriction
2. `user_purchases` - users who already bought still see it in inventory

## API Examples

### Creating a Temporal Product via Shell

```python
from datetime import datetime
from database.models import ShopItem

item = ShopItem(
    name="🎃 Especial Halloween",
    description="Contenido exclusivo de terror",
    price=40,
    is_vip_only=False,
    available_from=datetime(2025, 10, 25),
    available_until=datetime(2025, 11, 1),
    stock_limit=100,
    max_purchases_per_user=1,
    is_active=True
)
session.add(item)
await session.commit()
```

### Extending Product Availability

```python
item = await session.get(ShopItem, item_id)
item.available_until = datetime(2025, 12, 31)  # Extend until end of year
await session.commit()
```

### Making Product Permanent

```python
item = await session.get(ShopItem, item_id)
item.available_from = None
item.available_until = None
await session.commit()
```

## Future Enhancements

### Potential Improvements

1. **Timezone Support**
   - Allow admin to specify timezone
   - Convert to user's local timezone for display

2. **Recurring Schedules**
   - Weekly availability (e.g., "Weekend Specials")
   - Monthly cycles (e.g., "First Monday of each month")

3. **Advance Notifications**
   - Notify users 24h before product becomes available
   - Notify users 24h before product expires

4. **Countdown Timers**
   - Show "Available in X days" for future items
   - Show "Expires in X hours" for ending items

5. **Auto-Pricing**
   - Discount prices as expiration approaches
   - Dynamic pricing based on remaining time

6. **Analytics**
   - Track views vs purchases for temporal items
   - Measure effectiveness of time-limited offers

## Related Documentation

- `docs/admin_shop_stock_feature.md` - Mejora #4 (Stock and Purchase Limits)
- `migrations/add_stock_fields_to_shop_items.py` - Previous migration
- `migrations/add_availability_fields_to_shop_items.py` - This feature's migration
- `database/models.py:472-489` - ShopItem model definition

## Support

For issues with this feature:
1. Check logs: `logger.info` statements in `shop_service.py`
2. Verify database: Query `shop_items` table directly
3. Test with near-future dates (tomorrow) for quick validation

## Changelog

**2025-09-30** - Initial implementation (Mejora #5)
- Added `available_from` and `available_until` fields
- Implemented creation and edit flows
- Added filtering logic in `ShopService`
- Created migration script
- Added visual indicators (⏰ emoji)
- Comprehensive documentation
