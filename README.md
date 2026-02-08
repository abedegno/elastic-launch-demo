# NOVA-7 Launch Demo

**A multi-cloud space launch simulation that demonstrates Elastic Observability with OpenTelemetry, AI-powered anomaly detection, and automated remediation.**

NOVA-7 simulates a space launch mission running nine microservices across AWS, GCP, and Azure. Each service emits real OpenTelemetry telemetry (logs, metrics, traces) through an OTel Collector into Elastic. A 20-channel chaos system injects realistic faults that Elastic detects, an AI agent investigates, and automated workflows resolve.

---

## Architecture

```
                          NOVA-7 Launch Demo
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │  ┌─────────────────── AWS us-east-1 ───────────────────┐    │
   │  │  mission-control   fuel-system   ground-systems      │    │
   │  │  (command)         (propulsion)  (ground)            │    │
   │  └─────────────────────────────────────────────────────┘    │
   │                                                              │
   │  ┌─────────────────── GCP us-central1 ─────────────────┐    │
   │  │  navigation     comms-array     payload-monitor      │    │
   │  │  (guidance)     (comms)         (payload)            │    │
   │  └─────────────────────────────────────────────────────┘    │
   │                                                              │
   │  ┌─────────────────── Azure eastus ────────────────────┐    │
   │  │  sensor-validator   telemetry-relay   range-safety   │    │
   │  │  (validation)       (relay)           (safety)       │    │
   │  └─────────────────────────────────────────────────────┘    │
   │                                                              │
   │  ┌──────────┐    OTLP/HTTP     ┌────────────────────┐      │
   │  │ FastAPI   │ ───────────────> │ OTel Collector     │      │
   │  │ :8080     │                  │ :4317 gRPC         │      │
   │  │           │                  │ :4318 HTTP         │      │
   │  └──────────┘                  └────────┬───────────┘      │
   │       │                                  │                   │
   └───────│──────────────────────────────────│───────────────────┘
           │                                  │
           │ WebSocket + REST                 │ HTTPS / Elastic
           │                                  │ exporter
           ▼                                  ▼
   ┌──────────────┐               ┌──────────────────────┐
   │  Dashboard    │               │  Elastic Cloud       │
   │  Chaos UI     │               │  ┌────────────────┐  │
   │  Browser      │               │  │ Elasticsearch   │  │
   └──────────────┘               │  │ Kibana          │  │
                                   │  │ AI Assistant    │  │
   ┌──────────────┐               │  │ Rules / Alerts  │  │
   │ Notifications │               │  │ Workflows       │  │
   │  Slack        │               │  └────────────────┘  │
   │  Twilio SMS   │               └──────────────────────┘
   │  Twilio Voice │
   └──────────────┘
```

## Key Features

- **9 simulated microservices** spread across 3 cloud providers (AWS, GCP, Azure)
- **Real OpenTelemetry telemetry** — logs, metrics, and traces via OTLP
- **20 independent fault channels** covering propulsion, guidance, communications, payload, relay, ground, validation, and safety subsystems
- **Cascade effects** — primary faults propagate warnings to dependent services
- **Live dashboard** with real-time WebSocket updates
- **Chaos controller UI** for triggering and resolving faults during demos
- **Elastic integration** — significant event detection with ES|QL rules
- **AI agent investigation** — automated root cause analysis
- **Automated remediation** via Elastic workflows
- **Notifications** — Slack webhooks, Twilio SMS, and voice calls

---

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- An Elastic Cloud deployment (or self-hosted Elasticsearch 8.x+)

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set ELASTIC_ENDPOINT and ELASTIC_API_KEY at minimum
```

### 3. Deploy

```bash
./setup.sh
```

### 4. Open

| URL | Description |
|-----|-------------|
| http://localhost:8080/dashboard | Mission control dashboard |
| http://localhost:8080/chaos | Chaos controller UI |
| http://localhost:8080/health | Health check endpoint |
| http://localhost:8080/api/status | Full system status API |

### 5. Demo

Trigger a fault, watch Elastic detect it, let the AI investigate, resolve it:

```bash
# Trigger Channel 2 — Fuel Pressure Anomaly
curl -X POST http://localhost:8080/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}'

# Watch the dashboard and Kibana...

# Resolve
curl -X POST http://localhost:8080/api/remediate/2
```

### 6. Teardown

```bash
./teardown.sh
```

---

## Fault Channels

| Ch | Name | Subsystem | Cloud |
|----|------|-----------|-------|
| 1 | Thermal Calibration Drift | propulsion | AWS |
| 2 | Fuel Pressure Anomaly | propulsion | AWS |
| 3 | Oxidizer Flow Rate Deviation | propulsion | AWS |
| 4 | GPS Multipath Interference | guidance | GCP |
| 5 | IMU Synchronization Loss | guidance | GCP |
| 6 | Star Tracker Alignment Fault | guidance | GCP |
| 7 | S-Band Signal Degradation | communications | GCP |
| 8 | X-Band Packet Loss | communications | GCP |
| 9 | UHF Antenna Pointing Error | communications | GCP |
| 10 | Payload Thermal Excursion | payload | GCP |
| 11 | Payload Vibration Anomaly | payload | GCP |
| 12 | Cross-Cloud Relay Latency | relay | Azure |
| 13 | Relay Packet Corruption | relay | Azure |
| 14 | Ground Power Bus Fault | ground | AWS |
| 15 | Weather Station Data Gap | ground | AWS |
| 16 | Pad Hydraulic Pressure Loss | ground | AWS |
| 17 | Sensor Validation Pipeline Stall | validation | Azure |
| 18 | Calibration Epoch Mismatch | validation | Azure |
| 19 | FTS Check Failure | safety | Azure |
| 20 | Range Safety Tracking Loss | safety | Azure |

See [docs/CHANNEL_REFERENCE.md](docs/CHANNEL_REFERENCE.md) for full details on all 20 channels.

---

## API Reference

### Health

```
GET /health
```

### System Status

```
GET /api/status
```

### Chaos Control

```
POST /api/chaos/trigger     {"channel": 1, "mode": "calibration"}
POST /api/chaos/resolve     {"channel": 1}
GET  /api/chaos/status
GET  /api/chaos/status/{channel}
```

### Remediation

```
POST /api/remediate/{channel}
```

### Countdown

```
POST /api/countdown/start
POST /api/countdown/pause
POST /api/countdown/reset
POST /api/countdown/speed   {"speed": 2.0}
```

---

## Project Structure

```
elastic-launch-demo/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration and channel registry
│   ├── telemetry.py               # OTLP client (logs, metrics, traces)
│   ├── __init__.py
│   ├── services/                  # 9 simulated microservices
│   │   ├── manager.py             # Service lifecycle manager
│   │   ├── base_service.py        # Abstract base with telemetry helpers
│   │   ├── mission_control.py
│   │   ├── fuel_system.py
│   │   ├── ground_systems.py
│   │   ├── navigation.py
│   │   ├── comms_array.py
│   │   ├── payload_monitor.py
│   │   ├── sensor_validator.py
│   │   ├── telemetry_relay.py
│   │   └── range_safety.py
│   ├── chaos/                     # Chaos injection system
│   │   ├── controller.py          # Channel state management
│   │   ├── channels.py            # Channel definitions helper
│   │   └── channel_definitions.json
│   ├── dashboard/                 # Mission control dashboard
│   │   ├── websocket.py           # WebSocket handler
│   │   └── static/                # HTML/CSS/JS
│   ├── chaos_ui/                  # Chaos controller UI
│   │   └── static/                # HTML/CSS/JS
│   └── notify/                    # Notification handlers
│       ├── __init__.py
│       ├── twilio_handler.py      # SMS + voice via Twilio REST API
│       ├── slack_handler.py       # Slack webhook alerts
│       └── twiml_templates/       # TwiML XML for voice calls
│           ├── anomaly_detected.xml
│           └── anomaly_resolved.xml
├── docs/
│   ├── DEMO_SCRIPT.md             # Presenter talk track
│   ├── SE_QUICK_START.md          # Quick start for SEs
│   ├── SETUP_GUIDE.md             # Full deployment guide
│   ├── CHANNEL_REFERENCE.md       # All 20 channels detailed
│   └── TROUBLESHOOTING.md         # Common issues and solutions
├── docker-compose.yml             # Container orchestration
├── Dockerfile                     # NOVA-7 app container
├── otel-collector-config.yaml     # OTel Collector pipeline config
├── requirements.txt               # Python dependencies
├── setup.sh                       # Automated setup and deploy
├── teardown.sh                    # Clean teardown
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SE Quick Start](docs/SE_QUICK_START.md) | Get running in under 10 minutes |
| [Setup Guide](docs/SETUP_GUIDE.md) | Full deployment from scratch |
| [Demo Script](docs/DEMO_SCRIPT.md) | Presenter talk track with 3 acts |
| [Channel Reference](docs/CHANNEL_REFERENCE.md) | All 20 fault channels detailed |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Application | Python 3.11, FastAPI, uvicorn |
| Telemetry Protocol | OpenTelemetry (OTLP JSON over HTTP) |
| Telemetry Collector | OpenTelemetry Collector Contrib 0.96.0 |
| Observability Platform | Elastic (Elasticsearch, Kibana) |
| HTTP Client | httpx with HTTP/2 |
| Real-time Updates | WebSockets |
| Container Runtime | Docker, Docker Compose |
| Notifications | Twilio REST API (SMS + voice), Slack Webhooks |
