"""ScenarioInstance — self-contained runtime for one deployment.

Owns its own OTLPClient, ChaosController, ServiceManager, and stop_event.
Multiple instances can run simultaneously, each targeting a different
Elastic cluster with different scenario configurations.
"""

from __future__ import annotations

import logging
import threading

from app.chaos.controller import ChaosController
from app.context import ScenarioContext
from app.dashboard.websocket import DashboardWebSocket
from app.services.manager import ServiceManager
from app.telemetry import OTLPClient

logger = logging.getLogger("nova7.instance")


class ScenarioInstance:
    """One running deployment: scenario + credentials + generators."""

    def __init__(self, ctx: ScenarioContext):
        self.ctx = ctx
        self.scenario_id = ctx.scenario_id
        self.deployment_id = ctx.scenario_id  # default; can be overridden

        # Build per-instance OTLPClient
        self.otlp = OTLPClient(
            endpoint=ctx.otlp_endpoint or None,
            api_key=ctx.otlp_api_key or None,
        )

        # Per-instance chaos controller with this scenario's channel registry
        self.chaos_controller = ChaosController(channel_registry=ctx.channel_registry)

        # Per-instance dashboard WS (shared broadcast for all connected clients)
        self.dashboard_ws = DashboardWebSocket()

        # ServiceManager — owns service threads + generator threads
        self.service_manager = ServiceManager(
            chaos_controller=self.chaos_controller,
            dashboard_ws=self.dashboard_ws,
            ctx=ctx,
            otlp_client=self.otlp,
        )

        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start all services and generators for this deployment."""
        if self._running:
            logger.warning("Instance %s already running", self.scenario_id)
            return
        self.service_manager.start_all()
        self._running = True
        logger.info("Instance %s started (%d services)", self.scenario_id,
                     len(self.service_manager.services))

    def stop(self) -> None:
        """Stop all services and generators."""
        if not self._running:
            return
        self.service_manager.stop_all()
        self._running = False
        logger.info("Instance %s stopped", self.scenario_id)
