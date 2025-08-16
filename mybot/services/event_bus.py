"""
EventBus system for inter-module communication within the Bolt OK Telegram bot.
Implements Observer pattern for asynchronous event propagation between modules.
"""
import logging
import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Enumeration of system events that can be published and subscribed to."""
    # User engagement events
    USER_REACTION = "user_reaction"
    USER_PARTICIPATION = "user_participation"
    USER_DAILY_CHECKIN = "user_daily_checkin"
    
    # Narrative events
    NARRATIVE_DECISION = "narrative_decision"
    NARRATIVE_PROGRESS = "narrative_progress"
    NARRATIVE_ACCESS_DENIED = "narrative_access_denied"
    
    # Gamification events
    POINTS_AWARDED = "points_awarded"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    LEVEL_UP = "level_up"
    
    # Channel events
    CHANNEL_ENGAGEMENT = "channel_engagement"
    VIP_ACCESS_REQUIRED = "vip_access_required"
    
    # System events
    WORKFLOW_COMPLETED = "workflow_completed"
    ERROR_OCCURRED = "error_occurred"
    CONSISTENCY_CHECK = "consistency_check"

@dataclass
class Event:
    """
    Event data structure containing all information about a system event.
    """
    event_type: EventType
    user_id: int
    data: Dict[str, Any]
    timestamp: datetime
    event_id: Optional[str] = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None

class EventBus:
    """
    Central event bus for asynchronous inter-module communication.
    Implements the Observer pattern for loose coupling between system modules.
    
    This service maintains architectural coherence by:
    - Following the same async/await patterns as existing services
    - Using dependency injection compatible with current service structure
    - Providing non-intrusive event capabilities that don't break existing flows
    """
    
    def __init__(self):
        """Initialize the event bus with empty subscriber registry."""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000  # Keep last 1000 events for debugging
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        """
        Subscribe a handler function to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Async function that will be called when event is published
                    Should accept Event parameter and return None
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> bool:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            handler: The handler function to remove
            
        Returns:
            bool: True if handler was found and removed, False otherwise
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from {event_type.value}")
                return True
            except ValueError:
                pass
        return False
    
    async def publish(self, event_type: EventType, user_id: int, data: Dict[str, Any], 
                     source: Optional[str] = None, correlation_id: Optional[str] = None) -> Event:
        """
        Publish an event to all subscribers asynchronously.
        
        Args:
            event_type: Type of event being published
            user_id: Telegram user ID associated with this event
            data: Event-specific data dictionary
            source: Optional source identifier (service name, etc.)
            correlation_id: Optional correlation ID for tracking related events
            
        Returns:
            Event: The published event object
        """
        # Create event object
        event = Event(
            event_type=event_type,
            user_id=user_id,
            data=data,
            timestamp=datetime.utcnow(),
            source=source,
            correlation_id=correlation_id
        )
        
        # Add to history (thread-safe)
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event_type, [])
        
        if subscribers:
            logger.debug(f"Publishing {event_type.value} to {len(subscribers)} subscribers")
            
            # Call all subscribers asynchronously, but don't wait for them
            # This prevents event handling from blocking the main workflow
            for handler in subscribers:
                asyncio.create_task(self._safe_call_handler(handler, event))
        else:
            logger.debug(f"No subscribers for event {event_type.value}")
        
        return event
    
    async def _safe_call_handler(self, handler: Callable[[Event], Any], event: Event) -> None:
        """
        Safely call an event handler, catching and logging any exceptions.
        
        Args:
            handler: The handler function to call
            event: The event to pass to the handler
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.exception(f"Error in event handler for {event.event_type.value}: {e}")
            
            # Publish error event for system monitoring
            if event.event_type != EventType.ERROR_OCCURRED:  # Prevent infinite loops
                await self.publish(
                    EventType.ERROR_OCCURRED,
                    event.user_id,
                    {
                        "error": str(e),
                        "original_event": event.event_type.value,
                        "handler": str(handler),
                        "source": "event_bus"
                    },
                    source="event_bus",
                    correlation_id=event.correlation_id
                )
    
    def get_subscribers_count(self, event_type: EventType) -> int:
        """
        Get the number of subscribers for a specific event type.
        
        Args:
            event_type: The event type to check
            
        Returns:
            int: Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_event_history(self, limit: int = 100) -> List[Event]:
        """
        Get recent event history for debugging purposes.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: Recent events, most recent first
        """
        return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear the event history. Useful for testing."""
        self._event_history.clear()

# Global event bus instance for use across the application
# This follows the same singleton pattern used by other global services
_event_bus_instance = None

def get_event_bus() -> EventBus:
    """
    Get the global EventBus instance.
    Creates a new instance if one doesn't exist.
    
    Returns:
        EventBus: The global event bus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

def reset_event_bus() -> None:
    """
    Reset the global EventBus instance.
    Primarily used for testing purposes.
    """
    global _event_bus_instance
    _event_bus_instance = None