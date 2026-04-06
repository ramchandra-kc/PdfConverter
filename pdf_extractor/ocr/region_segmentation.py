"""Region segmentation for OCR extraction."""

from __future__ import annotations

import cv2
import numpy as np


def segment_text_regions(img_bgr: np.ndarray, table_bboxes: list[dict], min_area: int = 500) -> list[dict]:
    """Find contiguous text blobs outside table bounds."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10,
    )

    for table in table_bboxes:
        binary[table["y1"] : table["y2"], table["x1"] : table["x2"]] = 0

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 3))
    dilated = cv2.dilate(binary, h_kernel)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 12))
    dilated = cv2.dilate(dilated, v_kernel)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width * height < min_area:
            continue
        regions.append({"x1": x, "y1": y, "x2": x + width, "y2": y + height, "kind": "unknown"})

    regions.sort(key=lambda region: (region["y1"], region["x1"]))
    return regions
