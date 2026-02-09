# NOVA-7 Elastic Launch Demo — Learnings & API Reference

## Kibana Agent Builder API (Serverless 9.4.0)

### Tool Schema
```
POST /api/agent_builder/tools
{
  "id": "<tool-id>",
  "type": "index_search" | "esql" | "workflow",
  "description": "...",
  "configuration": {
    // for index_search:
    "pattern": "logs-*"           // NOT "index" — must be "pattern"
    // for esql:
    "query": "FROM logs-* | ...",
    "params": {}                  // REQUIRED even if empty
  }
}
```

**Tool types:**
- `index_search` — searches an Elasticsearch index; requires `configuration.pattern`
- `esql` — runs an ES|QL query; requires `configuration.query` and `configuration.params`
- `workflow` — invokes a Kibana workflow; requires `configuration.workflow_id`

**Gotchas:**
- `index_search` requires `configuration.pattern`, NOT `configuration.index` — returns 400 otherwise
- `esql` requires `configuration.params: {}` even when empty — returns 400 otherwise
- `workflow` requires `configuration.workflow_id` — discover via `POST /api/workflows/search`
- No `name` field on tools — use `id` and `description` only

### Updating Existing Tools (PUT)
POST fails if the tool already exists. Use PUT to update:
```
PUT /api/agent_builder/tools/{tool_id}
{
  "description": "...",
  "configuration": { ... }
}
```
**CRITICAL**: PUT body must NOT include `id` or `type` — returns 400 if present.
Only `description` and `configuration` are accepted.

### ES|QL Syntax for Agent Tools
- `COUNT_IF()` does NOT exist — use `COUNT(*) WHERE condition`
- Example: `STATS errors = COUNT(*) WHERE severity_text == "ERROR", total = COUNT(*) BY field`
- Always test via `POST /_query` before deploying to tool configuration

### Agent Schema
```
POST /api/agent_builder/agents
{
  "id": "<agent-id>",
  "name": "...",
  "description": "...",
  "configuration": {
    "instructions": "...",           // System prompt goes here — NOT top-level "system_prompt"
    "tools": [
      { "tool_ids": ["tool1", "tool2", ...] }
    ]
  }
}
```

**Gotchas:**
- `id` is REQUIRED — returns 400 if missing
- System prompt is `configuration.instructions`, NOT `system_prompt` at top level
- Tools must be `configuration.tools: [{tool_ids: [...]}]` (array of objects with tool_ids array)
- If agent already exists, POST returns error; use PUT with agent ID to update

### Validation
```
GET /api/agent_builder/agents    — List all agents
GET /api/agent_builder/tools     — List all tools (includes readonly defaults; filter by readonly=false)
```

---

## Kibana Saved Objects API (Serverless 9.4.0)

### Available Endpoints
| Endpoint | Status |
|----------|--------|
| `POST /api/saved_objects/_import` | Works |
| `POST /api/saved_objects/_export` | Works |
| `GET /api/saved_objects/_find` | **DISABLED** on serverless |
| `GET /api/saved_objects/<type>/<id>` | **DISABLED** on serverless |
| `DELETE /api/saved_objects/<type>/<id>` | **DISABLED** on serverless |

### Dashboard Import with Lens Panels — CRITICAL FIX

**Problem:** Importing dashboards with by-value Lens panels (embeddableConfig.attributes) causes HTTP 500 on Kibana serverless 9.4.0.

**Root Cause:** Without migration version fields, Kibana cannot determine which migrations to run on the embedded Lens state and crashes instead of gracefully handling it.

**Fix:** Add these two fields to the dashboard saved object:
```json
{
  "attributes": { ... },
  "id": "my-dashboard",
  "type": "dashboard",
  "coreMigrationVersion": "8.8.0",
  "typeMigrationVersion": "10.3.0",
  "references": [],
  "managed": false
}
```

**Key facts:**
- `coreMigrationVersion: "8.8.0"` — required for all saved objects on serverless
- `typeMigrationVersion: "10.3.0"` — required for dashboard type specifically
- Without these, ANY `embeddableConfig.attributes` (even `{title: "X"}`) causes 500
- Bare Lens panels (no embeddableConfig.attributes) import fine without migration versions
- Empty dashboards (no panels) import fine without migration versions
- `compatibilityMode=true` does NOT fix the issue — still 500

### Lens Panel Reference Format

For by-value Lens panels inside panelsJSON, use this reference name format:
```
"indexpattern-datasource-layer-<layerId>"
```

For exported dashboards with by-reference panels, Kibana uses:
```
"<panelIndex>:<panelRefName>"   (e.g., "p1:panel_p1")
```

### Verification (Serverless-Compatible)

Use `_export` instead of `_find` or `_get`:
```bash
POST /api/saved_objects/_export
{"objects": [{"type": "dashboard", "id": "my-dashboard-id"}], "includeReferencesDeep": false}
```

---

## Elasticsearch API Notes

### Bulk Indexing
```
POST /_bulk?refresh=true
{"index":{"_index":"my-index","_id":"doc-id"}}
{"field":"value"}
```
- Use `?refresh=true` to make docs immediately searchable
- Content-Type must be `application/x-ndjson`

### Index Creation
- On serverless, creating an index that already exists returns an error (not idempotent)
- Wrap in error handling: `|| log_warn "may already exist"`

---

## OTLP Telemetry Patterns

### Data Stream Routing
Resource attributes control data stream routing:
```python
"data_stream.type": "logs"      # → logs-*
"data_stream.dataset": "generic" # → *-generic.*
"data_stream.namespace": "default" # → *-*.default
```

**CRITICAL — Host Metrics & Infrastructure UI:**
Do NOT set `data_stream.*` attributes on host metrics. The Elastic OTLP endpoint
auto-routes based on the scope name (hostmetricsreceiver scraper names):
- With `data_stream.dataset="generic"` → `metrics-generic.otel-default` (Infrastructure UI ignores this)
- Without `data_stream.*` → `metrics-hostmetricsreceiver.otel-default` (Infrastructure UI finds this)

The Elastic OTLP endpoint recognizes the scraper scope names and routes accordingly.
This is the same behavior as the real OTel Collector — it doesn't set `data_stream.*` either.

### Trace Span Kinds
```python
SPAN_KIND_INTERNAL = 1
SPAN_KIND_SERVER = 2
SPAN_KIND_CLIENT = 3
```

### Trace Status Codes
```python
STATUS_CODE_OK = 1
STATUS_CODE_ERROR = 2
```

### Host Metrics — Infrastructure UI
Must use exact OTel Collector scraper scope names for Elastic Infrastructure UI recognition:
```
github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver/internal/scraper/<name>scraper
```
Where `<name>` is: load, cpu, memory, disk, filesystem, network, processes

Required resource attributes (from Elastic System OTel Assets guide):
- `host.name`, `host.id`, `host.arch`, `host.ip`, `host.mac`
- `host.cpu.vendor.id`, `host.cpu.family`, `host.cpu.model.id`, `host.cpu.model.name`, `host.cpu.stepping`, `host.cpu.cache.l2.size`
- `os.description`, `os.type`

Required metrics (must be enabled explicitly on upstream Collector):
- `system.cpu.utilization`, `system.cpu.logical.count`, `system.memory.utilization`
- All others enabled by default: `system.cpu.time`, `system.cpu.load_average.*`, `system.memory.usage`, `system.disk.io`, `system.network.io`, etc.

---

## Kibana Workflows API (Pre-GA, 9.4.0)

### Endpoints
```
POST /api/workflows              — Create (body: {"yaml": "..."})
PUT  /api/workflows/{id}         — Update (body: {"yaml": "..."})
POST /api/workflows/search       — List/search (body: {"page":1,"size":100})
GET  /api/workflows/{id}         — Get by ID
DELETE /api/workflows/{id}       — Delete
POST /api/workflows/{id}/run     — Run (body: {"inputs": {...}})
GET  /api/workflowExecutions/{id} — Execution status
```

### CRITICAL: Required Header
All workflow endpoints require `x-elastic-internal-origin: kibana` header.
Without it, returns 400: "exists but is not available with the current configuration".
This header is needed for pre-GA internal Kibana APIs.

### Workflow YAML Schema (workflow-schema-strict-with-dynamic-connectors.json)

**Required top-level fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable workflow name |
| `steps` | Yes | Array of step objects (at least 1) |
| `version` | No | String, e.g. `"1"` |
| `description` | No | Purpose/explanation |
| `triggers` | No | Array of trigger objects (defaults to manual) |
| `inputs` | No | Array of `{name, type, required, default, description}` |
| `consts` | No | Constants referenced via `{{ consts.key }}` |
| `tags` | No | Array of strings for categorization |
| `outputs` | No | Workflow output definitions |
| `settings` | No | Timeout, retries, log level |
| `enabled` | No | Boolean |

**NOT valid top-level:** `trigger` (singular), `input` (singular), `metadata`.

### Trigger Types
```yaml
triggers:
  - type: manual          # Default if triggers omitted
  - type: scheduled       # Cron/interval
    with:
      every: "5m"         # Simple interval (30s, 5m, 2h, 1d)
  - type: alert           # Fired by alert rules
```

### Input Format
```yaml
inputs:
  - name: my_param
    type: string           # string, number, boolean, array, object
    required: true
    default: "fallback"
    description: "What this does"
```

### Valid Step Types
| Type | Description | Key `with` fields |
|------|-------------|-------------------|
| `console` | Log a message | `message` |
| `http` | HTTP request | `url`, `method`, `headers`, `body`, `timeout` |
| `elasticsearch.search` | ES search | `index`, `size`, `query`, `aggs` |
| `elasticsearch.index` | Index a doc | `index`, `document`, `id`, `refresh` |
| `elasticsearch.request` | Generic ES | `method`, `path`, `headers`, `body` |
| `elasticsearch.indices.exists` | Check index | `index` |
| `elasticsearch.indices.create` | Create index | `index`, `mappings` |
| `if` | Conditional | `condition`, `steps`, `else` |
| `foreach` | Loop | `foreach` (expr), `steps` |
| `data.set` | Set variables | `var` (array of key-value pairs) |
| `wait` | Delay | `duration` (e.g. "30s") |
| `ai.agent` | AI agent call | `message` + `agent-id` (step-level) |
| `ai.prompt` | AI prompt | `prompt`, `schema` + `connector-id` |
| `slack` | Slack message | `message` + `connector-id` |
| `jira` | Jira ticket | `projectKey`, `summary` + `connector-id` |
| `kibana.request` | Kibana API | `method`, `path`, `body` |

**CRITICAL: `ai.agent` agent-id placement.** The `agent-id` for `ai.agent` steps MUST be
at the **step level** (like `connector-id`), NOT inside `with`. If placed inside `with`,
the workflow engine silently strips it and the agent step may fail or use a wrong default agent.
```yaml
# CORRECT — agent-id at step level
- name: invoke_agent
  type: ai.agent
  agent-id: nova7-launch-anomaly-analyst
  with:
    message: "Perform root cause analysis..."

# WRONG — agent_id inside with (silently stripped!)
- name: invoke_agent
  type: ai.agent
  with:
    agent_id: nova7-launch-anomaly-analyst   # ← STRIPPED BY ENGINE
    message: "..."
```

**NOT valid step types:** `condition`, `branch`, `elasticsearch_query`, `webhook`,
`index` (use `elasticsearch.index`), `script`, `connector`, `agent` (use `ai.agent`),
`parallel`, `wait_then_query`.

### Step Structure
```yaml
- name: step_name          # REQUIRED — unique identifier (NOT "id")
  type: step_type          # REQUIRED
  with:                    # Parameters (NOT "params")
    key: value
  connector-id: "..."      # For connector steps (slack, jira, ai.prompt)
  agent-id: "..."          # For ai.agent steps — MUST be at step level
  condition: "expr"        # Conditional execution
  on-failure:              # Error handling
    retry:
      max-attempts: 3
      delay: "5s"
    continue: true
  timeout: "30s"
```

### CRITICAL: `elasticsearch.search` — `sort` is NOT allowed
The `sort` field is **not in the workflow schema** for `elasticsearch.search`.
Including `sort` causes `valid: false` with no useful error message — the name
shows as "Untitled workflow" and `definition: null`. Remove `sort` from all
`elasticsearch.search` steps.

**Allowed `with` fields for `elasticsearch.search`:** `index`, `size`, `query`, `aggs`.

### Template Variables
| Context | Syntax | Example |
|---------|--------|---------|
| Inputs | `{{ inputs.name }}` | `{{ inputs.channel }}` |
| Step output | `{{ steps.name.output.path }}` | `{{ steps.search.output.hits.total.value }}` |
| Constants | `{{ consts.key }}` | `{{ consts.api_key }}` |
| Loop item | `{{ foreach.item.field }}` | `{{ foreach.item._source.name }}` |
| Workflow | `{{ workflow.name }}` | Workflow metadata |
| Execution | `{{ execution.id }}` | Execution metadata |

**Expression types:**
- `{{ }}` — inserts as string
- `${{ }}` — preserves data types (arrays, objects)
- Liquid filters supported: `json`, `json_parse`, `base64_encode`, `upcase`, `downcase`, `replace`, `map`, `where`, `sort`, `join`, `filter`

### Debugging Invalid Workflows
When `valid: false`:
1. Name shows as "Untitled workflow" = YAML parsing/schema failure (not just a step error)
2. `definition: null` = schema didn't match at all
3. No error details in API response — must bisect by removing steps
4. Strategy: start with minimal workflow (1 step), add steps back one at a time
5. Common causes: `sort` in es.search, wrong step type names, `params` instead of `with`, `id` instead of `name` on steps

### Example: Minimal Valid Workflow
```yaml
version: "1"
name: My Workflow
triggers:
  - type: manual
inputs:
  - name: query
    type: string
    default: "test"
steps:
  - name: search
    type: elasticsearch.search
    with:
      index: "logs-*"
      size: 10
      query:
        bool:
          filter:
            - range:
                "@timestamp":
                  gte: "now-5m"
  - name: log_result
    type: console
    with:
      message: "Found {{ steps.search.output.hits.total.value }} results"
```

---

## Kibana Streams Significant Events API (Technical Preview, 9.2.0+)

### Endpoints
```
POST /api/streams/_enable                      — Enable Streams (idempotent)
GET  /api/streams                              — List available streams
POST /api/streams/{name}/queries/_bulk         — Bulk create/update/delete queries
GET  /api/streams/{name}/queries               — List queries on a stream
DELETE /api/streams/{name}/queries/{id}         — Delete a single query
```

### CRITICAL: Required Headers
All Streams endpoints require both:
- `kbn-xsrf: true`
- `x-elastic-internal-origin: kibana`

### Query Schema — `kql` is MANDATORY
```json
{
  "operations": [
    {
      "index": {
        "id": "my-query-id",
        "title": "Human-readable title",
        "kql": {
          "query": "attributes.error.type: \"SomeException\" AND attributes.sensor.type: \"thermal\""
        }
      }
    }
  ]
}
```

**Gotchas:**
- The `kql` field (object with `query` string) is **REQUIRED** — without it, returns 400 ZodError
- The `filter` DSL (`and`/`or`/`eq` combinators) from the API docs does **NOT** work as the required field
- `evidence` and `feature` fields are optional metadata (they get stored but are not the detection mechanism)
- Delete operations in bulk: `{"delete": {"id": "query-id"}}`
- IDs should be prefixed for easy cleanup (e.g., `nova7-se-ch01`)

### KQL Query Format
KQL inside the `kql.query` field uses standard Kibana Query Language:
```
attributes.error.type: "ThermalCalibrationException" AND attributes.sensor.type: "thermal" AND attributes.vehicle_section: "engine_bay"
```

**Field mapping note:** OTLP log record attributes (set as `"error.type"` in code) become
`attributes.error.type` in the Elasticsearch index after OTLP ingestion.

### Stream Name Discovery
- `GET /api/streams` returns available streams
- For OTLP logs, the stream name is `logs`
- Stream must contain data for queries to match

### Verification
```bash
GET /api/streams/{name}/queries
# Response: {"queries": [{id, title, kql: {query: "..."}, ...}, ...]}
```
Count queries with your prefix to verify deployment.

---

## Kibana Lens Panel Format (9.4.0) — By-Value formBased

When creating Lens by-value panels (embedded in panelsJSON), the format must exactly match what Kibana 9.4 expects. Export a working built-in [OTel] dashboard panel to see the reference format.

### Layer Structure (inside `datasourceStates.formBased.layers`)
```json
{
  "<layer-uuid>": {
    "columnOrder": ["<col-uuid-1>", "<col-uuid-2>"],
    "columns": { ... },
    "ignoreGlobalFilters": false,
    "incompleteColumns": {},
    "sampling": 1
  }
}
```
**All three extra fields** (`ignoreGlobalFilters`, `incompleteColumns`, `sampling`) are **required** — without them, Kibana throws `Cannot read properties of undefined (reading 'columnOrder')`.

### State Structure
```json
{
  "adHocDataViews": {},
  "datasourceStates": { "formBased": { "layers": { ... } } },
  "filters": [],
  "internalReferences": [],
  "query": { "language": "kuery", "query": "" },
  "visualization": { ... }
}
```

### Panel Wrapper
```json
{
  "embeddableConfig": {
    "attributes": {
      "description": null,
      "references": [...],
      "savedObjectId": null,
      "state": { ... },
      "title": "",
      "type": "lens",
      "visualizationType": "lnsXY"
    },
    "enhancements": {},
    "syncColors": false,
    "syncCursor": true,
    "syncTooltips": false
  },
  "gridData": { "h": 12, "i": "p1", "w": 24, "x": 0, "y": 0 },
  "panelIndex": "p1",
  "title": "Panel Title",
  "type": "lens"
}
```

### Count Column `sourceField`
Use `"sourceField": "___records___"` (NOT `"Records"`) for count operations.

### lnsXY Visualization — Required Fields
All lnsXY panels MUST include `legend` and `valueLabels`:
```json
{
  "legend": {"isVisible": true, "position": "right"},
  "valueLabels": "hide",
  "preferredSeriesType": "area_stacked",
  "layers": [...]
}
```
Without `legend.isVisible`, Kibana throws `Cannot read properties of undefined (reading 'isVisible')` and the panel silently shows no data.

### lnsDatatable Visualization — Required Fields
Datatable columns need `isTransposed` and `isMetric`, plus `paging` and `sorting`:
```json
{
  "columns": [
    {"columnId": "...", "isTransposed": false, "isMetric": false},
    {"columnId": "...", "isTransposed": false, "isMetric": true}
  ],
  "layerId": "...",
  "layerType": "data",
  "paging": {"enabled": true, "size": 10},
  "sorting": null
}
```

### lnsHeatmap Visualization — Include Legend
Heatmap panels should include `"legend": {"isVisible": true, "position": "right"}`.

### terms Column — Include Bucket Params
Terms columns should include `missingBucket` and `otherBucket` params:
```json
"params": {
  "size": 10,
  "orderDirection": "desc",
  "orderBy": {"columnId": "...", "type": "column"},
  "missingBucket": false,
  "otherBucket": false
}
```

### Panel Attributes — Avoid null Fields
The working OTel panels do NOT include `"description": null` or `"savedObjectId": null`. Omit these entirely rather than setting to null.

### Generator Script
Use `elastic-config/dashboards/generate_exec_dashboard.py` to regenerate the NDJSON — it produces correct Kibana 9.4 format with random UUIDs for layer/column IDs.

---

## OTLP Field Mapping Reference

When OTLP data is ingested by Elastic, field paths differ from what you set in code:

| Set in OTLP Code | Actual ES Field Path | Notes |
|-------------------|---------------------|-------|
| Log attribute `error.type` | `attributes.error.type` | Log attributes → `attributes.*` |
| Log attribute `system.subsystem` | `attributes.system.subsystem` | |
| Log attribute `chaos.channel` | `attributes.chaos.channel` | |
| Resource attr `service.name` | `resource.attributes.service.name` | Resource attrs → `resource.attributes.*` |
| Resource attr `cloud.provider` | `resource.attributes.cloud.provider` | |
| Severity | `severity_text` | NOT `severityText` or `log.level` |
| Log body | `body` | NOT `message` |
| Data stream dataset | `data_stream.dataset` includes `.otel` | e.g., `nginx.access.otel` not `nginx.access` |

### CRITICAL: Passthrough Mapping on `logs` Stream

The `attributes` field on the `logs` data stream uses **passthrough** mapping type.
This means individual attribute keys (e.g., `attributes.error.type`, `attributes.chaos.channel`)
are stored in `_source` but are **NOT indexed** — they cannot be searched, filtered, or
aggregated with term/match/range queries or ES|QL WHERE clauses.

**Indexed (queryable) fields on `logs`:**
| Field | Type | Values |
|-------|------|--------|
| `body.text` | text | Log message body — error type names appear here |
| `severity_text` | keyword | `INFO`, `WARN`, `ERROR` |
| `log.level` | keyword | Same as `severity_text` |
| `service.name` | keyword | 9 services (e.g., `fuel-system`, `navigation`) |
| `resource.attributes.service.name` | keyword | Same as `service.name` |
| `@timestamp` | date | Event timestamp |

**NOT indexed (source-only) fields:** `attributes.*`, `resource.attributes.cloud.*`,
`resource.attributes.host.*` (except `host.name`).

**Consequence:** All queries (KQL, ES query DSL, ES|QL) that need to filter by error type
must use `body.text` instead of `attributes.error.type`. Examples:
- **KQL:** `body.text: "FuelPressureException" AND severity_text: "ERROR"`
- **ES query DSL:** `{"match_phrase": {"body.text": "FuelPressureException"}}`
- **ES|QL:** `WHERE body.text LIKE "*FuelPressureException*" AND severity_text == "ERROR"`

This affects: significant event queries, alert rules, workflow ES search steps, and agent tools.

### Required Host Metric Resource Attributes
These must be set for OTel dashboards to fully work:
```
host.name, host.id, host.arch, host.type, host.image.id
host.cpu.model.name, host.cpu.vendor.id, host.cpu.family
host.cpu.model.id, host.cpu.stepping, host.cpu.cache.l2.size
host.ip (array), host.mac (array)
os.type, os.description
cloud.provider, cloud.platform, cloud.region, cloud.availability_zone
```

### Required Host Metrics (for OTel dashboard panels)
Beyond the defaults (`system.cpu.time`, `system.memory.usage`, `system.disk.io`, `system.network.io`), these are needed:
- `system.disk.io_time` — disk IO time cumulative counter (per device + direction)
- `system.network.packets` — packet counts (per device + direction)
- `system.network.dropped` — dropped packet counts
- `system.network.errors` — error counts
- `system.processes.created` — cumulative process creation count

---

## Kibana Data Views

The OTel dashboards expect these data views to exist:
- `logs-*` — for log dashboards and Exec Dashboard
- `metrics-*` — for host/system metrics dashboards

Create via:
```bash
POST /api/data_views/data_view
{"data_view": {"title": "metrics-*", "name": "metrics-*", "timeFieldName": "@timestamp"}}
```

---

## Kibana Alerting API

### Alert Rules
```
POST /api/alerting/rule
{
  "name": "Rule Name",
  "rule_type_id": ".es-query",
  "consumer": "alerts",
  "schedule": { "interval": "30s" },
  "params": {
    "searchType": "esQuery",
    "index": ["logs-*"],
    "esQuery": "{ \"query\": { ... } }",
    "timeField": "@timestamp",
    "timeWindowSize": 1,
    "timeWindowUnit": "m",
    "threshold": [0],
    "thresholdComparator": ">"
  },
  "actions": [{ "group": "query matched", "id": "<connector-id>", "params": {...} }],
  "tags": ["nova7"]
}
```

### Webhook Connector
```
POST /api/actions/connector
{
  "name": "Connector Name",
  "connector_type_id": ".webhook",
  "config": { "url": "...", "method": "post", "headers": {...} },
  "secrets": {}
}
```

---

## General Lessons

1. **Search docs before trial-and-error** — API schemas aren't always intuitive; check official docs and GitHub issues first
2. **Export to learn format** — When import fails, export existing objects to see what Kibana expects (migration versions, field naming)
3. **Serverless != self-managed** — Many Kibana APIs are disabled on serverless; always test against the actual cluster
4. **Migration versions matter** — Kibana saved objects need `coreMigrationVersion` and `typeMigrationVersion` for proper import, especially with complex embedded content like Lens panels
5. **Test incrementally** — When debugging 500 errors, strip down to minimal reproducer and add fields back one at a time
6. **`x-elastic-internal-origin: kibana`** — Required header for pre-GA internal Kibana APIs (Workflows, etc.). Without it, routes return "exists but not available with current configuration"
7. **Bulk indexing large payloads** — Use `--data-binary @file` instead of `-d "$VARIABLE"` to avoid shell "Argument list too long" errors
8. **OTLP field paths are NOT intuitive** — Always verify with `_field_caps` against actual ES data before writing ESQL queries, dashboards, or KQL filters
9. **Lens format is fragile** — Missing a single field like `incompleteColumns: {}` causes cryptic JS errors; always use a generator script or export a working panel as reference
10. **Kibana API from shell** — The `source .env && curl` pattern often fails to load vars when piped; use `export $(grep -E '^[A-Za-z_]' .env | xargs)` or hardcode the URL. Also prefer writing curl output to a temp file, then parsing with a separate Python script, rather than piping inline — multiline heredoc Python inside `$()` is fragile with escaping
11. **Data views must exist before dashboard import** — If a Lens panel references data view ID `logs-*`, that data view must exist in Kibana. Create it via `POST /api/data_views/data_view` before importing the dashboard. After import, users may need to refresh the browser for Kibana to pick up new data view fields
12. **`ai.agent` context window overflow** — The workflow engine passes ALL accumulated step outputs as context to `ai.agent` steps. OTLP log documents are large (passthrough attributes in `_source`). If `elasticsearch.search` steps return full docs, the combined context can exceed the model's max input length: `"Input is too long for requested model"` (error from inference entity `.rainbow-sprinkles-elastic`). **Fix:** Always use `_source` filtering and small `size` in search steps that precede `ai.agent` steps
13. **`ai.agent` agent-id placement** — The `agent-id` for `ai.agent` steps MUST be at the **step level** (like `connector-id`), NOT inside `with`. If placed inside `with` (as `agent_id` or `agentId`), the workflow engine silently strips it
14. **Workflow `data.set` variable access** — Variables set by `data.set` inside an `if` step's nested branches are NOT accessible via the parent step name. `{{ steps.parent_if_step.output.var }}` resolves to empty. Use `{{ inputs.field }}` directly or `{{ steps.nested_set_step.output.var }}` instead
15. **Workflow execution API** — `GET /api/workflowExecutions?workflowId={id}` lists executions. `GET /api/workflowExecutions/{executionId}` gets details (status, error, startedAt, finishedAt). The `history` field on the workflow object only shows completed runs
16. **OTel CPU state names** — Use `wait` not `iowait` for I/O wait CPU state. The OTel standard CPU states are: `user`, `system`, `idle`, `wait`, `nice`, `interrupt`, `softirq`, `steal`. Elastic Infrastructure UI dashboards filter by these exact names
17. **Passthrough mapping on `logs` stream** — OTLP `attributes.*` and most `resource.attributes.*` use passthrough mapping (stored in `_source` but NOT indexed). Only `body.text`, `severity_text`, `service.name`, `resource.attributes.service.name`, `host.name`, `@timestamp` are indexed. Use `body.text LIKE "*ErrorType*"` for ES|QL, `body.text: "ErrorType"` for KQL, and `match`/`match_phrase` on `body.text` for query DSL
