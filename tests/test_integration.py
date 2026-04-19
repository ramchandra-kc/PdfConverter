"""Integration tests for pdf-converter."""

import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from pdf_converter import extract_from_pdf, extract_with_ocr, extract_with_pymupdf
        from pdf_converter.ocr import extract_with_ocr as ocr_api
        from pdf_converter.pymupdf import extract_with_pymupdf as pymupdf_api
        from pdf_converter.shared import (
            create_base_parser,
            validate_arguments,
            log_progress,
            get_page_count,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_cli_parser():
    """Test CLI argument parser."""
    try:
        from pdf_converter.shared import create_base_parser

        parser = create_base_parser()
        
        # Test with required arguments  
        args = parser.parse_args([
            "--input", "test.pdf",
            "--method", "ocr",
        ])
        
        assert args.input == "test.pdf"
        assert args.method == "ocr"
        assert args.text_format == "html"
        assert args.page_per_json is False
        
        print("✓ CLI parser works correctly")
        return True
    except Exception as e:
        print(f"✗ CLI parser test failed: {e}")
        return False


def test_shared_utils():
    """Test shared utility functions."""
    try:
        from pdf_converter.shared import build_page_metadata, get_output_path
        from pathlib import Path

        # Test metadata building
        metadata = build_page_metadata(0, 10, "test.pdf", "ocr")
        assert metadata["page_number"] == 1  # 0-indexed input, 1-indexed output
        assert metadata["total_pages"] == 10
        assert metadata["extraction_method"] == "ocr"

        # Test output path generation
        output_path = get_output_path("test.pdf", None, "json")
        assert "outputs" in output_path
        assert output_path.endswith("json")

        print("✓ Shared utils work correctly")
        return True
    except Exception as e:
        print(f"✗ Shared utils test failed: {e}")
        return False


def test_output_formatter():
    """Test output formatting functions."""
    try:
        from pdf_converter.shared import build_output_json

        # Test JSON output structure
        metadata = {
            "page_number": 1,
            "total_pages": 5,
            "file_path": "test.pdf",
            "extraction_method": "ocr",
        }
        page_boxes = [
            {
                "index": 0,
                "class": "paragraph",
                "bbox": [10, 20, 100, 50],
                "text": "Sample text",
            }
        ]

        output = build_output_json(metadata, page_boxes, "<p>Sample</p>", "Sample\n")
        
        assert output["metadata"] == metadata
        assert output["page_boxes"] == page_boxes
        assert output["rendered_html"] == "<p>Sample</p>"
        assert output["rendered_markdown"] == "Sample\n"

        print("✓ Output formatter works correctly")
        return True
    except Exception as e:
        print(f"✗ Output formatter test failed: {e}")
        return False


def test_extraction_methods_structure():
    """Test that extraction method modules have required exports."""
    try:
        from pdf_converter.ocr import extract_with_ocr
        from pdf_converter.pymupdf import extract_with_pymupdf

        # Check that functions are callable
        assert callable(extract_with_ocr)
        assert callable(extract_with_pymupdf)

        print("✓ Extraction method modules are properly structured")
        return True
    except Exception as e:
        print(f"✗ Extraction methods structure test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("pdf-converter Integration Tests")
    print("=" * 60)
    print()

    tests = [
        ("Imports", test_imports),
        ("CLI Parser", test_cli_parser),
        ("Shared Utils", test_shared_utils),
        ("Output Formatter", test_output_formatter),
        ("Extraction Methods Structure", test_extraction_methods_structure),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}...", end=" ")
        results.append((test_name, test_func()))
        print()

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
