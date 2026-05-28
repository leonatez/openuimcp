#!/usr/bin/env bash
set -e
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$HOME/.claude/skills/.venv/bin/python3"

echo "[brainstorm-ui] Installing Python dependencies..."
"$VENV_PYTHON" -m pip install -r "$SKILL_DIR/server/requirements.txt" -q

echo "[brainstorm-ui] Scaffolding Next.js app (first run only)..."
if [ ! -d "$SKILL_DIR/app" ]; then
  cd "$SKILL_DIR"
  npx @openuidev/cli@latest create --name app --yes 2>/dev/null || true
  if [ -d "$SKILL_DIR/app" ]; then
    cd "$SKILL_DIR/app" && npm install -q
  fi
else
  echo "[brainstorm-ui] app/ already exists, skipping scaffold."
fi

echo "[brainstorm-ui] Registering MCP server in Claude Code settings..."
"$VENV_PYTHON" - <<PYEOF
import json, os, sys

settings_path = os.path.expanduser("~/.claude/settings.json")
skill_dir = os.path.expanduser("~/.claude/skills/brainstorm")
venv_python = os.path.expanduser("~/.claude/skills/.venv/bin/python3")

if not os.path.exists(settings_path):
    print(f"[brainstorm-ui] settings.json not found at {settings_path}, skipping registration.")
    sys.exit(0)

with open(settings_path) as f:
    settings = json.load(f)

settings.setdefault("mcpServers", {})
settings["mcpServers"]["brainstorm-ui"] = {
    "command": venv_python,
    "args": [os.path.join(skill_dir, "server", "mcp-server.py")],
    "env": {}
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("[brainstorm-ui] MCP server registered as 'brainstorm-ui'.")
print("[brainstorm-ui] Restart Claude Code to activate the MCP server.")
PYEOF

echo "[brainstorm-ui] Setup complete."
