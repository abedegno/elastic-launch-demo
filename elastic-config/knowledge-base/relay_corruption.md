# Relay Packet Corruption — Root Cause Analysis Guide

## Overview

Relay Packet Corruption (Channel 13) occurs when the telemetry relay network detects data integrity failures in packets traversing the ground communication infrastructure between cloud regions. This anomaly is detected by the `PacketCorruptionException` error type on `data_integrity` sensors in the `ground_network` vehicle section.

## Error Signature

- **Error Type**: `PacketCorruptionException`
- **Sensor Type**: `data_integrity`
- **Vehicle Section**: `ground_network`
- **Affected Services**: telemetry-relay (Azure eastus), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The relay subsystem is responsible for aggregating telemetry data from all ground stations and cloud services, applying data integrity checks, and forwarding validated data to mission control and the archival system. The telemetry-relay service (Azure) acts as the central data hub, receiving data from AWS-hosted services (mission-control, fuel-system, ground-systems), GCP-hosted services (navigation, comms-array, payload-monitor), and Azure-hosted services (sensor-validator, range-safety). Packet corruption can lead to incorrect telemetry displays, false alarms, or missed real anomalies.

## Common Root Causes

### 1. Cross-Cloud Network Path Degradation
**Probability**: High
**Description**: The inter-cloud network paths (AWS-Azure, GCP-Azure) traverse public internet peering points that can experience congestion, causing packet retransmissions and occasional bit errors in TCP segments that pass CRC checks but contain application-layer corruption.
**Diagnostic Steps**:
- Check network latency and jitter metrics between cloud regions
- Look for patterns in which specific cloud-to-cloud paths show higher corruption rates
- Verify if corruption correlates with known internet congestion events or maintenance windows

### 2. Serialization/Deserialization Mismatch
**Probability**: Medium
**Description**: Version mismatches between the protobuf or OTLP serialization libraries across services can cause silent data corruption when newer field types are incorrectly decoded by older library versions.
**Diagnostic Steps**:
- Check service versions and OTLP library versions across all three clouds
- Look for corruption patterns specific to certain telemetry field types (e.g., float64, repeated fields)
- Verify if corruption affects all sources equally or only specific service pairs

### 3. TLS Session Resumption Error
**Probability**: Medium
**Description**: When TLS sessions are resumed with stale session tickets, some load balancers can introduce byte-level errors in the decrypted payload. This is intermittent and difficult to reproduce.
**Diagnostic Steps**:
- Check TLS session resumption rates and error counters
- Look for correlation between corruption events and TLS session ticket rotation periods
- Verify load balancer TLS configuration and firmware versions

### 4. Memory Corruption in Relay Service
**Probability**: Low
**Description**: A memory leak or buffer overflow in the telemetry-relay service can cause data in memory to be overwritten, corrupting packets before they are forwarded.
**Diagnostic Steps**:
- Check telemetry-relay service memory usage and garbage collection metrics
- Look for increasing corruption rates over time since the last service restart
- Verify if a service restart temporarily resolves the corruption

## Remediation Procedures

### Immediate Actions
1. **Verify data integrity end-to-end**: Compare checksums at the source service with checksums at the relay to isolate where corruption is introduced.
2. **Check network health**: Review cross-cloud network metrics for latency spikes, packet loss, and jitter.
3. **Monitor corruption rate**: Determine if corruption is isolated incidents or a sustained pattern.

### Corrective Actions
1. **Reroute traffic**: If a specific network path is degraded, reroute telemetry through an alternate peering point or VPN tunnel.
2. **Restart relay service**: If memory corruption is suspected, perform a rolling restart of the telemetry-relay service.
3. **Enable redundant checksumming**: Activate application-layer CRC verification in addition to transport-layer checks.

### Escalation Criteria
- Corruption rate exceeds 0.5% of total packets: Data quality at risk, escalate to data integrity team
- Corruption affecting safety-critical telemetry (FTS, range safety): Immediate escalation to range safety officer
- Sustained corruption for more than 5 minutes: Potential systematic failure, request hold for data path validation

## Historical Precedents

### NOVA-3 Cloud Peering Congestion
During NOVA-3 launch day, a major cloud provider peering point experienced congestion due to unrelated traffic, causing 0.3% packet corruption on the AWS-Azure path for 12 minutes. Resolution: traffic was rerouted through a dedicated VPN tunnel. Post-mission, dedicated express routes were established between cloud regions.

### NOVA-5 Protobuf Version Mismatch
After a software update to the navigation service, OTLP serialization library was upgraded but the telemetry-relay service was not updated simultaneously. Float64 fields in navigation telemetry were silently corrupted. Resolution: all services were updated to matching library versions during the next maintenance window.

## Related Channels
- Channel 8: X-Band Packet Loss (data integrity correlation)
- Channel 12: Cross-Cloud Relay Latency (network path dependency)
- Channel 17: Validation Pipeline Anomaly (data validation dependency)
- Channel 7: S-Band Signal Degradation (telemetry source quality)
