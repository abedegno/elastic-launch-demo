# Telecom Slides + Executive Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore two telecom-scenario surfaces lost during the rebase against `notoriousbdg/main`: per-scenario HTML slide decks and the live Business/Executive Kibana dashboard.

**Architecture:** All scenario-level changes are confined to `scenarios/telecom/**`. Cross-cutting changes to `app/main.py` and `app/selector/static/index.html` are additive (new routes, new mount loop, new conditional UI block) so other scenarios continue to behave identically. Validation is via smoke checks (import success, app startup clean, API responses, deploy end-to-end) since the repo has no pytest harness.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, vanilla JS, Kibana dashboards (NDJSON saved objects), OTLP-emitted `business.*` gauges.

**Spec:** [docs/superpowers/specs/2026-05-18-telecom-slides-and-exec-dashboard-design.md](../specs/2026-05-18-telecom-slides-and-exec-dashboard-design.md)

---

## Pre-flight

### Task 0: Establish baseline

**Files:** none

- [ ] **Step 1: Confirm working tree is clean and on the right branch**

Run:
```bash
git status -sb
```
Expected: `## add-telecom-scenario...origin/add-telecom-scenario`, working tree clean (or only untracked `tmp/` etc.).

- [ ] **Step 2: Confirm scenario registry currently loads 10 scenarios**

Run:
```bash
.venv/bin/python -c "from scenarios import list_scenarios; ids=[s['id'] for s in list_scenarios()]; print(sorted(ids)); assert len(ids)==10, f'Expected 10, got {len(ids)}'"
```
Expected: prints `['banking', 'ecommerce', 'fanatics', 'financial', 'gaming', 'gcp', 'healthcare', 'manufacturing', 'space', 'telecom']` and exits 0.

- [ ] **Step 3: Confirm the broken state for both features**

Run:
```bash
.venv/bin/python -c "from scenarios.telecom.scenario import scenario; print('emitter:', getattr(scenario, 'executive_kpi_emitter_service_name', None))"
```
Expected: `emitter: None`  (confirms exec dashboard properties not yet defined)

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/slides?deployment_id=telecom 2>/dev/null || echo "no server / no route"
```
Expected: `404` (no route) or "no server" — confirms slides route missing.

---

## Phase A — Executive dashboard for telecom (scenarios/telecom/ only)

### Task 1: Add executive dashboard scenario properties

**Files:**
- Modify: `scenarios/telecom/scenario.py` (insert ~80 lines after `countdown_config`/`agent_config` boundary — anywhere as a class-level set of properties)

- [ ] **Step 1: Verify the failing smoke state**

Run:
```bash
.venv/bin/python -c "from scenarios.telecom.scenario import scenario; print(repr(getattr(scenario, 'executive_kpi_emitter_service_name', None)))"
```
Expected: `None`

- [ ] **Step 2: Add the four properties to TelecomScenario class**

Open `scenarios/telecom/scenario.py`. Find the class body (`class TelecomScenario(BaseScenario):`). Add this block as new `@property` methods alongside the existing scenario_id/scenario_name/services/etc. — put it after the existing properties but BEFORE `agent_config`. The exact insertion point doesn't matter as long as it's inside the class:

```python
    # ── Executive Dashboard ───────────────────────────────────────────

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "bss-billing"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Meridian Telecom 5G subscriber platform KPIs** — subscriber growth, "
            "revenue & ARPU, network quality of experience, and retention. "
            "Synthetic `business.*` OTLP gauges from `bss-billing`."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Subscriber growth** — activations, MVNO, ports, eSIM",
                "specs": [
                    ("Activations / min", "metrics.business.activations_per_min"),
                    ("MVNO net-adds / min", "metrics.business.mvno_net_adds_per_min"),
                    ("Port-ins / min", "metrics.business.port_ins_per_min"),
                    ("Port-outs / min", "metrics.business.port_outs_per_min"),
                    ("eSIM provisions / min", "metrics.business.esim_provisions_per_min"),
                    ("Active subscribers (M)", "metrics.business.active_subscribers_m"),
                ],
            },
            {
                "header": "**Revenue & ARPU** — total revenue, by-tier, overage, roaming",
                "specs": [
                    ("Total revenue (USD/min)", "metrics.business.revenue_usd_per_min"),
                    ("Consumer ARPU (USD)", "metrics.business.consumer_arpu_usd"),
                    ("Enterprise ARPU (USD)", "metrics.business.enterprise_arpu_usd"),
                    ("MVNO partner revenue (USD/min)", "metrics.business.mvno_partner_revenue_usd_per_min"),
                    ("Data overage charges (USD/min)", "metrics.business.data_overage_charges_usd_per_min"),
                    ("Roaming revenue (USD/min)", "metrics.business.roaming_revenue_usd_per_min"),
                ],
            },
            {
                "header": "**Network & QoE** — handover, latency, voice, throughput",
                "specs": [
                    ("5G handover success (%)", "metrics.business.handover_success_pct"),
                    ("RAN latency p95 (ms)", "metrics.business.ran_latency_p95_ms"),
                    ("Voice MOS", "metrics.business.voice_mos"),
                    ("Data session est. success (%)", "metrics.business.data_session_success_pct"),
                    ("VoLTE call setup success (%)", "metrics.business.volte_call_setup_success_pct"),
                    ("Throughput p50 (Mbps)", "metrics.business.throughput_p50_mbps"),
                ],
            },
            {
                "header": "**Retention & support** — churn, NPS, tickets",
                "specs": [
                    ("Voluntary churn rate (%)", "metrics.business.voluntary_churn_rate_pct"),
                    ("NPS", "metrics.business.nps"),
                    ("Support tickets / min", "metrics.business.support_tickets_per_min"),
                    ("Avg ticket resolution (min)", "metrics.business.avg_ticket_resolution_min"),
                    ("First-call resolution (%)", "metrics.business.first_call_resolution_pct"),
                    ("Trouble-to-billing ratio (%)", "metrics.business.trouble_to_billing_ratio_pct"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Total revenue (USD/min)", "field": "metrics.business.revenue_usd_per_min", "y_label": "USD/min"},
            {"title": "Activations / min", "field": "metrics.business.activations_per_min", "y_label": "activations/min"},
            {"title": "Active subscribers (M)", "field": "metrics.business.active_subscribers_m", "y_label": "subscribers (M)"},
            {"title": "Voluntary churn rate (%)", "field": "metrics.business.voluntary_churn_rate_pct", "y_label": "%"},
            {"title": "RAN p95 latency (ms)", "field": "metrics.business.ran_latency_p95_ms", "y_label": "ms"},
            {"title": "NPS", "field": "metrics.business.nps", "y_label": "NPS"},
        ]
```

- [ ] **Step 3: Verify the smoke state passes**

Run:
```bash
.venv/bin/python -c "
from scenarios.telecom.scenario import scenario
print('emitter:', scenario.executive_kpi_emitter_service_name)
print('sections:', len(scenario.executive_kpi_sections))
print('trends:', len(scenario.executive_trend_charts))
print('intro snippet:', scenario.executive_dashboard_intro[:40])
assert scenario.executive_kpi_emitter_service_name == 'bss-billing'
assert len(scenario.executive_kpi_sections) == 4
assert all(len(s['specs']) == 6 for s in scenario.executive_kpi_sections)
assert len(scenario.executive_trend_charts) == 6
print('OK')
"
```
Expected: `emitter: bss-billing`, `sections: 4`, `trends: 6`, intro snippet, `OK`.

- [ ] **Step 4: Confirm all 10 scenarios still load**

Run:
```bash
.venv/bin/python -c "from scenarios import list_scenarios; ids=[s['id'] for s in list_scenarios()]; assert len(ids)==10, ids; print('OK 10 scenarios')"
```
Expected: `OK 10 scenarios`

- [ ] **Step 5: Commit**

```bash
git add scenarios/telecom/scenario.py
git commit -m "Add executive dashboard properties to telecom scenario"
```

### Task 2: Create the `business.*` metric emitter module

**Files:**
- Create: `scenarios/telecom/executive_kpis.py`

- [ ] **Step 1: Verify the failing smoke state**

Run:
```bash
.venv/bin/python -c "from scenarios.telecom.executive_kpis import emit_executive_business_metrics_if_eligible"
```
Expected: `ModuleNotFoundError: No module named 'scenarios.telecom.executive_kpis'`

- [ ] **Step 2: Write the file**

Create `scenarios/telecom/executive_kpis.py` with this content:

```python
"""Synthetic `business.*` OTLP gauges for the Meridian Telecom Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit live 5G subscriber platform KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Subscriber growth
    emit("business.activations_per_min", float(random.randint(380, 1_850)), "activations/min")
    emit("business.mvno_net_adds_per_min", float(random.randint(45, 280)), "net-adds/min")
    emit("business.port_ins_per_min", float(random.randint(120, 420)), "port-ins/min")
    emit("business.port_outs_per_min", float(random.randint(90, 380)), "port-outs/min")
    emit("business.esim_provisions_per_min", float(random.randint(200, 1_100)), "provisions/min")
    emit("business.active_subscribers_m", round(random.uniform(18.4, 19.2), 3), "subscribers (M)")

    # Revenue & ARPU
    emit("business.revenue_usd_per_min", round(random.uniform(82_000.0, 145_000.0), 1), "USD/min")
    emit("business.consumer_arpu_usd", round(random.uniform(38.2, 52.6), 2), "USD")
    emit("business.enterprise_arpu_usd", round(random.uniform(285.0, 480.0), 2), "USD")
    emit("business.mvno_partner_revenue_usd_per_min", round(random.uniform(4_500.0, 12_800.0), 1), "USD/min")
    emit("business.data_overage_charges_usd_per_min", round(random.uniform(1_800.0, 8_500.0), 1), "USD/min")
    emit("business.roaming_revenue_usd_per_min", round(random.uniform(2_200.0, 9_400.0), 1), "USD/min")

    # Network & QoE
    emit("business.handover_success_pct", round(random.uniform(98.2, 99.8), 3), "%")
    emit("business.ran_latency_p95_ms", round(random.uniform(18.0, 38.0), 1), "ms")
    emit("business.voice_mos", round(random.uniform(3.9, 4.4), 2), "MOS")
    emit("business.data_session_success_pct", round(random.uniform(97.5, 99.6), 3), "%")
    emit("business.volte_call_setup_success_pct", round(random.uniform(98.1, 99.7), 3), "%")
    emit("business.throughput_p50_mbps", round(random.uniform(85.0, 220.0), 1), "Mbps")

    # Retention & support
    emit("business.voluntary_churn_rate_pct", round(random.uniform(0.8, 2.4), 3), "%")
    emit("business.nps", float(random.randint(32, 58)), "NPS")
    emit("business.support_tickets_per_min", float(random.randint(28, 180)), "tickets/min")
    emit("business.avg_ticket_resolution_min", round(random.uniform(8.0, 42.0), 1), "min")
    emit("business.first_call_resolution_pct", round(random.uniform(62.0, 84.0), 2), "%")
    emit("business.trouble_to_billing_ratio_pct", round(random.uniform(1.2, 4.8), 3), "%")
```

- [ ] **Step 3: Verify the import works and the symbol is callable**

Run:
```bash
.venv/bin/python -c "
from scenarios.telecom.executive_kpis import emit_executive_business_metrics_if_eligible
assert callable(emit_executive_business_metrics_if_eligible)
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: Confirm function is a no-op when called without context (safety check)**

Run:
```bash
.venv/bin/python -c "
from scenarios.telecom.executive_kpis import emit_executive_business_metrics_if_eligible
class FakeService:
    SERVICE_NAME = 'something-else'
emit_executive_business_metrics_if_eligible(FakeService())
print('OK no-op')
"
```
Expected: `OK no-op` (no exception, no output from emits).

- [ ] **Step 5: Commit**

```bash
git add scenarios/telecom/executive_kpis.py
git commit -m "Add telecom executive KPI emitter module"
```

### Task 3: Wire emitter into bss-billing service

**Files:**
- Modify: `scenarios/telecom/services/bss_billing.py` (top of file: new import; inside `generate_telemetry()`: new call)

- [ ] **Step 1: Verify the failing smoke state — bss-billing currently does not emit business metrics**

Run:
```bash
grep -n "emit_executive_business_metrics" scenarios/telecom/services/bss_billing.py || echo "(not wired)"
```
Expected: `(not wired)`

- [ ] **Step 2: Read the existing file structure**

Open `scenarios/telecom/services/bss_billing.py`. Confirm:
- Existing imports near top (e.g. `import time`, `from app.services.base_service import BaseService`).
- Class `BssBillingService(BaseService)` with `def generate_telemetry(self) -> None:` method around line 19.

- [ ] **Step 3: Add the import**

Just after the existing `from app.services.base_service import BaseService` line, add:

```python
from scenarios.telecom.executive_kpis import emit_executive_business_metrics_if_eligible
```

- [ ] **Step 4: Add the emit call inside `generate_telemetry`**

Inside `def generate_telemetry(self) -> None:`, at the end of the method body (after `_emit_billing_summary` logic, before the method returns), add:

```python
        emit_executive_business_metrics_if_eligible(self)
```

(The indentation must match other statements inside `generate_telemetry`.)

- [ ] **Step 5: Verify the import still loads cleanly**

Run:
```bash
.venv/bin/python -c "from scenarios.telecom.services.bss_billing import BssBillingService; print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Verify the call site is in place**

Run:
```bash
grep -n "emit_executive_business_metrics_if_eligible" scenarios/telecom/services/bss_billing.py
```
Expected: two lines — one for the `from ... import ...`, one for the call inside `generate_telemetry`.

- [ ] **Step 7: Commit**

```bash
git add scenarios/telecom/services/bss_billing.py
git commit -m "Wire executive KPI emitter into telecom bss-billing service"
```

---

## Phase B — Slides restoration (app/main.py + selector UI)

### Task 4: Mount per-scenario static directories

**Files:**
- Modify: `app/main.py` (insert after the existing `selector-static` mount block, around line 244)

- [ ] **Step 1: Verify the failing smoke state**

Run:
```bash
ls scenarios/telecom/static/slides.html && echo "(file exists, route does not)"
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/scenarios/telecom/static/slides.html" 2>/dev/null || echo "(no server)"
```
Expected: file exists, curl returns `404` (or "no server" if the app isn't running).

- [ ] **Step 2: Add the mount loop**

In `app/main.py`, immediately after the `selector-static` `app.mount(...)` block (around line 244), insert:

```python

# Mount per-scenario static dirs (for scenario-specific slides, images, etc.)
_scenarios_root = os.path.join(os.path.dirname(__file__), "..", "scenarios")
for _sid in sorted(os.listdir(_scenarios_root)):
    _sdir = os.path.join(_scenarios_root, _sid, "static")
    if os.path.isdir(_sdir):
        app.mount(
            f"/scenarios/{_sid}/static",
            StaticFiles(directory=_sdir),
            name=f"{_sid}-static",
        )
```

- [ ] **Step 3: Restart the app and verify it starts cleanly**

Run:
```bash
ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' | xargs -I {} kill {}
sleep 1
PATH="$PWD/.venv/bin:$PATH" ./start.sh
sleep 2
tail -20 /tmp/nova7.log
```
Expected: log shows `Application startup complete` and `Uvicorn running on http://0.0.0.0:8080`. No tracebacks. No `ERROR` lines.

- [ ] **Step 4: Verify the static mount serves the slides file**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/scenarios/telecom/static/slides.html"
```
Expected: `200`

- [ ] **Step 5: Verify all other scenario static dirs (if any exist) also mount without errors**

Run:
```bash
for sid in $(ls scenarios/); do
  if [ -d "scenarios/$sid/static" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080/scenarios/$sid/static/")
    echo "$sid: $code"
  fi
done
```
Expected: each scenario with a `static/` dir returns `200` or `404` (file not found is fine, server errors are not). Currently only telecom has one, so output should be `telecom: 200` (or similar).

- [ ] **Step 6: Commit**

```bash
git add app/main.py
git commit -m "Mount per-scenario static directories"
```

### Task 5: Add `/slides` and `/api/setup/has-slides` routes

**Files:**
- Modify: `app/main.py` (add two new route handlers — placement: near other GET routes; recommended just after the `chaos` route or near the end of the route definitions)

- [ ] **Step 1: Verify the failing smoke state**

Run:
```bash
curl -s -o /dev/null -w "/slides: %{http_code}\n" "http://localhost:8080/slides?deployment_id=telecom"
curl -s -o /dev/null -w "/api/setup/has-slides: %{http_code}\n" "http://localhost:8080/api/setup/has-slides?scenario_id=telecom"
```
Expected: both return `404`.

- [ ] **Step 2: Locate a good insertion point**

In `app/main.py`, find the existing `chaos` route handler (`@app.get("/chaos", response_class=HTMLResponse)` around line 431). Add the new routes immediately after that handler (before the next section).

- [ ] **Step 3: Add the two routes**

Insert this code block:

```python


@app.get("/slides", response_class=HTMLResponse)
async def slides(deployment_id: Optional[str] = None):
    """Per-scenario HTML slide deck. Looks up the deployment's scenario and
    serves scenarios/<scenario_id>/static/slides.html, or 404 if none."""
    if not deployment_id:
        return JSONResponse(status_code=400, content={"error": "deployment_id required"})
    inst = INSTANCES.get(deployment_id)
    if not inst:
        rec = store.get(deployment_id)
        if not rec:
            return JSONResponse(status_code=404, content={"error": "deployment not found"})
        scenario_id = rec["scenario_id"]
    else:
        scenario_id = inst.ctx.scenario.scenario_id
    slides_path = os.path.join(
        _base, "..", "scenarios", scenario_id, "static", "slides.html"
    )
    if not os.path.isfile(slides_path):
        return JSONResponse(status_code=404, content={"error": f"no slides for scenario '{scenario_id}'"})
    with open(slides_path) as f:
        return HTMLResponse(content=f.read())


@app.get("/api/setup/has-slides")
async def has_slides(scenario_id: str):
    """Return whether the given scenario has a slide deck."""
    slides_path = os.path.join(
        _base, "..", "scenarios", scenario_id, "static", "slides.html"
    )
    return {"has_slides": os.path.isfile(slides_path)}
```

> Note: `INSTANCES`, `store`, `_base`, `Optional`, `JSONResponse`, `HTMLResponse`, and `os` are all already imported / defined at the top of `app/main.py`. If `Optional` is not imported, add `from typing import Optional` at the top.

- [ ] **Step 4: Restart the app and verify clean startup**

Run:
```bash
ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' | xargs -I {} kill {}
sleep 1
PATH="$PWD/.venv/bin:$PATH" ./start.sh
sleep 2
tail -10 /tmp/nova7.log
```
Expected: `Application startup complete`, no tracebacks.

- [ ] **Step 5: Verify `/api/setup/has-slides` returns correct truthiness**

Run:
```bash
curl -s "http://localhost:8080/api/setup/has-slides?scenario_id=telecom"
echo
curl -s "http://localhost:8080/api/setup/has-slides?scenario_id=banking"
echo
```
Expected:
- telecom: `{"has_slides":true}`
- banking: `{"has_slides":false}`

- [ ] **Step 6: Verify `/slides` returns the deck when given a valid deployment_id**

If a telecom deployment is active (`./apex.sh demo`-style or just a previous deploy), run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/slides?deployment_id=telecom"
```
Expected: `200` if telecom is deployed, `404` with `"deployment not found"` otherwise. The 200 response body must be HTML.

If no deployment is active, instead verify the route handler is wired by hitting it without an id:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/slides"
```
Expected: `400`

- [ ] **Step 7: Commit**

```bash
git add app/main.py
git commit -m "Add /slides and /api/setup/has-slides routes for per-scenario decks"
```

### Task 6: Add the Slides button to the selector UI

**Files:**
- Modify: `app/selector/static/index.html` (around line 642, in the `dep` branch of the action-row template)

- [ ] **Step 1: Verify the failing smoke state**

Run:
```bash
grep -n "Slides" app/selector/static/index.html || echo "(no Slides button)"
```
Expected: `(no Slides button)`

- [ ] **Step 2: Read the current action-row template**

The relevant block is around line 640-646:
```javascript
            } else if (dep) {
                actions = `
                    <a class="card-btn card-btn-exec" href="${dep.kibana_display_url}/app/dashboards#/view/${dep.namespace}-business-exec-dashboard" target="_blank" rel="noopener">Business Dashboard</a>
                    <a class="card-btn card-btn-ops" href="${dep.kibana_display_url}/app/dashboards#/view/${dep.namespace}-exec-dashboard" target="_blank" rel="noopener">Operations Dashboard</a>
                    <a class="card-btn card-btn-chaos" href="/chaos?deployment_id=${dep.deployment_id}">Chaos</a>
                    <button class="card-btn card-btn-teardown" onclick="stopAndTeardown('${dep.deployment_id}')">Stop &amp; Teardown</button>
                `;
            } else {
```

We'll inject a conditional Slides link that only renders when `s.has_slides` is truthy. We will populate `s.has_slides` on the scenario object when rendering.

- [ ] **Step 3: Modify the template to insert the conditional Slides link**

Replace the `} else if (dep) {` block with:

```javascript
            } else if (dep) {
                const slidesBtn = s.has_slides
                    ? `<a class="card-btn card-btn-slides" href="/slides?deployment_id=${dep.deployment_id}" target="_blank" rel="noopener">Slides</a>`
                    : '';
                actions = `
                    ${slidesBtn}
                    <a class="card-btn card-btn-exec" href="${dep.kibana_display_url}/app/dashboards#/view/${dep.namespace}-business-exec-dashboard" target="_blank" rel="noopener">Business Dashboard</a>
                    <a class="card-btn card-btn-ops" href="${dep.kibana_display_url}/app/dashboards#/view/${dep.namespace}-exec-dashboard" target="_blank" rel="noopener">Operations Dashboard</a>
                    <a class="card-btn card-btn-chaos" href="/chaos?deployment_id=${dep.deployment_id}">Chaos</a>
                    <button class="card-btn card-btn-teardown" onclick="stopAndTeardown('${dep.deployment_id}')">Stop &amp; Teardown</button>
                `;
            } else {
```

- [ ] **Step 4: Populate `s.has_slides` when scenarios are loaded**

Find the JS function that loads scenarios (search the file for `'/api/scenarios'`). It typically looks like:
```javascript
const resp = await fetch('/api/scenarios');
scenarios = await resp.json();
```

Augment that block to fetch `has_slides` per scenario:

```javascript
const resp = await fetch('/api/scenarios');
scenarios = await resp.json();
await Promise.all(scenarios.map(async (s) => {
    try {
        const r = await fetch(`/api/setup/has-slides?scenario_id=${s.id}`);
        const d = await r.json();
        s.has_slides = !!d.has_slides;
    } catch (e) {
        s.has_slides = false;
    }
}));
```

Place this immediately after `scenarios = await resp.json();`.

- [ ] **Step 5: Open the selector in a browser and visually verify**

Open `http://localhost:8080/` in a browser. If telecom is currently deployed, its card should show a **Slides** button as the first action. Other scenarios' cards (when deployed) should NOT show a Slides button.

If telecom is not currently deployed, the Slides button will only appear after launching it.

- [ ] **Step 6: Verify the static HTML still parses correctly (no missing braces)**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/"
```
Expected: `200`

- [ ] **Step 7: Commit**

```bash
git add app/selector/static/index.html
git commit -m "Add conditional Slides button to scenario card actions"
```

---

## Phase C — Pre-push validation

### Task 7: Run the no-regression validation bar

**Files:** none — verification only

- [ ] **Step 1: Confirm additive-only diff**

Run:
```bash
git diff upstream/main..HEAD --stat
```
Expected: changed files are limited to `scenarios/telecom/**`, `app/main.py`, `app/selector/static/index.html`, `app/store.py`, `app/telemetry.py`, `elastic_config/**`, `docs/superpowers/**`, plus any earlier-PR files. NO unrelated changes.

Then run:
```bash
git diff upstream/main..HEAD -- app/main.py | grep "^-" | grep -v "^---"
```
Expected: very few or zero lines (only minor reformats, no removed functionality).

- [ ] **Step 2: Scenario import smoke test (all 10 still load)**

Run:
```bash
.venv/bin/python -c "
from scenarios import list_scenarios
ids = sorted([s['id'] for s in list_scenarios()])
print('Loaded:', ids)
assert len(ids) == 10, f'Expected 10, got {len(ids)}'
expected = ['banking','ecommerce','fanatics','financial','gaming','gcp','healthcare','manufacturing','space','telecom']
assert ids == expected, f'mismatch: {ids}'
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: App startup smoke test (no ERROR in log)**

Run:
```bash
ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' | xargs -I {} kill {}
sleep 1
PATH="$PWD/.venv/bin:$PATH" ./start.sh
sleep 2
grep -E "ERROR|Traceback" /tmp/nova7.log || echo "(no errors)"
grep "Application startup complete" /tmp/nova7.log
```
Expected: `(no errors)` and `Application startup complete`.

- [ ] **Step 4: Scenario list API still returns 10 entries**

Run:
```bash
curl -s "http://localhost:8080/api/scenarios" | .venv/bin/python -c "
import json,sys
d = json.load(sys.stdin)
print(len(d), 'scenarios')
assert len(d) == 10
for s in d:
    assert 'id' in s and 'name' in s, s
print('OK')
"
```
Expected: `10 scenarios`, `OK`.

- [ ] **Step 5: `has-slides` API differentiates correctly**

Run:
```bash
echo "telecom: $(curl -s 'http://localhost:8080/api/setup/has-slides?scenario_id=telecom')"
echo "banking: $(curl -s 'http://localhost:8080/api/setup/has-slides?scenario_id=banking')"
echo "ecommerce: $(curl -s 'http://localhost:8080/api/setup/has-slides?scenario_id=ecommerce')"
```
Expected:
- telecom: `{"has_slides":true}`
- banking: `{"has_slides":false}`
- ecommerce: `{"has_slides":false}`

If any validation step fails, **stop and investigate before proceeding**. Do not push.

### Task 8: End-to-end deploy + dashboard verification

**Files:** none — manual verification

- [ ] **Step 1: Tear down existing telecom deployment (if any)**

In the selector UI, click "Stop & Teardown" on the telecom card. Wait for it to complete.

- [ ] **Step 2: Redeploy telecom**

In the selector UI, paste the live Elastic Kibana URL + API key, select Meridian Telecom, click Launch. Watch deploy progress in the UI and in `/tmp/nova7.log`. Expected: deploy completes with no failed steps.

- [ ] **Step 3: Verify Business Dashboard link works**

On the telecom card, click "Business Dashboard". Expected: opens a Kibana dashboard titled "Meridian Telecom 5G Platform" (or similar) with all 24 KPI tiles. Tiles may show "No data" for the first ~60 seconds while metrics flow; refresh after a minute.

- [ ] **Step 4: Verify KPI tiles populate**

After ~60 seconds, refresh the dashboard. Expected: at least 20 of 24 tiles show numeric values, trend charts begin populating.

- [ ] **Step 5: Verify Slides button works**

On the telecom card, click "Slides". Expected: opens the telecom slide deck in a new tab. The deck should render with no broken images or missing CSS.

- [ ] **Step 6: Verify a different scenario still works (banking)**

Launch banking against the same Elastic project. Expected: banking deploys successfully. Banking's Business Dashboard still works (since we didn't touch the banking code path). Banking's card has no Slides button.

- [ ] **Step 7: Push the branch and update the PR**

Run:
```bash
git push origin add-telecom-scenario
```
Expected: push succeeds. The existing PR (notoriousbdg/elastic-launch-demo#19) automatically updates.

- [ ] **Step 8: Comment on the PR with the validation summary**

Add a PR comment summarizing:
- New telecom executive dashboard with 4 sections × 6 KPIs + 6 trend charts
- Slides feature restored for scenarios with `static/slides.html` (telecom only at this time)
- Verified other scenarios unchanged via import + startup + API smoke tests
- Verified end-to-end against live Elastic project: dashboards render, KPIs populate, slides render

---

## Done

All tasks complete when:
- Validation bar (Task 7) green across all 5 checks
- End-to-end verification (Task 8) confirms Business Dashboard populates and Slides renders
- PR is updated on GitHub with validation summary
