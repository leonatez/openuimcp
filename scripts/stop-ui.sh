#!/usr/bin/env bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$SKILL_DIR/.logs/frontend.pid"
if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null && echo "[brainstorm-ui] Frontend stopped."
  rm "$PID_FILE"
else
  echo "[brainstorm-ui] No running frontend found."
fi
