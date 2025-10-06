# Mi Diván Localization - Before & After Examples

## Example 1: VIP Verification

### Before (Hardcoded)
```python
if role != "vip":
    await callback.answer(
        "🔐 Esta función es exclusiva para miembros VIP.",
        show_alert=True
    )
```

### After (Localized)
```python
if role != "vip":
    await callback.answer(
        get_text("midivan.vip_only"),
        show_alert=True
    )
```

## Example 2: Main Menu Text

### Before (Hardcoded)
```python
message_parts = [
    "💎 **Mi Diván - Espacio VIP Exclusivo**\n",
    "━━━━━━━━━━━━━━━━━━━━━"
]
```

### After (Localized)
```python
message_parts = [
    get_text("midivan.main_title"),
    get_text("midivan.divider")
]
```

## Example 3: Subscription Status

### Before (Hardcoded)
```python
if days_remaining > 30:
    status_emoji = "✨"
    status_text = "Activa"
elif days_remaining > 7:
    status_emoji = "⏰"
    status_text = f"Expira en {days_remaining} días"
```

### After (Localized)
```python
if days_remaining > 30:
    status_emoji = "✨"
    status_text = get_text("midivan.status_active")
elif days_remaining > 7:
    status_emoji = "⏰"
    status_text = get_text("midivan.status_expires_soon", days=days_remaining)
```

## Example 4: Quiz Introduction

### Before (Hardcoded)
```python
text = f"""💘 **{quiz.title}**

{quiz.description or "Descubre qué tan compatible eres con Diana respondiendo estas preguntas."}

━━━━━━━━━━━━━━━━━━━━━

**📝 Detalles:**
• {quiz.total_questions} preguntas
• Tiempo estimado: ~{quiz.total_questions} minutos
• Recompensa: {quiz.besitos_reward} besitos"""
```

### After (Localized)
```python
divider = get_text("midivan.divider")
description = quiz.description or get_text("midivan.quiz_intro_description")

text = f"""{get_text("midivan.quiz_intro_title", title=quiz.title)}

{description}

{divider}

{get_text("midivan.quiz_details_title")}
{get_text("midivan.quiz_questions_count", count=quiz.total_questions)}
{get_text("midivan.quiz_time_estimate", minutes=quiz.total_questions)}
{get_text("midivan.quiz_reward", besitos=quiz.besitos_reward)}"""
```

## Example 5: Compatibility Messages

### Before (Hardcoded)
```python
def _get_compatibility_message(score: float) -> str:
    if score >= 90:
        return (
            "💘 **¡Wow! Somos almas gemelas**\n\n"
            "Diana dice: \"Es como si me conocieras mejor que yo misma. "
            "Definitivamente hay una conexión especial aquí.\""
        )
```

### After (Localized)
```python
def _get_compatibility_message(score: float) -> str:
    if score >= 90:
        return get_text("midivan.compat_90_title") + get_text("midivan.compat_90_message")
```

## Example 6: Button Labels

### Before (Hardcoded)
```python
builder.button(
    text="💘 Test de Compatibilidad",
    callback_data="midivan:quiz"
)
builder.button(
    text="✉️ Mensaje Anónimo a Diana",
    callback_data="midivan:message"
)
```

### After (Localized)
```python
builder.button(
    text=get_text("midivan.button_compatibility_test"),
    callback_data="midivan:quiz"
)
builder.button(
    text=get_text("midivan.button_anonymous_message"),
    callback_data="midivan:message"
)
```

## Example 7: Error Messages

### Before (Hardcoded)
```python
except Exception as e:
    logger.error(f"Error showing Mi Diván menu: {e}")
    await callback.answer(
        "❌ Error al cargar Mi Diván. Intenta nuevamente.",
        show_alert=True
    )
```

### After (Localized)
```python
except Exception as e:
    logger.error(f"Error showing Mi Diván menu: {e}")
    await callback.answer(
        get_text("midivan.error_loading"),
        show_alert=True
    )
```

## Benefits Illustrated

### 1. Consistency
All "Volver a Mi Diván" buttons now use the same key:
```python
get_text("midivan.button_back_midivan")  # Used everywhere
```

### 2. Reusability
VIP check message is used in 5+ places:
```python
get_text("midivan.vip_only")  # Same text, multiple locations
```

### 3. Easy Updates
Change "Mi Diván" branding? Just update ONE place:
```json
{
  "midivan": {
    "main_title": "💎 **Mi Diván Exclusivo VIP**\n",  // Single update point
  }
}
```

### 4. Parameter Support
Dynamic values work seamlessly:
```python
get_text("midivan.pending_notification", count=pending)
// Outputs: "🔔 Tienes 3 mensaje(s) esperando respuesta de Diana"
```
