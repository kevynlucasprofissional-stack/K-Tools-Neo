from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional

from .models import SystemEvent


class SystemEventStream:
    """Thread-safe in-memory publish-subscribe stream for system runtime events."""

    def __init__(self, max_history: int = 500) -> None:
        self._lock = threading.RLock()
        self._listeners: List[Callable[[SystemEvent], None]] = []
        self._history: List[SystemEvent] = []
        self._max_history = max_history

    def subscribe(self, listener: Callable[[SystemEvent], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def publish(self, event: SystemEvent) -> SystemEvent:
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            listeners_copy = list(self._listeners)

        for listener in listeners_copy:
            try:
                listener(event)
            except Exception:
                pass
        return event

    def emit(self, event_type: str, message: str, payload: Optional[Dict[str, Any]] = None) -> SystemEvent:
        event = SystemEvent(event_type=event_type, message=message, payload=payload or {})
        return self.publish(event)

    def get_history(self, limit: int = 100) -> List[SystemEvent]:
        with self._lock:
            return list(self._history[-limit:])

    def drain(self) -> List[SystemEvent]:
        with self._lock:
            events = list(self._history)
            self._history.clear()
            return events

    def clear(self) -> None:
        with self._lock:
            self._history.clear()


_GLOBAL_STREAM: Optional[SystemEventStream] = None
_GLOBAL_STREAM_LOCK = threading.Lock()


def get_system_event_stream() -> SystemEventStream:
    global _GLOBAL_STREAM
    with _GLOBAL_STREAM_LOCK:
        if _GLOBAL_STREAM is None:
            _GLOBAL_STREAM = SystemEventStream()
        return _GLOBAL_STREAM
