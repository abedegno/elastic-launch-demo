# Oxidizer Flow Rate Deviation — Root Cause Analysis Guide

## Overview

Oxidizer Flow Rate Deviation (Channel 3) occurs when LOX (Liquid Oxygen) flow rate sensors in the engine bay detect flow rates that deviate more than 5% from the commanded profile during engine priming or ignition sequences. This anomaly is detected by the `OxidizerFlowException` error type on `flow_rate` sensors in the `engine_bay` vehicle section.

## Error Signature

- **Error Type**: `OxidizerFlowException`
- **Sensor Type**: `flow_rate`
- **Vehicle Section**: `engine_bay`
- **Affected Services**: fuel-system (AWS us-east-1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The propulsion subsystem oxidizer delivery system supplies liquid oxygen from the LOX tank through feed lines, a prevalve, the main oxidizer valve (MOV), and injector manifold to the combustion chamber. Flow rate is measured by turbine flowmeters in the feed lines. The fuel-system service monitors flow rates and compares them against the expected profile for the current mission phase. Oxidizer flow deviations can indicate valve actuator issues, cavitation in the feed system, or injector blockage.

## Common Root Causes

### 1. LOX Feed Line Cavitation
**Probability**: High
**Description**: Cavitation occurs when local pressure in the LOX feed line drops below the oxygen saturation pressure, forming vapor bubbles that disrupt the flow measurement. This is often caused by insufficient tank pressurization or rapid flow transients.
**Diagnostic Steps**:
- Check LOX tank ullage pressure against the minimum net positive suction pressure (NPSP) requirement
- Look for oscillatory patterns in the flow rate data — cavitation produces characteristic high-frequency fluctuations
- Verify helium pressurant system is maintaining adequate tank pressure (correlate with Channel 2)

### 2. Main Oxidizer Valve Position Error
**Probability**: Medium
**Description**: The MOV actuator may not be achieving the commanded position due to hydraulic actuator issues, position sensor drift, or mechanical binding from thermal contraction at cryogenic temperatures.
**Diagnostic Steps**:
- Compare commanded valve position versus actual position feedback
- Check hydraulic pressure to the MOV actuator (correlate with Channel 16)
- Review valve response time against specification limits

### 3. Injector Manifold Ice Formation
**Probability**: Medium
**Description**: Moisture contamination in the LOX can form ice crystals that partially block injector orifices, reducing effective flow area and causing flow rate deviations.
**Diagnostic Steps**:
- Check LOX purity analysis from the most recent propellant quality report
- Look for gradual flow reduction pattern consistent with progressive ice buildup
- Check combustion chamber pressure for asymmetric injection patterns

### 4. Turbine Flowmeter Bearing Wear
**Probability**: Low
**Description**: The turbine flowmeters in the LOX feed lines operate in an extremely cold environment. Bearing wear can cause the turbine to under-spin, reading lower than actual flow.
**Diagnostic Steps**:
- Compare primary and backup flowmeter readings for divergence
- Check flowmeter self-test spin-up and coast-down timing
- Review maintenance history for time since last flowmeter replacement

## Remediation Procedures

### Immediate Actions
1. **Verify tank pressurization**: Confirm LOX tank ullage pressure meets minimum NPSP requirement for current flow demand.
2. **Cross-check flowmeters**: Compare primary and backup flow measurements to isolate sensor error from actual flow deviation.
3. **Check valve positions**: Verify MOV and prevalve are at commanded positions.

### Corrective Actions
1. **Increase tank pressurization**: If cavitation is suspected, command a helium pressurant boost to raise LOX tank pressure by 2-3 PSI.
2. **Cycle MOV**: If valve position error is suspected, command a partial close/open cycle to clear any mechanical binding.
3. **Switch to backup flowmeter**: If primary flowmeter is suspect, transition to backup instrument for flow monitoring.

### Escalation Criteria
- Flow deviation exceeds 10% from commanded profile: Escalate to launch director
- MOV position error exceeds 2 degrees: Potential valve actuator failure, request hold
- Correlation with fuel pressure anomaly (Channel 2): Potential systemic propulsion issue, request hold

## Historical Precedents

### NOVA-3 LOX Cavitation Event
During NOVA-3 engine chill-down at T-15:00, oxidizer flow rates showed 7% deviation with characteristic oscillatory pattern. Root cause was insufficient LOX tank pressurization after a helium regulator transient. Resolution: pressurant system was boosted and flow normalized within 90 seconds.

### NOVA-5 Injector Ice Blockage
NOVA-5 experienced progressive oxidizer flow reduction during the ignition sequence. Post-flight analysis revealed moisture contamination in the LOX delivery from the ground storage facility. Resolution: LOX was drained and replaced with certified dry propellant. Launch delayed 48 hours.

## Related Channels
- Channel 1: Thermal Calibration Drift (engine bay thermal environment)
- Channel 2: Fuel Pressure Anomaly (propulsion system correlation)
- Channel 16: Hydraulic Pressure Anomaly (MOV actuator dependency)
- Channel 19: FTS Safety Check (propulsion safety integration)
