"""OCR extraction method API."""

from __future__ import annotations

from pathlib import Path
import json
from pdf_converter.ocr.core import build_page_boxes, extract_regions_from_image
from pdf_converter.ocr.ocr_utils import load_image
from pdf_converter.ocr.render import (
    render_html_from_ocr_regions,
    render_markdown_from_ocr_regions,
)
from pdf_converter.shared.utils import (
    build_page_metadata,
    log_progress,
    get_page_count,
)
from pdf_converter.shared.output_formatter import (
    save_html_output,
    save_markdown_output,
)


def extract_with_ocr(
    input_path: str,
    output_path: str | None = None,
    page_nums: list[int] | None = None,
    text_format: str = "html",
    page_per_json: bool = False,
    write_text_file: bool = False,
    lang: str = "eng",
    dpi: int = 200,
    draw_page_boxes_pdf: bool = False,
) -> dict:
    """
    Extract content from PDF or image using OCR method.

    Args:
        input_path: Path to PDF or image file
        output_path: Output directory or file path
        page_nums: List of 0-indexed page numbers to extract (all if None)
        text_format: 'html' or 'md' text rendering used inside JSON output
        page_per_json: If True, save one JSON file per page
        write_text_file: If True, save one .html/.md file per page (or a single merged file)
        lang: Tesseract language code
        dpi: DPI for PDF rendering

    Returns:
        Result dictionary with output metadata and file paths
    """
    total_pages = get_page_count(input_path)
    
    if page_nums is None:
        page_nums = list(range(total_pages))

    output_dir = Path(output_path) if output_path else Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    image_dir = output_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    json_dir = output_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)

    pdf_file_name = Path(input_path).stem

    log_progress(f"OCR extraction: {input_path}", level="INFO")
    log_progress(f"Pages: {[p + 1 for p in page_nums]} (1-indexed)", level="INFO")
    log_progress(
        f"Output format: json{'+text' if write_text_file else ''}, text format: {text_format}, per-page: {page_per_json}",
        level="INFO",
    )

    all_pages_data = []
    extracted_json_paths = []
    extracted_text_paths = []
    text_ext = "html" if text_format == "html" else "md"
    text_dir = output_dir / text_ext

    for page_idx in page_nums:
        actual_page_num = page_idx + 1  # Convert to 1-indexed for page loading
        log_progress(f"Processing page {actual_page_num}/{total_pages} ...", level="INFO")

        img = load_image(input_path, page=actual_page_num, dpi=dpi)
        regions = extract_regions_from_image(img, lang=lang)

        page_boxes = build_page_boxes(regions, dpi=dpi)
        metadata = build_page_metadata(page_idx, total_pages, input_path, "ocr")

        # Generate both HTML and Markdown for unified output
        if text_format == "html":
            rendered_text = render_html_from_ocr_regions(regions)
        else:
            rendered_text = render_markdown_from_ocr_regions(regions)
        page_data = {
            "metadata": metadata,
            "page_boxes": page_boxes,
            "text": rendered_text,
        }

        if write_text_file and page_per_json:
            page_text_path = text_dir / f"{pdf_file_name}_page_{actual_page_num}.{text_ext}"
            page_title = f"{pdf_file_name} - Page {actual_page_num}"
            if text_format == "html":
                save_html_output(rendered_text, page_text_path, title=page_title)
            else:
                save_markdown_output(rendered_text, page_text_path, title=page_title)
            extracted_text_paths.append(str(page_text_path))
            log_progress(f"Saved: {page_text_path}", level="INFO")
        
        if page_per_json:
            page_json_path = json_dir / f"{pdf_file_name}_page_{actual_page_num}.json"

            with open(page_json_path, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)

            log_progress(f"Saved: {page_json_path}", level="INFO")
            extracted_json_paths.append(str(page_json_path))
        else:
            all_pages_data.append(page_data)

    if not page_per_json:
        output_json_path = json_dir / f"{pdf_file_name}_extracted.json"
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(all_pages_data, f, ensure_ascii=False, indent=2)
        extracted_json_paths.append(str(output_json_path))
        
        log_progress(f"Saved: {Path(json_dir) / f'{pdf_file_name}_extracted.json'}", level="INFO")

        if write_text_file:
            merged_text_path = text_dir / f"{pdf_file_name}_extracted.{text_ext}"
            if text_format == "html":
                merged_parts = []
                for page_data in all_pages_data:
                    page_num = page_data["metadata"]["page_number"]
                    merged_parts.append(
                        f'<section class="page" data-page="{page_num}"><h2>Page {page_num}</h2>{page_data["text"]}</section>'
                    )
                merged_text = "\n".join(merged_parts)
                save_html_output(merged_text, merged_text_path, title=f"{pdf_file_name} Extracted")
            else:
                merged_parts = []
                for page_data in all_pages_data:
                    page_num = page_data["metadata"]["page_number"]
                    merged_parts.append(f"## Page {page_num}\n\n{page_data['text']}")
                merged_text = "\n\n---\n\n".join(merged_parts)
                save_markdown_output(merged_text, merged_text_path, title=f"{pdf_file_name} Extracted")
            extracted_text_paths.append(str(merged_text_path))
            log_progress(f"Saved: {merged_text_path}", level="INFO")
    
    if draw_page_boxes_pdf:
        from pdf_converter.shared.pdf_annotations import draw_page_boxes_pdf
        annotated_pdf_path = draw_page_boxes_pdf(
            pdf_path=input_path,
            extracted_json_paths=extracted_json_paths,
            output_dir=output_dir,
        )
        if annotated_pdf_path:
            log_progress(f"Annotated PDF with page boxes saved: {annotated_pdf_path}", level="INFO")
        else:
            log_progress("Failed to create annotated PDF with page boxes", level="ERROR")
            
    log_progress(json.dumps(extracted_json_paths), level="DATA")
    return {
        "success": True,
        "output_path": str(output_dir),
        "pages_extracted": len(page_nums),
        "format": f"json+{text_format}" if write_text_file else "json",
        "json_output_paths": extracted_json_paths,
        "text_output_paths": extracted_text_paths,
    }
