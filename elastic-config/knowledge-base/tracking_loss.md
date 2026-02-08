# Range Tracking Loss — Root Cause Analysis Guide

## Overview

Range Tracking Loss (Channel 20) occurs when the range safety tracking systems lose the ability to determine the vehicle's position and velocity with sufficient accuracy for flight safety decisions. This anomaly is detected by the `TrackingLossException` error type on `radar_tracking` sensors in the `vehicle_wide` vehicle section.

**CRITICAL**: Range tracking losses are ALWAYS flagged as CRITICAL regardless of duration. Continuous tracking is a non-waivable launch commit criterion per range safety regulations.

## Error Signature

- **Error Type**: `TrackingLossException`
- **Sensor Type**: `radar_tracking`
- **Vehicle Section**: `vehicle_wide`
- **Affected Services**: range-safety (Azure eastus), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), navigation (GCP us-central1)

## Subsystem Context

The safety subsystem range tracking network uses multiple C-band tracking radars, GPS-based tracking, and optical tracking cameras to provide independent position and velocity data for the vehicle. This data is used by the Mission Flight Control Officer (MFCO) to determine if the vehicle is within the planned flight corridor and to make flight termination decisions if it deviates. The range-safety service (Azure) fuses data from multiple tracking sources and computes the Instantaneous Impact Point (IIP). Loss of tracking means the range cannot verify the vehicle is flying safely, which is an automatic hold/termination condition during flight.

## Common Root Causes

### 1. Radar Transponder Signal Loss
**Probability**: High
**Description**: The vehicle carries C-band radar transponders that amplify and return the ground radar signal. Signal loss can occur due to antenna pattern nulls during vehicle roll, transponder power issues, or ground radar transmitter faults.
**Diagnostic Steps**:
- Check which ground radar sites have lost track and which still have valid returns
- Verify vehicle transponder power status and antenna coverage geometry
- Correlate tracking loss with vehicle attitude — roll maneuvers can cause temporary antenna nulls

### 2. Ground Radar Equipment Failure
**Probability**: Medium
**Description**: Mechanical or electronic failure in the ground tracking radar (antenna servo, transmitter, receiver, signal processor) can cause loss of track independent of vehicle health.
**Diagnostic Steps**:
- Check radar system Built-In Test Equipment (BITE) status and fault indicators
- Verify if tracking loss is on a single radar or multiple radars simultaneously
- Test radar capability using the fixed calibration transponder target

### 3. Weather Interference
**Probability**: Medium
**Description**: Heavy precipitation, particularly within the radar beam path, can attenuate the tracking signal and create clutter that confuses the radar tracking algorithms.
**Diagnostic Steps**:
- Check weather data (Channel 15) for precipitation along the radar-to-vehicle path
- Verify if weather radar shows rain cells between the tracking radar and the vehicle
- Compare tracking quality across radars at different locations with different weather exposure

### 4. GPS Tracking Receiver Interference
**Probability**: Low
**Description**: GPS-based tracking on the vehicle can be affected by ionospheric scintillation, multipath from the vehicle structure, or RF interference from other onboard systems.
**Diagnostic Steps**:
- Check GPS receiver signal-to-noise ratio and number of tracked satellites
- Verify if GPS tracking loss correlates with known interference sources
- Compare GPS-derived position with radar-derived position for consistency

## Remediation Procedures

### Immediate Actions
1. **MANDATORY HOLD**: Any tracking loss during countdown requires an immediate hold per range safety regulations.
2. **Assess tracking source status**: Determine which tracking sources (radar, GPS, optical) are available and which have lost track.
3. **Notify MFCO**: The Mission Flight Control Officer must be immediately informed of any tracking anomaly.

### Corrective Actions
1. **Radar recovery**: If a ground radar has lost track, attempt to reacquire using the last known position and predicted trajectory.
2. **Activate backup radar**: Bring additional tracking radar sites online to provide coverage.
3. **GPS troubleshooting**: If GPS tracking is affected, verify antenna connections and check for interference sources.

### Escalation Criteria
- ANY tracking loss: Automatic escalation to MFCO and range safety officer (mandatory)
- Tracking loss on two or more radar sites simultaneously: Potential vehicle transponder failure, launch scrubbed
- Tracking loss combined with FTS fault (Channel 19): Both safety systems compromised, immediate safing and scrub
- Tracking loss during flight: Automatic flight termination criteria engagement per range safety rules

## Historical Precedents

### NOVA-3 Radar Antenna Servo Failure
During NOVA-3 countdown at T-5:00, the primary C-band tracking radar experienced an antenna servo failure, losing the ability to track the vehicle. Resolution: backup radars confirmed vehicle tracking coverage was maintained by the two remaining radar sites. The failed radar's antenna drive motor was replaced during the next pad access.

### NOVA-5 Transponder Antenna Null During Roll Test
During the NOVA-5 vehicle roll checkout, the C-band transponder signal was lost for 8 seconds as the vehicle rolled through a known antenna pattern null. Resolution: the tracking algorithm was updated to predict and compensate for the known null pattern during roll maneuvers. GPS tracking provided gap-fill during the null.

### NOVA-6 Ionospheric Scintillation GPS Dropout
NOVA-6 GPS tracking experienced intermittent dropouts during a period of high ionospheric scintillation activity (geomagnetic storm). Resolution: GPS tracking was supplemented with additional radar tracking allocation, and the launch window was adjusted to a period of predicted lower scintillation.

## Related Channels
- Channel 19: FTS Safety Check (range safety system correlation)
- Channel 15: Weather Data Gap (radar propagation dependency)
- Channel 6: Star Tracker Alignment (vehicle attitude reference for antenna patterns)
- Channel 7: S-Band Signal Degradation (RF propagation conditions)
