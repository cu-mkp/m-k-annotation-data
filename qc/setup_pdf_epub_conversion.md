# PDF and EPUB Conversion Setup Guide

This guide will help you set up the environment to convert HTML files into attractive PDFs and EPUBs using the academic-print.css stylesheet.

## Overview

The conversion system includes:
- **Academic CSS stylesheet** (`academic-print.css`) - Professional formatting for scholarly content
- **Python conversion script** (`convert_to_pdf_epub.py`) - Batch conversion tool
- **WeasyPrint** - Modern CSS-to-PDF engine with excellent typography support
- **Pandoc** - Universal document converter for EPUB generation

## Prerequisites

### Python Environment
Ensure you're using the virtual environment in the qc directory:

```bash
cd qc
source venv/bin/activate
```

### System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install pandoc for EPUB generation
brew install pandoc

# Install system libraries for WeasyPrint
brew install cairo pango gdk-pixbuf libffi
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install pandoc
sudo apt install pandoc

# Install system libraries for WeasyPrint
sudo apt install build-essential python3-dev python3-pip python3-cffi \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info
```

#### Windows
```bash
# Install pandoc using chocolatey
choco install pandoc

# Or download from: https://pandoc.org/installing.html
```

### Python Dependencies

With your virtual environment activated:

```bash
# Install required Python packages
pip install weasyprint beautifulsoup4 requests

# Verify installation
python -c "import weasyprint; print('WeasyPrint installed successfully')"
python -c "import bs4; print('BeautifulSoup4 installed successfully')"
```

## Usage

### Basic Conversion

Convert all HTML files to both PDF and EPUB:

```bash
cd qc
source venv/bin/activate
python convert_to_pdf_epub.py
```

### Advanced Options

#### Create only PDFs:
```bash
python convert_to_pdf_epub.py --pdf-only
```

#### Create only EPUBs:
```bash
python convert_to_pdf_epub.py --epub-only
```

#### Specify custom output directory:
```bash
python convert_to_pdf_epub.py --output-dir /path/to/output
```

#### Specify custom HTML directory:
```bash
python convert_to_pdf_epub.py --html-dir /path/to/html/files
```

### Complete Example
```bash
# Convert only to PDF, save to custom directory
python convert_to_pdf_epub.py --pdf-only --output-dir ./my_pdfs --html-dir ../html
```

## Output Structure

The conversion creates the following directory structure:

```
converted_documents/
├── pdfs/
│   ├── document1.pdf
│   ├── document2.pdf
│   └── ...
├── epubs/
│   ├── document1.epub
│   ├── document2.epub
│   └── ...
└── conversion_report.txt
```

## Features

### PDF Generation (WeasyPrint)
- **High-quality typography** using Times New Roman
- **Professional page layout** with headers, footers, and page numbers
- **Academic formatting** for footnotes, citations, and bibliographies
- **Proper image handling** with scaling and borders
- **Page break control** to avoid awkward breaks
- **Print-optimized** with URL printing for references

### EPUB Generation (Pandoc)
- **Responsive design** that adapts to different screen sizes
- **Proper metadata** including language settings
- **Self-contained** with embedded styles and images
- **Accessible** with proper heading structure

### CSS Stylesheet Features
- **Typography**: Professional fonts with proper line spacing
- **Academic elements**: Specialized styling for footnotes, citations, figures
- **Page layout**: A4 format with appropriate margins
- **Responsive design**: Adapts to both print and digital formats
- **Accessibility**: High contrast mode support

## Troubleshooting

### Common Issues

#### WeasyPrint Installation Problems
```bash
# On macOS, if you get cairo/pango errors:
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
pip install weasyprint

# On Linux, ensure all system dependencies are installed:
sudo apt install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev
```

#### Pandoc Not Found
```bash
# Verify pandoc installation
pandoc --version

# If not found, reinstall:
# macOS: brew install pandoc
# Linux: sudo apt install pandoc
# Windows: choco install pandoc
```

#### Image Loading Issues
- Ensure image paths in HTML are correct relative to the HTML file
- The script converts relative paths to absolute paths automatically
- Missing images will generate warnings but won't stop conversion

#### Font Issues in PDFs
- The CSS uses system fonts (Times New Roman)
- If fonts are missing, WeasyPrint will substitute similar fonts
- For consistent results across systems, consider embedding fonts

### Performance Tips

#### For Large Batches
- Use `--pdf-only` or `--epub-only` to process faster
- Monitor system memory usage for very large HTML files
- Consider processing in smaller batches if memory is limited

#### Optimizing Output Size
- Images are automatically scaled for appropriate PDF size
- Large images may increase PDF file size significantly
- Consider optimizing source images if file size is a concern

## Customization

### Modifying the CSS
Edit `academic-print.css` to customize:
- Typography (fonts, sizes, spacing)
- Page layout (margins, headers, footers)
- Academic formatting (footnote styles, citation formatting)
- Color scheme and visual design

### Adding Metadata
The script automatically adds:
- Document title from first H1 or filename
- UTF-8 encoding
- Responsive viewport settings

## Quality Control

### Validation
- Check the `conversion_report.txt` for any errors
- Review sample outputs to ensure formatting meets requirements
- Test on different devices for EPUB compatibility

### Best Practices
- Keep HTML well-formed for best conversion results
- Use semantic HTML elements (h1, h2, p, etc.)
- Ensure all referenced images exist
- Test CSS changes with a small subset first

## Integration with Existing Workflow

This tool complements the existing QC tools:
1. **Link checking** (`check_broken_links.py`) - Verify all links work
2. **Content validation** - Ensure HTML is well-formed
3. **PDF/EPUB generation** - Create publication-ready formats

For a complete workflow:
```bash
# 1. Check for broken links
python check_broken_links.py

# 2. Fix any issues found

# 3. Generate PDFs and EPUBs
python convert_to_pdf_epub.py

# 4. Review conversion report and sample outputs
```

## Support

For issues with the conversion tools:
1. Check the conversion report for specific error messages
2. Verify all dependencies are properly installed
3. Test with a single HTML file first
4. Review the CSS for any syntax errors

The tools are designed to be robust and provide detailed error reporting to help identify and resolve issues quickly.