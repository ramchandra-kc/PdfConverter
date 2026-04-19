"""Hybrid extraction method API."""

from __future__ import annotations

import json
from pathlib import Path

from pdf_converter.hybrid.core import hybrid_extract_pages
from pdf_converter.pymupdf.core import get_total_pages
from pdf_converter.shared.output_formatter import save_html_output, save_markdown_output
from pdf_converter.shared.utils import log_progress


def extract_with_hybrid(
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
    """Extract with PyMuPDF base pipeline and OCR table replacement."""
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

        log_progress(f"Hybrid extraction: {input_path}", level="INFO")
        log_progress(f"Pages: {[p + 1 for p in page_nums]} (1-indexed)", level="INFO")
        log_progress(
            f"Output format: json{'+text' if write_text_file else ''}, text format: {text_format}, per-page: {page_per_json}",
            level="INFO",
        )

        extracted_json_paths: list[str] = []
        extracted_text_paths: list[str] = []
        text_ext = "html" if text_format == "html" else "md"
        text_dir = output_dir / text_ext

        pages_object, replaced_tables = hybrid_extract_pages(
            input_path=input_path,
            image_dir=str(image_dir),
            page_nums=page_nums,
            text_format=text_format,
            lang=lang,
            dpi=dpi,
        )

        if page_per_json:
            for page_data in pages_object:
                actual_page_num = page_data.get("metadata", {}).get("page_number", 1)
                page_json_path = json_dir / f"{pdf_file_name}_page_{actual_page_num}.json"
                with open(page_json_path, "w", encoding="utf-8") as file_obj:
                    json.dump(page_data, file_obj, ensure_ascii=False, indent=2)
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
            output_file_path = json_dir / f"{pdf_file_name}_extracted.json"
            with open(output_file_path, "w", encoding="utf-8") as file_obj:
                json.dump(pages_object, file_obj, ensure_ascii=False, indent=2)
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

        if draw_page_boxes_pdf:
            from pdf_converter.shared.pdf_annotations import draw_page_boxes_pdf

            annotated_pdf_path = draw_page_boxes_pdf(
                pdf_path=input_path,
                extracted_json_paths=extracted_json_paths,
                output_dir=output_dir,
            )
            if annotated_pdf_path:
                log_progress(f"Annotated PDF with page boxes saved to: {annotated_pdf_path}", level="INFO")

        log_progress(f"Hybrid extraction completed. Tables replaced via OCR: {replaced_tables}", level="INFO")
        
        log_progress(json.dumps(extracted_json_paths), level="DATA")
        return {
            "success": True,
            "output_path": str(output_dir),
            "pages_extracted": len(page_nums),
            "format": f"json+{text_format}" if write_text_file else "json",
            "json_output_paths": extracted_json_paths,
            "text_output_paths": extracted_text_paths,
            "tables_replaced": replaced_tables,
        }

    except Exception as exc:
        log_progress(f"Fatal error during hybrid extraction: {exc}", level="ERROR")
        raise
