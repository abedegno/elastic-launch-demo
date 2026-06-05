# Telecom Slides + Executive Dashboard — Design

**Status:** approved 2026-05-18
**Owner:** add-telecom-scenario branch
**Target PR:** notoriousbdg/elastic-launch-demo#19

## Context

When the `add-telecom-scenario` branch was rebased onto `notoriousbdg/main`, two
capabilities present on the branch did not survive the rebase against upstream's
refactored structure:

1. **Per-scenario HTML slide decks** — upstream removed the `/slides` route and
   landing page entirely ("Remove platform overview page"). The
   `scenarios/telecom/static/slides.html` deck (1,356 lines) is still in tree
   from our original commit `eb5b20d`, but no FastAPI route serves it and no UI
   button links to it.
2. **Executive ("Business") dashboard wiring for telecom** — upstream added a
   `{namespace}-business-exec-dashboard` Kibana saved object generated from four
   scenario properties (`executive_kpi_emitter_service_name`,
   `executive_kpi_sections`, `executive_trend_charts`, `executive_dashboard_intro`)
   plus a `scenarios/<id>/executive_kpis.py` emitter module. Every upstream
   scenario implements this. Telecom does not, so the "Business Dashboard"
   button on the running telecom card 404s in Kibana.

These are **complementary surfaces, not substitutes**: slides are the demo
narrative (architecture, talking points); the executive dashboard is a live
KPI view of `business.*` OTLP metrics.

This spec restores both for the telecom scenario, without touching any other
scenario.

## Non-goals

- No restoration of the global landing page (`/`) or generic slides fallback —
  upstream's selector is the new entry point.
- No backfill of slides for other scenarios — they were already missing on
  upstream before our branch existed.
- No changes to other scenarios' executive dashboards, KPI sections, or emitters.

## Section 1 — Slides restoration

### Mechanism

A new FastAPI route serves `scenarios/<id>/static/slides.html` for the
deployment's scenario. Each scenario directory that contains a `static/` folder
is mounted at startup so any in-deck assets (images, CSS) are reachable. The
selector UI renders a "Slides" button on the scenario card only when the
scenario has a slides file.

### Changes

| File | Change | Approx. lines |
|------|--------|---------------|
| `app/main.py` | At startup, iterate `scenarios/*/static/` and `app.mount(f"/scenarios/{sid}/static", StaticFiles(directory=...))` per directory that exists. | ~6 |
| `app/main.py` | New route `GET /slides?deployment_id=<id>` → look up deployment's scenario → read `scenarios/<scenario_id>/static/slides.html` → return as `HTMLResponse`. 404 if the file does not exist. | ~12 |
| `app/main.py` | New API `GET /api/setup/has-slides?scenario_id=<id>` → returns `{"has_slides": bool}` based on file existence. | ~6 |
| `app/selector/static/index.html` | In the action-row template (around L642), call `has-slides` per scenario when rendering deployment cards. If `true`, insert a `<a class="card-btn">Slides</a>` linking to `/slides?deployment_id=<id>`. | ~3 |

### Behavior contract

- For scenarios with no `static/slides.html`: button never renders, route
  responds 404.
- For scenarios with `static/slides.html`: button renders next to the
  Operations Dashboard button on the running scenario card; clicking opens the
  deck in a new tab.
- Static mounts are only registered for directories that exist — empty `static/`
  dirs are fine, but missing ones don't cause startup failures.

### What other scenarios see

Today only `scenarios/telecom/static/slides.html` exists, so only telecom gets a
Slides button. All other scenarios continue to show their existing action set
(Business / Operations / Chaos / Stop & Teardown) with no additions.

## Section 2 — Telecom executive dashboard

### Pattern

Wire telecom into upstream's existing `_build_business_executive_dashboard_ndjson`
generator. All changes are inside `scenarios/telecom/`.

### Emitter service

`bss-billing` — the canonical "business" service in a telco (billing, charging,
plan management). This matches the pattern other scenarios use (e.g. banking
uses `member-portal`, gaming uses `analytics-pipeline`).

### KPI catalog (4 sections × 6 tiles)

**Subscriber growth** — activations, MVNO, ports, eSIM
- Activations / min (`business.activations_per_min`)
- MVNO net-adds / min (`business.mvno_net_adds_per_min`)
- Port-ins / min (`business.port_ins_per_min`)
- Port-outs / min (`business.port_outs_per_min`)
- eSIM provisions / min (`business.esim_provisions_per_min`)
- Active subscribers (M) (`business.active_subscribers_m`)

**Revenue & ARPU** — total revenue, by-tier, overage, roaming
- Total revenue (USD/min) (`business.revenue_usd_per_min`)
- Consumer ARPU (USD) (`business.consumer_arpu_usd`)
- Enterprise ARPU (USD) (`business.enterprise_arpu_usd`)
- MVNO partner revenue (USD/min) (`business.mvno_partner_revenue_usd_per_min`)
- Data overage charges (USD/min) (`business.data_overage_charges_usd_per_min`)
- Roaming revenue (USD/min) (`business.roaming_revenue_usd_per_min`)

**Network & QoE** — quality-of-experience surfaces visible to leadership
- 5G handover success (%) (`business.handover_success_pct`)
- RAN latency p95 (ms) (`business.ran_latency_p95_ms`)
- Voice MOS (`business.voice_mos`)
- Data session establishment success (%) (`business.data_session_success_pct`)
- VoLTE call setup success (%) (`business.volte_call_setup_success_pct`)
- Throughput p50 (Mbps) (`business.throughput_p50_mbps`)

**Retention & support** — churn, NPS, tickets
- Voluntary churn rate (%) (`business.voluntary_churn_rate_pct`)
- NPS (`business.nps`)
- Support tickets / min (`business.support_tickets_per_min`)
- Avg ticket resolution (min) (`business.avg_ticket_resolution_min`)
- First-call resolution (%) (`business.first_call_resolution_pct`)
- Trouble-to-billing ratio (%) (`business.trouble_to_billing_ratio_pct`)

### Trend charts (6)

- Total revenue (USD/min)
- Activations / min
- Active subscribers (M)
- Voluntary churn rate (%)
- RAN p95 latency (ms)
- NPS

### Files

| File | Change | Approx. lines |
|------|--------|---------------|
| `scenarios/telecom/scenario.py` | Add four properties: `executive_kpi_emitter_service_name`, `executive_kpi_sections`, `executive_trend_charts`, `executive_dashboard_intro`. | ~80 |
| `scenarios/telecom/executive_kpis.py` (new) | Define `emit_executive_business_metrics_if_eligible(service)` emitting 24 `business.*` OTLP gauges with realistic 5G ranges. Mirrors gaming/ecommerce/banking shape (~53 lines each). | ~55 |
| `scenarios/telecom/services/bss_billing.py` | Import `emit_executive_business_metrics_if_eligible` and call it once per main-loop cycle. | ~3 |

### What other scenarios see

Zero changes. The emitter gate (`if want != service.SERVICE_NAME: return`) means
adding the import to telecom's `bss-billing` only fires when the telecom
scenario is active. Other scenarios' exec dashboards, emitters, and metric
streams are untouched.

## Section 3 — No-regression validation

### Pre-push checks (bar: all must pass)

1. **Additive-only diff check** — `git diff upstream/main..HEAD` must show only
   `scenarios/telecom/**` and additive hunks in `app/main.py` and
   `app/selector/static/index.html`. No edits to existing handlers, no removed
   lines outside whitespace.

2. **Scenario import smoke test** —
   ```
   .venv/bin/python -c "from scenarios import list_scenarios; \
       ids=[s['id'] for s in list_scenarios()]; print(ids); assert len(ids)==10"
   ```
   Bar: 10 scenarios load.

3. **App startup smoke test** — `./start.sh`, then check `/tmp/nova7.log` for
   tracebacks. Bar: no `ERROR`, scenario registry populates 10 entries,
   `Application startup complete` appears.

4. **Scenario list API** — `curl /api/scenarios` returns 10 entries with
   complete required fields.

5. **`has-slides` API** — telecom returns `true`; one other scenario (banking)
   returns `false`.

### Pre-push (informational, do not block)

6. **Telecom end-to-end** — redeploy telecom against live Elastic, watch deploy
   log for failures, then verify Business Dashboard populates within 1 min and
   Slides deck renders.

7. **One other scenario sanity** — launch banking (lightest deploy), verify its
   Business Dashboard still works unchanged.

Failures on 1–5 = revert before push. Failures on 6–7 = note in the PR for the
maintainer and proceed.

## Open questions

None.

## Out of scope (follow-up candidates)

- Slide deck content updates for the new exec dashboard surface.
- Other-scenario slide decks (if anyone wants to restore the broader pattern
  upstream removed).
- Generic landing-page fallback for `/slides` with no `deployment_id`.
