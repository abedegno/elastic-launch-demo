# X-Band Packet Loss — Root Cause Analysis Guide

## Overview

X-Band Packet Loss (Channel 8) occurs when the high-bandwidth X-band data link experiences packet loss rates exceeding the 0.1% threshold, degrading the quality of high-resolution telemetry, video, and payload data transmission. This anomaly is detected by the `PacketLossException` error type on `packet_integrity` sensors in the `antenna_array` vehicle section.

## Error Signature

- **Error Type**: `PacketLossException`
- **Sensor Type**: `packet_integrity`
- **Vehicle Section**: `antenna_array`
- **Affected Services**: comms-array (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: telemetry-relay (Azure eastus), mission-control (AWS us-east-1)

## Subsystem Context

The communications subsystem X-band link operates at 8.4 GHz and provides the high-bandwidth data downlink for payload telemetry, onboard video, and detailed engineering data. Unlike the S-band link used for commands and critical telemetry, the X-band carries bulk data at rates up to 150 Mbps. The comms-array service (GCP) manages packetization, forward error correction (FEC), and data prioritization. Packet losses can result in corrupted data frames that cannot be reconstructed by FEC, leading to gaps in the recorded mission data.

## Common Root Causes

### 1. FEC Encoder Buffer Overflow
**Probability**: High
**Description**: When multiple high-rate data sources (video, payload telemetry, engineering data) simultaneously demand bandwidth, the FEC encoder buffer can overflow, causing packets to be dropped before encoding.
**Diagnostic Steps**:
- Check the FEC encoder buffer utilization telemetry for values above 85%
- Identify which data sources are active and their current data rates
- Look for burst patterns in packet loss corresponding to periodic high-rate data dumps

### 2. Ground Station Receiver Synchronization Loss
**Probability**: Medium
**Description**: The ground station X-band receiver can lose symbol synchronization during rapid signal dynamics (e.g., vehicle maneuvers causing Doppler shifts), resulting in burst packet losses until resynchronization.
**Diagnostic Steps**:
- Check ground receiver sync status and lock indicators
- Correlate packet loss events with vehicle attitude maneuvers or trajectory events
- Verify Doppler pre-compensation is tracking correctly

### 3. Rain Fade at X-Band
**Probability**: Medium
**Description**: X-band frequencies are significantly more susceptible to rain attenuation than S-band. Even moderate rainfall (5 mm/hr) along the signal path can cause enough attenuation to push the link below the demodulation threshold.
**Diagnostic Steps**:
- Check weather data (Channel 15) for precipitation along the ground station path
- Compare S-band signal levels — if S-band is healthy but X-band is degraded, rain fade is likely
- Review link budget margin for current atmospheric conditions

### 4. Onboard Data Multiplexer Fault
**Probability**: Low
**Description**: The data multiplexer that combines multiple telemetry streams before X-band transmission can develop timing faults, producing malformed packets that fail CRC checks at the receiver.
**Diagnostic Steps**:
- Check multiplexer error counters and internal status registers
- Look for patterns in which specific data streams are experiencing losses vs. others
- Verify multiplexer clock synchronization with the master timing reference

## Remediation Procedures

### Immediate Actions
1. **Check data rate allocation**: Verify current aggregate data rate does not exceed the X-band link capacity for the current link budget.
2. **Monitor FEC performance**: Check the FEC decoder correction rate at the ground station — rising corrections indicate degrading margin.
3. **Verify ground receiver status**: Confirm receiver lock, sync, and bit error rate are within acceptable ranges.

### Corrective Actions
1. **Reduce data rate**: Shed lower-priority data sources (e.g., video) to reduce aggregate bandwidth demand.
2. **Increase FEC rate**: Switch to a higher FEC code rate to provide additional error correction margin at the cost of reduced throughput.
3. **Handover to alternate station**: If rain fade is the cause, hand over to a ground station outside the precipitation area.

### Escalation Criteria
- Packet loss exceeds 1%: High-rate data link effectively unusable, escalate to mission data team
- Correlation with S-band degradation (Channel 7): Potential systemic communications failure
- Packet loss during critical mission phase (LAUNCH, ASCENT): Escalate to launch director for data completeness assessment

## Historical Precedents

### NOVA-4 Buffer Overflow During Video Activation
During NOVA-4 ascent, activation of the onboard HD video camera caused the FEC encoder buffer to overflow, resulting in 2.3% packet loss for 45 seconds. Resolution: video data rate was automatically reduced by the comms-array service priority algorithm. Post-flight, the bandwidth allocation table was updated.

### NOVA-6 Rain Fade at Ascent
NOVA-6 X-band link experienced 15 seconds of complete data loss during ascent through a rain band at altitude 8-12 km. S-band link was unaffected. Resolution: data was recovered from onboard recording during post-flight download. Ascent rain fade mitigation procedures were updated.

## Related Channels
- Channel 7: S-Band Signal Degradation (communications subsystem correlation)
- Channel 9: UHF Antenna Pointing Anomaly (antenna array dependency)
- Channel 13: Relay Packet Corruption (data integrity correlation)
- Channel 15: Weather Data Gap (atmospheric conditions)
