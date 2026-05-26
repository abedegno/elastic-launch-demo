# BaseScenario property contract

Use this as a generation checklist during Phase 5. Work top-to-bottom and verify every property is present and correctly shaped.

Reference source: [scenarios/base.py](scenarios/base.py)

---

## Identity properties

| Property | Required | Type | Notes |
|---|---|---|---|
| `scenario_id` | ✅ | `str` | Lowercase slug. Used as dict key and in ES index names. E.g. `"logistics"` |
| `scenario_name` | ✅ | `str` | Display name. E.g. `"Global Logistics Platform"` |
| `scenario_description` | ✅ | `str` | 2–3 sentence card blurb. Shown on scenario selector. |
| `namespace` | ✅ | `str` | Short telemetry prefix. Used in index names: `logs.otel.<ns>`. E.g. `"logistics"` |
| `scenario_icon` | optional | `str` | Emoji. Default `"🔧"` |
| `sort_order` | optional | `int` | Lower = earlier. Default 999. Use 10–99 for new scenarios. |
| `nominal_label` | optional | `str` | Label for the "nominal" state in the UI. Default `"Nominal"`. Override if the vertical uses different terminology (e.g. `"Green"`, `"Stable"`). |
| `get_correlation_attribute` | optional | `str` | Returns a single attribute key whose value best correlates faults across services. Override when the vertical has a natural correlation ID (e.g. `"mission.id"`, `"order.id"`). Default returns `"chaos.channel"`. Signature: `def get_correlation_attribute(self) -> str`. |

---

## Executive KPIs

| Property | Required | Type | Notes |
|---|---|---|---|
| `executive_kpi_emitter_service_name` | optional | `str \| None` | `SERVICE_NAME` of the one service that emits `business.*` gauges. Required for exec dashboard. |
| `executive_dashboard_intro` | optional | `str` | Markdown blurb shown at top of exec dashboard. |
| `executive_kpi_sections` | optional | `list[dict]` | 4 sections, 6 metrics each. See shape below. |
| `executive_trend_charts` | optional | `list[dict]` | 6 trend charts (3×2 grid). See shape below. |

**`executive_kpi_sections` shape:**
```python
[
    {
        "header": "**Revenue** — GMV, conversion, ...",  # bold header + subtitle
        "specs": [
            ("Display Title (unit)", "metrics.business.<field_name>"),
            # ... 6 entries
        ],
    },
    # ... 4 sections total
]
```

**`executive_trend_charts` shape:**
```python
[
    {"title": "GMV trend", "field": "metrics.business.gmv_usd_per_min", "y_label": "USD/min"},
    # ... 6 entries total
]
```

Field names in `executive_kpi_sections` must match what `executive_kpis.py` actually emits (e.g. `emit_gauge("business.gmv_usd_per_min", ...)` → `"metrics.business.gmv_usd_per_min"`).

---

## Services

```python
@property
def services(self) -> dict[str, dict[str, Any]]:
    return {
        "<service-key>": {
            "cloud_provider": "aws",           # "aws" | "gcp" | "azure"
            "cloud_region": "us-east-1",       # e.g. "us-east-1", "us-central1", "eastus"
            "cloud_platform": "aws_ec2",       # "aws_ec2" | "gcp_compute_engine" | "azure_vm"
            "cloud_availability_zone": "us-east-1a",
            "subsystem": "payments",           # short functional area label
            "language": "java",                # python | java | go | dotnet | rust | cpp
        },
        # ... 9 total: 3 AWS, 3 GCP, 3 Azure
    }
```

Rules:
- Exactly 9 services.
- Exactly 3 per cloud provider (aws, gcp, azure).
- Service keys use kebab-case (e.g. `"payment-processor"`, `"order-management"`).
- Language must be one of: `python`, `java`, `go`, `dotnet`, `rust`, `cpp`. (These map to exception type dictionaries in `log_generators/trace_generator.py`.)

---

## Channel registry

```python
@property
def channel_registry(self) -> dict[int, dict[str, Any]]:
    return {
        1: {
            "name": "Payment Gateway Timeout",         # Display name
            "subsystem": "payments",                   # Matches a subsystem in services
            "vehicle_section": "checkout_pipeline",    # Domain flavor — physical or logical zone
            "error_type": "PAYMENT-GATEWAY-TIMEOUT",   # ALLCAPS-HYPHENATED. Appears in body.text logs.
            "sensor_type": "gateway_latency",          # Domain flavor — what sensor/metric triggered
            "affected_services": ["payment-processor", "order-management"],   # Direct fault targets
            "cascade_services": ["storefront-gateway"],                        # Downstream victims
            "description": "...",                      # 1–2 sentence customer-facing description
            "investigation_notes": "...",              # 5–6 numbered steps for the runbook skill
            "remediation_action": "restart_payment_gateway",  # snake_case action identifier
            "error_message": "[PaymentProcessor] PAYMENT-GATEWAY-TIMEOUT: provider={payment_provider} timeout={timeout_ms}ms",
            "stack_trace": "TimeoutException: PAYMENT-GATEWAY-TIMEOUT\n  at ...\nProvider: {payment_provider}\nTimeout: {timeout_ms}ms",
        },
        # ... 20 total
    }
```

Rules:
- Exactly 20 channels, keyed 1–20.
- Every value in `affected_services` and `cascade_services` must be a key in `services`.
- Every `{placeholder}` in `error_message` and `stack_trace` must be a key in `get_fault_params(channel)`.
- `investigation_notes`: 5–6 numbered steps. Should reference specific log field names, specific metric names, and `{placeholder}` values from `error_message`. Help the agent guide a real investigation.
- Channels 1–15: HITL. Investigation-grade faults. The `remediation_action` requires human approval.
- Channels 16–20: Auto-remediate. Must be faults a real production runbook would auto-handle: pod restart, autoscaler trigger, cache flush, credential rotation, certificate renewal, budget reset, circuit-breaker reset, cache warmup. See [GUARDRAILS.md](.claude/skills/add-scenario/GUARDRAILS.md).

---

## Topology

### `service_topology`
```python
{
    "<caller-service>": [
        ("<callee-service>", "/api/v1/path", "GET"),   # (callee, endpoint, method)
        # ...
    ],
    # ... all 9 services should appear as callers
}
```

### `entry_endpoints`
```python
{
    "<service>": [
        ("/api/v1/path", "GET"),    # (path, method)
        # ... 2–4 endpoints per service
    ],
}
```

### `db_operations`
```python
{
    "<service>": [
        ("SELECT", "table_name", "SELECT col, col2 FROM table_name WHERE ..."),
        # ... 1–3 ops per service
    ],
}
```

---

## Infrastructure

### `hosts` — 3 hosts, one per cloud

```python
[
    {
        # Identity
        "host.name": "<ns>-aws-host-01",
        "host.id": "i-0a1b2c3d4e5f67890",         # AWS instance ID format
        "host.arch": "amd64",
        "host.type": "m6i.2xlarge",                 # AWS instance type
        "host.image.id": "ami-0123456789abcdef0",
        # CPU
        "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz",
        "host.cpu.vendor.id": "GenuineIntel",
        "host.cpu.family": "6",
        "host.cpu.model.id": "106",
        "host.cpu.stepping": "6",
        "host.cpu.cache.l2.size": 1310720,
        # Network
        "host.ip": ["10.0.1.100", "172.31.0.10"],
        "host.mac": ["0e:1a:2b:3c:4d:5e"],
        # OS
        "os.type": "linux",
        "os.description": "Amazon Linux 2023.6.20250115",
        # Cloud
        "cloud.provider": "aws",
        "cloud.platform": "aws_ec2",
        "cloud.region": "us-east-1",
        "cloud.availability_zone": "us-east-1a",
        "cloud.account.id": "112233445566",
        "cloud.instance.id": "i-0a1b2c3d4e5f67890",
        # Resources
        "cpu_count": 8,
        "memory_total_bytes": 32 * 1024 * 1024 * 1024,
        "disk_total_bytes": 500 * 1024 * 1024 * 1024,
    },
    # GCP host: host.id = numeric string, cloud.platform = "gcp_compute_engine", cloud.region = "us-central1"
    # Azure host: host.id = ARM resource path, cloud.platform = "azure_vm", cloud.region = "eastus"
]
```

### `k8s_clusters` — 3 clusters

```python
[
    {
        "name": "<ns>-eks-cluster",
        "provider": "aws",
        "platform": "aws_eks",
        "region": "us-east-1",
        "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
        "os_description": "Amazon Linux 2",
        "services": ["<aws-svc-1>", "<aws-svc-2>", "<aws-svc-3>"],  # exact 3 AWS service keys
    },
    {
        "name": "<ns>-gke-cluster",
        "provider": "gcp",
        "platform": "gcp_gke",
        "region": "us-central1",
        "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
        "os_description": "Container-Optimized OS",
        "services": ["<gcp-svc-1>", "<gcp-svc-2>", "<gcp-svc-3>"],
    },
    {
        "name": "<ns>-aks-cluster",
        "provider": "azure",
        "platform": "azure_aks",
        "region": "eastus",
        "zones": ["eastus-1", "eastus-2", "eastus-3"],
        "os_description": "Ubuntu 22.04 LTS",
        "services": ["<azure-svc-1>", "<azure-svc-2>", "<azure-svc-3>"],
    },
]
```

Each cluster's `services` list must contain exactly the 3 service names for that cloud provider.

---

## Theme

```python
@property
def theme(self) -> UITheme:
    return UITheme(
        bg_primary="#0a0f1e",        # Main background
        bg_secondary="#111827",      # Card/panel backgrounds
        bg_tertiary="#1f2937",       # Input/accent backgrounds
        accent_primary="#f59e0b",    # Buttons, borders, highlights — pick something vertical-appropriate
        accent_secondary="#3b82f6",  # Secondary accents
        text_primary="#f9fafb",
        text_secondary="#9ca3af",
        text_accent="#f59e0b",       # Match accent_primary
        status_nominal="#10b981",    # Green
        status_warning="#f59e0b",    # Amber
        status_critical="#ef4444",   # Red
        status_info="#3b82f6",       # Blue
        font_family="'Inter', system-ui, sans-serif",
        # Effects — pick one if it fits:
        glow_effect=False,           # Neon glow (gaming)
        grid_background=False,       # Grid pattern (ecommerce, fintech)
        scanline_effect=False,       # CRT effect (space only)
        # Domain vocabulary:
        chaos_title="Incident Simulator",   # or "Fault Injector", "Chaos Engine", etc.
        service_label="Service",            # or "Node", "System", "Module", "Unit"
        channel_label="Channel",            # or "Incident", "Alert", "Scenario"
    )
```

---

## Agent config

```python
@property
def agent_config(self) -> dict[str, Any]:
    return {
        "id": "<ns>-ops-analyst",             # kebab-case, unique per scenario
        "name": "<Vertical> Operations Analyst",
        "assessment_tool_name": "<ns>_readiness_assessment",  # snake_case, matches assessment_tool_config id
        "system_prompt": (
            "You are the <Role> for a <description>. "
            "You help engineering teams investigate incidents and perform root cause analysis "
            "across 9 services spanning AWS, GCP, and Azure. "
            "You have deep expertise in <domain areas>. "
            "When investigating incidents, search for these error identifiers in logs (field: body.text): "
            "<list all 20 error_type values grouped by subsystem>. "
            "Log messages are in body.text — NEVER search the body field alone."
        ),
    }
```

The system_prompt MUST list all 20 `error_type` values from `channel_registry` grouped by subsystem. This is how the agent knows what to search for.

```python
@property
def assessment_tool_config(self) -> dict[str, Any]:
    return {
        "id": "<ns>_readiness_assessment",    # must match assessment_tool_name above
        "description": (
            "Comprehensive platform readiness assessment for <scenario name>. "
            "Evaluates <key subsystems>. Returns <business metrics> alongside infrastructure health. "
            "Log message field: body.text (never use 'body' alone)."
        ),
    }
```

```python
@property
def knowledge_base_docs(self) -> list[dict[str, Any]]:
    return []  # Populated by deployer from channel_registry
```

---

## `get_fault_params`

```python
def get_fault_params(self, channel: int) -> dict[str, Any]:
    rng = random.Random(channel + int(time.time()) // 10)
    params: dict[int, dict[str, Any]] = {
        1: {
            "param_name": rng.choice(["option_a", "option_b"]),
            "numeric_param": rng.randint(100, 999),
            # ... one key per {placeholder} in error_message + stack_trace for channel 1
        },
        # ... 20 entries total
    }
    return params.get(channel, {})
```

For every channel, collect all `{placeholder}` names from both `error_message` and `stack_trace` (regex `\{(\w+)\}`). Every one must be a key in the corresponding `params[channel]` dict.

---

## `get_trace_attributes`

```python
def get_trace_attributes(self, service_name: str, rng) -> dict:
    base = {
        "domain.attribute": rng.choice(["val_a", "val_b"]),   # 2–3 domain-wide attrs
    }
    svc_attrs = {
        "<service-key>": {
            "domain.service_attr": rng.choice([...]),          # 4–5 per-service attrs
        },
        # ... all 9 services
    }
    base.update(svc_attrs.get(service_name, {}))
    return base
```

Use OTel-style dotted attribute names. These appear on every trace span — pick attributes that make the demo data richly filterable.

---

## `get_rca_clues`

```python
def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
    clues = {
        1: {
            "<affected-service>": {"clue.attr": rng.uniform(...)},    # partial clue
            "<cascade-service>":  {"clue.attr": rng.randint(...)},    # different clue
        },
        # ... for all 20 channels
    }
    return clues.get(channel, {}).get(service_name, {})
```

Each inner service dict should have 2–3 domain-appropriate numeric or boolean attributes that suggest (but don't directly name) the root cause. Different services should get different clues — no single service has the complete picture.
