"""PyMuPDF extraction method API."""

from __future__ import annotations

import json
from pathlib import Path

from pdf_extractor.pymupdf.core import get_total_pages, log_progress
from pdf_extractor.pymupdf.core import get_html_per_page
from pdf_extractor.pymupdf.core import get_md_per_page
from pdf_extractor.shared.output_formatter import (
    save_html_output,
    save_markdown_output,
)

def extract_with_pymupdf(
    input_path: str,
    output_path: str | None = None,
    page_nums: list[int] | None = None,
    text_format: str = "html",
    page_per_json: bool = False,
    write_text_file: bool = False,
    draw_page_boxes_pdf: bool = False,
) -> dict:
    """
    Extract content from PDF using pymupdf4llm method.

    Args:
        input_path: Path to PDF file
        output_path: Output directory or file path
        page_nums: List of 0-indexed page numbers to extract (all if None)
        text_format: 'html' or 'md' text rendering used inside JSON output
        page_per_json: If True, save one JSON file per page
        write_text_file: If True, save one .html/.md file per page (or a single merged file)

    Returns:
        Result dictionary with output metadata and file paths
    """
    try:        
        total_pages = get_total_pages(input_path)
        
        if page_nums is None:
            page_nums = list(range(total_pages))

        output_dir = Path(output_path) if output_path else Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        image_dir = output_dir / "images"
        image_dir.mkdir(parents=True, exist_ok=True)

        json_dir = output_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        pdf_file_name = Path(input_path).stem

        log_progress(f"PyMuPDF extraction: {input_path}", level="INFO")
        log_progress(f"Pages: {[p + 1 for p in page_nums]} (1-indexed)", level="INFO")
        log_progress(
            f"Output format: json{'+text' if write_text_file else ''}, text format: {text_format}, per-page: {page_per_json}",
            level="INFO",
        )

        extracted_json_paths = []
        extracted_text_paths = []
        text_ext = "html" if text_format == "html" else "md"
        text_dir = output_dir / text_ext

        # Convert 0-indexed to 0-indexed for pymupdf4llm (uses 0-indexing)
        pymupdf_pages = page_nums

        if page_per_json:
            # Extract one page at a time
            for page_idx in page_nums:
                actual_page_num = page_idx + 1  # For display
                log_progress(f"Processing page {actual_page_num}/{total_pages} ...", level="INFO")

                if text_format == "html":
                    pages_object = get_html_per_page(input_path, str(image_dir), [page_idx])
                else:
                    pages_object = get_md_per_page(input_path, str(image_dir), [page_idx])

                if pages_object:
                    page_data = pages_object[0]
                    
                    # Save individual page file
                    page_json_path = json_dir / f"{pdf_file_name}_page_{actual_page_num}.json"
                    with open(page_json_path, "w", encoding="utf-8") as f:
                        json.dump(page_data, f, ensure_ascii=False, indent=2)

                    extracted_json_paths.append(str(page_json_path))
                    log_progress(f"Saved: {page_json_path}", level="INFO")

                    if write_text_file:
                        page_text_path = text_dir / f"{pdf_file_name}_page_{actual_page_num}.{text_ext}"
                        page_title = f"{pdf_file_name} - Page {actual_page_num}"
                        if text_format == "html":
                            save_html_output(page_data.get("text", ""), page_text_path, title=page_title)
                        else:
                            save_markdown_output(page_data.get("text", ""), page_text_path, title=page_title)
                        extracted_text_paths.append(str(page_text_path))
                        log_progress(f"Saved: {page_text_path}", level="INFO")
        else:
            # Extract all pages together
            if text_format == "html":
                pages_object = get_html_per_page(input_path, str(image_dir), pymupdf_pages)
            else:
                pages_object = get_md_per_page(input_path, str(image_dir), pymupdf_pages)

            if not pages_object:
                log_progress(
                    f"No content extracted from pages {pymupdf_pages[0] + 1} to {pymupdf_pages[-1] + 1}",
                    level="WARNING",
                )
            output_file_path = json_dir / f"{pdf_file_name}_extracted.json"

            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(pages_object, f, ensure_ascii=False, indent=2)

            extracted_json_paths.append(str(output_file_path))
            log_progress(f"Saved: {output_file_path}", level="INFO")

            if write_text_file:
                merged_text_path = text_dir / f"{pdf_file_name}_extracted.{text_ext}"
                if text_format == "html":
                    merged_parts = []
                    for page_data in pages_object:
                        page_num = page_data["metadata"]["page_number"]
                        merged_parts.append(
                            f'<section class="page" data-page="{page_num}"><h2>Page {page_num}</h2>{page_data.get("text", "")}</section>'
                        )
                    merged_text = "\n".join(merged_parts)
                    save_html_output(merged_text, merged_text_path, title=f"{pdf_file_name} Extracted")
                else:
                    merged_parts = []
                    for page_data in pages_object:
                        page_num = page_data["metadata"]["page_number"]
                        merged_parts.append(f"## Page {page_num}\n\n{page_data.get('text', '')}")
                    merged_text = "\n\n---\n\n".join(merged_parts)
                    save_markdown_output(merged_text, merged_text_path, title=f"{pdf_file_name} Extracted")
                extracted_text_paths.append(str(merged_text_path))
                log_progress(f"Saved: {merged_text_path}", level="INFO")

        log_progress("Extraction completed successfully", level="INFO")

        if draw_page_boxes_pdf:
            from pdf_extractor.shared.pdf_annotations import draw_page_boxes_pdf

            annotated_pdf_path = draw_page_boxes_pdf(
                pdf_path=input_path,
                extracted_json_paths=extracted_json_paths,
                output_dir=output_dir,
            )
            if annotated_pdf_path:
                log_progress(f"Annotated PDF with page boxes saved to: {annotated_pdf_path}", level="INFO")

        log_progress(json.dumps(extracted_json_paths), level="DATA")
        return {
            "success": True,
            "output_path": str(output_dir),
            "pages_extracted": len(page_nums),
            "format": f"json+{text_format}" if write_text_file else "json",
            "json_output_paths": extracted_json_paths,
            "text_output_paths": extracted_text_paths,
        }

    except Exception as exc:
        log_progress(f"Fatal error during pymupdf extraction: {exc}", level="ERROR")
        raise
