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

Pick the scenario with the most recent commit timestamp — on a tie, use `fanatics`. Read the full `scenarios/<id>/scenario.py` of the winner. That file is your structural template for the shapes of `services`, `channel_registry`, `hosts`, `k8s_clusters`, `service_topology`, `entry_endpoints`, `db_operations`, `get_trace_attributes`, `get_rca_clues`, `get_fault_params`, and `executive_kpis`.

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
- Channels 16–20: Auto-remediate faults — must be plausible unattended runbook actions (pod restart, cache flush, cert renewal, circuit-breaker reset, etc.). See [GUARDRAILS.md](GUARDRAILS.md) §6 for the full rule and validation question.

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

Match the section order and structure of the reference scenario exactly. The module must end with:

```python
scenario = <Name>Scenario()
```

This line is required for auto-discovery by `scenarios/__init__.py`.

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit <scenario> leadership KPI gauges once per telemetry cycle."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Emit one metric per KPI defined in scenario.executive_kpi_sections.
    # service.emit_metric(metric_name, value, unit)
    # e.g. emit("business.gmv_usd_per_min", round(random.uniform(1_000.0, 9_000.0), 1), "USD/min")
    # Field names must exactly match what executive_kpi_sections specs reference.
```

Read the reference scenario's `executive_kpis.py` for the exact OTLP emit pattern and fill in all KPI fields from `executive_kpi_sections`.

---

## Phase 5: Flesh out all properties

Work through [CONTRACT.md](CONTRACT.md) top-to-bottom. Pay extra attention to: language allowlist, placeholder/fault-param parity, and k8s-service-to-cloud grouping.

Two properties not in CONTRACT.md:

- **`raw_log_profile`**: set `service_name` to the edge-facing service, `paths` to realistic vertical URL paths, and `change_point_path` to the highest-revenue path (checkout, payment, etc.).
- **`theme.accent_primary`**: choose a color that evokes the vertical (logistics → `#f97316`; healthcare → `#0d9488`; telco → `#7c3aed`; financial → `#10b981`). Match `text_accent` to `accent_primary`.

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
