"""MCP tool: list_project_files — sends CWD-scoped file tree to browser panel."""
import asyncio
from pathlib import Path
from typing import Any


_SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", "dist", ".next", "build"}
_SKIP_PREFIXES = (".",)


def _build_tree(path: Path, root: Path, max_depth: int = 5, depth: int = 0) -> list[dict]:
    if depth > max_depth:
        return []
    nodes: list[dict[str, Any]] = []
    try:
        entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        return []
    for entry in entries:
        if entry.name in _SKIP_DIRS or any(entry.name.startswith(p) for p in _SKIP_PREFIXES):
            continue
        node: dict[str, Any] = {
            "name": entry.name,
            "path": str(entry.relative_to(root)),
            "type": "dir" if entry.is_dir() else "file",
        }
        if entry.is_dir():
            node["children"] = _build_tree(entry, root, max_depth, depth + 1)
        nodes.append(node)
    return nodes


def register_file_tree(mcp, broadcast, project_root: str):
    root = Path(project_root).resolve()

    @mcp.tool()
    async def list_project_files() -> str:
        """List all files in the active project directory and send to browser file tree panel."""
        if not root.is_dir():
            return f"Project root is not a directory: {project_root}"
        tree = _build_tree(root, root)

        async def _send():
            try:
                await broadcast({"type": "file_tree", "tree": tree})
            except Exception as e:
                import sys
                print(f"[visualize-ui] broadcast error: {e}", file=sys.stderr)

        asyncio.create_task(_send())
        return f"File tree sent: {len(tree)} top-level entries."
