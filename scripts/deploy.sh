#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-3001}"
SERVER_LOG=$(mktemp)
TUNNEL_LOG=$(mktemp)
SERVER_PID=""
TUNNEL_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$SERVER_PID" "$TUNNEL_PID" 2>/dev/null || true
  rm -f "$SERVER_LOG" "$TUNNEL_LOG"
  echo "Done."
}
trap cleanup EXIT INT TERM

# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Preflight: need a tunnel tool
TUNNEL_CMD=""
TUNNEL_NAME=""
if command -v cloudflared &>/dev/null; then
  TUNNEL_CMD="cloudflared tunnel --url http://localhost:$PORT"
  TUNNEL_NAME="cloudflared"
elif command -v ngrok &>/dev/null; then
  TUNNEL_CMD="ngrok http $PORT --log=stdout"
  TUNNEL_NAME="ngrok"
else
  echo "❌ No tunnel tool found. Install one:"
  echo "     brew install cloudflared"
  exit 1
fi

# 1. Start server
echo "▶  Starting server on port $PORT ..."
npm start > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "⏳ Waiting for http://localhost:$PORT/api/health ..."
for i in $(seq 1 15); do
  sleep 1
  if curl -sf "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
    echo "✅ Server is up."
    break
  fi
done
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "❌ Server failed to start. Log:" >&2
  cat "$SERVER_LOG" >&2
  exit 1
fi

# 2. Start tunnel
echo "▶  Starting $TUNNEL_NAME tunnel ..."
$TUNNEL_CMD > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
echo "⏳ Waiting for tunnel URL ..."
PUBLIC_URL=""
for i in $(seq 1 30); do
  sleep 1
  if [ "$TUNNEL_NAME" = "cloudflared" ]; then
    PUBLIC_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
  else
    TUNNEL_DATA=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null || true)
    PUBLIC_URL=$(echo "$TUNNEL_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])" 2>/dev/null || true)
  fi
  if [ -n "$PUBLIC_URL" ]; then
    break
  fi
done

if [ -z "$PUBLIC_URL" ]; then
  echo "❌ Could not obtain public URL. Tunnel log:" >&2
  tail -n 10 "$TUNNEL_LOG" >&2
  exit 1
fi

# 3. Print and verify
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "  🌍 Public URL:   $PUBLIC_URL"
echo "  ❤️  Health:       $PUBLIC_URL/api/health"
echo "  🎵 Scrobbles:    $PUBLIC_URL/api/scrobbles?user=elias_fisch"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "⏳ Verifying public health endpoint ..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$PUBLIC_URL/api/health" 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
  echo "✅ Public health check: $HEALTH"
else
  echo "⚠️  Public health check returned: $HEALTH"
fi

echo ""
echo "Press Ctrl-C to stop the server and tunnel."
wait
