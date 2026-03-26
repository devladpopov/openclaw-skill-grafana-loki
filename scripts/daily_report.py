#!/usr/bin/env python3
"""
Daily Morning Report — collects metrics from Prometheus, Loki, Pushgateway
and sends a summary to Telegram.

Configure via environment variables:
  PROMETHEUS_URL, LOKI_URL, PUSHGATEWAY_URL, TG_TOKEN, TG_CHAT_ID, GRAFANA_URL

Cron example: 0 5 * * * docker exec alert-webhook python /app/daily_report.py
"""

# See the full implementation in references/daily_report_example.py
# This is a template — customize SERVERS, SITES, and timezone for your setup.

import os
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone, timedelta

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://pushgateway:9091")
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "https://status.example.com")

# Customize these for your infrastructure
SERVERS = [
    # {"instance": "1.2.3.4:9100", "label": "prod-app"},
]

SITES = [
    # "https://example.com/health",
]


def prom_query(expr):
    url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(expr)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        if data["status"] == "success":
            return data["data"]["result"]
    except Exception as e:
        print(f"Prometheus query failed: {e}")
    return []


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


# Add your report building logic here
# See references/ for full example
