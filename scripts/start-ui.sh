#!/usr/bin/env bash
# Per-session startup: check ports, start Next.js frontend, open browser.
# Usage: start-ui.sh [project_dir]
set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PORT="${BRAINSTORM_APP_PORT:-3000}"
MCP_PORT="${BRAINSTORM_MCP_PORT:-8765}"
PROJECT_DIR="${1:-$(pwd)}"
LOG_DIR="$SKILL_DIR/.logs"
mkdir -p "$LOG_DIR"

# Export project root so MCP server sandboxes file access to this directory
export BRAINSTORM_PROJECT_ROOT="$PROJECT_DIR"

# --- Verify WebSocket server (MCP server managed by Claude Code via stdio) ---
if ! nc -z localhost "$MCP_PORT" 2>/dev/null; then
  echo "[brainstorm-ui] WARNING: MCP WebSocket not reachable on port $MCP_PORT."
  echo "[brainstorm-ui] Ensure Claude Code loaded the 'brainstorm-ui' MCP server."
  echo "[brainstorm-ui] If first run: execute scripts/setup.sh then restart Claude Code."
fi

# --- Start Next.js frontend (idempotent) ---
if nc -z localhost "$APP_PORT" 2>/dev/null; then
  echo "[brainstorm-ui] Frontend already running on port $APP_PORT."
else
  echo "[brainstorm-ui] Starting Next.js frontend on port $APP_PORT..."
  cd "$SKILL_DIR/app"
  NEXT_PUBLIC_MCP_WS_PORT="$MCP_PORT" \
    npm run dev -- --port "$APP_PORT" \
    > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$LOG_DIR/frontend.pid"

  echo -n "[brainstorm-ui] Waiting for frontend"
  FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid" 2>/dev/null)
  for _ in $(seq 1 20); do
    nc -z localhost "$APP_PORT" 2>/dev/null && break
    # Abort if process died
    if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
      echo ""
      echo "[brainstorm-ui] ERROR: Frontend process exited early. Check logs: $LOG_DIR/frontend.log"
      exit 1
    fi
    sleep 1
    echo -n "."
  done
  echo " ready."
fi

# --- Open browser with project context ---
ENCODED_PROJECT="$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$PROJECT_DIR")"
URL="http://localhost:${APP_PORT}?project=${ENCODED_PROJECT}"
echo "[brainstorm-ui] Opening: $URL"

if command -v xdg-open &>/dev/null; then
  xdg-open "$URL" &>/dev/null &
elif command -v open &>/dev/null; then
  open "$URL"
else
  echo "[brainstorm-ui] Open manually: $URL"
fi

echo "[brainstorm-ui] UI active. Chat in terminal as normal."
echo "[brainstorm-ui] Logs: $LOG_DIR/frontend.log"
