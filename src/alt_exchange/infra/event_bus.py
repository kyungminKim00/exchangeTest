from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, List, Protocol, TypeVar

Event = TypeVar("Event")


class Subscriber(Protocol[Event]):
    def __call__(self, event: Event) -> None:
        ...


class InMemoryEventBus:
    """Publish/subscribe bus for deterministic tests."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[type, List[Subscriber]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Subscriber) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in list(self._subscribers[type(event)]):
            handler(event)
