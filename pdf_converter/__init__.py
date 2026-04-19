"""PDF Extractor - Unified PDF extraction tool with OCR and pymupdf4llm methods."""

from __future__ import annotations

from pdf_converter.hybrid import extract_with_hybrid
from pdf_converter.ocr import extract_with_ocr
from pdf_converter.pymupdf import extract_with_pymupdf

__version__ = "1.0.0"
__author__ = "PDF Extract Contributors"

__all__ = ["extract_from_pdf", "extract_with_ocr", "extract_with_pymupdf", "extract_with_hybrid"]


def extract_from_pdf(
    input_path: str,
    method: str = "ocr",
    output_path: str | None = None,
    page_nums: list[int] | None = None,
    text_format: str = "html",
    page_per_json: bool = False,
    draw_page_boxes_pdf: bool = False,
    **kwargs,
) -> dict:
    """
    Extract content from PDF using specified method.

    Args:
        input_path: Path to PDF or image file
        method: 'ocr', 'pymupdf', or 'hybrid' extraction method
        output_path: Output directory or file path
        page_nums: List of 0-indexed page numbers to extract (all if None)
        text_format: 'html' or 'md' text rendering used inside JSON output
        page_per_json: If True, save one JSON file per page
        draw_page_boxes_pdf: If True, write an annotated PDF with page_boxes rectangles
        **kwargs: Method-specific arguments
            For OCR: lang, dpi, debug, debug_out
            For PyMuPDF: (none currently)

    Returns:
        Dictionary with extraction results including success status and output path

    Raises:
        ValueError: If method is not recognized
        FileNotFoundError: If input file not found
    """
    if method == "ocr":
        return extract_with_ocr(
            input_path=input_path,
            output_path=output_path,
            page_nums=page_nums,
            text_format=text_format,
            page_per_json=page_per_json,
            draw_page_boxes_pdf=draw_page_boxes_pdf,
            **kwargs,
        )
    elif method == "pymupdf":
        return extract_with_pymupdf(
            input_path=input_path,
            output_path=output_path,
            page_nums=page_nums,
            text_format=text_format,
            page_per_json=page_per_json,
            draw_page_boxes_pdf=draw_page_boxes_pdf,
        )
    elif method == "hybrid":
        return extract_with_hybrid(
            input_path=input_path,
            output_path=output_path,
            page_nums=page_nums,
            text_format=text_format,
            page_per_json=page_per_json,
            draw_page_boxes_pdf=draw_page_boxes_pdf,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown extraction method: '{method}'. Use 'ocr', 'pymupdf', or 'hybrid'")
