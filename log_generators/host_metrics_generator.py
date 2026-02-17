#!/usr/bin/env python3
"""Host Metrics Generator — sends system.* metrics for Elastic Infrastructure UI via OTLP.

Generates realistic host metrics matching the OTel hostmetricsreceiver scraper
scope names, so Elastic's Infrastructure UI recognizes them as host metrics.

Generates for 3 hosts (one per cloud: AWS, GCP, Azure) matching the active
scenario's multi-cloud architecture.

Usage (standalone):
    python3 -m log_generators.host_metrics_generator
"""

from __future__ import annotations

import logging
import os
import random
import signal
import threading
import time

from app.telemetry import OTLPClient, _format_attributes, SCHEMA_URL, _now_ns
from app.config import ACTIVE_SCENARIO

logger = logging.getLogger("host-metrics-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
METRICS_INTERVAL = int(os.getenv("METRICS_INTERVAL", "10"))  # seconds between scrapes

# ── OTel hostmetricsreceiver scope names ──────────────────────────────────────
SCRAPER_BASE = "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver/internal/scraper"
SCRAPERS = {
    "load": f"{SCRAPER_BASE}/loadscraper",
    "cpu": f"{SCRAPER_BASE}/cpuscraper",
    "memory": f"{SCRAPER_BASE}/memoryscraper",
    "disk": f"{SCRAPER_BASE}/diskscraper",
    "filesystem": f"{SCRAPER_BASE}/filesystemscraper",
    "network": f"{SCRAPER_BASE}/networkscraper",
    "processes": f"{SCRAPER_BASE}/processesscraper",
}

# ── Host definitions from active scenario ─────────────────────────────────────
def _load_hosts():
    from scenarios import get_scenario
    return get_scenario(ACTIVE_SCENARIO).hosts

HOSTS = _load_hosts()



def _build_host_resource(host_cfg: dict) -> dict:
    """Build OTLP resource for a host with all required Infrastructure UI attributes."""
    attrs = {}
    for key in [
        "host.name", "host.id", "host.arch", "host.type", "host.image.id",
        "host.cpu.model.name", "host.cpu.vendor.id", "host.cpu.family",
        "host.cpu.model.id", "host.cpu.stepping", "host.cpu.cache.l2.size",
        "os.type", "os.description",
        "cloud.provider", "cloud.platform", "cloud.region",
        "cloud.availability_zone", "cloud.account.id", "cloud.instance.id",
    ]:
        if key in host_cfg:
            attrs[key] = host_cfg[key]

    attrs["telemetry.sdk.name"] = "opentelemetry"
    attrs["telemetry.sdk.version"] = "1.24.0"
    attrs["telemetry.sdk.language"] = "python"
    # NOTE: Do NOT set data_stream.* attributes here — let the Elastic OTLP
    # endpoint auto-route based on metric names/scope. This is required for
    # the Infrastructure UI to recognize these as host metrics.

    # Format array attributes specially
    formatted = _format_attributes(attrs)

    # Add array-type attributes (host.ip, host.mac)
    for arr_key in ["host.ip", "host.mac"]:
        if arr_key in host_cfg:
            formatted.append({
                "key": arr_key,
                "value": {
                    "arrayValue": {
                        "values": [{"stringValue": v} for v in host_cfg[arr_key]]
                    }
                }
            })

    return {
        "attributes": formatted,
        "schemaUrl": SCHEMA_URL,
    }


# ── Per-host metric state (for cumulative counters) ──────────────────────────
class HostMetricState:
    """Tracks cumulative counter values for a single host."""

    def __init__(self, cpu_count: int, mem_total: int, disk_total: int, rng: random.Random):
        self.cpu_count = cpu_count
        self.mem_total = mem_total
        self.disk_total = disk_total
        self._rng = rng
        # Cumulative counters
        self.cpu_time = {
            f"cpu{i}": {"user": rng.uniform(1000, 5000), "system": rng.uniform(500, 2000),
                        "idle": rng.uniform(10000, 50000), "wait": rng.uniform(10, 200)}
            for i in range(cpu_count)
        }
        self.disk_io_read = rng.uniform(1e9, 5e9)
        self.disk_io_write = rng.uniform(2e9, 10e9)
        self.disk_ops_read = rng.randint(100000, 500000)
        self.disk_ops_write = rng.randint(200000, 800000)
        self.net_io_recv = rng.uniform(5e9, 20e9)
        self.net_io_send = rng.uniform(2e9, 10e9)
        # Additional cumulative counters for OTel dashboard panels
        self.disk_io_time_read = rng.uniform(1000, 10000)    # seconds of IO time
        self.disk_io_time_write = rng.uniform(2000, 15000)
        self.net_packets_recv = rng.randint(5000000, 50000000)
        self.net_packets_send = rng.randint(3000000, 30000000)
        self.net_dropped_recv = rng.randint(0, 500)
        self.net_dropped_send = rng.randint(0, 300)
        self.net_errors_recv = rng.randint(0, 200)
        self.net_errors_send = rng.randint(0, 100)
        self.processes_created = rng.randint(10000, 100000)

    def tick(self):
        """Advance cumulative counters by a realistic amount."""
        rng = self._rng
        for cpu_id in self.cpu_time:
            self.cpu_time[cpu_id]["user"] += rng.uniform(0.5, 3.0)
            self.cpu_time[cpu_id]["system"] += rng.uniform(0.2, 1.5)
            self.cpu_time[cpu_id]["idle"] += rng.uniform(5.0, 9.0)
            self.cpu_time[cpu_id]["wait"] += rng.uniform(0.0, 0.5)
        self.disk_io_read += rng.randint(50000, 5000000)
        self.disk_io_write += rng.randint(100000, 10000000)
        self.disk_ops_read += rng.randint(5, 200)
        self.disk_ops_write += rng.randint(10, 500)
        self.disk_io_time_read += rng.uniform(0.01, 0.5)
        self.disk_io_time_write += rng.uniform(0.02, 1.0)
        self.net_io_recv += rng.randint(100000, 50000000)
        self.net_io_send += rng.randint(50000, 20000000)
        self.net_packets_recv += rng.randint(100, 50000)
        self.net_packets_send += rng.randint(50, 30000)
        self.net_dropped_recv += rng.randint(0, 2)
        self.net_dropped_send += rng.randint(0, 1)
        self.net_errors_recv += rng.randint(0, 1)
        self.net_errors_send += rng.randint(0, 1)
        self.processes_created += rng.randint(1, 10)


def _build_sum_metric(name: str, value, unit: str, attributes: dict | None = None, is_int: bool = False) -> dict:
    """Build a cumulative sum metric."""
    now = _now_ns()
    dp: dict = {
        "startTimeUnixNano": str(int(now) - 60_000_000_000),
        "timeUnixNano": now,
    }
    if is_int:
        dp["asInt"] = str(int(value))
    else:
        dp["asDouble"] = float(value)

    if attributes:
        dp["attributes"] = _format_attributes(attributes)

    return {
        "name": name,
        "unit": unit,
        "sum": {
            "dataPoints": [dp],
            "aggregationTemporality": 2,  # cumulative
            "isMonotonic": True,
        },
    }


def _build_gauge_metric(name: str, value, unit: str, attributes: dict | None = None, is_int: bool = False) -> dict:
    """Build a gauge metric."""
    now = _now_ns()
    dp: dict = {"timeUnixNano": now}
    if is_int:
        dp["asInt"] = str(int(value))
    else:
        dp["asDouble"] = float(value)

    if attributes:
        dp["attributes"] = _format_attributes(attributes)

    return {
        "name": name,
        "unit": unit,
        "gauge": {"dataPoints": [dp]},
    }


def _generate_host_metrics(state: HostMetricState, rng: random.Random) -> dict[str, list]:
    """Generate all host metrics grouped by scraper scope name.

    Returns dict mapping scope_name -> list of metric dicts.
    """
    state.tick()
    metrics_by_scope: dict[str, list] = {}

    # ── Load metrics ──
    load_1m = rng.uniform(0.5, 4.0)
    load_5m = load_1m * rng.uniform(0.7, 1.1)
    load_15m = load_5m * rng.uniform(0.8, 1.05)
    metrics_by_scope[SCRAPERS["load"]] = [
        _build_gauge_metric("system.cpu.load_average.1m", load_1m, "{thread}"),
        _build_gauge_metric("system.cpu.load_average.5m", load_5m, "{thread}"),
        _build_gauge_metric("system.cpu.load_average.15m", load_15m, "{thread}"),
    ]

    # ── CPU metrics ──
    cpu_metrics = [
        _build_gauge_metric("system.cpu.logical.count", state.cpu_count, "{cpu}", is_int=True),
    ]
    for cpu_id, times in state.cpu_time.items():
        total = sum(times.values())
        for state_name, val in times.items():
            cpu_metrics.append(_build_sum_metric(
                "system.cpu.time", val, "s",
                attributes={"cpu": cpu_id, "state": state_name},
            ))
            cpu_metrics.append(_build_gauge_metric(
                "system.cpu.utilization", val / total if total > 0 else 0, "1",
                attributes={"cpu": cpu_id, "state": state_name},
            ))
    metrics_by_scope[SCRAPERS["cpu"]] = cpu_metrics

    # ── Memory metrics ──
    mem_used_pct = rng.uniform(0.35, 0.85)
    mem_cached_pct = rng.uniform(0.05, 0.20)
    mem_buffered_pct = rng.uniform(0.01, 0.05)
    mem_free_pct = 1.0 - mem_used_pct - mem_cached_pct - mem_buffered_pct
    if mem_free_pct < 0:
        mem_free_pct = 0.05
        mem_used_pct = 1.0 - mem_free_pct - mem_cached_pct - mem_buffered_pct

    mem_total = state.mem_total
    mem_states = {
        "used": mem_used_pct,
        "free": mem_free_pct,
        "cached": mem_cached_pct,
        "buffered": mem_buffered_pct,
    }
    mem_metrics = []
    for mem_state, pct in mem_states.items():
        mem_metrics.append(_build_gauge_metric(
            "system.memory.usage", int(mem_total * pct), "By",
            attributes={"state": mem_state}, is_int=True,
        ))
        mem_metrics.append(_build_gauge_metric(
            "system.memory.utilization", pct, "1",
            attributes={"state": mem_state},
        ))
    # Add slab states for utilization
    for slab_state in ["slab_reclaimable", "slab_unreclaimable"]:
        slab_pct = rng.uniform(0.01, 0.03)
        mem_metrics.append(_build_gauge_metric(
            "system.memory.utilization", slab_pct, "1",
            attributes={"state": slab_state},
        ))
    metrics_by_scope[SCRAPERS["memory"]] = mem_metrics

    # ── Disk metrics ──
    disk_metrics = []
    for device in ["sda", "sdb"]:
        disk_metrics.append(_build_sum_metric(
            "system.disk.io", state.disk_io_read, "By",
            attributes={"device": device, "direction": "read"},
        ))
        disk_metrics.append(_build_sum_metric(
            "system.disk.io", state.disk_io_write, "By",
            attributes={"device": device, "direction": "write"},
        ))
        disk_metrics.append(_build_sum_metric(
            "system.disk.operations", state.disk_ops_read, "{operation}",
            attributes={"device": device, "direction": "read"}, is_int=True,
        ))
        disk_metrics.append(_build_sum_metric(
            "system.disk.operations", state.disk_ops_write, "{operation}",
            attributes={"device": device, "direction": "write"}, is_int=True,
        ))
        # disk.io_time — cumulative seconds spent on IO (OTel dashboard panel)
        disk_metrics.append(_build_sum_metric(
            "system.disk.io_time", state.disk_io_time_read, "s",
            attributes={"device": device, "direction": "read"},
        ))
        disk_metrics.append(_build_sum_metric(
            "system.disk.io_time", state.disk_io_time_write, "s",
            attributes={"device": device, "direction": "write"},
        ))
    metrics_by_scope[SCRAPERS["disk"]] = disk_metrics

    # ── Filesystem metrics ──
    fs_metrics = []
    disk_total = state.disk_total
    disk_used_pct = rng.uniform(0.20, 0.75)
    for device, mountpoint, fs_type in [("/dev/sda1", "/", "ext4"), ("/dev/sdb1", "/data", "xfs")]:
        used = int(disk_total * disk_used_pct)
        free = disk_total - used
        fs_metrics.append(_build_gauge_metric(
            "system.filesystem.usage", used, "By",
            attributes={"device": device, "mountpoint": mountpoint, "type": fs_type, "state": "used"},
            is_int=True,
        ))
        fs_metrics.append(_build_gauge_metric(
            "system.filesystem.usage", free, "By",
            attributes={"device": device, "mountpoint": mountpoint, "type": fs_type, "state": "free"},
            is_int=True,
        ))
        fs_metrics.append(_build_gauge_metric(
            "system.filesystem.utilization", disk_used_pct, "1",
            attributes={"device": device, "mountpoint": mountpoint, "type": fs_type},
        ))
    metrics_by_scope[SCRAPERS["filesystem"]] = fs_metrics

    # ── Network metrics ──
    net_metrics = []
    for device in ["eth0", "eth1"]:
        net_metrics.append(_build_sum_metric(
            "system.network.io", state.net_io_recv, "By",
            attributes={"device": device, "direction": "receive"},
        ))
        net_metrics.append(_build_sum_metric(
            "system.network.io", state.net_io_send, "By",
            attributes={"device": device, "direction": "transmit"},
        ))
        # network.packets — cumulative packet counts (OTel dashboard panel)
        net_metrics.append(_build_sum_metric(
            "system.network.packets", state.net_packets_recv, "{packet}",
            attributes={"device": device, "direction": "receive"}, is_int=True,
        ))
        net_metrics.append(_build_sum_metric(
            "system.network.packets", state.net_packets_send, "{packet}",
            attributes={"device": device, "direction": "transmit"}, is_int=True,
        ))
        # network.dropped — cumulative dropped packet counts (OTel dashboard panel)
        net_metrics.append(_build_sum_metric(
            "system.network.dropped", state.net_dropped_recv, "{packet}",
            attributes={"device": device, "direction": "receive"}, is_int=True,
        ))
        net_metrics.append(_build_sum_metric(
            "system.network.dropped", state.net_dropped_send, "{packet}",
            attributes={"device": device, "direction": "transmit"}, is_int=True,
        ))
        # network.errors — cumulative error counts (OTel dashboard panel)
        net_metrics.append(_build_sum_metric(
            "system.network.errors", state.net_errors_recv, "{error}",
            attributes={"device": device, "direction": "receive"}, is_int=True,
        ))
        net_metrics.append(_build_sum_metric(
            "system.network.errors", state.net_errors_send, "{error}",
            attributes={"device": device, "direction": "transmit"}, is_int=True,
        ))
    metrics_by_scope[SCRAPERS["network"]] = net_metrics

    # ── Process metrics ──
    running_count = rng.randint(1, 8)
    sleeping = rng.randint(50, 200)
    metrics_by_scope[SCRAPERS["processes"]] = [
        _build_gauge_metric("system.processes.count", running_count, "{process}",
                            attributes={"status": "running"}, is_int=True),
        _build_gauge_metric("system.processes.count", sleeping, "{process}",
                            attributes={"status": "sleeping"}, is_int=True),
        # processes.created — cumulative process creation count (OTel dashboard panel)
        _build_sum_metric("system.processes.created", state.processes_created, "{process}",
                          is_int=True),
    ]

    return metrics_by_scope


def _send_metrics_with_scopes(client: OTLPClient, resource: dict, metrics_by_scope: dict[str, list]) -> int:
    """Send metrics grouped by scope name. Returns total metric count sent."""
    total = 0
    for scope_name, metrics in metrics_by_scope.items():
        if not metrics:
            continue
        # Build the payload with the specific scope name
        payload = {
            "resourceMetrics": [
                {
                    "resource": resource,
                    "scopeMetrics": [
                        {
                            "scope": {"name": scope_name, "version": "0.115.0"},
                            "metrics": metrics,
                        }
                    ],
                }
            ]
        }
        client._send(f"{client.endpoint}/v1/metrics", payload, "metrics")
        total += len(metrics)
    return total


# ── Run loop (used by ServiceManager and standalone) ──────────────────────────
def run(client: OTLPClient, stop_event: threading.Event, scenario_data: dict | None = None) -> None:
    """Run host metrics generator loop until stop_event is set."""
    rng = random.Random()

    hosts = scenario_data["hosts"] if scenario_data else HOSTS

    # Build resources and metric state for each host
    host_resources = []
    host_states = []
    for host_cfg in hosts:
        resource = _build_host_resource(host_cfg)
        state = HostMetricState(
            cpu_count=host_cfg["cpu_count"],
            mem_total=host_cfg["memory_total_bytes"],
            disk_total=host_cfg["disk_total_bytes"],
            rng=rng,
        )
        host_resources.append(resource)
        host_states.append(state)

    total_metrics = 0
    scrape_count = 0

    logger.info("Host metrics generator started (interval=%ds, hosts=%d)",
                METRICS_INTERVAL, len(hosts))

    while not stop_event.is_set():
        batch_metrics = 0
        for resource, state in zip(host_resources, host_states):
            metrics_by_scope = _generate_host_metrics(state, rng)
            sent = _send_metrics_with_scopes(client, resource, metrics_by_scope)
            batch_metrics += sent

        scrape_count += 1
        total_metrics += batch_metrics
        logger.info(
            "Scrape %d: sent %d metrics across %d hosts (total=%d)",
            scrape_count, batch_metrics, len(hosts), total_metrics,
        )

        stop_event.wait(METRICS_INTERVAL)

    logger.info("Host metrics generator stopped. Total: %d metrics in %d scrapes",
                total_metrics, scrape_count)


# ── Standalone entry point ────────────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    client = OTLPClient()
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    duration = int(os.environ.get("RUN_DURATION", "60"))
    timer = threading.Timer(duration, stop_event.set)
    timer.daemon = True
    timer.start()
    logger.info("Running for %ds (standalone mode)", duration)

    run(client, stop_event)
    timer.cancel()
    client.close()


if __name__ == "__main__":
    main()
