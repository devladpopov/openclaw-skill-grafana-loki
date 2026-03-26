#!/bin/bash
# Domain expiry & hosting balance monitor
# Pushes metrics to Prometheus Pushgateway
# Cron: 0 6 * * * /path/to/check_domains.sh >> /var/log/domain-monitor.log 2>&1

PUSHGATEWAY="${PUSHGATEWAY_URL:-http://localhost:9091}"

# Add your domains here
declare -A DOMAINS=(
  # ["example.com"]="2027-01-15"
)

# Add your hosting API check here
# FALCON_RESPONSE=$(curl -s -X GET "$HOSTING_API_URL" -H "x-api-key: $HOSTING_API_KEY")

NOW=$(date +%s)
METRICS=""

for domain in "${!DOMAINS[@]}"; do
  expiry_date=""
  whois_output=$(whois "$domain" 2>/dev/null)
  
  if [ -n "$whois_output" ]; then
    expiry_date=$(echo "$whois_output" | grep -iE "paid-till|Registry Expiry Date|Expiration Date|Expiry date|renewal date" | head -1 | grep -oE '[0-9]{4}[-/.][0-9]{2}[-/.][0-9]{2}(T[0-9:]+Z?)?' | head -1)
  fi
  
  if [ -z "$expiry_date" ]; then
    expiry_date="${DOMAINS[$domain]}"
  fi
  
  if [ -n "$expiry_date" ]; then
    clean_date=$(echo "$expiry_date" | sed 's/[/.]/-/g' | cut -dT -f1)
    expiry_ts=$(date -d "$clean_date" +%s 2>/dev/null)
    if [ -n "$expiry_ts" ]; then
      days_left=$(( (expiry_ts - NOW) / 86400 ))
      METRICS="${METRICS}domain_expiry_days{domain=\"${domain}\"} ${days_left}\n"
      echo "  $domain: ${days_left} days left (expires $clean_date)"
    fi
  fi
done

echo "Pushing metrics..."
echo -e "$METRICS" | curl -s --data-binary @- "${PUSHGATEWAY}/metrics/job/domain_monitor"
echo "Done."
