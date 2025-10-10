"""
Example usage of DecisionProcessor service.

This file demonstrates how to use the DecisionProcessor for various scenarios.
Run with: python -m services.decision_processor_example
"""

import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_check_item_requirement():
    """
    Example: Check if a user has the required item for a decision.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Checking Item Requirements")
    print("="*80)

    # This is a mock example - in real usage, you'd have a database session
    # from services.decision_processor import DecisionProcessor
    # from config.decision_constants import DecisionID
    #
    # processor = DecisionProcessor(session)
    #
    # # Check if user 12345 can make decision 15 (Diary Intimate)
    # has_item, item_name, teaser_key = await processor.check_item_requirement(
    #     user_id=12345,
    #     decision_id=DecisionID.DIARY_INTIMATE
    # )
    #
    # if has_item:
    #     print(f"✅ User has required item: {item_name}")
    #     print("   → Proceed with decision")
    # else:
    #     print(f"❌ User missing item: {item_name}")
    #     if teaser_key:
    #         print(f"   → Redirect to teaser: {teaser_key}")
    #     else:
    #         print("   → Block with item requirement message")

    print("""
Expected Output (user WITHOUT item):
  has_item = False
  item_name = "📓 Diario Íntimo"
  teaser_key = "diana_diary_tease"

Expected Output (user WITH item):
  has_item = True
  item_name = "📓 Diario Íntimo"
  teaser_key = None
    """)


async def example_process_special_decision():
    """
    Example: Process special decision flow (teaser redirect).
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Processing Special Decision (Teaser Redirect)")
    print("="*80)

    # This is a mock example - in real usage, you'd have a database session
    # from services.decision_processor import DecisionProcessor
    # from config.decision_constants import DecisionID
    #
    # processor = DecisionProcessor(session)
    #
    # # User doesn't have item, but there's a teaser available
    # fragment = await processor.process_special_decision(
    #     user_id=12345,
    #     decision_id=DecisionID.DIARY_INTIMATE,
    #     has_required_item=False,
    #     teaser_fragment_key="diana_diary_tease"
    # )
    #
    # if fragment:
    #     print(f"✅ User redirected to teaser fragment: {fragment.key}")
    #     print(f"   Fragment text preview: {fragment.text[:100]}...")
    #     return {
    #         "success": True,
    #         "fragment": fragment,
    #         "action": "decision_success"
    #     }
    # else:
    #     print("❌ No special processing - continue with normal flow")

    print("""
Expected Flow for DIARY_INTIMATE without item:

1. Check item requirement → User missing "📓 Diario Íntimo"
2. Teaser key detected → "diana_diary_tease"
3. Process special decision:
   - Load teaser fragment from database
   - Update user state to teaser fragment
   - Increment fragments_visited counter
   - Process fragment rewards (besitos)
   - Commit transaction
4. Return teaser fragment to user

Result: User sees teaser content instead of being blocked
    """)


async def example_get_required_item_message():
    """
    Example: Generate user-friendly message for item requirement.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Generating Item Requirement Message")
    print("="*80)

    # This is a mock example - in real usage, you'd have a database session
    # from services.decision_processor import DecisionProcessor
    # from services.character_voice_service import CharacterVoiceService
    # from config.decision_constants import DecisionID
    #
    # processor = DecisionProcessor(session)
    # voice_service = CharacterVoiceService()
    #
    # message = await processor.get_required_item_message(
    #     decision_id=DecisionID.DIARY_INTIMATE,
    #     required_item_name="📓 Diario Íntimo",
    #     character_voice_service=voice_service
    # )
    #
    # print("Message to user:")
    # print(message)

    print("""
Expected Message:

💋 Diana susurra: 'Este camino requiere algo más íntimo...'

🔒 **Acceso Restringido**

Necesitas el 📓 Diario Íntimo para tomar esta decisión.

Visita la tienda para adquirirlo.

Note: If CharacterVoiceService is available, it uses authentic Diana voice.
Otherwise, falls back to default message.
    """)


async def example_integration_flow():
    """
    Example: Complete integration flow in CoordinadorCentral.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Complete Integration Flow")
    print("="*80)

    print("""
Complete flow in CoordinadorCentral._flujo_tomar_decision:

# Step 1: Check item requirement
has_item, required_item, teaser_key = await self.decision_processor.check_item_requirement(
    user_id, decision_id
)

# Step 2: Handle missing item
if not has_item and required_item:
    # Transition to shop state
    await self.narrative_state_machine.transition_to_shop(
        user_id, current_fragment_key, pending_decision_id=decision_id
    )

    # Step 3: Check for special decision (teaser redirect)
    special_fragment = await self.decision_processor.process_special_decision(
        user_id, decision_id, has_item, teaser_key
    )

    if special_fragment:
        # Return teaser fragment
        return {
            "success": True,
            "fragment": special_fragment,
            "action": "decision_success"
        }

    # Step 4: Generate item requirement message
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

# Step 5: Proceed with normal decision flow (user has item)
decision_result = await self.narrative_point.process_decision_with_points(
    user_id, decision_id, bot
)
# ... rest of normal flow ...

BENEFITS:
- Reduced from 206 lines to ~100 lines
- Complexity reduced from 15 to ~8
- Clear separation of concerns
- Easier to test and maintain
    """)


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("DecisionProcessor Service - Usage Examples")
    print("="*80)
    print("""
These examples demonstrate how to use the DecisionProcessor service
that was extracted from CoordinadorCentral.

Location: /home/azureuser/repos/bolt_ok/mybot/services/decision_processor.py

Note: These are code demonstrations. For actual usage, you need:
  1. A database session (AsyncSession)
  2. Configured services (ShopService, NarrativeService)
  3. Decision requirements JSON configured
    """)

    await example_check_item_requirement()
    await example_process_special_decision()
    await example_get_required_item_message()
    await example_integration_flow()

    print("\n" + "="*80)
    print("Examples Complete!")
    print("="*80)
    print("""
For integration instructions, see:
  /home/azureuser/repos/bolt_ok/mybot/services/DECISION_PROCESSOR_INTEGRATION.md

For full documentation, see docstrings in:
  /home/azureuser/repos/bolt_ok/mybot/services/decision_processor.py
    """)


if __name__ == "__main__":
    asyncio.run(main())
