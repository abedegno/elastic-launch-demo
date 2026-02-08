# Fix Plan: Missing Data, Broken APIs, and Missing Telemetry

## Problem Summary

After investigating the actual Elastic cluster (Serverless 9.4.0), almost nothing from the original setup scripts works:

| Component | Expected | Actual |
|-----------|----------|--------|
| **APM Service Map / Traces** | Distributed traces across 9 services | **None** — 0 trace indices |
| **Infrastructure UI / Host metrics** | CPU, memory, disk, network, filesystem, processes | **None** — only generic app metrics, no `system.*` metrics |
| **K8s metrics** | Pod, container, node, deployment metrics | **None** |
| Custom Agent Builder tools | 7 tools | **0** — wrong API schema used |
| Custom Agent Builder agent | NOVA-7 agent | **0** — wrong API schema |
| Knowledge base | 5 docs | **Index doesn't exist** (404) |
| Executive dashboard | Imported via API | **Never tested** — import API works but NDJSON not validated |
| nginx/mysql log indices | Separate indices | **None** — data_stream routing not verified |
| Workflows | 3 deployed | **0** — API endpoint doesn't exist on serverless |
| Detection rules | 20 ES|QL rules | **API not available** on serverless |
| validate.sh | Pass/fail report | **Broken** — uses disabled serverless APIs |

## Root Causes

1. **Serverless API differences**: `_find`, `_get`, `_delete` on saved objects are disabled. Only `_import` and `_export` work.
2. **Agent Builder schema mismatch**: Tools need `{id, type, description, configuration}` — NOT `{name, ...}`. Valid types: `esql`, `index_search`, `workflow`, `mcp`.
3. **No trace generation at all**: The NOVA-7 app generates logs and metrics but NO traces. The APM Service Map needs distributed traces with proper parent-child spans linking services together.
4. **No host metrics**: Elastic's Infrastructure UI needs `system.cpu.*`, `system.memory.*`, `system.disk.*`, `system.filesystem.*`, `system.network.*`, `system.processes.*` — with exact scope names from the OTel hostmetricsreceiver. We generate none of these.
5. **No K8s metrics**: Elastic's Kubernetes views need `k8s.pod.*`, `k8s.container.*`, `k8s.node.*`, `k8s.deployment.*` metrics with proper kubeletstatsreceiver/k8sclusterreceiver scope names.
6. **Knowledge base indexing failed silently**: Need `?refresh=true`.
7. **Nothing was tested against the actual cluster**.

---

## Fixes (ordered by priority)

### 1. Create `log-generators/trace_generator.py` — APM Service Map traces (NEW)

The APM Service Map requires distributed traces where spans cross service boundaries. The otel-demo-gen generates these by creating trace trees with SERVER→CLIENT→SERVER span chains.

**What to generate:**
- **Entry-point HTTP spans** (kind=SERVER) for each NOVA-7 service
- **Client spans** (kind=CLIENT) for inter-service calls with `parentSpanId` linking
- **Database spans** (kind=CLIENT) with `db.system`, `db.name`, `db.statement`, `db.operation`
- **Proper attributes**: `http.request.method`, `url.path`, `http.response.status_code`, `server.address`, `net.peer.name`
- **Resource attributes**: `service.name`, `service.namespace`, `service.version`, `cloud.*`, `deployment.environment`, `data_stream.type: traces`, `data_stream.dataset: generic`, `data_stream.namespace: default`
- **Status codes**: `STATUS_CODE_OK=1`, `STATUS_CODE_ERROR=2`
- Span kinds: `INTERNAL=1`, `SERVER=2`, `CLIENT=3`

**Service topology** (matching existing NOVA-7 SERVICES):
```
[External] → mission-control → fuel-system, navigation, ground-systems
mission-control → comms-array, telemetry-relay
navigation → sensor-validator
fuel-system → sensor-validator
payload-monitor → sensor-validator
range-safety → navigation, comms-array
telemetry-relay → comms-array
```

Sends via `client.send_traces()` using `OTLPClient.build_span()` and `OTLPClient._patch_resource_data_stream()`.

### 2. Create `log-generators/host_metrics_generator.py` — Infrastructure UI (NEW)

Port the pattern from `otel-demo-gen/backend/host_metrics_generator.py`.

**Must use exact OTel Collector scraper scope names:**
```python
SCRAPERS = {
    "load": "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver/internal/scraper/loadscraper",
    "cpu": "...cpuscraper",
    "memory": "...memoryscraper",
    "disk": "...diskscraper",
    "filesystem": "...filesystemscraper",
    "network": "...networkscraper",
    "processes": "...processesscraper",
}
```

**Metrics to generate (exact names + types):**
| Metric | Unit | Type | Attributes |
|--------|------|------|------------|
| `system.cpu.logical.count` | `{cpu}` | gauge | — |
| `system.cpu.load_average.1m` | `{thread}` | gauge | — |
| `system.cpu.load_average.5m` | `{thread}` | gauge | — |
| `system.cpu.load_average.15m` | `{thread}` | gauge | — |
| `system.cpu.time` | `s` | sum (cumulative) | `cpu`, `state` (user/system/idle/iowait) |
| `system.cpu.utilization` | `1` | gauge | `cpu`, `state` (user/system/wait/nice/softirq/steal/irq/idle) |
| `system.memory.usage` | `By` | gauge | `state` (used/free/cached/buffered) |
| `system.memory.utilization` | `1` | gauge | `state` (used/free/cached/buffered/slab_reclaimable/slab_unreclaimable) |
| `system.disk.io` | `By` | sum (cumulative) | `device`, `direction` (read/write) |
| `system.disk.operations` | `{operation}` | sum (cumulative) | `device`, `direction` |
| `system.filesystem.usage` | `By` | gauge | `device`, `mountpoint`, `type`, `state` (used/free) |
| `system.filesystem.utilization` | `1` | gauge | `device`, `mountpoint`, `type` |
| `system.network.io` | `By` | sum (cumulative) | `device`, `direction` (receive/transmit) |
| `system.processes.count` | `{process}` | gauge | `status` (running/sleeping) |

**Resource attributes** (must match what Elastic expects for Infrastructure UI):
- `host.name`, `host.id`, `host.arch`, `host.type`, `host.image.id`
- `host.cpu.model.name`, `host.cpu.vendor.id`, `host.cpu.family`
- `host.ip` (array), `host.mac` (array)
- `os.type`, `os.description`
- `cloud.provider`, `cloud.platform`, `cloud.region`, `cloud.availability_zone`, `cloud.account.id`, `cloud.instance.id`

Generate 3 hosts (one per cloud: AWS, GCP, Azure) matching NOVA-7's multi-cloud architecture.

### 3. Fix `setup-agent-builder.sh` — Correct Agent Builder API calls

The existing tool JSON files have application-level schemas (ES queries, parameters) that don't match the Agent Builder API. Transform to:

**Tool format**: `{id, type, description, configuration}` — NO `name` field.
- `search_telemetry_logs` → `type: "index_search"`, `configuration: {pattern: "logs-*"}`
- `search_subsystem_health` → `type: "esql"`, `configuration: {query: "FROM logs-* | WHERE ..."}`
- `check_service_status` → `type: "esql"`, `configuration: {query: "FROM logs-* | WHERE ..."}`
- `search_known_anomalies` → `type: "index_search"`, `configuration: {pattern: "nova7-knowledge-base"}`
- `trace_anomaly_propagation` → `type: "esql"`, `configuration: {query: "FROM traces-* | WHERE ..."}`
- `launch_safety_assessment` → `type: "esql"`, `configuration: {query: "FROM logs-* | WHERE ..."}`
- `remediation_action` → `type: "esql"`, `configuration: {query: "..."}`

**Agent format**: `{name, description, system_prompt, tools: [...ids], ...}` — no `type` field.

Fix knowledge base indexing: add `?refresh=true` to PUT calls.

### 4. Fix `setup-exec-dashboard.sh` + NDJSON

The `POST /api/saved_objects/_import` endpoint works. Need to:
- Test the actual import against the cluster and fix errors
- Replace verification `GET /api/saved_objects/dashboard/...` (disabled) with `POST /api/saved_objects/_export`
- Fix NDJSON to reference correct data view IDs (may need `logs-*` data view that exists on serverless)

### 5. Enhance nginx/mysql generators with traces

Add HTTP trace spans to nginx generator and DB trace spans to mysql generator, linked to the log records via `traceId`/`spanId`.

### 6. Fix `validate.sh` — Serverless-compatible APIs

- Use `_export` instead of `_find` / `_get` for dashboard verification
- Count custom (non-readonly) tools from Agent Builder
- Add checks for trace data and host metrics
- Use proper data stream names

### 7. Fix `setup-workflows.sh`

The `/api/actions/workflows` endpoint doesn't exist on serverless. Print clear manual import instructions since the YAML configs are primarily documentation. The workflows reference internal webhook URLs that don't exist in this demo anyway.

### 8. Update `setup-all.sh` to match fixed scripts

### 9. Update `AGENTS.md` with serverless API findings

Document:
- Agent Builder tool/agent schema (serverless 9.4.0)
- Saved Objects API limitations
- Required metric names/scopes for Infrastructure UI
- Required span attributes for APM Service Map

---

## Files to Create
```
log-generators/trace_generator.py           # NEW — Distributed traces for APM Service Map
log-generators/host_metrics_generator.py    # NEW — Host metrics for Infrastructure UI
```

## Files to Fix
```
setup-agent-builder.sh                      # Fix API schema for serverless
setup-exec-dashboard.sh                     # Test + fix NDJSON import
setup-workflows.sh                          # Fix or document manual steps
setup-all.sh                                # Update orchestration
validate.sh                                 # Use serverless-compatible APIs
log-generators/nginx_log_generator.py       # Add trace spans
log-generators/mysql_log_generator.py       # Add trace spans
elastic-config/dashboards/exec-dashboard.ndjson  # Fix data view refs
AGENTS.md                                   # Document findings (NEW)
```

## Testing Plan (actually run everything)

1. Run `setup-agent-builder.sh` → verify tools via `GET /api/agent_builder/tools` (check for non-readonly)
2. Run `setup-exec-dashboard.sh` → verify via `POST /api/saved_objects/_export`
3. Run `python3 log-generators/trace_generator.py` for 30s → check for `traces-*` indices with `_cat/indices/traces*`
4. Run `python3 log-generators/host_metrics_generator.py` for 30s → check for `metrics-*` with `system.*` metric names
5. Run `python3 log-generators/nginx_log_generator.py` for 30s → check for `logs-nginx.access-*` indices
6. Run `python3 log-generators/mysql_log_generator.py` for 30s → check for `logs-mysql.slowlog-*` indices
7. Run `validate.sh` → all checks pass
8. Manual: Kibana APM → Service Map shows 9 services with connections
9. Manual: Kibana Infrastructure → Hosts view shows 3 hosts with CPU/memory charts
