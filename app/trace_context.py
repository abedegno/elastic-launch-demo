"""Thread-safe shared context store for log-trace correlation.

The trace generator writes (trace_id, span_id) per service after each trace batch.
Service log emitters read the latest context to correlate their logs with active traces.
Always returns the most recent trace context — no TTL expiry.

A parallel per-channel map captures the most recent *error* trace for each
(channel_id, service_name) pair, so fault logs can prefer a real error trace.id
over the generic last-seen-per-service one.
"""

from __future__ import annotations

import threading


class TraceContextStore:
    """Maps service_name -> (trace_id, span_id) plus a per-channel error-trace map."""

    def __init__(self):
        self._store: dict[str, tuple[str, str]] = {}
        self._channel_store: dict[tuple[int, str], tuple[str, str]] = {}
        self._lock = threading.Lock()

    def set(self, service_name: str, trace_id: str, span_id: str) -> None:
        with self._lock:
            self._store[service_name] = (trace_id, span_id)

    def get(self, service_name: str) -> tuple[str | None, str | None]:
        with self._lock:
            entry = self._store.get(service_name)
            if entry is None:
                return None, None
            return entry

    def set_for_channel(
        self, channel_id: int, service_name: str, trace_id: str, span_id: str
    ) -> None:
        """Record the most recent error trace for a (channel, service) pair."""
        with self._lock:
            self._channel_store[(channel_id, service_name)] = (trace_id, span_id)

    def get_for_channel(
        self, channel_id: int, service_name: str
    ) -> tuple[str | None, str | None]:
        with self._lock:
            entry = self._channel_store.get((channel_id, service_name))
            if entry is None:
                return None, None
            return entry


# Module-level singleton — imported by trace_generator and base_service
_trace_context_store = TraceContextStore()
