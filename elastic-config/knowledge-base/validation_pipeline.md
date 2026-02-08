# Validation Pipeline Anomaly — Root Cause Analysis Guide

## Overview

Validation Pipeline Anomaly (Channel 17) occurs when the sensor data validation pipeline experiences processing failures, backlog accumulation, or rule evaluation errors that prevent timely validation of incoming telemetry data. This anomaly is detected by the `ValidationPipelineException` error type on `pipeline_health` sensors in the `ground_network` vehicle section.

## Error Signature

- **Error Type**: `ValidationPipelineException`
- **Sensor Type**: `pipeline_health`
- **Vehicle Section**: `ground_network`
- **Affected Services**: sensor-validator (Azure eastus)
- **Cascade Services**: mission-control (AWS us-east-1), telemetry-relay (Azure eastus)

## Subsystem Context

The validation subsystem is the central quality gate for all telemetry data in the NOVA-7 mission. The sensor-validator service (Azure) receives raw telemetry from all 9 mission services and applies a series of validation rules: range checks, rate-of-change limits, cross-sensor consistency checks, and historical pattern matching. Validated data is tagged and forwarded to mission-control and the telemetry-relay for distribution. When the validation pipeline stalls or fails, downstream consumers either receive unvalidated data (reducing confidence) or experience data gaps.

## Common Root Causes

### 1. Validation Rule Evaluation Backlog
**Probability**: High
**Description**: During periods of high anomaly activity (multiple channels firing simultaneously), the volume of validation rules being evaluated increases dramatically, causing the pipeline to fall behind real-time processing.
**Diagnostic Steps**:
- Check the validation pipeline queue depth and processing latency
- Identify how many anomaly channels are currently active — each active channel increases validation load
- Verify if specific rule categories (cross-sensor checks, historical pattern matching) are the bottleneck

### 2. Database Connection Pool Exhaustion
**Probability**: Medium
**Description**: The validation rules reference baseline values and historical data stored in the validation database. Under high load, the connection pool can be exhausted, causing rule evaluation to block while waiting for database connections.
**Diagnostic Steps**:
- Check database connection pool utilization and wait times
- Verify database response latency for validation queries
- Look for connection timeout errors in the sensor-validator logs

### 3. Rule Configuration Error
**Probability**: Medium
**Description**: A recent update to validation rules may contain errors (incorrect thresholds, malformed expressions, circular dependencies) that cause the rule engine to enter an error state or infinite loop.
**Diagnostic Steps**:
- Check the timestamp of the most recent rule configuration update
- Look for rule evaluation error messages or timeouts in the sensor-validator logs
- Verify if the pipeline failure affects all data streams or only specific instrument types

### 4. Azure Service Degradation
**Probability**: Low
**Description**: The sensor-validator runs on Azure eastus. Azure platform issues (compute throttling, storage latency, network congestion) can degrade the validation pipeline performance.
**Diagnostic Steps**:
- Check Azure status page for eastus region service health
- Monitor sensor-validator pod CPU and memory utilization
- Verify Azure storage and database service response times

## Remediation Procedures

### Immediate Actions
1. **Assess data quality impact**: Determine what percentage of telemetry data is being validated versus passing through unvalidated.
2. **Check pipeline health metrics**: Review queue depth, processing latency, and error rates.
3. **Verify critical channel coverage**: Ensure that safety-critical channels (FTS, range safety) are still being validated even if other channels experience delays.

### Corrective Actions
1. **Scale pipeline workers**: Increase the number of validation worker instances to process the backlog.
2. **Reduce validation scope**: Temporarily disable non-critical validation rules (e.g., historical pattern matching) to prioritize real-time range checks and safety rules.
3. **Reset connection pool**: If database connection exhaustion is the cause, restart the connection pool and increase the pool size.

### Escalation Criteria
- Validation latency exceeds 30 seconds: Data quality compromised, escalate to data integrity team
- Safety-critical channels not being validated: Escalate to range safety officer immediately
- Pipeline completely stalled for more than 60 seconds: Request hold until validation is restored

## Historical Precedents

### NOVA-4 Cascading Validation Overload
During NOVA-4 countdown, a multi-channel anomaly event (Channels 1, 2, and 7 fired simultaneously) caused the validation pipeline to accumulate a 45-second backlog. Resolution: non-critical validation rules were temporarily suspended, and additional worker pods were scaled up. Pipeline caught up within 3 minutes.

### NOVA-6 Rule Engine Infinite Loop
A rule configuration update for NOVA-6 introduced a circular dependency between two cross-sensor validation rules, causing the rule engine to enter an infinite evaluation loop. Resolution: the offending rules were identified and disabled. Rule dependency analysis tooling was added to prevent recurrence.

## Related Channels
- Channel 13: Relay Packet Corruption (data integrity dependency)
- Channel 18: Calibration Epoch Mismatch (calibration data feeding validation rules)
- Channel 12: Cross-Cloud Relay Latency (data delivery timing)
- Channel 19: FTS Safety Check (safety validation priority)
