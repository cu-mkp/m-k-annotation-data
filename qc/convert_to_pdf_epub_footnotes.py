#!/usr/bin/env python3
"""
PDF and EPUB Converter for HTML Files - Footnotes Version

This is a specialized version of the conversion script that converts endnotes to 
proper footnotes for better academic formatting. This version processes footnote
references and converts them to bottom-of-page footnotes in PDFs.

Key Features:
- Converts endnotes to proper footnotes
- Maintains all frontmatter enhancements
- Academic-focused CSS styling for professional output
- WeasyPrint for PDF generation with proper typography
- Enhanced footnote formatting and placement

Dependencies:
- weasyprint: Modern CSS-to-PDF engine
- beautifulsoup4: HTML parsing and manipulation
- requests: For handling external resources

Usage:
    python convert_to_pdf_epub_footnotes.py [--pdf-only] [--epub-only] [--output-dir OUTPUT]

Output:
    Creates PDF and/or EPUB files with proper footnote formatting
"""

import os
import sys
import argparse
import subprocess
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import weasyprint
from bs4 import BeautifulSoup
import shutil
import tempfile

def check_dependencies():
    """
    Check if required dependencies are installed.
    
    Returns:
        tuple: (missing_python_deps, missing_system_deps)
    """
    missing_python = []
    missing_system = []
    
    # Check Python dependencies
    try:
        import weasyprint
    except ImportError:
        missing_python.append("weasyprint")
    
    try:
        import bs4
    except ImportError:
        missing_python.append("beautifulsoup4")
    
    # Check system dependencies
    try:
        subprocess.run(['pandoc', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_system.append("pandoc")
    
    return missing_python, missing_system

def load_metadata(html_dir: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load annotations and authors metadata from JSON files.
    
    Args:
        html_dir (str): Directory containing the JSON files
        
    Returns:
        tuple: (annotations_data, authors_data)
    """
    annotations_file = os.path.join(html_dir, 'annotations.json')
    authors_file = os.path.join(html_dir, 'authors.json')
    
    annotations_data = {}
    authors_data = {}
    
    try:
        if os.path.exists(annotations_file):
            with open(annotations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert list to dict indexed by ID
                if 'content' in data:
                    annotations_data = {item['id']: item for item in data['content']}
    except Exception as e:
        print(f"Warning: Could not load annotations.json: {e}")
    
    try:
        if os.path.exists(authors_file):
            with open(authors_file, 'r', encoding='utf-8') as f:
                authors_data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load authors.json: {e}")
    
    return annotations_data, authors_data

def create_frontmatter(annotation_id: str, annotations_data: Dict[str, Any], 
                      authors_data: Dict[str, Any]) -> str:
    """
    Create enhanced frontmatter HTML for the document.
    
    Args:
        annotation_id (str): The annotation ID (extracted from filename)
        annotations_data (dict): Loaded annotations metadata
        authors_data (dict): Loaded authors metadata
        
    Returns:
        str: HTML frontmatter content
    """
    if annotation_id not in annotations_data:
        return ""
    
    annotation = annotations_data[annotation_id]
    
    # Build author information
    author_info = []
    for author_id in annotation.get('authorIDs', []):
        if author_id in authors_data:
            author = authors_data[author_id]
            author_name = author.get('fullName', '')
            author_type = author.get('authorType', '')
            if author_name and author_type:
                author_info.append(f"{author_name}<br><em>{author_type}</em>")
            elif author_name:
                author_info.append(author_name)
    
    # Extract abstract text (remove HTML tags for cleaner display)
    abstract = annotation.get('abstract', '')
    if abstract:
        # Parse HTML and extract text, but keep basic formatting
        abstract_soup = BeautifulSoup(abstract, 'html.parser')
        # Remove <mark> tags but keep content
        for mark in abstract_soup.find_all('mark'):
            mark.unwrap()
        abstract = str(abstract_soup)
    
    # Build frontmatter HTML
    frontmatter_parts = []
    
    # Title page
    full_title = annotation.get('fullTitle', annotation.get('name', ''))
    year = annotation.get('year', '')
    if full_title:
        frontmatter_parts.append(f'<div class="title-page">')
        frontmatter_parts.append(f'<h1 class="document-title">{full_title}</h1>')
        
        # Authors side by side
        if author_info:
            frontmatter_parts.append('<div class="authors-container">')
            for author in author_info:
                frontmatter_parts.append(f'<div class="author">{author}</div>')
            frontmatter_parts.append('</div>')
        
        # Year on title page
        if year:
            frontmatter_parts.append(f'<div class="title-year">{year}</div>')
        
        frontmatter_parts.append('</div>')
    
    # Citation page (verso)
    cite_as = annotation.get('citeAs', '')
    doi = annotation.get('doi', '')
    if cite_as or doi:
        frontmatter_parts.append('<div class="citation-page">')
        
        if cite_as:
            frontmatter_parts.append('<div class="citation-section">')
            frontmatter_parts.append('<h3>How to Cite</h3>')
            frontmatter_parts.append(f'<p class="citation-text">{cite_as}</p>')
            frontmatter_parts.append('</div>')
        
        if doi:
            frontmatter_parts.append(f'<div class="doi-section"><strong>DOI:</strong> <a href="{doi}">{doi}</a></div>')
        
        frontmatter_parts.append('</div>')
    
    # Abstract on separate page
    if abstract:
        frontmatter_parts.append('<div class="abstract-page">')
        frontmatter_parts.append('<h3>Abstract</h3>')
        frontmatter_parts.append(f'<div class="abstract-text">{abstract}</div>')
        frontmatter_parts.append('</div>')
    
    # Add page break before main content
    frontmatter_parts.append('<div class="page-break"></div>')
    
    return '\n'.join(frontmatter_parts)

def convert_endnotes_to_footnotes(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Convert endnotes structure to proper footnotes for PDF generation.
    
    This function:
    1. Finds all footnote references in the text
    2. Locates the corresponding footnote content
    3. Converts them to proper footnote format using CSS regions
    
    Args:
        soup (BeautifulSoup): Parsed HTML document
        
    Returns:
        BeautifulSoup: Modified document with footnotes
    """
    print("  Converting endnotes to footnotes...")
    
    # Find footnote references (links with class="footnote-ref" or href starting with "#fn")
    footnote_refs = soup.find_all('a', class_='footnote-ref')
    if not footnote_refs:
        # Also look for links starting with #fn
        footnote_refs = soup.find_all('a', href=re.compile(r'^#fn\d+'))
    
    # Find footnotes section (usually at the end of document)
    footnotes_section = soup.find('div', class_='footnotes')
    if not footnotes_section:
        # Look for other common footnote containers
        footnotes_section = soup.find('section', class_='footnotes')
        if not footnotes_section:
            footnotes_section = soup.find('div', id='footnotes')
    
    if not footnote_refs:
        print("    No footnote references found")
        return soup
    
    if not footnotes_section:
        print("    No footnotes section found")
        return soup
    
    print(f"    Found {len(footnote_refs)} footnote references")
    
    # Extract footnote content
    footnotes_content = {}
    footnotes_full_content = {}
    
    # Look for footnote list items
    footnote_items = footnotes_section.find_all('li')
    if not footnote_items:
        # Look for divs or other containers
        footnote_items = footnotes_section.find_all('div', class_=re.compile(r'footnote'))
    
    for item in footnote_items:
        # Try to extract footnote ID
        footnote_id = None
        if item.get('id'):
            footnote_id = item.get('id')
        elif item.find('a', id=True):
            footnote_id = item.find('a', id=True).get('id')
        
        if footnote_id:
            # Get the text content, removing return links
            content_copy = BeautifulSoup(str(item), 'html.parser')
            
            # Remove return links (usually links back to the reference)
            for return_link in content_copy.find_all('a', href=re.compile(r'^#fnref')):
                return_link.decompose()
            
            # Extract text content and full HTML content
            text_content = content_copy.get_text(strip=True)
            full_content = str(content_copy)
            if text_content:
                footnotes_content[footnote_id] = text_content
                footnotes_full_content[footnote_id] = full_content
    
    print(f"    Extracted {len(footnotes_content)} footnote contents")
    
    # Convert footnote references to proper superscript with CSS footnote markup
    footnote_counter = 1
    for ref in footnote_refs:
        href = ref.get('href', '')
        if href.startswith('#'):
            footnote_id = href[1:]  # Remove the #
            
            if footnote_id in footnotes_content:
                footnote_text = footnotes_content[footnote_id]
                
                # Get the reference number from the link text
                ref_number = ref.get_text(strip=True)
                if not ref_number or not ref_number.isdigit():
                    ref_number = str(footnote_counter)
                
                # Create a proper footnote structure that WeasyPrint can handle
                footnote_container = soup.new_tag('span', class_='footnote-container')
                
                # Footnote call (superscript number in text)
                footnote_call = soup.new_tag('a', class_='footnote-ref')
                footnote_call['href'] = f'#footnote-{footnote_counter}'
                footnote_call['id'] = f'footnote-ref-{footnote_counter}'
                footnote_call_sup = soup.new_tag('sup')
                footnote_call_sup.string = ref_number
                footnote_call.append(footnote_call_sup)
                
                # Footnote content (hidden, will be moved to page bottom by CSS)
                footnote_content = soup.new_tag('span', class_='footnote-content')
                footnote_content['id'] = f'footnote-{footnote_counter}'
                footnote_content['data-footnote-number'] = ref_number
                footnote_content.string = footnote_text
                
                footnote_container.append(footnote_call)
                footnote_container.append(footnote_content)
                
                # Replace the original reference
                ref.replace_with(footnote_container)
                footnote_counter += 1
    
    # Remove the original footnotes section since we've converted them
    if footnotes_section:
        footnotes_section.decompose()
    
    print("    Endnotes conversion completed")
    return soup

def prepare_html_for_conversion(html_file_path: str, css_file_path: str, 
                               html_dir: str = None) -> str:
    """
    Prepare HTML file for conversion by adding CSS, optimizing structure, and converting footnotes.
    
    This function:
    1. Parses the HTML file
    2. Converts endnotes to footnotes
    3. Injects the academic CSS stylesheet
    4. Optimizes the document structure for PDF/EPUB
    5. Handles relative links and resources
    
    Args:
        html_file_path (str): Path to the HTML file to process
        css_file_path (str): Path to the CSS stylesheet
        html_dir (str): Directory containing HTML files and metadata (optional)
        
    Returns:
        str: Modified HTML content ready for conversion
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Load metadata if html_dir is provided
    annotations_data = {}
    authors_data = {}
    if html_dir:
        annotations_data, authors_data = load_metadata(html_dir)
    
    # Extract annotation ID from filename
    filename = os.path.basename(html_file_path)
    annotation_id = os.path.splitext(filename)[0]
    
    # Ensure proper HTML structure
    if not soup.html:
        # Wrap content in html tags if missing
        new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
        if soup.head:
            new_soup.head.replace_with(soup.head)
        if soup.body:
            new_soup.body.replace_with(soup.body)
        else:
            # Move all content to body
            for element in soup.contents:
                if hasattr(element, 'name'):
                    new_soup.body.append(element.extract())
        soup = new_soup
    
    # Ensure head section exists
    if not soup.head:
        head = soup.new_tag('head')
        soup.html.insert(0, head)
    
    # Add UTF-8 meta tag
    meta_charset = soup.find('meta', attrs={'charset': True})
    if not meta_charset:
        meta = soup.new_tag('meta', charset='utf-8')
        soup.head.insert(0, meta)
    
    # Add viewport meta for responsive design
    meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not meta_viewport:
        meta = soup.new_tag('meta', 
                           attrs={'name': 'viewport', 
                                 'content': 'width=device-width, initial-scale=1.0'})
        soup.head.append(meta)
    
    # Read and embed CSS
    with open(css_file_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Remove any existing links to external stylesheets to avoid conflicts
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    
    # Add our CSS as an embedded stylesheet
    style_tag = soup.new_tag('style', type='text/css')
    style_tag.string = css_content
    soup.head.append(style_tag)
    
    # Convert endnotes to footnotes BEFORE adding frontmatter
    soup = convert_endnotes_to_footnotes(soup)
    
    # Create and insert enhanced frontmatter if metadata is available
    if annotations_data and annotation_id in annotations_data:
        frontmatter_html = create_frontmatter(annotation_id, annotations_data, authors_data)
        if frontmatter_html:
            frontmatter_soup = BeautifulSoup(frontmatter_html, 'html.parser')
            
            # Remove the existing simple title structure if present
            existing_h1 = soup.body.find('h1')
            existing_h4 = None
            if existing_h1:
                # Look for h4 right after h1 (author info)
                next_sibling = existing_h1.find_next_sibling()
                if next_sibling and next_sibling.name == 'h4':
                    existing_h4 = next_sibling
            
            # Insert frontmatter at the beginning of body
            for element in reversed(frontmatter_soup.contents):
                if hasattr(element, 'name'):
                    soup.body.insert(0, element)
            
            # Remove old title elements if they exist
            if existing_h1:
                existing_h1.decompose()
            if existing_h4:
                existing_h4.decompose()
    
    # Add a title if missing
    if not soup.title:
        title_tag = soup.new_tag('title')
        # Try to extract title from h1 or use filename
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title_tag.string = h1.get_text(strip=True)
        else:
            filename = os.path.basename(html_file_path)
            title_tag.string = os.path.splitext(filename)[0].replace('_', ' ').title()
        soup.head.append(title_tag)
    
    # Convert relative image paths to absolute paths
    html_dir_path = os.path.dirname(html_file_path)
    for img in soup.find_all('img', src=True):
        src = img['src']
        if not src.startswith(('http://', 'https://', 'data:')):
            # Convert to absolute path
            abs_path = os.path.abspath(os.path.join(html_dir_path, src))
            if os.path.exists(abs_path):
                img['src'] = f"file://{abs_path}"
            else:
                print(f"Warning: Image not found: {abs_path}")
    
    return str(soup)

def convert_to_pdf(html_content: str, output_path: str) -> bool:
    """
    Convert HTML content to PDF using WeasyPrint.
    
    Args:
        html_content (str): HTML content to convert
        output_path (str): Path where PDF should be saved
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Create WeasyPrint HTML document
        html_doc = weasyprint.HTML(string=html_content, base_url=os.getcwd())
        
        # Generate PDF
        html_doc.write_pdf(output_path)
        return True
        
    except Exception as e:
        print(f"PDF conversion error: {e}")
        return False

def convert_to_epub(html_file_path: str, output_path: str, temp_dir: str) -> bool:
    """
    Convert HTML file to EPUB using Pandoc.
    
    Args:
        html_file_path (str): Path to the HTML file
        output_path (str): Path where EPUB should be saved
        temp_dir (str): Temporary directory for intermediate files
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Use pandoc to convert HTML to EPUB
        cmd = [
            'pandoc',
            html_file_path,
            '-o', output_path,
            '--epub-metadata=<dc:language>en</dc:language>',
            '--epub-cover-image=', # Empty to disable default cover
            '--self-contained'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"Pandoc error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"EPUB conversion error: {e}")
        return False

def process_html_files(html_dir: str, output_dir: str, css_file: str, 
                      create_pdf: bool = True, create_epub: bool = True) -> Tuple[int, int, List[str]]:
    """
    Process all HTML files in the directory for conversion.
    
    Args:
        html_dir (str): Directory containing HTML files
        output_dir (str): Directory to save converted files
        css_file (str): Path to CSS stylesheet
        create_pdf (bool): Whether to create PDF files
        create_epub (bool): Whether to create EPUB files
        
    Returns:
        tuple: (successful_conversions, total_files, error_list)
    """
    # Find all HTML files
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    total_files = len(html_files)
    successful_conversions = 0
    errors = []
    
    print(f"Found {total_files} HTML files to convert")
    
    # Create output directories
    if create_pdf:
        pdf_dir = os.path.join(output_dir, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
    
    if create_epub:
        epub_dir = os.path.join(output_dir, 'epubs')
        os.makedirs(epub_dir, exist_ok=True)
    
    # Process each file
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, html_file in enumerate(html_files, 1):
            base_name = os.path.splitext(html_file)[0]
            html_path = os.path.join(html_dir, html_file)
            
            print(f"Processing {i}/{total_files}: {html_file}")
            
            try:
                # Prepare HTML content
                prepared_html = prepare_html_for_conversion(html_path, css_file, html_dir)
                
                # Create temporary HTML file for processing
                temp_html_path = os.path.join(temp_dir, f"{base_name}_prepared.html")
                with open(temp_html_path, 'w', encoding='utf-8') as f:
                    f.write(prepared_html)
                
                file_success = True
                
                # Convert to PDF
                if create_pdf:
                    pdf_path = os.path.join(pdf_dir, f"{base_name}.pdf")
                    if convert_to_pdf(prepared_html, pdf_path):
                        print(f"  ✓ PDF created: {pdf_path}")
                    else:
                        print(f"  ✗ PDF conversion failed")
                        errors.append(f"PDF conversion failed for {html_file}")
                        file_success = False
                
                # Convert to EPUB
                if create_epub:
                    epub_path = os.path.join(epub_dir, f"{base_name}.epub")
                    if convert_to_epub(temp_html_path, epub_path, temp_dir):
                        print(f"  ✓ EPUB created: {epub_path}")
                    else:
                        print(f"  ✗ EPUB conversion failed")
                        errors.append(f"EPUB conversion failed for {html_file}")
                        file_success = False
                
                if file_success:
                    successful_conversions += 1
                    
            except Exception as e:
                error_msg = f"Error processing {html_file}: {e}"
                print(f"  ✗ {error_msg}")
                errors.append(error_msg)
    
    return successful_conversions, total_files, errors

def main():
    """
    Main function that orchestrates the conversion process.
    """
    parser = argparse.ArgumentParser(description='Convert HTML files to PDF and EPUB formats with footnotes')
    parser.add_argument('--pdf-only', action='store_true', 
                       help='Create only PDF files')
    parser.add_argument('--epub-only', action='store_true', 
                       help='Create only EPUB files')
    parser.add_argument('--output-dir', '-o', default='./converted_documents_footnotes',
                       help='Output directory for converted files (default: ./converted_documents_footnotes)')
    parser.add_argument('--html-dir', default='../html',
                       help='Directory containing HTML files (default: ../html)')
    
    args = parser.parse_args()
    
    # Determine what to create
    if args.pdf_only and args.epub_only:
        print("Error: Cannot specify both --pdf-only and --epub-only")
        sys.exit(1)
    
    create_pdf = not args.epub_only
    create_epub = not args.pdf_only
    
    # Check if directories exist
    html_dir = os.path.abspath(args.html_dir)
    if not os.path.exists(html_dir):
        print(f"Error: HTML directory not found: {html_dir}")
        sys.exit(1)
    
    css_file = os.path.join(os.path.dirname(__file__), 'academic-print-footnotes.css')
    if not os.path.exists(css_file):
        # Fall back to regular CSS if footnotes version doesn't exist
        css_file = os.path.join(os.path.dirname(__file__), 'academic-print.css')
        if not os.path.exists(css_file):
            print(f"Error: CSS file not found: {css_file}")
            sys.exit(1)
    
    # Check dependencies
    print("Checking dependencies...")
    missing_python, missing_system = check_dependencies()
    
    if missing_python:
        print(f"Missing Python packages: {', '.join(missing_python)}")
        print("Install with: pip install " + " ".join(missing_python))
        sys.exit(1)
    
    if missing_system:
        if create_epub and 'pandoc' in missing_system:
            print("Warning: pandoc not found. EPUB creation will be disabled.")
            create_epub = False
        if not create_pdf and not create_epub:
            print("No conversion tools available.")
            sys.exit(1)
    
    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting files from: {html_dir}")
    print(f"Output directory: {output_dir}")
    print(f"CSS stylesheet: {css_file}")
    print(f"Creating: {'PDF' if create_pdf else ''} {'EPUB' if create_epub else ''}")
    print("Special feature: Converting endnotes to footnotes")
    print("=" * 60)
    
    # Process files
    successful, total, errors = process_html_files(
        html_dir, output_dir, css_file, create_pdf, create_epub
    )
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY (FOOTNOTES VERSION)")
    print("=" * 60)
    print(f"Total HTML files: {total}")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {total - successful}")
    
    if errors:
        print(f"\nErrors encountered ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if successful > 0:
        print(f"\n✓ Converted files saved to: {output_dir}")
        if create_pdf:
            print(f"  PDFs: {os.path.join(output_dir, 'pdfs')}")
        if create_epub:
            print(f"  EPUBs: {os.path.join(output_dir, 'epubs')}")
    
    # Save detailed report
    report_path = os.path.join(output_dir, 'conversion_report_footnotes.txt')
    with open(report_path, 'w') as f:
        f.write("PDF/EPUB Conversion Report (Footnotes Version)\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"HTML directory: {html_dir}\n")
        f.write(f"Output directory: {output_dir}\n")
        f.write(f"CSS stylesheet: {css_file}\n")
        f.write(f"Formats created: {'PDF' if create_pdf else ''} {'EPUB' if create_epub else ''}\n")
        f.write("Special feature: Endnotes converted to footnotes\n\n")
        f.write(f"Total files processed: {total}\n")
        f.write(f"Successful conversions: {successful}\n")
        f.write(f"Failed conversions: {total - successful}\n\n")
        
        if errors:
            f.write("Errors:\n")
            for error in errors:
                f.write(f"  - {error}\n")
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()