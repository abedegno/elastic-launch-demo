# GPS Multipath Interference — Root Cause Analysis Guide

## Overview

GPS Multipath Interference (Channel 4) occurs when the vehicle's GPS receiver detects signal reflections (multipath) that corrupt the position solution. This anomaly is characterized by increased position uncertainty and degraded satellite geometry. It is detected by the `GPSMultipathException` error type on `gps` sensors in the `avionics` vehicle section.

## Error Signature

- **Error Type**: `GPSMultipathException`
- **Sensor Type**: `gps`
- **Vehicle Section**: `avionics`
- **Affected Services**: navigation (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), range-safety (Azure eastus)

## Subsystem Context

The guidance subsystem relies on GPS as one of three primary navigation sources (GPS, IMU, star tracker). The GPS receiver on the avionics bay processes signals from multiple satellites to compute a position fix. In the launch pad environment, large metallic structures (service tower, lightning masts, fuel tanks) can reflect GPS signals, creating multipath interference. The navigation service (running on GCP) fuses GPS data with IMU and star tracker inputs to produce the vehicle state vector.

## Common Root Causes

### 1. Launch Pad Structural Reflections
**Probability**: High
**Description**: GPS signals reflect off the mobile service tower, launch pad structure, or nearby metallic surfaces. This is most pronounced when the tower is in certain positions relative to satellite geometry.
**Diagnostic Steps**:
- Check if multipath correlates with specific satellite PRN numbers
- Verify the position of the mobile service tower (retracted vs. in place)
- Compare GPS pseudorange residuals for reflected vs. direct signals
- Check if the affected satellites are at low elevation angles (< 15 degrees)

### 2. Satellite Geometry Degradation (High DOP)
**Probability**: Medium
**Description**: Poor satellite geometry (high Dilution of Precision) amplifies the effect of multipath errors on the position solution. This can happen during satellite constellation transitions.
**Diagnostic Steps**:
- Check current GDOP/PDOP values from the GPS receiver
- Verify the number of tracked satellites vs. expected constellation
- Review GPS almanac for predicted geometry at the current time

### 3. RF Interference from Ground Systems
**Probability**: Medium
**Description**: Ground-based radio equipment (S-band, UHF communications, radar) can generate harmonics or intermodulation products that fall within GPS frequency bands (L1: 1575.42 MHz, L2: 1227.60 MHz).
**Diagnostic Steps**:
- Check comms-array signal levels (Channels 7, 8, 9) for unusual transmission patterns
- Verify ground radar operations schedule
- Look for correlation between GPS multipath events and communication system activity

### 4. Ionospheric Scintillation
**Probability**: Low
**Description**: Rapid fluctuations in the ionosphere's electron density cause GPS signal amplitude and phase variations that can mimic multipath signatures.
**Diagnostic Steps**:
- Check space weather indices (Kp, S4 scintillation index)
- Verify if multiple ground GPS reference stations also report anomalies
- Compare dual-frequency (L1/L2) measurements for ionospheric signature

## Remediation Procedures

### Immediate Actions
1. **Switch to multipath-resistant mode**: Command the GPS receiver to enable narrow correlator spacing and multipath estimation. This reduces (but does not eliminate) multipath error.
2. **Verify IMU backup**: Confirm the IMU (Channel 5) is providing valid navigation data as a backup. The navigation service should automatically increase IMU weighting when GPS quality degrades.
3. **Exclude affected satellites**: If specific PRNs are identified as multipath sources, exclude them from the position solution.

### Corrective Actions
1. **Elevation mask adjustment**: Increase the satellite elevation mask from the default 10 degrees to 20 degrees to exclude low-elevation satellites that are more prone to multipath.
2. **Navigation filter reinitialization**: If the position uncertainty exceeds 25m, reinitialize the navigation Kalman filter using the IMU-propagated state.
3. **Cross-validate with star tracker**: Request an attitude update from the star tracker (Channel 6) to verify the navigation solution.

### Escalation Criteria
- Position uncertainty exceeds 50m: Escalate to launch director
- All GPS satellites showing multipath: Potential jamming or severe interference, immediate hold
- GPS multipath combined with IMU sync loss (Channel 5): Navigation integrity compromised, request hold
- Less than 4 satellites tracked after multipath exclusion: Insufficient geometry for position fix, request hold

## Impact on Launch Commit Criteria

GPS multipath alone does not typically trigger a launch commit violation, provided:
1. The IMU is providing valid navigation data
2. At least 4 clean satellites remain after multipath exclusion
3. Position uncertainty remains below 30m

If any of these conditions fail, the Range Safety Officer must be notified, and a launch hold should be considered.

## Historical Precedents

### NOVA-3 GPS Multipath During Tower Retraction
During NOVA-3 at T-90:00, GPS multipath spiked when the mobile service tower was at the 45-degree retraction angle. The tower structure created a reflective surface aligned with two GPS satellites (PRN 15, PRN 22). Multipath resolved completely once the tower reached full retraction. Lesson learned: tower retraction timing was adjusted to occur during favorable satellite geometry windows.

### NOVA-6 GPS/IMU Dual Failure
NOVA-6 experienced simultaneous GPS multipath (Channel 4) and IMU sync loss (Channel 5) at T-30:00. Investigation revealed that a ground power bus transient (Channel 14) had reset both the GPS receiver and IMU timing reference. The cascading nature of this failure prompted the development of independent power filtering for navigation sensors.

## Related Channels
- Channel 5: IMU Synchronization Loss (navigation backup)
- Channel 6: Star Tracker Alignment Fault (navigation cross-check)
- Channel 7: S-Band Signal Degradation (RF interference potential)
- Channel 14: Ground Power Bus Fault (power supply dependency)
- Channel 20: Range Safety Tracking Loss (position accuracy dependency)
