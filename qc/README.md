# Quality Control (QC) Directory

This directory contains tools and scripts for quality control and validation of the m-k-annotation-data project. The tools help maintain data integrity, identify issues, and ensure the reliability of links and resources referenced in the HTML files.

## Directory Contents

### Scripts

#### `convert_to_pdf_epub.py` ⭐ **PRIMARY VERSION**
**Purpose:** HTML to PDF/EPUB converter with enhanced academic formatting  
**Description:** Professional tool that converts HTML files to attractive PDFs and EPUBs with enhanced footnote formatting. Features improved superscript sizing, better endnotes styling, enhanced frontmatter, and professional typography.

#### `convert_to_pdf_epub_original.py`
**Purpose:** Original HTML to PDF/EPUB converter (backup)  
**Description:** Original version before footnote enhancements. Kept as backup for reference.

#### `convert_to_pdf_epub_footnotes.py`
**Purpose:** Experimental footnotes converter (complex version)  
**Description:** Experimental version that attempted to convert endnotes to bottom-of-page footnotes. Had rendering issues - use the primary version instead.

**Key Features (Primary Version):**
- **Enhanced Footnote Formatting:** Proper superscript sizing (9pt) and improved styling
- **Figure Reference Linking:** Automatic linking of figure references (Fig. 1, Fig. 2) to actual figures
- **Clean External Links:** Removes URL display from link text while maintaining hyperlinks
- **Professional Frontmatter:** Enhanced title page, citation page, and abstract with metadata
- **Academic CSS Integration:** Uses `academic-print.css` with enhanced footnote styles
- **Dual Format Support:** Creates both PDF (via WeasyPrint) and EPUB (via Pandoc) formats
- **Batch Processing:** Converts all HTML files in a directory automatically
- **Smart HTML Preparation:** Optimizes HTML structure and embeds CSS for conversion
- **Image Handling:** Converts relative paths and handles missing images gracefully
- **Progress Tracking:** Real-time progress with detailed conversion reports
- **Enhanced Notes Section:** Better styling for endnotes with proper typography

**Usage (Primary Version):**
```bash
# Convert all files to both PDF and EPUB
python convert_to_pdf_epub.py

# Create only PDFs
python convert_to_pdf_epub.py --pdf-only

# Create only EPUBs  
python convert_to_pdf_epub.py --epub-only

# Custom output directory
python convert_to_pdf_epub.py --output-dir ./my_documents
```

**Output:** Creates organized directory structure with PDFs, EPUBs, and conversion report

**Dependencies:**
- `weasyprint` - Modern CSS-to-PDF engine
- `beautifulsoup4` - HTML parsing and manipulation
- `pandoc` - Universal document converter (system package)

**Setup Guide:** See `setup_pdf_epub_conversion.md` for detailed installation instructions

#### `check_broken_links.py`
**Purpose:** Comprehensive broken link checker for HTML files  
**Description:** Advanced tool that scans all HTML files in the `../html` directory to identify broken links, missing images, and inaccessible resources. Uses parallel processing with intelligent rate limiting and browser headers to minimize false positives.

**Key Features:**
- **Parallel Processing:** Uses multiple worker threads with configurable batch sizes
- **Rate Limiting:** Domain-specific delays to respect server resources and avoid being blocked
- **Browser Headers:** Mimics real browser requests to bypass basic bot detection
- **Smart Retry Logic:** Falls back from HEAD to GET requests when needed
- **Categorized Results:** Distinguishes between definitely broken links and those that may work in browsers
- **Progress Tracking:** Real-time progress reporting with intermediate saves
- **Comprehensive Reporting:** Detailed output with actionable categorized results

**Usage:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install requests beautifulsoup4

# Run the checker
python check_broken_links.py
```

**Output:** Creates `broken_links_report.txt` with detailed results

**Dependencies:**
- `requests` - HTTP library for web requests
- `beautifulsoup4` - HTML parsing library
- `urllib3` - Low-level HTTP client (installed with requests)

#### `check_hrefs.sh`
**Purpose:** Basic shell script for checking links  
**Description:** Simple bash script for preliminary link validation. Provides basic functionality for URL checking without the advanced features of the Python script.

#### `check_sheets.py`
**Purpose:** Validation tool for spreadsheet data  
**Description:** Python script for checking and validating data in spreadsheet files, ensuring data consistency and identifying potential issues.

#### `debug_uuid.py`
**Purpose:** UUID debugging and validation tool  
**Description:** Utility for debugging UUID-related issues in the data, helping identify malformed or duplicate UUIDs.

#### `test_url_extraction.py`
**Purpose:** URL extraction testing utility  
**Description:** Test script for validating URL extraction logic and ensuring proper parsing of links from HTML content.

#### `academic-print.css`
**Purpose:** Professional CSS stylesheet for PDF/EPUB generation  
**Description:** Comprehensive stylesheet designed for academic content with proper typography, page layout, and specialized formatting for scholarly elements.

**Features:**
- **Professional Typography:** Times New Roman with optimized line spacing and justification
- **Page Layout:** A4 format with headers, footers, and appropriate margins
- **Academic Elements:** Specialized styling for footnotes, citations, figures, and bibliographies
- **Responsive Design:** Adapts to both print (PDF) and digital (EPUB) formats
- **Print Optimization:** Proper page breaks, URL printing, and high-contrast support

### Configuration Files

#### `setup_pdf_epub_conversion.md`
**Purpose:** Complete setup guide for PDF/EPUB conversion  
**Description:** Detailed installation and usage instructions for the document conversion system, including dependency installation, troubleshooting, and customization options.

#### `media-full-list-alt-text-permissions.xlsx`
**Purpose:** Media permissions and alt-text tracking  
**Description:** Spreadsheet containing comprehensive information about media files, including alt-text descriptions and usage permissions.

### Virtual Environment

#### `venv/`
**Purpose:** Python virtual environment  
**Description:** Isolated Python environment containing all required dependencies for the QC tools. Ensures consistent package versions and avoids conflicts with system Python packages.

**Setup:**
```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install requests beautifulsoup4
```

### Log Files

#### `logs/`
**Purpose:** Directory containing various log files and reports  
**Description:** Centralized location for storing output from QC tools and analysis results.

**Contents:**
- `href_frq.txt` - Link frequency analysis
- `href_spider_log.txt` - Web spider log output
- `href_uniq.txt` - Unique links list
- `lizard-2.21.20.txt` - Code complexity analysis results
- `xmlwf_err_cnt.txt` - XML well-formedness error counts
- `xmlwf_errs.html` - XML error report in HTML format
- `xmlwf_errs.txt` - XML error report in text format
- `make_error_frq_count.sh` - Script for generating error frequency counts

### Output Files

#### `broken_links_report.txt`
**Purpose:** Generated report from broken link checker  
**Description:** Comprehensive report containing:
- Summary statistics (files checked, links found, broken links)
- Categorized broken links by file
- Distinction between definitely broken and potentially browser-accessible links
- Detailed error information for debugging

**Report Categories:**
- 🔴 **DEFINITELY BROKEN:** Links that are confirmed broken
- 🟡 **WORKS IN BROWSER:** Links that fail automated checks but work with browser headers
- 🟠 **MAY WORK IN BROWSER:** Links that may be accessible in browsers despite automation failures

#### `no-match-by-file.txt`
**Purpose:** File-specific mismatch tracking  
**Description:** Report of files that don't match expected patterns or contain unexpected content.

#### `pbcopy`
**Purpose:** Temporary clipboard data  
**Description:** Temporary file containing data copied to clipboard during analysis sessions.

## Best Practices

### Running Quality Control Checks

1. **Regular Monitoring:** Run broken link checks regularly, especially after content updates
2. **Environment Isolation:** Always use the virtual environment to ensure consistent results
3. **Resource Respect:** The tools implement rate limiting - avoid bypassing these safeguards
4. **Progress Tracking:** Monitor progress through console output and intermediate report files
5. **Result Analysis:** Review categorized results to prioritize fixes (definitely broken vs. potentially working)

### Interpreting Results

- **403 Forbidden:** Often academic paywalls or authentication-required sites
- **404 Not Found:** Genuinely missing pages or moved content
- **DNS Failures:** Dead domains or network connectivity issues
- **Timeout Errors:** Slow or unresponsive servers
- **406 Not Acceptable:** May work in browsers despite automation failure

### Maintenance

- **Dependencies:** Keep Python packages updated for security and compatibility
- **Virtual Environment:** Recreate venv periodically to ensure clean environment
- **Log Rotation:** Archive old log files to prevent disk space issues
- **Report Analysis:** Regular review of QC reports to identify patterns and trends

## Troubleshooting

### Common Issues

1. **Virtual Environment Issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install requests beautifulsoup4
   ```

2. **Network Connectivity:**
   - Ensure stable internet connection
   - Check firewall settings
   - Verify DNS resolution

3. **Rate Limiting:**
   - Script implements automatic rate limiting
   - If blocked, wait before retrying
   - Consider adjusting delays in script configuration

4. **Memory Issues:**
   - For large datasets, monitor system memory
   - Consider processing in smaller batches
   - Close other applications if needed

### Support

For issues with QC tools:
1. Check log files for detailed error information
2. Verify all dependencies are properly installed
3. Ensure virtual environment is activated
4. Review network connectivity and permissions

## Development

### Contributing

When modifying QC tools:
1. Test changes in isolated environment
2. Update documentation for new features
3. Add appropriate error handling
4. Include progress reporting for long-running operations
5. Respect rate limiting and server resources

### Configuration

Key configuration parameters in `check_broken_links.py`:
- `batch_size`: Number of URLs per batch (default: 20)
- `max_workers`: Concurrent worker threads (default: 4)
- `timeout`: Request timeout in seconds (default: 10)
- Domain-specific delays in `get_domain_delay()` function

Adjust these values based on:
- Available system resources
- Network bandwidth
- Target server responsiveness
- Desired balance between speed and politeness