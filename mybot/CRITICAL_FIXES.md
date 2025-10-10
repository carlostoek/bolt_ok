# 🚨 CRITICAL FIXES - Progress Not Saving

## Issues Found

### Issue #1: State Machine race condition ✅ FIXED
- `return_from_shop` was clearing context before decision processing
- Fixed to be READ-ONLY operation

### Issue #2: Progress reset bug 🔍 INVESTIGATING
- User's current fragment is reset to "start" if fragment not found in DB
- Happens in `narrative_service.py:44-47`

## Root Cause Analysis

```python
# narrative_service.py line 40-47
current_fragment = await self._get_fragment_by_key(user_state.current_fragment_key)
if current_fragment:
    return current_fragment
else:
    # ❌ PROBLEM: Resets progress if fragment not found
    logger.warning(f"Fragmento {user_state.current_fragment_key} no encontrado...")
    user_state.current_fragment_key = None  # Wipes progress!
```

## Possible Causes

1. **Fragments not loaded in database**
   - Check if story fragments are properly seeded
   - Run: `SELECT key FROM story_fragments;`

2. **Fragment keys mismatch**
   - User has `current_fragment_key = "some_fragment"`
   - But fragment in DB has different key

3. **Access level issues**
   - Fragment exists but user doesn't have access
   - `_get_fragment_by_key` returns None

## Investigation Steps

```bash
# 1. Check if fragments exist
psql mybot_db -c "SELECT key, level, character FROM story_fragments ORDER BY level, id LIMIT 20;"

# 2. Check user states
psql mybot_db -c "SELECT user_id, current_fragment_key, fragments_visited FROM user_narrative_state LIMIT 10;"

# 3. Check for orphaned fragment keys
psql mybot_db -c "
SELECT DISTINCT uns.current_fragment_key
FROM user_narrative_state uns
LEFT JOIN story_fragments sf ON uns.current_fragment_key = sf.key
WHERE uns.current_fragment_key IS NOT NULL
  AND sf.key IS NULL;
"
```

## Recommended Fix

### Option A: Better error handling (SAFER)
```python
if current_fragment:
    return current_fragment
else:
    # DON'T reset - log error and try recovery
    logger.error(
        f"[CRITICAL] Fragment '{user_state.current_fragment_key}' not found for user {user_id}. "
        f"Attempting recovery..."
    )

    # Try to find a safe fallback
    # Option 1: Try parent fragment
    # Option 2: Try "start" but DON'T clear current_fragment_key (preserve for debugging)
    # Option 3: Alert admin

    # For now, return start but keep the broken state visible
    return await self._get_fragment_by_key("start")
```

### Option B: Data validation (PREVENTIVE)
Add validation when setting `current_fragment_key`:
```python
async def _validate_and_set_fragment(self, user_id: int, fragment_key: str):
    # Verify fragment exists before setting
    fragment = await self._get_fragment_by_key(fragment_key)
    if not fragment:
        raise ValueError(f"Cannot set non-existent fragment: {fragment_key}")

    user_state = await self._get_or_create_user_state(user_id)
    user_state.current_fragment_key = fragment_key
    await self.session.commit()
```

## Action Items

- [ ] Run database queries to check fragment data
- [ ] Add comprehensive logging to `_get_fragment_by_key`
- [ ] Fix the reset logic
- [ ] Add data validation
- [ ] Create migration to fix any corrupted user states
