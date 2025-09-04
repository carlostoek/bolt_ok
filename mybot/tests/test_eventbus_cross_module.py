"""
EventBus Cross-Module Integration Tests
Tests the reliability of the EventBus system for cross-module communication.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import List

from services.event_bus import EventBus, EventType, Event
from datetime import datetime


@pytest.mark.asyncio
class TestEventBusCrossModuleReliability:
    """Tests for EventBus reliability in cross-module scenarios."""
    
    async def test_eventbus_basic_publish_subscribe(self):
        """Test basic publish/subscribe functionality."""
        event_bus = EventBus()
        received_events = []
        
        # Create event handler
        async def test_handler(event: Event):
            received_events.append(event)
        
        # Subscribe to event
        event_bus.subscribe(EventType.USER_REACTION, test_handler)
        
        # Publish event
        published_event = await event_bus.publish(
            EventType.USER_REACTION,
            123456789,
            {"reaction_type": "like", "points": 10}
        )
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # Validate event was received
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.USER_REACTION
        assert received_events[0].user_id == 123456789
        assert received_events[0].data["reaction_type"] == "like"

    async def test_eventbus_multiple_subscribers(self):
        """Test EventBus handles multiple subscribers correctly."""
        event_bus = EventBus()
        handler1_events = []
        handler2_events = []
        
        async def handler1(event: Event):
            handler1_events.append(event)
            
        async def handler2(event: Event):
            handler2_events.append(event)
        
        # Subscribe both handlers
        event_bus.subscribe(EventType.POINTS_AWARDED, handler1)
        event_bus.subscribe(EventType.POINTS_AWARDED, handler2)
        
        # Publish event
        await event_bus.publish(
            EventType.POINTS_AWARDED,
            123,
            {"points": 15}
        )
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # Both handlers should receive the event
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
        assert handler1_events[0].data["points"] == 15
        assert handler2_events[0].data["points"] == 15

    async def test_eventbus_error_handling_subscriber_failure(self):
        """Test EventBus handles subscriber failures gracefully."""
        event_bus = EventBus()
        successful_events = []
        
        async def failing_handler(event: Event):
            raise Exception("Handler failed")
            
        async def successful_handler(event: Event):
            successful_events.append(event)
        
        # Subscribe both handlers
        event_bus.subscribe(EventType.ACHIEVEMENT_UNLOCKED, failing_handler)
        event_bus.subscribe(EventType.ACHIEVEMENT_UNLOCKED, successful_handler)
        
        # Should not raise exception, successful handler should still work
        await event_bus.publish(
            EventType.ACHIEVEMENT_UNLOCKED,
            123,
            {"achievement": "first_reaction"}
        )
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # Successful handler should have received event
        assert len(successful_events) == 1
        assert successful_events[0].data["achievement"] == "first_reaction"

    async def test_eventbus_concurrent_publishing(self):
        """Test EventBus handles concurrent event publishing."""
        event_bus = EventBus()
        received_events = []
        
        async def collector_handler(event: Event):
            received_events.append(event.data["sequence"])
        
        event_bus.subscribe(EventType.WORKFLOW_COMPLETED, collector_handler)
        
        # Publish all events concurrently
        publish_tasks = [
            event_bus.publish(EventType.WORKFLOW_COMPLETED, i, {"sequence": i})
            for i in range(10)
        ]
        await asyncio.gather(*publish_tasks)
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # All events should be received
        assert len(received_events) == 10
        assert set(received_events) == set(range(10))

    async def test_eventbus_performance_under_load(self):
        """Test EventBus performance doesn't become bottleneck."""
        event_bus = EventBus()
        processed_count = 0
        
        async def counting_handler(event: Event):
            nonlocal processed_count
            processed_count += 1
        
        event_bus.subscribe(EventType.USER_PARTICIPATION, counting_handler)
        
        # Measure publishing performance
        start_time = asyncio.get_event_loop().time()
        
        # Publish 100 events
        for i in range(100):
            await event_bus.publish(
                EventType.USER_PARTICIPATION,
                i,
                {"action": "post"}
            )
        
        end_time = asyncio.get_event_loop().time()
        duration_ms = (end_time - start_time) * 1000
        
        # Wait for all async event handlers to complete
        await asyncio.sleep(0.1)
        
        # Performance validation
        assert duration_ms < 1000, f"100 events took {duration_ms:.2f}ms, too slow"
        assert processed_count == 100, "All events must be processed"

    async def test_eventbus_event_ordering(self):
        """Test EventBus maintains event ordering."""
        event_bus = EventBus()
        event_sequence = []
        
        async def sequence_handler(event: Event):
            event_sequence.append(event.data["order"])
        
        event_bus.subscribe(EventType.NARRATIVE_PROGRESS, sequence_handler)
        
        # Publish events in order
        for i in range(5):
            await event_bus.publish(
                EventType.NARRATIVE_PROGRESS,
                123,
                {"order": i}
            )
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # Events should be processed in order
        assert event_sequence == [0, 1, 2, 3, 4]

    async def test_eventbus_unsubscribe_functionality(self):
        """Test EventBus unsubscribe works correctly."""
        event_bus = EventBus()
        handler_called = False
        
        async def test_handler(event: Event):
            nonlocal handler_called
            handler_called = True
        
        # Subscribe then unsubscribe
        event_bus.subscribe(EventType.LEVEL_UP, test_handler)
        success = event_bus.unsubscribe(EventType.LEVEL_UP, test_handler)
        
        assert success is True, "Unsubscribe should return True for existing handler"
        
        # Publish event after unsubscribing
        await event_bus.publish(EventType.LEVEL_UP, 123, {})
        
        # Wait for async event handling
        await asyncio.sleep(0.01)
        
        # Handler should not have been called
        assert handler_called is False, "Unsubscribed handler should not be called"

    async def test_eventbus_cross_module_communication_simulation(self):
        """Simulate cross-module communication through EventBus."""
        event_bus = EventBus()
        
        # Simulate different modules
        narrative_events = []
        gamification_events = []
        notification_events = []
        
        async def narrative_handler(event: Event):
            narrative_events.append(event)
            # Simulate narrative module publishing back
            await event_bus.publish(
                EventType.NARRATIVE_PROGRESS,
                event.user_id,
                {"fragment_unlocked": True}
            )
        
        async def gamification_handler(event: Event):
            gamification_events.append(event)
        
        async def notification_handler(event: Event):
            notification_events.append(event)
        
        # Set up cross-module subscriptions
        event_bus.subscribe(EventType.USER_REACTION, narrative_handler)
        event_bus.subscribe(EventType.NARRATIVE_PROGRESS, gamification_handler)
        event_bus.subscribe(EventType.POINTS_AWARDED, notification_handler)
        
        # Trigger initial event
        await event_bus.publish(
            EventType.USER_REACTION,
            123,
            {"reaction": "like"}
        )
        
        # Wait for async event propagation
        await asyncio.sleep(0.02)
        
        # Validate cross-module communication
        assert len(narrative_events) == 1, "Narrative module should receive user reaction"
        assert len(gamification_events) == 1, "Gamification should receive narrative progress"
        assert narrative_events[0].event_type == EventType.USER_REACTION
        assert gamification_events[0].event_type == EventType.NARRATIVE_PROGRESS
        assert gamification_events[0].data["fragment_unlocked"] is True