#!/usr/bin/env python3
"""
Test script to verify enhanced admin menu integration.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mybot.handlers.admin.admin_menu import router
    print("✅ Enhanced VIP available:", hasattr(router, 'admin_vip_enhanced'))
    print("✅ Enhanced analytics available:", hasattr(router, 'admin_analytics_enhanced'))
    print("✅ Enhanced channel available:", hasattr(router, 'admin_channel_enhanced'))
    
    from mybot.keyboards.admin_main_kb import get_enhanced_admin_main_kb
    from mybot.handlers.admin.admin_menu import ENHANCED_VIP_AVAILABLE, ENHANCED_ANALYTICS_AVAILABLE, ENHANCED_CHANNEL_AVAILABLE
    
    print("\n📊 Availability Flags:")
    print("ENHANCED_VIP_AVAILABLE:", ENHANCED_VIP_AVAILABLE)
    print("ENHANCED_ANALYTICS_AVAILABLE:", ENHANCED_ANALYTICS_AVAILABLE)
    print("ENHANCED_CHANNEL_AVAILABLE:", ENHANCED_CHANNEL_AVAILABLE)
    
    # Test keyboard generation
    kb = get_enhanced_admin_main_kb()
    print("\n✅ Keyboard generated successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
