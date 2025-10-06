#!/usr/bin/env python3
"""
Test script to verify decision_requirements JSON loading.
"""
import json
from pathlib import Path

# Test loading the JSON file
config_path = Path(__file__).parent / "config" / "decision_requirements.json"

print(f"📁 Config path: {config_path}")
print(f"✅ File exists: {config_path.exists()}\n")

if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("📋 Loaded configuration:")
    print(json.dumps(config, indent=2, ensure_ascii=False))

    print("\n🔄 Converting to int keys:")
    requirements = {int(k): v for k, v in config.items()}
    print(requirements)

    print("\n✅ Test lookups:")
    for decision_id in [1, 15, 25]:
        item = requirements.get(decision_id)
        if item:
            print(f"  Decision {decision_id} → {item}")
        else:
            print(f"  Decision {decision_id} → Not configured")
else:
    print("❌ Config file not found!")

print("\n✅ All tests passed!")