"""Subscriber DB service — AWS eu-central-1a. PostgreSQL database for 45M subscriber records."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SubscriberDbService(BaseService):
    SERVICE_NAME = "subscriber-db"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._query_count = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_query()
        self._emit_pool_metrics()

        if time.time() - self._last_summary > 10:
            self._emit_db_summary()
            self._last_summary = time.time()

        latency_ms = round(random.uniform(5, 25), 1) if not active_channels else round(random.uniform(2000, 4500), 1)
        self.emit_metric("subscriber_db.query_latency_ms", latency_ms, "ms")
        self.emit_metric("subscriber_db.pool_active", float(random.randint(30, 60) if not active_channels else random.randint(90, 100)), "connections")
        self.emit_metric("subscriber_db.rows_scanned", float(random.randint(1, 100)), "rows")

    def _emit_query(self) -> None:
        self._query_count += 1
        query_type = random.choice(["SELECT", "UPDATE", "INSERT"])
        table = random.choice(["subscribers", "activation_log", "subscriber_profiles"])
        latency_ms = round(random.uniform(5, 20), 1)
        self.emit_log(
            "INFO",
            f"[DB] query_executed type={query_type} table={table} latency_ms={latency_ms} rows=1 status=OK",
            {
                "operation": "query_executed",
                "db.query_type": query_type,
                "db.table": table,
                "db.latency_ms": latency_ms,
            },
        )

    def _emit_pool_metrics(self) -> None:
        active = random.randint(30, 60)
        idle = random.randint(20, 40)
        self.emit_log(
            "INFO",
            f"[DB] pool_status active={active} idle={idle} max=100 wait_queue=0 status=NORMAL",
            {
                "operation": "pool_status",
                "db.pool_active": active,
                "db.pool_idle": idle,
                "db.pool_max": 100,
            },
        )

    def _emit_db_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[DB] db_summary queries={self._query_count} avg_latency_ms=12 replication_lag_ms=0 status=NORMAL",
            {
                "operation": "db_summary",
                "db.total_queries": self._query_count,
                "db.avg_latency_ms": 12,
            },
        )
