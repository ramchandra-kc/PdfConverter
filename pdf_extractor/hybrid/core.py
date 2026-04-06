"""Hybrid extraction core: PyMuPDF for structure + OCR for tables."""

from __future__ import annotations

from typing import Any

import cv2
import fitz
import numpy as np

from pdf_extractor.ocr.render import _table_to_html_ocr, _table_to_markdown
from pdf_extractor.ocr.table_extraction import detect_table_regions, extract_table_cells
from pdf_extractor.pymupdf.core import get_html_per_page, get_md_per_page
from pdf_extractor.shared.utils import log_progress


def _largest_table(tables: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the largest detected table region by area."""
    if not tables:
        return None

    def area(table: dict[str, Any]) -> int:
        return max(0, table["x2"] - table["x1"]) * max(0, table["y2"] - table["y1"])

    return max(tables, key=area)


def _crop_table_image(page: fitz.Page, bbox: list[float], dpi: int) -> np.ndarray | None:
    """Render a clipped table area from a PDF page into BGR image space."""
    if len(bbox) != 4:
        return None

    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return None

    page_rect = page.rect
    clip = fitz.Rect(x0, y0, x1, y1) & page_rect
    if clip.is_empty:
        return None

    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pixmap = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)

    if pixmap.width <= 0 or pixmap.height <= 0:
        return None

    channel_count = pixmap.n
    arr = np.frombuffer(pixmap.samples, dtype=np.uint8)
    arr = arr.reshape((pixmap.height, pixmap.width, channel_count))

    if channel_count == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _render_table(cells: list[dict[str, Any]], text_format: str) -> str:
    """Render OCR table cells to requested text format."""
    if text_format == "html":
        return _table_to_html_ocr(cells)
    return _table_to_markdown(cells)


def _rebuild_page_text(page_data: dict[str, Any], text_format: str) -> str:
    """Rebuild page text from page_boxes after table replacement."""
    page_boxes = page_data.get("page_boxes", [])
    parts = [str(box.get("text", "")) for box in page_boxes]

    if text_format == "html":
        page_number = page_data.get("metadata", {}).get("page_number", "")
        return f'<section class="page" data-page="{page_number}">' + "\n".join(parts)

    return "\n\n".join(parts).strip() + "\n"


def hybrid_extract_pages(
    input_path: str,
    image_dir: str,
    page_nums: list[int],
    text_format: str,
    lang: str,
    dpi: int,
) -> tuple[list[dict[str, Any]], int]:
    """Extract pages with PyMuPDF and replace tables using OCR table extraction."""
    if text_format == "html":
        pages = get_html_per_page(input_path, image_dir, page_nums)
    else:
        pages = get_md_per_page(input_path, image_dir, page_nums)

    replaced_tables = 0

    with fitz.open(input_path) as doc:
        for page_data in pages:
            metadata = page_data.get("metadata", {})
            page_number = int(metadata.get("page_number", 1))
            page_index = max(0, min(doc.page_count - 1, page_number - 1))
            pdf_page = doc.load_page(page_index)

            for box in page_data.get("page_boxes", []):
                if box.get("class") != "table":
                    continue

                cropped = _crop_table_image(pdf_page, box.get("bbox", []), dpi=dpi)
                if cropped is None:
                    continue

                _, _, tables = detect_table_regions(cropped)
                table = _largest_table(tables)
                if table is None:
                    continue

                cells = extract_table_cells(cropped, table, lang=lang)
                if not cells:
                    continue

                box["text"] = _render_table(cells, text_format)
                box["cells"] = cells
                replaced_tables += 1

            page_data["metadata"]["extraction_method"] = "hybrid"
            page_data["text"] = _rebuild_page_text(page_data, text_format)

    log_progress(f"Hybrid table replacements: {replaced_tables}", level="INFO")
    return pages, replaced_tables
