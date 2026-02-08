# Hydraulic Pressure Anomaly — Root Cause Analysis Guide

## Overview

Hydraulic Pressure Anomaly (Channel 16) occurs when the launch pad hydraulic systems detect pressure deviations outside the nominal 3000 PSI (+/- 150 PSI) operating range, affecting thrust vector control (TVC) actuators and launch platform mechanisms. This anomaly is detected by the `HydraulicPressureException` error type on `hydraulic` sensors in the `launch_pad` vehicle section.

## Error Signature

- **Error Type**: `HydraulicPressureException`
- **Sensor Type**: `hydraulic`
- **Vehicle Section**: `launch_pad`
- **Affected Services**: ground-systems (AWS us-east-1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The ground subsystem hydraulic system provides high-pressure hydraulic fluid to multiple users including the engine thrust vector control (TVC) actuators, launch platform hold-down clamps, umbilical retraction mechanisms, and mobile service tower positioning. The system operates at 3000 PSI and is supplied by redundant hydraulic power units (HPUs). The ground-systems service (AWS) monitors pressure, temperature, and flow rates throughout the hydraulic distribution network. Hydraulic pressure anomalies can directly affect engine gimbal capability during launch and the release sequence during liftoff.

## Common Root Causes

### 1. Hydraulic Pump Cavitation
**Probability**: High
**Description**: Air entrainment in the hydraulic fluid or insufficient fluid level in the reservoir can cause the hydraulic pumps to cavitate, resulting in pressure fluctuations and reduced output pressure.
**Diagnostic Steps**:
- Check hydraulic reservoir fluid level against the minimum operating level
- Listen for characteristic cavitation noise from the HPU (if audio monitoring is available)
- Look for rapid pressure oscillations characteristic of cavitation (10-100 Hz)

### 2. Accumulator Pre-Charge Loss
**Probability**: Medium
**Description**: Hydraulic accumulators maintain pressure during transient demand spikes. Loss of nitrogen pre-charge in an accumulator reduces its effectiveness, causing pressure dips during actuator movements.
**Diagnostic Steps**:
- Check accumulator pre-charge pressure readings
- Look for pressure dips that correlate with actuator commands (TVC slew tests, clamp operations)
- Verify last accumulator pre-charge service date

### 3. Hydraulic Fluid Temperature Excursion
**Probability**: Medium
**Description**: Hydraulic fluid viscosity is temperature-dependent. Extreme temperatures (too hot from continuous operation or too cold from ambient conditions) can degrade system performance and cause pressure deviations.
**Diagnostic Steps**:
- Check hydraulic fluid temperature at the HPU and at key distribution points
- Verify heat exchanger operation (if fluid is overheating)
- Correlate pressure deviations with ambient temperature (cold weather can cause sluggish response)

### 4. Servo Valve Sticking
**Probability**: Low
**Description**: Contamination particles in the hydraulic fluid can cause servo valves in the TVC actuators to stick, creating localized pressure spikes or drops in the actuator circuits.
**Diagnostic Steps**:
- Check hydraulic fluid contamination level from the most recent sample analysis
- Look for pressure anomalies isolated to specific actuator circuits
- Verify servo valve response during the most recent TVC slew test

## Remediation Procedures

### Immediate Actions
1. **Verify redundancy**: Confirm that the backup HPU is ready for immediate activation if the primary system fails.
2. **Check fluid level and temperature**: Verify hydraulic reservoir level is adequate and fluid temperature is within operating range.
3. **Monitor TVC readiness**: Verify that TVC actuator response is acceptable for the current mission phase.

### Corrective Actions
1. **Switch to backup HPU**: If the primary HPU is the source of the pressure anomaly, switch to the backup unit.
2. **Recharge accumulator**: If accumulator pre-charge is low, initiate a nitrogen recharge procedure.
3. **Flush and filter**: If contamination is suspected, activate the auxiliary filtration loop to clean the fluid.

### Escalation Criteria
- Pressure deviation exceeds 300 PSI from nominal: TVC actuator performance may be degraded, escalate to propulsion team
- Both HPUs showing anomalies: No hydraulic redundancy, request hold
- Pressure anomaly during TVC slew test: Engine gimbal capability at risk, escalate to launch director

## Historical Precedents

### NOVA-4 Accumulator Pre-Charge Loss
During NOVA-4 engine gimbal testing at T-45:00, the TVC hydraulic pressure dropped 400 PSI during a rapid slew command. Investigation revealed the engine-side accumulator had lost 30% of its nitrogen pre-charge. Resolution: accumulator was recharged during a 20-minute hold. TVC slew test was repeated successfully.

### NOVA-6 Hydraulic Fluid Contamination
NOVA-6 experienced intermittent TVC servo valve sticking during countdown, causing erratic pressure readings. Post-event analysis found metallic particles from a worn pump bearing. Resolution: HPU was switched to the backup unit and the primary HPU pump was replaced.

## Related Channels
- Channel 3: Oxidizer Flow Rate Deviation (MOV actuator hydraulic dependency)
- Channel 14: Power Bus Fault (HPU motor power supply)
- Channel 9: UHF Antenna Pointing (gimbal actuator similarity)
- Channel 19: FTS Safety Check (TVC functionality for flight safety)
