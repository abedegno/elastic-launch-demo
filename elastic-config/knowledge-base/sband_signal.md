# S-Band Signal Degradation — Root Cause Analysis Guide

## Overview

S-Band Signal Degradation (Channel 7) occurs when the S-band communication link between the vehicle and ground stations experiences signal-to-noise ratio (SNR) degradation below the 12 dB threshold required for reliable telemetry and command uplink. This anomaly is detected by the `SignalDegradationException` error type on `rf_signal` sensors in the `antenna_array` vehicle section.

## Error Signature

- **Error Type**: `SignalDegradationException`
- **Sensor Type**: `rf_signal`
- **Vehicle Section**: `antenna_array`
- **Affected Services**: comms-array (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), telemetry-relay (Azure eastus)

## Subsystem Context

The communications subsystem S-band link operates at 2.2 GHz and provides the primary command uplink and real-time telemetry downlink between the vehicle and ground tracking stations. The comms-array service (GCP) manages the onboard transponder, antenna pointing, and link budget calculations. Signal degradation can result in telemetry data gaps and loss of command authority, both of which are critical during launch and ascent phases.

## Common Root Causes

### 1. Atmospheric Attenuation
**Probability**: High
**Description**: Rain, cloud cover, or high humidity along the signal path between the vehicle and ground station can attenuate the S-band signal. Rain rates above 10 mm/hr can cause significant degradation at S-band frequencies.
**Diagnostic Steps**:
- Check weather data (Channel 15) for precipitation and humidity along the ground station line-of-sight
- Verify if degradation correlates with weather radar imagery showing rain cells
- Compare signal levels across multiple ground station receivers — if all degrade simultaneously, atmospheric cause is likely

### 2. Antenna Pointing Error
**Probability**: Medium
**Description**: The vehicle antenna array may not be optimally pointed toward the ground station due to vehicle attitude changes, antenna gimbal drift, or incorrect pointing commands.
**Diagnostic Steps**:
- Check antenna pointing angles versus the expected ground station direction
- Verify vehicle attitude from the navigation solution — pointing error may be a symptom of guidance issues (Channel 6)
- Review antenna gimbal telemetry for position errors or tracking loop instability

### 3. RF Interference
**Probability**: Medium
**Description**: External RF sources operating near the S-band frequency can raise the noise floor and degrade the SNR. Sources include other launch range radars, nearby communication systems, or onboard equipment electromagnetic interference (EMI).
**Diagnostic Steps**:
- Check the RF spectrum monitor data for unexpected signals in the S-band
- Verify that all onboard systems are in their expected EMI configuration for the current mission phase
- Check if the degradation is intermittent and correlates with any periodic RF source

### 4. Transponder Power Amplifier Degradation
**Probability**: Low
**Description**: The onboard S-band transponder power amplifier may be operating below rated output due to aging, thermal stress, or power supply issues.
**Diagnostic Steps**:
- Check transponder output power telemetry against specification
- Monitor transponder temperature — overheating can cause power derating
- Verify power bus voltage to the transponder (correlate with Channel 14)

## Remediation Procedures

### Immediate Actions
1. **Verify ground station tracking**: Confirm ground station antenna is tracking the vehicle correctly and autotrack loop is locked.
2. **Check link budget margin**: Review current link budget calculation to determine remaining margin before loss of signal.
3. **Monitor trend**: Determine if degradation is worsening, stable, or improving. Worsening trend requires immediate action.

### Corrective Actions
1. **Switch ground stations**: If atmospheric attenuation is the cause, hand over to an alternate ground station with better weather conditions.
2. **Increase transponder power**: Command the transponder to high-power mode to increase link margin.
3. **Adjust data rate**: Reduce telemetry data rate to improve bit energy and extend link margin.

### Escalation Criteria
- SNR below 6 dB: Command link at risk, escalate to launch director
- Complete loss of signal for more than 10 seconds: Escalate to range safety
- Correlation with X-band or UHF degradation (Channels 8, 9): Potential systemic antenna or pointing issue

## Historical Precedents

### NOVA-3 Rain Attenuation Event
During NOVA-3 countdown, a rain squall moved through the ground station area, causing S-band SNR to drop to 8 dB for approximately 4 minutes. Resolution: telemetry handover to the downrange station provided uninterrupted coverage. Weather cleared before launch commit.

### NOVA-5 Transponder Thermal Event
NOVA-5 S-band transponder experienced power output reduction due to inadequate thermal control in the avionics bay. Temperature rose to 65C, causing the amplifier to derate by 3 dB. Resolution: avionics bay cooling was increased and transponder temperature stabilized.

## Related Channels
- Channel 8: X-Band Packet Loss (communications subsystem correlation)
- Channel 9: UHF Antenna Pointing Anomaly (antenna array dependency)
- Channel 15: Weather Data Gap (atmospheric conditions)
- Channel 6: Star Tracker Alignment (vehicle attitude dependency)
