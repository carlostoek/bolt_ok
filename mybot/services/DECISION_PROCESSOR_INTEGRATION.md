# DecisionProcessor Integration Guide

## Overview

The `DecisionProcessor` service has been extracted from `CoordinadorCentral` to follow the Single Responsibility Principle (SRP). It handles all decision-specific logic including item requirements, teaser redirects, and special decision flows.

## File Location

```
/home/azureuser/repos/bolt_ok/mybot/services/decision_processor.py
```

## What Was Extracted

### From `coordinador_central.py` (lines 37-65, 358-568):

1. **`_load_decision_requirements()` function** - Loads item requirements from JSON config
2. **Item checking logic** - Validates if user has required items
3. **Special decision handling** - Processes teaser redirects (e.g., diary intimate)
4. **State machine transitions** - Shop redirect logic

## Class Structure

```python
class DecisionProcessor:
    """
    Handles special decision logic (item requirements, teasers, etc.)
    """

    def __init__(self, session: AsyncSession):
        """Initialize with ShopService and NarrativeService"""
        pass

    async def check_item_requirement(
        self,
        user_id: int,
        decision_id: int
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if decision requires an item.

        Returns:
            (has_item, required_item_name, teaser_fragment_key)
        """
        pass

    async def process_special_decision(
        self,
        user_id: int,
        decision_id: int,
        has_required_item: bool,
        teaser_fragment_key: Optional[str]
    ) -> Optional[StoryFragment]:
        """
        Handle special decision flows (teasers, redirects).

        Returns:
            StoryFragment if redirected, None otherwise
        """
        pass

    async def get_required_item_message(
        self,
        decision_id: int,
        required_item_name: str,
        character_voice_service=None
    ) -> str:
        """
        Generate user-friendly message for item requirements.
        """
        pass
```

## Integration into CoordinadorCentral

### Step 1: Import the Service

```python
# At top of coordinador_central.py
from services.decision_processor import DecisionProcessor
```

### Step 2: Initialize in `__init__`

```python
class CoordinadorCentral:
    def __init__(self, session: AsyncSession):
        self.session = session
        # ... existing services ...

        # NEW: Decision processor
        self.decision_processor = DecisionProcessor(session)
```

### Step 3: Replace Logic in `_flujo_tomar_decision`

**BEFORE (206 lines, complexity ~15):**

```python
async def _flujo_tomar_decision(self, user_id: int, decision_id: int, bot=None):
    # Load decision requirements
    decision_requirements = _load_decision_requirements()

    # Check if this decision requires an item
    required_item = decision_requirements.get(decision_id)
    if required_item:
        from services.shop_service import ShopService
        shop_service = ShopService(self.session)
        has_item = await shop_service.has_item_in_inventory(user_id, required_item)

        if not has_item:
            # ... 80+ lines of item handling logic ...

            # Special case for diary intimate
            if decision_id == DecisionID.DIARY_INTIMATE:
                teaser_fragment = await self.narrative_service._get_fragment_by_key("diana_diary_tease")
                # ... 20+ lines of teaser logic ...

            # ... more logic ...

    # ... 100+ more lines ...
```

**AFTER (cleaner, ~100 lines, complexity ~8):**

```python
async def _flujo_tomar_decision(self, user_id: int, decision_id: int, bot=None):
    """Flujo para manejar decisiones narrativas del usuario."""

    # Check item requirements using DecisionProcessor
    has_item, required_item, teaser_key = await self.decision_processor.check_item_requirement(
        user_id, decision_id
    )

    if not has_item and required_item:
        # Handle missing item scenario
        user_state = await self.narrative_service._get_or_create_user_state(user_id)

        # Transition to shop state
        transition_success = await self.narrative_state_machine.transition_to_shop(
            user_id=user_id,
            current_fragment_key=user_state.current_fragment_key,
            pending_decision_id=decision_id
        )

        if not transition_success:
            logger.error(f"Failed to transition user {user_id} to shop state")
            return {
                "success": False,
                "message": "No se pudo procesar la transición a la tienda.",
                "action": "state_transition_failed"
            }

        # Process special decisions (e.g., teaser redirects)
        special_fragment = await self.decision_processor.process_special_decision(
            user_id, decision_id, has_item, teaser_key
        )

        if special_fragment:
            # Special decision redirected to teaser
            return {
                "success": True,
                "fragment": special_fragment,
                "action": "decision_success"
            }

        # Standard item requirement message
        message = await self.decision_processor.get_required_item_message(
            decision_id, required_item, self.character_voice
        )

        return {
            "success": False,
            "message": message,
            "action": "item_required",
            "decision_id": decision_id,
            "required_item": required_item
        }

    # Proceed with normal decision flow (emotional analysis, etc.)
    # ... rest of the method ...
```

## Benefits

### 1. Single Responsibility Principle (SRP)
- `CoordinadorCentral` focuses on orchestration
- `DecisionProcessor` focuses on decision logic
- Each class has one reason to change

### 2. Reduced Complexity
- `_flujo_tomar_decision`: 206 → ~100 lines
- Cyclomatic complexity: 15 → ~8
- Easier to test and maintain

### 3. Better Testability
```python
# You can now test decision logic independently
async def test_check_item_requirement():
    processor = DecisionProcessor(session)
    has_item, item_name, teaser = await processor.check_item_requirement(
        user_id=12345,
        decision_id=DecisionID.DIARY_INTIMATE
    )
    assert has_item == False
    assert item_name == "📓 Diario Íntimo"
    assert teaser == "diana_diary_tease"
```

### 4. Reusability
- Can be used by other services that need decision validation
- Can be extended with new special decision types
- Independent of CoordinadorCentral

## Configuration

Decision requirements are managed via JSON:

```json
// /home/azureuser/repos/bolt_ok/mybot/config/decision_requirements.json
{
  "1": "📖 Diario Secreto",
  "15": "📓 Diario Íntimo",
  "3": "📖 Diario Secreto"
}
```

Managed through admin panel: **Admin → Tienda → Gestionar Desbloqueos**

## Special Decision Types

### 1. Diary Intimate (DecisionID.DIARY_INTIMATE = 15)
- **Behavior**: Redirects to teaser fragment instead of blocking
- **Teaser Fragment**: `diana_diary_tease`
- **Purpose**: Show preview of intimate content before purchase

### 2. Standard Item Decisions
- **Behavior**: Block with item requirement message
- **Redirect**: Transition to shop state
- **Purpose**: Prompt user to purchase required item

## Logging

All operations use `[DECISION_PROCESSOR]` prefix:

```
INFO [DECISION_PROCESSOR] Service initialized successfully
DEBUG [DECISION_PROCESSOR] Checking item requirement for user 12345, decision DIARY_INTIMATE (ID: 15)
INFO [DECISION_PROCESSOR] Special decision DIARY_INTIMATE has teaser fragment: diana_diary_tease
INFO [DECISION_PROCESSOR] Successfully redirected user 12345 to teaser fragment: diana_diary_tease
```

## Type Hints

Full type safety with Python type hints:

```python
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from database.narrative_models import StoryFragment
```

## Error Handling

Graceful degradation at every level:

1. **Config loading**: Falls back to hardcoded defaults
2. **Fragment loading**: Logs error, returns None
3. **Character voice**: Falls back to default message
4. **Database errors**: Logs exception, rolls back transaction

## Next Steps

After integration, you can:

1. **Remove old code** from `coordinador_central.py`:
   - Lines 37-65 (`_load_decision_requirements`)
   - Decision logic from `_flujo_tomar_decision`

2. **Add more special decisions**:
   ```python
   # In check_item_requirement
   if decision_id == DecisionID.SOME_NEW_DECISION:
       teaser_fragment_key = "some_new_teaser"

   # In process_special_decision
   if decision_id == DecisionID.SOME_NEW_DECISION:
       # Custom handling logic
       pass
   ```

3. **Create unit tests**:
   ```bash
   pytest tests/services/test_decision_processor.py -v
   ```

## Questions?

See the inline documentation in `/home/azureuser/repos/bolt_ok/mybot/services/decision_processor.py`

All methods have comprehensive docstrings with examples.
