"""OCR extraction core pipeline."""

from __future__ import annotations

import math
from pathlib import Path

from pdf_converter.ocr.region_classification import classify_regions, refine_text
from pdf_converter.ocr.region_segmentation import segment_text_regions
from pdf_converter.ocr.table_extraction import detect_table_regions, extract_table_cells
from pdf_converter.shared.utils import build_page_metadata, log_progress


def extract_regions_from_image(
    img,
    lang: str = "eng",
) -> list[dict]:
    """Extract and OCR semantic regions from a single image array."""
    _, _, tables = detect_table_regions(img)
    text_regions = segment_text_regions(img, tables)

    all_regions = classify_regions(img, text_regions, tables, lang)

    all_regions = refine_text(img, all_regions, lang)

    log_progress("Extracting table cells ...", level="DEBUG")
    for region in all_regions:
        if region["kind"] == "table":
            region["cells"] = extract_table_cells(img, region, lang)

    return all_regions

def build_page_boxes(regions: list[dict], dpi: int = 200) -> list[dict]:
    """Convert OCR regions to page_boxes format.
    
    Args:
        regions: List of OCR regions with pixel coordinates
        dpi: DPI at which the image was rendered from PDF (default 200)
    
    Returns:
        List of page boxes with normalized PDF page coordinates
    """
    # Convert image pixel coordinates to PDF page coordinates
    # PDF uses 72 DPI, so scale factor is 72.0 / rendering_dpi
    scale = 72.0 / dpi
    
    page_boxes: list[dict] = []
    for index, region in enumerate(regions):
        # Convert pixel coords to PDF coords and normalize with ceil/floor
        x1 = math.ceil(region.get("x1", 0.0) * scale)
        y1 = math.ceil(region.get("y1", 0.0) * scale)
        x2 = math.floor(region.get("x2", 0.0) * scale)
        y2 = math.floor(region.get("y2", 0.0) * scale)
        
        page_boxes.append(
            {
                "index": index,
                "class": region.get("kind", ""),
                "bbox": [x1, y1, x2, y2],
                "text": (region.get("text") or "").strip(),
            }
        )
    return page_boxes
