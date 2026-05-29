"""
Brainstorm UI MCP server.
Runs FastMCP stdio transport (Claude Code talks to this) alongside
a WebSocket server (browser connects to this) in the same asyncio loop.
"""
import asyncio
import json
import os
import sys

# Ensure tools/ is importable regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

import websockets
from mcp.server.fastmcp import FastMCP

from tools.render_ui_tool import register_render_ui  # type: ignore[import]
from tools.push_message_tool import register_push_message  # type: ignore[import]
from tools.file_tree_tool import register_file_tree  # type: ignore[import]
from tools.data_parser_tool import register_data_parser  # type: ignore[import]

mcp = FastMCP("visualize-ui")
WS_PORT = int(os.getenv("VISUALIZE_MCP_PORT", "8766"))
# Sandbox root: all file operations are restricted to this directory.
# Set via env at startup (start-ui.sh exports VISUALIZE_PROJECT_ROOT).
PROJECT_ROOT = os.path.realpath(os.getenv("VISUALIZE_PROJECT_ROOT", os.getcwd()))

# Tracks all connected browser WebSocket clients
_clients: set = set()


async def _broadcast(msg: dict) -> None:
    """Send JSON message to all connected browser clients."""
    if not _clients:
        return
    # Snapshot before await so set mutations during gather() don't misalign zip()
    snapshot = list(_clients)
    data = json.dumps(msg)
    results = await asyncio.gather(
        *(c.send(data) for c in snapshot), return_exceptions=True
    )
    dead = {c for c, r in zip(snapshot, results) if isinstance(r, Exception)}
    _clients.difference_update(dead)


async def _ws_handler(ws) -> None:
    """Handle a browser WebSocket connection (server-push only)."""
    _clients.add(ws)
    try:
        async for _ in ws:
            pass  # browser sends nothing; server-push only
    finally:
        _clients.discard(ws)


# Register all tools, injecting the broadcast coroutine
register_render_ui(mcp, _broadcast)
register_push_message(mcp, _broadcast)
register_file_tree(mcp, _broadcast, PROJECT_ROOT)
register_data_parser(mcp, _broadcast, PROJECT_ROOT)


async def main() -> None:
    async with websockets.serve(_ws_handler, "localhost", WS_PORT):
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
