"""Table detection and cell extraction for OCR."""

from __future__ import annotations

import cv2
import numpy as np
import pytesseract
from PIL import Image


def _morpho_lines(binary: np.ndarray, min_len: int, axis: str) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Return (mask, segments) for horizontal or vertical rule lines."""
    kernel_wh = (min_len, 1) if axis == "h" else (1, min_len)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_wh)
    mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    dilate_wh = (1, 3) if axis == "h" else (3, 1)
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, dilate_wh))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    segments: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if axis == "h":
            center_y = y + height // 2
            segments.append((x, center_y, x + width, center_y))
        else:
            center_x = x + width // 2
            segments.append((center_x, y, center_x, y + height))
    return mask, segments


def detect_table_regions(img_bgr: np.ndarray, min_ratio: float = 0.03) -> tuple[list, list, list[dict]]:
    """Detect table bounding boxes from intersecting horizontal and vertical lines."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10,
    )

    height, width = binary.shape
    h_mask, h_lines = _morpho_lines(binary, int(width * min_ratio), "h")
    v_mask, v_lines = _morpho_lines(binary, int(height * min_ratio), "v")

    grid_mask = cv2.bitwise_or(h_mask, v_mask)
    grid_mask = cv2.dilate(grid_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    contours, _ = cv2.findContours(grid_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tables: list[dict] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        local_h = [
            (x1, y1, x2, y2)
            for (x1, y1, x2, y2) in h_lines
            if x <= x1 and x2 <= x + width and y <= y1 <= y + height
        ]
        local_v = [
            (x1, y1, x2, y2)
            for (x1, y1, x2, y2) in v_lines
            if y <= y1 and y2 <= y + height and x <= x1 <= x + width
        ]
        if len(local_h) >= 2 and len(local_v) >= 2:
            tables.append(
                {
                    "x1": x,
                    "y1": y,
                    "x2": x + width,
                    "y2": y + height,
                    "h_lines": local_h,
                    "v_lines": local_v,
                }
            )

    return h_lines, v_lines, tables


def _snap(values: list[int], tol: int = 10) -> list[int]:
    """Cluster nearby coordinate values and return sorted cluster centers."""
    if not values:
        return []

    sorted_values = sorted(set(values))
    clusters = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if value - clusters[-1][-1] <= tol:
            clusters[-1].append(value)
        else:
            clusters.append([value])

    return [round(sum(cluster) / len(cluster)) for cluster in clusters]


def extract_table_cells(img_bgr: np.ndarray, table: dict, lang: str, snap_tol: int = 10) -> list[dict]:
    """Build grid cells from line segments and detect merged cell spans."""
    h_lines = table["h_lines"]
    v_lines = table["v_lines"]
    tx1, ty1, tx2, ty2 = table["x1"], table["y1"], table["x2"], table["y2"]
    img_h, img_w = img_bgr.shape[:2]

    raw_ys = [y1 for (_, y1, _, _) in h_lines] + [y2 for (_, _, _, y2) in h_lines] + [ty1, ty2]
    raw_xs = [x1 for (x1, _, _, _) in v_lines] + [x2 for (_, _, x2, _) in v_lines] + [tx1, tx2]

    ys = _snap(raw_ys, snap_tol)
    xs = _snap(raw_xs, snap_tol)
    if len(ys) < 2 or len(xs) < 2:
        return []

    n_rows = len(ys) - 1
    n_cols = len(xs) - 1

    def near(a: int, b: int) -> bool:
        return abs(a - b) <= snap_tol

    h_set: set[tuple[int, int]] = set()
    v_set: set[tuple[int, int]] = set()

    for (x1, y1, x2, _) in h_lines:
        for row_idx, y in enumerate(ys):
            if near(y1, y):
                for col_idx in range(n_cols):
                    midpoint = (xs[col_idx] + xs[col_idx + 1]) / 2
                    if x1 <= midpoint <= x2:
                        h_set.add((row_idx, col_idx))
                break

    for (x1, y1, _, y2) in v_lines:
        for col_idx, x in enumerate(xs):
            if near(x1, x):
                for row_idx in range(n_rows):
                    midpoint = (ys[row_idx] + ys[row_idx + 1]) / 2
                    if y1 <= midpoint <= y2:
                        v_set.add((row_idx, col_idx))
                break

    visited = [[False] * n_cols for _ in range(n_rows)]
    cells: list[dict] = []
    inset = 4

    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            if visited[row_idx][col_idx]:
                continue

            col_span = 1
            while col_idx + col_span < n_cols and (row_idx, col_idx + col_span) not in v_set:
                col_span += 1

            row_span = 1
            while row_idx + row_span < n_rows:
                if any((row_idx + row_span, col_idx + ci) in h_set for ci in range(col_span)):
                    break
                row_span += 1

            for rr in range(row_idx, row_idx + row_span):
                for cc in range(col_idx, col_idx + col_span):
                    visited[rr][cc] = True

            x1 = max(0, xs[col_idx] + inset)
            y1 = max(0, ys[row_idx] + inset)
            x2 = min(img_w, xs[col_idx + col_span] - inset)
            y2 = min(img_h, ys[row_idx + row_span] - inset)

            text = ""
            roi = img_bgr[y1:y2, x1:x2]
            if roi.size:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                text = pytesseract.image_to_string(Image.fromarray(thresholded), lang=lang, config="--psm 6")
                text = text.strip().replace("\n", " ")

            cells.append(
                {
                    "row": row_idx,
                    "col": col_idx,
                    "row_span": row_span,
                    "col_span": col_span,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "text": text,
                }
            )

    return cells


def extract_tables(img_bgr: np.ndarray, lang: str, min_ratio: float = 0.03) -> tuple[list, list, list[dict]]:
    """Convenience wrapper returning (h_lines, v_lines, table_regions_with_cells)."""
    h_lines, v_lines, tables = detect_table_regions(img_bgr, min_ratio=min_ratio)
    for table in tables:
        table["cells"] = extract_table_cells(img_bgr, table, lang)
    return h_lines, v_lines, tables
