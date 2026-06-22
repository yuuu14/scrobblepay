#!/usr/bin/env bash
#
# ScrobblePay — deploy.sh (SCR-002)
# Starts the TS server and exposes it publicly via ngrok, then prints the
# public URL and verifies /api/health returns 200 through the tunnel.
#
# Usage:   PORT=3000 ./scripts/deploy.sh
# Stop:    Ctrl-C  (tears down both the server and ngrok)
#
set -euo pipefail

PORT="${PORT:-3001}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGROK_API="http://localhost:4040/api/tunnels"

SERVER_PID=""
NGROK_PID=""

cleanup() {
  echo
  echo "Shutting down..."
  [ -n "$NGROK_PID" ]  && kill "$NGROK_PID"  2>/dev/null || true
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 1. Preflight: ngrok must be installed
if ! command -v ngrok >/dev/null 2>&1; then
  echo "❌ ngrok is not installed. Install it with:" >&2
  echo "     brew install ngrok" >&2
  echo "   then configure your authtoken once:" >&2
  echo "     ngrok config add-authtoken <token>   (https://dashboard.ngrok.com)" >&2
  exit 1
fi


# Load .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
# 2. Start the server (inherits PORT from env)
echo "▶  Starting server on port $PORT ..."
( cd "$ROOT_DIR" && PORT="$PORT" npm start ) &
SERVER_PID=$!

# 3. Wait for the server to become healthy
echo "⏳ Waiting for http://localhost:$PORT/api/health ..."
for i in $(seq 1 15); do
  if curl -fsS "http://localhost:$PORT/api/health" >/dev/null 2>&1; then
    echo "✅ Server is up."
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "❌ Server process exited before becoming healthy." >&2
    exit 1
  fi
  if [ "$i" -eq 15 ]; then
    echo "❌ Server did not become healthy in time." >&2
    exit 1
  fi
  sleep 1
done

# 4. Start ngrok tunnel
echo "▶  Starting ngrok tunnel ..."
ngrok http "$PORT" --log=stdout >/tmp/scrobblepay-ngrok.log 2>&1 &
NGROK_PID=$!

# 5. Resolve the public URL from ngrok's local API (jq-free JSON parse via python3)
PUBLIC_URL=""
for i in $(seq 1 15); do
  PUBLIC_URL="$(curl -fsS "$NGROK_API" 2>/dev/null \
    | python3 -c 'import sys,json
try:
    t=json.load(sys.stdin).get("tunnels",[])
    print(next((x["public_url"] for x in t if x.get("public_url","").startswith("https")), t[0]["public_url"] if t else ""))
except Exception:
    print("")' 2>/dev/null || true)"
  if [ -n "$PUBLIC_URL" ]; then
    break
  fi
  if ! kill -0 "$NGROK_PID" 2>/dev/null; then
    echo "❌ ngrok exited. Last log lines:" >&2
    tail -n 20 /tmp/scrobblepay-ngrok.log >&2 || true
    echo "   (If you see ERR_NGROK_4018, run: ngrok config add-authtoken <token>)" >&2
    exit 1
  fi
  sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
  echo "❌ Could not obtain public URL from ngrok." >&2
  tail -n 20 /tmp/scrobblepay-ngrok.log >&2 || true
  exit 1
fi

# 6. Print the public URL
echo
echo "╔══════════════════════════════════════════════════════════╗"
echo "  🌍 Public URL:   $PUBLIC_URL"
echo "  ❤️  Health:       $PUBLIC_URL/api/health"
echo "  🎵 Scrobbles:    $PUBLIC_URL/api/scrobbles"
echo "╚══════════════════════════════════════════════════════════╝"
echo

# 7. Verify /api/health returns 200 through the public URL
echo "⏳ Verifying public health endpoint ..."
CODE="$(curl -s -o /dev/null -w '%{http_code}' "$PUBLIC_URL/api/health")"
if [ "$CODE" = "200" ]; then
  echo "✅ Public health check: $CODE"
else
  echo "⚠️  Public health check returned: $CODE (expected 200)" >&2
fi

echo
echo "Press Ctrl-C to stop the server and tunnel."
wait "$SERVER_PID"
