"""Healthcare Clinical Systems scenario — hospital operations with EHR, patient monitoring, and clinical workflows."""

from __future__ import annotations

import random
import secrets
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class HealthcareScenario(BaseScenario):
    """Hospital clinical systems with 9 healthcare services and 20 fault channels."""

    # -- Identity ---------------------------------------------------------------

    @property
    def scenario_id(self) -> str:
        return "healthcare"

    @property
    def scenario_name(self) -> str:
        return "Healthcare Systems"

    @property
    def scenario_description(self) -> str:
        return (
            "Hospital clinical systems including EHR, patient monitoring, lab "
            "integration, pharmacy, imaging, scheduling, billing, and clinical "
            "alerting. Clean, calm clinical interface."
        )

    @property
    def namespace(self) -> str:
        return "healthcare"

    # -- Services ---------------------------------------------------------------

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "ehr-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "clinical_records",
                "language": "java",
            },
            "patient-monitor": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "vital_signs",
                "language": "python",
            },
            "lab-integration": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "laboratory",
                "language": "go",
            },
            "pharmacy-system": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "medication",
                "language": "java",
            },
            "imaging-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "radiology",
                "language": "python",
            },
            "scheduling-api": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "scheduling",
                "language": "go",
            },
            "billing-processor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "billing",
                "language": "dotnet",
            },
            "clinical-alerts": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "alerting",
                "language": "python",
            },
            "data-warehouse": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "analytics",
                "language": "java",
            },
        }

    # -- Channel Registry -------------------------------------------------------

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "HL7 Message Parsing Failure",
                "subsystem": "clinical_records",
                "vehicle_section": "adt_interface",
                "error_type": "HL7ParseException",
                "sensor_type": "hl7_parser",
                "affected_services": ["ehr-system", "lab-integration"],
                "cascade_services": ["patient-monitor", "clinical-alerts"],
                "description": "HL7 v2.x message parsing fails due to malformed segments or unsupported message types in the ADT interface",
                "error_message": "HL7 parse failure: message type {msg_type} segment {hl7_segment} at position {position} for patient MRN {mrn}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "clinical/hl7_parser.py", line 342, in parse_message\n'
                    "    segment = self._decode_segment(raw_segment, encoding)\n"
                    '  File "clinical/hl7_parser.py", line 298, in _decode_segment\n'
                    "    return self.segment_registry.parse(segment_id, fields)\n"
                    '  File "clinical/segment_registry.py", line 156, in parse\n'
                    '    raise HL7ParseException(f"Failed to parse {segment_id} segment at position {position}")\n'
                    "HL7ParseException: Failed to parse {hl7_segment} segment at position {position} in {msg_type} message"
                ),
            },
            2: {
                "name": "Vital Signs Alert Storm",
                "subsystem": "vital_signs",
                "vehicle_section": "vitals_engine",
                "error_type": "VitalAlertStormException",
                "sensor_type": "vital_signs_monitor",
                "affected_services": ["patient-monitor", "clinical-alerts"],
                "cascade_services": ["ehr-system"],
                "description": "Excessive simultaneous vital sign alerts overwhelming the alerting pipeline from bedside monitors",
                "error_message": "Vital alert storm: {alert_count} alerts in {window_seconds}s from unit {nursing_unit}, patient {patient_id} HR {heart_rate} SpO2 {spo2}%",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "vitals/alert_engine.py", line 218, in process_vitals\n'
                    "    self._evaluate_thresholds(patient_id, readings)\n"
                    '  File "vitals/alert_engine.py", line 195, in _evaluate_thresholds\n'
                    "    self._check_storm_condition(unit, active_alerts)\n"
                    '  File "vitals/alert_engine.py", line 172, in _check_storm_condition\n'
                    '    raise VitalAlertStormException(f"Alert storm: {count} alerts in {window}s on {unit}")\n'
                    "VitalAlertStormException: {alert_count} alerts in {window_seconds}s on unit {nursing_unit}"
                ),
            },
            3: {
                "name": "Lab Result Delivery Delay",
                "subsystem": "laboratory",
                "vehicle_section": "lab_interface",
                "error_type": "LabResultDelayException",
                "sensor_type": "lab_result_queue",
                "affected_services": ["lab-integration", "ehr-system"],
                "cascade_services": ["pharmacy-system", "clinical-alerts"],
                "description": "Laboratory result delivery exceeds critical TAT threshold, delaying clinical decisions",
                "error_message": "Lab result delay: order {lab_order_id} test {test_code} TAT {tat_minutes}min exceeds {max_tat}min threshold for patient {patient_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "laboratory/result_router.py", line 167, in deliver_result\n'
                    "    tat = self._compute_turnaround(order_id, completed_at)\n"
                    '  File "laboratory/result_router.py", line 145, in _compute_turnaround\n'
                    "    self._check_tat_threshold(test_code, tat)\n"
                    '  File "laboratory/result_router.py", line 128, in _check_tat_threshold\n'
                    '    raise LabResultDelayException(f"TAT {tat}min exceeds {threshold}min for {test_code}")\n'
                    "LabResultDelayException: Order {lab_order_id} TAT {tat_minutes}min exceeds {max_tat}min threshold"
                ),
            },
            4: {
                "name": "DICOM Transfer Failure",
                "subsystem": "radiology",
                "vehicle_section": "pacs_gateway",
                "error_type": "DICOMTransferException",
                "sensor_type": "dicom_transfer",
                "affected_services": ["imaging-service", "ehr-system"],
                "cascade_services": ["clinical-alerts", "data-warehouse"],
                "description": "DICOM C-STORE or C-MOVE operation fails during image transfer between modality and PACS",
                "error_message": "DICOM transfer failure: study {dicom_study_uid} modality {modality} operation {dicom_operation} error code {dicom_error_code}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "radiology/dicom_handler.py", line 445, in transfer_study\n'
                    "    association = self._establish_association(ae_title, scp_host)\n"
                    '  File "radiology/dicom_handler.py", line 412, in _establish_association\n'
                    "    result = self._send_c_store(dataset, association)\n"
                    '  File "radiology/dicom_handler.py", line 389, in _send_c_store\n'
                    '    raise DICOMTransferException(f"C-STORE failed for study {study_uid}: {error_code}")\n'
                    "DICOMTransferException: {dicom_operation} failed for study {dicom_study_uid}: error {dicom_error_code}"
                ),
            },
            5: {
                "name": "Medication Interaction Alert Overflow",
                "subsystem": "medication",
                "vehicle_section": "cpoe_engine",
                "error_type": "MedInteractionException",
                "sensor_type": "drug_interaction_checker",
                "affected_services": ["pharmacy-system", "ehr-system"],
                "cascade_services": ["clinical-alerts"],
                "description": "Drug interaction checking engine overwhelmed by excessive concurrent medication orders",
                "error_message": "Medication interaction overflow: {interaction_count} interactions queued, patient {patient_id} medication {medication_id} severity {severity_level}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "pharmacy/interaction_engine.py", line 267, in check_interactions\n'
                    "    results = self._screen_drug_pairs(medication_list, patient_allergies)\n"
                    '  File "pharmacy/interaction_engine.py", line 245, in _screen_drug_pairs\n'
                    "    self._check_queue_capacity(pending_count)\n"
                    '  File "pharmacy/interaction_engine.py", line 218, in _check_queue_capacity\n'
                    '    raise MedInteractionException(f"Interaction queue overflow: {pending_count} pending checks")\n'
                    "MedInteractionException: Interaction queue overflow: {interaction_count} pending for medication {medication_id}"
                ),
            },
            6: {
                "name": "E-Prescribe Transmission Error",
                "subsystem": "medication",
                "vehicle_section": "eprescribe_gateway",
                "error_type": "EPrescribeException",
                "sensor_type": "ncpdp_transmitter",
                "affected_services": ["pharmacy-system", "ehr-system"],
                "cascade_services": ["clinical-alerts", "billing-processor"],
                "description": "Electronic prescription transmission to external pharmacy via NCPDP SCRIPT fails",
                "error_message": "E-Prescribe transmission error: Rx {prescription_id} for patient {patient_id} pharmacy NPI {pharmacy_npi} NCPDP status {ncpdp_status}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "pharmacy/eprescribe_sender.py", line 312, in transmit_prescription\n'
                    "    response = self._send_ncpdp_script(rx_message, pharmacy_endpoint)\n"
                    '  File "pharmacy/eprescribe_sender.py", line 289, in _send_ncpdp_script\n'
                    "    self._validate_response(response)\n"
                    '  File "pharmacy/eprescribe_sender.py", line 267, in _validate_response\n'
                    '    raise EPrescribeException(f"NCPDP transmission failed: status {status}")\n'
                    "EPrescribeException: Transmission failed for Rx {prescription_id}: NCPDP status {ncpdp_status}"
                ),
            },
            7: {
                "name": "Patient Identity Match Failure",
                "subsystem": "clinical_records",
                "vehicle_section": "mpi_engine",
                "error_type": "PatientMatchException",
                "sensor_type": "mpi_matcher",
                "affected_services": ["ehr-system", "patient-monitor"],
                "cascade_services": ["lab-integration", "pharmacy-system"],
                "description": "Master Patient Index fails to resolve patient identity, risking duplicate records",
                "error_message": "Patient match failure: MRN {mrn} encounter {encounter_id} match score {match_score}% below threshold {match_threshold}% — potential duplicate",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "clinical/mpi_resolver.py", line 178, in resolve_patient\n'
                    "    candidates = self._search_demographics(demographics)\n"
                    '  File "clinical/mpi_resolver.py", line 156, in _search_demographics\n'
                    "    best_match = self._score_candidates(candidates)\n"
                    '  File "clinical/mpi_resolver.py", line 134, in _score_candidates\n'
                    '    raise PatientMatchException(f"Match score {score}% below threshold for MRN {mrn}")\n'
                    "PatientMatchException: MRN {mrn} match score {match_score}% below {match_threshold}% threshold"
                ),
            },
            8: {
                "name": "Bed Management Sync Error",
                "subsystem": "scheduling",
                "vehicle_section": "bed_board",
                "error_type": "BedManagementException",
                "sensor_type": "bed_tracker",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["clinical-alerts"],
                "description": "Bed management system loses synchronization with ADT events, showing stale census data",
                "error_message": "Bed sync error: unit {nursing_unit} bed {bed_id} shows {bed_status} but ADT event {adt_event} contradicts — last sync {sync_lag_seconds}s ago",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "scheduling/bed_manager.py", line 234, in sync_bed_state\n'
                    "    adt_state = self._fetch_adt_census(unit)\n"
                    '  File "scheduling/bed_manager.py", line 212, in _fetch_adt_census\n'
                    "    self._reconcile_state(local_state, adt_state)\n"
                    '  File "scheduling/bed_manager.py", line 189, in _reconcile_state\n'
                    '    raise BedManagementException(f"Bed {bed_id} state conflict: {local} vs ADT {adt}")\n'
                    "BedManagementException: Bed {bed_id} in unit {nursing_unit} state conflict, sync lag {sync_lag_seconds}s"
                ),
            },
            9: {
                "name": "Appointment Scheduling Conflict",
                "subsystem": "scheduling",
                "vehicle_section": "scheduler_core",
                "error_type": "ScheduleConflictException",
                "sensor_type": "appointment_scheduler",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["billing-processor"],
                "description": "Double-booking or resource conflict detected in appointment scheduling engine",
                "error_message": "Schedule conflict: provider {provider_id} slot {time_slot} already booked, patient {patient_id} encounter {encounter_id} resource {resource_type}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "scheduling/appointment_engine.py", line 189, in book_appointment\n'
                    "    self._check_availability(provider_id, slot, resource)\n"
                    '  File "scheduling/appointment_engine.py", line 167, in _check_availability\n'
                    "    conflicts = self._find_conflicts(provider_id, slot)\n"
                    '  File "scheduling/appointment_engine.py", line 145, in _find_conflicts\n'
                    '    raise ScheduleConflictException(f"Slot {slot} already booked for provider {provider_id}")\n'
                    "ScheduleConflictException: Provider {provider_id} slot {time_slot} conflict for patient {patient_id}"
                ),
            },
            10: {
                "name": "Insurance Eligibility Check Timeout",
                "subsystem": "billing",
                "vehicle_section": "eligibility_gateway",
                "error_type": "EligibilityTimeoutException",
                "sensor_type": "x12_270_271",
                "affected_services": ["billing-processor", "scheduling-api"],
                "cascade_services": ["ehr-system"],
                "description": "Real-time insurance eligibility verification via X12 270/271 transaction times out",
                "error_message": "Eligibility timeout: payer {payer_id} insurance {insurance_id} patient {patient_id} elapsed {elapsed_ms}ms exceeds {timeout_ms}ms",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "billing/eligibility_checker.py", line 278, in verify_eligibility\n'
                    "    response = self._send_x12_270(payer_endpoint, request)\n"
                    '  File "billing/eligibility_checker.py", line 256, in _send_x12_270\n'
                    "    self._check_response_timeout(elapsed, timeout)\n"
                    '  File "billing/eligibility_checker.py", line 234, in _check_response_timeout\n'
                    '    raise EligibilityTimeoutException(f"Payer {payer_id} timeout after {elapsed}ms")\n'
                    "EligibilityTimeoutException: Payer {payer_id} eligibility check timeout after {elapsed_ms}ms"
                ),
            },
            11: {
                "name": "Claims Processing Batch Failure",
                "subsystem": "billing",
                "vehicle_section": "claims_engine",
                "error_type": "ClaimsProcessException",
                "sensor_type": "x12_837",
                "affected_services": ["billing-processor", "data-warehouse"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Batch claims processing pipeline fails during X12 837 generation or submission",
                "error_message": "Claims batch failure: batch {batch_id} claim {claim_id} patient {patient_id} payer {payer_id} rejected at stage {claim_stage}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "billing/claims_processor.py", line 312, in process_batch\n'
                    "    x12_output = self._generate_837(claims_batch)\n"
                    '  File "billing/claims_processor.py", line 289, in _generate_837\n'
                    "    self._validate_claim(claim)\n"
                    '  File "billing/claims_processor.py", line 267, in _validate_claim\n'
                    '    raise ClaimsProcessException(f"Claim {claim_id} rejected at {stage}")\n'
                    "ClaimsProcessException: Batch {batch_id} claim {claim_id} rejected at stage {claim_stage}"
                ),
            },
            12: {
                "name": "PACS Storage Capacity Warning",
                "subsystem": "radiology",
                "vehicle_section": "pacs_storage",
                "error_type": "PACSCapacityException",
                "sensor_type": "storage_monitor",
                "affected_services": ["imaging-service", "data-warehouse"],
                "cascade_services": ["clinical-alerts", "ehr-system"],
                "description": "PACS archive storage capacity approaching critical threshold, risking image loss",
                "error_message": "PACS capacity warning: volume {volume_id} usage {usage_pct}% exceeds {threshold_pct}% threshold, {remaining_gb}GB remaining",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "radiology/pacs_monitor.py", line 198, in check_storage\n'
                    "    usage = self._compute_volume_usage(volume_id)\n"
                    '  File "radiology/pacs_monitor.py", line 176, in _compute_volume_usage\n'
                    "    self._check_capacity_threshold(volume_id, usage)\n"
                    '  File "radiology/pacs_monitor.py", line 154, in _check_capacity_threshold\n'
                    '    raise PACSCapacityException(f"Volume {volume_id} at {usage}% capacity")\n'
                    "PACSCapacityException: Volume {volume_id} at {usage_pct}%, {remaining_gb}GB remaining"
                ),
            },
            13: {
                "name": "Clinical Decision Support Overload",
                "subsystem": "alerting",
                "vehicle_section": "cds_engine",
                "error_type": "CDSOverloadException",
                "sensor_type": "cds_rule_engine",
                "affected_services": ["clinical-alerts", "ehr-system"],
                "cascade_services": ["pharmacy-system", "patient-monitor"],
                "description": "Clinical decision support rule engine overloaded, unable to evaluate rules within SLA",
                "error_message": "CDS overload: {pending_rules} rules pending, evaluation time {eval_ms}ms exceeds {max_eval_ms}ms SLA for patient {patient_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "alerting/cds_engine.py", line 267, in evaluate_rules\n'
                    "    results = self._run_rule_set(patient_context, rules)\n"
                    '  File "alerting/cds_engine.py", line 245, in _run_rule_set\n'
                    "    self._check_sla(elapsed, max_eval)\n"
                    '  File "alerting/cds_engine.py", line 223, in _check_sla\n'
                    '    raise CDSOverloadException(f"Rule evaluation {elapsed}ms exceeds {max_eval}ms SLA")\n'
                    "CDSOverloadException: {pending_rules} rules pending, evaluation {eval_ms}ms exceeds {max_eval_ms}ms SLA"
                ),
            },
            14: {
                "name": "Nurse Call System Integration Failure",
                "subsystem": "alerting",
                "vehicle_section": "nurse_call_bridge",
                "error_type": "NurseCallException",
                "sensor_type": "nurse_call_interface",
                "affected_services": ["clinical-alerts", "patient-monitor"],
                "cascade_services": ["ehr-system"],
                "description": "Integration bridge between nurse call system and EHR loses connectivity",
                "error_message": "Nurse call integration failure: station {station_id} unit {nursing_unit} bed {bed_id} call type {call_type} undelivered for {undelivered_seconds}s",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "alerting/nurse_call_bridge.py", line 189, in relay_call\n'
                    "    self._send_to_ehr(call_event, ehr_endpoint)\n"
                    '  File "alerting/nurse_call_bridge.py", line 167, in _send_to_ehr\n'
                    "    self._check_delivery_timeout(call_id, elapsed)\n"
                    '  File "alerting/nurse_call_bridge.py", line 145, in _check_delivery_timeout\n'
                    '    raise NurseCallException(f"Call {call_id} undelivered for {elapsed}s")\n'
                    "NurseCallException: Station {station_id} call undelivered for {undelivered_seconds}s on unit {nursing_unit}"
                ),
            },
            15: {
                "name": "Blood Bank Inventory Sync Error",
                "subsystem": "laboratory",
                "vehicle_section": "blood_bank_interface",
                "error_type": "BloodBankSyncException",
                "sensor_type": "blood_bank_inventory",
                "affected_services": ["lab-integration", "clinical-alerts"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Blood bank inventory management system loses sync with transfusion service records",
                "error_message": "Blood bank sync error: product {blood_product} type {blood_type} units on-hand {units_on_hand} vs system count {system_count} — discrepancy {discrepancy}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "laboratory/blood_bank_sync.py", line 223, in reconcile_inventory\n'
                    "    physical = self._count_physical_units(product_type)\n"
                    '  File "laboratory/blood_bank_sync.py", line 201, in _count_physical_units\n'
                    "    self._check_discrepancy(physical, system_count)\n"
                    '  File "laboratory/blood_bank_sync.py", line 178, in _check_discrepancy\n'
                    '    raise BloodBankSyncException(f"Inventory discrepancy: {physical} vs {system}")\n'
                    "BloodBankSyncException: {blood_product} {blood_type} discrepancy: {units_on_hand} physical vs {system_count} system"
                ),
            },
            16: {
                "name": "Surgical Schedule Conflict",
                "subsystem": "scheduling",
                "vehicle_section": "or_scheduler",
                "error_type": "SurgicalConflictException",
                "sensor_type": "surgical_scheduler",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["billing-processor", "clinical-alerts"],
                "description": "Operating room scheduling conflict detected between overlapping surgical cases",
                "error_message": "Surgical conflict: OR {or_number} case {case_id} surgeon {surgeon_id} overlaps with existing case at {conflict_time} — patient {patient_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "scheduling/surgical_scheduler.py", line 312, in book_case\n'
                    "    self._check_or_availability(or_number, start_time, duration)\n"
                    '  File "scheduling/surgical_scheduler.py", line 289, in _check_or_availability\n'
                    "    conflicts = self._find_overlaps(or_number, time_window)\n"
                    '  File "scheduling/surgical_scheduler.py", line 267, in _find_overlaps\n'
                    '    raise SurgicalConflictException(f"OR {or_number} conflict at {conflict_time}")\n'
                    "SurgicalConflictException: OR {or_number} case {case_id} conflicts at {conflict_time}"
                ),
            },
            17: {
                "name": "ADT Feed Synchronization Gap",
                "subsystem": "clinical_records",
                "vehicle_section": "adt_interface",
                "error_type": "ADTSyncException",
                "sensor_type": "adt_feed",
                "affected_services": ["ehr-system", "scheduling-api"],
                "cascade_services": ["patient-monitor", "billing-processor", "lab-integration"],
                "description": "ADT (Admit-Discharge-Transfer) event feed falls behind, causing stale patient location data",
                "error_message": "ADT sync gap: feed {feed_id} last event {gap_seconds}s ago, queue depth {queue_depth}, patient {patient_id} event {adt_event_type} pending",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "clinical/adt_processor.py", line 334, in process_feed\n'
                    "    lag = self._measure_feed_lag(feed_id)\n"
                    '  File "clinical/adt_processor.py", line 312, in _measure_feed_lag\n'
                    "    self._check_sync_threshold(feed_id, lag)\n"
                    '  File "clinical/adt_processor.py", line 289, in _check_sync_threshold\n'
                    '    raise ADTSyncException(f"Feed {feed_id} lag {lag}s exceeds threshold")\n'
                    "ADTSyncException: Feed {feed_id} sync gap {gap_seconds}s, queue depth {queue_depth}"
                ),
            },
            18: {
                "name": "Data Warehouse ETL Pipeline Stall",
                "subsystem": "analytics",
                "vehicle_section": "etl_pipeline",
                "error_type": "ETLPipelineException",
                "sensor_type": "etl_monitor",
                "affected_services": ["data-warehouse", "billing-processor"],
                "cascade_services": ["ehr-system"],
                "description": "Clinical data warehouse ETL pipeline stalls during extraction or transformation phase",
                "error_message": "ETL pipeline stall: pipeline {pipeline_id} stage {etl_stage} rows processed {rows_processed}/{total_rows} stalled for {stall_seconds}s",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "analytics/etl_manager.py", line 278, in run_pipeline\n'
                    "    self._execute_stage(pipeline_id, stage)\n"
                    '  File "analytics/etl_manager.py", line 256, in _execute_stage\n'
                    "    self._check_progress(pipeline_id, stage, elapsed)\n"
                    '  File "analytics/etl_manager.py", line 234, in _check_progress\n'
                    '    raise ETLPipelineException(f"Pipeline {pipeline_id} stalled at {stage}")\n'
                    "ETLPipelineException: Pipeline {pipeline_id} stalled at {etl_stage}, {rows_processed}/{total_rows} rows"
                ),
            },
            19: {
                "name": "HIPAA Audit Log Integrity Error",
                "subsystem": "analytics",
                "vehicle_section": "audit_subsystem",
                "error_type": "HIPAAAuditException",
                "sensor_type": "audit_log_integrity",
                "affected_services": ["data-warehouse", "ehr-system"],
                "cascade_services": ["clinical-alerts", "billing-processor"],
                "description": "HIPAA-mandated audit log chain integrity check fails, indicating possible tampering or data loss",
                "error_message": "HIPAA audit integrity error: log chain {chain_id} hash mismatch at sequence {sequence_number}, expected {expected_hash} got {actual_hash}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "analytics/audit_verifier.py", line 198, in verify_chain\n'
                    "    computed = self._compute_chain_hash(chain_id, sequence)\n"
                    '  File "analytics/audit_verifier.py", line 176, in _compute_chain_hash\n'
                    "    self._compare_hashes(computed, stored)\n"
                    '  File "analytics/audit_verifier.py", line 154, in _compare_hashes\n'
                    '    raise HIPAAAuditException(f"Hash mismatch at sequence {sequence}")\n'
                    "HIPAAAuditException: Chain {chain_id} integrity failure at sequence {sequence_number}"
                ),
            },
            20: {
                "name": "Telehealth Session Quality Degradation",
                "subsystem": "vital_signs",
                "vehicle_section": "telehealth_engine",
                "error_type": "TelehealthQualityException",
                "sensor_type": "telehealth_qos",
                "affected_services": ["patient-monitor", "clinical-alerts"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Telehealth video session quality degrades below clinical acceptability threshold",
                "error_message": "Telehealth quality degradation: session {session_id} patient {patient_id} bitrate {bitrate_kbps}kbps packet loss {packet_loss_pct}% latency {latency_ms}ms",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "vitals/telehealth_monitor.py", line 234, in check_session_quality\n'
                    "    metrics = self._collect_qos_metrics(session_id)\n"
                    '  File "vitals/telehealth_monitor.py", line 212, in _collect_qos_metrics\n'
                    "    self._evaluate_clinical_threshold(metrics)\n"
                    '  File "vitals/telehealth_monitor.py", line 189, in _evaluate_clinical_threshold\n'
                    '    raise TelehealthQualityException(f"Session {session_id} below clinical threshold")\n'
                    "TelehealthQualityException: Session {session_id} quality degraded: {bitrate_kbps}kbps, {packet_loss_pct}% loss, {latency_ms}ms latency"
                ),
            },
        }

    # -- Topology ---------------------------------------------------------------

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "ehr-system": [
                ("lab-integration", "/api/v1/lab/orders", "POST"),
                ("lab-integration", "/api/v1/lab/results", "GET"),
                ("pharmacy-system", "/api/v1/pharmacy/orders", "POST"),
                ("pharmacy-system", "/api/v1/pharmacy/verify", "GET"),
                ("imaging-service", "/api/v1/imaging/orders", "POST"),
                ("scheduling-api", "/api/v1/schedule/appointments", "GET"),
                ("billing-processor", "/api/v1/billing/charges", "POST"),
                ("clinical-alerts", "/api/v1/alerts/patient", "GET"),
            ],
            "patient-monitor": [
                ("ehr-system", "/api/v1/ehr/vitals", "POST"),
                ("clinical-alerts", "/api/v1/alerts/vital-signs", "POST"),
            ],
            "lab-integration": [
                ("ehr-system", "/api/v1/ehr/results", "POST"),
                ("clinical-alerts", "/api/v1/alerts/critical-lab", "POST"),
            ],
            "pharmacy-system": [
                ("ehr-system", "/api/v1/ehr/medication-admin", "POST"),
                ("clinical-alerts", "/api/v1/alerts/drug-interaction", "POST"),
            ],
            "imaging-service": [
                ("ehr-system", "/api/v1/ehr/imaging-results", "POST"),
                ("data-warehouse", "/api/v1/warehouse/imaging-archive", "POST"),
            ],
            "scheduling-api": [
                ("ehr-system", "/api/v1/ehr/encounter", "POST"),
                ("billing-processor", "/api/v1/billing/encounter-charges", "POST"),
            ],
            "billing-processor": [
                ("data-warehouse", "/api/v1/warehouse/claims", "POST"),
            ],
            "clinical-alerts": [
                ("ehr-system", "/api/v1/ehr/alert-response", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "ehr-system": [
                ("/api/v1/ehr/patient", "GET"),
                ("/api/v1/ehr/encounter", "POST"),
                ("/api/v1/ehr/clinical-notes", "POST"),
            ],
            "patient-monitor": [("/api/v1/vitals/stream", "POST")],
            "lab-integration": [("/api/v1/lab/submit", "POST")],
            "pharmacy-system": [("/api/v1/pharmacy/dispense", "POST")],
            "imaging-service": [("/api/v1/imaging/study", "POST")],
            "scheduling-api": [("/api/v1/schedule/book", "POST")],
            "billing-processor": [("/api/v1/billing/submit-claim", "POST")],
            "clinical-alerts": [("/api/v1/alerts/evaluate", "POST")],
            "data-warehouse": [("/api/v1/warehouse/etl-trigger", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "ehr-system": [
                ("SELECT", "patient_demographics", "SELECT * FROM patient_demographics WHERE mrn = ? AND facility_id = ?"),
                ("INSERT", "clinical_encounters", "INSERT INTO clinical_encounters (patient_id, encounter_type, admit_dt, provider_id) VALUES (?, ?, NOW(), ?)"),
                ("UPDATE", "patient_chart", "UPDATE patient_chart SET last_modified = NOW(), modified_by = ? WHERE patient_id = ?"),
            ],
            "patient-monitor": [
                ("INSERT", "vital_readings", "INSERT INTO vital_readings (patient_id, hr, bp_sys, bp_dia, spo2, temp, rr, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, NOW())"),
                ("SELECT", "alert_thresholds", "SELECT threshold_type, min_val, max_val FROM alert_thresholds WHERE unit_id = ? AND active = 1"),
            ],
            "lab-integration": [
                ("SELECT", "lab_orders", "SELECT order_id, test_code, priority, status FROM lab_orders WHERE patient_id = ? AND status IN ('pending', 'in-progress')"),
                ("INSERT", "lab_results", "INSERT INTO lab_results (order_id, test_code, value, unit, reference_range, abnormal_flag) VALUES (?, ?, ?, ?, ?, ?)"),
            ],
            "pharmacy-system": [
                ("SELECT", "medication_orders", "SELECT rx_id, drug_code, dose, route, frequency FROM medication_orders WHERE patient_id = ? AND status = 'active'"),
                ("SELECT", "drug_interactions", "SELECT drug_a, drug_b, severity, description FROM drug_interactions WHERE drug_a IN (?) OR drug_b IN (?)"),
            ],
            "billing-processor": [
                ("SELECT", "claim_submissions", "SELECT claim_id, payer_id, total_charges, status FROM claim_submissions WHERE batch_id = ? ORDER BY created_at"),
                ("INSERT", "claim_submissions", "INSERT INTO claim_submissions (encounter_id, payer_id, total_charges, dx_codes, cpt_codes) VALUES (?, ?, ?, ?, ?)"),
            ],
            "data-warehouse": [
                ("SELECT", "etl_pipeline_status", "SELECT pipeline_id, stage, rows_processed, total_rows, started_at FROM etl_pipeline_status WHERE status = 'running'"),
            ],
        }

    # -- Infrastructure ---------------------------------------------------------

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "healthcare-aws-host-01",
                "host.id": "i-0h1c2a3l4t5h67890",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0healthcare12345a",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.2.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "234567890123",
                "cloud.instance.id": "i-0h1c2a3l4t5h67890",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "healthcare-gcp-host-01",
                "host.id": "6738912345678901234",
                "host.arch": "amd64",
                "host.type": "e2-standard-4",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.20GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.1.20", "10.128.1.21"],
                "host.mac": ["42:01:0a:81:01:14", "42:01:0a:81:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "healthcare-project-prod",
                "cloud.instance.id": "6738912345678901234",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "healthcare-azure-host-01",
                "host.id": "/subscriptions/hca-def/resourceGroups/healthcare-rg/providers/Microsoft.Compute/virtualMachines/healthcare-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.4", "10.2.0.5"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "hca-def-ghi-jkl",
                "cloud.instance.id": "healthcare-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "healthcare-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["ehr-system", "patient-monitor", "lab-integration"],
            },
            {
                "name": "healthcare-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["pharmacy-system", "imaging-service", "scheduling-api"],
            },
            {
                "name": "healthcare-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["billing-processor", "clinical-alerts", "data-warehouse"],
            },
        ]

    # -- Theme ------------------------------------------------------------------

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#f5f5f5",
            bg_secondary="#ffffff",
            bg_tertiary="#e8e8e8",
            accent_primary="#00796b",
            accent_secondary="#004d40",
            text_primary="#212121",
            text_secondary="#757575",
            text_accent="#00796b",
            status_nominal="#2e7d32",
            status_warning="#f9a825",
            status_critical="#c62828",
            status_info="#1565c0",
            font_family="'Inter', system-ui, sans-serif",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            dashboard_title="Clinical Systems Dashboard",
            chaos_title="System Disruption Simulator",
            landing_title="Clinical Systems Operations",
            service_label="Service",
            channel_label="Channel",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # -- Agent Config -----------------------------------------------------------

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "healthcare-clinical-analyst",
            "name": "Clinical Systems Analyst",
            "assessment_tool_name": "patient_safety_assessment",
            "system_prompt": (
                "You are the Clinical Systems Analyst, an expert AI assistant for "
                "hospital clinical operations. You help IT operations teams investigate "
                "system anomalies, analyze integration failures, and provide root cause "
                "analysis for fault conditions across 9 clinical systems including EHR, "
                "patient monitoring, laboratory, pharmacy, imaging (DICOM/PACS), "
                "scheduling, billing (X12), clinical alerting, and data warehouse. "
                "You are well-versed in HL7 v2.x messaging, DICOM protocols, HIPAA "
                "compliance requirements, NCPDP SCRIPT e-prescribing, X12 270/271 "
                "eligibility and 837 claims transactions, ADT workflows, and clinical "
                "decision support systems."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "patient_safety_assessment",
            "description": (
                "Comprehensive patient safety assessment. Evaluates all "
                "clinical systems against operational health criteria for patient care "
                "continuity. Returns data for safety evaluation across EHR, patient "
                "monitoring, laboratory, pharmacy, and imaging systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # -- Service Classes --------------------------------------------------------

    def get_service_classes(self) -> list[type]:
        from scenarios.healthcare.services.ehr_system import EHRSystemService
        from scenarios.healthcare.services.patient_monitor import PatientMonitorService
        from scenarios.healthcare.services.lab_integration import LabIntegrationService
        from scenarios.healthcare.services.pharmacy_system import PharmacySystemService
        from scenarios.healthcare.services.imaging_service import ImagingServiceService
        from scenarios.healthcare.services.scheduling_api import SchedulingAPIService
        from scenarios.healthcare.services.billing_processor import BillingProcessorService
        from scenarios.healthcare.services.clinical_alerts import ClinicalAlertsService
        from scenarios.healthcare.services.data_warehouse import DataWarehouseService

        return [
            EHRSystemService,
            PatientMonitorService,
            LabIntegrationService,
            PharmacySystemService,
            ImagingServiceService,
            SchedulingAPIService,
            BillingProcessorService,
            ClinicalAlertsService,
            DataWarehouseService,
        ]

    # -- Fault Parameters -------------------------------------------------------

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            # Patient/clinical identifiers
            "patient_id": f"PT-{random.randint(100000, 999999)}",
            "mrn": f"MRN-{random.randint(1000000, 9999999)}",
            "encounter_id": f"ENC-{random.randint(100000, 999999)}",
            # HL7 / ADT
            "msg_type": random.choice(["ADT^A01", "ADT^A03", "ADT^A08", "ORU^R01", "ORM^O01"]),
            "hl7_segment": random.choice(["PID", "PV1", "OBX", "OBR", "MSH", "NK1", "DG1"]),
            "position": random.randint(1, 25),
            "adt_event_type": random.choice(["A01", "A02", "A03", "A04", "A08"]),
            "feed_id": random.choice(["ADT-FEED-01", "ADT-FEED-02", "ADT-FEED-03"]),
            # Vitals
            "alert_count": random.randint(15, 120),
            "window_seconds": random.choice([30, 60, 120]),
            "nursing_unit": random.choice(["ICU-3A", "ICU-3B", "MedSurg-4N", "MedSurg-4S", "ED-1", "NICU-2"]),
            "heart_rate": random.randint(35, 180),
            "spo2": random.randint(70, 100),
            # Lab
            "lab_order_id": f"LAB-{random.randint(100000, 999999)}",
            "test_code": random.choice(["CBC", "BMP", "CMP", "PT/INR", "Troponin", "BNP", "Lipase", "UA"]),
            "tat_minutes": random.randint(60, 360),
            "max_tat": random.choice([30, 45, 60]),
            # DICOM / Imaging
            "dicom_study_uid": f"1.2.840.{random.randint(10000, 99999)}.{random.randint(1, 999)}.{random.randint(1, 99)}",
            "modality": random.choice(["CT", "MRI", "XR", "US", "MG", "NM"]),
            "dicom_operation": random.choice(["C-STORE", "C-MOVE", "C-FIND"]),
            "dicom_error_code": f"0x{random.choice(['A700', 'A900', 'C000', 'A801'])}",
            "volume_id": random.choice(["PACS-VOL-01", "PACS-VOL-02", "PACS-ARCHIVE-01"]),
            "usage_pct": round(random.uniform(88.0, 98.5), 1),
            "threshold_pct": 85.0,
            "remaining_gb": random.randint(50, 500),
            # Pharmacy / Medication
            "medication_id": f"MED-{random.randint(10000, 99999)}",
            "interaction_count": random.randint(50, 500),
            "severity_level": random.choice(["critical", "major", "moderate"]),
            "prescription_id": f"RX-{random.randint(100000, 999999)}",
            "pharmacy_npi": f"{random.randint(1000000000, 9999999999)}",
            "ncpdp_status": random.choice(["000", "600", "900", "510", "210"]),
            # Patient identity
            "match_score": round(random.uniform(45.0, 78.0), 1),
            "match_threshold": 85.0,
            # Scheduling / Beds
            "bed_id": f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(101, 450)}",
            "bed_status": random.choice(["occupied", "vacant", "cleaning", "blocked"]),
            "adt_event": random.choice(["discharge", "transfer", "admit"]),
            "sync_lag_seconds": random.randint(60, 600),
            "provider_id": f"NPI-{random.randint(1000000000, 9999999999)}",
            "time_slot": f"{random.randint(7, 17):02d}:{random.choice(['00', '15', '30', '45'])}",
            "resource_type": random.choice(["exam_room", "procedure_room", "consult_room"]),
            # Surgical
            "or_number": f"OR-{random.randint(1, 12)}",
            "case_id": f"SURG-{random.randint(10000, 99999)}",
            "surgeon_id": f"NPI-{random.randint(1000000000, 9999999999)}",
            "conflict_time": f"{random.randint(7, 17):02d}:{random.choice(['00', '30'])}",
            # Billing / Insurance
            "insurance_id": f"INS-{random.randint(100000, 999999)}",
            "payer_id": random.choice(["BCBS-001", "AETNA-002", "UHC-003", "CIGNA-004", "MDCR-005", "MDCD-006"]),
            "elapsed_ms": random.randint(5000, 30000),
            "timeout_ms": 5000,
            "batch_id": f"BATCH-{random.randint(1000, 9999)}",
            "claim_id": f"CLM-{random.randint(100000, 999999)}",
            "claim_stage": random.choice(["validation", "scrubbing", "submission", "adjudication"]),
            # Clinical alerts / CDS
            "pending_rules": random.randint(50, 500),
            "eval_ms": random.randint(3000, 15000),
            "max_eval_ms": 2000,
            "station_id": f"NCS-{random.choice(['ICU', 'MEDSURG', 'ED', 'NICU'])}-{random.randint(1, 20)}",
            "call_type": random.choice(["emergency", "routine", "bathroom", "pain_management"]),
            "undelivered_seconds": random.randint(30, 300),
            # Blood bank
            "blood_product": random.choice(["PRBC", "FFP", "Platelets", "Cryoprecipitate"]),
            "blood_type": random.choice(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]),
            "units_on_hand": random.randint(2, 15),
            "system_count": random.randint(8, 25),
            "discrepancy": random.randint(3, 12),
            # ADT sync
            "gap_seconds": random.randint(60, 600),
            "queue_depth": random.randint(100, 5000),
            # ETL / Data Warehouse
            "pipeline_id": random.choice(["ETL-CLINICAL-01", "ETL-BILLING-02", "ETL-LAB-03", "ETL-QUALITY-04"]),
            "etl_stage": random.choice(["extract", "transform", "load", "validate"]),
            "rows_processed": random.randint(10000, 500000),
            "total_rows": random.randint(500000, 2000000),
            "stall_seconds": random.randint(120, 1800),
            # HIPAA audit
            "chain_id": f"AUDIT-{random.randint(1000, 9999)}",
            "sequence_number": random.randint(1, 100000),
            "expected_hash": f"sha256:{secrets.token_hex(16)}",
            "actual_hash": f"sha256:{secrets.token_hex(16)}",
            # Telehealth
            "session_id": f"TH-{random.randint(100000, 999999)}",
            "bitrate_kbps": random.randint(128, 512),
            "packet_loss_pct": round(random.uniform(5.0, 25.0), 1),
            "latency_ms": random.randint(200, 2000),
        }


# Module-level instance for registry discovery
scenario = HealthcareScenario()
