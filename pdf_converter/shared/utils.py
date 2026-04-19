"""Shared utilities for pdf-converter."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def log_progress(message: str, level: str = "INFO") -> None:
    """Log progress messages to stdout in a structured format for real-time parsing."""
    progress_msg = {"type": "progress", "level": level, "message": message}
    print(json.dumps(progress_msg), flush=True)


def get_page_count(file_path: str) -> int:
    """Return total page count for a PDF, or 1 for image inputs."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}:
        return 1

    if ext == ".pdf":
        try:
            from pdf2image import pdfinfo_from_path
        except ImportError:
            sys.exit("pip install pdf2image  (+ poppler-utils)")

        info = pdfinfo_from_path(str(path))
        pages = info.get("Pages")
        if not pages:
            raise ValueError(f"Unable to determine page count for: {path}")
        return int(pages)

    raise ValueError(f"Unsupported file type: {ext}. Supported: PDF and common image formats.")


def parse_page_range(start_page: int | None, end_page: int | None, total_pages: int) -> list[int]:
    """Parse start/end page arguments and return valid page numbers (0-indexed)."""
    start = 1 if start_page is None else int(start_page)
    end = total_pages if end_page is None else int(end_page)

    if start < 1 or start > total_pages:
        raise ValueError(f"Start page {start} out of range [1, {total_pages}]")

    if end < 1 or end > total_pages:
        raise ValueError(f"End page {end} out of range [1, {total_pages}]")

    if start > end:
        raise ValueError(f"Invalid page range: start page {start} is greater than end page {end}")

    # Convert to 0-indexed inclusive range
    return list(range(start - 1, end))


def ensure_output_dir(output_path: str | Path) -> Path:
    """Ensure output directory exists."""
    path = Path(output_path)
    if not path.suffix:
        # It's a directory
        path.mkdir(parents=True, exist_ok=True)
    else:
        # It's a file, ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_page_metadata(page_number: int, total_pages: int, file_path: str, extraction_method: str) -> dict:
    """Build standard metadata dict for a page."""
    return {
        "page_number": page_number + 1,  # Convert back to 1-indexed for output
        "total_pages": total_pages,
        "file_path": file_path,
        "extraction_method": extraction_method,
    }
