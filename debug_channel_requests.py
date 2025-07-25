#!/usr/bin/env python3
"""
Debug script to check the free channel request system configuration and logs.
"""
import sys
import os
from datetime import datetime

# Set environment variables
os.environ.setdefault('BOT_TOKEN', 'debug_token')
os.environ.setdefault('ADMIN_IDS', '123456789')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///debug.db')

# Add paths
sys.path.insert(0, '/data/data/com.termux/files/home/repos/bolt_ok/mybot')


def check_handler_registration():
    """Check that the channel access handler is properly configured."""
    print("🔍 Checking Handler Registration")
    print("=" * 35)
    
    try:
        # Check that the handler file exists and is importable
        from handlers.channel_access import router, handle_join_request
        print("✅ channel_access handler imported successfully")
        
        # Check router configuration
        if hasattr(router, 'observers'):
            print("✅ Router has observers configured")
            
            # Check for chat_join_request handlers
            join_handlers = 0
            for observer in router.observers.values():
                for handler in observer.handlers:
                    if 'chat_join_request' in str(handler):
                        join_handlers += 1
            
            print(f"✅ Found {join_handlers} chat_join_request handlers")
        else:
            print("❌ Router observers not accessible")
        
        # Check that the function signature is correct
        import inspect
        sig = inspect.signature(handle_join_request)
        params = list(sig.parameters.keys())
        expected_params = ['event', 'bot', 'session']
        
        if all(param in params for param in expected_params):
            print("✅ Handler function signature is correct")
        else:
            print(f"❌ Handler signature issue. Expected {expected_params}, got {params}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Handler check failed: {e}")
        return False


def check_service_configuration():
    """Check FreeChannelService configuration."""
    print("\n🔧 Checking Service Configuration")
    print("=" * 35)
    
    try:
        from services.free_channel_service import FreeChannelService
        print("✅ FreeChannelService imported successfully")
        
        # Check method existence
        required_methods = [
            'handle_join_request',
            '_send_social_media_message',
            'get_free_channel_id',
            'set_wait_time_minutes'
        ]
        
        for method in required_methods:
            if hasattr(FreeChannelService, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        # Check that the service can be instantiated (with mocks)
        from unittest.mock import AsyncMock
        mock_session = AsyncMock()
        mock_bot = AsyncMock()
        
        service = FreeChannelService(mock_session, mock_bot)
        print("✅ Service can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"❌ Service configuration check failed: {e}")
        return False


def check_database_models():
    """Check that database models are properly defined."""
    print("\n🗄️ Checking Database Models")
    print("=" * 30)
    
    try:
        from database.models import PendingChannelRequest, BotConfig, User
        print("✅ Required models imported successfully")
        
        # Check PendingChannelRequest fields
        pcr_fields = ['user_id', 'chat_id', 'request_timestamp', 'approved', 
                     'social_media_message_sent', 'welcome_message_sent']
        
        for field in pcr_fields:
            if hasattr(PendingChannelRequest, field):
                print(f"✅ PendingChannelRequest.{field} exists")
            else:
                print(f"❌ PendingChannelRequest.{field} missing")
                return False
        
        # Check BotConfig fields
        bc_fields = ['free_channel_wait_time_minutes', 'social_media_message', 
                    'welcome_message_template', 'auto_approval_enabled']
        
        for field in bc_fields:
            if hasattr(BotConfig, field):
                print(f"✅ BotConfig.{field} exists")
            else:
                print(f"❌ BotConfig.{field} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database models check failed: {e}")
        return False


def check_bot_registration():
    """Check that the router is registered in the main bot."""
    print("\n🤖 Checking Bot Registration")
    print("=" * 30)
    
    try:
        # Read the bot.py file to check if channel_access router is registered
        with open('/data/data/com.termux/files/home/repos/bolt_ok/mybot/bot.py', 'r') as f:
            bot_content = f.read()
        
        if 'channel_access_router' in bot_content:
            print("✅ channel_access_router imported in bot.py")
        else:
            print("❌ channel_access_router not imported in bot.py")
            return False
        
        if 'channel_access' in bot_content and 'router' in bot_content:
            print("✅ channel_access router appears to be registered")
        else:
            print("❌ channel_access router not registered")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bot registration check failed: {e}")
        return False


def diagnose_issue():
    """Provide diagnostic information about why join requests might not work."""
    print("\n🩺 Issue Diagnosis")
    print("=" * 20)
    
    print("📋 Common causes for join request not working:")
    print("  1. 🔧 Free channel ID not configured")
    print("  2. 🚫 Bot not admin in the channel")
    print("  3. 📱 Bot can't send private messages to users")
    print("  4. ⚙️ Wrong channel settings (join requests disabled)")
    print("  5. 🗄️ Database connection issues")
    print("  6. 📝 Handler not receiving events")
    
    print("\n🔍 Debug steps to try:")
    print("  1. Check bot logs for 'handle_join_request' calls")
    print("  2. Verify free channel ID in admin panel")
    print("  3. Test with /start to ensure bot responds to user")
    print("  4. Check channel settings allow join requests")
    print("  5. Verify bot has admin rights in channel")
    
    print("\n💡 Expected flow:")
    print("  1. User clicks join link → Chat join request created")
    print("  2. Bot receives ChatJoinRequest event")
    print("  3. handle_join_request called")
    print("  4. FreeChannelService.handle_join_request called")
    print("  5. Social media message sent immediately")
    print("  6. Request stored in database")
    print("  7. Scheduler processes request after delay")


def main():
    """Run all diagnostic checks."""
    print("🚀 Free Channel Request System - Diagnostic Tool")
    print("=" * 55)
    
    checks = [
        ("Handler Registration", check_handler_registration),
        ("Service Configuration", check_service_configuration),
        ("Database Models", check_database_models),
        ("Bot Registration", check_bot_registration)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n🧪 Running {check_name} Check...")
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 55)
    print("📊 DIAGNOSTIC RESULTS:")
    print("=" * 55)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(checks)} checks passed ({passed/len(checks)*100:.1f}%)")
    
    # Always show diagnosis
    diagnose_issue()
    
    if passed == len(checks):
        print("\n🎉 ALL CHECKS PASSED!")
        print("✅ The system appears to be configured correctly")
        print("📝 If join requests still don't work, check:")
        print("   • Bot admin rights in channel")
        print("   • Channel join request settings")
        print("   • User privacy settings for receiving messages")
        return 0
    else:
        print("\n⚠️ SOME CHECKS FAILED!")
        print("🔧 Fix the failed checks above to resolve the issue")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Diagnostic interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Diagnostic error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)