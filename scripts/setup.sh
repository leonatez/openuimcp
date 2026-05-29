#!/usr/bin/env bash
# setup.sh — Install the visualize skill into ~/.claude/skills/visualize/
# Run once after cloning: bash scripts/setup.sh
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="visualize"
INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
VENV_DIR="$HOME/.claude/skills/.venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
SETTINGS_PATH="$HOME/.claude/settings.json"

echo "[visualize] ============================================"
echo "[visualize]  Visualize Skill Setup"
echo "[visualize] ============================================"

# ── 1. Python venv ────────────────────────────────────────────────────────────
echo ""
echo "[visualize] Step 1/5: Checking Python virtual environment..."
if [ ! -f "$VENV_PYTHON" ]; then
  echo "[visualize] Creating venv at $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
fi
echo "[visualize] Using Python: $VENV_PYTHON"

# ── 2. Python dependencies ────────────────────────────────────────────────────
echo ""
echo "[visualize] Step 2/5: Installing Python dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip -q
"$VENV_PYTHON" -m pip install -r "$REPO_DIR/server/requirements.txt" -q
echo "[visualize] Python dependencies installed."

# ── 3. Copy skill files to install dir ───────────────────────────────────────
echo ""
echo "[visualize] Step 3/5: Copying skill files to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"

# Copy all skill source files (exclude .git, node_modules, .next, .logs)
rsync -a --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.logs' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  "$REPO_DIR/" "$INSTALL_DIR/"

# Ensure scripts are executable
chmod +x "$INSTALL_DIR/scripts/"*.sh

echo "[visualize] Skill files copied."

# ── 4. Node.js dependencies ───────────────────────────────────────────────────
echo ""
echo "[visualize] Step 4/5: Installing Node.js dependencies for the frontend..."
if ! command -v node &>/dev/null; then
  echo "[visualize] ERROR: Node.js not found. Install Node.js 18+ and re-run setup."
  exit 1
fi
if ! command -v npm &>/dev/null; then
  echo "[visualize] ERROR: npm not found. Install npm and re-run setup."
  exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo "[visualize] ERROR: Node.js 18+ required. Found: $(node --version)"
  exit 1
fi

cd "$INSTALL_DIR/app"
echo "[visualize] Running npm install in $INSTALL_DIR/app ..."
npm install --prefer-offline 2>&1 | tail -5
echo "[visualize] Node.js dependencies installed."

# ── 5. Register MCP server in Claude Code settings ───────────────────────────
echo ""
echo "[visualize] Step 5/5: Registering MCP server in Claude Code settings..."

"$VENV_PYTHON" - <<PYEOF
import json, os, sys

settings_path = "$SETTINGS_PATH"
skill_dir = "$INSTALL_DIR"
venv_python = "$VENV_PYTHON"

if not os.path.exists(settings_path):
    print(f"[visualize] settings.json not found at {settings_path}")
    print(f"[visualize] Skipping auto-registration. Add manually:")
    print(f"""  "mcpServers": {{
    "visualize-ui": {{
      "command": "{venv_python}",
      "args": ["{skill_dir}/server/mcp-server.py"],
      "env": {{}}
    }}
  }}""")
    sys.exit(0)

with open(settings_path) as f:
    settings = json.load(f)

settings.setdefault("mcpServers", {})
settings["mcpServers"]["visualize-ui"] = {
    "command": venv_python,
    "args": [os.path.join(skill_dir, "server", "mcp-server.py")],
    "env": {}
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("[visualize] MCP server 'visualize-ui' registered in settings.json.")
PYEOF

# ── Also install SKILL.md into project .claude/skills if in a project dir ─────
PROJECT_SKILL_DIR="$(pwd)/.claude/skills/$SKILL_NAME"
if [ -f "$(pwd)/CLAUDE.md" ] || [ -d "$(pwd)/.claude" ]; then
  echo ""
  echo "[visualize] Detected Claude project at $(pwd). Installing SKILL.md locally..."
  mkdir -p "$PROJECT_SKILL_DIR"
  cp "$INSTALL_DIR/SKILL.md" "$PROJECT_SKILL_DIR/SKILL.md"
  echo "[visualize] SKILL.md installed at $PROJECT_SKILL_DIR/SKILL.md"
fi

echo ""
echo "[visualize] ============================================"
echo "[visualize]  Setup complete!"
echo "[visualize] ============================================"
echo ""
echo "  Next steps:"
echo "  1. Restart Claude Code to load the 'visualize-ui' MCP server"
echo "  2. Type /visualize in any session to start a visualization session"
echo "  3. The browser UI will launch at http://localhost:3001"
echo ""
echo "  To update: git pull && bash scripts/setup.sh"
echo "  To stop UI: bash ~/.claude/skills/visualize/scripts/stop-ui.sh"
echo ""
