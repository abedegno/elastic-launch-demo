# Payload Thermal Excursion — Root Cause Analysis Guide

## Overview

Payload Thermal Excursion (Channel 10) occurs when the payload bay temperature deviates outside the safe operating range defined by the payload manufacturer. The payload bay contains sensitive satellite hardware, optical instruments, and electronics that are intolerant of temperature extremes. This anomaly is detected by the `PayloadThermalException` error type on `thermal` sensors in the `payload_bay` vehicle section.

## Error Signature

- **Error Type**: `PayloadThermalException`
- **Sensor Type**: `thermal`
- **Vehicle Section**: `payload_bay`
- **Affected Services**: payload-monitor (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1)

## Subsystem Context

The payload bay is thermally isolated from the rest of the vehicle by multi-layer insulation (MLI) blankets and an active thermal control system (TCS). The TCS uses heaters and cold plates to maintain the payload bay within the safe operating range, typically -10C to +45C for most satellite payloads. Four thermal zones (A, B, C, D) are independently monitored, each with redundant thermal sensors.

The payload-monitor service (running on GCP us-central1) processes thermal telemetry at 1 Hz per zone and commands the TCS heaters. The sensor-validator service cross-checks thermal readings for consistency across redundant sensors.

## Thermal Zone Layout

| Zone | Location | Sensors | Critical Components |
|------|----------|---------|---------------------|
| A | Forward payload adapter | 4 RTDs | Payload separation mechanism |
| B | Mid-bay starboard | 4 RTDs | Primary satellite electronics |
| C | Mid-bay port | 4 RTDs | Optical payload, star tracker |
| D | Aft payload adapter | 4 RTDs | Umbilical connections, harness |

## Common Root Causes

### 1. Solar Heating After Fairing/Tower Retraction
**Probability**: High
**Description**: When the mobile service tower is retracted or if the payload fairing has not yet been installed, direct solar radiation can heat the payload bay structure beyond TCS capacity. This is the most common cause of thermal excursions during pre-launch operations.
**Diagnostic Steps**:
- Check current tower position and fairing status
- Verify solar angle and time of day
- Compare Zone A (forward) and Zone D (aft) temperatures for asymmetric heating
- Review weather station data (Channel 15) for cloud cover

### 2. TCS Heater Malfunction
**Probability**: Medium
**Description**: A stuck-on heater can overheat a zone, or a failed heater can allow a zone to cool below the minimum temperature (especially during nighttime or cryogenic fuel loading).
**Diagnostic Steps**:
- Check TCS heater duty cycle telemetry for the affected zone
- Verify heater command state vs. actual power draw
- Look for heater cycling frequency anomalies (stuck-on shows 100% duty cycle)
- Check ground power bus (Channel 14) for voltage issues affecting heater circuits

### 3. Cryogenic Propellant Loading Thermal Bleed
**Probability**: Medium
**Description**: During fuel loading, the extreme cold of cryogenic propellants (LOX at -183C, LH2 at -253C) can conduct through the vehicle structure into the payload bay, especially through mounting brackets and structural members that bridge the thermal isolation.
**Diagnostic Steps**:
- Check if fuel loading is in progress or recently completed
- Look for correlation with fuel system events (Channel 2)
- Verify Zone D (aft, closest to fuel tanks) is the coldest zone
- Check thermal gradient across zones for conduction pattern

### 4. MLI Blanket Damage
**Probability**: Low
**Description**: Physical damage to multi-layer insulation blankets during payload integration or handling allows thermal shorts between the payload bay and the vehicle structure or external environment.
**Diagnostic Steps**:
- Check if excursion is localized to a specific zone
- Review pre-launch MLI inspection records
- Look for sudden thermal changes that would indicate a loss of insulation
- Compare with vibration data (Channel 11) for mechanical damage

### 5. Payload Internal Heat Dissipation
**Probability**: Low
**Description**: If the payload's internal electronics are powered on and generating heat beyond the TCS design capacity, the bay temperature rises. This can happen if the payload is in an unexpected operating mode.
**Diagnostic Steps**:
- Check payload power state and operating mode
- Verify payload heat dissipation rate against TCS capacity
- Look for payload mode change commands in the timeline

## Remediation Procedures

### Immediate Actions
1. **Identify affected zone**: Determine which of the four zones (A, B, C, D) is out of range and the direction of the excursion (too hot or too cold).
2. **Verify redundant sensors**: Compare readings across all 4 RTDs in the affected zone to rule out sensor error.
3. **Check TCS status**: Verify that the thermal control system is commanding the correct heater/cold plate states for the affected zone.

### For Overheating (temp > +45C)
1. **Increase cold plate flow**: Command increased coolant flow to the affected zone's cold plates.
2. **Reduce payload power**: If the payload is generating excess heat, command it to a lower power mode.
3. **Deploy thermal shade**: If solar heating is the cause and the tower is retracted, consider deploying the auxiliary thermal shade.
4. **Pause operations**: If cryogenic loading is driving thermal gradients, pause loading to allow the TCS to recover.

### For Overcooling (temp < -10C)
1. **Activate backup heaters**: Enable redundant heater circuits for the affected zone.
2. **Verify power supply**: Check ground power bus (Channel 14) to ensure heaters are receiving adequate power.
3. **Increase heater setpoint**: Temporarily raise the heater setpoint to provide additional thermal margin.

### Escalation Criteria
- Any zone exceeds +55C: Escalate to launch director, potential payload damage
- Any zone drops below -20C: Escalate to launch director, potential damage to electronics and optics
- Multiple zones simultaneously out of range: TCS failure, request hold
- Thermal excursion combined with vibration anomaly (Channel 11): Potential structural/MLI damage, request hold
- Rate of temperature change exceeds 5C/minute: Thermal runaway, immediate hold

## Payload Safety Constraints

The payload for NOVA-7 has the following thermal constraints defined by the payload manufacturer:

| Parameter | Limit | Notes |
|-----------|-------|-------|
| Operating range | -10C to +45C | All zones must be within range at launch |
| Non-operating range | -25C to +60C | Allowable during transport, not during powered operations |
| Rate of change | < 3C/minute | Thermal shock protection for optics |
| Gradient across zones | < 15C | Maximum allowed difference between any two zones |
| Time out of range | < 30 minutes | Cumulative time outside operating range before launch commit violation |

Exceeding any non-operating limit is a mandatory launch hold.

## Historical Precedents

### NOVA-5 Solar Heating Event
During NOVA-5 at T-180:00, Zone A temperature rose to 52C after the mobile service tower retracted under clear skies. The auxiliary thermal shade was deployed within 10 minutes, and the TCS recovered the zone to 38C within 20 minutes. Lesson learned: tower retraction should be timed to avoid peak solar angles, and the auxiliary shade should be pre-positioned.

### NOVA-6 Heater Stuck-On Event
NOVA-6 experienced a stuck-on heater in Zone C at T-60:00. The heater relay failed closed, driving the zone to 48C before the anomaly was detected. Resolution: the affected heater circuit was isolated, backup heaters in the zone were activated, and the TCS maintained the zone within limits. Root cause: relay contact welding due to inrush current. Post-mission action: current-limiting resistors added to all heater circuits.

## Related Channels
- Channel 1: Thermal Calibration Drift (sensor calibration dependency)
- Channel 2: Fuel Pressure Anomaly (cryogenic loading correlation)
- Channel 11: Payload Vibration Anomaly (structural integrity check)
- Channel 14: Ground Power Bus Fault (heater power supply)
- Channel 15: Weather Station Data Gap (environmental conditions)
