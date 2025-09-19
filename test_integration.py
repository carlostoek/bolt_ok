#!/usr/bin/env python3
"""
Test script to verify enhanced admin menu integration.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test 1: Check if enhanced handlers are registered
    from mybot.handlers.admin.admin_menu import router
    
    # Check if the enhanced handlers are in the router
    enhanced_vip_exists = any(hasattr(handler.callback, '__name__') and 'admin_vip_enhanced' in str(handler.callback.__name__) 
                            for handler in router.handlers)
    enhanced_analytics_exists = any(hasattr(handler.callback, '__name__') and 'admin_analytics_enhanced' in str(handler.callback.__name__) 
                                  for handler in router.handlers)
    enhanced_channel_exists = any(hasattr(handler.callback, '__name__') and 'admin_channel_enhanced' in str(handler.callback.__name__) 
                                for handler in router.handlers)
    
    print("✅ Enhanced VIP handler registered:", enhanced_vip_exists)
    print("✅ Enhanced analytics handler registered:", enhanced_analytics_exists)
    print("✅ Enhanced channel handler registered:", enhanced_channel_exists)
    
    # Test 2: Check availability flags
    try:
        from mybot.handlers.admin.admin_menu import ENHANCED_VIP_AVAILABLE, ENHANCED_ANALYTICS_AVAILABLE, ENHANCED_CHANNEL_AVAILABLE
        print("\n📊 Availability Flags:")
        print("ENHANCED_VIP_AVAILABLE:", ENHANCED_VIP_AVAILABLE)
        print("ENHANCED_ANALYTICS_AVAILABLE:", ENHANCED_ANALYTICS_AVAILABLE)
        print("ENHANCED_CHANNEL_AVAILABLE:", ENHANCED_CHANNEL_AVAILABLE)
    except ImportError:
        print("\n📊 Availability Flags: Not available (ImportError)")
    
    # Test 3: Test keyboard generation
    try:
        from mybot.keyboards.admin_main_kb import get_enhanced_admin_main_kb
        kb = get_enhanced_admin_main_kb()
        print("\n✅ Keyboard generated successfully")
    except ImportError as e:
        print(f"\n❌ Keyboard import error: {e}")
    except Exception as e:
        print(f"\n❌ Keyboard generation error: {e}")
    
except ImportError as e:
    print(f"❌ Main import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
