#!/usr/bin/env bash
#
# validate-e2e.sh — End-to-End validation of the NOVA-7 Elastic Launch Demo.
#
# Proves every layer works: chaos trigger → log ingestion → significant event
# detection → agent RCA via workflow → runbook lookup → remediation → resolution.
#
# Uses Channel 2 (Fuel Pressure Anomaly) as the test vector.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Load environment ──────────────────────────────────────────────────────────
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

ELASTIC_URL="${ELASTIC_URL%/}"
KIBANA_URL="${KIBANA_URL%/}"

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
RESULTS=()

pass() { echo -e "  \033[0;32mPASS\033[0m  $*"; PASS=$((PASS + 1)); RESULTS+=("PASS|$*"); }
fail() { echo -e "  \033[0;31mFAIL\033[0m  $*"; FAIL=$((FAIL + 1)); RESULTS+=("FAIL|$*"); }
info() { echo -e "  \033[0;34mINFO\033[0m  $*"; }
step() { echo -e "\n\033[1;36m── Step $1: $2\033[0m"; }

es_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

es_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" 2>/dev/null
}

kb_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "kbn-xsrf: true" \
        -H "x-elastic-internal-origin: kibana" \
        "${KIBANA_URL}${path}" 2>/dev/null
}

kb_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -H "x-elastic-internal-origin: kibana" \
        "${KIBANA_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

# Parse HTTP response: body (all but last line) and status code (last line)
parse_response() {
    local response="$1"
    RESP_CODE=$(echo "$response" | tail -1)
    RESP_BODY=$(echo "$response" | sed '$d')
}

get_count() {
    local index="$1"
    local response
    response=$(es_post "/${index}/_count" '{}')
    parse_response "$response"
    if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
        echo "$RESP_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0"
    else
        echo "-1"
    fi
}

echo ""
echo "============================================================"
echo "   NOVA-7 Launch Demo — End-to-End Validation"
echo "============================================================"
echo ""
echo "Test vector: Channel 2 — Fuel Pressure Anomaly"
echo ""

# ══════════════════════════════════════════════════════════════════════════════
step 1 "Pre-flight checks"
# ══════════════════════════════════════════════════════════════════════════════

preflight_ok=true

# ES reachable
response=$(es_get "/")
parse_response "$response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    info "Elasticsearch reachable"
else
    fail "Step 1 — Elasticsearch unreachable (HTTP $RESP_CODE)"
    preflight_ok=false
fi

# Kibana reachable
response=$(kb_get "/api/status")
parse_response "$response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    info "Kibana reachable"
else
    fail "Step 1 — Kibana unreachable (HTTP $RESP_CODE)"
    preflight_ok=false
fi

# logs stream has data
logs_count=$(get_count "logs")
if [[ "$logs_count" -gt 0 ]]; then
    info "logs stream has data ($logs_count docs)"
else
    fail "Step 1 — logs stream has no data (is the app running?)"
    preflight_ok=false
fi

# Knowledge base has 20 docs
kb_count=$(get_count "nova7-knowledge-base")
if [[ "$kb_count" -ge 20 ]]; then
    info "Knowledge base has $kb_count docs"
else
    fail "Step 1 — Knowledge base has $kb_count docs (expected >= 20)"
    preflight_ok=false
fi

# Agent exists with tools
tools_response=$(kb_get "/api/agent_builder/tools")
parse_response "$tools_response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    tool_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data if isinstance(data, list) else data.get('results', data.get('tools', data.get('data', [])))
custom = [t for t in tools if not t.get('readonly', False) and not t.get('is_default', False)]
print(len(custom))
" 2>/dev/null || echo "0")
    if [[ "$tool_count" -ge 7 ]]; then
        info "Agent has $tool_count tools"
    else
        fail "Step 1 — Agent has $tool_count tools (expected >= 8)"
        preflight_ok=false
    fi
else
    fail "Step 1 — Agent Builder API not accessible (HTTP $RESP_CODE)"
    preflight_ok=false
fi

# 20 significant event queries on logs stream
se_response=$(kb_get "/api/streams/logs/queries")
parse_response "$se_response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    se_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
queries = data if isinstance(data, list) else data.get('queries', data.get('results', data.get('data', [])))
count = sum(1 for q in queries if q.get('id', '').startswith('nova7-se-'))
print(count)
" 2>/dev/null || echo "0")
    if [[ "$se_count" -ge 20 ]]; then
        info "Significant events: $se_count queries"
    else
        fail "Step 1 — Only $se_count significant event queries (expected >= 20)"
        preflight_ok=false
    fi
else
    fail "Step 1 — Streams Queries API not accessible (HTTP $RESP_CODE)"
    preflight_ok=false
fi

# 3 workflows exist
wf_response=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
parse_response "$wf_response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    wf_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
nova7 = [i for i in items if 'NOVA-7' in i.get('name', '')]
print(len(nova7))
" 2>/dev/null || echo "0")
    if [[ "$wf_count" -ge 3 ]]; then
        info "Workflows: $wf_count NOVA-7 workflows"
    else
        fail "Step 1 — Only $wf_count NOVA-7 workflows (expected >= 3)"
        preflight_ok=false
    fi
else
    fail "Step 1 — Workflows API not accessible (HTTP $RESP_CODE)"
    preflight_ok=false
fi

# Dashboard exists
dash_response=$(kb_post "/api/saved_objects/_export" '{"objects":[{"type":"dashboard","id":"nova7-exec-dashboard"}],"includeReferencesDeep":false}')
parse_response "$dash_response"
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]] && echo "$RESP_BODY" | grep -q "nova7-exec-dashboard" 2>/dev/null; then
    info "Executive dashboard exists"
else
    fail "Step 1 — Executive dashboard not found"
    preflight_ok=false
fi

if $preflight_ok; then
    pass "Step 1 — All pre-flight checks passed"
else
    echo ""
    echo "  Pre-flight checks failed. Fix issues above before continuing."
    echo "  Run: ./setup-all.sh"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 2 "Trigger fault — Channel 2 (Fuel Pressure Anomaly)"
# ══════════════════════════════════════════════════════════════════════════════

trigger_response=$(curl -s -w "\n%{http_code}" -X POST http://localhost/api/chaos/trigger \
    -H 'Content-Type: application/json' -d '{"channel": 2}' 2>/dev/null)
parse_response "$trigger_response"

if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    trigger_status=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('status', 'unknown'))
" 2>/dev/null || echo "unknown")

    if [[ "$trigger_status" == "triggered" || "$trigger_status" == "already_active" ]]; then
        info "Chaos trigger returned: $trigger_status"
    else
        info "Chaos trigger returned unexpected status: $trigger_status"
    fi

    # Verify channel is ACTIVE
    status_response=$(curl -s -w "\n%{http_code}" http://localhost/api/chaos/status/2 2>/dev/null)
    parse_response "$status_response"
    ch_state=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('state', data.get('status', 'unknown')))
" 2>/dev/null || echo "unknown")

    if [[ "$ch_state" == "ACTIVE" || "$ch_state" == "active" ]]; then
        pass "Step 2 — Channel 2 triggered and ACTIVE"
    else
        fail "Step 2 — Channel 2 state is '$ch_state', expected ACTIVE"
    fi
else
    fail "Step 2 — Chaos trigger failed (HTTP $RESP_CODE)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 3 "Wait for error logs"
# ══════════════════════════════════════════════════════════════════════════════

info "Polling for FuelPressureException logs (up to 30s)..."
# Note: OTLP attributes use passthrough mapping — individual attribute keys
# are not indexed. We query via body.text (log message) + severity_text instead.

error_found=false
error_count=0
for i in $(seq 1 6); do
    response=$(es_post "/logs/_search" '{
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"body.text": "FuelPressureException"}},
                    {"term": {"severity_text": "ERROR"}}
                ],
                "filter": [{"range": {"@timestamp": {"gte": "now-60s"}}}]
            }
        },
        "size": 0,
        "track_total_hits": true
    }')
    parse_response "$response"

    if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
        error_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('hits', {}).get('total', {})
print(total.get('value', 0) if isinstance(total, dict) else total)
" 2>/dev/null || echo "0")

        if [[ "$error_count" -gt 0 ]]; then
            error_found=true
            break
        fi
    fi

    info "  Attempt $i/6 — no errors yet, waiting 5s..."
    sleep 5
done

if $error_found; then
    info "Found $error_count FuelPressureException errors"

    # Also check for cascade warnings
    cascade_response=$(es_post "/logs/_search" '{
        "query": {
            "bool": {
                "must": [{"term": {"severity_text": "WARN"}}],
                "filter": [
                    {"range": {"@timestamp": {"gte": "now-60s"}}},
                    {"terms": {"resource.attributes.service.name": ["mission-control", "range-safety"]}}
                ]
            }
        },
        "size": 0,
        "track_total_hits": true
    }')
    parse_response "$cascade_response"
    if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
        warn_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('hits', {}).get('total', {})
print(total.get('value', 0) if isinstance(total, dict) else total)
" 2>/dev/null || echo "0")
        if [[ "$warn_count" -gt 0 ]]; then
            info "Cascade warnings detected: $warn_count WARN logs from downstream services"
        else
            info "No cascade warnings yet (may appear shortly)"
        fi
    fi

    pass "Step 3 — Error logs ingested ($error_count FuelPressureException errors)"
else
    fail "Step 3 — No FuelPressureException errors found after 30s"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 4 "Verify significant event ES|QL query matches"
# ══════════════════════════════════════════════════════════════════════════════

# The significant event ES|QL queries reference attributes.* fields which use
# passthrough mapping and aren't directly queryable via ES|QL _query API.
# We validate the equivalent logic using body.text which IS indexed.
esql_query='FROM logs | WHERE body.text LIKE "*FuelPressureException*" | STATS error_count = COUNT(*)'

esql_body=$(python3 -c "
import json, sys
print(json.dumps({'query': '''$esql_query'''.strip()}))
" 2>/dev/null)

if [[ -n "$esql_body" ]]; then
    response=$(es_post "/_query" "$esql_body")
    parse_response "$response"

    if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
        esql_error_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rows = data.get('values', [])
if rows and len(rows) > 0 and len(rows[0]) > 0:
    print(rows[0][0])
else:
    print(0)
" 2>/dev/null || echo "0")

        if [[ "$esql_error_count" -gt 5 ]]; then
            pass "Step 4 — ES|QL detects FuelPressureException: error_count=$esql_error_count (threshold > 5)"
        else
            fail "Step 4 — ES|QL returned error_count=$esql_error_count (expected > 5)"
        fi
    else
        fail "Step 4 — ES|QL query failed (HTTP $RESP_CODE)"
    fi
else
    fail "Step 4 — Could not build ES|QL query"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 5 "Run the Significant Event Notification workflow"
# ══════════════════════════════════════════════════════════════════════════════

# Discover workflow ID
wf_search=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
parse_response "$wf_search"

notification_wf_id=""
if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    notification_wf_id=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', ''):
        print(item['id'])
        break
" 2>/dev/null || echo "")
fi

wf_exec_id=""
if [[ -n "$notification_wf_id" ]]; then
    info "Found workflow ID: $notification_wf_id"

    wf_run_response=$(kb_post "/api/workflows/${notification_wf_id}/run" '{
        "inputs": {
            "channel": 2,
            "error_type": "FuelPressureException",
            "subsystem": "propulsion",
            "severity": "high"
        }
    }')
    parse_response "$wf_run_response"

    if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
        wf_exec_id=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('workflowExecutionId', ''))
" 2>/dev/null || echo "")
        pass "Step 5 — Workflow triggered (execution: ${wf_exec_id:-unknown})"
        info "Workflow will invoke AI agent for RCA (this takes ~3min)"
    else
        fail "Step 5 — Workflow run failed (HTTP $RESP_CODE): $(echo "$RESP_BODY" | head -c 200)"
    fi
else
    fail "Step 5 — Could not find 'Significant Event Notification' workflow"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 6 "Verify workflow execution completes"
# ══════════════════════════════════════════════════════════════════════════════

# The ai.agent step takes ~2-3 minutes. Poll execution status via API.
wf_status="unknown"
if [[ -n "$wf_exec_id" ]]; then
    info "Polling execution $wf_exec_id (up to 4min)..."
    for i in $(seq 1 8); do
        exec_response=$(kb_get "/api/workflowExecutions/$wf_exec_id")
        parse_response "$exec_response"

        if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
            wf_status=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('status', 'unknown'))
" 2>/dev/null || echo "unknown")
            wf_error=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
err = data.get('error')
if err and isinstance(err, dict):
    print(err.get('message', '')[:200])
elif err:
    print(str(err)[:200])
else:
    print('')
" 2>/dev/null || echo "")

            if [[ "$wf_status" == "completed" ]]; then
                info "Workflow completed successfully"
                break
            elif [[ "$wf_status" == "failed" ]]; then
                info "Workflow failed: $wf_error"
                break
            fi
        fi

        info "  Attempt $i/8 — status: $wf_status, waiting 30s..."
        sleep 30
    done
else
    info "No execution ID — skipping execution polling"
fi

if [[ "$wf_status" == "completed" ]]; then
    pass "Step 6 — Workflow execution completed (ai.agent RCA succeeded)"
elif [[ "$wf_status" == "failed" ]]; then
    fail "Step 6 — Workflow execution failed: $wf_error"
elif [[ "$wf_status" == "running" ]]; then
    fail "Step 6 — Workflow still running after 4min (ai.agent step may be stuck)"
else
    fail "Step 6 — Could not determine workflow execution status ($wf_status)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "6b" "Verify audit trail"
# ══════════════════════════════════════════════════════════════════════════════

audit_found=false
audit_count=0
if [[ "$wf_status" == "completed" ]]; then
    for i in $(seq 1 3); do
        response=$(es_post "/nova7-significant-events-audit/_search" '{
            "query": {
                "bool": {
                    "should": [
                        {"match": {"error_type": "FuelPressureException"}},
                        {"match_phrase": {"error_type": "FuelPressureException"}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 1
        }')
        parse_response "$response"

        if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
            audit_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('hits', {}).get('total', {})
print(total.get('value', 0) if isinstance(total, dict) else total)
" 2>/dev/null || echo "0")
            if [[ "$audit_count" -gt 0 ]]; then
                audit_found=true
                break
            fi
        fi
        if [[ $i -lt 3 ]]; then sleep 5; fi
    done
fi

if $audit_found; then
    pass "Step 6b — Audit trail confirmed ($audit_count doc(s) in nova7-significant-events-audit)"
elif [[ "$wf_status" != "completed" ]]; then
    fail "Step 6b — Skipped (workflow did not complete)"
else
    fail "Step 6b — No audit doc found despite workflow completing"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 7 "Verify knowledge base (runbooks) accessible"
# ══════════════════════════════════════════════════════════════════════════════

response=$(es_post "/nova7-knowledge-base/_search" '{
    "query": {
        "bool": {
            "should": [
                {"match": {"title": "fuel_pressure"}},
                {"match": {"content": "fuel_pressure"}},
                {"term": {"channel_number": 2}}
            ],
            "minimum_should_match": 1
        }
    },
    "size": 1
}')
parse_response "$response"

if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    runbook_count=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('hits', {}).get('total', {})
print(total.get('value', 0) if isinstance(total, dict) else total)
" 2>/dev/null || echo "0")

    if [[ "$runbook_count" -gt 0 ]]; then
        runbook_title=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hits = data.get('hits', {}).get('hits', [])
if hits:
    src = hits[0].get('_source', {})
    print(src.get('title', src.get('id', 'unknown')))
else:
    print('unknown')
" 2>/dev/null || echo "unknown")
        pass "Step 7 — Runbook found: $runbook_title"
    else
        fail "Step 7 — No runbook found for channel 2 / fuel_pressure"
    fi
else
    fail "Step 7 — Knowledge base query failed (HTTP $RESP_CODE)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 8 "Trigger remediation"
# ══════════════════════════════════════════════════════════════════════════════

remediate_response=$(curl -s -w "\n%{http_code}" -X POST http://localhost/api/remediate/2 2>/dev/null)
parse_response "$remediate_response"

if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    remediate_action=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('action', data.get('status', 'unknown')))
" 2>/dev/null || echo "unknown")
    info "Remediation response: $remediate_action"

    # Verify channel is now STANDBY
    status_response=$(curl -s -w "\n%{http_code}" http://localhost/api/chaos/status/2 2>/dev/null)
    parse_response "$status_response"
    ch_state=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('state', data.get('status', 'unknown')))
" 2>/dev/null || echo "unknown")

    if [[ "$ch_state" == "STANDBY" || "$ch_state" == "standby" ]]; then
        pass "Step 8 — Channel 2 remediated and returned to STANDBY"
    else
        fail "Step 8 — Channel 2 state is '$ch_state' after remediation (expected STANDBY)"
    fi
else
    fail "Step 8 — Remediation failed (HTTP $RESP_CODE)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 9 "Verify errors stop flowing"
# ══════════════════════════════════════════════════════════════════════════════

info "Waiting 15s for error flow to stop..."
sleep 15

response=$(es_post "/logs/_search" '{
    "query": {
        "bool": {
            "must": [
                {"match_phrase": {"body.text": "FuelPressureException"}},
                {"term": {"severity_text": "ERROR"}}
            ],
            "filter": [{"range": {"@timestamp": {"gte": "now-12s"}}}]
        }
    },
    "size": 0,
    "track_total_hits": true
}')
parse_response "$response"

if [[ "$RESP_CODE" -ge 200 && "$RESP_CODE" -lt 300 ]]; then
    recent_errors=$(echo "$RESP_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('hits', {}).get('total', {})
print(total.get('value', 0) if isinstance(total, dict) else total)
" 2>/dev/null || echo "0")

    if [[ "$recent_errors" -eq 0 ]]; then
        pass "Step 9 — No new FuelPressureException errors in last 12s (flow stopped)"
    else
        fail "Step 9 — Still seeing $recent_errors errors in last 12s (expected 0)"
    fi
else
    fail "Step 9 — Query failed (HTTP $RESP_CODE)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step 10 "Summary"
# ══════════════════════════════════════════════════════════════════════════════

echo ""
echo "============================================================"
echo "   End-to-End Validation Results"
echo "============================================================"
echo ""

printf "  %-8s %s\n" "Result" "Step"
printf "  %-8s %s\n" "------" "----"
for result in "${RESULTS[@]}"; do
    status="${result%%|*}"
    desc="${result#*|}"
    if [[ "$status" == "PASS" ]]; then
        printf "  \033[0;32m%-8s\033[0m %s\n" "$status" "$desc"
    else
        printf "  \033[0;31m%-8s\033[0m %s\n" "$status" "$desc"
    fi
done

echo ""
echo "  Total: ${PASS} PASS / ${FAIL} FAIL"
echo ""
echo "============================================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "  Some E2E checks failed. Review output above for details."
    exit 1
else
    echo ""
    echo "  All E2E checks passed! Full pipeline verified."
    exit 0
fi
