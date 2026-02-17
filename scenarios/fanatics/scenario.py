"""Fanatics Collectibles scenario — enterprise infrastructure and network operations."""

from __future__ import annotations

import random
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme



class FanaticsScenario(BaseScenario):
    """Enterprise infrastructure and network operations for Fanatics Collectibles."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "fanatics"

    @property
    def scenario_name(self) -> str:
        return "Fanatics Collectibles"

    @property
    def scenario_description(self) -> str:
        return (
            "Enterprise infrastructure and network operations for vertically integrated "
            "trading cards and memorabilia. Recently migrated 100% out of physical DCs to "
            "50% AWS / 50% Azure with GCP edge."
        )

    @property
    def namespace(self) -> str:
        return "fanatics"

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "card-printing-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "manufacturing",
                "language": "java",
            },
            "digital-marketplace": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "commerce",
                "language": "python",
            },
            "auction-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "commerce",
                "language": "go",
            },
            "packaging-fulfillment": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "logistics",
                "language": "python",
            },
            "wifi-controller": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "network_access",
                "language": "cpp",
                "generates_traces": False,
            },
            "cloud-inventory-scanner": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "cloud_ops",
                "language": "python",
            },
            "network-controller": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "network_core",
                "language": "go",
                "generates_traces": False,
            },
            "firewall-gateway": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "security",
                "language": "rust",
                "generates_traces": False,
            },
            "dns-dhcp-service": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "network_services",
                "language": "java",
                "generates_traces": False,
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "MAC Address Flapping",
                "subsystem": "network_core",
                "vehicle_section": "switching_fabric",
                "error_type": "SW_MATM-4-MACFLAP_NOTIF",
                "sensor_type": "mac_table",
                "affected_services": ["network-controller", "dns-dhcp-service"],
                "cascade_services": ["firewall-gateway", "wifi-controller"],
                "description": "MAC address table instability causing port flapping on the switching fabric",
                "error_message": (
                    "%SW_MATM-4-MACFLAP_NOTIF: Host {mac_address} in vlan {vlan_id} "
                    "is flapping between port {interface_src} and port {interface_dst}, "
                    "{flap_count} moves in {flap_window}s"
                ),
                "stack_trace": (
                    "switch# show mac address-table notification mac-move\n"
                    "MAC Move Notification Feature is Enabled on the switch\n"
                    "VLAN  MAC Address       From Port          To Port            Move Count\n"
                    "----  ----------------  -----------------  -----------------  ----------\n"
                    "{vlan_id}   {mac_address}     {interface_src}         {interface_dst}         {flap_count}\n"
                    "\n"
                    "switch# show mac address-table count\n"
                    "Total MAC Addresses for this criterion: 3847\n"
                    "Multicast MAC Addresses:                12\n"
                    "Unicast MAC Addresses:                  3835\n"
                    "Total MAC Addresses in Use:             3847"
                ),
            },
            2: {
                "name": "Spanning Tree Topology Change",
                "subsystem": "network_core",
                "vehicle_section": "switching_fabric",
                "error_type": "SPANTREE-2-TOPO_CHANGE",
                "sensor_type": "stp_state",
                "affected_services": ["network-controller", "firewall-gateway"],
                "cascade_services": ["dns-dhcp-service", "wifi-controller"],
                "description": "Rapid spanning tree topology changes destabilizing Layer 2 forwarding",
                "error_message": (
                    "%SPANTREE-2-TOPO_CHANGE: Topology Change received on VLAN {vlan_id} "
                    "instance {stp_instance} from bridge {bridge_id} via port {interface}, "
                    "{tc_count} TCN BPDUs in {tc_window}s"
                ),
                "stack_trace": (
                    "switch# show spanning-tree vlan {vlan_id} detail\n"
                    "VLAN{vlan_id} is executing the rstp compatible Spanning Tree protocol\n"
                    "  Bridge Identifier has priority 32768, address {bridge_id}\n"
                    "  Topology change flag set, detected flag set\n"
                    "  Number of topology changes {tc_count}\n"
                    "  Last change occurred on port {interface}\n"
                    "  Times: hello 2, max age 20, forward delay 15, topology change {tc_window}\n"
                    "  Port {interface} of VLAN{vlan_id} is designated forwarding\n"
                    "    Port cost 4, Port priority 128, Port Identifier 128.1\n"
                    "    Number of transitions to forwarding state: {tc_count}"
                ),
            },
            3: {
                "name": "BGP Peer Flapping",
                "subsystem": "network_core",
                "vehicle_section": "routing_engine",
                "error_type": "BGP-3-NOTIFICATION",
                "sensor_type": "bgp_session",
                "affected_services": ["network-controller", "firewall-gateway"],
                "cascade_services": ["dns-dhcp-service", "cloud-inventory-scanner"],
                "description": "BGP peering session repeatedly transitioning between Established and Idle states",
                "error_message": (
                    "%BGP-3-NOTIFICATION: Neighbor {bgp_peer_ip} (AS {bgp_peer_as}) "
                    "sent NOTIFICATION {bgp_notification}, {bgp_flap_count} transitions "
                    "in {bgp_flap_window}s, last state {bgp_last_state}"
                ),
                "stack_trace": (
                    "router# show bgp neighbors {bgp_peer_ip}\n"
                    "BGP neighbor is {bgp_peer_ip}, remote AS {bgp_peer_as}, external link\n"
                    "  BGP state = {bgp_last_state}, up for 00:00:03\n"
                    "  Last read 00:00:03, Last write 00:00:08\n"
                    "  Hold time is 180, keepalive interval is 60 seconds\n"
                    "  Neighbor sessions: 1 active\n"
                    "  Notification received: {bgp_notification}\n"
                    "  Flap count: {bgp_flap_count} in {bgp_flap_window}s\n"
                    "    Opens:           Sent 12   Rcvd 9\n"
                    "    Notifications:   Sent 0    Rcvd {bgp_flap_count}\n"
                    "    Updates:         Sent 245  Rcvd 0\n"
                    "    Keepalives:      Sent 1024 Rcvd 891"
                ),
            },
            4: {
                "name": "Firewall Session Table Exhaustion",
                "subsystem": "security",
                "vehicle_section": "perimeter_defense",
                "error_type": "SYSTEM-session-threshold",
                "sensor_type": "session_table",
                "affected_services": ["firewall-gateway", "network-controller"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "Firewall session table approaching maximum capacity, new connections being dropped",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,session,0,"
                    "SYSTEM-session-threshold,Session table utilization critical: "
                    "{session_count}/{session_max} ({session_util_pct}%) in zone {fw_zone}, "
                    "{session_drops} new connections dropped, top source {top_source_ip}"
                ),
                "stack_trace": (
                    "> show session info\n"
                    "Number of sessions supported:    {session_max}\n"
                    "Number of active sessions:       {session_count}\n"
                    "Session table utilization:       {session_util_pct}%\n"
                    "Number of sessions dropped:      {session_drops}\n"
                    "  Zone: {fw_zone}\n"
                    "  Top source: {top_source_ip}\n"
                    "TCP sessions:    {session_count}\n"
                    "UDP sessions:    1245\n"
                    "ICMP sessions:   89\n"
                    "Session aging:   TCP default timeout 3600s"
                ),
            },
            5: {
                "name": "Firewall CPU Overload",
                "subsystem": "security",
                "vehicle_section": "perimeter_defense",
                "error_type": "SYSTEM-cpu-critical",
                "sensor_type": "cpu_utilization",
                "affected_services": ["firewall-gateway", "network-controller"],
                "cascade_services": ["dns-dhcp-service", "digital-marketplace"],
                "description": "Firewall data plane CPU exceeding safe operating threshold",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,general,0,"
                    "SYSTEM-cpu-critical,Data plane CPU at {fw_dp_cpu_pct}% "
                    "(threshold {fw_cpu_threshold}%), management plane {fw_mgmt_cpu_pct}%, "
                    "packet buffer {fw_buffer_pct}%, active rules {fw_policy_count}"
                ),
                "stack_trace": (
                    "> show running resource-monitor\n"
                    "Resource utilization (observed over last 60 seconds):\n"
                    "  Data Plane CPU Utilization:\n"
                    "    DP-0:  {fw_dp_cpu_pct}%  (threshold: {fw_cpu_threshold}%)\n"
                    "    DP-1:  {fw_dp_cpu_pct}%\n"
                    "  Management Plane CPU: {fw_mgmt_cpu_pct}%\n"
                    "  Packet Buffer:        {fw_buffer_pct}%\n"
                    "  Active Security Rules: {fw_policy_count}\n"
                    "  Session Rate:          8,452 sessions/sec\n"
                    "  Throughput:            4.2 Gbps\n"
                    "  Packet Rate:           892,341 pps"
                ),
            },
            6: {
                "name": "SSL Decryption Certificate Expiry",
                "subsystem": "security",
                "vehicle_section": "ssl_inspection",
                "error_type": "SYSTEM-cert-expire",
                "sensor_type": "certificate",
                "affected_services": ["firewall-gateway", "dns-dhcp-service"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "SSL decryption forward proxy certificate expiring or expired, breaking TLS inspection",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,general,0,"
                    "SYSTEM-cert-expire,Certificate '{cert_cn}' (serial {cert_serial}) "
                    "expires in {cert_days_remaining} days, decryption profile {cert_profile}, "
                    "affecting {cert_affected_rules} policy rules"
                ),
                "stack_trace": (
                    "> show system certificate detail\n"
                    "Certificate '{cert_cn}'\n"
                    "  Serial Number: {cert_serial}\n"
                    "  Issuer: CN=Fanatics-Internal-CA,O=Fanatics Inc\n"
                    "  Subject: CN={cert_cn}\n"
                    "  Not Before: Jan 15 00:00:00 2024 GMT\n"
                    "  Not After:  Jan 18 00:00:00 2025 GMT\n"
                    "  Days Remaining: {cert_days_remaining}\n"
                    "  Key Size: 2048\n"
                    "  Used by decryption profile: {cert_profile}\n"
                    "  Policy rules referencing: {cert_affected_rules}\n"
                    "  Status: EXPIRING"
                ),
            },
            7: {
                "name": "WiFi AP Disconnect Storm",
                "subsystem": "network_access",
                "vehicle_section": "wireless_lan",
                "error_type": "AP_DISCONNECTED",
                "sensor_type": "ap_status",
                "affected_services": ["wifi-controller", "network-controller"],
                "cascade_services": ["packaging-fulfillment", "card-printing-system"],
                "description": "Multiple wireless access points simultaneously losing connectivity to the controller",
                "error_message": (
                    "AP_DISCONNECTED event_id=mist-evt-{ap_disconnect_count}: "
                    "{ap_disconnect_count} APs lost connectivity in {ap_disconnect_window}s, "
                    "including {ap_name} (site {ap_site}), "
                    "last CAPWAP heartbeat {ap_last_heartbeat}s ago"
                ),
                "stack_trace": (
                    '{{"type": "AP_DISCONNECTED", "event_id": "mist-evt-{ap_disconnect_count}", '
                    '"org_id": "fanatics-org-001", "site_id": "{ap_site}", '
                    '"ap_name": "{ap_name}", "ap_mac": "5c:5b:35:a1:b2:c3", '
                    '"timestamp": 1705329121, "duration": {ap_disconnect_window}, '
                    '"count": {ap_disconnect_count}, "last_seen": {ap_last_heartbeat}, '
                    '"reason": "CAPWAP heartbeat timeout", "firmware": "0.14.29313"}}'
                ),
            },
            8: {
                "name": "WiFi Channel Interference",
                "subsystem": "network_access",
                "vehicle_section": "wireless_lan",
                "error_type": "INTERFERENCE_DETECTED",
                "sensor_type": "rf_spectrum",
                "affected_services": ["wifi-controller", "network-controller"],
                "cascade_services": ["packaging-fulfillment"],
                "description": "Co-channel and adjacent-channel interference degrading wireless performance",
                "error_message": (
                    "INTERFERENCE_DETECTED event_id=mist-rf-{channel_number}: "
                    "ap_name={ap_name} channel={channel_number} "
                    "co_channel_interference={interference_pct}% "
                    "noise_floor={noise_floor_dbm}dBm "
                    "retransmit_rate={retransmit_pct}% "
                    "neighbor_aps={neighbor_ap_count}"
                ),
                "stack_trace": (
                    '{{"type": "INTERFERENCE_DETECTED", "event_id": "mist-rf-{channel_number}", '
                    '"ap_name": "{ap_name}", "band": "5GHz", "channel": {channel_number}, '
                    '"bandwidth": 40, "co_channel_interference": {interference_pct}, '
                    '"adjacent_channel_interference": 8.2, "noise_floor": {noise_floor_dbm}, '
                    '"retransmit_rate": {retransmit_pct}, "neighbor_aps": {neighbor_ap_count}, '
                    '"recommended_channel": 36, "rrm_action": "pending"}}'
                ),
            },
            9: {
                "name": "Client Authentication Storm",
                "subsystem": "network_access",
                "vehicle_section": "wireless_auth",
                "error_type": "AUTH_FAILURE_STORM",
                "sensor_type": "radius_auth",
                "affected_services": ["wifi-controller", "dns-dhcp-service"],
                "cascade_services": ["network-controller"],
                "description": "RADIUS authentication requests spiking beyond server capacity",
                "error_message": (
                    "AUTH_FAILURE_STORM event_id=mist-auth-storm: "
                    "rate={auth_requests_per_sec}/s (threshold {auth_threshold}/s), "
                    "failures={auth_failures} timeouts={auth_timeouts} "
                    "nas={radius_nas_ip} server={radius_server}"
                ),
                "stack_trace": (
                    '{{"type": "AUTH_FAILURE_STORM", "event_id": "mist-auth-storm", '
                    '"org_id": "fanatics-org-001", "nas_ip": "{radius_nas_ip}", '
                    '"radius_server": "{radius_server}", "auth_rate": {auth_requests_per_sec}, '
                    '"threshold": {auth_threshold}, "failures": {auth_failures}, '
                    '"timeouts": {auth_timeouts}, "eap_type": "PEAP-MSCHAPv2", '
                    '"ssid": "Fanatics-Corp", '
                    '"reason_codes": ["timeout", "reject", "invalid_credential"]}}'
                ),
            },
            10: {
                "name": "DNS Resolution Failure Over VPN",
                "subsystem": "network_services",
                "vehicle_section": "name_resolution",
                "error_type": "NAMED-SERVFAIL-FORWARDER",
                "sensor_type": "dns_query",
                "affected_services": ["dns-dhcp-service", "network-controller"],
                "cascade_services": ["digital-marketplace", "auction-engine", "cloud-inventory-scanner"],
                "description": "DNS queries traversing VPN tunnel failing to resolve internal records",
                "error_message": (
                    "named[12345]: NAMED-SERVFAIL-FORWARDER: query '{dns_query_name}' "
                    "type {dns_query_type} via tunnel {vpn_tunnel_name}: "
                    "forwarder {dns_forwarder_ip} unreachable, fallback {dns_fallback_ip} "
                    "timeout after {dns_timeout_ms}ms, returning {dns_rcode}"
                ),
                "stack_trace": (
                    "named[12345]: debug: query '{dns_query_name}' IN {dns_query_type} +E(0)\n"
                    "named[12345]: debug: forwarding query to {dns_forwarder_ip} via {vpn_tunnel_name}\n"
                    "named[12345]: debug: send: no response from {dns_forwarder_ip}#53\n"
                    "named[12345]: debug: trying fallback forwarder {dns_fallback_ip}\n"
                    "named[12345]: debug: receive: timeout from {dns_fallback_ip}#53 after {dns_timeout_ms}ms\n"
                    "named[12345]: error: NAMED-SERVFAIL-FORWARDER: all forwarders unreachable for '{dns_query_name}'\n"
                    "named[12345]: debug: query failed (SERVFAIL) '{dns_query_name}/{dns_query_type}/IN': all forwarders failed"
                ),
            },
            11: {
                "name": "DHCP Lease Storm",
                "subsystem": "network_services",
                "vehicle_section": "address_management",
                "error_type": "DHCPD-LEASE-EXHAUSTION",
                "sensor_type": "dhcp_lease",
                "affected_services": ["dns-dhcp-service", "network-controller"],
                "cascade_services": ["wifi-controller", "packaging-fulfillment"],
                "description": "DHCP scope exhaustion from excessive DISCOVER/REQUEST rate",
                "error_message": (
                    "dhcpd[6789]: DHCPD-LEASE-EXHAUSTION: pool {dhcp_scope} at {dhcp_util_pct}% "
                    "({dhcp_active_leases}/{dhcp_total_leases} leases), "
                    "DISCOVER rate {dhcp_discover_rate}/s, {dhcp_nak_count} NAKs, "
                    "rogue server detected at {dhcp_rogue_ip}"
                ),
                "stack_trace": (
                    "dhcpd[6789]: info: DHCPDISCOVER from 00:11:22:33:44:55 via eth0\n"
                    "dhcpd[6789]: info: pool {dhcp_scope}: {dhcp_active_leases} of {dhcp_total_leases} leases active ({dhcp_util_pct}%)\n"
                    "dhcpd[6789]: warning: DHCPD-LEASE-EXHAUSTION: pool near capacity\n"
                    "dhcpd[6789]: warning: {dhcp_discover_rate} DHCPDISCOVER packets/sec (storm threshold: 50/s)\n"
                    "dhcpd[6789]: warning: {dhcp_nak_count} DHCPNAK sent — no available leases\n"
                    "dhcpd[6789]: alert: rogue DHCP server detected: {dhcp_rogue_ip} offering leases on {dhcp_scope}\n"
                    "dhcpd[6789]: info: lease pool statistics: free=0, backup=0, expired=3, abandoned=2"
                ),
            },
            12: {
                "name": "Auction Bid Latency Spike",
                "subsystem": "commerce",
                "vehicle_section": "bidding_platform",
                "error_type": "BID_LATENCY_SLA_BREACH",
                "sensor_type": "bid_processing",
                "affected_services": ["auction-engine", "digital-marketplace"],
                "cascade_services": ["network-controller", "firewall-gateway"],
                "description": "Real-time bid processing latency exceeding SLA thresholds",
                "error_message": (
                    'level=error ts=2025-01-15T14:32:01.234Z caller=bid_processor.go:289 '
                    'msg="BID_LATENCY_SLA_BREACH" auction={auction_id} bid={bid_id} '
                    "latency_ms={bid_latency_ms} sla_ms={bid_sla_ms} "
                    "queue_depth={bid_queue_depth} ws_delay_ms={ws_delay_ms} "
                    "affected_bidders={affected_bidders}"
                ),
                "stack_trace": (
                    "goroutine 847 [running]:\n"
                    "runtime/debug.Stack()\n"
                    "\t/usr/local/go/src/runtime/debug/stack.go:24 +0x5e\n"
                    "github.com/fanatics/auction-engine/internal/processor.(*BidProcessor).ProcessBid(0xc000518000, "
                    "{{0xc000a12480, 0x24}}, {{0xc000a124c0, 0x26}}, 0x{bid_latency_ms})\n"
                    "\t/app/internal/processor/bid_processor.go:289 +0x3a2\n"
                    "github.com/fanatics/auction-engine/internal/processor.(*BidProcessor).handleBidQueue(0xc000518000)\n"
                    "\t/app/internal/processor/bid_processor.go:145 +0x1b8\n"
                    "github.com/fanatics/auction-engine/internal/ws.(*Hub).broadcastBidUpdate(0xc000420000, "
                    "{{0xc000a12480, 0x24}})\n"
                    "\t/app/internal/ws/hub.go:89 +0x204\n"
                    "created by github.com/fanatics/auction-engine/cmd/server.Run in goroutine 1\n"
                    "\t/app/cmd/server/main.go:67 +0x2a5"
                ),
            },
            13: {
                "name": "Payment Processing Timeout",
                "subsystem": "commerce",
                "vehicle_section": "payment_system",
                "error_type": "PAYMENT_GATEWAY_TIMEOUT",
                "sensor_type": "payment_gateway",
                "affected_services": ["digital-marketplace", "auction-engine"],
                "cascade_services": ["firewall-gateway"],
                "description": "Payment gateway requests timing out, affecting checkout and auction settlements",
                "error_message": (
                    "[PaymentHandler] PAYMENT_GATEWAY_TIMEOUT: order={order_id} "
                    "provider={payment_provider} timeout={payment_timeout_ms}ms "
                    "gateway_code={gateway_response_code} "
                    "retry={payment_retry_count}/{payment_max_retries} "
                    "amount=${payment_amount}"
                ),
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "/app/marketplace/handlers/payment.py", line 178, in process_payment\n'
                    "    response = await self.gateway.charge(order_id, amount, provider)\n"
                    '  File "/app/marketplace/gateways/{payment_provider}.py", line 92, in charge\n'
                    "    result = await self._http.post(self.endpoint, json=payload, timeout={payment_timeout_ms}/1000)\n"
                    '  File "/app/venv/lib/python3.11/site-packages/httpx/_client.py", line 1574, in post\n'
                    '    raise ReadTimeout("Timed out while receiving data")\n'
                    "httpx.ReadTimeout: Payment gateway did not respond within {payment_timeout_ms}ms\n"
                    "PAYMENT_GATEWAY_TIMEOUT: order {order_id} via {payment_provider} — {gateway_response_code}"
                ),
            },
            14: {
                "name": "Product Catalog Sync Failure",
                "subsystem": "commerce",
                "vehicle_section": "catalog_system",
                "error_type": "CATALOG_SYNC_FAILURE",
                "sensor_type": "catalog_sync",
                "affected_services": ["digital-marketplace", "card-printing-system"],
                "cascade_services": ["auction-engine"],
                "description": "Product catalog replication between marketplace and printing system failing",
                "error_message": (
                    "[CatalogReplicator] CATALOG_SYNC_FAILURE: "
                    "{catalog_sync_failed}/{catalog_sync_total} records failed syncing "
                    '{catalog_source} -> {catalog_destination}, '
                    'last_sync={catalog_last_sync_min}m ago, '
                    'error="{catalog_error_detail}"'
                ),
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "/app/marketplace/sync/catalog_replicator.py", line 267, in sync_catalog\n'
                    "    result = await self.replicate_batch(source, dest, batch)\n"
                    '  File "/app/marketplace/sync/catalog_replicator.py", line 245, in replicate_batch\n'
                    "    async for record in batch:\n"
                    '  File "/app/marketplace/db/connector.py", line 134, in execute_batch\n'
                    '    raise DBSyncError("{catalog_error_detail}")\n'
                    "marketplace.exceptions.CatalogSyncError: CATALOG_SYNC_FAILURE — "
                    "{catalog_sync_failed}/{catalog_sync_total} records failed\n"
                    "  Source: {catalog_source}\n"
                    "  Destination: {catalog_destination}\n"
                    "  Last successful sync: {catalog_last_sync_min} minutes ago"
                ),
            },
            15: {
                "name": "Print Queue Overflow",
                "subsystem": "manufacturing",
                "vehicle_section": "production_line",
                "error_type": "MES-QUEUE-OVERFLOW",
                "sensor_type": "print_queue",
                "affected_services": ["card-printing-system", "packaging-fulfillment"],
                "cascade_services": ["digital-marketplace"],
                "description": "Print job queue exceeding buffer capacity, new jobs being rejected",
                "error_message": (
                    "[PrintScheduler] MES-QUEUE-OVERFLOW: "
                    "queue={print_queue_depth}/{print_queue_max} ({print_queue_pct}%) "
                    "job={print_job_id} REJECTED, oldest_pending={print_oldest_job_min}m "
                    "printer={printer_name} status={printer_status}"
                ),
                "stack_trace": (
                    "com.fanatics.mes.exception.QueueOverflowException: "
                    "MES-QUEUE-OVERFLOW: queue capacity exceeded {print_queue_depth}/{print_queue_max}\n"
                    "\tat com.fanatics.mes.scheduler.PrintScheduler.enqueueJob(PrintScheduler.java:312)\n"
                    "\tat com.fanatics.mes.scheduler.PrintScheduler.processIncoming(PrintScheduler.java:245)\n"
                    "\tat com.fanatics.mes.queue.JobQueueManager.submit(JobQueueManager.java:189)\n"
                    "\tat com.fanatics.mes.api.PrintJobController.submitJob(PrintJobController.java:78)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)\n"
                    "\tat java.base/java.lang.Thread.run(Thread.java:842)\n"
                    "  Printer: {printer_name} Status: {printer_status}\n"
                    "  Job: {print_job_id} Oldest pending: {print_oldest_job_min}m"
                ),
            },
            16: {
                "name": "Quality Control Rejection Spike",
                "subsystem": "manufacturing",
                "vehicle_section": "quality_assurance",
                "error_type": "MES-QC-REJECT-THRESHOLD",
                "sensor_type": "qc_inspection",
                "affected_services": ["card-printing-system", "packaging-fulfillment"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "Automated quality inspection system rejecting cards above acceptable defect rate",
                "error_message": (
                    "[QCInspector] MES-QC-REJECT-THRESHOLD: batch={qc_batch_id} "
                    "rejected={qc_reject_count}/{qc_inspected_count} "
                    "({qc_reject_pct}% defect rate, threshold {qc_threshold_pct}%) "
                    "defect={qc_defect_type} line={qc_line_number}"
                ),
                "stack_trace": (
                    "com.fanatics.mes.exception.QCRejectException: "
                    "MES-QC-REJECT-THRESHOLD: defect rate {qc_reject_pct}% exceeds threshold {qc_threshold_pct}%\n"
                    "\tat com.fanatics.mes.quality.QCInspector.inspectBatch(QCInspector.java:234)\n"
                    "\tat com.fanatics.mes.quality.QCInspector.runInspection(QCInspector.java:178)\n"
                    "\tat com.fanatics.mes.quality.InspectionPipeline.process(InspectionPipeline.java:145)\n"
                    "\tat com.fanatics.mes.api.QCController.triggerInspection(QCController.java:56)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)\n"
                    "\tat java.base/java.lang.Thread.run(Thread.java:842)\n"
                    "  Batch: {qc_batch_id} Line: {qc_line_number}\n"
                    "  Primary defect: {qc_defect_type}\n"
                    "  Inspected: {qc_inspected_count} Rejected: {qc_reject_count}"
                ),
            },
            17: {
                "name": "Fulfillment Label Printer Failure",
                "subsystem": "logistics",
                "vehicle_section": "shipping_bay",
                "error_type": "WMS-LABEL-PRINTER-FAULT",
                "sensor_type": "label_printer",
                "affected_services": ["packaging-fulfillment", "card-printing-system"],
                "cascade_services": ["digital-marketplace"],
                "description": "Shipping label printers going offline or producing unreadable labels",
                "error_message": (
                    "wms.shipping WMS-LABEL-PRINTER-FAULT printer={label_printer_id} "
                    "status={label_printer_status} error_code={label_error_code} "
                    "failed_labels={label_failed_count} window={label_window_min}m "
                    "carrier={label_carrier} queue_depth={label_queue_depth}"
                ),
                "stack_trace": (
                    "WMS Label Subsystem Diagnostic Report\n"
                    "--------------------------------------\n"
                    "Printer ID:     {label_printer_id}\n"
                    "Status:         {label_printer_status}\n"
                    "Error Code:     {label_error_code}\n"
                    "Failed Labels:  {label_failed_count} in last {label_window_min} minutes\n"
                    "Carrier:        {label_carrier}\n"
                    "Queue Depth:    {label_queue_depth} shipments pending\n"
                    "ZPL Version:    ZPL-II\n"
                    "Print Head:     NEEDS_REPLACEMENT\n"
                    "Last Maintenance: 45 days ago\n"
                    "Recommended Action: Replace print head, recalibrate label alignment"
                ),
            },
            18: {
                "name": "Warehouse Scanner Desync",
                "subsystem": "logistics",
                "vehicle_section": "inventory_system",
                "error_type": "WMS-SCANNER-DESYNC",
                "sensor_type": "barcode_scanner",
                "affected_services": ["packaging-fulfillment", "cloud-inventory-scanner"],
                "cascade_services": ["digital-marketplace", "card-printing-system"],
                "description": "Barcode scanners losing synchronization with inventory management system",
                "error_message": (
                    "wms.inventory WMS-SCANNER-DESYNC scanner={scanner_id} "
                    "zone={scanner_zone} last_sync={scanner_last_sync_sec}s "
                    "(max {scanner_sync_max_sec}s) missed_scans={scanner_missed_scans} "
                    "inventory_delta={inventory_delta} firmware=v{scanner_firmware}"
                ),
                "stack_trace": (
                    "WMS Scanner Sync Diagnostic Report\n"
                    "------------------------------------\n"
                    "Scanner ID:     {scanner_id}\n"
                    "Zone:           {scanner_zone}\n"
                    "Last Sync:      {scanner_last_sync_sec}s ago (threshold: {scanner_sync_max_sec}s)\n"
                    "Missed Scans:   {scanner_missed_scans}\n"
                    "Inventory Delta: {inventory_delta} items\n"
                    "Firmware:       v{scanner_firmware}\n"
                    "WiFi Signal:    -72 dBm (marginal)\n"
                    "Battery Level:  34%\n"
                    "Recommended Action: Reconnect scanner, verify WiFi coverage in {scanner_zone}"
                ),
            },
            19: {
                "name": "Orphaned Cloud Resource Alert",
                "subsystem": "cloud_ops",
                "vehicle_section": "asset_management",
                "error_type": "CLOUD-ORPHANED-RESOURCE",
                "sensor_type": "cloud_asset",
                "affected_services": ["cloud-inventory-scanner", "network-controller"],
                "cascade_services": ["firewall-gateway"],
                "description": "Cloud resources detected without owner tags or associated workloads",
                "error_message": (
                    "cloud-governance CLOUD-ORPHANED-RESOURCE "
                    "resource_type={cloud_resource_type} resource_id={cloud_resource_id} "
                    "provider={cloud_resource_provider} region={cloud_resource_region} "
                    "age_days={cloud_resource_age_days} cost=${cloud_resource_cost_daily}/day "
                    "security_group={cloud_resource_sg} owner=NONE"
                ),
                "stack_trace": (
                    "Cloud Governance Scan Report\n"
                    "-----------------------------\n"
                    "Resource:       {cloud_resource_type} ({cloud_resource_id})\n"
                    "Provider:       {cloud_resource_provider}\n"
                    "Region:         {cloud_resource_region}\n"
                    "Created:        {cloud_resource_age_days} days ago\n"
                    "Daily Cost:     ${cloud_resource_cost_daily}\n"
                    "Security Group: {cloud_resource_sg}\n"
                    "Owner Tag:      MISSING\n"
                    "Team Tag:       MISSING\n"
                    "Compliance:     FAIL — no owner tag after 14-day grace period\n"
                    "Action:         Schedule for termination review"
                ),
            },
            20: {
                "name": "Cross-Cloud VPN Tunnel Flapping",
                "subsystem": "cloud_ops",
                "vehicle_section": "vpn_connectivity",
                "error_type": "VPN-TUNNEL-FLAP",
                "sensor_type": "vpn_tunnel",
                "affected_services": ["cloud-inventory-scanner", "network-controller"],
                "cascade_services": ["dns-dhcp-service", "firewall-gateway"],
                "description": "Site-to-site VPN tunnels between cloud providers repeatedly going up and down",
                "error_message": (
                    "cloud-networking VPN-TUNNEL-FLAP tunnel={vpn_tunnel_name} "
                    "path={vpn_src_cloud}->{vpn_dst_cloud} flaps={vpn_flap_count} "
                    "window={vpn_flap_window}s state={vpn_current_state} "
                    "ike_phase={vpn_ike_phase} ike_status={vpn_ike_status} "
                    "last_dpd={vpn_last_dpd_sec}s"
                ),
                "stack_trace": (
                    "VPN Tunnel Diagnostic Report\n"
                    "------------------------------\n"
                    "Tunnel:         {vpn_tunnel_name}\n"
                    "Path:           {vpn_src_cloud} -> {vpn_dst_cloud}\n"
                    "Current State:  {vpn_current_state}\n"
                    "Flap Count:     {vpn_flap_count} in {vpn_flap_window}s\n"
                    "IKE Phase:      {vpn_ike_phase}\n"
                    "IKE Status:     {vpn_ike_status}\n"
                    "Last DPD:       {vpn_last_dpd_sec}s ago\n"
                    "Local Gateway:  10.0.1.1\n"
                    "Remote Gateway: 10.2.0.1\n"
                    "MTU:            1400\n"
                    "Rekey Interval: 3600s\n"
                    "Action:         Check IPSec SA, verify gateway reachability"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "network-controller": [
                ("firewall-gateway", "/api/v1/firewall/sessions", "GET"),
                ("firewall-gateway", "/api/v1/firewall/policy-push", "POST"),
                ("dns-dhcp-service", "/api/v1/dns/zone-status", "GET"),
                ("dns-dhcp-service", "/api/v1/dhcp/scope-status", "GET"),
                ("wifi-controller", "/api/v1/wifi/ap-status", "GET"),
            ],
            "firewall-gateway": [
                ("dns-dhcp-service", "/api/v1/dns/resolve", "POST"),
                ("network-controller", "/api/v1/network/route-table", "GET"),
            ],
            "digital-marketplace": [
                ("auction-engine", "/api/v1/auction/active-listings", "GET"),
                ("auction-engine", "/api/v1/auction/place-bid", "POST"),
                ("card-printing-system", "/api/v1/printing/order-status", "GET"),
                ("card-printing-system", "/api/v1/printing/submit-job", "POST"),
                ("packaging-fulfillment", "/api/v1/fulfillment/ship-order", "POST"),
            ],
            "auction-engine": [
                ("digital-marketplace", "/api/v1/marketplace/listing-update", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/payment-settle", "POST"),
            ],
            "card-printing-system": [
                ("packaging-fulfillment", "/api/v1/fulfillment/queue-package", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/inventory-update", "POST"),
            ],
            "packaging-fulfillment": [
                ("cloud-inventory-scanner", "/api/v1/inventory/reconcile", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/shipment-notify", "POST"),
            ],
            "cloud-inventory-scanner": [
                ("network-controller", "/api/v1/network/vpn-health", "GET"),
                ("firewall-gateway", "/api/v1/firewall/sg-audit", "GET"),
            ],
            "wifi-controller": [
                ("dns-dhcp-service", "/api/v1/dhcp/client-lease", "GET"),
                ("network-controller", "/api/v1/network/vlan-map", "GET"),
            ],
            "dns-dhcp-service": [
                ("network-controller", "/api/v1/network/interface-status", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "network-controller": [
                ("/api/v1/network/health", "GET"),
                ("/api/v1/network/topology", "GET"),
                ("/api/v1/network/config-push", "POST"),
            ],
            "firewall-gateway": [
                ("/api/v1/firewall/status", "GET"),
                ("/api/v1/firewall/threat-log", "GET"),
            ],
            "dns-dhcp-service": [
                ("/api/v1/dns/query", "POST"),
                ("/api/v1/dhcp/lease-report", "GET"),
                ("/api/v1/dns/health", "GET"),
            ],
            "digital-marketplace": [
                ("/api/v1/marketplace/browse", "GET"),
                ("/api/v1/marketplace/checkout", "POST"),
                ("/api/v1/marketplace/search", "GET"),
            ],
            "auction-engine": [
                ("/api/v1/auction/live", "GET"),
                ("/api/v1/auction/bid", "POST"),
            ],
            "card-printing-system": [
                ("/api/v1/printing/queue-status", "GET"),
                ("/api/v1/printing/submit", "POST"),
            ],
            "packaging-fulfillment": [
                ("/api/v1/fulfillment/status", "GET"),
                ("/api/v1/fulfillment/ship", "POST"),
            ],
            "wifi-controller": [
                ("/api/v1/wifi/dashboard", "GET"),
            ],
            "cloud-inventory-scanner": [
                ("/api/v1/inventory/scan", "POST"),
                ("/api/v1/inventory/compliance", "GET"),
            ],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "digital-marketplace": [
                ("SELECT", "products", "SELECT id, name, price, stock FROM products WHERE category = ? AND status = 'active' ORDER BY listed_at DESC LIMIT 50"),
                ("INSERT", "orders", "INSERT INTO orders (user_id, product_id, quantity, total, status, created_at) VALUES (?, ?, ?, ?, 'pending', NOW())"),
                ("UPDATE", "inventory", "UPDATE inventory SET quantity = quantity - ? WHERE sku = ? AND quantity >= ?"),
            ],
            "auction-engine": [
                ("SELECT", "auctions", "SELECT id, current_bid, bid_count, end_time FROM auctions WHERE status = 'active' AND end_time > NOW()"),
                ("INSERT", "bids", "INSERT INTO bids (auction_id, bidder_id, amount, placed_at) VALUES (?, ?, ?, NOW())"),
                ("UPDATE", "auctions", "UPDATE auctions SET current_bid = ?, bid_count = bid_count + 1, last_bid_at = NOW() WHERE id = ? AND current_bid < ?"),
            ],
            "card-printing-system": [
                ("SELECT", "print_jobs", "SELECT job_id, card_design_id, quantity, priority, status FROM print_jobs WHERE status IN ('queued', 'printing') ORDER BY priority DESC"),
                ("UPDATE", "print_jobs", "UPDATE print_jobs SET status = ?, completed_at = NOW() WHERE job_id = ?"),
            ],
            "packaging-fulfillment": [
                ("SELECT", "shipments", "SELECT order_id, tracking_number, carrier, status FROM shipments WHERE created_at > NOW() - INTERVAL 24 HOUR AND status = 'pending'"),
                ("INSERT", "shipments", "INSERT INTO shipments (order_id, tracking_number, carrier, weight_oz, status) VALUES (?, ?, ?, ?, 'label_printed')"),
            ],
            "dns-dhcp-service": [
                ("SELECT", "dns_records", "SELECT fqdn, record_type, ttl, value FROM dns_records WHERE zone = ? AND record_type = ?"),
                ("SELECT", "dhcp_leases", "SELECT mac_addr, ip_addr, lease_start, lease_end, hostname FROM dhcp_leases WHERE scope = ? AND lease_end > NOW()"),
            ],
            "cloud-inventory-scanner": [
                ("SELECT", "cloud_resources", "SELECT resource_id, resource_type, provider, region, owner_tag, created_at FROM cloud_resources WHERE owner_tag IS NULL AND created_at < NOW() - INTERVAL 7 DAY"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "fanatics-aws-host-01",
                "host.id": "i-0f2a3b4c5d6e78901",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0fedcba987654321",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.10.1.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "987654321012",
                "cloud.instance.id": "i-0f2a3b4c5d6e78901",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "fanatics-gcp-host-01",
                "host.id": "7823456789012345678",
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
                "host.mac": ["42:01:0a:80:01:14", "42:01:0a:80:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "fanatics-infra-prod",
                "cloud.instance.id": "7823456789012345678",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "fanatics-azure-host-01",
                "host.id": "/subscriptions/fab-012/resourceGroups/fanatics-rg/providers/Microsoft.Compute/virtualMachines/fanatics-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.10", "10.2.0.11"],
                "host.mac": ["00:0d:3a:7e:8f:9a", "00:0d:3a:7e:8f:9b"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "fab-012-345-678",
                "cloud.instance.id": "fanatics-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "fanatics-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["card-printing-system", "digital-marketplace", "auction-engine"],
            },
            {
                "name": "fanatics-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["packaging-fulfillment", "wifi-controller", "cloud-inventory-scanner"],
            },
            {
                "name": "fanatics-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["network-controller", "firewall-gateway", "dns-dhcp-service"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0d1117",
            bg_secondary="#161b22",
            bg_tertiary="#21262d",
            accent_primary="#58a6ff",
            accent_secondary="#3fb950",
            text_primary="#e6edf3",
            text_secondary="#8b949e",
            text_accent="#58a6ff",
            status_nominal="#3fb950",
            status_warning="#d29922",
            status_critical="#f85149",
            status_info="#58a6ff",
            font_family="'Inter', system-ui, sans-serif",
            grid_background=True,
            dashboard_title="Network Operations Center (NOC)",
            chaos_title="Incident Simulator",
            landing_title="Fanatics Infrastructure Operations",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "fanatics-infra-analyst",
            "name": "Infrastructure & Network Analyst",
            "assessment_tool_name": "platform_load_assessment",
            "system_prompt": (
                "You are the Fanatics Infrastructure & Network Analyst, an expert AI assistant "
                "for enterprise network and infrastructure operations. You help NOC engineers "
                "investigate incidents, analyze telemetry data, and provide root cause analysis "
                "for fault conditions across 9 infrastructure services spanning AWS, GCP, and Azure. "
                "You have deep expertise in Cisco IOS-XE/NX-OS switching and routing, "
                "Palo Alto PAN-OS firewall management, Juniper Mist wireless LAN controllers, "
                "Infoblox DDI (DNS/DHCP/IPAM), AWS VPC networking, Azure Virtual Network, "
                "and GCP VPC. You understand BGP peering, spanning tree protocol, "
                "802.1X/RADIUS authentication, SSL inspection, and cross-cloud VPN tunneling. "
                "When investigating incidents, search for these vendor-specific identifiers in logs: "
                "Cisco syslog mnemonics (SW_MATM-4-MACFLAP_NOTIF, SPANTREE-2-TOPO_CHANGE, BGP-3-NOTIFICATION), "
                "PAN-OS system events (SYSTEM-session-threshold, SYSTEM-cpu-critical, SYSTEM-cert-expire), "
                "Juniper Mist events (AP_DISCONNECTED, INTERFERENCE_DETECTED, AUTH_FAILURE_STORM), "
                "DNS/DHCP faults (NAMED-SERVFAIL-FORWARDER, DHCPD-LEASE-EXHAUSTION), "
                "commerce errors (BID_LATENCY_SLA_BREACH, PAYMENT_GATEWAY_TIMEOUT, CATALOG_SYNC_FAILURE), "
                "manufacturing faults (MES-QUEUE-OVERFLOW, MES-QC-REJECT-THRESHOLD), "
                "warehouse faults (WMS-LABEL-PRINTER-FAULT, WMS-SCANNER-DESYNC), "
                "and cloud ops events (CLOUD-ORPHANED-RESOURCE, VPN-TUNNEL-FLAP). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "platform_load_assessment",
            "description": (
                "Comprehensive platform load assessment. Evaluates all "
                "infrastructure services against event-day readiness criteria. "
                "Returns data for load evaluation across networking, DNS, "
                "VPN, firewall, and cloud infrastructure systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.fanatics.services.card_printing import CardPrintingSystemService
        from scenarios.fanatics.services.digital_marketplace import DigitalMarketplaceService
        from scenarios.fanatics.services.auction_engine import AuctionEngineService
        from scenarios.fanatics.services.packaging_fulfillment import PackagingFulfillmentService
        from scenarios.fanatics.services.wifi_controller import WifiControllerService
        from scenarios.fanatics.services.cloud_inventory_scanner import CloudInventoryScannerService
        from scenarios.fanatics.services.network_controller import NetworkControllerService
        from scenarios.fanatics.services.firewall_gateway import FirewallGatewayService
        from scenarios.fanatics.services.dns_dhcp_service import DnsDhcpService

        return [
            CardPrintingSystemService,
            DigitalMarketplaceService,
            AuctionEngineService,
            PackagingFulfillmentService,
            WifiControllerService,
            CloudInventoryScannerService,
            NetworkControllerService,
            FirewallGatewayService,
            DnsDhcpService,
        ]

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            # ── Network core (channels 1-3) ──
            "mac_address": f"{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}",
            "interface_src": random.choice(["Gi0/0/1", "Gi0/0/2", "Gi0/0/3", "Te1/0/1", "Te1/0/2"]),
            "interface_dst": random.choice(["Gi0/0/4", "Gi0/0/5", "Te1/0/3", "Te1/0/4"]),
            "interface": random.choice(["Gi0/0/1", "Gi0/0/2", "Te1/0/1", "Te1/0/2", "Po1"]),
            "vlan_id": random.choice([100, 200, 300, 400, 500, 1000]),
            "flap_count": random.randint(10, 50),
            "flap_window": random.randint(5, 30),
            "stp_instance": random.randint(0, 15),
            "tc_count": random.randint(15, 80),
            "tc_window": random.randint(10, 60),
            "bridge_id": f"8000.{random.randint(0,255):02x}{random.randint(0,255):02x}.{random.randint(0,255):02x}{random.randint(0,255):02x}.{random.randint(0,255):02x}{random.randint(0,255):02x}",
            "bgp_peer_ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "bgp_peer_as": random.choice([64512, 64513, 64514, 65001, 65002, 65100]),
            "bgp_flap_count": random.randint(5, 25),
            "bgp_flap_window": random.randint(30, 300),
            "bgp_last_state": random.choice(["Idle", "Active", "OpenSent", "OpenConfirm"]),
            "bgp_notification": random.choice([
                "Hold Timer Expired (code 4/0)",
                "Cease/Admin Reset (code 6/4)",
                "UPDATE Message Error (code 3/1)",
                "FSM Error (code 5/0)",
            ]),

            # ── Security (channels 4-6) ──
            "session_count": random.randint(58000, 63500),
            "session_max": 64000,
            "session_util_pct": round(random.uniform(90.0, 99.5), 1),
            "session_drops": random.randint(50, 500),
            "fw_zone": random.choice(["TRUST", "UNTRUST", "DMZ"]),
            "top_source_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "fw_dp_cpu_pct": round(random.uniform(85.0, 99.0), 1),
            "fw_mgmt_cpu_pct": round(random.uniform(60.0, 90.0), 1),
            "fw_cpu_threshold": 80,
            "fw_buffer_pct": round(random.uniform(75.0, 98.0), 1),
            "fw_policy_count": random.randint(800, 2500),
            "cert_cn": random.choice([
                "*.fanatics.internal", "forward-proxy.fanatics.com",
                "ssl-inspect.collectibles.prod", "tls-decrypt.warehouse.local",
            ]),
            "cert_serial": f"{random.randint(100000,999999):X}",
            "cert_days_remaining": random.randint(-5, 3),
            "cert_profile": random.choice(["ssl-forward-proxy", "ssl-inbound-inspection", "tls-decrypt-all"]),
            "cert_affected_rules": random.randint(15, 80),

            # ── Network access (channels 7-9) ──
            "ap_name": random.choice([
                "AP-WAREHOUSE-01", "AP-WAREHOUSE-02", "AP-PRINT-FLOOR-01",
                "AP-OFFICE-01", "AP-SHIPPING-01", "AP-DOCK-01",
            ]),
            "ap_site": random.choice(["warehouse-east", "print-facility", "office-hq", "shipping-dock"]),
            "ap_disconnect_count": random.randint(5, 20),
            "ap_disconnect_window": random.randint(10, 60),
            "ap_last_heartbeat": random.randint(30, 300),
            "channel_number": random.choice([1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161]),
            "interference_pct": round(random.uniform(25.0, 75.0), 1),
            "noise_floor_dbm": round(random.uniform(-80.0, -60.0), 1),
            "retransmit_pct": round(random.uniform(10.0, 40.0), 1),
            "neighbor_ap_count": random.randint(5, 20),
            "auth_requests_per_sec": random.randint(200, 1000),
            "auth_threshold": 100,
            "auth_failures": random.randint(50, 300),
            "auth_timeouts": random.randint(20, 150),
            "radius_nas_ip": f"10.1.{random.randint(1,10)}.{random.randint(1,254)}",
            "radius_server": random.choice(["radius-01.fanatics.internal", "radius-02.fanatics.internal"]),

            # ── Network services (channels 10-11) ──
            "dns_query_name": random.choice([
                "marketplace.fanatics.internal", "auction-api.collectibles.prod",
                "card-printer-01.warehouse.local", "inventory.cloud-ops.internal",
            ]),
            "dns_query_type": random.choice(["A", "AAAA", "CNAME", "SRV"]),
            "vpn_tunnel_name": random.choice(["aws-to-azure-01", "aws-to-gcp-01", "gcp-to-azure-01"]),
            "dns_rcode": random.choice(["SERVFAIL", "REFUSED", "NXDOMAIN"]),
            "dns_forwarder_ip": random.choice(["10.0.0.53", "10.1.0.53", "168.63.129.16"]),
            "dns_fallback_ip": random.choice(["10.0.1.53", "10.2.0.53"]),
            "dns_timeout_ms": random.randint(3000, 10000),
            "dhcp_scope": random.choice(["10.1.0.0/24", "10.2.0.0/24", "172.16.0.0/22", "192.168.1.0/24"]),
            "dhcp_util_pct": round(random.uniform(92.0, 100.0), 1),
            "dhcp_active_leases": random.randint(235, 254),
            "dhcp_total_leases": 254,
            "dhcp_discover_rate": random.randint(50, 300),
            "dhcp_nak_count": random.randint(10, 100),
            "dhcp_rogue_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",

            # ── Commerce (channels 12-14) ──
            "auction_id": f"AUC-{random.randint(100000,999999)}",
            "bid_id": f"BID-{random.randint(1000000,9999999)}",
            "bid_latency_ms": random.randint(500, 5000),
            "bid_sla_ms": 200,
            "bid_queue_depth": random.randint(100, 2000),
            "ws_delay_ms": random.randint(200, 3000),
            "affected_bidders": random.randint(10, 500),
            "order_id": f"ORD-{random.randint(100000,999999)}",
            "payment_provider": random.choice(["Stripe", "PayPal", "Adyen", "Braintree"]),
            "payment_timeout_ms": random.randint(5000, 30000),
            "gateway_response_code": random.choice(["504", "408", "429", "503"]),
            "payment_retry_count": random.randint(1, 3),
            "payment_max_retries": 3,
            "payment_amount": round(random.uniform(9.99, 4999.99), 2),
            "catalog_sync_failed": random.randint(50, 500),
            "catalog_sync_total": random.randint(1000, 5000),
            "catalog_source": random.choice(["card-printing-system", "product-master"]),
            "catalog_destination": random.choice(["digital-marketplace", "auction-engine"]),
            "catalog_last_sync_min": random.randint(30, 360),
            "catalog_error_detail": random.choice([
                "connection reset by peer",
                "schema version mismatch",
                "primary key conflict on sku column",
                "timeout waiting for lock on products table",
            ]),

            # ── Manufacturing (channels 15-16) ──
            "print_queue_depth": random.randint(450, 500),
            "print_queue_max": 500,
            "print_queue_pct": round(random.uniform(90.0, 100.0), 1),
            "print_job_id": f"PJ-{random.randint(10000,99999)}",
            "print_oldest_job_min": random.randint(30, 480),
            "printer_name": random.choice(["HP-Indigo-7K-01", "HP-Indigo-7K-02", "Koenig-Bauer-01", "Heidelberg-XL-01"]),
            "printer_status": random.choice(["PAPER_JAM", "INK_LOW", "OFFLINE", "HEAD_CLOG"]),
            "qc_reject_count": random.randint(20, 150),
            "qc_inspected_count": random.randint(500, 2000),
            "qc_reject_pct": round(random.uniform(5.0, 25.0), 1),
            "qc_threshold_pct": 2.0,
            "qc_defect_type": random.choice([
                "color_registration_shift", "die_cut_misalignment",
                "foil_stamp_incomplete", "surface_scratch", "centering_off",
            ]),
            "qc_batch_id": f"BATCH-{random.randint(1000,9999)}",
            "qc_line_number": random.choice(["LINE-A", "LINE-B", "LINE-C"]),

            # ── Logistics (channels 17-18) ──
            "label_printer_id": random.choice(["ZBR-SHIP-01", "ZBR-SHIP-02", "ZBR-DOCK-01"]),
            "label_printer_status": random.choice(["OFFLINE", "PAPER_OUT", "HEAD_ERROR", "RIBBON_EMPTY"]),
            "label_error_code": random.choice(["E1001", "E2003", "E3005", "E4002"]),
            "label_failed_count": random.randint(10, 100),
            "label_window_min": random.randint(5, 30),
            "label_carrier": random.choice(["UPS", "FedEx", "USPS", "DHL"]),
            "label_queue_depth": random.randint(50, 500),
            "scanner_id": random.choice(["SCN-WH-01", "SCN-WH-02", "SCN-WH-03", "SCN-DOCK-01"]),
            "scanner_zone": random.choice(["receiving", "storage-A", "storage-B", "packing", "shipping"]),
            "scanner_last_sync_sec": random.randint(120, 600),
            "scanner_sync_max_sec": 60,
            "scanner_missed_scans": random.randint(20, 200),
            "inventory_delta": random.randint(5, 50),
            "scanner_firmware": random.choice(["3.2.1", "3.1.8", "3.0.5"]),

            # ── Cloud ops (channels 19-20) ──
            "cloud_resource_type": random.choice(["EC2 Instance", "Azure VM", "GCE Instance", "EBS Volume", "Managed Disk", "S3 Bucket"]),
            "cloud_resource_id": f"res-{random.randint(10000,99999)}",
            "cloud_resource_provider": random.choice(["aws", "azure", "gcp"]),
            "cloud_resource_region": random.choice(["us-east-1", "eastus", "us-central1"]),
            "cloud_resource_age_days": random.randint(14, 180),
            "cloud_resource_cost_daily": round(random.uniform(2.50, 85.00), 2),
            "cloud_resource_sg": random.choice(["sg-0abc1234", "nsg-fanatics-default", "fw-rule-legacy"]),
            "vpn_src_cloud": random.choice(["aws", "gcp"]),
            "vpn_dst_cloud": random.choice(["azure", "gcp"]),
            "vpn_flap_count": random.randint(5, 30),
            "vpn_flap_window": random.randint(60, 600),
            "vpn_current_state": random.choice(["DOWN", "NEGOTIATING", "REKEYING"]),
            "vpn_ike_phase": random.choice(["1", "2"]),
            "vpn_ike_status": random.choice(["FAILED", "TIMEOUT", "SA_EXPIRED"]),
            "vpn_last_dpd_sec": random.randint(30, 300),
        }


# Module-level instance for registry discovery
scenario = FanaticsScenario()
