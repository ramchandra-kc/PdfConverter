"""Unified CLI for pdf-converter."""

from __future__ import annotations

import sys

from pdf_converter.hybrid import extract_with_hybrid
from pdf_converter.ocr import extract_with_ocr
from pdf_converter.pymupdf import extract_with_pymupdf
from pdf_converter.shared import (
    create_base_parser,
    validate_arguments,
    print_method_info,
    parse_page_range,
    get_page_count,
)


def main() -> int:
    """Main CLI entry point."""
    parser = create_base_parser()
    args = parser.parse_args()

    try:
        # Validate arguments
        validate_arguments(args)

        # Get total pages
        total_pages = get_page_count(args.input)

        # Parse page range
        try:
            page_nums = parse_page_range(args.start_page, args.end_page, total_pages)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        print_method_info(args.method)

        # Route to appropriate extraction method
        if args.method == "ocr":
            result = extract_with_ocr(
                input_path=args.input,
                output_path=args.output,
                page_nums=page_nums,
                text_format=args.text_format,
                page_per_json=args.page_per_json,
                write_text_file=args.write_text_file,
                lang=args.lang,
                dpi=args.dpi,
                draw_page_boxes_pdf=args.draw_page_boxes_pdf,
            )
        elif args.method == "hybrid":
            result = extract_with_hybrid(
                input_path=args.input,
                output_path=args.output,
                page_nums=page_nums,
                text_format=args.text_format,
                page_per_json=args.page_per_json,
                write_text_file=args.write_text_file,
                lang=args.lang,
                dpi=args.dpi,
                draw_page_boxes_pdf=args.draw_page_boxes_pdf,
            )
        elif args.method == "pymupdf":
            result = extract_with_pymupdf(
                input_path=args.input,
                output_path=args.output,
                page_nums=page_nums,
                text_format=args.text_format,
                page_per_json=args.page_per_json,
                write_text_file=args.write_text_file,
                draw_page_boxes_pdf=args.draw_page_boxes_pdf,
            )
        else:
            print(f"Error: Unknown method '{args.method}'", file=sys.stderr)
            return 1

        if result.get("success"):

            print(f"\nExtraction completed successfully!")
            print(f"Output saved to: {result.get('output_path')}")
            print(f"Pages extracted: {result.get('pages_extracted')}")
            print(f"Format: {result.get('format')}")
            text_paths = result.get("text_output_paths") or []
            if text_paths:
                print(f"Text files written: {len(text_paths)}")
            return 0
        else:
            print(f"Error: Extraction failed", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
