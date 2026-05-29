#!/usr/bin/env python3
"""
Visualize UI relay server — no MCP required.

Starts two servers in one process:
  - WebSocket on WS_PORT  (8766): browser connects here to receive messages
  - HTTP     on HTTP_PORT (8767): Claude posts JSON messages here to broadcast

HTTP API:
  POST /              body = any JSON message → broadcast to all WS clients
  POST /push_message  body = {"role","content"}
  POST /render_ui     body = {"spec": "root = ..."}
  POST /chart_data    body = {"title","x_key","y_key","rows":[...]}
  POST /parse_file    body = {"path": "/abs/path/to/file.csv"}
  POST /list_files    body = {"project_dir": "/abs/path"}
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "-q"], check=False)
    import websockets

WS_PORT = int(os.environ.get("VISUALIZE_MCP_PORT", "8766"))
HTTP_PORT = int(os.environ.get("VISUALIZE_HTTP_PORT", "8767"))
PROJECT_ROOT = Path(os.environ.get("VISUALIZE_PROJECT_ROOT", os.getcwd())).resolve()

CLIENTS: set = set()
LOOP: asyncio.AbstractEventLoop = None


# ── WebSocket ──────────────────────────────────────────────────────────────

async def ws_handler(ws):
    CLIENTS.add(ws)
    try:
        async for _ in ws:
            pass
    finally:
        CLIENTS.discard(ws)


async def broadcast(msg: dict):
    if not CLIENTS:
        return
    data = json.dumps(msg, ensure_ascii=False)
    await asyncio.gather(*(c.send(data) for c in list(CLIENTS)), return_exceptions=True)


# ── File parsing helpers ───────────────────────────────────────────────────

def _parse_csv(path: Path):
    import csv
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for i, r in enumerate(reader) if i < 200]
    cols = list(rows[0].keys()) if rows else []
    return cols, rows


def _parse_excel(path: Path):
    try:
        import pandas as pd
        df = pd.read_excel(path, nrows=200, engine="openpyxl")
        return df.columns.tolist(), df.fillna("").to_dict("records")
    except ImportError:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            headers = [str(c) for c in next(rows_iter, [])]
            rows = [dict(zip(headers, r)) for _, r in zip(range(200), rows_iter)]
            return headers, rows
        except ImportError:
            return ["error"], [{"error": "Install pandas or openpyxl to parse Excel files"}]


def _parse_pdf(path: Path):
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages[:10]):
                text = (page.extract_text() or "").strip()
                pages.append({"page": i + 1, "content": text[:500]})
        return ["page", "content"], pages
    except ImportError:
        return ["error"], [{"error": "Install pdfplumber to parse PDF files"}]


_PARSERS = {".csv": _parse_csv, ".xlsx": _parse_excel, ".xls": _parse_excel, ".pdf": _parse_pdf}


def parse_file(path_str: str) -> dict:
    path = Path(path_str).resolve()
    if not path.exists():
        return {"type": "push_message", "role": "assistant",
                "content": f"File not found: {path}", "timestamp": _ts()}
    suffix = path.suffix.lower()
    parser = _PARSERS.get(suffix)
    if not parser:
        return {"type": "push_message", "role": "assistant",
                "content": f"Unsupported file type: {suffix}", "timestamp": _ts()}
    try:
        cols, rows = parser(path)
        return {"type": "data_preview", "filename": path.name,
                "columns": [str(c) for c in cols], "rows": rows}
    except Exception as e:
        return {"type": "push_message", "role": "assistant",
                "content": f"Parse error: {e}", "timestamp": _ts()}


# ── File tree helper ───────────────────────────────────────────────────────

IGNORED = {".git", "node_modules", "__pycache__", ".next", "dist", ".venv", "venv"}


def _build_tree(path: Path, depth: int = 0) -> list:
    if depth > 4:
        return []
    nodes = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return []
    for entry in entries:
        if entry.name.startswith(".") or entry.name in IGNORED:
            continue
        if entry.is_dir():
            children = _build_tree(entry, depth + 1)
            nodes.append({"name": entry.name, "path": str(entry), "type": "dir", "children": children})
        else:
            nodes.append({"name": entry.name, "path": str(entry), "type": "file"})
    return nodes


def _ts():
    return datetime.now(timezone.utc).isoformat()


# ── HTTP handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # silence access logs

    def _respond(self, status: int, body: bytes = b"ok"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._respond(204)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError as e:
            self._respond(400, f"bad json: {e}".encode())
            return

        path = self.path.rstrip("/")

        try:
            if path in ("", "/"):
                msg = body                              # broadcast raw message

            elif path == "/push_message":
                msg = {"type": "push_message",
                       "role": body.get("role", "assistant"),
                       "content": body.get("content", ""),
                       "timestamp": body.get("timestamp", _ts())}

            elif path == "/render_ui":
                msg = {"type": "render_ui", "spec": body.get("spec", "")}

            elif path == "/chart_data":
                msg = {**body, "type": "chart_data"}

            elif path == "/parse_file":
                msg = parse_file(body.get("path", ""))

            elif path == "/list_files":
                project = Path(body.get("project_dir", str(PROJECT_ROOT))).resolve()
                msg = {"type": "file_tree", "tree": _build_tree(project)}

            else:
                self._respond(404, b"unknown endpoint")
                return

            asyncio.run_coroutine_threadsafe(broadcast(msg), LOOP)
            self._respond(200)
        except Exception as e:
            self._respond(500, str(e).encode())


# ── Main ───────────────────────────────────────────────────────────────────

async def main():
    global LOOP
    LOOP = asyncio.get_running_loop()

    http = HTTPServer(("localhost", HTTP_PORT), Handler)
    Thread(target=http.serve_forever, daemon=True).start()

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        print(f"[visualize-relay] WS  ready on :{WS_PORT}", flush=True)
        print(f"[visualize-relay] HTTP ready on :{HTTP_PORT}", flush=True)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
