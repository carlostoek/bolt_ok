# Shop Product Compound Requirements System

## Overview

The **Compound Requirements System** (Mejora #6) enables complex unlock conditions for shop products, allowing administrators to create exclusive items that require users to meet multiple criteria before they can see or purchase them.

**Date Added**: 2025-09-30
**Feature ID**: SHOP-REQUIREMENTS-001
**Dependencies**: Mejora #4, #5, ConditionChecker service

## Key Features

### 1. Flexible Condition Types
- **`level`**: User level requirements (>=, >, ==, <, <=)
- **`vip_status`**: VIP subscription status (true/false)
- **`owns_item`**: Ownership of another shop item (by ID or name)
- **`points`**: User points (besitos) requirements
- **`owns_lore_piece`**: Unlocked narrative pieces (by code_name)
- **`completed_mission`**: Completed missions (by mission_id)

### 2. Logical Operators
- **`AND`**: All conditions must be met
- **`OR`**: At least one condition must be met

### 3. Quick Templates
Pre-configured templates for common scenarios:
- 👑 **Solo VIP**: Only for VIP users
- ⭐ **Nivel 5+**: Requires level 5 or higher
- 💎 **VIP + Nivel 10**: Requires both VIP and level 10

### 4. Manual JSON Configuration
For advanced users, full JSON configuration is supported for complex compound conditions.

## Database Schema

### New Field in `shop_items` Table

```sql
ALTER TABLE shop_items
ADD COLUMN unlock_requirements JSON;
```

**Field Details:**
- `unlock_requirements`: JSON, nullable - Compound conditions for unlock (NULL = no requirements)

## JSON Structure

```json
{
  "operator": "AND",  // "AND" or "OR"
  "conditions": [
    {
      "type": "level",
      "value": 5,
      "comparison": ">="
    },
    {
      "type": "vip_status",
      "value": true
    },
    {
      "type": "points",
      "value": 100,
      "comparison": ">="
    }
  ]
}
```

## Admin Interface

### Accessing Requirements Configuration

Admin → Tienda → [Select Product] → Editar → 🔐 Requisitos

### Quick Templates

**1. Solo VIP**
```json
{
  "operator": "AND",
  "conditions": [
    {"type": "vip_status", "value": true}
  ]
}
```

**2. Nivel 5+**
```json
{
  "operator": "AND",
  "conditions": [
    {"type": "level", "value": 5, "comparison": ">="}
  ]
}
```

**3. VIP + Nivel 10**
```json
{
  "operator": "AND",
  "conditions": [
    {"type": "vip_status", "value": true},
    {"type": "level", "value": 10, "comparison": ">="}
  ]
}
```

### Manual JSON Configuration

For complex requirements, use the ⚙️ Manual (JSON) option:

**Example: VIP OR (Nivel 15 AND 200 puntos)**
```json
{
  "operator": "OR",
  "conditions": [
    {"type": "vip_status", "value": true},
    {"type": "level", "value": 15, "comparison": ">="},
    {"type": "points", "value": 200, "comparison": ">="}
  ]
}
```

**Note**: When using `OR`, users need to meet ANY of the conditions.

## Condition Types Reference

### 1. Level Condition
```json
{
  "type": "level",
  "value": 10,
  "comparison": ">="
}
```
- **Comparisons**: `>=`, `>`, `==`, `<`, `<=`
- **Example**: User must be level 10 or higher

### 2. VIP Status
```json
{
  "type": "vip_status",
  "value": true
}
```
- **value**: `true` (requires VIP) or `false` (requires Free user)

### 3. Owns Item
```json
{
  "type": "owns_item",
  "value": 5
}
```
or
```json
{
  "type": "owns_item",
  "value": "📓 Diario Íntimo"
}
```
- **value**: Item ID (integer) or Item name (string)
- User must have previously purchased the specified item

### 4. Points (Besitos)
```json
{
  "type": "points",
  "value": 150,
  "comparison": ">="
}
```
- **Comparisons**: `>=`, `>`, `==`, `<`, `<=`
- **Example**: User must have at least 150 besitos

### 5. Owns Lore Piece
```json
{
  "type": "owns_lore_piece",
  "value": "diario_secreto_diana"
}
```
- **value**: Lore piece `code_name`
- User must have unlocked the narrative piece

### 6. Completed Mission
```json
{
  "type": "completed_mission",
  "value": "mision_especial_1"
}
```
- **value**: Mission `id`
- User must have completed the mission

## Technical Implementation

### Files Created/Modified

1. **`database/models.py`** (line 486)
   - Added `unlock_requirements` JSON column

2. **`services/condition_checker.py`** (NEW FILE)
   - `ConditionChecker` class with requirement evaluation logic
   - Methods for checking each condition type
   - Human-readable summary generation

3. **`utils/admin_state.py`** (lines 218, 224-226)
   - Added FSM states for requirements configuration

4. **`handlers/admin/shop_admin.py`**
   - Lines 1144: Added "🔐 Requisitos" button to edit menu
   - Lines 2268-2532: Requirements configuration handlers
   - Lines 171-178: Show requirements in product view
   - Line 91: Show 🔐 indicator in product list

5. **`services/shop_service.py`**
   - Lines 87-95: Filter items by requirements in `get_available_items()`
   - Lines 231-243: Validate requirements in `purchase_item()`

### ConditionChecker Service

**Key Methods:**
```python
async def check_requirements(
    user_id: int,
    requirements: Optional[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """Returns (meets_requirements, failed_conditions)"""

async def get_requirements_summary(
    requirements: Optional[Dict[str, Any]]
) -> str:
    """Returns human-readable summary"""
```

## Use Cases

### 1. Progressive Unlock System
**Scenario**: Advanced diary entry for experienced users

```json
{
  "operator": "AND",
  "conditions": [
    {"type": "level", "value": 10, "comparison": ">="},
    {"type": "owns_item", "value": "📓 Diario Íntimo"},
    {"type": "points", "value": 100, "comparison": ">="}
  ]
}
```

**Effect**: Users must reach level 10, own the basic diary, and have 100 points to unlock.

### 2. VIP Exclusive with Level Gate
**Scenario**: Premium content for high-level VIPs

```json
{
  "operator": "AND",
  "conditions": [
    {"type": "vip_status", "value": true},
    {"type": "level", "value": 15, "comparison": ">="}
  ]
}
```

### 3. Alternative Paths (OR Logic)
**Scenario**: Item available through two different paths

```json
{
  "operator": "OR",
  "conditions": [
    {"type": "vip_status", "value": true},
    {"type": "points", "value": 300, "comparison": ">="}
  ]
}
```

**Effect**: Users can unlock either by being VIP OR by having 300+ points.

### 4. Story-Gated Content
**Scenario**: Item requires narrative progress

```json
{
  "operator": "AND",
  "conditions": [
    {"type": "owns_lore_piece", "value": "capitulo_3_revelacion"},
    {"type": "completed_mission", "value": "mision_verdad"}
  ]
}
```

## User Experience

### Filtering
Products with requirements that users don't meet are **completely hidden** from the shop. Users only see items they can purchase.

### Purchase Validation
If somehow a user attempts to purchase (e.g., requirements changed after they opened shop), they receive clear error messages:

```
❌ No cumples los requisitos para 📓 Diario Exclusivo:

• Requiere nivel >= 10 (tienes nivel 7)
• Requiere suscripción VIP
```

### Visual Indicators

**Admin Product List:**
```
✅ 👑 🔓 ⏰ 🔐 **📓 Diario Secreto Premium**
   💰 150 besitos
```
- 🔐 emoji indicates product has unlock requirements

**Admin Product View:**
```
🔐 **Requisitos:**
Ser VIP Y Nivel >= 10
```

## Best Practices

### 1. Clear User Communication
- Combine with descriptive product names
- Use requirements to create clear progression paths

### 2. Avoid Circular Dependencies
❌ **Bad**: Item A requires Item B, Item B requires Item A
✅ **Good**: Linear or branching progression

### 3. Test Requirements
Before publishing, test with a test user account to verify:
- Requirements are achievable
- Error messages are clear
- Logic works as expected

### 4. Combine with Other Features
```json
{
  "name": "🏆 Pack Exclusivo Fin de Mes",
  "price": 200,
  "unlock_requirements": {
    "operator": "AND",
    "conditions": [
      {"type": "vip_status", "value": true},
      {"type": "level", "value": 5, "comparison": ">="}
    ]
  },
  "available_from": "2025-09-25",
  "available_until": "2025-09-30",
  "stock_limit": 50,
  "max_purchases_per_user": 1
}
```

Creates a time-limited, stock-limited, single-purchase exclusive item for VIP users level 5+.

## Troubleshooting

### Problem: Users report item not appearing

**Checklist:**
1. Check `is_active = True`
2. Verify requirements using Admin → Ver Producto
3. Test with Admin account (admins bypass all requirements for testing)
4. Check logs for requirement failures

**Debug Query:**
```sql
SELECT name, unlock_requirements
FROM shop_items
WHERE id = ?;
```

### Problem: Requirements not saving

**Solution:**
- Ensure JSON is valid (use validator: jsonlint.com)
- Check for proper quoting (double quotes, not single)
- Verify operator is "AND" or "OR"

### Problem: Users shouldn't see item but do

**Diagnosis:**
Requirements might be too permissive or using `OR` when `AND` was intended.

**Fix:**
Review operator logic. With `OR`, users need to meet ANY condition.

## Migration

### Running the Migration

```bash
cd /home/azureuser/repos/bolt_ok/mybot
python migrations/add_unlock_requirements_to_shop_items.py
```

### Migration Script
- Location: `migrations/add_unlock_requirements_to_shop_items.py`
- Adds one nullable JSON column
- Idempotent (safe to run multiple times)

### Post-Migration
1. Restart bot
2. All existing products default to no requirements (NULL)
3. Configure requirements via Admin interface

## API Examples

### Programmatically Setting Requirements

```python
from database.models import ShopItem

item = await session.get(ShopItem, item_id)
item.unlock_requirements = {
    "operator": "AND",
    "conditions": [
        {"type": "level", "value": 10, "comparison": ">="},
        {"type": "vip_status", "value": True}
    ]
}
await session.commit()
```

### Checking Requirements for a User

```python
from services.condition_checker import ConditionChecker

checker = ConditionChecker(session)
meets_req, failed = await checker.check_requirements(
    user_id,
    item.unlock_requirements
)

if meets_req:
    print("User can purchase")
else:
    print(f"Failed conditions: {failed}")
```

## Future Enhancements

### Potential Improvements

1. **Time-Based Conditions**
   - Require user to be active for X days
   - Require account age

2. **Activity Conditions**
   - Require X messages sent
   - Require X reactions given

3. **Social Conditions**
   - Require X referrals
   - Require participation in specific events

4. **Negative Conditions**
   - "NOT owns_item" (doesn't own specific item)
   - More flexible exclusion logic

5. **UI Builder**
   - Visual drag-and-drop condition builder
   - No need for JSON knowledge

## Related Documentation

- `docs/admin_shop_stock_feature.md` - Mejora #4
- `docs/admin_shop_availability_feature.md` - Mejora #5
- `services/condition_checker.py` - Complete service code
- `migrations/add_unlock_requirements_to_shop_items.py` - Migration script

## Support

For issues with this feature:
1. Check logs in `services/shop_service.py` and `services/condition_checker.py`
2. Verify JSON structure with online validator
3. Test conditions with different user accounts
4. Review ConditionChecker implementation for supported types

## Changelog

**2025-09-30** - Initial implementation (Mejora #6)
- Added `unlock_requirements` JSON field
- Implemented ConditionChecker service with 6 condition types
- Created quick templates UI
- Added manual JSON configuration
- Integrated filtering in shop and purchase validation
- Added visual indicators (🔐 emoji)
- Created migration script
- Comprehensive documentation
