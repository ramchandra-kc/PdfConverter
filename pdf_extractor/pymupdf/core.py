"""PyMuPDF extraction core module."""

from __future__ import annotations
from typing import Any

import fitz
import math
import json
import pymupdf4llm
from pdf_extractor.pymupdf.render import render_box
from pdf_extractor.shared.utils import log_progress

def get_total_pages(pdf_path: str) -> int:
    """Get total page count from PDF."""
    with fitz.open(pdf_path) as doc:
        return doc.page_count
    

def get_page_boxes(page: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract normalized page boxes from pymupdf4llm page data."""
    if "boxes" not in page:
        return []

    boxes = []
    for i, box in enumerate(page["boxes"]):
        boxes.append(
            {
                "index": i,
                "class": box.get("boxclass"),
                "bbox": [
                    math.ceil(box.get("x0")),
                    math.ceil(box.get("y0")),
                    math.floor(box.get("x1")),
                    math.floor(box.get("y1")),
                ],
                "text": render_box(box),
            }
        )
    return boxes


def get_html_per_page(
    pdf_path: str,
    image_dir: str,
    pages: list[int],
) -> list[object]:
    """Extract HTML content per page using pymupdf4llm."""
    try:
        raw_document = pymupdf4llm.to_json(
            pdf_path,
            write_images=True,
            image_path=image_dir,
            pages=pages,
            header=False,
            footer=False,
            use_ocr=False,
        )
        document = json.loads(raw_document) if isinstance(raw_document, str) else raw_document
        document_pages = document.get("pages", [])
        result = []
        if not document_pages:
            first_page = pages[0] + 1
            last_page = pages[-1] + 1
            log_progress(
                f"No content extracted from pages {first_page} to {last_page}",
                level="WARNING",
            )
        for page in document_pages:
            page_boxes = get_page_boxes(page)
            metadata = document.get("metadata", {})
            metadata["page_number"] = page.get("page_number", metadata.get("page_number"))
            page_head = f'<section class="page" data-page="{metadata["page_number"]}">'
            result.append(
                {
                    "text": page_head + "\n".join(pb["text"] for pb in page_boxes),
                    "page_boxes": page_boxes,
                    "metadata": metadata.copy(),
                    "text_format": "html",
                }
            )
        return result
    except Exception as exc:
        first_page = pages[0] + 1
        last_page = pages[-1] + 1
        log_progress(
            f"Error extracting pages {first_page} to {last_page}: {exc}",
            level="ERROR",
        )
        raise


def get_md_per_page(
    pdf_path: str,
    image_dir: str,
    pages: list[int],
) -> list[object]:
    """Extract Markdown content per page using pymupdf4llm."""
    try:
        raw_document = pymupdf4llm.to_markdown(
            pdf_path,
            write_images=True,
            image_path=image_dir,
            pages=pages,
            header=False,
            footer=False,
            page_chunks=True,
            use_ocr=False,
        )
        document_pages = (
            json.loads(raw_document) if isinstance(raw_document, str) else raw_document
        )
        result = []
        if not document_pages:
            first_page = pages[0] + 1
            last_page = pages[-1] + 1
            log_progress(
                f"No content extracted from pages {first_page} to {last_page}",
                level="WARNING",
            )
        for page in document_pages:
            result.append(
                {
                    "text": page.get("text", ""),
                    "page_boxes": page.get("page_boxes", []),
                    "metadata": page.get("metadata", {}).copy(),
                    "text_format": "md",
                }
            )
        return result
    except Exception as exc:
        first_page = pages[0] + 1
        last_page = pages[-1] + 1
        log_progress(
            f"Error extracting pages {first_page} to {last_page}: {exc}",
            level="ERROR",
        )
        raise
