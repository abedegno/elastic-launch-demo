# NOVA-7 Troubleshooting Guide

Common issues and their solutions when running the NOVA-7 Launch Demo.

---

## Table of Contents

1. [Startup Issues](#1-startup-issues)
2. [Telemetry Pipeline Issues](#2-telemetry-pipeline-issues)
3. [Dashboard Issues](#3-dashboard-issues)
4. [Chaos Controller Issues](#4-chaos-controller-issues)
5. [Notification Issues](#5-notification-issues)
6. [Elastic / Kibana Issues](#6-elastic--kibana-issues)
7. [Docker Issues](#7-docker-issues)
8. [Performance Issues](#8-performance-issues)

---

## 1. Startup Issues

### Container fails to start

**Symptoms:** `docker compose up` exits with an error, or the container restarts repeatedly.

**Check logs:**
```bash
docker compose logs nova7
docker compose logs otel-collector
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Port 8080 already in use | Change `APP_PORT` in `.env` or stop the conflicting process: `lsof -i :8080` |
| Invalid Python syntax | Check `docker compose logs nova7` for import errors |
| Missing .env file | Run `cp .env.example .env` and configure required variables |
| Docker daemon not running | Start Docker: `sudo systemctl start docker` |

### setup.sh fails validation

**Symptoms:** The setup script reports missing variables or failed checks.

**Solution:**
```bash
# Check what is set
./setup.sh --dry-run

# Ensure .env is loaded
source .env
echo $ELASTIC_ENDPOINT
```

### Health check fails

**Symptoms:** `curl http://localhost:8080/health` returns connection refused or times out.

**Diagnosis:**
```bash
# Is the container running?
docker compose ps

# Check container logs
docker compose logs --tail 50 nova7

# Is the port mapped?
docker port $(docker compose ps -q nova7) 8080
```

---

## 2. Telemetry Pipeline Issues

### No data appears in Elastic

**Symptoms:** The NOVA-7 app is running but no logs/metrics/traces appear in Kibana.

**Diagnosis steps:**

1. **Check the OTel Collector logs:**
   ```bash
   docker compose logs otel-collector
   ```
   Look for connection errors, authentication failures, or export errors.

2. **Verify ELASTIC_ENDPOINT is correct:**
   ```bash
   # Test from your machine
   curl -H "Authorization: ApiKey $ELASTIC_API_KEY" "$ELASTIC_ENDPOINT"
   ```

3. **Check the NOVA-7 app logs for OTLP errors:**
   ```bash
   docker compose logs nova7 | grep -i "otlp\|send failed"
   ```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Wrong ELASTIC_ENDPOINT | Must include port (e.g., `:443`). Check Elastic Cloud console. |
| Invalid ELASTIC_API_KEY | Regenerate the key in Kibana > Stack Management > API Keys |
| API key lacks permissions | Key needs write access to `logs-*`, `metrics-*`, `traces-*` |
| OTel Collector cannot reach Elastic | Check firewall rules, VPN, proxy settings |
| Network timeout | Increase collector timeout in `otel-collector-config.yaml` |

### OTLP send failures in app logs

**Symptoms:** Repeated "OTLP logs send failed" or "OTLP metrics send failed" messages.

**Solution:** The NOVA-7 app sends to the OTel Collector, not directly to Elastic. Verify:
```bash
# Is the collector running?
docker compose ps otel-collector

# Can nova7 reach it?
docker compose exec nova7 curl -s http://otel-collector:4318/v1/logs
```

### Data arrives but with wrong format

**Symptoms:** Data is in Elastic but fields are missing or incorrectly mapped.

**Solution:** Ensure the OTel Collector config uses ECS mapping:
```yaml
exporters:
  elasticsearch:
    mapping:
      mode: ecs
```

---

## 3. Dashboard Issues

### Dashboard page is blank

**Symptoms:** Navigating to `/dashboard` shows a white page.

**Solutions:**
- Hard refresh the browser (Ctrl+Shift+R / Cmd+Shift+R)
- Check browser console for JavaScript errors (F12 > Console)
- Verify static files are being served: `curl http://localhost:8080/dashboard/static/app.js`

### WebSocket connection fails

**Symptoms:** Dashboard loads but does not update in real time. Browser console shows WebSocket errors.

**Solutions:**
- Check that WebSocket connections are not blocked by a proxy or firewall
- Verify the WebSocket endpoint: `ws://localhost:8080/ws/dashboard`
- If behind a reverse proxy, ensure it supports WebSocket upgrades

### Dashboard shows stale data

**Symptoms:** Services remain in a previous state after triggering or resolving faults.

**Solution:** The dashboard updates via WebSocket push events. If the connection dropped:
1. Refresh the page
2. Check `docker compose logs nova7` for WebSocket errors

---

## 4. Chaos Controller Issues

### Channel trigger has no effect

**Symptoms:** Triggering a channel via API or UI does not change the dashboard or generate error logs.

**Diagnosis:**
```bash
# Check channel status
curl -s http://localhost:8080/api/chaos/status/2 | python3 -m json.tool

# Trigger and check response
curl -s -X POST http://localhost:8080/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}' | python3 -m json.tool
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Channel already active | Check status first; resolve before re-triggering |
| Invalid channel number | Must be 1-20 |
| Service not running | Check `docker compose ps` and app logs |

### Channel will not resolve

**Symptoms:** Calling the resolve API returns success but the channel stays active.

**Solution:**
```bash
# Use the resolve endpoint directly
curl -X POST http://localhost:8080/api/chaos/resolve \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}'

# Or use the remediate endpoint
curl -X POST http://localhost:8080/api/remediate/2
```

If it still persists, restart the container:
```bash
docker compose restart nova7
```

---

## 5. Notification Issues

### SMS not sending

**Symptoms:** `send_sms()` returns `{"sent": false}` or logs an error.

**Diagnosis checklist:**

- [ ] `TWILIO_ACCOUNT_SID` is set and starts with `AC`
- [ ] `TWILIO_AUTH_TOKEN` is set
- [ ] `TWILIO_FROM_NUMBER` is a valid Twilio number in E.164 format (+1XXXXXXXXXX)
- [ ] `TWILIO_TO_NUMBER` is a verified number (required for trial accounts)
- [ ] Twilio account has sufficient balance

**Test from the command line:**
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
  --data-urlencode "Body=NOVA-7 test message" \
  --data-urlencode "From=$TWILIO_FROM_NUMBER" \
  --data-urlencode "To=$TWILIO_TO_NUMBER" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"
```

### Voice call not connecting

**Symptoms:** Call API returns success but the phone never rings.

**Common causes:**

| Cause | Solution |
|-------|----------|
| TwiML URL not publicly accessible | Use ngrok, a public server, or Twilio TwiML Bins |
| Twilio cannot fetch the TwiML | Check the URL returns valid XML with `curl` |
| Destination number not verified | On trial accounts, add the number to verified callers |

### Slack webhook not posting

**Symptoms:** `send_slack_alert()` returns an error.

**Diagnosis:**

```bash
# Test the webhook directly
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"text": "NOVA-7 test alert"}'
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Webhook URL is invalid or expired | Create a new webhook in the Slack app settings |
| Channel was deleted or archived | Re-add the webhook to an active channel |
| Slack app was uninstalled | Reinstall the app in your workspace |
| Network/firewall blocks outbound | Ensure the container can reach `hooks.slack.com` |

---

## 6. Elastic / Kibana Issues

### Cannot find NOVA-7 data in Discover

**Symptoms:** Kibana Discover shows no results for NOVA-7 logs.

**Solutions:**

1. Create or select the correct data view:
   - Go to **Stack Management** > **Data Views**
   - Create a new data view: `logs-*`
   - Set the time field to `@timestamp`

2. Check the time range in Discover — make sure it includes "now"

3. Verify data exists:
   ```
   GET logs-generic-default/_count
   ```

### Significant event rules not firing

**Symptoms:** Faults are triggered and errors appear in Kibana, but no alerts fire.

**Check:**
- Rule is enabled in **Security** > **Rules**
- Rule schedule interval is short enough (1 minute recommended)
- The ES|QL query matches the actual field names in your data
- Time window in the query covers the fault duration

### ES|QL query returns no results

**Symptoms:** Running the detection query manually returns empty.

**Debug approach:**
```esql
-- Start broad, then narrow
FROM logs-*
| WHERE service.namespace == "nova7"
| LIMIT 10

-- Add the error filter
FROM logs-*
| WHERE service.namespace == "nova7" AND severity_text == "ERROR"
| LIMIT 10

-- Add the specific error type
FROM logs-*
| WHERE service.namespace == "nova7" AND error.type == "FuelPressureException"
| LIMIT 10
```

---

## 7. Docker Issues

### Docker Compose version mismatch

**Symptoms:** `docker compose` commands fail with syntax errors.

**Solutions:**
- Docker Compose V2 (plugin): Use `docker compose` (no hyphen)
- Docker Compose V1 (standalone): Use `docker-compose` (with hyphen)
- The setup and teardown scripts try both automatically

### Container cannot resolve DNS

**Symptoms:** OTel Collector logs show DNS resolution failures.

**Solution:**
```bash
# Check Docker DNS
docker compose exec otel-collector nslookup your-elastic-endpoint.es.cloud.es.io

# If DNS fails, add a DNS server to docker-compose.yml:
# services:
#   otel-collector:
#     dns:
#       - 8.8.8.8
```

### Out of disk space

**Symptoms:** Docker build fails or containers crash with I/O errors.

**Solution:**
```bash
# Check disk usage
df -h

# Clean up Docker resources
docker system prune -f
docker volume prune -f
```

---

## 8. Performance Issues

### High CPU usage

**Symptoms:** The NOVA-7 container uses excessive CPU.

**Cause:** Nine services each emit telemetry every 1.5-3 seconds. This is normal but can be adjusted.

**Solution:** The emission interval is controlled in `app/services/base_service.py`:
```python
interval = random.uniform(1.5, 3.0)  # Increase these values to reduce CPU
```

### OTel Collector memory growing

**Symptoms:** The collector container's memory usage increases over time.

**Solution:** The collector config includes a memory limiter:
```yaml
processors:
  memory_limiter:
    limit_mib: 256
    check_interval: 1s
```

If 256 MiB is not enough, increase the limit. If it is still growing, check for export backpressure (slow Elastic endpoint).

### Slow Elastic ingestion

**Symptoms:** Data appears in Kibana with significant delay (more than 30 seconds).

**Common causes:**

| Cause | Solution |
|-------|----------|
| Elastic cluster is overloaded | Scale up or reduce telemetry volume |
| Collector batch size too large | Reduce `send_batch_size` in collector config |
| Network latency to Elastic Cloud | Choose a closer cloud region |
| Index refresh interval | Default is 1s; should be fine for demos |

---

## Getting Help

If none of the above resolves your issue:

1. Collect diagnostic information:
   ```bash
   docker compose ps
   docker compose logs --tail 100 nova7
   docker compose logs --tail 100 otel-collector
   curl -s http://localhost:8080/api/status | python3 -m json.tool
   ```

2. Check the version:
   ```bash
   docker compose version
   docker --version
   python3 --version
   ```

3. Open an issue with the diagnostic output attached.
