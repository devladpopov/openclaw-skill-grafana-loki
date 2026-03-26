# OpenClaw Skill: Grafana Loki Monitoring

AgentSkill for managing infrastructure monitoring via Grafana, Prometheus, Loki, and Pushgateway APIs.

## Features

- Create, update, pause/unpause Grafana alert rules via API
- Query logs from Loki (application errors, fail2ban bans, nginx access)
- Check server metrics from Prometheus (CPU, RAM, Disk, Uptime)
- Monitor domain expiry via WHOIS + Pushgateway
- Monitor hosting balance via provider API + Pushgateway
- Investigate production errors with enriched context (log text + nginx IP/URL/UA)
- Daily morning report to Telegram
- Telegram bot commands (/status, /domains, /balance)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────┐
│  App Servers │────▶│   Promtail   │────▶│  Loki   │
│  (prod/stg)  │     │  (per server) │     │         │
└─────────────┘     └──────────────┘     └────┬────┘
                                               │
┌─────────────┐     ┌──────────────┐     ┌────▼────┐
│ Node Exporter│────▶│  Prometheus  │────▶│ Grafana │
│  (per server) │     │              │     │         │
└─────────────┘     └──────────────┘     └────┬────┘
                                               │
┌─────────────┐     ┌──────────────┐     ┌────▼────┐
│ Cron Scripts │────▶│ Pushgateway  │     │ Alert   │
│ (domains,   │     │              │     │ Webhook │──▶ Telegram
│  balance)   │     └──────────────┘     └─────────┘
└─────────────┘
```

## Installation

```bash
# Copy skill to your OpenClaw workspace
cp -r ixparcel-monitoring/ ~/.openclaw/workspace/skills/

# Set up credentials
mkdir -p ~/.openclaw/secrets
cat > ~/.openclaw/secrets/monitoring.env << 'ENVEOF'
MONITORING_HOST=your-monitoring-server-ip
GRAFANA_URL=https://your-grafana-domain
GRAFANA_USER=admin
GRAFANA_PASS=your-grafana-password
LOKI_URL=http://loki:3100
PROMETHEUS_URL=http://prometheus:9090
PUSHGATEWAY_URL=http://localhost:9091
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id
ENVEOF
chmod 600 ~/.openclaw/secrets/monitoring.env
```

## What the Agent Can Do

### Alert Management
- Create alert rules (Loki log queries, Prometheus metrics)
- Update thresholds, evaluation intervals, pending periods
- Pause/unpause rules
- Configure notification policies (rate limiting, grouping)
- Set up contact points (Telegram, Webhook)

### Log Investigation
- Query Loki for recent errors with LogQL
- Cross-reference Laravel errors with nginx access logs (IP, URL, User-Agent)
- Search fail2ban bans by jail, IP, action
- Filter by host, level, job, time range

### Metrics & Monitoring
- Query Prometheus for server health (CPU, RAM, Disk)
- Check SSL certificate expiry
- Monitor HTTP endpoint availability
- Track domain expiry dates via WHOIS
- Track hosting provider balance via API

### Reporting
- Daily morning summary to Telegram (servers, sites, domains, balance, error count)
- On-demand status via Telegram bot commands

## Promtail Log Pipeline

The skill configures Promtail with smart log parsing:

| Job | Source | Parsing |
|-----|--------|---------|
| `laravel` | App log files | `[timestamp] env.LEVEL:` → labels: level, env |
| `docker` | Container stdout | HTTP status code regex → 5xx = level=ERROR |
| `system` | syslog, auth.log | Regex for error/crit/alert/emerg |
| `fail2ban` | fail2ban.log | Regex → labels: jail, action (Ban/Unban/Found), level |

## Alert Webhook

The included `alert-webhook` container receives Grafana webhooks and enriches alerts:

1. Grafana fires alert → sends webhook to alert-webhook container
2. Webhook queries Loki for actual error text
3. Webhook queries nginx Docker logs for IP/URL/User-Agent context
4. Sends single consolidated Telegram message with all details

## Grafana API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/provisioning/alert-rules` | GET/POST | List/create alert rules |
| `/api/v1/provisioning/alert-rules/{uid}` | GET/PUT | Get/update specific rule |
| `/api/v1/provisioning/policies` | GET/PUT | Notification policy |
| `/api/v1/provisioning/contact-points` | GET/POST/PUT | Contact points |
| `/api/v1/provisioning/templates` | GET/PUT | Message templates |
| `/api/alertmanager/grafana/api/v2/alerts` | GET | Currently firing alerts |

## Requirements

- Grafana OSS >= 9.x with built-in alerting
- Prometheus
- Loki + Promtail (on each monitored server)
- Pushgateway (for cron-based metrics)
- Docker (all components run in containers)
- Python 3.12+ (for alert-webhook and daily report)

## Author

**Vladislav Popov** — [vladislavpopov.ru](https://vladislavpopov.ru) | [GitHub](https://github.com/devladpopov)

Built for [OpenClaw](https://openclaw.ai) AI agent platform.

## License

MIT
