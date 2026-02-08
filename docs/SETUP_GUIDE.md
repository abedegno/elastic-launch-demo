# NOVA-7 Setup Guide — Full Deployment from Scratch

This guide walks through every step to get the NOVA-7 Launch Demo running, from zero to a fully functional demo environment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Elastic Cloud Setup](#2-elastic-cloud-setup)
3. [Clone the Repository](#3-clone-the-repository)
4. [Configure Environment Variables](#4-configure-environment-variables)
5. [Build and Deploy](#5-build-and-deploy)
6. [Verify Telemetry Pipeline](#6-verify-telemetry-pipeline)
7. [Configure Kibana Dashboards](#7-configure-kibana-dashboards)
8. [Configure Significant Event Rules](#8-configure-significant-event-rules)
9. [Optional: Configure Notifications](#9-optional-configure-notifications)
10. [Optional: Configure AI Agent](#10-optional-configure-ai-agent)
11. [Running the Demo](#11-running-the-demo)

---

## 1. Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.x+ | Multi-container orchestration |
| curl | any | Health checks and API calls |
| A web browser | modern | Dashboard and Kibana |

### Required Accounts

| Service | Purpose | Free Tier Available |
|---------|---------|---------------------|
| Elastic Cloud | Telemetry storage and analysis | Yes (14-day trial) |

### Optional Accounts

| Service | Purpose | Free Tier Available |
|---------|---------|---------------------|
| Twilio | SMS and voice call alerts | Yes (trial credits) |
| Slack | Webhook notifications | Yes |

### System Requirements

- **CPU:** 2+ cores
- **RAM:** 4 GB minimum (8 GB recommended)
- **Disk:** 2 GB for Docker images
- **Network:** Outbound HTTPS to Elastic Cloud

---

## 2. Elastic Cloud Setup

### Create a Deployment

1. Sign up or log in at [cloud.elastic.co](https://cloud.elastic.co)
2. Create a new deployment:
   - **Name:** `nova7-demo` (or your preference)
   - **Cloud provider:** Any (AWS, GCP, or Azure)
   - **Region:** Choose one close to you
   - **Version:** 8.x (latest)
   - **Size:** The smallest tier works fine for demos
3. Wait for the deployment to become healthy

### Get Your Credentials

#### Elasticsearch Endpoint

1. In the Elastic Cloud console, go to your deployment
2. Click **Manage** next to Elasticsearch
3. Copy the **Endpoint URL** (e.g., `https://my-deploy-abc123.es.us-central1.gcp.cloud.es.io:443`)

#### API Key

1. Open Kibana for your deployment
2. Go to **Stack Management** > **Security** > **API Keys**
3. Click **Create API Key**
4. Configure:
   - **Name:** `nova7-otel-collector`
   - **Expiration:** Set to your demo timeframe or "Never"
   - **Privileges:** (use the JSON editor)
     ```json
     {
       "index": [
         {
           "names": ["logs-*", "metrics-*", "traces-*"],
           "privileges": ["create_index", "create_doc", "auto_configure", "write"]
         }
       ]
     }
     ```
5. Click **Create API Key** and copy the Base64-encoded key

---

## 3. Clone the Repository

```bash
git clone <repo-url> elastic-launch-demo
cd elastic-launch-demo
```

Verify the project structure:

```bash
ls -la
# Should show: app/ docs/ docker-compose.yml Dockerfile setup.sh teardown.sh etc.
```

---

## 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your editor of choice:

```bash
# Required — set these
ELASTIC_ENDPOINT=https://your-deployment.es.cloud.es.io:443
ELASTIC_API_KEY=your-base64-encoded-api-key

# These defaults are fine for Docker deployments
OTLP_ENDPOINT=http://otel-collector:4318
APP_PORT=8080
APP_HOST=0.0.0.0
```

### Validate Configuration

```bash
./setup.sh --dry-run
```

This checks all environment variables and prerequisites without making any changes.

---

## 5. Build and Deploy

### Automated Setup

```bash
./setup.sh
```

The setup script will:
1. Check prerequisites (Docker, docker-compose, curl)
2. Load and validate environment variables
3. Verify project structure
4. Test Elastic Cloud connectivity
5. Build Docker images
6. Start containers
7. Run health checks

### Manual Setup (if you prefer)

```bash
# Build
docker compose build

# Start
docker compose up -d

# Verify
curl http://localhost:8080/health
```

### Check Logs

```bash
# All services
docker compose logs -f

# Just the NOVA-7 app
docker compose logs -f nova7

# Just the OTel collector
docker compose logs -f otel-collector
```

---

## 6. Verify Telemetry Pipeline

### Check NOVA-7 Health

```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```

Expected:
```json
{
    "status": "ok",
    "mission": "NOVA-7"
}
```

### Check System Status

```bash
curl -s http://localhost:8080/api/status | python3 -m json.tool
```

This should show all nine services in NOMINAL status.

### Verify Data in Kibana

1. Open Kibana for your Elastic deployment
2. Go to **Discover**
3. Select the `logs-*` data view (create one if it doesn't exist)
4. You should see log entries arriving with:
   - `service.name`: mission-control, fuel-system, navigation, etc.
   - `service.namespace`: nova7
   - `cloud.provider`: aws, gcp, azure
   - Various severity levels (INFO, DEBUG, WARN)

### Verify Metrics

1. In Kibana, go to **Discover** with the `metrics-*` data view
2. Look for metric names like gauge values from the services

### Verify Traces

1. In Kibana, navigate to **APM** > **Traces** or use the `traces-*` data view
2. Look for spans from nova7 services

---

## 7. Configure Kibana Dashboards

### Recommended Views

Create these saved searches and dashboards in Kibana:

#### Discover Saved Search: "NOVA-7 All Logs"

- Index pattern: `logs-*`
- Filter: `service.namespace: nova7`
- Columns: `@timestamp`, `service.name`, `severity_text`, `body`, `cloud.provider`

#### Discover Saved Search: "NOVA-7 Errors Only"

- Index pattern: `logs-*`
- Filter: `service.namespace: nova7 AND severity_text: ERROR`
- Columns: `@timestamp`, `service.name`, `error.type`, `body`, `exception.stacktrace`

#### Dashboard: "NOVA-7 Mission Overview"

Create a dashboard with:
- Log volume over time (broken down by severity)
- Service health table (log count by service.name and severity_text)
- Error rate visualization
- Cloud provider distribution pie chart
- Metric gauges for key readings

---

## 8. Configure Significant Event Rules

To get automatic anomaly detection, create ES|QL rules in Elastic:

### Example Rule: Fuel Pressure Anomaly

1. Go to **Security** > **Rules** > **Create New Rule**
2. Select **ES|QL** rule type
3. Query:
   ```esql
   FROM logs-*
   | WHERE service.namespace == "nova7"
     AND error.type == "FuelPressureException"
     AND @timestamp > NOW() - 2 minutes
   | STATS error_count = COUNT(*) BY service.name
   | WHERE error_count > 5
   ```
4. Set schedule to run every 1 minute
5. Configure actions (webhook to NOVA-7 remediation endpoint, Slack, etc.)

### Example Rule: Any Channel Error Spike

```esql
FROM logs-*
| WHERE service.namespace == "nova7"
  AND severity_text == "ERROR"
  AND error.type IS NOT NULL
  AND @timestamp > NOW() - 2 minutes
| STATS error_count = COUNT(*) BY error.type, service.name
| WHERE error_count > 5
```

---

## 9. Optional: Configure Notifications

### Twilio (SMS + Voice)

1. Create a Twilio account at [twilio.com](https://www.twilio.com/)
2. Get a phone number
3. Find your Account SID and Auth Token on the console dashboard
4. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=+1XXXXXXXXXX
   TWILIO_TO_NUMBER=+1XXXXXXXXXX
   ```
5. For voice calls, the TwiML templates need to be served at a public URL. Options:
   - Host them on a public web server
   - Use ngrok to expose a local URL
   - Use Twilio's TwiML Bins feature

### Slack

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable **Incoming Webhooks**
3. Add a webhook to your desired channel
4. Copy the webhook URL
5. Add to `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXX
   ```

---

## 10. Optional: Configure AI Agent

The NOVA-7 demo can integrate with AI agents for automated investigation. Options:

### Elastic AI Assistant

Use Elastic's built-in AI Assistant to investigate alerts. Configure an LLM connector in Kibana under **Stack Management** > **Connectors**.

### Custom Agent via Elastic Workflow

Create an Elastic workflow that:
1. Triggers on the significant event rule
2. Queries Elastic for related logs, metrics, and traces
3. Sends context to an LLM for analysis
4. Calls the NOVA-7 remediation API: `POST /api/remediate/{channel}`

---

## 11. Running the Demo

1. Open the dashboard: http://localhost:8080/dashboard
2. Open the chaos UI: http://localhost:8080/chaos
3. Open Kibana in another tab
4. Follow the [DEMO_SCRIPT.md](DEMO_SCRIPT.md) talk track

### Quick Test

```bash
# Trigger a fault
curl -X POST http://localhost:8080/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}'

# Check status
curl -s http://localhost:8080/api/chaos/status/2

# Resolve
curl -X POST http://localhost:8080/api/remediate/2
```

---

## Appendix: Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌─────────────┐        ┌──────────────────────┐       │
│  │   NOVA-7     │ OTLP   │  OTel Collector      │       │
│  │   FastAPI    │───────>│  (contrib 0.96.0)    │       │
│  │   :8080      │  HTTP   │  :4317 gRPC          │       │
│  │             │        │  :4318 HTTP          │       │
│  └─────────────┘        └──────────┬───────────┘       │
│                                    │                    │
└────────────────────────────────────│────────────────────┘
                                     │ HTTPS
                                     ▼
                          ┌──────────────────────┐
                          │   Elastic Cloud       │
                          │   Elasticsearch       │
                          │   Kibana             │
                          └──────────────────────┘
```
