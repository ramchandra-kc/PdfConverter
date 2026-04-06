# pdf-extractor

A unified PDF extraction tool supporting multiple extraction methods: OCR-based custom pipeline and pymupdf4llm library-based extraction. Extract document structure from PDFs or images and render it as semantic HTML, Markdown, or JSON.

## Features

### Extraction Methods

**OCR Method** (`--method ocr`)
- Supports PDF and image formats (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`, `.webp`)
- OCR via Tesseract with configurable language support
- Region detection and classification into semantic blocks (headings, paragraphs, lists, tables)
- Table extraction with cell detection
- Debug visualization overlays
- **Best for**: Scanned PDFs, images, multi-language documents

**PyMuPDF Method** (`--method pymupdf`)
- Fast PDF text extraction using PyMuPDF and pymupdf4llm
- Native image extraction from PDFs
- URL and email linkification
- Lightweight, fewer dependencies
- **Best for**: Native PDFs with embedded text, quick extraction, minimal overhead

### Common Features

- Output formats: HTML, Markdown, JSON
- Output modes: whole document or per-page files
- Page range selection
- Progress logging and structured output
- Unified Python API and CLI interface

## Requirements

- Python 3.10+
- Tesseract OCR (for OCR method): `brew install tesseract poppler` on macOS
- PyMuPDF (automatically installed)
- pymupdf4llm library (installed from GitHub)

## Installation

```bash
# Clone or navigate to the project
cd pdf-extractor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Quick Start

### OCR Method - Scanned PDF

```bash
pdf-extractor --input data/scanned.pdf --method ocr --output outputs/result.html
```

### PyMuPDF Method - Native PDF

```bash
pdf-extractor --input data/native.pdf --method pymupdf --output outputs/result.html
```

### Usage Examples

**OCR: Single page**
```bash
pdf-extractor --input data/sample.pdf --method ocr --page 2
```

**OCR: Page range**
```bash
pdf-extractor --input data/sample.pdf --method ocr --pages 2-5 --output outputs/pages_2_5.html
```

**OCR: Markdown output with French language**
```bash
pdf-extractor --input data/sample.pdf --method ocr --output-format md --lang fra
```

**PyMuPDF: Per-page JSON output**
```bash
pdf-extractor --input data/sample.pdf --method pymupdf --output-format json --output-mode per-page
```

**OCR: Without debug overlay**
```bash
pdf-extractor --input data/sample.pdf --method ocr
```

**PyMuPDF: Extract with custom output directory**
```bash
pdf-extractor --input data/sample.pdf --method pymupdf --output outputs/custom_dir
```

## CLI Options

```
--input, -i              Input file path (PDF or image) [REQUIRED]
--method                 ocr | pymupdf [REQUIRED]
--output, -o             Output directory path (default: outputs)
--text-format, -f        html | md (default: md)
--page-per-json          Write one JSON file per selected page
--write-text-file        Also write real .html/.md files (uses --text-format)
--draw-page-boxes-pdf    Also write an annotated PDF with page_boxes bbox rectangles
--start-page             Start page number (1-indexed)
--end-page               End page number (1-indexed, inclusive)
--lang, -l               Tesseract language code (OCR only, default: eng)
--dpi                    PDF render DPI for OCR (OCR only, default: 200)
```

JSON output is always generated. Use --write-text-file to additionally generate .html or .md files, and in --page-per-json mode text files are also generated per page.

Use --draw-page-boxes-pdf to generate an additional PDF in the output directory named <input_stem>_boxed.pdf with rectangles drawn from each page's page_boxes.bbox values.

## JSON Output Format

Each page is output as a JSON object with:

```json
{
  "metadata": {
    "page_number": 1,
    "total_pages": 26,
    "file_path": "./sample/sample.pdf",
    "extraction_method": "ocr"
  },
  "page_boxes": [
    {
      "index": 0,
      "class": "paragraph",
      "bbox": [40.1, 808.01, 587.22, 775.64],
      "text": "extracted text content"
    }
  ],
  "rendered_html": "<p>extracted text content</p>",
  "rendered_markdown": "extracted text content\n"
}
```

For whole-document output, JSON contains an array of page objects.

## API Usage (Python)

```python
from pdf_extractor import extract_from_pdf

# OCR extraction
result = extract_from_pdf(
    input_path="./sample.pdf",
    method="ocr",
    output_format="html",
    lang="eng",
    dpi=200
)

# PyMuPDF extraction
result = extract_from_pdf(
    input_path="./sample.pdf",
    method="pymupdf",
    output_format="json",
    per_page_output=False
)
```

## Project Structure

```
pdf-extractor/
  pyproject.toml
  README.md

  pdf_extractor/
    __init__.py           # Main API entry point
    cli.py                # Unified CLI interface

    shared/               # Shared modules
      __init__.py
      output_formatter.py # Unified HTML/MD/JSON rendering
      utils.py            # Logging, file I/O, utilities
      cli_base.py         # Common CLI argument parsing

    ocr/                  # OCR extraction method
      __init__.py
      api.py              # OCR method wrapper
      core.py             # Main OCR extraction pipeline
      region_classification.py
      region_segmentation.py
      table_extraction.py
      ocr_utils.py

    pymupdf/              # PyMuPDF extraction method
      __init__.py
      api.py              # PyMuPDF method wrapper
      core.py             # PyMuPDF extraction orchestration
      render.py
  
  tests/
    test_integration.py  # Integration tests
  
  data/                   # Sample input files
  outputs/                # Generated output files
```

## Method Comparison

### OCR Method
- **Strengths**: Handles scanned PDFs, images, any language with Tesseract model
- **Weaknesses**: Slower, requires Tesseract installation, OCR errors
- **Best for**: Scanned documents, poor-quality PDFs, non-English content
- **Dependencies**: Tesseract, Poppler, OpenCV

### PyMuPDF Method
- **Strengths**: Fast, lightweight, native PDF support, image extraction
- **Weaknesses**: Fails on scanned PDFs, no image input support
- **Best for**: Standard PDFs with embedded text, quick extraction
- **Dependencies**: PyMuPDF, pymupdf4llm

## Troubleshooting

### Tesseract Not Found (OCR Method)

Ensure Tesseract is installed and in your PATH:

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
Download installer from https://github.com/UB-Mannheim/tesseract/wiki

### Poor OCR Quality

Try increasing DPI and verify correct language is installed:
```bash
pdf-extractor --input data/sample.pdf --method ocr --dpi 300 --lang eng
```

### PyMuPDF Extraction Fails

Ensure pymupdf4llm is installed correctly:
```bash
pip install git+https://github.com/ramchandra-kc/pymupdf4llm.git
```

## Contributing

Both extraction methods live in separate modules under `pdf_extractor/ocr/` and `pdf_extractor/pymupdf/`. Improvements to either method should be made in the respective module, then tested against the unified interface.

## License

MIT
