from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pdf_extractor import extract_from_pdf

def pymupdf_test():
    # Example usage
    input_pdf = "/Users/ram/Documents/Github/PdfExtractor/data/sample.pdf"
    output_base_dir = "/Users/ram/Documents/Github/PdfExtractor/outputs"

    # Extract using PyMuPDF method with markdown text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/pymupdf_md_page_per_json",
        method="pymupdf",
        text_format="md",
        page_per_json=True,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )
    
    # Extract using PyMuPDF method with HTML text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/pymupdf_html_single_json",
        method="pymupdf",
        text_format="html",
        page_per_json=False,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )

    # Extract using PyMuPDF method with markdown text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/pymupdf_md_single_json",
        method="pymupdf",
        text_format="md",
        page_per_json=False,
        write_text_file=True,
    )

    # Extract using PyMuPDF method with HTML text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/pymupdf_html_page_per_json",
        method="pymupdf",
        text_format="html",
        page_per_json=True,
        write_text_file=True,
    )

def ocr_test():
    # Example usage
    input_pdf = "/Users/ram/Documents/Github/PdfExtractor/data/sample.pdf"
    output_base_dir = "/Users/ram/Documents/Github/PdfExtractor/outputs"

     # Extract using ocr method with markdown text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/ocr_md_page_per_json",
        method="ocr",
        text_format="md",
        page_per_json=True,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )
    
    # Extract using ocr method with HTML text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/ocr_html_page_per_json",
        method="ocr",
        text_format="html",
        page_per_json=True,
        write_text_file=True,
    )

    # Extract using ocr method with markdown text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/ocr_md_single_json",
        method="ocr",
        text_format="md",
        page_per_json=False,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )

    # Extract using ocr method with HTML text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/ocr_html_single_json",
        method="ocr",
        text_format="html",
        page_per_json=False,
        write_text_file=True,
    )

def hybrid_test():
    # Example usage
    input_pdf = "/Users/ram/Documents/Github/PdfExtractor/data/sample.pdf"
    output_base_dir = "/Users/ram/Documents/Github/PdfExtractor/outputs"

     # Extract using hybrid method with markdown text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/hybrid_md_page_per_json",
        method="hybrid",
        text_format="md",
        page_per_json=True,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )
    
    # Extract using hybrid method with HTML text format and page-per-json output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/hybrid_html_page_per_json",
        method="hybrid",
        text_format="html",
        page_per_json=True,
        write_text_file=True,
    )

    # Extract using hybrid method with markdown text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/hybrid_md_single_json",
        method="hybrid",
        text_format="md",
        page_per_json=False,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )

    # Extract using hybrid method with HTML text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/hybrid_html_single_json",
        method="hybrid",
        text_format="html",
        page_per_json=False,
        write_text_file=True,
    )

def one_test():
    # Example usage
    input_pdf = "/Users/ram/Documents/Github/PdfExtractor/data/sample.pdf"
    output_base_dir = "/Users/ram/Documents/Github/PdfExtractor/outputs"

   # Extract using PyMuPDF method with HTML text format and single JSON output
    extract_from_pdf(
        input_path=input_pdf,
        output_path=output_base_dir + "/pymupdf_html_single_json",
        method="pymupdf",
        text_format="html",
        page_per_json=False,
        draw_page_boxes_pdf=True,
        write_text_file=True,
    )

# if __name__ == "__main__":
#     pymupdf_test()
#     ocr_test()
#     one_test()
#     hybrid_test()

