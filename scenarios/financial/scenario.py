"""Financial Trading Platform scenario — real-time trading operations with order management,
matching engine, risk calculation, market data, and settlement systems."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class FinancialScenario(BaseScenario):
    """Financial trading platform with 9 trading services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "financial"

    @property
    def scenario_name(self) -> str:
        return "Financial Trading Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Real-time trading operations with order management, matching engine, "
            "risk calculation, market data, and settlement systems. Bloomberg "
            "terminal-style Operations Center."
        )

    @property
    def namespace(self) -> str:
        return "finserv"

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "order-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "order_management",
                "language": "java",
            },
            "matching-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "trade_execution",
                "language": "cpp",
            },
            "risk-calculator": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "risk_management",
                "language": "python",
            },
            "market-data-feed": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "market_data",
                "language": "go",
            },
            "settlement-processor": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "settlement",
                "language": "java",
            },
            "fraud-detector": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "compliance",
                "language": "python",
            },
            "compliance-monitor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "compliance",
                "language": "dotnet",
            },
            "customer-portal": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "client_services",
                "language": "python",
            },
            "audit-logger": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "audit",
                "language": "go",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Order Book Inconsistency",
                "subsystem": "order_management",
                "vehicle_section": "order_book",
                "error_type": "OrderBookException",
                "sensor_type": "order_book_integrity",
                "affected_services": ["order-gateway", "matching-engine"],
                "cascade_services": ["risk-calculator", "audit-logger"],
                "description": "Order book bid/ask levels out of sync between primary and replica shards",
                "error_message": "Order book inconsistency: instrument {instrument} bid/ask spread {spread} ticks exceeds max {max_spread} ticks on book {book_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "order_management/order_book_engine.py", line 412, in validate_book_state\n'
                    "    spread = self._compute_bid_ask_spread(instrument, book_id)\n"
                    '  File "order_management/order_book_engine.py", line 387, in _compute_bid_ask_spread\n'
                    "    replica_state = self.replica_store.get_snapshot(book_id)\n"
                    '  File "order_management/book_replicator.py", line 234, in get_snapshot\n'
                    '    raise OrderBookException(f"Book {book_id} spread {spread} ticks > max {max_spread}")\n'
                    "OrderBookException: Order book {book_id} inconsistency for {instrument}, spread {spread} ticks"
                ),
            },
            2: {
                "name": "Matching Engine Latency",
                "subsystem": "trade_execution",
                "vehicle_section": "matching_core",
                "error_type": "MatchingLatencyException",
                "sensor_type": "latency_monitor",
                "affected_services": ["matching-engine", "order-gateway"],
                "cascade_services": ["risk-calculator", "settlement-processor"],
                "description": "Matching engine order processing latency exceeds SLA threshold",
                "error_message": "Matching engine latency spike: order {order_id} processing took {latency_us}us, SLA threshold {sla_us}us on partition {partition_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "trade_execution/matching_engine.cpp", line 1847, in process_order\n'
                    "    auto elapsed = clock::now() - start;\n"
                    '  File "trade_execution/matching_engine.cpp", line 1852, in process_order\n'
                    '    if (elapsed_us > sla_threshold_us) throw MatchingLatencyException(order_id, elapsed_us);\n'
                    '  File "trade_execution/latency_guard.cpp", line 94, in check_sla\n'
                    '    throw MatchingLatencyException("Order " + order_id + " exceeded SLA: " + std::to_string(latency_us) + "us");\n'
                    "MatchingLatencyException: Order {order_id} matching latency {latency_us}us exceeds {sla_us}us SLA"
                ),
            },
            3: {
                "name": "Price Feed Gap",
                "subsystem": "market_data",
                "vehicle_section": "feed_handler",
                "error_type": "PriceFeedGapException",
                "sensor_type": "feed_continuity",
                "affected_services": ["market-data-feed", "matching-engine"],
                "cascade_services": ["risk-calculator", "customer-portal"],
                "description": "Market data feed missing price ticks for one or more instruments",
                "error_message": "Price feed gap detected: {symbol} no ticks for {gap_ms}ms from exchange {exchange}, sequence gap {seq_start}-{seq_end}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "market_data/feed_handler.go", line 523, in processFeed\n'
                    "    gap := time.Since(lastTick)\n"
                    '  File "market_data/feed_handler.go", line 531, in processFeed\n'
                    '    return fmt.Errorf("PriceFeedGapException: %s gap %dms from %s", symbol, gap.Milliseconds(), exchange)\n'
                    '  File "market_data/sequence_tracker.go", line 178, in validateSequence\n'
                    '    panic(PriceFeedGapException{Symbol: symbol, GapMs: gapMs, Exchange: exchange})\n'
                    "PriceFeedGapException: {symbol} feed gap {gap_ms}ms from {exchange}, seq {seq_start}-{seq_end}"
                ),
            },
            4: {
                "name": "Risk Limit Breach",
                "subsystem": "risk_management",
                "vehicle_section": "risk_engine",
                "error_type": "RiskLimitException",
                "sensor_type": "risk_threshold",
                "affected_services": ["risk-calculator", "order-gateway"],
                "cascade_services": ["matching-engine", "compliance-monitor"],
                "description": "Trading desk risk exposure exceeds configured limit thresholds",
                "error_message": "Risk limit breach: desk {desk_id} exposure ${exposure} exceeds limit ${risk_limit} for asset class {asset_class}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "risk_management/risk_engine.py", line 678, in evaluate_position\n'
                    "    exposure = self._calculate_net_exposure(desk_id, asset_class)\n"
                    '  File "risk_management/risk_engine.py", line 645, in _calculate_net_exposure\n'
                    "    return self.position_aggregator.get_exposure(desk_id)\n"
                    '  File "risk_management/limit_checker.py", line 312, in check_limits\n'
                    '    raise RiskLimitException(f"Desk {desk_id} exposure ${exposure} > limit ${risk_limit}")\n'
                    "RiskLimitException: Desk {desk_id} exposure ${exposure} exceeds ${risk_limit} limit for {asset_class}"
                ),
            },
            5: {
                "name": "Margin Call Calculation Error",
                "subsystem": "risk_management",
                "vehicle_section": "margin_system",
                "error_type": "MarginCallException",
                "sensor_type": "margin_calculator",
                "affected_services": ["risk-calculator", "settlement-processor"],
                "cascade_services": ["customer-portal", "compliance-monitor"],
                "description": "Margin requirement calculation fails due to stale collateral valuations",
                "error_message": "Margin call calculation error: account {account_id} margin_ratio {margin_ratio} below maintenance {maintenance_ratio}, collateral valuation age {valuation_age_s}s",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "risk_management/margin_engine.py", line 456, in calculate_margin\n'
                    "    collateral = self._value_collateral(account_id)\n"
                    '  File "risk_management/margin_engine.py", line 423, in _value_collateral\n'
                    "    if valuation_age > MAX_COLLATERAL_STALENESS:\n"
                    '  File "risk_management/margin_engine.py", line 428, in _value_collateral\n'
                    '    raise MarginCallException(f"Account {account_id} margin ratio {margin_ratio} < {maintenance_ratio}")\n'
                    "MarginCallException: Account {account_id} margin_ratio {margin_ratio} below maintenance {maintenance_ratio}"
                ),
            },
            6: {
                "name": "Position Reconciliation Failure",
                "subsystem": "risk_management",
                "vehicle_section": "position_keeper",
                "error_type": "PositionReconException",
                "sensor_type": "reconciliation",
                "affected_services": ["risk-calculator", "settlement-processor"],
                "cascade_services": ["audit-logger"],
                "description": "Position records diverge between real-time and end-of-day systems",
                "error_message": "Position reconciliation failure: {instrument} position mismatch {realtime_qty} vs EOD {eod_qty}, delta {position_delta} lots for account {account_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "risk_management/position_reconciler.py", line 345, in reconcile\n'
                    "    rt_pos = self.realtime_positions.get(instrument, account_id)\n"
                    '  File "risk_management/position_reconciler.py", line 352, in reconcile\n'
                    "    eod_pos = self.eod_positions.get(instrument, account_id)\n"
                    '  File "risk_management/position_reconciler.py", line 361, in reconcile\n'
                    '    raise PositionReconException(f"{instrument} position mismatch: RT={rt_pos} EOD={eod_pos}")\n'
                    "PositionReconException: {instrument} position mismatch RT={realtime_qty} EOD={eod_qty} delta={position_delta}"
                ),
            },
            7: {
                "name": "Settlement Timeout",
                "subsystem": "settlement",
                "vehicle_section": "settlement_engine",
                "error_type": "SettlementTimeoutException",
                "sensor_type": "settlement_timer",
                "affected_services": ["settlement-processor", "audit-logger"],
                "cascade_services": ["risk-calculator", "compliance-monitor"],
                "description": "Trade settlement fails to complete within T+2 SLA window",
                "error_message": "Settlement timeout: trade {trade_id} settlement_id {settlement_id} pending {pending_hours}h, SLA {sla_hours}h for counterparty {counterparty}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "settlement/settlement_engine.java", line 712, in processSettlement\n'
                    "    Duration elapsed = Duration.between(tradeDate, Instant.now());\n"
                    '  File "settlement/settlement_engine.java", line 718, in processSettlement\n'
                    "    if (elapsed.toHours() > slaHours) throw new SettlementTimeoutException(tradeId);\n"
                    '  File "settlement/sla_monitor.java", line 234, in checkSLA\n'
                    '    throw new SettlementTimeoutException("Trade " + tradeId + " settlement timeout after " + hours + "h");\n'
                    "SettlementTimeoutException: Trade {trade_id} settlement {settlement_id} timeout after {pending_hours}h"
                ),
            },
            8: {
                "name": "Failed Trade Settlement",
                "subsystem": "settlement",
                "vehicle_section": "settlement_engine",
                "error_type": "SettlementFailureException",
                "sensor_type": "settlement_status",
                "affected_services": ["settlement-processor", "risk-calculator"],
                "cascade_services": ["compliance-monitor", "audit-logger"],
                "description": "Trade settlement fails due to insufficient securities or funding",
                "error_message": "Settlement failure: trade {trade_id} failed for {instrument} qty {quantity}, reason: {failure_reason}, counterparty {counterparty}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "settlement/delivery_manager.java", line 456, in executeDelivery\n'
                    "    AvailableInventory inv = inventoryService.check(instrument, quantity);\n"
                    '  File "settlement/delivery_manager.java", line 463, in executeDelivery\n'
                    '    if (!inv.sufficient()) throw new SettlementFailureException("Insufficient " + instrument);\n'
                    '  File "settlement/funding_validator.java", line 189, in validateFunding\n'
                    '    throw new SettlementFailureException("Trade " + tradeId + ": " + reason);\n'
                    "SettlementFailureException: Trade {trade_id} settlement failed for {instrument}: {failure_reason}"
                ),
            },
            9: {
                "name": "Netting Calculation Error",
                "subsystem": "settlement",
                "vehicle_section": "netting_engine",
                "error_type": "NettingCalcException",
                "sensor_type": "netting_integrity",
                "affected_services": ["settlement-processor", "risk-calculator"],
                "cascade_services": ["audit-logger", "compliance-monitor"],
                "description": "Multilateral netting calculation produces inconsistent net obligations",
                "error_message": "Netting calculation error: batch {batch_id} net obligation mismatch ${net_mismatch} across {counterparty_count} counterparties for {currency}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "settlement/netting_engine.java", line 567, in computeNetObligations\n'
                    "    BigDecimal netSum = obligations.stream().reduce(BigDecimal.ZERO, BigDecimal::add);\n"
                    '  File "settlement/netting_engine.java", line 574, in computeNetObligations\n'
                    "    if (netSum.abs().compareTo(TOLERANCE) > 0) throw new NettingCalcException(batchId);\n"
                    '  File "settlement/netting_validator.java", line 123, in validate\n'
                    '    throw new NettingCalcException("Batch " + batchId + " net mismatch $" + mismatch);\n'
                    "NettingCalcException: Batch {batch_id} netting mismatch ${net_mismatch} for {currency}"
                ),
            },
            10: {
                "name": "Fraud Detection False Positive Storm",
                "subsystem": "compliance",
                "vehicle_section": "fraud_engine",
                "error_type": "FraudFalsePositiveException",
                "sensor_type": "fraud_classifier",
                "affected_services": ["fraud-detector", "order-gateway"],
                "cascade_services": ["compliance-monitor", "customer-portal"],
                "description": "Fraud detection model generating excessive false positive alerts blocking legitimate orders",
                "error_message": "Fraud false positive storm: {blocked_orders} orders blocked in {window_s}s window, FP rate {fp_rate}% for pattern {pattern_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "compliance/fraud_detector.py", line 389, in classify_order\n'
                    "    score = self.model.predict(features)\n"
                    '  File "compliance/fraud_detector.py", line 395, in classify_order\n'
                    "    if self._is_false_positive_storm(pattern_id, window_s):\n"
                    '  File "compliance/fp_monitor.py", line 167, in check_storm\n'
                    '    raise FraudFalsePositiveException(f"FP storm: {blocked} orders in {window}s, rate {rate}%")\n'
                    "FraudFalsePositiveException: {blocked_orders} orders blocked, FP rate {fp_rate}% for pattern {pattern_id}"
                ),
            },
            11: {
                "name": "Regulatory Report Generation Failure",
                "subsystem": "compliance",
                "vehicle_section": "reporting_engine",
                "error_type": "RegReportException",
                "sensor_type": "report_generator",
                "affected_services": ["compliance-monitor", "audit-logger"],
                "cascade_services": ["settlement-processor"],
                "description": "Mandatory regulatory report fails to generate before submission deadline",
                "error_message": "Regulatory report failure: report {report_type} for period {report_period} failed at stage {stage}, deadline {deadline_utc}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "compliance/report_generator.cs", line 478, in GenerateReport\n'
                    "    var data = _aggregator.CollectReportData(reportType, period);\n"
                    '  File "compliance/report_generator.cs", line 491, in GenerateReport\n'
                    "    if (data.ValidationErrors.Any()) throw new RegReportException(reportType);\n"
                    '  File "compliance/report_validator.cs", line 234, in Validate\n'
                    '    throw new RegReportException($"Report {reportType} for {period} failed at {stage}");\n'
                    "RegReportException: Report {report_type} for {report_period} failed at stage {stage}"
                ),
            },
            12: {
                "name": "AML Screening Timeout",
                "subsystem": "compliance",
                "vehicle_section": "screening_engine",
                "error_type": "AMLScreeningException",
                "sensor_type": "aml_screener",
                "affected_services": ["compliance-monitor", "fraud-detector"],
                "cascade_services": ["order-gateway", "customer-portal"],
                "description": "Anti-money laundering screening service exceeds response time SLA",
                "error_message": "AML screening timeout: transaction {transaction_id} screening took {screening_ms}ms, SLA {aml_sla_ms}ms for jurisdiction {jurisdiction}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "compliance/aml_screener.cs", line 345, in ScreenTransaction\n'
                    "    var result = await _watchlistService.CheckAsync(transactionId, timeout);\n"
                    '  File "compliance/aml_screener.cs", line 352, in ScreenTransaction\n'
                    "    if (elapsed > slaMs) throw new AMLScreeningException(transactionId);\n"
                    '  File "compliance/watchlist_client.cs", line 189, in CheckAsync\n'
                    '    throw new AMLScreeningException($"Transaction {txnId} screening {elapsed}ms > SLA {sla}ms");\n'
                    "AMLScreeningException: Transaction {transaction_id} screening timeout {screening_ms}ms in {jurisdiction}"
                ),
            },
            13: {
                "name": "Customer Session Timeout",
                "subsystem": "client_services",
                "vehicle_section": "portal_gateway",
                "error_type": "SessionTimeoutException",
                "sensor_type": "session_manager",
                "affected_services": ["customer-portal", "order-gateway"],
                "cascade_services": ["audit-logger"],
                "description": "Customer trading sessions expiring mid-transaction causing order failures",
                "error_message": "Session timeout: session {session_id} for user {user_id} expired after {session_age_s}s during {operation}, orders_pending {pending_orders}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "client_services/session_manager.py", line 267, in validate_session\n'
                    "    age = time.time() - session.created_at\n"
                    '  File "client_services/session_manager.py", line 273, in validate_session\n'
                    "    if age > self.max_session_age:\n"
                    '  File "client_services/session_manager.py", line 278, in validate_session\n'
                    '    raise SessionTimeoutException(f"Session {session_id} expired after {age}s")\n'
                    "SessionTimeoutException: Session {session_id} for {user_id} expired after {session_age_s}s"
                ),
            },
            14: {
                "name": "Portfolio Valuation Lag",
                "subsystem": "client_services",
                "vehicle_section": "valuation_engine",
                "error_type": "ValuationLagException",
                "sensor_type": "valuation_timer",
                "affected_services": ["customer-portal", "risk-calculator"],
                "cascade_services": ["compliance-monitor"],
                "description": "Real-time portfolio valuation falling behind, showing stale P&L to clients",
                "error_message": "Portfolio valuation lag: portfolio {portfolio_id} last valued {lag_s}s ago, max {max_lag_s}s, {position_count} positions pending revaluation",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "client_services/valuation_engine.py", line 523, in revalue_portfolio\n'
                    "    lag = time.time() - self._last_valuation[portfolio_id]\n"
                    '  File "client_services/valuation_engine.py", line 529, in revalue_portfolio\n'
                    "    if lag > max_lag_s:\n"
                    '  File "client_services/valuation_engine.py", line 534, in revalue_portfolio\n'
                    '    raise ValuationLagException(f"Portfolio {portfolio_id} valuation lag {lag}s")\n'
                    "ValuationLagException: Portfolio {portfolio_id} valuation lag {lag_s}s exceeds {max_lag_s}s max"
                ),
            },
            15: {
                "name": "Trade Confirmation Delay",
                "subsystem": "client_services",
                "vehicle_section": "confirmation_service",
                "error_type": "ConfirmationDelayException",
                "sensor_type": "confirmation_timer",
                "affected_services": ["customer-portal", "settlement-processor"],
                "cascade_services": ["audit-logger", "compliance-monitor"],
                "description": "Trade confirmation messages delayed beyond regulatory reporting window",
                "error_message": "Trade confirmation delay: trade {trade_id} confirmation pending {delay_s}s, regulatory max {reg_max_s}s for {instrument} qty {quantity}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "client_services/confirmation_service.py", line 389, in send_confirmation\n'
                    "    delay = time.time() - trade.execution_time\n"
                    '  File "client_services/confirmation_service.py", line 395, in send_confirmation\n'
                    "    if delay > reg_max_s:\n"
                    '  File "client_services/confirmation_service.py", line 400, in send_confirmation\n'
                    '    raise ConfirmationDelayException(f"Trade {trade_id} confirmation delay {delay}s")\n'
                    "ConfirmationDelayException: Trade {trade_id} confirmation delayed {delay_s}s for {instrument}"
                ),
            },
            16: {
                "name": "Audit Log Sequence Gap",
                "subsystem": "audit",
                "vehicle_section": "audit_pipeline",
                "error_type": "AuditSequenceException",
                "sensor_type": "sequence_validator",
                "affected_services": ["audit-logger", "compliance-monitor"],
                "cascade_services": ["settlement-processor"],
                "description": "Audit trail event sequence numbers have gaps indicating lost events",
                "error_message": "Audit log sequence gap: stream {audit_stream} sequence {expected_seq} missing, last seen {last_seq}, gap count {gap_count} events",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "audit/sequence_validator.go", line 234, in ValidateSequence\n'
                    "    if next != expected {\n"
                    '  File "audit/sequence_validator.go", line 241, in ValidateSequence\n'
                    '    return fmt.Errorf("AuditSequenceException: stream %s seq %d missing, last %d", stream, expected, last)\n'
                    '  File "audit/audit_pipeline.go", line 178, in processEvent\n'
                    '    panic(AuditSequenceException{Stream: stream, Expected: expected, Last: last})\n'
                    "AuditSequenceException: Stream {audit_stream} sequence gap at {expected_seq}, last {last_seq}"
                ),
            },
            17: {
                "name": "Cross-Region Replication Lag",
                "subsystem": "audit",
                "vehicle_section": "replication_bus",
                "error_type": "ReplicationLagException",
                "sensor_type": "replication_monitor",
                "affected_services": ["audit-logger", "settlement-processor"],
                "cascade_services": ["compliance-monitor", "risk-calculator"],
                "description": "Cross-region audit log replication falling behind, DR site stale",
                "error_message": "Replication lag: {source_region}->{dest_region} lag {lag_ms}ms exceeds {max_lag_ms}ms threshold, {pending_events} events pending",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "audit/replication_monitor.go", line 312, in checkLag\n'
                    "    lag := time.Since(lastReplicated)\n"
                    '  File "audit/replication_monitor.go", line 318, in checkLag\n'
                    '    if lag.Milliseconds() > maxLag {\n'
                    '  File "audit/replication_monitor.go", line 323, in checkLag\n'
                    '    return fmt.Errorf("ReplicationLagException: %s->%s lag %dms > %dms", src, dst, lag, max)\n'
                    "ReplicationLagException: {source_region}->{dest_region} replication lag {lag_ms}ms exceeds {max_lag_ms}ms"
                ),
            },
            18: {
                "name": "Market Data Stale Quote",
                "subsystem": "market_data",
                "vehicle_section": "quote_cache",
                "error_type": "StaleQuoteException",
                "sensor_type": "quote_freshness",
                "affected_services": ["market-data-feed", "risk-calculator"],
                "cascade_services": ["matching-engine", "customer-portal"],
                "description": "Cached market quotes exceeding staleness threshold affecting pricing",
                "error_message": "Stale quote detected: {symbol} last update {stale_ms}ms ago, threshold {quote_max_age_ms}ms, source {data_source}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "market_data/quote_cache.go", line 456, in getQuote\n'
                    "    age := time.Since(entry.UpdatedAt)\n"
                    '  File "market_data/quote_cache.go", line 462, in getQuote\n'
                    '    if age.Milliseconds() > maxAge {\n'
                    '  File "market_data/quote_cache.go", line 467, in getQuote\n'
                    '    return Quote{}, StaleQuoteException{Symbol: symbol, AgeMs: age.Milliseconds()}\n'
                    "StaleQuoteException: {symbol} quote stale {stale_ms}ms from {data_source}"
                ),
            },
            19: {
                "name": "FIX Protocol Parse Error",
                "subsystem": "order_management",
                "vehicle_section": "fix_gateway",
                "error_type": "FIXParseException",
                "sensor_type": "protocol_parser",
                "affected_services": ["order-gateway", "audit-logger"],
                "cascade_services": ["matching-engine", "compliance-monitor"],
                "description": "FIX 4.4 message parsing failure due to malformed tags or checksum errors",
                "error_message": "FIX parse error: session {fix_session} message type {msg_type} tag {bad_tag} invalid, checksum expected {expected_checksum} got {actual_checksum}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "order_management/fix_gateway.java", line 567, in parseMessage\n'
                    "    FixMessage msg = parser.parse(rawBytes);\n"
                    '  File "order_management/fix_parser.java", line 234, in parse\n'
                    "    validateChecksum(msg, rawBytes);\n"
                    '  File "order_management/fix_parser.java", line 198, in validateChecksum\n'
                    '    throw new FIXParseException("Tag " + tag + " invalid in " + msgType + " message");\n'
                    "FIXParseException: Session {fix_session} msg {msg_type} tag {bad_tag} parse failure"
                ),
            },
            20: {
                "name": "Dark Pool Routing Failure",
                "subsystem": "trade_execution",
                "vehicle_section": "smart_router",
                "error_type": "DarkPoolException",
                "sensor_type": "routing_engine",
                "affected_services": ["matching-engine", "order-gateway"],
                "cascade_services": ["risk-calculator", "audit-logger", "compliance-monitor"],
                "description": "Smart order router fails to route block orders to dark pool venues",
                "error_message": "Dark pool routing failure: order {order_id} for {symbol} qty {quantity} rejected by venue {venue}, reason {rejection_reason}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "trade_execution/smart_router.cpp", line 892, in routeOrder\n'
                    "    auto venue_response = dark_pool_client.submit(order);\n"
                    '  File "trade_execution/smart_router.cpp", line 898, in routeOrder\n'
                    '    if (!venue_response.accepted()) throw DarkPoolException(order.id(), venue.name());\n'
                    '  File "trade_execution/venue_client.cpp", line 345, in submit\n'
                    '    throw DarkPoolException("Order " + orderId + " rejected by " + venue + ": " + reason);\n'
                    "DarkPoolException: Order {order_id} for {symbol} rejected by {venue}: {rejection_reason}"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "order-gateway": [
                ("matching-engine", "/api/v1/orders/submit", "POST"),
                ("matching-engine", "/api/v1/orders/cancel", "DELETE"),
                ("risk-calculator", "/api/v1/risk/pre-trade-check", "POST"),
                ("fraud-detector", "/api/v1/fraud/screen-order", "POST"),
                ("audit-logger", "/api/v1/audit/log-order", "POST"),
            ],
            "matching-engine": [
                ("risk-calculator", "/api/v1/risk/position-update", "POST"),
                ("settlement-processor", "/api/v1/settlement/initiate", "POST"),
                ("market-data-feed", "/api/v1/market/last-price", "GET"),
            ],
            "risk-calculator": [
                ("market-data-feed", "/api/v1/market/quotes", "GET"),
                ("settlement-processor", "/api/v1/settlement/margin-status", "GET"),
            ],
            "settlement-processor": [
                ("audit-logger", "/api/v1/audit/log-settlement", "POST"),
                ("compliance-monitor", "/api/v1/compliance/settlement-report", "POST"),
            ],
            "customer-portal": [
                ("order-gateway", "/api/v1/orders/place", "POST"),
                ("risk-calculator", "/api/v1/risk/portfolio-exposure", "GET"),
                ("market-data-feed", "/api/v1/market/stream", "GET"),
            ],
            "compliance-monitor": [
                ("audit-logger", "/api/v1/audit/compliance-event", "POST"),
                ("fraud-detector", "/api/v1/fraud/alert-status", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "order-gateway": [
                ("/api/v1/orders/new", "POST"),
                ("/api/v1/orders/status", "GET"),
                ("/api/v1/orders/amend", "PUT"),
            ],
            "matching-engine": [("/api/v1/engine/health", "GET")],
            "risk-calculator": [
                ("/api/v1/risk/evaluate", "POST"),
                ("/api/v1/risk/limits", "GET"),
            ],
            "market-data-feed": [
                ("/api/v1/market/subscribe", "POST"),
                ("/api/v1/market/snapshot", "GET"),
            ],
            "settlement-processor": [("/api/v1/settlement/status", "GET")],
            "fraud-detector": [("/api/v1/fraud/analyze", "POST")],
            "compliance-monitor": [
                ("/api/v1/compliance/report", "GET"),
                ("/api/v1/compliance/alerts", "GET"),
            ],
            "customer-portal": [
                ("/api/v1/portfolio/overview", "GET"),
                ("/api/v1/portfolio/positions", "GET"),
                ("/api/v1/portfolio/pnl", "GET"),
            ],
            "audit-logger": [("/api/v1/audit/query", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "order-gateway": [
                ("INSERT", "orders", "INSERT INTO orders (order_id, instrument, side, qty, price, status, ts) VALUES (?, ?, ?, ?, ?, 'NEW', NOW())"),
                ("SELECT", "orders", "SELECT order_id, status, filled_qty FROM orders WHERE account_id = ? AND status IN ('NEW', 'PARTIAL') ORDER BY ts DESC LIMIT 50"),
            ],
            "matching-engine": [
                ("UPDATE", "order_book", "UPDATE order_book SET best_bid = ?, best_ask = ?, last_match_ts = NOW() WHERE instrument = ?"),
                ("INSERT", "trades", "INSERT INTO trades (trade_id, instrument, buy_order, sell_order, qty, price, ts) VALUES (?, ?, ?, ?, ?, ?, NOW())"),
            ],
            "risk-calculator": [
                ("SELECT", "positions", "SELECT instrument, net_qty, avg_price, unrealized_pnl FROM positions WHERE desk_id = ? AND asset_class = ?"),
                ("UPDATE", "risk_limits", "UPDATE risk_limits SET current_exposure = ?, last_checked = NOW() WHERE desk_id = ? AND limit_type = ?"),
            ],
            "settlement-processor": [
                ("SELECT", "settlements", "SELECT settlement_id, trade_id, status, due_date FROM settlements WHERE status = 'PENDING' AND due_date < NOW() + INTERVAL 1 DAY"),
                ("UPDATE", "settlements", "UPDATE settlements SET status = ?, settled_at = NOW() WHERE settlement_id = ?"),
            ],
            "audit-logger": [
                ("INSERT", "audit_events", "INSERT INTO audit_events (event_id, event_type, actor, payload, seq_num, ts) VALUES (?, ?, ?, ?, ?, NOW())"),
                ("SELECT", "audit_events", "SELECT event_id, event_type, payload FROM audit_events WHERE stream_id = ? AND seq_num > ? ORDER BY seq_num ASC LIMIT 100"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "finserv-aws-host-01",
                "host.id": "i-0f1a2b3c4d5e67890",
                "host.arch": "amd64",
                "host.type": "c5.2xlarge",
                "host.image.id": "ami-0fedcba9876543210",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8275CL CPU @ 3.00GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.2.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "987654321098",
                "cloud.instance.id": "i-0f1a2b3c4d5e67890",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "finserv-gcp-host-01",
                "host.id": "7823456789012345678",
                "host.arch": "amd64",
                "host.type": "c2-standard-8",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 3.10GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.1.20", "10.128.1.21"],
                "host.mac": ["42:01:0a:80:01:14", "42:01:0a:80:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "finserv-trading-prod",
                "cloud.instance.id": "7823456789012345678",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "finserv-azure-host-01",
                "host.id": "/subscriptions/def-456/resourceGroups/finserv-rg/providers/Microsoft.Compute/virtualMachines/finserv-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_F8s_v2",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.10", "10.2.0.11"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "def-456-ghi-789",
                "cloud.instance.id": "finserv-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "finserv-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["order-gateway", "matching-engine", "risk-calculator"],
            },
            {
                "name": "finserv-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["market-data-feed", "settlement-processor", "fraud-detector"],
            },
            {
                "name": "finserv-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["compliance-monitor", "customer-portal", "audit-logger"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0a1628",
            bg_secondary="#0f1d32",
            bg_tertiary="#162240",
            accent_primary="#ffa500",
            accent_secondary="#ff6600",
            text_primary="#ff8c00",
            text_secondary="#cc7000",
            text_accent="#ffa500",
            status_nominal="#00ff00",
            status_warning="#ffa500",
            status_critical="#ff0000",
            font_family="'Bloomberg Terminal', 'Consolas', monospace",
            font_mono="'Bloomberg Terminal', 'Consolas', monospace",
            dashboard_title="Trading Operations Center",
            chaos_title="Market Disruption Simulator",
            landing_title="Trading Operations Center",
            service_label="Service",
            channel_label="Channel",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "finserv-trading-analyst",
            "name": "Trading Operations Analyst",
            "assessment_tool_name": "trading_risk_assessment",
            "system_prompt": (
                "You are the Trading Operations Analyst, an expert AI assistant for "
                "financial trading platform operations. You specialize in FIX protocol "
                "analysis, order management systems, matching engine diagnostics, risk "
                "limit monitoring, settlement processing, and regulatory compliance. "
                "You help trading desk operators investigate anomalies, analyze order "
                "flow, diagnose latency issues, and provide root cause analysis for "
                "fault conditions across 9 trading infrastructure services."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "trading_risk_assessment",
            "description": (
                "Comprehensive pre-market trading risk assessment. Evaluates all "
                "services against operational readiness criteria for trading sessions. "
                "Returns data for risk evaluation across order management, matching "
                "engine, settlement, and compliance systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.financial.services.order_gateway import OrderGatewayService
        from scenarios.financial.services.matching_engine import MatchingEngineService
        from scenarios.financial.services.risk_calculator import RiskCalculatorService
        from scenarios.financial.services.market_data_feed import MarketDataFeedService
        from scenarios.financial.services.settlement_processor import SettlementProcessorService
        from scenarios.financial.services.fraud_detector import FraudDetectorService
        from scenarios.financial.services.compliance_monitor import ComplianceMonitorService
        from scenarios.financial.services.customer_portal import CustomerPortalService
        from scenarios.financial.services.audit_logger import AuditLoggerService

        return [
            OrderGatewayService,
            MatchingEngineService,
            RiskCalculatorService,
            MarketDataFeedService,
            SettlementProcessorService,
            FraudDetectorService,
            ComplianceMonitorService,
            CustomerPortalService,
            AuditLoggerService,
        ]

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "JPM", "GS", "MS", "BAC", "C"]
        instruments = ["US.AAPL", "US.GOOGL", "US.MSFT", "US.AMZN", "US.TSLA", "FX.EURUSD", "FX.GBPUSD", "FUT.ES", "FUT.NQ", "OPT.SPX"]
        exchanges = ["NYSE", "NASDAQ", "CBOE", "CME", "ICE", "BATS", "IEX"]
        venues = ["SIGMA-X", "CROSSFINDER", "SUPERX", "POSIT", "LIQUIDNET", "INSTINET"]
        counterparties = ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citadel Securities", "Virtu Financial", "Jane Street"]
        currencies = ["USD", "EUR", "GBP", "JPY", "CHF"]
        asset_classes = ["equity", "fixed_income", "fx", "derivatives", "commodities"]
        jurisdictions = ["US-SEC", "US-CFTC", "UK-FCA", "EU-ESMA", "SG-MAS", "JP-FSA"]
        report_types = ["EMIR-TR", "MiFID-II-RTS25", "CAT-FINRA", "SFTR", "SEC-13F", "TRF-TRACE"]
        failure_reasons = ["insufficient_securities", "funding_shortfall", "counterparty_default", "DTCC_rejection", "SSI_mismatch"]
        rejection_reasons = ["minimum_size_not_met", "price_outside_band", "venue_capacity", "symbol_restricted", "IOI_expired"]

        return {
            # Order/trade identifiers
            "order_id": f"ORD-{random.randint(100000, 999999)}",
            "trade_id": f"TRD-{random.randint(100000, 999999)}",
            "settlement_id": f"STL-{random.randint(100000, 999999)}",
            "batch_id": f"NET-{random.randint(1000, 9999)}",
            "transaction_id": f"TXN-{random.randint(100000, 999999)}",
            "book_id": f"BOOK-{random.choice(['EQ', 'FI', 'FX', 'DRV'])}-{random.randint(1, 50):02d}",
            # Instruments and symbols
            "symbol": random.choice(symbols),
            "instrument": random.choice(instruments),
            "exchange": random.choice(exchanges),
            "venue": random.choice(venues),
            # Pricing and quantity
            "price": round(random.uniform(50.0, 500.0), 2),
            "quantity": random.randint(100, 50000),
            "spread": random.randint(5, 50),
            "max_spread": 3,
            # Latency (microseconds for HFT)
            "latency_us": random.randint(500, 50000),
            "sla_us": 200,
            "partition_id": f"P-{random.randint(0, 15)}",
            # Market data
            "gap_ms": random.randint(500, 10000),
            "seq_start": random.randint(1000000, 9999999),
            "seq_end": random.randint(1000000, 9999999),
            "stale_ms": random.randint(5000, 60000),
            "quote_max_age_ms": 3000,
            "data_source": random.choice(["Bloomberg-B-PIPE", "Reuters-Elektron", "CQS-SIP", "OPRA", "CME-MDP3"]),
            # Risk parameters
            "desk_id": f"DESK-{random.choice(['EQ-FLOW', 'EQ-PROP', 'FI-RATES', 'FX-SPOT', 'DRV-VOL'])}",
            "exposure": f"{random.randint(10, 500)}M",
            "risk_limit": f"{random.randint(5, 100)}M",
            "asset_class": random.choice(asset_classes),
            # Margin
            "account_id": f"ACC-{random.randint(10000, 99999)}",
            "margin_ratio": round(random.uniform(0.05, 0.20), 3),
            "maintenance_ratio": 0.25,
            "valuation_age_s": random.randint(300, 3600),
            # Position reconciliation
            "realtime_qty": random.randint(1000, 100000),
            "eod_qty": random.randint(1000, 100000),
            "position_delta": random.randint(1, 5000),
            # Settlement
            "counterparty": random.choice(counterparties),
            "pending_hours": round(random.uniform(48.5, 96.0), 1),
            "sla_hours": 48,
            "failure_reason": random.choice(failure_reasons),
            "currency": random.choice(currencies),
            "net_mismatch": round(random.uniform(10000, 5000000), 2),
            "counterparty_count": random.randint(3, 20),
            # Compliance / fraud
            "blocked_orders": random.randint(50, 500),
            "window_s": random.randint(30, 300),
            "fp_rate": round(random.uniform(15.0, 85.0), 1),
            "pattern_id": f"FRD-{random.choice(['VELOCITY', 'GEOLOC', 'AMOUNT', 'PATTERN', 'WASH'])}-{random.randint(1, 99):02d}",
            "report_type": random.choice(report_types),
            "report_period": f"2026-Q{random.randint(1, 4)}",
            "stage": random.choice(["data_collection", "validation", "aggregation", "formatting", "submission"]),
            "deadline_utc": "2026-02-16T23:59:00Z",
            "screening_ms": random.randint(5000, 30000),
            "aml_sla_ms": 3000,
            "jurisdiction": random.choice(jurisdictions),
            # Client services
            "session_id": f"SESS-{random.randint(100000, 999999)}",
            "user_id": f"USR-{random.randint(10000, 99999)}",
            "session_age_s": random.randint(1800, 7200),
            "operation": random.choice(["order_submit", "portfolio_view", "position_close", "margin_check"]),
            "pending_orders": random.randint(1, 10),
            "portfolio_id": f"PF-{random.randint(10000, 99999)}",
            "lag_s": round(random.uniform(30.0, 300.0), 1),
            "max_lag_s": 15.0,
            "position_count": random.randint(50, 500),
            "delay_s": round(random.uniform(600, 7200), 1),
            "reg_max_s": 300,
            # Audit
            "audit_stream": random.choice(["orders", "trades", "settlements", "risk-events", "compliance-alerts"]),
            "expected_seq": random.randint(1000000, 9999999),
            "last_seq": random.randint(1000000, 9999999),
            "gap_count": random.randint(1, 100),
            # Replication
            "source_region": random.choice(["us-east-1", "us-central1", "eastus"]),
            "dest_region": random.choice(["eu-west-1", "us-west-2", "westus"]),
            "lag_ms": random.randint(5000, 60000),
            "max_lag_ms": 3000,
            "pending_events": random.randint(100, 10000),
            # FIX protocol
            "fix_session": f"FIX-{random.choice(['NYSE', 'NSDQ', 'CBOE', 'CME'])}-{random.randint(1, 20):02d}",
            "msg_type": random.choice(["D", "G", "F", "8", "9"]),
            "bad_tag": random.choice([35, 49, 56, 11, 55, 44, 38, 54, 40]),
            "expected_checksum": f"{random.randint(0, 255):03d}",
            "actual_checksum": f"{random.randint(0, 255):03d}",
            # Dark pool
            "rejection_reason": random.choice(rejection_reasons),
        }


# Module-level instance for registry discovery
scenario = FinancialScenario()
