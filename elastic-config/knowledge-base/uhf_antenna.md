# UHF Antenna Pointing Anomaly — Root Cause Analysis Guide

## Overview

UHF Antenna Pointing Anomaly (Channel 9) occurs when the UHF antenna tracking system fails to maintain the required pointing accuracy of 2 degrees toward the assigned relay satellite or ground station. This anomaly is detected by the `AntennaPointingException` error type on `antenna_position` sensors in the `antenna_array` vehicle section.

## Error Signature

- **Error Type**: `AntennaPointingException`
- **Sensor Type**: `antenna_position`
- **Vehicle Section**: `antenna_array`
- **Affected Services**: comms-array (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The communications subsystem UHF antenna provides backup voice and low-rate data communication, as well as the Tracking and Data Relay Satellite System (TDRSS) link for beyond-line-of-sight communications during ascent. The antenna is mechanically steered by a two-axis gimbal system controlled by the comms-array service. Pointing commands are derived from the navigation solution and the known positions of target relay satellites. Loss of UHF pointing during ascent can eliminate backup communication paths when the vehicle is beyond direct ground station visibility.

## Common Root Causes

### 1. Gimbal Motor Controller Fault
**Probability**: High
**Description**: The UHF antenna gimbal is driven by stepper motors with position feedback from resolvers. A motor controller fault can cause the gimbal to slew to an incorrect position or stop tracking entirely.
**Diagnostic Steps**:
- Check gimbal motor current draw — abnormally high current indicates a mechanical bind, zero current indicates a controller failure
- Verify resolver position feedback matches the commanded position
- Test gimbal response to a small step command to verify the control loop is operational

### 2. Navigation Solution Latency
**Probability**: Medium
**Description**: The antenna pointing commands are computed from the navigation solution. If the navigation service (GCP) experiences processing delays or the cross-cloud data path introduces latency, the pointing commands will lag behind the actual vehicle attitude, causing pointing error.
**Diagnostic Steps**:
- Check the age of the navigation solution used for pointing computation
- Measure the latency between the navigation service and the comms-array service
- Correlate pointing errors with vehicle angular rates — errors worsen during rapid maneuvers when latency matters most

### 3. Gimbal Cable Harness Interference
**Probability**: Medium
**Description**: The gimbal cable harness can snag or become constrained at certain gimbal angles, particularly near the mechanical stops, preventing smooth tracking motion.
**Diagnostic Steps**:
- Check if the pointing error occurs only at specific gimbal angles
- Review gimbal position history for sudden jumps or stalls at consistent angles
- Verify gimbal range-of-motion test results from the last pre-launch checkout

### 4. Target Ephemeris Error
**Probability**: Low
**Description**: Incorrect or outdated relay satellite ephemeris data can cause the pointing algorithm to compute incorrect target directions.
**Diagnostic Steps**:
- Verify the relay satellite ephemeris load date and version
- Cross-check computed target direction against known satellite positions from external tracking data
- Check if pointing error is consistent (constant offset) or varying (suggests navigation rather than ephemeris issue)

## Remediation Procedures

### Immediate Actions
1. **Switch to omnidirectional mode**: If the directional UHF antenna cannot maintain pointing, switch to the omnidirectional UHF antenna (lower gain but no pointing requirement).
2. **Verify navigation solution**: Confirm the navigation service is providing timely and accurate attitude data.
3. **Check gimbal health**: Review motor current, resolver feedback, and control loop error signals.

### Corrective Actions
1. **Reset gimbal controller**: Command a gimbal controller reset and re-initialization to clear any latched fault states.
2. **Update ephemeris**: If target ephemeris is stale, upload the current relay satellite ephemeris.
3. **Reduce pointing update rate**: If latency is the cause, increase the pointing command lead time to compensate for data path delay.

### Escalation Criteria
- Pointing error exceeds 5 degrees: UHF link may be lost, escalate to communications team
- Gimbal motor current at zero: Potential complete gimbal failure, escalate to launch director
- All three antenna systems degraded (Channels 7, 8, 9): Communications subsystem failure, immediate hold

## Historical Precedents

### NOVA-3 Gimbal Cable Snag
During NOVA-3 pre-launch antenna checkout, the UHF gimbal stalled at 45 degrees elevation due to a cable harness interference with a bracket. Resolution: ground crew adjusted the cable routing during a scheduled pad access. No impact to timeline.

### NOVA-5 Ephemeris Upload Error
NOVA-5 UHF antenna consistently pointed 0.8 degrees off-target after ascent. Root cause was an ephemeris file that used the previous day's satellite position predictions. Resolution: updated ephemeris was uploaded via S-band command link during ascent. UHF link recovered at T+4:30.

## Related Channels
- Channel 7: S-Band Signal Degradation (communications subsystem correlation)
- Channel 8: X-Band Packet Loss (antenna array dependency)
- Channel 6: Star Tracker Alignment (vehicle attitude reference)
- Channel 14: Power Bus Fault (gimbal motor power supply)
