# Calibration Epoch Mismatch — Root Cause Analysis Guide

## Overview

Calibration Epoch Mismatch (Channel 18) occurs when the sensor calibration reference timestamps diverge beyond the acceptable staleness threshold, indicating that calibration baselines may no longer accurately represent current sensor characteristics. This anomaly is detected by the `CalibrationEpochException` error type on `calibration` sensors in the `ground_network` vehicle section.

## Error Signature

- **Error Type**: `CalibrationEpochException`
- **Sensor Type**: `calibration`
- **Vehicle Section**: `ground_network`
- **Affected Services**: sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), fuel-system (AWS us-east-1), navigation (GCP us-central1)

## Subsystem Context

The validation subsystem calibration management system maintains reference baselines for all onboard and ground sensors. Each calibration baseline has an epoch timestamp indicating when it was generated. The sensor-validator service (Azure) compares live sensor readings against these baselines for anomaly detection. When a calibration epoch becomes stale (typically beyond 24 hours or after significant environmental changes), the baseline may no longer be valid, causing either missed detections (false negatives) or spurious alarms (false positives). The impact cascades to fuel-system and navigation because those services rely on validated sensor data for critical operations.

## Common Root Causes

### 1. Launch Delay Without Recalibration
**Probability**: High
**Description**: When a launch is delayed (scrub, weather hold, technical hold), the calibration baselines established during the original pre-launch checkout become progressively staler. Many calibrations are time-sensitive due to thermal drift, sensor aging, and environmental changes.
**Diagnostic Steps**:
- Check the time delta between the calibration epoch and the current time
- Verify if a launch delay or hold has occurred since the last calibration cycle
- Identify which sensor categories have exceeded their maximum calibration age

### 2. Calibration Store Synchronization Failure
**Probability**: Medium
**Description**: The calibration store is distributed across cloud regions for low-latency access. Synchronization failures between the master store (Azure) and replica stores (AWS, GCP) can cause services to use outdated calibration data.
**Diagnostic Steps**:
- Check calibration store replication status and lag between master and replicas
- Compare calibration epochs reported by sensor-validator (Azure) versus fuel-system (AWS) and navigation (GCP)
- Look for network connectivity issues between the calibration store instances

### 3. Incomplete Calibration Cycle
**Probability**: Medium
**Description**: A calibration cycle that was interrupted (by a power glitch, software error, or operator cancellation) may have updated some sensors but not others, leaving the calibration set in an inconsistent state.
**Diagnostic Steps**:
- Check the calibration cycle completion log for any partial or failed calibration runs
- Verify if the epoch mismatch affects all sensors or only a specific subset
- Review the calibration orchestrator logs for error messages or timeout events

### 4. Clock Synchronization Error
**Probability**: Low
**Description**: If the NTP time synchronization between the calibration system and the sensor-validator is skewed, epoch comparisons can produce false mismatch alerts.
**Diagnostic Steps**:
- Check NTP sync status on the calibration system and sensor-validator hosts
- Compare system clocks across all three cloud regions
- Verify if the epoch mismatch is a constant offset (suggesting clock skew) or variable (suggesting real staleness)

## Remediation Procedures

### Immediate Actions
1. **Assess calibration staleness**: Determine which sensors have exceeded their maximum calibration age and the magnitude of the staleness.
2. **Evaluate safety impact**: Determine if stale calibrations affect safety-critical sensor categories (propulsion, FTS, range safety).
3. **Check environmental changes**: Review whether environmental conditions have changed significantly since the last calibration (temperature, humidity, vibration).

### Corrective Actions
1. **Initiate recalibration cycle**: Trigger a fresh calibration cycle for all stale sensors against current reference values.
2. **Synchronize calibration stores**: If replication lag is the cause, force a full synchronization from the master to all replicas.
3. **Adjust staleness thresholds**: If conditions are stable and the calibration drift is within acceptable engineering limits, temporarily extend the maximum age threshold (requires launch director approval).

### Escalation Criteria
- Safety-critical sensor calibrations stale by more than 4 hours: Escalate to launch director
- Calibration store synchronization failed across all regions: Validation integrity compromised, request hold
- Calibration epoch mismatch correlating with thermal drift (Channel 1): Calibration may be actively diverging, escalate immediately

## Historical Precedents

### NOVA-4 24-Hour Launch Delay Calibration Expiry
NOVA-4 was scrubbed and rescheduled for the next day. The pre-launch calibration baselines from the original countdown were not refreshed, causing epoch mismatch alerts across 60% of sensors at T-2:00:00 in the recycled count. Resolution: a complete recalibration cycle was performed, adding 90 minutes to the countdown.

### NOVA-5 Calibration Store Split-Brain
A network partition between Azure regions caused the calibration store to enter a split-brain state where two replicas accepted different calibration updates. Resolution: the partition was resolved, the newer calibration set was promoted as authoritative, and a full resynchronization was completed.

## Related Channels
- Channel 1: Thermal Calibration Drift (calibration accuracy dependency)
- Channel 17: Validation Pipeline Anomaly (validation rule dependency on calibration)
- Channel 4: GPS Multipath Error (navigation calibration)
- Channel 5: IMU Sync Loss (inertial sensor calibration)
