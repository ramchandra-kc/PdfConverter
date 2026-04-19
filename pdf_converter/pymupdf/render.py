"""Rendering utilities for pymupdf4llm extraction."""

import html as html_module
import re
from typing import Any

URL_RE = re.compile(r"(?<![\\w@])(https?://[^\s<]+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


def is_bold(span: dict[str, Any]) -> bool:
    """Check if span is bold."""
    flags = int(span.get("flags", 0) or 0)
    font_name = str(span.get("font", "") or "").lower()
    return bool(flags & 0x10) or "bold" in font_name


def is_italic(span: dict[str, Any]) -> bool:
    """Check if span is italic."""
    flags = int(span.get("flags", 0) or 0)
    font_name = str(span.get("font", "") or "").lower()
    return bool(flags & 0x02) or "italic" in font_name or "oblique" in font_name


def wrap_formatting(text: str, bold: bool, italic: bool) -> str:
    """Wrap text with HTML formatting tags."""
    if bold:
        text = f"<strong>{text}</strong>"
    if italic:
        text = f"<em>{text}</em>"
    return text


def linkify_text(text: str) -> str:
    """Add HTML links to URLs and emails in text."""
    text = URL_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', text)
    text = EMAIL_RE.sub(lambda m: f'<a href="mailto:{m.group(1)}">{m.group(1)}</a>', text)
    return text


def span_to_html(span: dict[str, Any]) -> str:
    """Convert a pymupdf4llm span to HTML."""
    raw = str(span.get("text", "") or "")
    if not raw:
        return ""

    escaped = html_module.escape(raw)
    escaped = linkify_text(escaped)
    return wrap_formatting(escaped, is_bold(span), is_italic(span))


def textline_to_html(textline: dict[str, Any]) -> str:
    """Convert a pymupdf4llm textline to HTML."""
    spans = textline.get("spans") or []
    rendered = "".join(span_to_html(span) for span in spans)
    return " ".join(rendered.split())


def box_text_lines(box: dict[str, Any]) -> list[str]:
    """Extract text lines from a pymupdf4llm box."""
    textlines = box.get("textlines") or []
    lines = [textline_to_html(line) for line in textlines]
    return [line for line in lines if line]


def parse_markdown_table(md: str) -> list[list[str]]:
    """Parse markdown table into rows."""
    rows: list[list[str]] = []
    for i, raw_line in enumerate(md.splitlines()):
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        if i == 1 and re.match(r"^\\|[\\-:| ]+\\|$", line):
            continue
        parts = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(parts)
    return rows


def render_table(table: dict[str, Any]) -> str:
    """Render a pymupdf4llm table as HTML."""
    extracted = table.get("extract") or []
    rows = extracted if extracted else parse_markdown_table(str(table.get("markdown", "") or ""))
    if not rows:
        return ""

    out = ["<table>"]
    for row_index, row in enumerate(rows):
        out.append("<tr>")
        cell_tag = "th" if row_index == 0 else "td"
        for cell in row:
            cell_text = html_module.escape(str(cell or ""))
            cell_text = linkify_text(cell_text)
            out.append(f"<{cell_tag}>{cell_text}</{cell_tag}>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def render_box(box: dict[str, Any]) -> str:
    """Render a pymupdf4llm box to HTML."""
    box_class = str(box.get("boxclass", "") or "").strip().lower()

    if box_class == "table":
        table = box.get("table") or {}
        table_html = render_table(table)
        return f'<div class="table-block">{table_html}</div>' if table_html else ""

    lines = box_text_lines(box)
    if not lines:
        return ""

    if box_class == "page-header":
        return "<header>" + "<br>".join(lines) + "</header>"

    if box_class == "section-header":
        text = " ".join(lines)
        return f"<h2>{text}</h2>"

    if box_class == "list-item":
        return "<ul><li>" + " ".join(lines) + "</li></ul>"

    text = " ".join(lines)
    return f"<p>{text}</p>"


def render_page(page: dict[str, Any]) -> str:
    """Render a pymupdf4llm page to HTML."""
    page_number = int(page.get("page_number", 0) or 0)
    boxes = page.get("boxes") or []
    rendered_boxes = [render_box(box) for box in boxes]
    body = "\n".join(block for block in rendered_boxes if block)
    return f'<section class="page" data-page="{page_number}">\n{body}\n</section>'


def _table_to_html_pymupdf(table: dict[str, Any]) -> str:
    """Render pymupdf4llm table data as HTML table."""
    extracted = table.get("extract") or []
    rows = extracted if extracted else parse_markdown_table(str(table.get("markdown", "") or ""))
    
    if not rows:
        return '<p><em>(empty table)</em></p>'

    table_html = ["<table>"]
    for row_index, row in enumerate(rows):
        table_html.append("<tr>")
        cell_tag = "th" if row_index == 0 else "td"
        for cell in row:
            cell_text = html_module.escape(str(cell or ""))
            cell_text = linkify_text(cell_text)
            table_html.append(f"<{cell_tag}>{cell_text}</{cell_tag}>")
        table_html.append("</tr>")
    table_html.append("</table>")
    return "    " + "\n    ".join("".join(table_html).split("\n"))


def _table_to_markdown_pymupdf(table: dict[str, Any]) -> str:
    """Render pymupdf4llm table as markdown."""
    rows = table.get("extract") or []
    if not rows:
        rows = parse_markdown_table(str(table.get("markdown", "") or ""))
    
    if not rows:
        return ""

    lines = []
    for row_index, row in enumerate(rows):
        line = "| " + " | ".join(str(cell or "") for cell in row) + " |"
        lines.append(line)
        if row_index == 0:
            sep = "| " + " | ".join(["---"] * len(row)) + " |"
            lines.append(sep)

    return "\n".join(lines)


def render_html_from_pymupdf_boxes(boxes: list[dict]) -> str:
    """Render HTML from pymupdf4llm-extracted boxes."""
    parts: list[str] = []
    
    for box in boxes:
        box_class = str(box.get("boxclass", "") or "").strip().lower()

        if box_class == "table":
            table = box.get("table") or {}
            table_html = _table_to_html_pymupdf(table)
            if table_html:
                parts.append(f'    <div class="table-block">{table_html}</div>')
        else:
            lines = box_text_lines(box)
            if not lines:
                continue

            text = " ".join(lines)
            if box_class == "page-header" or box_class == "section-header":
                parts.append(f"    <h2>{text}</h2>")
            elif box_class == "list-item":
                parts.append(f"    <ul><li>{text}</li></ul>")
            else:
                parts.append(f"    <p>{text}</p>")

    return "\n\n".join(parts)


def render_markdown_from_pymupdf_boxes(boxes: list[dict]) -> str:
    """Render Markdown from pymupdf4llm-extracted boxes."""
    parts: list[str] = []
    
    for box in boxes:
        box_class = str(box.get("boxclass", "") or "").strip().lower()

        if box_class == "table":
            table = box.get("table") or {}
            table_md = _table_to_markdown_pymupdf(table)
            if table_md:
                parts.append(table_md)
        else:
            lines = box_text_lines(box)
            if not lines:
                continue

            text = " ".join(lines)
            if box_class == "page-header" or box_class == "section-header":
                parts.append(f"## {text}")
            elif box_class == "list-item":
                parts.append(f"- {text}")
            else:
                parts.append(text)

    return "\n\n".join(parts).strip() + "\n" if parts else "\n"


def render_html(document: dict[str, Any]) -> str:
    """Render a complete pymupdf4llm document to HTML."""
    metadata = document.get("metadata") or {}
    title = str(metadata.get("title", "") or "").strip() or str(document.get("filename", "document"))
    escaped_title = html_module.escape(title)

    pages = document.get("pages") or []
    rendered_pages = "\n".join(render_page(page) for page in pages)

    css = """
    :root { color-scheme: light; }
    body {
      font-family: "Charter", "Georgia", serif;
      margin: 0;
      padding: 2rem;
      background: #f7f7f5;
      color: #1d1d1b;
      line-height: 1.45;
    }
    main {
      max-width: 980px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #ddd;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
      padding: 1.5rem;
    }
    .page {
      padding-bottom: 2rem;
      margin-bottom: 2rem;
      border-bottom: 1px dashed #c7c7c3;
    }
    .page:last-child {
      border-bottom: 0;
      margin-bottom: 0;
      padding-bottom: 0;
    }
    header {
      color: #555;
      font-size: 0.92rem;
      margin-bottom: 0.75rem;
    }
    h1 {
      margin: 0 0 1rem 0;
      font-size: 1.65rem;
    }
    h2 {
      margin: 1.2rem 0 0.45rem;
      font-size: 1.1rem;
    }
    p {
      margin: 0.35rem 0;
    }
    ul {
      margin: 0.25rem 0;
      padding-left: 1.4rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 0.75rem 0;
      font-size: 0.94rem;
    }
    th, td {
      border: 1px solid #d5d5d1;
      text-align: left;
      padding: 0.42rem 0.5rem;
      vertical-align: top;
    }
    th {
      background: #f1f1ee;
      font-weight: 600;
    }
    a {
      color: #0f4fa8;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
    @media (max-width: 700px) {
      body { padding: 0.75rem; }
      main { padding: 0.75rem; }
      table { font-size: 0.86rem; }
    }
    """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>{css}</style>
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    {rendered_pages}
  </main>
</body>
</html>
"""
