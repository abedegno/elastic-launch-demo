#!/usr/bin/env bash
#
# setup-significant-events.sh — Create NOVA-7 Significant Event definitions
# via the Kibana Streams Queries API.
#
# Creates 20 Streams query definitions (one per chaos fault channel) that
# detect specific error patterns in logs. These power
# the Significant Events tab in the Kibana Streams UI.
#
# API reference (Technical Preview, added 9.2.0):
#   POST /api/streams/_enable              — Enable Streams
#   GET  /api/streams                      — List streams
#   POST /api/streams/{name}/queries/_bulk — Bulk create/update queries
#   GET  /api/streams/{name}/queries       — List queries on a stream
#   DELETE /api/streams/{name}/queries/{id} — Delete a query
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Load environment ──────────────────────────────────────────────────────────
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ── Validate environment ─────────────────────────────────────────────────────
for var in KIBANA_URL ELASTIC_API_KEY; do
    if [[ -z "${!var:-}" ]]; then
        echo "ERROR: $var is not set. Check your .env file."
        exit 1
    fi
done

KIBANA_URL="${KIBANA_URL%/}"

# ── Helpers ───────────────────────────────────────────────────────────────────
log_info()  { echo "[INFO]  $*"; }
log_ok()    { echo "[OK]    $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*"; }

# Kibana API helper — returns body on success, logs error on failure
kb_request() {
    local method="$1" path="$2" body="${3:-}"

    local curl_args=(
        -s -w "\n%{http_code}"
        -X "$method"
        "${KIBANA_URL}${path}"
        -H "Content-Type: application/json"
        -H "kbn-xsrf: true"
        -H "x-elastic-internal-origin: kibana"
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
        echo "$response_body"
        return 0
    else
        log_error "HTTP $http_code on $method $path: $(echo "$response_body" | head -c 500)"
        return 1
    fi
}

echo ""
log_info "=========================================="
log_info "NOVA-7 Significant Events Setup"
log_info "=========================================="
log_info "Kibana: ${KIBANA_URL}"
echo ""

# ── Step 1: Enable Streams ───────────────────────────────────────────────────
log_info "--- Step 1: Enable Streams ---"

if kb_request POST "/api/streams/_enable" '{}' > /dev/null 2>&1; then
    log_ok "Streams enabled (or already enabled)."
else
    log_warn "Could not enable Streams (may already be enabled or API unavailable)."
    log_info "Continuing — Streams may have been enabled via the UI."
fi
echo ""

# ── Step 2: Discover stream name ─────────────────────────────────────────────
log_info "--- Step 2: Discover target stream ---"

STREAM_NAME=""

streams_out=$(kb_request GET "/api/streams" 2>/dev/null) || true

if [[ -n "$streams_out" ]]; then
    # Try to find the 'logs' stream (root stream where service logs are routed)
    STREAM_NAME=$(echo "$streams_out" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    streams = data if isinstance(data, list) else data.get('streams', data.get('results', data.get('data', [])))

    # Prefer exact match for 'logs' (root stream)
    for s in streams:
        name = s.get('name', s) if isinstance(s, dict) else s
        if name == 'logs':
            print(name)
            sys.exit(0)

    # Fall back to any stream with 'log' in name
    for s in streams:
        name = s.get('name', s) if isinstance(s, dict) else s
        if 'log' in str(name).lower():
            print(name)
            sys.exit(0)

    # Last resort: first stream
    if streams:
        s = streams[0]
        name = s.get('name', s) if isinstance(s, dict) else s
        print(name)
except Exception as e:
    pass
" 2>/dev/null || true)
fi

if [[ -z "$STREAM_NAME" ]]; then
    # Default to 'logs' — the standard wired root stream
    STREAM_NAME="logs"
    log_warn "Could not discover stream name, defaulting to: ${STREAM_NAME}"
else
    log_ok "Target stream: ${STREAM_NAME}"
fi
echo ""

# ── Step 3: Clean existing queries ───────────────────────────────────────────
log_info "--- Step 3: Clean existing nova7-se-* queries ---"

existing_queries=$(kb_request GET "/api/streams/${STREAM_NAME}/queries" 2>/dev/null) || true
deleted=0

if [[ -n "$existing_queries" ]]; then
    # Extract IDs of existing nova7-se-* queries
    nova7_ids=$(echo "$existing_queries" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    queries = data if isinstance(data, list) else data.get('queries', data.get('results', data.get('data', [])))
    for q in queries:
        qid = q.get('id', '')
        if qid.startswith('nova7-se-'):
            print(qid)
except:
    pass
" 2>/dev/null || true)

    if [[ -n "$nova7_ids" ]]; then
        while IFS= read -r qid; do
            if [[ -n "$qid" ]]; then
                if kb_request DELETE "/api/streams/${STREAM_NAME}/queries/${qid}" > /dev/null 2>&1; then
                    deleted=$((deleted + 1))
                fi
            fi
        done <<< "$nova7_ids"
    fi
fi

if [[ "$deleted" -gt 0 ]]; then
    log_ok "Deleted $deleted existing nova7-se-* queries."
else
    log_info "No existing nova7-se-* queries to clean."
fi
echo ""

# ── Step 4: Build bulk operations JSON ───────────────────────────────────────
log_info "--- Step 4: Build & send bulk operations ---"

# Channel data from app/config.py CHANNEL_REGISTRY
# Format: CH_NUM|NAME|SUBSYSTEM|ERROR_TYPE|SENSOR_TYPE|VEHICLE_SECTION
CHANNELS=(
    "01|Thermal Calibration Drift|Propulsion|ThermalCalibrationException|thermal|engine_bay"
    "02|Fuel Pressure Anomaly|Propulsion|FuelPressureException|pressure|fuel_tanks"
    "03|Oxidizer Flow Rate Deviation|Propulsion|OxidizerFlowException|flow_rate|engine_bay"
    "04|GPS Multipath Interference|Guidance|GPSMultipathException|gps|avionics"
    "05|IMU Synchronization Loss|Guidance|IMUSyncException|imu|avionics"
    "06|Star Tracker Alignment Fault|Guidance|StarTrackerAlignmentException|star_tracker|avionics"
    "07|S-Band Signal Degradation|Communications|SignalDegradationException|rf_signal|antenna_array"
    "08|X-Band Packet Loss|Communications|PacketLossException|packet_integrity|antenna_array"
    "09|UHF Antenna Pointing Error|Communications|AntennaPointingException|antenna_position|antenna_array"
    "10|Payload Thermal Excursion|Payload|PayloadThermalException|thermal|payload_bay"
    "11|Payload Vibration Anomaly|Payload|PayloadVibrationException|vibration|payload_bay"
    "12|Cross-Cloud Relay Latency|Relay|RelayLatencyException|network_latency|ground_network"
    "13|Relay Packet Corruption|Relay|PacketCorruptionException|data_integrity|ground_network"
    "14|Ground Power Bus Fault|Ground|PowerBusFaultException|electrical|launch_pad"
    "15|Weather Station Data Gap|Ground|WeatherDataGapException|weather|launch_pad"
    "16|Pad Hydraulic Pressure Loss|Ground|HydraulicPressureException|hydraulic|launch_pad"
    "17|Sensor Validation Pipeline Stall|Validation|ValidationPipelineException|pipeline_health|ground_network"
    "18|Calibration Epoch Mismatch|Validation|CalibrationEpochException|calibration|ground_network"
    "19|FTS Check Failure|Safety|FTSCheckException|safety_system|vehicle_wide"
    "20|Range Safety Tracking Loss|Safety|TrackingLossException|radar_tracking|vehicle_wide"
)

# Build bulk operations JSON using Python for safe JSON construction
# The Streams Queries API requires a `kql` object with a KQL query string.
BULK_JSON=$(python3 -c "
import json

channels = [
$(for ch in "${CHANNELS[@]}"; do
    IFS='|' read -r num name subsystem error_type sensor_type vehicle_section <<< "$ch"
    echo "    ('$num', '$name', '$subsystem', '$error_type', '$sensor_type', '$vehicle_section'),"
done)
]

operations = []
for num, name, subsystem, error_type, sensor_type, vehicle_section in channels:
    kql_query = f'body.text: \"{error_type}\" AND severity_text: \"ERROR\"'
    op = {
        'index': {
            'id': f'nova7-se-ch{num}',
            'title': f'Channel {num}: {name}',
            'kql': {
                'query': kql_query
            }
        }
    }
    operations.append(op)

print(json.dumps({'operations': operations}))
")

if [[ -z "$BULK_JSON" ]]; then
    log_error "Failed to build bulk operations JSON."
    exit 1
fi

log_info "Built 20 query operations."

# ── Step 5: POST bulk ────────────────────────────────────────────────────────
log_info "Sending bulk create to /api/streams/${STREAM_NAME}/queries/_bulk ..."

if bulk_result=$(kb_request POST "/api/streams/${STREAM_NAME}/queries/_bulk" "$BULK_JSON" 2>&1); then
    log_ok "Bulk create succeeded."
    # Show summary of response
    echo "$bulk_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                print(f'  {key}: {len(val)} items')
            elif isinstance(val, (int, float)):
                print(f'  {key}: {val}')
except:
    pass
" 2>/dev/null || true
else
    log_error "Bulk create failed. Response:"
    echo "$bulk_result" | head -c 500
    echo ""
    log_info ""
    log_info "Troubleshooting:"
    log_info "  1. Check that Streams is enabled in your Kibana deployment"
    log_info "  2. Try enabling Streams via UI: ${KIBANA_URL}/app/streams"
    log_info "  3. The Streams API is Technical Preview (requires Kibana 9.2.0+)"
    exit 1
fi
echo ""

# ── Step 6: Verify ───────────────────────────────────────────────────────────
log_info "--- Step 6: Verify ---"

if verify_out=$(kb_request GET "/api/streams/${STREAM_NAME}/queries" 2>/dev/null); then
    nova7_count=$(echo "$verify_out" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    queries = data if isinstance(data, list) else data.get('queries', data.get('results', data.get('data', [])))
    count = sum(1 for q in queries if q.get('id', '').startswith('nova7-se-'))
    print(count)
except:
    print('0')
" 2>/dev/null || echo "0")

    if [[ "$nova7_count" -ge 20 ]]; then
        log_ok "Verified: $nova7_count nova7-se-* queries found (expected 20)."
    elif [[ "$nova7_count" -gt 0 ]]; then
        log_warn "Only $nova7_count nova7-se-* queries found (expected 20)."
    else
        log_warn "No nova7-se-* queries found in verification."
    fi
else
    log_warn "Could not verify queries (GET request failed)."
fi

echo ""
log_info "=========================================="
log_info "Significant Events setup complete."
log_info "  Stream:  ${STREAM_NAME}"
log_info "  Queries: 20 channels"
log_info "=========================================="
