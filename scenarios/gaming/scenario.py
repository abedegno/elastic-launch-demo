"""Live Gaming Platform scenario — multiplayer gaming infrastructure with live-ops chaos engineering."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class GamingScenario(BaseScenario):
    """Live multiplayer gaming platform with 9 game services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "gaming"

    @property
    def scenario_name(self) -> str:
        return "Live Gaming Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Live multiplayer gaming platform with game servers, matchmaking, "
            "content delivery, chat, leaderboards, authentication, payments, "
            "analytics, and content moderation. Cyberpunk neon command center."
        )

    @property
    def namespace(self) -> str:
        return "gaming"

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "game-server": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "game_engine",
                "language": "cpp",
            },
            "matchmaking-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "matchmaking",
                "language": "go",
            },
            "content-delivery": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "cdn",
                "language": "rust",
            },
            "chat-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "social",
                "language": "java",
            },
            "leaderboard-api": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "progression",
                "language": "go",
            },
            "auth-gateway": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "identity",
                "language": "python",
            },
            "payment-processor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "monetization",
                "language": "dotnet",
            },
            "analytics-pipeline": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "analytics",
                "language": "python",
            },
            "moderation-engine": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "trust_safety",
                "language": "java",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Game State Desync",
                "subsystem": "game_engine",
                "vehicle_section": "game_loop",
                "error_type": "StateDesyncException",
                "sensor_type": "state_validator",
                "affected_services": ["game-server", "matchmaking-engine"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Game state diverges between server authoritative state and client prediction, causing rubber-banding and rollback cascades",
                "error_message": "Game state desync detected: player {player_id} position delta {position_delta}m exceeds sync threshold 0.5m in match {match_id} at tick {tick_number}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "game_engine/state_manager.cpp", line 847, in ValidateClientState\n'
                    "    auto delta = ComputePositionDelta(server_state, client_state);\n"
                    '  File "game_engine/state_manager.cpp", line 812, in ComputePositionDelta\n'
                    "    throw StateDesyncException(delta, player_id, tick);\n"
                    '  File "game_engine/reconciler.cpp", line 234, in ForceReconcile\n'
                    '    LOG_ERROR("Forcing state reconciliation for player {player_id}");\n'
                    "StateDesyncException: State desync {position_delta}m for player {player_id} in match {match_id}"
                ),
            },
            2: {
                "name": "Physics Simulation Overflow",
                "subsystem": "game_engine",
                "vehicle_section": "physics_engine",
                "error_type": "PhysicsOverflowException",
                "sensor_type": "physics_validator",
                "affected_services": ["game-server", "analytics-pipeline"],
                "cascade_services": ["matchmaking-engine"],
                "description": "Physics simulation accumulates floating-point errors causing object positions to overflow into NaN territory",
                "error_message": "Physics simulation overflow: entity {entity_id} velocity {velocity} exceeds max {max_velocity} in zone {zone_id}, simulation tick {tick_number}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "game_engine/physics/rigid_body.cpp", line 512, in IntegrateForces\n'
                    "    velocity += acceleration * delta_time;\n"
                    '  File "game_engine/physics/collision_solver.cpp", line 378, in ResolveOverlap\n'
                    "    auto impulse = ComputeSeparationImpulse(body_a, body_b);\n"
                    '  File "game_engine/physics/validator.cpp", line 89, in CheckBounds\n'
                    '    throw PhysicsOverflowException("Velocity overflow on entity " + entity_id);\n'
                    "PhysicsOverflowException: Entity {entity_id} velocity {velocity} exceeds simulation bounds"
                ),
            },
            3: {
                "name": "Matchmaking Queue Overflow",
                "subsystem": "matchmaking",
                "vehicle_section": "matchmaker_core",
                "error_type": "MatchmakingOverflowException",
                "sensor_type": "queue_monitor",
                "affected_services": ["matchmaking-engine", "game-server"],
                "cascade_services": ["auth-gateway", "analytics-pipeline"],
                "description": "Matchmaking queue depth exceeds capacity causing player wait times to spike beyond acceptable thresholds",
                "error_message": "Matchmaking queue overflow: queue {queue_name} depth {queue_depth} exceeds capacity {max_capacity}, avg wait time {wait_time_ms}ms, region {region}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "matchmaking/queue_manager.go", line 234, in EnqueuePlayer\n'
                    "    if q.Depth() > q.MaxCapacity {\n"
                    '  File "matchmaking/queue_manager.go", line 198, in checkCapacity\n'
                    "    return fmt.Errorf(\"queue overflow: %d > %d\", depth, max)\n"
                    '  File "matchmaking/dispatcher.go", line 156, in Dispatch\n'
                    "    return nil, MatchmakingOverflowException{Queue: name, Depth: depth}\n"
                    "MatchmakingOverflowException: Queue {queue_name} depth {queue_depth} exceeds max {max_capacity}"
                ),
            },
            4: {
                "name": "Skill Rating Calculation Error",
                "subsystem": "matchmaking",
                "vehicle_section": "rating_engine",
                "error_type": "SkillRatingException",
                "sensor_type": "rating_validator",
                "affected_services": ["matchmaking-engine", "leaderboard-api"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Skill rating calculation produces invalid MMR values due to edge cases in the Elo/Glicko algorithm implementation",
                "error_message": "Skill rating calculation error: player {player_id} MMR {mmr_value} outside valid range [0, {max_mmr}], volatility {volatility}, match {match_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "matchmaking/rating/glicko2.go", line 189, in CalculateNewRating\n'
                    "    newRating := oldRating + k * (actual - expected)\n"
                    '  File "matchmaking/rating/glicko2.go", line 167, in validateRating\n'
                    "    if rating < 0 || rating > MaxMMR {\n"
                    '  File "matchmaking/rating/validator.go", line 78, in Validate\n'
                    "    return SkillRatingException{Player: pid, Rating: rating}\n"
                    "SkillRatingException: Player {player_id} MMR {mmr_value} invalid (volatility: {volatility})"
                ),
            },
            5: {
                "name": "CDN Cache Miss Storm",
                "subsystem": "cdn",
                "vehicle_section": "cdn_edge",
                "error_type": "CacheMissStormException",
                "sensor_type": "cache_monitor",
                "affected_services": ["content-delivery", "game-server"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Cascading cache misses overwhelm origin servers as hot content expires simultaneously across edge nodes",
                "error_message": "CDN cache miss storm: edge {edge_node} cache hit rate dropped to {cache_hit_rate}% (threshold 85%), origin load {origin_load_pct}%, asset_group {asset_group}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "cdn/edge_cache.rs", line 456, in serve_asset\n'
                    "    let entry = self.cache.get(&asset_key)?;\n"
                    '  File "cdn/edge_cache.rs", line 423, in fetch_from_origin\n'
                    "    if self.origin_circuit_breaker.is_open() {\n"
                    '  File "cdn/storm_detector.rs", line 112, in check_miss_rate\n'
                    '    return Err(CacheMissStormException::new(hit_rate, edge_id));\n'
                    "CacheMissStormException: Cache hit rate {cache_hit_rate}% on edge {edge_node}, origin overloaded at {origin_load_pct}%"
                ),
            },
            6: {
                "name": "Asset Bundle Corruption",
                "subsystem": "cdn",
                "vehicle_section": "asset_pipeline",
                "error_type": "AssetCorruptionException",
                "sensor_type": "integrity_checker",
                "affected_services": ["content-delivery", "game-server"],
                "cascade_services": ["moderation-engine"],
                "description": "Game asset bundles fail integrity verification after CDN transfer, causing client crashes on load",
                "error_message": "Asset bundle corruption: bundle {bundle_id} checksum mismatch (expected {expected_hash}, got {actual_hash}), size {bundle_size_mb}MB, version {bundle_version}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "cdn/asset_manager.rs", line 334, in verify_bundle\n'
                    "    let computed = sha256::digest(&data);\n"
                    '  File "cdn/asset_manager.rs", line 312, in compare_checksums\n'
                    "    if computed != expected {\n"
                    '  File "cdn/integrity.rs", line 78, in report_corruption\n'
                    '    return Err(AssetCorruptionException::new(bundle_id, expected, actual));\n'
                    "AssetCorruptionException: Bundle {bundle_id} integrity check failed — checksum mismatch"
                ),
            },
            7: {
                "name": "Chat Message Flood",
                "subsystem": "social",
                "vehicle_section": "chat_gateway",
                "error_type": "ChatFloodException",
                "sensor_type": "rate_limiter",
                "affected_services": ["chat-service", "moderation-engine"],
                "cascade_services": ["auth-gateway"],
                "description": "Chat channels experiencing message floods that overwhelm rate limiters and moderation pipelines",
                "error_message": "Chat message flood: channel {channel_id} message rate {message_rate}/s exceeds limit {rate_limit}/s, {pending_moderation} messages pending moderation",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "social/chat/MessageRouter.java", line 289, in routeMessage\n'
                    "    rateLimiter.acquire(channelId);\n"
                    '  File "social/chat/RateLimiter.java", line 145, in acquire\n'
                    "    if (currentRate > maxRate) {\n"
                    '  File "social/chat/FloodDetector.java", line 67, in onFloodDetected\n'
                    '    throw new ChatFloodException("Channel " + channelId + " rate " + rate);\n'
                    "ChatFloodException: Channel {channel_id} message rate {message_rate}/s exceeds limit"
                ),
            },
            8: {
                "name": "Voice Channel Degradation",
                "subsystem": "social",
                "vehicle_section": "voice_server",
                "error_type": "VoiceChannelException",
                "sensor_type": "audio_quality_monitor",
                "affected_services": ["chat-service", "game-server"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Voice chat channels experiencing audio quality degradation with packet loss, jitter, and codec failures",
                "error_message": "Voice channel degradation: channel {voice_channel_id} packet loss {voice_packet_loss_pct}%, jitter {jitter_ms}ms, {active_speakers} active speakers, codec {codec}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "social/voice/VoiceRouter.java", line 378, in processAudioFrame\n'
                    "    qualityMetrics = analyzeStream(channelId, frame);\n"
                    '  File "social/voice/QualityAnalyzer.java", line 212, in analyzeStream\n'
                    "    if (packetLoss > DEGRADATION_THRESHOLD) {\n"
                    '  File "social/voice/QualityAnalyzer.java", line 198, in reportDegradation\n'
                    '    throw new VoiceChannelException("Quality below threshold on " + channelId);\n'
                    "VoiceChannelException: Voice channel {voice_channel_id} quality degraded — {voice_packet_loss_pct}% packet loss"
                ),
            },
            9: {
                "name": "Leaderboard Corruption",
                "subsystem": "progression",
                "vehicle_section": "leaderboard_core",
                "error_type": "LeaderboardCorruptException",
                "sensor_type": "consistency_checker",
                "affected_services": ["leaderboard-api", "game-server"],
                "cascade_services": ["analytics-pipeline", "moderation-engine"],
                "description": "Leaderboard sorted set becomes inconsistent due to concurrent score updates causing rank calculation errors",
                "error_message": "Leaderboard corruption: board {leaderboard_id} inconsistency detected — {corrupt_entries} entries with invalid rank ordering, season {season_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "progression/leaderboard/RankManager.go", line 267, in UpdateRank\n'
                    "    newRank := board.ComputeRank(playerId, newScore)\n"
                    '  File "progression/leaderboard/ConsistencyChecker.go", line 134, in Verify\n'
                    "    if prev.Score < curr.Score && prev.Rank < curr.Rank {\n"
                    '  File "progression/leaderboard/ConsistencyChecker.go", line 142, in reportCorruption\n'
                    "    return LeaderboardCorruptException{Board: id, Entries: count}\n"
                    "LeaderboardCorruptException: Board {leaderboard_id} has {corrupt_entries} inconsistent entries"
                ),
            },
            10: {
                "name": "Season Pass Progression Sync Error",
                "subsystem": "progression",
                "vehicle_section": "progression_tracker",
                "error_type": "SeasonPassSyncException",
                "sensor_type": "sync_validator",
                "affected_services": ["leaderboard-api", "payment-processor"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Season pass XP and tier progression fails to synchronize between game server events and the progression backend",
                "error_message": "Season pass sync error: player {player_id} tier {current_tier} but XP {xp_total} qualifies for tier {expected_tier}, season {season_id}, delta {xp_delta}XP",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "progression/season/PassManager.go", line 189, in SyncProgression\n'
                    "    expectedTier := computeTier(player.XP, seasonConfig)\n"
                    '  File "progression/season/PassManager.go", line 167, in computeTier\n'
                    "    if actualTier != expectedTier {\n"
                    '  File "progression/season/SyncValidator.go", line 78, in Validate\n'
                    "    return SeasonPassSyncException{Player: pid, Actual: actual, Expected: expected}\n"
                    "SeasonPassSyncException: Player {player_id} tier mismatch — at {current_tier}, should be {expected_tier}"
                ),
            },
            11: {
                "name": "OAuth Token Refresh Storm",
                "subsystem": "identity",
                "vehicle_section": "auth_core",
                "error_type": "TokenRefreshStormException",
                "sensor_type": "token_monitor",
                "affected_services": ["auth-gateway", "game-server"],
                "cascade_services": ["matchmaking-engine", "chat-service"],
                "description": "Mass token refresh requests overwhelm the auth service when tokens expire simultaneously due to clock sync issues",
                "error_message": "OAuth token refresh storm: {refresh_rate}/s refresh requests (capacity {max_refresh_rate}/s), {failed_refreshes} failures, token_pool {token_pool_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "identity/token_service.py", line 289, in refresh_token\n'
                    "    new_token = self._issue_token(claims, ttl)\n"
                    '  File "identity/token_service.py", line 256, in _issue_token\n'
                    "    if self.rate_limiter.is_exceeded():\n"
                    '  File "identity/storm_detector.py", line 112, in check_refresh_rate\n'
                    '    raise TokenRefreshStormException(f"Refresh rate {rate}/s exceeds {max_rate}/s")\n'
                    "TokenRefreshStormException: Token refresh rate {refresh_rate}/s exceeds capacity {max_refresh_rate}/s"
                ),
            },
            12: {
                "name": "Account Takeover Detection Spike",
                "subsystem": "identity",
                "vehicle_section": "fraud_detector",
                "error_type": "AccountTakeoverException",
                "sensor_type": "anomaly_detector",
                "affected_services": ["auth-gateway", "payment-processor"],
                "cascade_services": ["moderation-engine", "analytics-pipeline"],
                "description": "Anomaly detection system flags a surge in credential stuffing attempts indicating a coordinated account takeover campaign",
                "error_message": "Account takeover spike: {ato_attempts} suspicious login attempts in {window_seconds}s, {blocked_ips} IPs blocked, risk_score {risk_score}, geo_anomaly {geo_region}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "identity/fraud/ato_detector.py", line 378, in analyze_login_batch\n'
                    "    risk = self._compute_risk_score(attempts, window)\n"
                    '  File "identity/fraud/ato_detector.py", line 345, in _compute_risk_score\n'
                    "    if risk > self.CRITICAL_THRESHOLD:\n"
                    '  File "identity/fraud/alert_manager.py", line 89, in escalate\n'
                    '    raise AccountTakeoverException(f"ATO spike: {attempts} attempts, risk {risk}")\n'
                    "AccountTakeoverException: {ato_attempts} suspicious attempts detected from {blocked_ips} IPs, risk score {risk_score}"
                ),
            },
            13: {
                "name": "In-App Purchase Processing Failure",
                "subsystem": "monetization",
                "vehicle_section": "payment_gateway",
                "error_type": "PurchaseFailureException",
                "sensor_type": "transaction_monitor",
                "affected_services": ["payment-processor", "auth-gateway"],
                "cascade_services": ["analytics-pipeline"],
                "description": "In-app purchase transactions failing at the payment gateway level due to provider timeouts or validation errors",
                "error_message": "Purchase processing failure: transaction {purchase_id} for player {player_id} amount {amount}{currency} — provider {payment_provider} returned {error_code}, retry {retry_count}/{max_retries}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "monetization/PurchaseProcessor.cs", line 312, in ProcessPurchase\n'
                    "    var result = await _gateway.ChargeAsync(transaction);\n"
                    '  File "monetization/PaymentGateway.cs", line 234, in ChargeAsync\n'
                    "    if (result.StatusCode != 200)\n"
                    '  File "monetization/RetryHandler.cs", line 89, in OnFailure\n'
                    '    throw new PurchaseFailureException($"Transaction {txId} failed: {errorCode}");\n'
                    "PurchaseFailureException: Transaction {purchase_id} failed — provider {payment_provider} error {error_code}"
                ),
            },
            14: {
                "name": "Virtual Currency Ledger Inconsistency",
                "subsystem": "monetization",
                "vehicle_section": "ledger_service",
                "error_type": "LedgerInconsistencyException",
                "sensor_type": "ledger_auditor",
                "affected_services": ["payment-processor", "leaderboard-api"],
                "cascade_services": ["moderation-engine", "analytics-pipeline"],
                "description": "Virtual currency ledger double-entry balances fail reconciliation, indicating potential duplication or lost transactions",
                "error_message": "Ledger inconsistency: player {player_id} balance {currency_balance} {virtual_currency} but ledger sum {ledger_sum} {virtual_currency}, discrepancy {discrepancy}, last_txn {last_transaction_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "monetization/LedgerService.cs", line 267, in ReconcileBalance\n'
                    "    var ledgerTotal = _ledger.SumEntries(playerId);\n"
                    '  File "monetization/LedgerService.cs", line 245, in CompareBalances\n'
                    "    if (Math.Abs(cached - ledgerTotal) > TOLERANCE)\n"
                    '  File "monetization/AuditLogger.cs", line 112, in LogInconsistency\n'
                    '    throw new LedgerInconsistencyException($"Balance mismatch for {playerId}");\n'
                    "LedgerInconsistencyException: Player {player_id} balance {currency_balance} != ledger sum {ledger_sum}"
                ),
            },
            15: {
                "name": "Event Ingestion Pipeline Lag",
                "subsystem": "analytics",
                "vehicle_section": "ingestion_pipeline",
                "error_type": "EventIngestionLagException",
                "sensor_type": "pipeline_monitor",
                "affected_services": ["analytics-pipeline", "game-server"],
                "cascade_services": ["leaderboard-api"],
                "description": "Analytics event ingestion pipeline falls behind, causing data lag and stale dashboards for live-ops teams",
                "error_message": "Event ingestion lag: pipeline {pipeline_id} lag {lag_seconds}s (threshold {max_lag_seconds}s), backlog {backlog_count} events, throughput {throughput}/s vs expected {expected_throughput}/s",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "analytics/ingestion/pipeline.py", line 289, in process_batch\n'
                    "    lag = self._compute_consumer_lag(partition)\n"
                    '  File "analytics/ingestion/pipeline.py", line 267, in _compute_consumer_lag\n'
                    "    if lag > self.max_lag:\n"
                    '  File "analytics/ingestion/alerting.py", line 78, in on_lag_exceeded\n'
                    '    raise EventIngestionLagException(f"Pipeline {pid} lag {lag}s")\n'
                    "EventIngestionLagException: Pipeline {pipeline_id} lag {lag_seconds}s with {backlog_count} event backlog"
                ),
            },
            16: {
                "name": "Player Telemetry Buffer Overflow",
                "subsystem": "analytics",
                "vehicle_section": "telemetry_buffer",
                "error_type": "TelemetryOverflowException",
                "sensor_type": "buffer_monitor",
                "affected_services": ["analytics-pipeline", "game-server"],
                "cascade_services": ["matchmaking-engine"],
                "description": "Player telemetry ring buffer overflows causing event data loss for analytics and anti-cheat systems",
                "error_message": "Telemetry buffer overflow: buffer {buffer_id} at {buffer_usage_pct}% capacity ({buffer_size}/{max_buffer_size} events), dropped {dropped_events} events in last {window_seconds}s",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "analytics/telemetry/ring_buffer.py", line 198, in enqueue\n'
                    "    if self._tail == self._head:\n"
                    '  File "analytics/telemetry/ring_buffer.py", line 176, in _handle_overflow\n'
                    "    self._dropped += 1\n"
                    '  File "analytics/telemetry/monitor.py", line 89, in check_overflow\n'
                    '    raise TelemetryOverflowException(f"Buffer {bid} overflow — {dropped} events lost")\n'
                    "TelemetryOverflowException: Buffer {buffer_id} at {buffer_usage_pct}% — {dropped_events} events dropped"
                ),
            },
            17: {
                "name": "Auto-Moderation False Positive Storm",
                "subsystem": "trust_safety",
                "vehicle_section": "automod_engine",
                "error_type": "ModerationFalsePositiveException",
                "sensor_type": "accuracy_monitor",
                "affected_services": ["moderation-engine", "chat-service"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Automated content moderation system producing excessive false positives, silencing legitimate player communication",
                "error_message": "Auto-moderation false positive storm: {false_positive_count} false positives in {window_minutes}min (rate {fp_rate_pct}%), model {model_version}, affected_players {affected_players}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "trust_safety/AutoModEngine.java", line 345, in classifyContent\n'
                    "    var prediction = model.predict(content, context);\n"
                    '  File "trust_safety/AccuracyMonitor.java", line 189, in checkFalsePositiveRate\n'
                    "    if (fpRate > ALERT_THRESHOLD) {\n"
                    '  File "trust_safety/AccuracyMonitor.java", line 167, in onThresholdExceeded\n'
                    '    throw new ModerationFalsePositiveException("FP rate " + fpRate + "%");\n'
                    "ModerationFalsePositiveException: False positive rate {fp_rate_pct}% — {false_positive_count} legitimate messages flagged"
                ),
            },
            18: {
                "name": "Report Queue Overflow",
                "subsystem": "trust_safety",
                "vehicle_section": "report_processor",
                "error_type": "ReportQueueOverflowException",
                "sensor_type": "queue_monitor",
                "affected_services": ["moderation-engine", "chat-service"],
                "cascade_services": ["auth-gateway"],
                "description": "Player report queue exceeds processing capacity causing delays in abuse case resolution",
                "error_message": "Report queue overflow: queue depth {report_queue_depth}, processing rate {processing_rate}/min, backlog age {oldest_report_hours}h, category {report_category}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "trust_safety/ReportProcessor.java", line 278, in processReportBatch\n'
                    "    if (queue.size() > MAX_QUEUE_DEPTH) {\n"
                    '  File "trust_safety/ReportProcessor.java", line 256, in onOverflow\n'
                    "    escalate(queue.oldestEntry(), queue.size());\n"
                    '  File "trust_safety/QueueMonitor.java", line 89, in reportOverflow\n'
                    '    throw new ReportQueueOverflowException("Queue depth " + depth);\n'
                    "ReportQueueOverflowException: Report queue depth {report_queue_depth} — oldest report {oldest_report_hours}h old"
                ),
            },
            19: {
                "name": "Server Tick Rate Degradation",
                "subsystem": "game_engine",
                "vehicle_section": "game_loop",
                "error_type": "TickRateDegradationException",
                "sensor_type": "performance_monitor",
                "affected_services": ["game-server", "matchmaking-engine"],
                "cascade_services": ["analytics-pipeline", "chat-service"],
                "description": "Game server tick rate drops below target causing gameplay lag, hit registration failures, and desync cascades",
                "error_message": "Server tick rate degradation: server {server_id} tick rate {tick_rate}Hz (target {target_tick_rate}Hz), frame time {frame_time_ms}ms, {active_players} players, match {match_id}",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "game_engine/server_loop.cpp", line 134, in RunTick\n'
                    "    auto elapsed = clock::now() - tick_start;\n"
                    '  File "game_engine/server_loop.cpp", line 112, in CheckTickRate\n'
                    "    if (current_rate < target_rate * 0.8) {\n"
                    '  File "game_engine/performance_monitor.cpp", line 67, in ReportDegradation\n'
                    '    throw TickRateDegradationException(server_id, current_rate, target_rate);\n'
                    "TickRateDegradationException: Server {server_id} tick rate {tick_rate}Hz below target {target_tick_rate}Hz"
                ),
            },
            20: {
                "name": "Cross-Region Player Migration Failure",
                "subsystem": "matchmaking",
                "vehicle_section": "migration_controller",
                "error_type": "PlayerMigrationException",
                "sensor_type": "migration_monitor",
                "affected_services": ["matchmaking-engine", "auth-gateway"],
                "cascade_services": ["game-server", "leaderboard-api", "analytics-pipeline"],
                "description": "Player session migration between regional game server clusters fails during rebalancing or failover operations",
                "error_message": "Player migration failure: player {player_id} migration {source_region}->{target_region} failed at phase {migration_phase}, session {session_id}, latency {latency_ms}ms",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "matchmaking/migration/controller.go", line 312, in MigratePlayer\n'
                    "    state, err := sourceCluster.ExtractPlayerState(playerId)\n"
                    '  File "matchmaking/migration/controller.go", line 289, in transferState\n'
                    "    if err := targetCluster.InjectPlayerState(state); err != nil {\n"
                    '  File "matchmaking/migration/validator.go", line 78, in ValidateMigration\n'
                    "    return PlayerMigrationException{Player: pid, Phase: phase}\n"
                    "PlayerMigrationException: Player {player_id} migration failed at {migration_phase} — {source_region} to {target_region}"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "game-server": [
                ("matchmaking-engine", "/api/v1/matchmaking/assign", "POST"),
                ("chat-service", "/api/v1/chat/game-events", "POST"),
                ("leaderboard-api", "/api/v1/leaderboard/score", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/event", "POST"),
                ("content-delivery", "/api/v1/cdn/asset", "GET"),
                ("auth-gateway", "/api/v1/auth/validate-session", "POST"),
            ],
            "matchmaking-engine": [
                ("game-server", "/api/v1/server/allocate", "POST"),
                ("auth-gateway", "/api/v1/auth/player-profile", "GET"),
                ("leaderboard-api", "/api/v1/leaderboard/mmr", "GET"),
            ],
            "chat-service": [
                ("moderation-engine", "/api/v1/moderation/check", "POST"),
                ("auth-gateway", "/api/v1/auth/validate-token", "POST"),
            ],
            "leaderboard-api": [
                ("analytics-pipeline", "/api/v1/analytics/rank-change", "POST"),
            ],
            "payment-processor": [
                ("auth-gateway", "/api/v1/auth/verify-identity", "POST"),
                ("leaderboard-api", "/api/v1/leaderboard/unlock-reward", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/transaction", "POST"),
            ],
            "moderation-engine": [
                ("analytics-pipeline", "/api/v1/analytics/moderation-event", "POST"),
                ("auth-gateway", "/api/v1/auth/player-flags", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "game-server": [
                ("/api/v1/game/join", "POST"),
                ("/api/v1/game/state", "GET"),
                ("/api/v1/game/action", "POST"),
            ],
            "matchmaking-engine": [("/api/v1/matchmaking/queue", "POST")],
            "content-delivery": [("/api/v1/cdn/download", "GET")],
            "chat-service": [("/api/v1/chat/send", "POST")],
            "leaderboard-api": [("/api/v1/leaderboard/top", "GET")],
            "auth-gateway": [("/api/v1/auth/login", "POST")],
            "payment-processor": [("/api/v1/payment/purchase", "POST")],
            "analytics-pipeline": [("/api/v1/analytics/ingest", "POST")],
            "moderation-engine": [("/api/v1/moderation/report", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "game-server": [
                ("SELECT", "game_sessions", "SELECT * FROM game_sessions WHERE match_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 100"),
                ("INSERT", "game_events", "INSERT INTO game_events (match_id, player_id, event_type, payload, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "matchmaking-engine": [
                ("SELECT", "player_ratings", "SELECT player_id, mmr, volatility, games_played FROM player_ratings WHERE player_id = ? AND season = ?"),
                ("UPDATE", "player_ratings", "UPDATE player_ratings SET mmr = ?, volatility = ?, games_played = games_played + 1 WHERE player_id = ? AND season = ?"),
            ],
            "leaderboard-api": [
                ("SELECT", "leaderboards", "SELECT rank, player_id, score FROM leaderboards WHERE board_id = ? ORDER BY score DESC LIMIT 100"),
                ("INSERT", "rank_history", "INSERT INTO rank_history (player_id, board_id, old_rank, new_rank, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "auth-gateway": [
                ("SELECT", "player_sessions", "SELECT session_id, player_id, token_expires_at FROM player_sessions WHERE token = ? AND expires_at > NOW()"),
            ],
            "payment-processor": [
                ("SELECT", "transactions", "SELECT txn_id, player_id, amount, currency, status FROM transactions WHERE player_id = ? AND created_at > NOW() - INTERVAL 24 HOUR"),
                ("INSERT", "transactions", "INSERT INTO transactions (txn_id, player_id, amount, currency, item_id, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', NOW())"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "gaming-aws-host-01",
                "host.id": "i-0g4m1ng5e7v8r9012",
                "host.arch": "amd64",
                "host.type": "c5.2xlarge",
                "host.image.id": "ami-0gaming1234567890",
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
                "cloud.account.id": "234567890123",
                "cloud.instance.id": "i-0g4m1ng5e7v8r9012",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gaming-gcp-host-01",
                "host.id": "7891234567890123456",
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
                "cloud.account.id": "gaming-platform-prod",
                "cloud.instance.id": "7891234567890123456",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gaming-azure-host-01",
                "host.id": "/subscriptions/ghi-jkl/resourceGroups/gaming-rg/providers/Microsoft.Compute/virtualMachines/gaming-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_F8s_v2",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.2.0.8", "10.2.0.9"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "ghi-jkl-mno-pqr",
                "cloud.instance.id": "gaming-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "gaming-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["game-server", "matchmaking-engine", "content-delivery"],
            },
            {
                "name": "gaming-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["chat-service", "leaderboard-api", "auth-gateway"],
            },
            {
                "name": "gaming-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["payment-processor", "analytics-pipeline", "moderation-engine"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#13111c",
            bg_secondary="#1a1726",
            bg_tertiary="#221e30",
            accent_primary="#a855f7",
            accent_secondary="#ec4899",
            text_primary="#e2e8f0",
            text_secondary="#94a3b8",
            text_accent="#a855f7",
            status_nominal="#22c55e",
            status_warning="#eab308",
            status_critical="#ef4444",
            status_info="#58a6ff",
            font_family="'Inter', system-ui, sans-serif",
            glow_effect=True,
            gradient_accent="linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
            dashboard_title="Live Ops Command Center",
            chaos_title="Chaos Engineering Console",
            landing_title="Live Ops Command Center",
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
            "id": "gaming-liveops-analyst",
            "name": "Live Operations Analyst",
            "assessment_tool_name": "liveops_health_assessment",
            "system_prompt": (
                "You are the Live Operations Analyst, an expert AI assistant for "
                "live multiplayer gaming platform operations. You help live-ops engineers "
                "investigate incidents across game servers, matchmaking, CDN, chat, "
                "leaderboards, authentication, payments, analytics, and content moderation "
                "systems. You specialize in real-time system diagnostics, player impact "
                "assessment, and root cause analysis for fault conditions across 9 "
                "interconnected gaming services."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "liveops_health_assessment",
            "description": (
                "Comprehensive live service health assessment. Evaluates all "
                "gaming services against operational readiness criteria. Returns data "
                "for live-ops evaluation across game servers, matchmaking, CDN, "
                "authentication, and payment systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.gaming.services.game_server import GameServerService
        from scenarios.gaming.services.matchmaking_engine import MatchmakingEngineService
        from scenarios.gaming.services.content_delivery import ContentDeliveryService
        from scenarios.gaming.services.chat_service import ChatServiceService
        from scenarios.gaming.services.leaderboard_api import LeaderboardApiService
        from scenarios.gaming.services.auth_gateway import AuthGatewayService
        from scenarios.gaming.services.payment_processor import PaymentProcessorService
        from scenarios.gaming.services.analytics_pipeline import AnalyticsPipelineService
        from scenarios.gaming.services.moderation_engine import ModerationEngineService

        return [
            GameServerService,
            MatchmakingEngineService,
            ContentDeliveryService,
            ChatServiceService,
            LeaderboardApiService,
            AuthGatewayService,
            PaymentProcessorService,
            AnalyticsPipelineService,
            ModerationEngineService,
        ]

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            # Player/session identifiers
            "player_id": f"PLR-{random.randint(100000, 999999)}",
            "session_id": f"SESS-{random.randint(10000000, 99999999)}",
            "match_id": f"MATCH-{random.randint(100000, 999999)}",
            "server_id": f"GS-{random.choice(['US-E', 'US-W', 'EU-W', 'AP-SE'])}-{random.randint(1, 99):02d}",
            # Game state desync
            "position_delta": round(random.uniform(1.0, 25.0), 2),
            "tick_number": random.randint(100000, 9999999),
            # Physics
            "entity_id": f"ENT-{random.randint(10000, 99999)}",
            "velocity": round(random.uniform(1000.0, 999999.0), 1),
            "max_velocity": 500.0,
            "zone_id": random.choice(["ZONE-A1", "ZONE-B2", "ZONE-C3", "ZONE-D4"]),
            # Matchmaking
            "queue_name": random.choice(["ranked-solo", "ranked-duo", "casual-squad", "tournament-5v5"]),
            "queue_depth": random.randint(5000, 50000),
            "max_capacity": 3000,
            "wait_time_ms": random.randint(30000, 300000),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
            # Skill rating
            "mmr_value": random.randint(-500, 10000),
            "max_mmr": 5000,
            "volatility": round(random.uniform(0.01, 2.5), 3),
            # CDN
            "edge_node": random.choice(["edge-iad-01", "edge-lax-02", "edge-fra-01", "edge-nrt-01"]),
            "cache_hit_rate": round(random.uniform(20.0, 75.0), 1),
            "origin_load_pct": round(random.uniform(85.0, 100.0), 1),
            "asset_group": random.choice(["textures-hd", "models-characters", "audio-sfx", "maps-terrain"]),
            # Asset corruption
            "bundle_id": f"BDL-{random.randint(10000, 99999)}",
            "expected_hash": f"sha256:{random.randbytes(8).hex()}",
            "actual_hash": f"sha256:{random.randbytes(8).hex()}",
            "bundle_size_mb": round(random.uniform(50.0, 500.0), 1),
            "bundle_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            # Chat
            "channel_id": random.choice(["global-en", "guild-12345", "match-lobby", "trade-market"]),
            "message_rate": random.randint(500, 5000),
            "rate_limit": 200,
            "pending_moderation": random.randint(1000, 20000),
            # Voice
            "voice_channel_id": f"VC-{random.randint(10000, 99999)}",
            "voice_packet_loss_pct": round(random.uniform(5.0, 35.0), 1),
            "jitter_ms": round(random.uniform(20.0, 150.0), 1),
            "active_speakers": random.randint(2, 25),
            "codec": random.choice(["opus", "g711", "aac"]),
            # Leaderboard
            "leaderboard_id": random.choice(["ranked-global", "seasonal-solo", "guild-wars", "tournament-finals"]),
            "corrupt_entries": random.randint(10, 500),
            "season_id": f"S{random.randint(1, 12)}",
            # Season pass
            "current_tier": random.randint(1, 50),
            "expected_tier": random.randint(51, 100),
            "xp_total": random.randint(50000, 500000),
            "xp_delta": random.randint(1000, 50000),
            # Auth / tokens
            "refresh_rate": random.randint(5000, 50000),
            "max_refresh_rate": 2000,
            "failed_refreshes": random.randint(100, 5000),
            "token_pool_id": random.choice(["pool-primary", "pool-secondary", "pool-failover"]),
            # Account takeover
            "ato_attempts": random.randint(500, 10000),
            "window_seconds": random.randint(60, 300),
            "blocked_ips": random.randint(50, 500),
            "risk_score": round(random.uniform(0.85, 0.99), 2),
            "geo_region": random.choice(["Eastern Europe", "Southeast Asia", "South America", "Unknown VPN"]),
            # Payments
            "purchase_id": f"TXN-{random.randint(10000000, 99999999)}",
            "amount": round(random.uniform(0.99, 99.99), 2),
            "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
            "payment_provider": random.choice(["stripe", "paypal", "apple_iap", "google_play"]),
            "error_code": random.choice(["TIMEOUT", "DECLINED", "INSUFFICIENT_FUNDS", "FRAUD_HOLD", "PROVIDER_ERROR"]),
            "retry_count": random.randint(1, 5),
            "max_retries": 3,
            # Ledger
            "currency_balance": random.randint(100, 100000),
            "ledger_sum": random.randint(100, 100000),
            "discrepancy": random.randint(1, 5000),
            "virtual_currency": random.choice(["gems", "coins", "credits", "tokens"]),
            "last_transaction_id": f"LTXN-{random.randint(1000000, 9999999)}",
            # Analytics pipeline
            "pipeline_id": random.choice(["events-primary", "events-secondary", "replay-pipeline"]),
            "lag_seconds": round(random.uniform(30.0, 600.0), 1),
            "max_lag_seconds": 10.0,
            "backlog_count": random.randint(50000, 5000000),
            "throughput": random.randint(100, 2000),
            "expected_throughput": 5000,
            # Telemetry buffer
            "buffer_id": random.choice(["buf-player-events", "buf-game-state", "buf-combat-log"]),
            "buffer_usage_pct": round(random.uniform(95.0, 100.0), 1),
            "buffer_size": random.randint(90000, 100000),
            "max_buffer_size": 100000,
            "dropped_events": random.randint(100, 10000),
            "window_seconds_buf": random.randint(30, 300),
            # Moderation
            "false_positive_count": random.randint(100, 5000),
            "window_minutes": random.randint(5, 60),
            "fp_rate_pct": round(random.uniform(15.0, 45.0), 1),
            "model_version": f"automod-v{random.randint(3, 7)}.{random.randint(0, 9)}",
            "affected_players": random.randint(50, 2000),
            # Report queue
            "report_queue_depth": random.randint(5000, 50000),
            "processing_rate": round(random.uniform(5.0, 30.0), 1),
            "oldest_report_hours": round(random.uniform(4.0, 72.0), 1),
            "report_category": random.choice(["harassment", "cheating", "hate_speech", "exploits", "spam"]),
            # Tick rate
            "tick_rate": round(random.uniform(12.0, 45.0), 1),
            "target_tick_rate": 64,
            "frame_time_ms": round(random.uniform(22.0, 83.0), 1),
            "active_players": random.randint(10, 100),
            # Migration
            "source_region": random.choice(["us-east-1", "eu-west-1"]),
            "target_region": random.choice(["us-west-2", "ap-southeast-1"]),
            "migration_phase": random.choice(["state_extraction", "transfer", "injection", "validation"]),
            "latency_ms": random.randint(200, 5000),
        }


# Module-level instance for registry discovery
scenario = GamingScenario()
