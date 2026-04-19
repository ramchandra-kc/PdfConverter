"""OCR-method-specific rendering functions."""

from __future__ import annotations

import re
from typing import Any


def _escape_cell(text: str) -> str:
    """Escape markdown table control characters in cell text."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _list_to_html(text: str) -> str:
    """Convert list text into HTML bullet list."""
    normalized = re.sub(r"(?<!\w)[\{\[]\s*([\da-zA-Z])\s*[\)\}\]]", r"(\1)", text)
    normalized = re.sub(r"(?<!\w)\(\s*([\da-zA-Z])\s*[\}\]]", r"(\1)", normalized)
    normalized = re.sub(r"(?<!\w)\(\(\s*([\da-zA-Z])\s*[\)\}\]]", r"(\1)", normalized)
    normalized = re.sub(r"(?<!\w)[\{\[]\s*([\da-zA-Z])\s*[\)\}\]]\)", r"(\1)", normalized)

    marker_re = re.compile(r"(?<!\w)[\(\{\[]?(?:\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)[\)\}\]\.\,](?=\s+)")
    lines: list[str] = []
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        markers = list(marker_re.finditer(line))
        if len(markers) < 2:
            lines.append(line)
            continue

        prefix = line[: markers[0].start()].strip()
        if prefix:
            lines.append(prefix)

        for idx, marker in enumerate(markers):
            start = marker.start()
            end = markers[idx + 1].start() if idx + 1 < len(markers) else len(line)
            segment = line[start:end].strip()
            if segment:
                lines.append(segment)

    items = []
    for line in lines:
        cleaned = re.sub(r"^[•·▪▸►◆○●\-\*]\s*", "", line)
        items.append(f"      <li>{cleaned}</li>")

    return "    <ul>\n" + "\n".join(items) + "\n    </ul>"


def _list_to_markdown(text: str) -> str:
    """Render list text as markdown bullets."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    return "\n".join(f"- {line}" for line in lines)


def _table_to_html_ocr(cells: list[dict]) -> str:
    """Render OCR-extracted table cells as HTML table."""
    if not cells:
        return '    <p><em>(empty table)</em></p>'

    n_rows = max(cell["row"] + cell["row_span"] for cell in cells)
    n_cols = max(cell["col"] + cell["col_span"] for cell in cells)

    grid = [[None] * n_cols for _ in range(n_rows)]
    for cell in cells:
        for rr in range(cell["row"], cell["row"] + cell["row_span"]):
            for cc in range(cell["col"], cell["col"] + cell["col_span"]):
                grid[rr][cc] = "covered"
        grid[cell["row"]][cell["col"]] = cell

    rows_html = []
    for row_idx in range(n_rows):
        tds = []
        for col_idx in range(n_cols):
            item = grid[row_idx][col_idx]
            if item == "covered" or item is None:
                continue
            rs = item["row_span"]
            cs = item["col_span"]
            attrs = (f' rowspan="{rs}"' if rs > 1 else "") + (f' colspan="{cs}"' if cs > 1 else "")
            text = item["text"] or "&nbsp;"
            tds.append(f"        <td{attrs}>{text}</td>")
        rows_html.append("      <tr>\n" + "\n".join(tds) + "\n      </tr>")

    return '    <div class="table-wrap">\n      <table>\n' + "\n".join(rows_html) + "\n      </table>\n    </div>"


def _table_to_markdown(cells: list[dict] | None) -> str:
    """Render OCR table cells as markdown table."""
    if not cells:
        return "(empty table)"

    n_rows = max(cell["row"] + cell["row_span"] for cell in cells)
    n_cols = max(cell["col"] + cell["col_span"] for cell in cells)

    grid = [[""] * n_cols for _ in range(n_rows)]
    for cell in cells:
        row_idx = cell["row"]
        col_idx = cell["col"]
        grid[row_idx][col_idx] = _escape_cell(cell.get("text", ""))

    if n_rows == 0:
        return "(empty table)"

    header = grid[0]
    sep = ["---"] * n_cols
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]

    for row in grid[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def render_html_from_ocr_regions(regions: list[dict], title: str = "Document") -> str:
    """Render HTML from OCR-extracted regions."""
    parts: list[str] = []

    for region in regions:
        kind = region.get("kind", "paragraph")

        if kind == "table":
            parts.append(_table_to_html_ocr(region.get("cells", [])))
        elif kind == "heading":
            text = region.get("text", "").replace("\n", " ").strip()
            # OCR doesn't have explicit heading level, use level 2 as default
            parts.append(f"    <h2>{text}</h2>")
        elif kind == "list":
            parts.append(_list_to_html(region.get("text", "")))
        elif kind == "paragraph":
            text = region.get("text", "").replace("\n", " ").strip()
            if text:
                parts.append(f"    <p>{text}</p>")

    return "\n\n".join(parts)


def render_markdown_from_ocr_regions(regions: list[dict]) -> str:
    """Render Markdown from OCR-extracted regions."""
    parts: list[str] = []

    for region in regions:
        kind = region.get("kind", "paragraph")

        if kind == "table":
            parts.append(_table_to_markdown(region.get("cells")))
            continue

        text = region.get("text", "").strip()
        if not text:
            continue

        if kind == "heading":
            parts.append(f"## {text.replace(chr(10), ' ')}")
        elif kind == "list":
            rendered = _list_to_markdown(text)
            if rendered:
                parts.append(rendered)
        elif kind == "paragraph":
            parts.append(text.replace("\n", " "))

    return "\n\n".join(parts).strip() + "\n" if parts else "\n"
