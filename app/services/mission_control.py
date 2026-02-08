"""Mission Control service — AWS us-east-1. Orchestrates launch sequence."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MissionControlService(BaseService):
    SERVICE_NAME = "mission-control"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._last_health_summary = time.time()
        self._subsystem_poll_idx = 0
        self._subsystems = [
            "propulsion", "guidance", "communications",
            "payload", "relay", "ground", "validation", "safety",
        ]

    def generate_telemetry(self) -> None:
        # ── Check for active faults (this is a cascade target) ──
        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_subsystem_poll()
        self._emit_phase_log()

        if time.time() - self._last_health_summary > 10:
            self._emit_health_summary()
            self._last_health_summary = time.time()

        # Metrics
        self.emit_metric(
            "mission_control.subsystem_polls",
            self._subsystem_poll_idx,
            "polls",
        )
        self.emit_metric(
            "mission_control.active_alerts",
            float(len(cascade_channels)),
            "alerts",
        )

    def _emit_subsystem_poll(self) -> None:
        subsystem = self._subsystems[self._subsystem_poll_idx % len(self._subsystems)]
        self._subsystem_poll_idx += 1
        latency = round(random.uniform(1.2, 8.5), 1)
        self.emit_log(
            "INFO",
            f"Subsystem poll: {subsystem} responded in {latency}ms — status NOMINAL",
            {
                "operation": "subsystem_poll",
                "target.subsystem": subsystem,
                "poll.latency_ms": latency,
                "poll.result": "NOMINAL",
            },
        )

    def _emit_phase_log(self) -> None:
        phases_messages = {
            "PRE-LAUNCH": [
                "Pre-launch checks in progress — all systems reporting",
                "Vehicle power nominal, telemetry links active",
                "Launch director confirms readiness review underway",
            ],
            "COUNTDOWN": [
                "Countdown sequence active — monitoring all subsystems",
                "Go/No-Go poll in progress",
                "Final systems verification proceeding nominally",
            ],
            "LAUNCH": [
                "Main engine ignition confirmed",
                "Vehicle clearing tower, all engines nominal",
                "Thrust nominal, trajectory on profile",
            ],
            "ASCENT": [
                "Ascending through max-Q, structural loads nominal",
                "Stage separation approaching, systems go",
                "Telemetry nominal, tracking stable",
            ],
        }
        messages = phases_messages.get(self._phase, phases_messages["PRE-LAUNCH"])
        self.emit_log("INFO", random.choice(messages), {"operation": "phase_status"})

    def _emit_health_summary(self) -> None:
        active = self.get_cascade_channels_for_service()
        status = "NOMINAL" if not active else "DEGRADED"
        self.emit_log(
            "INFO",
            f"Health summary: {len(self._subsystems)} subsystems polled — overall status {status}",
            {
                "operation": "health_summary",
                "health.subsystem_count": len(self._subsystems),
                "health.overall_status": status,
                "health.active_alerts": len(active),
            },
        )
