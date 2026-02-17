"""DeploymentStore — SQLite persistence for active deployments.

Survives app restarts so active deployments can be restored from the DB
rather than being lost when the process recycles.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from typing import Any

logger = logging.getLogger("nova7.store")

_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_DB_PATH = os.path.join(_DB_DIR, "deployments.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS deployments (
    deployment_id   TEXT PRIMARY KEY,
    scenario_id     TEXT NOT NULL,
    otlp_endpoint   TEXT NOT NULL DEFAULT '',
    otlp_api_key    TEXT NOT NULL DEFAULT '',
    elastic_url     TEXT NOT NULL DEFAULT '',
    elastic_api_key TEXT NOT NULL DEFAULT '',
    kibana_url      TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);
"""


class DeploymentStore:
    """Thread-safe SQLite store for deployment records."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def upsert(
        self,
        deployment_id: str,
        scenario_id: str,
        *,
        otlp_endpoint: str = "",
        otlp_api_key: str = "",
        elastic_url: str = "",
        elastic_api_key: str = "",
        kibana_url: str = "",
        status: str = "active",
    ) -> None:
        """Insert or replace a deployment record."""
        now = time.time()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO deployments
                       (deployment_id, scenario_id, otlp_endpoint, otlp_api_key,
                        elastic_url, elastic_api_key, kibana_url, status,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        deployment_id,
                        scenario_id,
                        otlp_endpoint,
                        otlp_api_key,
                        elastic_url,
                        elastic_api_key,
                        kibana_url,
                        status,
                        now,
                        now,
                    ),
                )

    def get(self, deployment_id: str) -> dict[str, Any] | None:
        """Return a single deployment record or None."""
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM deployments WHERE deployment_id = ?",
                    (deployment_id,),
                ).fetchone()
                return dict(row) if row else None

    def get_all_active(self) -> list[dict[str, Any]]:
        """Return all deployments with status='active'."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM deployments WHERE status = 'active' ORDER BY created_at",
                ).fetchall()
                return [dict(r) for r in rows]

    def set_status(self, deployment_id: str, status: str) -> None:
        """Update status of a deployment."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE deployments SET status = ?, updated_at = ? WHERE deployment_id = ?",
                    (status, time.time(), deployment_id),
                )

    def delete(self, deployment_id: str) -> None:
        """Remove a deployment record entirely."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM deployments WHERE deployment_id = ?",
                    (deployment_id,),
                )
