"""
Standalone test script: starts WebSocket server, parses CSVs, pushes data to browser.
Usage: python3 test-with-csv.py <csv1> [csv2] [--project-dir <dir>]

Does NOT require Claude Code MCP integration — useful for visual testing.
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path

import pandas as pd
import websockets

connected_clients: set = set()


async def broadcast(msg: dict) -> None:
    if not connected_clients:
        return
    data = json.dumps(msg, ensure_ascii=False)
    snapshot = list(connected_clients)
    await asyncio.gather(*(c.send(data) for c in snapshot), return_exceptions=True)


async def ws_handler(ws) -> None:
    connected_clients.add(ws)
    print(f"[test] Browser connected ({len(connected_clients)} total)")
    # Push all pending data immediately on connect
    for msg in _pending:
        try:
            await ws.send(json.dumps(msg, ensure_ascii=False))
        except Exception:
            pass
    try:
        async for _ in ws:
            pass
    finally:
        connected_clients.discard(ws)
        print(f"[test] Browser disconnected")


_pending: list[dict] = []


def parse_csv(path: Path) -> dict:
    df = pd.read_csv(path, nrows=100)
    return {
        "type": "data_preview",
        "filename": path.name,
        "columns": [str(c) for c in df.columns.tolist()],
        "rows": df.fillna("").to_dict("records"),
    }


def build_file_tree(project_dir: Path, files: list[Path]) -> list[dict]:
    nodes = []
    for f in files:
        try:
            rel = f.relative_to(project_dir)
        except ValueError:
            rel = Path(f.name)
        nodes.append({"name": f.name, "path": str(rel), "type": "file"})
    return nodes


async def main(csv_files: list[Path], project_dir: Path, port: int) -> None:
    # Build file tree
    tree_msg = {"type": "file_tree", "tree": build_file_tree(project_dir, csv_files)}
    _pending.append(tree_msg)

    # Parse each CSV and push preview + simulated chat message
    for path in csv_files:
        print(f"[test] Parsing {path.name}...")
        preview = parse_csv(path)
        _pending.append({
            "type": "push_message",
            "role": "user",
            "content": f"@{path.name} — show me this data",
            "timestamp": "2026-05-29T06:38:00Z",
        })
        _pending.append({
            "type": "push_message",
            "role": "assistant",
            "content": f"Parsed **{path.name}**: {len(preview['rows'])} rows × {len(preview['columns'])} columns. Preview sent to browser.",
            "timestamp": "2026-05-29T06:38:01Z",
        })
        _pending.append(preview)
        print(f"[test]   → {len(preview['rows'])} rows, columns: {preview['columns'][:5]}")

    print(f"[test] WebSocket server on ws://localhost:{port}")
    print(f"[test] Open browser at http://localhost:3000?project={project_dir}")
    print(f"[test] Ctrl+C to stop\n")

    async with websockets.serve(ws_handler, "localhost", port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    missing = [f for f in args.csv_files if not f.exists()]
    if missing:
        print(f"[test] ERROR: files not found: {missing}")
        sys.exit(1)

    asyncio.run(main(args.csv_files, args.project_dir, args.port))
