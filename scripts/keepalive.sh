#!/usr/bin/env bash
# keepalive.sh — ping Dreams Atlas /healthz to prevent Render free-tier cold starts
# Run manually: bash scripts/keepalive.sh
# Or via GitHub Actions cron (see .github/workflows/keepalive.yml)

set -euo pipefail

DEMO_URL="${DEMO_URL:-https://dreams-atlas.onrender.com}"
HEALTHZ="${DEMO_URL}/healthz"
MAX_WAIT=90

echo "[keepalive] pinging ${HEALTHZ}"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$MAX_WAIT" "$HEALTHZ" || true)

if [ "$STATUS" = "200" ]; then
  echo "[keepalive] OK (HTTP 200)"
else
  echo "[keepalive] WARN: got HTTP ${STATUS} — site may be cold or down"
  exit 1
fi
