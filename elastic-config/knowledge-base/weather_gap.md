# Weather Data Gap — Root Cause Analysis Guide

## Overview

Weather Data Gap (Channel 15) occurs when the meteorological data collection system experiences interruptions, causing gaps in weather observations critical for launch commit criteria evaluation. This anomaly is detected by the `WeatherDataGapException` error type on `weather` sensors in the `launch_pad` vehicle section.

## Error Signature

- **Error Type**: `WeatherDataGapException`
- **Sensor Type**: `weather`
- **Vehicle Section**: `launch_pad`
- **Affected Services**: ground-systems (AWS us-east-1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), range-safety (Azure eastus)

## Subsystem Context

The ground subsystem meteorological monitoring network includes surface weather stations at the launch pad and surrounding area, upper-air sounding balloons, wind profilers, and lightning detection systems. Weather data is critical for evaluating launch commit criteria including wind limits, precipitation, lightning standoff distances, and cloud cover. The ground-systems service (AWS) aggregates data from all weather instruments and provides real-time weather assessments. Data gaps can prevent the launch weather officer from certifying that launch commit criteria are met.

## Common Root Causes

### 1. Weather Station Communication Failure
**Probability**: High
**Description**: The weather stations communicate via serial links or wireless connections that can be disrupted by the very weather conditions they are measuring — heavy rain, high winds, or lightning-induced EMI.
**Diagnostic Steps**:
- Check communication link status for each weather station
- Verify if the gap affects specific stations or all stations simultaneously
- Correlate the gap timing with severe weather events that could disrupt communications

### 2. Sensor Power Supply Interruption
**Probability**: Medium
**Description**: Remote weather stations rely on local power supplies (solar panels with battery backup). Extended cloudy periods or battery degradation can cause power failures.
**Diagnostic Steps**:
- Check battery voltage and solar panel output for affected stations
- Verify if the data gap correlates with the station's known battery endurance
- Review power bus status (Channel 14) for pad-powered weather instruments

### 3. Data Acquisition System Overload
**Probability**: Medium
**Description**: During rapidly changing weather conditions, the data acquisition system may be overwhelmed by high-rate data from multiple instruments, causing buffer overflows and data loss.
**Diagnostic Steps**:
- Check data acquisition system CPU utilization and buffer levels
- Verify if the gap affects all instruments or only specific data types
- Look for correlation with periods of rapidly changing weather conditions

### 4. Balloon Sounding Failure
**Probability**: Low
**Description**: Upper-air weather data from radiosonde balloons can be lost if the balloon bursts prematurely, the radiosonde malfunctions, or the tracking antenna loses signal.
**Diagnostic Steps**:
- Check the most recent balloon launch time and current altitude
- Verify radiosonde signal strength and data quality indicators
- Determine if the gap is in surface data (station issue) or upper-air data (balloon issue)

## Remediation Procedures

### Immediate Actions
1. **Identify gap scope**: Determine which weather parameters are affected and whether launch commit criteria can still be evaluated with available data.
2. **Check backup sources**: Verify availability of backup weather data from regional airports, NWS stations, or satellite-derived products.
3. **Assess weather stability**: If current conditions are well within launch commit criteria limits and stable, short data gaps may be acceptable.

### Corrective Actions
1. **Reset communication links**: Cycle power or reinitialize communication links to affected weather stations.
2. **Launch supplemental balloon**: If upper-air data is missing, request an additional radiosonde launch.
3. **Activate backup stations**: Bring online any standby weather instruments in the network.

### Escalation Criteria
- Data gap exceeds 15 minutes for any launch commit criterion parameter: Escalate to launch weather officer
- No upper-air wind data within 2 hours of launch: Cannot evaluate upper-level wind shear criteria, request hold
- Lightning detection system offline: Cannot evaluate lightning standoff criteria, immediate hold per range safety rules

## Historical Precedents

### NOVA-3 Weather Station Network Failure
During NOVA-3 countdown, a thunderstorm-induced power surge took out the primary data acquisition system for the weather station network, causing a 20-minute data gap across all surface stations. Resolution: backup data acquisition system was brought online and regional airport data was used to bridge the gap. Launch delayed 35 minutes.

### NOVA-5 Radiosonde Tracking Loss
The pre-launch radiosonde balloon for NOVA-5 was lost at 12 km altitude when high upper-level winds carried it out of the tracking antenna range. Resolution: a second balloon was launched from a downwind location with extended tracking capability. Upper-air data was restored within 45 minutes.

## Related Channels
- Channel 7: S-Band Signal Degradation (atmospheric conditions correlation)
- Channel 11: Payload Vibration Exceedance (wind loading dependency)
- Channel 14: Power Bus Fault (weather station power)
- Channel 20: Range Tracking Loss (weather affecting radar operations)
