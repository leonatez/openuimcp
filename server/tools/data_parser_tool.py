"""MCP tool: parse_data_file — parses CSV/Excel/PDF and sends preview to browser."""
import asyncio
from pathlib import Path


def _validate_path(path: str, project_root: Path) -> Path:
    """Resolve path and verify it is inside project_root (server-side anchor)."""
    resolved = Path(path).resolve()
    if not str(resolved).startswith(str(project_root) + "/") and resolved != project_root:
        raise ValueError(f"Access denied: {path} is outside project directory.")
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return resolved


def _parse_csv(file_path: Path) -> tuple[list, list]:
    import pandas as pd
    df = pd.read_csv(file_path, nrows=100)
    return df.columns.tolist(), df.fillna("").to_dict("records")


def _parse_excel(file_path: Path) -> tuple[list, list]:
    import pandas as pd
    df = pd.read_excel(file_path, nrows=100, engine="openpyxl")
    return df.columns.tolist(), df.fillna("").to_dict("records")


def _parse_pdf(file_path: Path) -> tuple[list, list]:
    import pdfplumber
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages[:10]):
            text = (page.extract_text() or "").strip()
            pages.append({"page": i + 1, "content": text[:500]})
    return ["page", "content"], pages


_PARSERS = {
    ".csv": _parse_csv,
    ".xlsx": _parse_excel,
    ".xls": _parse_excel,
    ".pdf": _parse_pdf,
}


def register_data_parser(mcp, broadcast, project_root: str):
    root = Path(project_root).resolve()

    @mcp.tool()
    async def parse_data_file(path: str) -> str:
        """Parse a CSV, Excel (.xlsx/.xls), or PDF file and send a data preview to browser.

        path: absolute path to the file (must be inside the active project directory).
        """
        try:
            file_path = _validate_path(path, root)
        except (ValueError, FileNotFoundError) as e:
            return str(e)

        suffix = file_path.suffix.lower()
        parser = _PARSERS.get(suffix)
        if parser is None:
            return f"Unsupported file type: {suffix}. Supported: {', '.join(_PARSERS)}"

        try:
            columns, rows = parser(file_path)
        except Exception as e:
            return f"Parse error: {e}"

        asyncio.create_task(broadcast({
            "type": "data_preview",
            "filename": file_path.name,
            "columns": [str(c) for c in columns],
            "rows": rows[:100],
        }))
        return f"Preview sent: {len(rows)} rows, {len(columns)} columns."
