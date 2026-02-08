# Plan: Fix Dashboard, Add Alerts, Test Agent & Workflows

## Findings Summary

### Dashboard — Why It's Empty (6 field name bugs)
| Panel | Broken Field | Actual Field | Fix |
|-------|-------------|--------------|-----|
| Error Rate | `severityText` | `severity_text` | Fix KQL filter |
| All count panels | `sourceField: "Records"` | `sourceField: "___records___"` | Fix all 11 panels |
| Active Anomalies | `resource.attributes.chaos.channel` | `attributes.chaos.channel` | Fix path |
| Errors by Subsystem | `resource.attributes.system.subsystem` | `attributes.system.subsystem` | Fix path |
| Top 10 Error Types | `resource.attributes.error.type` | `attributes.error.type` | Fix path |
| Nginx Request Rate | `data_stream.dataset: nginx.access` | `data_stream.dataset: nginx.access.otel` | Add `.otel` suffix |
| MySQL Slow Queries | `data_stream.dataset: mysql.slowlog` | `data_stream.dataset: mysql.slowlog.otel` | Add `.otel` suffix |
| All panels | ref name `indexpattern-datasource-layer1` | `indexpattern-datasource-layer-layer1` | Fix reference name |

Working panels (correct fields): Active Services (`resource.attributes.service.name`), Cloud Provider (`resource.attributes.cloud.provider`), Log Volume Over Time, Service Health Matrix.

### Alerts — Streams Rules Exist, No Actions
- 20 `streams.rules.esql` alert rules were auto-created by Streams when we deployed sig event queries
- All enabled, running every 1m with correct ES|QL queries
- **All have `actions: []`** — no notifications configured
- Connector available: **`Elastic-Cloud-SMTP`** (email)
- 7 LLM connectors available (Claude Sonnet, GPT, Gemini)

### Agent Builder — Working, Needs Testing
- `nova7-launch-anomaly-analyst` agent exists with 7 custom tools
- Agent mode is ON — agent can be invoked
- System prompt has strong RCA methodology (8-step process)
- Knowledge base has only 5/20 channel runbooks

### Workflows — 3 Exist, Field Issues
- `significant_event_notification` — invokes AI agent for RCA, audits result
- `remediation_action` — executes remediation with pre/post verification
- `escalation_hold` — countdown hold/resume state machine
- Workflows use `log.level` and `error.type` without `attributes.` prefix — need to verify these work

---

## Implementation Steps

### Step 1: Fix Executive Dashboard NDJSON
**File**: `elastic-config/dashboards/exec-dashboard.ndjson`

Use Python to rebuild the NDJSON with all field corrections:
- `severityText` → `severity_text` (in all KQL filters)
- `"Records"` → `"___records___"` (sourceField on all count columns)
- `resource.attributes.system.subsystem` → `attributes.system.subsystem`
- `resource.attributes.chaos.channel` → `attributes.chaos.channel`
- `resource.attributes.error.type` → `attributes.error.type`
- `nginx.access` → `nginx.access.otel` (data_stream.dataset filter)
- `mysql.slowlog` → `mysql.slowlog.otel` (data_stream.dataset filter)
- `indexpattern-datasource-layer1` → `indexpattern-datasource-layer-layer1` (reference name)
- Also add `severity_text: ERROR` filter to Service Health Matrix and Errors by Subsystem panels

Re-import via `setup-exec-dashboard.sh` and verify panels populate.

### Step 2: Add Email Actions to Streams Alert Rules
**File**: NEW `setup-alerts.sh`

For each of the 20 `streams.rules.esql` rules:
1. `GET /api/alerting/rules/_find` to list all streams rules
2. For each rule with `nova7-se-` in the ES|QL query, `PUT /api/alerting/rule/{id}` to add an action:
   - Connector: `Elastic-Cloud-SMTP`
   - Action: Send email with channel name, error details, link to Streams UI
   - Throttle: 5 minutes (avoid email storms during active chaos)

Add to `setup-all.sh` as Step 2.6 and `validate.sh` for verification.

### Step 3: Add Remaining 15 Knowledge Base Runbooks
**Files**: NEW `elastic-config/knowledge-base/ch{NN}-*.md` (15 files)

Create runbook documents for channels 2, 3, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20.
Each follows the existing format (channels 1, 4, 5, 10, 12):
- Error signature, affected/cascade services
- Common root causes with diagnostic steps
- Remediation procedures (step-by-step)
- Escalation criteria (when to HOLD)
- Related channels

Index via `setup-agent-builder.sh` (already handles all .md files in knowledge-base/).

### Step 4: Test Agent RCA End-to-End
1. Ensure app is running with generators active
2. Trigger chaos channel: `curl -X POST localhost/api/chaos/trigger -d '{"channel": 1}'`
3. Wait 30s for logs to accumulate
4. Invoke agent via Kibana API or workflow:
   - Option A: Direct agent invocation via Agent Builder API
   - Option B: Run `significant_event_notification` workflow which calls the agent
5. Verify agent produces structured RCA output with:
   - Root cause identification
   - Evidence from telemetry
   - Remediation recommendation
   - Confidence level
6. Resolve channel: `curl -X POST localhost/api/chaos/resolve -d '{"channel": 1}'`

### Step 5: Test Workflows
Test each workflow via `POST /api/workflows/{id}/run`:
1. **significant_event_notification**: trigger with channel=1, error_type=ThermalCalibrationException, subsystem=propulsion, severity=critical
2. **remediation_action**: trigger with channel=1, action_type=recalibrate_sensor, target_service=fuel-system, dry_run=true
3. **escalation_hold**: trigger with action=escalate, channel=1, severity=critical

Check execution status via `GET /api/workflowExecutions/{id}` and verify audit trail in `nova7-significant-events-audit` / `nova7-remediation-audit` indices.

### Step 6: Update setup-all.sh and validate.sh
- Add Step 2.6 for alerts setup
- Add validation for alert rules with actions
- Update summary to include alerts count

---

## Execution Order
1. Dashboard fix (Step 1) — immediate visual payoff
2. Alert actions (Step 2) — complete the notification pipeline
3. Knowledge base (Step 3) — enable full-coverage RCA
4. Test agent (Step 4) — verify RCA works
5. Test workflows (Step 5) — verify automation works
6. Integration updates (Step 6) — tie it all together
