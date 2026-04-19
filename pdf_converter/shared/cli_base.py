"""Shared CLI argument parsing base."""

from __future__ import annotations

import argparse


def create_base_parser() -> argparse.ArgumentParser:
    """Create base argument parser with common arguments."""
    parser = argparse.ArgumentParser(
        description="Unified PDF extraction tool supporting OCR, PyMuPDF, and hybrid methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # OCR method for scanned PDF with JSON output
    pdf-converter --input sample.pdf --method ocr --output output.json

    # OCR with markdown file output in addition to JSON
    pdf-converter --input sample.pdf --method ocr -f md --write-text-file
  
    # PyMuPDF method for native PDF with Markdown text in JSON
    pdf-converter --input sample.pdf --method pymupdf -f md
  
    # OCR with page range and custom language
    pdf-converter --input sample.pdf --method ocr --start-page 2 --end-page 5 --lang fra
  
    # PyMuPDF with per-page JSON output
    pdf-converter --input sample.pdf --method pymupdf --page-per-json

    # Hybrid method (PyMuPDF + OCR tables)
    pdf-converter --input sample.pdf --method hybrid -f html
        """,
    )

    # Required arguments
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input file path (PDF or image)",
    )

    parser.add_argument(
        "--method",
        type=str,
        required=True,
        choices=["ocr", "pymupdf", "hybrid"],
        help="Extraction method: 'ocr' for OCR-based extraction, 'pymupdf' for PyMuPDF-based extraction, 'hybrid' for PyMuPDF + OCR-table extraction",
    )

    # Output arguments
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path or directory (default: outputs/<input_name>_output.json)",
    )

    parser.add_argument(
        "-f",
        "--text-format",
        type=str,
        choices=["html", "md"],
        default="md",
        help="Text format inside JSON output (default: md)",
    )

    parser.add_argument(
        "--page-per-json",
        action="store_true",
        help="Write one JSON file per selected page (default: single JSON file)",
    )

    parser.add_argument(
        "--write-text-file",
        action="store_true",
        help="Write .html/.md files in addition to JSON outputs (uses --text-format)",
    )

    parser.add_argument(
        "--draw-page-boxes-pdf",
        action="store_true",
        help="Write an additional PDF with rectangles drawn from page_boxes bboxes",
    )

    # Page selection arguments
    parser.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="Start page number to extract (1-indexed)",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="End page number to extract (1-indexed, inclusive)",
    )

    # OCR-specific arguments
    parser.add_argument(
        "--lang",
        "-l",
        type=str,
        default="eng",
        help="Tesseract language code for OCR/hybrid methods (default: eng)",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="DPI for PDF to image rendering (OCR/hybrid methods, default: 200)",
    )

    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Disable debug artifacts for OCR method",
    )

    parser.add_argument(
        "--debug-out",
        type=str,
        default=None,
        help="Directory for OCR debug artifacts (OCR method only)",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate argument combinations."""
    # If OCR-specific args are provided with pymupdf method, warn user
    if args.method == "pymupdf":
        if args.lang != "eng":
            print("Warning: --lang is only used with --method ocr/hybrid, ignoring")
        if args.dpi != 200:
            print("Warning: --dpi is only used with --method ocr/hybrid, ignoring")
        
    if args.start_page is not None and args.start_page < 1:
        raise ValueError("--start-page must be >= 1")

    if args.end_page is not None and args.end_page < 1:
        raise ValueError("--end-page must be >= 1")

    if (
        args.start_page is not None
        and args.end_page is not None
        and args.start_page > args.end_page
    ):
        raise ValueError("--start-page cannot be greater than --end-page")


def print_method_info(method: str) -> None:
    """Print information about the selected extraction method."""
    if method == "ocr":
        print("Using OCR extraction method (Tesseract + custom pipeline)")
        print("  Best for: Scanned PDFs, images, multi-language content")
        print("  Input: PDF or image files")
    elif method == "pymupdf":
        print("Using PyMuPDF extraction method (pymupdf4llm)")
        print("  Best for: Native PDFs with embedded text, fast extraction")
        print("  Input: PDF files only")
    elif method == "hybrid":
        print("Using Hybrid extraction method (PyMuPDF + OCR tables)")
        print("  Best for: Native PDFs where table extraction needs OCR refinement")
        print("  Input: PDF files only")
