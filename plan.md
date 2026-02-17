# Plan: Scenario-Specific Tools, Agent, Dashboard & Generators

## Problem Summary

When switching scenarios (e.g. space → financial), the deployer currently:
1. **Reuses identical tool definitions** — `launch_safety_assessment` appears in finserve (makes no sense for trading)
2. **Ignores scenario `tool_definitions` property** — every scenario returns `[]` ("populated by setup scripts") but the deployer auto-generates hardcoded tools instead
3. **Ignores scenario `agent_config.system_prompt`** — only uses the opening sentence, then generates a generic prompt
4. **Dashboard says "NOVA-7"** — title, description, cluster names, service names all hardcoded to space scenario
5. **Log generators hardcode "nova7"** — nginx hosts, VPC names, k8s daemonset/statefulset names, mysql databases, nginx server names
6. **`deployment.environment` is always "production"** — should be `production-{scenario_id}` (e.g. `production-finserve`)

## Architecture Principle

**Scenarios should own their customizations; the deployer should be a dumb executor.**

Each scenario already has abstract properties (`tool_definitions`, `knowledge_base_docs`, `agent_config`) — we just need to:
1. Have scenarios actually populate these properties with scenario-specific content
2. Have the deployer USE what the scenario provides instead of auto-generating
3. Make generators read scenario config instead of using hardcoded values

## Changes

### 1. Scenario-Specific Tool Definitions

**Files**: `scenarios/base.py`, each `scenarios/*/scenario.py`

The `tool_definitions` property on BaseScenario currently returns `[]`. Instead, each scenario should return its 7 tool definitions with scenario-appropriate names and descriptions.

**Approach**: Add a default implementation in `BaseScenario` that auto-generates generic tools from `self.services` and `self.channel_registry` (move the current `_generate_tool_definitions` logic there). Then let individual scenarios override specific tools. Key change: rename `launch_safety_assessment` to something scenario-appropriate:

| Scenario | Tool Name | Description |
|----------|-----------|-------------|
| space | `launch_safety_assessment` | GO/NO-GO launch readiness |
| financial | `trading_risk_assessment` | Pre-market risk evaluation |
| healthcare | `patient_safety_assessment` | Clinical system safety check |
| gaming | `liveops_health_assessment` | Live service health check |
| fanatics | `platform_load_assessment` | Event-day load readiness |

**Implementation**:
- Add `BaseScenario.default_tool_definitions() -> list[dict]` method that generates the 6 generic tools (search_error_logs, search_subsystem_health, search_service_logs, search_known_anomalies, trace_anomaly_propagation, browse_recent_errors)
- Add abstract property `assessment_tool_config -> dict` to BaseScenario returning `{"id": "...", "description": "..."}` for the scenario-specific assessment tool
- `tool_definitions` default impl calls `default_tool_definitions()` + appends the assessment tool
- Deployer's `_generate_tool_definitions` → reads `self.scenario.tool_definitions` instead of generating from scratch
- Workflow tools (remediation_action, escalation_action) still added by deployer since they need workflow IDs

### 2. Scenario-Specific Agent Prompt

**Files**: `elastic_config/deployer.py`, each `scenarios/*/scenario.py`

Currently `_generate_system_prompt()` uses a template with hardcoded sections. The scenario's `agent_config["system_prompt"]` is only used as the identity opening.

**Approach**: Keep the deployer's prompt generation but have it compose the full prompt from:
- `agent_config["system_prompt"]` → identity + domain expertise (scenario provides full text)
- Auto-generated sections from scenario properties (services list, subsystems, field names) → these are correct to auto-generate since they're structural
- `agent_config.get("assessment_tool_name")` → used in the Tool Selection Guide section instead of hardcoded `launch_safety_assessment`

This means the "Tool Selection Guide" section needs to reference the scenario's tool name, not `launch_safety_assessment`.

### 3. Dashboard Generation — Scenario-Aware

**Files**: `elastic-config/dashboards/generate_exec_dashboard.py`, `elastic_config/deployer.py`

This is the **most important visual gap** — the dashboard currently shows "NOVA-7" to every scenario.

**Approach**: Make the dashboard generator accept scenario parameters instead of using hardcoded values.

- Convert `generate_exec_dashboard.py` from a standalone script to an importable function: `generate_dashboard(scenario) -> str` (returns NDJSON string)
- The function reads from the scenario object:
  - `scenario.scenario_name` → dashboard title and description
  - `scenario.namespace` → dashboard ID (`{ns}-exec-dashboard`)
  - `scenario.cloud_groups` → service names per cloud column, cluster names
  - Cloud labels (already present in CLOUD_GROUPS structure)
- Deployer's `_deploy_dashboard()` calls `generate_dashboard(self.scenario)` instead of reading a static NDJSON file
- Remove the static `exec-dashboard.ndjson` file (or keep it as a fallback for space only)

**CLOUD_GROUPS derivation**: Each scenario already has `cloud_groups` and `k8s_clusters` properties. Combine them:
```python
# In BaseScenario, add:
@property
def dashboard_cloud_groups(self) -> list[dict]:
    """Cloud groups for exec dashboard layout."""
    cloud_order = ["aws", "gcp", "azure"]
    groups = []
    for provider in cloud_order:
        svcs = self.cloud_groups.get(provider, [])
        cluster = next((c for c in self.k8s_clusters if c["provider"] == provider), {})
        groups.append({
            "label": f"**{provider.upper()}** {cluster.get('region', '')}",
            "services": svcs,
            "cluster": cluster.get("name", ""),
        })
    return groups
```

### 4. Log Generators — Read from Active Scenario

**Files**: Multiple generators

#### 4a. `log_generators/nginx_metrics_generator.py`
- Replace hardcoded `NGINX_HOSTS` with scenario-derived names
- Read `NAMESPACE` from `app.config` and use `{namespace}-nginx-01`, `{namespace}-nginx-02`

#### 4b. `log_generators/vpc_flow_generator.py`
- Replace `SCOPE_NAME = "nova7-vpc-flow-generator"` → `f"{NAMESPACE}-vpc-flow-generator"`
- Replace `GCP_VPC_NAMES` → `[f"{NAMESPACE}-vpc-prod", f"{NAMESPACE}-vpc-staging", f"{NAMESPACE}-vpc-data"]`
- Replace `"cloud.account.id": "nova7-project-prod"` → `f"{NAMESPACE}-project-prod"`

#### 4c. `log_generators/k8s_metrics_generator.py`
- Replace `DAEMONSETS = ["nova7-log-collector", "nova7-node-exporter"]` → `[f"{NAMESPACE}-log-collector", f"{NAMESPACE}-node-exporter"]`
- Replace `STATEFULSETS = ["nova7-redis", "nova7-postgres"]` → `[f"{NAMESPACE}-redis", f"{NAMESPACE}-postgres"]`

#### 4d. `log_generators/nginx_log_generator.py`
- Replace all `"nova7-proxy-*"` hostnames with `f"{NAMESPACE}-proxy-*"`
- Replace `"service.namespace": "nova7"` with NAMESPACE
- Replace `"url.domain": "nova7.internal"` with `f"{NAMESPACE}.internal"`
- Replace `"/api/v1/agents/nova7"` with scenario-appropriate paths

#### 4e. `log_generators/mysql_log_generator.py`
- Replace `nova7_telemetry`, `nova7_mission`, etc. database names
- Replace `nova7_app` user names
- Replace `nova7-app-01.internal` host names
- Replace `nova7-mysql-host` host names
- Replace `"service.namespace": "nova7"` with NAMESPACE

### 5. `deployment.environment` — Scenario-Qualified

**Files**: `log_generators/trace_generator.py`, `log_generators/nginx_log_generator.py`, `log_generators/mysql_log_generator.py`

Change `"deployment.environment": "production"` to `f"production-{NAMESPACE}"` (e.g. `production-finserve`, `production-nova7`).

This allows filtering traces by scenario in Kibana's APM Service Map.

### 6. BaseScenario Infrastructure Naming

**File**: `scenarios/base.py`

Add a helper property for generating consistent infrastructure names:
```python
@property
def infra_names(self) -> dict[str, Any]:
    """Standard infrastructure names derived from namespace."""
    ns = self.namespace
    return {
        "nginx_hosts": [f"{ns}-nginx-01", f"{ns}-nginx-02"],
        "nginx_servers": [f"{ns}-proxy-01", f"{ns}-proxy-02"],
        "proxy_host": f"{ns}-proxy-host",
        "mysql_host": f"{ns}-mysql-host",
        "vpc_names": [f"{ns}-vpc-prod", f"{ns}-vpc-staging", f"{ns}-vpc-data"],
        "daemonsets": [f"{ns}-log-collector", f"{ns}-node-exporter"],
        "statefulsets": [f"{ns}-redis", f"{ns}-postgres"],
        "url_domain": f"{ns}.internal",
    }
```

Generators import and use this instead of hardcoding.

## Execution Order

1. **BaseScenario additions** — `infra_names`, `dashboard_cloud_groups`, default `tool_definitions` with assessment tool hook
2. **Scenario implementations** — update all 5 scenarios with assessment tool config
3. **Deployer updates** — use scenario's tool_definitions, fix agent prompt's tool guide
4. **Dashboard generator** — convert to function, accept scenario parameter
5. **Log generators** — replace all hardcoded nova7 references with scenario-derived values
6. **deployment.environment** — add namespace suffix in trace/nginx/mysql generators
7. **Test** — deploy financial scenario and verify dashboard title, tool names, agent prompt, deployment.environment

## Files Modified (summary)

| File | Change |
|------|--------|
| `scenarios/base.py` | Add `infra_names`, `dashboard_cloud_groups`, default `tool_definitions`, `assessment_tool_config` |
| `scenarios/space/scenario.py` | Add `assessment_tool_config`, verify existing config |
| `scenarios/financial/scenario.py` | Add `assessment_tool_config` |
| `scenarios/healthcare/scenario.py` | Add `assessment_tool_config` |
| `scenarios/gaming/scenario.py` | Add `assessment_tool_config` |
| `scenarios/fanatics/scenario.py` | Add `assessment_tool_config` |
| `elastic_config/deployer.py` | Use scenario tools, fix agent prompt, generate dashboard dynamically |
| `elastic-config/dashboards/generate_exec_dashboard.py` | Convert to `generate_dashboard(scenario)` function |
| `log_generators/nginx_metrics_generator.py` | Use scenario namespace for host names |
| `log_generators/vpc_flow_generator.py` | Use scenario namespace for VPC/scope names |
| `log_generators/k8s_metrics_generator.py` | Use scenario namespace for daemonset/statefulset names |
| `log_generators/nginx_log_generator.py` | Use scenario namespace for all nova7 refs |
| `log_generators/mysql_log_generator.py` | Use scenario namespace for all nova7 refs |
| `log_generators/trace_generator.py` | `deployment.environment` = `production-{namespace}` |
