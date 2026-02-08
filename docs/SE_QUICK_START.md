# SE Quick Start Guide

> Get the NOVA-7 demo running and presenting in under 10 minutes.

---

## 1. Prerequisites

You need:
- Docker and Docker Compose installed
- An Elastic Cloud deployment (or self-hosted Elasticsearch 8.x+)
- An Elastic API key with write access to `logs-*`, `metrics-*`, `traces-*`

## 2. Clone and Configure

```bash
git clone <repo-url> elastic-launch-demo
cd elastic-launch-demo

cp .env.example .env
```

Edit `.env` and set (at minimum):

```
ELASTIC_ENDPOINT=https://your-deployment.es.cloud.es.io:443
ELASTIC_API_KEY=your-base64-api-key
```

## 3. Deploy

```bash
./setup.sh
```

This validates your config, builds the container, and starts everything.

## 4. Verify

Open these URLs:

| URL | What it shows |
|-----|---------------|
| http://localhost:8080/health | Health check (should return `{"status": "ok"}`) |
| http://localhost:8080/dashboard | Mission control dashboard |
| http://localhost:8080/chaos | Chaos controller UI |
| Your Kibana URL | Logs flowing into Elastic |

## 5. Pick a Channel

Choose the fault channel that best fits your audience:

### For Security / Ops Audiences

| Channel | Name | Story |
|---------|------|-------|
| 19 | Flight Termination System Check Failure | Safety-critical system anomaly |
| 20 | Range Safety Tracking Loss | Loss of tracking — immediate response needed |
| 17 | Sensor Validation Pipeline Stall | Pipeline failure affecting all validation |

### For Cloud / Infrastructure Audiences

| Channel | Name | Story |
|---------|------|-------|
| 12 | Cross-Cloud Relay Latency | Multi-cloud latency spike (AWS to GCP) |
| 13 | Relay Packet Corruption | Data integrity failure in cross-cloud relay |
| 14 | Ground Power Bus Fault | Infrastructure power failure |

### For Developer / APM Audiences

| Channel | Name | Story |
|---------|------|-------|
| 1 | Thermal Calibration Drift | Sensor calibration drift with stack traces |
| 2 | Fuel Pressure Anomaly | Classic pressure bounds exception |
| 4 | GPS Multipath Interference | Signal processing error in guidance |

### For Executive / High-Level Audiences

| Channel | Name | Story |
|---------|------|-------|
| 7 | S-Band Signal Degradation | Communications failure (easy to understand) |
| 2 | Fuel Pressure Anomaly | Fuel system issue (universally relatable) |
| 11 | Payload Vibration Anomaly | Payload at risk (high stakes narrative) |

## 6. Trigger the Fault

**Option A — Chaos UI**

Open http://localhost:8080/chaos and click the trigger button for your chosen channel.

**Option B — curl**

```bash
# Replace CHANNEL with the channel number (1-20)
curl -X POST http://localhost:8080/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": CHANNEL}'
```

## 7. Demo Flow

1. **Show normal state** — Point out all-green dashboard, telemetry flowing in Kibana
2. **Trigger the fault** — Watch the dashboard go red/yellow
3. **Switch to Kibana** — Show error logs with structured attributes
4. **Show detection** — Elastic alert / significant event fires
5. **Show investigation** — AI agent analyzes the root cause
6. **Resolve** — Automated or manual remediation

## 8. Resolve the Fault

**Option A — Chaos UI**

Click the resolve button in the Chaos UI.

**Option B — curl**

```bash
curl -X POST http://localhost:8080/api/remediate/CHANNEL
```

**Option C — Let Elastic Do It**

If you have an Elastic workflow configured, it will call the remediation API automatically.

## 9. Teardown

```bash
./teardown.sh
```

## Troubleshooting

If something goes wrong, check [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**Quick fixes:**

| Problem | Fix |
|---------|-----|
| Dashboard is blank | Hard refresh (Ctrl+Shift+R). Check WebSocket connection. |
| No data in Kibana | Verify ELASTIC_ENDPOINT and ELASTIC_API_KEY in .env |
| Container won't start | Run `docker compose logs nova7` to see errors |
| Port 8080 in use | Change APP_PORT in .env or stop the conflicting service |
