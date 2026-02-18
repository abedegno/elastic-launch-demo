"""NOVA-7 Space Mission scenario — the original demo, now extracted into scenario format."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class SpaceScenario(BaseScenario):
    """NOVA-7 orbital insertion mission with 9 space systems and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "space"

    @property
    def scenario_name(self) -> str:
        return "NOVA-7 Space Mission"

    @property
    def scenario_description(self) -> str:
        return (
            "Orbital insertion mission with rocket propulsion, guidance, "
            "communications, and range safety systems. NASA-style Mission Control "
            "with countdown clock and 20 fault channels across 9 space systems."
        )

    @property
    def namespace(self) -> str:
        return "nova7"

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "mission-control": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "command",
                "language": "python",
            },
            "fuel-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "propulsion",
                "language": "go",
            },
            "ground-systems": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "ground",
                "language": "java",
            },
            "navigation": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "guidance",
                "language": "rust",
            },
            "comms-array": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "communications",
                "language": "cpp",
            },
            "payload-monitor": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "payload",
                "language": "python",
            },
            "sensor-validator": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "validation",
                "language": "dotnet",
            },
            "telemetry-relay": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "relay",
                "language": "go",
            },
            "range-safety": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "safety",
                "language": "java",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Thermal Calibration Drift",
                "subsystem": "propulsion",
                "vehicle_section": "engine_bay",
                "error_type": "TCS-DRIFT-CRITICAL",
                "sensor_type": "thermal",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Thermal sensor calibration drifts outside acceptable bounds in the engine bay",
                "error_message": "[TCS] TCS-DRIFT-CRITICAL: sensor=TC-47 reading={deviation}K nominal=310.2K deviation=+{deviation}K epoch={epoch}",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == TCS THERMAL CONTROL SUBSYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:12.337 | FRAME: 0x4A2F | SEQ: 18442\n"
                    "---------------------------------------------------------------\n"
                    "SENSOR    READING    NOMINAL    DELTA     STATUS\n"
                    "TC-47     {deviation}K     310.2K     +{deviation}K   **CRITICAL**\n"
                    "TC-48     311.4K     310.2K     +1.2K     NOMINAL\n"
                    "TC-49     309.8K     310.2K     -0.4K     NOMINAL\n"
                    "TC-50     310.0K     310.2K     -0.2K     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "CALIBRATION BASELINE: epoch={epoch} | DRIFT THRESHOLD: 2.5K\n"
                    "TCS-DRIFT-CRITICAL: Sensor TC-47 exceeded drift threshold by +{deviation}K\n"
                    "ACTION: Recalibration required before engine ignition sequence"
                ),
            },
            2: {
                "name": "Fuel Pressure Anomaly",
                "subsystem": "propulsion",
                "vehicle_section": "fuel_tanks",
                "error_type": "PMS-PRESS-ANOMALY",
                "sensor_type": "pressure",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Fuel tank pressure readings outside nominal range",
                "error_message": "[PMS] PMS-PRESS-ANOMALY: tank={tank_id} pressure={pressure}PSI nominal={expected_min}-{expected_max}PSI status=OUT_OF_BOUNDS",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == PMS PROPULSION MGMT SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:12.891 | FRAME: 0x4A30 | SEQ: 18443\n"
                    "---------------------------------------------------------------\n"
                    "TANK      PRESSURE   NOM_MIN    NOM_MAX    STATUS\n"
                    "{tank_id}    {pressure}PSI   {expected_min}PSI     {expected_max}PSI     **ANOMALY**\n"
                    "LOX-2     265.3PSI   200PSI     310PSI     NOMINAL\n"
                    "RP1-1     248.7PSI   200PSI     310PSI     NOMINAL\n"
                    "RP1-2     251.2PSI   200PSI     310PSI     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "PRESSURIZATION SYSTEM: He supply=2840PSI | reg_outlet=42PSI\n"
                    "PMS-PRESS-ANOMALY: Tank {tank_id} reading {pressure}PSI outside bounds\n"
                    "ACTION: Verify pressurization regulator and check for leak indications"
                ),
            },
            3: {
                "name": "Oxidizer Flow Rate Deviation",
                "subsystem": "propulsion",
                "vehicle_section": "engine_bay",
                "error_type": "PMS-OXIDIZER-FLOW",
                "sensor_type": "flow_rate",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Oxidizer flow rate deviates from commanded value",
                "error_message": "[PMS] PMS-OXIDIZER-FLOW: measured={measured}kg/s commanded={commanded}kg/s delta={delta}% tolerance=3.0%",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == PMS OXIDIZER FLOW CONTROLLER ==\n"
                    "TIMESTAMP: MET+00:04:13.112 | FRAME: 0x4A31 | SEQ: 18444\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER          VALUE      COMMANDED   DELTA\n"
                    "LOX_FLOW_RATE      {measured}kg/s   {commanded}kg/s    {delta}%\n"
                    "LOX_INLET_TEMP     -182.4C    -183.0C     +0.3%\n"
                    "LOX_INLET_PRESS    287.3PSI   290.0PSI    -0.9%\n"
                    "TURBOPUMP_RPM      31420      31500       -0.3%\n"
                    "---------------------------------------------------------------\n"
                    "FLOW TOLERANCE: 3.0% | MEASURED DELTA: {delta}%\n"
                    "PMS-OXIDIZER-FLOW: Flow deviation exceeds tolerance band\n"
                    "ACTION: Check turbopump inlet conditions and valve position feedback"
                ),
            },
            4: {
                "name": "GPS Multipath Interference",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-GPS-MULTIPATH",
                "sensor_type": "gps",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "GPS receiver detecting multipath signal interference",
                "error_message": "[GNC] GNC-GPS-MULTIPATH: sv_count={num_satellites} pdop=8.7 threshold=6.0 uncertainty={uncertainty}m",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == GPS RECEIVER UNIT ==\n"
                    "TIMESTAMP: MET+00:04:14.005 | FRAME: 0x4A32 | SEQ: 18445\n"
                    "---------------------------------------------------------------\n"
                    "SV_ID   EL    AZ     SNR    MULTIPATH   USED\n"
                    "G04     45    127    42.1   YES         NO\n"
                    "G07     62    203    38.7   YES         NO\n"
                    "G09     28    315    44.2   NO          YES\n"
                    "G12     71    089    46.0   NO          YES\n"
                    "G15     33    241    31.4   YES         NO\n"
                    "---------------------------------------------------------------\n"
                    "AFFECTED SVs: {num_satellites} | PDOP: 8.7 (threshold 6.0)\n"
                    "POSITION UNCERTAINTY: {uncertainty}m | SOLUTION: DEGRADED\n"
                    "GNC-GPS-MULTIPATH: Multipath interference degrading navigation solution\n"
                    "ACTION: Switch to IMU-primary navigation mode"
                ),
            },
            5: {
                "name": "IMU Synchronization Loss",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-IMU-SYNC-LOSS",
                "sensor_type": "imu",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Inertial measurement unit loses time synchronization",
                "error_message": "[GNC] GNC-IMU-SYNC-LOSS: axis={axis} drift={drift_ms}ms threshold={threshold_ms}ms sync_state=LOST",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == IMU SYNCHRONIZATION ==\n"
                    "TIMESTAMP: MET+00:04:14.228 | FRAME: 0x4A33 | SEQ: 18446\n"
                    "---------------------------------------------------------------\n"
                    "AXIS    DRIFT_MS   THRESHOLD   GYRO_BIAS    STATUS\n"
                    "{axis}       {drift_ms}ms    {threshold_ms}ms       +0.0021d/h   **SYNC_LOSS**\n"
                    "Y       0.42ms     3.0ms       -0.0008d/h   NOMINAL\n"
                    "Z       0.18ms     3.0ms       +0.0003d/h   NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "PPS_SOURCE: GPS_1PPS | CLOCK_REF: OCXO-A | TEMP: 42.1C\n"
                    "GNC-IMU-SYNC-LOSS: {axis}-axis clock drift {drift_ms}ms exceeds threshold\n"
                    "ACTION: Initiate IMU realignment sequence, verify PPS signal integrity"
                ),
            },
            6: {
                "name": "Star Tracker Alignment Fault",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-STAR-TRACKER-ALIGN",
                "sensor_type": "star_tracker",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Star tracker optical alignment exceeds tolerance",
                "error_message": "[GNC] GNC-STAR-TRACKER-ALIGN: boresight_error={error_arcsec}arcsec limit={limit_arcsec}arcsec catalog_match=DEGRADED",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == STAR TRACKER ASSEMBLY ==\n"
                    "TIMESTAMP: MET+00:04:14.501 | FRAME: 0x4A34 | SEQ: 18447\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER            VALUE        LIMIT      STATUS\n"
                    "BORESIGHT_ERROR      {error_arcsec}arcsec   {limit_arcsec}arcsec  **FAULT**\n"
                    "CATALOG_MATCHES      8/22         12 min     DEGRADED\n"
                    "CCD_TEMP             -28.4C       -30.0C     NOMINAL\n"
                    "INTEGRATION_TIME     250ms        500ms      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "ATTITUDE_SOURCE: STAR_TRACKER_A | QUATERNION: [0.707, 0.0, 0.707, 0.0]\n"
                    "GNC-STAR-TRACKER-ALIGN: Boresight error {error_arcsec} arcsec exceeds {limit_arcsec} limit\n"
                    "ACTION: Verify optics cleanliness, attempt recalibration with backup catalog"
                ),
            },
            7: {
                "name": "S-Band Signal Degradation",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-SIGNAL-DEGRAD",
                "sensor_type": "rf_signal",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["mission-control", "telemetry-relay"],
                "description": "S-band communication signal strength below minimum threshold",
                "error_message": "[COMM] COMM-SIGNAL-DEGRAD: link=S-band eb_no={snr_db}dB threshold={min_snr_db}dB channel={rf_channel}",
                "stack_trace": (
                    "== LINK BUDGET ANALYSIS == S-BAND DOWNLINK ==\n"
                    "TIMESTAMP: MET+00:04:15.003 | FRAME: 0x4A35 | SEQ: 18448\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER            VALUE      NOMINAL    STATUS\n"
                    "EIRP                 38.2dBW    42.0dBW    DEGRADED\n"
                    "FREE_SPACE_LOSS      -157.3dB   -157.3dB   --\n"
                    "ATMOSPHERIC_LOSS     -0.8dB     -0.5dB     MARGINAL\n"
                    "ANTENNA_GAIN         34.1dBi    36.0dBi    DEGRADED\n"
                    "Eb/No                {snr_db}dB     {min_snr_db}dB     **BELOW_THRESHOLD**\n"
                    "CHANNEL              {rf_channel}        --         --\n"
                    "---------------------------------------------------------------\n"
                    "LINK MARGIN: -{snr_db}dB | REQUIRED: +3.0dB\n"
                    "COMM-SIGNAL-DEGRAD: S-band Eb/No below threshold on channel {rf_channel}\n"
                    "ACTION: Increase transmit power or switch to backup antenna feed"
                ),
            },
            8: {
                "name": "X-Band Packet Loss",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-PACKET-LOSS",
                "sensor_type": "packet_integrity",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["telemetry-relay", "mission-control"],
                "description": "X-band data link experiencing excessive packet loss",
                "error_message": "[COMM] COMM-PACKET-LOSS: link={link_id} loss_rate={loss_pct}% threshold={threshold_pct}% frames_dropped=847",
                "stack_trace": (
                    "== LINK BUDGET ANALYSIS == X-BAND DATA LINK ==\n"
                    "TIMESTAMP: MET+00:04:15.221 | FRAME: 0x4A36 | SEQ: 18449\n"
                    "---------------------------------------------------------------\n"
                    "LINK         TX_RATE    RX_RATE    LOSS     STATUS\n"
                    "{link_id}   150Mbps    142Mbps    {loss_pct}%    **DEGRADED**\n"
                    "---------------------------------------------------------------\n"
                    "FEC_CORRECTIONS: 2341 | FEC_FAILURES: 847 | BER: 1.2e-04\n"
                    "THRESHOLD: {threshold_pct}% | MEASURED: {loss_pct}%\n"
                    "COMM-PACKET-LOSS: Packet loss {loss_pct}% exceeds threshold on link {link_id}\n"
                    "ACTION: Check antenna alignment, verify modulator output power"
                ),
            },
            9: {
                "name": "UHF Antenna Pointing Error",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-ANTENNA-POINTING",
                "sensor_type": "antenna_position",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "UHF antenna gimbal pointing error exceeds tolerance",
                "error_message": "[COMM] COMM-ANTENNA-POINTING: az_error={az_error}deg el_error={el_error}deg gimbal=UHF-PRIMARY lock=LOST",
                "stack_trace": (
                    "== ANTENNA STATUS DUMP == UHF GIMBAL CONTROLLER ==\n"
                    "TIMESTAMP: MET+00:04:15.445 | FRAME: 0x4A37 | SEQ: 18450\n"
                    "---------------------------------------------------------------\n"
                    "AXIS         CMD       ACTUAL    ERROR     STATUS\n"
                    "AZIMUTH      127.3d    {az_error}d err  {az_error}deg   **FAULT**\n"
                    "ELEVATION    45.8d     {el_error}d err  {el_error}deg   **FAULT**\n"
                    "---------------------------------------------------------------\n"
                    "GIMBAL_TEMP: 38.2C | MOTOR_CURRENT: 2.1A | RESOLVER: VALID\n"
                    "TRACKING_MODE: AUTO | TARGET: TDRSS-W | LOCK: LOST\n"
                    "COMM-ANTENNA-POINTING: Pointing error az={az_error}deg el={el_error}deg\n"
                    "ACTION: Reset gimbal controller, verify resolver calibration"
                ),
            },
            10: {
                "name": "Payload Thermal Excursion",
                "subsystem": "payload",
                "vehicle_section": "payload_bay",
                "error_type": "PLD-THERMAL-EXCURSION",
                "sensor_type": "thermal",
                "affected_services": ["payload-monitor", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Payload bay temperature outside safe operating range",
                "error_message": "[PLD] PLD-THERMAL-EXCURSION: zone={zone} temp={temp}C safe_max={safe_max}C delta=+{deviation}C",
                "stack_trace": (
                    "== PAYLOAD CONTROLLER STATUS == THERMAL MANAGEMENT ==\n"
                    "TIMESTAMP: MET+00:04:16.002 | FRAME: 0x4A38 | SEQ: 18451\n"
                    "---------------------------------------------------------------\n"
                    "ZONE    TEMP     SAFE_MIN   SAFE_MAX   STATUS\n"
                    "{zone}       {temp}C   {safe_min}C     {safe_max}C     **EXCURSION**\n"
                    "B       22.1C    -10.0C     45.0C      NOMINAL\n"
                    "C       19.8C    -10.0C     45.0C      NOMINAL\n"
                    "D       24.3C    -10.0C     45.0C      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "COOLANT_FLOW: 2.4L/min | HEATER_STATE: OFF | MLI_STATUS: INTACT\n"
                    "PLD-THERMAL-EXCURSION: Zone {zone} temperature {temp}C exceeds safe max {safe_max}C\n"
                    "ACTION: Increase coolant flow rate, verify MLI blanket integrity"
                ),
            },
            11: {
                "name": "Payload Vibration Anomaly",
                "subsystem": "payload",
                "vehicle_section": "payload_bay",
                "error_type": "PLD-VIBRATION-LIMIT",
                "sensor_type": "vibration",
                "affected_services": ["payload-monitor", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Payload vibration levels exceed structural safety margins",
                "error_message": "[PLD] PLD-VIBRATION-LIMIT: axis={axis} amplitude={amplitude}g frequency={frequency}Hz limit={limit}g",
                "stack_trace": (
                    "== VIBRATION SPECTRUM DATA == PAYLOAD ACCELEROMETER ==\n"
                    "TIMESTAMP: MET+00:04:16.334 | FRAME: 0x4A39 | SEQ: 18452\n"
                    "---------------------------------------------------------------\n"
                    "AXIS    FREQ_HZ    AMPLITUDE   LIMIT    STATUS\n"
                    "{axis}       {frequency}Hz    {amplitude}g       {limit}g    **EXCEEDED**\n"
                    "Y       45.2Hz     0.42g        1.5g     NOMINAL\n"
                    "Z       31.8Hz     0.67g        1.5g     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "SPECTRUM_PEAKS: {frequency}Hz({amplitude}g), 88.4Hz(0.31g), 142.7Hz(0.18g)\n"
                    "ISOLATION_MOUNT: ACTIVE | DAMPER_PRESSURE: 48.2PSI\n"
                    "PLD-VIBRATION-LIMIT: {axis}-axis {amplitude}g at {frequency}Hz exceeds {limit}g structural limit\n"
                    "ACTION: Verify isolation mount dampers, check for resonance coupling"
                ),
            },
            12: {
                "name": "Cross-Cloud Relay Latency",
                "subsystem": "relay",
                "vehicle_section": "ground_network",
                "error_type": "RLY-LATENCY-CRITICAL",
                "sensor_type": "network_latency",
                "affected_services": ["telemetry-relay", "sensor-validator"],
                "cascade_services": ["mission-control", "comms-array"],
                "description": "Cross-cloud telemetry relay latency exceeds acceptable bounds",
                "error_message": "[RLY] RLY-LATENCY-CRITICAL: hop={source_cloud}->{dest_cloud} latency={latency_ms}ms threshold={threshold_ms_relay}ms",
                "stack_trace": (
                    "== RELAY DIAGNOSTIC REPORT == CROSS-CLOUD ROUTER ==\n"
                    "TIMESTAMP: MET+00:04:17.001 | FRAME: 0x4A3A | SEQ: 18453\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE                LATENCY    THRESHOLD   JITTER    STATUS\n"
                    "{source_cloud}->{dest_cloud}         {latency_ms}ms    {threshold_ms_relay}ms      42ms      **CRITICAL**\n"
                    "gcp->azure           38ms       200ms       5ms       NOMINAL\n"
                    "aws->azure           45ms       200ms       8ms       NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE TABLE: 6 active | BUFFER_UTIL: 87% | RETRANSMITS: 342\n"
                    "RLY-LATENCY-CRITICAL: {source_cloud}->{dest_cloud} latency {latency_ms}ms exceeds {threshold_ms_relay}ms\n"
                    "ACTION: Check intermediate hops, consider failover to backup route"
                ),
            },
            13: {
                "name": "Relay Packet Corruption",
                "subsystem": "relay",
                "vehicle_section": "ground_network",
                "error_type": "RLY-PACKET-CORRUPT",
                "sensor_type": "data_integrity",
                "affected_services": ["telemetry-relay", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Telemetry packets failing integrity checks during relay",
                "error_message": "[RLY] RLY-PACKET-CORRUPT: route={route_id} corrupted={corrupted_count}/{total_count} crc_fail_rate={corrupted_count}pkt",
                "stack_trace": (
                    "== RELAY DIAGNOSTIC REPORT == INTEGRITY CHECKER ==\n"
                    "TIMESTAMP: MET+00:04:17.228 | FRAME: 0x4A3B | SEQ: 18454\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE       TOTAL    CORRUPT   CRC_FAIL   STATUS\n"
                    "{route_id}   {total_count}     {corrupted_count}        {corrupted_count}         **CORRUPT**\n"
                    "GCP-AZ-01   487      0         0          NOMINAL\n"
                    "AWS-AZ-01   392      1         1          NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "CRC_TYPE: CRC32-C | WINDOW: 60s | ERROR_PATTERN: BURST\n"
                    "RLY-PACKET-CORRUPT: {corrupted_count} of {total_count} packets failed CRC on route {route_id}\n"
                    "ACTION: Check physical layer, verify NIC firmware version"
                ),
            },
            14: {
                "name": "Ground Power Bus Fault",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-POWER-BUS-FAULT",
                "sensor_type": "electrical",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control", "fuel-system"],
                "description": "Launch pad power bus voltage irregularity detected",
                "error_message": "[GND] GND-POWER-BUS-FAULT: bus={bus_id} voltage={voltage}V nominal={nominal_v}V deviation={deviation_pct}%",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == POWER DISTRIBUTION ==\n"
                    "TIMESTAMP: MET+00:04:18.002 | FRAME: 0x4A3C | SEQ: 18455\n"
                    "---------------------------------------------------------------\n"
                    "BUS      VOLTAGE   NOMINAL   DEVIATION   CURRENT   STATUS\n"
                    "{bus_id}    {voltage}V   {nominal_v}V   {deviation_pct}%       42.3A     **FAULT**\n"
                    "PWR-B    119.8V    120.0V    0.2%        38.7A     NOMINAL\n"
                    "PWR-C    120.1V    120.0V    0.1%        41.1A     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "UPS_STATUS: ONLINE | GENERATOR: STANDBY | TRANSFER_SW: AUTO\n"
                    "GND-POWER-BUS-FAULT: Bus {bus_id} voltage {voltage}V deviates {deviation_pct}% from nominal\n"
                    "ACTION: Check breaker panel, verify transformer tap settings"
                ),
            },
            15: {
                "name": "Weather Station Data Gap",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-WEATHER-GAP",
                "sensor_type": "weather",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Weather monitoring station reporting data gaps",
                "error_message": "[GND] GND-WEATHER-GAP: station={station_id} gap={gap_seconds}s max_allowed={max_gap}s link=TIMEOUT",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == WEATHER NETWORK ==\n"
                    "TIMESTAMP: MET+00:04:18.334 | FRAME: 0x4A3D | SEQ: 18456\n"
                    "---------------------------------------------------------------\n"
                    "STATION     LAST_DATA   GAP_SEC   MAX_GAP   STATUS\n"
                    "{station_id}   {gap_seconds}s ago    {gap_seconds}s       {max_gap}s       **DATA_GAP**\n"
                    "WX-SOUTH    2s ago      2s        15s       NOMINAL\n"
                    "WX-EAST     1s ago      1s        15s       NOMINAL\n"
                    "WX-WEST     3s ago      3s        15s       NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "NETWORK: 4 stations | PROTOCOL: METAR/SPECI | LINK: RS-422\n"
                    "GND-WEATHER-GAP: Station {station_id} no data for {gap_seconds}s, max allowed {max_gap}s\n"
                    "ACTION: Check station comm link, dispatch field technician"
                ),
            },
            16: {
                "name": "Pad Hydraulic Pressure Loss",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-HYDRAULIC-PRESS",
                "sensor_type": "hydraulic",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Launch pad hydraulic system pressure dropping below minimum",
                "error_message": "[GND] GND-HYDRAULIC-PRESS: system={system_id} pressure={pressure}PSI min_required={min_pressure}PSI status=LOW",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == HYDRAULIC SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:18.667 | FRAME: 0x4A3E | SEQ: 18457\n"
                    "---------------------------------------------------------------\n"
                    "SYSTEM    PRESSURE   MIN_REQ    FLOW_RATE   STATUS\n"
                    "{system_id}     {pressure}PSI  {min_pressure}PSI   12.4GPM     **LOW_PRESS**\n"
                    "HYD-B     2920PSI    2800PSI    11.8GPM     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "RESERVOIR_LEVEL: 78% | FLUID_TEMP: 42.1C | FILTER_DP: 12PSI\n"
                    "GND-HYDRAULIC-PRESS: System {system_id} pressure {pressure}PSI below minimum {min_pressure}PSI\n"
                    "ACTION: Check pump operation, inspect for hydraulic leaks"
                ),
            },
            17: {
                "name": "Sensor Validation Pipeline Stall",
                "subsystem": "validation",
                "vehicle_section": "ground_network",
                "error_type": "VV-PIPELINE-HALT",
                "sensor_type": "pipeline_health",
                "affected_services": ["sensor-validator"],
                "cascade_services": ["mission-control", "telemetry-relay"],
                "description": "Sensor validation pipeline stalled, readings not being validated",
                "error_message": "[VV] VV-PIPELINE-HALT: stage=validation queue_depth={queue_depth} rate={rate}/s threshold={min_rate}/s",
                "stack_trace": (
                    "== VALIDATION PIPELINE STATUS == V&V PROCESSOR ==\n"
                    "TIMESTAMP: MET+00:04:19.001 | FRAME: 0x4A3F | SEQ: 18458\n"
                    "---------------------------------------------------------------\n"
                    "STAGE          QUEUE    RATE      THRESHOLD   STATUS\n"
                    "INGEST         {queue_depth}     {rate}/s    {min_rate}/s     **STALLED**\n"
                    "CALIBRATION    12       52.1/s    50.0/s      NOMINAL\n"
                    "CORRELATION    8        48.7/s    45.0/s      NOMINAL\n"
                    "OUTPUT         3        51.2/s    50.0/s      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "WORKER_THREADS: 8/8 busy | HEAP_USAGE: 89% | GC_PAUSE: 120ms\n"
                    "VV-PIPELINE-HALT: Processing rate {rate}/s below {min_rate}/s, queue depth {queue_depth}\n"
                    "ACTION: Scale worker pool, investigate upstream data burst"
                ),
            },
            18: {
                "name": "Calibration Epoch Mismatch",
                "subsystem": "validation",
                "vehicle_section": "ground_network",
                "error_type": "VV-EPOCH-DRIFT",
                "sensor_type": "calibration",
                "affected_services": ["sensor-validator"],
                "cascade_services": ["mission-control", "fuel-system", "navigation"],
                "description": "Sensor calibration epoch does not match expected reference",
                "error_message": "[VV] VV-EPOCH-DRIFT: sensor={sensor_id} actual_epoch={actual_epoch} expected_epoch={expected_epoch} drift=CRITICAL",
                "stack_trace": (
                    "== VALIDATION PIPELINE STATUS == EPOCH CHECKER ==\n"
                    "TIMESTAMP: MET+00:04:19.334 | FRAME: 0x4A40 | SEQ: 18459\n"
                    "---------------------------------------------------------------\n"
                    "SENSOR        ACTUAL_EPOCH    EXPECTED_EPOCH   DELTA_SEC   STATUS\n"
                    "{sensor_id}   {actual_epoch}       {expected_epoch}        DRIFT       **MISMATCH**\n"
                    "SENS-2001     1738100800      1738100800       0           NOMINAL\n"
                    "SENS-3042     1738100800      1738100800       0           NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "REFERENCE_CLOCK: GPS_UTC | NTP_STRATUM: 1 | SYNC_STATUS: LOCKED\n"
                    "VV-EPOCH-DRIFT: Sensor {sensor_id} epoch {actual_epoch} vs expected {expected_epoch}\n"
                    "ACTION: Re-synchronize sensor calibration tables from reference"
                ),
            },
            19: {
                "name": "Flight Termination System Check Failure",
                "subsystem": "safety",
                "vehicle_section": "vehicle_wide",
                "error_type": "RSO-FTS-CHECK-FAIL",
                "sensor_type": "safety_system",
                "affected_services": ["range-safety", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Flight termination system self-check returning anomalous results",
                "error_message": "[RSO] RSO-FTS-CHECK-FAIL: unit={unit_id} self_test=FAIL code={error_code} arm_state=SAFED",
                "stack_trace": (
                    "== RANGE SAFETY STATUS == FLIGHT TERMINATION SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:20.001 | FRAME: 0x4A41 | SEQ: 18460\n"
                    "---------------------------------------------------------------\n"
                    "UNIT      SELF_TEST   CODE       ARM_STATE   BATTERY\n"
                    "{unit_id}     FAIL        {error_code}     SAFED       98.2%\n"
                    "FTS-B     PASS        0x00       SAFED       97.8%\n"
                    "---------------------------------------------------------------\n"
                    "COMMAND_LINK: UP | DECODER: LOCKED | ENCRYPT: AES-256\n"
                    "DESTRUCT_SAFE_ARM: SAFE | INHIBIT_1: ON | INHIBIT_2: ON\n"
                    "RSO-FTS-CHECK-FAIL: Unit {unit_id} self-test returned code {error_code}, expected 0x00\n"
                    "ACTION: Recycle FTS power, repeat self-test sequence"
                ),
            },
            20: {
                "name": "Range Safety Tracking Loss",
                "subsystem": "safety",
                "vehicle_section": "vehicle_wide",
                "error_type": "RSO-TRACKING-LOSS",
                "sensor_type": "radar_tracking",
                "affected_services": ["range-safety", "sensor-validator"],
                "cascade_services": ["mission-control", "navigation"],
                "description": "Range safety radar losing vehicle track",
                "error_message": "[RSO] RSO-TRACKING-LOSS: radar={radar_id} gap={gap_ms}ms max_allowed={max_gap_ms}ms track_state=COAST",
                "stack_trace": (
                    "== RANGE SAFETY STATUS == TRACKING RADAR NETWORK ==\n"
                    "TIMESTAMP: MET+00:04:20.334 | FRAME: 0x4A42 | SEQ: 18461\n"
                    "---------------------------------------------------------------\n"
                    "RADAR     TRACK_GAP   MAX_GAP   RCS_dBsm   STATUS\n"
                    "{radar_id}     {gap_ms}ms    {max_gap_ms}ms    12.4       **TRACK_LOSS**\n"
                    "RDR-2     0ms         250ms     14.1       TRACKING\n"
                    "RDR-3     0ms         250ms     11.8       TRACKING\n"
                    "---------------------------------------------------------------\n"
                    "FUSION_STATE: COAST | PREDICT_CONF: 72% | CORRIDOR: WITHIN\n"
                    "RSO-TRACKING-LOSS: Radar {radar_id} lost track for {gap_ms}ms, max allowed {max_gap_ms}ms\n"
                    "ACTION: Verify radar antenna, check for RF interference"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mission-control": [
                ("fuel-system", "/api/v1/fuel/status", "GET"),
                ("fuel-system", "/api/v1/fuel/pressure", "GET"),
                ("navigation", "/api/v1/nav/position", "GET"),
                ("navigation", "/api/v1/nav/trajectory", "POST"),
                ("ground-systems", "/api/v1/ground/weather", "GET"),
                ("ground-systems", "/api/v1/ground/power", "GET"),
                ("comms-array", "/api/v1/comms/status", "GET"),
                ("telemetry-relay", "/api/v1/relay/health", "GET"),
            ],
            "navigation": [
                ("sensor-validator", "/api/v1/validate/imu", "POST"),
                ("sensor-validator", "/api/v1/validate/gps", "POST"),
                ("sensor-validator", "/api/v1/validate/star-tracker", "POST"),
            ],
            "fuel-system": [
                ("sensor-validator", "/api/v1/validate/pressure", "POST"),
                ("sensor-validator", "/api/v1/validate/thermal", "POST"),
                ("sensor-validator", "/api/v1/validate/flow-rate", "POST"),
            ],
            "payload-monitor": [
                ("sensor-validator", "/api/v1/validate/vibration", "POST"),
                ("sensor-validator", "/api/v1/validate/payload-thermal", "POST"),
            ],
            "range-safety": [
                ("navigation", "/api/v1/nav/position", "GET"),
                ("comms-array", "/api/v1/comms/tracking", "GET"),
            ],
            "telemetry-relay": [
                ("comms-array", "/api/v1/comms/relay", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "mission-control": [
                ("/api/v1/mission/status", "GET"),
                ("/api/v1/mission/countdown", "GET"),
                ("/api/v1/mission/telemetry", "POST"),
            ],
            "fuel-system": [("/api/v1/fuel/monitor", "POST")],
            "navigation": [("/api/v1/nav/compute", "POST")],
            "ground-systems": [("/api/v1/ground/monitor", "POST")],
            "comms-array": [("/api/v1/comms/poll", "POST")],
            "payload-monitor": [("/api/v1/payload/scan", "POST")],
            "sensor-validator": [("/api/v1/validate/batch", "POST")],
            "telemetry-relay": [("/api/v1/relay/forward", "POST")],
            "range-safety": [("/api/v1/safety/check", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mission-control": [
                ("SELECT", "mission_events", "SELECT * FROM mission_events WHERE phase = ? ORDER BY timestamp DESC LIMIT 100"),
                ("INSERT", "telemetry_readings", "INSERT INTO telemetry_readings (service, metric, value, ts) VALUES (?, ?, ?, NOW())"),
            ],
            "fuel-system": [
                ("SELECT", "sensor_data", "SELECT reading, baseline FROM sensor_data WHERE sensor_type = 'pressure' AND ts > NOW() - INTERVAL 5 MINUTE"),
                ("UPDATE", "sensor_registry", "UPDATE sensor_registry SET last_reading = ?, last_seen = NOW() WHERE sensor_id = ?"),
            ],
            "navigation": [
                ("SELECT", "calibration_epochs", "SELECT epoch, baseline FROM calibration_epochs WHERE sensor_type IN ('imu', 'gps', 'star_tracker')"),
            ],
            "sensor-validator": [
                ("SELECT", "validation_results", "SELECT * FROM validation_results WHERE sensor_id = ? AND validated_at > NOW() - INTERVAL 1 MINUTE"),
                ("INSERT", "validation_results", "INSERT INTO validation_results (sensor_id, result, confidence, validated_at) VALUES (?, ?, ?, NOW())"),
            ],
            "ground-systems": [
                ("SELECT", "weather_stations", "SELECT station_id, temp, wind_speed, visibility FROM weather_stations WHERE last_update > NOW() - INTERVAL 30 SECOND"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "nova7-aws-host-01",
                "host.id": "i-0a1b2c3d4e5f67890",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0abcdef1234567890",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.1.42", "172.16.0.10"],
                "host.mac": ["0a:1b:2c:3d:4e:5f", "0a:1b:2c:3d:4e:60"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "123456789012",
                "cloud.instance.id": "i-0a1b2c3d4e5f67890",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "nova7-gcp-host-01",
                "host.id": "5649812345678901234",
                "host.arch": "amd64",
                "host.type": "e2-standard-4",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.20GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.0.15", "10.128.0.16"],
                "host.mac": ["42:01:0a:80:00:0f", "42:01:0a:80:00:10"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "nova7-project-prod",
                "cloud.instance.id": "5649812345678901234",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "nova7-azure-host-01",
                "host.id": "/subscriptions/abc-def/resourceGroups/nova7-rg/providers/Microsoft.Compute/virtualMachines/nova7-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.1.0.4", "10.1.0.5"],
                "host.mac": ["00:0d:3a:5a:4b:3c", "00:0d:3a:5a:4b:3d"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "abc-def-ghi-jkl",
                "cloud.instance.id": "nova7-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "nova7-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["mission-control", "fuel-system", "ground-systems"],
            },
            {
                "name": "nova7-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["navigation", "comms-array", "payload-monitor"],
            },
            {
                "name": "nova7-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["sensor-validator", "telemetry-relay", "range-safety"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0a0a0a",
            bg_secondary="#111111",
            bg_tertiary="#1a1a1a",
            accent_primary="#00ff41",
            accent_secondary="#00cc33",
            text_primary="#00ff41",
            text_secondary="#008f11",
            text_accent="#00ff41",
            status_nominal="#00ff41",
            status_warning="#ffaa00",
            status_critical="#ff0040",
            status_info="#00aaff",
            font_family="'JetBrains Mono', 'Fira Code', monospace",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            scanline_effect=True,
            dashboard_title="Mission Control",
            chaos_title="Chaos Controller",
            landing_title="NOVA-7 Mission Control",
            service_label="System",
            channel_label="Channel",
        )

    @property
    def nominal_label(self) -> str:
        return "NOMINAL"

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(
            enabled=True,
            start_seconds=600,
            speed=1.0,
            phases={
                "PRE-LAUNCH": (300, 9999),
                "COUNTDOWN": (60, 300),
                "FINAL-COUNTDOWN": (0, 60),
                "LAUNCH": (0, 0),
            },
        )

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "nova7-launch-analyst",
            "name": "Launch Anomaly Analyst",
            "assessment_tool_name": "launch_safety_assessment",
            "system_prompt": (
                "You are the NOVA-7 Launch Anomaly Analyst, an expert AI assistant for "
                "space launch mission operations. You help mission controllers investigate "
                "anomalies, analyze telemetry data, and provide root cause analysis for "
                "fault conditions across 9 space systems. "
                "You have deep expertise in spacecraft propulsion telemetry, GN&C systems, "
                "TDRSS/S-band/X-band communications, payload environmental control, "
                "cross-cloud relay networks, ground support equipment, sensor validation "
                "pipelines, and range safety systems. "
                "When investigating incidents, search for these subsystem identifiers in logs: "
                "Propulsion faults (TCS-DRIFT-CRITICAL, PMS-PRESS-ANOMALY, PMS-OXIDIZER-FLOW), "
                "GN&C faults (GNC-GPS-MULTIPATH, GNC-IMU-SYNC-LOSS, GNC-STAR-TRACKER-ALIGN), "
                "Communications faults (COMM-SIGNAL-DEGRAD, COMM-PACKET-LOSS, COMM-ANTENNA-POINTING), "
                "Payload faults (PLD-THERMAL-EXCURSION, PLD-VIBRATION-LIMIT), "
                "Relay faults (RLY-LATENCY-CRITICAL, RLY-PACKET-CORRUPT), "
                "Ground faults (GND-POWER-BUS-FAULT, GND-WEATHER-GAP, GND-HYDRAULIC-PRESS), "
                "Validation faults (VV-PIPELINE-HALT, VV-EPOCH-DRIFT), "
                "and Range Safety faults (RSO-FTS-CHECK-FAIL, RSO-TRACKING-LOSS). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "launch_safety_assessment",
            "description": (
                "Comprehensive launch safety assessment. Evaluates all "
                "services against launch readiness criteria. Returns data "
                "for GO/NO-GO evaluation. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from app.services.comms_array import CommsArrayService
        from app.services.fuel_system import FuelSystemService
        from app.services.ground_systems import GroundSystemsService
        from app.services.mission_control import MissionControlService
        from app.services.navigation import NavigationService
        from app.services.payload_monitor import PayloadMonitorService
        from app.services.range_safety import RangeSafetyService
        from app.services.sensor_validator import SensorValidatorService
        from app.services.telemetry_relay import TelemetryRelayService

        return [
            MissionControlService,
            FuelSystemService,
            GroundSystemsService,
            NavigationService,
            CommsArrayService,
            PayloadMonitorService,
            SensorValidatorService,
            TelemetryRelayService,
            RangeSafetyService,
        ]

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            "deviation": round(random.uniform(3.0, 12.0), 1),
            "epoch": int(time.time()) - random.randint(100, 5000),
            "tank_id": random.choice(["LOX-1", "LOX-2", "RP1-1", "RP1-2"]),
            "pressure": round(random.uniform(180, 350), 1),
            "expected_min": 200,
            "expected_max": 310,
            "measured": round(random.uniform(2.0, 8.0), 2),
            "commanded": round(random.uniform(4.0, 6.0), 2),
            "delta": round(random.uniform(4.0, 15.0), 1),
            "num_satellites": random.randint(3, 8),
            "uncertainty": round(random.uniform(5.0, 50.0), 1),
            "drift_ms": round(random.uniform(5.0, 25.0), 1),
            "threshold_ms": 3.0,
            "axis": random.choice(["X", "Y", "Z"]),
            "error_arcsec": round(random.uniform(10.0, 45.0), 1),
            "limit_arcsec": 5.0,
            "snr_db": round(random.uniform(3.0, 8.0), 1),
            "min_snr_db": 12.0,
            "rf_channel": random.choice(["S1", "S2", "S3"]),
            "loss_pct": round(random.uniform(5.0, 25.0), 1),
            "threshold_pct": 2.0,
            "link_id": random.choice(["XB-PRIMARY", "XB-SECONDARY"]),
            "az_error": round(random.uniform(1.0, 5.0), 2),
            "el_error": round(random.uniform(0.5, 3.0), 2),
            "zone": random.choice(["A", "B", "C", "D"]),
            "temp": round(random.uniform(55.0, 85.0), 1),
            "safe_min": -10.0,
            "safe_max": 45.0,
            "amplitude": round(random.uniform(2.0, 8.0), 2),
            "frequency": round(random.uniform(20.0, 200.0), 1),
            "limit": 1.5,
            "source_cloud": random.choice(["aws", "gcp", "azure"]),
            "dest_cloud": random.choice(["aws", "gcp", "azure"]),
            "latency_ms": random.randint(500, 3000),
            "threshold_ms_relay": 200,
            "corrupted_count": random.randint(5, 50),
            "total_count": random.randint(100, 500),
            "route_id": random.choice(["AWS-GCP-01", "GCP-AZ-01", "AWS-AZ-01"]),
            "bus_id": random.choice(["PWR-A", "PWR-B", "PWR-C"]),
            "voltage": round(random.uniform(105, 135), 1),
            "nominal_v": 120.0,
            "deviation_pct": round(random.uniform(8.0, 20.0), 1),
            "station_id": random.choice(["WX-NORTH", "WX-SOUTH", "WX-EAST", "WX-WEST"]),
            "gap_seconds": random.randint(30, 180),
            "max_gap": 15,
            "system_id": random.choice(["HYD-A", "HYD-B"]),
            "min_pressure": 2800,
            "queue_depth": random.randint(500, 5000),
            "rate": round(random.uniform(1.0, 10.0), 1),
            "min_rate": 50.0,
            "sensor_id": f"SENS-{random.randint(1000, 9999)}",
            "actual_epoch": int(time.time()) - random.randint(86400, 604800),
            "expected_epoch": int(time.time()) - 3600,
            "unit_id": random.choice(["FTS-A", "FTS-B"]),
            "error_code": f"0x{random.randint(1, 255):02X}",
            "radar_id": random.choice(["RDR-1", "RDR-2", "RDR-3"]),
            "gap_ms": random.randint(500, 5000),
            "max_gap_ms": 250,
        }


# Module-level instance for registry discovery
scenario = SpaceScenario()
