# Payload Vibration Exceedance — Root Cause Analysis Guide

## Overview

Payload Vibration Exceedance (Channel 11) occurs when accelerometers in the payload bay detect vibration levels exceeding the payload envelope specification, risking damage to sensitive payload instrumentation and satellite hardware. This anomaly is detected by the `PayloadVibrationException` error type on `vibration` sensors in the `payload_bay` vehicle section.

## Error Signature

- **Error Type**: `PayloadVibrationException`
- **Sensor Type**: `vibration`
- **Vehicle Section**: `payload_bay`
- **Affected Services**: payload-monitor (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), range-safety (Azure eastus)

## Subsystem Context

The payload subsystem is housed in the payload fairing at the top of the vehicle and is connected to the vehicle through the payload adapter fitting (PAF). Tri-axial accelerometers at multiple locations on the payload and PAF measure vibration in the axial, lateral, and torsional axes. The payload-monitor service (GCP) performs real-time spectral analysis and compares vibration levels against the payload coupled loads analysis (CLA) envelope. Vibration exceedances can damage solar panels, optical instruments, antennas, and other sensitive payload components.

## Common Root Causes

### 1. Wind-Induced Oscillation
**Probability**: High
**Description**: Surface winds and upper-level wind shear can excite structural resonances of the launch vehicle on the pad, particularly the first bending mode. The payload, being at the tip, experiences amplified oscillation.
**Diagnostic Steps**:
- Check weather data (Channel 15) for current wind speed and direction at various altitudes
- Verify if vibration frequency matches known structural modes (typically 1-5 Hz for the first bending mode)
- Check if vibration correlates with wind gust patterns from the meteorological tower

### 2. Ground Support Equipment Coupling
**Probability**: Medium
**Description**: Vibrations from ground support equipment (hydraulic pumps, cryogenic transfer systems, umbilical retraction mechanisms) can couple into the vehicle structure and propagate to the payload bay.
**Diagnostic Steps**:
- Identify which ground equipment is currently operating
- Check if vibration exceedances correlate with specific GSE activation events
- Verify vibration isolation mounts between the vehicle and launch platform are functioning

### 3. Propellant Slosh Resonance
**Probability**: Medium
**Description**: Liquid propellant slosh in partially filled tanks can generate lateral forces at frequencies that couple with the vehicle structural modes, amplifying vibration at the payload.
**Diagnostic Steps**:
- Check current propellant fill levels and slosh baffle effectiveness
- Look for vibration frequency content matching predicted slosh modes for current fill level
- Verify if vibration worsens during propellant loading or topping operations

### 4. Payload Adapter Fitting Anomaly
**Probability**: Low
**Description**: A loose or improperly torqued bolt in the PAF can create a local compliance that amplifies certain vibration frequencies and may cause rattling or impact loading.
**Diagnostic Steps**:
- Check for broadband vibration content characteristic of loose hardware
- Compare vibration signatures at different PAF sensor locations for localized anomalies
- Review PAF assembly and torque verification records from payload integration

## Remediation Procedures

### Immediate Actions
1. **Assess severity**: Compare measured vibration spectral levels against the payload CLA envelope at each frequency band to determine which frequencies are exceeding limits.
2. **Identify source**: Determine if vibration is environmental (wind), operational (GSE), or structural (slosh, loose hardware).
3. **Monitor trend**: Track peak vibration levels over time to determine if the exceedance is transient or sustained.

### Corrective Actions
1. **Wind mitigation**: If wind-induced, verify wind constraints are met for launch. Consider rotating the vehicle on the pad if the wind direction is unfavorable.
2. **GSE isolation**: Shut down non-essential ground equipment contributing to vibration coupling.
3. **Propellant management**: If slosh is the cause, adjust propellant loading rate or temporarily halt loading to allow slosh to dampen.

### Escalation Criteria
- Vibration exceeds 150% of CLA envelope at any frequency: Escalate to payload integration team
- Sustained vibration above 120% for more than 60 seconds: Potential fatigue damage, request payload health assessment
- Vibration correlated with structural anomaly indicators: Escalate to vehicle structures team, request hold

## Historical Precedents

### NOVA-4 Wind Shear Vibration Event
During NOVA-4 countdown at T-2:00:00, high-altitude wind shear caused first bending mode vibration that exceeded the payload envelope by 130% at 2.3 Hz for 40 seconds. Resolution: countdown held until wind profile improved. Launch window was extended by 30 minutes.

### NOVA-6 GSE Pump Coupling
NOVA-6 payload accelerometers detected unexpected 60 Hz vibration during propellant loading. Root cause was a hydraulic pump on the mobile service tower with a failed vibration isolator. Resolution: pump was shut down and isolator replaced during a planned hold.

## Related Channels
- Channel 1: Thermal Calibration Drift (vehicle structural thermal effects)
- Channel 6: Star Tracker Alignment (vibration affecting optical systems)
- Channel 15: Weather Data Gap (wind data for vibration source identification)
- Channel 19: FTS Safety Check (structural integrity monitoring)
