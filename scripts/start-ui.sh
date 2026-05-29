#!/usr/bin/env bash
# Per-session startup: start relay + Next.js frontend, open browser.
# Usage: start-ui.sh [project_dir]
set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PORT="${VISUALIZE_APP_PORT:-3001}"
WS_PORT="${VISUALIZE_MCP_PORT:-8766}"
HTTP_PORT="${VISUALIZE_HTTP_PORT:-8767}"
PROJECT_DIR="${1:-$(pwd)}"
LOG_DIR="$SKILL_DIR/.logs"
mkdir -p "$LOG_DIR"

# Detect Python (prefer venv)
PYTHON="$SKILL_DIR/.venv/bin/python3"
if [ ! -x "$PYTHON" ]; then
  PYTHON="$(command -v python3 || command -v python)"
fi
if [ -z "$PYTHON" ]; then
  echo "[visualize-ui] ERROR: python3 not found. Run scripts/setup.sh first." >&2
  exit 1
fi

# ── Start relay (idempotent) ──────────────────────────────────────────────
if nc -z localhost "$WS_PORT" 2>/dev/null && nc -z localhost "$HTTP_PORT" 2>/dev/null; then
  echo "[visualize-ui] Relay already running (WS :$WS_PORT  HTTP :$HTTP_PORT)."
else
  echo "[visualize-ui] Starting relay..."
  VISUALIZE_PROJECT_ROOT="$PROJECT_DIR" \
  VISUALIZE_MCP_PORT="$WS_PORT" \
  VISUALIZE_HTTP_PORT="$HTTP_PORT" \
    "$PYTHON" "$SKILL_DIR/scripts/relay.py" \
    > "$LOG_DIR/relay.log" 2>&1 &
  echo $! > "$LOG_DIR/relay.pid"

  echo -n "[visualize-ui] Waiting for relay"
  for _ in $(seq 1 15); do
    nc -z localhost "$WS_PORT" 2>/dev/null && nc -z localhost "$HTTP_PORT" 2>/dev/null && break
    sleep 1
    echo -n "."
  done

  if ! nc -z localhost "$WS_PORT" 2>/dev/null; then
    echo ""
    echo "[visualize-ui] ERROR: Relay failed to start. Check: $LOG_DIR/relay.log" >&2
    exit 1
  fi
  echo " ready."
fi

# ── Start Next.js frontend (idempotent) ───────────────────────────────────
if nc -z localhost "$APP_PORT" 2>/dev/null; then
  echo "[visualize-ui] Frontend already running on port $APP_PORT."
else
  echo "[visualize-ui] Starting Next.js frontend on port $APP_PORT..."
  cd "$SKILL_DIR/app"
  NEXT_PUBLIC_MCP_WS_PORT="$WS_PORT" \
    npm run dev -- --port "$APP_PORT" \
    > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$LOG_DIR/frontend.pid"

  echo -n "[visualize-ui] Waiting for frontend"
  FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid" 2>/dev/null)
  for _ in $(seq 1 20); do
    nc -z localhost "$APP_PORT" 2>/dev/null && break
    if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
      echo ""
      echo "[visualize-ui] ERROR: Frontend process exited early. Check: $LOG_DIR/frontend.log" >&2
      exit 1
    fi
    sleep 1
    echo -n "."
  done
  echo " ready."
fi

# ── Open browser with project context ─────────────────────────────────────
ENCODED_PROJECT="$("$PYTHON" -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$PROJECT_DIR")"
URL="http://localhost:${APP_PORT}?project=${ENCODED_PROJECT}"
echo "[visualize-ui] Opening: $URL"

if command -v xdg-open &>/dev/null; then
  xdg-open "$URL" &>/dev/null &
elif command -v open &>/dev/null; then
  open "$URL"
else
  echo "[visualize-ui] Open manually: $URL"
fi

echo "[visualize-ui] UI active. Relay: HTTP :$HTTP_PORT  WS :$WS_PORT"
echo "[visualize-ui] Logs: $LOG_DIR/"
