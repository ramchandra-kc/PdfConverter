# Installation Guide

This guide will help you install and set up the unified pdf-extractor project with both OCR and pymupdf4llm extraction methods.

## Prerequisites

- **Python 3.10 or higher**
- **pip** (Python package manager)
- For OCR method: **Tesseract OCR** and **Poppler**

## System Dependencies

### macOS

Install Tesseract and Poppler using Homebrew:

```bash
brew install tesseract poppler
```

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils libsm6 libxext6
```

### Windows

1. **Tesseract**: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
2. **Poppler**: Download from https://github.com/oschwartz10612/poppler-windows/releases

After installation, add the paths to your system PATH or configure them in your Python code.

## Python Package Installation

### 1. Clone or Navigate to Project

```bash
cd pdf-extractor
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install pdf-extractor

Install in development mode (recommended for development):

```bash
pip install -e .
```

Or install from source:

```bash
pip install .
```

### 5. Verify Installation

Test the installation:

```bash
# Check if CLI is available
pdf-extractor --help

# Or run the integration tests
python tests/test_integration.py
```

## Dependency Details

The project has the following key dependencies:

### Core Dependencies
- **NumPy**: Numerical computing
- **OpenCV (cv2)**: Image processing for OCR method
- **Pillow**: Image handling
- **PyMuPDF (fitz)**: PDF parsing for pymupdf method
- **pytesseract**: Python wrapper for Tesseract OCR

### For OCR Method
- **Tesseract OCR**: Must be installed separately (system package)
- **pdf2image**: PDF to image conversion
- **Poppler**: Required by pdf2image for PDF rendering

### For PyMuPDF Method
- **pymupdf4llm**: Custom library from https://github.com/ramchandra-kc/pymupdf4llm.git
- **PyMuPDF**: PDF parsing library

## Troubleshooting

### Issue: "tesseract is  not installed" or can't find Tesseract

**Solution**: Ensure Tesseract is installed and in your PATH:

```bash
# macOS
brew install tesseract

# Linux (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Check installation
tesseract --version
```

If Tesseract is installed but still getting errors, specify the path in your code:

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
pytesseract.pytesseract.pytesseract_cmd = '/usr/local/bin/tesseract'  # macOS
```

### Issue: "pdf2image requires Poppler"

**Solution**: Install Poppler:

```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils

# Windows - download from https://github.com/oschwartz10612/poppler-windows/releases
```

### Issue: OpenCV (cv2) import errors

**Solution**: Reinstall OpenCV:

```bash
pip install --force-reinstall opencv-python
```

If you have multiple Python environments, ensure you're using the correct one:

```bash
which python  # Check which Python is being used
which pip
```

### Issue: pymupdf4llm not installing

**Solution**: Install from GitHub directly with proper git handling:

```bash
pip install git+https://github.com/ramchandra-kc/pymupdf4llm.git
```

If you get SSL certificate errors, try:

```bash
pip install --trusted-host github.com git+https://github.com/ramchandra-kc/pymupdf4llm.git
```

## Verifying Dependencies

Check what's installed:

```bash
pip list | grep -E "(pdf|ocr|pymupdf|tesseract|pillow|opencv)"
```

Check if Tesseract works:

```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

Check if PyMuPDF works:

```bash
python -c "import fitz; print(fitz.version)"
```

Check if pymupdf4llm works:

```bash
python -c "import pymupdf4llm; print('pymupdf4llm installed')"
```

## Development Installation

For development with additional tools:

```bash
pip install -e ".[dev]"
```

This installs additional testing and linting tools:
- pytest
- pytest-cov
- black
- ruff

## Next Steps

Once installed, you can:

1. **Use the CLI**:
   ```bash
   pdf-extractor --input sample.pdf --method ocr --output output.html
   pdf-extractor --input sample.pdf --method pymupdf --output output.md
   ```

2. **Use as a Python library**:
   ```python
   from pdf_extractor import extract_from_pdf
   
   result = extract_from_pdf("sample.pdf", method="ocr", output_format="html")
   ```

3. **Read the main README.md** for detailed usage examples and feature information.

## Getting Help

- Check the [README.md](README.md) for algorithm documentation and usage examples
- Run `pdf-extractor --help` for CLI options
- Check the source code in `pdf_extractor/` for implementation details
- Review the test files in `tests/` for integration examples

## Quick Test

To quickly verify everything works (requires test PDF):

```bash
# If you have a sample PDF in data/ directory:
python -c "
from pdf_extractor import extract_from_pdf
result = extract_from_pdf('data/sample.pdf', method='ocr', page_nums=[0], output_format='html')
print('Extraction successful!' if result['success'] else 'Extraction failed')
"
```

## Uninstallation

To uninstall pdf-extractor:

```bash
pip uninstall pdf-extractor
```

To completely remove all dependencies:

```bash
pip uninstall pdf-extractor pillow numpy opencv-python pdf2image PyMuPDF pytesseract pymupdf4llm -y
```

Note: This will not remove system dependencies (Tesseract, Poppler). Remove those separately using your system package manager if desired.
