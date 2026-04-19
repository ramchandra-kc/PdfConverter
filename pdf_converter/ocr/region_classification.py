"""Region classification and text refinement for OCR."""

from __future__ import annotations

import re

import numpy as np

from pdf_converter.ocr.ocr_utils import avg_blob_height, quick_ocr

_BULLET_RE = re.compile(
    r"^\s*(?:"
    r"[•·▪▸▹►◆◇○●\-\*]"
    r"|[\(\{\[]?(?:\d+|[a-zA-Z])[\)\}\]\.\,]"
    r"|[ivxlcdmIVXLCDM]+[.\)]"
    r")\s+",
    re.MULTILINE,
)

_INLINE_MARKER_RE = re.compile(r"(?<!\w)[\(\{\[]?(?:\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)[\)\}\]\.\,](?=\s+)")
_SINGLE_ITEM_MARKER_RE = re.compile(r"^\s*[\(\{\[]?(?:\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)[\)\}\]\.\,]\s+")


def _normalize_list_markers(text: str) -> str:
    """Repair OCR bracket confusions for list markers only."""
    normalized = text
    normalized = re.sub(r"(?<!\w)[\{\[]\s*([\da-zA-Z])\s*[\)\}\]]", r"(\1)", normalized)
    normalized = re.sub(r"(?<!\w)\(\s*([\da-zA-Z])\s*[\}\]]", r"(\1)", normalized)
    normalized = re.sub(r"(?<!\w)\(\(\s*([\da-zA-Z])\s*[\)\}\]]", r"(\1)", normalized)
    normalized = re.sub(r"(?<!\w)[\{\[]\s*([\da-zA-Z])\s*[\)\}\]]\)", r"(\1)", normalized)
    return normalized


def _split_inline_enumerations(text: str) -> str:
    """Split one-line sequences like '(a) x (b) y' into separate lines."""
    out_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        markers = list(_INLINE_MARKER_RE.finditer(line))
        if len(markers) < 2:
            out_lines.append(line)
            continue

        prefix = line[: markers[0].start()].strip()
        if prefix:
            out_lines.append(prefix)

        for idx, marker in enumerate(markers):
            start = marker.start()
            end = markers[idx + 1].start() if idx + 1 < len(markers) else len(line)
            segment = line[start:end].strip()
            if segment:
                out_lines.append(segment)

    return "\n".join(out_lines)


def _is_list(text: str) -> bool:
    """True when text likely represents a list, including inline enumerations."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False

    if len(lines) == 1:
        return len(_INLINE_MARKER_RE.findall(lines[0])) >= 2

    hits = sum(1 for line in lines if _BULLET_RE.match(line))
    return hits / len(lines) >= 0.4


def _looks_like_single_list_item(text: str) -> bool:
    """Heuristic for one-line list item candidates such as 'c. Annexure C'."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return len(lines) == 1 and bool(_SINGLE_ITEM_MARKER_RE.match(lines[0]))


def _is_heading(img_bgr: np.ndarray, bbox: dict, text: str) -> bool:
    """Heading heuristic based on line/word count and median glyph height."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > 2:
        return False

    if len(" ".join(lines).split()) > 12:
        return False

    return avg_blob_height(img_bgr, bbox) > 18


def classify_regions(img_bgr: np.ndarray, text_regions: list[dict], table_bboxes: list[dict], lang: str) -> list[dict]:
    """Assign kind and preliminary text to all regions and sort by reading order."""
    all_regions: list[dict] = []

    for table in table_bboxes:
        all_regions.append({**table, "kind": "table", "text": ""})

    for region in text_regions:
        text = quick_ocr(img_bgr, region, lang, psm=6)
        text = _split_inline_enumerations(_normalize_list_markers(text))
        region["text"] = text
        if not text.strip():
            continue

        if _is_list(text):
            region["kind"] = "list"
        elif _is_heading(img_bgr, region, text):
            region["kind"] = "heading"
        else:
            region["kind"] = "paragraph"
        all_regions.append(region)

    all_regions.sort(key=lambda region: (region["y1"], region["x1"]))

    # Promote isolated marker lines when neighboring text regions are lists.
    for idx, region in enumerate(all_regions):
        if region.get("kind") != "paragraph" or not _looks_like_single_list_item(region.get("text", "")):
            continue

        prev_kind = None
        next_kind = None

        for prev_idx in range(idx - 1, -1, -1):
            prev_kind = all_regions[prev_idx].get("kind")
            if prev_kind in {"list", "paragraph", "heading"}:
                break

        for next_idx in range(idx + 1, len(all_regions)):
            next_kind = all_regions[next_idx].get("kind")
            if next_kind in {"list", "paragraph", "heading"}:
                break

        if prev_kind == "list" or next_kind == "list":
            region["kind"] = "list"

    return all_regions


def refine_text(img_bgr: np.ndarray, regions: list[dict], lang: str) -> list[dict]:
    """Re-run OCR with tuned PSM per region kind."""
    psm_by_kind = {"heading": 7, "paragraph": 4, "list": 4}
    for region in regions:
        psm = psm_by_kind.get(region["kind"])
        if psm is not None:
            text = quick_ocr(img_bgr, region, lang, psm=psm)
            text = _normalize_list_markers(text)
            if region["kind"] == "list":
                text = _split_inline_enumerations(text)
            region["text"] = text
    return regions
