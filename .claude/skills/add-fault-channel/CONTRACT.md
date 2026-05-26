# Channel property contract

Use this as a generation checklist. Work top-to-bottom and verify every property is present and correctly shaped before writing the edit.

Reference source: [scenarios/base.py](scenarios/base.py), channel_registry section of [scenarios/<id>/scenario.py](scenarios/)

---

## `channel_registry[N]` — all required fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | ✅ | `str` | Display name. E.g. `"Payment Gateway Timeout"` |
| `subsystem` | ✅ | `str` | Matches a `subsystem` value in the scenario's `services` dict |
| `vehicle_section` | ✅ | `str` | Domain-appropriate logical zone. E.g. `"checkout_pipeline"`, `"engine_bay"`, `"auth_layer"` |
| `error_type` | ✅ | `str` | ALLCAPS-HYPHENATED. Used in `body.text` log search. E.g. `"PAYMENT-GATEWAY-TIMEOUT"` |
| `sensor_type` | ✅ | `str` | Domain flavor — what sensor/metric triggered this. E.g. `"gateway_latency"`, `"pressure"` |
| `affected_services` | ✅ | `list[str]` | Direct fault targets. Every entry must be a key in `services`. |
| `cascade_services` | ✅ | `list[str]` | Downstream victims. Every entry must be a key in `services`. May be empty `[]`. |
| `description` | ✅ | `str` | 1–2 sentence customer-facing description of the observable failure |
| `investigation_notes` | ✅ | `str` | 5–6 numbered steps for the runbook skill. See shape below. |
| `remediation_action` | ✅ | `str` | `snake_case` action identifier. E.g. `"restart_payment_gateway"` |
| `error_message` | ✅ | `str` | Log line template. All `{placeholder}` names must be keys in `get_fault_params(N)`. |
| `stack_trace` | ✅ | `str` | Multi-line dump template. All `{placeholder}` names must be keys in `get_fault_params(N)`. |

### `investigation_notes` shape

5–6 numbered steps. Should reference:
- Specific log field names (always `body.text`, never `body` alone)
- Specific metric names from the scenario's service telemetry
- `{placeholder}` values from `error_message` to anchor searches
- The root cause hypothesis (what component or condition triggers this)
- The remediation action and how to confirm it worked

Good example:
```
1. Search body.text for PAYMENT-GATEWAY-TIMEOUT in logs.otel.{ns} to establish blast radius.
2. Check {provider} gateway health endpoint — compare {timeout_ms}ms against p99 baseline (typically <800ms).
3. Inspect connection pool metrics on payment-processor: active_connections vs pool_max.
4. Cross-reference with order-management error rate spike at the same timestamp.
5. Trigger restart_payment_gateway action and confirm new connections establish within 30s.
6. Verify no in-flight transactions were dropped (check transaction_id rollback logs).
```

---

## `get_fault_params(N)` — placeholder parity

```python
N: {
    "placeholder_name": rng.choice(["val_a", "val_b"]),    # string params
    "numeric_param": rng.randint(100, 999),                  # int params
    "float_param": round(rng.uniform(0.1, 9.9), 2),          # float params
}
```

Rules:
- Use `rng = random.Random(channel + int(time.time()) // 10)` (already initialized in the method)
- Every `{name}` in `error_message` **and** `stack_trace` must be a key here
- Domain-appropriate ranges (don't use `randint(0, 9999)` for a latency in milliseconds)
- 2–5 params per channel is typical

---

## `get_rca_clues(N, service_name, rng)` — inner service dict

```python
N: {
    "<affected-service>": {
        "clue.attribute_name": rng.uniform(low, high),   # numeric clue
        "clue.flag_name": rng.random() > 0.7,            # boolean clue
    },
    "<cascade-service>": {
        "clue.different_attr": rng.randint(low, high),
    },
}
```

Rules:
- Keys must be service names from `affected_services` + `cascade_services`
- 2–3 attributes per service
- Attributes should suggest (but not directly name) the root cause — different services see different partial symptoms
- Use OTel-style dotted names: `"payment.pool_exhaustion_pct"`, `"gateway.connection_wait_ms"`
- Numeric values with domain-appropriate ranges, not random noise

---

## `agent_config` system_prompt — error_type list

After writing the new channel, verify the `system_prompt` string in `agent_config` lists the new `error_type` under the correct subsystem grouping. If the `error_type` changed, both the old value must be removed and the new value added.

Format used in existing scenarios:
```python
"<Subsystem> faults (<ERR-TYPE-1>, <ERR-TYPE-2>, <ERR-TYPE-3>), "
```

If the new channel adds a first fault in a new subsystem, add a new grouping line.

---

## Validation checklist (run after editing)

- [ ] `len(channel_registry) == 20`
- [ ] Channel number unchanged (replaced in-place)
- [ ] All `{placeholder}` in `error_message` are keys in `get_fault_params(N)`
- [ ] All `{placeholder}` in `stack_trace` are keys in `get_fault_params(N)`
- [ ] All `affected_services` values are keys in `services`
- [ ] All `cascade_services` values are keys in `services`
- [ ] `error_type` appears in `agent_config.system_prompt` under the correct subsystem
- [ ] Old `error_type` removed from `system_prompt` (if it changed)
- [ ] Channel number ≤ 15 → `remediation_action` is a HITL action
- [ ] Channel number 16–20 → `remediation_action` is a plausible auto-runbook action
- [ ] `git diff --name-only` shows only `scenarios/<id>/scenario.py`
