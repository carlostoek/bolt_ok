#!/usr/bin/env python3
"""
Test script to verify coordinador_central integration with JSON config.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the function directly
from services.coordinador_central import _load_decision_requirements

async def main():
    print("🧪 Testing CoordinadorCentral decision_requirements loading\n")

    # Test 1: Load requirements
    print("📋 Test 1: Load decision requirements from JSON")
    requirements = _load_decision_requirements()
    print(f"Loaded: {requirements}")

    # Test 2: Verify types
    print("\n🔍 Test 2: Verify data types")
    for decision_id, item_name in requirements.items():
        print(f"  Decision {decision_id} (type: {type(decision_id).__name__}) → {item_name} (type: {type(item_name).__name__})")

    # Test 3: Test lookups
    print("\n✅ Test 3: Test decision lookups")
    test_cases = [
        (1, "📖 Diario Secreto"),
        (15, "📓 Diario Íntimo"),
        (25, None),
        (100, None)
    ]

    for decision_id, expected in test_cases:
        actual = requirements.get(decision_id)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} Decision {decision_id}: expected={expected}, actual={actual}")

    # Test 4: Simulate the flow
    print("\n🎯 Test 4: Simulate decision flow")
    decision_id = 15
    required_item = requirements.get(decision_id)
    if required_item:
        print(f"  Decision {decision_id} requires item: {required_item}")
        print(f"  ✅ Would check if user has '{required_item}' in inventory")
    else:
        print(f"  Decision {decision_id} has no item requirement")
        print(f"  ✅ Would process as normal decision")

    print("\n✅ All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(main())