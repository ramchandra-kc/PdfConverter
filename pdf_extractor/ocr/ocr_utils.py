"""OCR-specific utility functions."""

from __future__ import annotations

import cv2
import numpy as np
import pytesseract
from PIL import Image


def avg_blob_height(img_bgr: np.ndarray, bbox: dict) -> float:
    """Estimate median character height (px) inside a region."""
    roi = img_bgr[bbox["y1"] : bbox["y2"], bbox["x1"] : bbox["x2"]]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    heights = []
    for contour in contours:
        _, _, width, height = cv2.boundingRect(contour)
        if width > 3 and height > 3:
            heights.append(height)

    return float(np.median(heights)) if heights else 0.0


def quick_ocr(img_bgr: np.ndarray, bbox: dict, lang: str, psm: int = 6) -> str:
    """Fast OCR of one region; returns stripped plain text."""
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
    if x2 <= x1 or y2 <= y1:
        return ""

    roi = img_bgr[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return pytesseract.image_to_string(Image.fromarray(thresholded), lang=lang, config=f"--psm {psm}").strip()


def load_image(file_path: str, page: int = 1, dpi: int = 200) -> np.ndarray:
    """Return a BGR numpy array for the requested page of a PDF or image file."""
    from pathlib import Path

    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}:
        img = cv2.imread(str(path))
        if img is None:
            raise FileNotFoundError(f"Cannot read: {path}")
        return img

    if ext == ".pdf":
        try:
            from pdf2image import convert_from_path
        except ImportError:
            import sys
            sys.exit("pip install pdf2image  (+ poppler-utils)")
        pages = convert_from_path(str(path), dpi=dpi, first_page=page, last_page=page)
        if not pages:
            raise ValueError(f"No page {page} in {path}")
        return cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)

    raise ValueError(f"Unsupported file type: {ext}. Supported: PDF and common image formats.")
