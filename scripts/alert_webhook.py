#!/usr/bin/env python3
"""
Grafana Alert Webhook with Loki enrichment.

Receives Grafana webhook alerts, fetches error text from Loki,
cross-references with nginx access logs for IP/URL/UA context,
sends consolidated message to Telegram.

Configure via environment variables:
  LOKI_URL, TG_TOKEN, TG_CHAT_ID, MAX_ERROR_LEN, GRAFANA_URL, PUSHGATEWAY_URL, PORT

Docker: python -u alert_webhook.py (listens on PORT, default 8090)

Endpoints:
  POST /        — Grafana webhook receiver
  GET  /domains — domain expiry + hosting balance (JSON)
  GET  /health  — health check
"""

# See the full implementation in references/alert_webhook_example.py
# This is a template — customize for your setup.

import os

PORT = int(os.environ.get("PORT", "8090"))
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# Full implementation handles:
# 1. POST webhook from Grafana with alerts
# 2. Fetches last N ERROR lines from Loki
# 3. Fetches nginx 4xx/5xx logs for IP/URL/UA context
# 4. Deduplicates and consolidates into single Telegram message
# 5. GET /domains returns domain expiry + hosting balance from Pushgateway
