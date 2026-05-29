"""MCP tool: push_message — mirrors a chat message to the browser panel."""
import asyncio
import sys
from datetime import datetime, timezone


def register_push_message(mcp, broadcast):
    @mcp.tool()
    async def push_message(role: str, content: str) -> str:
        """Mirror a chat message to the browser chat history panel.

        Call after every response to keep the browser in sync with the terminal.
        role: 'user' or 'assistant'
        """
        msg = {
            "type": "push_message",
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async def _send():
            try:
                await broadcast(msg)
            except Exception as e:
                print(f"[visualize-ui] push_message broadcast error: {e}", file=sys.stderr)

        asyncio.create_task(_send())
        return "Message pushed to browser."
