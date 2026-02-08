# FTS Safety Check Anomaly — Root Cause Analysis Guide

## Overview

FTS Safety Check Anomaly (Channel 19) occurs when the Flight Termination System (FTS) self-test or monitoring detects a fault condition in the vehicle destruct system, safe-and-arm devices, or command destruct receivers. This anomaly is detected by the `FTSCheckException` error type on `safety_system` sensors in the `vehicle_wide` vehicle section.

**CRITICAL**: FTS anomalies can NEVER be ignored per range safety rules. Any FTS fault must be resolved before launch can proceed, regardless of the assessed probability of mission impact. This is a non-waivable launch commit criterion.

## Error Signature

- **Error Type**: `FTSCheckException`
- **Sensor Type**: `safety_system`
- **Vehicle Section**: `vehicle_wide`
- **Affected Services**: range-safety (Azure eastus), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The safety subsystem Flight Termination System is an independent safety system required by range safety regulations. It provides the capability to terminate the vehicle flight if it deviates from the planned trajectory and poses a risk to populated areas or property. The FTS consists of command destruct receivers (CDR) that receive encrypted destruct commands from ground stations, safe-and-arm devices (S&A) that enable or inhibit the destruct ordnance, and the ordnance train itself. The range-safety service (Azure) continuously monitors FTS health and performs periodic self-tests. FTS integrity is the single most critical safety requirement for launch.

## Common Root Causes

### 1. Command Destruct Receiver Signal Loss
**Probability**: High
**Description**: The CDR must maintain continuous lock on the ground command transmitter signal. Signal loss can be caused by antenna obscuration, transmitter issues, or multipath interference at the launch pad.
**Diagnostic Steps**:
- Check CDR signal strength on both primary and redundant receivers
- Verify ground command transmitter power output and antenna pointing
- Look for correlation with vehicle orientation changes that could obscure the CDR antenna

### 2. Safe-and-Arm Device Position Uncertainty
**Probability**: Medium
**Description**: The S&A device position indicators may report an ambiguous state (neither definitively SAFE nor ARM), typically due to a position sensor fault rather than an actual mechanical problem.
**Diagnostic Steps**:
- Check S&A position indicator readings on primary and backup sensors
- Verify if the S&A was commanded to change state recently
- Review S&A self-test results for mechanical response time within specification

### 3. FTS Battery Voltage Decline
**Probability**: Medium
**Description**: The FTS operates on independent thermal batteries that are activated during countdown. If battery voltage drops below the minimum threshold, the FTS may not have sufficient power to execute a destruct command.
**Diagnostic Steps**:
- Check FTS battery voltage against minimum operating threshold
- Verify battery activation time and compare against expected voltage decay profile
- Check for abnormal current draw that could indicate a partial short circuit

### 4. Self-Test Sequence Timeout
**Probability**: Low
**Description**: The periodic FTS self-test runs a sequence of checks including CDR decode verification, S&A circuit continuity, and ordnance bridge wire resistance. A timeout in any step indicates a potential system fault.
**Diagnostic Steps**:
- Check which self-test step timed out
- Review the self-test timing profile for degraded but passing steps
- Verify if the timeout is repeatable or was a one-time event

## Remediation Procedures

### Immediate Actions
1. **MANDATORY HOLD**: Any FTS fault requires an immediate countdown hold per range safety regulations. No exceptions.
2. **Notify range safety officer**: FTS anomalies must be reported to the range safety officer immediately regardless of apparent severity.
3. **Run full FTS self-test**: Command a comprehensive FTS self-test sequence to characterize the fault.

### Corrective Actions
1. **CDR signal recovery**: If signal loss, verify and repoint ground command transmitter antennas. Check for new obstructions in the line of sight.
2. **S&A verification**: If position uncertainty, command an S&A cycle (SAFE-ARM-SAFE) to verify mechanical operation. If ambiguity persists, this is a no-go condition.
3. **Battery replacement**: If battery voltage is declining, the FTS thermal batteries may need to be replaced. This requires pad access and timeline impact.

### Escalation Criteria
- ANY FTS fault: Automatic escalation to range safety officer (mandatory)
- S&A position ambiguity that persists after cycling: Vehicle must be safed, launch scrubbed
- CDR signal loss on both receivers simultaneously: Potential systemic failure, launch scrubbed
- FTS battery voltage below minimum: Launch scrubbed, pad access required for battery replacement

## Historical Precedents

### NOVA-3 CDR Multipath Interference
During NOVA-3 countdown at T-10:00, the primary CDR reported intermittent signal loss due to multipath interference from a newly installed reflective surface on the mobile service tower. Resolution: the ground command transmitter was switched to an alternate frequency, and the tower surface was identified for anti-reflective treatment. Countdown held for 35 minutes.

### NOVA-5 FTS Battery Early Activation
The NOVA-5 FTS thermal batteries were inadvertently activated 2 hours earlier than planned due to a procedure error. By T-30:00, battery voltage was approaching the minimum threshold. Resolution: launch was scrubbed and batteries were replaced. The battery activation checklist was revised to add independent verification.

### NOVA-6 S&A Position Sensor Failure
NOVA-6 S&A device reported an ambiguous position reading despite mechanical operation being nominal. Root cause was a failed position sensor potentiometer. Resolution: backup position sensor confirmed correct S&A state. Launch proceeded after range safety officer certification, but the primary sensor was flagged for post-flight replacement.

## Related Channels
- Channel 20: Range Tracking Loss (range safety system correlation)
- Channel 2: Fuel Pressure Anomaly (propulsion safety integration)
- Channel 14: Power Bus Fault (FTS ground power backup)
- Channel 17: Validation Pipeline Anomaly (safety data validation priority)
