#!/usr/bin/env bash
#
# import.sh — Import all NOVA-7 Elastic configurations into an Elasticsearch cluster.
#
# Environment variables:
#   ELASTIC_URL     — Base URL of the Elasticsearch cluster (e.g. https://my-cluster.es.cloud:443)
#   ELASTIC_API_KEY — API key for authentication
#
# Options:
#   --dry-run       — Print what would be done without making any API calls
#
# Usage:
#   ELASTIC_URL=https://... ELASTIC_API_KEY=abc123 ./import.sh
#   ELASTIC_URL=https://... ELASTIC_API_KEY=abc123 ./import.sh --dry-run
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Parse flags ───────────────────────────────────────────────────────────────
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            ;;
        --help|-h)
            head -17 "$0" | tail -14
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ── Validate environment ─────────────────────────────────────────────────────
if [[ -z "${ELASTIC_URL:-}" ]]; then
    echo "ERROR: ELASTIC_URL environment variable is not set."
    echo "Usage: ELASTIC_URL=https://... ELASTIC_API_KEY=... $0 [--dry-run]"
    exit 1
fi

if [[ -z "${ELASTIC_API_KEY:-}" ]]; then
    echo "ERROR: ELASTIC_API_KEY environment variable is not set."
    echo "Usage: ELASTIC_URL=https://... ELASTIC_API_KEY=... $0 [--dry-run]"
    exit 1
fi

# Strip trailing slash from URL
ELASTIC_URL="${ELASTIC_URL%/}"

# ── Helpers ───────────────────────────────────────────────────────────────────
log_info()  { echo "[INFO]  $*"; }
log_ok()    { echo "[OK]    $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*"; }
log_dry()   { echo "[DRY]   $*"; }

# Execute a curl request against Elasticsearch.
# Usage: es_request <METHOD> <PATH> [<JSON_BODY>]
es_request() {
    local method="$1"
    local path="$2"
    local body="${3:-}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "curl -X $method ${ELASTIC_URL}${path}"
        if [[ -n "$body" ]]; then
            log_dry "  Body: $(echo "$body" | head -c 200)..."
        fi
        return 0
    fi

    local curl_args=(
        -s -w "\n%{http_code}"
        -X "$method"
        "${ELASTIC_URL}${path}"
        -H "Content-Type: application/json"
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}"
    )

    if [[ -n "$body" ]]; then
        curl_args+=(-d "$body")
    fi

    local response
    response=$(curl "${curl_args[@]}")

    local http_code
    http_code=$(echo "$response" | tail -1)
    local response_body
    response_body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        return 0
    else
        log_error "HTTP $http_code: $response_body"
        return 1
    fi
}

# ── Step 1: Verify cluster connectivity ──────────────────────────────────────
log_info "=========================================="
log_info "NOVA-7 Elastic Configuration Import"
log_info "=========================================="
log_info "Target: ${ELASTIC_URL}"
log_info "Dry run: ${DRY_RUN}"
log_info ""

if [[ "$DRY_RUN" == "false" ]]; then
    log_info "Verifying cluster connectivity..."
    if es_request GET "/"; then
        log_ok "Cluster is reachable."
    else
        log_error "Cannot reach cluster at ${ELASTIC_URL}. Aborting."
        exit 1
    fi
else
    log_dry "Would verify cluster connectivity at ${ELASTIC_URL}"
fi
echo ""

# ── Step 2: Create index patterns / index templates ──────────────────────────
log_info "--- Creating Index Templates ---"

# Index template for NOVA-7 telemetry logs
LOGS_TEMPLATE='{
  "index_patterns": ["logs"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs",
      "index.default_pipeline": "logs-default-pipeline"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" },
        "log.level": { "type": "keyword" },
        "service.name": { "type": "keyword" },
        "service.namespace": { "type": "keyword" },
        "error.type": { "type": "keyword" },
        "sensor.type": { "type": "keyword" },
        "vehicle_section": { "type": "keyword" },
        "launch.mission_id": { "type": "keyword" },
        "launch.phase": { "type": "keyword" },
        "system.subsystem": { "type": "keyword" },
        "system.status": { "type": "keyword" },
        "chaos.channel": { "type": "integer" },
        "chaos.fault_type": { "type": "keyword" },
        "exception.type": { "type": "keyword" },
        "exception.message": { "type": "text" },
        "exception.stacktrace": { "type": "text" },
        "cascade.source_channel": { "type": "integer" },
        "cascade.source_subsystem": { "type": "keyword" },
        "cloud.provider": { "type": "keyword" },
        "cloud.platform": { "type": "keyword" },
        "cloud.region": { "type": "keyword" },
        "cloud.availability_zone": { "type": "keyword" },
        "host.name": { "type": "keyword" },
        "data_stream.type": { "type": "constant_keyword", "value": "logs" },
        "data_stream.dataset": { "type": "constant_keyword", "value": "generic" },
        "data_stream.namespace": { "type": "constant_keyword", "value": "default" }
      }
    }
  },
  "priority": 200,
  "composed_of": [],
  "_meta": {
    "description": "NOVA-7 Launch Telemetry Logs — index template for all OTel log data",
    "mission_id": "NOVA-7"
  }
}'

log_info "Creating index template: nova7-logs-template"
es_request PUT "/_index_template/nova7-logs-template" "$LOGS_TEMPLATE" && \
    log_ok "Index template nova7-logs-template created." || \
    log_warn "Failed to create nova7-logs-template (may already exist)."

# Metrics index template
METRICS_TEMPLATE='{
  "index_patterns": ["metrics-generic-default"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "metrics"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "service.name": { "type": "keyword" },
        "service.namespace": { "type": "keyword" },
        "launch.mission_id": { "type": "keyword" },
        "launch.phase": { "type": "keyword" },
        "system.subsystem": { "type": "keyword" },
        "cloud.provider": { "type": "keyword" },
        "cloud.region": { "type": "keyword" }
      }
    }
  },
  "priority": 200,
  "_meta": {
    "description": "NOVA-7 Launch Telemetry Metrics",
    "mission_id": "NOVA-7"
  }
}'

log_info "Creating index template: nova7-metrics-template"
es_request PUT "/_index_template/nova7-metrics-template" "$METRICS_TEMPLATE" && \
    log_ok "Index template nova7-metrics-template created." || \
    log_warn "Failed to create nova7-metrics-template (may already exist)."

# Traces index template
TRACES_TEMPLATE='{
  "index_patterns": ["traces-generic-default"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "traces"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "service.name": { "type": "keyword" },
        "service.namespace": { "type": "keyword" },
        "trace.id": { "type": "keyword" },
        "span.id": { "type": "keyword" },
        "parent.id": { "type": "keyword" },
        "launch.mission_id": { "type": "keyword" },
        "launch.phase": { "type": "keyword" },
        "system.subsystem": { "type": "keyword" },
        "cloud.provider": { "type": "keyword" },
        "cloud.region": { "type": "keyword" }
      }
    }
  },
  "priority": 200,
  "_meta": {
    "description": "NOVA-7 Launch Telemetry Traces",
    "mission_id": "NOVA-7"
  }
}'

log_info "Creating index template: nova7-traces-template"
es_request PUT "/_index_template/nova7-traces-template" "$TRACES_TEMPLATE" && \
    log_ok "Index template nova7-traces-template created." || \
    log_warn "Failed to create nova7-traces-template (may already exist)."

echo ""

# ── Step 3: Import Significant Event ES|QL rules ────────────────────────────
log_info "--- Importing Significant Event ES|QL Rules ---"

CHANNEL_NAMES=(
    "Thermal Calibration Drift"
    "Fuel Pressure Anomaly"
    "Oxidizer Flow Rate Deviation"
    "GPS Multipath Interference"
    "IMU Synchronization Loss"
    "Star Tracker Alignment Fault"
    "S-Band Signal Degradation"
    "X-Band Packet Loss"
    "UHF Antenna Pointing Error"
    "Payload Thermal Excursion"
    "Payload Vibration Anomaly"
    "Cross-Cloud Relay Latency"
    "Relay Packet Corruption"
    "Ground Power Bus Fault"
    "Weather Station Data Gap"
    "Pad Hydraulic Pressure Loss"
    "Sensor Validation Pipeline Stall"
    "Calibration Epoch Mismatch"
    "Flight Termination System Check Failure"
    "Range Safety Tracking Loss"
)

CHANNEL_SUBSYSTEMS=(
    "propulsion"
    "propulsion"
    "propulsion"
    "guidance"
    "guidance"
    "guidance"
    "communications"
    "communications"
    "communications"
    "payload"
    "payload"
    "relay"
    "relay"
    "ground"
    "ground"
    "ground"
    "validation"
    "validation"
    "safety"
    "safety"
)

CHANNEL_SEVERITIES=(
    "high"
    "critical"
    "high"
    "high"
    "critical"
    "medium"
    "high"
    "high"
    "medium"
    "high"
    "critical"
    "medium"
    "medium"
    "high"
    "medium"
    "high"
    "high"
    "medium"
    "critical"
    "critical"
)

ESQL_FILES=( "$SCRIPT_DIR"/significant-events/channel_*.esql )

import_count=0
fail_count=0

for esql_file in "${ESQL_FILES[@]}"; do
    if [[ ! -f "$esql_file" ]]; then
        log_warn "No ES|QL files found in $SCRIPT_DIR/significant-events/"
        break
    fi

    filename=$(basename "$esql_file")
    # Extract channel number from filename (e.g., channel_01_... -> 1)
    channel_num=$(echo "$filename" | sed 's/channel_0*\([0-9]*\)_.*/\1/')
    channel_idx=$((channel_num - 1))

    channel_name="${CHANNEL_NAMES[$channel_idx]}"
    channel_subsystem="${CHANNEL_SUBSYSTEMS[$channel_idx]}"
    channel_severity="${CHANNEL_SEVERITIES[$channel_idx]}"

    # Read and escape the ES|QL query for JSON embedding
    esql_query=$(cat "$esql_file" | tr '\n' ' ' | sed 's/  */ /g' | sed 's/^ //;s/ $//')
    esql_query_escaped=$(echo "$esql_query" | sed 's/"/\\"/g')

    rule_id="nova7-se-channel-$(printf '%02d' "$channel_num")"

    RULE_BODY=$(cat <<ENDJSON
{
  "rule_id": "${rule_id}",
  "name": "NOVA-7 CH${channel_num}: ${channel_name}",
  "description": "Significant event detection for NOVA-7 channel ${channel_num} — ${channel_name}. Triggers when error count exceeds threshold for the ${channel_subsystem} subsystem.",
  "type": "esql",
  "query": "${esql_query_escaped}",
  "severity": "${channel_severity}",
  "risk_score": $((channel_num * 5)),
  "interval": "1m",
  "enabled": true,
  "tags": ["nova7", "launch-anomaly", "${channel_subsystem}", "channel-${channel_num}"],
  "meta": {
    "mission_id": "NOVA-7",
    "channel": ${channel_num},
    "subsystem": "${channel_subsystem}"
  },
  "actions": [
    {
      "action_type": "webhook",
      "params": {
        "body": "{\"channel\": ${channel_num}, \"name\": \"${channel_name}\", \"subsystem\": \"${channel_subsystem}\", \"severity\": \"${channel_severity}\"}"
      }
    }
  ]
}
ENDJSON
)

    log_info "Importing rule: ${rule_id} — ${channel_name}"
    if es_request PUT "/_security/significant_events/rules/${rule_id}" "$RULE_BODY"; then
        log_ok "Rule ${rule_id} imported."
        import_count=$((import_count + 1))
    else
        log_warn "Failed to import rule ${rule_id}. Continuing..."
        fail_count=$((fail_count + 1))
    fi
done

log_info "Significant events: ${import_count} imported, ${fail_count} failed."
echo ""

# ── Step 4: Import AI Agent configuration ────────────────────────────────────
log_info "--- Importing AI Agent Configuration ---"

if [[ -f "$SCRIPT_DIR/agent/launch-anomaly-agent.json" ]]; then
    AGENT_CONFIG=$(cat "$SCRIPT_DIR/agent/launch-anomaly-agent.json")
    log_info "Importing agent: NOVA-7 Launch Anomaly Analyst"
    es_request PUT "/_inference/agent/nova7-launch-anomaly-analyst" "$AGENT_CONFIG" && \
        log_ok "Agent configuration imported." || \
        log_warn "Failed to import agent configuration."
else
    log_warn "Agent config not found: $SCRIPT_DIR/agent/launch-anomaly-agent.json"
fi
echo ""

# ── Step 5: Import Tool definitions ──────────────────────────────────────────
log_info "--- Importing Tool Definitions ---"

for tool_file in "$SCRIPT_DIR"/tools/*.json; do
    if [[ ! -f "$tool_file" ]]; then
        log_warn "No tool definitions found in $SCRIPT_DIR/tools/"
        break
    fi

    tool_name=$(basename "$tool_file" .json)
    tool_body=$(cat "$tool_file")

    log_info "Importing tool: ${tool_name}"
    es_request PUT "/_inference/agent/nova7-launch-anomaly-analyst/tools/${tool_name}" "$tool_body" && \
        log_ok "Tool ${tool_name} imported." || \
        log_warn "Failed to import tool ${tool_name}."
done
echo ""

# ── Step 6: Import Streams configuration ─────────────────────────────────────
log_info "--- Importing Streams Configuration ---"

if [[ -f "$SCRIPT_DIR/streams/streams-config.json" ]]; then
    STREAMS_CONFIG=$(cat "$SCRIPT_DIR/streams/streams-config.json")
    log_info "Importing streams configuration"
    es_request PUT "/_streams/nova7-telemetry" "$STREAMS_CONFIG" && \
        log_ok "Streams configuration imported." || \
        log_warn "Failed to import streams configuration."
else
    log_warn "Streams config not found: $SCRIPT_DIR/streams/streams-config.json"
fi
echo ""

# ── Step 7: Import Knowledge Base documents ──────────────────────────────────
log_info "--- Importing Knowledge Base Documents ---"

KB_INDEX="nova7-knowledge-base"

# Create the knowledge base index if it does not exist
KB_INDEX_BODY='{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "title": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "content": { "type": "text" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "mission_id": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}'

log_info "Ensuring knowledge base index: ${KB_INDEX}"
es_request PUT "/${KB_INDEX}" "$KB_INDEX_BODY" && \
    log_ok "Knowledge base index created." || \
    log_warn "Knowledge base index may already exist."

kb_count=0
for kb_file in "$SCRIPT_DIR"/knowledge-base/*.md; do
    if [[ ! -f "$kb_file" ]]; then
        log_warn "No knowledge base docs found in $SCRIPT_DIR/knowledge-base/"
        break
    fi

    kb_name=$(basename "$kb_file" .md)
    kb_content=$(cat "$kb_file" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || cat "$kb_file" | sed 's/"/\\"/g; s/$/\\n/' | tr -d '\n')

    # Extract title from first markdown heading
    kb_title=$(head -1 "$kb_file" | sed 's/^#* *//')

    KB_DOC=$(cat <<ENDJSON
{
  "title": "${kb_title}",
  "content": ${kb_content},
  "category": "launch-anomaly",
  "tags": ["nova7", "${kb_name}"],
  "mission_id": "NOVA-7",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
ENDJSON
)

    log_info "Importing KB doc: ${kb_name}"
    es_request PUT "/${KB_INDEX}/_doc/${kb_name}" "$KB_DOC" && \
        log_ok "KB doc ${kb_name} imported." || \
        log_warn "Failed to import KB doc ${kb_name}."
    kb_count=$((kb_count + 1))
done

log_info "Knowledge base: ${kb_count} documents processed."
echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
log_info "=========================================="
log_info "Import complete."
log_info "=========================================="
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "This was a dry run. No changes were made."
fi
