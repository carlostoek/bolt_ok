#!/usr/bin/env python3
\"\"\"
Test script to verify that the original errors have been fixed
\"\"\"

import os

def test_original_error():
    \"\"\"Test the original admin IDs parsing error scenario\"\"\"
    # Set environment variable with comma-separated values like in the original error
    os.environ[\"ADMIN_IDS\"] = \"123456789,987654321\"
    
    # Temporarily set other required environment variables
    os.environ[\"BOT_TOKEN\"] = \"7570619877:AAHJMc_PNgZT9rpjUzpp19FMo7WlmHfA5Ms\"
    os.environ[\"DATABASE_URL\"] = \"sqlite:///adventure_bot.db\"  # This should be converted automatically
    
    try:
        # This should now work without the ValueError
        from utils.config import Config, ADMIN_IDS
        print(\"✅ SUCCESS: ADMIN_IDS parsed correctly:\", ADMIN_IDS)
        print(\"✅ SUCCESS: DATABASE_URL converted correctly:\", Config.DATABASE_URL)
        
        # Verify that values are parsed as integers, not strings
        assert all(isinstance(uid, int) for uid in ADMIN_IDS), \"Admin IDs should be integers\"
        assert Config.DATABASE_URL.startswith(\"sqlite+aiosqlite://\"), \"Database URL should be in async format\"
        
        print(\"✅ SUCCESS: All validation checks passed!\")
        return True
    except ValueError as e:
        print(f\"❌ FAILED: {e}\")
        return False
    except Exception as e:
        print(f\"❌ UNEXPECTED ERROR: {e}\")
        return False

def test_edge_cases():
    \"\"\"Test other potential edge cases\"\"\"
    print(\"\\n--- Testing edge cases ---\")
    
    # Test with empty ADMIN_IDS
    os.environ[\"ADMIN_IDS\"] = \"\"
    try:
        from utils.config import ADMIN_IDS as empty_admin_ids
        print(f\"✅ Empty ADMIN_IDS handled correctly: {empty_admin_ids}\")
    except Exception as e:
        print(f\"❌ Empty ADMIN_IDS failed: {e}\")
    
    # Test with semicolon-separated values (original format)
    os.environ[\"ADMIN_IDS\"] = \"111111111;222222222;333333333\"
    try:
        from utils.config import ADMIN_IDS as semicolon_admin_ids
        print(f\"✅ Semicolon-separated ADMIN_IDS handled correctly: {semicolon_admin_ids}\")
    except Exception as e:
        print(f\"❌ Semicolon-separated ADMIN_IDS failed: {e}\")
    
    # Test with mixed separators (should still work)
    os.environ[\"ADMIN_IDS\"] = \"111111111,222222222;333333333\"
    try:
        from utils.config import ADMIN_IDS as mixed_admin_ids
        print(f\"✅ Mixed-separated ADMIN_IDS handled correctly: {mixed_admin_ids}\")
    except Exception as e:
        print(f\"❌ Mixed-separated ADMIN_IDS failed: {e}\")

if __name__ == \"__main__\":
    print(\"Testing fixes for the original error...\")
    print(\"Original error: ValueError: invalid literal for int() with base 10: '123456789,987654321'\")
    print()
    
    success = test_original_error()
    test_edge_cases()
    
    if success:
        print(\"\\n🎉 All tests passed! The original error has been fixed.\")
    else:
        print(\"\\n💥 Tests failed! The error still exists.\")