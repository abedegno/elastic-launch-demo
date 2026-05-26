---
name: add-scenario
description: Add a new customer-vertical scenario (e.g. retail, logistics, telco) to elastic-launch-demo. Use when the user wants to onboard a new demo persona — gather their customer brief, design 9 services + 20 fault channels, and generate the scenario folder. Enforces that all scenario-specific code lives in scenarios/<id>/ and generators/deployer stay untouched.
---

# Add a new scenario

This skill gathers a customer brief, designs a vertically-appropriate scenario, and generates the full `scenarios/<id>/` folder. No files outside `scenarios/<id>/` are ever modified.

Read [GUARDRAILS.md](.claude/skills/add-scenario/GUARDRAILS.md) now and hold every rule in it for the duration of this session.

---

## Phase 1: Gather the customer brief

Parse any context the user already provided. Then read [BRIEF.md](.claude/skills/add-scenario/BRIEF.md) and ask — via `AskUserQuestion` — only about signals that are missing. Ask at most 3 questions per call.

Required signals before proceeding to Phase 2:
- **Vertical** — broad industry label
- **Primary workflow** — the user-visible business flow the demo will center on
- **Pain points** — top 2–3 observability gaps the customer feels

Helpful but not blocking: goals/wins, personas in the room, compliance angle, tone/theme hint.

---

## Phase 2: Pick a reference scenario

Run the following for every scenario folder (excluding `space`):

```
git log -1 --format="%cI %f" -- scenarios/<id>/scenario.py
```

Pick the scenario with the most recent commit timestamp. Read the full `scenarios/<id>/scenario.py` of the winner. That file is your structural template for the shapes of `services`, `channel_registry`, `hosts`, `k8s_clusters`, `service_topology`, `entry_endpoints`, `db_operations`, `get_trace_attributes`, `get_rca_clues`, `get_fault_params`, and `executive_kpis`.

Also read [CONTRACT.md](.claude/skills/add-scenario/CONTRACT.md) now as a generation checklist.

---

## Phase 3: Design — propose then confirm

Synthesize the brief into a one-screen design draft. Present it via `AskUserQuestion` (single question, long description field) and ask the user to confirm, adjust, or replace before you write any code.

The draft must cover:

**Identity**
- `scenario_id` — short lowercase slug (e.g. `logistics`, `telco`, `medtech`)
- `namespace` — telemetry prefix, same as or abbreviated from scenario_id
- `scenario_name` — display name (e.g. "Global Logistics Platform")
- `scenario_description` — 2–3 sentence card blurb
- `scenario_icon` — emoji

**9 services** (3 per cloud — AWS, GCP, Azure)
- Name, subsystem, language (∈ python/java/go/dotnet/rust/cpp), cloud, purpose
- Designate which service is the `executive_kpi_emitter_service_name`

**20 fault channels summary** — channel number, name, subsystem, and one-line description
- Channels 1–15: HITL faults (human must approve remediation). These should be the "interesting" investigation stories — data corruption, novel anomalies, multi-system cascades, regulatory/compliance violations, fraud signals, anything that benefits from an SRE's judgment.
- Channels 16–20: Auto-remediate faults. These MUST be faults that would plausibly be handled automatically in a real production runbook: pod restart on OOM, autoscaler bumping replicas under CPU spike, circuit-breaker tripping a stuck upstream, cache flush after TTL expiry, credential/token rotation, certificate auto-renewal, budget cap reset, cache warmup. Do NOT put investigation-worthy faults here. Validate this choice against the rule: "Would a real on-call team let this auto-resolve without human review?"

**Theme sketch** — primary accent color, `chaos_title`, `service_label`, `channel_label`

**Executive KPI categories** — 4 sections of 6 metrics each (titles only, not field names yet)

---

## Phase 4: Generate scaffolding

After the user confirms the design, create all files. Do not ask permission for each file — generate them all.

### File list

```
scenarios/<id>/__init__.py
scenarios/<id>/scenario.py
scenarios/<id>/executive_kpis.py
scenarios/<id>/services/__init__.py
scenarios/<id>/services/<svc1>.py
scenarios/<id>/services/<svc2>.py
... (9 total)
```

### `__init__.py` content

```python
"""<Scenario Display Name> scenario — <one-line description>."""
```

### `scenario.py` structure

Follow this exact top-level structure, in this order:

```python
"""<Scenario Display Name> scenario — <one-line description>."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class <Name>Scenario(BaseScenario):
    """<Class docstring>."""

    # ── Identity ──────────────────────────────────────────────────────
    # scenario_id, scenario_icon, scenario_name, scenario_description, namespace, sort_order
    # executive_kpi_emitter_service_name, executive_dashboard_intro
    # executive_kpi_sections, executive_trend_charts
    # raw_log_profile

    # ── Services ──────────────────────────────────────────────────────
    # services (9 services)

    # ── Channel Registry ──────────────────────────────────────────────
    # channel_registry (20 channels)

    # ── Topology ──────────────────────────────────────────────────────
    # service_topology, entry_endpoints, db_operations

    # ── Infrastructure ────────────────────────────────────────────────
    # hosts (3), k8s_clusters (3)

    # ── Theme ─────────────────────────────────────────────────────────
    # theme, countdown_config

    # ── Agent Config ──────────────────────────────────────────────────
    # agent_config, assessment_tool_config, knowledge_base_docs

    # ── Service Classes ───────────────────────────────────────────────
    # get_service_classes() — lazy imports

    # ── Trace Attributes & RCA ────────────────────────────────────────
    # get_trace_attributes, get_rca_clues, get_fault_params


scenario = <Name>Scenario()
```

The module-level `scenario = <Name>Scenario()` at the bottom is required for auto-discovery.

### `services/__init__.py`

Empty file (or single-line docstring).

### Per-service file

Each of the 9 service files follows this pattern:

```python
"""<ServiceName> service — <one-line purpose>."""

from __future__ import annotations

from app.services.base_service import BaseService
from scenarios.<id>.executive_kpis import emit_executive_business_metrics_if_eligible


class <ServiceName>Service(BaseService):
    SERVICE_NAME = "<service-key-from-services-dict>"

    def generate_telemetry(self) -> None:
        # Emit fault logs for active fault channels
        for ch in self.get_active_channels_for_service():
            self.emit_fault_logs(ch)

        # Emit cascade logs for channels where this service is downstream
        for ch in self.get_cascade_channels_for_service():
            self.emit_cascade_logs(ch)

        # Emit business KPIs (only fires for the designated emitter service)
        emit_executive_business_metrics_if_eligible(self)
```

Only the designated `executive_kpi_emitter_service_name` service should import and call `emit_executive_business_metrics_if_eligible`. Add the import to all other service files too (they'll be no-ops — the function gates on SERVICE_NAME internally) or only add it to the emitter. Choose whichever is consistent with the reference scenario.

### `executive_kpis.py`

```python
"""Executive business KPI emitter for <Scenario Name>."""

from __future__ import annotations

import random


def emit_executive_business_metrics_if_eligible(service) -> None:
    """Emit synthetic business.* OTLP gauges from the designated KPI emitter service."""
    if service.SERVICE_NAME != "<executive_kpi_emitter_service_name>":
        return

    rng = random.Random()
    ctx = service._ctx
    otlp = service._otlp_client

    # Emit one gauge per KPI defined in scenario.executive_kpi_sections
    # Use metrics field names that match scenario.executive_kpi_sections specs
    # e.g. otlp.emit_gauge("business.gmv_usd_per_min", rng.uniform(...), ctx)
    # Pattern: follow the reference scenario's executive_kpis.py exactly
```

Read the reference scenario's `executive_kpis.py` for the exact OTLP emit pattern and fill in all KPI fields from `executive_kpi_sections`.

---

## Phase 5: Flesh out all properties

Work through [CONTRACT.md](.claude/skills/add-scenario/CONTRACT.md) top-to-bottom. For each property, generate realistic, domain-appropriate content that will resonate with the customer vertical. Keep these rules:

- **Services**: each service dict has exactly these keys: `cloud_provider`, `cloud_region`, `cloud_platform`, `cloud_availability_zone`, `subsystem`, `language`. Language ∈ {python, java, go, dotnet, rust, cpp}.
- **Channel_registry**: every channel must have `name`, `subsystem`, `error_type`, `affected_services`, `cascade_services`, `description`, `investigation_notes`, `remediation_action`, `error_message`, `stack_trace`. `vehicle_section` and `sensor_type` are domain flavor — include them. Every `{placeholder}` in `error_message` and `stack_trace` must be supplied by `get_fault_params(channel)`.
- **`get_fault_params`**: returns a dict keyed by channel number. Every placeholder used across error_message and stack_trace for that channel must appear as a key. Use `rng = random.Random(channel + int(time.time()) // 10)` for time-varying but reproducible values.
- **`get_trace_attributes`**: return a `base` dict with 2–3 domain-wide attributes, then a per-service dict with 4–5 domain-specific OTel-style attributes. Merge and return.
- **`get_rca_clues`**: for each of the 20 channels, provide a per-service inner dict of 2–3 attributes that give partial clues without exposing the full root cause. Different services should get different clues — no single service has the complete picture.
- **`knowledge_base_docs`**: return `[]`. The deployer generates KB docs from `channel_registry`.
- **`agent_config.system_prompt`**: include the agent's persona, domain expertise, all 20 `error_type` values grouped by subsystem, and the reminder "Log messages are in body.text — NEVER search the body field alone."
- **`hosts`**: 3 hosts, one per cloud. Use realistic OTel host attributes matching the cloud provider (see CONTRACT.md for the exact key list). Use the namespace to name the host (e.g. `<ns>-aws-host-01`).
- **`k8s_clusters`**: 3 clusters (EKS, GKE, AKS). Each cluster's `services` list must contain exactly the 3 service names for that cloud.
- **`service_topology`**: every service should appear as a caller at least once. The topology should reflect the primary business workflow. The executive KPI emitter service should be reachable via the topology.
- **`raw_log_profile`**: set `service_name` to the edge-facing service for the vertical, and `paths` to realistic URL paths for that domain. Set `change_point_path` to the highest-revenue path (checkout, payment, etc.).
- **`theme`**: choose an accent color that evokes the vertical (e.g. logistics → orange `#f97316`; healthcare → teal `#0d9488`; telco → purple `#7c3aed`). Set `chaos_title`, `service_label` (`"Service"`, `"Node"`, `"System"`, `"Module"`, etc.), and `channel_label` (`"Channel"`, `"Incident"`, `"Alert"`, etc.) to vocabulary the vertical naturally uses.

---

## Phase 6: Validate

After generation, run these checks:

**Auto-discovery check:**
```bash
python -c "
from scenarios import list_scenarios
hit = next((s for s in list_scenarios() if s['id'] == '<id>'), None)
print('FOUND:', hit) if hit else print('NOT FOUND — check scenario = <Class>() at module bottom')
"
```

**Static integrity checks** (run inline Python or grep):
1. Every value in `channel_registry[ch]["affected_services"]` and `cascade_services` appears as a key in `services`.
2. Every `{name}` placeholder (regex `\{(\w+)\}`) in every `error_message` and `stack_trace` is a key in `get_fault_params(ch)` for that channel.
3. `len(scenario.get_service_classes()) == 9`
4. `len(scenario.channel_registry) == 20`
5. `len(scenario.hosts) == 3` and `len(scenario.k8s_clusters) == 3`
6. Channels 16–20: confirm each `remediation_action` describes a plausible automated runbook action.

**Scope check:**
```bash
git diff --name-only
```
Output must show only files under `scenarios/<id>/`. If any other file appears, stop and alert the user.

**Report:** Summarize what was generated, the file count, any validation warnings, and how to activate:
```
ACTIVE_SCENARIO=<id> ./start.sh
```
