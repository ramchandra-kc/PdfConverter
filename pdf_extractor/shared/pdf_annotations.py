"""Utilities for writing PDF annotations from extracted page boxes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fitz

from pdf_extractor.shared.utils import log_progress


def draw_page_boxes_pdf(
    pdf_path: str,
    extracted_json_paths: list[str],
    output_dir: str | Path,
) -> str | None:
    """Create an annotated PDF by reading extracted JSON files and drawing page_boxes bboxes."""
    source_path = Path(pdf_path)
    if source_path.suffix.lower() != ".pdf":
        log_progress(
            "Skipping --draw-page-boxes-pdf: input is not a PDF file",
            level="WARNING",
        )
        return None

    if not extracted_json_paths:
        log_progress(
            "Skipping --draw-page-boxes-pdf: no extracted JSON paths were provided",
            level="WARNING",
        )
        return None

    output_path = Path(output_dir) / f"{source_path.stem}_boxed.pdf"
    pages_data: list[dict[str, Any]] = []

    for json_path in extracted_json_paths:
        path_obj = Path(json_path)
        if not path_obj.exists():
            log_progress(f"Skipping missing JSON file: {path_obj}", level="WARNING")
            continue

        with open(path_obj, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list):
            pages_data.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            pages_data.append(payload)

    if not pages_data:
        log_progress(
            "Skipping --draw-page-boxes-pdf: no page data could be parsed from extracted JSON files",
            level="WARNING",
        )
        return None

    with fitz.open(str(source_path)) as doc:
        for page_data in pages_data:
            metadata = page_data.get("metadata") or {}
            page_number = metadata.get("page_number")
            if not isinstance(page_number, int) or page_number < 1:
                continue

            page_idx = page_number - 1
            if page_idx < 0 or page_idx >= doc.page_count:
                continue

            page = doc.load_page(page_idx)
            for box in page_data.get("page_boxes") or []:
                bbox = box.get("bbox")
                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue

                try:
                    x1, y1, x2, y2 = [float(value) for value in bbox]
                except (TypeError, ValueError):
                    continue

                rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                if rect.width <= 0 or rect.height <= 0:
                    continue

                page.draw_rect(rect, color=(1, 0, 0), width=1.0, overlay=True)

        doc.save(str(output_path))

    log_progress(f"Saved: {output_path}", level="INFO")
    return str(output_path)
