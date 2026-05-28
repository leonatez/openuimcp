"""MCP tool: render_ui — sends an OpenUI Lang spec to the browser renderer."""
import asyncio
import sys


def register_render_ui(mcp, broadcast):
    @mcp.tool()
    async def render_ui(spec: str) -> str:
        """Render an OpenUI Lang component spec in the browser panel.

        spec must be a valid OpenUI Lang v0.5 string starting with 'root = '.
        Example:
          rows = Query("sales", {}, {items: []})
          tbl = Table([Col("Name", rows.items.name), Col("Value", rows.items.value)])
          root = Stack([tbl])
        """
        async def _send():
            try:
                await broadcast({"type": "render_ui", "spec": spec})
            except Exception as e:
                print(f"[brainstorm-ui] render_ui broadcast error: {e}", file=sys.stderr)

        asyncio.create_task(_send())
        return "UI rendered in browser panel."
