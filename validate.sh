#!/usr/bin/env bash
#
# validate.sh — Comprehensive validation of the NOVA-7 Elastic Launch Demo.
#
# Checks ES/Kibana connectivity, data indices, agent, tools, dashboard,
# trace data, host metrics, and optional nginx/mysql log generator data.
#
# Uses only serverless-compatible APIs (no _find, no _get for saved objects).
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
WARN=0

pass() { echo -e "  \033[0;32mPASS\033[0m  $*"; PASS=$((PASS + 1)); }
fail() { echo -e "  \033[0;31mFAIL\033[0m  $*"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  \033[1;33mWARN\033[0m  $*"; WARN=$((WARN + 1)); }
info() { echo -e "  \033[0;34mINFO\033[0m  $*"; }

es_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" 2>/dev/null
}

es_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

kb_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "kbn-xsrf: true" \
        "${KIBANA_URL}${path}" 2>/dev/null
}

kb_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        "${KIBANA_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

get_count() {
    local index="$1"
    local response
    response=$(es_post "/${index}/_count" '{}')
    local http_code
    http_code=$(echo "$response" | tail -1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0"
    else
        echo "-1"
    fi
}

echo ""
echo "============================================================"
echo "   NOVA-7 Launch Demo — Validation Report"
echo "============================================================"
echo ""

# ── 1. Environment Variables ─────────────────────────────────────────────────
echo "--- Environment ---"
for var in ELASTIC_URL ELASTIC_API_KEY KIBANA_URL OTLP_ENDPOINT OTLP_API_KEY; do
    if [[ -n "${!var:-}" ]]; then
        pass "$var is set"
    else
        fail "$var is NOT set"
    fi
done
echo ""

# ── 2. Cluster Connectivity ──────────────────────────────────────────────────
echo "--- Elasticsearch Connectivity ---"
es_response=$(es_get "/")
es_code=$(echo "$es_response" | tail -1)
es_body=$(echo "$es_response" | sed '$d')

if [[ "$es_code" -ge 200 && "$es_code" -lt 300 ]]; then
    cluster_name=$(echo "$es_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cluster_name','?'))" 2>/dev/null || echo "?")
    pass "Elasticsearch reachable (cluster: $cluster_name)"
else
    fail "Elasticsearch unreachable (HTTP $es_code)"
fi
echo ""

echo "--- Kibana Connectivity ---"
kb_response=$(kb_get "/api/status")
kb_code=$(echo "$kb_response" | tail -1)

if [[ "$kb_code" -ge 200 && "$kb_code" -lt 300 ]]; then
    pass "Kibana reachable (HTTP $kb_code)"
else
    fail "Kibana unreachable (HTTP $kb_code)"
fi
echo ""

# ── 3. OTel Log Data ─────────────────────────────────────────────────────────
echo "--- OTel Log Data ---"
otel_count=$(get_count "logs")
if [[ "$otel_count" -gt 0 ]]; then
    pass "logs has data ($otel_count docs)"
elif [[ "$otel_count" -eq 0 ]]; then
    warn "logs exists but is empty (run the demo app first)"
else
    warn "logs index not found (run the demo app first)"
fi
echo ""

# ── 4. Knowledge Base ────────────────────────────────────────────────────────
echo "--- Knowledge Base ---"
kb_count=$(get_count "nova7-knowledge-base")
if [[ "$kb_count" -ge 5 ]]; then
    pass "nova7-knowledge-base has $kb_count documents"
elif [[ "$kb_count" -gt 0 ]]; then
    warn "nova7-knowledge-base has only $kb_count documents (expected >= 5)"
elif [[ "$kb_count" -eq 0 ]]; then
    fail "nova7-knowledge-base is empty (run setup-agent-builder.sh)"
else
    fail "nova7-knowledge-base index not found (run setup-agent-builder.sh)"
fi
echo ""

# ── 5. Agent Builder ─────────────────────────────────────────────────────────
echo "--- Agent Builder ---"

# Check agents
agents_response=$(kb_get "/api/agent_builder/agents")
agents_code=$(echo "$agents_response" | tail -1)
agents_body=$(echo "$agents_response" | sed '$d')

if [[ "$agents_code" -ge 200 && "$agents_code" -lt 300 ]]; then
    agent_found=$(echo "$agents_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
agents = data if isinstance(data, list) else data.get('results', data.get('agents', data.get('data', [])))
found = any('nova7' in str(a).lower() or 'NOVA' in str(a) for a in (agents if isinstance(agents, list) else [agents]))
print('yes' if found else 'no')
" 2>/dev/null || echo "unknown")

    if [[ "$agent_found" == "yes" ]]; then
        pass "NOVA-7 agent found in Agent Builder"
    else
        warn "Agent Builder reachable but NOVA-7 agent not found"
    fi
else
    warn "Agent Builder API not accessible (HTTP $agents_code) — may need manual setup"
fi

# Check tools (filter for non-readonly custom tools)
tools_response=$(kb_get "/api/agent_builder/tools")
tools_code=$(echo "$tools_response" | tail -1)
tools_body=$(echo "$tools_response" | sed '$d')

if [[ "$tools_code" -ge 200 && "$tools_code" -lt 300 ]]; then
    tool_count=$(echo "$tools_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data if isinstance(data, list) else data.get('results', data.get('tools', data.get('data', [])))
custom = [t for t in tools if not t.get('readonly', False) and not t.get('is_default', False)]
print(len(custom))
" 2>/dev/null || echo "0")

    if [[ "$tool_count" -ge 7 ]]; then
        pass "Agent Builder has $tool_count custom tools (>= 7 expected)"
    elif [[ "$tool_count" -gt 0 ]]; then
        warn "Agent Builder has $tool_count custom tools (expected >= 7)"
    else
        warn "No custom tools found in Agent Builder"
    fi
else
    warn "Agent Builder tools API not accessible (HTTP $tools_code)"
fi
echo ""

# ── 6. Dashboard (serverless-compatible: uses _export, NOT _get/_find) ───────
echo "--- Executive Dashboard ---"
dash_response=$(kb_post "/api/saved_objects/_export" '{"objects":[{"type":"dashboard","id":"nova7-exec-dashboard"}],"includeReferencesDeep":false}')
dash_code=$(echo "$dash_response" | tail -1)
dash_body=$(echo "$dash_response" | sed '$d')

if [[ "$dash_code" -ge 200 && "$dash_code" -lt 300 ]]; then
    # Check the export response contains the dashboard (not just an error export)
    if echo "$dash_body" | grep -q "nova7-exec-dashboard" 2>/dev/null; then
        pass "NOVA-7 Executive Dashboard exists"
        info "URL: ${KIBANA_URL}/app/dashboards#/view/nova7-exec-dashboard"
    else
        warn "Export returned but dashboard ID not confirmed"
    fi
else
    fail "NOVA-7 Executive Dashboard not found (run setup-exec-dashboard.sh)"
fi
echo ""

# ── 7. Significant Events (Streams Queries) ─────────────────────────────────
echo "--- Significant Events (Streams Queries) ---"

# Discover stream name (same logic as setup-significant-events.sh)
se_stream=""
se_streams_out=$(kb_get "/api/streams" 2>/dev/null) || true
se_streams_code=$(echo "$se_streams_out" | tail -1)
se_streams_body=$(echo "$se_streams_out" | sed '$d')

if [[ "$se_streams_code" -ge 200 && "$se_streams_code" -lt 300 ]] && [[ -n "$se_streams_body" ]]; then
    se_stream=$(echo "$se_streams_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    streams = data if isinstance(data, list) else data.get('streams', data.get('results', data.get('data', [])))
    for s in streams:
        name = s.get('name', s) if isinstance(s, dict) else s
        if name == 'logs':
            print(name); exit(0)
except:
    pass
" 2>/dev/null || true)
fi

if [[ -z "$se_stream" ]]; then
    se_stream="logs"
fi

se_response=$(kb_get "/api/streams/${se_stream}/queries")
se_code=$(echo "$se_response" | tail -1)
se_body=$(echo "$se_response" | sed '$d')

if [[ "$se_code" -ge 200 && "$se_code" -lt 300 ]]; then
    se_count=$(echo "$se_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    queries = data if isinstance(data, list) else data.get('queries', data.get('results', data.get('data', [])))
    count = sum(1 for q in queries if q.get('id', '').startswith('nova7-se-'))
    print(count)
except:
    print('0')
" 2>/dev/null || echo "0")

    if [[ "$se_count" -ge 20 ]]; then
        pass "Significant Events: $se_count nova7-se-* queries on stream '${se_stream}'"
    elif [[ "$se_count" -gt 0 ]]; then
        warn "Significant Events: only $se_count queries found (expected >= 20)"
    else
        warn "No nova7-se-* queries found on stream '${se_stream}' (run setup-significant-events.sh)"
    fi
else
    warn "Streams Queries API not accessible (HTTP $se_code) — Streams may not be enabled"
fi
echo ""

# ── 8. Trace Data ─────────────────────────────────────────────────────────────
echo "--- Trace Data (APM Service Map) ---"

# Check for traces-* indices
traces_response=$(es_get "/_cat/indices/traces-*?format=json&h=index,docs.count")
traces_code=$(echo "$traces_response" | tail -1)
traces_body=$(echo "$traces_response" | sed '$d')

if [[ "$traces_code" -ge 200 && "$traces_code" -lt 300 ]]; then
    trace_indices=$(echo "$traces_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_docs = sum(int(idx.get('docs.count', 0)) for idx in data)
print(f'{len(data)} indices, {total_docs} docs')
" 2>/dev/null || echo "unknown")

    if echo "$traces_body" | python3 -c "import sys,json; data=json.load(sys.stdin); exit(0 if any(int(i.get('docs.count',0))>0 for i in data) else 1)" 2>/dev/null; then
        pass "Trace data exists ($trace_indices)"
    else
        info "Trace indices exist but are empty (run: python3 log_generators/trace_generator.py)"
    fi
else
    info "No traces-* indices found (run: python3 log_generators/trace_generator.py)"
fi
echo ""

# ── 9. Host Metrics ──────────────────────────────────────────────────────────
echo "--- Host Metrics (Infrastructure UI) ---"

# Check for metrics-* indices with system.* metric names
metrics_response=$(es_get "/_cat/indices/metrics-*?format=json&h=index,docs.count")
metrics_code=$(echo "$metrics_response" | tail -1)
metrics_body=$(echo "$metrics_response" | sed '$d')

if [[ "$metrics_code" -ge 200 && "$metrics_code" -lt 300 ]]; then
    metrics_info=$(echo "$metrics_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_docs = sum(int(idx.get('docs.count', 0)) for idx in data)
print(f'{len(data)} indices, {total_docs} docs')
" 2>/dev/null || echo "unknown")

    if echo "$metrics_body" | python3 -c "import sys,json; data=json.load(sys.stdin); exit(0 if any(int(i.get('docs.count',0))>0 for i in data) else 1)" 2>/dev/null; then
        pass "Metrics data exists ($metrics_info)"
    else
        info "Metrics indices exist but are empty (run: python3 log_generators/host_metrics_generator.py)"
    fi
else
    info "No metrics-* indices found (run: python3 log_generators/host_metrics_generator.py)"
fi
echo ""

# ── 10. Nginx Log Data ───────────────────────────────────────────────────────
echo "--- Nginx Log Generator Data ---"
nginx_access_count=$(get_count "logs-nginx.access.otel-default")
nginx_error_count=$(get_count "logs-nginx.error.otel-default")

if [[ "$nginx_access_count" -gt 0 ]]; then
    pass "logs-nginx.access.otel-default has $nginx_access_count docs"
else
    info "logs-nginx.access.otel-default not found (start: python3 log_generators/nginx_log_generator.py)"
fi

if [[ "$nginx_error_count" -gt 0 ]]; then
    pass "logs-nginx.error.otel-default has $nginx_error_count docs"
else
    info "logs-nginx.error.otel-default not yet populated"
fi
echo ""

# ── 11. MySQL Log Data ───────────────────────────────────────────────────────
echo "--- MySQL Log Generator Data ---"
mysql_slow_count=$(get_count "logs-mysql.slowlog.otel-default")
mysql_error_count=$(get_count "logs-mysql.error.otel-default")

if [[ "$mysql_slow_count" -gt 0 ]]; then
    pass "logs-mysql.slowlog.otel-default has $mysql_slow_count docs"
else
    info "logs-mysql.slowlog.otel-default not found (start: python3 log_generators/mysql_log_generator.py)"
fi

if [[ "$mysql_error_count" -gt 0 ]]; then
    pass "logs-mysql.error.otel-default has $mysql_error_count docs"
else
    info "logs-mysql.error.otel-default not yet populated"
fi
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "============================================================"
echo "   Results: ${PASS} PASS / ${FAIL} FAIL / ${WARN} WARN"
echo "============================================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Run the setup scripts to fix:"
    echo "  ./setup-all.sh"
    exit 1
elif [[ "$WARN" -gt 0 ]]; then
    echo ""
    echo "Some checks returned warnings. This is expected if generators"
    echo "haven't been started yet or if certain APIs are not available."
    exit 0
else
    echo ""
    echo "All checks passed!"
    exit 0
fi
