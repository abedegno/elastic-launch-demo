# Channel Reference

Complete reference for the fault channel system. Each scenario defines 20 independent fault channels. This document details the channels for the default **space** (NOVA-7) scenario. Other scenarios follow the same structure with industry-specific channel names, subsystems, and error types.

> **Note:** Channels are defined per-scenario in each scenario's `scenario.py` file. The channel numbers (1-20), structure (affected services, cascade services, subsystem, error type), and API endpoints are consistent across all scenarios — only the names and domain-specific details differ.

---

## Channel Overview

| Ch | Name | Subsystem | Section | Error Type |
|----|------|-----------|---------|------------|
| 1 | Thermal Calibration Drift | propulsion | engine_bay | ThermalCalibrationException |
| 2 | Fuel Pressure Anomaly | propulsion | fuel_tanks | FuelPressureException |
| 3 | Oxidizer Flow Rate Deviation | propulsion | engine_bay | OxidizerFlowException |
| 4 | GPS Multipath Interference | guidance | avionics | GPSMultipathException |
| 5 | IMU Synchronization Loss | guidance | avionics | IMUSyncException |
| 6 | Star Tracker Alignment Fault | guidance | avionics | StarTrackerAlignmentException |
| 7 | S-Band Signal Degradation | communications | antenna_array | SignalDegradationException |
| 8 | X-Band Packet Loss | communications | antenna_array | PacketLossException |
| 9 | UHF Antenna Pointing Error | communications | antenna_array | AntennaPointingException |
| 10 | Payload Thermal Excursion | payload | payload_bay | PayloadThermalException |
| 11 | Payload Vibration Anomaly | payload | payload_bay | PayloadVibrationException |
| 12 | Cross-Cloud Relay Latency | relay | ground_network | RelayLatencyException |
| 13 | Relay Packet Corruption | relay | ground_network | PacketCorruptionException |
| 14 | Ground Power Bus Fault | ground | launch_pad | PowerBusFaultException |
| 15 | Weather Station Data Gap | ground | launch_pad | WeatherDataGapException |
| 16 | Pad Hydraulic Pressure Loss | ground | launch_pad | HydraulicPressureException |
| 17 | Sensor Validation Pipeline Stall | validation | ground_network | ValidationPipelineException |
| 18 | Calibration Epoch Mismatch | validation | ground_network | CalibrationEpochException |
| 19 | Flight Termination System Check Failure | safety | vehicle_wide | FTSCheckException |
| 20 | Range Safety Tracking Loss | safety | vehicle_wide | TrackingLossException |

---

## Detailed Channel Descriptions

### Channel 1 — Thermal Calibration Drift

- **Subsystem:** propulsion
- **Vehicle Section:** engine_bay
- **Error Type:** `ThermalCalibrationException`
- **Sensor Type:** thermal
- **Affected Services:** fuel-system, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** Thermal sensor calibration drifts outside acceptable bounds in the engine bay. The calibration baseline stored in the propulsion calibration store no longer matches the observed sensor readings, producing deviations that exceed the 2.5K threshold.
- **Cloud Context:** fuel-system on AWS us-east-1b, sensor-validator on Azure eastus-1

### Channel 2 — Fuel Pressure Anomaly

- **Subsystem:** propulsion
- **Vehicle Section:** fuel_tanks
- **Error Type:** `FuelPressureException`
- **Sensor Type:** pressure
- **Affected Services:** fuel-system, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** Fuel tank pressure readings fall outside the nominal range of 200-310 PSI. The fuel controller detects out-of-bounds pressure on one or more LOX or RP-1 tanks.
- **Cloud Context:** fuel-system on AWS us-east-1b, sensor-validator on Azure eastus-1

### Channel 3 — Oxidizer Flow Rate Deviation

- **Subsystem:** propulsion
- **Vehicle Section:** engine_bay
- **Error Type:** `OxidizerFlowException`
- **Sensor Type:** flow_rate
- **Affected Services:** fuel-system, sensor-validator
- **Cascade Services:** mission-control
- **Description:** The measured oxidizer flow rate deviates from the commanded value by more than the 3% tolerance. This indicates a potential valve or injector issue in the engine bay.
- **Cloud Context:** fuel-system on AWS us-east-1b, sensor-validator on Azure eastus-1

### Channel 4 — GPS Multipath Interference

- **Subsystem:** guidance
- **Vehicle Section:** avionics
- **Error Type:** `GPSMultipathException`
- **Sensor Type:** gps
- **Affected Services:** navigation, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** The GPS receiver detects multipath signal interference affecting multiple satellites. Position uncertainty increases significantly, degrading the navigation solution.
- **Cloud Context:** navigation on GCP us-central1-a, sensor-validator on Azure eastus-1

### Channel 5 — IMU Synchronization Loss

- **Subsystem:** guidance
- **Vehicle Section:** avionics
- **Error Type:** `IMUSyncException`
- **Sensor Type:** imu
- **Affected Services:** navigation, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** The inertial measurement unit loses time synchronization. Clock drift on one or more axes exceeds the 3.0ms threshold, producing unreliable inertial readings.
- **Cloud Context:** navigation on GCP us-central1-a, sensor-validator on Azure eastus-1

### Channel 6 — Star Tracker Alignment Fault

- **Subsystem:** guidance
- **Vehicle Section:** avionics
- **Error Type:** `StarTrackerAlignmentException`
- **Sensor Type:** star_tracker
- **Affected Services:** navigation, sensor-validator
- **Cascade Services:** mission-control
- **Description:** The star tracker optical alignment exceeds the 5.0 arcsecond tolerance. Boresight error between the catalog star positions and observed positions indicates a mechanical or thermal misalignment.
- **Cloud Context:** navigation on GCP us-central1-a, sensor-validator on Azure eastus-1

### Channel 7 — S-Band Signal Degradation

- **Subsystem:** communications
- **Vehicle Section:** antenna_array
- **Error Type:** `SignalDegradationException`
- **Sensor Type:** rf_signal
- **Affected Services:** comms-array, sensor-validator
- **Cascade Services:** mission-control, telemetry-relay
- **Description:** S-band communication signal-to-noise ratio falls below the 12.0dB minimum threshold on one or more RF channels. This degrades the primary command and telemetry link.
- **Cloud Context:** comms-array on GCP us-central1-b, sensor-validator on Azure eastus-1

### Channel 8 — X-Band Packet Loss

- **Subsystem:** communications
- **Vehicle Section:** antenna_array
- **Error Type:** `PacketLossException`
- **Sensor Type:** packet_integrity
- **Affected Services:** comms-array, sensor-validator
- **Cascade Services:** telemetry-relay, mission-control
- **Description:** The X-band high-rate data link experiences packet loss exceeding the 2% threshold. This affects high-bandwidth telemetry and payload data downlink.
- **Cloud Context:** comms-array on GCP us-central1-b, sensor-validator on Azure eastus-1

### Channel 9 — UHF Antenna Pointing Error

- **Subsystem:** communications
- **Vehicle Section:** antenna_array
- **Error Type:** `AntennaPointingException`
- **Sensor Type:** antenna_position
- **Affected Services:** comms-array, sensor-validator
- **Cascade Services:** mission-control
- **Description:** The UHF antenna gimbal has a pointing error exceeding tolerance in azimuth and/or elevation. The antenna cannot accurately track the ground station.
- **Cloud Context:** comms-array on GCP us-central1-b, sensor-validator on Azure eastus-1

### Channel 10 — Payload Thermal Excursion

- **Subsystem:** payload
- **Vehicle Section:** payload_bay
- **Error Type:** `PayloadThermalException`
- **Sensor Type:** thermal
- **Affected Services:** payload-monitor, sensor-validator
- **Cascade Services:** mission-control
- **Description:** Payload bay temperature in one or more thermal zones exceeds the safe operating range of -10C to +45C. This threatens payload integrity and mission success.
- **Cloud Context:** payload-monitor on GCP us-central1-a, sensor-validator on Azure eastus-1

### Channel 11 — Payload Vibration Anomaly

- **Subsystem:** payload
- **Vehicle Section:** payload_bay
- **Error Type:** `PayloadVibrationException`
- **Sensor Type:** vibration
- **Affected Services:** payload-monitor, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** Vibration levels on one or more axes exceed the 1.5g structural safety limit. High-frequency vibration at specific resonant frequencies could damage the payload.
- **Cloud Context:** payload-monitor on GCP us-central1-a, sensor-validator on Azure eastus-1

### Channel 12 — Cross-Cloud Relay Latency

- **Subsystem:** relay
- **Vehicle Section:** ground_network
- **Error Type:** `RelayLatencyException`
- **Sensor Type:** network_latency
- **Affected Services:** telemetry-relay, sensor-validator
- **Cascade Services:** mission-control, comms-array
- **Description:** Cross-cloud telemetry relay latency between cloud providers exceeds the 200ms threshold. This indicates network congestion or routing issues between AWS, GCP, and Azure regions.
- **Cloud Context:** telemetry-relay on Azure eastus-2, sensor-validator on Azure eastus-1

### Channel 13 — Relay Packet Corruption

- **Subsystem:** relay
- **Vehicle Section:** ground_network
- **Error Type:** `PacketCorruptionException`
- **Sensor Type:** data_integrity
- **Affected Services:** telemetry-relay, sensor-validator
- **Cascade Services:** mission-control
- **Description:** Telemetry packets are failing CRC integrity checks during cross-cloud relay. A significant fraction of packets on one or more routes have corrupted data.
- **Cloud Context:** telemetry-relay on Azure eastus-2, sensor-validator on Azure eastus-1

### Channel 14 — Ground Power Bus Fault

- **Subsystem:** ground
- **Vehicle Section:** launch_pad
- **Error Type:** `PowerBusFaultException`
- **Sensor Type:** electrical
- **Affected Services:** ground-systems, sensor-validator
- **Cascade Services:** mission-control, fuel-system
- **Description:** Launch pad power bus voltage deviates significantly from the 120V nominal. This can affect ground support equipment, fueling systems, and pad safety systems.
- **Cloud Context:** ground-systems on AWS us-east-1c, sensor-validator on Azure eastus-1

### Channel 15 — Weather Station Data Gap

- **Subsystem:** ground
- **Vehicle Section:** launch_pad
- **Error Type:** `WeatherDataGapException`
- **Sensor Type:** weather
- **Affected Services:** ground-systems, sensor-validator
- **Cascade Services:** mission-control, range-safety
- **Description:** One or more weather monitoring stations stop reporting data. Gaps exceeding 15 seconds violate launch commit criteria for weather monitoring coverage.
- **Cloud Context:** ground-systems on AWS us-east-1c, sensor-validator on Azure eastus-1

### Channel 16 — Pad Hydraulic Pressure Loss

- **Subsystem:** ground
- **Vehicle Section:** launch_pad
- **Error Type:** `HydraulicPressureException`
- **Sensor Type:** hydraulic
- **Affected Services:** ground-systems, sensor-validator
- **Cascade Services:** mission-control
- **Description:** Launch pad hydraulic system pressure drops below the 2800 PSI minimum required for pad operations including launch clamp release and service arm retraction.
- **Cloud Context:** ground-systems on AWS us-east-1c, sensor-validator on Azure eastus-1

### Channel 17 — Sensor Validation Pipeline Stall

- **Subsystem:** validation
- **Vehicle Section:** ground_network
- **Error Type:** `ValidationPipelineException`
- **Sensor Type:** pipeline_health
- **Affected Services:** sensor-validator
- **Cascade Services:** mission-control, telemetry-relay
- **Description:** The sensor validation pipeline processing rate drops below 50 readings/second while the queue depth grows. Sensor readings are not being validated, meaning fault detection is impaired.
- **Cloud Context:** sensor-validator on Azure eastus-1

### Channel 18 — Calibration Epoch Mismatch

- **Subsystem:** validation
- **Vehicle Section:** ground_network
- **Error Type:** `CalibrationEpochException`
- **Sensor Type:** calibration
- **Affected Services:** sensor-validator
- **Cascade Services:** mission-control, fuel-system, navigation
- **Description:** A sensor's calibration epoch does not match the expected reference epoch. This means the sensor is using stale or incorrect calibration data, potentially producing inaccurate readings across multiple subsystems.
- **Cloud Context:** sensor-validator on Azure eastus-1

### Channel 19 — Flight Termination System Check Failure

- **Subsystem:** safety
- **Vehicle Section:** vehicle_wide
- **Error Type:** `FTSCheckException`
- **Sensor Type:** safety_system
- **Affected Services:** range-safety, sensor-validator
- **Cascade Services:** mission-control
- **Description:** The flight termination system self-test returns an anomalous error code instead of the expected 0x00 success code. This is a safety-critical system — any anomaly requires immediate investigation.
- **Cloud Context:** range-safety on Azure eastus-1, sensor-validator on Azure eastus-1

### Channel 20 — Range Safety Tracking Loss

- **Subsystem:** safety
- **Vehicle Section:** vehicle_wide
- **Error Type:** `TrackingLossException`
- **Sensor Type:** radar_tracking
- **Affected Services:** range-safety, sensor-validator
- **Cascade Services:** mission-control, navigation
- **Description:** Range safety radar loses vehicle track for longer than the 250ms maximum allowed gap. Continuous tracking is required for flight safety — loss of track may require activation of the flight termination system.
- **Cloud Context:** range-safety on Azure eastus-1, sensor-validator on Azure eastus-1

---

## Service-to-Channel Mapping

### Which channels affect each service?

| Service | Primary Channels | Cascade Channels |
|---------|-----------------|------------------|
| fuel-system | 1, 2, 3 | 14 |
| navigation | 4, 5, 6 | 18, 20 |
| comms-array | 7, 8, 9 | 12 |
| payload-monitor | 10, 11 | — |
| telemetry-relay | 12, 13 | 7, 8, 17 |
| ground-systems | 14, 15, 16 | — |
| sensor-validator | 1-20 (all) | — |
| range-safety | 19, 20 | 1, 2, 4, 5, 11, 15 |
| mission-control | — | 1-20 (all) |

### Subsystem Grouping

| Subsystem | Channels | Cloud Provider |
|-----------|----------|----------------|
| propulsion | 1, 2, 3 | AWS |
| guidance | 4, 5, 6 | GCP |
| communications | 7, 8, 9 | GCP |
| payload | 10, 11 | GCP |
| relay | 12, 13 | Azure |
| ground | 14, 15, 16 | AWS |
| validation | 17, 18 | Azure |
| safety | 19, 20 | Azure |

---

## Triggering Channels via API

### Trigger a single channel

```bash
curl -X POST http://<host>/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 7}'
```

### Resolve a channel

```bash
curl -X POST http://<host>/api/remediate/7
```

### Check channel status

```bash
curl -s http://<host>/api/chaos/status/7 | python3 -m json.tool
```

### Check all channels

```bash
curl -s http://<host>/api/chaos/status | python3 -m json.tool
```
