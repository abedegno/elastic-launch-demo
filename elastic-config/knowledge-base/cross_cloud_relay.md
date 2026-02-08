# Cross-Cloud Relay Latency — Root Cause Analysis Guide

## Overview

Cross-Cloud Relay Latency (Channel 12) occurs when telemetry data relay between cloud providers experiences latency that exceeds acceptable bounds. In the NOVA-7 multi-cloud architecture, services are distributed across AWS (us-east-1), GCP (us-central1), and Azure (eastus), and the telemetry-relay service is responsible for ensuring timely data delivery across these boundaries. This anomaly is detected by the `RelayLatencyException` error type on `network_latency` sensors in the `ground_network` vehicle section.

## Error Signature

- **Error Type**: `RelayLatencyException`
- **Sensor Type**: `network_latency`
- **Vehicle Section**: `ground_network`
- **Affected Services**: telemetry-relay (Azure eastus), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), comms-array (GCP us-central1)

## Subsystem Context

The NOVA-7 mission architecture is deliberately multi-cloud to demonstrate cross-cloud observability:

| Service | Cloud | Region |
|---------|-------|--------|
| mission-control | AWS | us-east-1 |
| fuel-system | AWS | us-east-1 |
| ground-systems | AWS | us-east-1 |
| navigation | GCP | us-central1 |
| comms-array | GCP | us-central1 |
| payload-monitor | GCP | us-central1 |
| sensor-validator | Azure | eastus |
| telemetry-relay | Azure | eastus |
| range-safety | Azure | eastus |

The telemetry-relay service acts as the central hub, receiving telemetry from services on all three clouds and forwarding it to the appropriate consumers. Latency on the relay path directly impacts the freshness of data available to downstream consumers, including the sensor-validator, mission-control, and range-safety services.

## Cloud-to-Cloud Relay Paths

| Path | Source | Destination | Expected Latency | Critical Data |
|------|--------|-------------|-------------------|---------------|
| AWS -> Azure | fuel-system | sensor-validator | < 50ms | Propulsion telemetry |
| AWS -> GCP | mission-control | comms-array | < 40ms | Command uplinks |
| GCP -> Azure | navigation | sensor-validator | < 60ms | Navigation state vectors |
| GCP -> Azure | comms-array | telemetry-relay | < 60ms | Communication health |
| Azure -> AWS | range-safety | mission-control | < 50ms | Safety status |

## Common Root Causes

### 1. Cloud Provider Network Congestion
**Probability**: High
**Description**: Internet backbone congestion between cloud provider regions increases round-trip latency. This is more common during business hours and can be exacerbated by large data transfers on shared infrastructure.
**Diagnostic Steps**:
- Check baseline latency metrics for each cloud-to-cloud path
- Compare current latency against the 24-hour average
- Verify if the latency spike affects all paths or specific routes
- Check cloud provider status pages for known network issues

### 2. Telemetry-Relay Service Overload
**Probability**: Medium
**Description**: The telemetry-relay service on Azure becomes overwhelmed by the volume of telemetry data, especially when multiple fault channels are active simultaneously. Queue depth grows, causing processing delays that manifest as increased end-to-end latency.
**Diagnostic Steps**:
- Check telemetry-relay queue depth metrics
- Verify CPU and memory utilization on the relay service
- Look for concurrent fault channel activations that may be generating high error log volume
- Check the sensor-validator pipeline health (Channel 17)

### 3. DNS Resolution Delays
**Probability**: Medium
**Description**: Cross-cloud service discovery relies on DNS, and DNS resolution delays or cache expiry can add latency to the first request in a connection cycle.
**Diagnostic Steps**:
- Check DNS resolution times in the telemetry-relay logs
- Verify DNS cache TTL configuration
- Look for DNS NXDOMAIN or timeout errors

### 4. TLS Handshake Overhead
**Probability**: Low
**Description**: When connections are re-established (e.g., after a timeout or service restart), the TLS handshake adds latency. Connection pooling and keep-alive should mitigate this, but configuration errors can cause frequent reconnections.
**Diagnostic Steps**:
- Check connection pool utilization metrics
- Look for TLS handshake error events
- Verify keep-alive timeout configuration
- Check if connections are being prematurely closed

### 5. OTel Collector Batch Processing
**Probability**: Low
**Description**: The OpenTelemetry Collector's batch processor introduces intentional latency (configured at 1s timeout, 1024 batch size in NOVA-7). If the batch timeout is too aggressive or the batch size too large, it can add perceived latency.
**Diagnostic Steps**:
- Check OTel Collector batch processor metrics (batch_send_size, batch_send_latency)
- Verify collector memory limiter is not throttling
- Review the otel-collector-config.yaml for batch settings

## Remediation Procedures

### Immediate Actions
1. **Identify the affected path**: Determine which cloud-to-cloud relay path is experiencing latency. This narrows the investigation scope.
2. **Check downstream impact**: Verify whether the latency is causing stale data in sensor-validator or mission-control. Stale data can lead to false anomaly detections or missed real anomalies.
3. **Monitor queue depth**: If the telemetry-relay queue depth exceeds 1000, the service is falling behind and may need load shedding.

### Corrective Actions
1. **Enable direct path failover**: For critical data paths (e.g., navigation state vectors), enable direct service-to-service communication bypassing the relay.
2. **Scale relay service**: If the relay is overloaded, scale up the Azure VM or add replica instances.
3. **Adjust batch settings**: Reduce the OTel Collector batch timeout from 1s to 500ms to reduce buffering latency.
4. **Purge stale data**: If accumulated stale data is causing downstream issues, flush the relay queue and reinitialize from current state.

### Escalation Criteria
- Latency exceeds 500ms on any path: Escalate to launch director
- Latency exceeds 1000ms on the Azure -> AWS path (range-safety -> mission-control): Immediate hold, safety data is stale
- Total data loss (no relay throughput): Immediate hold, telemetry blackout
- Concurrent packet corruption (Channel 13): Data integrity compromised, request hold

## Impact Assessment

Cross-cloud relay latency affects the entire mission monitoring capability:

- **Sensor-validator**: Cannot validate readings in real-time, may miss anomalies or generate false positives
- **Mission-control**: Receives delayed subsystem status, impairing situational awareness
- **Range-safety**: If range-safety data is delayed reaching mission-control, the safety decision loop is extended
- **Comms-array**: May not receive timely command feedback, affecting uplink scheduling

The relay latency threshold of 200ms was established based on the requirement that the mission-control decision loop must complete within 2 seconds for any safety-critical event.

## Historical Precedents

### NOVA-5 Azure Network Partition
During NOVA-5 at T-120:00, a partial network partition between Azure eastus and AWS us-east-1 caused relay latency to spike to 2,300ms. The sensor-validator continued processing but mission-control was receiving data 2+ seconds stale. Resolution: direct VPN tunnel was established between the two providers, bypassing the congested internet path. Countdown proceeded without hold after latency dropped to 45ms.

### NOVA-6 Relay Queue Overflow
NOVA-6 activated 8 fault channels simultaneously during testing, generating a surge of error logs. The telemetry-relay service's queue overflowed at 5,000 entries, causing data loss for 15 seconds. Resolution: relay service was scaled to 3 replicas with a shared queue, and the batch size was tuned to handle burst traffic.

## Related Channels
- Channel 8: X-Band Packet Loss (data delivery reliability)
- Channel 13: Relay Packet Corruption (data integrity on relay path)
- Channel 17: Validation Pipeline Stall (downstream processing impact)
- Channel 18: Calibration Epoch Mismatch (stale calibration data from latency)
