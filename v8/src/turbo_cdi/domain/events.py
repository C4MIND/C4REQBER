"""
Domain events and event handling for TURBO-CDI v8.4
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable, List, Any
from turbo_cdi.domain.entities.advanced import DomainEvent


@runtime_checkable
class EventHandler(Protocol):
    """Protocol for event handlers"""

    async def handle(self, event: DomainEvent) -> None: ...


class EventBus:
    """
    In-memory event bus for domain events.

    Handles publishing events to registered handlers.
    """

    def __init__(self):
        self._handlers: dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe handler to event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe handler from event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all registered handlers"""
        event_type = event.event_type
        if event_type in self._handlers:
            # Publish to all handlers for this event type
            tasks = []
            for handler in self._handlers[event_type]:
                tasks.append(handler.handle(event))

            # Wait for all handlers to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events"""
        for event in events:
            await self.publish(event)


# Global event bus instance
event_bus = EventBus()


class DomainEventPublisher:
    """
    Utility class for publishing domain events.

    Can be injected into domain services to enable event publishing.
    """

    def __init__(self, event_bus: EventBus = event_bus):
        self.event_bus = event_bus

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event"""
        await self.event_bus.publish(event)

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events"""
        await self.event_bus.publish_batch(events)
