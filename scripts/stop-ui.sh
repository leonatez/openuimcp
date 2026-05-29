#!/usr/bin/env bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$SKILL_DIR/.logs"

_kill() {
  local name="$1" pid_file="$2"
  if [ -f "$pid_file" ]; then
    kill "$(cat "$pid_file")" 2>/dev/null && echo "[visualize-ui] $name stopped."
    rm "$pid_file"
  else
    echo "[visualize-ui] No running $name found."
  fi
}

_kill "Frontend" "$LOG_DIR/frontend.pid"
_kill "Relay"    "$LOG_DIR/relay.pid"
