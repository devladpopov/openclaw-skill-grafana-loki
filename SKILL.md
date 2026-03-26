# Grafana Loki Monitoring Skill

## Description
Manage infrastructure monitoring via Grafana, Prometheus, Loki, and Pushgateway APIs. Create alert rules, query logs, check metrics, investigate production errors with enriched context, send daily reports to Telegram.

## When to Use
- Create, update, pause/unpause Grafana alert rules
- Query logs from Loki (application errors, fail2ban bans, nginx access)
- Check server metrics (CPU, RAM, Disk, Uptime)
- Monitor domain expiry and hosting balance
- Investigate production errors (fetch log context + nginx IP/URL/UA)
- Send daily reports or ad-hoc status checks

## Configuration

Environment variables (loaded from `~/.openclaw/secrets/monitoring.env`):
```
MONITORING_HOST=your-monitoring-server-ip
GRAFANA_USER=admin
GRAFANA_PASS=your-grafana-password
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id
```

Before any operation, source the env file:
```bash
source ~/.openclaw/secrets/monitoring.env
```

## Architecture

### Monitoring Server
- SSH: `ssh -T -i ~/.ssh/id_ed25519 root@$MONITORING_HOST`
- Docker containers: prometheus, grafana, loki, pushgateway, blackbox, alert-webhook, nginx

### Internal Endpoints (from monitoring server)
- Grafana API: `http://<grafana-container-ip>:3000` (Basic Auth)
- Loki API: via `docker exec loki wget -qO- 'http://localhost:3100/...'`
- Prometheus API: via `docker exec prometheus wget -qO- 'http://localhost:9090/...'`
- Pushgateway: `http://localhost:9091`

### Promtail (on app servers)
- Config: `/opt/promtail/config.yml` on each server
- Jobs: laravel, docker, system, fail2ban
- See `references/promtail-config-example.yml` for full config

### Telegram Notifications
- Bot token and chat ID configured via env vars
- Alert webhook enriches errors with Loki text + nginx context

## Common Operations

### Query recent errors from Loki
```bash
ssh root@$MONITORING_HOST "docker exec loki wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bhost=%22prod-app%22,+level=%22ERROR%22%7D&limit=5&since=1h'"
```

### Create/update Grafana alert rule
```bash
ssh root@$MONITORING_HOST "curl -s -X POST \
  -u '$GRAFANA_USER:$GRAFANA_PASS' \
  -H 'Content-Type: application/json' \
  -d @/tmp/alert.json \
  'http://<grafana-ip>:3000/api/v1/provisioning/alert-rules'"
```

### Update promtail config
```bash
scp -P 2222 config.yml root@$APP_HOST:/opt/promtail/config.yml
ssh -p 2222 root@$APP_HOST "docker restart promtail"
```

### Run daily report manually
```bash
ssh root@$MONITORING_HOST "docker exec alert-webhook python /app/daily_report.py"
```

### Check domain/balance metrics
```bash
ssh root@$MONITORING_HOST "curl -s http://localhost:9091/metrics | grep -E 'domain_expiry|hosting_balance' | grep -v '^#'"
```

## Grafana API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/provisioning/alert-rules` | GET/POST | List/create alert rules |
| `/api/v1/provisioning/alert-rules/{uid}` | GET/PUT | Get/update specific rule |
| `/api/v1/provisioning/policies` | GET/PUT | Notification policy |
| `/api/v1/provisioning/contact-points` | GET/POST/PUT | Contact points |
| `/api/alertmanager/grafana/api/v2/alerts` | GET | Currently firing alerts |

## Loki LogQL Examples

```
# All errors on prod
{host="prod-app", level="ERROR"}

# fail2ban bans
{job="fail2ban", action="Ban"}

# fail2ban by jail
{job="fail2ban", jail="sshd"}

# nginx 5xx in docker logs
{host="prod-app", job="docker", level="ERROR"}

# Count errors over time
count_over_time({host="prod-app", level="ERROR"} [5m])
```

## Notification Policy Settings

Recommended rate-limit:
- group_wait: 2m (first alert after 2 min)
- group_interval: 15m (repeat not more than every 15 min)
- repeat_interval: 1h (remind about unresolved issues hourly)
- disableResolveMessage: true (no RESOLVED spam)

## Cron Jobs

| Schedule | Task |
|----------|------|
| `0 5 * * *` | Daily report (08:00 MSK / 09:00 Dubai) |
| `0 6 * * *` | Domain expiry + hosting balance check |

## Files on Monitoring Server

- `/opt/monitoring/docker-compose.yml` — all containers
- `/opt/monitoring/prometheus/prometheus.yml` — scrape config
- `/opt/monitoring/alert-webhook/app.py` — webhook + /domains endpoint
- `/opt/monitoring/alert-webhook/daily_report.py` — morning report
- `/opt/monitoring/scripts/check_domains.sh` — WHOIS + balance
- `/opt/monitoring/nginx/conf.d/grafana.conf` — nginx reverse proxy
