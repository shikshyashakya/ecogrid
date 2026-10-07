"""A tiny in-memory event bus. It stands in for Kafka in the prototype:
services publish events and subscribe to event types, never calling each other directly."""
from collections import defaultdict
from typing import Callable


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = defaultdict(list)
        self.published: list[object] = []

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        self.published.append(event)
        for handler in self._handlers[type(event)]:
            handler(event)
