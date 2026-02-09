#!/usr/bin/env bash
#
# setup-alerting.sh — Create NOVA-7 alert rules with webhook connector
# targeting the Significant Event Notification workflow.
#
# Creates:
#   1. A webhook connector pointing to the workflow run endpoint
#   2. 20 alert rules (one per fault channel) using .es-query rule type
#
# API reference:
#   POST /api/actions/connector          — Create connector
#   POST /api/alerting/rule              — Create alert rule
#   GET  /api/alerting/rules/_find       — List alert rules
#   DELETE /api/alerting/rule/{id}       — Delete alert rule
#   POST /api/workflows/search           — Search workflows
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
log_info "NOVA-7 Alerting Rules Setup"
log_info "=========================================="
log_info "Kibana: ${KIBANA_URL}"
echo ""

# ── Step 1: Discover workflow ID ──────────────────────────────────────────────
log_info "--- Step 1: Discover Significant Event Notification workflow ---"

WORKFLOW_ID=""

if wf_search=$(kb_request POST "/api/workflows/search" '{"page":1,"size":100}' 2>&1); then
    WORKFLOW_ID=$(echo "$wf_search" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
    for item in items:
        name = item.get('name', '')
        if 'Significant Event Notification' in name:
            print(item['id'])
            break
except:
    pass
" 2>/dev/null || true)
fi

if [[ -z "$WORKFLOW_ID" ]]; then
    log_error "Could not find 'Significant Event Notification' workflow."
    log_info "Make sure setup-workflows.sh has been run first."
    exit 1
fi

log_ok "Workflow ID: ${WORKFLOW_ID}"
echo ""

# ── Step 2: Clean old NOVA-7 connectors & create webhook connector ───────────
log_info "--- Step 2: Clean old NOVA-7 connectors ---"

# Delete any existing NOVA-7 connectors to avoid duplicates
old_deleted=0
if connectors_out=$(kb_request GET "/api/actions/connectors" 2>/dev/null); then
    old_connector_ids=$(echo "$connectors_out" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for c in data:
        if 'NOVA-7' in c.get('name', ''):
            print(c['id'])
except:
    pass
" 2>/dev/null || true)

    while IFS= read -r cid; do
        if [[ -n "$cid" ]]; then
            if kb_request DELETE "/api/actions/connector/${cid}" > /dev/null 2>&1; then
                old_deleted=$((old_deleted + 1))
            fi
        fi
    done <<< "$old_connector_ids"
fi

if [[ "$old_deleted" -gt 0 ]]; then
    log_ok "Deleted $old_deleted existing NOVA-7 connector(s)."
else
    log_info "No existing NOVA-7 connectors to clean."
fi

log_info "Creating webhook connector..."

CONNECTOR_BODY=$(python3 -c "
import json
body = {
    'connector_type_id': '.webhook',
    'name': 'NOVA-7 Significant Event Workflow',
    'config': {
        'url': '${KIBANA_URL}/api/workflows/${WORKFLOW_ID}/run',
        'method': 'post',
        'headers': {
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true',
            'x-elastic-internal-origin': 'kibana'
        },
        'hasAuth': True
    },
    'secrets': {
        'user': 'elastic',
        'password': '${ELASTIC_API_KEY}'
    }
}
print(json.dumps(body))
")

CONNECTOR_ID=""

if connector_result=$(kb_request POST "/api/actions/connector" "$CONNECTOR_BODY" 2>&1); then
    CONNECTOR_ID=$(echo "$connector_result" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    pass
" 2>/dev/null || true)
fi

if [[ -z "$CONNECTOR_ID" ]]; then
    log_error "Failed to create webhook connector."
    exit 1
fi

log_ok "Connector ID: ${CONNECTOR_ID}"
echo ""

# ── Step 3: Clean existing nova7-alert-* rules ───────────────────────────────
log_info "--- Step 3: Clean existing nova7-alert-* rules ---"

deleted=0
page=1

while true; do
    rules_out=$(kb_request GET "/api/alerting/rules/_find?per_page=100&page=${page}&filter=alert.attributes.tags:nova7" 2>/dev/null) || break

    rule_ids=$(echo "$rules_out" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rules = data.get('data', [])
    for r in rules:
        name = r.get('name', '')
        if name.startswith('NOVA-7 CH'):
            print(r['id'])
except:
    pass
" 2>/dev/null || true)

    if [[ -z "$rule_ids" ]]; then
        break
    fi

    while IFS= read -r rid; do
        if [[ -n "$rid" ]]; then
            if kb_request DELETE "/api/alerting/rule/${rid}" > /dev/null 2>&1; then
                deleted=$((deleted + 1))
            fi
        fi
    done <<< "$rule_ids"

    page=$((page + 1))
    # Safety: don't loop forever
    if [[ "$page" -gt 10 ]]; then
        break
    fi
done

if [[ "$deleted" -gt 0 ]]; then
    log_ok "Deleted $deleted existing NOVA-7 alert rules."
else
    log_info "No existing NOVA-7 alert rules to clean."
fi
echo ""

# ── Step 4: Create 20 alert rules ────────────────────────────────────────────
log_info "--- Step 4: Create alert rules ---"

# Channel data: NUM|NAME|SUBSYSTEM|ERROR_TYPE|SENSOR_TYPE|VEHICLE_SECTION
CHANNELS=(
    "01|Thermal Calibration Drift|propulsion|ThermalCalibrationException|thermal|engine_bay"
    "02|Fuel Pressure Anomaly|propulsion|FuelPressureException|pressure|fuel_tanks"
    "03|Oxidizer Flow Rate Deviation|propulsion|OxidizerFlowException|flow_rate|engine_bay"
    "04|GPS Multipath Interference|guidance|GPSMultipathException|gps|avionics"
    "05|IMU Synchronization Loss|guidance|IMUSyncException|imu|avionics"
    "06|Star Tracker Alignment Fault|guidance|StarTrackerAlignmentException|star_tracker|avionics"
    "07|S-Band Signal Degradation|communications|SignalDegradationException|rf_signal|antenna_array"
    "08|X-Band Packet Loss|communications|PacketLossException|packet_integrity|antenna_array"
    "09|UHF Antenna Pointing Error|communications|AntennaPointingException|antenna_position|antenna_array"
    "10|Payload Thermal Excursion|payload|PayloadThermalException|thermal|payload_bay"
    "11|Payload Vibration Anomaly|payload|PayloadVibrationException|vibration|payload_bay"
    "12|Cross-Cloud Relay Latency|relay|RelayLatencyException|network_latency|ground_network"
    "13|Relay Packet Corruption|relay|PacketCorruptionException|data_integrity|ground_network"
    "14|Ground Power Bus Fault|ground|PowerBusFaultException|electrical|launch_pad"
    "15|Weather Station Data Gap|ground|WeatherDataGapException|weather|launch_pad"
    "16|Pad Hydraulic Pressure Loss|ground|HydraulicPressureException|hydraulic|launch_pad"
    "17|Sensor Validation Pipeline Stall|validation|ValidationPipelineException|pipeline_health|ground_network"
    "18|Calibration Epoch Mismatch|validation|CalibrationEpochException|calibration|ground_network"
    "19|FTS Check Failure|safety|FTSCheckException|safety_system|vehicle_wide"
    "20|Range Safety Tracking Loss|safety|TrackingLossException|radar_tracking|vehicle_wide"
)

created=0
failed=0

for ch in "${CHANNELS[@]}"; do
    IFS='|' read -r num name subsystem error_type sensor_type vehicle_section <<< "$ch"

    # Determine severity
    case "$num" in
        19|20) severity="critical" ;;
        01|02|03|04|05|06) severity="high" ;;
        *) severity="medium" ;;
    esac

    rule_name="NOVA-7 CH${num}: ${name}"
    log_info "Creating rule: ${rule_name} [${severity}]"

    # Build the rule JSON with Python for safe escaping
    rule_json=$(python3 -c "
import json

num = '${num}'
name = '''${name}'''
subsystem = '${subsystem}'
error_type = '${error_type}'
sensor_type = '${sensor_type}'
vehicle_section = '${vehicle_section}'
severity = '${severity}'
connector_id = '${CONNECTOR_ID}'
channel_int = int(num)

es_query = json.dumps({
    'query': {
        'bool': {
            'filter': [
                {'range': {'@timestamp': {'gte': 'now-1m'}}},
                {'match_phrase': {'body.text': error_type}},
                {'term': {'severity_text': 'ERROR'}}
            ]
        }
    }
})

action_body = json.dumps({
    'channel': channel_int,
    'error_type': error_type,
    'subsystem': subsystem,
    'severity': severity
})

rule = {
    'name': f'NOVA-7 CH{num}: {name}',
    'rule_type_id': '.es-query',
    'consumer': 'alerts',
    'tags': ['nova7', f'ch{num}', subsystem],
    'schedule': {'interval': '1m'},
    'params': {
        'searchType': 'esQuery',
        'esQuery': es_query,
        'index': ['logs*'],
        'timeField': '@timestamp',
        'threshold': [0],
        'thresholdComparator': '>',
        'size': 100,
        'timeWindowSize': 1,
        'timeWindowUnit': 'm'
    },
    'actions': [{
        'group': 'query matched',
        'id': connector_id,
        'frequency': {
            'summary': False,
            'notify_when': 'onActiveAlert',
            'throttle': None
        },
        'params': {
            'body': action_body
        }
    }]
}

print(json.dumps(rule))
")

    if kb_request POST "/api/alerting/rule" "$rule_json" > /dev/null 2>&1; then
        log_ok "  Created: ${rule_name}"
        created=$((created + 1))
    else
        log_warn "  Failed: ${rule_name}"
        failed=$((failed + 1))
    fi
done

echo ""
log_info "Rules created: ${created}, failed: ${failed}"
echo ""

# ── Step 5: Verify ───────────────────────────────────────────────────────────
log_info "--- Step 5: Verify ---"

if verify_out=$(kb_request GET "/api/alerting/rules/_find?per_page=100&filter=alert.attributes.tags:nova7" 2>/dev/null); then
    rule_count=$(echo "$verify_out" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rules = data.get('data', [])
    count = sum(1 for r in rules if r.get('name', '').startswith('NOVA-7 CH'))
    print(count)
except:
    print('0')
" 2>/dev/null || echo "0")

    if [[ "$rule_count" -ge 20 ]]; then
        log_ok "Verified: $rule_count NOVA-7 alert rules found."
    elif [[ "$rule_count" -gt 0 ]]; then
        log_warn "Only $rule_count NOVA-7 alert rules found (expected 20)."
    else
        log_warn "No NOVA-7 alert rules found in verification."
    fi
else
    log_warn "Could not verify alert rules."
fi

echo ""
log_info "=========================================="
log_info "NOVA-7 Alerting setup complete."
log_info "  Connector: ${CONNECTOR_ID}"
log_info "  Workflow:  ${WORKFLOW_ID}"
log_info "  Rules:     ${created} created"
log_info "=========================================="
