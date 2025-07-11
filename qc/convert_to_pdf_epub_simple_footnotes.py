#!/usr/bin/env python3
"""
PDF and EPUB Converter for HTML Files - Simple Footnotes Version

This version improves footnote formatting without complex conversion.
It keeps endnotes but ensures proper superscript formatting and styling.

Key Features:
- Improved superscript formatting for footnote references
- Enhanced endnotes styling
- Maintains all frontmatter enhancements
- Academic-focused CSS styling for professional output

Usage:
    python convert_to_pdf_epub_simple_footnotes.py [--pdf-only] [--output-dir OUTPUT]
"""

# Import the main conversion functions but skip the complex footnote conversion
from convert_to_pdf_epub_footnotes import (
    check_dependencies, load_metadata, create_frontmatter, 
    convert_to_pdf, process_html_files, main as main_template
)
import os
import sys
import argparse
import json
from typing import Dict, Any
from bs4 import BeautifulSoup

def prepare_html_for_conversion(html_file_path: str, css_file_path: str, 
                               html_dir: str = None) -> str:
    """
    Prepare HTML file for conversion with improved footnote formatting.
    
    This version:
    1. Parses the HTML file
    2. Improves footnote reference formatting (ensures proper superscript)
    3. Enhances endnotes section styling
    4. Injects the academic CSS stylesheet
    5. Optimizes the document structure for PDF/EPUB
    
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
        new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
        if soup.head:
            new_soup.head.replace_with(soup.head)
        if soup.body:
            new_soup.body.replace_with(soup.body)
        else:
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
    
    # Remove any existing links to external stylesheets
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    
    # Add our CSS as an embedded stylesheet
    style_tag = soup.new_tag('style', type='text/css')
    style_tag.string = css_content
    soup.head.append(style_tag)
    
    # Improve footnote formatting (keep as endnotes but enhance styling)
    print("  Improving footnote formatting...")
    
    # Find and enhance footnote references
    footnote_refs = soup.find_all('a', class_='footnote-ref')
    if footnote_refs:
        print(f"    Found {len(footnote_refs)} footnote references")
        for ref in footnote_refs:
            # Ensure proper superscript formatting
            sup_elem = ref.find('sup')
            if sup_elem:
                # Add CSS class for consistent styling
                ref.attrs['class'] = ref.get('class', []) + ['enhanced-footnote-ref']
                sup_elem.attrs['class'] = sup_elem.get('class', []) + ['enhanced-footnote-sup']
    
    # Enhance footnotes section
    footnotes_section = soup.find('div', class_='footnotes')
    if footnotes_section:
        print(f"    Enhanced footnotes section")
        footnotes_section.attrs['class'] = footnotes_section.get('class', []) + ['enhanced-footnotes']
        
        # Add section title if missing
        h2_title = footnotes_section.find('h2')
        if not h2_title:
            title = soup.new_tag('h2')
            title.string = 'Notes'
            footnotes_section.insert(0, title)
    
    # Create and insert enhanced frontmatter if metadata is available
    if annotations_data and annotation_id in annotations_data:
        frontmatter_html = create_frontmatter(annotation_id, annotations_data, authors_data)
        if frontmatter_html:
            frontmatter_soup = BeautifulSoup(frontmatter_html, 'html.parser')
            
            # Remove the existing simple title structure if present
            existing_h1 = soup.body.find('h1')
            existing_h4 = None
            if existing_h1:
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
            abs_path = os.path.abspath(os.path.join(html_dir_path, src))
            if os.path.exists(abs_path):
                img['src'] = f"file://{abs_path}"
            else:
                print(f"Warning: Image not found: {abs_path}")
    
    return str(soup)

def main():
    """Main function for simple footnotes version."""
    parser = argparse.ArgumentParser(description='Convert HTML files to PDF with enhanced footnote formatting')
    parser.add_argument('--pdf-only', action='store_true', 
                       help='Create only PDF files')
    parser.add_argument('--output-dir', '-o', default='./converted_documents_simple_footnotes',
                       help='Output directory for converted files')
    parser.add_argument('--html-dir', default='../html',
                       help='Directory containing HTML files')
    
    args = parser.parse_args()
    
    # Check if directories exist
    html_dir = os.path.abspath(args.html_dir)
    if not os.path.exists(html_dir):
        print(f"Error: HTML directory not found: {html_dir}")
        sys.exit(1)
    
    css_file = os.path.join(os.path.dirname(__file__), 'academic-print-simple-footnotes.css')
    if not os.path.exists(css_file):
        # Fall back to regular CSS
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
    
    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting files from: {html_dir}")
    print(f"Output directory: {output_dir}")
    print(f"CSS stylesheet: {css_file}")
    print("Creating: PDF with enhanced footnote formatting")
    print("=" * 60)
    
    # Process files - only PDF, enhanced footnotes
    successful, total, errors = process_html_files(
        html_dir, output_dir, css_file, create_pdf=True, create_epub=False
    )
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY (SIMPLE FOOTNOTES VERSION)")
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
        print(f"  PDFs: {os.path.join(output_dir, 'pdfs')}")

if __name__ == "__main__":
    main()