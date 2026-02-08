# Fuel Pressure Anomaly — Root Cause Analysis Guide

## Overview

Fuel Pressure Anomaly (Channel 2) occurs when fuel tank pressure sensors detect readings outside the nominal operating envelope of 28-32 PSI during pre-launch and countdown phases. This anomaly is detected by the `FuelPressureException` error type on `pressure` sensors in the `fuel_tanks` vehicle section.

## Error Signature

- **Error Type**: `FuelPressureException`
- **Sensor Type**: `pressure`
- **Vehicle Section**: `fuel_tanks`
- **Affected Services**: fuel-system (AWS us-east-1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), range-safety (Azure eastus)

## Subsystem Context

The propulsion subsystem fuel pressure monitoring network consists of redundant pressure transducers distributed across the RP-1 fuel tank, LOX tank, and feed lines. The fuel-system service (AWS) aggregates readings at 10 Hz and forwards them to sensor-validator (Azure) for cross-check against expected pressure profiles. Pressure deviations can indicate tank structural issues, valve malfunctions, or helium pressurant system failures.

## Common Root Causes

### 1. Helium Pressurant Regulator Drift
**Probability**: High
**Description**: The helium pressurant system that maintains fuel tank ullage pressure can experience regulator drift due to thermal effects or mechanical wear. This causes a slow, steady deviation from the setpoint.
**Diagnostic Steps**:
- Check helium supply pressure and regulator outlet pressure trends over the past 30 minutes
- Compare tank ullage pressure against the helium flow rate — rising flow with stable pressure indicates a leak
- Verify regulator calibration status from the last ground checkout

### 2. Fuel Loading Thermal Transient
**Probability**: Medium
**Description**: During cryogenic propellant loading, thermal gradients in the fuel tank cause localized pressure variations. Sensors in warmer zones may read higher than sensors near the fill point.
**Diagnostic Steps**:
- Check if the anomaly coincides with active fuel loading or topping operations
- Compare multiple pressure sensors at different tank locations for gradient patterns
- Review fuel temperature profiles for expected thermal stratification

### 3. Pressure Transducer Fault
**Probability**: Medium
**Description**: A faulty pressure transducer providing incorrect readings. May be caused by diaphragm damage, electrical noise, or connector corrosion from pad environment exposure.
**Diagnostic Steps**:
- Isolate the specific sensor(s) reporting anomalous values
- Compare against redundant sensors in the same tank zone
- Check sensor self-test diagnostics and last calibration date

### 4. Vent Valve Partial Opening
**Probability**: Low
**Description**: A fuel tank vent valve that is not fully sealed can cause slow pressure bleed-down. This is especially dangerous if undetected during countdown.
**Diagnostic Steps**:
- Check vent valve position indicators for fully closed status
- Monitor pressure decay rate — a linear decay suggests a leak rather than sensor error
- Cross-reference with ground camera imagery of the vent stack for visible propellant vapor

## Remediation Procedures

### Immediate Actions
1. **Cross-check redundant sensors**: Verify the pressure anomaly is confirmed by at least two independent transducers in the same zone.
2. **Check pressurant system**: Verify helium supply pressure and regulator output are within normal parameters.
3. **Monitor rate of change**: Determine if pressure is diverging, stable, or recovering. Divergence > 0.5 PSI/minute warrants escalation.

### Corrective Actions
1. **Adjust pressurant regulator**: If regulator drift is confirmed, command a setpoint adjustment through the ground control system.
2. **Recalibrate sensor**: If a single sensor is suspect, trigger recalibration using the sensor-validator baseline reference.
3. **Verify vent valve sealing**: Command a vent valve cycle (close-open-close) to reseat the valve if partial opening is suspected.

### Escalation Criteria
- Pressure deviation exceeds 5 PSI from nominal: Escalate to launch director
- Pressure trending toward structural limit: Immediate hold and safing
- Correlation with thermal calibration drift (Channel 1): Potential engine bay thermal event, request hold

## Historical Precedents

### NOVA-4 Pressurant Regulator Failure
During NOVA-4 countdown at T-30:00, fuel tank pressure dropped 3.2 PSI over 10 minutes due to a helium pressurant regulator that stuck in a partially open bypass mode. Resolution: regulator was commanded to backup mode and pressure recovered. Launch proceeded after 15-minute hold.

### NOVA-6 Vent Valve Ice Blockage
In the NOVA-6 pre-launch sequence, ice formation on the LOX tank vent valve prevented full closure, causing a slow pressure decay. Resolution: ground crew applied heated nitrogen purge to the valve assembly. Countdown recycled to T-60:00.

## Related Channels
- Channel 1: Thermal Calibration Drift (engine bay thermal dependency)
- Channel 3: Oxidizer Flow Rate Deviation (propulsion system correlation)
- Channel 14: Power Bus Fault (ground pressurant system power)
- Channel 19: FTS Safety Check (safety system integration)
