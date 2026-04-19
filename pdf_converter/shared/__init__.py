"""Shared utilities and formatting for pdf-converter."""

from pdf_converter.shared.cli_base import create_base_parser, validate_arguments, print_method_info
from pdf_converter.shared.output_formatter import (
    save_html_output,
    save_markdown_output,
)
from pdf_converter.shared.pdf_annotations import draw_page_boxes_pdf
from pdf_converter.shared.utils import (
    log_progress,
    get_page_count,
    parse_page_range,
    ensure_output_dir,
    build_page_metadata,
)

__all__ = [
    "create_base_parser",
    "validate_arguments",
    "print_method_info",
    "save_html_output",
    "save_markdown_output",
    "draw_page_boxes_pdf",
    "log_progress",
    "get_page_count",
    "parse_page_range",
    "ensure_output_dir",
    "build_page_metadata",
    ]
