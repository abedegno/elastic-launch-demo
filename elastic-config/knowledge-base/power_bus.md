# Power Bus Fault — Root Cause Analysis Guide

## Overview

Power Bus Fault (Channel 14) occurs when the ground power distribution system detects voltage or current anomalies on the electrical buses supplying the launch pad and vehicle ground support equipment. This anomaly is detected by the `PowerBusFaultException` error type on `electrical` sensors in the `launch_pad` vehicle section.

## Error Signature

- **Error Type**: `PowerBusFaultException`
- **Sensor Type**: `electrical`
- **Vehicle Section**: `launch_pad`
- **Affected Services**: ground-systems (AWS us-east-1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), fuel-system (AWS us-east-1)

## Subsystem Context

The ground subsystem power distribution network supplies electrical power to all launch pad equipment including propellant loading systems, hydraulic systems, environmental control, pad lighting, and the vehicle umbilical connections. The ground-systems service (AWS) monitors power bus voltage, current, frequency, and power factor across multiple distribution panels. Power bus faults can cascade to affect propellant loading (fuel-system), hydraulic systems (Channel 16), and vehicle pre-launch conditioning.

## Common Root Causes

### 1. Load Transient from Propellant Systems
**Probability**: High
**Description**: Large motors in the propellant transfer system (pumps, compressors, valve actuators) draw significant inrush current during startup, causing voltage dips on the power bus that can trip protection thresholds.
**Diagnostic Steps**:
- Correlate power bus voltage dips with propellant system motor startup events
- Check if the affected bus is shared with high-power propellant equipment
- Verify motor soft-start controllers are functioning correctly

### 2. Generator Synchronization Fault
**Probability**: Medium
**Description**: The launch pad is typically powered by redundant generators. When generators fail to maintain synchronization, power quality degrades with voltage fluctuations and frequency variations.
**Diagnostic Steps**:
- Check generator synchronization status and frequency match between units
- Look for power factor variations indicating reactive power imbalance
- Verify generator governor and voltage regulator settings

### 3. Ground Fault in Pad Wiring
**Probability**: Medium
**Description**: Exposure to weather, propellant vapors, and salt air can degrade insulation in pad wiring, causing ground faults that trip protection devices and reduce available power capacity.
**Diagnostic Steps**:
- Check ground fault indicator readings on distribution panels
- Identify which circuit or zone is showing the fault
- Review insulation resistance test results from the most recent pad inspection

### 4. Uninterruptible Power Supply (UPS) Failure
**Probability**: Low
**Description**: Critical systems are protected by UPS units. A UPS internal fault can cause its connected loads to momentarily lose power during the transfer to bypass mode.
**Diagnostic Steps**:
- Check UPS status indicators and battery health
- Verify if the power fault is isolated to UPS-protected circuits
- Review UPS event logs for internal fault codes

## Remediation Procedures

### Immediate Actions
1. **Assess scope**: Determine which buses and loads are affected by the power fault.
2. **Check critical loads**: Verify that safety-critical systems (FTS, range safety, fire suppression) are on uninterrupted power.
3. **Monitor voltage stability**: Track bus voltage and frequency to determine if the fault is transient or sustained.

### Corrective Actions
1. **Shed non-essential loads**: Disconnect non-critical loads from the affected bus to restore voltage within acceptable limits.
2. **Switch to backup generator**: If the primary generator is faulting, transfer to the backup generator or utility power.
3. **Isolate faulted circuit**: If a ground fault is identified, isolate the affected circuit and verify remaining bus integrity.

### Escalation Criteria
- Bus voltage below 90% nominal for more than 30 seconds: Escalate to pad electrical team
- Power loss to propellant system (affects Channel 2, Channel 3): Potential propulsion safety issue, request hold
- Power loss to vehicle umbilical: Vehicle internal batteries engaged, escalate to launch director

## Historical Precedents

### NOVA-4 Generator Synchronization Loss
During NOVA-4 propellant loading, one of three pad generators lost synchronization, causing bus voltage to fluctuate between 440-470V (nominal 460V). Resolution: the out-of-sync generator was taken offline and loads redistributed to the remaining two generators. Propellant loading was paused for 8 minutes.

### NOVA-6 Ground Fault During Rain
A rain event during NOVA-6 countdown caused a ground fault in an outdoor junction box on the pad, tripping a 200A breaker and de-powering the LOX transfer pump. Resolution: the affected junction box was isolated and the LOX pump was transferred to an alternate circuit. Countdown was held for 22 minutes.

## Related Channels
- Channel 2: Fuel Pressure Anomaly (propellant system power dependency)
- Channel 3: Oxidizer Flow Rate Deviation (propellant pump power)
- Channel 15: Weather Data Gap (weather station power)
- Channel 16: Hydraulic Pressure Anomaly (hydraulic pump power)
