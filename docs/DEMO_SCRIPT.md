# NOVA-7 Demo Script — Presenter Talk Track

> **Duration:** 15-25 minutes (adjustable)
> **Audience:** SEs, prospects, partners, or internal teams
> **Setup:** Ensure the NOVA-7 app is running and Elastic/Kibana is accessible. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for deployment instructions.

---

## Pre-Demo Checklist

- [ ] NOVA-7 app is running (`http://localhost:8080/health` returns OK)
- [ ] Elastic/Kibana is accessible and receiving telemetry
- [ ] Dashboard is open at `http://localhost:8080/dashboard`
- [ ] Chaos UI is open in a separate tab at `http://localhost:8080/chaos`
- [ ] Kibana Discover/Dashboard views are loaded and showing live data
- [ ] (Optional) Slack webhook is configured and test message sent
- [ ] (Optional) Twilio is configured for SMS/voice alerts

---

## Act 1: Streams — Normal Telemetry Flow

**Duration:** ~5 minutes

### Opening

> "Welcome to the NOVA-7 launch control demo. What you are seeing is a simulated multi-cloud space launch mission — nine microservices running across AWS, GCP, and Azure, all generating real OpenTelemetry telemetry that flows into Elastic."

### Show the Dashboard

Navigate to the NOVA-7 dashboard (`/dashboard`).

> "This is our mission control dashboard. Each service represents a subsystem of the launch vehicle — propulsion, guidance, communications, payload, ground systems, telemetry relay, validation, and safety."

Point out the service cards showing NOMINAL status across all services.

> "Every service is currently green — NOMINAL. They are continuously emitting logs, metrics, and traces through OpenTelemetry."

### Show Elastic / Kibana

Switch to the Kibana Discover view filtered to `service.namespace: nova7`.

> "Here in Elastic, we can see the telemetry arriving in real time. Notice the resource attributes — each log record carries cloud provider, region, availability zone, subsystem, and mission phase metadata."

Highlight the multi-cloud aspect:

> "This is a key point for the architecture. The fuel system runs on AWS in us-east-1. Navigation runs on GCP in us-central1. The sensor validator runs on Azure in eastus. Elastic is the single pane of glass that unifies observability across all three clouds."

### Show Traces and Metrics

If traces and metrics dashboards are configured:

> "We also have distributed traces showing request flows between services, and gauge metrics tracking sensor readings, temperatures, pressures — all the telemetry a real mission would produce."

### Transition

> "Everything looks nominal. Now let us see what happens when something goes wrong."

---

## The Interruption — Trigger a Fault

**Duration:** ~2 minutes

### Trigger via Chaos UI

Open the Chaos UI (`/chaos`) or use the API directly.

Choose a visually impactful channel. Recommended first faults:

| Channel | Name | Why it is good for demos |
|---------|------|--------------------------|
| 2 | Fuel Pressure Anomaly | Everyone understands fuel pressure |
| 7 | S-Band Signal Degradation | Visible cascade to telemetry-relay |
| 4 | GPS Multipath Interference | Multi-cloud (GCP service) |
| 12 | Cross-Cloud Relay Latency | Shows the multi-cloud story |

> "I am going to trigger a fault — a fuel pressure anomaly in the propulsion subsystem. Watch the dashboard."

Click the trigger button or run:

```bash
curl -X POST http://localhost:8080/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2, "mode": "calibration"}'
```

### Watch the Dashboard React

> "Immediately, the fuel system and sensor validator services go CRITICAL. And notice — mission control and range safety have gone to WARNING. That is the cascade effect. When a primary subsystem fails, dependent services detect degraded readings."

Point out the status changes on the dashboard.

> "Now let us look at what Elastic sees."

---

## Act 2: Significant Events + AI Agent

**Duration:** ~5-8 minutes

### Show Error Logs in Kibana

Switch to Kibana Discover. Filter to `error.type: FuelPressureException` or `severity_text: ERROR`.

> "The error logs are flowing in immediately. Each one carries the exact error type, stack trace, sensor type, and vehicle section. This is not just a generic error message — it is a richly structured signal that Elastic can detect automatically."

### Show Significant Event Detection (ES|QL)

If a significant event rule is configured in Elastic:

> "This is where Elastic's detection engine comes in. We have an ES|QL rule watching for this exact error signature. When the rate of FuelPressureException errors exceeds the threshold, Elastic fires a significant event."

Show the Alerts view in Kibana.

> "There it is — Elastic has detected the anomaly and created an alert. It knows the channel, the subsystem, the affected services, and the time window."

### Show AI Agent Investigation

If the Elastic AI Assistant or a custom agent is configured:

> "Now watch this. The significant event automatically triggers an AI investigation agent. The agent queries Elastic — it looks at the error logs, checks the metrics for the fuel system, reviews the traces, and correlates the cascade pattern."

Show the agent's investigation output or the workflow execution.

> "The agent has determined that the fuel pressure in tanks LOX-1 and RP1-2 are outside nominal bounds. It has traced the cascade to mission control and range safety. And it is recommending automated remediation."

### Show Notifications (if configured)

> "At the same time, the system has sent an SMS alert to the on-call engineer and posted a structured alert to the Slack channel with a direct link to investigate in Elastic."

Show the Slack message or SMS on your phone if available.

---

## Act 3: Remediation

**Duration:** ~3-5 minutes

### Automated Remediation

> "The Elastic workflow includes a remediation step. It calls the NOVA-7 remediation API to resolve the fault channel."

If using automated remediation via Elastic workflow:

> "Watch the dashboard — the fault is being resolved automatically."

Or trigger manual resolution:

```bash
curl -X POST http://localhost:8080/api/remediate/2
```

### Watch Recovery

> "The fuel system and sensor validator are returning to NOMINAL. The cascade warnings on mission control and range safety are clearing. Telemetry is flowing cleanly again."

Switch to Kibana to show the error rate dropping back to zero.

> "In Elastic, you can see the error rate dropping. The significant event closes. The AI agent logs its resolution. Everything is green."

### Show Resolution Notification

If Slack/Twilio is configured:

> "And the team gets a resolution notification — the fault was automatically detected, investigated, and resolved. Total time from anomaly to resolution: under two minutes, with zero human intervention."

---

## Closing

> "What you have just seen is the full Elastic observability lifecycle:
>
> 1. **Collect** — OpenTelemetry ingests telemetry from nine services across three clouds
> 2. **Detect** — Elastic's ES|QL rules identify the anomaly in real time
> 3. **Investigate** — An AI agent queries Elastic to determine root cause
> 4. **Remediate** — Automated workflows resolve the fault and confirm recovery
>
> This is not a contrived demo. This is the same architecture you would use in production — the same OTLP protocol, the same Elastic detection engine, the same AI-powered investigation."

### Optional: Second Fault

For longer demos, trigger a second fault from a different subsystem to show that the system handles multiple simultaneous faults:

> "Let me trigger a second fault — this time in the communications subsystem on GCP. Watch how Elastic correlates two independent faults across different cloud providers."

---

## Q&A Talking Points

**"Is the telemetry real OpenTelemetry?"**
> Yes. The services emit OTLP JSON over HTTP to a standard OpenTelemetry Collector, which exports to Elastic. The same pipeline works with any OTLP-compatible source.

**"How many channels can be active at once?"**
> All 20 channels are independent. You can trigger multiple faults simultaneously to demonstrate Elastic's ability to correlate and prioritize.

**"Can this run on my laptop?"**
> Yes. It is a single Docker Compose stack. The NOVA-7 app and the OTel Collector run in two containers. You just need an Elastic Cloud deployment (or self-hosted cluster) to receive the telemetry.

**"What about the AI agent — is that Elastic's AI Assistant?"**
> It can work with Elastic's built-in AI Assistant, a custom connector, or any LLM-powered agent that queries Elastic's APIs. The demo architecture is flexible.

**"How do I add my own fault scenarios?"**
> Add a new entry to the CHANNEL_REGISTRY in `app/config.py` and the corresponding entry in `channel_definitions.json`. The chaos controller and services pick it up automatically.
