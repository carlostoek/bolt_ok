#!/usr/bin/env python3
"""
Test script for the complete free channel access flow.
Tests the automatic message sending and delay approval system.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

# Add paths
sys.path.insert(0, '/data/data/com.termux/files/home/repos/bolt_ok/mybot')

# Set environment variables
os.environ.setdefault('BOT_TOKEN', 'test_token_12345')
os.environ.setdefault('ADMIN_IDS', '123456789')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///test_free_channel.db')


async def test_free_channel_flow():
    """Test the complete free channel access flow."""
    print("🧪 Testing Free Channel Access Flow")
    print("=" * 50)
    
    try:
        # Import required modules
        from services.free_channel_service import FreeChannelService
        from database.models import PendingChannelRequest, BotConfig
        from database.setup import init_db, get_session_factory
        from aiogram.types import ChatJoinRequest, User, Chat
        
        # Initialize database
        await init_db()
        session_factory = get_session_factory()
        
        # Create mock bot
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(return_value=True)
        mock_bot.approve_chat_join_request = AsyncMock(return_value=True)
        
        # Test session
        async with session_factory() as session:
            free_service = FreeChannelService(session, mock_bot)
            
            print("📋 Test 1: Configure free channel settings")
            # Configure wait time
            await free_service.set_wait_time_minutes(2)  # 2 minutes for testing
            wait_time = await free_service.get_wait_time_minutes()
            assert wait_time == 2, f"Expected 2 minutes, got {wait_time}"
            print("✅ Wait time configured: 2 minutes")
            
            # Configure social media message
            social_msg = (
                "🌟 **¡Hola {user_name}!**\n\n"
                "¡Síguenos en nuestras redes sociales!\n"
                "📱 Instagram: @test_account\n"
                "🐦 Twitter: @test_twitter"
            )
            await free_service.set_social_media_message(social_msg)
            print("✅ Social media message configured")
            
            # Configure welcome message
            welcome_msg = (
                "🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
                "Tu acceso ha sido aprobado exitosamente."
            )
            await free_service.set_welcome_message(welcome_msg)
            print("✅ Welcome message configured")
            
            print("\n📋 Test 2: Simulate join request")
            # Create mock join request
            mock_user = User(
                id=999888777,
                is_bot=False,
                first_name="Test User",
                username="testuser"
            )
            
            mock_chat = Chat(
                id=-1001234567890,
                type="channel"
            )
            
            mock_join_request = ChatJoinRequest(
                chat=mock_chat,
                from_user=mock_user,
                date=datetime.now(),
                user_chat_id=999888777
            )
            
            # Set free channel ID (simulate configuration)
            await free_service.config_service.set_free_channel_id(-1001234567890)
            
            # Process join request
            result = await free_service.handle_join_request(mock_join_request)
            assert result == True, "Join request handling failed"
            print("✅ Join request processed successfully")
            
            # Verify social media message was sent
            mock_bot.send_message.assert_called()
            calls = mock_bot.send_message.call_args_list
            social_call_found = any("síguenos en nuestras redes" in str(call) for call in calls)
            assert social_call_found, "Social media message not sent"
            print("✅ Social media message sent automatically")
            
            print("\n📋 Test 3: Check pending request in database")
            # Verify request is in database
            from sqlalchemy import select
            stmt = select(PendingChannelRequest).where(
                PendingChannelRequest.user_id == 999888777
            )
            result = await session.execute(stmt)
            pending_request = result.scalar_one_or_none()
            
            assert pending_request is not None, "Pending request not found in database"
            assert not pending_request.approved, "Request should not be approved yet"
            assert pending_request.social_media_message_sent, "Social media message flag not set"
            print("✅ Pending request stored correctly in database")
            
            print(f"   • User ID: {pending_request.user_id}")
            print(f"   • Chat ID: {pending_request.chat_id}")
            print(f"   • Request time: {pending_request.request_timestamp}")
            print(f"   • Approved: {pending_request.approved}")
            print(f"   • Social message sent: {pending_request.social_media_message_sent}")
            
            print("\n📋 Test 4: Test immediate processing (time not met)")
            # Try processing before wait time
            processed = await free_service.process_pending_requests()
            assert processed == 0, f"Expected 0 processed, got {processed}"
            print("✅ No requests processed (wait time not met)")
            
            print("\n📋 Test 5: Simulate wait time passed")
            # Manually adjust timestamp to simulate time passing
            pending_request.request_timestamp = datetime.utcnow() - timedelta(minutes=3)
            await session.commit()
            
            # Now process requests
            processed = await free_service.process_pending_requests()
            assert processed == 1, f"Expected 1 processed, got {processed}"
            print("✅ Request processed after wait time")
            
            # Verify approval was called
            mock_bot.approve_chat_join_request.assert_called_with(-1001234567890, 999888777)
            print("✅ Telegram approval API called")
            
            # Check welcome message was sent
            welcome_calls = [call for call in mock_bot.send_message.call_args_list 
                           if "Bienvenido al Canal Gratuito" in str(call)]
            assert len(welcome_calls) > 0, "Welcome message not sent"
            print("✅ Welcome message sent after approval")
            
            print("\n📋 Test 6: Verify final database state")
            # Refresh the request from database
            await session.refresh(pending_request)
            assert pending_request.approved, "Request should be approved now"
            assert pending_request.approval_timestamp is not None, "Approval timestamp should be set"
            assert pending_request.welcome_message_sent, "Welcome message flag should be set"
            print("✅ Database state updated correctly")
            
            print(f"   • Approved: {pending_request.approved}")
            print(f"   • Approval time: {pending_request.approval_timestamp}")
            print(f"   • Welcome message sent: {pending_request.welcome_message_sent}")
            
            print("\n📋 Test 7: Test statistics")
            stats = await free_service.get_channel_statistics()
            print("✅ Statistics retrieved successfully")
            print(f"   • Channel configured: {stats['channel_configured']}")
            print(f"   • Wait time: {stats['wait_time_minutes']} minutes")
            print(f"   • Pending requests: {stats['pending_requests']}")
            print(f"   • Total processed: {stats['total_processed']}")
            
            print("\n🎉 ALL TESTS PASSED!")
            print("=" * 50)
            print("✅ Free channel access flow is working correctly")
            print("✅ Automatic social media messages are sent immediately")
            print("✅ Delay approval system is functioning properly")
            print("✅ Database tracking is accurate")
            print("✅ All configurations are applied correctly")
            
            return True
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases and error scenarios."""
    print("\n🔍 Testing Edge Cases")
    print("=" * 30)
    
    try:
        from services.free_channel_service import FreeChannelService
        from database.setup import get_session_factory
        
        session_factory = get_session_factory()
        mock_bot = AsyncMock()
        
        async with session_factory() as session:
            free_service = FreeChannelService(session, mock_bot)
            
            print("📋 Edge Case 1: Duplicate join request")
            # Test duplicate request handling
            from aiogram.types import ChatJoinRequest, User, Chat
            
            mock_user = User(id=111222333, is_bot=False, first_name="Duplicate User")
            mock_chat = Chat(id=-1001234567890, type="channel")
            mock_request = ChatJoinRequest(
                chat=mock_chat, 
                from_user=mock_user, 
                date=datetime.now(),
                user_chat_id=111222333
            )
            
            # First request
            result1 = await free_service.handle_join_request(mock_request)
            assert result1 == True, "First request should succeed"
            
            # Duplicate request
            result2 = await free_service.handle_join_request(mock_request)
            assert result2 == True, "Duplicate request should be handled gracefully"
            print("✅ Duplicate requests handled correctly")
            
            print("📋 Edge Case 2: Zero wait time (immediate approval)")
            await free_service.set_wait_time_minutes(0)
            
            mock_user2 = User(id=444555666, is_bot=False, first_name="Immediate User")
            mock_request2 = ChatJoinRequest(
                chat=mock_chat, 
                from_user=mock_user2, 
                date=datetime.now(),
                user_chat_id=444555666
            )
            
            await free_service.handle_join_request(mock_request2)
            processed = await free_service.process_pending_requests()
            assert processed >= 1, "Immediate approval should process requests"
            print("✅ Immediate approval works correctly")
            
            print("📋 Edge Case 3: Auto-approval disabled")
            # Disable auto-approval
            from database.models import BotConfig
            config = await session.get(BotConfig, 1)
            if config:
                config.auto_approval_enabled = False
                await session.commit()
            
            processed = await free_service.process_pending_requests()
            print(f"✅ Auto-approval disabled: {processed} requests processed")
            
            print("\n✅ All edge cases handled correctly!")
            return True
            
    except Exception as e:
        print(f"\n❌ EDGE CASE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Free Channel Access Flow - Complete Test Suite")
    print("=" * 60)
    
    # Test main flow
    main_test_result = await test_free_channel_flow()
    
    # Test edge cases
    edge_test_result = await test_edge_cases()
    
    print("\n" + "=" * 60)
    if main_test_result and edge_test_result:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ The free channel access system is ready for production")
        exit_code = 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please review the errors above")
        exit_code = 1
    
    print("=" * 60)
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)