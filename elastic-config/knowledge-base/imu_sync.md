# IMU Synchronization Loss — Root Cause Analysis Guide

## Overview

IMU Synchronization Loss (Channel 5) occurs when the Inertial Measurement Unit loses time synchronization with the vehicle's master clock, causing measurement timestamps to drift beyond the acceptable threshold. This anomaly is detected by the `IMUSyncException` error type on `imu` sensors in the `avionics` vehicle section.

## Error Signature

- **Error Type**: `IMUSyncException`
- **Sensor Type**: `imu`
- **Vehicle Section**: `avionics`
- **Affected Services**: navigation (GCP us-central1), sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), range-safety (Azure eastus)

## Subsystem Context

The IMU is the backbone of the guidance subsystem, providing high-rate (1000 Hz) measurements of acceleration and angular rate on all three axes (X, Y, Z). Time synchronization is critical because the navigation filter integrates IMU measurements over precise time intervals to propagate the vehicle state. A clock drift of even a few milliseconds can introduce significant position and velocity errors, especially during the high-dynamics phases of launch and ascent.

The IMU synchronization is maintained by a Pulse-Per-Second (PPS) signal from the GPS receiver, cross-checked against the vehicle's crystal oscillator. The navigation service on GCP processes the IMU data stream and fuses it with GPS and star tracker inputs.

## Common Root Causes

### 1. PPS Signal Loss from GPS
**Probability**: High
**Description**: The GPS receiver provides the primary time reference via its PPS output. If GPS multipath (Channel 4) degrades the receiver's timing accuracy, or if the GPS receiver loses lock, the PPS signal becomes unreliable.
**Diagnostic Steps**:
- Check for concurrent GPS multipath events (Channel 4)
- Verify GPS receiver PPS quality flag in telemetry
- Check the number of satellites used for the timing solution (minimum 4 required)
- Look for GPS receiver reset events in the logs

### 2. Crystal Oscillator Frequency Drift
**Probability**: Medium
**Description**: The IMU's internal crystal oscillator is temperature-sensitive. Rapid temperature changes in the avionics bay can cause frequency drift that exceeds the PPS correction capability.
**Diagnostic Steps**:
- Check avionics bay thermal data for recent temperature changes
- Verify oscillator frequency stability metrics (Allen deviation)
- Compare IMU clock against the backup rubidium reference (if available)
- Check if the drift is consistently on one axis or random

### 3. EMI from Power Bus
**Probability**: Medium
**Description**: Electromagnetic interference from the vehicle or ground power bus can disrupt the digital timing circuits in the IMU. This is often correlated with power bus transients (Channel 14).
**Diagnostic Steps**:
- Check for concurrent power bus fault events (Channel 14)
- Verify IMU power supply voltage ripple
- Look for periodic sync losses that correlate with power system switching events
- Check if shielding integrity was verified during pre-launch checkout

### 4. Software Timing Bug
**Probability**: Low
**Description**: A race condition or buffer overflow in the IMU firmware can cause the timing counter to skip or repeat, producing an apparent sync loss.
**Diagnostic Steps**:
- Check IMU firmware version against the known issue database
- Look for patterns in the sync loss (e.g., always at the same count value)
- Verify IMU self-test results for internal timing checks
- Check if a firmware update was applied recently

## Remediation Procedures

### Immediate Actions
1. **Verify drift magnitude**: Check the reported drift value. Drifts under 5ms are correctable by the navigation filter; drifts over 10ms require intervention.
2. **Check GPS PPS**: Verify that the GPS receiver is providing a valid PPS signal. If GPS is degraded (Channel 4), the IMU must rely on its internal oscillator.
3. **Switch to backup timing**: If the primary PPS source is compromised, switch to the vehicle backup timing reference (rubidium oscillator or ground-provided time mark).

### Corrective Actions
1. **IMU resynchronization**: Command a forced resync of the IMU to the current time reference. This requires a brief (< 100ms) data gap in IMU measurements.
2. **Navigation filter adjustment**: Increase the IMU noise covariance in the navigation Kalman filter to account for timing uncertainty. This will widen the position error bounds but prevent filter divergence.
3. **Cross-reference with star tracker**: Use star tracker attitude measurements (Channel 6) to bound the IMU drift error and verify the navigation solution integrity.

### Escalation Criteria
- IMU drift exceeds 10ms on any axis: Escalate to launch director
- IMU drift combined with GPS multipath (Channel 4): Navigation integrity at risk, request hold
- Multiple IMU axes showing simultaneous drift: Potential systemic timing failure, immediate hold
- IMU sync loss during COUNTDOWN or LAUNCH phase: Automatic hold per range safety requirements
- Star tracker also degraded (Channel 6): Triple navigation failure, mandatory hold

## Safety Implications

IMU synchronization is classified as a **Category 1 safety-critical function** for the NOVA-7 mission. The range safety system (Channel 20) depends on accurate navigation data to maintain tracking. If the IMU cannot provide synchronized data, and GPS is also degraded, the vehicle's position uncertainty grows rapidly, potentially exceeding the range safety corridor limits.

**Mandatory hold conditions**:
- IMU drift > 15ms AND GPS unavailable: Navigation cannot maintain required accuracy
- IMU drift on 2+ axes simultaneously: Potential common-cause failure
- Any IMU anomaly during T-10:00 to T+120:00: During this critical phase, the IMU is the primary navigation sensor

## Historical Precedents

### NOVA-4 IMU Timing Glitch at T-5:00
NOVA-4 experienced a 12ms IMU sync loss at T-5:00 caused by a power bus transient during fuel system pressurization. The transient induced a spike in the IMU power supply that reset the timing counter. Resolution: IMU was resynchronized to GPS PPS, navigation filter was reinitialized, and countdown resumed after a 6-minute hold. Post-mission action: additional power filtering was added to the IMU power rail.

### NOVA-6 GPS/IMU Dual Failure
As documented in the GPS Multipath knowledge base entry, NOVA-6 experienced simultaneous GPS and IMU failures due to a ground power bus transient. This event drove the requirement for independent power supplies and the triple-redundant timing architecture.

## Related Channels
- Channel 4: GPS Multipath Interference (primary timing source)
- Channel 6: Star Tracker Alignment Fault (navigation cross-check)
- Channel 14: Ground Power Bus Fault (power supply dependency)
- Channel 18: Calibration Epoch Mismatch (timing reference dependency)
- Channel 19: FTS Check Failure (safety system impact)
- Channel 20: Range Safety Tracking Loss (navigation accuracy dependency)
