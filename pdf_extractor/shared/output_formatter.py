"""Shared output formatting utilities for both extraction methods."""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path
from typing import Any


def _parse_markdown_table(md: str) -> list[list[str]]:
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


def _linkify_text(text: str) -> str:
    """Add HTML links to URLs and emails."""
    url_pattern = r"(?<![\\w@])(https?://[^\s<]+)"
    email_pattern = r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
    
    text = re.sub(url_pattern, lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', text, flags=re.IGNORECASE)
    text = re.sub(email_pattern, lambda m: f'<a href="mailto:{m.group(1)}">{m.group(1)}</a>', text)
    return text


def save_html_output(html_content: str, output_path: Path, title: str = "Document") -> None:
    """Save HTML content to file with full document wrapper."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
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
    h1 { margin: 0 0 1rem 0; font-size: 1.65rem; }
    h2 { margin: 1.2rem 0 0.45rem; font-size: 1.1rem; }
    p { margin: 0.35rem 0; }
    ul { margin: 0.25rem 0; padding-left: 1.4rem; }
    li { margin: 0.1rem 0; }
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
    }
    th { background: #f1f1ee; font-weight: 600; }
    a { color: #0f4fa8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    """

    escaped_title = html_module.escape(title)
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>{css}</style>
</head>
<body>
    <main>
        <h1>{escaped_title}</h1>
        {html_content}
    </main>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(full_html)


def save_markdown_output(markdown_content: str, output_path: Path, title: str = "Document") -> None:
    """Save Markdown content to file with title header."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    full_markdown = f"# {title}\n\n{markdown_content}"
    
    with open(output_path, "w") as f:
        f.write(full_markdown)
