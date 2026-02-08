# Star Tracker Alignment Anomaly — Root Cause Analysis Guide

## Overview

Star Tracker Alignment Anomaly (Channel 6) occurs when the star tracker optical sensors in the avionics bay report attitude determination errors exceeding the 0.01-degree threshold required for orbital insertion accuracy. This anomaly is detected by the `StarTrackerAlignmentException` error type on `star_tracker` sensors in the `avionics` vehicle section.

## Error Signature

- **Error Type**: `StarTrackerAlignmentException`
- **Sensor Type**: `star_tracker`
- **Vehicle Section**: `avionics`
- **Affected Services**: navigation (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The guidance subsystem relies on two redundant star tracker units mounted in the avionics bay to provide precision attitude reference. Each star tracker captures images of the star field and matches observed star patterns against an onboard catalog to determine vehicle orientation. The navigation service (GCP) fuses star tracker data with IMU measurements to maintain the integrated navigation solution. Alignment errors degrade the guidance solution quality, which directly impacts orbital insertion accuracy.

## Common Root Causes

### 1. Stray Light Contamination
**Probability**: High
**Description**: Sunlight or ground illumination reflecting off vehicle surfaces or the launch tower can enter the star tracker baffle, washing out star images and preventing accurate centroid determination.
**Diagnostic Steps**:
- Check the current sun angle relative to the star tracker boresight and baffle exclusion zone
- Verify launch tower lighting status — bright pad lights during nighttime operations can cause stray light
- Look for periodic pattern in alignment errors correlating with vehicle roll orientation

### 2. Vibration-Induced Image Blur
**Probability**: Medium
**Description**: Mechanical vibrations from ground support equipment, wind loading, or propellant system operations can cause star tracker image blur during the integration period, preventing accurate star centroid measurement.
**Diagnostic Steps**:
- Check vibration data (Channel 11) for elevated levels in the avionics bay
- Verify that the star tracker vibration isolation mounts are performing within specification
- Look for correlation between alignment errors and known vibration sources (e.g., cryogenic pump operations)

### 3. Star Catalog Database Corruption
**Probability**: Low
**Description**: Corruption of the onboard star catalog database can cause the pattern matching algorithm to fail or produce incorrect matches. This can occur due to radiation-induced bit flips or incomplete software upload.
**Diagnostic Steps**:
- Run the star catalog integrity check (CRC validation)
- Compare the number of matched stars per frame against the expected count for the current sky region
- Verify the star catalog version matches the mission-specified version

### 4. Thermal Distortion of Optical Path
**Probability**: Low
**Description**: Temperature gradients across the star tracker optical assembly can cause differential thermal expansion, distorting the optical path and shifting the apparent star positions.
**Diagnostic Steps**:
- Check star tracker housing temperature and temperature gradient between front and rear of the assembly
- Correlate alignment errors with thermal calibration data (Channel 1)
- Verify if errors follow a predictable pattern consistent with thermal distortion modeling

## Remediation Procedures

### Immediate Actions
1. **Switch to backup tracker**: If alignment errors are isolated to one unit, switch primary attitude reference to the redundant star tracker.
2. **Verify exclusion zone compliance**: Confirm that no stray light sources are within the star tracker baffle exclusion cone.
3. **Check tracker health telemetry**: Review star count per frame, centroid quality metrics, and tracking loop status.

### Corrective Actions
1. **Recalibrate alignment**: Command an in-flight alignment calibration using the known star field for the current sidereal time.
2. **Update exclusion zones**: If stray light is the cause, update the sun and Earth exclusion angle parameters.
3. **Fall back to IMU-only navigation**: If both star trackers are compromised, the navigation system can operate on IMU-only mode for up to 30 minutes before attitude drift becomes unacceptable.

### Escalation Criteria
- Alignment error exceeds 0.05 degrees: Escalate to flight dynamics team
- Both star trackers reporting errors simultaneously: Potential systemic issue, request hold
- Alignment error combined with IMU anomaly (Channel 4 or 5): Navigation system integrity at risk, immediate hold

## Historical Precedents

### NOVA-4 Stray Light Event
During NOVA-4 pre-dawn countdown, the star tracker reported intermittent alignment errors every 45 seconds. Root cause was identified as reflection from a rotating beacon on the mobile service tower. Resolution: beacon was deactivated and star tracker recovered nominal tracking within one update cycle.

### NOVA-6 Catalog Version Mismatch
NOVA-6 star tracker was loaded with the previous mission's star catalog during software upload. The catalog was valid but optimized for a different launch window, resulting in reduced star match counts. Resolution: correct catalog was uploaded during a 25-minute hold.

## Related Channels
- Channel 4: GPS Multipath Error (navigation subsystem correlation)
- Channel 5: IMU Sync Loss (inertial navigation dependency)
- Channel 11: Payload Vibration Exceedance (vibration environment)
- Channel 1: Thermal Calibration Drift (optical thermal effects)
